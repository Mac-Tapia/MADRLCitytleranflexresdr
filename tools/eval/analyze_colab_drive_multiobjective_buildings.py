"""Análisis multiobjetivo Colab/Drive: KPIs por distrito y por edificio (17 edificios Iquitos).

Genera inventario con elementos controlados/no controlados, cantidad de EVs,
tablas CSV y figuras en outputs/<run_id>/resumen_comparativo/multiobjetivo/.
"""

from __future__ import annotations

import csv
import json
import math
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np

REPO = Path(__file__).resolve().parents[2]
if str(REPO / "tools") not in sys.path:
    sys.path.insert(0, str(REPO / "tools" / "dataset"))

from dimension_ev_chargers import build_charger_config  # noqa: E402

RUN_ID = "madrl_v3_20260627_164047"
KPIS_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
FULL_DATA = REPO / "outputs" / "_drive_madrl" / "full_data"
METADATA = REPO / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025" / "building_metadata.json"
MACHINES = REPO / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025" / "controlled_machines_log.json"
OUT = REPO / "outputs" / RUN_ID / "resumen_comparativo" / "multiobjetivo"

ALGOS = ("MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")
SCENARIO_OBJECTIVE = {"E1": "OE1_flexibilidad", "E2": "OE2_co2", "E3": "OE3_costo"}


@dataclass
class BuildingInventoryRow:
    building_id: int
    agent: str
    nombre: str
    tipo_uso: str
    area_techada_m2: float
    ev_total: int
    ev_moto_lineal: int
    ev_mototaxi: int
    ev_camioneta: int
    ev_pool_size: int
    elementos_controlados: str
    elementos_no_controlados: str
    acciones_dim: int
    observaciones_dim: int


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def parse_building_id(agent: str) -> int:
    m = re.search(r"(\d+)", agent)
    return int(m.group(1)) if m else 0


def load_building_metadata() -> dict[int, dict]:
    payload = read_json(METADATA)
    return {int(b["building_id"]): b for b in payload.get("buildings", [])}


def load_controlled_machines() -> dict[int, dict]:
    payload = read_json(MACHINES)
    return {int(r["building_id"]): r for r in payload.get("rows", [])}


def classify_action(name: str) -> str:
    if name.startswith("electrical_storage"):
        return "BESS (electrical_storage)"
    if name.startswith("electric_vehicle_storage"):
        return "EV charger"
    if name.startswith("washing_machine"):
        return "Carga desplazable (washing_machine)"
    return name


def uncontrolled_elements(meta: dict, machine: dict | None) -> str:
    parts = [
        "non_shiftable_load (carga base medida)",
        "cooling_demand / refrigeración (modelada, no accionada directamente)",
        "dhw_demand (ACS modelada)",
        "solar_generation (FV fija por edificio)",
    ]
    if meta.get("sistemas_refrigeracion_grandes") and meta["sistemas_refrigeracion_grandes"] != "None":
        parts.append(f"sistema grande: {meta['sistemas_refrigeracion_grandes']}")
    if machine:
        parts.append(f"ciclo desplazable potencial: {machine.get('shiftable_cycle_kwh')} kWh/ciclo")
    return "; ".join(parts)


def parse_schema(schema_path: Path) -> dict[str, dict[str, Any]]:
    by_agent: dict[str, dict[str, Any]] = {}
    with schema_path.open(encoding="utf-8", newline="") as f:
        for row in csv.DictReader(f):
            agent = row["agent"]
            slot = by_agent.setdefault(
                agent,
                {"actions": [], "observations": [], "action_dim": 0, "observation_dim": 0},
            )
            vtype = row["variable_type"]
            name = row["variable_name"]
            if vtype == "action":
                slot["actions"].append(name)
            elif vtype == "observation":
                slot["observations"].append(name)
    for slot in by_agent.values():
        slot["action_dim"] = len(slot["actions"])
        slot["observation_dim"] = len(slot["observations"])
    return by_agent


def build_inventory() -> list[BuildingInventoryRow]:
    meta_by_id = load_building_metadata()
    machines = load_controlled_machines()
    _, ev_rows = build_charger_config(return_summary=True)
    ev_by_id = {int(r["B"]): r for r in ev_rows}

    schema_path = FULL_DATA / "MATD3" / "E1" / "data" / "building_observation_action_schema.csv"
    if not schema_path.exists():
        raise FileNotFoundError(f"Falta schema local: {schema_path}")
    schema = parse_schema(schema_path)

    rows: list[BuildingInventoryRow] = []
    for bid in sorted(meta_by_id):
        agent = f"Building_{bid}"
        meta = meta_by_id[bid]
        ev = ev_by_id[bid]
        sch = schema.get(agent, {"actions": [], "observations": [], "action_dim": 0, "observation_dim": 0})

        controlled_counts: dict[str, int] = {}
        for act in sch["actions"]:
            label = classify_action(act)
            controlled_counts[label] = controlled_counts.get(label, 0) + 1
        controlled_str = ", ".join(f"{k} x{v}" for k, v in sorted(controlled_counts.items()))

        rows.append(
            BuildingInventoryRow(
                building_id=bid,
                agent=agent,
                nombre=meta.get("name", agent),
                tipo_uso=meta.get("tipo_uso_citylearn", ""),
                area_techada_m2=float(meta.get("area_techada_m2") or 0),
                ev_total=int(ev["total_chargers"]),
                ev_moto_lineal=int(ev["n_moto_stalls"]),
                ev_mototaxi=int(ev["n_mototaxi_stalls"]),
                ev_camioneta=int(ev["n_cam_stalls"]),
                ev_pool_size=int(ev["electric_vehicle_pool_count"]),
                elementos_controlados=controlled_str,
                elementos_no_controlados=uncontrolled_elements(meta, machines.get(bid)),
                acciones_dim=int(sch["action_dim"]),
                observaciones_dim=int(sch["observation_dim"]),
            )
        )
    return rows


def write_inventory_csv(rows: list[BuildingInventoryRow]) -> Path:
    out = OUT / "building_inventory_multiobjective.csv"
    fields = [
        "building_id",
        "agent",
        "nombre",
        "tipo_uso",
        "area_techada_m2",
        "ev_total",
        "ev_moto_lineal",
        "ev_mototaxi",
        "ev_camioneta",
        "ev_pool_size",
        "elementos_controlados",
        "elementos_no_controlados",
        "acciones_dim",
        "observaciones_dim",
    ]
    with out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow({k: getattr(row, k) for k in fields})
    return out


def resolve_data_file(algo: str, scen: str, fname: str) -> Path | None:
    candidates = [
        FULL_DATA / algo / scen / "data" / fname,
        REPO / "outputs" / RUN_ID / algo / scen / "data" / fname,
    ]
    for path in candidates:
        if path.is_file() and path.stat().st_size > 0:
            return path
    return None


def read_results(algo: str, scen: str) -> dict | None:
    path = KPIS_DIR / f"{algo.lower()}_{scen}_results.json"
    if not path.exists():
        return None
    return read_json(path)


def district_objectives(results: dict) -> dict[str, float | None]:
    av = (results.get("citylearn_v3_report") or {}).get("all_values") or {}
    peak = av.get("peak_average") or av.get("cost_peak_average")
    ramp = av.get("ramping_average") or av.get("cost_ramping_average")
    lf = av.get("one_minus_load_factor_average") or av.get("cost_one_minus_load_factor_average")
    flex_vals = [v for v in (peak, ramp, lf) if v is not None and not (isinstance(v, float) and math.isnan(v))]
    flex = sum(flex_vals) / len(flex_vals) if flex_vals else None
    return {
        "flex_composite": flex,
        "peak_average": peak,
        "ramping_average": ramp,
        "one_minus_load_factor_average": lf,
        "carbon_emissions_delta_kg": av.get("carbon_emissions_delta"),
        "electricity_cost_delta_eur": av.get("electricity_cost_delta"),
        "ev_departure_count": av.get("ev_departure_count"),
        "ev_departure_success_rate": av.get("ev_departure_success_rate"),
        "pv_generation_total": av.get("pv_generation_total"),
        "grid_import_delta": av.get("grid_import_delta"),
    }


def read_behavior_summary(algo: str, scen: str) -> list[dict[str, Any]]:
    path = resolve_data_file(algo, scen, "building_behavior_summary.csv")
    if path is None:
        return []
    with path.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


def building_objectives(behavior_rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for row in behavior_rows:
        agent = row.get("agent") or ""
        bid = parse_building_id(agent)
        gmax = _f(row.get("grid_import_max"))
        emax = _f(row.get("grid_export_max"))
        pv_sc = _f(row.get("pv_self_consumption_ratio"))
        flex_parts = [v for v in (gmax, emax, (1.0 - pv_sc) if pv_sc is not None else None) if v is not None]
        flex = sum(flex_parts) / len(flex_parts) if flex_parts else None
        out.append(
            {
                "building_id": bid,
                "agent": agent,
                "flex_composite_proxy": flex,
                "grid_import_max": gmax,
                "grid_export_max": emax,
                "pv_self_consumption_ratio": pv_sc,
                "carbon_emissions_delta_kgco2": _f(row.get("carbon_emissions_delta_kgco2")),
                "electricity_cost_delta_eur": _f(row.get("electricity_cost_delta_eur")),
                "ev_departure_count": _f(row.get("ev_departure_count")),
                "ev_departure_success_rate": _f(row.get("ev_departure_success_rate")),
                "ev_charge_total_kwh": _f(row.get("ev_charge_total_kwh")),
                "battery_throughput_total_kwh": _f(row.get("battery_throughput_total_kwh")),
                "grid_role_control": row.get("grid_role_control"),
            }
        )
    return out


def _f(val: Any) -> float | None:
    if val is None or val == "":
        return None
    try:
        x = float(val)
        if math.isnan(x):
            return None
        return x
    except (TypeError, ValueError):
        return None


def collect_tables(inventory: list[BuildingInventoryRow]) -> tuple[list[dict], list[dict]]:
    inv_by_id = {r.building_id: r for r in inventory}
    district_rows: list[dict] = []
    building_rows: list[dict] = []

    for algo in ALGOS:
        for scen in SCENARIOS:
            results = read_results(algo, scen)
            if not results:
                continue
            dist = district_objectives(results)
            district_rows.append(
                {
                    "run_id": RUN_ID,
                    "algorithm": algo,
                    "scenario": scen,
                    "objective": SCENARIO_OBJECTIVE[scen],
                    **dist,
                }
            )
            for brow in building_objectives(read_behavior_summary(algo, scen)):
                inv = inv_by_id.get(brow["building_id"])
                building_rows.append(
                    {
                        "run_id": RUN_ID,
                        "algorithm": algo,
                        "scenario": scen,
                        "objective": SCENARIO_OBJECTIVE[scen],
                        "nombre": inv.nombre if inv else "",
                        "tipo_uso": inv.tipo_uso if inv else "",
                        "ev_total": inv.ev_total if inv else None,
                        **brow,
                    }
                )
    return district_rows, building_rows


def write_csv(path: Path, rows: list[dict]) -> Path:
    if not rows:
        return path
    fields = sorted({k for r in rows for k in r})
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    return path


def plot_district_heatmap(district_rows: list[dict]) -> Path:
    metrics = {
        "E1": "flex_composite",
        "E2": "carbon_emissions_delta_kg",
        "E3": "electricity_cost_delta_eur",
    }
    fig, axes = plt.subplots(1, 3, figsize=(13, 4.5))
    fig.suptitle("KPIs multiobjetivo — distrito (Colab/Drive)")

    for ax, (scen, metric) in zip(axes, metrics.items()):
        matrix = []
        labels = []
        for algo in ALGOS:
            match = next(
                (r for r in district_rows if r["algorithm"] == algo and r["scenario"] == scen),
                None,
            )
            labels.append(algo)
            matrix.append(match.get(metric) if match else np.nan)

        colors = ["#2b6cb0", "#2f855a", "#dd6b20"]
        bars = ax.bar(labels, matrix, color=colors[: len(labels)])
        ax.set_title(SCENARIO_OBJECTIVE[scen])
        ax.tick_params(axis="x", rotation=15)
        for bar, val in zip(bars, matrix):
            if val is None or (isinstance(val, float) and math.isnan(val)):
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:,.0f}" if abs(val) > 100 else f"{val:.3f}",
                ha="center",
                va="bottom",
                fontsize=8,
            )

    plt.tight_layout()
    out = OUT / "drive_district_objectives.png"
    plt.savefig(out, dpi=300)
    plt.close()
    return out


def plot_building_heatmap(building_rows: list[dict], scen: str, metric: str, title: str) -> Path:
    inv_names = {
        r["building_id"]: f"B{r['building_id']:02d}"
        for r in building_rows
        if r["scenario"] == scen
    }
    bids = sorted(inv_names)
    if not bids:
        raise ValueError(f"Sin filas de edificio para {scen}")

    data = np.full((len(bids), len(ALGOS)), np.nan)
    for j, algo in enumerate(ALGOS):
        for i, bid in enumerate(bids):
            match = next(
                (
                    r
                    for r in building_rows
                    if r["algorithm"] == algo and r["scenario"] == scen and r["building_id"] == bid
                ),
                None,
            )
            if match and match.get(metric) is not None:
                data[i, j] = float(match[metric])

    fig, ax = plt.subplots(figsize=(8, 10))
    im = ax.imshow(data, aspect="auto", cmap="YlOrRd")
    ax.set_xticks(range(len(ALGOS)))
    ax.set_xticklabels(ALGOS)
    ax.set_yticks(range(len(bids)))
    ax.set_yticklabels([inv_names[b] for b in bids], fontsize=8)
    ax.set_title(title)
    plt.colorbar(im, ax=ax, fraction=0.025, pad=0.02)
    plt.tight_layout()
    out = OUT / f"drive_building_{scen}_{metric}.png"
    plt.savefig(out, dpi=300)
    plt.close()
    return out


def plot_ev_inventory(inventory: list[BuildingInventoryRow]) -> Path:
    labels = [f"B{r.building_id:02d}" for r in inventory]
    totals = [r.ev_total for r in inventory]
    moto = [r.ev_moto_lineal for r in inventory]
    mototaxi = [r.ev_mototaxi for r in inventory]
    cam = [r.ev_camioneta for r in inventory]

    x = np.arange(len(labels))
    width = 0.22
    fig, ax = plt.subplots(figsize=(14, 5))
    ax.bar(x - width, moto, width, label="Moto lineal")
    ax.bar(x, mototaxi, width, label="Mototaxi")
    ax.bar(x + width, cam, width, label="Camioneta")
    ax.set_xticks(x)
    ax.set_xticklabels(labels, rotation=90, fontsize=8)
    ax.set_ylabel("Cargadores EV controlables")
    ax.set_title("Inventario EV por edificio — Iquitos (185 tomas totales)")
    ax.legend()
    plt.tight_layout()
    out = OUT / "drive_building_ev_inventory.png"
    plt.savefig(out, dpi=300)
    plt.close()
    return out


def plot_ev_success(building_rows: list[dict], inventory: list[BuildingInventoryRow]) -> Path:
    """Tasa de éxito EV por edificio para el mejor algoritmo MATD3 E2."""
    rows = [r for r in building_rows if r["algorithm"] == "MATD3" and r["scenario"] == "E2"]
    rows.sort(key=lambda r: r["building_id"])
    names = [f"B{r['building_id']:02d}" for r in rows]
    rates = [r.get("ev_departure_success_rate") or 0 for r in rows]
    counts = [r.get("ev_departure_count") or 0 for r in rows]

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax2 = ax1.twinx()
    ax1.bar(names, rates, color="#3182ce", alpha=0.85, label="success rate")
    ax2.plot(names, counts, color="#dd6b20", marker="o", label="departures")
    ax1.set_ylabel("EV departure success rate")
    ax2.set_ylabel("EV departure count")
    ax1.set_title("Desempeño EV por edificio — MATD3 / E2 (Colab/Drive)")
    ax1.tick_params(axis="x", rotation=90)
    plt.tight_layout()
    out = OUT / "drive_building_ev_success_matd3_e2.png"
    plt.savefig(out, dpi=300)
    plt.close()
    return out


def plot_building_objectives_card(
    building_rows: list[dict],
    inventory: list[BuildingInventoryRow],
    building_id: int,
) -> Path:
    """Figura individual Bxx: 3 escenarios × 3 algoritmos para flex, CO₂ y costo."""
    inv = next((r for r in inventory if r.building_id == building_id), None)
    label = f"B{building_id:02d}"
    title_name = inv.nombre if inv else label

    metrics = [
        ("flex_composite_proxy", "OE1 Flex proxy", "E1"),
        ("carbon_emissions_delta_kgco2", "OE2 Δ CO₂ (kg)", "E2"),
        ("electricity_cost_delta_eur", "OE3 Δ Costo (EUR)", "E3"),
    ]
    colors = {"MASAC": "#2b6cb0", "MATD3": "#2f855a", "MAAC": "#dd6b20"}

    fig, axes = plt.subplots(1, 3, figsize=(12, 4))
    fig.suptitle(f"{label} — {title_name}", fontsize=11)

    for ax, (metric, ylabel, scen) in zip(axes, metrics):
        x = np.arange(len(ALGOS))
        vals = []
        for algo in ALGOS:
            match = next(
                (
                    r
                    for r in building_rows
                    if r["algorithm"] == algo
                    and r["scenario"] == scen
                    and r["building_id"] == building_id
                ),
                None,
            )
            vals.append(match.get(metric) if match else np.nan)
        bars = ax.bar(x, vals, color=[colors[a] for a in ALGOS])
        ax.set_xticks(x)
        ax.set_xticklabels(ALGOS, fontsize=8)
        ax.set_title(SCENARIO_OBJECTIVE[scen])
        ax.set_ylabel(ylabel)
        for bar, val in zip(bars, vals):
            if val is None or (isinstance(val, float) and math.isnan(val)):
                continue
            ax.text(
                bar.get_x() + bar.get_width() / 2,
                bar.get_height(),
                f"{val:,.0f}" if abs(val) > 100 else f"{val:.2f}",
                ha="center",
                va="bottom" if val >= 0 else "top",
                fontsize=7,
            )

    plt.tight_layout()
    per_dir = OUT / "por_edificio"
    per_dir.mkdir(parents=True, exist_ok=True)
    out = per_dir / f"drive_building_{label}_objectives.png"
    plt.savefig(out, dpi=300)
    plt.close()
    return out


def plot_all_building_cards(
    building_rows: list[dict],
    inventory: list[BuildingInventoryRow],
) -> list[Path]:
    bids = sorted({r["building_id"] for r in building_rows})
    return [plot_building_objectives_card(building_rows, inventory, bid) for bid in bids]


def write_building_detail_report(
    inventory: list[BuildingInventoryRow],
    building_rows: list[dict],
    algo: str = "MATD3",
) -> Path:
    inv_by_id = {r.building_id: r for r in inventory}
    out = OUT / f"building_detail_{algo.lower()}_by_scenario.md"
    lines = [f"# Detalle por edificio — {algo} (Colab/Drive)\n"]
    for scen in SCENARIOS:
        lines.append(f"\n## {scen} — {SCENARIO_OBJECTIVE[scen]}\n")
        lines.append(
            "| ID | Edificio | EV | Controlados | Δ CO₂ (kg) | Δ Costo (EUR) | "
            "Flex proxy | EV éxito | Rol red |\n"
            "|----|----------|----|-------------|------------|---------------|"
            "-----------|----------|--------|\n"
        )
        rows = sorted(
            [r for r in building_rows if r["algorithm"] == algo and r["scenario"] == scen],
            key=lambda r: r["building_id"],
        )
        for row in rows:
            inv = inv_by_id.get(row["building_id"])
            co2 = row.get("carbon_emissions_delta_kgco2")
            cost = row.get("electricity_cost_delta_eur")
            flex = row.get("flex_composite_proxy")
            ev_ok = row.get("ev_departure_success_rate")

            def _fmt_num(val: float | None, spec: str) -> str:
                return "-" if val is None else format(val, spec)

            lines.append(
                f"| B{row['building_id']:02d} | {inv.nombre if inv else row['agent']} | "
                f"{inv.ev_total if inv else '-'} | "
                f"{(inv.elementos_controlados if inv else '-').replace('|', '/')} | "
                f"{_fmt_num(co2, ',.1f')} | {_fmt_num(cost, ',.1f')} | {_fmt_num(flex, '.3f')} | "
                f"{_fmt_num(ev_ok, '.1%')} | {row.get('grid_role_control', '-')} |\n"
            )
    out.write_text("".join(lines), encoding="utf-8")
    return out


def write_thesis_mapping(inventory: list[BuildingInventoryRow], generated: dict[str, str]) -> Path:
    total_ev = sum(r.ev_total for r in inventory)
    content = f"""# Análisis multiobjetivo Colab/Drive — {RUN_ID}

## Alcance

- **Distrito:** KPIs agregados desde `citylearn_v3_report.all_values` en `outputs/_drive_madrl/kpis/*_results.json`.
- **Edificio:** KPIs desde `building_behavior_summary.csv` (17 filas por job) y `building_kpis.csv` (1275 filas).
- **Inventario:** 17 edificios Iquitos con nombre, tipo de uso, elementos controlados/no controlados y **{total_ev} cargadores EV** dimensionados.

## Objetivos multiobjetivo

| Escenario | Objetivo | KPI distrito principal | KPI edificio principal |
|-----------|----------|------------------------|-------------------------|
| E1 | OE1 Flexibilidad | flex_composite (peak+ramping+load_factor)/3 | flex_composite_proxy |
| E2 | OE2 CO₂ | carbon_emissions_delta_kg | carbon_emissions_delta_kgco2 |
| E3 | OE3 Costo | electricity_cost_delta_eur | electricity_cost_delta_eur |

## Elementos por edificio

- **Controlados (acciones MADRL):** BESS (`electrical_storage`), cargadores EV (`electric_vehicle_storage_*`), carga desplazable (`washing_machine_*`).
- **No controlados:** `non_shiftable_load`, refrigeración/ACS modeladas, generación FV fija.

## Artefactos generados

"""
    for key, path in sorted(generated.items()):
        content += f"- `{Path(path).name}`: {key}\n"

    content += """

## Cobertura por algoritmo

Detalle por edificio disponible para **MASAC**, **MATD3** y **MAAC** (17 edificios × 3 escenarios).

## Edificios incluidos

"""
    for row in inventory:
        content += (
            f"- **B{row.building_id:02d} {row.nombre}** ({row.tipo_uso}): "
            f"EV={row.ev_total} (ML={row.ev_moto_lineal}, MT={row.ev_mototaxi}, CV={row.ev_camioneta}); "
            f"controlados: {row.elementos_controlados}\n"
        )

    out = OUT / "drive_multiobjective_thesis_mapping.md"
    out.write_text(content, encoding="utf-8")
    return out


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = build_inventory()
    district_rows, building_rows = collect_tables(inventory)

    generated = {
        "building_inventory_csv": str(write_inventory_csv(inventory)),
        "district_objectives_csv": str(write_csv(OUT / "district_objectives_by_algorithm.csv", district_rows)),
        "building_objectives_csv": str(write_csv(OUT / "building_objectives_by_algorithm.csv", building_rows)),
        "district_objectives_png": str(plot_district_heatmap(district_rows)),
        "building_ev_inventory_png": str(plot_ev_inventory(inventory)),
    }

    if building_rows:
        for algo in ALGOS:
            generated[f"building_detail_{algo.lower()}_md"] = str(
                write_building_detail_report(inventory, building_rows, algo)
            )
        generated["building_e1_flex_png"] = str(
            plot_building_heatmap(
                building_rows,
                "E1",
                "flex_composite_proxy",
                "OE1 Flexibilidad por edificio — proxy compuesto",
            )
        )
        generated["building_e2_co2_png"] = str(
            plot_building_heatmap(
                building_rows,
                "E2",
                "carbon_emissions_delta_kgco2",
                "OE2 Delta CO₂ por edificio (kg)",
            )
        )
        generated["building_e3_cost_png"] = str(
            plot_building_heatmap(
                building_rows,
                "E3",
                "electricity_cost_delta_eur",
                "OE3 Delta costo por edificio (EUR)",
            )
        )
        generated["building_ev_success_png"] = str(plot_ev_success(building_rows, inventory))
        per_building = plot_all_building_cards(building_rows, inventory)
        generated["building_cards_dir"] = str(OUT / "por_edificio")
        generated["building_cards_count"] = str(len(per_building))

    generated["thesis_mapping_md"] = str(write_thesis_mapping(inventory, generated))
    print(json.dumps({"output_dir": str(OUT), "generated": generated}, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
