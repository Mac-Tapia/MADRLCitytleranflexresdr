"""Ground 7.2 monitor panel in build_jobs_resume_report (same truth as launcher)."""
from __future__ import annotations

import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb"

OLD_COLLECT_END = """        return active_lp, lp_cache

    # ── panel principal de estado ─────────────────────────────────────────────
    def _print_panel(output_root):"""

NEW_COLLECT_END = """        return active_lp, lp_cache

    def _load_resume_report(out):
        \"\"\"Misma fuente que 2.1b / 7.1 / --skip-completed (artefactos en disco).\"\"\"
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
            happo_rollout_threads=globals().get('HAPPO_ROLLOUT_THREADS'),
        )

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
    def _print_panel(output_root):"""

OLD_GLOBAL = """        # ── 1. Estado global de los 12 jobs ───────────────────────────
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
                _gp = float(done)
                for _lpf in out.rglob('live_progress.json'):
                    try:
                        _l = _json.loads(_lpf.read_text())
                    except Exception:
                        continue
                    _nm = str(_l.get('algorithm', '')).lower()
                    _sc = str(_l.get('scenario', '')).upper()
                    _mj = [j for j in all_jobs
                           if str(j.get('name', '')).lower() == _nm
                           and str(j.get('scenario', '')).upper() == _sc]
                    if _mj and _job_done(_mj[0]):
                        continue
                    _es = int(_l.get('episode_time_steps', _ep_steps) or _ep_steps)
                    _gp += min(1.0, (int(_l.get('episode', 0))
                                     + int(_l.get('episode_step', 0)) / max(_es, 1)) / max(_n_ep, 1))
                bar12 = _bar(_gp, total, 24)
                print(f'\\n  PROGRESO GLOBAL  [{bar12}]  '
                      f'{done}/{total} OK  {run} activas  {fail} fallo  {skip} omitidas')
                print(f'  status = {st.get(\"status\", \"?\")}')
                _par = st.get('parallelization') or {}
                if _par:
                    print(f'  paralelismo: {_par.get(\"strategy\", \"?\")}')
                _dyn_bf = bool((_par or {}).get('dynamic_backfill', globals().get('DYNAMIC_BACKFILL', True)))
                _phase, _phase_algos = _infer_phase(all_jobs)
                _phase_jobs = [j for j in all_jobs if j.get('name') in _phase_algos] if _phase_algos else []
                _phase_run = sum(1 for j in _phase_jobs
                               if j.get('completed_at') is None and not j.get('planned_only')
                               and not j.get('skipped'))
                _p1_done = sum(1 for j in all_jobs if j.get('name') in ('happo', 'masac') and _job_done(j))
                _p2_run = sum(1 for j in all_jobs if j.get('name') in ('matd3', 'maac')
                              and j.get('completed_at') is None and not j.get('planned_only')
                              and not j.get('skipped'))
                if _phase == 0:
                    print('  progreso     : completado (12/12)')
                elif _dyn_bf:
                    print(f'  backfill dinámico | fase1 HAPPO+MASAC {_p1_done}/6 ok | '
                          f'fase2 MATD3+MAAC {_p2_run} activos | {run} activos total (cap 6)')
                elif _phase == 1:
                    print(f'  fase 1/2 (HAPPO+MASAC×3) | {_phase_run} activos en fase | {run} activos total')
                else:
                    print(f'  fase 2/2 (MATD3+MAAC×3) | {_phase_run} activos en fase | {run} activos total')
            except Exception as e:
                print(f'  [status] error leyendo official_full_status.json: {e}')

        # ── 2. Live progress por corrida activa (desde jobs running en status) ──
        active_lp, lp_cache = _collect_running_progress(out, all_jobs) if all_jobs else ([], {})
        _lp_key = dict(lp_cache)

        if all_jobs:
            try:
                _dyn_bf = bool(globals().get('DYNAMIC_BACKFILL', True))
                _cap = 6
                if _dyn_bf:
                    # Backfill dinámico: makespan sobre TODOS los jobs no terminados (cap 6),
                    # porque la fase 2 se solapa con la fase 1 al liberarse cada slot.
                    _rem = []
                    _run_rem = []
                    for j in all_jobs:
                        if _job_done(j):
                            continue
                        _a = str(j.get('name', '')).lower()
                        _s = str(j.get('scenario', '')).upper()
                        _m = _eta_minutes(_lp_key.get((_a, _s)), _a, _n_ep, _ep_steps)
                        _rem.append(_m)
                        if j.get('completed_at') is None and not j.get('planned_only') and not j.get('skipped'):
                            _run_rem.append(_m)
                    if _rem:
                        _eta_run = max(_run_rem) if _run_rem else 0.0
                        _eta_total = max(max(_rem), sum(_rem) / max(_cap, 1))
                        print(f'  ETA activos: ~{_eta_run/60:.1f} h | '
                              f'ETA total restante (makespan cap{_cap}): ~{_eta_total/60:.1f} h')
                else:
                    _phase, _phase_algos = _infer_phase(all_jobs)
                    _eta_phase = 0.0
                    if _phase_algos:
                        _etas = []
                        for lp in active_lp:
                            if str(lp.get('algorithm', '')).lower() in _phase_algos:
                                _etas.append(_eta_minutes(lp, str(lp.get('algorithm', '')).lower(), _n_ep, _ep_steps))
                        if _etas:
                            _eta_phase = max(_etas)
                    _eta_total = _eta_phase + (_n_ep * _EST_PHASE if _phase == 1 else 0.0)
                    if _phase:
                        print(f'  ETA fase {_phase}: ~{_eta_phase/60:.1f} h | ETA total restante: ~{_eta_total/60:.1f} h')
            except Exception:
                pass"""

NEW_GLOBAL = """        # ── 1. Estado global (artefactos en disco = misma verdad que launcher) ──
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
        bar12 = _bar(_gp, total, 24)
        print(f'\\n  PROGRESO GLOBAL  [{bar12}]  '
              f'{done_art}/{total} OK (artefactos)  {run} activas  {fail} fallo  {pending_n} pendientes')
        if st:
            print(f'  status = {st.get(\"status\", \"?\")}')
            _par = st.get('parallelization') or {}
            if _par:
                print(f'  paralelismo: {_par.get(\"strategy\", \"?\")}')
        _dyn_bf = bool((st.get('parallelization') or {}).get('dynamic_backfill', globals().get('DYNAMIC_BACKFILL', True)))
        _p1_done = sum(1 for a in ('happo', 'masac') for s in _SCENS if _artifact_complete(_resume_map, a, s))
        _p2_done = sum(1 for a in ('matd3', 'maac') for s in _SCENS if _artifact_complete(_resume_map, a, s))
        _p2_run = sum(1 for a in ('matd3', 'maac') for s in _SCENS
                      if not _artifact_complete(_resume_map, a, s)
                      and (_resume_map.get((a, s)) or {}).get('action') == 'resume')
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
                if row.get('action') == 'resume' and _lp:
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
            pass"""

OLD_TABLA_BLOCK = """        # ── 5. Tabla 4x3 de los 12 jobs ──────────────────────────────
        if all_jobs:
            print('\\n  TABLA DE CORRIDAS (4 algoritmos x 3 escenarios):')
            print(f'  {\"ALGO\":<8}  {\"E1\":^14}  {\"E2\":^14}  {\"E3\":^14}')
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
                            _lk = (algo.lower(), esc)
                            _jlp = lp_cache.get(_lk) or _lp_key.get(_lk)
                            ep_str = ''
                            if _jlp:
                                _, _, _ep_show, _ = _ep_progress(_jlp, _n_ep, _ep_steps)
                                ep_str = f'ep{_ep_show}'
                            cells.append(f'activo {ep_str:>4}')
                        else:
                            cells.append('  [FALLO]  ')
                print(f'  {algo:<8}  {cells[0]:^14}  {cells[1]:^14}  {cells[2]:^14}')"""

NEW_TABLA_BLOCK = """        # ── 5. Tabla 4x3 (artefactos en disco, no solo status.json) ───
        if _resume_map:
            print('\\n  TABLA DE CORRIDAS (4 algoritmos x 3 escenarios):')
            print(f'  {\"ALGO\":<8}  {\"E1\":^14}  {\"E2\":^14}  {\"E3\":^14}')
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
                    elif row and row.get('action') == 'resume':
                        _lk = (algo.lower(), esc)
                        _jlp = lp_cache.get(_lk) or _lp_key.get(_lk)
                        _ce = int(row.get('completed_episodes') or 0)
                        ep_str = f'ep{_ce}' if not _jlp else ''
                        if _jlp:
                            _, _, _ep_show, _ = _ep_progress(_jlp, _n_ep, _ep_steps)
                            ep_str = f'ep{_ep_show}'
                        cells.append(f'activo {ep_str:>4}')
                    elif match and match[0].get('skipped'):
                        cells.append('  [SKIP]   ')
                    elif match and match[0].get('exit_code') not in (None, 0) and match[0].get('completed_at'):
                        cells.append('  [FALLO]  ')
                    elif row:
                        cells.append(' [pendiente]')
                    else:
                        cells.append('     —     ')
                print(f'  {algo:<8}  {cells[0]:^14}  {cells[1]:^14}  {cells[2]:^14}')"""


def main() -> int:
    nb = json.loads(NB.read_text(encoding="utf-8"))
    cell_idx = None
    for i, cell in enumerate(nb["cells"]):
        src = "".join(cell.get("source", []))
        if "# ── 7.2  Lanzar entrenamiento" in src:
            cell_idx = i
            break
    if cell_idx is None:
        print("7.2 cell not found", file=sys.stderr)
        return 1

    src = "".join(nb["cells"][cell_idx]["source"])
    for old, new, label in [
        (OLD_COLLECT_END, NEW_COLLECT_END, "collect_end"),
        (OLD_GLOBAL, NEW_GLOBAL, "global"),
        (OLD_TABLA_BLOCK, NEW_TABLA_BLOCK, "tabla"),
    ]:
        if old not in src:
            print(f"MISSING: {label}", file=sys.stderr)
            return 1
        src = src.replace(old, new, 1)

    nb["cells"][cell_idx]["source"] = [line + "\n" for line in src.splitlines(keepends=False)]
    if src.endswith("\n"):
        nb["cells"][cell_idx]["source"][-1] += "\n"
    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Patched artifact truth in cell {cell_idx}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
