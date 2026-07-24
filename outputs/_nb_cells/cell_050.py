# ── 7.2  Lanzar entrenamiento + monitor en paralelo ─────────────────────────
# SOLO en VM Colab (A100). No ejecutar con kernel Python local en VS Code.
LAUNCH_FULL_TRAINING = True

import importlib.util
_IN_COLAB_72 = importlib.util.find_spec('google.colab') is not None

# Bootstrap integral en Colab: git 1.2 + Drive 1.5 + OUTPUT_ROOT 2.1 + config 6.1/7.0.
if _IN_COLAB_72:
    import sys as _sys72
    import subprocess as _sp72
    from pathlib import Path as _Path72
    _repo72 = _Path72(globals().get('REPO', '/content/MADRLCitytleranflexresdr'))
    _helpers72 = _repo72 / 'CityLearn/scripts/colab_notebook_launch_helpers.py'
    if not _helpers72.is_file() and not (_repo72 / '.git').is_dir():
        print('[7.2] Runtime nuevo: clonando repo para bootstrap...')
        _sp72.check_call([
            'git', 'clone', '--branch', 'codex/fix-madrl-traceability-docs',
            '--depth', '1', '--recurse-submodules', '--shallow-submodules',
            'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git', str(_repo72),
        ])
    if not _helpers72.is_file():
        raise RuntimeError(
            f'Falta {_helpers72}. Ejecuta celda 1.2 una vez o reinicia con REPO vacio.'
        )
    _spec72 = importlib.util.spec_from_file_location('_nb72_helpers', _helpers72)
    _mod72 = importlib.util.module_from_spec(_spec72)
    _spec72.loader.exec_module(_mod72)
    _mod72.prepare_colab_cell_72_standalone(
        globals(),
        repo=_repo72,
        resume_output_root=globals().get('RESUME_OUTPUT_ROOT'),
        skip_git_sync=bool(globals().get('CELL_72_SKIP_GIT_SYNC', False)),
    )

if LAUNCH_FULL_TRAINING and not _IN_COLAB_72:
    raise RuntimeError(
        'Entrenamiento oficial bloqueado en maquina local.\n'
        '  En VS Code: Select Kernel -> Google Colab -> A100 High-RAM (no .venv local).\n'
        '  O abre el notebook en colab.research.google.com y ejecuta 1.2 -> 7.2.\n'
        '  Local solo sirve para editar codigo / dry-run ligero; el compute es la VM Google.'
    )

if not LAUNCH_FULL_TRAINING:
    print('LAUNCH_FULL_TRAINING=False — cambia a True para entrenar.')
else:
    import signal as _signal
    import subprocess
    import sys
    import time
    import json as _json
    import threading as _th
    from pathlib import Path as _P
    from datetime import datetime as _DT, timezone as _TZ

    _repo    = globals().get('REPO', '/content/MADRLCitytleranflexresdr')
    if not Path(_repo).exists():
        _repo = next((p for p in ('d:/MADRLCitytleranflexresdr', str(Path.cwd()))
                      if (Path(p) / 'CityLearn').exists()), _repo)
    _python  = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
    _MON_INTERVAL = int(globals().get('MONITOR_INTERVAL', 120))
    _POLL_SLEEP   = 10   # segundos entre polls del proceso; reduce CPU local del notebook
    _AUTO_DISCONNECT = bool(globals().get('AUTO_DISCONNECT_COLAB', False))

    def _disconnect_colab(reason, delay_s=20):
        if not _AUTO_DISCONNECT:
            print(f'\n[7.2] Kernel activo (AUTO_DISCONNECT_COLAB=False). {reason}.')
            return
        try:
            from google.colab import runtime as _colab_rt  # type: ignore[import-not-found]
            print(f'\n[7.2] Desconectando runtime Colab en {delay_s}s ({reason})...')
            sys.stdout.flush()
            time.sleep(delay_s)
            _colab_rt.unassign()
        except Exception as _dc_exc:
            print(f'[7.2] No se pudo desconectar Colab automaticamente: {_dc_exc}')

    _TWO_PHASE = (
        ('happo', 'masac'),
        ('matd3', 'maac'),
    )
    _EST_BY_ALGO = globals().get('EST_MIN_BY_ALGO', {'happo': 11, 'masac': 15, 'matd3': 12, 'maac': 8})
    _EST_PHASE = int(globals().get('EST_MIN_PER_EPISODE', 12))

    def _detect_hw_label():
        """Banner dinamico: GPU real (nvidia-smi) + RAM real, no valores fijos A100."""
        gpu = 'GPU?'
        try:
            _out = subprocess.check_output(
                ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
                text=True, stderr=subprocess.DEVNULL,
            ).strip().splitlines()[0]
            _name, _vram = _out.split(',')
            gpu = f'{_name.strip()} {int(_vram)/1024:.0f}GiB'
        except Exception:
            pass
        ram = ''
        try:
            with open('/proc/meminfo') as _f:
                for _ln in _f:
                    if _ln.startswith('MemTotal'):
                        ram = f" + {int(_ln.split()[1]) / (1024 * 1024):.0f}GiB RAM"
                        break
        except Exception:
            pass
        return f'{gpu}{ram}'

    _HW_LABEL = _detect_hw_label()

    def _job_done(j):
        if j.get('planned_only'):
            return False
        if j.get('skipped'):
            return True
        return j.get('exit_code') == 0

    def _job_running(j):
        return (j.get('completed_at') is None
                and not j.get('planned_only')
                and not j.get('skipped'))

    def _infer_phase(all_jobs):
        for phase_idx, algos in enumerate(_TWO_PHASE, 1):
            phase_jobs = [j for j in all_jobs if j.get('name') in algos]
            if not phase_jobs:
                continue
            if any(not _job_done(j) for j in phase_jobs):
                return phase_idx, algos
        return 0, ()

    _LP_STALE_SEC = int(globals().get('LIVE_PROGRESS_STALE_SEC', 600))

    def _ep_progress(lp, n_ep, ep_steps):
        """Grounded episode index + step for ETA and display (handles boundary writes)."""
        if not lp:
            return 0, 0, 0, 0
        completed = int(lp.get('completed_episode_count') or 0)
        ep = int(lp.get('episode', 0))
        ep_step = int(lp.get('episode_step', 0))
        if ep_step >= ep_steps:
            ep = min(ep + 1, n_ep)
            ep_step = 0
        ep_show = min(max(completed, ep + 1), n_ep)
        ep_step_show = ep_steps if ep_step >= ep_steps else ep_step
        return ep, ep_step, ep_show, ep_step_show

    def _eta_minutes(lp, algo, n_ep, ep_steps):
        if not lp:
            return n_ep * _EST_BY_ALGO.get(algo, 13)
        ep, ep_step, _, _ = _ep_progress(lp, n_ep, ep_steps)
        rem_steps = max(0, (n_ep - ep - 1) * ep_steps + (ep_steps - ep_step))
        fps = lp.get('fps')
        try:
            fps = float(fps)
        except (TypeError, ValueError):
            fps = 0.0
        if fps > 0.1:
            return rem_steps / fps / 60.0
        mins_per_ep = _EST_BY_ALGO.get(algo, 13)
        return (rem_steps / max(ep_steps, 1)) * mins_per_ep

    _SCENARIO_WEIGHTS = {
        'E1': {'OE1 flex': 0.70, 'OE2 CO2': 0.15, 'OE3 cost': 0.15},
        'E2': {'OE1 flex': 0.15, 'OE2 CO2': 0.70, 'OE3 cost': 0.15},
        'E3': {'OE1 flex': 0.25, 'OE2 CO2': 0.15, 'OE3 cost': 0.60},
    }
    _ALGOS    = ['HAPPO', 'MASAC', 'MATD3', 'MAAC']
    _SCENS    = ['E1', 'E2', 'E3']
    _SEP      = '=' * 78
    _SEP_THIN = '-' * 78

    # ── helpers ───────────────────────────────────────────────────────────────
    def _progress_bar(n, total, width=18):
        filled = int(width * n / max(total, 1))
        return '█' * filled + '░' * (width - filled)

    def _fmt_pct(v):
        if v is None:
            return '   N/A '
        sign = '+' if v >= 0 else ''
        return f'{sign}{v * 100:.1f}%'

    def _utc_now():
        return _DT.now(_TZ.utc)

    def _lag_seconds(ts_str):
        if not ts_str:
            return None
        try:
            ts = _DT.fromisoformat(ts_str.replace('Z', '+00:00'))
            return (_utc_now() - ts).total_seconds()
        except Exception:
            return None

    def _resolve_job_lp(out, job, lp_cache):
        algo = str(job.get('name', '')).lower()
        esc = str(job.get('scenario', '')).upper()
        key = (algo, esc)
        if key in lp_cache:
            return lp_cache[key]
        odir = str(job.get('output_dir') or '').strip()
        if not odir:
            return None
        lpf = _P(odir) if _P(odir).is_absolute() else out / odir
        lpf = lpf / 'live_progress.json'
        if not lpf.is_file():
            return None
        try:
            lp = _json.loads(lpf.read_text(encoding='utf-8'))
        except Exception:
            return None
        lag = _lag_seconds(lp.get('live_status_updated_at', ''))
        lp['_lag'] = lag
        lp['_stale'] = lag is None or lag > _LP_STALE_SEC
        lp_cache[key] = lp
        return lp

    def _collect_running_progress(out, all_jobs):
        lp_cache = {}
        for lpf in out.rglob('live_progress.json'):
            try:
                lp = _json.loads(lpf.read_text(encoding='utf-8'))
            except Exception:
                continue
            key = (str(lp.get('algorithm', '')).lower(),
                   str(lp.get('scenario', '')).upper())
            lag = _lag_seconds(lp.get('live_status_updated_at', ''))
            lp['_lag'] = lag
            lp['_stale'] = lag is None or lag > _LP_STALE_SEC
            lp_cache[key] = lp
        active_lp = []
        for job in all_jobs:
            if not _job_running(job):
                continue
            lp = _resolve_job_lp(out, job, lp_cache)
            if lp is None:
                lp = {
                    'algorithm': job.get('name', '?'),
                    'scenario': job.get('scenario', '?'),
                    '_lag': None,
                    '_stale': True,
                    'live_status': 'waiting_for_progress',
                }
            active_lp.append(lp)
        order = {a: i for i, a in enumerate(_ALGOS)}
        scen_order = {s: i for i, s in enumerate(_SCENS)}
        active_lp.sort(key=lambda lp: (
            order.get(str(lp.get('algorithm', '')).upper(), 99),
            scen_order.get(str(lp.get('scenario', '')).upper(), 99),
        ))
        return active_lp, lp_cache

    def _load_resume_report(out):
        """Misma fuente que 2.1b / 7.1 / --skip-completed (artefactos en disco)."""
        import importlib.util
        common_mod = _P(_repo) / 'CityLearn/scripts/citylearn_v3_training_common.py'
        spec = importlib.util.spec_from_file_location('_cl_v3_panel', common_mod)
        if spec is None or spec.loader is None:
            return {'jobs': [], 'completed': 0, 'resumable': 0, 'pending': 0, 'progress_pct': 0.0}
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        n_ep = int(globals().get('N_EPISODES', globals().get('EPISODES', 50)))
        seed = int(globals().get('SEED', 0))
        return mod.build_jobs_resume_report(
            _P(out),
            target_episodes=n_ep,
            seed=seed,
            episode_time_steps=int(globals().get('EPISODE_STEPS', 8760)),
            happo_rollout_threads=int(globals().get('HAPPO_ROLLOUT_THREADS', 0)) or None,
        )

    def _resumable_action(row):
        act = str((row or {}).get('action') or '').lower()
        return act in ('resume', 'happo_salvage_kpi')

    def _resume_row_map(report):
        rows = report.get('jobs') or []
        return {
            (str(r.get('algorithm', '')).lower(), str(r.get('scenario', '')).upper()): r
            for r in rows
        }

    def _artifact_complete(resume_map, algo, esc):
        row = resume_map.get((str(algo).lower(), str(esc).upper()))
        return bool(row and row.get('action') == 'skip')

    # ── panel principal de estado ─────────────────────────────────────────────
    def _print_panel(output_root):
        out = _P(output_root)
        now_str = _utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')
        print('\n' + _SEP)
        print(f'  MADRL CityLearn v3  |  {_HW_LABEL}  |  {now_str}')
        print(f'  Run: {out.name}')
        _est_min_ep = int(globals().get('EST_MIN_PER_EPISODE', 13))
        _n_ep = int(globals().get('N_EPISODES', globals().get('EPISODES', 50)))
        _ep_steps = int(globals().get('EPISODE_STEPS', 8760))
        _total_prior_h = 2 * _EST_PHASE * _n_ep / 60
        _dyn_bf = bool(globals().get('DYNAMIC_BACKFILL', True))
        _mode_txt = ('backfill dinámico (6 en paralelo; fase 2 entra solo al terminar un job de fase 1)'
                     if _dyn_bf else '2 fases (6 jobs/fase)')
        print(f'  Modo: {globals().get("EXECUTION_MODE", "two_phase_happo_masac")} | '
              f'{_mode_txt} | prior ~{_total_prior_h:.0f} h (límite superior) | ETA dinámico con FPS')
        print(_SEP)

        # ── 1. Estado global (artefactos en disco = misma verdad que launcher) ──
        _resume = _load_resume_report(out)
        _resume_map = _resume_row_map(_resume)
        status_file = out / 'official_full_status.json'
        all_jobs = []
        st = {}
        if status_file.exists():
            try:
                st = _json.loads(status_file.read_text())
                all_jobs = st.get('jobs', [])
            except Exception as e:
                print(f'  [status] error leyendo official_full_status.json: {e}')

        done_art = int(_resume.get('completed') or 0)
        resume_n = int(_resume.get('resumable') or 0)
        pending_n = int(_resume.get('pending') or 0) + int(_resume.get('restart_fresh') or 0)
        fail = sum(1 for j in all_jobs if j.get('exit_code') not in (None, 0) and not j.get('skipped'))
        run = resume_n
        total = 12
        _gp = float(_resume.get('progress_pct') or 0) / 100.0 * total
        bar12 = _progress_bar(_gp, total, 24)
        print(f'\n  PROGRESO GLOBAL  [{bar12}]  '
              f'{done_art}/{total} OK (artefactos)  {run} activas  {fail} fallo  {pending_n} pendientes')
        if st:
            print(f'  status = {st.get("status", "?")}')
            _par = st.get('parallelization') or {}
            if _par:
                print(f'  paralelismo: {_par.get("strategy", "?")}')
        _dyn_bf = bool((st.get('parallelization') or {}).get('dynamic_backfill', globals().get('DYNAMIC_BACKFILL', True)))
        _p1_done = sum(1 for a in ('happo', 'masac') for s in _SCENS if _artifact_complete(_resume_map, a, s))
        _p2_done = sum(1 for a in ('matd3', 'maac') for s in _SCENS if _artifact_complete(_resume_map, a, s))
        _p2_run = sum(1 for a in ('matd3', 'maac') for s in _SCENS
                      if not _artifact_complete(_resume_map, a, s)
                      and _resumable_action(_resume_map.get((a, s))))
        if done_art >= total:
            print('  progreso     : completado (12/12 artefactos verificados)')
        elif _dyn_bf:
            print(f'  backfill dinámico | fase1 HAPPO+MASAC {_p1_done}/6 ok | '
                  f'fase2 MATD3+MAAC {_p2_done}/6 ok ({_p2_run} activos) | {run} activos total (cap 6)')
        else:
            print(f'  jobs por artefactos: {done_art} ok | {run} reanudables | {pending_n} pendientes')

        # ── 2. Live progress (solo jobs NO completos por artefacto) ─────────────
        _running_jobs = [
            j for j in all_jobs
            if _job_running(j)
            and not _artifact_complete(_resume_map, j.get('name'), j.get('scenario'))
        ]
        active_lp, lp_cache = _collect_running_progress(out, _running_jobs) if _running_jobs else ([], {})
        _lp_key = dict(lp_cache)

        try:
            _dyn_bf = bool(globals().get('DYNAMIC_BACKFILL', True))
            _cap = 6
            _rem = []
            _run_rem = []
            for row in _resume.get('jobs') or []:
                if row.get('action') == 'skip':
                    continue
                _a = str(row.get('algorithm', '')).lower()
                _s = str(row.get('scenario', '')).upper()
                _lp = _lp_key.get((_a, _s))
                if _resumable_action(row) and _lp:
                    _m = _eta_minutes(_lp, _a, _n_ep, _ep_steps)
                    _run_rem.append(_m)
                else:
                    _done_ep = int(row.get('completed_episodes') or 0)
                    _m = max(0, _n_ep - _done_ep) * _EST_BY_ALGO.get(_a, 13)
                _rem.append(_m)
            if _rem:
                _eta_run = max(_run_rem) if _run_rem else 0.0
                _eta_total = max(max(_rem), sum(_rem) / max(_cap, 1))
                print(f'  ETA activos: ~{_eta_run/60:.1f} h | '
                      f'ETA restante ({len(_rem)} jobs, cap {_cap}): ~{_eta_total/60:.1f} h')
        except Exception:
            pass

        if active_lp:
            print(f'\n  CORRIDAS ACTIVAS  ({len(active_lp)} en paralelo)')
            hdr = f'  {"ALGO/ESC":<10} {"Episodio":>10}  {"ep_step":>12}  {"FPS":>6}  {"r_mix_mean":>11}  {"Lag":>6}  Estado'
            print(hdr)
            print('  ' + _SEP_THIN[:76])
            def _cn(v, nd=3):
                try:
                    return f'{float(v):+.{nd}f}'
                except (TypeError, ValueError):
                    return '   —  '
            for lp in active_lp:
                algo  = lp.get('algorithm', '?').upper()
                esc   = lp.get('scenario', '?').upper()
                ep_steps = int(lp.get('episode_time_steps', _ep_steps))
                _, _, ep, ep_step = _ep_progress(lp, _n_ep, ep_steps)
                try:
                    fps = float(lp.get('fps') or 0.0)
                except (TypeError, ValueError):
                    fps = 0.0
                ret = lp.get('mean_return', lp.get('episode_reward_mean_cumulative'))
                lag = lp.get('_lag')
                lag_s = f'{lag:.0f}s' if lag is not None else '  n/d'
                if lp.get('_stale'):
                    lag_s += '!'
                bar_s = _progress_bar((ep - 1) + ep_step / max(ep_steps, 1), _n_ep, 16)
                ret_s = f'{float(ret):+.4f}' if ret is not None else '    —   '
                fps_s = f'{fps:.1f}' if fps > 0 else '  —  '
                stage = str(lp.get('live_status') or '?')
                if lp.get('backend_training_active'):
                    stage += '+GPU'
                print(f'  {algo}/{esc:<5}  [{bar_s}] {ep:>3}/{_n_ep}  {ep_step:>5}/{ep_steps:<5}  '
                      f'{fps_s:>6}  {ret_s:>11}  {lag_s:>6}  {stage}')
                print(f'  {"":<12}comp  flex={_cn(lp.get("reward_component_flex_mean"))} '
                      f'co2={_cn(lp.get("reward_component_carbon_mean"))} '
                      f'cost={_cn(lp.get("reward_component_cost_mean"))} '
                      f'ev={_cn(lp.get("reward_component_ev_mean"))} '
                      f'team={_cn(lp.get("reward_team_reward"))}')
                print(f'  {"":<12}kpi   cost={_cn(lp.get("district_net_electricity_consumption_cost"), 2)} '
                      f'co2={_cn(lp.get("district_net_electricity_consumption_emission"), 2)} '
                      f'load={_cn(lp.get("district_net_electricity_consumption"), 2)} '
                      f'price={_cn(lp.get("electricity_price_mean"))}')
        else:
            print('\n  (sin corridas activas aun — el launcher puede estar iniciando)')

        # ── 3. Pesos multiobjetivo ────────────────────────────────────
        print('\n  PESOS MULTIOBJETIVO  '
              'r_mix_i = 0.30 × r_local_i  +  0.70 × mean(r₁…r₁₇)')
        print(f'  {"Escenario":<12}  {"OE1 flex":>10}  {"OE2 CO2":>9}  {"OE3 cost":>10}')
        print('  ' + '-' * 46)
        for esc, w in _SCENARIO_WEIGHTS.items():
            print(f'  {esc:<12}  {w["OE1 flex"]:>10.2f}  {w["OE2 CO2"]:>9.2f}  {w["OE3 cost"]:>10.2f}')

        # ── 4. Ganancias de jobs completados ──────────────────────────
        gains_rows = {}
        for algo in _ALGOS:
            for esc in _SCENS:
                # Carpeta canonica del launcher = MAYUSCULA (HAPPO/E1); respaldo minuscula/legacy.
                # Identico para los 4 MADRL (sin preferencia) y robusto en Colab (case-sensitive).
                jdir = next(
                    (c for c in (out / algo.upper() / f'{esc}' / 'data',
                                 out / algo.lower() / f'{esc}' / 'data',
                                 out / algo.upper() / f'{esc}_seed_0' / 'data',
                                 out / algo.lower() / f'{esc}_seed_0' / 'data')
                     if c.exists()),
                    out / algo.upper() / f'{esc}' / 'data',
                )
                for fname in ('training_summary.json', 'results.json'):
                    jf = jdir / fname
                    if not jf.exists():
                        continue
                    try:
                        td = _json.loads(jf.read_text())
                        # Buscar claves de ganancia/improvement
                        gain_keys = [k for k in td
                                     if any(x in k.lower()
                                            for x in ('gain', 'improvement', 'delta',
                                                       'reduction', 'saving'))]
                        if gain_keys:
                            gains_rows[f'{algo}/{esc}'] = {
                                k: td[k] for k in gain_keys[:5]
                            }
                            break
                    except Exception:
                        pass

        if gains_rows:
            print('\n  GANANCIAS vs BASELINE (corridas completadas):')
            for key, gd in list(gains_rows.items())[:9]:
                parts = []
                for k, v in gd.items():
                    short = (k.replace('_gain', '').replace('_improvement', '')
                              .replace('_reduction', '').replace('_saving', ''))
                    try:
                        parts.append(f'{short}={_fmt_pct(float(v))}')
                    except Exception:
                        parts.append(f'{short}={v}')
                print(f'  {key:<14}  ' + '  '.join(parts))

        # ── 5. Tabla 4x3 (artefactos en disco, no solo status.json) ───
        if _resume_map:
            print('\n  TABLA DE CORRIDAS (4 algoritmos x 3 escenarios):')
            print(f'  {"ALGO":<8}  {"E1":^14}  {"E2":^14}  {"E3":^14}')
            print('  ' + '-' * 56)
            for algo in _ALGOS:
                cells = []
                for esc in _SCENS:
                    row = _resume_map.get((algo.lower(), esc))
                    match = [j for j in all_jobs
                             if j.get('name', '').upper() == algo
                             and j.get('scenario', '').upper() == esc]
                    if row and row.get('action') == 'skip':
                        cells.append(f'OK {_n_ep}/{_n_ep}ep')
                    elif row and _resumable_action(row):
                        _lk = (algo.lower(), esc)
                        _jlp = lp_cache.get(_lk) or _lp_key.get(_lk)
                        _ce = int(row.get('completed_episodes') or 0)
                        if match and _job_running(match[0]):
                            ep_str = f'ep{_ce}' if not _jlp else ''
                            if _jlp:
                                _, _, _ep_show, _ = _ep_progress(_jlp, _n_ep, _ep_steps)
                                ep_str = f'ep{_ep_show}'
                            cells.append(f'activo {ep_str:>4}')
                        elif str(row.get('action') or '').lower() == 'happo_salvage_kpi':
                            cells.append(f'cola ep{_n_ep:>2}')
                        else:
                            ep_str = f'ep{_ce + 1}' if _ce < _n_ep else f'ep{_n_ep}'
                            cells.append(f'reanuda {ep_str:>4}')
                    elif match and match[0].get('skipped'):
                        cells.append('  [SKIP]   ')
                    elif match and match[0].get('exit_code') not in (None, 0) and match[0].get('completed_at'):
                        cells.append('  [FALLO]  ')
                    elif row:
                        cells.append(' [pendiente]')
                    else:
                        cells.append('     —     ')
                print(f'  {algo:<8}  {cells[0]:^14}  {cells[1]:^14}  {cells[2]:^14}')

        print(_SEP + '\n')
        sys.stdout.flush()

    # ── arrancar proceso ──────────────────────────────────────────────────────
    verify_two_phase_protocol()
    if not globals().get('_created_new_run'):
        _scripts72 = _P(_repo) / 'CityLearn' / 'scripts'
        if str(_scripts72) not in sys.path:
            sys.path.insert(0, str(_scripts72))
        import importlib as _il72
        _cm72 = _il72.import_module('citylearn_v3_training_common')
        _out72 = _P(str(globals().get('OUTPUT_ROOT', '') or resolve_output_root_or_latest()))
        if not _out72.is_dir():
            raise RuntimeError(f'OUTPUT_ROOT no existe: {_out72}')
        _pre72 = _cm72.build_jobs_resume_report(
            _out72,
            target_episodes=int(globals().get('N_EPISODES', globals().get('EPISODES', 50))),
            episode_time_steps=int(globals().get('EPISODE_STEPS', 8760)),
            happo_rollout_threads=int(globals().get('HAPPO_ROLLOUT_THREADS', 0)) or None,
            seed=int(globals().get('SEED', 0)),
        )
        _cm72.assert_canonical_colab_skip_plan(_pre72, output_root=_out72)
    # Omite el dry-run interno si 7.1 ya lo valido para esta misma config (no duplicar).
    if 'dry_run_already_validated' in globals() and dry_run_already_validated():
        print('[preflight] dry-run ya validado en 7.1 para esta config — se omite el dry-run interno.')
    else:
        _preflight = launcher_base_args() + ['--dry-run', '--skip-completed']
        _pf = subprocess.run(_preflight, cwd=_repo, capture_output=True, text=True)
        if _pf.returncode != 0:
            print(_pf.stdout)
            print(_pf.stderr)
            raise RuntimeError(f'Preflight dry-run fallo exit={_pf.returncode}')
        if 'protocol=two_phase_happo_masac_v3' not in _pf.stdout:
            raise RuntimeError(
                'Launcher sin protocol=two_phase_happo_masac_v3 — scripts legacy en Colab. '
                'Runtime restart + celdas 1.2 -> 1.5 -> 2.1 -> 6.1 -> 7.1.'
            )
        _st_path = _P(globals().get('OUTPUT_ROOT', '')) / 'official_full_status.json'
        if _st_path.exists():
            _st = _json.loads(_st_path.read_text(encoding='utf-8'))
            import importlib.util as _ilu
            _gp = Path(_repo) / 'CityLearn/scripts/colab_protocol_guard.py'
            _gs = _ilu.spec_from_file_location('_pg_launch', _gp)
            if _gs is None or _gs.loader is None:
                raise ImportError(f'No se pudo cargar colab_protocol_guard desde {_gp}')
            _pgl = _ilu.module_from_spec(_gs)
            _gs.loader.exec_module(_pgl)
            _pgl.validate_dry_run_status(_st)
        print('[preflight] dry-run OK — two_phase_happo_masac_v3')
    train_cmd = launcher_base_args() + ['--skip-completed']
    print('\n' + _SEP)
    print('  Lanzando entrenamiento...')
    print('  protocol: two_phase_happo_masac_v3 | execution: two_phase_happo_masac')
    print('  ' + ' '.join(str(c) for c in train_cmd))
    print(_SEP + '\n')
    sys.stdout.flush()

    proc = subprocess.Popen(
        train_cmd,
        cwd=_repo,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    # Hilo que imprime cada linea del launcher en tiempo real
    def _stream(p):
        try:
            for line in p.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
        except Exception:
            pass

    _th.Thread(target=_stream, args=(proc,), daemon=True).start()

    # ── stop gracioso ─────────────────────────────────────────────────────────
    def _graceful_stop(p):
        if p.poll() is not None:
            return
        print('\n[7.2] SIGINT al launcher (checkpoints se guardan)...')
        try:
            p.send_signal(_signal.SIGINT)
        except Exception:
            pass
        try:
            p.wait(timeout=40)
        except subprocess.TimeoutExpired:
            p.kill()  # SIGKILL fallback after graceful SIGINT timeout
            p.wait(timeout=10)

    # ── bucle de monitoreo ────────────────────────────────────────────────────
    _last_panel = time.monotonic()
    try:
        while proc.poll() is None:
            _now = time.monotonic()
            if _now - _last_panel >= _MON_INTERVAL:
                _root = resolve_output_root_or_latest()
                if _root and _P(_root).exists():
                    _print_panel(_root)
                _last_panel = _now
            time.sleep(_POLL_SLEEP)
    except KeyboardInterrupt:
        print('\n[7.2] Interrumpido.')
        _graceful_stop(proc)
        print('[7.2] Para reanudar: Interrupt → git pull (celda 1.2) → run ONLY celda 7.2.')
        raise

    time.sleep(1)   # dar tiempo al hilo de streaming para vaciar el buffer
    _exit = int(proc.returncode or 0)

    # Panel final
    _root = resolve_output_root_or_latest()
    if _root and _P(_root).exists():
        _print_panel(_root)

    if _exit == 0:
        print(_SEP)
        print('  ENTRENAMIENTO COMPLETADO')
        print(_SEP + '\n')
        _root_done = resolve_output_root_or_latest()
        _auto_post = bool(globals().get('AUTO_RUN_POST_TRAINING', True))
        _artifacts_ok = False
        if _root_done and 'verify_training_artifacts_complete' in globals():
            _verdict = verify_training_artifacts_complete(_root_done)
            print_training_artifacts_verdict(_verdict)
            _artifacts_ok = bool(_verdict.get('ok'))
        elif _root_done:
            print('[7.2] verify_training_artifacts_complete no disponible — re-ejecuta celda 7.0.')
        if _auto_post and _artifacts_ok and 'run_post_training_notebook_cells' in globals():
            print('\n[7.2] Artefactos OK — ejecutando pipeline post-entrenamiento (7.3→...)')
            try:
                run_post_training_notebook_cells(
                    include_section_8=bool(globals().get('POST_TRAINING_INCLUDE_SECTION_8', True)),
                    include_section_9=bool(globals().get('POST_TRAINING_INCLUDE_SECTION_9', True)),
                )
                print('\n[7.2] Pipeline post-entrenamiento finalizado. Kernel activo.')
            except Exception as _post_exc:
                print(f'\n[7.2] Post-proceso automatico fallo: {_post_exc}')
                print('  Ejecuta manualmente celdas 7.3 en adelante.')
        elif _auto_post and not _artifacts_ok:
            print('\n[7.2] Artefactos incompletos — no se ejecuta pipeline automatico.')
            print('  Corrige y ejecuta 7.4+ manualmente, o re-lanza 7.2 con --skip-completed.')
        elif not _auto_post:
            print('\n[7.2] AUTO_RUN_POST_TRAINING=False — ejecuta 7.3+ manualmente.')
        else:
            print('  Procede con seccion 7.3 — Monitor y auditoria.')
        _disconnect_colab('entrenamiento completado', delay_s=30)
    else:
        # Diagnostico de fallo
        print(f'\n[7.2] FALLO (exit={_exit})\n')
        if _root:
            _sp = _P(_root) / 'official_full_status.json'
            if _sp.exists():
                try:
                    _s = _json.loads(_sp.read_text())
                    for _j in _s.get('jobs', []):
                        if _j.get('exit_code') not in (None, 0) and not _j.get('skipped'):
                            print(f'  FAIL: {_j.get("name","?").upper()}/'
                                  f'{_j.get("scenario","?")}  '
                                  f'attempt={_j.get("attempt",0)}')
                except Exception:
                    pass
            for _ep in sorted(_P(_root).glob('logs/*.stderr.log')):
                if _ep.stat().st_size == 0:
                    continue
                _et = _ep.read_text(errors='replace')
                print(f'\n  === {_ep.name} (ultimas 25 lineas) ===')
                print('  ' + '\n  '.join(_et.strip().splitlines()[-25:]))
        print('\n  RELAUNCH: Interrupt → git pull (celda 1.2) → run ONLY celda 7.2.')
        _disconnect_colab(f'fallo exit={_exit} — reanuda con RESUME_OUTPUT_ROOT', delay_s=45)
        raise RuntimeError(f'Entrenamiento fallo exit={_exit}')


