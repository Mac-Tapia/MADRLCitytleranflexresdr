# ── 1.5  Montar Google Drive (workspace canonico; verificacion en 2.1) ─────
import os
import sys
import shutil
import subprocess
import time
from pathlib import Path

USE_GOOGLE_DRIVE = True
REQUIRE_GOOGLE_DRIVE = True
DRIVE_MOUNT_POINT = '/content/drive'
PROJECT_NAME = globals().get('PROJECT_NAME', 'MADRLCitytleranflexresdr')
GDRIVE_ROOT = None
GDRIVE_OUTPUT_PARENT = None
CANONICAL_DRIVE_URL = 'https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX'

MIN_DRIVE_FREE_GIB = 30.0  # A100-80GB HAPPO hidden=512: checkpoints + timeseries persistentes
DRIVE_MOUNT_MAX_ATTEMPTS = 3

def _drive_mydrive_ready(mount_point=DRIVE_MOUNT_POINT):
    mydrive = f'{mount_point}/MyDrive'
    return os.path.isdir(mydrive) and os.access(mydrive, os.R_OK | os.W_OK)

def _mount_google_drive_colab(mount_point=DRIVE_MOUNT_POINT, max_attempts=DRIVE_MOUNT_MAX_ATTEMPTS):
    """Monta Drive con un solo popup OAuth (drive.mount). Cualquier cuenta Google sirve."""
    from google.colab import drive  # type: ignore[import-not-found,import-untyped]

    if _drive_mydrive_ready(mount_point):
        print(f'[OK] Google Drive ya montado en {mount_point}')
        return

    # No llamar auth.authenticate_user(): dispara un segundo OAuth efimero y rompe
    # credentials-propagation de drive.mount (400 Bad Request, authuser=0).
    last_exc = None
    for attempt in range(1, max_attempts + 1):
        force = attempt > 1 and os.path.isdir(mount_point)
        try:
            print(f'Montando Google Drive (intento {attempt}/{max_attempts}, force_remount={force})...')
            drive.mount(mount_point, force_remount=force)
            if not _drive_mydrive_ready(mount_point):
                raise RuntimeError(f'Mount OK pero {mount_point}/MyDrive no es accesible')
            print(f'[OK] Google Drive montado en {mount_point}')
            return
        except Exception as exc:
            last_exc = exc
            print(f'[WARN] Intento {attempt} fallo: {type(exc).__name__}: {exc}')
            if attempt < max_attempts:
                time.sleep(5)

    help_msg = (
        'Google Drive no se pudo montar.\n'
        '1) Acepta el popup "Permitir acceso" con la cuenta Google que prefieras\n'
        '2) Si falla: Runtime -> Disconnect and delete runtime (o Factory reset)\n'
        '3) Abre el notebook en colab.research.google.com (no solo VS Code + extension)\n'
        '4) Re-ejecuta solo la celda 1.5'
    )
    raise RuntimeError(help_msg) from last_exc

if USE_GOOGLE_DRIVE:
    try:
        _mount_google_drive_colab()
        _repo15 = Path(globals().get('REPO', '/content/MADRLCitytleranflexresdr'))
        _scripts15 = str(_repo15 / 'CityLearn' / 'scripts')
        if _scripts15 not in sys.path:
            sys.path.insert(0, _scripts15)
        import importlib as _il15
        _cm15 = _il15.import_module('citylearn_v3_training_common')
        _ctx15 = _cm15.prepare_colab_drive_mount_context(
            Path(DRIVE_MOUNT_POINT),
            project_name=PROJECT_NAME,
            repo=_repo15,
        )
        GDRIVE_ROOT = _ctx15['gdrive_root']
        GDRIVE_OUTPUT_PARENT = _ctx15['outputs_parent']
        os.makedirs(GDRIVE_OUTPUT_PARENT, exist_ok=True)
        _cm15.print_colab_drive_mount_report(_ctx15)
        print(f'[OK] Carpeta canonica: {CANONICAL_DRIVE_URL}')
        print('[INFO] 2.1 lee checkpoints en outputs/ (sin mirror ni copia).')

        # ── Verificar espacio libre en Drive ────────────────────────────────
        try:
            usage = shutil.disk_usage('/content/drive/MyDrive')
            free_gib = usage.free / (1024 ** 3)
            total_gib = usage.total / (1024 ** 3)
            if free_gib < MIN_DRIVE_FREE_GIB:
                raise RuntimeError(
                    f"Espacio insuficiente en Google Drive: {free_gib:.1f} GiB libre "
                    f"(total {total_gib:.0f} GiB). Se necesitan >= {MIN_DRIVE_FREE_GIB} GiB. "
                    "Libera espacio antes de entrenar."
                )
            print(f"[OK] Drive espacio libre: {free_gib:.1f} GiB / {total_gib:.0f} GiB")
        except RuntimeError:
            raise
        except Exception as _de:
            print(f"[WARN] No se pudo verificar espacio en Drive: {_de}")

        # ── Cuarentena clone legacy en Drive (scripts 9+3 no deben ejecutarse) ──
        _LEGACY_DRIVE_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3/MADRLCitytleranflexresdr'
        _legacy_launcher = f'{_LEGACY_DRIVE_ROOT}/CityLearn/scripts/colab_a100_official_launcher.py'
        _guard_py15 = f'{globals().get("REPO", "/content/MADRLCitytleranflexresdr")}/CityLearn/scripts/colab_protocol_guard.py'
        if os.path.isdir(_LEGACY_DRIVE_ROOT):
            print(f'[WARN] Clone legacy en Drive detectado: {_LEGACY_DRIVE_ROOT}')
            if os.path.isfile(_legacy_launcher):
                _leg_src = open(_legacy_launcher, encoding='utf-8').read()
                if (
                    'FASE 1: HAPPO + MATD3' in _leg_src
                    or 'run_two_phase_jobs' in _leg_src
                    or 'two_phase_happo_masac_v3' not in _leg_src
                ):
                    if os.path.isfile(_guard_py15):
                        subprocess.check_call(
                            [sys.executable, _guard_py15, 'quarantine-legacy-drive']
                        )
                    else:
                        raise RuntimeError(
                            'Launcher legacy 9+3 en Drive. Borra o renombra '
                            f'{_LEGACY_DRIVE_ROOT}/CityLearn/scripts antes de entrenar.'
                        )
            print('  Codigo SOLO desde /content/MADRLCitytleranflexresdr (celda 1.2).')

    except Exception as exc:
        if REQUIRE_GOOGLE_DRIVE:
            raise RuntimeError(
                'Google Drive es obligatorio para este entrenamiento largo. '
                'Sigue los pasos del mensaje anterior (cualquier cuenta Google con '
                'Colab Pro+ y espacio en Drive) y vuelve a ejecutar 1.5.'
            ) from exc
        print('Drive no disponible; usando outputs local del runtime:', exc)
        GDRIVE_ROOT = None
        GDRIVE_OUTPUT_PARENT = None