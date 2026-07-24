# ── 2.1b  Verificación de reanudación (ejecutar DESPUÉS de la celda 2.1) ─────
# Fuente unica: notebook_jobs_resume_preview() en citylearn_v3_training_common.
from pathlib import Path

assert 'OUTPUT_ROOT' in globals(), 'Ejecuta la celda 2.1 primero.'
root = Path(str(OUTPUT_ROOT))
assert root.exists(), f'NO EXISTE OUTPUT_ROOT: {OUTPUT_ROOT}'

if globals().get('_created_new_run'):
    print('AVISO: run NUEVO — los 12 jobs empezaran fresh en 7.2 (salvo rescates en 2.2/2.3).\n')
elif not bool(globals().get('RESUME_OUTPUT_ROOT')):
    print('AVISO: sin RESUME_OUTPUT_ROOT — revisa la auditoria de 2.1.\n')

_repo21b = Path(globals().get('CODE_ROOT', globals().get('REPO', '.')))
_common21b = _common21 if '_common21' in globals() else None
if _common21b is None:
    _common21b = __import__('importlib').import_module('citylearn_v3_training_common')

_report = _common21b.notebook_jobs_resume_preview(
    root,
    target_episodes=int(globals().get('N_EPISODES', globals().get('EPISODES', 50))),
    episode_time_steps=int(globals().get('EPISODE_STEPS', 8760)),
    happo_rollout_threads=int(globals().get('HAPPO_ROLLOUT_THREADS', 0)) or None,
    label='2.1b',
    show_footer_hint=True,
    require_canonical_plan=not bool(globals().get('_created_new_run')),
)
