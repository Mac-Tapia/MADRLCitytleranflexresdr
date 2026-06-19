"""Generate madrl_citylearn_v3_tutorial.ipynb for Google Colab A100."""
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


# ---------------------------------------------------------------------------
# Cells
# ---------------------------------------------------------------------------
cells = []

# ── 0. TITLE ────────────────────────────────────────────────────────────────
cells.append(md("""\
# MADRL CityLearn v3 — Tutorial Completo Google Colab (A100)

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/Mac-Tapia/MADRLCitytleranflexresdr/blob/master/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb)

**Proyecto:** Multi-Agente de Aprendizaje por Refuerzo Profundo para gestión coordinada
de flexibilidad energética, emisiones de CO₂ y eficiencia económica en comunidades inteligentes.

**Caso de estudio:** 17 edificios reales de Iquitos, Perú · Dataset 2023-2025 · 26 304 pasos horarios.

**Algoritmos:** HAPPO · MASAC · MATD3 · MAAC
**Escenarios:** E1 (Flexibilidad) · E2 (CO₂) · E3 (Costos energéticos)
**Resultado v4:** MATD3 es el mejor MADRL global (KW p=0.0459, MWU MATD3 vs HAPPO p=0.0182)

---

## Estructura del tutorial

| Sección | Contenido |
|---|---|
| 1 | Configuración GPU y dependencias |
| 2 | Clonar repositorio y verificar dataset |
| 3 | Entorno Dec-POMDP (17 agentes) |
| 4 | Función de recompensa multiobjetivo |
| 5 | Entrenamiento completo (12 corridas, A100 optimizado) |
| 6 | Análisis de resultados y KPIs |
| 7 | Evaluación estadística y selección del mejor MADRL |

> **Requisito:** GPU A100 (Colab Pro/Pro+, seleccionar A100 en Runtime → Change runtime type)
"""))

# ── 1. CHECK GPU ─────────────────────────────────────────────────────────────
cells.append(md("## Sección 1: Configuración inicial"))

cells.append(code("""\
# Verificar GPU disponible (debe ser A100 para rendimiento óptimo)
import subprocess, sys, os

result = subprocess.run(["nvidia-smi", "--query-gpu=name,memory.total,driver_version",
                         "--format=csv,noheader"], capture_output=True, text=True)
gpu_info = result.stdout.strip()
print("GPU detectada:", gpu_info)

import torch
print(f"PyTorch {torch.__version__}")
print(f"CUDA disponible: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"Dispositivo: {torch.cuda.get_device_name(0)}")
    mem_gib = torch.cuda.get_device_properties(0).total_memory / 1024**3
    print(f"VRAM total: {mem_gib:.1f} GiB")
    if "A100" in torch.cuda.get_device_name(0):
        print("✅ A100 detectado — parámetros A100 activos")
    else:
        print("⚠️  GPU no es A100 — se usarán parámetros conservadores")
"""))

# ── 2. CLONE REPO ────────────────────────────────────────────────────────────
cells.append(code("""\
# Clonar repositorio con todos los submódulos (backends HARL, MARLlib, off-policy, MAAC)
import os

REPO_URL = "https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git"
REPO_DIR = "/content/MADRLCitytleranflexresdr"

if not os.path.exists(REPO_DIR):
    print("Clonando repositorio (incluye submódulos externos)...")
    !git clone --recurse-submodules --depth 1 {REPO_URL} {REPO_DIR}
else:
    print("Repositorio ya existe, actualizando...")
    !cd {REPO_DIR} && git pull --recurse-submodules

os.chdir(REPO_DIR)
print(f"Directorio de trabajo: {os.getcwd()}")
"""))

# ── 3. INSTALL DEPS ──────────────────────────────────────────────────────────
cells.append(code("""\
# Instalar dependencias del proyecto
# CityLearn base (v2 + extensiones v3 propuestas)
!pip install -e CityLearn/ --quiet

# Backends MADRL externos
!pip install -e external/HARL/ --quiet          # HAPPO (on-policy, trust region)
!pip install -e external/MARL/src/ --quiet      # MASAC (off-policy, discrete actions)
!pip install -e external/off-policy/ --quiet    # MATD3 (off-policy, twin-critic TD3)
!pip install -e external/MAAC/ --quiet          # MAAC (attention critic SAC)

# Dependencias de análisis y visualización
!pip install scipy pandas matplotlib seaborn --quiet

print("✅ Todas las dependencias instaladas.")
"""))

# ── 4. PYTHON PATH ───────────────────────────────────────────────────────────
cells.append(code("""\
import sys, os

REPO = "/content/MADRLCitytleranflexresdr"

# Rutas que deben estar en sys.path para importar los módulos del proyecto
paths = [
    REPO,
    f"{REPO}/CityLearn",
    f"{REPO}/CityLearn/scripts",
    f"{REPO}/external/HARL",
    f"{REPO}/external/MARL/src",
    f"{REPO}/external/off-policy",
    f"{REPO}/external/MAAC",
    f"{REPO}/uc3m",
]
for p in paths:
    if p not in sys.path:
        sys.path.insert(0, p)

# Variables de entorno necesarias
os.environ["PYTHONPATH"] = ":".join(paths)
os.environ["CITYLEARN_PROJECT_ROOT"] = REPO

print("sys.path configurado:")
for p in sys.path[:10]:
    print(f"  {p}")
"""))

# ── 5. OPTIONAL GDRIVE ───────────────────────────────────────────────────────
cells.append(md("""\
### (Opcional) Montar Google Drive para persistencia de resultados

Si deseas guardar los checkpoints y artefactos en tu Google Drive (recomendado para sesiones largas), ejecuta la siguiente celda. De lo contrario, los resultados se guardarán en `/content/` y se perderán al cerrar la sesión.
"""))

cells.append(code("""\
# CELDA OPCIONAL: montar Google Drive
# Descomenta si quieres persistencia entre sesiones

# from google.colab import drive
# drive.mount('/content/drive')
# GDRIVE_BASE = "/content/drive/MyDrive/MADRL_CityLearn_v3"
# os.makedirs(GDRIVE_BASE, exist_ok=True)
# print(f"Google Drive montado en: {GDRIVE_BASE}")
"""))

# ── 6. OUTPUT ROOT ───────────────────────────────────────────────────────────
cells.append(code("""\
from datetime import datetime
import os

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPO = "/content/MADRLCitytleranflexresdr"

# Directorio raíz de resultados de esta sesión Colab
OUTPUT_ROOT = f"{REPO}/outputs/colab_madrl_{TIMESTAMP}"
os.makedirs(OUTPUT_ROOT, exist_ok=True)

# Schema del dataset Iquitos 2023-2025
SCHEMA_PATH = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"

print(f"OUTPUT_ROOT  : {OUTPUT_ROOT}")
print(f"SCHEMA_PATH  : {SCHEMA_PATH}")
print(f"Schema existe: {os.path.exists(SCHEMA_PATH)}")

# Guardar la ruta para referencia posterior
with open(f"{REPO}/outputs/latest_colab_output_root.txt", "w") as f:
    f.write(OUTPUT_ROOT)
"""))

# ── SECTION 2: DATASET ───────────────────────────────────────────────────────
cells.append(md("""\
## Sección 2: Dataset Iquitos 2023-2025

El dataset contiene datos reales de **17 edificios institucionales y comerciales** de Iquitos, Perú, con registros horarios de 2023 a 2025 (26 304 pasos).

| Recurso | Detalle |
|---|---|
| Edificios | 17 (B01–B17): hospitales, mall, aeropuerto, universidad, oficinas |
| Período | 2023-2025 · 26 304 horas |
| BESS total | 26 266 kWh / 6 648 kW |
| PV total | 48 790.9 kWp |
| EV chargers | 185 tomas · 96 equipos físicos · 1 850 EVs en pool |
| V2G | Activo en 31 tomas de camiones (B01 Electro Oriente) |
| CSV activos | 222 archivos sin NaN/Inf |
"""))

cells.append(code("""\
import json, os

SCHEMA_PATH = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"

with open(SCHEMA_PATH) as f:
    schema = json.load(f)

buildings = schema.get("buildings", {})
print(f"Edificios en schema: {len(buildings)}")
print(f"Pasos de simulación: {schema.get('simulation_end_time_step', 'N/A') + 1}")
print(f"Agente central: {schema.get('central_agent', False)}")
print()

# Mostrar los primeros 5 edificios con sus DER
for i, (name, bld) in enumerate(buildings.items()):
    if i >= 5:
        print(f"  ... y {len(buildings) - 5} edificios más")
        break
    ev = bld.get("electric_vehicle_chargers", [])
    bess = bld.get("electrical_storage", {})
    pv = bld.get("pv", {})
    print(f"  {name}: EV={len(ev)} tomas | BESS={bess.get('capacity', 'N/A')} kWh | PV={pv.get('nominal_power', 'N/A')} kWp")

# Verificar CSV del primer edificio
first_bld = list(buildings.keys())[0]
csv_path = buildings[first_bld].get("energy_simulation")
if csv_path:
    full = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/{csv_path}"
    import pandas as pd
    df = pd.read_csv(full)
    print(f"\\nPrimer edificio ({first_bld}) CSV shape: {df.shape}")
    print(df.head(3))
"""))

# ── SECTION 3: ENV ───────────────────────────────────────────────────────────
cells.append(md("""\
## Sección 3: Entorno Dec-POMDP — 17 Agentes

CityLearn v3 (propuesto) extiende CityLearn v2 con una capa **Dec-POMDP** (Decentralized Partially Observable MDP) y arquitectura **CTDE** (Centralized Training with Decentralized Execution).

### ¿Qué es Dec-POMDP?

Cada edificio es un **agente autónomo** que:
- Solo observa su propia información local (observación parcial)
- Toma decisiones locales (BESS, EV, lavadora)
- Contribuye a objetivos **distritales** compartidos

### ¿Qué es CTDE?

| Fase | Descripción |
|---|---|
| **Entrenamiento** | El crítico usa el **estado global** concat(o₁,...,o₁₇) para mejores gradientes |
| **Ejecución** | Cada agente usa **solo su observación local** oᵢ — totalmente distribuido |

```
Arquitectura:
  Edificio 1 → π₁(a₁|o₁)  ─┐
  Edificio 2 → π₂(a₂|o₂)  ─┤→ Red → V(s_global) o Q(s_global, a)  [solo entrenamiento]
  ...                        │
  Edificio 17 → π₁₇(a₁₇|o₁₇) ─┘
```
"""))

cells.append(code("""\
# Crear entorno Dec-POMDP (smoke test con 4 pasos por episodio)
import sys, os
sys.path.insert(0, f"{REPO}/CityLearn")
sys.path.insert(0, f"{REPO}/CityLearn/scripts")

from citylearn.v3.environment import make_citylearn_v3_project_env, describe_environment

env = make_citylearn_v3_project_env(
    scenario="E1",
    seed=0,
    episode_time_steps=4,           # Smoke test: 4 pasos
    reward_aggregation="team_mean", # CTDE: recompensa compartida
    normalize_observations=True,
    madrl_algorithm="MATD3",        # Cualquier algoritmo para describir
    use_citylearn_v3_reward=True,
)

desc = describe_environment(env)
print("=" * 60)
print("DESCRIPCIÓN DEL ENTORNO DEC-POMDP")
print("=" * 60)
print(f"  Capa:            {desc['version_layer']}")
print(f"  Simulador base:  {desc['simulator']}")
print(f"  Num agentes:     {desc['num_agents']}")
print(f"  Reward func:     {desc.get('reward_function', 'N/A')}")
print(f"  Reward aggr:     {desc.get('reward_aggregation', 'N/A')}")
print(f"  Obs normaliz.:   {desc.get('normalize_observations', 'N/A')}")
print(f"  Escenario:       E1 (Flexibilidad energética)")
print()
print("Dimensiones por agente:")
for agent, obs_dim in desc.get("observation_dims", {}).items():
    act_dim = desc.get("action_dims", {}).get(agent, "?")
    print(f"  {agent}: obs={obs_dim}D  acc={act_dim}D")
    break  # Solo mostrar el primero (todos iguales)
print(f"  ... (17 agentes en total, todos {list(desc.get('observation_dims', {}).values())[0]}D obs)")

env.close()
print("\\n✅ Entorno creado y cerrado correctamente.")
"""))

# ── SECTION 4: REWARD ────────────────────────────────────────────────────────
cells.append(md("""\
## Sección 4: Función de Recompensa Multiobjetivo

### CityLearnV3MADRLRewardFunction

La recompensa combina **5 componentes** con pesos distintos según el escenario:

| Componente | Descripción |
|---|---|
| **Flexibilidad (flex)** | peak_penalty + ramping_penalty + load_factor + ev_service |
| **CO₂ (carbon)** | carbon_emissions × carbon_intensity_signal |
| **Costo (cost)** | electricity_cost × price_signal |
| **EV urgency** | SOC_deficit × (1/horas_hasta_salida) |
| **BESS degradation** | C-rate penalty Arrhenius LiFePO₄ (v4) |

### Pesos por escenario

| Escenario | flex | carbon | cost | Objetivo |
|:---:|:---:|:---:|:---:|---|
| **E1** | **0.70** | 0.15 | 0.15 | Flexibilidad energética (OE1) |
| **E2** | 0.15 | **0.70** | 0.15 | Emisiones CO₂ (OE2) |
| **E3** | 0.25 | 0.15 | **0.60** | Costos energéticos (OE3) |

### Recompensa mixta CTDE

```
r_i_mix = 0.30 × r_i_local + 0.70 × team_reward
team_reward = mean(r₁, r₂, ..., r₁₇)  # cooperación distrital
```
"""))

cells.append(code("""\
# Visualizar configuración de recompensa por escenario
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

scenarios = ["E1\\nFlexibilidad", "E2\\nCO₂", "E3\\nCostos"]
weights = {
    "Flexibilidad": [0.70, 0.15, 0.25],
    "Emisiones CO₂": [0.15, 0.70, 0.15],
    "Costos energéticos": [0.15, 0.15, 0.60],
}
colors = ["#3b82f6", "#22c55e", "#f59e0b"]

fig, axes = plt.subplots(1, 3, figsize=(14, 5))
fig.suptitle("Pesos de Recompensa por Escenario (CityLearnV3MADRLRewardFunction v4)",
             fontsize=14, fontweight="bold", y=1.02)

for ax, scenario, color in zip(axes, scenarios, colors):
    vals = [w[scenarios.index(scenario.replace("\\n", "\\n"))]
            for w in weights.values()]
    # Fix index
    idx = list(scenarios).index(scenario)
    vals = [weights[k][idx] for k in weights]
    bars = ax.bar(list(weights.keys()), vals, color=["#3b82f6", "#22c55e", "#f59e0b"],
                  edgecolor="white", linewidth=1.5)
    ax.set_title(f"Escenario {scenario}", fontsize=12, fontweight="bold")
    ax.set_ylim(0, 0.85)
    ax.set_ylabel("Peso")
    ax.tick_params(axis="x", rotation=20)
    for bar, val in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.02,
                f"{val:.2f}", ha="center", fontsize=11, fontweight="bold")
    ax.axhline(0.5, color="red", linestyle="--", alpha=0.3, linewidth=1)
    ax.set_facecolor("#f8fafc")
    ax.grid(axis="y", alpha=0.3)

plt.tight_layout()
os.makedirs(f"{OUTPUT_ROOT}/figures", exist_ok=True)
plt.savefig(f"{OUTPUT_ROOT}/figures/reward_weights_by_scenario.png", dpi=150, bbox_inches="tight")
plt.show()
print(f"✅ Figura guardada: {OUTPUT_ROOT}/figures/reward_weights_by_scenario.png")
"""))

# ── SECTION 5: TRAINING CONFIG ───────────────────────────────────────────────
cells.append(md("""\
## Sección 5: Entrenamiento Completo (12 corridas · A100 optimizado)

### Estrategia de entrenamiento

- **12 corridas totales**: 4 algoritmos × 3 escenarios
- **75 episodios** por corrida · **8 760 pasos** por episodio (año completo)
- **657 000 pasos** de entorno por corrida · **7 884 000 pasos** en total
- Secuencial: HAPPO → MASAC → MATD3 → MAAC (cada escenario E1→E2→E3)

### Parámetros A100 (40/80 GB VRAM)

| Parámetro | HAPPO | MASAC | MATD3 | MAAC |
|---|---|---|---|---|
| hidden_size | 512 | 256 | 512 | 256 |
| batch_size | — | 512 | 512 | 512 |
| buffer_size (k) | — | 8192 | 8192 | — |
| episodes | 75 | 75 | 75 | 75 |
| CUDA | ✅ | ✅ | ✅ | ✅ |

> **Nota:** Para un smoke test rápido (verificar que todo funciona), ejecuta con `QUICK_TEST = True` (5 episodios, 4 pasos). Para entrenamiento completo, usa `QUICK_TEST = False`.
"""))

cells.append(code("""\
import subprocess, sys, os, json
from pathlib import Path
from datetime import datetime

# ─── Configuración principal ───────────────────────────────────────────────
REPO = "/content/MADRLCitytleranflexresdr"
OUTPUT_ROOT  # definido en la celda de configuración

SCHEMA_PATH = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
PYTHON = sys.executable

# Cambiar a True para test rápido (5 ep × 4 steps); False para entrenamiento real
QUICK_TEST = False  # ← cambiar a False para entrenamiento completo A100

if QUICK_TEST:
    EPISODES        = 5
    EPISODE_STEPS   = 4
    TOTAL_STEPS     = EPISODES * EPISODE_STEPS
    BATCH_SIZE      = 4
    BUFFER_SIZE     = 128
    HIDDEN_SIZE_HP  = 128
    HIDDEN_SIZE_OFF = 64
    print("⚠️  Modo QUICK_TEST activo — solo 5 episodios × 4 pasos para verificar pipeline")
else:
    EPISODES        = 75
    EPISODE_STEPS   = 8760          # año completo
    TOTAL_STEPS     = EPISODES * EPISODE_STEPS  # 657 000
    BATCH_SIZE      = 512           # A100 40GB puede manejar batches grandes
    BUFFER_SIZE     = 8192          # en miles → 8 192 000 transiciones
    HIDDEN_SIZE_HP  = 512
    HIDDEN_SIZE_OFF = 512
    print(f"🚀 Modo FULL TRAINING — {EPISODES} episodios × {EPISODE_STEPS} pasos = {TOTAL_STEPS:,} pasos/corrida")

SCENARIOS  = ["E1", "E2", "E3"]
ALGORITHMS = ["happo", "masac", "matd3", "maac"]
SEED       = 0

def out_dir(scenario: str, algorithm: str) -> str:
    return f"{OUTPUT_ROOT}/{scenario}/{algorithm}"

print(f"\\nOutput root: {OUTPUT_ROOT}")
print(f"Schema: {SCHEMA_PATH}")
print(f"Escenarios: {SCENARIOS}")
print(f"Algoritmos: {ALGORITHMS}")
"""))

# ── HELPER RUN FUNCTION ───────────────────────────────────────────────────────
cells.append(code("""\
import subprocess, time, sys

def run_training(cmd: list, label: str) -> int:
    \"\"\"Ejecutar entrenamiento con salida en tiempo real.\"\"\"
    print(f"\\n{'='*70}")
    print(f"  INICIANDO: {label}")
    print(f"  Comando: {' '.join(cmd[:6])} ...")
    print(f"{'='*70}")
    t0 = time.time()
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        cwd=REPO,
    )
    # Stream output — mostrar solo líneas relevantes para no saturar la celda
    keep_keywords = [
        "Episode", "episode", "Step", "step", "Reward", "reward",
        "KPI", "kpi", "ERROR", "error", "COMPLETE", "complete",
        "carbon", "peak", "cost", "DONE", "Saved", "saved",
        "E1", "E2", "E3", "happo", "masac", "matd3", "maac",
        "✅", "⚠️", "🏁",
    ]
    line_count = 0
    for line in proc.stdout:
        line = line.rstrip()
        if line_count < 20 or any(k.lower() in line.lower() for k in keep_keywords):
            print(line)
        line_count += 1
    proc.wait()
    elapsed = time.time() - t0
    status = "✅ OK" if proc.returncode == 0 else f"❌ FAILED (rc={proc.returncode})"
    print(f"  {status} — {label} — {elapsed/60:.1f} min")
    return proc.returncode
"""))

# ── HAPPO ─────────────────────────────────────────────────────────────────────
cells.append(md("""\
### HAPPO — Heterogeneous-Agent PPO (on-policy)

HAPPO realiza actualizaciones **secuenciales por agente** con trust region individual.
Cada agente actualiza su política usando el gradiente del crítico centralizado,
manteniendo un ratio de probabilidad entre política nueva y antigua (PPO clip).

**Backend:** `external/HARL/`
"""))

cells.append(code("""\
import os, sys

happo_script = f"{REPO}/CityLearn/scripts/train_citylearn_v3_happo.py"
happo_results = {}

for scenario in SCENARIOS:
    odir = out_dir(scenario, "happo")
    os.makedirs(odir, exist_ok=True)

    cmd = [
        PYTHON, "-B", happo_script,
        "--schema-path", SCHEMA_PATH,
        "--scenario", scenario,
        "--seed", str(SEED),
        "--episode-time-steps", str(EPISODE_STEPS),
        "--episodes", str(EPISODES),
        "--num-env-steps", str(TOTAL_STEPS),
        "--hidden-size", str(HIDDEN_SIZE_HP),
        "--output-dir", odir,
        "--artifact-profile", "full",
        "--trace-record-interval", "10",
        "--trace-detail", "compact",
        "--live-progress-interval", "1000",
        "--gpu-profile", "aws",       # perfil para GPU servidor
        "--cuda",
    ]

    rc = run_training(cmd, f"HAPPO {scenario}")
    happo_results[scenario] = rc
    print(f"HAPPO {scenario}: {'✅ OK' if rc == 0 else '❌ FAILED'}")

print("\\nResumen HAPPO:", happo_results)
"""))

# ── MASAC ────────────────────────────────────────────────────────────────────
cells.append(md("""\
### MASAC — Multi-Agent SAC Discreto (off-policy)

MASAC usa un **Q-mixer centralizado** y entropía máxima.
Las acciones son **discretas por eje** (BESS / EV / Lavadora), mapeadas al espacio continuo de CityLearn.

**Backend:** `external/MARL/src/`
"""))

cells.append(code("""\
masac_script = f"{REPO}/CityLearn/scripts/train_citylearn_v3_masac.py"
masac_results = {}

for scenario in SCENARIOS:
    odir = out_dir(scenario, "masac")
    os.makedirs(odir, exist_ok=True)

    cmd = [
        PYTHON, "-B", masac_script,
        "--schema-path", SCHEMA_PATH,
        "--scenario", scenario,
        "--seed", str(SEED),
        "--episode-time-steps", str(EPISODE_STEPS),
        "--episodes", str(EPISODES),
        "--action-bins", "3",
        "--batch-size", str(BATCH_SIZE),
        "--buffer-size", str(BUFFER_SIZE),
        "--output-dir", odir,
        "--artifact-profile", "full",
        "--trace-record-interval", "10",
        "--trace-detail", "compact",
        "--live-progress-interval", "1000",
        "--gpu-profile", "aws",
        "--cuda",
    ]

    rc = run_training(cmd, f"MASAC {scenario}")
    masac_results[scenario] = rc
    print(f"MASAC {scenario}: {'✅ OK' if rc == 0 else '❌ FAILED'}")

print("\\nResumen MASAC:", masac_results)
"""))

# ── MATD3 ────────────────────────────────────────────────────────────────────
cells.append(md("""\
### MATD3 — Multi-Agent TD3 (off-policy · **GANADOR v4**)

MATD3 usa **doble crítico** para evitar sobreestimación del Q-value, con:
- Policy delay: el actor se actualiza cada 2 pasos del crítico
- Target noise: ruido sobre las acciones objetivo para suavizar el Q

**Resultado v4:** Score global MATD3 = 0.7445 (KW p=0.0459, MWU vs HAPPO p=0.0182)

**Backend:** `external/off-policy/`
"""))

cells.append(code("""\
matd3_script = f"{REPO}/CityLearn/scripts/train_citylearn_v3_matd3.py"
matd3_results = {}

for scenario in SCENARIOS:
    odir = out_dir(scenario, "matd3")
    os.makedirs(odir, exist_ok=True)

    cmd = [
        PYTHON, "-B", matd3_script,
        "--schema-path", SCHEMA_PATH,
        "--scenario", scenario,
        "--seed", str(SEED),
        "--episode-time-steps", str(EPISODE_STEPS),
        "--episodes", str(EPISODES),
        "--num-env-steps", str(TOTAL_STEPS),
        "--batch-size", str(BATCH_SIZE),
        "--buffer-size", str(BUFFER_SIZE),
        "--hidden-size", str(HIDDEN_SIZE_OFF),
        "--gamma", "0.9999",          # alto para horizonte anual (8760 steps)
        "--lr", "3e-4",
        "--output-dir", odir,
        "--artifact-profile", "full",
        "--trace-record-interval", "10",
        "--trace-detail", "compact",
        "--live-progress-interval", "1000",
        "--gpu-profile", "aws",
        "--cuda",
    ]

    rc = run_training(cmd, f"MATD3 {scenario}")
    matd3_results[scenario] = rc
    print(f"MATD3 {scenario}: {'✅ OK' if rc == 0 else '❌ FAILED'}")

print("\\nResumen MATD3:", matd3_results)
"""))

# ── MAAC ─────────────────────────────────────────────────────────────────────
cells.append(md("""\
### MAAC — Multi-Agent Attention Critic (off-policy)

MAAC usa **atención multi-cabeza** en el crítico para ponderar la contribución
de cada agente al Q-value global. El actor es estocástico (SAC-like).

**Backend:** `external/MAAC/`
"""))

cells.append(code("""\
maac_script = f"{REPO}/CityLearn/scripts/train_citylearn_v3_maac.py"
maac_results = {}

for scenario in SCENARIOS:
    odir = out_dir(scenario, "maac")
    os.makedirs(odir, exist_ok=True)

    cmd = [
        PYTHON, "-B", maac_script,
        "--schema-path", SCHEMA_PATH,
        "--scenario", scenario,
        "--seed", str(SEED),
        "--episode-time-steps", str(EPISODE_STEPS),
        "--episodes", str(EPISODES),
        "--batch-size", str(BATCH_SIZE),
        "--action-bins", "3",
        "--attend-heads", "4",
        "--output-dir", odir,
        "--artifact-profile", "full",
        "--trace-record-interval", "10",
        "--trace-detail", "compact",
        "--live-progress-interval", "1000",
        "--gpu-profile", "aws",
        "--cuda",
    ]

    rc = run_training(cmd, f"MAAC {scenario}")
    maac_results[scenario] = rc
    print(f"MAAC {scenario}: {'✅ OK' if rc == 0 else '❌ FAILED'}")

print("\\nResumen MAAC:", maac_results)
"""))

# ── SECTION 6: RESULTS ───────────────────────────────────────────────────────
cells.append(md("""\
## Sección 6: Análisis de Resultados y KPIs

Los artefactos de cada corrida siguen la estructura canónica:

```
{OUTPUT_ROOT}/{escenario}/{algoritmo}/{escenario}_seed_0/
  data/
    results.json          ← KPIs finales de CityLearn v2
    training_summary.json ← resumen de entrenamiento
    timeseries.csv        ← reward y KPIs por episodio
    trace.csv             ← trace por agente y paso
  checkpoints/            ← modelos .pt guardados
  figures/                ← 13 figuras PNG
    tables/               ← tablas CSV y Markdown
```
"""))

cells.append(code("""\
import json, os, glob
import pandas as pd
import numpy as np

def load_results(output_root: str) -> pd.DataFrame:
    \"\"\"Cargar todos los results.json y construir DataFrame comparativo.\"\"\"
    records = []
    pattern = f"{output_root}/*/*/*/data/results.json"
    files = glob.glob(pattern, recursive=True)

    for fp in sorted(files):
        parts = fp.replace(output_root, "").split(os.sep)
        # estructura: /scenario/algorithm/scenario_seed_0/data/results.json
        scenario  = parts[1] if len(parts) > 1 else "?"
        algorithm = parts[2] if len(parts) > 2 else "?"
        try:
            with open(fp) as f:
                data = json.load(f)
            # Extraer KPIs principales
            rec = {
                "algorithm": algorithm.upper(),
                "scenario":  scenario,
                "peak_average":            data.get("peak_average", np.nan),
                "ramping_average":         data.get("ramping_average", np.nan),
                "load_factor_average":     data.get("load_factor_average", np.nan),
                "carbon_emissions":        data.get("carbon_emissions", np.nan),
                "electricity_cost":        data.get("electricity_cost", np.nan),
                "ev_departure_success_rate": data.get("ev_departure_success_rate", np.nan),
                "pv_self_consumption_ratio": data.get("pv_self_consumption_ratio", np.nan),
            }
            records.append(rec)
        except Exception as e:
            print(f"  ⚠️  No se pudo leer {fp}: {e}")

    if not records:
        print("⚠️  No se encontraron results.json — ejecuta el entrenamiento primero.")
        return pd.DataFrame()
    return pd.DataFrame(records)


df_results = load_results(OUTPUT_ROOT)
if not df_results.empty:
    print(f"✅ {len(df_results)} corridas cargadas\\n")
    pd.set_option("display.float_format", "{:.4f}".format)
    pd.set_option("display.max_columns", 20)
    print(df_results.to_string(index=False))
    os.makedirs(f"{OUTPUT_ROOT}/evaluation", exist_ok=True)
    df_results.to_csv(f"{OUTPUT_ROOT}/evaluation/all_results_kpis.csv", index=False)
    print(f"\\nGuardado: {OUTPUT_ROOT}/evaluation/all_results_kpis.csv")
else:
    print("(Sin resultados disponibles aún)")
"""))

# ── LOAD TIMESERIES ───────────────────────────────────────────────────────────
cells.append(code("""\
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import glob, os
import pandas as pd

def load_timeseries(output_root: str) -> dict:
    \"\"\"Cargar curvas de convergencia (timeseries.csv) de todas las corridas.\"\"\"
    ts_data = {}
    pattern = f"{output_root}/*/*/*/data/timeseries.csv"
    for fp in sorted(glob.glob(pattern, recursive=True)):
        parts = fp.replace(output_root, "").split(os.sep)
        scenario  = parts[1] if len(parts) > 1 else "?"
        algorithm = parts[2].upper() if len(parts) > 2 else "?"
        key = f"{algorithm}_{scenario}"
        try:
            df = pd.read_csv(fp)
            ts_data[key] = df
        except Exception:
            pass
    return ts_data

ts = load_timeseries(OUTPUT_ROOT)

if ts:
    fig, axes = plt.subplots(1, 3, figsize=(18, 5))
    scenario_labels = {"E1": "Flexibilidad (OE1)", "E2": "CO₂ (OE2)", "E3": "Costos (OE3)"}
    colors_alg = {"HAPPO": "#3b82f6", "MASAC": "#a21caf", "MATD3": "#16a34a", "MAAC": "#d97706"}

    for ax, (sc_code, sc_label) in zip(axes, scenario_labels.items()):
        for key, df in ts.items():
            if f"_{sc_code}" in key:
                alg = key.replace(f"_{sc_code}", "")
                reward_col = next(
                    (c for c in df.columns if "reward" in c.lower()), None)
                if reward_col and len(df) > 0:
                    ax.plot(df.index, df[reward_col].rolling(3, min_periods=1).mean(),
                            label=alg, color=colors_alg.get(alg, "gray"),
                            linewidth=2, alpha=0.85)
        ax.set_title(f"Escenario {sc_code}: {sc_label}", fontweight="bold")
        ax.set_xlabel("Episodio")
        ax.set_ylabel("Reward medio (smoothed)")
        ax.legend(loc="lower right", fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_facecolor("#f8fafc")

    fig.suptitle("Convergencia de Recompensa — 4 Algoritmos × 3 Escenarios",
                 fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_ROOT}/evaluation/convergence_all.png", dpi=150, bbox_inches="tight")
    plt.show()
    print(f"✅ Figura guardada: {OUTPUT_ROOT}/evaluation/convergence_all.png")
else:
    print("Sin datos de timeseries disponibles.")
"""))

# ── KPI HEATMAP ───────────────────────────────────────────────────────────────
cells.append(code("""\
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

if not df_results.empty:
    # Heatmap de KPIs normalizados: mejor = más azul
    # Para peak/ramping/carbon/cost: MENOR es mejor → invertir
    # Para load_factor/ev_success/pv_self: MAYOR es mejor

    kpi_cols = ["peak_average", "carbon_emissions", "electricity_cost",
                "ev_departure_success_rate", "pv_self_consumption_ratio"]
    invert = {"peak_average", "carbon_emissions", "electricity_cost"}  # lower is better

    pivot_list = []
    for sc in ["E1", "E2", "E3"]:
        sub = df_results[df_results["scenario"] == sc].set_index("algorithm")[kpi_cols]
        for col in kpi_cols:
            col_vals = sub[col].astype(float)
            lo, hi = col_vals.min(), col_vals.max()
            rng = hi - lo if hi > lo else 1.0
            normalized = (col_vals - lo) / rng
            if col in invert:
                normalized = 1 - normalized
            sub[col] = normalized
        sub.columns = [f"{c}\\n({sc})" for c in kpi_cols]
        pivot_list.append(sub)

    combined = pd.concat(pivot_list, axis=1).fillna(0)

    fig, ax = plt.subplots(figsize=(18, 5))
    im = ax.imshow(combined.values, cmap="Blues", aspect="auto", vmin=0, vmax=1)
    ax.set_yticks(range(len(combined.index)))
    ax.set_yticklabels(combined.index, fontsize=11)
    ax.set_xticks(range(len(combined.columns)))
    ax.set_xticklabels(combined.columns, fontsize=8, rotation=45, ha="right")
    for i in range(len(combined.index)):
        for j in range(len(combined.columns)):
            v = combined.values[i, j]
            ax.text(j, i, f"{v:.2f}", ha="center", va="center",
                    fontsize=8, color="white" if v > 0.6 else "black")
    plt.colorbar(im, ax=ax, label="Score normalizado (1=mejor)")
    ax.set_title("KPIs Normalizados por Algoritmo y Escenario", fontweight="bold", fontsize=13)
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_ROOT}/evaluation/kpi_heatmap.png", dpi=150, bbox_inches="tight")
    plt.show()
    print(f"✅ Figura guardada: {OUTPUT_ROOT}/evaluation/kpi_heatmap.png")
"""))

# ── SECTION 7: STATISTICAL TESTS ─────────────────────────────────────────────
cells.append(md("""\
## Sección 7: Evaluación Estadística — Selección del Mejor MADRL

Para determinar si las diferencias entre algoritmos son **estadísticamente significativas**
seguimos el mismo protocolo usado en el análisis oficial del proyecto:

1. **Shapiro-Wilk** — ¿Son normales las distribuciones de KPIs? → Si no, usar tests no paramétricos
2. **Kruskal-Wallis** — ¿Hay diferencia global entre los 4 algoritmos?
3. **Mann-Whitney U** — ¿Qué pares de algoritmos difieren? + Effect size (Cliff's δ)
4. **Wilcoxon Signed-Rank** — Diferencias sistemáticas en pares (muestras pareadas)

**Resultado oficial v4:** MATD3 es el mejor MADRL global (KW p=0.0459 < 0.05)
"""))

cells.append(code("""\
from scipy import stats
import numpy as np
import pandas as pd
import itertools
import json, os

def cliff_delta(x, y):
    \"\"\"Effect size: Cliff's delta ∈ [-1, 1]. |d|>0.33 = large.\"\"\"
    n1, n2 = len(x), len(y)
    dom = sum(1 for xi in x for yj in y if xi > yj) - sum(1 for xi in x for yj in y if xi < yj)
    return dom / (n1 * n2)

def run_statistical_analysis(df: pd.DataFrame, output_dir: str) -> dict:
    \"\"\"Ejecutar suite completa de pruebas estadísticas.\"\"\"
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    # KPIs de comparación (normalizados: mayor es mejor)
    kpi_main = ["peak_average", "carbon_emissions", "electricity_cost"]
    kpi_invert = {"peak_average", "carbon_emissions", "electricity_cost"}
    algorithms = sorted(df["algorithm"].unique())

    # ── Construir scores por escenario ─────────────────────────────────────
    scenario_weights = {
        "E1": {"peak_average": 0.50, "carbon_emissions": 0.25, "electricity_cost": 0.25},
        "E2": {"peak_average": 0.25, "carbon_emissions": 0.50, "electricity_cost": 0.25},
        "E3": {"peak_average": 0.25, "carbon_emissions": 0.25, "electricity_cost": 0.50},
    }
    scores_per_alg = {alg: [] for alg in algorithms}

    for sc, weights_sc in scenario_weights.items():
        sub = df[df["scenario"] == sc].copy()
        if sub.empty:
            continue
        for kpi, w in weights_sc.items():
            if kpi not in sub.columns:
                continue
            vals = sub[kpi].astype(float)
            lo, hi = vals.min(), vals.max()
            rng = hi - lo if hi > lo else 1.0
            normalized = (vals - lo) / rng
            if kpi in kpi_invert:
                normalized = 1 - normalized
            sub[f"{kpi}_norm"] = normalized
        norm_cols = [f"{k}_norm" for k in weights_sc if f"{k}_norm" in sub.columns]
        w_arr = np.array([weights_sc[k] for k in weights_sc if f"{k}_norm" in sub.columns])
        w_arr /= w_arr.sum()
        sub["weighted_score"] = sum(
            sub[nc] * wt for nc, wt in zip(norm_cols, w_arr)
        )
        for alg in algorithms:
            v = sub[sub["algorithm"] == alg]["weighted_score"].values
            if len(v) > 0:
                scores_per_alg[alg].append(float(v[0]))

    score_arrays = {alg: np.array(v) for alg, v in scores_per_alg.items() if v}

    # ── Shapiro-Wilk ───────────────────────────────────────────────────────
    sw_results = {}
    print("\\n1. SHAPIRO-WILK (normalidad)")
    print("-" * 50)
    for alg, arr in score_arrays.items():
        if len(arr) < 3:
            sw_results[alg] = {"stat": None, "p": None, "normal": None}
            print(f"  {alg}: muestras insuficientes (<3)")
            continue
        stat, p = stats.shapiro(arr)
        normal = p > 0.05
        sw_results[alg] = {"stat": float(stat), "p": float(p), "normal": bool(normal)}
        print(f"  {alg}: W={stat:.4f}, p={p:.4f} — {'NORMAL ✅' if normal else 'NO NORMAL ⚠️'}")
    results["shapiro_wilk"] = sw_results

    # ── Kruskal-Wallis ─────────────────────────────────────────────────────
    print("\\n2. KRUSKAL-WALLIS (diferencia global)")
    print("-" * 50)
    groups = [score_arrays[alg] for alg in algorithms if alg in score_arrays and len(score_arrays[alg]) > 0]
    if len(groups) >= 2:
        kw_stat, kw_p = stats.kruskal(*groups)
        kw_sig = kw_p < 0.05
        print(f"  H={kw_stat:.4f}, p={kw_p:.4f} — {'SIGNIFICATIVO ✅' if kw_sig else 'No significativo'}")
        results["kruskal_wallis"] = {"stat": float(kw_stat), "p": float(kw_p), "significant": kw_sig}
    else:
        print("  Insuficientes grupos para KW.")
        results["kruskal_wallis"] = None

    # ── Mann-Whitney U ─────────────────────────────────────────────────────
    print("\\n3. MANN-WHITNEY U (pairwise)")
    print("-" * 50)
    mwu_results = {}
    for a1, a2 in itertools.combinations(algorithms, 2):
        if a1 not in score_arrays or a2 not in score_arrays:
            continue
        arr1, arr2 = score_arrays[a1], score_arrays[a2]
        if len(arr1) < 1 or len(arr2) < 1:
            continue
        try:
            mwu_stat, mwu_p = stats.mannwhitneyu(arr1, arr2, alternative="two-sided")
            delta = cliff_delta(arr1.tolist(), arr2.tolist())
            sig = mwu_p < 0.05
            winner = a1 if np.mean(arr1) > np.mean(arr2) else a2
            key = f"{a1}_vs_{a2}"
            mwu_results[key] = {
                "stat": float(mwu_stat), "p": float(mwu_p),
                "significant": sig, "cliff_delta": float(delta), "winner": winner
            }
            print(f"  {a1} vs {a2}: p={mwu_p:.4f} {'✅' if sig else ''} | "
                  f"Cliff δ={delta:.3f} | Winner: {winner}")
        except Exception as e:
            print(f"  {a1} vs {a2}: ERROR {e}")
    results["mann_whitney_u"] = mwu_results

    # ── Score global ranking ───────────────────────────────────────────────
    print("\\n4. RANKING GLOBAL")
    print("-" * 50)
    ranking = []
    for alg in algorithms:
        if alg in score_arrays and len(score_arrays[alg]) > 0:
            ranking.append({"algorithm": alg, "mean_score": float(np.mean(score_arrays[alg])),
                            "scores": score_arrays[alg].tolist()})
    ranking.sort(key=lambda x: -x["mean_score"])
    for i, r in enumerate(ranking, 1):
        print(f"  {i}. {r['algorithm']}: {r['mean_score']:.4f}")
    results["ranking"] = ranking
    if ranking:
        results["best_madrl"] = ranking[0]["algorithm"]
        print(f"\\n  ★ MEJOR MADRL: {ranking[0]['algorithm']}")

    # Guardar resultados
    out_path = f"{output_dir}/statistical_analysis.json"
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2, default=str)
    print(f"\\n✅ Análisis guardado: {out_path}")
    return results


stat_results = {}
if not df_results.empty:
    stat_results = run_statistical_analysis(df_results, f"{OUTPUT_ROOT}/evaluation")
else:
    print("⚠️  Sin datos para análisis estadístico — ejecuta el entrenamiento primero.")
    print("   (Resultado oficial v4: MATD3 KW p=0.0459, MWU MATD3 vs HAPPO p=0.0182)")
"""))

# ── FINAL SUMMARY ─────────────────────────────────────────────────────────────
cells.append(code("""\
# Resumen final de la sesión Colab
import json, os, glob

print("=" * 65)
print("  RESUMEN FINAL — MADRL CityLearn v3 Colab A100")
print("=" * 65)
print(f"  Output root: {OUTPUT_ROOT}")

# Contar artefactos generados
json_files   = glob.glob(f"{OUTPUT_ROOT}/**/*.json", recursive=True)
csv_files    = glob.glob(f"{OUTPUT_ROOT}/**/*.csv",  recursive=True)
png_files    = glob.glob(f"{OUTPUT_ROOT}/**/*.png",  recursive=True)
ckpt_files   = glob.glob(f"{OUTPUT_ROOT}/**/*.pt",   recursive=True)
print(f"  Archivos JSON    : {len(json_files)}")
print(f"  Archivos CSV     : {len(csv_files)}")
print(f"  Figuras PNG      : {len(png_files)}")
print(f"  Checkpoints .pt  : {len(ckpt_files)}")

# Mostrar ranking si disponible
if stat_results and "ranking" in stat_results:
    print("\\n  RANKING DE ALGORITMOS:")
    for i, r in enumerate(stat_results["ranking"], 1):
        marker = " ★" if i == 1 else ""
        print(f"    {i}. {r['algorithm']}: {r['mean_score']:.4f}{marker}")
    best = stat_results.get("best_madrl", "N/A")
    print(f"\\n  ★ MEJOR MADRL: {best}")
    kw = stat_results.get("kruskal_wallis", {}) or {}
    if kw:
        p = kw.get("p", "N/A")
        sig = "✅ Significativo" if kw.get("significant") else "No significativo"
        print(f"  Kruskal-Wallis: p={p} — {sig}")
else:
    print("\\n  Referencia oficial v4:")
    print("  1. MATD3: 0.7445 ★")
    print("  2. MASAC: ~0.73")
    print("  3. MAAC:  ~0.72")
    print("  4. HAPPO: ~0.70")
    print("  Kruskal-Wallis: p=0.0459 ✅ Significativo")

# Guardar resumen de sesión
summary = {
    "timestamp": TIMESTAMP,
    "output_root": OUTPUT_ROOT,
    "quick_test": QUICK_TEST,
    "episodes": EPISODES,
    "episode_time_steps": EPISODE_STEPS,
    "total_steps_per_run": TOTAL_STEPS,
    "scenarios": SCENARIOS,
    "algorithms": ALGORITHMS,
    "artifacts": {
        "json_files": len(json_files),
        "csv_files": len(csv_files),
        "png_files": len(png_files),
        "checkpoint_files": len(ckpt_files),
    },
    "statistical_analysis": stat_results if stat_results else "see official v4 results",
}
with open(f"{OUTPUT_ROOT}/colab_session_summary.json", "w") as f:
    json.dump(summary, f, indent=2, default=str)
print(f"\\n  Resumen guardado: {OUTPUT_ROOT}/colab_session_summary.json")
print("=" * 65)
"""))

cells.append(md("""\
## Próximos pasos

1. **Descargar resultados**: Usa el panel de archivos de Colab para descargar `outputs/colab_madrl_*/`
2. **Google Drive**: Si montaste Drive, los resultados ya están en `MyDrive/MADRL_CityLearn_v3/`
3. **Análisis adicional**: Ejecuta `CityLearn/scripts/generate_thesis_objective_evidence.py` con los artefactos generados
4. **Comparación con baseline RBC/SAC v2**: Usa `CityLearn/scripts/benchmark_citylearn_v2_agents.py`

---

**Referencia del proyecto:**
Repositorio: [Mac-Tapia/MADRLCitytleranflexresdr](https://github.com/Mac-Tapia/MADRLCitytleranflexresdr)
Contacto: mac.tapia@unmsm.edu.pe
Universidad Nacional Mayor de San Marcos — 2026
"""))


# ── ASSEMBLE NOTEBOOK ────────────────────────────────────────────────────────
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

nb_size_kb = OUT.stat().st_size / 1024
print(f"Notebook generado: {OUT}")
print(f"Celdas: {len(cells)}")
print(f"Tamaño: {nb_size_kb:.1f} KB")
