"""Extrae all_values evaluate_v2 + ranking canonico (con/sin HAPPO) desde results.json Drive."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

REPO = Path(__file__).resolve().parents[2]
KPIS = REPO / "outputs" / "_drive_madrl" / "kpis"
OUT = REPO / "outputs" / "_drive_madrl" / "kpi_recalc_20260728"
ALGOS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENS = ("E1", "E2", "E3")

LOWER_BETTER = {
    "grid_import",
    "zero_net_energy",
    "grid_export_ratio",
    "peak_average",
    "ramping_average",
    "one_minus_load_factor_average",
    "flex_composite",
    "carbon_emissions",
    "carbon_emissions_control",
    "carbon_emissions_delta",
    "carbon_emissions_daily_average_control",
    "carbon_emissions_daily_average_delta",
    "electricity_cost",
    "electricity_cost_control",
    "electricity_cost_delta",
    "electricity_cost_daily_average_control",
    "electricity_cost_daily_average_delta",
    "cost_peak_average",
    "cost_ramping_average",
    "cost_one_minus_load_factor_average",
    "price_signal_deviation",
    "battery_capacity_fade_ratio",
    "pv_export_total",
    "pv_export_daily_average",
    "ev_departure_soc_deficit_mean",
    "grid_import_control",
    "grid_import_delta",
    "net_exchange_control",
    "net_exchange_delta",
    "grid_export_control",
    "grid_export_delta",
}


def load_all_values(algo: str, scen: str) -> dict:
    path = KPIS / f"{algo.lower()}_{scen}_results.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    report = payload.get("citylearn_v3_report") or {}
    values = dict(report.get("all_values") or {})
    # derived flex composite when shape KPIs present
    need = ("peak_average", "ramping_average", "one_minus_load_factor_average")
    if all(k in values for k in need):
        values["flex_composite"] = (
            float(values["peak_average"])
            + float(values["ramping_average"])
            + float(values["one_minus_load_factor_average"])
        ) / 3.0
    values["_episodes"] = payload.get("episodes_recorded") or payload.get("episodes")
    return values


def write_csv(path: Path, rows: list[dict], fields: list[str] | None = None) -> None:
    if not rows:
        return
    cols = fields or sorted({k for r in rows for k in r})
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def norm_lb(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if hi <= lo:
        return {k: 0.5 for k in values}
    return {k: 1.0 - (v - lo) / (hi - lo) for k, v in values.items()}


def ranking_for(algos: tuple[str, ...], label: str) -> list[dict]:
    flex, co2, cost = {}, {}, {}
    for algo in algos:
        e1, e2, e3 = load_all_values(algo, "E1"), load_all_values(algo, "E2"), load_all_values(algo, "E3")
        if "flex_composite" in e1:
            flex[algo] = float(e1["flex_composite"])
        if "carbon_emissions_delta" in e2:
            co2[algo] = float(e2["carbon_emissions_delta"])
        if "electricity_cost_delta" in e3:
            cost[algo] = float(e3["electricity_cost_delta"])
    nf, nc, nt = norm_lb(flex), norm_lb(co2), norm_lb(cost)
    rows = []
    for algo in algos:
        s1, s2, s3 = nf.get(algo, 0.0), nc.get(algo, 0.0), nt.get(algo, 0.0)
        rows.append(
            {
                "ranking_set": label,
                "algorithm": algo,
                "score_oe1_flex": round(s1, 4),
                "score_oe2_co2": round(s2, 4),
                "score_oe3_cost": round(s3, 4),
                "score_global": round((s1 + s2 + s3) / 3.0, 4),
                "flex_composite_e1": flex.get(algo),
                "co2_delta_kg_e2": co2.get(algo),
                "cost_delta_eur_e3": cost.get(algo),
            }
        )
    rows.sort(key=lambda x: -x["score_global"])
    for i, row in enumerate(rows, 1):
        row["rank"] = i
        row["selected"] = i == 1
    return rows


def oriented_gain(kpi: str, value: float) -> float | None:
    if kpi.endswith("_baseline") or kpi in {"_episodes"}:
        return None
    if kpi in LOWER_BETTER or kpi.endswith("_delta") or "ratio" in kpi and kpi not in {
        "pv_self_consumption_ratio",
        "community_import_share",
        "ev_departure_success_rate",
        "ev_departure_within_tolerance_rate",
    }:
        # ratios vs baseline: gain = 1 - value; deltas: gain = -value
        if kpi.endswith("_delta") or kpi in {
            "carbon_emissions_delta",
            "electricity_cost_delta",
            "grid_import_delta",
            "net_exchange_delta",
            "grid_export_delta",
            "carbon_emissions_daily_average_delta",
            "electricity_cost_daily_average_delta",
        }:
            return -float(value)
        if kpi.endswith("_ratio") or kpi in LOWER_BETTER:
            # only treat near-baseline ratios as gain
            if abs(float(value)) < 50:
                return 1.0 - float(value)
    return None


def main() -> int:
    tables = OUT / "tables"
    tables.mkdir(parents=True, exist_ok=True)

    long_rows = []
    catalog: set[str] = set()
    for algo in ALGOS:
        for scen in SCENS:
            values = load_all_values(algo, scen)
            ep = values.pop("_episodes", None)
            for kpi, val in values.items():
                if not isinstance(val, (int, float)):
                    continue
                catalog.add(kpi)
                gain = oriented_gain(kpi, float(val))
                long_rows.append(
                    {
                        "algorithm": algo,
                        "scenario": scen,
                        "episodes": ep,
                        "kpi": kpi,
                        "value": float(val),
                        "gain": gain,
                        "improved": (gain > 0) if gain is not None else None,
                    }
                )

    write_csv(
        tables / "all_evaluate_v2_kpis_long.csv",
        long_rows,
        ["algorithm", "scenario", "episodes", "kpi", "value", "gain", "improved"],
    )

    # wide per treatment
    wide = []
    for algo in ALGOS:
        for scen in SCENS:
            values = load_all_values(algo, scen)
            ep = values.pop("_episodes", None)
            row = {"algorithm": algo, "scenario": scen, "episodes": ep}
            for kpi in sorted(catalog):
                if kpi in values and isinstance(values[kpi], (int, float)):
                    row[kpi] = float(values[kpi])
            wide.append(row)
    write_csv(tables / "all_evaluate_v2_kpis_wide.csv", wide)

    # per OE focused extracts using all_values
    oe_map = {
        "E1_OE1_all_values": (
            "E1",
            [
                "grid_import",
                "zero_net_energy",
                "peak_average",
                "ramping_average",
                "one_minus_load_factor_average",
                "flex_composite",
                "pv_self_consumption_ratio",
                "pv_generation_total",
                "battery_throughput_total",
                "battery_capacity_fade_ratio",
                "ev_departure_success_rate",
                "ev_v2g_export_total",
                "community_local_traded_total",
                "carbon_emissions",
                "electricity_cost",
            ],
        ),
        "E2_OE2_all_values": (
            "E2",
            [
                "carbon_emissions",
                "carbon_emissions_control",
                "carbon_emissions_baseline",
                "carbon_emissions_delta",
                "carbon_emissions_daily_average_control",
                "carbon_emissions_daily_average_baseline",
                "carbon_emissions_daily_average_delta",
                "peak_average",
                "electricity_cost",
            ],
        ),
        "E3_OE3_all_values": (
            "E3",
            [
                "electricity_cost",
                "electricity_cost_control",
                "electricity_cost_baseline",
                "electricity_cost_delta",
                "electricity_cost_daily_average_control",
                "electricity_cost_daily_average_baseline",
                "electricity_cost_daily_average_delta",
                "cost_peak_average",
                "cost_ramping_average",
                "cost_one_minus_load_factor_average",
                "price_signal_deviation",
                "peak_average",
                "carbon_emissions",
            ],
        ),
    }
    for name, (scen, cols) in oe_map.items():
        rows = []
        for algo in ALGOS:
            values = load_all_values(algo, scen)
            row = {"algorithm": algo, "scenario": scen}
            for c in cols:
                row[c] = values.get(c)
            rows.append(row)
        write_csv(tables / f"{name}.csv", rows, ["algorithm", "scenario"] + cols)

    rank_all = ranking_for(ALGOS, "all4_including_happo")
    rank_canon = ranking_for(("MASAC", "MATD3", "MAAC"), "canonical3_no_happo")
    write_csv(tables / "ranking_oe_scores_all_values.csv", rank_all + rank_canon)

    # gains summary by OE using all_values gains where available
    he = {
        "OE1_E1_flex": ("E1", {"peak_average", "ramping_average", "one_minus_load_factor_average", "grid_import", "zero_net_energy", "flex_composite"}),
        "OE2_E2_co2": ("E2", {"carbon_emissions", "carbon_emissions_delta"}),
        "OE3_E3_cost": ("E3", {"electricity_cost", "electricity_cost_delta"}),
    }
    summ = []
    for label, (scen, kpis) in he.items():
        for algo in ALGOS:
            sub = [
                r
                for r in long_rows
                if r["algorithm"] == algo
                and r["scenario"] == scen
                and r["kpi"] in kpis
                and r["gain"] is not None
            ]
            if not sub:
                continue
            gains = [r["gain"] for r in sub]
            improved = sum(1 for g in gains if g > 0)
            summ.append(
                {
                    "group": label,
                    "algorithm": algo,
                    "n": len(gains),
                    "mean_gain": mean(gains),
                    "median_gain": median(gains),
                    "improved": improved,
                    "not_improved": len(gains) - improved,
                    "pct_improved": 100.0 * improved / len(gains),
                }
            )
    write_csv(tables / "kpi_gains_summary_all_values.csv", summ)

    # episode nonparametric descriptives already exist; refresh OW stats quickly
    ep_path = (
        REPO
        / "outputs"
        / "_drive_madrl"
        / "full_data"
        / "analysis_real_drive"
        / "tables"
        / "district_episode_kpis.csv"
    )
    infer = []
    if ep_path.exists():
        import numpy as np
        import pandas as pd
        from scipy import stats

        ep = pd.read_csv(ep_path)
        metric_map = {
            "OE1": ("E1", "reward_mean", True),
            "OE2": ("E2", "district_emission", False),
            "OE3": ("E3", "district_cost", False),
        }
        for oe, (scen, metric, higher_better) in metric_map.items():
            sub = ep[(ep["scenario"] == scen) & ep[metric].notna()].copy()
            groups = []
            for algo in ("HAPPO", "MASAC", "MATD3", "MAAC"):
                vals = sub.loc[sub["algorithm"] == algo, metric].astype(float).to_numpy()
                if len(vals) == 0:
                    continue
                sw = stats.shapiro(vals) if 3 <= len(vals) <= 5000 else (float("nan"), float("nan"))
                groups.append(vals)
                infer.append(
                    {
                        "objective": oe,
                        "scenario": scen,
                        "metric": metric,
                        "algorithm": algo,
                        "n": int(len(vals)),
                        "mean": float(np.mean(vals)),
                        "median": float(np.median(vals)),
                        "std": float(np.std(vals, ddof=1)),
                        "shapiro_W": float(sw[0]),
                        "shapiro_p": float(sw[1]),
                        "normality_rejected_alpha05": bool(sw[1] < 0.05) if sw[1] == sw[1] else None,
                    }
                )
            if len(groups) >= 2:
                h, p = stats.kruskal(*groups)
                infer.append(
                    {
                        "objective": oe,
                        "scenario": scen,
                        "metric": metric,
                        "algorithm": "ALL_KRUSKAL",
                        "n": int(sum(len(g) for g in groups)),
                        "mean": float("nan"),
                        "median": float("nan"),
                        "std": float("nan"),
                        "shapiro_W": float("nan"),
                        "shapiro_p": float(p),
                        "normality_rejected_alpha05": None,
                        "kruskal_H": float(h),
                        "kruskal_p": float(p),
                    }
                )
        write_csv(tables / "episode_inferential_by_oe.csv", infer)

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source_drive": "https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX",
        "n_evaluate_v2_kpi_names": len(catalog),
        "n_evaluate_v2_values": len(long_rows),
        "catalog": sorted(catalog),
        "ranking_all4": rank_all,
        "ranking_canonical3": rank_canon,
        "kpi_gains_summary": summ,
        "mejor_madrl_all4": rank_all[0]["algorithm"] if rank_all else None,
        "mejor_madrl_canonical3": rank_canon[0]["algorithm"] if rank_canon else None,
    }
    (OUT / "kpi_metrics_report_full.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # update markdown
    lines = [
        "# KPIs y metricas recalculados desde Drive (evaluate_v2 completo)",
        "",
        "Fuente: [Drive folder](https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX)",
        "Run: `madrl_v3_20260627_164047`",
        f"Generado: {report['generated_at']}",
        "",
        f"- Catalogo `citylearn_v3_report.all_values`: **{len(catalog)}** KPIs",
        f"- Valores totales (4 algos x 3 escenarios): **{len(long_rows)}**",
        f"- Mejor MADRL (4/4, incluye HAPPO): **{report['mejor_madrl_all4']}**",
        f"- Mejor MADRL (canonico 3/3, sin HAPPO): **{report['mejor_madrl_canonical3']}**",
        "",
        "## Ranking OE — 4 algoritmos",
        "",
        "| Rank | Algoritmo | Score | OE1 | OE2 | OE3 | flex_E1 | CO2d_E2 | Costd_E3 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rank_all:
        lines.append(
            f"| {r['rank']} | {r['algorithm']} | {r['score_global']:.4f} | {r['score_oe1_flex']:.4f} | "
            f"{r['score_oe2_co2']:.4f} | {r['score_oe3_cost']:.4f} | {r['flex_composite_e1']:.6f} | "
            f"{r['co2_delta_kg_e2']:.2f} | {r['cost_delta_eur_e3']:.2f} |"
        )
    lines += [
        "",
        "## Ranking OE — canonico (MASAC/MATD3/MAAC)",
        "",
        "| Rank | Algoritmo | Score | OE1 | OE2 | OE3 | flex_E1 | CO2d_E2 | Costd_E3 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for r in rank_canon:
        lines.append(
            f"| {r['rank']} | {r['algorithm']} | {r['score_global']:.4f} | {r['score_oe1_flex']:.4f} | "
            f"{r['score_oe2_co2']:.4f} | {r['score_oe3_cost']:.4f} | {r['flex_composite_e1']:.6f} | "
            f"{r['co2_delta_kg_e2']:.2f} | {r['cost_delta_eur_e3']:.2f} |"
        )
    lines += [
        "",
        "## KPI-gains por OE (all_values)",
        "",
        "| Grupo | Algoritmo | n | Media | Mediana | Mejorados | % |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for s in summ:
        lines.append(
            f"| {s['group']} | {s['algorithm']} | {s['n']} | {s['mean_gain']:.4f} | "
            f"{s['median_gain']:.4f} | {s['improved']} | {s['pct_improved']:.1f}% |"
        )
    if infer:
        lines += [
            "",
            "## Inferencia episodica (Shapiro + Kruskal)",
            "",
            "| OE | Algo | n | mean | median | Shapiro p | KW p |",
            "| --- | --- | --- | --- | --- | --- | --- |",
        ]
        for row in infer:
            lines.append(
                f"| {row.get('objective')} | {row.get('algorithm')} | {row.get('n')} | "
                f"{row.get('mean')} | {row.get('median')} | {row.get('shapiro_p')} | "
                f"{row.get('kruskal_p', '')} |"
            )
    lines += [
        "",
        "## Archivos generados",
        "",
        "- `tables/all_evaluate_v2_kpis_long.csv`",
        "- `tables/all_evaluate_v2_kpis_wide.csv`",
        "- `tables/E1_OE1_all_values.csv`",
        "- `tables/E2_OE2_all_values.csv`",
        "- `tables/E3_OE3_all_values.csv`",
        "- `tables/ranking_oe_scores_all_values.csv`",
        "- `tables/kpi_gains_summary_all_values.csv`",
        "- `tables/episode_inferential_by_oe.csv`",
        "- `kpi_metrics_report_full.json`",
    ]
    (OUT / "KPIs_y_metricas_FULL.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(
        {
            "n_kpi_names": len(catalog),
            "n_values": len(long_rows),
            "mejor_all4": report["mejor_madrl_all4"],
            "mejor_canonical3": report["mejor_madrl_canonical3"],
            "rank_canon": rank_canon,
            "rank_all": rank_all,
        },
        indent=2,
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
