# ── 1.1  Verificar entorno: IN_COLAB, GPU, CUDA, Python 3.9 ─────────────────

# ── Deteccion automatica de entorno ──────────────────────────────────────────
import importlib.util
IN_COLAB = importlib.util.find_spec('google.colab') is not None

print(f"Ejecutando en Google Colab : {IN_COLAB}")
print(f"Python version             : {sys.version.split()[0]}")
print(f"Plataforma                 : {sys.platform}")

if not sys.version_info[:2] == (3, 9):
    msg = (
        f"Python {sys.version.split()[0]} detectado; el proyecto usa Python 3.9.25. "
        "El venv .venv39-citylearn-v3 garantiza la version correcta."
    )
    if IN_COLAB:
        print(f"[WARN] {msg}")
    else:
        print(f"[INFO] {msg} (normal si el kernel de VS Code usa otra version)")

# ── GPU via nvidia-smi ───────────────────────────────────────────────────────
res = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
     "--format=csv,noheader"],
    capture_output=True, text=True,
)
if res.returncode == 0:
    print(f"GPU                        : {res.stdout.strip()}")
else:
    if IN_COLAB:
        raise RuntimeError(
            "nvidia-smi fallo. Habilita el runtime GPU A100 antes de ejecutar esta celda."
        )
    else:
        print("GPU                        : nvidia-smi no disponible — ejecuta en Colab A100-SXM4-80GB")

# ── Verificacion PyTorch + CUDA ───────────────────────────────────────────────
try:
    import torch
    cuda_ok = torch.cuda.is_available()
    print(f"PyTorch version            : {torch.__version__}")
    print(f"CUDA disponible            : {cuda_ok}")
    if cuda_ok:
        name = torch.cuda.get_device_name(0)
        mem  = torch.cuda.get_device_properties(0).total_memory / 1024**3
        vram_free = torch.cuda.mem_get_info(0)[0] / 1024**3
        print(f"Dispositivo GPU            : {name}")
        print(f"VRAM total                 : {mem:.1f} GiB")
        print(f"VRAM libre inicial         : {vram_free:.1f} GiB")
        torch.cuda.empty_cache()
        _known_gpu = any(k in name.upper() for k in ('A100','H100','H200','RTX PRO 6000','BLACKWELL','A40','L40','L4'))
        if _known_gpu or mem >= 38.0:
            print(f"[OK] {name} detectado — TF32 + expandable_segments activos")
            if mem >= 78.0:
                print(f"     {mem:.0f} GiB VRAM: holgado para 6 jobs/fase. La Seccion 6 auto-ajusta hilos a las vCPU.")
        else:
            if IN_COLAB:
                raise RuntimeError(
                    f"GPU detectada: {name} ({mem:.0f} GiB). Se requiere >=38 GiB VRAM (A100/H100/RTX PRO 6000). "
                    "Cambia el runtime: Entorno de ejecucion > Cambiar tipo > A100 / H100."
                )
            else:
                print(f"[WARN] GPU: {name} ({mem:.0f} GiB < 38). Este notebook esta optimizado para GPUs >=40 GiB.")
    else:
        if IN_COLAB:
            raise RuntimeError(
                "CUDA no disponible. Selecciona runtime A100 en Colab y vuelve a ejecutar."
            )
        else:
            print("[INFO] CUDA no disponible — se usara CPU (entorno local). El entrenamiento sera lento.")
except ImportError:
    print("[INFO] torch no disponible en kernel Python. La celda 1.3 lo instala en .venv39.")
    print("       La verificacion GPU (nvidia-smi) confirma que el hardware esta presente.")
