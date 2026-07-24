# 1.4 Configurar sys.path, CUDA y smoke imports
# Vinculada con 1.3: usa PROJECT_PYTHON aunque el kernel Colab sea Python 3.11.
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(globals().get('PROJECT_DIR', '/content/MADRLCitytleranflexresdr'))
if not PROJECT_ROOT.exists() and Path.cwd().name == 'MADRLCitytleranflexresdr':
    PROJECT_ROOT = Path.cwd()
PROJECT_ROOT = PROJECT_ROOT.resolve()
REPO = str(PROJECT_ROOT)

PYTHON_MIN = globals().get('PYTHON_MIN', (3, 9))
PYTHON_MAX_EXCLUSIVE = globals().get('PYTHON_MAX_EXCLUSIVE', (3, 10))
PROJECT_PYTHON = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
PYTHON = PROJECT_PYTHON
EDITABLES = globals().get('EDITABLES', [
    'CityLearn/',
    'external/HARL/',
    'external/off-policy/',
    'external/MAAC/',
    'external/MARL/src/',
])


def repo_path(path):
    path = Path(path)
    return path if path.is_absolute() else PROJECT_ROOT / path


def _python_info_strict(python):
    code = """
import json
import sys
print(json.dumps({
    'executable': sys.executable,
    'version': sys.version.split()[0],
    'version_info': list(sys.version_info[:3]),
}))
"""
    result = subprocess.run([str(python), '-c', code], capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or f'No se pudo ejecutar {python}')
    return json.loads(result.stdout)


python_info = _python_info_strict


if 'same_executable' not in globals():
    def same_executable(left, right):
        try:
            return Path(left).resolve() == Path(right).resolve()
        except Exception:
            return str(left) == str(right)

if 'restart_runtime' not in globals():
    def restart_runtime(reason):
        print(f'\n[RESTART REQUERIDO] {reason}')
        print('Reinicia el runtime y vuelve a ejecutar desde la celda 1.2b.')
        try:
            from IPython.core.getipython import get_ipython
            import time

            print('Colab detectado: reiniciando kernel automaticamente...')
            _ip = get_ipython()
            _kernel = getattr(_ip, 'kernel', None) if _ip is not None else None
            if _kernel is not None:
                _kernel.do_shutdown(restart=True)
            time.sleep(10)
        except Exception:
            pass
        raise RuntimeError(reason)


project_python_info = python_info(PROJECT_PYTHON)
if project_python_info is None:
    raise RuntimeError(f'No se pudo leer Python de proyecto: {PROJECT_PYTHON}')
if not (PYTHON_MIN <= tuple(project_python_info['version_info'][:2]) < PYTHON_MAX_EXCLUSIVE):
    raise RuntimeError(
        f"Python de proyecto {project_python_info['version']} no soportado. "
        'Ejecuta primero la celda 1.3 para crear/validar .venv39-citylearn-v3.'
    )

PATHS = list(dict.fromkeys(str(path) for path in [
    PROJECT_ROOT,
    PROJECT_ROOT / 'CityLearn',
    PROJECT_ROOT / 'CityLearn' / 'scripts',
    *(repo_path(path) for path in EDITABLES),
]))
missing = [path for path in PATHS if not Path(path).exists()]
if missing:
    raise FileNotFoundError(f'Rutas requeridas no encontradas: {missing}')

for path in reversed(PATHS):
    while path in sys.path:
        sys.path.remove(path)
    sys.path.insert(0, path)

old_pythonpath = [p for p in os.environ.get('PYTHONPATH', '').split(os.pathsep) if p]
old_pythonpath = [p for p in old_pythonpath if p not in PATHS]
os.environ['PYTHONPATH'] = os.pathsep.join(PATHS + old_pythonpath)
os.environ['CITYLEARN_PROJECT_ROOT'] = REPO
os.environ.setdefault('CUDA_DEVICE_ORDER', 'PCI_BUS_ID')
os.environ.setdefault('PYTORCH_CUDA_ALLOC_CONF', 'expandable_segments:True,max_split_size_mb:128')
os.environ.setdefault('WANDB_MODE', 'disabled')
os.environ.setdefault('PYTHONHASHSEED', '0')

SMOKE_IMPORTS = {
    'torch': 'torch',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'scipy': 'scipy',
    'sklearn': 'sklearn',
    'citylearn': 'citylearn',
    'citylearn.v3.environment': 'citylearn.v3.environment',
    'harl': 'harl',
    'runner_msac': 'runner_msac',
    'offpolicy': 'offpolicy',
    'algorithms.attention_sac': 'algorithms.attention_sac',
}
OPTIONAL_IMPORTS = {'harl', 'runner_msac', 'offpolicy', 'algorithms.attention_sac'}

smoke_code = f"""
import importlib, json, sys
paths = {PATHS!r}
modules = {SMOKE_IMPORTS!r}
optional = set({sorted(OPTIONAL_IMPORTS)!r})
for path in reversed(paths):
    if path not in sys.path:
        sys.path.insert(0, path)
imports, versions = {{}}, {{'python': sys.version.split()[0], 'executable': sys.executable}}
for label, module_name in modules.items():
    try:
        module = importlib.import_module(module_name)
        imports[label] = 'ok'
        version = getattr(module, '__version__', None)
        if version:
            versions[label] = version
    except Exception as exc:
        imports[label] = f'FAILED: {{exc}}'
print(json.dumps({{'imports': imports, 'versions': versions}}, indent=2, sort_keys=True))
failed = {{k: v for k, v in imports.items() if v.startswith('FAILED')}}
critical_failed = {{k: v for k, v in failed.items() if k not in optional}}
if failed.keys() - critical_failed.keys():
    print(f'[WARN] Modulos opcionales no disponibles: {{sorted(failed.keys() - critical_failed.keys())}}')
if critical_failed:
    abi = any('numpy.dtype size changed' in v or 'numpy.core' in v or 'numpy.strings' in v or '_center' in v for v in critical_failed.values())
    hint = 'Reinicia el runtime y ejecuta 1.1-1.4 en orden.' if abi else 'Ejecuta primero la celda 1.3 y repite 1.4.'
    raise SystemExit(f'ERROR: imports criticos fallaron: {{critical_failed}}. {{hint}}')
"""

result = subprocess.run([PROJECT_PYTHON, '-c', smoke_code], capture_output=True, text=True, env=os.environ.copy())
if result.stdout.strip():
    print(result.stdout, end='')
if result.returncode != 0:
    if result.stderr.strip():
        print('[STDERR smoke check:]')
        print(result.stderr, end='')
    raise RuntimeError('Smoke imports criticos fallaron en Python 3.9 del proyecto. Revisa el JSON anterior.')

if same_executable(PROJECT_PYTHON, sys.executable):
    current_failures = {}
    for label, module_name in SMOKE_IMPORTS.items():
        if label in OPTIONAL_IMPORTS:
            continue
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            current_failures[label] = repr(exc)
    if current_failures:
        restart_runtime(
            'El subprocess importa bien, pero el kernel actual esta inconsistente: '
            f'{current_failures}.'
        )
else:
    print(f'Kernel notebook en {sys.version.split()[0]}; smoke imports ejecutados con {PROJECT_PYTHON}.')

print(f'Celda 1.4 OK: sys.path, CUDA env y smoke imports configurados para {PROJECT_PYTHON}.')
