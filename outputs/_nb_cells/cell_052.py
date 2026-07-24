# ── 7.3  Monitor visible en notebook ────────────────────────────────────────
# Autosuficiente: funciona aunque el kernel haya sido reiniciado.
import subprocess
import sys
import os
from pathlib import Path

_repo   = globals().get('REPO', '/content/MADRLCitytleranflexresdr')
_mon    = f'{_repo}/CityLearn/scripts/colab_a100_live_monitor.py'
_python = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))

# OUTPUT_ROOT del scope o del archivo de referencia del launcher.
# Usa el helper de 7.0 si existe; si no (kernel reiniciado), fallback autosuficiente.
if 'resolve_output_root_or_latest' in globals():
    _output_root = resolve_output_root_or_latest()
else:
    _output_root = globals().get('OUTPUT_ROOT', '')
    _ref = Path(_repo) / 'outputs' / 'latest_colab_output_root.txt'
    if not _output_root and _ref.exists():
        _output_root = _ref.read_text(encoding='utf-8').strip()

if not _output_root:
    print('[7.3] OUTPUT_ROOT no disponible. Ejecuta la celda 6.1 o espera a que el launcher escriba outputs/latest_colab_output_root.txt.')
else:
    if 'MADRL_CityLearn_v3' in _output_root:
        raise RuntimeError(
            f'OUTPUT_ROOT legacy prohibido: {_output_root}. Re-ejecuta 1.5 y 2.1.'
        )
    _guard = f'{_repo}/CityLearn/scripts/colab_protocol_guard.py'
    if Path(_guard).is_file():
        subprocess.check_call([_python, _guard, 'verify-repo', '--repo', _repo])
    result = subprocess.run(
        [_python, '-B', _mon, '--output-root', _output_root, '--once', '--log-tail', str(globals().get('LOG_TAIL', 4))],
        capture_output=True,
        text=True,
    )
    print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)
    if 'protocol=two_phase_happo_masac_v3' not in (result.stdout or ''):
        raise RuntimeError(
            'Monitor legacy (sin protocol=two_phase_happo_masac_v3). Ejecuta celda 1.2.'
        )
    for _bad in ('FASE 1: HAPPO + MATD3', 'En espera de inicio: delay=600'):
        if _bad in (result.stdout or ''):
            raise RuntimeError(f'Monitor layout 9+3 detectado: {_bad!r}')
    if result.returncode not in (0, 1):
        print(f'[7.3] Monitor salio con codigo {result.returncode}')
