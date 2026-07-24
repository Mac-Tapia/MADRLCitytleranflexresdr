# ── 2.1c  Limpieza de runs madrl_v3_* duplicados ───────────────────────────
# Usa plan_madrl_duplicate_run_cleanup() (misma puntuacion por artefactos que 2.1).
import shutil
from pathlib import Path as _Path

DELETE_DUPLICATE_RUNS = globals().get('DELETE_DUPLICATE_RUNS', False)

_parent = _Path(globals().get('BASE_OUTPUT_PARENT', '') or '.')
_active = _Path(globals().get('OUTPUT_ROOT', '')).resolve() if globals().get('OUTPUT_ROOT') else None
_common21c = _common21 if '_common21' in globals() else None
if _common21c is None:
    import importlib
    _common21c = importlib.import_module('citylearn_v3_training_common')

_plan = _common21c.plan_madrl_duplicate_run_cleanup(
    _parent,
    active_output_root=_active,
    target_episodes=int(globals().get('N_EPISODES', globals().get('EPISODES', 50))),
    episode_time_steps=int(globals().get('EPISODE_STEPS', 8760)),
    happo_rollout_threads=int(globals().get('HAPPO_ROLLOUT_THREADS', 0)) or None,
)

if not _plan.get('summaries'):
    print(f'[2.1c] No hay carpetas madrl_v3_* en {_parent} -> nada que limpiar.')
else:
    print(f'[2.1c] Runs madrl_v3_* en {_parent} (score por artefactos MADRL):')
    for s in _plan['summaries']:
        r = _Path(str(s['output_root']))
        _flag = '  <- ACTIVO' if _active and r.resolve() == _active else ''
        _keep = '  [CONSERVAR]' if str(r) in _plan['keep'] else ''
        print(
            f"   {r.name:30s} completos={s.get('completed_jobs', 0)}/12  "
            f"reanudables={s.get('resumable_jobs', 0)}  "
            f"~{float(s.get('progress_pct') or 0.0):.1f}% ep{_flag}{_keep}"
        )
    print(f"\n[2.1c] CONSERVAR: {', '.join(_Path(p).name for p in _plan['keep'])}")
    if not _plan['delete']:
        print('[2.1c] No hay duplicados para borrar.')
    else:
        for p in _plan['delete']:
            r = _Path(p)
            if DELETE_DUPLICATE_RUNS:
                shutil.rmtree(r, ignore_errors=True)
                print(f'[2.1c] BORRADO   : {r.name}')
            else:
                print(f'[2.1c] borraria   : {r.name}')
        if not DELETE_DUPLICATE_RUNS:
            print('\n[2.1c] Pon DELETE_DUPLICATE_RUNS = True y re-ejecuta para borrar.')
