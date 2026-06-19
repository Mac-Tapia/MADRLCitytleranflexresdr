"""Generate madrl_citylearn_v3_tutorial.ipynb — Colab A100, 75 episodios.

Parámetros base: corrida oficial v4 (run_aws_training.sh build_command).
Ajustes A100: mayor batch/buffer donde es seguro sin riesgo OOM.
Layout de salida: algorithm-first  →  {OUTPUT_ROOT}/{algorithm}/{scenario}_seed_0/
(idéntico al lanzador oficial).
"""
import json
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def md(source: str):
    return {"cell_type": "markdown", "metadata": {}, "source": [source]}


def code(source: str, tags=None):
    meta = {"tags": tags} if tags else {}
    return {
        "cell_type": "code",
        "execution_count": None,
        "metadata": meta,
        "outputs": [],
        "source": [source],
    }


cells = []

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 0 — PORTADA
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("""\
# MADRL CityLearn v3 — Tutorial Completo (Google Colab · A100)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Mac-Tapia/MADRLCitytleranflexresdr/blob/master/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb)

**Proyecto:** Multi-Agente de Aprendizaje por Refuerzo Profundo para gestión coordinada
de flexibilidad energética, emisiones de CO₂ y eficiencia económica en comunidades inteligentes.

**Caso de estudio:** 17 edificios reales de Iquitos, Perú · Dataset 2023-2025 · 26 304 pasos horarios.

| Parámetro | Valor |
|---|---|
| Algoritmos | HAPPO · MASAC · MATD3 · MAAC |
| Escenarios | E1 (Flexibilidad) · E2 (CO₂) · E3 (Costos) |
| Episodios | 75 por corrida · 8 760 pasos/episodio |
| Total steps | 657 000 por corrida · 7 884 000 en total |
| GPU objetivo | A100 40 GB (Colab Pro/Pro+) |
| Resultado v4 | **MATD3** es el mejor MADRL global (KW p=0.0459) |

> **Requisito:** Seleccionar A100 en *Runtime → Change runtime type → A100 GPU*
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 1 — SETUP
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("## Sección 1: Configuración inicial"))

# 1.1 GPU check
cells.append(code("""\
# ── 1.1  Verificar GPU ──────────────────────────────────────────────────────
import subprocess, os, sys

res = subprocess.run(
    ["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
     "--format=csv,noheader"],
    capture_output=True, text=True,
)
print("GPU:", res.stdout.strip())

import torch
print(f"PyTorch {torch.__version__}  |  CUDA disponible: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    name = torch.cuda.get_device_name(0)
    mem  = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"Dispositivo: {name}  |  VRAM: {mem:.1f} GiB")
    if "A100" in name:
        print("✅ A100 detectado — parámetros A100 activos")
    else:
        print(f"⚠️  GPU detectada: {name} — parámetros A100 pueden ser excesivos")
else:
    raise RuntimeError("❌ No hay GPU disponible. Habilita la GPU A100 en Runtime settings.")
"""))

# 1.2 Clone repo
cells.append(code("""\
# ── 1.2  Clonar repositorio con submódulos ──────────────────────────────────
REPO_URL = "https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git"
REPO     = "/content/MADRLCitytleranflexresdr"

if not os.path.exists(f"{REPO}/.git"):
    print("Clonando repositorio (incluye submódulos externos)…")
    !git clone --recurse-submodules --depth 1 {REPO_URL} {REPO}
else:
    print("Repositorio ya existe — actualizando submódulos…")
    !cd {REPO} && git submodule update --init --recursive

os.chdir(REPO)
print(f"\\nDirectorio de trabajo: {os.getcwd()}")
"""))

# 1.3 Install deps
cells.append(code("""\
# ── 1.3  Instalar dependencias del proyecto ─────────────────────────────────
# CityLearn base (v2) + extensiones v3 propuestas
!pip install -e CityLearn/ -q

# Backends MADRL externos (cada uno con su propio setup.py)
!pip install -e external/HARL/      -q   # HAPPO  — on-policy, trust region secuencial
!pip install -e external/MARL/src/  -q   # MASAC  — Q-mix + SAC discreto
!pip install -e external/off-policy/ -q  # MATD3  — twin-critic TD3 off-policy
!pip install -e external/MAAC/      -q   # MAAC   — attention critic SAC

# Análisis estadístico y visualización
!pip install scipy pandas matplotlib seaborn -q

print("\\n✅ Dependencias instaladas.")
"""))

# 1.4 Python path
cells.append(code("""\
# ── 1.4  Configurar sys.path y variables de entorno ─────────────────────────
import sys, os

REPO = "/content/MADRLCitytleranflexresdr"
_paths = [
    REPO,
    f"{REPO}/CityLearn",
    f"{REPO}/CityLearn/scripts",
    f"{REPO}/external/HARL",
    f"{REPO}/external/MARL/src",
    f"{REPO}/external/off-policy",
    f"{REPO}/external/MAAC",
    f"{REPO}/uc3m",
]
for p in _paths:
    if p not in sys.path:
        sys.path.insert(0, p)

os.environ["PYTHONPATH"]             = ":".join(_paths)
os.environ["CITYLEARN_PROJECT_ROOT"] = REPO

print("sys.path configurado  ✅")
print("CITYLEARN_PROJECT_ROOT:", os.environ["CITYLEARN_PROJECT_ROOT"])
"""))

# 1.5 Optional GDrive
cells.append(md("""\
### (Opcional) Montar Google Drive

Si quieres persistencia entre sesiones, descomenta y ejecuta la celda siguiente. Los checkpoints y artefactos se guardarán en tu Drive aunque la sesión expire.
"""))
cells.append(code("""\
# OPCIONAL — montar Google Drive para persistir resultados entre sesiones
# from google.colab import drive
# drive.mount('/content/drive')
# GDRIVE_ROOT = "/content/drive/MyDrive/MADRL_CityLearn_v3"
# os.makedirs(GDRIVE_ROOT, exist_ok=True)
# print("Google Drive montado:", GDRIVE_ROOT)
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 2 — CONFIGURACIÓN DEL PROYECTO
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("## Sección 2: Configuración del proyecto"))

cells.append(code("""\
# ── 2.1  Rutas, timestamp y directorio de salida ────────────────────────────
import os, sys
from datetime import datetime

REPO        = "/content/MADRLCitytleranflexresdr"
TIMESTAMP   = datetime.now().strftime("%Y%m%d_%H%M%S")
SCHEMA_PATH = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
PYTHON      = sys.executable

# Directorio raíz de esta sesión — mismo esquema que el lanzador oficial
#   {OUTPUT_ROOT}/{algorithm}/{scenario}_seed_0/data|checkpoints|figures
OUTPUT_ROOT = f"{REPO}/outputs/colab_madrl_{TIMESTAMP}"
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# Guardar ruta para referencia rápida
with open(f"{REPO}/outputs/latest_colab_output_root.txt", "w") as _f:
    _f.write(OUTPUT_ROOT)

assert os.path.exists(SCHEMA_PATH), f"Schema no encontrado: {SCHEMA_PATH}"

print(f"TIMESTAMP   : {TIMESTAMP}")
print(f"OUTPUT_ROOT : {OUTPUT_ROOT}")
print(f"SCHEMA_PATH : {SCHEMA_PATH}  ✅")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 3 — DATASET
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("""\
## Sección 3: Dataset Iquitos 2023-2025

**17 edificios reales** · 26 304 pasos horarios · 222 CSV sin NaN/Inf

| Recurso | Detalle |
|---|---|
| Período | 2023-2025 · año horario completo |
| BESS total | 26 266 kWh / 6 648 kW |
| PV total | 48 790 kWp (PVGIS TMY/pvlib) |
| EV chargers | 185 tomas · 96 equipos · 1 850 EVs en pool |
| V2G | 31 tomas de camiones (B01 Electro Oriente) |
| Intensidad carbono | 0.671-0.790 kgCO₂/kWh (MINAM RAGEI 2019) |
| Tarifa punta (18-22h) | 0.38 USD/kWh · fuera punta: 0.26 USD/kWh |
"""))

cells.append(code("""\
# ── 3.1  Verificar estructura del dataset ────────────────────────────────────
import json, os, pandas as pd

with open(SCHEMA_PATH) as f:
    schema = json.load(f)

buildings = schema.get("buildings", {})
print(f"Edificios: {len(buildings)}")
print(f"Pasos de simulación: {schema.get('simulation_end_time_step', 0) + 1}")
print(f"Agente central: {schema.get('central_agent', False)}")

# Mostrar primeros 5 edificios
for i, (name, bld) in enumerate(buildings.items()):
    if i >= 5:
        print(f"  ... y {len(buildings)-5} edificios más")
        break
    ev   = len(bld.get("electric_vehicle_chargers", []))
    bess = bld.get("electrical_storage", {}).get("capacity", "N/A")
    pv   = bld.get("pv", {}).get("nominal_power", "N/A")
    print(f"  {name}: EV={ev} tomas | BESS={bess} kWh | PV={pv} kWp")

# Verificar primer CSV
first_bld = list(buildings.keys())[0]
csv_rel = buildings[first_bld].get("energy_simulation", "")
csv_full = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/{csv_rel}"
df = pd.read_csv(csv_full)
print(f"\\nCSV {first_bld}: shape={df.shape} — filas ok: {len(df)==26304}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 4 — ENTORNO DEC-POMDP
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("""\
## Sección 4: Entorno Dec-POMDP — 17 agentes

**Dec-POMDP:** cada edificio es un agente con observación parcial local.
**CTDE:** el crítico usa el estado global durante entrenamiento; la ejecución es completamente local.

```
Observación local oᵢ(t) ≈ 40 dimensiones
  ├── Tiempo (mes, hora, tipo_día)
  ├── Física edificio (NSL, DHW, cooling, T_interior)
  ├── BESS (SOC, acción previa)
  ├── EV (SOC_k, salida_k, SOC_req_k)
  └── Señales globales (carbono, precio, GHI, T_amb)

Acción local aᵢ(t): [BESS_charge, EV_charge, Lavadora_on_off]
```
"""))

cells.append(code("""\
# ── 4.1  Crear entorno smoke-test (4 pasos) y describir agentes ─────────────
from citylearn.v3.environment import make_citylearn_v3_project_env, describe_environment

env = make_citylearn_v3_project_env(
    scenario="E1",
    seed=0,
    episode_time_steps=4,
    reward_aggregation="team_mean",
    normalize_observations=True,
    madrl_algorithm="MATD3",
    use_citylearn_v3_reward=True,
)
desc = describe_environment(env)
env.close()

obs_dims = list(desc.get("observation_dims", {}).values())
act_dims = list(desc.get("action_dims",      {}).values())

print(f"Num agentes  : {desc['num_agents']}")
print(f"Obs dim      : {obs_dims[0] if obs_dims else '?'}  (por agente)")
print(f"Action dim   : {act_dims[0] if act_dims else '?'}  (por agente)")
print(f"Reward func  : {desc.get('reward_function', 'N/A')}")
print(f"Reward aggr  : {desc.get('reward_aggregation', 'N/A')}")
print(f"Escenario    : E1 (Flexibilidad energética)")
print("\\n✅ Entorno Dec-POMDP verificado.")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 5 — RECOMPENSA MULTIOBJETIVO
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("""\
## Sección 5: Función de recompensa multiobjetivo

### Componentes (v4)

| Componente | Descripción |
|---|---|
| **Flexibilidad** | peak_penalty + ramping_penalty + load_factor + ev_service |
| **CO₂** | carbon_emissions × carbon_intensity |
| **Costo** | electricity_cost × price_signal |
| **EV urgency** | SOC_deficit × 1/horas_hasta_salida |
| **BESS degradación** | C-rate penalty Arrhenius LiFePO₄ (v4) |

### Pesos por escenario

| Escenario | flex | carbon | cost |
|:---:|:---:|:---:|:---:|
| **E1** | **0.70** | 0.15 | 0.15 |
| **E2** | 0.15 | **0.70** | 0.15 |
| **E3** | 0.25 | 0.15 | **0.60** |

### Recompensa mixta CTDE (team_ratio = 0.70)
```
r_i_mix = 0.30 × r_i_local  +  0.70 × mean(r₁,...,r₁₇)
```
"""))

cells.append(code("""\
# ── 5.1  Visualizar pesos de recompensa por escenario ────────────────────────
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np, os

WEIGHTS = {
    "E1": {"Flexibilidad": 0.70, "CO₂": 0.15, "Costo": 0.15},
    "E2": {"Flexibilidad": 0.15, "CO₂": 0.70, "Costo": 0.15},
    "E3": {"Flexibilidad": 0.25, "CO₂": 0.15, "Costo": 0.60},
}
COLORS = ["#3b82f6", "#22c55e", "#f59e0b"]
LABELS = list(WEIGHTS["E1"].keys())

fig, axes = plt.subplots(1, 3, figsize=(13, 4.5), sharey=True)
fig.suptitle("Pesos de recompensa por escenario (CityLearnV3MADRLRewardFunction v4)",
             fontsize=13, fontweight="bold")
for ax, (sc, wts), in zip(axes, WEIGHTS.items()):
    vals = list(wts.values())
    bars = ax.bar(LABELS, vals, color=COLORS, edgecolor="white", linewidth=1.5, width=0.55)
    ax.set_title(f"Escenario {sc}", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 0.85)
    ax.tick_params(axis="x", rotation=15)
    ax.grid(axis="y", alpha=0.25)
    ax.set_facecolor("#f8fafc")
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{v:.2f}", ha="center", fontsize=11, fontweight="bold")

plt.tight_layout()
os.makedirs(f"{OUTPUT_ROOT}/figures", exist_ok=True)
plt.savefig(f"{OUTPUT_ROOT}/figures/reward_weights.png", dpi=150, bbox_inches="tight")
plt.show()
print(f"✅  Figura: {OUTPUT_ROOT}/figures/reward_weights.png")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 6 — HIPERPARÁMETROS A100
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("""\
## Sección 6: Hiperparámetros (A100 optimizado · 75 episodios)

Todos los parámetros base vienen de la **corrida oficial v4** (`run_aws_training.sh`).
Los ajustes A100 aumentan batch, buffer y red donde el VRAM de 40 GB lo permite.

### Tabla comparativa

| Parámetro | Official v4 (A10G 24 GB) | **A100 40 GB (este notebook)** |
|---|:---:|:---:|
| Torch threads | 8 (servidor) | 2 (Colab CPU) |
| Artifact profile | efficient | efficient |
| Trace interval | 24 pasos | 24 pasos |
| **HAPPO hidden_size** | 384 | 384 |
| **MASAC buffer_size** | 20 epis. | 25 epis. |
| **MASAC critic_batch** | 64 | 128 |
| **MASAC max_buf_gib** | 8 GiB | 20 GiB |
| **MATD3 batch_size** | 256 | 512 |
| **MATD3 buffer_size** | 4 096 k | 6 000 k |
| **MAAC batch_size** | 256 | 512 |
| **MAAC buffer_length** | 50 000 | 100 000 |

> **QUICK_TEST = True** ejecuta 3 episodios × 8 760 pasos para verificar el pipeline sin costo de tiempo.
> **QUICK_TEST = False** lanza el entrenamiento completo de 75 episodios.
"""))

cells.append(code("""\
# ── 6.1  Configuración central de entrenamiento ──────────────────────────────
import os, sys, subprocess, time, json
from pathlib import Path

REPO        = "/content/MADRLCitytleranflexresdr"
PYTHON      = sys.executable
SCHEMA_PATH = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"

# ── Toggle principal ─────────────────────────────────────────────────────────
QUICK_TEST = False   # ← True  = 3 ep × 8760 steps (smoke test ~30 min)
                     # ← False = 75 ep × 8760 steps (entrenamiento real ~8 h)

# ── Parámetros comunes ───────────────────────────────────────────────────────
EPISODES        = 3      if QUICK_TEST else 75
EPISODE_STEPS   = 8760                        # año completo (no cambiar)
NUM_ENV_STEPS   = EPISODES * EPISODE_STEPS    # 26 280 (QT) o 657 000 (full)
SEED            = 0

TORCH_THREADS        = 2       # Colab A100 expone 2 cores CPU
LIVE_PROGRESS_INT    = 1000    # escribir live_progress.json cada 1 000 pasos
ARTIFACT_PROFILE     = "efficient"   # efficient | full
TRACE_INTERVAL       = 24     # registrar trace cada 24 pasos de entorno
TRACE_DETAIL         = "compact"
GPU_PROFILE          = "aws"   # perfil para GPU servidores (A10G/A100)

SCENARIOS  = ["E1", "E2", "E3"]
ALGORITHMS = ["happo", "masac", "matd3", "maac"]

# ── Layout de salida: algorithm-first (igual al lanzador oficial) ─────────────
# Ruta final:  {OUTPUT_ROOT}/{algorithm}/{scenario}_seed_0/data|checkpoints|figures
def out_dir(algorithm: str) -> str:
    return f"{OUTPUT_ROOT}/{algorithm}"

mode = "QUICK_TEST (3 ep)" if QUICK_TEST else "FULL TRAINING (75 ep)"
print(f"Modo          : {mode}")
print(f"Episodios     : {EPISODES}  ×  {EPISODE_STEPS} pasos  =  {NUM_ENV_STEPS:,} pasos/corrida")
print(f"Corridas total: {len(SCENARIOS) * len(ALGORITHMS)} ({len(ALGORITHMS)} algos × {len(SCENARIOS)} escenarios)")
print(f"Output root   : {OUTPUT_ROOT}")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 7 — LANZAMIENTO DEL ENTRENAMIENTO
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("## Sección 7: Lanzamiento del entrenamiento"))

# Helper run function
cells.append(code("""\
# ── 7.0  Helper: run_training con streaming de salida ─────────────────────────
import subprocess, time, sys, json, os
from pathlib import Path

def run_training(cmd: list[str], label: str, log_path: str) -> int:
    \"\"\"
    Ejecutar un training script con salida en tiempo real.
    Filtra líneas para no saturar la celda. Devuelve el exit code.
    \"\"\"
    Path(log_path).parent.mkdir(parents=True, exist_ok=True)
    SHOW_KEYWORDS = [
        "episode", "Episode", "step", "Step", "reward", "Reward",
        "ERROR", "error", "Exception", "Traceback",
        "COMPLETE", "complete", "DONE", "Saved", "saved",
        "KPI", "peak", "carbon", "cost",
        "happo", "masac", "matd3", "maac",
        "WARNING", "INFO:", "✅", "⚠️", "🏁",
    ]
    t0 = time.time()
    print(f"\\n{'='*68}")
    print(f"  ▶  {label}")
    print(f"     {' '.join(cmd[:4])} ...")
    print(f"{'='*68}")

    with open(log_path, "w") as log_f:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=REPO,
        )
        line_n = 0
        for line in proc.stdout:
            line = line.rstrip()
            log_f.write(line + "\\n")
            log_f.flush()
            if line_n < 30 or any(k.lower() in line.lower() for k in SHOW_KEYWORDS):
                print(line)
            line_n += 1
        proc.wait()

    elapsed = time.time() - t0
    ok = proc.returncode == 0
    print(f"\\n  {'✅ OK' if ok else '❌ FAILED'} — {label} — {elapsed/60:.1f} min")
    if not ok:
        print(f"  Log guardado en: {log_path}")
        print(f"  Últimas líneas:")
        with open(log_path) as lf:
            tail = lf.readlines()[-20:]
        for l in tail:
            print("    ", l.rstrip())
    return proc.returncode
"""))

# ── HAPPO ───────────────────────────────────────────────────────────────────
cells.append(md("""\
### HAPPO — Heterogeneous-Agent PPO

On-policy · Actualización secuencial por agente · Trust region individual
Backend: `external/HARL/`

**Hiperparámetros A100:**
- `hidden_size = 384`  (igual a oficial v4)
- `actor_lr = 1e-4`, `critic_lr = 5e-4`
- `gamma = 0.9999`  (esencial para horizonte anual 8 760 pasos)
- `n_rollout_threads = 1`  (CityLearn no paraleliza nodo-a-nodo)
"""))

cells.append(code("""\
# ── 7.1  HAPPO (E1, E2, E3) ─────────────────────────────────────────────────
HAPPO_SCRIPT = f"{REPO}/CityLearn/scripts/train_citylearn_v3_happo.py"
happo_results = {}

for scenario in SCENARIOS:
    odir = out_dir("happo")
    os.makedirs(odir, exist_ok=True)
    log  = f"{OUTPUT_ROOT}/logs/happo_{scenario}.log"
    os.makedirs(f"{OUTPUT_ROOT}/logs", exist_ok=True)

    cmd = [
        PYTHON, "-B", HAPPO_SCRIPT,
        # ── Argumentos comunes ──────────────────────────────────────────────
        "--schema-path",            SCHEMA_PATH,
        "--scenario",               scenario,
        "--seed",                   str(SEED),
        "--episode-time-steps",     str(EPISODE_STEPS),
        "--output-dir",             odir,
        "--torch-threads",          str(TORCH_THREADS),
        "--live-progress-interval", str(LIVE_PROGRESS_INT),
        "--artifact-profile",       ARTIFACT_PROFILE,
        "--trace-record-interval",  str(TRACE_INTERVAL),
        "--trace-detail",           TRACE_DETAIL,
        "--gpu-profile",            GPU_PROFILE,
        "--cuda",
        # ── Argumentos HAPPO-específicos (base: oficial v4) ─────────────────
        "--episodes",               str(EPISODES),
        "--num-env-steps",          str(NUM_ENV_STEPS),
        "--hidden-size",            "384",      # red actor/crítico
        "--n-rollout-threads",      "1",        # CityLearn serial
        "--log-interval",           "1",        # loggear cada episodio
        "--eval-interval",          "1",        # checkpoint cada episodio
        "--actor-lr",               "1e-4",
        "--critic-lr",              "5e-4",
        "--max-grad-norm",          "1.0",
        "--gamma",                  "0.9999",   # horizonte año completo
        "--action-aggregation",     "mean",
    ]

    rc = run_training(cmd, f"HAPPO  {scenario}", log)
    happo_results[scenario] = rc

print("\\nResumen HAPPO:", {k: "✅" if v==0 else "❌" for k,v in happo_results.items()})
"""))

# ── MASAC ────────────────────────────────────────────────────────────────────
cells.append(md("""\
### MASAC — Multi-Agent SAC Discreto

Off-policy · Q-mixer centralizado · Entropía máxima · Acciones discretas por eje
Backend: `external/MARL/src/`

**Hiperparámetros A100:**
- `buffer_size = 25`  epis. (oficial: 20 · +25% con 40 GB RAM)
- `critic_batch_size = 128`  (oficial: 64 · A100 CPU–GPU puede manejar doble)
- `max_replay_buffer_gib = 20`  (seguro en A100 con 83 GB RAM Colab)
- `masac_preload_batch_device = auto`  (intenta CUDA, fallback CPU)
"""))

cells.append(code("""\
# ── 7.2  MASAC (E1, E2, E3) ─────────────────────────────────────────────────
MASAC_SCRIPT = f"{REPO}/CityLearn/scripts/train_citylearn_v3_masac.py"
masac_results = {}

for scenario in SCENARIOS:
    odir = out_dir("masac")
    os.makedirs(odir, exist_ok=True)
    log  = f"{OUTPUT_ROOT}/logs/masac_{scenario}.log"

    cmd = [
        PYTHON, "-B", MASAC_SCRIPT,
        # ── Argumentos comunes ──────────────────────────────────────────────
        "--schema-path",            SCHEMA_PATH,
        "--scenario",               scenario,
        "--seed",                   str(SEED),
        "--episode-time-steps",     str(EPISODE_STEPS),
        "--output-dir",             odir,
        "--torch-threads",          str(TORCH_THREADS),
        "--live-progress-interval", str(LIVE_PROGRESS_INT),
        "--artifact-profile",       ARTIFACT_PROFILE,
        "--trace-record-interval",  str(TRACE_INTERVAL),
        "--trace-detail",           TRACE_DETAIL,
        "--gpu-profile",            GPU_PROFILE,
        "--cuda",
        # ── Argumentos MASAC-específicos (base: oficial v4, tuning A100) ────
        "--episodes",               str(EPISODES),
        "--epochs",                 str(EPISODES),   # MASAC usa epochs=episodes
        "--action-bins",            "3",             # 3 bins por eje de acción
        "--discrete-action-mode",   "axis",          # lineal en dims (no cartesiano)
        "--buffer-size",            "25",            # 25 episodios en replay (A100: +25%)
        "--critic-batch-size",      "128",           # doble vs oficial (A100)
        "--critic-train-steps",     "1",
        "--actor-sample-times",     "5",
        "--max-replay-buffer-gib",  "20",            # A100 RAM: 83 GB disponible
        "--masac-preload-batch-device", "auto",      # CUDA→CPU fallback
        "--actor-lr",               "3e-4",
        "--critic-lr",              "5e-4",
        "--alpha-lr",               "3e-4",
        "--grad-norm-clip",         "1.0",
        "--gamma",                  "0.9999",
        "--rnn-hidden-dim",         "256",
        "--qmix-hidden-dim",        "128",
        "--hyper-hidden-dim",       "256",
    ]

    rc = run_training(cmd, f"MASAC  {scenario}", log)
    masac_results[scenario] = rc

print("\\nResumen MASAC:", {k: "✅" if v==0 else "❌" for k,v in masac_results.items()})
"""))

# ── MATD3 ────────────────────────────────────────────────────────────────────
cells.append(md("""\
### MATD3 — Multi-Agent TD3  ★ Ganador v4

Off-policy · Doble crítico (anti-sobreestimación) · Policy delay · Target noise
Backend: `external/off-policy/`

**Hiperparámetros A100:**
- `batch_size = 512`  (oficial: 256 · A100 VRAM permite el doble)
- `buffer_size = 6000`  k transiciones (oficial: 4 096 k · +46%)
- `train_interval = 100`  (actualizar red cada 100 steps → igual a oficial)
- `gamma = 0.9999`  (esencial para horizonte anual)

**Resultado oficial v4:** MATD3 es el mejor MADRL global (KW p=0.0459)
"""))

cells.append(code("""\
# ── 7.3  MATD3 (E1, E2, E3) ─────────────────────────────────────────────────
MATD3_SCRIPT = f"{REPO}/CityLearn/scripts/train_citylearn_v3_matd3.py"
matd3_results = {}

for scenario in SCENARIOS:
    odir = out_dir("matd3")
    os.makedirs(odir, exist_ok=True)
    log  = f"{OUTPUT_ROOT}/logs/matd3_{scenario}.log"

    cmd = [
        PYTHON, "-B", MATD3_SCRIPT,
        # ── Argumentos comunes ──────────────────────────────────────────────
        "--schema-path",            SCHEMA_PATH,
        "--scenario",               scenario,
        "--seed",                   str(SEED),
        "--episode-time-steps",     str(EPISODE_STEPS),
        "--output-dir",             odir,
        "--torch-threads",          str(TORCH_THREADS),
        "--live-progress-interval", str(LIVE_PROGRESS_INT),
        "--artifact-profile",       ARTIFACT_PROFILE,
        "--trace-record-interval",  str(TRACE_INTERVAL),
        "--trace-detail",           TRACE_DETAIL,
        "--gpu-profile",            GPU_PROFILE,
        "--cuda",
        # ── Argumentos MATD3-específicos (base: oficial v4, tuning A100) ────
        "--episodes",               str(EPISODES),
        "--num-env-steps",          str(NUM_ENV_STEPS),
        "--batch-size",             "512",      # doble vs oficial (A100 VRAM)
        "--buffer-size",            "6000",     # 6 M transiciones (oficial: 4 096 k)
        "--hidden-size",            "256",      # igual a oficial (estabilidad)
        "--lr",                     "3e-4",
        "--max-grad-norm",          "1.0",
        "--gamma",                  "0.9999",   # horizonte año completo
        "--train-interval",         "100",      # actualizar redes cada 100 steps
        "--num-random-episodes",    "1",        # 1 ep. aleatorio antes de train
    ]

    rc = run_training(cmd, f"MATD3  {scenario}", log)
    matd3_results[scenario] = rc

print("\\nResumen MATD3:", {k: "✅" if v==0 else "❌" for k,v in matd3_results.items()})
"""))

# ── MAAC ─────────────────────────────────────────────────────────────────────
cells.append(md("""\
### MAAC — Multi-Agent Attention Critic

Off-policy · Atención multi-cabeza sobre agentes · Actor estocástico (SAC-like)
Backend: `external/MAAC/`

**Hiperparámetros A100:**
- `batch_size = 512`  (oficial: 256)
- `buffer_length = 100 000`  transiciones (oficial: 50 000)
- `steps_per_update = 250`  (igual a oficial)
- `num_updates = 8`  (igual a oficial)
- `attend_heads = 4`  (igual a oficial)
"""))

cells.append(code("""\
# ── 7.4  MAAC (E1, E2, E3) ─────────────────────────────────────────────────
MAAC_SCRIPT = f"{REPO}/CityLearn/scripts/train_citylearn_v3_maac.py"
maac_results = {}

for scenario in SCENARIOS:
    odir = out_dir("maac")
    os.makedirs(odir, exist_ok=True)
    log  = f"{OUTPUT_ROOT}/logs/maac_{scenario}.log"

    cmd = [
        PYTHON, "-B", MAAC_SCRIPT,
        # ── Argumentos comunes ──────────────────────────────────────────────
        "--schema-path",            SCHEMA_PATH,
        "--scenario",               scenario,
        "--seed",                   str(SEED),
        "--episode-time-steps",     str(EPISODE_STEPS),
        "--output-dir",             odir,
        "--torch-threads",          str(TORCH_THREADS),
        "--live-progress-interval", str(LIVE_PROGRESS_INT),
        "--artifact-profile",       ARTIFACT_PROFILE,
        "--trace-record-interval",  str(TRACE_INTERVAL),
        "--trace-detail",           TRACE_DETAIL,
        "--gpu-profile",            GPU_PROFILE,
        "--cuda",
        # ── Argumentos MAAC-específicos (base: oficial v4, tuning A100) ─────
        "--episodes",               str(EPISODES),
        "--action-bins",            "3",
        "--discrete-action-mode",   "axis",         # lineal en dims (no cartesiano)
        "--batch-size",             "512",           # doble vs oficial (A100)
        "--buffer-length",          "100000",        # doble vs oficial (A100)
        "--steps-per-update",       "250",           # igual a oficial
        "--num-updates",            "8",             # igual a oficial
        "--max-discrete-actions",   "512",           # límite safety check
        "--hidden-size",            "256",
        "--attend-heads",           "4",
        "--pi-lr",                  "3e-4",
        "--q-lr",                   "1e-3",
        "--tau",                    "1e-3",
        "--gamma",                  "0.9999",
        "--reward-scale",           "10.0",
    ]

    rc = run_training(cmd, f"MAAC   {scenario}", log)
    maac_results[scenario] = rc

print("\\nResumen MAAC:", {k: "✅" if v==0 else "❌" for k,v in maac_results.items()})
"""))

# ── Resumen de entrenamiento ──────────────────────────────────────────────────
cells.append(code("""\
# ── 7.5  Resumen global de todas las corridas ────────────────────────────────
import json, os, glob

print("=" * 60)
print("  RESUMEN DE ENTRENAMIENTO — 12 CORRIDAS")
print("=" * 60)

all_results = {
    "happo": happo_results,
    "masac": masac_results,
    "matd3": matd3_results,
    "maac" : maac_results,
}

total_ok = total_fail = 0
for algo, results in all_results.items():
    for sc, rc in results.items():
        ok = rc == 0
        total_ok   += ok
        total_fail += not ok
        status = "✅ OK" if ok else "❌ FAILED"
        print(f"  {algo.upper():<6} {sc}  →  {status}")

print(f"\\n  Completadas: {total_ok}/12  |  Fallidas: {total_fail}/12")

# Contar artefactos generados
n_json  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.json",  recursive=True))
n_csv   = len(glob.glob(f"{OUTPUT_ROOT}/**/*.csv",   recursive=True))
n_png   = len(glob.glob(f"{OUTPUT_ROOT}/**/*.png",   recursive=True))
n_ckpt  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.pt",    recursive=True))
print(f"\\n  Artefactos: {n_json} JSON · {n_csv} CSV · {n_png} PNG · {n_ckpt} checkpoints .pt")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 8 — ANÁLISIS DE RESULTADOS
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("""\
## Sección 8: Análisis de resultados y KPIs

### Estructura de artefactos (algorithm-first)
```
{OUTPUT_ROOT}/
  happo/
    E1_seed_0/data/results.json  timeseries.csv  training_summary.json
    E2_seed_0/data/results.json  ...
    E3_seed_0/data/results.json  ...
  masac/ matd3/ maac/  → misma estructura
  logs/  happo_E1.log  masac_E1.log  ...
  figures/  evaluation/
```
"""))

cells.append(code("""\
# ── 8.1  Cargar todos los results.json ──────────────────────────────────────
import json, os, glob
import pandas as pd
import numpy as np

def load_all_results(output_root: str) -> pd.DataFrame:
    records = []
    # Layout algorithm-first: {output_root}/{algo}/{scenario}_seed_0/data/results.json
    for fp in sorted(glob.glob(f"{output_root}/*/*/data/results.json", recursive=False)):
        parts = Path(fp).parts
        # ... /output_root/algo/scenario_seed_0/data/results.json
        algo_idx  = next(i for i,p in enumerate(parts) if p == Path(output_root).name) + 1
        algo      = parts[algo_idx] if algo_idx < len(parts) else "?"
        sc_seed   = parts[algo_idx + 1] if algo_idx+1 < len(parts) else "?"
        scenario  = sc_seed.split("_seed_")[0] if "_seed_" in sc_seed else sc_seed
        try:
            with open(fp) as f:
                data = json.load(f)
            records.append({
                "algorithm":                 algo.upper(),
                "scenario":                  scenario,
                "peak_average":              data.get("peak_average",            np.nan),
                "ramping_average":           data.get("ramping_average",         np.nan),
                "load_factor_average":       data.get("load_factor_average",     np.nan),
                "carbon_emissions":          data.get("carbon_emissions",        np.nan),
                "electricity_cost":          data.get("electricity_cost",        np.nan),
                "ev_departure_success_rate": data.get("ev_departure_success_rate", np.nan),
                "pv_self_consumption_ratio": data.get("pv_self_consumption_ratio",  np.nan),
            })
        except Exception as e:
            print(f"  ⚠️  {fp}: {e}")
    return pd.DataFrame(records)

from pathlib import Path
df_results = load_all_results(OUTPUT_ROOT)

if df_results.empty:
    print("⚠️  Sin results.json todavía — ejecuta el entrenamiento primero.")
    print("   (Referencia v4: MATD3 KW p=0.0459, Score global 0.7445)")
else:
    pd.set_option("display.float_format", "{:.4f}".format)
    print(f"✅  {len(df_results)} corridas cargadas\\n")
    print(df_results.to_string(index=False))
    os.makedirs(f"{OUTPUT_ROOT}/evaluation", exist_ok=True)
    df_results.to_csv(f"{OUTPUT_ROOT}/evaluation/all_kpis.csv", index=False)
"""))

cells.append(code("""\
# ── 8.2  Curvas de convergencia (timeseries.csv) ────────────────────────────
import matplotlib.pyplot as plt, glob, pandas as pd

ts_data = {}
for fp in sorted(glob.glob(f"{OUTPUT_ROOT}/*/*/data/timeseries.csv")):
    parts = Path(fp).parts
    root_idx = next(i for i,p in enumerate(parts) if p == Path(OUTPUT_ROOT).name)
    algo     = parts[root_idx + 1].upper()
    sc_seed  = parts[root_idx + 2]
    sc       = sc_seed.split("_seed_")[0] if "_seed_" in sc_seed else sc_seed
    try:
        ts_data[f"{algo}_{sc}"] = pd.read_csv(fp)
    except Exception:
        pass

if ts_data:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    CLR = {"HAPPO":"#3b82f6","MASAC":"#a21caf","MATD3":"#16a34a","MAAC":"#d97706"}
    for ax, sc in zip(axes, ["E1", "E2", "E3"]):
        for key, df in ts_data.items():
            if f"_{sc}" in key:
                alg = key.replace(f"_{sc}", "")
                rcol = next((c for c in df.columns if "reward" in c.lower()), None)
                if rcol:
                    ax.plot(df.index, df[rcol].rolling(3, min_periods=1).mean(),
                            label=alg, color=CLR.get(alg,"gray"), lw=2, alpha=0.85)
        ax.set_title(f"Escenario {sc}", fontweight="bold")
        ax.set_xlabel("Episodio"); ax.set_ylabel("Reward medio (smoothed)")
        ax.legend(fontsize=9); ax.grid(alpha=0.3); ax.set_facecolor("#f8fafc")
    fig.suptitle("Convergencia — 4 Algoritmos × 3 Escenarios", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_ROOT}/evaluation/convergencia.png", dpi=150, bbox_inches="tight")
    plt.show()
    print(f"✅  {OUTPUT_ROOT}/evaluation/convergencia.png")
else:
    print("Sin timeseries disponibles.")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 9 — EVALUACIÓN ESTADÍSTICA
# ════════════════════════════════════════════════════════════════════════════
cells.append(md("""\
## Sección 9: Evaluación estadística — Selección del mejor MADRL

Protocolo idéntico al análisis oficial:
1. **Shapiro-Wilk** — normalidad por algoritmo
2. **Kruskal-Wallis** — diferencia global (4 grupos)
3. **Mann-Whitney U** — pares con effect size (Cliff's δ)
4. **Ranking global** — score ponderado por escenario
"""))

cells.append(code("""\
# ── 9.1  Suite de pruebas estadísticas ──────────────────────────────────────
from scipy import stats
import itertools, json, os
import numpy as np, pandas as pd

SCENARIO_WEIGHTS = {
    "E1": {"peak_average": 0.50, "carbon_emissions": 0.25, "electricity_cost": 0.25},
    "E2": {"peak_average": 0.25, "carbon_emissions": 0.50, "electricity_cost": 0.25},
    "E3": {"peak_average": 0.25, "carbon_emissions": 0.25, "electricity_cost": 0.50},
}
INVERT = {"peak_average", "carbon_emissions", "electricity_cost"}  # menor = mejor

def cliff_delta(x, y):
    n1, n2 = len(x), len(y)
    d = sum(1 for a in x for b in y if a>b) - sum(1 for a in x for b in y if a<b)
    return d / (n1 * n2)

def build_scores(df: pd.DataFrame) -> dict:
    algorithms = sorted(df["algorithm"].unique())
    scores = {a: [] for a in algorithms}
    for sc, weights in SCENARIO_WEIGHTS.items():
        sub = df[df["scenario"] == sc].copy()
        if sub.empty:
            continue
        norm_cols = []
        w_arr = []
        for kpi, w in weights.items():
            if kpi not in sub.columns:
                continue
            vals = sub[kpi].astype(float)
            rng  = vals.max() - vals.min()
            nrm  = (vals - vals.min()) / rng if rng > 0 else pd.Series(0.5, index=vals.index)
            sub[f"{kpi}_n"] = 1 - nrm if kpi in INVERT else nrm
            norm_cols.append(f"{kpi}_n")
            w_arr.append(w)
        w_arr = np.array(w_arr) / sum(w_arr)
        sub["score"] = sum(sub[nc] * wt for nc, wt in zip(norm_cols, w_arr))
        for a in algorithms:
            v = sub[sub["algorithm"]==a]["score"].values
            if len(v) > 0:
                scores[a].append(float(v[0]))
    return {a: np.array(v) for a, v in scores.items() if v}

stat_results = {}
if not df_results.empty:
    score_arrays = build_scores(df_results)
    algorithms   = sorted(score_arrays.keys())

    # 1. Shapiro-Wilk
    print("1. SHAPIRO-WILK")
    for a, arr in score_arrays.items():
        if len(arr) >= 3:
            s, p = stats.shapiro(arr)
            print(f"  {a:<6}: W={s:.4f} p={p:.4f}  {'NORMAL' if p>0.05 else 'no normal'}")
        else:
            print(f"  {a:<6}: muestras insuficientes")

    # 2. Kruskal-Wallis
    print("\\n2. KRUSKAL-WALLIS")
    groups = [score_arrays[a] for a in algorithms if len(score_arrays.get(a,[])) > 0]
    if len(groups) >= 2:
        h, p = stats.kruskal(*groups)
        sig = p < 0.05
        print(f"  H={h:.4f}  p={p:.4f}  → {'SIGNIFICATIVO ✅' if sig else 'No significativo'}")
        stat_results["kruskal_wallis"] = {"H": float(h), "p": float(p), "significant": sig}

    # 3. Mann-Whitney U
    print("\\n3. MANN-WHITNEY U (pairwise + Cliff δ)")
    mwu = {}
    for a1, a2 in itertools.combinations(algorithms, 2):
        arr1, arr2 = score_arrays.get(a1, np.array([])), score_arrays.get(a2, np.array([]))
        if len(arr1)<1 or len(arr2)<1: continue
        try:
            s, p = stats.mannwhitneyu(arr1, arr2, alternative="two-sided")
            d = cliff_delta(arr1.tolist(), arr2.tolist())
            winner = a1 if arr1.mean() > arr2.mean() else a2
            mwu[f"{a1}_vs_{a2}"] = {"p": float(p), "cliff_delta": float(d), "winner": winner}
            print(f"  {a1} vs {a2}: p={p:.4f} {'✅' if p<0.05 else ''}  δ={d:.3f}  ▶ {winner}")
        except Exception as e:
            print(f"  {a1} vs {a2}: {e}")
    stat_results["mann_whitney_u"] = mwu

    # 4. Ranking
    print("\\n4. RANKING GLOBAL")
    ranking = sorted(
        [{"algorithm": a, "mean_score": float(v.mean())} for a, v in score_arrays.items()],
        key=lambda x: -x["mean_score"],
    )
    for i, r in enumerate(ranking, 1):
        print(f"  {i}. {r['algorithm']:<6}  {r['mean_score']:.4f} {'★ Ganador' if i==1 else ''}")
    stat_results["ranking"]   = ranking
    stat_results["best_madrl"] = ranking[0]["algorithm"] if ranking else "N/A"

    os.makedirs(f"{OUTPUT_ROOT}/evaluation", exist_ok=True)
    with open(f"{OUTPUT_ROOT}/evaluation/statistical_analysis.json", "w") as f:
        json.dump(stat_results, f, indent=2, default=str)
    print(f"\\n✅  {OUTPUT_ROOT}/evaluation/statistical_analysis.json")
else:
    print("⚠️  Sin datos — referencia oficial v4: MATD3 mejor (KW p=0.0459)")
"""))

# ════════════════════════════════════════════════════════════════════════════
# SECCIÓN 10 — RESUMEN FINAL
# ════════════════════════════════════════════════════════════════════════════
cells.append(code("""\
# ── 10.  Resumen final de la sesión Colab ───────────────────────────────────
import json, glob, os
from datetime import datetime

print("=" * 65)
print("  RESUMEN FINAL — MADRL CityLearn v3 · Colab A100")
print("=" * 65)
print(f"  Output root : {OUTPUT_ROOT}")
print(f"  Timestamp   : {TIMESTAMP}")
print(f"  Modo        : {'QUICK_TEST' if QUICK_TEST else 'FULL TRAINING (75 ep)'}")

n_json = len(glob.glob(f"{OUTPUT_ROOT}/**/*.json",  recursive=True))
n_csv  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.csv",   recursive=True))
n_png  = len(glob.glob(f"{OUTPUT_ROOT}/**/*.png",   recursive=True))
n_ckpt = len(glob.glob(f"{OUTPUT_ROOT}/**/*.pt",    recursive=True))
print(f"\\n  Artefactos : {n_json} JSON · {n_csv} CSV · {n_png} PNG · {n_ckpt} .pt")

if stat_results and "ranking" in stat_results:
    print("\\n  RANKING FINAL:")
    for i, r in enumerate(stat_results["ranking"], 1):
        mark = " ★" if i == 1 else ""
        print(f"    {i}. {r['algorithm']:<6} {r['mean_score']:.4f}{mark}")
    kw = stat_results.get("kruskal_wallis", {})
    if kw:
        print(f"  KW: p={kw.get('p','?')} ({'✅' if kw.get('significant') else ''})")
else:
    print("\\n  Referencia oficial v4:")
    print("    1. MATD3  0.7445 ★")
    print("    2. MASAC  ~0.73")
    print("    3. MAAC   ~0.72")
    print("    4. HAPPO  ~0.70")
    print("    KW p=0.0459 ✅")

# Escribir session summary JSON
summary = {
    "timestamp":        TIMESTAMP,
    "output_root":      OUTPUT_ROOT,
    "mode":             "quick_test" if QUICK_TEST else "full_training",
    "episodes":         EPISODES,
    "episode_steps":    EPISODE_STEPS,
    "num_env_steps":    NUM_ENV_STEPS,
    "algorithms":       ALGORITHMS,
    "scenarios":        SCENARIOS,
    "a100_tuning": {
        "happo_hidden":         384,
        "masac_buffer_size":    25,
        "masac_critic_batch":   128,
        "masac_max_buf_gib":    20,
        "matd3_batch_size":     512,
        "matd3_buffer_size":    6000,
        "maac_batch_size":      512,
        "maac_buffer_length":   100000,
    },
    "artifacts": {"json": n_json, "csv": n_csv, "png": n_png, "pt": n_ckpt},
    "statistical_analysis": stat_results if stat_results else "run training first",
}
with open(f"{OUTPUT_ROOT}/colab_session_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)

print(f"\\n  ✅  Resumen: {OUTPUT_ROOT}/colab_session_summary.json")
print("=" * 65)
"""))

cells.append(md("""\
## Próximos pasos

1. **Descargar artefactos**: panel de Archivos de Colab → seleccionar `outputs/colab_madrl_*/`
2. **Google Drive**: si montaste Drive, ya están en `MyDrive/MADRL_CityLearn_v3/`
3. **Evidencia de tesis**: ejecutar `CityLearn/scripts/generate_thesis_objective_evidence.py`
4. **Comparar con baseline**: `CityLearn/scripts/benchmark_citylearn_v2_agents.py`

---

Repositorio: [Mac-Tapia/MADRLCitytleranflexresdr](https://github.com/Mac-Tapia/MADRLCitytleranflexresdr)
Contacto: mac.tapia.c@uni.pe · Universidad Nacional de Ingenieria - UNI · 2026
"""))

# ════════════════════════════════════════════════════════════════════════════
# GENERAR NOTEBOOK
# ════════════════════════════════════════════════════════════════════════════
nb = {
    "nbformat": 4,
    "nbformat_minor": 5,
    "metadata": {
        "colab": {
            "name": "madrl_citylearn_v3_tutorial.ipynb",
            "provenance": [],
            "gpuType": "A100",
            "collapsed_sections": [],
            "toc_visible": True,
        },
        "kernelspec": {
            "display_name": "Python 3",
            "language": "python",
            "name": "python3",
        },
        "language_info": {
            "name": "python",
            "version": "3.10.0",
        },
        "accelerator": "GPU",
    },
    "cells": cells,
}

OUT = Path("CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, "w", encoding="utf-8") as f:
    json.dump(nb, f, indent=1, ensure_ascii=False)

n_code = sum(1 for c in cells if c["cell_type"] == "code")
n_md   = sum(1 for c in cells if c["cell_type"] == "markdown")
print(f"Notebook: {OUT}")
print(f"Celdas: {len(cells)} total  ({n_code} código · {n_md} markdown)")
print(f"Tamaño: {OUT.stat().st_size / 1024:.1f} KB")
