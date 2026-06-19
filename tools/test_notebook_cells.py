"""Validate notebook cell logic: params, layout, imports, env, stats."""
import sys, os, json, datetime, subprocess, shlex
from pathlib import Path

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

SCHEMA = f"{REPO}/CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
PYTHON = sys.executable

# ────────────────────────────────────────────────────────────────────────────
# Test 1 — Dataset schema
# ────────────────────────────────────────────────────────────────────────────
with open(SCHEMA) as f:
    schema = json.load(f)
buildings = schema.get("buildings", {})
assert len(buildings) == 17, f"Expected 17 buildings, got {len(buildings)}"
assert schema.get("simulation_end_time_step") == 26303
print(f"[PASS] Schema: {len(buildings)} edificios, end_step=26303")

# ────────────────────────────────────────────────────────────────────────────
# Test 2 — Environment creation (smoke, E1)
# ────────────────────────────────────────────────────────────────────────────
from citylearn.v3.environment import make_citylearn_v3_project_env, describe_environment
env = make_citylearn_v3_project_env(
    scenario="E1", seed=0, episode_time_steps=4,
    reward_aggregation="team_mean", normalize_observations=True,
    madrl_algorithm="MATD3", use_citylearn_v3_reward=True,
)
desc = describe_environment(env)
n_agents = desc["num_agents"]
obs_dim  = list(desc.get("observation_dims", {}).values())[0]
env.close()
assert n_agents == 17,  f"Expected 17 agents, got {n_agents}"
assert obs_dim  >= 19,  f"obs_dim too small: {obs_dim}"
print(f"[PASS] Entorno Dec-POMDP: {n_agents} agentes, obs_dim={obs_dim}")

# ────────────────────────────────────────────────────────────────────────────
# Test 3 — Notebook JSON válido y parámetros completos
# ────────────────────────────────────────────────────────────────────────────
NB = Path(f"{REPO}/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
with open(NB, encoding="utf-8") as f:
    nb = json.load(f)
assert nb["nbformat"] == 4
assert nb["metadata"]["colab"]["gpuType"] == "A100"
assert nb["metadata"].get("accelerator") == "GPU"

cells   = nb["cells"]
code_src = "\n".join(
    "".join(c["source"]) for c in cells if c["cell_type"] == "code"
)

# Verificar que cada algoritmo tiene todos sus flags obligatorios
REQUIRED = {
    "happo": [
        "--episodes", "--num-env-steps", "--hidden-size", "384",
        "--n-rollout-threads", "--log-interval", "--eval-interval",
        "--actor-lr", "--critic-lr", "--gamma", "0.9999",
        "--action-aggregation",
    ],
    "masac": [
        "--episodes", "--epochs", "--action-bins", "3",
        "--discrete-action-mode", "axis",
        "--buffer-size", "25",
        "--critic-batch-size", "128",
        "--critic-train-steps", "--actor-sample-times",
        "--max-replay-buffer-gib", "20",
        "--masac-preload-batch-device", "auto",
        "--gamma", "0.9999",
        "--rnn-hidden-dim", "--qmix-hidden-dim",
    ],
    "matd3": [
        "--episodes", "--num-env-steps",
        "--batch-size", "512",
        "--buffer-size", "6000",
        "--hidden-size", "256",
        "--train-interval", "100",
        "--num-random-episodes", "1",
        "--gamma", "0.9999", "--lr",
    ],
    "maac": [
        "--episodes",
        "--action-bins", "3",
        "--discrete-action-mode", "axis",
        "--batch-size", "512",
        "--buffer-length", "100000",
        "--steps-per-update", "250",
        "--num-updates", "8",
        "--max-discrete-actions", "512",
        "--attend-heads", "4",
        "--gamma", "0.9999",
        "--pi-lr", "--q-lr", "--tau",
    ],
}
COMMON = [
    "--schema-path", "--scenario", "--seed",
    "--episode-time-steps", "--output-dir",
    "--torch-threads", "--live-progress-interval",
    "--artifact-profile", "--trace-record-interval",
    "--trace-detail", "--gpu-profile", "--cuda",
]

missing = {}
for algo, flags in REQUIRED.items():
    for flag in flags + COMMON:
        if flag not in code_src:
            missing.setdefault(algo, []).append(flag)

if missing:
    for algo, flags in missing.items():
        print(f"[FAIL] {algo}: faltan flags: {flags}")
    raise AssertionError("Faltan parámetros en el notebook")
print("[PASS] Todos los parámetros obligatorios presentes en el notebook")

# ────────────────────────────────────────────────────────────────────────────
# Test 4 — Layout algorithm-first correcto
# ────────────────────────────────────────────────────────────────────────────
assert 'out_dir("happo")' in code_src or '"happo"' in code_src, \
    "No se usa algorithm-first layout"
assert 'out_dir("masac")' in code_src or '"masac"' in code_src
assert 'out_dir("matd3")' in code_src or '"matd3"' in code_src
assert 'out_dir("maac")'  in code_src or '"maac"'  in code_src

# Verificar que resolve_output_dir producirá la ruta correcta
# --output-dir {OUTPUT_ROOT}/{algorithm} → resolve crea {algo}/{scenario}_seed_0
from citylearn_v3_training_common import resolve_output_dir
import tempfile, os
with tempfile.TemporaryDirectory() as tmp:
    odir = resolve_output_dir(f"{tmp}/happo", "happo", "E1", 0)
    expected = Path(tmp) / "happo" / "E1_seed_0"
    assert odir == expected, f"resolve_output_dir={odir} expected={expected}"
print(f"[PASS] Layout algorithm-first: {{OUTPUT_ROOT}}/happo/E1_seed_0/ OK")

# ────────────────────────────────────────────────────────────────────────────
# Test 5 — Hiperparámetros A100 en los valores correctos
# ────────────────────────────────────────────────────────────────────────────
A100_CHECKS = {
    '"384"'    : "HAPPO hidden_size=384",
    '"25"'     : "MASAC buffer_size=25",
    '"128"'    : "MASAC critic_batch=128",
    '"20"'     : "MASAC max_replay_gib=20",
    '"512"'    : "MATD3/MAAC batch_size=512",
    '"6000"'   : "MATD3 buffer_size=6000",
    '"100000"' : "MAAC buffer_length=100000",
    '"0.9999"' : "gamma=0.9999 (horizonte anual)",
    '"aws"'    : "gpu_profile=aws",
}
for val, desc_str in A100_CHECKS.items():
    assert val in code_src, f"No se encontró {desc_str} ({val}) en el notebook"
print("[PASS] Todos los valores A100 correctos en el notebook")

# ────────────────────────────────────────────────────────────────────────────
# Test 6 — Visualización reward weights
# ────────────────────────────────────────────────────────────────────────────
import matplotlib; matplotlib.use("Agg")
import matplotlib.pyplot as plt

fig, ax = plt.subplots(1, 3, figsize=(12, 4))
for axis, (sc, wts) in zip(ax, {
    "E1": [0.70, 0.15, 0.15],
    "E2": [0.15, 0.70, 0.15],
    "E3": [0.25, 0.15, 0.60],
}.items()):
    axis.bar(["Flex", "CO2", "Cost"], wts, color=["#3b82f6","#22c55e","#f59e0b"])
    axis.set_title(sc)
plt.tight_layout()
out_dir = f"{REPO}/outputs/test_notebook"
os.makedirs(out_dir, exist_ok=True)
plt.savefig(f"{out_dir}/reward_weights_test.png", dpi=72)
plt.close()
print("[PASS] Reward weights plot OK")

# ────────────────────────────────────────────────────────────────────────────
# Test 7 — Funciones estadísticas
# ────────────────────────────────────────────────────────────────────────────
from scipy import stats
import pandas as pd, numpy as np, itertools

# Datos dummy que simulan scores de 4 algoritmos en 3 escenarios
df = pd.DataFrame({
    "algorithm": ["HAPPO","MASAC","MATD3","MAAC"] * 3,
    "scenario":  ["E1"]*4 + ["E2"]*4 + ["E3"]*4,
    "peak_average":     [0.80,0.78,0.75,0.79]*3,
    "carbon_emissions": [0.88,0.86,0.85,0.87]*3,
    "electricity_cost": [0.90,0.88,0.87,0.89]*3,
})

INVERT = {"peak_average", "carbon_emissions", "electricity_cost"}
WEIGHTS = {
    "E1": {"peak_average": 0.50, "carbon_emissions": 0.25, "electricity_cost": 0.25},
    "E2": {"peak_average": 0.25, "carbon_emissions": 0.50, "electricity_cost": 0.25},
    "E3": {"peak_average": 0.25, "carbon_emissions": 0.25, "electricity_cost": 0.50},
}

scores = {"HAPPO":[], "MASAC":[], "MATD3":[], "MAAC":[]}
for sc, wts in WEIGHTS.items():
    sub = df[df["scenario"]==sc].copy()
    for kpi, w in wts.items():
        vals = sub[kpi].astype(float)
        rng  = vals.max() - vals.min()
        nrm  = (vals - vals.min()) / rng if rng > 0 else pd.Series(0.5, index=vals.index)
        sub[f"{kpi}_n"] = 1 - nrm if kpi in INVERT else nrm
    norm_cols = [f"{k}_n" for k in wts]
    w_arr = np.array(list(wts.values())); w_arr /= w_arr.sum()
    sub["score"] = sum(sub[nc]*wt for nc, wt in zip(norm_cols, w_arr))
    for a in scores:
        v = sub[sub["algorithm"]==a]["score"].values
        if len(v): scores[a].append(float(v[0]))

arrs = {a: np.array(v) for a, v in scores.items() if v}
groups = list(arrs.values())
assert len(groups) == 4
kw_h, kw_p = stats.kruskal(*groups)
print(f"[PASS] Kruskal-Wallis (dummy): H={kw_h:.3f} p={kw_p:.4f}")

ranking = sorted(arrs.items(), key=lambda x: -x[1].mean())
best = ranking[0][0]
print(f"[PASS] Ranking: {[a for a,_ in ranking]} — Mejor: {best}")

# ────────────────────────────────────────────────────────────────────────────
# Test 8 — Glob pattern para results con layout algorithm-first
# ────────────────────────────────────────────────────────────────────────────
import tempfile, glob
with tempfile.TemporaryDirectory() as tmp:
    # Simular estructura algorithm-first
    for algo in ["happo","masac","matd3","maac"]:
        for sc in ["E1","E2","E3"]:
            p = Path(tmp) / algo / f"{sc}_seed_0" / "data"
            p.mkdir(parents=True, exist_ok=True)
            (p / "results.json").write_text("{}")

    # Patrón del notebook
    found = sorted(glob.glob(f"{tmp}/*/*/data/results.json"))
    assert len(found) == 12, f"Esperaba 12 results.json, encontré {len(found)}"
    # Extraer algo y scenario correctamente
    for fp in found:
        parts = Path(fp).parts
        root_idx = next(i for i,p in enumerate(parts) if p == Path(tmp).name)
        algo     = parts[root_idx + 1]
        sc_seed  = parts[root_idx + 2]
        scenario = sc_seed.split("_seed_")[0]
        assert algo in ["happo","masac","matd3","maac"], f"algo={algo}"
        assert scenario in ["E1","E2","E3"], f"scenario={scenario}"

print("[PASS] Glob pattern algorithm-first OK (12/12 archivos encontrados)")

# ────────────────────────────────────────────────────────────────────────────
# Resumen
# ────────────────────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("  TODOS LOS TESTS PASARON [OK]")
print(f"  Notebook: {NB}")
print(f"  Celdas: {len(cells)} ({sum(1 for c in cells if c['cell_type']=='code')} código)")
print("=" * 55)
