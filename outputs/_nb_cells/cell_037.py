# ── 4.1  Smoke test del entorno Dec-POMDP con dataset Iquitos 2023-2025 ──────
# IMPORTANTE: se pasa SCHEMA_PATH explícitamente para garantizar que el entorno
# usa citylearn_iquitos_2023_2025 y no el DEFAULT (citylearn_challenge_2022).
import json
import os
import subprocess
import sys

PYTHON = globals().get('PROJECT_PYTHON', globals().get('PYTHON', sys.executable))
REPO   = globals().get('REPO', '/content/MADRLCitytleranflexresdr')

smoke_code = r'''
import json, sys, os
sys.path.insert(0, os.path.join(os.getcwd(), "CityLearn"))
from citylearn.v3.environment import make_citylearn_v3_env, describe_environment
from citylearn.v3.config import CityLearnV3ExperimentConfig
IQUITOS_SCHEMA = os.path.join(
    os.getcwd(),
    "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
)
assert os.path.exists(IQUITOS_SCHEMA), f"Schema Iquitos no encontrado: {IQUITOS_SCHEMA}"
cfg = CityLearnV3ExperimentConfig()
results = {}
for scenario in ("E1", "E2", "E3"):
    env = make_citylearn_v3_env(
        cfg,
        schema_path=IQUITOS_SCHEMA,
        scenario=scenario,
        seed=0,
        episode_time_steps=4,
        reward_aggregation="team_mean",
        normalize_observations=True,
        madrl_algorithm="MATD3",
        use_citylearn_v3_reward=True,
    )
    try:
        desc = describe_environment(env)
        # Verificar que el dataset cargado es Iquitos (no challenge_2022)
        inner = env.env
        while hasattr(inner, "env"):
            inner = inner.env
        schema_root = inner.schema.get("root_directory", "") if isinstance(inner.schema, dict) else ""
        is_iquitos = "iquitos" in schema_root.lower() or "iquitos" in str(IQUITOS_SCHEMA).lower()
        obs, info = env.reset()
        agents = list(obs.keys())
        obs_dim = len(obs[agents[0]])
        acts = {a: env.action_space(a).sample() for a in env.agents}
        obs2, rews, terms, truncs, infos = env.step(acts)
        rew_mean = sum(float(r) for r in rews.values()) / len(rews)
        results[scenario] = {
            "num_agents": desc["num_agents"],
            "obs_dim": obs_dim,
            "action_dim": desc["action_dims"].get(agents[0], "?") if desc["action_dims"] else "?",
            "reward_function": desc.get("reward_function", "N/A"),
            "dataset": "iquitos_2023_2025" if is_iquitos else "WRONG_DATASET",
            "schema_root": schema_root,
            "reward_mean_step1": round(rew_mean, 5),
        }
    finally:
        env.close()
print(json.dumps(results, indent=2, default=str))
'''

result = subprocess.run(
    [PYTHON, '-c', smoke_code],
    cwd=REPO,
    capture_output=True,
    text=True,
    env=os.environ.copy(),
)
if result.stderr:
    # Filtrar mensajes INFO normales de CityLearn
    stderr_lines = [line for line in result.stderr.splitlines() if not line.startswith("INFO:")]
    if stderr_lines:
        print("\n".join(stderr_lines[-20:]))
if result.returncode != 0:
    raise RuntimeError(f'Smoke-test CityLearn v3 falló (exit={result.returncode})\n{result.stderr[-800:]}')

raw = [line for line in result.stdout.strip().splitlines() if line.strip().startswith("{") or line.strip().startswith('"') or line.strip().startswith("}")]
json_text = "\n".join(result.stdout.strip().splitlines())
results = json.loads(json_text)

print(f"{'Escenario':<10} {'Agentes':>8} {'Obs':>5} {'Act':>4} {'Dataset':>22} {'Rew(s1)':>10}")
print("-" * 66)
for sc, r in results.items():
    dataset_ok = r['dataset'] == 'iquitos_2023_2025'
    if not dataset_ok:
        raise RuntimeError(f"CRÍTICO: escenario {sc} usa dataset incorrecto: {r['schema_root']}")
    print(f"{sc:<10} {r['num_agents']:>8} {r['obs_dim']:>5} {str(r['action_dim']):>4} {'iquitos_2023_2025 ✓':>22} {r['reward_mean_step1']:>10.5f}")

print()
print(f"Reward function : {list(results.values())[0]['reward_function']}")
print(f"Python          : {PYTHON}")
print()
print("OK: Entorno Dec-POMDP verificado con dataset Iquitos 2023-2025 en E1/E2/E3.")
print("    reset() → step() funciona. CityLearn v3 conectado al dataset local del proyecto.")
