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
# Test 3 — Notebook JSON válido y parámetros del launcher
#
# The notebook now delegates all training to colab_a100_official_launcher.py.
# Per-algorithm flags live in the launcher, not the notebook. We check both.
# ────────────────────────────────────────────────────────────────────────────
NB = Path(f"{REPO}/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
with open(NB, encoding="utf-8") as f:
    nb = json.load(f)
assert nb["nbformat"] == 4
assert nb["metadata"]["colab"]["gpuType"] == "A100"
assert nb["metadata"].get("accelerator") == "GPU"

cells   = nb["cells"]
cell_ids = [c.get("id") for c in cells]
code_src = "\n".join(
    "".join(c["source"]) for c in cells if c["cell_type"] == "code"
)
dirty_code_cells = [
    (i, c.get("id"), c.get("execution_count"), len(c.get("outputs", [])))
    for i, c in enumerate(cells)
    if c["cell_type"] == "code" and (c.get("execution_count") is not None or c.get("outputs"))
]
assert not dirty_code_cells, f"Notebook contiene outputs/execution_count: {dirty_code_cells[:5]}"

LAUNCHER_PATH = Path(f"{REPO}/CityLearn/scripts/colab_a100_official_launcher.py")
assert LAUNCHER_PATH.exists(), f"Launcher no encontrado: {LAUNCHER_PATH}"
launcher_src = LAUNCHER_PATH.read_text(encoding="utf-8")

# Check notebook references the launcher correctly
assert "colab_a100_official_launcher.py" in code_src, \
    "Notebook no referencia colab_a100_official_launcher.py"
assert "--require-a100" in code_src, "Notebook no pasa --require-a100 al launcher"
assert "--oom-retry" in code_src, "Notebook no pasa --oom-retry al launcher"
assert "--skip-completed" in code_src, "Notebook no pasa --skip-completed al launcher"
assert "--dry-run" in code_src, "Notebook no incluye --dry-run (preflight)"
assert "--include-baselines" not in code_src, \
    "Notebook no debe activar MAPPO/MADDPG en el launcher v3 oficial"

required_order = [
    "e6bd10e8",          # 1.1 GPU
    "c06557c1",          # 1.2 clone validated branch
    "repo_mirror_verify",# 1.2b project mirror
    "188059f1",          # 1.3 deps
    "221bf910",          # 1.4 sys.path/smoke imports
    "56e338c7",          # 1.5 Drive
    "c1f8ada9",          # 2.1 output root
    "226d3513",          # 6.1 config
    "2adf11df",          # 7.0 launcher helpers
    "3c0758f9",          # 7.1 dry-run
    "9a97f863",          # 7.2 training
]
missing_cells = [cell_id for cell_id in required_order if cell_id not in cell_ids]
assert not missing_cells, f"Faltan celdas críticas: {missing_cells}"
positions = [cell_ids.index(cell_id) for cell_id in required_order]
assert positions == sorted(positions), f"Orden crítico de celdas incorrecto: {positions}"

assert "REPO_BRANCH      = 'codex/fix-madrl-traceability-docs'" in code_src, \
    "Notebook no fija la rama codex/fix-madrl-traceability-docs del repo padre para Colab"
assert "'clone'," in code_src and "'--branch', REPO_BRANCH" in code_src, \
    "Clone de Colab no usa --branch REPO_BRANCH"
assert "git_check(['checkout', '-B', CITYLEARN_BRANCH" in code_src, \
    "Notebook no activa CityLearn en rama viva con checkout -B"
assert "cl_branch == 'HEAD'" in code_src, \
    "Notebook no repara detached HEAD de CityLearn en celda 1.2b"
assert "'submodule', 'update', '--init', '--recursive'" in code_src and "'--force'" in code_src, \
    "Notebook no fuerza submódulos al commit fijado por el repo padre"
assert "submodule_status = sh(['git', 'submodule', 'status', '--recursive'])" in code_src, \
    "Notebook no valida estado de submódulos"
assert "cl_branch == CITYLEARN_BRANCH" in code_src and "'citylearn_live': True" in code_src, \
    "Notebook no valida que CityLearn este en la rama viva esperada"
assert "csv_count == 222" in code_src, "Notebook no valida dataset completo de 222 CSV"
print("[PASS] Orden crítico y espejo repo/submódulos/dataset validados en notebook")

DEPENDENCY_GUARDS = [
    "PYTHON_MAX_EXCLUSIVE = (3, 10)",
    "Usa Python 3.9 del proyecto",
    "COMPAT_WHEELS = [",
    "'numpy==1.23.5'",
    "'pandas==2.0.3'",
    "'scipy==1.10.1'",
    "'scikit-learn==1.2.2'",
    "'matplotlib==3.7.5'",
    "'seaborn==0.12.2'",
    "CONSTRAINTS = Path('/tmp/madrl_compat.txt')",
    "--force-reinstall",
    "repair_binary_abi",
    "BINARY_DEPS = ('numpy', 'pandas', 'scipy', 'scikit-learn', 'matplotlib', 'seaborn')",
    "Verificando ABI en Python 3.9 del proyecto",
    "result = subprocess.run([PROJECT_PYTHON, '-c', ABI_CHECK], capture_output=True, text=True)",
    "'scipy'",
    "'sklearn'",
    "Esto ocurre si pip cambio numpy/scipy sin reiniciar",
]
for guard in DEPENDENCY_GUARDS:
    assert guard in code_src, f"Falta guardrail de dependencias Colab: {guard}"
print("[PASS] Dependencias Colab fijadas y smoke imports con diagnóstico ABI")

# Per-algorithm flags now live in the launcher — check launcher instead of notebook
LAUNCHER_REQUIRED = {
    "happo": [
        "--num-env-steps", "--hidden-size", "--n-rollout-threads", "--log-interval",
        "--eval-interval", "--actor-lr", "--critic-lr", "--gamma", "0.9999",
        "--action-aggregation",
    ],
    "masac": [
        "--epochs", "--action-bins", "3", "--discrete-action-mode", "axis",
        "--buffer-size", "--critic-batch-size", "--critic-train-steps",
        "--actor-sample-times", "--max-replay-buffer-gib",
        "--masac-preload-batch-device", "--gamma", "0.9999",
        "--rnn-hidden-dim", "--qmix-hidden-dim",
    ],
    "matd3": [
        "--num-env-steps", "--batch-size", "--buffer-size", "--hidden-size",
        "--train-interval", "--num-random-episodes", "--gamma", "0.9999", "--lr",
    ],
    "maac": [
        "--action-bins", "3", "--discrete-action-mode", "axis",
        "--batch-size", "--buffer-length", "--steps-per-update",
        "--num-updates", "--max-discrete-actions", "--attend-heads",
        "--gamma", "0.9999", "--pi-lr", "--q-lr", "--tau",
    ],
}
COMMON_IN_LAUNCHER = [
    "--schema-path", "--scenario", "--seed",
    "--episode-time-steps", "--output-dir",
    "--torch-threads", "--live-progress-interval",
    "--artifact-profile", "--trace-record-interval",
    "--trace-detail", "--gpu-profile",
]

missing = {}
for algo, flags in LAUNCHER_REQUIRED.items():
    for flag in flags + COMMON_IN_LAUNCHER:
        if flag not in launcher_src:
            missing.setdefault(algo, []).append(flag)

if missing:
    for algo, flags in missing.items():
        print(f"[FAIL] launcher/{algo}: faltan flags: {flags}")
    raise AssertionError("Faltan parámetros en el launcher")
print("[PASS] Todos los parámetros obligatorios presentes en el launcher")

# ────────────────────────────────────────────────────────────────────────────
# Test 4 — Layout algorithm-first correcto
# ────────────────────────────────────────────────────────────────────────────
assert "happo" in code_src, "No se usa algorithm-first layout (happo ausente)"
assert "masac" in code_src, "masac ausente en notebook"
assert "matd3" in code_src, "matd3 ausente en notebook"
assert "maac"  in code_src, "maac ausente en notebook"

# Verificar que resolve_output_dir producirá la ruta correcta
from citylearn_v3_training_common import resolve_output_dir
import tempfile
with tempfile.TemporaryDirectory() as tmp:
    odir = resolve_output_dir(f"{tmp}/HAPPO", "happo", "E1", 0)
    expected = Path(tmp) / "HAPPO" / "E1"
    assert odir == expected, f"resolve_output_dir={odir} expected={expected}"
print(f"[PASS] Layout simple: {{OUTPUT_ROOT}}/HAPPO/E1/ OK")

# ────────────────────────────────────────────────────────────────────────────
# Test 4b — Colab output isolation and resumability guardrails
# ────────────────────────────────────────────────────────────────────────────
OUTPUT_GUARDS = [
    "REQUIRE_GOOGLE_DRIVE = True",
    "GDRIVE_OUTPUT_PARENT = f'{GDRIVE_ROOT}/outputs'",
    "RUN_LABEL    = f'madrl_v3_{TIMESTAMP}'",
    "RESUME_OUTPUT_ROOT = None",
    "resumed_existing_output_root",
    "run_context_manifest.json",
    "relative_to(expected_root)",
    "len(seen_outputs) == 12",
    "outputs aislados en OUTPUT_ROOT",
]
for guard in OUTPUT_GUARDS:
    assert guard in code_src, f"Falta guardrail de aislamiento/reanudación: {guard}"

# Check launcher job construction directly without running GPU code.
import importlib.util
import tempfile

spec = importlib.util.spec_from_file_location("colab_a100_official_launcher", LAUNCHER_PATH)
launcher = importlib.util.module_from_spec(spec)
assert spec.loader is not None
spec.loader.exec_module(launcher)

with tempfile.TemporaryDirectory() as tmp:
    output_root = Path(tmp) / "colab_madrl_a100_test"
    args = launcher.parse_args([
        "--scenario", "ALL",
        "--seed", "0",
        "--episode-time-steps", "8760",
        "--episodes", "50",
        "--output-root", str(output_root),
        "--schema-path", "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json",
        "--skip-gpu-preflight",
        "--no-require-a100",
        "--no-smoke-imports",
    ])
    jobs = launcher.build_jobs(
        args,
        Path(REPO),
        output_root,
        "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json",
    )
    expected_dirs = {
        str(output_root / algo / sc)
        for algo in ["HAPPO", "MASAC", "MATD3", "MAAC"]
        for sc in ["E1", "E2", "E3"]
    }
    actual_dirs = {
        str(launcher.run_dir(output_root, str(job["name"]), str(job["scenario"]), 0))
        for job in jobs
    }
    assert len(jobs) == 12, f"Launcher planifica {len(jobs)} jobs, esperado 12"
    assert actual_dirs == expected_dirs, "Launcher no produce output dirs algorithm-first únicos bajo OUTPUT_ROOT"
    assert all(job["name"] in {"happo", "masac", "matd3", "maac"} for job in jobs), \
        "Launcher no debe planificar MAPPO/MADDPG como baseline v3"

print("[PASS] Guardrails de OUTPUT_ROOT Colab aislado y launcher 12 dirs únicos OK")

# ────────────────────────────────────────────────────────────────────────────
# Test 5 — Hiperparámetros A100 en el launcher (valores correctos)
# ────────────────────────────────────────────────────────────────────────────
# Per-algorithm values live in the launcher; notebook has high-level config only.
LAUNCHER_A100_CHECKS = {
    'parser.add_argument("--happo-hidden-size", default=512': "HAPPO hidden_size=512",
    'parser.add_argument("--masac-buffer-size", default=2': "MASAC buffer_size=2 (ep replay RAM)",
    'parser.add_argument("--masac-critic-batch-size", default=1': "MASAC critic_batch=1 (ep QMIX)",
    'parser.add_argument("--matd3-batch-size", default=1280': "MATD3 batch_size=1280",
    'parser.add_argument("--matd3-buffer-size", default=2000000': "MATD3 buffer_size=2000000",
    'parser.add_argument("--maac-batch-size", default=768': "MAAC batch_size=768",
    'parser.add_argument("--maac-buffer-length", default=1000000': "MAAC buffer_length=1000000",
    'parser.add_argument("--maac-num-updates", default=12': "MAAC num_updates=12",
    "0.9999": "gamma=0.9999 (horizonte anual)",
}
for val, desc_str in LAUNCHER_A100_CHECKS.items():
    assert val in launcher_src, f"No se encontró {desc_str} ({val}) en el launcher"

# High-level config lives in the notebook (single or double quoted strings)
NB_A100_CHECKS = {
    "aws"    : "gpu_profile=aws",
    "0.92"   : "cuda_memory_fraction=0.92",
    "50"     : "EPISODES=50",
    "8760"   : "EPISODE_STEPS=8760",
}
for val, desc_str in NB_A100_CHECKS.items():
    assert val in code_src, f"No se encontró {desc_str} ({val}) en el notebook"

print("[PASS] Todos los valores A100 correctos (launcher + notebook)")

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
    # Simular estructura simple <MADRL>/<Escenario>
    for algo in ["HAPPO","MASAC","MATD3","MAAC"]:
        for sc in ["E1","E2","E3"]:
            p = Path(tmp) / algo / sc / "data"
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
        assert algo in ["HAPPO","MASAC","MATD3","MAAC"], f"algo={algo}"
        assert scenario in ["E1","E2","E3"], f"scenario={scenario}"

print("[PASS] Glob pattern algorithm-first OK (12/12 archivos encontrados)")

# ────────────────────────────────────────────────────────────────────────────
# Test 9 — load_all_results KPI path (citylearn_v3_report.all_values)
# ────────────────────────────────────────────────────────────────────────────
# KPIs must be read from citylearn_v3_report.all_values, not root level
assert "citylearn_v3_report" in code_src, \
    "Notebook no lee KPIs de citylearn_v3_report.all_values"
assert "all_values" in code_src, \
    "Notebook no extrae all_values de citylearn_v3_report"
print("[PASS] load_all_results usa citylearn_v3_report.all_values (ruta correcta)")

# ────────────────────────────────────────────────────────────────────────────
# Test 10 — Convergence plot uses episode-level aggregation
# ────────────────────────────────────────────────────────────────────────────
assert 'groupby("episode")' in code_src, \
    "Convergence plot no agrega por episodio (groupby episode)"
assert '"reward_mean"' in code_src, \
    "Convergence plot no usa columna reward_mean explícitamente"
print("[PASS] Convergence plot agrega por episodio usando reward_mean")

# ────────────────────────────────────────────────────────────────────────────
# Resumen
# ────────────────────────────────────────────────────────────────────────────
print()
print("=" * 55)
print("  TODOS LOS TESTS PASARON [OK]")
print(f"  Notebook: {NB}")
print(f"  Celdas: {len(cells)} ({sum(1 for c in cells if c['cell_type']=='code')} código)")
print("=" * 55)
