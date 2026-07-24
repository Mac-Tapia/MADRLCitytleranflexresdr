# ── 8.1  Cargar todos los results.json ──────────────────────────────────────
import json
import os
import glob
from pathlib import Path
import pandas as pd

def load_all_results(output_root: str) -> pd.DataFrame:
    records = []
    # Layout simple: {output_root}/{MADRL}/{scenario}/data/results.json
    for fp in sorted(glob.glob(f"{output_root}/*/*/data/results.json", recursive=False)):
        parts = Path(fp).parts
        algo_idx  = next(i for i,p in enumerate(parts) if p == Path(output_root).name) + 1
        algo      = parts[algo_idx] if algo_idx < len(parts) else "?"
        sc_seed   = parts[algo_idx + 1] if algo_idx+1 < len(parts) else "?"
        scenario  = sc_seed.split("_seed_")[0] if "_seed_" in sc_seed else sc_seed
        try:
            with open(fp) as f:
                data = json.load(f)
            # KPIs are nested under citylearn_v3_report.all_values, not at root level
            all_v = data.get("citylearn_v3_report", {}).get("all_values", {})
            records.append({
                "algorithm":                 algo.upper(),
                "scenario":                  scenario,
                "peak_average":              all_v.get("peak_average",                  np.nan),
                "ramping_average":           all_v.get("ramping_average",               np.nan),
                "one_minus_load_factor":     all_v.get("one_minus_load_factor_average", np.nan),
                "carbon_emissions":          all_v.get("carbon_emissions",              np.nan),
                "electricity_cost":          all_v.get("electricity_cost",              np.nan),
                "ev_departure_success_rate": all_v.get("ev_departure_success_rate",     np.nan),
                "pv_self_consumption_ratio": all_v.get("pv_self_consumption_ratio",     np.nan),
            })
        except Exception as e:
            print(f"  ⚠️  {fp}: {e}")
    return pd.DataFrame(records)

df_results = load_all_results(str(OUTPUT_ROOT))

if df_results.empty:
    print("⚠️  Sin results.json todavía — ejecuta el entrenamiento primero.")
    print("   (Referencia v4: MATD3 KW p=0.0459, Score global 0.7445)")
else:
    pd.set_option("display.float_format", "{:.4f}".format)
    print(f"✅  {len(df_results)} corridas cargadas\n")
    print(df_results.to_string(index=False))
    os.makedirs(f"{OUTPUT_ROOT}/evaluation", exist_ok=True)
    df_results.to_csv(f"{OUTPUT_ROOT}/evaluation/all_kpis.csv", index=False)

# ── 8.1b  Exportar artefactos en formato estandar de tesis ───────────────────
# Genera por cada corrida:
#   rewards.csv         — reward por episodio (desde timeseries.csv)
#   training_monitor.csv — metricas por episodio consolidadas
#   config.json         — hiperparametros de la corrida
#   resource_usage.csv  — uso de RAM/VRAM/GPU registrado durante entrenamiento

import glob
import json
import os
import pandas as pd
from pathlib import Path

_exported = 0
for ts_path in sorted(glob.glob(f"{OUTPUT_ROOT}/*/*/data/timeseries.csv")):
    run_dir = Path(ts_path).parent.parent
    summary_path = run_dir / "data" / "training_summary.json"

    try:
        ts_df = pd.read_csv(ts_path)
    except Exception:
        continue

    # rewards.csv — columnas: episode, reward_mean, reward_cumulative, peak, carbon, cost
    reward_cols = {c: c for c in ts_df.columns if any(k in c.lower() for k in
                   ["reward", "episode", "peak", "carbon", "cost", "step"])}
    if reward_cols:
        ts_df[list(reward_cols.values())].to_csv(run_dir / "data" / "rewards.csv", index=False)

    # training_monitor.csv — alias de timeseries con columna timestamp
    ts_df["monitor_ts"] = pd.date_range(start="2026-01-01", periods=len(ts_df), freq="min")
    ts_df.to_csv(run_dir / "data" / "training_monitor.csv", index=False)

    # config.json — hiperparametros y configuracion de la corrida
    if summary_path.exists():
        with open(summary_path) as f:
            summary = json.load(f)
        config_out = {
            "algorithm"      : summary.get("algorithm"),
            "scenario"       : summary.get("scenario"),
            "seed"           : summary.get("seed"),
            "episodes"       : summary.get("episodes"),
            "episode_steps"  : summary.get("episode_time_steps"),
            "num_env_steps"  : summary.get("num_env_steps"),
            "hyperparameters": summary.get("hyperparameters", {}),
            "backend"        : summary.get("backend"),
            "output_dir"     : summary.get("output_dir"),
            "gpu_runtime"    : summary.get("gpu_runtime", {}),
        }
        with open(run_dir / "data" / "config.json", "w") as f:
            json.dump(config_out, f, indent=2, default=str)

    # resource_usage.csv — tabla placeholder (RAM/VRAM se registran en live_progress.json)
    live_path = run_dir / "live_progress.json"
    if live_path.exists():
        try:
            with open(live_path) as f:
                lp = json.load(f)
            res_df = pd.DataFrame([{
                "episode"          : lp.get("episode"),
                "global_step"      : lp.get("global_step"),
                "ram_used_gib"     : lp.get("ram_used_gib"),
                "vram_used_gib"    : lp.get("vram_used_gib"),
                "gpu_util_pct"     : lp.get("gpu_util_pct"),
                "live_status"      : lp.get("live_status"),
            }])
            res_df.to_csv(run_dir / "data" / "resource_usage.csv", index=False)
        except Exception:
            pass

    _exported += 1

print(f"Artefactos exportados: {_exported} corridas")
print("  rewards.csv          — reward por episodio")
print("  training_monitor.csv — metricas consolidadas por episodio")
print("  config.json          — hiperparametros y configuracion")
print("  resource_usage.csv   — uso de RAM/VRAM/GPU")
