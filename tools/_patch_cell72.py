import json
import pathlib
import sys

sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = pathlib.Path(
    r'd:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb'
)
nb = json.loads(NB_PATH.read_bytes().decode('utf-8-sig'))

NEW_SOURCE = r"""# ── 7.2  Lanzar entrenamiento + monitor en paralelo ─────────────────────────
# Lanza el launcher con Popen (no bloqueante) y hace dos cosas en paralelo:
#   1. Un hilo de streaming imprime CADA LINEA del launcher en tiempo real.
#   2. Cada 30 s imprime un panel de estado rico: progreso bar, pesos OE1/OE2/OE3,
#      retorno por escenario, ganancias de jobs completados y tabla 4x3 de corridas.
LAUNCH_FULL_TRAINING = True

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
    _python  = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
    _MON_INTERVAL = 30   # segundos entre paneles de estado
    _POLL_SLEEP   = 4    # segundos entre polls del proceso

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
    def _bar(n, total, width=18):
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

    # ── panel principal de estado ─────────────────────────────────────────────
    def _print_panel(output_root):
        out = _P(output_root)
        now_str = _utc_now().strftime('%Y-%m-%d %H:%M:%S UTC')
        print('\n' + _SEP)
        print(f'  MADRL CityLearn v3  |  A100-SXM4-80GB 80GiB + 167GiB RAM  |  {now_str}')
        print(f'  Run: {out.name}')
        print(_SEP)

        # ── 1. Estado global de los 12 jobs ───────────────────────────
        status_file = out / 'official_full_status.json'
        all_jobs = []
        if status_file.exists():
            try:
                st = _json.loads(status_file.read_text())
                all_jobs = st.get('jobs', [])
                done  = sum(1 for j in all_jobs if j.get('exit_code') == 0)
                skip  = sum(1 for j in all_jobs if j.get('skipped'))
                fail  = sum(1 for j in all_jobs if j.get('exit_code') not in (None, 0)
                            and not j.get('skipped'))
                run   = sum(1 for j in all_jobs if j.get('completed_at') is None
                            and not j.get('planned_only') and not j.get('skipped'))
                total = 12
                bar12 = _bar(done, total, 24)
                print(f'\n  PROGRESO GLOBAL  [{bar12}]  '
                      f'{done}/{total} OK  {run} activas  {fail} fallo  {skip} omitidas')
                print(f'  status = {st.get("status", "?")}')
            except Exception as e:
                print(f'  [status] error leyendo official_full_status.json: {e}')

        # ── 2. Live progress por corrida activa ───────────────────────
        lp_files = sorted(out.rglob('live_progress.json'))
        active_lp = []
        for lpf in lp_files:
            try:
                lp = _json.loads(lpf.read_text())
                lag = _lag_seconds(lp.get('live_status_updated_at', ''))
                if lag is not None and lag < 180:
                    lp['_lag'] = lag
                    active_lp.append(lp)
            except Exception:
                pass

        if active_lp:
            print(f'\n  CORRIDAS ACTIVAS  ({len(active_lp)} en paralelo)')
            hdr = f'  {"ALGO/ESC":<10} {"Episodio":>12}  {"Paso":>8}  {"FPS":>5}  {"r_mix_mean":>11}  {"Lag":>5}'
            print(hdr)
            print('  ' + _SEP_THIN[:76])
            for lp in active_lp:
                algo  = lp.get('algorithm', '?').upper()
                esc   = lp.get('scenario', '?').upper()
                ep    = int(lp.get('episode', 0))
                step  = int(lp.get('global_step', 0))
                fps   = float(lp.get('fps', 0.0))
                ret   = lp.get('mean_return', None)
                lag   = lp.get('_lag', 0)
                bar_s = _bar(ep, globals().get('N_EPISODES', 50), 16)
                ret_s = f'{ret:+.4f}' if ret is not None else '    —   '
                lag_s = f'{lag:.0f}s'
                print(f'  {algo}/{esc:<5}  [{bar_s}] {ep:>3}/{globals().get("N_EPISODES", 50)}  {step:>8}  '
                      f'{fps:>4.1f}  {ret_s:>11}  {lag_s:>5}')
        else:
            print('\n  (sin corridas activas aun — el launcher puede estar iniciando)')

        # ── 3. Pesos multiobjetivo ────────────────────────────────────
        print(f'\n  PESOS MULTIOBJETIVO  '
              f'r_mix_i = 0.30 × r_local_i  +  0.70 × mean(r₁…r₁₇)')
        print(f'  {"Escenario":<12}  {"OE1 flex":>10}  {"OE2 CO2":>9}  {"OE3 cost":>10}')
        print('  ' + '-' * 46)
        for esc, w in _SCENARIO_WEIGHTS.items():
            print(f'  {esc:<12}  {w["OE1 flex"]:>10.2f}  {w["OE2 CO2"]:>9.2f}  {w["OE3 cost"]:>10.2f}')

        # ── 4. Ganancias de jobs completados ──────────────────────────
        gains_rows = {}
        for algo in _ALGOS:
            for esc in _SCENS:
                jdir = out / algo.lower() / f'{esc}_seed_0' / 'data'
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
            print(f'\n  GANANCIAS vs BASELINE (corridas completadas):')
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

        # ── 5. Tabla 4x3 de los 12 jobs ──────────────────────────────
        if all_jobs:
            print(f'\n  TABLA DE CORRIDAS (4 algoritmos x 3 escenarios):')
            print(f'  {"ALGO":<8}  {"E1":^14}  {"E2":^14}  {"E3":^14}')
            print('  ' + '-' * 56)
            for algo in _ALGOS:
                cells = []
                for esc in _SCENS:
                    match = [j for j in all_jobs
                             if j.get('name', '').upper() == algo
                             and j.get('scenario', '').upper() == esc]
                    if not match:
                        cells.append('     —     ')
                    else:
                        j = match[0]
                        if j.get('planned_only'):
                            cells.append(' [pendiente]')
                        elif j.get('skipped'):
                            cells.append('  [SKIP]   ')
                        elif j.get('exit_code') == 0:
                            dur = j.get('duration_minutes', 0)
                            cells.append(f'OK  {dur:>5.0f}min')
                        elif j.get('completed_at') is None:
                            ep_str = ''
                            for lp in active_lp:
                                if (lp.get('algorithm', '').upper() == algo
                                        and lp.get('scenario', '').upper() == esc):
                                    ep_str = f'ep{lp.get("episode", 0)}'
                            cells.append(f'activo {ep_str:>4}')
                        else:
                            cells.append('  [FALLO]  ')
                print(f'  {algo:<8}  {cells[0]:^14}  {cells[1]:^14}  {cells[2]:^14}')

        print(_SEP + '\n')
        sys.stdout.flush()

    # ── arrancar proceso ──────────────────────────────────────────────────────
    train_cmd = launcher_base_args() + ['--skip-completed']
    print('\n' + _SEP)
    print('  Lanzando entrenamiento...')
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
            p.kill()
            p.wait(timeout=10)

    # ── bucle de monitoreo ────────────────────────────────────────────────────
    _last_panel = 0.0
    try:
        while proc.poll() is None:
            _now = time.time()
            if _now - _last_panel >= _MON_INTERVAL:
                _ref = _P(_repo) / 'outputs' / 'latest_colab_output_root.txt'
                _root = globals().get('OUTPUT_ROOT', '') or (
                    _ref.read_text(encoding='utf-8').strip()
                    if _ref.exists() else ''
                )
                if _root and _P(_root).exists():
                    _print_panel(_root)
                _last_panel = _now
            time.sleep(_POLL_SLEEP)
    except KeyboardInterrupt:
        print('\n[7.2] Interrumpido.')
        _graceful_stop(proc)
        print('[7.2] Para reanudar: define RESUME_OUTPUT_ROOT en celda 2.1 y re-ejecuta 7.2.')
        raise

    time.sleep(1)   # dar tiempo al hilo de streaming para vaciar el buffer
    _exit = int(proc.returncode or 0)

    # Panel final
    _ref = _P(_repo) / 'outputs' / 'latest_colab_output_root.txt'
    _root = globals().get('OUTPUT_ROOT', '') or (
        _ref.read_text(encoding='utf-8').strip() if _ref.exists() else ''
    )
    if _root and _P(_root).exists():
        _print_panel(_root)

    if _exit == 0:
        print(_SEP)
        print('  ENTRENAMIENTO COMPLETADO')
        print('  Procede con seccion 8 — Analisis estadistico y resultados.')
        print(_SEP + '\n')
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
        print(f'\n  RELAUNCH: en celda 2.1 establece RESUME_OUTPUT_ROOT = "{_root}"')
        raise RuntimeError(f'Entrenamiento fallo exit={_exit}')
"""

# Convertir a lista de lineas como espera el formato .ipynb
lines = NEW_SOURCE.split('\n')
source_list = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])

nb['cells'][40]['source'] = source_list
NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print("Cell 40 actualizada OK.")
print(f"Lineas: {len(source_list)}")
