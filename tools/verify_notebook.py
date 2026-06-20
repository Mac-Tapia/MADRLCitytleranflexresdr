"""Verifica integridad y correcciones del notebook madrl_citylearn_v3_tutorial.ipynb."""
import glob
import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NB_PATH = os.path.join(ROOT, "CityLearn", "examples", "madrl_citylearn_v3_tutorial.ipynb")

with open(NB_PATH, encoding="utf-8") as f:
    nb = json.load(f)

results = []


def check(label, ok, detail=""):
    status = "OK" if ok else "FAIL"
    msg = f"[{status}] {label}"
    if detail:
        msg += f"  ({detail})"
    results.append((ok, msg))
    print(msg)


# ── 1. Metadata ──────────────────────────────────────────────────────────────
lang_info = nb.get("metadata", {}).get("language_info", {})
lang_ver = lang_info.get("version", "missing")
# language_info es opcional en Colab; solo verificar si está presente
if lang_ver != "missing":
    check("language_info.version = 3.9.25", lang_ver == "3.9.25", f"actual={lang_ver!r}")
else:
    check("kernelspec presente en metadata", "kernelspec" in nb.get("metadata", {}))
kernelspec = nb.get("metadata", {}).get("kernelspec", {})
check("kernelspec.language = python", kernelspec.get("language") == "python")

# ── 2. Versiones de paquetes en celda 19 (1.3) ───────────────────────────────
cell19 = "".join(nb["cells"][19]["source"])
pz_refs = re.findall(r"pettingzoo[^\n]*", cell19)
for ref in pz_refs:
    if "pettingzoo==" in ref or ("pettingzoo': '" in ref and ref.strip().startswith("'pettingzoo'")):
        check("pettingzoo==1.12.0 en celda 1.3", "1.12.0" in ref and "1.24.1" not in ref, ref[:60])

# ── 3. Rama en celda 17 (1.2) ────────────────────────────────────────────────
cell17 = "".join(nb["cells"][17]["source"])
branch_lines = [l.strip() for l in cell17.splitlines() if "REPO_BRANCH" in l and "=" in l]
check("REPO_BRANCH = codex/fix-madrl-traceability-docs",
      any("codex/fix-madrl-traceability-docs" in l for l in branch_lines),
      str(branch_lines))

# ── 4. Total de celdas ───────────────────────────────────────────────────────
check("55 celdas en el notebook", len(nb["cells"]) == 55, f"actual={len(nb['cells'])}")

# ── 5. Rutas requeridas ──────────────────────────────────────────────────────
required = [
    "CityLearn/scripts/train_citylearn_v3_happo.py",
    "CityLearn/scripts/train_citylearn_v3_masac.py",
    "CityLearn/scripts/train_citylearn_v3_matd3.py",
    "CityLearn/scripts/train_citylearn_v3_maac.py",
    # Baseline comparison scripts (Observacion 1 corregida)
    "CityLearn/scripts/train_citylearn_v3_mappo.py",
    "CityLearn/scripts/train_citylearn_v3_maddpg.py",
    "CityLearn/citylearn/v3/environment.py",
    "external/HARL",
    "external/MARL/src",
    "external/off-policy",
    "external/MAAC",
    "CityLearn/scripts/colab_a100_official_launcher.py",
    "CityLearn/scripts/colab_a100_live_monitor.py",
    "tools",
    "docs",
]
for p in required:
    full = os.path.join(ROOT, p)
    check(f"Ruta existe: {p}", os.path.exists(full))

# ── 6. Dataset Iquitos ───────────────────────────────────────────────────────
csv_count = len(glob.glob(os.path.join(ROOT, "CityLearn/data/datasets/citylearn_iquitos_2023_2025/*.csv")))
check("222 CSV en dataset Iquitos", csv_count == 222, f"actual={csv_count}")

schema_path = os.path.join(ROOT, "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json")
with open(schema_path) as sf:
    schema = json.load(sf)
check("17 edificios en schema.json", len(schema.get("buildings", {})) == 17)
check("simulation_end_time_step = 26303", schema.get("simulation_end_time_step") == 26303)

# ── 7. venv Python 3.9 ───────────────────────────────────────────────────────
venv_python = os.path.join(ROOT, ".venv39-citylearn-v3", "Scripts", "python.exe")
if not os.path.exists(venv_python):
    venv_python = os.path.join(ROOT, ".venv39-citylearn-v3", "bin", "python")
check("venv Python 3.9 existe", os.path.exists(venv_python))

# ── 8. requirements.txt ──────────────────────────────────────────────────────
req_path = os.path.join(ROOT, "requirements.txt")
with open(req_path) as rf:
    req_content = rf.read()
check("requirements.txt pettingzoo==1.12.0", "pettingzoo==1.12.0" in req_content)
check("requirements.txt ray[rllib]==1.8.0", "ray[rllib]==1.8.0" in req_content)

# ── 9. A100 — celda 3 (0.verify): assertions VRAM y RAM ─────────────────────
cell3 = "".join(nb["cells"][3]["source"])
check("Celda 3: MIN_VRAM_GIB = 39.0 definido", "MIN_VRAM_GIB" in cell3 and "39.0" in cell3)
check("Celda 3: MIN_RAM_GIB = 60.0 definido", "MIN_RAM_GIB" in cell3 and "60.0" in cell3)
check("Celda 3: RuntimeError si GPU no es A100", "RuntimeError" in cell3)
check("Celda 3: RuntimeError si RAM insuficiente", "RAM insuficiente" in cell3)

# ── 10. Celda 16 (1.1): torch import protegido con try/except ────────────────
cell16 = "".join(nb["cells"][16]["source"])
check("Celda 16: import torch en try/except", "try:" in cell16 and "import torch" in cell16)
check("Celda 16: RuntimeError si no A100", "RuntimeError" in cell16)

# ── 11. Celda 22 (1.5): check espacio Drive ──────────────────────────────────
cell22 = "".join(nb["cells"][22]["source"])
check("Celda 22: MIN_DRIVE_FREE_GIB definido", "MIN_DRIVE_FREE_GIB" in cell22)
check("Celda 22: shutil.disk_usage para check espacio", "disk_usage" in cell22)
check("Celda 22: RuntimeError si espacio insuficiente", "Espacio insuficiente en Google Drive" in cell22)

# ── 12. Celda 32 (6.1): GPU_PROFILE='aws' con comentario, OUTPUT_ROOT guard ──
cell32 = "".join(nb["cells"][32]["source"])
check("Celda 32: GPU_PROFILE = 'aws'", "GPU_PROFILE" in cell32 and "'aws'" in cell32)
check("Celda 32: comentario explica 'aws' para Colab A100", "Colab A100" in cell32 or "colab A100" in cell32)
check("Celda 32: guard OUTPUT_ROOT not in globals()", "OUTPUT_ROOT" in cell32 and "not in globals()" in cell32)
check("Celda 32: CUDA_MEMORY_FRACTION = 0.92", "0.92" in cell32)

# ── 13. Celda 38 (7.2): signal handling robusto ──────────────────────────────
cell38 = "".join(nb["cells"][38]["source"])
check("Celda 38: import signal", "import signal" in cell38 or "import _signal" in cell38 or "_signal" in cell38)
check("Celda 38: _graceful_stop con SIGINT", "_graceful_stop" in cell38 and "SIGINT" in cell38)
check("Celda 38: timeout SIGKILL fallback", "SIGKILL" in cell38 or "proc.kill()" in cell38)
check("Celda 38: instrucciones RESUME en KeyboardInterrupt", "RESUME_OUTPUT_ROOT" in cell38)

# ── 14. Parametros A100 en celda 32 ──────────────────────────────────────────
check("Celda 32: EPISODES = 75 (modo full)", "EPISODES" in cell32 and "75" in cell32)
check("Celda 32: EPISODE_STEPS = 8760", "8760" in cell32)
check("Celda 32: QUICK_TEST = False por defecto", "QUICK_TEST" in cell32 and "False" in cell32)

# ── 15. Launcher args en celda 34 (7.0): --require-a100 activo ───────────────
cell34 = "".join(nb["cells"][34]["source"])
check("Celda 34: --require-a100 en launcher args", "'--require-a100'" in cell34)
check("Celda 34: --oom-retry activo", "'--oom-retry'" in cell34)
cell38_check = "".join(nb["cells"][38]["source"])
check("Celda 38: --skip-completed en launch args", "skip-completed" in cell38_check or "skip_completed" in cell38_check)

print()
failed = [m for ok, m in results if not ok]
print(f"=== RESULTADO: {len(results) - len(failed)}/{len(results)} checks OK ===")
if failed:
    print("FALLIDOS:")
    for m in failed:
        print(" ", m)
    sys.exit(1)
else:
    print("Todos los checks pasaron. Notebook listo para A100.")
