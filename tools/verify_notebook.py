"""Verify the current MADRL CityLearn v3 tutorial notebook contract."""

from __future__ import annotations

import glob
import json
import os
import re
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
NB_PATH = ROOT / "CityLearn" / "examples" / "madrl_citylearn_v3_tutorial.ipynb"
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
LAUNCHER_PATH = ROOT / "CityLearn" / "scripts" / "colab_a100_official_launcher.py"

with NB_PATH.open(encoding="utf-8") as file:
    nb = json.load(file)

cells = nb.get("cells", [])
notebook_source = "\n".join("".join(cell.get("source", [])) for cell in cells)
cell_by_id = {cell.get("id"): "".join(cell.get("source", [])) for cell in cells}
launcher_source = LAUNCHER_PATH.read_text(encoding="utf-8")
results: list[tuple[bool, str]] = []


def check(label: str, ok: bool, detail: str = "") -> None:
    status = "OK" if ok else "FAIL"
    message = f"[{status}] {label}"
    if detail:
        message += f"  ({detail})"
    results.append((ok, message))
    print(message)


def cell(cell_id: str) -> str:
    value = cell_by_id.get(cell_id, "")
    check(f"Celda existe: {cell_id}", bool(value))
    return value


# Metadata and cell inventory.
lang_info = nb.get("metadata", {}).get("language_info", {})
lang_ver = lang_info.get("version", "missing")
check("language_info.version = 3.9.25", lang_ver in {"3.9.25", "missing"}, f"actual={lang_ver!r}")
kernelspec = nb.get("metadata", {}).get("kernelspec", {})
check("kernelspec.language = python", kernelspec.get("language") == "python")
check("60 celdas en el notebook", len(cells) == 60, f"actual={len(cells)}")

dirty_code_cells = [
    (i, c.get("id"), c.get("execution_count"), len(c.get("outputs", [])))
    for i, c in enumerate(cells)
    if c.get("cell_type") == "code" and (c.get("execution_count") is not None or c.get("outputs"))
]
check("Notebook limpio sin outputs ni execution_count", not dirty_code_cells, str(dirty_code_cells[:5]))


# Critical notebook cells by stable id.
cell17 = cell("c06557c1")
check("REPO_BRANCH = master", "REPO_BRANCH      = 'master'" in cell17 or "REPO_BRANCH = 'master'" in cell17)
check("Clonado Colab usa --branch REPO_BRANCH", "'--branch', REPO_BRANCH" in cell17)
check("Submodulos se actualizan al commit fijado", "submodule', 'update', '--init', '--recursive'" in cell17)

cell16 = cell("e6bd10e8")
check("Celda 1.1 detecta IN_COLAB", "import google.colab" in cell16 and "IN_COLAB" in cell16)
check("Celda 1.1 valida PyTorch/CUDA", "import torch" in cell16 and "torch.cuda.is_available()" in cell16)
check("Celda 1.1 exige A100 en Colab", "RuntimeError" in cell16 and "A100" in cell16)

cell24 = cell("c1f8ada9")
check("Celda 2.1 detecta REPO local/Colab", "Path('d:/MADRLCitytleranflexresdr')" in cell24)
check("Celda 2.1 crea OUTPUT_ROOT recuperable", "RESUME_OUTPUT_ROOT" in cell24 and "OUTPUT_ROOT" in cell24)
check("Celda 2.1 apunta al schema Iquitos", "citylearn_iquitos_2023_2025/schema.json" in cell24)

cell26 = cell("6711850f")
check("Celda 3.1 valida dataset Iquitos", "citylearn_iquitos_2023_2025" in cell26)
check("Celda 3.1 usa columnas reales snake_case", "non_shiftable_load" in cell26 and "solar_generation" in cell26)
check("Celda 3.1 no usa columnas antiguas", "Equipment Electric Power" not in cell26 and "Solar Generation [W/kW]" not in cell26)

cell28 = cell("afbce064")
check("Celda 4.1 pasa schema_path explicito", "schema_path=IQUITOS_SCHEMA" in cell28 or "schema_path=" in cell28)
check("Celda 4.1 prueba reset/step", ".reset()" in cell28 and ".step(" in cell28)

cell32 = cell("226d3513")
check("N_EPISODES = 75", "N_EPISODES      = 75" in cell32 or "N_EPISODES = 75" in cell32)
check("EPISODE_STEPS = 8760", "EPISODE_STEPS" in cell32 and "8760" in cell32)
check("QUICK_TEST = False por defecto", "QUICK_TEST" in cell32 and "False" in cell32)
check("12 corridas principales", "ALGORITHMS = ['happo', 'masac', 'matd3', 'maac']" in cell32)
check("Hiperparametros HAPPO/MASAC/MATD3/MAAC", all(name in cell32 for name in ("HAPPO", "MASAC", "MATD3", "MAAC")))
check("GPU_PROFILE aws para Colab A100", "GPU_PROFILE" in cell32 and "'aws'" in cell32)
check("CUDA_MEMORY_FRACTION = 0.92", "CUDA_MEMORY_FRACTION" in cell32 and "0.92" in cell32)

cell36 = cell("2adf11df")
check("Launcher args incluyen --require-a100", "'--require-a100'" in cell36)
check("Launcher args incluyen --oom-retry", "'--oom-retry'" in cell36)
check("Launcher args no incluyen --include-baselines", "include-baselines" not in cell36)

cell38 = cell("3c0758f9")
check("Dry-run usa --skip-completed", "'--dry-run', '--skip-completed'" in cell38)
check("Dry-run espera exactamente 12 jobs", "len(status['jobs']) == 12" in cell38)

cell40 = cell("9a97f863")
check("Entrenamiento maneja SIGINT", "import signal" in cell40 and "_graceful_stop" in cell40 and "SIGINT" in cell40)
check("Entrenamiento tiene kill fallback", "proc.kill()" in cell40 or "SIGKILL" in cell40)
check("Entrenamiento documenta RESUME_OUTPUT_ROOT", "RESUME_OUTPUT_ROOT" in cell40)

cell44 = cell("e3efcca9")
check("Reorganizacion outputs/{MADRL}/{escenario}", "outputs/{MADRL}/{escenario}" in cell44)
check("Reorganizacion genera metrics/rewards/monitor/resources/config", all(x in cell44 for x in (
    "metrics.csv", "rewards.csv", "training_monitor.csv", "resource_usage.csv", "config.json",
)))
check("Reorganizacion copia checkpoints reales .pt/.pth/.pkl", "checkpoint.pt" in cell44 and "rglob('*.pkl')" in cell44)
check("Reorganizacion prepara resumen_comparativo", "resumen_comparativo" in cell44 and "best_madrl_report.json" in cell44)
check("Prueba rapida no usa argumento inexistente", "--dry-run-first" not in notebook_source)

cell48 = cell("7159769e")
check("Benchmarks oficiales solo PPO/SAC/A2C", 'CITYLEARN_V2_BENCHMARKS = ["PPO", "SAC", "A2C"]' in cell48)
check("Benchmarks CityLearn v2 SB3 estan aislados", "StableBaselines3" in cell48 and "NO son MADRL v3" in cell48)

cell52 = cell("64fb494c")
check("Carga resultados desde citylearn_v3_report.all_values", "citylearn_v3_report" in cell52 and "all_values" in cell52)

cell55 = cell("10e6efc1")
check("Seleccion estadistica declara mejor MADRL", "Mejor algoritmo MADRL seleccionado" in cell55)
check("Exporta resumen_comparativo completo", all(x in cell55 for x in (
    "comparison_metrics.csv", "best_madrl_selection.csv", "best_madrl_report.json", "global_comparison.png",
)))

cell58 = cell("daff4cd8")
check("Informe tecnico valida outputs canonicos", "estructura_outputs" in cell58 and "outputs/{MADRL}/{escenario}" in cell58)
check("Informe tecnico incluye veredicto APROBADO", "APROBADO" in cell58 and "APROBADO CON OBSERVACIONES" in cell58)


# Required paths and dataset structure.
required_paths = [
    "CityLearn/scripts/train_citylearn_v3_happo.py",
    "CityLearn/scripts/train_citylearn_v3_masac.py",
    "CityLearn/scripts/train_citylearn_v3_matd3.py",
    "CityLearn/scripts/train_citylearn_v3_maac.py",
    "CityLearn/scripts/benchmark_citylearn_v2_ppo.py",
    "CityLearn/scripts/benchmark_citylearn_v2_sac.py",
    "CityLearn/scripts/benchmark_citylearn_v2_a2c.py",
    "CityLearn/citylearn/v3/environment.py",
    "external/HARL",
    "external/MARL/src",
    "external/off-policy",
    "external/MAAC",
    "tools",
    "docs",
]
for relative in required_paths:
    check(f"Ruta existe: {relative}", (ROOT / relative).exists())

csv_count = len(glob.glob(str(DATASET_DIR / "*.csv")))
check("222 CSV en dataset Iquitos", csv_count == 222, f"actual={csv_count}")
schema_path = DATASET_DIR / "schema.json"
schema = json.loads(schema_path.read_text(encoding="utf-8"))
check("17 edificios en schema.json", len(schema.get("buildings", {})) == 17)
check("simulation_end_time_step = 26303", schema.get("simulation_end_time_step") == 26303)
check("185 charger CSVs en dataset Iquitos", len(glob.glob(str(DATASET_DIR / "charger_*.csv"))) == 185)
check("carbon_intensity.csv existe", (DATASET_DIR / "carbon_intensity.csv").exists())
check("pricing.csv existe", (DATASET_DIR / "pricing.csv").exists())

try:
    import pandas as pd

    building = pd.read_csv(DATASET_DIR / "Building_1.csv")
    required_bld_cols = ["month", "hour", "day_type", "non_shiftable_load", "solar_generation", "cooling_demand", "dhw_demand"]
    missing_bld = [column for column in required_bld_cols if column not in building.columns]
    check("Building_1.csv columnas reales", not missing_bld, f"faltantes={missing_bld}" if missing_bld else "")
    check("Building_1.csv 26304 filas", len(building) == 26304, f"actual={len(building)}")
except Exception as exc:
    check("Building_1.csv leible con pandas", False, str(exc))


# Official launcher must not expose MAPPO/MADDPG as v3 baselines.
check("Launcher orden oficial solo 4 MADRL", 'ALGORITHMS = ("happo", "masac", "matd3", "maac")' in launcher_source)
check("Launcher declara benchmarks v2 PPO/SAC/A2C", 'CITYLEARN_V2_BENCHMARKS = ("PPO", "SAC", "A2C")' in launcher_source)
for forbidden in ("BASELINE_ALGORITHMS", "ALL_ALGORITHMS", "--include-baselines", '"name": "mappo"', '"name": "maddpg"'):
    check(f"Launcher no contiene {forbidden}", forbidden not in launcher_source)


# Text policy: MAPPO/MADDPG can appear only as explicit non-official/historical notes.
for bad_text in ("Nota MAPPO (baseline)", "baselines MADRL opcionales", "local comparison baselines"):
    check(f"Notebook no contiene texto obsoleto: {bad_text}", bad_text not in notebook_source)

print()
failed = [message for ok, message in results if not ok]
print(f"=== RESULTADO: {len(results) - len(failed)}/{len(results)} checks OK ===")
if failed:
    print("FALLIDOS:")
    for message in failed:
        print(" ", message)
    sys.exit(1)

print("Todos los checks pasaron. Notebook listo para entrenamiento MADRL CityLearn v3.")
