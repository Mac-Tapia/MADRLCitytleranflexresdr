"""Smoke-test the key logic from notebook cells (runs locally without Colab)."""
import sys, os, json, datetime

REPO = "D:/MADRLCitytleranflexresdr"
paths = [
    REPO, f"{REPO}/CityLearn", f"{REPO}/CityLearn/scripts",
    f"{REPO}/external/HARL", f"{REPO}/external/MARL/src",
    f"{REPO}/external/off-policy", f"{REPO}/external/MAAC", f"{REPO}/uc3m",
]
for p in paths:
    if p not in sys.path:
        sys.path.insert(0, p)
os.environ["CITYLEARN_PROJECT_ROOT"] = REPO

# ── Test 1: Dataset schema ───────────────────────────────────────────────────
SCHEMA_PATH = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
with open(SCHEMA_PATH) as f:
    schema = json.load(f)
buildings = schema.get("buildings", {})
print(f"[PASS] Schema: {len(buildings)} edificios, end_step={schema.get('simulation_end_time_step')}")

# ── Test 2: Environment creation ─────────────────────────────────────────────
from citylearn.v3.environment import make_citylearn_v3_project_env, describe_environment
env = make_citylearn_v3_project_env(
    scenario="E1", seed=0, episode_time_steps=4,
    reward_aggregation="team_mean", normalize_observations=True,
    madrl_algorithm="MATD3", use_citylearn_v3_reward=True,
)
desc = describe_environment(env)
n_agents = desc["num_agents"]
obs_dims = list(desc.get("observation_dims", {}).values())
print(f"[PASS] Entorno Dec-POMDP: {n_agents} agentes, obs_dim={obs_dims[0] if obs_dims else '?'}")
env.close()

# ── Test 3: Reward weights plot ───────────────────────────────────────────────
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt, numpy as np
fig, ax = plt.subplots(1, 1, figsize=(6, 4))
ax.bar(["E1", "E2", "E3"], [0.70, 0.15, 0.25], color="#3b82f6")
plt.tight_layout()
os.makedirs(f"{REPO}/outputs/test_notebook", exist_ok=True)
plt.savefig(f"{REPO}/outputs/test_notebook/reward_weights_test.png", dpi=72)
plt.close()
print("[PASS] Matplotlib figure OK")

# ── Test 4: Stats imports ─────────────────────────────────────────────────────
from scipy import stats
import pandas as pd, itertools
# Dummy KW test
g1, g2, g3, g4 = [0.74, 0.75], [0.70, 0.71], [0.72, 0.73], [0.70, 0.71]
kw_stat, kw_p = stats.kruskal(g1, g2, g3, g4)
print(f"[PASS] Kruskal-Wallis (dummy data): H={kw_stat:.3f}, p={kw_p:.4f}")

# ── Test 5: Statistical analysis function ─────────────────────────────────────
import itertools

def cliff_delta(x, y):
    n1, n2 = len(x), len(y)
    dom = sum(1 for xi in x for yj in y if xi > yj) - sum(1 for xi in x for yj in y if xi < yj)
    return dom / (n1 * n2)

df = pd.DataFrame({
    "algorithm": ["HAPPO", "MASAC", "MATD3", "MAAC"] * 3,
    "scenario":  ["E1"]*4 + ["E2"]*4 + ["E3"]*4,
    "peak_average":     [0.80, 0.78, 0.75, 0.79, 0.85, 0.83, 0.80, 0.84, 0.82, 0.80, 0.77, 0.81],
    "carbon_emissions": [0.88, 0.86, 0.85, 0.87, 0.82, 0.80, 0.79, 0.81, 0.87, 0.85, 0.84, 0.86],
    "electricity_cost": [0.90, 0.88, 0.87, 0.89, 0.91, 0.89, 0.88, 0.90, 0.85, 0.83, 0.82, 0.84],
})
# Basic aggregation test
pivot = df.groupby("algorithm")[["peak_average", "carbon_emissions", "electricity_cost"]].mean()
print("[PASS] DataFrame aggregation OK")
print(pivot.round(4))

# ── Test 6: Output root creation ──────────────────────────────────────────────
TIMESTAMP = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
OUTPUT_ROOT = f"{REPO}/outputs/colab_madrl_{TIMESTAMP}"
os.makedirs(f"{OUTPUT_ROOT}/evaluation", exist_ok=True)
print(f"[PASS] Output root creado: {OUTPUT_ROOT}")

# Summary JSON
summary = {
    "timestamp": TIMESTAMP,
    "output_root": OUTPUT_ROOT,
    "test": "smoke_test_notebook_cells",
    "n_agents": n_agents,
    "obs_dim": obs_dims[0] if obs_dims else None,
}
with open(f"{OUTPUT_ROOT}/colab_session_summary.json", "w") as f:
    json.dump(summary, f, indent=2)
print("[PASS] Session summary JSON OK")
print()
print("=" * 50)
print("TODOS LOS TESTS PASARON - Notebook listo para Colab")
print("=" * 50)
