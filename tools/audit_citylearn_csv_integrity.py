"""Audit active CityLearn dataset CSV files for clean training inputs.

The audit is schema-driven: only files referenced by schema.json plus the
required shared support files are checked. CityLearn-defined sentinels are
accepted where they have explicit semantics:

- EV: -1 for absent time values, -0.1 for absent SOC values.
- Washing machine: -1 for inactive start/end time steps.
"""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import math
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
DEFAULT_OUT = ROOT / "outputs" / "dataset_audit" / "csv_integrity_manifest.json"
EXPECTED_ROWS = 26304

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
CHARGER_COLUMNS = [
    "electric_vehicle_charger_state",
    "electric_vehicle_id",
    "electric_vehicle_departure_time",
    "electric_vehicle_required_soc_departure",
    "electric_vehicle_estimated_arrival_time",
    "electric_vehicle_estimated_soc_arrival",
]
WASHING_MACHINE_COLUMNS = [
    "day_type",
    "hour",
    "wm_start_time_step",
    "wm_end_time_step",
    "load_profile",
]
PRICING_COLUMNS = [
    "electricity_pricing",
    "electricity_pricing_predicted_1",
    "electricity_pricing_predicted_2",
    "electricity_pricing_predicted_3",
]
WEATHER_COLUMNS = 16
VALID_CHARGER_STATES = {1, 2, 3}


def _project_path(path: Path | str) -> Path:
    p = Path(path)
    return (ROOT / p).resolve() if not p.is_absolute() else p.resolve()


def _rel(path: Path | str) -> str:
    p = _project_path(path)
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _read_csv(path: Path, issues: list[str]) -> pd.DataFrame | None:
    try:
        return pd.read_csv(path)
    except Exception as exc:
        issues.append(f"{_rel(path)} no se pudo leer como CSV: {exc}")
        return None


def _base_checks(path: Path, df: pd.DataFrame, expected_columns: list[str] | int | None, issues: list[str]) -> dict[str, Any]:
    numeric = df.select_dtypes(include=[np.number])
    nan_cells = int(df.isna().sum().sum())
    inf_cells = int(np.isinf(numeric.to_numpy()).sum()) if not numeric.empty else 0
    empty_columns = [col for col in df.columns if int(df[col].notna().sum()) == 0]

    entry: dict[str, Any] = {
        "path": _rel(path),
        "sha256": _sha256(path),
        "rows": int(len(df)),
        "columns": int(len(df.columns)),
        "nan_cells": nan_cells,
        "inf_cells": inf_cells,
        "empty_columns": empty_columns,
        "status": "ok",
    }

    if len(df) != EXPECTED_ROWS:
        issues.append(f"{_rel(path)} tiene {len(df)} filas; esperado {EXPECTED_ROWS}")
    if isinstance(expected_columns, list) and df.columns.tolist() != expected_columns:
        issues.append(f"{_rel(path)} no tiene columnas esperadas: {df.columns.tolist()}")
    elif isinstance(expected_columns, int) and len(df.columns) != expected_columns:
        issues.append(f"{_rel(path)} tiene {len(df.columns)} columnas; esperado {expected_columns}")
    if nan_cells:
        issues.append(f"{_rel(path)} contiene {nan_cells} celdas NaN/vacias")
    if inf_cells:
        issues.append(f"{_rel(path)} contiene {inf_cells} celdas infinitas")
    if empty_columns:
        issues.append(f"{_rel(path)} contiene columnas completamente vacias: {empty_columns}")

    return entry


def _parse_profile(value: Any) -> list[float]:
    if value is None or (isinstance(value, float) and math.isnan(value)):
        return []
    text = str(value).strip()
    if not text or text in {"-1", "[]"}:
        return []
    parsed = ast.literal_eval(text)
    if isinstance(parsed, (int, float)):
        parsed = [float(parsed)]
    return [float(x) for x in parsed]


def _check_building(path: Path, issues: list[str]) -> dict[str, Any]:
    df = _read_csv(path, issues)
    if df is None:
        return {"path": _rel(path), "status": "failed_read"}

    entry = _base_checks(path, df, BUILDING_COLUMNS, issues)
    energy_cols = ["non_shiftable_load", "dhw_demand", "cooling_demand", "heating_demand", "solar_generation"]
    if all(col in df.columns for col in energy_cols):
        minimums = {col: float(pd.to_numeric(df[col], errors="coerce").min()) for col in energy_cols}
        entry["energy_min"] = minimums
        negative = [col for col, value in minimums.items() if value < 0.0]
        if negative:
            issues.append(f"{_rel(path)} tiene energia negativa en {negative}")
    return entry


def _check_charger(path: Path, issues: list[str]) -> dict[str, Any]:
    df = _read_csv(path, issues)
    if df is None:
        return {"path": _rel(path), "status": "failed_read"}

    entry = _base_checks(path, df, CHARGER_COLUMNS, issues)
    if "electric_vehicle_charger_state" in df.columns:
        states = set(pd.to_numeric(df["electric_vehicle_charger_state"], errors="coerce").dropna().astype(int).tolist())
        invalid = sorted(states - VALID_CHARGER_STATES)
        entry["states"] = sorted(states)
        if invalid:
            issues.append(f"{_rel(path)} contiene estados EV invalidos: {invalid}")

    checks = {
        "electric_vehicle_departure_time": (-1.0, 24.0),
        "electric_vehicle_estimated_arrival_time": (-1.0, 24.0),
        "electric_vehicle_required_soc_departure": (-0.1, 100.0),
        "electric_vehicle_estimated_soc_arrival": (-0.1, 100.0),
    }
    for col, (low, high) in checks.items():
        if col not in df.columns:
            continue
        values = pd.to_numeric(df[col], errors="coerce")
        if bool(values.isna().any()):
            issues.append(f"{_rel(path)} tiene valores no numericos en {col}")
            continue
        if float(values.min()) < low or float(values.max()) > high:
            issues.append(f"{_rel(path)} tiene {col} fuera de rango [{low}, {high}]")
    if "electric_vehicle_id" in df.columns:
        ids = df["electric_vehicle_id"].astype(str).str.strip()
        if bool((ids == "").any()):
            issues.append(f"{_rel(path)} tiene electric_vehicle_id vacio")
    entry["allowed_sentinels"] = {
        "time_absent": -1,
        "soc_absent": -0.1,
        "ev_id_absent": "NONE",
    }
    return entry


def _check_washing_machine(path: Path, issues: list[str]) -> dict[str, Any]:
    df = _read_csv(path, issues)
    if df is None:
        return {"path": _rel(path), "status": "failed_read"}

    entry = _base_checks(path, df, WASHING_MACHINE_COLUMNS, issues)
    if all(col in df.columns for col in ["wm_start_time_step", "wm_end_time_step", "load_profile"]):
        starts = pd.to_numeric(df["wm_start_time_step"], errors="coerce")
        ends = pd.to_numeric(df["wm_end_time_step"], errors="coerce")
        if bool(starts.isna().any()) or bool(ends.isna().any()):
            issues.append(f"{_rel(path)} tiene start/end no numericos")
        if float(starts.min()) < -1.0 or float(ends.min()) < -1.0:
            issues.append(f"{_rel(path)} usa centinelas menores que -1")

        active = (starts >= 0) & (ends >= 0)
        profile_errors = 0
        negative_profile_values = 0
        active_cycles = set()
        for idx, value in df["load_profile"].items():
            try:
                profile = _parse_profile(value)
            except Exception:
                profile_errors += 1
                continue
            if any(v < 0.0 for v in profile):
                negative_profile_values += 1
            if bool(active.iloc[idx]) and profile:
                active_cycles.add(int(starts.iloc[idx]))
        entry["active_window_rows"] = int(active.sum())
        entry["active_cycle_count"] = int(len(active_cycles))
        entry["profile_parse_errors"] = int(profile_errors)
        entry["negative_profile_rows"] = int(negative_profile_values)
        entry["allowed_sentinels"] = {"inactive_start_end": -1, "inactive_load_profile": "[]"}
        if profile_errors:
            issues.append(f"{_rel(path)} tiene {profile_errors} load_profile no parseables")
        if negative_profile_values:
            issues.append(f"{_rel(path)} tiene perfiles de maquina con valores negativos")
        if int(len(active_cycles)) <= 0:
            issues.append(f"{_rel(path)} no tiene ciclos activos de maquina controlada")
    return entry


def _check_support(path: Path, expected_columns: list[str] | int, issues: list[str]) -> dict[str, Any]:
    df = _read_csv(path, issues)
    if df is None:
        return {"path": _rel(path), "status": "failed_read"}

    entry = _base_checks(path, df, expected_columns, issues)
    numeric = df.select_dtypes(include=[np.number])
    if not numeric.empty:
        minimum = float(numeric.min().min())
        maximum = float(numeric.max().max())
        entry["numeric_min"] = minimum
        entry["numeric_max"] = maximum
        if minimum < 0.0 and path.name in {"pricing.csv", "carbon_intensity.csv"}:
            issues.append(f"{_rel(path)} tiene valores negativos")
    return entry


def _schema_buildings(schema: dict[str, Any]) -> dict[str, Any]:
    return schema.get("buildings") or {
        key: value for key, value in schema.items() if str(key).startswith("Building_")
    }


def audit(dataset_dir: Path) -> dict[str, Any]:
    dataset_dir = _project_path(dataset_dir)
    issues: list[str] = []
    schema_path = dataset_dir / "schema.json"
    if not schema_path.exists():
        return {
            "generated_at": _utc_now(),
            "dataset_dir": _rel(dataset_dir),
            "status": "failed",
            "issues": [f"Falta schema.json: {_rel(schema_path)}"],
        }

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    buildings = _schema_buildings(schema)
    files: dict[str, Any] = {}

    for name, expected in {
        "weather.csv": WEATHER_COLUMNS,
        "carbon_intensity.csv": ["carbon_intensity"],
        "pricing.csv": PRICING_COLUMNS,
    }.items():
        path = dataset_dir / name
        if not path.exists():
            issues.append(f"Falta archivo de soporte: {_rel(path)}")
            files[name] = {"path": _rel(path), "status": "missing"}
        else:
            files[name] = _check_support(path, expected, issues)

    referenced_chargers: set[str] = set()
    referenced_machines: set[str] = set()
    for bkey, bdata in sorted(buildings.items()):
        csv_name = str(bdata.get("energy_simulation") or f"{bkey}.csv")
        bpath = dataset_dir / csv_name
        files[csv_name] = _check_building(bpath, issues) if bpath.exists() else {"path": _rel(bpath), "status": "missing"}
        if not bpath.exists():
            issues.append(f"Falta CSV de edificio: {_rel(bpath)}")

        for cfg in (bdata.get("chargers") or {}).values():
            sim_name = cfg.get("charger_simulation")
            if sim_name:
                referenced_chargers.add(str(sim_name))
        for cfg in (bdata.get("washing_machines") or {}).values():
            sim_name = cfg.get("washing_machine_energy_simulation")
            if sim_name:
                referenced_machines.add(str(sim_name))

    for name in sorted(referenced_chargers):
        path = dataset_dir / name
        files[name] = _check_charger(path, issues) if path.exists() else {"path": _rel(path), "status": "missing"}
        if not path.exists():
            issues.append(f"Falta CSV de cargador referenciado: {_rel(path)}")

    for name in sorted(referenced_machines):
        path = dataset_dir / name
        files[name] = _check_washing_machine(path, issues) if path.exists() else {"path": _rel(path), "status": "missing"}
        if not path.exists():
            issues.append(f"Falta CSV de maquina controlada referenciado: {_rel(path)}")

    active_chargers = {p.name for p in dataset_dir.glob("charger_*.csv")}
    active_machines = {p.name for p in dataset_dir.glob("Washing_Machine_*.csv")}
    stale_schema_backups: set[str] = set()
    for pattern in ("schema*.bak", "schema*.backup", "schema_old*.json", "schema_backup*.json"):
        stale_schema_backups.update(p.name for p in dataset_dir.glob(pattern) if p.name != "schema.json")

    orphan_chargers = sorted(active_chargers - referenced_chargers)
    orphan_machines = sorted(active_machines - referenced_machines)
    missing_chargers = sorted(referenced_chargers - active_chargers)
    missing_machines = sorted(referenced_machines - active_machines)
    if orphan_chargers:
        issues.append(f"Hay charger_*.csv no referenciados: {orphan_chargers[:10]}")
    if orphan_machines:
        issues.append(f"Hay Washing_Machine_*.csv no referenciados: {orphan_machines[:10]}")
    if missing_chargers:
        issues.append(f"schema.json referencia charger_*.csv faltantes: {missing_chargers[:10]}")
    if missing_machines:
        issues.append(f"schema.json referencia Washing_Machine_*.csv faltantes: {missing_machines[:10]}")
    if stale_schema_backups:
        issues.append(f"Hay schemas antiguos/backups en dataset activo: {sorted(stale_schema_backups)}")

    nan_cells = sum(int(entry.get("nan_cells", 0)) for entry in files.values())
    inf_cells = sum(int(entry.get("inf_cells", 0)) for entry in files.values())

    return {
        "generated_at": _utc_now(),
        "dataset_dir": _rel(dataset_dir),
        "status": "ok" if not issues else "failed",
        "expected_rows": EXPECTED_ROWS,
        "csv_files_checked": len(files),
        "nan_cells": int(nan_cells),
        "inf_cells": int(inf_cells),
        "schema_references": {
            "buildings": len(buildings),
            "chargers": len(referenced_chargers),
            "controlled_machines": len(referenced_machines),
            "orphan_chargers": orphan_chargers,
            "orphan_machines": orphan_machines,
            "missing_chargers": missing_chargers,
            "missing_machines": missing_machines,
            "stale_schema_backups": sorted(stale_schema_backups),
        },
        "issues": issues,
        "files": files,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit active CityLearn CSV integrity.")
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--manifest-out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args()

    manifest = audit(args.dataset_dir)
    out = _project_path(args.manifest_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps({
        "status": manifest["status"],
        "dataset_dir": manifest["dataset_dir"],
        "csv_files_checked": manifest["csv_files_checked"],
        "nan_cells": manifest["nan_cells"],
        "inf_cells": manifest["inf_cells"],
        "issues": manifest["issues"][:10],
    }, indent=2, ensure_ascii=False))
    return 0 if manifest["status"] == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
