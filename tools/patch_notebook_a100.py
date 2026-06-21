"""Aplica parches de robustez A100 al notebook madrl_citylearn_v3_tutorial.ipynb."""
import json
import sys

NB_PATH = "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb"

with open(NB_PATH, encoding="utf-8") as f:
    nb = json.load(f)

cells = nb["cells"]
changes = []


def set_cell_source(idx, new_source):
    lines = new_source.splitlines()
    source_list = [line + "\n" for line in lines]
    if source_list:
        source_list[-1] = source_list[-1].rstrip("\n")
    cells[idx]["source"] = source_list
    changes.append(f"Cell {idx} ({cells[idx]['cell_type']}): updated")


# ═══════════════════════════════════════════════════════════════════════════
# PARCHE 1 — Celda 3 (0.verify): assertions VRAM>=39GB y RAM>=60GB
# ═══════════════════════════════════════════════════════════════════════════
CELL3_NEW = r"""# ── 0.verify  Verificar conexion al runtime A100 ───────────────────────────
import subprocess, os, sys, platform

MIN_VRAM_GIB = 39.0   # A100 40GB PCIe minimo aceptable
MIN_RAM_GIB  = 60.0   # Colab A100 High-RAM; MASAC usa hasta 20 GiB en host RAM

def check_connection():
    _errors = []

    # 1. GPU — hard fail si VRAM < 39 GiB o no es A100
    try:
        result = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        gpu_name, gpu_mem = result.split(',')
        gpu_mem_gib = int(gpu_mem.strip()) / 1024.0
        gpu_ok = 'A100' in gpu_name
        vram_ok = gpu_mem_gib >= MIN_VRAM_GIB
        print(f"{'[OK]' if (gpu_ok and vram_ok) else '[FAIL]'} GPU    : {gpu_name.strip()}  ({gpu_mem_gib:.1f} GiB VRAM)")
        if not gpu_ok:
            _errors.append(
                f"GPU no es A100 (detectado: {gpu_name.strip()}). "
                "Colab: Runtime > Cambiar tipo de entorno de ejecucion > A100."
            )
        if not vram_ok:
            _errors.append(
                f"VRAM insuficiente: {gpu_mem_gib:.1f} GiB < {MIN_VRAM_GIB} GiB requeridos. "
                "Selecciona A100 (40 GB o 80 GB)."
            )
    except Exception as e:
        print(f"[FAIL] GPU    : nvidia-smi no disponible ({e})")
        _errors.append("nvidia-smi no disponible: no hay GPU o driver NVIDIA.")

    # 2. RAM — hard fail si < 60 GiB (MASAC requiere High-RAM para buffer 20 GiB)
    try:
        with open('/proc/meminfo') as f:
            for line in f:
                if 'MemTotal' in line:
                    mem_gib = int(line.split()[1]) / (1024 * 1024)
                    ram_ok = mem_gib >= MIN_RAM_GIB
                    print(f"{'[OK]' if ram_ok else '[FAIL]'} RAM    : ~{mem_gib:.0f} GiB")
                    if not ram_ok:
                        _errors.append(
                            f"RAM insuficiente: {mem_gib:.0f} GiB < {MIN_RAM_GIB:.0f} GiB requeridos. "
                            "Activa 'A100 High-RAM' en Colab: Runtime > Cambiar tipo > A100 con RAM alta."
                        )
                    break
    except Exception:
        print("[--] RAM    : /proc/meminfo no disponible (no Colab)")

    # 3. Python & runtime
    print(f"[OK] Python : {sys.version.split()[0]}  ({platform.system()} {platform.machine()})")

    # 4. Google Drive
    drive_ok = os.path.exists('/content/drive/MyDrive')
    print(f"{'[OK]' if drive_ok else '[--]'} Drive  : {'montado en /content/drive/MyDrive' if drive_ok else 'no montado (ejecuta celda 1.5)'}")

    # 5. Colab environment
    try:
        import google.colab
        print("[OK] Entorno: Google Colab")
    except ImportError:
        print("[INFO] Entorno: NO es Colab (kernel local u otro)")

    # 6. CUDA
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        if cuda_ok:
            print(f"[OK] CUDA   : {torch.version.cuda}  device={torch.cuda.get_device_name(0)}")
        else:
            print("[WARN] CUDA  : torch disponible pero CUDA no detectado")
    except ImportError:
        print("[--] CUDA   : torch no instalado aun (normal antes de celda 1.3)")

    # ── Resultado final ──────────────────────────────────────────────────────
    if _errors:
        print()
        for err in _errors:
            print(f"  ❌  {err}")
        raise RuntimeError(
            f"Pre-vuelo A100 fallo ({len(_errors)} error(es)). "
            "Corrige los problemas anteriores antes de continuar."
        )
    print("\n✅  Runtime A100 High-RAM listo para entrenamiento MADRL.")

check_connection()
"""

set_cell_source(3, CELL3_NEW)

# ═══════════════════════════════════════════════════════════════════════════
# PARCHE 2 — Celda 16 (1.1): wrap torch import en try/except
# ═══════════════════════════════════════════════════════════════════════════
CELL16_NEW = r"""# ── 1.1  Verificar GPU ──────────────────────────────────────────────────────
# Nota: este check usa el Python del kernel (puede ser 3.11).
# La verificación del torch del entrenamiento (PROJECT_PYTHON / .venv39)
# se realiza en la celda 1.4 con smoke imports en subproceso.
import subprocess, os, sys

res = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
     "--format=csv,noheader"],
    capture_output=True, text=True,
)
print("GPU:", res.stdout.strip() or "[nvidia-smi sin salida — asegura runtime GPU]")
if res.returncode != 0:
    raise RuntimeError(
        "nvidia-smi fallo. Habilita el runtime GPU A100 antes de ejecutar esta celda."
    )

try:
    import torch
    cuda_ok = torch.cuda.is_available()
    print(f"PyTorch (kernel) {torch.__version__}  |  CUDA disponible: {cuda_ok}")
    if cuda_ok:
        name = torch.cuda.get_device_name(0)
        mem  = torch.cuda.get_device_properties(0).total_memory / 1024**3
        print(f"Dispositivo: {name}  |  VRAM: {mem:.1f} GiB")
        if "A100" in name:
            print("✅ A100 detectado — parametros A100 activos")
        else:
            raise RuntimeError(
                f"GPU detectada: {name}. Se requiere A100. "
                "Cambia el runtime: Entorno de ejecucion > Cambiar tipo > A100."
            )
    else:
        raise RuntimeError(
            "CUDA no disponible para el torch del kernel. "
            "Selecciona runtime A100 en Colab y vuelve a ejecutar."
        )
except ImportError:
    # torch no instalado en el kernel — normal si Colab no lo incluye aun.
    # La celda 1.3 instala torch en PROJECT_PYTHON (.venv39-citylearn-v3).
    print("[INFO] torch no disponible en kernel Python. La celda 1.3 lo instala en .venv39.")
    print("       La verificacion GPU (nvidia-smi) confirma que el hardware A100 esta presente.")
"""

set_cell_source(16, CELL16_NEW)

# ═══════════════════════════════════════════════════════════════════════════
# PARCHE 3 — Celda 22 (1.5): check espacio libre en Drive post-mount
# ═══════════════════════════════════════════════════════════════════════════
CELL22_NEW = r"""# ── 1.5  Montar Google Drive para checkpoints y reanudacion ─────────────────
import os, shutil

USE_GOOGLE_DRIVE = True
REQUIRE_GOOGLE_DRIVE = True
DRIVE_WORKSPACE_ROOT = '/content/drive/MyDrive/MADRL_CityLearn_v3'
PROJECT_NAME = globals().get('PROJECT_NAME', 'MADRLCitytleranflexresdr')
GDRIVE_ROOT = None
GDRIVE_OUTPUT_PARENT = None

MIN_DRIVE_FREE_GIB = 15.0  # artefactos ~10-12 GiB para 12 corridas completas

if USE_GOOGLE_DRIVE:
    try:
        from google.colab import drive
        drive.mount('/content/drive', force_remount=False)
        GDRIVE_ROOT = f'{DRIVE_WORKSPACE_ROOT}/{PROJECT_NAME}'
        GDRIVE_OUTPUT_PARENT = f'{GDRIVE_ROOT}/outputs'
        os.makedirs(GDRIVE_OUTPUT_PARENT, exist_ok=True)
        print('Google Drive montado:', GDRIVE_ROOT)
        print('Outputs del entrenamiento:', GDRIVE_OUTPUT_PARENT)

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

    except Exception as exc:
        if REQUIRE_GOOGLE_DRIVE:
            raise RuntimeError(
                'Google Drive es obligatorio para este entrenamiento largo. '
                'Conecta Colab con tu cuenta de Google y vuelve a ejecutar 1.5.'
            ) from exc
        print('Drive no disponible; usando outputs local del runtime:', exc)
        GDRIVE_ROOT = None
        GDRIVE_OUTPUT_PARENT = None
"""

set_cell_source(22, CELL22_NEW)

# ═══════════════════════════════════════════════════════════════════════════
# PARCHE 4 — Celda 32 (6.1): comentar GPU_PROFILE y QUICK_TEST
# ═══════════════════════════════════════════════════════════════════════════
CELL32_NEW = r"""# ── 6.1  Configuracion central de entrenamiento A100 ───────────────────────
import os, sys, subprocess, json, time
from pathlib import Path

REPO        = '/content/MADRLCitytleranflexresdr'
PYTHON      = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
SCHEMA_PATH = f'{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json'
LAUNCHER    = f'{REPO}/CityLearn/scripts/colab_a100_official_launcher.py'
MONITOR     = f'{REPO}/CityLearn/scripts/colab_a100_live_monitor.py'

# ── QUICK_TEST ────────────────────────────────────────────────────────────
# False  → entrenamiento oficial completo ajustado (50 episodios, HAPPO ~11 FPS objetivo).
# True   → prueba de infraestructura rapida (3 episodios, ~15 min).
#          Util para verificar que el pipeline funciona antes del run largo.
QUICK_TEST      = False
EPISODES        = 3 if QUICK_TEST else 50
EPISODE_STEPS   = 8760
NUM_ENV_STEPS   = EPISODES * EPISODE_STEPS
SEED            = 0

# ── Parametros de rendimiento A100 ───────────────────────────────────────
TORCH_THREADS        = 2    # 2 hilos CPU: la GPU es el cuello; mas hilos => mas contension RAM
LIVE_PROGRESS_INT    = 1000 # snapshot de progreso cada 1000 pasos
LIVE_HEARTBEAT_SEC   = 30   # log heartbeat cada 30 s (visible en salida del launcher)
ARTIFACT_PROFILE     = 'efficient'  # 'efficient' guarda results.json + timeseries + checkpoints
TRACE_INTERVAL       = 24   # tracing de observaciones cada 24 pasos horarios (= 1 dia)
TRACE_DETAIL         = 'compact'

# GPU_PROFILE: 'aws' es el perfil correcto para Colab A100 (80 GiB VRAM).
# El launcher no tiene perfil 'colab' separado; 'aws' aplica los mismos
# parametros de memoria TF32 + expandable_segments que un A100 EC2.
GPU_PROFILE          = 'aws'
CUDA_MEMORY_FRACTION = 0.92  # reserva 92% de VRAM (~73.6 GiB en A100-80GB)

SCENARIOS  = ['E1', 'E2', 'E3']
ALGORITHMS = ['happo', 'masac', 'matd3', 'maac']

# ── Validar que OUTPUT_ROOT ya esta configurado (celda 2.1) ─────────────
if 'OUTPUT_ROOT' not in globals():
    raise RuntimeError(
        "OUTPUT_ROOT no definido. Ejecuta las celdas 1.x y 2.1 en orden antes de 6.1."
    )

mode = 'QUICK_TEST (3 ep)' if QUICK_TEST else 'FULL TRAINING (50 ep)'
print(f'Modo          : {mode}')
print(f'Episodios     : {EPISODES} x {EPISODE_STEPS} pasos = {NUM_ENV_STEPS:,} pasos/corrida')
print(f'Corridas total: {len(SCENARIOS) * len(ALGORITHMS)} ({len(ALGORITHMS)} algos x {len(SCENARIOS)} escenarios)')
print(f'GPU profile   : {GPU_PROFILE} (A100 TF32 + expandable_segments)')
print(f'CUDA fraccion : {CUDA_MEMORY_FRACTION} ({CUDA_MEMORY_FRACTION*80:.0f} GiB reservados en A100-80GB)')
print(f'Output root   : {OUTPUT_ROOT}')
print(f'Launcher      : {LAUNCHER}')
"""

set_cell_source(32, CELL32_NEW)

# ═══════════════════════════════════════════════════════════════════════════
# PARCHE 5 — Celda 38 (7.2): corregir signal handling en KeyboardInterrupt
# ═══════════════════════════════════════════════════════════════════════════
CELL38_NEW = r"""# ── 7.2  Lanzar entrenamiento + monitor en paralelo ─────────────────────────
# Usa Popen (no blocking) + bucle de monitoreo: mientras el launcher
# entrena, esta celda muestra snapshots de progreso cada 60 s.
# Si un job falla, imprime diagnostico S1-S3 con instrucciones de relaunch.
LAUNCH_FULL_TRAINING = True

if not LAUNCH_FULL_TRAINING:
    print('LAUNCH_FULL_TRAINING=False — cambia a True para entrenar.')
else:
    import signal as _signal
    import subprocess, sys, time, json as _json
    from pathlib import Path as _P
    from datetime import datetime as _DT, timezone as _TZ

    _repo    = '/content/MADRLCitytleranflexresdr'
    _mon     = f'{_repo}/CityLearn/scripts/colab_a100_live_monitor.py'
    _python  = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
    _mon_interval = 60          # segundos entre snapshots del monitor
    _poll_sleep   = 5           # segundos entre polls al proceso

    train_cmd = launcher_base_args() + ['--skip-completed']
    print('\n' + '=' * 80)
    print(' '.join(str(c) for c in train_cmd))
    print('=' * 80)

    # Lanzar entrenamiento SIN bloquear (Popen)
    proc = subprocess.Popen(
        train_cmd,
        cwd=_repo,
        stdout=None,    # hereda stdout del kernel -> aparece en esta celda
        stderr=None,    # hereda stderr del kernel
        text=True,
    )

    def _graceful_stop(proc, timeout_sigint=30, timeout_sigkill=10):
        # Detiene el proceso graciosamente: SIGINT -> espera -> SIGKILL.
        if proc.poll() is not None:
            return
        print('\n[7.2] Enviando SIGINT al launcher (checkpoints seran guardados)...')
        try:
            proc.send_signal(_signal.SIGINT)
        except Exception:
            pass
        try:
            proc.wait(timeout=timeout_sigint)
            print(f'[7.2] Launcher detenido (SIGINT) tras {timeout_sigint}s.')
            return
        except subprocess.TimeoutExpired:
            pass
        print(f'[7.2] SIGINT sin respuesta tras {timeout_sigint}s, enviando SIGKILL...')
        try:
            proc.kill()
            proc.wait(timeout=timeout_sigkill)
        except Exception:
            pass

    _last_mon = 0.0
    try:
        while proc.poll() is None:
            _now = time.time()
            if _now - _last_mon >= _mon_interval:
                # ── Monitor snapshot ────────────────────────────────────────
                _ref = _P(_repo) / 'outputs' / 'latest_colab_output_root.txt'
                _out = globals().get('OUTPUT_ROOT', '') or (
                    _ref.read_text(encoding='utf-8').strip()
                    if _ref.exists() else ''
                )
                if _out:
                    try:
                        subprocess.run(
                            [_python, '-B', _mon,
                             '--output-root', _out,
                             '--once', '--log-tail', '12'],
                            text=True,
                        )
                    except Exception as _em:
                        print(f'[monitor] error: {_em}')
                _last_mon = _now
            time.sleep(_poll_sleep)
    except KeyboardInterrupt:
        print('\n[7.2] Interrumpido — guardando checkpoints antes de detener...')
        _graceful_stop(proc)
        print('[7.2] Para reanudar: en celda 2.1 define RESUME_OUTPUT_ROOT y re-ejecuta 7.2.')
        raise

    _exit = int(proc.returncode or 0)
    if _exit == 0:
        print('\nEntrenamiento COMPLETADO — procede con celda 7.4 / Seccion 8.')
    else:
        # ── Diagnostico automatico al fallar ─────────────────────────────
        print(f'\n[7.2] FALLO (exit={_exit}) — Diagnostico automatico:\n')
        _ref = _P(_repo) / 'outputs' / 'latest_colab_output_root.txt'
        _out = globals().get('OUTPUT_ROOT', '') or (
            _ref.read_text(encoding='utf-8').strip() if _ref.exists() else ''
        )
        if not _out:
            print('  OUTPUT_ROOT desconocido — ejecuta celda 2.1 y reintenta.')
        else:
            # S1 — estado de jobs
            _sp = _P(_out) / 'official_full_status.json'
            if not _sp.exists():
                print(f'  [S1] official_full_status.json NO EXISTE en:\n  {_out}')
            else:
                _s    = _json.loads(_sp.read_text())
                _jobs = _s.get('jobs', [])
                _done = [j for j in _jobs
                         if j.get('exit_code') == 0 and not j.get('skipped')]
                _fail = [j for j in _jobs
                         if j.get('exit_code') not in (None, 0)
                         and not j.get('skipped')]
                print(f'  [S1] status="{_s.get("status")}"  '
                      f'OK={len(_done)}/12  FAIL={len(_fail)}')
                for _j in _jobs:
                    if _j.get('planned_only'):
                        continue
                    if _j.get('skipped'):
                        _st = 'SKIP'
                    elif _j.get('exit_code') == 0:
                        _st = 'OK  '
                    elif _j.get('completed_at') is None:
                        _st = 'RUN '
                    else:
                        _st = 'FAIL'
                    print(f'    {_j.get("name","?").upper():<6}'
                          f' {_j.get("scenario","?"):<3} -> {_st}'
                          f'  attempt={_j.get("attempt",0)}')

            # S2 — live_progress reciente
            _pf = sorted(_P(_out).rglob('live_progress.json'))
            if _pf:
                try:
                    _pg  = _json.loads(_pf[-1].read_text())
                    _ts  = _pg.get('live_status_updated_at', '')
                    _lag = (
                        (_DT.now(_TZ.utc) -
                         _DT.fromisoformat(_ts.replace('Z', '+00:00'))
                         ).total_seconds() if _ts else None
                    )
                    _sig = ('ACTIVO' if _lag is not None and _lag < 120
                            else f'COLGADO ({_lag:.0f}s)' if _lag else '?')
                    print(f'  [S2] {_sig}  '
                          f'{_pg.get("algorithm","?")}/'
                          f'{_pg.get("scenario","?")} '
                          f'ep={_pg.get("episode","?")} '
                          f'step={_pg.get("global_step","?")}')
                except Exception as _e2:
                    print(f'  [S2] live_progress ilegible: {_e2}')

            # S3 — stderr con errores
            _errs = [(p, p.read_text(errors='replace'))
                     for p in sorted(_P(_out).glob('logs/*.stderr.log'))
                     if p.stat().st_size > 0]
            if _errs:
                print(f'  [S3] {len(_errs)} stderr con errores:')
                for _ep, _et in _errs:
                    print(f'    === {_ep.name} ===')
                    print('    ' + '\n    '.join(_et.strip().splitlines()[-20:]))
            else:
                print('  [S3] Sin errores stderr')

            print()
            print('  RELAUNCH: En celda 2.1 establece:')
            print(f'    RESUME_OUTPUT_ROOT = "{_out}"')
            print('  Luego: 1.x setup -> 2.1 -> 6.1 -> 7.2')
        raise RuntimeError(f'Entrenamiento fallo con exit={_exit}')
"""

set_cell_source(38, CELL38_NEW)

# ═══════════════════════════════════════════════════════════════════════════
# Escribir notebook modificado
# ═══════════════════════════════════════════════════════════════════════════
with open(NB_PATH, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)
    f.write("\n")

print()
for msg in changes:
    print(" ", msg)
print(f"\nTotal cambios: {len(changes)}")
print("Notebook escrito OK.")
