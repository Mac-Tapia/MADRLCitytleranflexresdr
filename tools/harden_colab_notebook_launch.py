"""Harden the Colab A100 launch notebook against wrong repo/output context."""

from __future__ import annotations

import json
from pathlib import Path


NB_PATH = Path("CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")


def source_lines(text: str) -> list[str]:
    return text.strip("\n").splitlines(keepends=True)


def set_cell_source(cells: list[dict], cell_id: str, source: str) -> None:
    for cell in cells:
        if cell.get("id") == cell_id:
            cell["source"] = source_lines(source)
            if cell.get("cell_type") == "code":
                cell["outputs"] = []
                cell["execution_count"] = None
            return
    raise KeyError(f"Cell not found: {cell_id}")


def insert_after(cells: list[dict], after_id: str, new_cell: dict) -> None:
    cells[:] = [cell for cell in cells if cell.get("id") != new_cell["id"]]
    for index, cell in enumerate(cells):
        if cell.get("id") == after_id:
            cells.insert(index + 1, new_cell)
            return
    raise KeyError(f"Cell not found: {after_id}")


clone_cell = r"""
# ── 1.2  Clonar repositorio con submodulos desde rama validada ─────────────
import os, subprocess
from pathlib import Path

REPO_URL    = 'https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git'
REPO_BRANCH = 'codex/fix-madrl-traceability-docs'
REPO        = '/content/MADRLCitytleranflexresdr'


def git_check(args):
    cmd = ['git'] + [str(a) for a in args]
    print('+', ' '.join(cmd))
    subprocess.check_call(cmd)


def git_out(args) -> str:
    return subprocess.check_output(['git'] + [str(a) for a in args], text=True).strip()


if not os.path.exists(f'{REPO}/.git'):
    if os.path.exists(REPO):
        raise RuntimeError(f'{REPO} existe pero no contiene .git; elimina esa carpeta antes de clonar.')
    print(f'Clonando {REPO_URL} rama {REPO_BRANCH} ...')
    git_check(['clone', '--branch', REPO_BRANCH, '--depth', '1', REPO_URL, REPO])
else:
    origin = git_out(['-C', REPO, 'config', '--get', 'remote.origin.url'])
    if origin != REPO_URL:
        raise RuntimeError(f'Repo existente apunta a {origin}, esperado {REPO_URL}')
    print(f'Repositorio existente; sincronizando espejo limpio de rama {REPO_BRANCH} ...')
    git_check(['-C', REPO, 'fetch', '--depth', '1', 'origin', REPO_BRANCH])
    git_check(['-C', REPO, 'reset', '--hard'])
    git_check(['-C', REPO, 'checkout', '-B', REPO_BRANCH, 'FETCH_HEAD'])
    git_check(['-C', REPO, 'reset', '--hard', 'FETCH_HEAD'])

git_check(['-C', REPO, 'submodule', 'sync', '--recursive'])
git_check(['-C', REPO, 'submodule', 'update', '--init', '--recursive', '--force'])

os.chdir(REPO)
print(f'\nDirectorio de trabajo: {os.getcwd()}')
print('Rama activa:', git_out(['-C', REPO, 'rev-parse', '--abbrev-ref', 'HEAD']))
print('Commit activo:', git_out(['-C', REPO, 'rev-parse', '--short', 'HEAD']))
"""


mirror_cell = r"""
# ── 1.2b  Validar espejo del proyecto Colab antes de entrenar ──────────────
import glob, json, os, subprocess
from pathlib import Path

PROJECT_NAME = 'MADRLCitytleranflexresdr'
DATASET_DIR = f'{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025'
SCHEMA_FOR_CONTEXT = f'{DATASET_DIR}/schema.json'


def sh(args, *, cwd=REPO) -> str:
    return subprocess.check_output([str(a) for a in args], cwd=cwd, text=True).strip()


repo_root = sh(['git', 'rev-parse', '--show-toplevel'])
branch = sh(['git', 'rev-parse', '--abbrev-ref', 'HEAD'])
head = sh(['git', 'rev-parse', 'HEAD'])
origin = sh(['git', 'config', '--get', 'remote.origin.url'])

assert Path(repo_root).resolve() == Path(REPO).resolve(), f'Repo root inesperado: {repo_root}'
assert branch == REPO_BRANCH, f'Rama incorrecta: {branch} != {REPO_BRANCH}'
assert origin == REPO_URL, f'Origin incorrecto: {origin} != {REPO_URL}'

submodule_status = sh(['git', 'submodule', 'status', '--recursive'])
bad_submodules = [
    line for line in submodule_status.splitlines()
    if line and line[0] in {'-', '+', 'U'}
]
if bad_submodules:
    raise RuntimeError('Submodulos no inicializados o fuera del commit fijado:\n' + '\n'.join(bad_submodules))

citylearn_tree = sh(['git', 'ls-tree', 'HEAD', 'CityLearn'])
expected_citylearn_commit = citylearn_tree.split()[2]
actual_citylearn_commit = sh(['git', '-C', f'{REPO}/CityLearn', 'rev-parse', 'HEAD'])
assert actual_citylearn_commit == expected_citylearn_commit, (
    f'CityLearn no coincide con el commit fijado por el repo padre: '
    f'{actual_citylearn_commit[:12]} != {expected_citylearn_commit[:12]}'
)

required_paths = [
    'CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb',
    'CityLearn/scripts/colab_a100_official_launcher.py',
    'CityLearn/scripts/colab_a100_live_monitor.py',
    'CityLearn/scripts/train_citylearn_v3_happo.py',
    'CityLearn/scripts/train_citylearn_v3_masac.py',
    'CityLearn/scripts/train_citylearn_v3_matd3.py',
    'CityLearn/scripts/train_citylearn_v3_maac.py',
    'CityLearn/citylearn/v3/environment.py',
    'external/HARL',
    'external/MARL/src',
    'external/off-policy',
    'external/MAAC',
    'tools',
    'docs',
]
missing = [p for p in required_paths if not (Path(REPO) / p).exists()]
if missing:
    raise FileNotFoundError('Faltan rutas requeridas en el espejo Colab: ' + ', '.join(missing))

csv_count = len(glob.glob(f'{DATASET_DIR}/*.csv'))
with open(SCHEMA_FOR_CONTEXT) as f:
    schema_context = json.load(f)
assert csv_count == 222, f'Dataset incompleto: {csv_count}/222 CSV'
assert len(schema_context.get('buildings', {})) == 17, 'Schema no tiene 17 edificios'
assert schema_context.get('simulation_end_time_step') == 26303, 'simulation_end_time_step inesperado'

COLAB_PROJECT_CONTEXT = {
    'project_name': PROJECT_NAME,
    'repo_url': REPO_URL,
    'repo_branch': branch,
    'repo_commit': head,
    'repo_root': REPO,
    'citylearn_commit': actual_citylearn_commit,
    'submodule_status': submodule_status,
    'dataset_dir': DATASET_DIR,
    'dataset_csv_count': csv_count,
    'buildings': len(schema_context.get('buildings', {})),
    'simulation_steps': schema_context.get('simulation_end_time_step') + 1,
}

os.makedirs(f'{REPO}/outputs', exist_ok=True)
with open(f'{REPO}/outputs/colab_project_context.json', 'w') as f:
    json.dump(COLAB_PROJECT_CONTEXT, f, indent=2)

print('[OK] Espejo Colab validado contra repo/submodulos/dataset.')
print(f"Repo    : {branch} @ {head[:12]}")
print(f"CityLearn submodule: {actual_citylearn_commit[:12]}")
print(f"Dataset : {csv_count} CSV, {COLAB_PROJECT_CONTEXT['buildings']} edificios")
"""


deps_cell = r"""
# ── 1.3  Instalar dependencias del proyecto de forma reproducible ───────────
# No se instalan como paquetes los backends que no tienen setup.py/pyproject
# (external/MARL/src y external/MAAC). Esos se exponen via sys.path.
import json, os, sys, subprocess
from pathlib import Path

os.chdir('/content/MADRLCitytleranflexresdr')

PYTHON_MIN = (3, 9)
PYTHON_MAX_EXCLUSIVE = (3, 12)
if not (PYTHON_MIN <= sys.version_info[:2] < PYTHON_MAX_EXCLUSIVE):
    raise RuntimeError(
        f'Python {sys.version.split()[0]} no soportado para este notebook. '
        'Usa un runtime Colab con Python 3.9, 3.10 o 3.11. '
        'Python 3.12 rompe la combinación CityLearn/scikit-learn<=1.2.2 y '
        'suele producir errores ABI numpy/pandas.'
    )

BINARY_MODULES = ['numpy', 'pandas', 'scipy', 'sklearn', 'matplotlib', 'seaborn']
modules_loaded_before_install = sorted(m for m in BINARY_MODULES if m in sys.modules)
KERNEL_BINARY_MODULES_LOADED_BEFORE_INSTALL = modules_loaded_before_install
KERNEL_BINARY_MODULES_STALE_AFTER_INSTALL = False

CONSTRAINTS = Path('/tmp/madrl_citylearn_colab_constraints.txt')
COMPAT_WHEELS = [
    'numpy==1.26.4',
    'pandas==2.1.4',
    'scipy==1.11.4',
    'scikit-learn==1.2.2',
    'matplotlib==3.8.4',
    'seaborn==0.13.2',
]
RUNTIME_UTILS = [
    'tensorboard',
    'tensorboardX',
    'setproctitle',
    'simplejson',
]
CONSTRAINTS.write_text('\n'.join(COMPAT_WHEELS) + '\n')


def pip_install(*args):
    cmd = [sys.executable, '-m', 'pip', 'install', '--disable-pip-version-check', *args]
    print(' '.join(cmd))
    subprocess.check_call(cmd)


# Usar constraints durante los editables evita que pip resuelva pandas/numpy a
# ruedas incompatibles con CityLearn y el Python del runtime Colab.
pip_install('-q', '-c', str(CONSTRAINTS), '-e', 'CityLearn/')
pip_install('-q', '-c', str(CONSTRAINTS), '-e', 'external/HARL/')
pip_install('-q', '-c', str(CONSTRAINTS), '-e', 'external/off-policy/')

# Reinstalación final: deja numpy/pandas/scipy/sklearn en una ABI coherente.
pip_install('-q', '--force-reinstall', '--no-cache-dir', *COMPAT_WHEELS, *RUNTIME_UTILS)

compat_check = r'''
import json
import numpy, pandas, scipy, sklearn, matplotlib, seaborn
versions = {
    'numpy': numpy.__version__,
    'pandas': pandas.__version__,
    'scipy': scipy.__version__,
    'scikit-learn': sklearn.__version__,
    'matplotlib': matplotlib.__version__,
    'seaborn': seaborn.__version__,
}
print(json.dumps(versions, indent=2))
'''
print('\nVerificando ABI en un proceso Python nuevo...')
subprocess.check_call([sys.executable, '-c', compat_check])

if modules_loaded_before_install:
    KERNEL_BINARY_MODULES_STALE_AFTER_INSTALL = True
    print(
        '\n[WARN] Se reinstalaron paquetes binarios, pero ya estaban cargados en este kernel: '
        f'{modules_loaded_before_install}.'
    )
    print(
        '[WARN] No se detiene el notebook: el entrenamiento oficial corre en procesos Python nuevos '
        'y usara las ruedas compatibles recien instaladas.'
    )
    print(
        '[WARN] Si necesitas ejecutar analisis/imports pesados dentro de este mismo kernel, '
        'reinicia runtime y repite 1.1 -> 1.2 -> 1.2b -> 1.3 -> 1.4.'
    )

print('\nDependencias instaladas con ABI compatible. MASAC y MAAC se cargan por sys.path, no por pip editable.')
"""


smoke_cell = r"""
# ── 1.4  Configurar sys.path, CUDA y smoke imports ──────────────────────────
import os, sys, subprocess, json
from pathlib import Path

if not ((3, 9) <= sys.version_info[:2] < (3, 12)):
    raise RuntimeError(
        f'Python {sys.version.split()[0]} no soportado. '
        'Selecciona un runtime Colab con Python 3.9, 3.10 o 3.11.'
    )

REPO = '/content/MADRLCitytleranflexresdr'
_paths = [
    REPO,
    f'{REPO}/CityLearn',
    f'{REPO}/CityLearn/scripts',
    f'{REPO}/external/HARL',
    f'{REPO}/external/MARL/src',
    f'{REPO}/external/off-policy',
    f'{REPO}/external/MAAC',
]
for p in reversed(_paths):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ['PYTHONPATH'] = ':'.join(_paths + [os.environ.get('PYTHONPATH', '')])
os.environ['CITYLEARN_PROJECT_ROOT'] = REPO
os.environ.setdefault('CUDA_DEVICE_ORDER', 'PCI_BUS_ID')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True,max_split_size_mb:128')
os.environ.setdefault('WANDB_MODE', 'disabled')
os.environ.setdefault('PYTHONHASHSEED', '0')

required_paths = [Path(p) for p in _paths]
missing = [str(p) for p in required_paths if not p.exists()]
if missing:
    raise FileNotFoundError(f'Rutas requeridas no encontradas: {missing}')

modules = [
    'torch',
    'numpy',
    'pandas',
    'scipy',
    'sklearn',
    'citylearn',
    'citylearn.v3.environment',
    'harl',
    'runner_msac',
    'offpolicy',
    'algorithms.attention_sac',
]

smoke_check = r'''
import importlib, json, os, sys

_paths = __PATHS__
modules = __MODULES__
for p in reversed(_paths):
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ['PYTHONPATH'] = ':'.join(_paths + [os.environ.get('PYTHONPATH', '')])
os.environ['CITYLEARN_PROJECT_ROOT'] = _paths[0]
os.environ.setdefault('CUDA_DEVICE_ORDER', 'PCI_BUS_ID')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True,max_split_size_mb:128')
os.environ.setdefault('WANDB_MODE', 'disabled')
os.environ.setdefault('PYTHONHASHSEED', '0')

smoke = {}
versions = {}
for name in modules:
    try:
        module = importlib.import_module(name)
        smoke[name] = 'ok'
        version = getattr(module, '__version__', None)
        if version:
            versions[name] = version
    except Exception as exc:
        smoke[name] = f'FAILED: {exc}'

print(json.dumps({'imports': smoke, 'versions': versions}, indent=2))
failures = {k: v for k, v in smoke.items() if v.startswith('FAILED')}
if failures:
    abi_fail = any('numpy.dtype size changed' in v for v in failures.values())
    hint = (
        ' Detectado conflicto ABI numpy/pandas: ejecuta 1.3 en un runtime limpio, '
        'reinicia el kernel si 1.3 indica que reinstalo paquetes ya cargados, y luego repite 1.4.'
        if abi_fail else ''
    )
    raise RuntimeError(f'Smoke imports fallaron: {failures}.{hint}')
'''.replace('__PATHS__', repr(_paths)).replace('__MODULES__', repr(modules))

if globals().get('KERNEL_BINARY_MODULES_STALE_AFTER_INSTALL', False):
    print('[WARN] Kernel con modulos binarios cargados antes de 1.3; validando smoke imports en un proceso Python nuevo.')
    subprocess.check_call([sys.executable, '-c', smoke_check])
    print('sys.path, CUDA env y smoke imports validados en proceso Python nuevo. Entrenamiento listo para launcher subprocess.')
else:
    exec(smoke_check)
    print('sys.path, CUDA env y smoke imports configurados.')
"""


drive_cell = r"""
# ── 1.5  Montar Google Drive para checkpoints y reanudacion ─────────────────
import os

USE_GOOGLE_DRIVE = True
REQUIRE_GOOGLE_DRIVE = True
DRIVE_WORKSPACE_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3'
PROJECT_NAME = globals().get('PROJECT_NAME', 'MADRLCitytleranflexresdr')
GDRIVE_ROOT = None
GDRIVE_OUTPUT_PARENT = None

if USE_GOOGLE_DRIVE:
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        GDRIVE_ROOT = f'{DRIVE_WORKSPACE_ROOT}/{PROJECT_NAME}'
        GDRIVE_OUTPUT_PARENT = f'{GDRIVE_ROOT}/outputs'
        os.makedirs(GDRIVE_OUTPUT_PARENT, exist_ok=True)
        print('Google Drive montado:', GDRIVE_ROOT)
        print('Outputs del entrenamiento:', GDRIVE_OUTPUT_PARENT)
    except Exception as exc:
        if REQUIRE_GOOGLE_DRIVE:
            raise RuntimeError(
                'Google Drive es obligatorio para este entrenamiento largo. '
                'Conecta Colab con mac.tapia.c@uni.pe y vuelve a ejecutar 1.5.'
            ) from exc
        print('Drive no disponible; usando outputs local del runtime:', exc)
        GDRIVE_ROOT = None
        GDRIVE_OUTPUT_PARENT = None
"""


paths_cell = r"""
# ── 2.1  Rutas, timestamp y directorio de salida recuperable ────────────────
import json, os, sys
from datetime import datetime
from pathlib import Path

REPO        = '/content/MADRLCitytleranflexresdr'
PROJECT_NAME = globals().get('PROJECT_NAME', 'MADRLCitytleranflexresdr')
TIMESTAMP   = datetime.now().strftime('%Y%m%d_%H%M%S')
RUN_LABEL   = f'colab_madrl_a100_{TIMESTAMP}'
SCHEMA_PATH = f'{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'
PYTHON      = sys.executable

BASE_OUTPUT_PARENT = GDRIVE_OUTPUT_PARENT if GDRIVE_OUTPUT_PARENT else f'{REPO}/outputs'
# Para reanudar una corrida existente, pega aqui el output root exacto de Drive.
# Mantener None crea una corrida nueva y aislada.
RESUME_OUTPUT_ROOT = None

OUTPUT_ROOT = RESUME_OUTPUT_ROOT or f'{BASE_OUTPUT_PARENT}/{RUN_LABEL}'
Path(OUTPUT_ROOT).mkdir(parents=True, exist_ok=bool(RESUME_OUTPUT_ROOT))
Path(f'{REPO}/outputs').mkdir(parents=True, exist_ok=True)

output_norm = str(Path(OUTPUT_ROOT)).replace('\\', '/')
expected_drive_prefix = f'/content/drive/MyDrive/MADRL_CityLearn_v3/{PROJECT_NAME}/outputs/colab_madrl_a100_'
if GDRIVE_OUTPUT_PARENT:
    assert output_norm.startswith(expected_drive_prefix), (
        f'OUTPUT_ROOT fuera del namespace del proyecto: {OUTPUT_ROOT}'
    )

forbidden_markers = [
    'citylearn_v3_madrl_full_',
    'visible_pwsh',
    'benchmark_v2_baseline',
    'thesis_objective_evidence',
    'test_notebook',
]
if any(marker in Path(OUTPUT_ROOT).name for marker in forbidden_markers):
    raise RuntimeError(f'OUTPUT_ROOT parece mezclarse con otro flujo: {OUTPUT_ROOT}')

# El monitor Colab y el monitor oficial buscan estas rutas dentro del repo clonado.
for latest_name in ['latest_colab_output_root.txt', 'latest_visible_training_output_root.txt']:
    with open(f'{REPO}/outputs/{latest_name}', 'w') as _f:
        _f.write(OUTPUT_ROOT)
    if GDRIVE_ROOT:
        with open(f'{GDRIVE_ROOT}/{latest_name}', 'w') as _f:
            _f.write(OUTPUT_ROOT)

assert os.path.exists(SCHEMA_PATH), f'Schema no encontrado: {SCHEMA_PATH}'

RUN_CONTEXT = dict(globals().get('COLAB_PROJECT_CONTEXT', {}))
RUN_CONTEXT.update({
    'timestamp': TIMESTAMP,
    'run_label': RUN_LABEL,
    'output_root': OUTPUT_ROOT,
    'resumed_existing_output_root': bool(RESUME_OUTPUT_ROOT),
    'base_output_parent': BASE_OUTPUT_PARENT,
    'drive_required': REQUIRE_GOOGLE_DRIVE,
    'drive_project_root': GDRIVE_ROOT,
})
with open(f'{OUTPUT_ROOT}/run_context_manifest.json', 'w') as f:
    json.dump(RUN_CONTEXT, f, indent=2)

print(f'TIMESTAMP   : {TIMESTAMP}')
print(f'OUTPUT_ROOT : {OUTPUT_ROOT}')
print(f'SCHEMA_PATH : {SCHEMA_PATH}  OK')
print(f'Contexto    : {OUTPUT_ROOT}/run_context_manifest.json')
"""


dry_run_cell = r"""
# ── 7.1  Preflight A100 + dry-run oficial ───────────────────────────────────
dry_run_cmd = launcher_base_args() + ['--dry-run', '--skip-completed']
run_cmd(dry_run_cmd)
monitor_once()

status_path = Path(OUTPUT_ROOT) / 'official_full_status.json'
with open(status_path) as f:
    status = json.load(f)
assert status['status'] == 'dry_run', status['status']
assert status['training_config']['a100_ready'] is True
assert len(status['jobs']) == 12, len(status['jobs'])

expected_root = Path(OUTPUT_ROOT).resolve()
seen_outputs = set()
for job in status['jobs']:
    job_output = Path(job['output_dir'])
    if not job_output.is_absolute():
        job_output = Path(REPO) / job_output
    job_output = job_output.resolve()
    rel = job_output.relative_to(expected_root)
    parts = rel.parts
    assert len(parts) == 2, f'Layout inesperado: {job_output}'
    assert parts[0] in ALGORITHMS, f'Algoritmo inesperado en output_dir: {parts[0]}'
    assert parts[1] in {f'{sc}_seed_{SEED}' for sc in SCENARIOS}, f'Scenario/seed inesperado: {parts[1]}'
    seen_outputs.add(str(job_output))
assert len(seen_outputs) == 12, f'Output dirs duplicados o incompletos: {len(seen_outputs)}'

print('Dry-run validado: 12 jobs planificados, A100 config lista, outputs aislados en OUTPUT_ROOT.')
"""


summary_cell = r"""
# ── 10.  Resumen final de la sesión Colab ───────────────────────────────────
import json, glob, os
from datetime import datetime

print("=" * 65)
print("  RESUMEN FINAL — MADRL CityLearn v3 · Colab A100")
print("=" * 65)
print(f"  Output root : {OUTPUT_ROOT}")
print(f"  Timestamp   : {TIMESTAMP}")
print(f"  Modo        : {'QUICK_TEST' if QUICK_TEST else 'FULL TRAINING (50 ep)'}")

n_json = len(glob.glob(f"{OUTPUT_ROOT}/**/*.json",  recursive=True))
n_csv  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.csv",   recursive=True))
n_png  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.png",   recursive=True))
n_ckpt = len(glob.glob(f"{OUTPUT_ROOT}/**/*.pt",    recursive=True))
print(f"\n  Artefactos : {n_json} JSON · {n_csv} CSV · {n_png} PNG · {n_ckpt} .pt")

if stat_results and "ranking" in stat_results:
    print("\n  RANKING FINAL:")
    for i, r in enumerate(stat_results["ranking"], 1):
        mark = " ★" if i == 1 else ""
        print(f"    {i}. {r['algorithm']:<6} {r['mean_score']:.4f}{mark}")
    kw = stat_results.get("kruskal_wallis", {})
    if kw:
        print(f"  KW: p={kw.get('p','?')} ({'✅' if kw.get('significant') else ''})")
else:
    print("\n  Referencia oficial v4:")
    print("    1. MATD3  0.7445 ★")
    print("    2. MASAC  ~0.73")
    print("    3. MAAC   ~0.72")
    print("    4. HAPPO  ~0.70")
    print("    KW p=0.0459 ✅")

summary = {
    "timestamp":        TIMESTAMP,
    "output_root":      OUTPUT_ROOT,
    "run_context":      RUN_CONTEXT,
    "mode":             "quick_test" if QUICK_TEST else "full_training",
    "episodes":         EPISODES,
    "episode_steps":    EPISODE_STEPS,
    "num_env_steps":    NUM_ENV_STEPS,
    "algorithms":       ALGORITHMS,
    "scenarios":        SCENARIOS,
    "a100_tuning": {
        "happo_hidden":         512,
        "masac_buffer_size":    20,
        "masac_critic_batch":   64,
        "masac_max_buf_gib":    20,
        "matd3_batch_size":     512,
        "matd3_buffer_size":    6000,
        "maac_batch_size":      512,
        "maac_buffer_length":   100000,
    },
    "artifacts": {"json": n_json, "csv": n_csv, "png": n_png, "pt": n_ckpt},
    "statistical_analysis": stat_results if stat_results else "run training first",
}
with open(f"{OUTPUT_ROOT}/colab_session_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\n  ✅  Resumen: {OUTPUT_ROOT}/colab_session_summary.json")
print("=" * 65)
"""


def main() -> None:
    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    cells = nb["cells"]

    set_cell_source(cells, "c06557c1", clone_cell)
    insert_after(
        cells,
        "c06557c1",
        {
            "cell_type": "code",
            "execution_count": None,
            "id": "repo_mirror_verify",
            "metadata": {},
            "outputs": [],
            "source": source_lines(mirror_cell),
        },
    )
    set_cell_source(cells, "188059f1", deps_cell)
    set_cell_source(cells, "221bf910", smoke_cell)
    set_cell_source(cells, "56e338c7", drive_cell)
    set_cell_source(cells, "c1f8ada9", paths_cell)
    set_cell_source(cells, "3c0758f9", dry_run_cell)
    set_cell_source(cells, "f1cac01b", summary_cell)

    for cell in cells:
        if cell.get("id") == "launch_guide":
            src = "".join(cell.get("source", []))
            src = src.replace(
                "`MyDrive/MADRL_CityLearn_v3/colab_madrl_a100_<timestamp>/`",
                "`MyDrive/MADRL_CityLearn_v3/MADRLCitytleranflexresdr/outputs/colab_madrl_a100_<timestamp>/`",
            )
            src = src.replace(
                "OUTPUT_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3/<tu_timestamp>'",
                "OUTPUT_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3/MADRLCitytleranflexresdr/outputs/<tu_timestamp>'",
            )
            src = src.replace(
                "> Si Colab se desconecta: vuelve a ejecutar 1.1 → 1.5 → 2.1 → 6.1 → 7.0 → 7.2.",
                "> Si Colab se desconecta: vuelve a ejecutar 1.1 → 1.5, pega el `OUTPUT_ROOT` anterior en `RESUME_OUTPUT_ROOT` dentro de 2.1, y luego ejecuta 2.1 → 6.1 → 7.0 → 7.2.",
            )
            src = src.replace(
                "# Luego ejecutar: 1.2 → 1.3 → 1.4 → 1.5 → 6.1 → 7.0 → 7.2",
                "# Luego ejecutar: 1.2 → 1.2b → 1.3 → 1.4 → 1.5 → 2.1 → 6.1 → 7.0 → 7.2",
            )
            src = src.replace(
                "# Luego ejecutar en orden: 1.2 -> 1.3 -> 1.4 -> 1.5 -> 6.1 -> 7.0 -> 7.2",
                "# Luego ejecutar en orden: 1.2 -> 1.2b -> 1.3 -> 1.4 -> 1.5 -> 2.1 -> 6.1 -> 7.0 -> 7.2",
            )
            cell["source"] = source_lines(src)

    for cell in cells:
        if cell.get("cell_type") == "code":
            cell["outputs"] = []
            cell["execution_count"] = None

    NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"Updated {NB_PATH}: {len(cells)} cells")


if __name__ == "__main__":
    main()
