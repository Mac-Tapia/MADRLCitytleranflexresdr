"""Final gate for the raw Iquitos CityLearn training dataset.

This check runs before MADRL backends normalize observations. It verifies that
the real/supplied raw layers, generated CityLearn files, DER audits and
CityLearnEnv loading all agree on the same dataset.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
DEFAULT_BUILDINGCSV_DIR = ROOT / "CityLearn" / "data" / "buildingcsv"
DEFAULT_AUDIT_DIR = ROOT / "outputs" / "dataset_audit"
DEFAULT_MANIFEST = DEFAULT_AUDIT_DIR / "training_dataset_ready_manifest.json"

EXPECTED_ROWS = 26304
EXPECTED_BUILDINGS = 17
BUILDING_COLUMNS = [
    "month",
    "hour",
    "day_type",
    "daylight_savings_status",
    "indoor_dry_bulb_temperature",
    "average_unmet_cooling_setpoint_difference",
    "indoor_relative_humidity",
    "non_shiftable_load",
    "dhw_demand",
    "cooling_demand",
    "heating_demand",
    "solar_generation",
]
SUPPORT_FILES = {
    "weather.csv": 16,
    "carbon_intensity.csv": 1,
    "pricing.csv": 4,
}
PRICING_COLUMNS = [
    "electricity_pricing",
    "electricity_pricing_predicted_1",
    "electricity_pricing_predicted_2",
    "electricity_pricing_predicted_3",
]
CARBON_COLUMNS = ["carbon_intensity"]
WASHING_MACHINE_COLUMNS = [
    "day_type",
    "hour",
    "wm_start_time_step",
    "wm_end_time_step",
    "load_profile",
]
CHARGER_COLUMNS = [
    "electric_vehicle_charger_state",
    "electric_vehicle_id",
    "electric_vehicle_departure_time",
    "electric_vehicle_required_soc_departure",
    "electric_vehicle_estimated_arrival_time",
    "electric_vehicle_estimated_soc_arrival",
]
VALID_CHARGER_STATES = {1, 2, 3}
MAX_EV_OUTSIDE_WINDOW_MWH = 1.0e-6
MAX_BASE_DELTA_PCT = 0.01
MAX_PV_CLOSURE_MWH = 0.01


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _jsonable(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(k): _jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_jsonable(v) for v in value]
    if isinstance(value, (np.integer,)):
        return int(value)
    if isinstance(value, (np.floating,)):
        return float(value)
    if isinstance(value, (np.bool_,)):
        return bool(value)
    if isinstance(value, Path):
        return _rel(value)
    return value


def _load_json(path: Path, issues: list[str]) -> dict[str, Any]:
    if not path.exists():
        issues.append(f"Falta archivo requerido: {_rel(path)}")
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:  # pragma: no cover - defensive report path
        issues.append(f"No se pudo leer JSON {_rel(path)}: {exc}")
        return {}


def _schema_buildings(schema: dict[str, Any]) -> dict[str, Any]:
    buildings = schema.get("buildings", {})
    return buildings if isinstance(buildings, dict) else {}


def _check_raw_inputs(buildingcsv_dir: Path, issues: list[str], warnings: list[str]) -> dict[str, Any]:
    status: dict[str, Any] = {
        "building_inventory": _rel(buildingcsv_dir / "building.csv"),
        "monthly_files_required": [],
        "monthly_files_optional": [],
    }

    if not (buildingcsv_dir / "building.csv").exists():
        issues.append(f"Falta inventario real de edificios: {_rel(buildingcsv_dir / 'building.csv')}")

    for bid in range(2, EXPECTED_BUILDINGS + 1):
        path = buildingcsv_dir / f"B_{bid:02d}.csv"
        status["monthly_files_required"].append(_rel(path))
        if not path.exists():
            issues.append(f"Falta medicion/fuente mensual real B{bid:02d}: {_rel(path)}")

    b01 = buildingcsv_dir / "B_01.csv"
    status["monthly_files_optional"].append(_rel(b01))
    if not b01.exists():
        warnings.append("B01 no tiene B_01.csv mensual; se acepta solo si la auditoria lo marca como politica explicita.")

    return status


def _check_support_files(dataset_dir: Path, issues: list[str]) -> dict[str, Any]:
    status: dict[str, Any] = {}

    for filename, expected_cols in SUPPORT_FILES.items():
        path = dataset_dir / filename
        entry = {"path": _rel(path), "exists": path.exists()}
        if not path.exists():
            issues.append(f"Falta archivo de soporte: {_rel(path)}")
            status[filename] = entry
            continue

        df = pd.read_csv(path)
        entry.update({"rows": len(df), "columns": len(df.columns), "sha256": _sha256(path)})
        if len(df) != EXPECTED_ROWS:
            issues.append(f"{_rel(path)} tiene {len(df)} filas; esperado {EXPECTED_ROWS}")
        if len(df.columns) != expected_cols:
            issues.append(f"{_rel(path)} tiene {len(df.columns)} columnas; esperado {expected_cols}")
        if bool(df.isna().any().any()):
            issues.append(f"{_rel(path)} contiene NaN")

        if filename == "pricing.csv":
            entry["role"] = "costos_energia"
            if df.columns.tolist() != PRICING_COLUMNS:
                issues.append(f"{_rel(path)} no tiene columnas de costo CityLearn esperadas")
            if "electricity_pricing" in df.columns:
                price = pd.to_numeric(df["electricity_pricing"], errors="coerce")
                entry["min"] = float(price.min())
                entry["max"] = float(price.max())
                entry["mean"] = float(price.mean())
                if bool(price.isna().any()) or float(price.min()) < 0.0 or float(price.max()) <= 0.0:
                    issues.append(f"{_rel(path)} no contiene una senal de costo positiva valida")

        if filename == "carbon_intensity.csv":
            entry["role"] = "emisiones_CO2"
            if df.columns.tolist() != CARBON_COLUMNS:
                issues.append(f"{_rel(path)} no tiene columna carbon_intensity esperada")
            if "carbon_intensity" in df.columns:
                carbon = pd.to_numeric(df["carbon_intensity"], errors="coerce")
                entry["min"] = float(carbon.min())
                entry["max"] = float(carbon.max())
                entry["mean"] = float(carbon.mean())
                if bool(carbon.isna().any()) or float(carbon.min()) <= 0.0:
                    issues.append(f"{_rel(path)} no contiene una senal de emisiones positiva valida")

        if filename == "weather.csv":
            entry["role"] = "clima_CityLearn"
        status[filename] = entry

    controlled_status: dict[str, Any] = {"role": "maquinas_controladas_por_edificio", "files": {}}
    for bid in range(1, EXPECTED_BUILDINGS + 1):
        washing_path = dataset_dir / f"Washing_Machine_{bid}.csv"
        washing_entry = {"path": _rel(washing_path), "exists": washing_path.exists()}
        if not washing_path.exists():
            issues.append(f"Falta dataset de maquina controlada B{bid:02d}: {_rel(washing_path)}")
            controlled_status["files"][f"B{bid:02d}"] = washing_entry
            continue

        df = pd.read_csv(washing_path)
        washing_entry.update({"rows": len(df), "columns": len(df.columns), "sha256": _sha256(washing_path)})
        if len(df) != EXPECTED_ROWS:
            issues.append(f"{_rel(washing_path)} tiene {len(df)} filas; esperado {EXPECTED_ROWS}")
        if df.columns.tolist() != WASHING_MACHINE_COLUMNS:
            issues.append(f"{_rel(washing_path)} no tiene columnas de maquina controlada esperadas")
        if bool(df.isna().any().any()):
            issues.append(f"{_rel(washing_path)} contiene NaN")
        if "wm_start_time_step" in df.columns:
            active_cycles = int((pd.to_numeric(df["wm_start_time_step"], errors="coerce") >= 0).sum())
            washing_entry["active_cycle_rows"] = active_cycles
            if active_cycles <= 0:
                issues.append(f"{_rel(washing_path)} no contiene ventanas activas de maquina controlada")
        controlled_status["files"][f"B{bid:02d}"] = washing_entry
    status["controlled_machines"] = controlled_status

    return status


def _check_citylearn_files(dataset_dir: Path, schema: dict[str, Any], issues: list[str]) -> dict[str, Any]:
    buildings = _schema_buildings(schema)
    status: dict[str, Any] = {
        "building_count": len(buildings),
        "charger_count": 0,
        "physical_charger_count": 0,
        "ev_definition_count": len(schema.get("electric_vehicles_def", {}) or {}),
        "building_hashes": {},
        "support_references": {"weather": 0, "carbon_intensity": 0, "pricing": 0},
        "controlled_machine_references": 0,
    }

    if len(buildings) != EXPECTED_BUILDINGS:
        issues.append(f"schema.json tiene {len(buildings)} edificios; esperado {EXPECTED_BUILDINGS}")
    if schema.get("central_agent") is not False:
        issues.append("schema.json debe usar central_agent=false para entrenamiento multiagente descentralizado.")

    physical_ids: set[str] = set()
    referenced_charger_files: set[str] = set()
    referenced_machine_files: set[str] = set()
    for bid in range(1, EXPECTED_BUILDINGS + 1):
        bkey = f"Building_{bid}"
        bdata = buildings.get(bkey, {})
        if not bdata:
            issues.append(f"schema.json no contiene {bkey}")
            continue

        for field, expected_file in (
            ("weather", "weather.csv"),
            ("carbon_intensity", "carbon_intensity.csv"),
            ("pricing", "pricing.csv"),
        ):
            if bdata.get(field) != expected_file:
                issues.append(f"{bkey} no referencia {expected_file} en campo {field}")
            else:
                status["support_references"][field] += 1

        csv_name = bdata.get("energy_simulation", f"{bkey}.csv")
        csv_path = dataset_dir / str(csv_name)
        if not csv_path.exists():
            issues.append(f"Falta CSV de edificio: {_rel(csv_path)}")
        else:
            df = pd.read_csv(csv_path)
            status["building_hashes"][bkey] = _sha256(csv_path)
            if len(df) != EXPECTED_ROWS:
                issues.append(f"{_rel(csv_path)} tiene {len(df)} filas; esperado {EXPECTED_ROWS}")
            if df.columns.tolist() != BUILDING_COLUMNS:
                issues.append(f"{_rel(csv_path)} no conserva las 12 columnas CityLearn esperadas")
            if bool(df[BUILDING_COLUMNS].isna().any().any()):
                issues.append(f"{_rel(csv_path)} contiene NaN")
            nonnegative_cols = ["non_shiftable_load", "dhw_demand", "cooling_demand", "heating_demand", "solar_generation"]
            if bool((df[nonnegative_cols] < 0.0).any().any()):
                issues.append(f"{_rel(csv_path)} contiene valores energeticos negativos")

        pv_kw = float((bdata.get("pv", {}).get("attributes", {}) or {}).get("nominal_power", 0.0) or 0.0)
        if pv_kw <= 0.0:
            issues.append(f"{bkey} no tiene PV nominal positivo en schema.json")

        storage = bdata.get("electrical_storage", {}).get("attributes", {}) or {}
        bess_kwh = float(storage.get("capacity", 0.0) or 0.0)
        bess_kw = float(storage.get("nominal_power", 0.0) or 0.0)
        if bess_kwh <= 10.0 or bess_kw <= 5.0:
            issues.append(f"{bkey} conserva BESS preliminar o invalido: {bess_kwh:.3f} kWh / {bess_kw:.3f} kW")

        for cname, cfg in (bdata.get("chargers") or {}).items():
            status["charger_count"] += 1
            hardware = cfg.get("hardware", {}) or {}
            physical_id = hardware.get("physical_charger_id")
            if physical_id:
                physical_ids.add(str(physical_id))

            sim_name = cfg.get("charger_simulation")
            if not sim_name:
                issues.append(f"{bkey}/{cname} no referencia charger_simulation")
                continue

            referenced_charger_files.add(str(sim_name))
            cpath = dataset_dir / str(sim_name)
            if not cpath.exists():
                issues.append(f"Falta CSV de cargador: {_rel(cpath)}")
                continue

            cdf = pd.read_csv(cpath)
            if len(cdf) != EXPECTED_ROWS:
                issues.append(f"{_rel(cpath)} tiene {len(cdf)} filas; esperado {EXPECTED_ROWS}")
            if cdf.columns.tolist() != CHARGER_COLUMNS:
                issues.append(f"{_rel(cpath)} no tiene columnas EV esperadas")
            if bool(cdf.isna().any().any()):
                issues.append(f"{_rel(cpath)} contiene NaN")
            if "electric_vehicle_charger_state" not in cdf.columns:
                issues.append(f"{_rel(cpath)} no tiene electric_vehicle_charger_state")
            else:
                states = set(cdf["electric_vehicle_charger_state"].dropna().astype(int).unique().tolist())
                invalid = sorted(states - VALID_CHARGER_STATES)
                if invalid:
                    issues.append(f"{_rel(cpath)} contiene estados EV invalidos: {invalid}")

        washing_machines = bdata.get("washing_machines") or {}
        expected_wm = f"Washing_Machine_{bid}.csv"
        if not washing_machines:
            issues.append(f"{bkey} no referencia su maquina controlada {expected_wm}")
        for wm_name, wm_cfg in washing_machines.items():
            sim_name = wm_cfg.get("washing_machine_energy_simulation")
            if sim_name != expected_wm:
                issues.append(f"{bkey}/{wm_name} no apunta a {expected_wm}")
            elif not (dataset_dir / sim_name).exists():
                issues.append(f"{bkey}/{wm_name} apunta a un archivo inexistente: {sim_name}")
            else:
                referenced_machine_files.add(str(sim_name))
                status["controlled_machine_references"] += 1

    status["physical_charger_count"] = len(physical_ids)
    if status["charger_count"] <= 0:
        issues.append("schema.json no contiene cargadores EV controlables")
    if status["ev_definition_count"] < status["charger_count"]:
        issues.append(
            "electric_vehicles_def tiene menos EV definidos que tomas controlables "
            f"({status['ev_definition_count']} < {status['charger_count']})"
        )

    for field, count in status["support_references"].items():
        if count != EXPECTED_BUILDINGS:
            issues.append(f"schema.json carga {field} en {count}/{EXPECTED_BUILDINGS} edificios")
    if status["controlled_machine_references"] != EXPECTED_BUILDINGS:
        issues.append(
            f"schema.json debe cargar una maquina controlada por edificio "
            f"({status['controlled_machine_references']}/{EXPECTED_BUILDINGS})"
        )

    charger_files = {path.name for path in dataset_dir.glob("charger_*.csv")}
    orphan_chargers = sorted(charger_files - referenced_charger_files)
    missing_chargers = sorted(referenced_charger_files - charger_files)
    status["orphan_charger_files"] = orphan_chargers
    status["missing_charger_files"] = missing_chargers
    if orphan_chargers:
        issues.append(f"Hay charger_*.csv no cargados por schema.json: {orphan_chargers[:10]}")
    if missing_chargers:
        issues.append(f"schema.json referencia charger_*.csv faltantes: {missing_chargers[:10]}")

    machine_files = {path.name for path in dataset_dir.glob("Washing_Machine_*.csv")}
    orphan_machines = sorted(machine_files - referenced_machine_files)
    missing_machines = sorted(referenced_machine_files - machine_files)
    status["orphan_machine_files"] = orphan_machines
    status["missing_machine_files"] = missing_machines
    if orphan_machines:
        issues.append(f"Hay Washing_Machine_*.csv no cargados por schema.json: {orphan_machines[:10]}")
    if missing_machines:
        issues.append(f"schema.json referencia Washing_Machine_*.csv faltantes: {missing_machines[:10]}")

    actions = schema.get("actions", {}) or {}
    for action_name in ("electrical_storage", "electric_vehicle_storage", "washing_machine"):
        action_cfg = actions.get(action_name)
        if not action_cfg:
            issues.append(f"schema.json no expone accion controlable {action_name}")
        elif isinstance(action_cfg, dict) and action_cfg.get("active") is False:
            issues.append(f"schema.json tiene accion {action_name} desactivada")

    return status


def _check_training_audit(audit_dir: Path, issues: list[str], warnings: list[str]) -> dict[str, Any]:
    path = audit_dir / "training_dataset_validation.json"
    data = _load_json(path, issues)
    metadata = data.get("metadata", {}) if isinstance(data, dict) else {}
    rows = data.get("rows", []) if isinstance(data, dict) else []

    status = {
        "path": _rel(path),
        "all_valid": bool(metadata.get("all_valid", False)),
        "rows": len(rows),
        "max_abs_base_delta_pct_B02_B17": metadata.get("max_abs_base_delta_pct_B02_B17"),
        "pv_closure_max_MWh": metadata.get("pv_closure_max_MWh"),
        "total_forecast_months": metadata.get("total_forecast_months"),
    }

    if not metadata.get("all_valid", False):
        issues.append("training_dataset_validation.json no declara all_valid=true")
    if len(rows) != EXPECTED_BUILDINGS:
        issues.append(f"training_dataset_validation.json tiene {len(rows)} filas; esperado {EXPECTED_BUILDINGS}")

    max_delta = float(metadata.get("max_abs_base_delta_pct_B02_B17", np.inf))
    if max_delta > MAX_BASE_DELTA_PCT:
        issues.append(f"Delta de carga base B02-B17 excede tolerancia: {max_delta:.9f}%")

    pv_closure = float(metadata.get("pv_closure_max_MWh", np.inf))
    if pv_closure > MAX_PV_CLOSURE_MWH:
        issues.append(f"Cierre PV excede tolerancia: {pv_closure:.9f} MWh")

    for row in rows:
        bid = str(row.get("ID", "?"))
        if not row.get("Validacion_ok", False):
            issues.append(f"{bid} no paso Validacion_ok en auditoria de entrenamiento")
        outside = float(row.get("EV_fuera_ventana_MWh", 0.0) or 0.0)
        if outside > MAX_EV_OUTSIDE_WINDOW_MWH:
            issues.append(f"{bid} tiene EV fuera de ventana operativa: {outside:.9f} MWh")
        if bid == "B01" and "sin_factura" in str(row.get("Fuente_carga_base", "")):
            warnings.append("B01 se mantiene como perfil de inventario sin factura mensual directa.")

    return status


def _check_der_audit(audit_dir: Path, issues: list[str]) -> dict[str, Any]:
    path = audit_dir / "der_sizing_audit.csv"
    status = {"path": _rel(path), "rows": 0}
    if not path.exists():
        issues.append(f"Falta auditoria DER: {_rel(path)}")
        return status

    df = pd.read_csv(path)
    status["rows"] = len(df)
    status["sha256"] = _sha256(path)
    if len(df) != EXPECTED_BUILDINGS:
        issues.append(f"der_sizing_audit.csv tiene {len(df)} filas; esperado {EXPECTED_BUILDINGS}")

    required = [
        "ID",
        "PV_schema_kWp",
        "BESS_schema_kWh",
        "BESS_schema_kW",
        "BESS_corregido_schemaPV_kWh",
        "BESS_corregido_schemaPV_kW",
        "EV_load_fuera_ventana_MWh",
        "EV_schema_count",
        "EV_dimensionador_v3_count",
        "PV_utilizacion_pct",
    ]
    missing = [col for col in required if col not in df.columns]
    if missing:
        issues.append(f"der_sizing_audit.csv no tiene columnas requeridas: {missing}")
        return status

    numeric_cols = [c for c in required if c != "ID"]
    if bool(df[numeric_cols].isna().any().any()):
        issues.append("der_sizing_audit.csv contiene NaN en columnas DER criticas")

    for _, row in df.iterrows():
        bid = str(row["ID"])
        if float(row["BESS_schema_kWh"]) <= 10.0 or float(row["BESS_schema_kW"]) <= 5.0:
            issues.append(f"{bid} conserva BESS preliminar en auditoria DER")
        if abs(float(row["BESS_schema_kWh"]) - float(row["BESS_corregido_schemaPV_kWh"])) > 1.0:
            issues.append(f"{bid} BESS schema no coincide con BESS corregido por auditoria")
        if abs(float(row["BESS_schema_kW"]) - float(row["BESS_corregido_schemaPV_kW"])) > 1.0:
            issues.append(f"{bid} potencia BESS schema no coincide con auditoria")
        if float(row["EV_load_fuera_ventana_MWh"]) > MAX_EV_OUTSIDE_WINDOW_MWH:
            issues.append(f"{bid} EV fuera de ventana en auditoria DER")
        if int(row["EV_schema_count"]) != int(row["EV_dimensionador_v3_count"]):
            issues.append(f"{bid} EV schema_count no coincide con dimensionador v3")
        if not (99.9 <= float(row["PV_utilizacion_pct"]) <= 100.1):
            issues.append(f"{bid} PV_utilizacion_pct no cierra alrededor de 100%")

    return status


def _check_auxiliary_audit_files(dataset_dir: Path, audit_dir: Path, issues: list[str]) -> dict[str, Any]:
    files = [
        dataset_dir / "solar_fix_log.json",
        dataset_dir / "ev_charger_sizing_log.json",
        dataset_dir / "controlled_machines_log.json",
        dataset_dir / "building_metadata.json",
        ROOT / "tools" / "dataset_docs" / "distillation_report.csv",
        audit_dir / "ev_charger_sizing_audit.csv",
        audit_dir / "ev_charger_sizing_audit.json",
        audit_dir / "training_dataset_validation.csv",
        audit_dir / "der_sizing_audit.json",
        audit_dir / "orphaned_dataset_files_manifest.json",
        audit_dir / "csv_integrity_manifest.json",
    ]
    status: dict[str, Any] = {}
    for path in files:
        entry = {"exists": path.exists()}
        if path.exists():
            entry["sha256"] = _sha256(path)
            if path.name == "csv_integrity_manifest.json":
                try:
                    integrity = json.loads(path.read_text(encoding="utf-8"))
                    entry["status"] = integrity.get("status")
                    entry["nan_cells"] = integrity.get("nan_cells")
                    entry["inf_cells"] = integrity.get("inf_cells")
                    if integrity.get("status") != "ok":
                        issues.append("csv_integrity_manifest.json no esta en status=ok")
                except Exception as exc:
                    issues.append(f"No se pudo leer csv_integrity_manifest.json: {exc}")
        else:
            issues.append(f"Falta archivo de auditoria/sincronizacion: {_rel(path)}")
        status[_rel(path)] = entry
    return status


def _check_citylearn_load(schema_path: Path, issues: list[str]) -> dict[str, Any]:
    status: dict[str, Any] = {"schema": _rel(schema_path), "scenarios": {}}
    sys.path.insert(0, str(ROOT / "CityLearn"))
    sys.path.insert(0, str(ROOT))

    try:
        from citylearn.citylearn import CityLearnEnv  # type: ignore
    except Exception as exc:
        issues.append(f"No se pudo importar CityLearnEnv: {exc}")
        status["import_error"] = str(exc)
        return status

    # Load the environment once — all 17 building CSVs, charger CSVs, and support
    # files are shared across scenarios. apply_scenario_modifications() only modifies
    # electricity_pricing in memory, so a single CityLearnEnv instance can be reused
    # for all three scenario checks without re-reading any data from disk.
    try:
        env = CityLearnEnv(schema=str(schema_path))
    except Exception as exc:
        issues.append(f"CityLearnEnv no pudo instanciarse desde schema: {exc}")
        status["load_error"] = str(exc)
        return status

    try:
        from citylearn.scenario_manager import ScenarioManager  # type: ignore
        manager = ScenarioManager()
        scenario_manager_ok = True
    except Exception:
        manager = None
        scenario_manager_ok = False

    for scenario in ["E1", "E2", "E3"]:
        try:
            if scenario_manager_ok and manager is not None:
                manager.select_scenario(scenario)
                manager.apply_scenario_modifications(env)

            obs, _ = env.reset()
            obs_lens = [len(o) for o in obs]
            ok = len(obs) == EXPECTED_BUILDINGS and min(obs_lens) > 0
            if not ok:
                issues.append(f"CityLearnEnv {scenario} no cargo 17 agentes con observaciones validas")
            status["scenarios"][scenario] = {
                "ok": ok,
                "agents": len(obs),
                "obs_min": min(obs_lens) if obs_lens else 0,
                "obs_max": max(obs_lens) if obs_lens else 0,
            }
        except Exception as exc:
            issues.append(f"CityLearnEnv fallo en {scenario}: {exc}")
            status["scenarios"][scenario] = {"ok": False, "error": str(exc)}

    return status


def build_manifest(
    dataset_dir: Path,
    buildingcsv_dir: Path,
    audit_dir: Path,
    *,
    citylearn_load: bool,
) -> dict[str, Any]:
    issues: list[str] = []
    warnings: list[str] = []
    schema_path = dataset_dir / "schema.json"
    schema = _load_json(schema_path, issues)

    checks = {
        "raw_inputs": _check_raw_inputs(buildingcsv_dir, issues, warnings),
        "support_files": _check_support_files(dataset_dir, issues),
        "citylearn_files": _check_citylearn_files(dataset_dir, schema, issues) if schema else {},
        "training_audit": _check_training_audit(audit_dir, issues, warnings),
        "der_audit": _check_der_audit(audit_dir, issues),
        "auxiliary_audit_files": _check_auxiliary_audit_files(dataset_dir, audit_dir, issues),
    }
    if citylearn_load:
        checks["citylearn_load"] = _check_citylearn_load(schema_path, issues)

    ok = not issues
    manifest = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_dir": _rel(dataset_dir),
        "buildingcsv_dir": _rel(buildingcsv_dir),
        "audit_dir": _rel(audit_dir),
        "schema_sha256": _sha256(schema_path) if schema_path.exists() else None,
        "status": "ready" if ok else "blocked",
        "raw_dataset_loaded_before_normalization": ok,
        "normalization_allowed_for_training": ok,
        "checks": checks,
        "issues": issues,
        "warnings": warnings,
    }
    return _jsonable(manifest)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Validate raw CityLearn Iquitos dataset before MADRL training normalization."
    )
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--buildingcsv-dir", type=Path, default=DEFAULT_BUILDINGCSV_DIR)
    parser.add_argument("--audit-dir", type=Path, default=DEFAULT_AUDIT_DIR)
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_MANIFEST)
    parser.add_argument("--skip-citylearn-load", action="store_true")
    args = parser.parse_args()

    manifest = build_manifest(
        args.dataset_dir.resolve(),
        args.buildingcsv_dir.resolve(),
        args.audit_dir.resolve(),
        citylearn_load=not args.skip_citylearn_load,
    )
    args.manifest_out.parent.mkdir(parents=True, exist_ok=True)
    args.manifest_out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Manifest: {args.manifest_out}")
    print(f"Estado dataset entrenamiento: {manifest['status'].upper()}")
    print(f"Normalizacion permitida: {manifest['normalization_allowed_for_training']}")
    if manifest["issues"]:
        print("Problemas:")
        for item in manifest["issues"]:
            print(f"  - {item}")
    if manifest["warnings"]:
        print("Advertencias:")
        for item in manifest["warnings"]:
            print(f"  - {item}")
    return 0 if manifest["status"] == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
