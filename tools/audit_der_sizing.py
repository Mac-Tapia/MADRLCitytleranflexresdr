"""
Audit AC, PV, BESS and EV sizing for the Iquitos CityLearn dataset.

This script is intentionally non-destructive for the dataset: it reads current
CSV/schema inputs, computes corrected values, and writes audit artifacts under
docs/ and outputs/dataset_audit/.
"""

from __future__ import annotations

import json
import logging
import sys
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pvlib

sys.path.insert(0, str(Path(__file__).resolve().parent))

from buildingcsv_inputs import load_building_inventory  # noqa: E402
import dimension_ev_chargers as ev_sizing  # noqa: E402
import size_bess_optimal as bess_sizing  # noqa: E402


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
DOC_PATH = ROOT / "docs" / "INFORME_AUDITORIA_DIMENSIONAMIENTO_DER_IQUITOS.md"
OUT_DIR = ROOT / "outputs" / "dataset_audit"
CSV_PATH = OUT_DIR / "der_sizing_audit.csv"
JSON_PATH = OUT_DIR / "der_sizing_audit.json"

PV_FACTORS = {
    "actual_0_63": 0.63,
    "agresivo_0_85": 0.85,
    "techo_max_1_00": 1.00,
}
PV_POWER_DENSITY_KWP_M2 = 0.24
PV_PARKING_FACTOR = 0.0

BESS_DOD = 0.80
BESS_ETA_C = 0.95
BESS_ETA_D = 0.95
BESS_COP_ACS = 0.85
BESS_T_TARGET = 8.5
BESS_PERC_EXCURSION = 90
BESS_PERC_POWER = 99


def _sort_key(key: str) -> int:
    return int(key.split("_")[1])


def _select_sandia_module() -> tuple[str, dict]:
    modules = pvlib.pvsystem.retrieve_sam("SandiaMod")
    modules = modules.T if modules.shape[0] < modules.shape[1] else modules
    for col in ("Vmpo", "Impo", "Area", "Bvoco"):
        modules[col] = pd.to_numeric(modules[col], errors="coerce")
    modules["Pmp_stc"] = modules["Vmpo"] * modules["Impo"]
    modules["eta_stc"] = modules["Pmp_stc"] / (modules["Area"] * 1000)
    modules["abs_Bvoco"] = modules["Bvoco"].abs()
    candidates = modules[
        ~modules.index.str.contains("CPV", case=False, na=False)
        & (modules["eta_stc"] >= 0.15)
        & (modules["Area"].between(1.5, 2.6))
        & (modules["Pmp_stc"] >= 250)
    ].sort_values(["eta_stc", "abs_Bvoco"], ascending=[False, True])
    key = candidates.index[0]
    return str(key), modules.loc[key].to_dict()


def _pv_kwp(area_m2: float, module: dict, area_factor: float) -> float:
    n_modules = max(1, int(area_m2 * area_factor // float(module["Area"])))
    return n_modules * float(module["Vmpo"]) * float(module["Impo"]) / 1000.0


def _pv_kwp_power_density(area_m2: float, parking_m2: float = 0.0, parking_factor: float = 0.0) -> float:
    return (area_m2 + parking_m2 * parking_factor) * PV_POWER_DENSITY_KWP_M2


def _bess_for_profile(
    df: pd.DataFrame,
    pv_kwp: float,
    t_out: np.ndarray,
    bdata: dict,
    building_id: int,
) -> dict[str, Any]:
    result = bess_sizing.size_profile(df, pv_kwp, t_out, bdata, building_id=building_id)
    return {
        "e_bess_kwh": result["E_bess"],
        "p_bess_kw": result["P_nom"],
        "solar_avg_kw": result["solar_avg"],
        "load_avg_kw": result["load_avg"],
        "pv_load_pct": result["pv_load_pct"],
        "load_total_kwh": result["load_total_kwh"],
        "base_building_load_total_kwh": result["base_building_load_total_kwh"],
        "load_without_ev_total_kwh": result["load_without_ev_total_kwh"],
        "controlled_machine_load_total_kwh": result["controlled_machine_load_total_kwh"],
        "controlled_machine_load_peak_kw": result["controlled_machine_load_peak_kw"],
        "controlled_machine_load_avg_kw": result["controlled_machine_load_avg_kw"],
        "controlled_machine_count": result["controlled_machine_count"],
        "controlled_machine_active_window_rows": result["controlled_machine_active_window_rows"],
        "controlled_machine_potential_cycles": result["controlled_machine_potential_cycles"],
        "ev_load_total_kwh": result["ev_load_total_kwh"],
        "ev_load_operating_kwh": result["ev_load_operating_kwh"],
        "ev_load_outside_operating_kwh": result["ev_load_outside_operating_kwh"],
        "ev_load_peak_kw": result["ev_load_peak_kw"],
        "ev_load_avg_kw": result["ev_load_avg_kw"],
        "ev_state1_hours": result["ev_state1_hours"],
        "solar_total_kwh": result["solar_total_kwh"],
        "direct_pv_to_load_kwh": result["direct_pv_to_load_kwh"],
        "direct_pv_to_ev_kwh": result["direct_pv_to_ev_kwh"],
        "direct_pv_to_building_kwh": result["direct_pv_to_building_kwh"],
        "pv_surplus_before_kwh": result["pv_surplus_before_kwh"],
        "grid_before_kwh": result["grid_before_kwh"],
        "ev_grid_before_kwh": result["ev_grid_before_kwh"],
        "building_grid_before_kwh": result["building_grid_before_kwh"],
        "grid_after_kwh": result["grid_after_kwh"],
        "ev_grid_after_kwh": result["ev_grid_after_kwh"],
        "building_grid_after_kwh": result["building_grid_after_kwh"],
        "grid_reduction_pct": result["grid_reduction_pct"],
        "pv_export_after_kwh": result["pv_export_after_kwh"],
        "bess_charge_from_pv_kwh": result["bess_charge_from_pv_kwh"],
        "bess_charge_from_grid_kwh": result["bess_charge_from_grid_kwh"],
        "bess_discharge_to_ev_kwh": result["bess_discharge_to_ev_kwh"],
        "bess_discharge_to_building_kwh": result["bess_discharge_to_building_kwh"],
        "bess_discharge_to_load_kwh": result["bess_discharge_to_load_kwh"],
        "solar_utilization_pct": result["solar_utilization_pct"],
        "e_balance_kwh": result["E_balance"],
        "p_balance_kw": result["P_balance"],
        "e_peak_shaving_kwh": result["E_peak_shaving"],
        "p_peak_shaving_kw": result["P_peak_shaving"],
        "sizing_driver": result["sizing_driver"],
        "peak_before_kw": result["peak_before_kw"],
        "peak_operating_before_kw": result["peak_operating_before_kw"],
        "peak_target_kw": result["peak_target_kw"],
        "peak_after_estimated_kw": result["peak_after_estimated_kw"],
        "peak_operating_after_estimated_kw": result["peak_operating_after_estimated_kw"],
        "peak_reduction_pct": result["peak_reduction_pct"],
        "peak_operating_reduction_pct": result["peak_operating_reduction_pct"],
        "peak_shaving_delivered_kwh": result["peak_shaving_delivered_kwh"],
        "solar_shift_target_delivered_ev_kwh": result["solar_shift_target_delivered_ev_kwh"],
        "solar_shift_target_delivered_building_kwh": result["solar_shift_target_delivered_building_kwh"],
        "operating_window": result["operating_window"],
        "valley_charge_hours": result["valley_charge_hours"],
        "valley_charge_unserved_kwh": result["valley_charge_unserved_kwh"],
    }


def build_audit() -> tuple[pd.DataFrame, dict]:
    schema = json.loads((DATASET_DIR / "schema.json").read_text(encoding="utf-8"))
    inventory = load_building_inventory()
    module_key, module = _select_sandia_module()
    weather = pd.read_csv(DATASET_DIR / "weather.csv")
    t_out = weather["outdoor_dry_bulb_temperature"].to_numpy(dtype=float)

    ev_sizing.log.setLevel(logging.WARNING)
    ev_config = ev_sizing.build_charger_config()

    rows = []
    for bkey, bdata in sorted(schema["buildings"].items(), key=lambda item: _sort_key(item[0])):
        bid = _sort_key(bkey)
        meta = inventory[bid]
        df = pd.read_csv(DATASET_DIR / f"{bkey}.csv")
        pv_schema = float(bdata["pv"]["attributes"]["nominal_power"])
        bess_schema = bdata["electrical_storage"]["attributes"]
        chargers = bdata.get("chargers", {})
        ev_current_kw = sum(float(c["attributes"]["nominal_power"]) for c in chargers.values())
        ev_v3_list = ev_config[bid]
        ev_v3_kw = sum(float(ev_sizing.EV_SPEC[e]["charger_kw"]) for e in ev_v3_list)

        pv_values = {name: _pv_kwp(meta.area_techada_m2, module, factor) for name, factor in PV_FACTORS.items()}
        pv_tecnico = _pv_kwp_power_density(
            meta.area_techada_m2,
            meta.area_estacionamiento_m2,
            PV_PARKING_FACTOR,
        )
        bess_current = _bess_for_profile(df, pv_schema, t_out, bdata, bid)
        bess_roof_max = _bess_for_profile(df, pv_values["techo_max_1_00"], t_out, bdata, bid)
        bess_pv_tecnico = _bess_for_profile(df, pv_tecnico, t_out, bdata, bid)

        rows.append({
            "ID": f"B{bid:02d}",
            "Edificio": meta.name,
            "Tipo": meta.tipo_uso_citylearn,
            "Area_m2": round(float(meta.area_techada_m2), 2),
            "AC_pico_cooling_demand_kWth": round(float(df["cooling_demand"].max()), 3),
            "AC_media_cooling_demand_kWth": round(float(df["cooling_demand"].mean()), 3),
            "PV_schema_kWp": round(pv_schema, 1),
            "PV_calc_0_63_kWp": round(pv_values["actual_0_63"], 1),
            "PV_agresivo_0_85_kWp": round(pv_values["agresivo_0_85"], 1),
            "PV_techo_max_1_00_kWp": round(pv_values["techo_max_1_00"], 1),
            "PV_tecnico_0_24_kWp": round(pv_tecnico, 1),
            "BESS_schema_kWh": round(float(bess_schema["capacity"]), 1),
            "BESS_schema_kW": round(float(bess_schema["nominal_power"]), 1),
            "BESS_corregido_schemaPV_kWh": round(bess_current["e_bess_kwh"], 1),
            "BESS_corregido_schemaPV_kW": round(bess_current["p_bess_kw"], 1),
            "BESS_corregido_PVmax_kWh": round(bess_roof_max["e_bess_kwh"], 1),
            "BESS_corregido_PVmax_kW": round(bess_roof_max["p_bess_kw"], 1),
            "BESS_corregido_PVtecnico_kWh": round(bess_pv_tecnico["e_bess_kwh"], 1),
            "BESS_corregido_PVtecnico_kW": round(bess_pv_tecnico["p_bess_kw"], 1),
            "BESS_balance_kWh": round(bess_current["e_balance_kwh"], 1),
            "BESS_balance_kW": round(bess_current["p_balance_kw"], 1),
            "BESS_peak_shaving_kWh": round(bess_current["e_peak_shaving_kwh"], 1),
            "BESS_peak_shaving_kW": round(bess_current["p_peak_shaving_kw"], 1),
            "BESS_driver": bess_current["sizing_driver"],
            "Carga_total_MWh": round(bess_current["load_total_kwh"] / 1000.0, 3),
            "Carga_base_medida_MWh": round(bess_current["base_building_load_total_kwh"] / 1000.0, 3),
            "Maquina_controlada_MWh": round(bess_current["controlled_machine_load_total_kwh"] / 1000.0, 3),
            "Maquina_controlada_pico_kW": round(bess_current["controlled_machine_load_peak_kw"], 3),
            "Maquina_controlada_count": int(bess_current["controlled_machine_count"]),
            "Maquina_controlada_ciclos": int(bess_current["controlled_machine_potential_cycles"]),
            "Carga_sin_EV_MWh": round(bess_current["load_without_ev_total_kwh"] / 1000.0, 3),
            "EV_load_total_MWh": round(bess_current["ev_load_total_kwh"] / 1000.0, 3),
            "EV_load_en_ventana_MWh": round(bess_current["ev_load_operating_kwh"] / 1000.0, 3),
            "EV_load_fuera_ventana_MWh": round(bess_current["ev_load_outside_operating_kwh"] / 1000.0, 3),
            "EV_load_peak_kW": round(bess_current["ev_load_peak_kw"], 3),
            "EV_state1_hours": int(bess_current["ev_state1_hours"]),
            "PV_total_MWh": round(bess_current["solar_total_kwh"] / 1000.0, 3),
            "PV_directa_a_carga_MWh": round(bess_current["direct_pv_to_load_kwh"] / 1000.0, 3),
            "PV_directa_a_EV_MWh": round(bess_current["direct_pv_to_ev_kwh"] / 1000.0, 3),
            "PV_directa_a_edificio_MWh": round(bess_current["direct_pv_to_building_kwh"] / 1000.0, 3),
            "PV_exportada_MWh": round(bess_current["pv_export_after_kwh"] / 1000.0, 3),
            "PV_excedente_antes_BESS_MWh": round(bess_current["pv_surplus_before_kwh"] / 1000.0, 3),
            "Red_publica_antes_BESS_MWh": round(bess_current["grid_before_kwh"] / 1000.0, 3),
            "Red_EV_antes_BESS_MWh": round(bess_current["ev_grid_before_kwh"] / 1000.0, 3),
            "Red_edificio_antes_BESS_MWh": round(bess_current["building_grid_before_kwh"] / 1000.0, 3),
            "Red_publica_despues_BESS_MWh": round(bess_current["grid_after_kwh"] / 1000.0, 3),
            "Red_EV_despues_BESS_MWh": round(bess_current["ev_grid_after_kwh"] / 1000.0, 3),
            "Red_edificio_despues_BESS_MWh": round(bess_current["building_grid_after_kwh"] / 1000.0, 3),
            "Red_publica_reduccion_pct": round(bess_current["grid_reduction_pct"], 3),
            "Pico_red_antes_kW": round(bess_current["peak_before_kw"], 3),
            "Pico_operativo_antes_kW": round(bess_current["peak_operating_before_kw"], 3),
            "Pico_red_objetivo_kW": round(bess_current["peak_target_kw"], 3),
            "Pico_red_estimado_despues_kW": round(bess_current["peak_after_estimated_kw"], 3),
            "Pico_operativo_estimado_despues_kW": round(bess_current["peak_operating_after_estimated_kw"], 3),
            "Pico_red_reduccion_pct": round(bess_current["peak_reduction_pct"], 3),
            "Pico_operativo_reduccion_pct": round(bess_current["peak_operating_reduction_pct"], 3),
            "Energia_corte_pico_MWh": round(bess_current["peak_shaving_delivered_kwh"] / 1000.0, 3),
            "BESS_carga_desde_PV_MWh": round(bess_current["bess_charge_from_pv_kwh"] / 1000.0, 3),
            "BESS_carga_desde_red_valle_MWh": round(bess_current["bess_charge_from_grid_kwh"] / 1000.0, 3),
            "BESS_descarga_a_EV_MWh": round(bess_current["bess_discharge_to_ev_kwh"] / 1000.0, 3),
            "BESS_descarga_a_edificio_MWh": round(bess_current["bess_discharge_to_building_kwh"] / 1000.0, 3),
            "BESS_descarga_a_carga_MWh": round(bess_current["bess_discharge_to_load_kwh"] / 1000.0, 3),
            "BESS_objetivo_EV_MWh": round(bess_current["solar_shift_target_delivered_ev_kwh"] / 1000.0, 3),
            "BESS_objetivo_edificio_MWh": round(bess_current["solar_shift_target_delivered_building_kwh"] / 1000.0, 3),
            "BESS_recarga_valle_no_servida_MWh": round(bess_current["valley_charge_unserved_kwh"] / 1000.0, 3),
            "Ventana_operativa_BESS": bess_current["operating_window"],
            "Ventana_EV_recarga": bess_current["operating_window"],
            "Horas_recarga_valle": bess_current["valley_charge_hours"],
            "PV_utilizacion_pct": round(bess_current["solar_utilization_pct"], 3),
            "EV_schema_count": len(chargers),
            "EV_schema_kW": round(ev_current_kw, 1),
            "EV_dimensionador_v3_count": len(ev_v3_list),
            "EV_dimensionador_v3_kW": round(ev_v3_kw, 1),
        })

    metadata = {
        "dataset_dir": str(DATASET_DIR),
        "module_key": module_key,
        "module_area_m2": float(module["Area"]),
        "module_kwp": float(module["Vmpo"] * module["Impo"] / 1000.0),
        "module_efficiency": float(module["Vmpo"] * module["Impo"] / (module["Area"] * 1000.0)),
        "pv_factors": PV_FACTORS,
        "pv_power_density_kwp_m2": PV_POWER_DENSITY_KWP_M2,
        "pv_parking_factor": PV_PARKING_FACTOR,
        "bess_method": {
            "solar_scaling": "solar_generation_W_per_kW * pv_nominal_kWp / 1000",
            "base_building_load": "non_shiftable_load + cooling_demand/COP + dhw_demand/COP_DHW",
            "controlled_machine_load": "one expected shiftable cycle per active Washing_Machine_X.csv window and building type",
            "load_without_ev": "base_building_load + controlled_machine_load",
            "ev_load": "sum(max_charging_power for charger_state == 1)",
            "pv_priority": "PV directo se asigna primero a EV, luego a carga del edificio y finalmente a excedente/exportacion",
            "load": "load_without_ev + ev_load, separado en balance EV/edificio para auditoria",
            "public_grid_before_bess": "ev_deficit + building_deficit despues de PV directo con prioridad EV",
            "pv_export": "max(pv - ev_load - load_without_ev, 0)",
            "solar_shift": "desplazamiento diario de excedente FV factible hacia deficit EV en ventana operativa; despues hacia deficit del edificio",
            "target_shift_ratio": bess_sizing.TARGET_SHIFT_RATIO,
            "e_raw": "max(percentil diario de excursion SOC por desplazamiento FV, energia diaria de corte de pico)",
            "p_nom": "max(potencia FV->BESS, potencia BESS->EV/edificio, potencia de corte de pico, potencia de recarga valle)",
            "min_peak_shaving_pct": bess_sizing.MIN_PEAK_SHAVING_PCT,
            "peak_shaving_target": "piso minimo: max(public_grid_before_bess en todo el horizonte) * (1 - min_peak_shaving_pct)",
            "final_capacity": "max(BESS desplazamiento solar diario, BESS corte de pico)",
            "final_power": "max(P desplazamiento solar, P descarga pico, P recarga valle)",
            "window_use": "la ventana operativa por edificio define que deficit EV es prioritario para descarga BESS hasta el cierre",
            "valley_charge_hours": bess_sizing.VALLEY_CHARGE_HOURS,
            "dod": bess_sizing.DOD,
            "eta_c": bess_sizing.ETA_C,
            "eta_d": bess_sizing.ETA_D,
        },
    }
    return pd.DataFrame(rows), metadata


def _fmt(num: float, digits: int = 1) -> str:
    return f"{num:,.{digits}f}"


def write_report(df: pd.DataFrame, metadata: dict) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    df.to_csv(CSV_PATH, index=False)
    JSON_PATH.write_text(
        json.dumps({"metadata": metadata, "rows": df.to_dict(orient="records")}, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )
    total_ev = int(df["EV_schema_count"].sum()) if "EV_schema_count" in df else 0

    lines = [
        "# Informe de auditoria de dimensionamiento DER - Iquitos CityLearn",
        "",
        "Este informe se genera con `tools/audit_der_sizing.py` y no modifica el dataset.",
        "",
        "## Hallazgos",
        "",
        "- PV aplicado al dataset de entrenamiento usa el area de techo suministrada por edificio en `CityLearn/data/buildingcsv/building.csv` (`Area_Techada_m2`) y densidad tecnica `0.24 kWp/m2`; no usa areas inventadas.",
        "- La curva horaria `solar_generation` se calcula con `pvlib` para Iquitos y se normaliza como W/kW; `schema.json` escala esa curva con `pv.nominal_power` de cada edificio.",
        "- Los factores `0.63`, `0.85` y `1.00` se conservan solo como escenarios de sensibilidad/auditoria, no como criterio aplicado al dataset vigente.",
        "- `size_bess_optimal.py` usa balance horario por edificio: carga electrica base, carga EV, PV, PV directo a EV, PV directo al edificio, excedente PV y deficit residual de red publica.",
        "- La red publica no se reemplaza artificialmente: `grid_before_bess = EV_deficit + edificio_deficit` y `grid_after_bess` queda como deficit residual despues de la descarga factible del BESS.",
        f"- El excedente solar dimensiona el BESS: se desplaza hasta `{bess_sizing.TARGET_SHIFT_RATIO:.0%}` de la energia diaria factible PV->deficit, priorizando primero EV en la ventana operativa del edificio y luego carga del edificio.",
        f"- El BESS conserva un piso de corte de pico minimo de `{bess_sizing.MIN_PEAK_SHAVING_PCT:.0%}` sobre la importacion maxima de red en todo el horizonte horario del dataset.",
        "- La ventana operativa por edificio define que energia EV entra como prioridad BESS hasta el cierre; la EV fuera de ventana queda separada en la auditoria.",
        "- La capacidad final es el maximo entre desplazamiento solar diario con prioridad EV y corte de pico; la potencia final es el maximo entre carga FV, descarga a EV/edificio, descarga de pico y recarga valle/nocturna.",
        f"- El dimensionador EV v3 aporta `{total_ev}` tomas controlables en el schema actual; la energia EV se suma solo cuando `electric_vehicle_charger_state == 1` en cada `charger_*.csv`.",
        "- AC se reporta como pico real de `cooling_demand` del CSV en kW termicos, porque `cooling_device` esta en `autosize=True`.",
        "",
        "## Parametros PV",
        "",
        f"- Modulo Sandia: `{metadata['module_key']}`",
        f"- Potencia modulo: `{metadata['module_kwp']:.4f}` kWp",
        f"- Area modulo: `{metadata['module_area_m2']:.4f}` m2",
        f"- Eficiencia STC: `{metadata['module_efficiency']:.2%}`",
        f"- Criterio aplicado al dataset: `Area_Techada_m2 * {metadata['pv_power_density_kwp_m2']:.2f} kWp/m2`",
        "- Fuente de area: `CityLearn/data/buildingcsv/building.csv`, columna `Area_Techada_m2`",
        "- Escenario conservador de sensibilidad: `0.63 = 70% techo util * 90% packing`",
        "- Escenario agresivo de sensibilidad: `0.85`",
        "- Escenario techo maximo teorico de sensibilidad: `1.00`",
        "",
        "## Balance BESS auditado",
        "",
        "- `Carga total` = energia electrica real estimada del edificio antes de BESS, incluyendo EV.",
        "- `Carga base medida` = demanda electrica base + climatizacion electrica + ACS electrico.",
        "- `Maquina controlada` = carga flexible por edificio cargada mediante `Washing_Machine_X.csv` y expuesta como accion CityLearn.",
        "- `Carga sin EV` = carga base medida + maquina controlada.",
        "- `EV MWh` = carga horaria de tomas modo 3 cuando el CSV del cargador indica `state=1`.",
        "- `EV ventana` = parte de EV dentro del horario operativo del edificio; esta energia es prioridad de descarga BESS.",
        "- `PV a EV` = solar directo asignado primero a EV antes de cubrir carga del edificio.",
        "- `BESS a EV` = descarga BESS dedicada a EV dentro de la ventana operativa.",
        "- `PV exportada` = excedente solar remanente despues del desplazamiento BESS factible.",
        "- `Red antes` = energia que compraria el edificio a la red despues del autoconsumo PV directo y antes del BESS.",
        "- `Red despues` = energia residual de red despues de descarga BESS y recarga valle desde red.",
        "- `Pico obj.` = 90% del pico global de importacion de red antes del BESS; se mantiene como piso de potencia/capacidad.",
        "- `PV uso` = autoconsumo directo + carga BESS desde PV + exportacion; debe cerrar en 100% salvo redondeo.",
        "",
        "## Tabla auditada",
        "",
        "| ID | Edificio | Area m2 | PV kWp | BESS kWh | BESS kW | Ventana EV/recarga | EV tomas | EV MWh | EV ventana MWh | PV a EV MWh | BESS a EV MWh | Pico global -% |",
        "|---|---|---:|---:|---:|---:|---|---:|---:|---:|---:|---:|---:|",
    ]
    for row in df.to_dict(orient="records"):
        lines.append(
            "| {ID} | {Edificio} | {Area} | {PV} | {BESS} | {BESSP} | {Window} | {EV} | {EVLoad} | {EVWindow} | {PVToEV} | {BESSToEV} | {PeakReduction} |".format(
                ID=row["ID"],
                Edificio=row["Edificio"],
                Area=_fmt(row["Area_m2"], 2),
                PV=_fmt(row["PV_schema_kWp"], 1),
                PeakReduction=_fmt(row["Pico_red_reduccion_pct"], 1),
                BESS=_fmt(row["BESS_schema_kWh"], 1),
                BESSP=_fmt(row["BESS_schema_kW"], 1),
                Window=row["Ventana_EV_recarga"],
                EV=row["EV_schema_count"],
                EVLoad=_fmt(row["EV_load_total_MWh"], 1),
                EVWindow=_fmt(row["EV_load_en_ventana_MWh"], 1),
                PVToEV=_fmt(row["PV_directa_a_EV_MWh"], 1),
                BESSToEV=_fmt(row["BESS_descarga_a_EV_MWh"], 1),
            )
        )

    lines.extend([
        "",
        "## Balance energetico por edificio",
        "",
        "| ID | Base medida MWh | Maquina ctrl MWh | Carga sin EV MWh | EV MWh | EV ventana MWh | PV MWh | PV a EV MWh | PV a edificio MWh | PV a BESS MWh | BESS a EV MWh | BESS a edificio MWh | PV exportada MWh | Red EV despues MWh | Red edificio despues MWh | BESS solar kWh |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])
    for row in df.to_dict(orient="records"):
        lines.append(
            "| {ID} | {BaseLoad} | {MachineLoad} | {LoadNoEV} | {EVLoad} | {EVWindow} | {PVTotal} | {PVToEV} | {PVToBuilding} | {PVToBESS} | {BESSToEV} | {BESSToBuilding} | {PVExport} | {EVGridAfter} | {BuildingGridAfter} | {ESolar} |".format(
                ID=row["ID"],
                BaseLoad=_fmt(row["Carga_base_medida_MWh"], 1),
                MachineLoad=_fmt(row["Maquina_controlada_MWh"], 1),
                LoadNoEV=_fmt(row["Carga_sin_EV_MWh"], 1),
                EVLoad=_fmt(row["EV_load_total_MWh"], 1),
                EVWindow=_fmt(row["EV_load_en_ventana_MWh"], 1),
                PVTotal=_fmt(row["PV_total_MWh"], 1),
                PVToEV=_fmt(row["PV_directa_a_EV_MWh"], 1),
                PVToBuilding=_fmt(row["PV_directa_a_edificio_MWh"], 1),
                PVToBESS=_fmt(row["BESS_carga_desde_PV_MWh"], 1),
                BESSToEV=_fmt(row["BESS_descarga_a_EV_MWh"], 1),
                BESSToBuilding=_fmt(row["BESS_descarga_a_edificio_MWh"], 1),
                PVExport=_fmt(row["PV_exportada_MWh"], 1),
                EVGridAfter=_fmt(row["Red_EV_despues_BESS_MWh"], 1),
                BuildingGridAfter=_fmt(row["Red_edificio_despues_BESS_MWh"], 1),
                ESolar=_fmt(row["BESS_balance_kWh"], 1),
            )
        )

    lines.extend([
        "",
        "## Archivos generados",
        "",
        f"- CSV: `{CSV_PATH.relative_to(ROOT)}`",
        f"- JSON: `{JSON_PATH.relative_to(ROOT)}`",
        "",
        "## Reproduccion tecnica",
        "",
        "Este auditor no sobrescribe `schema.json` ni los CSV, pero documenta el estado aplicado. Para reproducir el dimensionamiento vigente del dataset:",
        "",
        "```powershell",
        "# PV aplicado al entrenamiento: Iquitos TMY via PVGIS/pvlib + area techada suministrada * 0.24 kWp/m2",
        ".\\.venv39-citylearn-v3\\Scripts\\python.exe tools\\fix_solar_pvlib.py --weather-source tmy --capacity-method power-density --power-density-kwp-m2 0.24 --parking-factor 0.0 --dry-run",
        "",
        "# Aplicar PV al dataset si se necesita regenerar los CSV solares",
        ".\\.venv39-citylearn-v3\\Scripts\\python.exe tools\\fix_solar_pvlib.py --weather-source tmy --capacity-method power-density --power-density-kwp-m2 0.24 --parking-factor 0.0",
        "",
        "# EV v3 aplica cargadores y escribe schema/charger CSV",
        ".\\.venv39-citylearn-v3\\Scripts\\python.exe tools\\dimension_ev_chargers.py",
        "",
        "# BESS con PV->EV y BESS->EV prioritario por ventana operativa, solo verificar",
        ".\\.venv39-citylearn-v3\\Scripts\\python.exe tools\\size_bess_optimal.py --dry-run",
        "",
        "# Aplicar BESS corregido al schema.json despues de EV",
        ".\\.venv39-citylearn-v3\\Scripts\\python.exe tools\\size_bess_optimal.py --write",
        "```",
    ])

    DOC_PATH.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    df, metadata = build_audit()
    write_report(df, metadata)
    print(f"Informe: {DOC_PATH}")
    print(f"CSV: {CSV_PATH}")
    print(f"JSON: {JSON_PATH}")


if __name__ == "__main__":
    main()
