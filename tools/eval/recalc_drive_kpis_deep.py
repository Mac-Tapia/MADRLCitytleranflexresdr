"""Recalcula KPIs y metricas desde artefactos Drive (mirror G: + outputs/_drive_madrl)."""

from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean, median

REPO = Path(__file__).resolve().parents[2]
KPIS = REPO / "outputs" / "_drive_madrl" / "kpis"
G = Path(r"G:\Mi unidad\MADRLCitytleranflexresdr\outputs\madrl_v3_20260627_164047")
OUT = REPO / "outputs" / "_drive_madrl" / "kpi_recalc_20260728"
ALGOS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENS = ("E1", "E2", "E3")

OE1_KPIS = [
    "grid_import",
    "zero_net_energy",
    "peak_average",
    "ramping_average",
    "one_minus_load_factor_average",
    "flex_composite",
    "pv_self_consumption_ratio",
    "battery_throughput_total",
    "ev_departure_success_rate",
    "ev_v2g_export_total",
    "carbon_emissions",
    "electricity_cost",
]
OE2_KPIS = [
    "carbon_emissions",
    "carbon_emissions_control",
    "carbon_emissions_baseline",
    "carbon_emissions_delta",
    "carbon_emissions_daily_average_control",
    "carbon_emissions_daily_average_baseline",
    "carbon_emissions_daily_average_delta",
    "peak_average",
    "electricity_cost",
]
OE3_KPIS = [
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
    "peak_average",
    "carbon_emissions",
]

LOWER_BETTER_RATIO = {
    "grid_import",
    "zero_net_energy",
    "peak_average",
    "ramping_average",
    "one_minus_load_factor_average",
    "flex_composite",
    "carbon_emissions",
    "electricity_cost",
    "cost_peak_average",
    "cost_ramping_average",
    "cost_one_minus_load_factor_average",
    "grid_export_ratio",
}
LOWER_BETTER_DELTA = {
    "carbon_emissions_delta",
    "electricity_cost_delta",
    "grid_import_delta",
    "net_exchange_delta",
    "grid_export_delta",
}
HIGHER_BETTER = {
    "pv_self_consumption_ratio",
    "pv_generation_total",
    "battery_throughput_total",
    "ev_departure_success_rate",
    "ev_v2g_export_total",
    "community_local_traded_total",
}
HE_FLEX = [
    "peak_average",
    "ramping_average",
    "one_minus_load_factor_average",
    "grid_import",
    "zero_net_energy",
    "flex_composite",
]
HE_CO2 = ["carbon_emissions", "carbon_emissions_delta"]
HE_COST = ["electricity_cost", "electricity_cost_delta"]


def read_core(algo: str, scen: str) -> dict | None:
    path = KPIS / f"{algo.lower()}_{scen}_core_kpis.csv"
    if not path.exists():
        return None
    data: dict = {}
    with path.open(encoding="utf-8") as f:
        for row in csv.DictReader(f):
            val = (row.get("value") or "").strip()
            if not val:
                continue
            try:
                data[row["kpi"]] = float(val)
            except ValueError:
                data[row["kpi"]] = val
    return data


def read_results(algo: str, scen: str) -> dict | None:
    path = KPIS / f"{algo.lower()}_{scen}_results.json"
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def episodes_of(payload: dict | None) -> int | None:
    if not payload:
        return None
    if payload.get("episodes_recorded") is not None:
        return int(payload["episodes_recorded"])
    jr = (payload.get("hyperparameters") or {}).get("job_resume") or {}
    if jr.get("completed_episodes") is not None:
        return int(jr["completed_episodes"])
    if payload.get("episodes") is not None:
        return int(payload["episodes"])
    return None


def flex_comp(kpis: dict) -> float:
    return (
        float(kpis["peak_average"])
        + float(kpis["ramping_average"])
        + float(kpis["one_minus_load_factor_average"])
    ) / 3.0


def norm_lower_better(values: dict[str, float]) -> dict[str, float]:
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    if hi <= lo:
        return {k: 0.5 for k in values}
    return {k: 1.0 - (v - lo) / (hi - lo) for k, v in values.items()}


def write_csv(path: Path, rows: list[dict], fieldnames: list[str] | None = None) -> None:
    if not rows:
        return
    fields = fieldnames or sorted({k for row in rows for k in row})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def summarize(rows: list[dict], label: str) -> list[dict]:
    out = []
    for algo in ALGOS:
        sub = [r for r in rows if r["algorithm"] == algo]
        if not sub:
            continue
        gains = [r["gain"] for r in sub]
        improved = sum(1 for g in gains if g > 0)
        out.append(
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
    return out


def oe_table(scen: str, kpis: list[str], name: str) -> list[dict]:
    rows = []
    for algo in ALGOS:
        raw = read_core(algo, scen) or {}
        data = dict(raw)
        if scen == "E1" and all(
            x in data
            for x in ("peak_average", "ramping_average", "one_minus_load_factor_average")
        ):
            data["flex_composite"] = flex_comp(data)
        row = {"algorithm": algo, "scenario": scen}
        for kpi in kpis:
            row[kpi] = data.get(kpi)
        rows.append(row)
    write_csv(OUT / "tables" / f"{name}.csv", rows, ["algorithm", "scenario"] + kpis)
    return rows


def load_building_rows() -> list[dict]:
    rows: list[dict] = []
    for algo in ALGOS:
        for scen in SCENS:
            candidates = [
                REPO / "outputs" / "_drive_madrl" / "full_data" / algo / scen / "data" / "building_kpis.csv",
                G / algo / scen / "data" / "building_kpis.csv",
                G / algo / scen / "figures" / "tables" / "building_kpis.csv",
            ]
            for cand in candidates:
                if cand.exists() and cand.stat().st_size > 0:
                    with cand.open(encoding="utf-8") as f:
                        for row in csv.DictReader(f):
                            clean = {str(k).strip(): v for k, v in row.items() if k is not None}
                            clean["algorithm"] = algo
                            clean["scenario"] = scen
                            rows.append(clean)
                    break
    return rows


def main() -> int:
    (OUT / "tables").mkdir(parents=True, exist_ok=True)
    (OUT / "by_building").mkdir(parents=True, exist_ok=True)

    long_rows: list[dict] = []
    wide_rows: list[dict] = []
    catalog: set[str] = set()

    for algo in ALGOS:
        for scen in SCENS:
            kpis = read_core(algo, scen)
            payload = read_results(algo, scen)
            ep = episodes_of(payload)
            if not kpis:
                continue
            catalog.update(kpis)
            wide = {"algorithm": algo, "scenario": scen, "episodes": ep}
            for kpi, val in kpis.items():
                long_rows.append(
                    {
                        "algorithm": algo,
                        "scenario": scen,
                        "episodes": ep,
                        "kpi": kpi,
                        "value": val,
                    }
                )
                wide[kpi] = val
            if all(
                x in kpis
                for x in ("peak_average", "ramping_average", "one_minus_load_factor_average")
            ):
                fc = flex_comp(kpis)
                wide["flex_composite"] = fc
                long_rows.append(
                    {
                        "algorithm": algo,
                        "scenario": scen,
                        "episodes": ep,
                        "kpi": "flex_composite",
                        "value": fc,
                    }
                )
            wide_rows.append(wide)

    write_csv(
        OUT / "tables" / "all_core_kpis_long.csv",
        long_rows,
        ["algorithm", "scenario", "episodes", "kpi", "value"],
    )
    write_csv(
        OUT / "tables" / "all_core_kpis_wide.csv",
        wide_rows,
        ["algorithm", "scenario", "episodes"] + sorted(catalog) + ["flex_composite"],
    )

    flex: dict[str, float] = {}
    co2: dict[str, float] = {}
    cost: dict[str, float] = {}
    for algo in ALGOS:
        e1, e2, e3 = read_core(algo, "E1"), read_core(algo, "E2"), read_core(algo, "E3")
        if e1:
            flex[algo] = flex_comp(e1)
        if e2 and "carbon_emissions_delta" in e2:
            co2[algo] = float(e2["carbon_emissions_delta"])
        if e3 and "electricity_cost_delta" in e3:
            cost[algo] = float(e3["electricity_cost_delta"])

    nf, nc, nt = norm_lower_better(flex), norm_lower_better(co2), norm_lower_better(cost)
    ranking = []
    for algo in ALGOS:
        if algo not in nf and algo not in nc and algo not in nt:
            continue
        s1, s2, s3 = nf.get(algo, 0.0), nc.get(algo, 0.0), nt.get(algo, 0.0)
        ranking.append(
            {
                "algorithm": algo,
                "score_oe1_flex": round(s1, 4),
                "score_oe2_co2": round(s2, 4),
                "score_oe3_cost": round(s3, 4),
                "score_global": round((s1 + s2 + s3) / 3.0, 4),
                "flex_composite_e1": flex.get(algo),
                "co2_delta_kg_e2": co2.get(algo),
                "cost_delta_eur_e3": cost.get(algo),
                "episodes_e1": episodes_of(read_results(algo, "E1")),
                "episodes_e2": episodes_of(read_results(algo, "E2")),
                "episodes_e3": episodes_of(read_results(algo, "E3")),
            }
        )
    ranking.sort(key=lambda x: -x["score_global"])
    for i, item in enumerate(ranking, 1):
        item["rank"] = i
        item["selected"] = i == 1
    write_csv(OUT / "tables" / "ranking_oe_scores.csv", ranking)

    oe_table("E1", OE1_KPIS, "E1_OE1_kpis")
    oe_table("E2", OE2_KPIS, "E2_OE2_kpis")
    oe_table("E3", OE3_KPIS, "E3_OE3_kpis")

    gain_rows = []
    for row in long_rows:
        kpi, val = row["kpi"], row["value"]
        if not isinstance(val, (int, float)):
            continue
        gain = None
        kind = None
        if kpi in LOWER_BETTER_RATIO:
            gain = 1.0 - float(val)
            kind = "ratio_lower_better"
        elif kpi in LOWER_BETTER_DELTA:
            gain = -float(val)
            kind = "delta_lower_better"
        elif kpi in HIGHER_BETTER:
            kind = "higher_better"
            if 0 <= float(val) <= 2:
                gain = float(val) - 1.0
        if gain is None:
            continue
        gain_rows.append({**row, "gain": gain, "gain_kind": kind, "improved": gain > 0})

    write_csv(
        OUT / "tables" / "kpi_gains_long.csv",
        gain_rows,
        ["algorithm", "scenario", "episodes", "kpi", "value", "gain", "gain_kind", "improved"],
    )

    summ = []
    summ += summarize(
        [r for r in gain_rows if r["scenario"] == "E1" and r["kpi"] in HE_FLEX],
        "OE1_E1_flex",
    )
    summ += summarize(
        [r for r in gain_rows if r["scenario"] == "E2" and r["kpi"] in HE_CO2],
        "OE2_E2_co2",
    )
    summ += summarize(
        [r for r in gain_rows if r["scenario"] == "E3" and r["kpi"] in HE_COST],
        "OE3_E3_cost",
    )
    summ += summarize(
        [r for r in gain_rows if r["kpi"] in (HE_FLEX + HE_CO2 + HE_COST)],
        "ALL_hypothesis_kpis",
    )
    write_csv(OUT / "tables" / "kpi_gains_summary.csv", summ)

    building_rows = load_building_rows()
    if building_rows:
        write_csv(OUT / "by_building" / "building_kpis_all.csv", building_rows)

    ep_summary = []
    ep_path = (
        REPO
        / "outputs"
        / "_drive_madrl"
        / "full_data"
        / "analysis_real_drive"
        / "tables"
        / "district_episode_kpis.csv"
    )
    if ep_path.exists():
        import pandas as pd

        ep = pd.read_csv(ep_path)
        ep.to_csv(OUT / "tables" / "district_episode_kpis_source.csv", index=False)
        for (algo, scen), group in ep.groupby(["algorithm", "scenario"]):
            row = {"algorithm": algo, "scenario": scen, "n_episodes": len(group)}
            for col in [
                "reward_mean",
                "district_emission",
                "district_cost",
                "district_net_electricity_consumption",
            ]:
                if col in group.columns:
                    row[f"{col}_mean"] = float(group[col].mean())
                    row[f"{col}_std"] = float(group[col].std())
                    row[f"{col}_median"] = float(group[col].median())
                    row[f"{col}_last"] = float(group[col].iloc[-1])
            ep_summary.append(row)
        write_csv(OUT / "tables" / "episode_metrics_summary.csv", ep_summary)

    report = {
        "source_drive": "https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX",
        "source_gdrive_mount": str(G),
        "run_id": "madrl_v3_20260627_164047",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "n_treatments": len(wide_rows),
        "n_core_kpi_names": len(catalog),
        "n_core_kpi_values": len(long_rows),
        "n_gain_rows": len(gain_rows),
        "n_building_rows": len(building_rows),
        "mejor_madrl": ranking[0]["algorithm"] if ranking else None,
        "ranking": ranking,
        "kpis_primarios": {
            "flex_composite_e1": flex,
            "co2_delta_kg_e2": co2,
            "cost_delta_eur_e3": cost,
        },
        "kpi_gains_summary": summ,
        "episode_summary": ep_summary,
        "core_kpi_catalog": sorted(catalog),
    }
    (OUT / "kpi_metrics_report.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    lines = [
        "# KPIs y metricas recalculados desde Drive",
        "",
        "Fuente: [Drive folder](https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX)",
        "Run: `madrl_v3_20260627_164047`",
        f"Generado: {report['generated_at']}",
        "",
        f"- Tratamientos: **{report['n_treatments']}**/12",
        f"- Catalogo core KPI: **{report['n_core_kpi_names']}** nombres",
        f"- Valores core: **{report['n_core_kpi_values']}**",
        f"- Filas building KPI: **{report['n_building_rows']}**",
        f"- Mejor MADRL (score global normalizado): **{report['mejor_madrl']}**",
        "",
        "## Ranking OE",
        "",
        "| Rank | Algoritmo | Score global | OE1 flex | OE2 CO2 | OE3 costo | flex_composite E1 | CO2 delta E2 | Cost delta E3 |",
        "| --- | --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in ranking:
        lines.append(
            "| {rank} | {algorithm} | {score_global:.4f} | {score_oe1_flex:.4f} | "
            "{score_oe2_co2:.4f} | {score_oe3_cost:.4f} | {flex_composite_e1:.6f} | "
            "{co2_delta_kg_e2:.4f} | {cost_delta_eur_e3:.4f} |".format(**item)
        )
    lines += [
        "",
        "## Resumen KPI-gains (hipotesis)",
        "",
        "| Grupo | Algoritmo | n | Media gain | Mediana | Mejorados | No mejorados | % mejorados |",
        "| --- | --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in summ:
        lines.append(
            "| {group} | {algorithm} | {n} | {mean_gain:.4f} | {median_gain:.4f} | "
            "{improved} | {not_improved} | {pct_improved:.1f}% |".format(**item)
        )
    lines += [
        "",
        "## Metricas episodicas (district_episode_kpis)",
        "",
        "| Algo | Esc | n | reward mean | emission mean | cost mean |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for item in ep_summary:
        lines.append(
            "| {algorithm} | {scenario} | {n_episodes} | {rm:.4f} | {em:.2f} | {cm:.2f} |".format(
                algorithm=item["algorithm"],
                scenario=item["scenario"],
                n_episodes=item["n_episodes"],
                rm=item.get("reward_mean_mean", float("nan")),
                em=item.get("district_emission_mean", float("nan")),
                cm=item.get("district_cost_mean", float("nan")),
            )
        )
    (OUT / "KPIs_y_metricas.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(
        {
            "out": str(OUT),
            "n_treatments": report["n_treatments"],
            "n_core_kpi_names": report["n_core_kpi_names"],
            "n_core_kpi_values": report["n_core_kpi_values"],
            "n_building_rows": report["n_building_rows"],
            "mejor_madrl": report["mejor_madrl"],
            "ranking": ranking,
            "kpi_gains_summary": summ,
        },
        indent=2,
        ensure_ascii=False,
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
