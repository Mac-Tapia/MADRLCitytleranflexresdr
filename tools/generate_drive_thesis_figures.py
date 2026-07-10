"""Figuras de tesis desde artefactos REALES de Drive (sin sintesis).

Fuente unica: outputs/_drive_madrl/full_data/ (espejo de
https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX)

Salida:
  outputs/madrl_v3_20260627_164047/{ALGO}/{SCEN}/figures/  (por job)
  outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CITYLEARN_SCRIPTS = REPO / "CityLearn" / "scripts"
if str(CITYLEARN_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(CITYLEARN_SCRIPTS))

from citylearn_v3_training_common import (  # noqa: E402
    _episode_summaries,
    _write_training_figures_and_tables,
    ensure_artifact_layout,
)

RUN_ID = "madrl_v3_20260627_164047"
DRIVE_FOLDER = "1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX"
FULL_DATA = REPO / "outputs" / "_drive_madrl" / "full_data"
KPIS_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
OUT_RUN = REPO / "outputs" / RUN_ID
OUT_COMP = OUT_RUN / "resumen_comparativo" / "figuras_drive_reales"

ALGOS_KPI = ("MASAC", "MATD3", "MAAC")
ALGOS_TS = ("MASAC", "MATD3", "MAAC", "HAPPO")
SCENARIOS = ("E1", "E2", "E3")

SCENARIO_OBJECTIVE = {
    "E1": ("OE1", "flexibilidad", ["peak_average", "ramping_average", "one_minus_load_factor_average"]),
    "E2": ("OE2", "co2", ["carbon_emissions_delta", "carbon_emissions"]),
    "E3": ("OE3", "costo", ["electricity_cost_delta", "electricity_cost"]),
}

TS_USECOLS = [
    "episode",
    "episode_step",
    "global_step",
    "time_step",
    "all_done",
    "reward_mean",
    "reward_sum",
    "district_net_electricity_consumption",
    "district_net_electricity_consumption_cost",
    "district_net_electricity_consumption_emission",
    "district_net_electricity_consumption_without_storage",
    "carbon_intensity_mean",
    "electricity_price_mean",
]

COLORS = {"MASAC": "#2b6cb0", "MATD3": "#2f855a", "MAAC": "#dd6b20", "HAPPO": "#805ad5"}


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def data_dir(algo: str, scen: str) -> Path:
    return FULL_DATA / algo / scen / "data"


def has_file(algo: str, scen: str, name: str, min_bytes: int = 1000) -> bool:
    p = data_dir(algo, scen) / name
    return p.is_file() and p.stat().st_size >= min_bytes


def load_timeseries_rows(algo: str, scen: str) -> list[dict[str, Any]]:
    path = data_dir(algo, scen) / "timeseries.csv"
    df = pd.read_csv(path, usecols=lambda c: c in TS_USECOLS)
    return df.to_dict(orient="records")


def load_trace_rows(algo: str, scen: str) -> list[dict[str, Any]]:
    path = data_dir(algo, scen) / "trace.csv"
    return pd.read_csv(path).to_dict(orient="records")


def load_checkpoints(algo: str, scen: str) -> list[dict[str, Any]]:
    path = data_dir(algo, scen) / "checkpoint_manifest.json"
    if not path.is_file():
        return []
    obj = read_json(path)
    rows = []
    for item in obj.get("checkpoints", []):
        rows.append(
            {
                "relative_path": item.get("relative_path"),
                "bytes": item.get("bytes"),
                "backend": obj.get("backend"),
            }
        )
    return rows


def read_core_kpis(algo: str, scen: str) -> dict[str, float]:
    path = KPIS_DIR / f"{algo.lower()}_{scen.lower()}_core_kpis.csv"
    if not path.is_file():
        path = data_dir(algo, scen) / "results.json"
        if path.is_file():
            av = (read_json(path).get("citylearn_v3_report") or {}).get("all_values") or {}
            return {k: float(v) for k, v in av.items() if isinstance(v, (int, float))}
        return {}
    out: dict[str, float] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            val = (row.get("value") or "").strip()
            if val:
                out[row["kpi"]] = float(val)
    return out


def flex_composite(kpis: dict[str, float]) -> float | None:
    parts = [kpis.get(k) for k in ("peak_average", "ramping_average", "one_minus_load_factor_average")]
    vals = [v for v in parts if v is not None]
    return sum(vals) / len(vals) if vals else None


def generate_per_job_figures() -> list[dict[str, Any]]:
    manifest: list[dict[str, Any]] = []
    for algo in ALGOS_TS:
        for scen in SCENARIOS:
            if not has_file(algo, scen, "timeseries.csv") or not has_file(algo, scen, "trace.csv"):
                manifest.append({"algo": algo, "scen": scen, "status": "skip_missing_ts_trace"})
                continue
            results_path = data_dir(algo, scen) / "results.json"
            results = read_json(results_path) if results_path.is_file() else {}
            report = results.get("citylearn_v3_report") or {}
            ts_rows = load_timeseries_rows(algo, scen)
            tr_rows = load_trace_rows(algo, scen)
            ep_summaries = _episode_summaries(ts_rows)

            out_dir = OUT_RUN / algo / scen
            dirs = ensure_artifact_layout(out_dir)
            fig_manifest = _write_training_figures_and_tables(
                dirs=dirs,
                report=report,
                timeseries_rows=ts_rows,
                trace_rows=tr_rows,
                episode_summaries=ep_summaries,
                checkpoints=load_checkpoints(algo, scen),
                extra_tables={
                    "drive_data_provenance": [
                        {
                            "source": "google_drive",
                            "folder_id": DRIVE_FOLDER,
                            "timeseries": str(data_dir(algo, scen) / "timeseries.csv"),
                            "trace": str(data_dir(algo, scen) / "trace.csv"),
                            "trace_rows": len(tr_rows),
                            "timeseries_rows": len(ts_rows),
                            "note": "Figuras desde CSV reales; trace parcial si < pasos totales.",
                        }
                    ]
                },
            )
            manifest.append(
                {
                    "algo": algo,
                    "scen": scen,
                    "status": "ok",
                    "figure_count": fig_manifest.get("figure_count"),
                    "figures_dir": str(dirs["figures"]),
                }
            )
            print(f"OK per-job {algo}/{scen}: {fig_manifest.get('figure_count')} figuras")
    return manifest


def episode_reward_series(algo: str, scen: str) -> pd.DataFrame | None:
    if not has_file(algo, scen, "timeseries.csv"):
        return None
    df = pd.read_csv(data_dir(algo, scen) / "timeseries.csv", usecols=["episode", "reward_mean", "reward_sum"])
    return (
        df.groupby("episode", as_index=False)
        .agg(reward_mean=("reward_mean", "mean"), reward_sum=("reward_sum", "sum"))
        .assign(algorithm=algo, scenario=scen)
    )


def plot_convergence_by_scenario(out_dir: Path) -> list[str]:
    paths: list[str] = []
    for scen in SCENARIOS:
        fig, ax = plt.subplots(figsize=(11, 5))
        for algo in ALGOS_TS:
            ep = episode_reward_series(algo, scen)
            if ep is None:
                continue
            ax.plot(
                ep["episode"],
                ep["reward_mean"],
                label=f"{algo} (n={len(ep)})",
                color=COLORS.get(algo, None),
                linewidth=1.6,
            )
        oe, name, _ = SCENARIO_OBJECTIVE[scen]
        ax.set_title(f"Convergencia real — {scen} ({oe} {name}) [timeseries.csv Drive]")
        ax.set_xlabel("Episodio")
        ax.set_ylabel("reward_mean (distrito)")
        ax.grid(True, alpha=0.25)
        ax.legend()
        fig.tight_layout()
        path = out_dir / f"comparativo_{scen}_convergence_reward_mean.png"
        fig.savefig(path, dpi=300)
        plt.close(fig)
        paths.append(str(path))
    return paths


def plot_objective_kpis_by_scenario(out_dir: Path) -> list[str]:
    paths: list[str] = []
    for scen in SCENARIOS:
        oe, name, metrics = SCENARIO_OBJECTIVE[scen]
        metric = metrics[0]
        fig, ax = plt.subplots(figsize=(8, 5))
        labels, vals = [], []
        for algo in ALGOS_KPI:
            kpis = read_core_kpis(algo, scen)
            if metric not in kpis:
                if scen == "E1" and metric.startswith("peak"):
                    v = flex_composite(kpis)
                else:
                    v = None
            else:
                v = kpis.get(metric)
            if scen == "E1" and metric == "peak_average":
                v = flex_composite(kpis)
                metric_label = "flex_composite"
            else:
                metric_label = metric
            if v is None:
                continue
            labels.append(algo)
            vals.append(v)
        if not labels:
            plt.close(fig)
            continue
        bars = ax.bar(labels, vals, color=[COLORS[a] for a in labels])
        ax.set_title(f"{oe} {name} — {metric_label} ({scen}) [core_kpis Drive]")
        ax.set_ylabel(metric_label)
        for bar, val in zip(bars, vals):
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:,.3f}" if abs(val) < 1000 else f"{val:,.0f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )
        fig.tight_layout()
        path = out_dir / f"comparativo_{scen}_{oe}_kpi.png"
        fig.savefig(path, dpi=300)
        plt.close(fig)
        paths.append(str(path))
    return paths


def build_ranking_table() -> pd.DataFrame:
    rows: list[dict[str, Any]] = []
    for algo in ALGOS_KPI:
        e1, e2, e3 = (read_core_kpis(algo, s) for s in SCENARIOS)
        rows.append(
            {
                "algorithm": algo,
                "E1_flex_composite": flex_composite(e1),
                "E2_carbon_delta_kg": e2.get("carbon_emissions_delta"),
                "E3_cost_delta_eur": e3.get("electricity_cost_delta"),
            }
        )
    df = pd.DataFrame(rows)

    def rank_col(col: str, ascending: bool = True) -> pd.Series:
        return df[col].rank(ascending=ascending, method="min")

    df["rank_E1"] = rank_col("E1_flex_composite", True)
    df["rank_E2"] = rank_col("E2_carbon_delta_kg", True)
    df["rank_E3"] = rank_col("E3_cost_delta_eur", True)
    for c in ("E1_flex_composite", "E2_carbon_delta_kg", "E3_cost_delta_eur"):
        lo, hi = df[c].min(), df[c].max()
        norm = 1.0 - (df[c] - lo) / (hi - lo) if hi > lo else 0.5
        df[f"score_{c}"] = norm
    df["score_global"] = df[[f"score_{c}" for c in ("E1_flex_composite", "E2_carbon_delta_kg", "E3_cost_delta_eur")]].mean(axis=1)
    df["rank_global"] = df["score_global"].rank(ascending=False, method="min")
    df["best_global"] = df["rank_global"] == 1
    return df.sort_values("rank_global")


def plot_global_ranking(df: pd.DataFrame, out_dir: Path) -> str:
    fig, axes = plt.subplots(1, 2, figsize=(13, 5))
    x = np.arange(len(df))
    axes[0].bar(x, df["score_global"], color=[COLORS.get(a, "#666") for a in df["algorithm"]])
    axes[0].set_xticks(x)
    axes[0].set_xticklabels(df["algorithm"])
    axes[0].set_title("Score global normalizado (OE1+OE2+OE3)")
    axes[0].set_ylabel("score (mayor = mejor)")

    metrics = ["E1_flex_composite", "E2_carbon_delta_kg", "E3_cost_delta_eur"]
    width = 0.25
    for i, algo in enumerate(df["algorithm"]):
        row = df[df["algorithm"] == algo].iloc[0]
        for j, m in enumerate(metrics):
            axes[1].bar(i + (j - 1) * width, row[m], width=width, label=m if i == 0 else "", color=list(COLORS.values())[j])
    axes[1].set_xticks(range(len(df)))
    axes[1].set_xticklabels(df["algorithm"])
    axes[1].set_title("KPI fisicos por objetivo (valores Drive)")
    axes[1].legend(fontsize=7)
    fig.suptitle("Ranking MADRL — datos reales Drive (sin HAPPO: sin KPIs finales)")
    fig.tight_layout()
    path = out_dir / "comparativo_global_ranking_oe.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return str(path)


def plot_best_worst(df: pd.DataFrame, out_dir: Path) -> str:
    fig, ax = plt.subplots(figsize=(10, 4))
    scenarios = [
        ("E1", "E1_flex_composite", "rank_E1", "OE1 flex"),
        ("E2", "E2_carbon_delta_kg", "rank_E2", "OE2 CO2"),
        ("E3", "E3_cost_delta_eur", "rank_E3", "OE3 costo"),
    ]
    y = np.arange(len(scenarios))
    height = 0.35
    best_algos, worst_algos = [], []
    for scen, col, rank_col, _ in scenarios:
        best = df.loc[df[rank_col] == 1, "algorithm"].iloc[0]
        worst = df.loc[df[rank_col] == df[rank_col].max(), "algorithm"].iloc[0]
        best_algos.append(best)
        worst_algos.append(worst)
    ax.barh(y - height / 2, [1] * 3, height=height, color="#2f855a", label="Mejor")
    ax.barh(y + height / 2, [1] * 3, height=height, color="#c53030", label="Peor")
    for i, (b, w) in enumerate(zip(best_algos, worst_algos)):
        ax.text(0.5, i - height / 2, f"  {b}", va="center", fontsize=10, color="white", fontweight="bold")
        ax.text(0.5, i + height / 2, f"  {w}", va="center", fontsize=10, color="white", fontweight="bold")
    ax.set_yticks(y)
    ax.set_yticklabels([s[3] for s in scenarios])
    ax.set_xlim(0, 1)
    ax.set_xticks([])
    ax.set_title("Mejor / peor algoritmo por escenario (KPIs Drive)")
    ax.legend(loc="lower right")
    fig.tight_layout()
    path = out_dir / "comparativo_best_worst_por_escenario.png"
    fig.savefig(path, dpi=300)
    plt.close(fig)
    return str(path)


def plot_district_metrics_compare(out_dir: Path) -> list[str]:
    paths = []
    metrics = [
        ("district_net_electricity_consumption_cost", "Costo distrito (sum/episodio)"),
        ("district_net_electricity_consumption_emission", "Emision distrito (sum/episodio)"),
    ]
    for scen in SCENARIOS:
        for col, title in metrics:
            if col not in TS_USECOLS:
                continue
            fig, ax = plt.subplots(figsize=(10, 5))
            for algo in ALGOS_TS:
                if not has_file(algo, scen, "timeseries.csv"):
                    continue
                df = pd.read_csv(data_dir(algo, scen) / "timeseries.csv", usecols=["episode", col])
                ep = df.groupby("episode", as_index=False)[col].sum()
                ax.plot(ep["episode"], ep[col], label=algo, color=COLORS.get(algo), linewidth=1.4)
            ax.set_title(f"{title} — {scen} [timeseries.csv]")
            ax.set_xlabel("Episodio")
            ax.legend()
            ax.grid(True, alpha=0.25)
            fig.tight_layout()
            fname = f"comparativo_{scen}_{col}.png"
            fig.savefig(out_dir / fname, dpi=300)
            plt.close(fig)
            paths.append(str(out_dir / fname))
    return paths


def plot_control_trace_compare(out_dir: Path) -> list[str]:
    """Control/exploracion desde trace.csv real (submuestra Drive)."""
    paths = []
    for scen in SCENARIOS:
        fig, axes = plt.subplots(1, 2, figsize=(12, 5))
        for algo in ALGOS_TS:
            if not has_file(algo, scen, "trace.csv"):
                continue
            tr = pd.read_csv(data_dir(algo, scen) / "trace.csv")
            if "action_l2" in tr.columns:
                by_ep = tr.groupby("episode", as_index=False)["action_l2"].mean()
                axes[0].plot(by_ep["episode"], by_ep["action_l2"], label=algo, color=COLORS.get(algo))
            if "ev_charge_kwh" in tr.columns:
                by_ep2 = tr.groupby("episode", as_index=False)["ev_charge_kwh"].sum()
                axes[1].plot(by_ep2["episode"], by_ep2["ev_charge_kwh"], label=algo, color=COLORS.get(algo))
        axes[0].set_title(f"action_l2 medio — {scen}")
        axes[1].set_title(f"EV charge kWh — {scen}")
        axes[0].set_xlabel("Episodio")
        axes[1].set_xlabel("Episodio")
        axes[0].legend(fontsize=8)
        axes[1].legend(fontsize=8)
        axes[0].grid(True, alpha=0.25)
        axes[1].grid(True, alpha=0.25)
        fig.suptitle(f"Control MADRL — trace.csv Drive ({scen})")
        fig.tight_layout()
        path = out_dir / f"comparativo_{scen}_control_trace.png"
        fig.savefig(path, dpi=300)
        plt.close(fig)
        paths.append(str(path))
    return paths


def write_thesis_mapping(per_job: list[dict], comp_paths: list[str], ranking: pd.DataFrame) -> Path:
    best = ranking.loc[ranking["best_global"]].iloc[0]["algorithm"]
    md = OUT_COMP / "drive_figures_thesis_mapping.md"
    lines = [
        f"# Figuras desde Drive real — {RUN_ID}",
        "",
        f"Carpeta Drive: https://drive.google.com/drive/folders/{DRIVE_FOLDER}",
        "",
        "**Regla:** solo `timeseries.csv`, `trace.csv`, `results.json`, `core_kpis.csv` "
        "y `checkpoint_manifest.json` descargados. Sin datos sinteticos.",
        "",
        f"**Mejor MADRL global (KPIs Drive):** {best}",
        "",
        "## Objetivos de tesis",
        "",
        "| OE | Escenario | KPI figura comparativa | Mejor (Drive) |",
        "|----|-----------|------------------------|---------------|",
    ]
    for scen in SCENARIOS:
        oe, name, _ = SCENARIO_OBJECTIVE[scen]
        col = {"E1": "rank_E1", "E2": "rank_E2", "E3": "rank_E3"}[scen]
        best_a = ranking.loc[ranking[col] == 1, "algorithm"].iloc[0]
        lines.append(f"| {oe} | {scen} | comparativo_{scen}_*.png | **{best_a}** |")
    lines.extend(["", "## Figuras comparativas", ""])
    for p in comp_paths:
        lines.append(f"- `{Path(p).name}`")
    lines.extend(["", "## Figuras por job (pipeline training_common)", ""])
    for item in per_job:
        if item.get("status") == "ok":
            lines.append(f"- {item['algo']}/{item['scen']}: {item['figure_count']} figuras en `{item['figures_dir']}`")
    md.write_text("\n".join(lines), encoding="utf-8")
    return md


def main() -> int:
    OUT_COMP.mkdir(parents=True, exist_ok=True)
    (OUT_COMP / "comparativo").mkdir(exist_ok=True)

    print("=== Figuras por job (timeseries + trace reales) ===")
    per_job = generate_per_job_figures()

    print("=== Figuras comparativas tesis ===")
    comp_dir = OUT_COMP / "comparativo"
    comp_paths: list[str] = []
    comp_paths.extend(plot_convergence_by_scenario(comp_dir))
    comp_paths.extend(plot_objective_kpis_by_scenario(comp_dir))
    comp_paths.extend(plot_district_metrics_compare(comp_dir))
    comp_paths.extend(plot_control_trace_compare(comp_dir))

    ranking = build_ranking_table()
    ranking.to_csv(OUT_COMP / "ranking_global_oe_drive.csv", index=False)
    comp_paths.append(plot_global_ranking(ranking, comp_dir))
    comp_paths.append(plot_best_worst(ranking, comp_dir))

    mapping = write_thesis_mapping(per_job, comp_paths, ranking)
    summary = {
        "run_id": RUN_ID,
        "drive_folder": DRIVE_FOLDER,
        "per_job": per_job,
        "comparative_figures": comp_paths,
        "ranking_csv": str(OUT_COMP / "ranking_global_oe_drive.csv"),
        "mapping_md": str(mapping),
    }
    (OUT_COMP / "generation_manifest.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print(f"\nListo: {OUT_COMP}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
