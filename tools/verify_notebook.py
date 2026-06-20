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


# 1. Kernel metadata
lang_ver = nb["metadata"]["language_info"]["version"]
check("language_info.version = 3.9.25", lang_ver == "3.9.25", f"actual={lang_ver!r}")

# 2. pettingzoo en celda 19
cell19 = "".join(nb["cells"][19]["source"])
pz_refs = re.findall(r"pettingzoo[^\n]*", cell19)
for ref in pz_refs:
    # Solo verificar líneas que fijan la versión (PINNED dict o pip spec), no el dict de módulos
    if "pettingzoo==" in ref or ("pettingzoo': '" in ref and ref.strip().startswith("'pettingzoo'")):
        check(f"pettingzoo version 1.12.0 en: {ref[:50]}", "1.12.0" in ref and "1.24.1" not in ref)

# 3. Rama en celda 17
cell17 = "".join(nb["cells"][17]["source"])
branch_lines = [l.strip() for l in cell17.splitlines() if "REPO_BRANCH" in l and "=" in l]
check("REPO_BRANCH definida en celda 17", bool(branch_lines), str(branch_lines))
if branch_lines:
    check("REPO_BRANCH = codex/fix-madrl-traceability-docs",
          "codex/fix-madrl-traceability-docs" in branch_lines[0])

# 4. Total celdas
check("51 celdas en el notebook", len(nb["cells"]) == 51, f"actual={len(nb['cells'])}")

# 5. Rutas requeridas
required = [
    "CityLearn/scripts/train_citylearn_v3_happo.py",
    "CityLearn/scripts/train_citylearn_v3_masac.py",
    "CityLearn/scripts/train_citylearn_v3_matd3.py",
    "CityLearn/scripts/train_citylearn_v3_maac.py",
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

# 6. Dataset
csv_count = len(glob.glob(os.path.join(ROOT, "CityLearn/data/datasets/citylearn_iquitos_2023_2025/*.csv")))
check("222 CSV en dataset Iquitos", csv_count == 222, f"actual={csv_count}")

schema_path = os.path.join(ROOT, "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json")
with open(schema_path) as sf:
    schema = json.load(sf)
check("17 edificios en schema.json", len(schema.get("buildings", {})) == 17)
check("simulation_end_time_step = 26303", schema.get("simulation_end_time_step") == 26303)

# 7. venv Python 3.9
venv_python = os.path.join(ROOT, ".venv39-citylearn-v3", "Scripts", "python.exe")
if not os.path.exists(venv_python):
    venv_python = os.path.join(ROOT, ".venv39-citylearn-v3", "bin", "python")
check("venv Python 3.9 existe", os.path.exists(venv_python), venv_python)

# 8. requirements.txt pettingzoo==1.12.0
req_path = os.path.join(ROOT, "requirements.txt")
with open(req_path) as rf:
    req_content = rf.read()
check("requirements.txt pettingzoo==1.12.0", "pettingzoo==1.12.0" in req_content)
check("requirements.txt ray[rllib]==1.8.0", "ray[rllib]==1.8.0" in req_content)

print()
failed = [m for ok, m in results if not ok]
print(f"=== RESULTADO: {len(results) - len(failed)}/{len(results)} checks OK ===")
if failed:
    print("FALLIDOS:")
    for m in failed:
        print(" ", m)
    sys.exit(1)
else:
    print("Todos los checks pasaron.")
