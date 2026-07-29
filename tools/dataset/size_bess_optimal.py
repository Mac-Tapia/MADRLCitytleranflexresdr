"""
size_bess_optimal.py
====================
Dimensiona BESS por edificio para desplazamiento solar diario y corte de picos.

El dimensionamiento usa la energia real suministrada a cada edificio,
incluyendo carga EV horaria de los cargadores modo 3:

    load = (
        non_shiftable_load
        + cooling_demand/COP
        + dhw_demand/COP_DHW
        + controlled_machine_load
        + ev_charger_load
    )

y el balance fisico solar con prioridad EV por edificio:

    direct_pv_to_ev       = min(ev_load, pv)
    direct_pv_to_building = min(building_load, pv - direct_pv_to_ev)
    pv_export             = max(pv - ev_load - building_load, 0)
    grid_before_bess      = ev_deficit + building_deficit

El excedente solar participa en el dimensionamiento BESS por edificio. Primero
se cubre carga EV con PV directo. Luego, el BESS desplaza excedente FV hacia
deficit EV dentro de la ventana operativa del edificio hasta su cierre. Solo
despues de esa prioridad se asigna descarga BESS a la carga propia del edificio.
El remanente no desplazable se mantiene como exportacion a red.

El BESS conserva ademas un piso de corte de pico sobre la importacion neta de red:

    grid_peak_target = max(grid_before_bess) * (1 - min_peak_shaving_pct)

La capacidad final es el maximo entre:

    1. el requerimiento de desplazamiento de excedente FV factible diario; y
    2. el requerimiento minimo de corte de pico con recarga valle.

Esto evita capacidades simbolicas cuando hay gran generacion solar, pero tampoco
sobredimensiona el BESS para almacenar excedentes que no tienen demanda posterior
local que cubrir.

Correccion critica:
  Building_X.csv guarda solar_generation normalizada en W/kW. CityLearn escala
  esa serie con schema.pv.attributes.nominal_power. Por tanto, para calcular
  BESS se debe usar:

      solar_kWh_h = solar_generation_W_per_kW * pv_nominal_kWp / 1000

Uso recomendado:
  python tools/dataset/size_bess_optimal.py --dry-run
  python tools/dataset/size_bess_optimal.py --write
"""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path
from typing import Any, Optional

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from buildingcsv_inputs import load_building_inventory  # noqa: E402
import distill_building_loads as load_distill  # noqa: E402


ROOT = Path(__file__).resolve().parents[2]
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
SCHEMA_PATH = DATASET_DIR / "schema.json"
WEATHER_PATH = DATASET_DIR / "weather.csv"
_INVENTORY_CACHE = None

# Parametros LFP
DOD = 0.80
ETA_C = 0.95
ETA_D = 0.95
ETA_RT = round(ETA_C * ETA_D, 6)
LOSS = 1e-5
SOC_INI = 0.50
COP_ACS = 0.85
T_TARGET = 8.5
PERC_EXCURSION = 90
PERC_POWER = 99
TARGET_SHIFT_RATIO = 0.70
MIN_PEAK_SHAVING_PCT = 0.10
MIN_CAPACITY_KWH = 10
MIN_POWER_KW = 5
VALLEY_CHARGE_HOURS = (0, 1, 2, 3, 4, 5, 22, 23)
BUILDING_OPERATION_WINDOWS: dict[int, tuple[tuple[int, ...], tuple[int, ...], str]] = {
    1: (tuple(range(7, 19)), tuple(range(1, 6)), "electro_oriente_lun_vie_07_18"),
    2: (tuple(range(8, 16)), tuple(range(1, 6)), "municipalidad_lun_vie_08_15"),
    3: (tuple(range(24)), tuple(range(1, 8)), "aeropuerto_24h"),
    4: (tuple(range(8, 23)), tuple(range(1, 8)), "tottus_lun_dom_08_22"),
    5: (tuple(range(24)), tuple(range(1, 8)), "hotel_24h"),
    6: (tuple(range(10, 23)), tuple(range(1, 8)), "mall_lun_dom_10_22"),
    7: (tuple(range(7, 15)), tuple(range(1, 6)), "unap_lun_vie_07_14"),
    8: (tuple(range(7, 19)), tuple(range(1, 6)), "pnp_ets_academico_lun_vie_07_18"),
    9: (tuple(range(24)), tuple(range(1, 8)), "coer_24h"),
    10: (tuple(range(7, 16)), tuple(range(1, 6)), "gorel_lun_vie_07_15"),
    11: (tuple(range(24)), tuple(range(1, 8)), "hospital_regional_24h"),
    12: (tuple(range(24)), tuple(range(1, 8)), "essalud_24h"),
    13: (tuple(range(7, 15)), tuple(range(1, 6)), "unap_lun_vie_07_14"),
    14: (tuple(range(24)), tuple(range(1, 8)), "apn_operativo_24h"),
    15: (tuple(range(7, 19)), tuple(range(1, 6)), "cni_lun_vie_07_18"),
    16: (tuple(range(7, 18)), tuple(range(1, 6)), "sima_lun_vie_07_17"),
    17: (tuple(range(24)), tuple(range(1, 8)), "acsa_salud_24h"),
}


def _operating_window(building_id: Optional[int]) -> tuple[tuple[int, ...], tuple[int, ...], str]:
    """Return active discharge hours/days for realistic peak shaving."""
    if building_id in BUILDING_OPERATION_WINDOWS:
        return BUILDING_OPERATION_WINDOWS[building_id]
    return tuple(range(7, 19)), tuple(range(1, 6)), "office_weekday_07_18"


def _operating_mask(df: pd.DataFrame, building_id: Optional[int]) -> tuple[np.ndarray, str]:
    hours, days, label = _operating_window(building_id)
    hour = df["hour"].to_numpy(dtype=int)
    day_type = df["day_type"].to_numpy(dtype=int)
    mask = np.isin(hour, hours) & np.isin(day_type, days)
    if not bool(mask.any()):
        mask = np.ones(len(df), dtype=bool)
        label = "fallback_all_hours"
    return mask, label


def _valley_charge_mask(df: pd.DataFrame) -> np.ndarray:
    hour = df["hour"].to_numpy(dtype=int)
    return np.isin(hour, VALLEY_CHARGE_HOURS)


def _building_sort_key(key: str) -> int:
    return int(key.split("_")[1])


def _load_schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


def _load_inventory_once():
    global _INVENTORY_CACHE
    if _INVENTORY_CACHE is None:
        _INVENTORY_CACHE = load_building_inventory()
    return _INVENTORY_CACHE


def _cooling_cop(
    bdata: dict,
    t_out: np.ndarray,
    n: int,
    building_id: Optional[int] = None,
) -> np.ndarray:
    """Return hourly COP using the same convention as load distillation."""
    schema_fragment = {"buildings": {}}
    if building_id is not None:
        schema_fragment["buildings"][f"Building_{building_id}"] = bdata

    try:
        eta_carnot, _ = load_distill.get_cop_params(
            schema_fragment,
            int(building_id) if building_id is not None else -1,
            _load_inventory_once(),
        )
    except Exception:
        attrs = bdata.get("cooling_device", {}).get("attributes", {}) or {}
        eta_carnot = float(attrs.get("efficiency", 2.8 / 14.44))

    return load_distill.compute_cop_array(t_out[:n], float(eta_carnot))


def _ev_charger_load(bdata: dict, n: int) -> tuple[np.ndarray, dict[str, float]]:
    """Return hourly EV charging load from charger simulations in schema."""
    ev_load = np.zeros(n, dtype=float)
    charger_count = 0
    state1_hours = 0
    missing_files: list[str] = []

    for cname, cfg in (bdata.get("chargers") or {}).items():
        attrs = cfg.get("attributes", {}) or {}
        sim_name = cfg.get("charger_simulation")
        power_kw = float(
            attrs.get("max_charging_power", attrs.get("nominal_power", 0.0)) or 0.0
        )

        if not sim_name or power_kw <= 0.0:
            continue

        sim_path = DATASET_DIR / sim_name
        if not sim_path.exists():
            missing_files.append(str(sim_name))
            continue

        cdf = pd.read_csv(sim_path, usecols=["electric_vehicle_charger_state"])
        states = cdf["electric_vehicle_charger_state"].to_numpy(dtype=float)
        if len(states) != n:
            raise ValueError(
                f"{cname}: {sim_name} tiene {len(states)} filas, se esperaban {n}"
            )

        charging = states == 1.0
        ev_load += charging.astype(float) * power_kw
        charger_count += 1
        state1_hours += int(charging.sum())

    if missing_files:
        raise FileNotFoundError(
            "Faltan CSV de cargadores EV referenciados en schema.json: "
            + ", ".join(missing_files[:8])
        )

    return ev_load, {
        "ev_charger_count": float(charger_count),
        "ev_state1_hours": float(state1_hours),
        "ev_load_total_kwh": float(ev_load.sum()),
        "ev_load_peak_kw": float(ev_load.max()) if len(ev_load) else 0.0,
        "ev_load_avg_kw": float(ev_load.mean()) if len(ev_load) else 0.0,
    }


def _parse_load_profile(value: Any) -> list[float]:
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


def _controlled_machine_load(bdata: dict, n: int) -> tuple[np.ndarray, dict[str, float]]:
    """Return one expected controlled machine cycle per available window."""
    load = np.zeros(n, dtype=float)
    machine_count = 0
    active_window_rows = 0
    potential_cycles = 0
    missing_files: list[str] = []

    for mname, cfg in (bdata.get("washing_machines") or {}).items():
        sim_name = cfg.get("washing_machine_energy_simulation")
        if not sim_name:
            continue

        path = DATASET_DIR / sim_name
        if not path.exists():
            missing_files.append(str(sim_name))
            continue

        cdf = pd.read_csv(
            path,
            usecols=["wm_start_time_step", "wm_end_time_step", "load_profile"],
        )
        if len(cdf) != n:
            raise ValueError(
                f"{mname}: {sim_name} tiene {len(cdf)} filas, se esperaban {n}"
            )

        machine_count += 1
        starts = pd.to_numeric(cdf["wm_start_time_step"], errors="coerce").fillna(-1).astype(int)
        active = starts >= 0
        active_window_rows += int(active.sum())
        seen_starts: set[int] = set()
        for idx, row in cdf[active].iterrows():
            start = int(row["wm_start_time_step"])
            if start in seen_starts:
                continue
            seen_starts.add(start)
            profile = _parse_load_profile(row["load_profile"])
            for offset, value in enumerate(profile):
                step = start + offset
                if 0 <= step < n:
                    load[step] += float(value)
        potential_cycles += len(seen_starts)

    if missing_files:
        raise FileNotFoundError(
            "Faltan CSV de maquinas controladas referenciadas en schema.json: "
            + ", ".join(missing_files[:8])
        )

    return load, {
        "controlled_machine_count": float(machine_count),
        "controlled_machine_active_window_rows": float(active_window_rows),
        "controlled_machine_potential_cycles": float(potential_cycles),
        "controlled_machine_load_total_kwh": float(load.sum()),
        "controlled_machine_load_peak_kw": float(load.max()) if len(load) else 0.0,
        "controlled_machine_load_avg_kw": float(load.mean()) if len(load) else 0.0,
    }


def _pv_priority_balance(
    solar: np.ndarray,
    building_load: np.ndarray,
    ev_load: np.ndarray,
) -> dict[str, np.ndarray]:
    """Allocate PV first to EV load, then to the building load."""
    direct_pv_to_ev = np.minimum(solar, ev_load)
    remaining_pv = np.clip(solar - direct_pv_to_ev, 0.0, None)
    direct_pv_to_building = np.minimum(remaining_pv, building_load)
    surplus = np.clip(remaining_pv - direct_pv_to_building, 0.0, None)
    ev_deficit = np.clip(ev_load - direct_pv_to_ev, 0.0, None)
    building_deficit = np.clip(building_load - direct_pv_to_building, 0.0, None)
    return {
        "direct_pv_to_ev": direct_pv_to_ev,
        "direct_pv_to_building": direct_pv_to_building,
        "surplus": surplus,
        "ev_deficit": ev_deficit,
        "building_deficit": building_deficit,
    }


def _build_bess_shift_profiles(
    surplus: np.ndarray,
    priority_ev_deficit: np.ndarray,
    building_deficit: np.ndarray,
    target_shift_ratio: float,
) -> dict[str, np.ndarray]:
    """Return daily PV-to-BESS and prioritized BESS discharge profiles."""
    n_days = len(surplus) // 24
    charge_from_pv = np.zeros(len(surplus), dtype=float)
    discharge_to_ev = np.zeros(len(surplus), dtype=float)
    discharge_to_building = np.zeros(len(surplus), dtype=float)
    excursions = np.zeros(n_days, dtype=float)

    for day in range(n_days):
        start = day * 24
        end = start + 24
        surplus_day = surplus[start:end]
        priority_ev_day = priority_ev_deficit[start:end]
        building_day = building_deficit[start:end]

        surplus_total = float(surplus_day.sum())
        priority_ev_total = float(priority_ev_day.sum())
        building_total = float(building_day.sum())
        deficit_total = priority_ev_total + building_total
        feasible_delivered = min(deficit_total, surplus_total * ETA_C * ETA_D)
        target_delivered = feasible_delivered * target_shift_ratio

        if target_delivered <= 0.0 or surplus_total <= 0.0 or deficit_total <= 0.0:
            continue

        pv_surplus_required = target_delivered / (ETA_C * ETA_D)
        charge_ratio = min(1.0, pv_surplus_required / surplus_total)
        charge_day = surplus_day * charge_ratio
        remaining_target = target_delivered

        priority_ev_delivered = min(priority_ev_total, remaining_target)
        if priority_ev_delivered > 0.0 and priority_ev_total > 0.0:
            discharge_to_ev[start:end] = priority_ev_day * (
                priority_ev_delivered / priority_ev_total
            )
            remaining_target -= priority_ev_delivered

        building_delivered = min(building_total, remaining_target)
        if building_delivered > 0.0 and building_total > 0.0:
            discharge_to_building[start:end] = building_day * (
                building_delivered / building_total
            )

        discharge_day = discharge_to_ev[start:end] + discharge_to_building[start:end]
        charge_from_pv[start:end] = charge_day

        soc_curve = np.cumsum(charge_day * ETA_C - discharge_day / ETA_D)
        excursions[day] = float(soc_curve.max() - soc_curve.min())

    return {
        "charge_from_pv": charge_from_pv,
        "discharge_to_ev": discharge_to_ev,
        "discharge_to_building": discharge_to_building,
        "excursions": excursions,
    }


def _peak_shaving_requirement(
    grid_before: np.ndarray,
    df: pd.DataFrame,
    building_id: Optional[int],
    min_peak_shaving_pct: float,
) -> dict[str, Any]:
    """Return BESS sizing for global peak shaving and valley recharge."""
    operating_mask, operating_label = _operating_mask(df, building_id)
    charge_mask = _valley_charge_mask(df)
    peak_global_before = float(grid_before.max()) if len(grid_before) > 0 else 0.0
    operating_basis = grid_before[operating_mask]
    peak_operating_before = float(operating_basis.max()) if len(operating_basis) > 0 else peak_global_before

    if peak_global_before <= 0.0 or min_peak_shaving_pct <= 0.0:
        grid_after = grid_before.copy()
        return {
            "peak_before_kw": peak_global_before,
            "peak_operating_before_kw": peak_operating_before,
            "peak_target_kw": peak_global_before,
            "peak_after_estimated_kw": peak_global_before,
            "peak_operating_after_estimated_kw": peak_operating_before,
            "peak_reduction_pct": 0.0,
            "peak_operating_reduction_pct": 0.0,
            "peak_shaving_power_kw": 0.0,
            "peak_shaving_nominal_power_kw": float(MIN_POWER_KW),
            "peak_shaving_energy_raw_kwh": 0.0,
            "peak_shaving_capacity_kwh": float(MIN_CAPACITY_KWH),
            "peak_shaving_delivered_kwh": 0.0,
            "grid_charge_to_bess_kwh": 0.0,
            "grid_after_series": grid_after,
            "grid_after_kwh": float(grid_after.sum()),
            "operating_window": operating_label,
            "valley_charge_hours": ",".join(str(h) for h in VALLEY_CHARGE_HOURS),
            "valley_charge_unserved_kwh": 0.0,
        }

    peak_target = peak_global_before * (1.0 - min_peak_shaving_pct)
    discharge_required = np.clip(grid_before - peak_target, 0.0, None)

    n_days = len(grid_before) // 24
    daily_discharge = np.array(
        [discharge_required[day * 24:(day + 1) * 24].sum() for day in range(n_days)],
        dtype=float,
    )

    peak_power = float(discharge_required.max()) if len(discharge_required) > 0 else 0.0
    energy_raw = float(daily_discharge.max() / ETA_D) if len(daily_discharge) > 0 else 0.0
    capacity = max(math.ceil(energy_raw / DOD), MIN_CAPACITY_KWH)

    daily_charge_ac = daily_discharge / (ETA_C * ETA_D)
    daily_charge_power = []
    for day in range(n_days):
        start = day * 24
        end = start + 24
        charge_hours = int(charge_mask[start:end].sum())
        if charge_hours <= 0:
            daily_charge_power.append(0.0)
        else:
            daily_charge_power.append(float(daily_charge_ac[day] / charge_hours))
    p_charge = max(daily_charge_power) if daily_charge_power else 0.0
    p_nom = max(math.ceil(max(peak_power, p_charge)), MIN_POWER_KW)

    grid_after = grid_before - discharge_required
    charge_unserved = 0.0
    for day in range(n_days):
        start = day * 24
        end = start + 24
        remaining = float(daily_charge_ac[day])
        if remaining <= 0.0:
            continue

        candidates = [i for i in range(start, end) if charge_mask[i]]
        # Fill the lowest valley imports first so recharge does not create a new peak.
        candidates.sort(key=lambda i: grid_after[i])
        for i in candidates:
            if remaining <= 1e-9:
                break
            headroom = max(0.0, peak_target - grid_after[i])
            charge = min(float(p_nom), headroom, remaining)
            if charge <= 0.0:
                continue
            grid_after[i] += charge
            remaining -= charge

        if remaining > 1e-9:
            charge_unserved += remaining

    peak_global_after = float(grid_after.max()) if len(grid_after) > 0 else 0.0
    operating_after = grid_after[operating_mask]
    peak_operating_after = float(operating_after.max()) if len(operating_after) > 0 else peak_global_after
    global_reduction = (
        (peak_global_before - peak_global_after) / peak_global_before * 100.0
        if peak_global_before > 0 else 0.0
    )
    operating_reduction = (
        (peak_operating_before - peak_operating_after) / peak_operating_before * 100.0
        if peak_operating_before > 0 else 0.0
    )

    return {
        "peak_before_kw": peak_global_before,
        "peak_operating_before_kw": peak_operating_before,
        "peak_target_kw": peak_target,
        "peak_after_estimated_kw": peak_global_after,
        "peak_operating_after_estimated_kw": peak_operating_after,
        "peak_reduction_pct": global_reduction,
        "peak_operating_reduction_pct": operating_reduction,
        "peak_shaving_power_kw": peak_power,
        "peak_shaving_nominal_power_kw": float(p_nom),
        "peak_shaving_energy_raw_kwh": energy_raw,
        "peak_shaving_capacity_kwh": float(capacity),
        "peak_shaving_delivered_kwh": float(discharge_required.sum()),
        "grid_charge_to_bess_kwh": float(daily_charge_ac.sum() - charge_unserved),
        "grid_after_series": grid_after,
        "grid_after_kwh": float(grid_after.sum()),
        "operating_window": operating_label,
        "valley_charge_hours": ",".join(str(h) for h in VALLEY_CHARGE_HOURS),
        "valley_charge_unserved_kwh": float(charge_unserved),
    }


def _simulate_grid_balance(
    surplus: np.ndarray,
    priority_ev_deficit: np.ndarray,
    building_deficit: np.ndarray,
    nonpriority_ev_deficit: np.ndarray,
    charge_from_pv: np.ndarray,
    discharge_to_ev: np.ndarray,
    discharge_to_building: np.ndarray,
    usable_capacity_kwh: float,
    nominal_power_kw: float,
) -> dict[str, float]:
    """Simulate residual public-grid import/export with finite BESS capacity."""
    soc = max(0.0, usable_capacity_kwh * SOC_INI)
    grid_after = np.zeros(len(surplus), dtype=float)
    ev_grid_after = np.zeros(len(surplus), dtype=float)
    building_grid_after = np.zeros(len(surplus), dtype=float)
    export_after = np.zeros(len(surplus), dtype=float)
    actual_charge_from_pv = np.zeros(len(surplus), dtype=float)
    actual_discharge_to_ev = np.zeros(len(surplus), dtype=float)
    actual_discharge_to_building = np.zeros(len(surplus), dtype=float)

    for i in range(len(surplus)):
        if surplus[i] > 0.0:
            charge_room_ac = max(0.0, (usable_capacity_kwh - soc) / ETA_C)
            charge_ac = min(charge_from_pv[i], nominal_power_kw, charge_room_ac)
            soc += charge_ac * ETA_C
            actual_charge_from_pv[i] = charge_ac
            export_after[i] = max(0.0, surplus[i] - charge_ac)

        remaining_power = nominal_power_kw
        ev_deficit_i = priority_ev_deficit[i]
        if ev_deficit_i > 0.0:
            discharge_room_ac = max(0.0, soc * ETA_D)
            discharge_ac = min(
                discharge_to_ev[i],
                remaining_power,
                discharge_room_ac,
                ev_deficit_i,
            )
            soc -= discharge_ac / ETA_D
            remaining_power -= discharge_ac
            actual_discharge_to_ev[i] = discharge_ac

        building_deficit_i = building_deficit[i]
        if building_deficit_i > 0.0 and remaining_power > 0.0:
            discharge_room_ac = max(0.0, soc * ETA_D)
            discharge_ac = min(
                discharge_to_building[i],
                remaining_power,
                discharge_room_ac,
                building_deficit_i,
            )
            soc -= discharge_ac / ETA_D
            actual_discharge_to_building[i] = discharge_ac

        ev_grid_after[i] = (
            max(0.0, priority_ev_deficit[i] - actual_discharge_to_ev[i])
            + nonpriority_ev_deficit[i]
        )
        building_grid_after[i] = max(
            0.0,
            building_deficit[i] - actual_discharge_to_building[i],
        )
        grid_after[i] = ev_grid_after[i] + building_grid_after[i]

    return {
        "grid_after_kwh": float(grid_after.sum()),
        "ev_grid_after_kwh": float(ev_grid_after.sum()),
        "building_grid_after_kwh": float(building_grid_after.sum()),
        "pv_export_after_kwh": float(export_after.sum()),
        "bess_charge_from_pv_kwh": float(actual_charge_from_pv.sum()),
        "bess_discharge_to_ev_kwh": float(actual_discharge_to_ev.sum()),
        "bess_discharge_to_building_kwh": float(actual_discharge_to_building.sum()),
        "bess_discharge_to_load_kwh": float(
            actual_discharge_to_ev.sum() + actual_discharge_to_building.sum()
        ),
        "grid_after_series": grid_after,
        "ev_grid_after_series": ev_grid_after,
        "building_grid_after_series": building_grid_after,
        "pv_export_after_series": export_after,
        "bess_charge_from_pv_series": actual_charge_from_pv,
        "bess_discharge_to_ev_series": actual_discharge_to_ev,
        "bess_discharge_to_building_series": actual_discharge_to_building,
    }


def _solar_shift_requirement(
    surplus: np.ndarray,
    priority_ev_deficit: np.ndarray,
    building_deficit: np.ndarray,
    target_shift_ratio: float,
) -> dict[str, Any]:
    """Return BESS sizing needed to shift feasible PV surplus with EV priority."""
    profiles = _build_bess_shift_profiles(
        surplus,
        priority_ev_deficit,
        building_deficit,
        target_shift_ratio,
    )
    charge_from_pv = profiles["charge_from_pv"]
    discharge_to_ev = profiles["discharge_to_ev"]
    discharge_to_building = profiles["discharge_to_building"]
    discharge_to_load = discharge_to_ev + discharge_to_building
    excursions = profiles["excursions"]

    positive_excursions = excursions[excursions > 1e-9]
    if len(positive_excursions) == 0:
        e_raw = 0.0
    else:
        e_raw = float(np.percentile(positive_excursions, PERC_EXCURSION))

    p_charge = (
        float(np.percentile(charge_from_pv[charge_from_pv > 1e-9], PERC_POWER))
        if np.any(charge_from_pv > 1e-9)
        else 0.0
    )
    p_discharge = (
        float(np.percentile(discharge_to_load[discharge_to_load > 1e-9], PERC_POWER))
        if np.any(discharge_to_load > 1e-9)
        else 0.0
    )

    return {
        "solar_shift_energy_raw_kwh": e_raw,
        "solar_shift_capacity_kwh": float(max(math.ceil(e_raw / DOD), MIN_CAPACITY_KWH)),
        "solar_shift_power_kw": float(max(math.ceil(max(p_charge, p_discharge)), MIN_POWER_KW)),
        "solar_shift_charge_from_pv_profile": charge_from_pv,
        "solar_shift_discharge_to_ev_profile": discharge_to_ev,
        "solar_shift_discharge_to_building_profile": discharge_to_building,
        "solar_shift_discharge_to_load_profile": discharge_to_load,
        "solar_shift_p_charge_kw": p_charge,
        "solar_shift_p_discharge_kw": p_discharge,
        "solar_shift_target_delivered_kwh": float(discharge_to_load.sum()),
        "solar_shift_target_delivered_ev_kwh": float(discharge_to_ev.sum()),
        "solar_shift_target_delivered_building_kwh": float(discharge_to_building.sum()),
        "solar_shift_target_charge_from_pv_kwh": float(charge_from_pv.sum()),
    }


def size_profile(
    df: pd.DataFrame,
    pv_kwp: float,
    t_out: np.ndarray,
    bdata: dict,
    building_id: Optional[int] = None,
    target_shift_ratio: float = TARGET_SHIFT_RATIO,
    min_peak_shaving_pct: float = MIN_PEAK_SHAVING_PCT,
) -> dict:
    """Dimension BESS from one building profile and PV nominal power."""
    nsl = df["non_shiftable_load"].to_numpy(dtype=float)
    cd = df["cooling_demand"].to_numpy(dtype=float)
    dhw = df["dhw_demand"].to_numpy(dtype=float)
    solar_per_kw = df["solar_generation"].to_numpy(dtype=float)
    solar = solar_per_kw * pv_kwp / 1000.0

    cop = _cooling_cop(bdata, t_out, len(df), building_id)
    ev_load, ev_stats = _ev_charger_load(bdata, len(df))
    controlled_machine_load, controlled_machine_stats = _controlled_machine_load(bdata, len(df))
    base_building_load = np.clip(nsl + cd / cop + dhw / COP_ACS, 0.0, None)
    load_without_ev = np.clip(base_building_load + controlled_machine_load, 0.0, None)
    load = load_without_ev + ev_load

    pv_balance = _pv_priority_balance(solar, load_without_ev, ev_load)
    direct_pv_to_ev = pv_balance["direct_pv_to_ev"]
    direct_pv_to_building = pv_balance["direct_pv_to_building"]
    direct_pv_to_load = direct_pv_to_ev + direct_pv_to_building
    surplus = pv_balance["surplus"]
    ev_deficit = pv_balance["ev_deficit"]
    building_deficit = pv_balance["building_deficit"]

    operating_mask, operating_label = _operating_mask(df, building_id)
    priority_ev_deficit = np.where(operating_mask, ev_deficit, 0.0)
    nonpriority_ev_deficit = ev_deficit - priority_ev_deficit
    deficit = priority_ev_deficit + building_deficit + nonpriority_ev_deficit

    grid_before = float(deficit.sum())
    ev_grid_before = float(ev_deficit.sum())
    building_grid_before = float(building_deficit.sum())
    pv_surplus_before = float(surplus.sum())
    peak = _peak_shaving_requirement(deficit, df, building_id, min_peak_shaving_pct)
    solar_shift = _solar_shift_requirement(
        surplus,
        priority_ev_deficit,
        building_deficit,
        target_shift_ratio,
    )
    e_bess = max(
        float(solar_shift["solar_shift_capacity_kwh"]),
        float(peak["peak_shaving_capacity_kwh"]),
        MIN_CAPACITY_KWH,
    )
    p_nom = max(
        float(solar_shift["solar_shift_power_kw"]),
        float(peak["peak_shaving_nominal_power_kw"]),
        MIN_POWER_KW,
    )

    usable_capacity = e_bess * DOD
    solar_dispatch = _simulate_grid_balance(
        surplus,
        priority_ev_deficit,
        building_deficit,
        nonpriority_ev_deficit,
        solar_shift["solar_shift_charge_from_pv_profile"],
        solar_shift["solar_shift_discharge_to_ev_profile"],
        solar_shift["solar_shift_discharge_to_building_profile"],
        usable_capacity,
        p_nom,
    )

    load_avg = float(load.mean())
    solar_avg = float(solar.mean())
    grid_after_series = solar_dispatch["grid_after_series"]
    grid_after = float(solar_dispatch["grid_after_kwh"])
    load_total = float(load.sum())
    solar_total = float(solar.sum())
    pv_export = float(solar_dispatch["pv_export_after_kwh"])
    pv_accounted = float(direct_pv_to_load.sum()) + pv_export
    pv_shift_charge = float(solar_dispatch["bess_charge_from_pv_kwh"])
    pv_shift_discharge_ev = float(solar_dispatch["bess_discharge_to_ev_kwh"])
    pv_shift_discharge_building = float(solar_dispatch["bess_discharge_to_building_kwh"])
    pv_shift_discharge = pv_shift_discharge_ev + pv_shift_discharge_building
    pv_accounted += pv_shift_charge

    peak_after_dispatch = float(grid_after_series.max()) if len(grid_after_series) else 0.0
    operating_after = grid_after_series[operating_mask]
    peak_operating_after_dispatch = (
        float(operating_after.max()) if len(operating_after) else peak_after_dispatch
    )
    peak_reduction_dispatch = (
        (peak["peak_before_kw"] - peak_after_dispatch) / peak["peak_before_kw"] * 100.0
        if peak["peak_before_kw"] > 0 else 0.0
    )
    peak_operating_reduction_dispatch = (
        (peak["peak_operating_before_kw"] - peak_operating_after_dispatch)
        / peak["peak_operating_before_kw"] * 100.0
        if peak["peak_operating_before_kw"] > 0 else 0.0
    )

    if solar_shift["solar_shift_capacity_kwh"] >= peak["peak_shaving_capacity_kwh"]:
        sizing_driver = "solar_shift_daily_surplus"
    else:
        sizing_driver = "peak_shaving_valley_charge"

    return {
        "E_raw": float(max(solar_shift["solar_shift_energy_raw_kwh"], peak["peak_shaving_energy_raw_kwh"])),
        "E_bess": float(e_bess),
        "P_nom": float(p_nom),
        "E_balance": solar_shift["solar_shift_capacity_kwh"],
        "P_balance": solar_shift["solar_shift_power_kw"],
        "E_peak_shaving": peak["peak_shaving_capacity_kwh"],
        "P_peak_shaving": peak["peak_shaving_power_kw"],
        "P_charge": float(p_nom),
        "P_discharge": max(
            float(solar_shift["solar_shift_p_discharge_kw"]),
            float(peak["peak_shaving_power_kw"]),
        ),
        "sizing_driver": sizing_driver,
        "solar_avg": solar_avg,
        "load_avg": load_avg,
        "pv_load_pct": solar_avg / load_avg * 100.0 if load_avg > 0 else 0.0,
        "load_total_kwh": load_total,
        "base_building_load_total_kwh": float(base_building_load.sum()),
        "load_without_ev_total_kwh": float(load_without_ev.sum()),
        "controlled_machine_load_total_kwh": controlled_machine_stats["controlled_machine_load_total_kwh"],
        "controlled_machine_load_peak_kw": controlled_machine_stats["controlled_machine_load_peak_kw"],
        "controlled_machine_load_avg_kw": controlled_machine_stats["controlled_machine_load_avg_kw"],
        "controlled_machine_count": controlled_machine_stats["controlled_machine_count"],
        "controlled_machine_active_window_rows": controlled_machine_stats["controlled_machine_active_window_rows"],
        "controlled_machine_potential_cycles": controlled_machine_stats["controlled_machine_potential_cycles"],
        "ev_load_total_kwh": ev_stats["ev_load_total_kwh"],
        "ev_load_operating_kwh": float(ev_load[operating_mask].sum()),
        "ev_load_outside_operating_kwh": float(ev_load[~operating_mask].sum()),
        "ev_load_peak_kw": ev_stats["ev_load_peak_kw"],
        "ev_load_avg_kw": ev_stats["ev_load_avg_kw"],
        "ev_charger_count": ev_stats["ev_charger_count"],
        "ev_state1_hours": ev_stats["ev_state1_hours"],
        "solar_total_kwh": solar_total,
        "direct_pv_to_load_kwh": float(direct_pv_to_load.sum()),
        "direct_pv_to_ev_kwh": float(direct_pv_to_ev.sum()),
        "direct_pv_to_building_kwh": float(direct_pv_to_building.sum()),
        "pv_surplus_before_kwh": pv_surplus_before,
        "grid_before_kwh": grid_before,
        "ev_grid_before_kwh": ev_grid_before,
        "building_grid_before_kwh": building_grid_before,
        "grid_after_kwh": grid_after,
        "ev_grid_after_kwh": solar_dispatch["ev_grid_after_kwh"],
        "building_grid_after_kwh": solar_dispatch["building_grid_after_kwh"],
        "grid_reduction_pct": (grid_before - grid_after) / grid_before * 100.0 if grid_before > 0 else 0.0,
        "pv_export_after_kwh": pv_export,
        "bess_charge_from_pv_kwh": pv_shift_charge,
        "bess_charge_from_grid_kwh": 0.0,
        "bess_discharge_to_ev_kwh": pv_shift_discharge_ev,
        "bess_discharge_to_building_kwh": pv_shift_discharge_building,
        "bess_discharge_to_load_kwh": pv_shift_discharge,
        "solar_utilization_pct": pv_accounted / solar_total * 100.0 if solar_total > 0 else 0.0,
        "peak_before_kw": peak["peak_before_kw"],
        "peak_operating_before_kw": peak["peak_operating_before_kw"],
        "peak_target_kw": peak["peak_target_kw"],
        "peak_after_estimated_kw": peak_after_dispatch,
        "peak_operating_after_estimated_kw": peak_operating_after_dispatch,
        "peak_reduction_pct": peak_reduction_dispatch,
        "peak_operating_reduction_pct": peak_operating_reduction_dispatch,
        "peak_shaving_delivered_kwh": peak["peak_shaving_delivered_kwh"],
        "solar_shift_target_delivered_kwh": solar_shift["solar_shift_target_delivered_kwh"],
        "solar_shift_target_delivered_ev_kwh": solar_shift["solar_shift_target_delivered_ev_kwh"],
        "solar_shift_target_delivered_building_kwh": solar_shift["solar_shift_target_delivered_building_kwh"],
        "solar_shift_target_charge_from_pv_kwh": solar_shift["solar_shift_target_charge_from_pv_kwh"],
        "operating_window": operating_label,
        "valley_charge_hours": peak["valley_charge_hours"],
        "valley_charge_unserved_kwh": peak["valley_charge_unserved_kwh"],
        "target_shift_ratio": target_shift_ratio,
        "min_peak_shaving_pct": min_peak_shaving_pct,
        "days": int(len(surplus) // 24),
    }


def size_building(
    bkey: str,
    bdata: dict,
    t_out: np.ndarray,
    target_shift_ratio: float = TARGET_SHIFT_RATIO,
    min_peak_shaving_pct: float = MIN_PEAK_SHAVING_PCT,
) -> dict:
    df = pd.read_csv(DATASET_DIR / f"{bkey}.csv")
    pv_kwp = float(
        bdata.get("pv", {})
        .get("attributes", {})
        .get("nominal_power", 0.0)
    )
    return size_profile(
        df,
        pv_kwp,
        t_out,
        bdata,
        _building_sort_key(bkey),
        target_shift_ratio,
        min_peak_shaving_pct,
    )


def build_results(
    schema: dict,
    target_shift_ratio: float = TARGET_SHIFT_RATIO,
    min_peak_shaving_pct: float = MIN_PEAK_SHAVING_PCT,
) -> dict[str, dict]:
    weather = pd.read_csv(WEATHER_PATH)
    t_out = weather["outdoor_dry_bulb_temperature"].to_numpy(dtype=float)
    return {
        bkey: size_building(bkey, bdata, t_out, target_shift_ratio, min_peak_shaving_pct)
        for bkey, bdata in sorted(schema["buildings"].items(), key=lambda item: _building_sort_key(item[0]))
    }


def print_results(schema: dict, results: dict[str, dict]) -> None:
    target_shift_ratio = next(iter(results.values()))["target_shift_ratio"] if results else TARGET_SHIFT_RATIO
    peak_shaving_pct = next(iter(results.values()))["min_peak_shaving_pct"] if results else MIN_PEAK_SHAVING_PCT
    print("=" * 168)
    print("SIZING BESS - PV prioriza EV + BESS prioriza EV en ventana operativa")
    print(f"DOD={DOD} eta_c={ETA_C} eta_d={ETA_D} eta_rt={ETA_RT}")
    print(
        f"E_final=max(E_solar_shift_ev_priority, E_peak_shaving) | "
        f"P_nom=max(P_solar_shift, P_peak_shaving, P_recarga) | "
        f"target_shift_ratio={target_shift_ratio:.1%} | "
        f"min_peak_shaving={peak_shaving_pct:.1%}"
    )
    print("=" * 168)
    print(
        f"{'B':>3} {'E_old':>10} {'P_old':>8} {'E_new':>10} {'P_new':>8} "
        f"{'E_solar':>10} {'E_peak':>10} {'PV->EV':>9} {'PV->BESS':>10} "
        f"{'BESS->EV':>10} {'PV exp':>9} "
        f"{'grid -%':>8} {'driver':>24} {'dias':>5}"
    )
    print("-" * 168)
    for bkey, res in results.items():
        bid = _building_sort_key(bkey)
        old = schema["buildings"][bkey].get("electrical_storage", {}).get("attributes", {})
        print(
            f"{bid:>3} {float(old.get('capacity', 0.0)):>10.1f} "
            f"{float(old.get('nominal_power', 0.0)):>8.1f} "
            f"{res['E_bess']:>10.0f} {res['P_nom']:>8.0f} "
            f"{res['E_balance']:>10.0f} "
            f"{res['E_peak_shaving']:>10.0f} "
            f"{res['direct_pv_to_ev_kwh'] / 1000.0:>9.1f} "
            f"{res['bess_charge_from_pv_kwh'] / 1000.0:>10.1f} "
            f"{res['bess_discharge_to_ev_kwh'] / 1000.0:>10.1f} "
            f"{res['pv_export_after_kwh'] / 1000.0:>9.1f} "
            f"{res['grid_reduction_pct']:>7.1f}% "
            f"{res['sizing_driver']:>24} {res['days']:>5}"
        )
    print("=" * 168)


def apply_results(schema: dict, results: dict[str, dict]) -> None:
    for bkey, res in results.items():
        schema["buildings"][bkey]["electrical_storage"] = {
            "type": "citylearn.energy_model.Battery",
            "autosize": False,
            "attributes": {
                "capacity": res["E_bess"],
                "nominal_power": res["P_nom"],
                "depth_of_discharge": DOD,
                "efficiency": ETA_RT,
                "capacity_loss_coefficient": LOSS,
                "loss_coefficient": 0.0,
                "initial_soc": SOC_INI,
            },
        }
    SCHEMA_PATH.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Dimensiona BESS del dataset Iquitos.")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--dry-run", action="store_true", help="Calcula e imprime sin escribir schema.json.")
    mode.add_argument("--write", action="store_true", help="Actualiza schema.json con los nuevos BESS.")
    parser.add_argument(
        "--target-shift-ratio",
        type=float,
        default=TARGET_SHIFT_RATIO,
        help="Fraccion de energia factible PV excedente -> deficit de red que se dimensiona para desplazar.",
    )
    parser.add_argument(
        "--min-peak-shaving-pct",
        type=float,
        default=MIN_PEAK_SHAVING_PCT,
        help="Reduccion minima del pico de importacion de red por edificio, por ejemplo 0.10 = 10%%.",
    )
    args = parser.parse_args()
    if not 0.0 <= args.target_shift_ratio <= 1.0:
        raise ValueError("--target-shift-ratio debe estar entre 0.0 y 1.0")
    if not 0.0 <= args.min_peak_shaving_pct < 1.0:
        raise ValueError("--min-peak-shaving-pct debe estar en [0.0, 1.0)")

    schema = _load_schema()
    results = build_results(schema, args.target_shift_ratio, args.min_peak_shaving_pct)
    print_results(schema, results)

    if args.write:
        apply_results(schema, results)
        print(f"schema.json actualizado: {SCHEMA_PATH}")
    else:
        print("Dry-run: schema.json no fue modificado. Usa --write para aplicar.")


if __name__ == "__main__":
    main()
