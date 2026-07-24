# ── 2.2  Rescate HAPPO (opcional) ───────────────────────────────────────────
import json
import subprocess
import sys
from pathlib import Path

RESCUE_MODE = 'skip'  # 'skip' | 'rescue' | 'inject'
FAILED_OUTPUT_ROOT = None  # ej. '/content/drive/.../outputs/madrl_v3_20260624_175429'
HAPPO_RESCUE_ARCHIVE = None  # default: outputs/rescued_happo_<run_name>

if 'OUTPUT_ROOT' not in globals():
    raise RuntimeError('Ejecuta celda 2.1 antes de 2.2.')

_repo = Path(globals().get('REPO', Path.cwd()))
_script = _repo / 'CityLearn' / 'scripts' / 'colab_rescue_happo_checkpoints.py'
if not _script.is_file():
    raise FileNotFoundError(f'No se encuentra {_script}. Ejecuta celda 1.2 (git sync).')

_py = globals().get('PYTHON', sys.executable)

if RESCUE_MODE == 'skip':
    print('[2.2] RESCUE_MODE=skip — sin rescate HAPPO.')
elif RESCUE_MODE == 'rescue':
    if not FAILED_OUTPUT_ROOT:
        raise ValueError('Define FAILED_OUTPUT_ROOT con el OUTPUT_ROOT del run fallido.')
    cmd = [_py, '-B', str(_script), 'rescue', '--source-run', str(FAILED_OUTPUT_ROOT)]
    if HAPPO_RESCUE_ARCHIVE:
        cmd.extend(['--dest', str(HAPPO_RESCUE_ARCHIVE)])
    print('[2.2] rescue:', ' '.join(cmd))
    subprocess.run(cmd, check=True, cwd=str(_repo))
    _archive = Path(HAPPO_RESCUE_ARCHIVE) if HAPPO_RESCUE_ARCHIVE else _repo / 'outputs' / f"rescued_happo_{Path(FAILED_OUTPUT_ROOT).name.replace('madrl_v3_', '')}"
    _manifest = _archive / 'rescue_manifest.json'
    if _manifest.is_file():
        print(json.dumps(json.loads(_manifest.read_text(encoding='utf-8')), indent=2)[:2000])
    print(f'[2.2] Archive: {_archive}')
elif RESCUE_MODE == 'inject':
    if not HAPPO_RESCUE_ARCHIVE:
        raise ValueError('Define HAPPO_RESCUE_ARCHIVE (directorio del rescate).')
    cmd = [_py, '-B', str(_script), 'inject', '--archive', str(HAPPO_RESCUE_ARCHIVE), '--target-run', str(OUTPUT_ROOT)]
    print('[2.2] inject:', ' '.join(cmd))
    subprocess.run(cmd, check=True, cwd=str(_repo))
    print(f'[2.2] HAPPO inyectado en {OUTPUT_ROOT}. Continua con 6.1 -> 7.2.')
else:
    raise ValueError(f'RESCUE_MODE invalido: {RESCUE_MODE!r}')