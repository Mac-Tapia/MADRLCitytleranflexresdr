"""KPIs CityLearn v3 a nivel distrito y edificio (Drive 50 episodios, 4 MADRL).

Fuente unica (sin caja negra):
  - outputs/_drive_madrl/kpi_recalc_20260728/tables/all_core_kpis_wide.csv
  - outputs/_drive_madrl/kpi_recalc_20260728/by_building/building_kpis_all.csv
  - outputs/_drive_madrl/full_data/{ALGO}/{E}/data/building_behavior_summary.csv
  - building_metadata.json (nombre / tipo de uso)

Genera rankings por edificio (mejor flexibilidad, reduccion CO2, reduccion costo)
y metricas de control de recursos (BESS, EV) por edificio.
"""

from __future__ import annotations

import csv
import json
import math
from collections import defaultdict
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
RUN_ID = "madrl_v3_20260627_164047"
KPI_RECALC = REPO / "outputs" / "_drive_madrl" / "kpi_recalc_20260728"
FULL_DATA = REPO / "outputs" / "_drive_madrl" / "full_data"
METADATA = (
    REPO
    / "CityLearn"
    / "data"
    / "datasets"
    / "citylearn_iquitos_2023_2025"
    / "building_metadata.json"
)
OUT = (
    REPO
    / "outputs"
    / RUN_ID
    / "resumen_comparativo"
    / "multiobjetivo"
    / "kpi_rankings_drive50"
)

ALGOS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")
SCENARIO_OE = {
    "E1": ("OE.1", "flexibilidad"),
    "E2": ("OE.2", "co2"),
    "E3": ("OE.3", "costo"),
}

# evaluate_v2 building cost_function names
KPI_IMPORT_RATIO = "building_energy_grid_ratio_to_baseline_import_total_ratio"
KPI_CO2_DELTA = "building_emissions_total_delta_kgco2"
KPI_CO2_RATIO = "building_emissions_ratio_to_baseline_total_ratio"
KPI_COST_DELTA = "building_cost_total_delta_eur"
KPI_COST_RATIO = "building_cost_ratio_to_baseline_total_ratio"
KPI_BESS_THPUT = "building_battery_total_throughput_kwh"
KPI_EV_CHARGE = "building_ev_total_charge_kwh"
KPI_EV_V2G = "building_ev_total_v2g_export_kwh"
KPI_EV_SUCCESS = "building_ev_performance_departure_success_ratio"


def _f(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        x = float(val)
        if math.isnan(x) or math.isinf(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


def _bid(name: str) -> int:
    digits = "".join(ch for ch in str(name) if ch.isdigit())
    return int(digits) if digits else 0


def load_metadata() -> dict[int, dict[str, Any]]:
    payload = json.loads(METADATA.read_text(encoding="utf-8"))
    return {int(b["building_id"]): b for b in payload.get("buildings", [])}


def load_district_wide() -> list[dict[str, Any]]:
    path = KPI_RECALC / "tables" / "all_core_kpis_wide.csv"
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    out: list[dict[str, Any]] = []
    for r in rows:
        peak = _f(r.get("peak_average"))
        ramp = _f(r.get("ramping_average"))
        lf = _f(r.get("one_minus_load_factor_average"))
        parts = [v for v in (peak, ramp, lf) if v is not None]
        flex = sum(parts) / len(parts) if parts else None
        out.append(
            {
                "run_id": RUN_ID,
                "algorithm": r["algorithm"],
                "scenario": r["scenario"],
                "oe": SCENARIO_OE[r["scenario"]][0],
                "episodes": _f(r.get("episodes")),
                "flex_composite": flex,
                "peak_average": peak,
                "ramping_average": ramp,
                "one_minus_load_factor_average": lf,
                "carbon_emissions": _f(r.get("carbon_emissions")),
                "carbon_emissions_delta": _f(r.get("carbon_emissions_delta")),
                "electricity_cost": _f(r.get("electricity_cost")),
                "electricity_cost_delta": _f(r.get("electricity_cost_delta")),
                "grid_import_delta": _f(r.get("grid_import_delta")),
                "ev_departure_success_rate": _f(r.get("ev_departure_success_rate")),
                "battery_throughput_total": _f(r.get("battery_throughput_total")),
                "ev_charge_total": _f(r.get("ev_charge_total")),
                "ev_v2g_export_total": _f(r.get("ev_v2g_export_total")),
                "pv_self_consumption_ratio": _f(r.get("pv_self_consumption_ratio")),
            }
        )
    return out


def load_building_kpis_pivot() -> dict[tuple[str, str, str], dict[str, float | None]]:
    """(algorithm, scenario, building_name) -> cost_function -> value."""
    path = KPI_RECALC / "by_building" / "building_kpis_all.csv"
    pivot: dict[tuple[str, str, str], dict[str, float | None]] = defaultdict(dict)
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            key = (row["algorithm"], row["scenario"], row["name"])
            pivot[key][row["cost_function"]] = _f(row.get("value"))
    return pivot


def load_behavior(algo: str, scen: str) -> dict[str, dict[str, Any]]:
    path = FULL_DATA / algo / scen / "data" / "building_behavior_summary.csv"
    if not path.is_file():
        return {}
    out: dict[str, dict[str, Any]] = {}
    with path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            agent = row.get("agent") or ""
            out[agent] = row
    return out


def build_building_table(
    meta: dict[int, dict[str, Any]],
    pivot: dict[tuple[str, str, str], dict[str, float | None]],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for algo in ALGOS:
        for scen in SCENARIOS:
            behavior = load_behavior(algo, scen)
            for bid in range(1, 18):
                agent = f"Building_{bid}"
                kpis = pivot.get((algo, scen, agent), {})
                beh = behavior.get(agent, {})
                m = meta.get(bid, {})
                import_ratio = kpis.get(KPI_IMPORT_RATIO)
                co2_delta = kpis.get(KPI_CO2_DELTA)
                co2_ratio = kpis.get(KPI_CO2_RATIO)
                cost_delta = kpis.get(KPI_COST_DELTA)
                cost_ratio = kpis.get(KPI_COST_RATIO)
                # Reduccion = -delta (positivo = redujo vs baseline)
                co2_reduction = (-co2_delta) if co2_delta is not None else None
                cost_reduction = (-cost_delta) if cost_delta is not None else None
                # Flex score: menor ratio de importacion vs baseline = mejor
                # (1 - ratio) positivo si mejoro; tambien se reporta el ratio crudo.
                flex_gain = (1.0 - import_ratio) if import_ratio is not None else None
                rows.append(
                    {
                        "run_id": RUN_ID,
                        "algorithm": algo,
                        "scenario": scen,
                        "oe": SCENARIO_OE[scen][0],
                        "building_id": bid,
                        "agent": agent,
                        "nombre": m.get("name", agent),
                        "tipo_uso": m.get("tipo_uso_citylearn", ""),
                        "import_ratio_to_baseline": import_ratio,
                        "flex_gain_vs_baseline": flex_gain,
                        "carbon_emissions_delta_kgco2": co2_delta,
                        "carbon_emissions_ratio": co2_ratio,
                        "co2_reduction_kgco2": co2_reduction,
                        "electricity_cost_delta_eur": cost_delta,
                        "electricity_cost_ratio": cost_ratio,
                        "cost_reduction_eur": cost_reduction,
                        "battery_throughput_kwh": kpis.get(KPI_BESS_THPUT),
                        "ev_charge_kwh": kpis.get(KPI_EV_CHARGE),
                        "ev_v2g_export_kwh": kpis.get(KPI_EV_V2G),
                        "ev_departure_success_ratio": kpis.get(KPI_EV_SUCCESS),
                        "grid_role_control": beh.get("grid_role_control", ""),
                        "action_dim": _f(beh.get("action_dim")),
                        "action_l2_mean": _f(beh.get("action_l2_mean")),
                        "battery_charge_total_kwh": _f(beh.get("battery_charge_total_kwh")),
                        "battery_discharge_total_kwh": _f(beh.get("battery_discharge_total_kwh")),
                        "ev_charge_total_kwh_behavior": _f(beh.get("ev_charge_total_kwh")),
                        "ev_departure_success_rate_behavior": _f(
                            beh.get("ev_departure_success_rate")
                        ),
                        "pv_self_consumption_ratio": _f(beh.get("pv_self_consumption_ratio")),
                    }
                )
    return rows


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fields = list(rows[0].keys())
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)


def rank_buildings(
    building_rows: list[dict[str, Any]],
    algo: str,
    scenario: str,
    metric: str,
    higher_is_better: bool,
    top_n: int = 17,
) -> list[dict[str, Any]]:
    subset = [
        r
        for r in building_rows
        if r["algorithm"] == algo and r["scenario"] == scenario and r.get(metric) is not None
    ]
    subset.sort(key=lambda r: float(r[metric]), reverse=higher_is_better)
    ranked: list[dict[str, Any]] = []
    for i, r in enumerate(subset[:top_n], start=1):
        ranked.append(
            {
                "rank": i,
                "algorithm": algo,
                "scenario": scenario,
                "oe": SCENARIO_OE[scenario][0],
                "metric": metric,
                "higher_is_better": higher_is_better,
                "building_id": r["building_id"],
                "agent": r["agent"],
                "nombre": r["nombre"],
                "tipo_uso": r["tipo_uso"],
                "value": r[metric],
                "import_ratio_to_baseline": r["import_ratio_to_baseline"],
                "co2_reduction_kgco2": r["co2_reduction_kgco2"],
                "cost_reduction_eur": r["cost_reduction_eur"],
                "battery_throughput_kwh": r["battery_throughput_kwh"],
                "ev_charge_kwh": r["ev_charge_kwh"],
                "ev_departure_success_ratio": r["ev_departure_success_ratio"],
                "grid_role_control": r["grid_role_control"],
            }
        )
    return ranked


def best_per_treatment(building_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mejor edificio por algoritmo×escenario en el KPI primario del OE."""
    specs = {
        "E1": ("flex_gain_vs_baseline", True),
        "E2": ("co2_reduction_kgco2", True),
        "E3": ("cost_reduction_eur", True),
    }
    out: list[dict[str, Any]] = []
    for algo in ALGOS:
        for scen, (metric, hib) in specs.items():
            ranked = rank_buildings(building_rows, algo, scen, metric, hib, top_n=1)
            if ranked:
                best = ranked[0]
                out.append(
                    {
                        "algorithm": algo,
                        "scenario": scen,
                        "oe": SCENARIO_OE[scen][0],
                        "primary_metric": metric,
                        "best_building_id": best["building_id"],
                        "best_agent": best["agent"],
                        "best_nombre": best["nombre"],
                        "best_tipo_uso": best["tipo_uso"],
                        "best_value": best["value"],
                        "battery_throughput_kwh": best["battery_throughput_kwh"],
                        "ev_charge_kwh": best["ev_charge_kwh"],
                        "ev_departure_success_ratio": best["ev_departure_success_ratio"],
                        "grid_role_control": best["grid_role_control"],
                    }
                )
    return out


def full_rankings(building_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    specs = {
        "E1": ("flex_gain_vs_baseline", True),
        "E2": ("co2_reduction_kgco2", True),
        "E3": ("cost_reduction_eur", True),
    }
    out: list[dict[str, Any]] = []
    for algo in ALGOS:
        for scen, (metric, hib) in specs.items():
            out.extend(rank_buildings(building_rows, algo, scen, metric, hib))
    return out


def district_winners(district_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Mejor algoritmo a nivel distrito por escenario (KPI primario)."""
    specs = {
        "E1": ("flex_composite", False),  # closer to/below 1 better
        "E2": ("carbon_emissions_delta", False),  # lower delta better
        "E3": ("electricity_cost_delta", False),
    }
    winners: list[dict[str, Any]] = []
    for scen, (metric, hib) in specs.items():
        subset = [r for r in district_rows if r["scenario"] == scen and r.get(metric) is not None]
        subset.sort(key=lambda r: float(r[metric]), reverse=hib)
        for i, r in enumerate(subset, start=1):
            winners.append(
                {
                    "rank": i,
                    "scenario": scen,
                    "oe": SCENARIO_OE[scen][0],
                    "metric": metric,
                    "algorithm": r["algorithm"],
                    "value": r[metric],
                    "flex_composite": r["flex_composite"],
                    "carbon_emissions_delta": r["carbon_emissions_delta"],
                    "electricity_cost_delta": r["electricity_cost_delta"],
                    "ev_departure_success_rate": r["ev_departure_success_rate"],
                    "battery_throughput_total": r["battery_throughput_total"],
                }
            )
    return winners


def plot_district_bars(district_rows: list[dict[str, Any]], out: Path) -> None:
    metrics = [
        ("E1", "flex_composite", "OE.1 flex_composite (menor mejor)"),
        ("E2", "carbon_emissions_delta", "OE.2 ΔCO₂ kg (menor mejor)"),
        ("E3", "electricity_cost_delta", "OE.3 Δcosto EUR (menor mejor)"),
    ]
    colors = {"HAPPO": "#805ad5", "MASAC": "#2b6cb0", "MATD3": "#2f855a", "MAAC": "#dd6b20"}
    fig, axes = plt.subplots(1, 3, figsize=(14, 4.5))
    fig.suptitle("KPIs distrito — 4 MADRL × 50 episodios Drive")
    for ax, (scen, metric, title) in zip(axes, metrics):
        vals = []
        for algo in ALGOS:
            match = next(
                (r for r in district_rows if r["algorithm"] == algo and r["scenario"] == scen),
                None,
            )
            vals.append(match.get(metric) if match else np.nan)
        bars = ax.bar(ALGOS, vals, color=[colors[a] for a in ALGOS])
        ax.set_title(title, fontsize=9)
        ax.tick_params(axis="x", rotation=20)
        for bar, val in zip(bars, vals):
            if val is None or (isinstance(val, float) and math.isnan(val)):
                continue
            label = f"{val:,.0f}" if abs(val) >= 100 else f"{val:.4f}"
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                label,
                ha="center",
                va="bottom",
                fontsize=7,
            )
    plt.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)


def plot_building_rank_bars(
    building_rows: list[dict[str, Any]],
    algo: str,
    scenario: str,
    metric: str,
    title: str,
    out: Path,
    higher_is_better: bool = True,
) -> None:
    ranked = rank_buildings(building_rows, algo, scenario, metric, higher_is_better)
    if not ranked:
        return
    labels = [f"B{r['building_id']:02d}" for r in ranked]
    vals = [float(r["value"]) for r in ranked]
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ["#276749" if i == 0 else "#63b3ed" for i in range(len(vals))]
    ax.bar(labels, vals, color=colors)
    ax.set_title(title)
    ax.set_ylabel(metric)
    ax.tick_params(axis="x", rotation=45)
    best = ranked[0]
    ax.annotate(
        f"Mejor: B{best['building_id']:02d}\n{best['nombre'][:40]}",
        xy=(0, vals[0]),
        xytext=(1.5, vals[0] * 0.85 if vals[0] else 0.1),
        fontsize=8,
        arrowprops={"arrowstyle": "->", "color": "#276749"},
    )
    plt.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)


def plot_resource_control_heatmap(building_rows: list[dict[str, Any]], out: Path) -> None:
    """Throughput BESS + carga EV por edificio (MATD3 E1) — control de recursos visible."""
    rows = [
        r for r in building_rows if r["algorithm"] == "MATD3" and r["scenario"] == "E1"
    ]
    rows.sort(key=lambda r: r["building_id"])
    if not rows:
        return
    labels = [f"B{r['building_id']:02d}" for r in rows]
    bess = [r.get("battery_throughput_kwh") or 0.0 for r in rows]
    ev = [r.get("ev_charge_kwh") or 0.0 for r in rows]
    x = np.arange(len(labels))
    width = 0.38
    fig, ax = plt.subplots(figsize=(13, 5))
    ax.bar(x - width / 2, bess, width, label="BESS throughput (kWh)", color="#2f855a")
    ax.bar(x + width / 2, ev, width, label="EV charge (kWh)", color="#2b6cb0")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=45)
    ax.set_ylabel("kWh")
    ax.set_title("Control de recursos por edificio — MATD3 / E1 (Drive 50 ep)")
    ax.legend()
    plt.tight_layout()
    fig.savefig(out, dpi=300)
    plt.close(fig)


def write_report(
    district_rows: list[dict[str, Any]],
    district_rank: list[dict[str, Any]],
    best_buildings: list[dict[str, Any]],
    out: Path,
) -> None:
    lines = [
        "# KPIs distrito y edificio — Drive 50 episodios (4 MADRL)",
        "",
        f"Corrida canónica: `{RUN_ID}`.",
        "Fuente: `kpi_recalc_20260728` + `building_behavior_summary.csv` (no caja negra).",
        "",
        "## 1. Distrito — ranking por escenario",
        "",
    ]
    for scen in SCENARIOS:
        oe, _ = SCENARIO_OE[scen]
        lines.append(f"### {scen} ({oe})")
        lines.append("")
        lines.append("| Rank | Algoritmo | KPI primario | Valor |")
        lines.append("|------|-----------|--------------|-------|")
        for r in [x for x in district_rank if x["scenario"] == scen]:
            val = r["value"]
            vtxt = f"{val:,.4f}" if abs(float(val)) < 100 else f"{val:,.0f}"
            lines.append(
                f"| {r['rank']} | {r['algorithm']} | {r['metric']} | {vtxt} |"
            )
        lines.append("")

    lines += [
        "## 2. Mejor edificio por algoritmo × escenario",
        "",
        "| Algo | Esc. | OE | Mejor edificio | Nombre | Valor KPI | BESS thr. | EV charge | EV éxito |",
        "|------|------|----|----------------|--------|-----------|-----------|-----------|----------|",
    ]
    for r in best_buildings:
        val = r["best_value"]
        vtxt = f"{val:,.4f}" if abs(float(val)) < 100 else f"{val:,.0f}"
        bess = r.get("battery_throughput_kwh")
        evc = r.get("ev_charge_kwh")
        evs = r.get("ev_departure_success_ratio")
        lines.append(
            "| {algo} | {scen} | {oe} | B{bid:02d} | {nombre} | {val} | {bess} | {evc} | {evs} |".format(
                algo=r["algorithm"],
                scen=r["scenario"],
                oe=r["oe"],
                bid=r["best_building_id"],
                nombre=(r["best_nombre"] or "")[:32],
                val=vtxt,
                bess=f"{bess:,.0f}" if bess is not None else "—",
                evc=f"{evc:,.0f}" if evc is not None else "—",
                evs=f"{evs:.3f}" if evs is not None else "—",
            )
        )
    lines += [
        "",
        "## 3. Criterio de ranking edificio",
        "",
        "- **OE.1 / E1 flexibilidad:** `flex_gain_vs_baseline = 1 − import_ratio` (mayor = mejor).",
        "- **OE.2 / E2 CO₂:** `co2_reduction_kgco2 = −emissions_delta` (mayor = más reducción).",
        "- **OE.3 / E3 costo:** `cost_reduction_eur = −cost_delta` (mayor = más reducción).",
        "- Control de recursos reportado: throughput BESS, carga EV, éxito salida EV, rol de red.",
        "",
    ]
    out.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    meta = load_metadata()
    district_rows = load_district_wide()
    pivot = load_building_kpis_pivot()
    building_rows = build_building_table(meta, pivot)
    district_rank = district_winners(district_rows)
    best_buildings = best_per_treatment(building_rows)
    rankings = full_rankings(building_rows)

    write_csv(OUT / "district_kpis_4madrl.csv", district_rows)
    write_csv(OUT / "district_ranking_by_scenario.csv", district_rank)
    write_csv(OUT / "building_kpis_4madrl.csv", building_rows)
    write_csv(OUT / "building_best_per_algo_scenario.csv", best_buildings)
    write_csv(OUT / "building_full_rankings.csv", rankings)

    plot_district_bars(district_rows, OUT / "district_kpis_4madrl.png")
    plot_resource_control_heatmap(building_rows, OUT / "building_resource_control_matd3_e1.png")

    # Rankings visuales con el ganador distrital de cada OE (si existe)
    win_e1 = next((r for r in district_rank if r["scenario"] == "E1" and r["rank"] == 1), None)
    win_e2 = next((r for r in district_rank if r["scenario"] == "E2" and r["rank"] == 1), None)
    win_e3 = next((r for r in district_rank if r["scenario"] == "E3" and r["rank"] == 1), None)
    if win_e1:
        plot_building_rank_bars(
            building_rows,
            win_e1["algorithm"],
            "E1",
            "flex_gain_vs_baseline",
            f"Ranking edificios OE.1 flexibilidad — {win_e1['algorithm']} / E1",
            OUT / "building_rank_E1_flex.png",
            True,
        )
    if win_e2:
        plot_building_rank_bars(
            building_rows,
            win_e2["algorithm"],
            "E2",
            "co2_reduction_kgco2",
            f"Ranking edificios OE.2 reducción CO₂ — {win_e2['algorithm']} / E2",
            OUT / "building_rank_E2_co2.png",
            True,
        )
    if win_e3:
        plot_building_rank_bars(
            building_rows,
            win_e3["algorithm"],
            "E3",
            "cost_reduction_eur",
            f"Ranking edificios OE.3 reducción costo — {win_e3['algorithm']} / E3",
            OUT / "building_rank_E3_cost.png",
            True,
        )

    # Tambien rankings MATD3 (referencia tesis) por si el ganador distrital difiere
    for scen, metric, title, fname in [
        ("E1", "flex_gain_vs_baseline", "OE.1 flex — MATD3/E1", "building_rank_MATD3_E1_flex.png"),
        ("E2", "co2_reduction_kgco2", "OE.2 CO₂ — MATD3/E2", "building_rank_MATD3_E2_co2.png"),
        ("E3", "cost_reduction_eur", "OE.3 costo — MATD3/E3", "building_rank_MATD3_E3_cost.png"),
    ]:
        plot_building_rank_bars(
            building_rows, "MATD3", scen, metric, title, OUT / fname, True
        )

    write_report(district_rows, district_rank, best_buildings, OUT / "KPI_RANKINGS_REPORT.md")

    summary = {
        "run_id": RUN_ID,
        "n_district_rows": len(district_rows),
        "n_building_rows": len(building_rows),
        "algorithms": list(ALGOS),
        "district_winners": {
            r["scenario"]: r["algorithm"]
            for r in district_rank
            if r["rank"] == 1
        },
        "best_buildings_sample": best_buildings,
        "outputs_dir": str(OUT.relative_to(REPO)).replace("\\", "/"),
    }
    (OUT / "summary.json").write_text(
        json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
