# ── 8.2  Curvas de convergencia (timeseries.csv, por episodio) ───────────────
import matplotlib.pyplot as plt
import glob
import pandas as pd
from pathlib import Path

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
                if "episode" in df.columns and "reward_mean" in df.columns:
                    # Aggregate step-level timeseries to episode-level mean reward
                    ep_df = df.groupby("episode")["reward_mean"].mean().reset_index()
                    smoothed = ep_df["reward_mean"].rolling(2, min_periods=1).mean()
                    ax.plot(ep_df["episode"], smoothed,
                            label=alg, color=CLR.get(alg, "gray"), lw=2, alpha=0.85)
        ax.set_title(f"Escenario {sc}", fontweight="bold")
        ax.set_xlabel("Episodio")
        ax.set_ylabel("Reward medio por episodio (smoothed)")
        ax.legend(fontsize=9)
        ax.grid(alpha=0.3)
        ax.set_facecolor("#f8fafc")
    fig.suptitle("Convergencia — 4 Algoritmos × 3 Escenarios", fontsize=14, fontweight="bold")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_ROOT}/evaluation/convergencia.png", dpi=150, bbox_inches="tight")
    plt.show()
    print(f"✅  {OUTPUT_ROOT}/evaluation/convergencia.png")
else:
    print("Sin timeseries disponibles.")
