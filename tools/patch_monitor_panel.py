"""Patch 7.2 monitor panel in madrl_citylearn_v3_tutorial.ipynb."""
from __future__ import annotations

import json
import sys
from pathlib import Path

NB = Path(__file__).resolve().parents[1] / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb"

OLD_JOB_DONE_BLOCK = """    def _job_done(j):
        if j.get('planned_only'):
            return False
        if j.get('skipped'):
            return True
        return j.get('exit_code') == 0

    def _infer_phase(all_jobs):"""

NEW_JOB_DONE_BLOCK = """    def _job_done(j):
        if j.get('planned_only'):
            return False
        if j.get('skipped'):
            return True
        return j.get('exit_code') == 0

    def _job_running(j):
        return (j.get('completed_at') is None
                and not j.get('planned_only')
                and not j.get('skipped'))

    def _infer_phase(all_jobs):"""

OLD_ETA = """    def _eta_minutes(lp, algo, n_ep, ep_steps):
        if not lp:
            return n_ep * _EST_BY_ALGO.get(algo, 13)
        ep = int(lp.get('episode', 0))
        ep_step = int(lp.get('episode_step', 0))
        rem_steps = max(0, (n_ep - ep - 1) * ep_steps + (ep_steps - ep_step))
        fps = lp.get('fps')
        try:
            fps = float(fps)
        except (TypeError, ValueError):
            fps = 0.0
        if fps > 0.1:
            return rem_steps / fps / 60.0
        return max(0, n_ep - ep) * _EST_BY_ALGO.get(algo, 13)
"""

NEW_ETA = """    _LP_STALE_SEC = int(globals().get('LIVE_PROGRESS_STALE_SEC', 600))

    def _ep_progress(lp, n_ep, ep_steps):
        \"\"\"Grounded episode index + step for ETA and display (handles boundary writes).\"\"\"
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
"""

OLD_LAG = """    def _lag_seconds(ts_str):
        if not ts_str:
            return None
        try:
            ts = _DT.fromisoformat(ts_str.replace('Z', '+00:00'))
            return (_utc_now() - ts).total_seconds()
        except Exception:
            return None

    # ── panel principal de estado ─────────────────────────────────────────────"""

NEW_LAG = """    def _lag_seconds(ts_str):
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

    # ── panel principal de estado ─────────────────────────────────────────────"""

OLD_ACTIVE_LP = """        # ── 2. Live progress por corrida activa ───────────────────────
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

        if active_lp and all_jobs:"""

NEW_ACTIVE_LP = """        # ── 2. Live progress por corrida activa (desde jobs running en status) ──
        active_lp, lp_cache = _collect_running_progress(out, all_jobs) if all_jobs else ([], {})
        _lp_key = dict(lp_cache)

        if all_jobs:"""

OLD_ETA_KEY = """                _lp_key = {}
                for lp in active_lp:
                    _lp_key[(str(lp.get('algorithm', '')).lower(), str(lp.get('scenario', '')).upper())] = lp
                if _dyn_bf:"""

NEW_ETA_KEY = """                if _dyn_bf:"""

OLD_HDR = """            hdr = f'  {\"ALGO/ESC\":<10} {\"Episodio\":>10}  {\"ep_step\":>12}  {\"FPS\":>6}  {\"r_mix_mean\":>11}  {\"Lag\":>5}'
            print(hdr)"""

NEW_HDR = """            hdr = f'  {\"ALGO/ESC\":<10} {\"Episodio\":>10}  {\"ep_step\":>12}  {\"FPS\":>6}  {\"r_mix_mean\":>11}  {\"Lag\":>6}  Estado'
            print(hdr)"""

OLD_DISPLAY_LOOP = """            for lp in active_lp:
                algo  = lp.get('algorithm', '?').upper()
                esc   = lp.get('scenario', '?').upper()
                ep    = int(lp.get('episode', 0)) + 1
                ep_step = int(lp.get('episode_step', 0))
                ep_steps = int(lp.get('episode_time_steps', _ep_steps))
                try:
                    fps = float(lp.get('fps') or 0.0)
                except (TypeError, ValueError):
                    fps = 0.0
                ret = lp.get('mean_return', lp.get('episode_reward_mean_cumulative'))
                lag = lp.get('_lag', 0)
                bar_s = _bar((ep - 1) + ep_step / max(ep_steps, 1), _n_ep, 16)
                ret_s = f'{float(ret):+.4f}' if ret is not None else '    —   '
                lag_s = f'{lag:.0f}s'
                fps_s = f'{fps:.1f}' if fps > 0 else '  —  '
                print(f'  {algo}/{esc:<5}  [{bar_s}] {ep:>3}/{_n_ep}  {ep_step:>5}/{ep_steps:<5}  '
                      f'{fps_s:>6}  {ret_s:>11}  {lag_s:>5}')
"""

NEW_DISPLAY_LOOP = """            for lp in active_lp:
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
                bar_s = _bar((ep - 1) + ep_step / max(ep_steps, 1), _n_ep, 16)
                ret_s = f'{float(ret):+.4f}' if ret is not None else '    —   '
                fps_s = f'{fps:.1f}' if fps > 0 else '  —  '
                stage = str(lp.get('live_status') or '?')
                if lp.get('backend_training_active'):
                    stage += '+GPU'
                print(f'  {algo}/{esc:<5}  [{bar_s}] {ep:>3}/{_n_ep}  {ep_step:>5}/{ep_steps:<5}  '
                      f'{fps_s:>6}  {ret_s:>11}  {lag_s:>6}  {stage}')
"""

OLD_TABLA_EP = """                            ep_str = ''
                            for lp in active_lp:
                                if (lp.get('algorithm', '').upper() == algo
                                        and lp.get('scenario', '').upper() == esc):
                                    ep_str = f'ep{int(lp.get(\"episode\", 0)) + 1}'
                            cells.append(f'activo {ep_str:>4}')"""

NEW_TABLA_EP = """                            _lk = (algo.lower(), esc)
                            _jlp = lp_cache.get(_lk) or _lp_key.get(_lk)
                            ep_str = ''
                            if _jlp:
                                _, _, _ep_show, _ = _ep_progress(_jlp, _n_ep, _ep_steps)
                                ep_str = f'ep{_ep_show}'
                            cells.append(f'activo {ep_str:>4}')"""

REPLACEMENTS = [
    (OLD_JOB_DONE_BLOCK, NEW_JOB_DONE_BLOCK),
    (OLD_ETA, NEW_ETA),
    (OLD_LAG, NEW_LAG),
    (OLD_ACTIVE_LP, NEW_ACTIVE_LP),
    (OLD_ETA_KEY, NEW_ETA_KEY),
    (OLD_HDR, NEW_HDR),
    (OLD_DISPLAY_LOOP, NEW_DISPLAY_LOOP),
    (OLD_TABLA_EP, NEW_TABLA_EP),
]


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
    for old, new in REPLACEMENTS:
        if old not in src:
            print(f"MISSING block: {old[:60]}...", file=sys.stderr)
            return 1
        src = src.replace(old, new, 1)

    if "return ep, ep_step, ep_show, ep_step_show" not in src:
        print("_ep_progress fix missing", file=sys.stderr)
        return 1

    nb["cells"][cell_idx]["source"] = [line + "\n" for line in src.splitlines(keepends=False)]
    if src.endswith("\n"):
        nb["cells"][cell_idx]["source"][-1] += "\n"
    NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Patched cell {cell_idx} in {NB}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
