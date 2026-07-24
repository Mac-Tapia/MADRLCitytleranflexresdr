# ── 2.1  Rutas, timestamp y directorio de salida recuperable ────────────────
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ── Deteccion automatica de REPO (Colab o local) ─────────────────────────────
import importlib.util
IN_COLAB = importlib.util.find_spec('google.colab') is not None

if IN_COLAB:
    # Codigo SIEMPRE en /content (hard sync celda 1.2). Outputs van a Drive.
    REPO = '/content/MADRLCitytleranflexresdr'
    CODE_ROOT = REPO
else:
    # Buscar repo root desde el directorio del notebook hacia arriba
    _start = Path(__file__).resolve().parent if '__file__' in dir() else Path.cwd()
    _candidates = [
        _start,
        _start.parent,
        _start.parent.parent,
        Path('d:/MADRLCitytleranflexresdr'),
        Path.home() / 'MADRLCitytleranflexresdr',
    ]
    REPO = next(
        (str(p) for p in _candidates if (p / 'CityLearn').exists()),
        str(_start)
    )
    CODE_ROOT = REPO

PROJECT_NAME = globals().get('PROJECT_NAME', 'MADRLCitytleranflexresdr')
TIMESTAMP    = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_LABEL    = f'madrl_v3_{TIMESTAMP}'
SCHEMA_PATH  = str(Path(REPO) / 'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json')
PYTHON       = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))

GDRIVE_OUTPUT_PARENT = globals().get('GDRIVE_OUTPUT_PARENT', None)
GDRIVE_ROOT          = globals().get('GDRIVE_ROOT', None)
REQUIRE_GOOGLE_DRIVE = globals().get('REQUIRE_GOOGLE_DRIVE', False)

# Outputs en Drive: SOLO ruta canonica (nunca MADRL_CityLearn_v3 legacy)
_DRIVE_OUTPUT_CANDIDATES = []
if IN_COLAB:
    if GDRIVE_OUTPUT_PARENT:
        _DRIVE_OUTPUT_CANDIDATES.append(GDRIVE_OUTPUT_PARENT)
    else:
        _DRIVE_OUTPUT_CANDIDATES.append(
            '/content/drive/MyDrive/MADRLCitytleranflexresdr/outputs'
        )

BASE_OUTPUT_PARENT = None
for _cand in _DRIVE_OUTPUT_CANDIDATES:
    if _cand and Path(_cand).parent.exists():
        BASE_OUTPUT_PARENT = _cand
        break
if BASE_OUTPUT_PARENT is None:
    BASE_OUTPUT_PARENT = str(Path(REPO) / 'outputs')
# 2.1: audita outputs/ en Drive (MyDrive + carpeta compartida); reanuda o run nuevo.
AUTO_RESUME_LATEST = globals().get('AUTO_RESUME_LATEST', True)
FORCE_NEW_RUN      = globals().get('FORCE_NEW_RUN', False)
ENABLE_FUSE_MIRROR = globals().get('ENABLE_FUSE_MIRROR', False)  # opt-in: bootstrap solo si MyDrive vacio

RESUME_OUTPUT_ROOT = globals().get('RESUME_OUTPUT_ROOT', None)

_scripts_dir = str(Path(REPO) / 'CityLearn' / 'scripts')
if _scripts_dir not in sys.path:
    sys.path.insert(0, _scripts_dir)
sys.modules.pop('citylearn_v3_training_common', None)
import importlib
_common21 = importlib.import_module('citylearn_v3_training_common')
_pick = getattr(_common21, 'pick_colab_output_root', None)
if _pick is None:
    raise RuntimeError(
        'citylearn_v3_training_common desactualizado (falta pick_colab_output_root).\n'
        '  Ejecuta celda 1.2 (hard sync CityLearn) y vuelve a 2.1.'
    )

_n_ep_pick = int(globals().get('N_EPISODES', globals().get('EPISODES', 50)))
_ep_steps_pick = int(globals().get('EPISODE_STEPS', 8760))
_happo_roll_pick = int(globals().get('HAPPO_ROLLOUT_THREADS', 0)) or None
_gdrive_root_path = Path(GDRIVE_ROOT) if globals().get('GDRIVE_ROOT') else None
_mount_point_21 = Path(globals().get('DRIVE_MOUNT_POINT', '/content/drive'))

_picked = _pick(
    Path(BASE_OUTPUT_PARENT),
    run_label=RUN_LABEL,
    resume_output_root=RESUME_OUTPUT_ROOT,
    auto_resume_latest=AUTO_RESUME_LATEST,
    force_new_run=FORCE_NEW_RUN,
    target_episodes=_n_ep_pick,
    episode_time_steps=_ep_steps_pick,
    happo_rollout_threads=_happo_roll_pick,
    repo=Path(REPO),
    in_colab=IN_COLAB,
    gdrive_root=_gdrive_root_path,
    mount_point=_mount_point_21 if IN_COLAB else None,
    ensure_shared_run=bool(ENABLE_FUSE_MIRROR),
    skip_fuse_mirror=True,
    print_audit=True,
)
OUTPUT_ROOT = str(_picked['output_root'])
RESUME_OUTPUT_ROOT = _picked.get('resume_output_root')
_resume_reason = str(_picked['resume_reason'])
_created_new_run = bool(_picked.get('created_new_run'))
globals()['_created_new_run'] = _created_new_run
globals()['_MYDRIVE_RESUMED'] = bool(_picked.get('mydrive_resumed'))

Path(OUTPUT_ROOT).mkdir(parents=True, exist_ok=True)
(Path(REPO) / 'outputs').mkdir(parents=True, exist_ok=True)

# Solo en Colab: OUTPUT_ROOT debe estar bajo MyDrive/outputs/madrl_v3_*
if IN_COLAB and str(Path(OUTPUT_ROOT)).startswith('/content/drive/'):
    output_norm = str(Path(OUTPUT_ROOT)).replace('\\', '/')
    _drive_outputs_prefix = '/content/drive/MyDrive/'
    assert 'MADRL_CityLearn_v3' not in output_norm, (
        f'OUTPUT_ROOT en namespace legacy prohibido: {OUTPUT_ROOT}. '
        'Ejecuta celda 1.5 (Drive canonico) y 2.1 de nuevo.'
    )
    assert output_norm.startswith(_drive_outputs_prefix) and '/outputs/madrl_v3_' in output_norm, (
        f'OUTPUT_ROOT fuera del namespace Drive esperado: {OUTPUT_ROOT}'
    )

assert Path(SCHEMA_PATH).exists(), f'Schema Iquitos no encontrado: {SCHEMA_PATH}'

# Punteros + monitor (fuente unica; lo reusan 7.2/7.3 via latest_colab_output_root.txt)
_common21.sync_output_root_pointer_files(
    Path(REPO), Path(OUTPUT_ROOT), gdrive_root=_gdrive_root_path
)
if not (globals().get('_MYDRIVE_RESUMED') and not _created_new_run):
    _mon_rc = _common21.refresh_colab_live_monitor_once(
        Path(REPO), Path(OUTPUT_ROOT), python_executable=PYTHON, log_tail=8
    )
    if _mon_rc not in (0, 1):
        print(f'[2.1] Monitor snapshot salio con codigo {_mon_rc} (continuando)')

RUN_CONTEXT = dict(globals().get('COLAB_PROJECT_CONTEXT', {}))
RUN_CONTEXT.update({
    'timestamp': TIMESTAMP,
    'run_label': RUN_LABEL,
    'output_root': OUTPUT_ROOT,
    'in_colab': IN_COLAB,
    'repo': REPO,
    'schema_path': SCHEMA_PATH,
    'resumed_existing_output_root': bool(RESUME_OUTPUT_ROOT),
    'created_new_run': _created_new_run,
    'base_output_parent': BASE_OUTPUT_PARENT,
    'drive_required': REQUIRE_GOOGLE_DRIVE,
    'drive_project_root': GDRIVE_ROOT,
})
with open(f'{OUTPUT_ROOT}/run_context_manifest.json', 'w') as f:
    json.dump(RUN_CONTEXT, f, indent=2)

print(f"Entorno     : {'Google Colab' if IN_COLAB else 'Local'}")
print(f"CODE_ROOT   : {CODE_ROOT}  (codigo fuente — launcher/monitor)")
print(f"OUTPUT_ROOT : {OUTPUT_ROOT}  (checkpoints/artefactos)")
print(f"MODO RUN    : {_resume_reason}")
print(f"TIMESTAMP   : {TIMESTAMP}")
print(f"SCHEMA_PATH : {SCHEMA_PATH}  {'OK' if Path(SCHEMA_PATH).exists() else 'NO ENCONTRADO'}")
print(f"Contexto    : {OUTPUT_ROOT}/run_context_manifest.json")
