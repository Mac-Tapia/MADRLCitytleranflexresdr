"""Final CityLearn v3 loading evaluation for the Iquitos dataset."""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
CITYLEARN_ROOT = ROOT / "CityLearn"
DATASET_DIR = CITYLEARN_ROOT / "data" / "datasets" / "citylearn_iquitos_2023_2025"
SCHEMA_PATH = DATASET_DIR / "schema.json"
OUT_DIR = ROOT / "outputs" / "dataset_audit"
REPORT_PATH = ROOT / "docs" / "INFORME_EVALUACION_FINAL_DATASET_IQUITOS_CITYLEARN_V3.md"
MANIFEST_PATH = OUT_DIR / "iquitos_citylearn_v3_dataset_evaluation.json"
EXPECTED_ROWS = 26304
SCENARIOS = ("E1", "E2", "E3")

if str(CITYLEARN_ROOT) not in sys.path:
    sys.path.insert(0, str(CITYLEARN_ROOT))


def _jsonable(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_jsonable(v) for v in value]
    return value


def _read_schema() -> dict[str, Any]:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _csv_row_count(path: Path) -> int:
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        reader = csv.reader(f)
        next(reader)
        return sum(1 for _ in reader)


def _charger_dataframe(path: Path) -> pd.DataFrame:
    return pd.read_csv(
        path,
        usecols=[
            "electric_vehicle_charger_state",
            "electric_vehicle_id",
            "electric_vehicle_required_soc_departure",
            "electric_vehicle_estimated_soc_arrival",
        ],
    )


def evaluate_schema(schema: dict[str, Any]) -> dict[str, Any]:
    buildings = {
        name: building
        for name, building in schema.get("buildings", {}).items()
        if building.get("include", True)
    }
    errors: list[str] = []
    charger_records: list[dict[str, Any]] = []
    physical_groups: dict[str, list[str]] = defaultdict(list)
    charger_counts_by_building: dict[str, int] = {}
    ev_pool_prefixes: dict[str, set[str]] = defaultdict(set)
    total_ev_kw = 0.0

    for building_name, building in sorted(buildings.items()):
        energy_file = DATASET_DIR / str(building.get("energy_simulation", ""))
        if not energy_file.exists():
            errors.append(f"{building_name}: missing {energy_file.name}")
        elif _csv_row_count(energy_file) != EXPECTED_ROWS:
            errors.append(f"{building_name}: invalid row count in {energy_file.name}")

        chargers = building.get("chargers") or {}
        charger_counts_by_building[building_name] = len(chargers)
        if len(chargers) <= 0:
            errors.append(f"{building_name}: no EV chargers assigned")

        for charger_name, charger in sorted(chargers.items()):
            hardware = charger.get("hardware") or {}
            attrs = charger.get("attributes") or {}
            csv_path = DATASET_DIR / str(charger.get("charger_simulation", ""))
            physical_id = str(hardware.get("physical_charger_id", ""))
            socket_count = int(hardware.get("socket_count_per_physical_unit", 0) or 0)
            outlet_index = int(hardware.get("outlet_index", 0) or 0)
            pool_size = int(hardware.get("electric_vehicle_pool_size", 0) or 0)
            pool_prefix = str(hardware.get("electric_vehicle_pool_prefix", ""))
            nominal_kw = float(attrs.get("nominal_power", 0.0) or 0.0)

            total_ev_kw += nominal_kw
            physical_groups[physical_id].append(charger_name)
            ev_pool_prefixes[charger_name] = set()

            if socket_count != 2:
                errors.append(f"{building_name}/{charger_name}: Mode 3 socket_count_per_physical_unit != 2")
            if outlet_index not in (1, 2):
                errors.append(f"{building_name}/{charger_name}: invalid outlet_index={outlet_index}")
            if pool_size <= 0:
                errors.append(f"{building_name}/{charger_name}: missing EV pool size")
            if not csv_path.exists():
                errors.append(f"{building_name}/{charger_name}: missing charger CSV {csv_path.name}")
                continue

            df = _charger_dataframe(csv_path)
            if len(df) != EXPECTED_ROWS:
                errors.append(f"{building_name}/{charger_name}: invalid row count {len(df)}")

            states = pd.to_numeric(df["electric_vehicle_charger_state"], errors="coerce").astype("Int64")
            occupied = df[states.isin([1, 2])].copy()
            active = df[states.eq(1)].copy()

            if not set(states.dropna().astype(int).unique()).issubset({1, 2, 3}):
                errors.append(f"{building_name}/{charger_name}: invalid charger states")

            ev_ids = set(str(v).strip() for v in occupied["electric_vehicle_id"].dropna().unique())
            ev_ids = {v for v in ev_ids if v and v.upper() != "NONE" and v.lower() != "nan"}
            ev_pool_prefixes[charger_name] = ev_ids
            if len(ev_ids) > pool_size:
                errors.append(f"{building_name}/{charger_name}: EV ids exceed pool size")
            if pool_prefix and any(not ev_id.startswith(pool_prefix) for ev_id in ev_ids):
                errors.append(f"{building_name}/{charger_name}: EV id outside charger pool prefix")

            req = pd.to_numeric(active["electric_vehicle_required_soc_departure"], errors="coerce")
            arr = pd.to_numeric(active["electric_vehicle_estimated_soc_arrival"], errors="coerce")
            if len(active) > 0:
                if not req.between(0.0, 100.0).all():
                    errors.append(f"{building_name}/{charger_name}: required SOC outside 0-100")
                if not arr.between(0.0, 100.0).all():
                    errors.append(f"{building_name}/{charger_name}: arrival SOC outside 0-100")

            charger_records.append(
                {
                    "building": building_name,
                    "charger": charger_name,
                    "physical_charger_id": physical_id,
                    "outlet_index": outlet_index,
                    "nominal_power_kw": nominal_kw,
                    "pool_size": pool_size,
                    "unique_ev_ids_used": len(ev_ids),
                    "state1_hours": int(states.eq(1).sum()),
                    "state2_hours": int(states.eq(2).sum()),
                }
            )

    ev_defs = schema.get("electric_vehicles_def") or {}
    ev_ids_used = set().union(*(record_ids for record_ids in ev_pool_prefixes.values())) if ev_pool_prefixes else set()
    missing_defs = sorted(ev_id for ev_id in ev_ids_used if ev_id not in ev_defs)
    if missing_defs:
        errors.append(f"{len(missing_defs)} EV ids used in charger CSVs are missing from electric_vehicles_def")

    physical_group_errors = []
    for physical_id, chargers in physical_groups.items():
        if not physical_id:
            physical_group_errors.append("empty physical_charger_id")
        if len(chargers) > 2:
            physical_group_errors.append(f"{physical_id}: more than 2 outlets")
    errors.extend(physical_group_errors)

    return {
        "ok": not errors,
        "errors": errors,
        "buildings": len(buildings),
        "buildings_with_chargers": sum(1 for count in charger_counts_by_building.values() if count > 0),
        "charger_count": len(charger_records),
        "physical_mode3_units": len(physical_groups),
        "electric_vehicle_definitions": len(ev_defs),
        "electric_vehicle_ids_used": len(ev_ids_used),
        "ev_nominal_power_kw": round(total_ev_kw, 3),
        "charger_counts_by_building": charger_counts_by_building,
        "charger_records": charger_records,
    }


def evaluate_simultaneity(schema: dict[str, Any]) -> dict[str, Any]:
    buildings = {name: b for name, b in schema.get("buildings", {}).items() if b.get("include", True)}
    physical_to_files: dict[str, list[Path]] = defaultdict(list)
    for building in buildings.values():
        for charger in (building.get("chargers") or {}).values():
            hardware = charger.get("hardware") or {}
            physical_id = str(hardware.get("physical_charger_id", ""))
            physical_to_files[physical_id].append(DATASET_DIR / str(charger.get("charger_simulation", "")))

    paired_units = 0
    paired_units_with_simultaneous_state1 = 0
    max_pair_simultaneous = 0
    for files in physical_to_files.values():
        if len(files) != 2:
            continue
        paired_units += 1
        states = []
        for path in files:
            df = pd.read_csv(path, usecols=["electric_vehicle_charger_state"])
            states.append(pd.to_numeric(df["electric_vehicle_charger_state"], errors="coerce").eq(1))
        simultaneous = (states[0] & states[1]).sum()
        max_pair_simultaneous = max(max_pair_simultaneous, int(simultaneous))
        if simultaneous > 0:
            paired_units_with_simultaneous_state1 += 1

    return {
        "mode3_units_with_two_outlets": paired_units,
        "units_observed_with_simultaneous_state1": paired_units_with_simultaneous_state1,
        "max_simultaneous_hours_in_one_unit": max_pair_simultaneous,
        "simultaneous_charging_allowed_by_schema": True,
    }


def evaluate_citylearn_v3_loads() -> dict[str, Any]:
    from citylearn.v3 import describe_environment, make_citylearn_v3_env

    scenario_results: dict[str, Any] = {}
    errors: list[str] = []
    for scenario in SCENARIOS:
        try:
            env = make_citylearn_v3_env(
                schema_path=str(SCHEMA_PATH),
                scenario=scenario,
                seed=0,
                episode_time_steps=24,
            )
            try:
                observations, infos = env.reset(seed=0)
                for _ in range(3):
                    actions = {
                        agent: np.zeros(env.action_space(agent).shape, dtype=np.float32)
                        for agent in env.possible_agents
                    }
                    observations, rewards, terminations, truncations, infos = env.step(actions)
                    if any(terminations.values()) or any(truncations.values()):
                        break

                description = describe_environment(env)
                scenario_results[scenario] = {
                    "ok": True,
                    "num_agents": description.get("num_agents"),
                    "state_dim": description.get("state_dim"),
                    "observation_dims": description.get("observation_dims"),
                    "action_dims": description.get("action_dims"),
                    "has_ev_actions": description.get("has_ev_actions"),
                    "has_ev_observations": description.get("has_ev_observations"),
                    "reward_function": description.get("reward_function"),
                    "reward_aggregation": description.get("reward_aggregation"),
                    "kpi_frame_shape": list(env.get_kpi_frame().shape),
                }
            finally:
                env.close()
        except Exception as exc:
            scenario_results[scenario] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            errors.append(f"{scenario}: {type(exc).__name__}: {exc}")

    return {"ok": not errors, "errors": errors, "scenarios": scenario_results}


def write_report(payload: dict[str, Any]) -> None:
    schema_eval = payload["schema_evaluation"]
    citylearn_eval = payload["citylearn_v3_load_evaluation"]
    sim_eval = payload["mode3_simultaneity"]
    scenario_rows = []
    for scenario, data in citylearn_eval["scenarios"].items():
        scenario_rows.append(
            f"| {scenario} | {'OK' if data.get('ok') else 'FAIL'} | {data.get('num_agents', '')} | "
            f"{data.get('state_dim', '')} | {data.get('has_ev_actions', '')} | {data.get('has_ev_observations', '')} |"
        )

    lines = [
        "# Evaluacion final dataset Iquitos - CityLearn v3",
        "",
        f"Fecha UTC: `{payload['generated_at']}`",
        "",
        "## Resultado",
        "",
        f"- Estado global: `{'OK' if payload['ok'] else 'FAIL'}`.",
        f"- Edificios cargados: `{schema_eval['buildings']}`.",
        f"- Edificios con tomas EV: `{schema_eval['buildings_with_chargers']}`.",
        f"- Tomas/loadpoints Mode 3 CityLearn: `{schema_eval['charger_count']}`.",
        f"- Equipos fisicos Mode 3 doble toma: `{schema_eval['physical_mode3_units']}`.",
        f"- EV definidos en pool: `{schema_eval['electric_vehicle_definitions']}`.",
        f"- Potencia EV nominal simultanea: `{schema_eval['ev_nominal_power_kw']}` kW.",
        f"- Unidades fisicas con simultaneidad observada en ambas tomas: `{sim_eval['units_observed_with_simultaneous_state1']}` de `{sim_eval['mode3_units_with_two_outlets']}`.",
        "",
        "## Carga CityLearn v3",
        "",
        "| Escenario | Estado | Agentes | State dim | EV acciones | EV observaciones |",
        "|---|---:|---:|---:|---:|---:|",
        *scenario_rows,
        "",
        "## Criterio EV",
        "",
        "El dataset trata `charger_X_Y.csv` como toma/loadpoint controlable Mode 3. Cada equipo fisico agrupa dos tomas mediante `physical_charger_id` y ambas pueden cargar simultaneamente. Los EV no son fijos 1:1 con tomas: cada toma usa un pool de EVs y cada sesion queda gobernada por `electric_vehicle_estimated_soc_arrival` y `electric_vehicle_required_soc_departure`.",
        "",
        "## Evidencia",
        "",
        f"- Manifest JSON: `{MANIFEST_PATH}`",
        "- Compueras previas: `outputs/dataset_audit/csv_integrity_manifest.json` y `outputs/dataset_audit/training_dataset_ready_manifest.json`.",
        "",
    ]
    REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    schema = _read_schema()
    schema_eval = evaluate_schema(schema)
    simultaneity = evaluate_simultaneity(schema)
    citylearn_eval = evaluate_citylearn_v3_loads()
    payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "schema_path": str(SCHEMA_PATH),
        "ok": bool(schema_eval["ok"] and citylearn_eval["ok"]),
        "schema_evaluation": schema_eval,
        "mode3_simultaneity": simultaneity,
        "citylearn_v3_load_evaluation": citylearn_eval,
    }
    MANIFEST_PATH.write_text(json.dumps(_jsonable(payload), indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(payload)
    print(json.dumps(_jsonable(payload), indent=2, ensure_ascii=False))
    return 0 if payload["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
