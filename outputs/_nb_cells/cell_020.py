# 1.3 Instalar dependencias del proyecto de forma reproducible
# Usa Python 3.9 del proyecto. Si Colab entrega kernel 3.11, crea/usa .venv39-citylearn-v3.
import importlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

PROJECT_DIR = '/content/MADRLCitytleranflexresdr'
PROJECT_ROOT = Path(PROJECT_DIR)
if not PROJECT_ROOT.exists() and Path.cwd().name == 'MADRLCitytleranflexresdr':
    PROJECT_ROOT = Path.cwd()
    PROJECT_DIR = str(PROJECT_ROOT)

VENV_DIR = PROJECT_ROOT / '.venv39-citylearn-v3'
SETUP_LOG = Path('/tmp/madrl_py39_setup.log')
CONSTRAINTS = Path('/tmp/madrl_compat.txt')
PYTHON_REQUIRED = (3, 9)
PYTHON_MIN = PYTHON_REQUIRED
PYTHON_MAX_EXCLUSIVE = (3, 10)
PYTORCH_INDEX_CU126 = 'https://download.pytorch.org/whl/cu126'
PYTORCH_INDEX_CU128 = 'https://download.pytorch.org/whl/cu128'
TORCH_PACKAGES = ('torch', 'torchvision')

def detect_pytorch_cuda_wheel():
    """Blackwell (sm_120, RTX PRO 6000) requiere wheels cu128; A100/H100 usan cu126."""
    try:
        name = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name', '--format=csv,noheader'],
            text=True, stderr=subprocess.DEVNULL,
        ).strip().splitlines()[0].strip()
    except Exception:
        return PYTORCH_INDEX_CU126, None
    upper = name.upper()
    blackwell = any(k in upper for k in ('BLACKWELL', 'RTX PRO 6000', 'RTX 50'))
    index = PYTORCH_INDEX_CU128 if blackwell else PYTORCH_INDEX_CU126
    return index, name

PYTORCH_INDEX_URL, _DETECTED_GPU = detect_pytorch_cuda_wheel()
print(f'[torch] GPU: {_DETECTED_GPU or "(sin nvidia-smi)"} -> index {PYTORCH_INDEX_URL.split("/")[-1]}')

COMPAT_WHEELS = [
    'numpy==1.23.5',
    'pandas==2.0.3',
    'scipy==1.10.1',
    'scikit-learn==1.2.2',
    'matplotlib==3.7.5',
    'seaborn==0.12.2',
]
PINNED = {
    'numpy': '1.23.5',
    'pandas': '2.0.3',
    'scipy': '1.10.1',
    'scikit-learn': '1.2.2',
    'matplotlib': '3.7.5',
    'seaborn': '0.12.2',
    'gymnasium': '0.28.1',
    'pettingzoo': '1.12.0',
}
BASE_DEPS = [
    *COMPAT_WHEELS,
    'pyyaml',
    'requests>=2.28',
    'tqdm>=4.65',
    'psutil>=5.9',
    'platformdirs>=3.0',
    'protobuf==3.20.3',
    'gymnasium==0.28.1',
    'pettingzoo==1.12.0',
    'gym==0.20.0',
    'tensorboard',
    'tensorboardX',
    'setproctitle',
    'simplejson',
    'absl-py',
    'dm-tree',
    'importlib-metadata>=6.0,<9',
]
NO_DEPS_UTILS = [
    'supersuit==3.2.0',
    'icecream==2.1.3',
]
EDITABLES = [
    'CityLearn/',
    'external/HARL/',
    'external/off-policy/',
    'external/MAAC/',
    'external/MARL/src/',
]
BINARY_DEPS = ('numpy', 'pandas', 'scipy', 'scikit-learn', 'matplotlib', 'seaborn')

ABI_CHECK = """
import importlib
import json
import sys

modules = {
    'torch': 'torch',
    'numpy': 'numpy',
    'pandas': 'pandas',
    'scipy': 'scipy',
    'scikit-learn': 'sklearn',
    'matplotlib': 'matplotlib',
    'seaborn': 'seaborn',
    'gym': 'gym',
    'gymnasium': 'gymnasium',
    'pettingzoo': 'pettingzoo',
    'citylearn.v3.environment': 'citylearn.v3.environment',
}
CRITICAL = {'numpy', 'scipy', 'sklearn', 'gymnasium', 'pettingzoo', 'citylearn.v3.environment'}
versions = {'python': sys.version.split()[0], 'executable': sys.executable}
failures = {}
for label, module_name in modules.items():
    try:
        module = importlib.import_module(module_name)
        versions[label] = getattr(module, '__version__', 'importado')
    except Exception as exc:
        failures[label] = repr(exc)
        versions[label] = f'ERROR: {exc}'
try:
    import torch
    versions['torch_cuda_available'] = bool(torch.cuda.is_available())
    versions['torch_cuda'] = getattr(torch.version, 'cuda', None)
except Exception as exc:
    versions['torch_cuda_error'] = repr(exc)
print(json.dumps(versions, indent=2, sort_keys=True))
critical_failures = {k: v for k, v in failures.items() if k in CRITICAL}
if critical_failures:
    print('CRITICAL_FAILURES: ' + json.dumps(critical_failures), file=sys.stderr)
    sys.exit(1)
elif failures:
    print('NON_CRITICAL_FAILURES: ' + json.dumps(failures), file=sys.stderr)
"""


def write_log(text):
    SETUP_LOG.parent.mkdir(parents=True, exist_ok=True)
    with SETUP_LOG.open('a', encoding='utf-8') as f:
        f.write(text)
        if not text.endswith('\n'):
            f.write('\n')


def print_log_tail(lines=80):
    if not SETUP_LOG.exists():
        return
    tail = SETUP_LOG.read_text(encoding='utf-8', errors='replace').splitlines()[-lines:]
    print(f'\n[TAIL {SETUP_LOG}]')
    print('\n'.join(tail))


def run(cmd, *, cwd=None, env=None, check=True):
    cmd = [str(part) for part in cmd]
    message = '+ ' + ' '.join(cmd)
    print(message)
    write_log('\n' + message)
    proc = subprocess.run(
        cmd,
        cwd=str(cwd or PROJECT_ROOT),
        env=env,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    if proc.stdout:
        write_log(proc.stdout)
    if check and proc.returncode != 0:
        print_log_tail()
        raise RuntimeError(
            f'Comando fallo con exit={proc.returncode}: {message}. '
            f'Log completo: {SETUP_LOG}'
        )
    return proc


def run_shell(script, *, cwd=None, env=None, check=True):
    return run(['bash', '-lc', script], cwd=cwd, env=env, check=check)


def venv_python_path():
    if os.name == 'nt':
        return VENV_DIR / 'Scripts' / 'python.exe'
    return VENV_DIR / 'bin' / 'python'


def python_info(python):
    python = str(python)
    if not Path(python).exists() and python != sys.executable:
        return None
    code = """
import json
import sys
print(json.dumps({
    'executable': sys.executable,
    'version': sys.version.split()[0],
    'version_info': list(sys.version_info[:3]),
}))
"""
    result = subprocess.run([python, '-c', code], capture_output=True, text=True)
    if result.returncode != 0:
        return None
    return json.loads(result.stdout)


def same_executable(left, right):
    try:
        return Path(left).resolve() == Path(right).resolve()
    except Exception:
        return str(left) == str(right)


def setup_env():
    env = os.environ.copy()
    home_bin = str(Path.home() / '.local' / 'bin')
    env['PATH'] = home_bin + os.pathsep + env.get('PATH', '')
    return env


def ensure_uv(env):
    uv = shutil.which('uv', path=env.get('PATH'))
    if uv:
        return uv
    run_shell('curl -LsSf https://astral.sh/uv/install.sh | sh', env=env)
    uv = shutil.which('uv', path=env.get('PATH'))
    if uv:
        return uv
    candidate = Path.home() / '.local' / 'bin' / 'uv'
    if candidate.exists():
        return str(candidate)
    raise RuntimeError('uv no quedo disponible en PATH despues de instalarlo.')


def ensure_project_python39():
    current_info = python_info(sys.executable)
    if current_info and tuple(current_info['version_info'][:2]) == PYTHON_REQUIRED:
        return sys.executable

    project_python = venv_python_path()
    project_info = python_info(project_python)
    if project_info and tuple(project_info['version_info'][:2]) == PYTHON_REQUIRED:
        return str(project_python)

    if platform.system() == 'Windows':
        raise RuntimeError(
            'El kernel actual no es Python 3.9. En Windows selecciona '
            '.venv39-citylearn-v3 como kernel o recrea el entorno con scripts/setup.'
        )

    env = setup_env()
    uv = ensure_uv(env)
    print(
        f'Kernel actual: Python {sys.version.split()[0]} ({sys.executable}). '
        f'Creando entorno de proyecto Python 3.9 en {VENV_DIR}.'
    )
    run([uv, 'python', 'install', '3.9'], cwd=PROJECT_ROOT, env=env)
    run([uv, 'venv', '--python', '3.9', str(VENV_DIR)], cwd=PROJECT_ROOT, env=env)

    project_info = python_info(project_python)
    if not project_info or tuple(project_info['version_info'][:2]) != PYTHON_REQUIRED:
        raise RuntimeError(f'No se pudo crear un Python 3.9 valido en {project_python}')
    return str(project_python)


def pip_install(*args):
    cmd = [PROJECT_PYTHON, '-m', 'pip', 'install', '--disable-pip-version-check', *args]
    run(cmd)


def installed_version(package):
    code = """
import importlib.metadata as im
import sys
package = sys.argv[1]
names = (package, package.replace('-', '_'), package.replace('_', '-'))
for name in dict.fromkeys(names):
    try:
        print(im.version(name))
        raise SystemExit(0)
    except im.PackageNotFoundError:
        pass
raise SystemExit(1)
"""
    result = subprocess.run([PROJECT_PYTHON, '-c', code, package], capture_output=True, text=True)
    return result.stdout.strip() if result.returncode == 0 else None


def torch_gpu_ready():
    """True solo si PyTorch puede ejecutar un kernel real en la GPU (detecta sm_120 sin cu128)."""
    code = """
import json, sys
try:
    import torch
    info = {
        'version': torch.__version__,
        'cuda_runtime': getattr(torch.version, 'cuda', None),
        'cuda_available': bool(torch.cuda.is_available()),
    }
    if not info['cuda_available']:
        print(json.dumps({**info, 'ready': False, 'reason': 'cuda_unavailable'}))
        raise SystemExit(0)
    cap = torch.cuda.get_device_capability(0)
    info['device'] = torch.cuda.get_device_name(0)
    info['capability'] = list(cap)
    upper = info['device'].upper()
    needs_cu128 = cap[0] >= 12 or any(k in upper for k in ('BLACKWELL', 'RTX PRO 6000', 'RTX 50'))
    info['needs_cu128'] = needs_cu128
    cuda_rt = str(info['cuda_runtime'] or '')
    if needs_cu128 and not cuda_rt.startswith('12.8'):
        print(json.dumps({**info, 'ready': False, 'reason': 'blackwell_needs_cu128'}))
        raise SystemExit(0)
    x = torch.zeros(1, device='cuda')
    _ = (x + 1).item()
    torch.cuda.synchronize()
    print(json.dumps({**info, 'ready': True, 'kernel_ok': True}))
except Exception as exc:
    print(json.dumps({'ready': False, 'reason': 'kernel_failed', 'error': repr(exc)}))
"""
    result = subprocess.run([PROJECT_PYTHON, '-c', code], capture_output=True, text=True)
    line = (result.stdout or '').strip().splitlines()
    if not line:
        return False, {}
    try:
        data = json.loads(line[-1])
    except Exception:
        return False, {}
    if result.stdout.strip():
        print('[torch]', line[-1])
    return bool(data.get('ready')), data


def torch_cuda_available():
    ready, _ = torch_gpu_ready()
    return ready


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


def repair_binary_abi():
    print('[ABI] Reinstalando ruedas binarias con versiones fijadas (numpy 1.23.5)...')
    pip_install('-q', '--force-reinstall', '--no-cache-dir', *COMPAT_WHEELS)


def verify_subprocess_imports():
    result = subprocess.run([PROJECT_PYTHON, '-c', ABI_CHECK], capture_output=True, text=True)
    if result.stdout.strip():
        print(result.stdout, end='')
    if result.returncode != 0:
        stderr = result.stderr.strip()
        abi_mismatch = any(
            token in stderr
            for token in ('numpy.dtype size changed', 'binary incompatibility', 'numpy.core', 'numpy.strings')
        )
        if abi_mismatch:
            repair_binary_abi()
            result = subprocess.run([PROJECT_PYTHON, '-c', ABI_CHECK], capture_output=True, text=True)
            if result.stdout.strip():
                print(result.stdout, end='')
        if result.returncode != 0:
            if result.stderr.strip():
                print('[STDERR verificacion ABI:]')
                print(result.stderr[-4000:], end='')
            print_log_tail()
            raise RuntimeError('ABI fallo: ' + result.stderr.strip()[-2000:])
    elif result.stderr.strip():
        print('[advertencias ABI (no criticas):]')
        print(result.stderr.strip())


def verify_current_kernel_imports_if_needed():
    if not same_executable(PROJECT_PYTHON, sys.executable):
        print(
            f'Kernel notebook: Python {sys.version.split()[0]} ({sys.executable}). '
            f'Entrenamiento: {PROJECT_PYTHON}. No se importan paquetes del proyecto en el kernel.'
        )
        return

    modules = ('numpy', 'scipy', 'sklearn', 'pandas', 'citylearn.v3.environment')
    failures = {}
    for module_name in modules:
        try:
            importlib.import_module(module_name)
        except Exception as exc:
            failures[module_name] = repr(exc)
    if failures:
        restart_runtime(
            'El kernel actual tiene imports binarios inconsistentes: '
            f'{failures}. Esto ocurre si pip cambio numpy/scipy sin reiniciar.'
        )


if not PROJECT_ROOT.exists():
    raise FileNotFoundError(f'PROJECT_DIR no existe: {PROJECT_ROOT}. Ejecuta primero la celda 1.2.')

SETUP_LOG.write_text('', encoding='utf-8')
PROJECT_PYTHON = ensure_project_python39()
PYTHON = PROJECT_PYTHON
project_info = python_info(PROJECT_PYTHON)
if not project_info or tuple(project_info['version_info'][:2]) != PYTHON_REQUIRED:
    raise RuntimeError(f'Python de proyecto invalido: {project_info}')

os.chdir(PROJECT_DIR)
CONSTRAINTS.write_text('\n'.join(f'{p}=={v}' for p, v in PINNED.items()) + '\n')
print(f"Python proyecto: {project_info['version']} ({PROJECT_PYTHON})")
print(f"Python kernel  : {sys.version.split()[0]} ({sys.executable})")
print(f'Log setup      : {SETUP_LOG}')

# Pip compatible con gym/ray legacy del proyecto.
run([PROJECT_PYTHON, '-m', 'ensurepip', '--upgrade'], check=False)
pip_install('--force-reinstall', 'pip==21.3.1', 'setuptools==65.5.0', 'wheel==0.38.0')

pip_install('-q', *BASE_DEPS)
for package in NO_DEPS_UTILS:
    if installed_version(package.split('==')[0]) is None:
        pip_install('-q', '--no-deps', package)

ready, torch_info = torch_gpu_ready() if installed_version('torch') else (False, {})
if not ready:
    reason = torch_info.get('reason', 'missing_or_incompatible')
    print(f'[torch] Instalando PyTorch ({PYTORCH_INDEX_URL.split("/")[-1]}) — motivo: {reason}')
    pip_install('--force-reinstall', '-q', *TORCH_PACKAGES, '--index-url', PYTORCH_INDEX_URL)
    ready, torch_info = torch_gpu_ready()
if not ready:
    raise RuntimeError(
        'PyTorch no puede ejecutar kernels en esta GPU. '
        f'info={torch_info}. Blackwell (RTX PRO 6000) requiere cu128: '
        'pip install torch torchvision --index-url https://download.pytorch.org/whl/cu128'
    )

for package_dir in EDITABLES:
    pip_install('-q', '--no-deps', '-c', str(CONSTRAINTS), '-e', package_dir)

# Reinstalacion final: evita ruedas pandas/scipy compiladas para numpy 2.x.
pip_install('-q', '--force-reinstall', '--no-cache-dir', *COMPAT_WHEELS)

binary_after = {package: installed_version(package) for package in BINARY_DEPS}
print('Paquetes binarios:', binary_after)

print('\nVerificando ABI en Python 3.9 del proyecto...')
verify_subprocess_imports()
verify_current_kernel_imports_if_needed()
print('\nCelda 1.3 OK: Python 3.9 del proyecto listo y backends en modo editable.')
