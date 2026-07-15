"""Read-only validation of Figura 5.8e heatmap values vs trace.csv."""
from __future__ import annotations

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
BASES = [
    REPO / "outputs" / "_drive_madrl" / "full_data",
    REPO / "outputs" / "madrl_v3_20260627_164047",
]
ALGOS = ["HAPPO", "MAAC", "MASAC", "MATD3"]
SCENARIOS = ["E1", "E2", "E3"]
WANT = [
    "action_l2",
    "action_mean",
    "action_max",
    "action_min",
    "ev_charge_kwh",
    "ev_v2g_export_kwh",
    "electrical_storage_soc",
    "electrical_storage_energy_balance_kwh",
    "episode",
    "agent",
]


def summarize(base: Path) -> pd.DataFrame:
    rows = []
    for algo in ALGOS:
        for scen in SCENARIOS:
            p = base / algo / scen / "data" / "trace.csv"
            if not p.exists():
                rows.append(
                    {
                        "base": str(base),
                        "algorithm": algo,
                        "scenario": scen,
                        "path": str(p),
                        "exists": False,
                    }
                )
                continue
            header = pd.read_csv(p, nrows=0).columns.tolist()
            use = [c for c in WANT if c in header]
            df = pd.read_csv(p, usecols=use)
            row = {
                "base": str(base),
                "algorithm": algo,
                "scenario": scen,
                "path": str(p),
                "exists": True,
                "rows": len(df),
                "columns_used": "|".join(use),
                "missing_wanted": "|".join([c for c in WANT if c not in header]),
            }
            if "episode" in df.columns:
                ep = pd.to_numeric(df["episode"], errors="coerce")
                row["episode_min"] = float(ep.min())
                row["episode_max"] = float(ep.max())
                row["n_episodes"] = int(ep.nunique())
            if "agent" in df.columns:
                row["n_agents"] = int(df["agent"].nunique())
            for c in [
                "action_l2",
                "action_mean",
                "ev_charge_kwh",
                "ev_v2g_export_kwh",
                "electrical_storage_soc",
                "electrical_storage_energy_balance_kwh",
            ]:
                if c not in df.columns:
                    row[f"{c}_mean"] = float("nan")
                    row[f"{c}_nz"] = 0
                    row[f"{c}_exact0"] = 0
                    row[f"{c}_nan"] = len(df)
                    continue
                s = pd.to_numeric(df[c], errors="coerce")
                row[f"{c}_mean"] = float(s.mean())
                row[f"{c}_std"] = float(s.std())
                row[f"{c}_min"] = float(s.min())
                row[f"{c}_max"] = float(s.max())
                row[f"{c}_nz"] = int((s.abs() > 1e-12).sum())
                row[f"{c}_exact0"] = int((s == 0).sum())
                row[f"{c}_nan"] = int(s.isna().sum())
            rows.append(row)
            print(
                f"{algo}/{scen}: rows={len(df)} "
                f"action_l2={row.get('action_l2_mean'):.6g} "
                f"ev={row.get('ev_charge_kwh_mean'):.6g} "
                f"soc={row.get('electrical_storage_soc_mean'):.6g} "
                f"ev_nz={row.get('ev_charge_kwh_nz')} "
                f"soc_nz={row.get('electrical_storage_soc_nz')} "
                f"missing={row['missing_wanted'] or '-'}"
            )
    return pd.DataFrame(rows)


def reproduce_figure_agg(base: Path) -> pd.DataFrame:
    frames = []
    for algo in ALGOS:
        for scen in SCENARIOS:
            p = base / algo / scen / "data" / "trace.csv"
            if not p.exists():
                continue
            header = pd.read_csv(p, nrows=0).columns.tolist()
            use = [
                c
                for c in [
                    "action_l2",
                    "action_mean",
                    "ev_charge_kwh",
                    "ev_v2g_export_kwh",
                    "electrical_storage_soc",
                ]
                if c in header
            ]
            df = pd.read_csv(p, usecols=use)
            if df.empty:
                continue
            df["algorithm"] = algo
            df["scenario"] = scen
            frames.append(df)
    if not frames:
        return pd.DataFrame()
    traces = pd.concat(frames, ignore_index=True)
    cols = [
        c
        for c in [
            "action_l2",
            "action_mean",
            "ev_charge_kwh",
            "ev_v2g_export_kwh",
            "electrical_storage_soc",
        ]
        if c in traces.columns
    ]
    return (
        traces.groupby(["algorithm", "scenario"])[cols]
        .mean(numeric_only=True)
        .reset_index()
    )


def main() -> None:
    out_dir = REPO / "outputs"
    all_rows = []
    for base in BASES:
        print("=" * 80)
        print("BASE", base, "exists=", base.exists())
        if not base.exists():
            continue
        df = summarize(base)
        all_rows.append(df)
        agg = reproduce_figure_agg(base)
        print("\nFigure-style groupby mean:")
        print(agg.to_string(index=False))
        agg.to_csv(out_dir / f"_tmp_fig58e_agg_{base.name}.csv", index=False)

    if all_rows:
        full = pd.concat(all_rows, ignore_index=True)
        full.to_csv(out_dir / "_tmp_fig58e_trace_validation.csv", index=False)
        print("\nWrote", out_dir / "_tmp_fig58e_trace_validation.csv")

    # Compare existing consolidated sample table if present
    sample = (
        REPO
        / "outputs"
        / "_drive_madrl"
        / "gdrive_20260627_164047_objective_analysis"
        / "tables"
        / "gdrive_trace_samples_all.csv"
    )
    if sample.exists():
        tr = pd.read_csv(sample)
        print("\nConsolidated sample:", sample)
        print("rows=", len(tr), "algos=", sorted(tr["algorithm"].unique()) if "algorithm" in tr.columns else None)
        for c in ["action_l2", "ev_charge_kwh", "electrical_storage_soc", "action_mean"]:
            if c in tr.columns:
                s = pd.to_numeric(tr[c], errors="coerce")
                print(
                    f"  {c}: mean={s.mean():.6g} nz={(s.abs()>1e-12).sum()} "
                    f"exact0={(s==0).sum()} nan={s.isna().sum()} min={s.min()} max={s.max()}"
                )
        if {"algorithm", "scenario"}.issubset(tr.columns):
            cols = [c for c in ["action_l2", "action_mean", "ev_charge_kwh", "ev_v2g_export_kwh", "electrical_storage_soc"] if c in tr.columns]
            ag = tr.groupby(["algorithm", "scenario"])[cols].mean(numeric_only=True).reset_index()
            print("\nConsolidated figure-style agg:")
            print(ag.to_string(index=False))
            ag.to_csv(out_dir / "_tmp_fig58e_agg_consolidated.csv", index=False)


if __name__ == "__main__":
    main()
