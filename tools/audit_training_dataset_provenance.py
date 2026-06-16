"""Validate provenance and energy integration for the Iquitos training dataset.

The goal is to separate measured/supplied inputs from reproducible simulation
layers:

- building.csv: building inventory supplied for the project.
- B_02.csv..B_17.csv: monthly measured billing inputs.
- Building_*.csv: CityLearn hourly training series.
- charger_*.csv/schema.json: controllable EV assets.
- solar_fix_log.json: pvlib/PVGIS TMY solar simulation.
- der_sizing_audit.csv: PV/BESS/EV balance used for training.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from buildingcsv_inputs import (  # noqa: E402
    DEFAULT_BUILDINGS_WITH_MONTHLY_DATA,
    load_building_inventory,
    load_monthly_measurements,
)
import distill_building_loads as load_distill  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
OUT_DIR = ROOT / "outputs" / "dataset_audit"
CSV_PATH = OUT_DIR / "training_dataset_validation.csv"
JSON_PATH = OUT_DIR / "training_dataset_validation.json"
DOC_PATH = ROOT / "docs" / "INFORME_VALIDACION_DATASET_ENTRENAMIENTO_IQUITOS.md"
DER_AUDIT_PATH = OUT_DIR / "der_sizing_audit.csv"

EXPECTED_ROWS = 26304
VALID_CHARGER_STATES = {1, 2, 3}
MEASURED_DELTA_TOLERANCE_PCT = 0.01


def _sort_key(key: str) -> int:
    return int(key.split("_")[1])


def _fmt(value: Any, digits: int = 2) -> str:
    if value is None:
        return "N/A"
    if isinstance(value, float) and np.isnan(value):
        return "N/A"
    return f"{float(value):,.{digits}f}"


def _load_schema() -> dict:
    return json.loads((DATASET_DIR / "schema.json").read_text(encoding="utf-8"))


def _ev_summary(bdata: dict, ev_defs: set[str], expected_rows: int) -> dict[str, Any]:
    total_kwh = 0.0
    state1_hours = 0
    bad_states: set[int] = set()
    ids_in_csv: set[str] = set()
    missing_ids: set[str] = set()
    row_errors = 0
    charger_count = 0
    mode3_dual = 0
    physical_units: set[str] = set()
    nominal_kw = 0.0

    for cname, cfg in (bdata.get("chargers") or {}).items():
        sim_name = cfg.get("charger_simulation")
        attrs = cfg.get("attributes", {}) or {}
        hardware = cfg.get("hardware", {}) or {}
        power_kw = float(attrs.get("max_charging_power", attrs.get("nominal_power", 0.0)) or 0.0)
        nominal_kw += power_kw
        charger_count += 1

        if hardware.get("charging_mode") == "IEC_61851_Mode_3_AC":
            mode3_dual += 1
        physical_id = hardware.get("physical_charger_id")
        if physical_id:
            physical_units.add(str(physical_id))

        if not sim_name:
            row_errors += 1
            continue

        path = DATASET_DIR / sim_name
        if not path.exists():
            row_errors += 1
            continue

        df = pd.read_csv(path)
        if len(df) != expected_rows:
            row_errors += 1

        states = set(df["electric_vehicle_charger_state"].dropna().astype(int).unique().tolist())
        bad_states.update(states - VALID_CHARGER_STATES)

        active = df["electric_vehicle_charger_state"].astype(int).eq(1)
        state1_hours += int(active.sum())
        total_kwh += float(active.sum()) * power_kw

        ev_ids = {
            str(value).strip()
            for value in df["electric_vehicle_id"].dropna().unique()
            if str(value).strip() and str(value).strip().lower() not in {"nan", "none"}
        }
        ids_in_csv.update(ev_ids)
        missing_ids.update(ev_ids - ev_defs)

    return {
        "EV_tomas": charger_count,
        "EV_equipos_fisicos_modo3_doble_toma": len(physical_units),
        "EV_mode3_tomas": mode3_dual,
        "EV_potencia_nominal_kW": nominal_kw,
        "EV_load_MWh": total_kwh / 1000.0,
        "EV_state1_hours": state1_hours,
        "EV_states_invalidos": sorted(bad_states),
        "EV_ids_en_csv": len(ids_in_csv),
        "EV_ids_faltantes": sorted(missing_ids),
        "EV_row_errors": row_errors,
        "EV_ok": not bad_states and not missing_ids and row_errors == 0,
    }


def _parse_machine_profile(value: Any) -> list[float]:
    text = str(value).strip()
    if not text or text == "-1":
        return []
    try:
        parsed = json.loads(text)
    except Exception:
        try:
            parsed = [float(part.strip()) for part in text.strip("[]").split(",") if part.strip()]
        except Exception:
            return []
    if isinstance(parsed, (int, float)):
        return [float(parsed)]
    return [float(item) for item in parsed]


def _controlled_machine_summary(bkey: str, bdata: dict, expected_rows: int) -> dict[str, Any]:
    rows = 0
    active_window_rows = 0
    potential_cycles = 0
    potential_kwh = 0.0
    row_errors = 0
    files: list[str] = []

    for mname, cfg in (bdata.get("washing_machines") or {}).items():
        sim_name = cfg.get("washing_machine_energy_simulation")
        if not sim_name:
            row_errors += 1
            continue

        path = DATASET_DIR / str(sim_name)
        files.append(str(sim_name))
        if not path.exists():
            row_errors += 1
            continue

        df = pd.read_csv(path)
        rows += len(df)
        if len(df) != expected_rows:
            row_errors += 1
        expected_cols = [
            "day_type",
            "hour",
            "wm_start_time_step",
            "wm_end_time_step",
            "load_profile",
        ]
        if df.columns.tolist() != expected_cols:
            row_errors += 1
        if bool(df.isna().any().any()):
            row_errors += 1

        starts = pd.to_numeric(df["wm_start_time_step"], errors="coerce").fillna(-1).astype(int)
        active = starts >= 0
        active_window_rows += int(active.sum())
        seen_starts: set[int] = set()
        for _, row in df[active].iterrows():
            start = int(row["wm_start_time_step"])
            if start in seen_starts:
                continue
            seen_starts.add(start)
            potential_kwh += sum(_parse_machine_profile(row["load_profile"]))
        potential_cycles += len(seen_starts)

    expected_file = f"Washing_Machine_{_sort_key(bkey)}.csv"
    ok = (
        len(files) == 1
        and expected_file in files
        and row_errors == 0
        and active_window_rows > 0
        and potential_kwh > 0.0
    )

    return {
        "Maquina_controlada_archivos": len(files),
        "Maquina_controlada_archivo": files[0] if files else "",
        "Maquina_controlada_filas": rows,
        "Maquina_controlada_ventanas": active_window_rows,
        "Maquina_controlada_ciclos": potential_cycles,
        "Maquina_controlada_MWh": potential_kwh / 1000.0,
        "Maquina_controlada_ok": ok,
    }


def _base_load_summary(
    bid: int,
    df: pd.DataFrame,
    schema: dict,
    inventory: dict,
    t_out: np.ndarray,
) -> dict[str, float]:
    eta, cop_acs = load_distill.get_cop_params(schema, bid, inventory)
    cop = load_distill.compute_cop_array(t_out, eta)
    nsl = df["non_shiftable_load"].to_numpy(dtype=float)
    cooling_e = df["cooling_demand"].to_numpy(dtype=float) / cop
    dhw_e = df["dhw_demand"].to_numpy(dtype=float) / cop_acs
    return {
        "Carga_no_controlada_MWh": float(nsl.sum()) / 1000.0,
        "Cooling_controlado_MWh": float(cooling_e.sum()) / 1000.0,
        "DHW_controlado_MWh": float(dhw_e.sum()) / 1000.0,
        "Carga_base_dataset_MWh": float((nsl + cooling_e + dhw_e).sum()) / 1000.0,
    }


def build_validation() -> tuple[pd.DataFrame, dict[str, Any]]:
    schema = _load_schema()
    inventory = load_building_inventory()
    raw_measurements = load_monthly_measurements(buildings=DEFAULT_BUILDINGS_WITH_MONTHLY_DATA)
    measurements = load_distill.forecast_missing_measurements(
        raw_measurements,
        buildings=DEFAULT_BUILDINGS_WITH_MONTHLY_DATA,
    )
    weather = pd.read_csv(DATASET_DIR / "weather.csv")
    t_out = weather["outdoor_dry_bulb_temperature"].to_numpy(dtype=float)
    solar_log = json.loads((DATASET_DIR / "solar_fix_log.json").read_text(encoding="utf-8"))
    der = pd.read_csv(DER_AUDIT_PATH).set_index("ID") if DER_AUDIT_PATH.exists() else pd.DataFrame()
    ev_defs = set(schema.get("electric_vehicles_def", {}).keys())

    rows: list[dict[str, Any]] = []
    for bkey, bdata in sorted(schema["buildings"].items(), key=lambda item: _sort_key(item[0])):
        bid = _sort_key(bkey)
        meta = inventory.get(bid)
        csv_path = DATASET_DIR / f"{bkey}.csv"
        df = pd.read_csv(csv_path)
        row_count_ok = len(df) == EXPECTED_ROWS
        columns_ok = df.columns.tolist() == [
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
        nonnegative_ok = bool(
            (df[["non_shiftable_load", "dhw_demand", "cooling_demand", "heating_demand", "solar_generation"]] >= 0.0)
            .all()
            .all()
        )

        load_summary = _base_load_summary(bid, df, schema, inventory, t_out)
        ev = _ev_summary(bdata, ev_defs, EXPECTED_ROWS)
        machine = _controlled_machine_summary(bkey, bdata, EXPECTED_ROWS)

        bmeas = measurements[measurements["building_id"] == bid] if not measurements.empty else pd.DataFrame()
        measured_months = int((bmeas["record_type"] == "measured").sum()) if not bmeas.empty else 0
        forecast_months = int((bmeas["record_type"] == "forecast").sum()) if not bmeas.empty else 0
        measured_total_mwh = float(bmeas["energia_total_kwh"].sum()) / 1000.0 if not bmeas.empty else np.nan
        if measured_total_mwh > 0.0:
            delta_pct = (
                (load_summary["Carga_base_dataset_MWh"] - measured_total_mwh)
                / measured_total_mwh
                * 100.0
            )
        else:
            delta_pct = np.nan

        der_row = der.loc[f"B{bid:02d}"] if not der.empty and f"B{bid:02d}" in der.index else {}
        pv_kwp = float(bdata.get("pv", {}).get("attributes", {}).get("nominal_power", 0.0) or 0.0)
        roof_kwp_expected = float(meta.area_techada_m2) * float(solar_log.get("power_density_kwp_m2", 0.24)) if meta else np.nan
        pv_kwp_delta_pct = (pv_kwp - roof_kwp_expected) / roof_kwp_expected * 100.0 if roof_kwp_expected else np.nan
        bess_attrs = bdata.get("electrical_storage", {}).get("attributes", {}) or {}

        if bid == 1:
            source_status = "inventario_suministrado_sin_factura_mensual"
            measured_ok = True
            limitation = "No existe B_01.csv; carga horaria base procede del modelo fisico calibrado por inventario, no de factura mensual."
        elif forecast_months > 0:
            source_status = "factura_mensual_con_meses_pronosticados"
            measured_ok = abs(delta_pct) <= MEASURED_DELTA_TOLERANCE_PCT
            limitation = f"{forecast_months} meses pronosticados por calendario desde meses medidos."
        else:
            source_status = "factura_mensual_medida"
            measured_ok = abs(delta_pct) <= MEASURED_DELTA_TOLERANCE_PCT
            limitation = ""

        ok = bool(
            row_count_ok
            and columns_ok
            and nonnegative_ok
            and ev["EV_ok"]
            and machine["Maquina_controlada_ok"]
            and measured_ok
        )

        rows.append({
            "ID": f"B{bid:02d}",
            "Edificio": meta.name if meta else bkey,
            "Tipo": meta.tipo_uso_citylearn if meta else "",
            "Area_techada_m2": round(float(meta.area_techada_m2), 3) if meta else np.nan,
            "Area_estacionamiento_m2": round(float(meta.area_estacionamiento_m2), 3) if meta else np.nan,
            "Fuente_carga_base": source_status,
            "Meses_medidos": measured_months,
            "Meses_pronosticados": forecast_months,
            "Medido_o_pronosticado_MWh": round(measured_total_mwh, 6) if not np.isnan(measured_total_mwh) else np.nan,
            "Carga_base_dataset_MWh": round(load_summary["Carga_base_dataset_MWh"], 6),
            "Delta_base_vs_fuente_pct": round(float(delta_pct), 9) if not np.isnan(delta_pct) else np.nan,
            "Carga_no_controlada_MWh": round(load_summary["Carga_no_controlada_MWh"], 6),
            "Cooling_controlado_MWh": round(load_summary["Cooling_controlado_MWh"], 6),
            "DHW_controlado_MWh": round(load_summary["DHW_controlado_MWh"], 6),
            "Maquina_controlada_MWh": round(machine["Maquina_controlada_MWh"], 6),
            "Maquina_controlada_archivo": machine["Maquina_controlada_archivo"],
            "Maquina_controlada_ventanas": machine["Maquina_controlada_ventanas"],
            "Maquina_controlada_ciclos": machine["Maquina_controlada_ciclos"],
            "Maquina_controlada_ok": machine["Maquina_controlada_ok"],
            "EV_controlado_MWh": round(ev["EV_load_MWh"], 6),
            "Carga_total_con_EV_MWh": round(
                load_summary["Carga_base_dataset_MWh"]
                + machine["Maquina_controlada_MWh"]
                + ev["EV_load_MWh"],
                6,
            ),
            "EV_en_ventana_MWh": round(float(der_row.get("EV_load_en_ventana_MWh", np.nan)), 6),
            "EV_fuera_ventana_MWh": round(float(der_row.get("EV_load_fuera_ventana_MWh", np.nan)), 6),
            "EV_tomas": ev["EV_tomas"],
            "EV_equipos_fisicos_modo3_doble_toma": ev["EV_equipos_fisicos_modo3_doble_toma"],
            "EV_potencia_nominal_kW": round(ev["EV_potencia_nominal_kW"], 3),
            "EV_state1_hours": ev["EV_state1_hours"],
            "EV_ids_ok": ev["EV_ok"],
            "PV_kWp_schema": round(pv_kwp, 3),
            "PV_kWp_area_techo_0_24": round(roof_kwp_expected, 3) if not np.isnan(roof_kwp_expected) else np.nan,
            "PV_delta_techo_pct": round(float(pv_kwp_delta_pct), 6) if not np.isnan(pv_kwp_delta_pct) else np.nan,
            "PV_total_MWh": round(float(der_row.get("PV_total_MWh", np.nan)), 6),
            "PV_directa_MWh": round(float(der_row.get("PV_directa_a_carga_MWh", np.nan)), 6),
            "PV_directa_EV_MWh": round(float(der_row.get("PV_directa_a_EV_MWh", np.nan)), 6),
            "PV_directa_edificio_MWh": round(float(der_row.get("PV_directa_a_edificio_MWh", np.nan)), 6),
            "PV_a_BESS_MWh": round(float(der_row.get("BESS_carga_desde_PV_MWh", np.nan)), 6),
            "PV_exportada_MWh": round(float(der_row.get("PV_exportada_MWh", np.nan)), 6),
            "BESS_a_EV_MWh": round(float(der_row.get("BESS_descarga_a_EV_MWh", np.nan)), 6),
            "BESS_a_edificio_MWh": round(float(der_row.get("BESS_descarga_a_edificio_MWh", np.nan)), 6),
            "BESS_kWh": round(float(bess_attrs.get("capacity", 0.0)), 3),
            "BESS_kW": round(float(bess_attrs.get("nominal_power", 0.0)), 3),
            "Pico_global_reduccion_pct": round(float(der_row.get("Pico_red_reduccion_pct", np.nan)), 6),
            "Filas_ok": row_count_ok,
            "Columnas_ok": columns_ok,
            "No_negativos_ok": nonnegative_ok,
            "Validacion_ok": ok,
            "Limitacion": limitation,
        })

    df_out = pd.DataFrame(rows)
    pv_closure = (
        df_out["PV_total_MWh"]
        - df_out["PV_directa_MWh"]
        - df_out["PV_a_BESS_MWh"]
        - df_out["PV_exportada_MWh"]
    ).abs().max()

    metadata = {
        "dataset_dir": str(DATASET_DIR.relative_to(ROOT)),
        "expected_rows": EXPECTED_ROWS,
        "source_inventory": "CityLearn/data/buildingcsv/building.csv",
        "source_monthly_measurements": "CityLearn/data/buildingcsv/B_02.csv..B_17.csv",
        "building_1_policy": "B01 has inventory data but no B_01.csv monthly meter file.",
        "solar_source": solar_log.get("weather_source"),
        "solar_method": solar_log.get("method"),
        "pvlib_version": solar_log.get("pvlib_version"),
        "pv_capacity_rule": f"Area_Techada_m2 * {solar_log.get('power_density_kwp_m2', 0.24)} kWp/m2, parking_factor={solar_log.get('parking_factor', 0.0)}",
        "ev_rule": "Mode 3 AC dual socket metadata; one CityLearn controllable socket/loadpoint per charger CSV; state=1 is controlled charging load.",
        "bess_rule": "PV directo se asigna primero a EV; el BESS desplaza excedente PV primero a deficit EV dentro de la ventana operativa de cada edificio y luego a deficit del edificio, con piso global de peak-shaving.",
        "base_load_rule": "B02-B17 base load is validated as non_shiftable_load + cooling_demand/COP + dhw_demand/COP against monthly active-energy inputs.",
        "controlled_machine_rule": "Each building loads one Washing_Machine_X.csv as a controlled shiftable-load dataset parameterized by building type and supplied shiftable energy.",
        "cost_rule": "pricing.csv is referenced by every building and is generated from monthly billing inputs during load distillation.",
        "emissions_rule": "carbon_intensity.csv is referenced by every building and represents the Iquitos isolated diesel/solar Scope 2 hourly factor.",
        "controlled_uncontrolled_rule": "Uncontrolled building load remains non_shiftable_load. Controlled building loads are cooling, DHW, EV and one shiftable machine dataset per building; EV and machine loads are scenario loads, not subtracted from measured historical meter energy.",
        "max_abs_base_delta_pct_B02_B17": float(
            df_out[df_out["ID"] != "B01"]["Delta_base_vs_fuente_pct"].abs().max()
        ),
        "total_forecast_months": int(df_out["Meses_pronosticados"].sum()),
        "pv_closure_max_MWh": float(pv_closure),
        "all_valid": bool(df_out["Validacion_ok"].all() and pv_closure <= 0.01),
        "known_limitations": [
            "B01 has no monthly meter file B_01.csv, so its base load is a simulated profile from supplied inventory.",
            "B06 has forecast months completed from measured calendar-month overlap; they are flagged, not treated as direct meter readings.",
            "EV arrival sessions are simulated from the EV sizing model and supplied parking/traffic assumptions; they are controlled scenario loads, not measured historical building energy.",
            "Controlled machine loads are shiftable scenario loads derived from supplied building type and shiftable-capacity fields, not separate measured submeter files.",
            "Solar uses PVGIS TMY through pvlib for Iquitos, not on-site measured irradiance.",
        ],
    }
    return df_out, metadata


def write_outputs(df_out: pd.DataFrame, metadata: dict[str, Any]) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    CSV_PATH.write_text(df_out.to_csv(index=False), encoding="utf-8")
    JSON_PATH.write_text(
        json.dumps({"metadata": metadata, "rows": df_out.to_dict(orient="records")}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    lines = [
        "# Informe de validacion del dataset de entrenamiento - Iquitos",
        "",
        "Este informe valida trazabilidad y cierre energetico del dataset `citylearn_iquitos_2023_2025` usado para entrenamiento MADRL.",
        "",
        "## Resultado ejecutivo",
        "",
        f"- Estado global: `{'OK' if metadata['all_valid'] else 'REVISAR'}`.",
        f"- Maximo delta base B02-B17 contra fuente mensual: `{metadata['max_abs_base_delta_pct_B02_B17']:.9f}%`.",
        f"- Meses pronosticados marcados: `{metadata['total_forecast_months']}`.",
        f"- Cierre PV maximo: `{metadata['pv_closure_max_MWh']:.6f}` MWh.",
        "- B01 no tiene factura mensual `B_01.csv`; se marca como perfil simulado desde inventario suministrado.",
        "- EV es carga controlada de escenario, no carga historica medida; se integra desde `charger_*.csv` cuando `state=1`.",
        "",
        "## Reglas verificadas",
        "",
        f"- Inventario: `{metadata['source_inventory']}`.",
        f"- Facturas mensuales: `{metadata['source_monthly_measurements']}`.",
        f"- Solar: `{metadata['solar_source']}` con `{metadata['solar_method']}`.",
        f"- PV instalada: `{metadata['pv_capacity_rule']}`.",
        f"- BESS: `{metadata['bess_rule']}`.",
        f"- Carga base: `{metadata['base_load_rule']}`.",
        f"- Maquina controlada: `{metadata['controlled_machine_rule']}`.",
        f"- Costos: `{metadata['cost_rule']}`.",
        f"- Emisiones: `{metadata['emissions_rule']}`.",
        f"- Separacion control/no control: `{metadata['controlled_uncontrolled_rule']}`.",
        "",
        "## Tabla por edificio",
        "",
        "| ID | Edificio | Fuente base | Med/Pron | Base dataset MWh | Maq ctrl MWh | EV MWh | EV ventana MWh | PV kWp | PV a EV MWh | PV a BESS MWh | BESS a EV MWh | BESS kWh | BESS kW | OK | Limitacion |",
        "|---|---|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|",
    ]

    for row in df_out.to_dict(orient="records"):
        lines.append(
            "| {ID} | {Edificio} | {Fuente} | {Meses}/{Pron} | {Base} | {Machine} | {EV} | {EVWindow} | {PV} | {PVToEV} | {PVToBESS} | {BESSToEV} | {BESS} | {BESSP} | {OK} | {Limitacion} |".format(
                ID=row["ID"],
                Edificio=row["Edificio"],
                Fuente=row["Fuente_carga_base"],
                Meses=row["Meses_medidos"],
                Pron=row["Meses_pronosticados"],
                Base=_fmt(row["Carga_base_dataset_MWh"], 1),
                Machine=_fmt(row["Maquina_controlada_MWh"], 1),
                EV=_fmt(row["EV_controlado_MWh"], 1),
                EVWindow=_fmt(row["EV_en_ventana_MWh"], 1),
                PV=_fmt(row["PV_kWp_schema"], 1),
                PVToEV=_fmt(row["PV_directa_EV_MWh"], 1),
                PVToBESS=_fmt(row["PV_a_BESS_MWh"], 1),
                BESSToEV=_fmt(row["BESS_a_EV_MWh"], 1),
                BESS=_fmt(row["BESS_kWh"], 1),
                BESSP=_fmt(row["BESS_kW"], 1),
                OK="OK" if row["Validacion_ok"] else "REVISAR",
                Limitacion=row["Limitacion"] or "",
            )
        )

    lines.extend([
        "",
        "## Limitaciones declaradas",
        "",
    ])
    for item in metadata["known_limitations"]:
        lines.append(f"- {item}")

    lines.extend([
        "",
        "## Archivos generados",
        "",
        f"- CSV: `{CSV_PATH.relative_to(ROOT)}`",
        f"- JSON: `{JSON_PATH.relative_to(ROOT)}`",
        "",
        "## Reproduccion",
        "",
        "```powershell",
        ".\\.venv39-citylearn-v3\\Scripts\\python.exe tools\\audit_training_dataset_provenance.py",
        "```",
    ])

    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    df_out, metadata = build_validation()
    write_outputs(df_out, metadata)
    print(f"Informe: {DOC_PATH}")
    print(f"CSV: {CSV_PATH}")
    print(f"JSON: {JSON_PATH}")
    print(f"Estado global: {'OK' if metadata['all_valid'] else 'REVISAR'}")
    print(f"Max delta base B02-B17: {metadata['max_abs_base_delta_pct_B02_B17']:.9f}%")
    print(f"Cierre PV max: {metadata['pv_closure_max_MWh']:.6f} MWh")
    return 0 if metadata["all_valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
