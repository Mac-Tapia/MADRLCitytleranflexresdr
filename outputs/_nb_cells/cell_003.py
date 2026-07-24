# ── 0.verify  Verificar conexion al runtime (A100 en Colab; local con advertencias) ────
import subprocess
import os
import sys
import platform

MIN_VRAM_GIB = 38.0   # config conservadora 6-jobs corre desde ~40 GiB (A100-40/80, H100, RTX PRO 6000)
MIN_RAM_GIB  = 64.0   # buffers conservadores: MASAC 3x12 + MATD3 3x14 GiB en RAM (replay CPU)
# GPUs datacenter conocidas que soportan TF32 + expandable_segments (perfil 'aws').
# La validacion real es por VRAM suficiente; el nombre solo informa.
_KNOWN_GPUS = ('A100', 'H100', 'H200', 'RTX PRO 6000', 'BLACKWELL', 'A40', 'L40', 'L4')

import importlib.util
IN_COLAB = importlib.util.find_spec('google.colab') is not None

def check_connection():
    _errors = []
    _warnings = []
    gpu_mem_gib = None
    mem_gib = None

    # 1. GPU — hard fail en Colab si no A100; advertencia local
    try:
        result = subprocess.check_output(
            ['nvidia-smi', '--query-gpu=name,memory.total', '--format=csv,noheader,nounits'],
            text=True, stderr=subprocess.DEVNULL
        ).strip()
        gpu_name, gpu_mem = result.split(',')
        gpu_mem_gib = int(gpu_mem.strip()) / 1024.0
        vram_ok = gpu_mem_gib >= MIN_VRAM_GIB
        _name_known = any(k in gpu_name.upper() for k in _KNOWN_GPUS)
        gpu_ok = vram_ok  # requisito real = VRAM suficiente (cualquier GPU datacenter capaz)
        status = '[OK]' if gpu_ok else ('[WARN]' if not IN_COLAB else '[FAIL]')
        print(f"{status} GPU    : {gpu_name.strip()}  ({gpu_mem_gib:.1f} GiB VRAM)")
        if gpu_ok and not _name_known:
            print(f"     (GPU no listada pero {gpu_mem_gib:.0f} GiB VRAM >= {MIN_VRAM_GIB:.0f} -> apta; TF32 perfil 'aws')")
        if gpu_ok and any(k in gpu_name.upper() for k in ('BLACKWELL', 'RTX PRO 6000')):
            print('     [!] Blackwell sm_120: celda 1.3 instalara PyTorch cu128 (cu126 falla con no kernel image)')
        if not vram_ok:
            msg = f"VRAM insuficiente: {gpu_mem_gib:.1f} GiB < {MIN_VRAM_GIB:.0f} GiB minimos."
            if IN_COLAB:
                _errors.append(msg + " Selecciona A100/H100/RTX PRO 6000 (80 GiB) en Colab Pro+.")
            else:
                _warnings.append(msg + " Entorno local: se usara la GPU disponible o CPU.")
    except Exception as e:
        status = '[FAIL]' if IN_COLAB else '[--]'
        print(f"{status} GPU    : nvidia-smi no disponible ({e})")
        if IN_COLAB:
            _errors.append("nvidia-smi no disponible: no hay GPU o driver NVIDIA en Colab.")
        else:
            _warnings.append("nvidia-smi no disponible: entorno local sin GPU NVIDIA detectada.")

    # 2. RAM — hard fail en Colab si < 64 GiB (buffers conservadores); advertencia local
    try:
        if sys.platform.startswith('linux'):
            with open('/proc/meminfo') as f:
                for line in f:
                    if 'MemTotal' in line:
                        mem_gib = int(line.split()[1]) / (1024 * 1024)
                        ram_ok = mem_gib >= MIN_RAM_GIB
                        status = '[OK]' if ram_ok else ('[WARN]' if not IN_COLAB else '[FAIL]')
                        print(f"{status} RAM    : ~{mem_gib:.0f} GiB")
                        if not ram_ok:
                            msg = f"RAM insuficiente: {mem_gib:.0f} GiB < {MIN_RAM_GIB:.0f} GiB recomendados."
                            if IN_COLAB:
                                _errors.append(msg + " Activa 'A100 High-RAM' en Colab.")
                            else:
                                _warnings.append(msg + " MASAC puede requerir reducir replay_buffer_size.")
                        break
        else:
            import psutil
            mem_gib = psutil.virtual_memory().total / (1024**3)
            ram_ok = mem_gib >= MIN_RAM_GIB
            status = '[OK]' if ram_ok else '[WARN]'
            print(f"{status} RAM    : ~{mem_gib:.0f} GiB  (psutil, entorno local)")
    except Exception:
        print("[--] RAM    : No se pudo leer memoria del sistema")

    # 3. Python y plataforma
    print(f"[OK] Python : {sys.version.split()[0]}  ({platform.system()} {platform.machine()})")
    print(f"[OK] Entorno: {'Google Colab' if IN_COLAB else 'Local / otro'}")

    # 4. Google Drive (solo Colab)
    if IN_COLAB:
        drive_ok = os.path.exists('/content/drive/MyDrive')
        print(f"{'[OK]' if drive_ok else '[--]'} Drive  : {'montado en /content/drive/MyDrive' if drive_ok else 'no montado (ejecuta celda 1.5)'}")

    # 5. CUDA y PyTorch
    try:
        import torch
        cuda_ok = torch.cuda.is_available()
        if cuda_ok:
            print(f"[OK] CUDA   : {getattr(getattr(torch, 'version', None), 'cuda', None)}  device={torch.cuda.get_device_name(0)}")
        else:
            print("[INFO] CUDA : torch disponible pero CUDA no detectado — se usara CPU")
    except ImportError:
        print("[--] CUDA   : torch no instalado aun (normal antes de celda 1.3)")

    # ── Resultado final ──────────────────────────────────────────────────────
    for w in _warnings:
        print(f"  ⚠️  {w}")
    if _errors:
        # Diagnóstico: Pro+ puede entregar A100 Standard (~40 GiB VRAM, ~83 GiB RAM)
        _std_a100 = (
            IN_COLAB
            and gpu_mem_gib is not None and mem_gib is not None
            and gpu_mem_gib < MIN_VRAM_GIB
            and mem_gib < MIN_RAM_GIB
            and gpu_mem_gib >= 35 and mem_gib >= 75
        )
        if _std_a100:
            print()
            print("  ℹ️  Diagnóstico: estás en A100 *Standard*, no en A100 *High-RAM*.")
            print("      Detectado : ~40 GiB VRAM + ~83 GiB RAM")
            print("      Requerido : ~80 GiB VRAM + ~167 GiB RAM (MASAC buffer en CPU)")
            print("      VS Code   : Select Kernel → Colab → New Colab Server → A100 → High-RAM")
            print("      Colab web : Runtime → Cambiar tipo → A100 → activar High RAM")
            print("      Luego desconecta el runtime actual y vuelve a conectar.")
        print()
        for err in _errors:
            print(f"  ❌  {err}")
        raise RuntimeError(
            f"Pre-vuelo A100 fallo ({len(_errors)} error(es)). "
            "Corrige los problemas anteriores antes de continuar en Colab."
        )
    if IN_COLAB:
        print("\n✅  Runtime GPU + High-RAM listo para entrenamiento MADRL.")
    else:
        print("\n✅  Entorno local verificado. Advertencias anteriores son normales fuera de Colab.")

check_connection()
