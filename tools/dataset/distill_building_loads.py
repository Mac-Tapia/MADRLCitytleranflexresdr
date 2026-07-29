"""
Component-based load distillation for citylearn_iquitos_2023_2025.

This script transforms monthly metered inputs from CityLearn/data/buildingcsv
into the hourly CityLearn building files. The monthly files B_01.csv..B_17.csv
are raw inputs; they are not loaded directly by CityLearn. B_01.csv (Electro
Oriente S.A.) was generated on 2026-06-06 from Building_1.csv using COP=2.80
and MT2 tariff prices calibrated from the district pricing_monthly_audit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd

from buildingcsv_inputs import (
    BUILDINGCSV_DIR,
    DATASET_DIR,
    DEFAULT_BUILDINGS_WITH_MONTHLY_DATA,
    PRICING_COLUMNS,
    YEARS,
    BuildingInventory,
    build_hourly_pricing_from_monthly_measurements,
    derive_tariff_period_prices,
    inventory_as_records,
    load_building_inventory,
    load_monthly_measurements,
    measurements_to_total_dict,
)


ROOT = Path(__file__).resolve().parents[2]
SCHEMA_PATH = DATASET_DIR / "schema.json"
WEATHER_CSV = DATASET_DIR / "weather.csv"
DEFAULT_REPORT_PATH = ROOT / "tools" / "dataset_docs" / "distillation_report.csv"
PRICING_CSV = DATASET_DIR / "pricing.csv"

try:
    sys.stdout.reconfigure(encoding="utf-8")
except AttributeError:
    pass


def _project_path(path: Path | str) -> Path:
    p = Path(path)
    return (ROOT / p).resolve() if not p.is_absolute() else p.resolve()


def _rel(path: Path | str) -> str:
    p = _project_path(path)
    try:
        return str(p.relative_to(ROOT))
    except Exception:
        return str(p)


# Physical parameters retained for compatibility with existing tests.
T_TARGET = 8.5
COP_ACS_DEF = 0.85
COP_CLIP_LOW = 1.5
COP_CLIP_HIGH = 5.0
PEAK_HOURS = {18, 19, 20, 21, 22}

# The eta values are COP_design / 14.44, matching the previous engineering
# convention in this repository. They are only fallbacks when schema.json does
# not define cooling_device.attributes.efficiency.
ETA_BY_USE = {
    "office": 2.8 / 14.44,
    "office_critical": 2.8 / 14.44,
    "assembly": 3.0 / 14.44,
    "assembly_military": 2.5 / 14.44,
    "retail": 3.0 / 14.44,
    "multifamily_hotel": 3.0 / 14.44,
    "commercial_mall": 3.0 / 14.44,
    "education": 2.5 / 14.44,
    "healthcare": 2.5 / 14.44,
    "healthcare_hospital": 2.5 / 14.44,
    "industrial_port": 2.5 / 14.44,
    "industrial": 2.8 / 14.44,
    "laboratory": 2.5 / 14.44,
}


def _normalise_use(value: str) -> str:
    return str(value or "").strip().lower()


def _load_default_inventory() -> dict[int, BuildingInventory]:
    try:
        return load_building_inventory()
    except FileNotFoundError:
        return {}


def _eta_by_building(inventory: dict[int, BuildingInventory]) -> dict[int, float]:
    eta: dict[int, float] = {}
    for bid, meta in inventory.items():
        eta[bid] = ETA_BY_USE.get(_normalise_use(meta.tipo_uso_citylearn), 2.8 / 14.44)
    return eta


DEFAULT_INVENTORY = _load_default_inventory()
ETA_BY_BLDG = _eta_by_building(DEFAULT_INVENTORY)

def _with_source_columns(measurements: pd.DataFrame) -> pd.DataFrame:
    out = measurements.copy()
    if "record_type" not in out.columns:
        out["record_type"] = "measured"
    if "forecast_method" not in out.columns:
        out["forecast_method"] = ""
    if "forecast_scale_factor" not in out.columns:
        out["forecast_scale_factor"] = np.nan
    if "forecast_reference_months" not in out.columns:
        out["forecast_reference_months"] = ""
    return out


def _mode_or_default(series: pd.Series, default: str = "") -> str:
    values = series.dropna().astype(str).str.strip()
    values = values[values != ""]
    if values.empty:
        return default
    return str(values.mode().iloc[0])


def forecast_missing_measurements(
    measurements: pd.DataFrame,
    buildings: Iterable[int] = DEFAULT_BUILDINGS_WITH_MONTHLY_DATA,
) -> pd.DataFrame:
    """
    Complete missing 2023-2025 monthly records using measured data from the
    same building.

    Method:
      E_hat(y,m) = mean(E(measured same month in other years)) * overlap_scale

    overlap_scale is the ratio between measured target-year energy and the
    same-month reference profile for all months that are present in both sets.
    For B06 this backcasts Jan-Aug 2023 from 2024-2025 monthly seasonality and
    the Sep-Dec 2023 overlap level.
    """
    if measurements.empty:
        return _with_source_columns(measurements)

    base = _with_source_columns(measurements)
    additions: list[dict[str, object]] = []

    for bid in buildings:
        bdf = base[base["building_id"] == bid].copy()
        if bdf.empty:
            continue

        source_name = _mode_or_default(bdf["source_name"], f"Building_{bid}")
        tariff = _mode_or_default(bdf["tarifa"], "")

        for year in YEARS:
            target = bdf[bdf["year"] == year]
            for month in range(1, 13):
                already_present = ((target["month"] == month)).any()
                if already_present:
                    continue

                refs = bdf[(bdf["year"] != year) & (bdf["month"] == month)]
                if refs.empty:
                    continue

                ref_years = sorted(int(y) for y in refs["year"].unique())
                ref_profile = (
                    bdf[bdf["year"].isin(ref_years)]
                    .groupby("month", as_index=True)["energia_total_kwh"]
                    .mean()
                )

                overlap_months = sorted(set(target["month"].astype(int)).intersection(ref_profile.index.astype(int)))
                if overlap_months:
                    target_overlap = float(target[target["month"].isin(overlap_months)]["energia_total_kwh"].sum())
                    ref_overlap = float(ref_profile.loc[overlap_months].sum())
                    scale = target_overlap / ref_overlap if ref_overlap > 0.0 else 1.0
                else:
                    scale = 1.0

                total = float(refs["energia_total_kwh"].mean()) * scale
                punta_share = float((refs["energia_punta_kwh"] / refs["energia_total_kwh"]).mean())
                punta = total * punta_share
                fuera = total - punta

                reactiva_ratio = float((refs["energia_reactiva_kvarh"] / refs["energia_total_kwh"]).replace([np.inf, -np.inf], np.nan).dropna().mean())
                if np.isnan(reactiva_ratio):
                    reactiva_ratio = 0.0

                facturado_ratio = float((refs["total_facturado"] / refs["energia_total_kwh"]).replace([np.inf, -np.inf], np.nan).dropna().mean())
                if np.isnan(facturado_ratio):
                    facturado_ratio = 0.0

                factor_carga = float(refs["factor_carga"].dropna().mean()) if not refs["factor_carga"].dropna().empty else 0.0
                additions.append({
                    "building_id": bid,
                    "year": year,
                    "month": month,
                    "source_name": source_name,
                    "energia_punta_kwh": punta,
                    "energia_fuera_punta_kwh": fuera,
                    "energia_total_kwh": total,
                    "raw_energia_punta_kwh": punta,
                    "raw_energia_fuera_punta_kwh": fuera,
                    "raw_split_total_kwh": total,
                    "energia_reactiva_kvarh": total * reactiva_ratio,
                    "factor_carga": factor_carga,
                    "total_facturado": total * facturado_ratio,
                    "reported_total_energia_activa": total,
                    "reported_total_delta_kwh": 0.0,
                    "reported_total_delta_pct": 0.0,
                    "active_energy_source": "forecast_from_monthly_active_energy",
                    "measurement_quality_flag": "forecast",
                    "tarifa": tariff,
                    "source_file": "forecast",
                    "line_number": 0,
                    "record_type": "forecast",
                    "forecast_method": "calendar_month_mean_overlap_scaled",
                    "forecast_scale_factor": scale,
                    "forecast_reference_months": (
                        f"ref_years={','.join(str(y) for y in ref_years)};"
                        f"overlap={','.join(f'{year}-{m:02d}' for m in overlap_months) or 'none'}"
                    ),
                })

    if additions:
        base = pd.concat([base, pd.DataFrame(additions)], ignore_index=True)

    return base.sort_values(["building_id", "year", "month", "record_type"]).reset_index(drop=True)


try:
    _DEFAULT_RAW_MEASUREMENTS = load_monthly_measurements(buildings=DEFAULT_BUILDINGS_WITH_MONTHLY_DATA)
    _DEFAULT_MEASUREMENTS = forecast_missing_measurements(_DEFAULT_RAW_MEASUREMENTS)
except FileNotFoundError:
    _DEFAULT_RAW_MEASUREMENTS = pd.DataFrame()
    _DEFAULT_MEASUREMENTS = pd.DataFrame()

MEDIDAS_REALES = measurements_to_total_dict(_DEFAULT_MEASUREMENTS)
BUILDINGS_WITH_DATA = sorted(MEDIDAS_REALES.keys())


def load_schema(dataset_dir: Path = DATASET_DIR) -> dict:
    schema_path = dataset_dir / "schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"schema.json not found: {schema_path}")
    with schema_path.open("r", encoding="utf-8") as f:
        return json.load(f)


def load_weather(dataset_dir: Path = DATASET_DIR) -> np.ndarray:
    weather_csv = dataset_dir / "weather.csv"
    if not weather_csv.exists():
        raise FileNotFoundError(f"weather.csv not found: {weather_csv}")
    df = pd.read_csv(weather_csv, usecols=["outdoor_dry_bulb_temperature"])
    return df["outdoor_dry_bulb_temperature"].to_numpy(dtype=float)


def get_cop_params(
    schema: dict,
    bldg_id: int,
    inventory: dict[int, BuildingInventory] | None = None,
) -> tuple[float, float]:
    bkey = f"Building_{bldg_id}"
    bdata = schema.get("buildings", {}).get(bkey, {})

    cd = bdata.get("cooling_device", {})
    cattr = cd.get("attributes", {}) if isinstance(cd, dict) else {}
    eta = cattr.get("efficiency")
    if eta is not None:
        eta = float(eta)
    else:
        inventory = DEFAULT_INVENTORY if inventory is None else inventory
        if bldg_id in inventory:
            use_key = _normalise_use(inventory[bldg_id].tipo_uso_citylearn)
            eta = ETA_BY_USE.get(use_key, 2.8 / 14.44)
        else:
            eta = ETA_BY_BLDG.get(bldg_id, 2.8 / 14.44)

    dhw = bdata.get("dhw_device", {})
    dattr = dhw.get("attributes", {}) if isinstance(dhw, dict) else {}
    cop_acs = float(dattr.get("efficiency", COP_ACS_DEF)) if dattr else COP_ACS_DEF
    return float(eta), cop_acs


def compute_cop_array(t_out: np.ndarray, eta: float) -> np.ndarray:
    """Variable hourly cooling COP using the repository's Carnot convention."""
    denom = np.maximum(np.asarray(t_out, dtype=float) - T_TARGET, 0.5)
    cop = (T_TARGET + 273.15) * float(eta) / denom
    return np.clip(cop, COP_CLIP_LOW, COP_CLIP_HIGH)


def compute_managed_energy(df: pd.DataFrame, cop_act: np.ndarray, cop_acs: float) -> np.ndarray:
    """Electrical energy of controlled cooling and DHW in kWh per hour."""
    cd = df["cooling_demand"].to_numpy(dtype=float) if "cooling_demand" in df.columns else np.zeros(len(df))
    dw = df["dhw_demand"].to_numpy(dtype=float) if "dhw_demand" in df.columns else np.zeros(len(df))
    return cd / cop_act + dw / cop_acs


def build_month_year_index(df: pd.DataFrame) -> pd.DataFrame:
    """Add _year and _month for the fixed 2023-2025 hourly dataset."""
    n = len(df)
    years_arr = np.empty(n, dtype=int)
    end_2023 = min(8760, n)
    end_2024 = min(8760 + 8784, n)
    years_arr[:end_2023] = 2023
    years_arr[end_2023:end_2024] = 2024
    years_arr[end_2024:] = 2025

    out = df.copy()
    out["_year"] = years_arr
    out["_month"] = out["month"].to_numpy(dtype=int)
    return out


def _weekday_scale(day_type: np.ndarray, saturday: float, sunday: float) -> np.ndarray:
    scale = np.ones(len(day_type), dtype=float)
    scale[day_type == 6] = saturday
    scale[day_type == 7] = sunday
    return scale


def operational_factor(meta: BuildingInventory, hours: np.ndarray, day_type: np.ndarray) -> np.ndarray:
    """Deterministic operating schedule by inventory use type."""
    h = np.asarray(hours, dtype=int)
    day = np.asarray(day_type, dtype=int)
    use = _normalise_use(meta.tipo_uso_citylearn)

    if "healthcare" in use:
        profile = np.where((h >= 7) & (h <= 18), 1.0, 0.72)
        return profile

    if "hotel" in use:
        profile = np.where((h >= 6) & (h <= 10), 0.95, 0.70)
        profile = np.where((h >= 17) & (h <= 23), 1.0, profile)
        return profile

    if "mall" in use or "retail" in use:
        profile = np.where((h >= 10) & (h <= 22), 1.0, 0.18)
        profile = np.where((h >= 7) & (h < 10), 0.45, profile)
        return profile * _weekday_scale(day, 1.05, 1.00)

    if "assembly" in use:
        profile = np.where((h >= 6) & (h <= 22), 0.90, 0.45)
        return profile * _weekday_scale(day, 0.95, 0.85)

    if "education" in use:
        profile = np.where((h >= 7) & (h <= 17), 1.0, 0.08)
        profile = np.where((h >= 18) & (h <= 21), 0.30, profile)
        return profile * _weekday_scale(day, 0.35, 0.12)

    if "port" in use or "industrial" in use:
        profile = np.where((h >= 7) & (h <= 18), 1.0, 0.45)
        return profile * _weekday_scale(day, 0.70, 0.55)

    if "laboratory" in use:
        profile = np.where((h >= 8) & (h <= 18), 1.0, 0.55)
        return profile * _weekday_scale(day, 0.55, 0.40)

    profile = np.where((h >= 8) & (h <= 17), 1.0, 0.12)
    profile = np.where((h >= 18) & (h <= 21), 0.35, profile)
    return profile * _weekday_scale(day, 0.35, 0.15)


def cooling_setpoint(meta: BuildingInventory) -> float:
    use = _normalise_use(meta.tipo_uso_citylearn)
    if "healthcare" in use:
        return 22.0
    if "hotel" in use or "mall" in use or "retail" in use:
        return 23.0
    if "education" in use or "laboratory" in use:
        return 25.0
    if "assembly" in use:
        return 24.0
    return 24.0


def large_system_proxies(meta: BuildingInventory) -> tuple[float, float, str]:
    """Return controlled-cooling and critical-load capacity proxies."""
    system = meta.sistemas_refrigeracion_grandes.strip()
    text = system.lower()
    if text in {"", "none", "nan"}:
        return 0.0, 0.0, "none"

    split = max(float(meta.split_units), 1.0)
    offices = max(float(meta.oficinas_locales), 1.0)

    controlled = 0.0
    critical = 0.0
    label = "mixed"
    if "chiller" in text or "duct" in text or "vessel ac" in text or "split system" in text:
        controlled += 1.60 * split
        label = "controlled_cooling"

    if "precision" in text or "datacenter" in text:
        controlled += 0.80 * split
        critical += 0.50 * offices
        label = "critical_precision_ac"

    if (
        "cold" in text
        or "freezer" in text
        or "blood bank" in text
        or "archive" in text
        or "hepa" in text
    ):
        critical += 0.80 * offices
        label = "critical_refrigeration"

    if controlled == 0.0 and critical == 0.0:
        controlled = 0.75 * split

    return controlled, critical, label


def cooling_fraction(meta: BuildingInventory, t_out: np.ndarray, op_factor: np.ndarray) -> np.ndarray:
    degree = np.maximum(np.asarray(t_out, dtype=float) - cooling_setpoint(meta), 0.0)
    if np.nanmax(degree) <= 0.0:
        thermal = np.zeros(len(degree), dtype=float)
    else:
        ref = max(float(np.nanpercentile(degree, 95)), 0.1)
        thermal = np.clip(degree / ref, 0.0, 1.25)
    return np.clip(thermal * (0.30 + 0.70 * op_factor), 0.0, None)


def dhw_electric_driver(df: pd.DataFrame, meta: BuildingInventory, cop_acs: float) -> np.ndarray:
    if "dhw_demand" in df.columns and float(df["dhw_demand"].sum()) > 0.0:
        return df["dhw_demand"].to_numpy(dtype=float) / max(cop_acs, 0.1)

    use = _normalise_use(meta.tipo_uso_citylearn)
    if "hotel" not in use and "healthcare" not in use:
        return np.zeros(len(df), dtype=float)

    h = df["hour"].to_numpy(dtype=int)
    if "hotel" in use:
        hourly = np.array([
            0.020, 0.015, 0.012, 0.012, 0.020, 0.045,
            0.080, 0.090, 0.075, 0.045, 0.030, 0.028,
            0.030, 0.032, 0.035, 0.040, 0.055, 0.075,
            0.085, 0.075, 0.055, 0.040, 0.030, 0.021,
        ])
    else:
        hourly = np.array([
            0.030, 0.025, 0.025, 0.025, 0.030, 0.040,
            0.060, 0.070, 0.070, 0.060, 0.050, 0.045,
            0.045, 0.045, 0.050, 0.055, 0.060, 0.060,
            0.055, 0.045, 0.040, 0.035, 0.030, 0.030,
        ])
    return hourly[h] * max(meta.oficinas_locales, 1)


def component_drivers(
    df: pd.DataFrame,
    t_out: np.ndarray,
    meta: BuildingInventory,
    cop_acs: float,
) -> tuple[dict[str, np.ndarray], dict[str, float | str]]:
    hours = df["hour"].to_numpy(dtype=int)
    day_type = df["day_type"].to_numpy(dtype=int)
    op = operational_factor(meta, hours, day_type)
    controlled_proxy, critical_proxy, system_class = large_system_proxies(meta)

    area_proxy = max(meta.area_techada_m2 / 1000.0, 0.1)
    office_proxy = max(float(meta.oficinas_locales), 1.0)
    split_proxy = max(float(meta.split_units), 0.0)

    base_driver = np.ones(len(df), dtype=float) * (0.45 + 0.10 * area_proxy)
    equipment_driver = op * (0.22 * office_proxy + 0.02 * area_proxy)
    critical_driver = np.ones(len(df), dtype=float) * critical_proxy

    cooling_capacity = split_proxy + controlled_proxy
    cool_driver = cooling_capacity * cooling_fraction(meta, t_out, op)
    dhw_driver = dhw_electric_driver(df, meta, cop_acs)

    drivers = {
        "non_shiftable": np.clip(base_driver + equipment_driver + critical_driver, 0.0, None),
        "cooling": np.clip(cool_driver, 0.0, None),
        "dhw": np.clip(dhw_driver, 0.0, None),
    }
    metadata = {
        "area_proxy": area_proxy,
        "office_proxy": office_proxy,
        "split_proxy": split_proxy,
        "controlled_cooling_proxy": controlled_proxy,
        "critical_load_proxy": critical_proxy,
        "large_system_class": system_class,
    }
    return drivers, metadata


def _allocate_residual_energy_block(
    energy_kwh: float,
    idx: np.ndarray,
    drivers: dict[str, np.ndarray],
    nsl_elec: np.ndarray,
    cooling_elec: np.ndarray,
    dhw_elec: np.ndarray,
) -> dict[str, float]:
    """Set NSL as measured active energy minus controllable electric loads.

    The controllable loads already represented in CityLearn's training CSV are
    cooling_demand/COP and dhw_demand/COP. They are not copied into
    non_shiftable_load; NSL receives only the residual measured energy.
    """
    empty = {
        "measured_energy_kwh": 0.0,
        "controlled_model_kwh": 0.0,
        "controlled_used_kwh": 0.0,
        "controlled_scale": 1.0,
        "residual_nsl_kwh": 0.0,
    }

    if len(idx) == 0:
        return empty

    energy = max(float(energy_kwh), 0.0)
    if energy == 0.0:
        nsl_elec[idx] = 0.0
        cooling_elec[idx] = 0.0
        dhw_elec[idx] = 0.0
        return empty

    cooling_model = np.clip(cooling_elec[idx], 0.0, None)
    dhw_model = np.clip(dhw_elec[idx], 0.0, None)
    controlled_model = float(cooling_model.sum() + dhw_model.sum())
    controlled_scale = min(1.0, energy / controlled_model) if controlled_model > 0.0 else 1.0
    cooling_elec[idx] = cooling_model * controlled_scale
    dhw_elec[idx] = dhw_model * controlled_scale
    controlled_used = float(cooling_elec[idx].sum() + dhw_elec[idx].sum())

    residual = max(energy - controlled_used, 0.0)
    nsl = np.clip(drivers["non_shiftable"][idx], 0.0, None)
    denom = float(nsl.sum())
    if residual == 0.0:
        nsl_elec[idx] = 0.0
    elif denom <= 0.0:
        nsl_elec[idx] = residual / len(idx)
    else:
        nsl_elec[idx] = residual * nsl / denom

    return {
        "measured_energy_kwh": energy,
        "controlled_model_kwh": controlled_model,
        "controlled_used_kwh": controlled_used,
        "controlled_scale": controlled_scale,
        "residual_nsl_kwh": float(nsl_elec[idx].sum()),
    }


def _monthly_original_energy(
    df_indexed: pd.DataFrame,
    idx: np.ndarray,
    nsl_orig: np.ndarray,
    managed_orig: np.ndarray,
) -> tuple[float, float, float]:
    e_gest = float(managed_orig[idx].sum())
    e_ns = float(nsl_orig[idx].sum())
    return e_gest + e_ns, e_gest, e_ns


def calibrate_building(
    bldg_id: int,
    schema: dict,
    t_out: np.ndarray,
    dry_run: bool = False,
    report_only: bool = False,
    dataset_dir: Path = DATASET_DIR,
    inventory: dict[int, BuildingInventory] | None = None,
    measurements: pd.DataFrame | None = None,
) -> pd.DataFrame:
    # B_01 now has B_01.csv billing data (generated 2026-06-06) — no longer skipped
    inventory = DEFAULT_INVENTORY if inventory is None else inventory
    if bldg_id not in inventory:
        return pd.DataFrame()

    if measurements is None:
        measurements = _DEFAULT_MEASUREMENTS

    bmeas = measurements[measurements["building_id"] == bldg_id].copy() if not measurements.empty else pd.DataFrame()
    if bmeas.empty:
        return pd.DataFrame()

    csv_path = dataset_dir / f"Building_{bldg_id}.csv"
    if not csv_path.exists():
        return pd.DataFrame()

    df_orig = pd.read_csv(csv_path)
    if len(df_orig) != len(t_out):
        raise ValueError(f"B{bldg_id}: Building CSV rows={len(df_orig)} != weather rows={len(t_out)}")

    eta, cop_acs = get_cop_params(schema, bldg_id, inventory)
    cop_act = compute_cop_array(t_out, eta)
    managed_orig = compute_managed_energy(df_orig, cop_act, cop_acs)
    nsl_orig = df_orig["non_shiftable_load"].to_numpy(dtype=float)

    df_indexed = build_month_year_index(df_orig)
    drivers, driver_meta = component_drivers(df_indexed, t_out, inventory[bldg_id], cop_acs)

    nsl_elec = nsl_orig.copy()
    cooling_elec = df_orig["cooling_demand"].to_numpy(dtype=float) / cop_act
    if "dhw_demand" in df_orig.columns:
        dhw_elec = df_orig["dhw_demand"].to_numpy(dtype=float) / cop_acs
    else:
        dhw_elec = np.zeros(len(df_orig), dtype=float)

    rows: list[dict[str, object]] = []
    for m in bmeas.itertuples(index=False):
        month_mask = (
            (df_indexed["_year"].to_numpy(dtype=int) == int(m.year))
            & (df_indexed["_month"].to_numpy(dtype=int) == int(m.month))
        )
        month_idx = np.where(month_mask)[0]
        if len(month_idx) == 0:
            continue

        hours = df_indexed["hour"].to_numpy(dtype=int)
        peak_idx = month_idx[np.isin(hours[month_idx], list(PEAK_HOURS))]
        offpeak_idx = month_idx[~np.isin(hours[month_idx], list(PEAK_HOURS))]

        peak_audit = _allocate_residual_energy_block(
            m.energia_punta_kwh, peak_idx, drivers, nsl_elec, cooling_elec, dhw_elec
        )
        offpeak_audit = _allocate_residual_energy_block(
            m.energia_fuera_punta_kwh, offpeak_idx, drivers, nsl_elec, cooling_elec, dhw_elec
        )

        e_total_syn, e_gest_syn, e_ns_syn = _monthly_original_energy(
            df_indexed, month_idx, nsl_orig, managed_orig
        )
        e_ns_cal = float(nsl_elec[month_idx].sum())
        e_cooling_elec_cal = float(cooling_elec[month_idx].sum())
        e_dhw_elec_cal = float(dhw_elec[month_idx].sum())
        e_peak_cal = float((nsl_elec[peak_idx] + cooling_elec[peak_idx] + dhw_elec[peak_idx]).sum())
        e_offpeak_cal = float((nsl_elec[offpeak_idx] + cooling_elec[offpeak_idx] + dhw_elec[offpeak_idx]).sum())
        e_cal = e_ns_cal + e_cooling_elec_cal + e_dhw_elec_cal
        e_med = float(m.energia_total_kwh)
        delta_pct = (e_cal - e_med) / max(e_med, 1.0) * 100.0
        e_controlled_model = float(peak_audit["controlled_model_kwh"] + offpeak_audit["controlled_model_kwh"])
        e_controlled_used = float(peak_audit["controlled_used_kwh"] + offpeak_audit["controlled_used_kwh"])
        controlled_scale_min = min(float(peak_audit["controlled_scale"]), float(offpeak_audit["controlled_scale"]))
        tariff_prices = derive_tariff_period_prices(
            float(m.energia_punta_kwh),
            float(m.energia_fuera_punta_kwh),
            float(getattr(m, "total_facturado", 0.0)),
            str(m.tarifa),
        )

        rows.append({
            "building_id": bldg_id,
            "building_name": inventory[bldg_id].name,
            "year": int(m.year),
            "mes": int(m.month),
            "E_medido_kWh": round(e_med, 6),
            "E_punta_medido_kWh": round(float(m.energia_punta_kwh), 6),
            "E_fuera_punta_medido_kWh": round(float(m.energia_fuera_punta_kwh), 6),
            "E_punta_raw_kWh": round(float(getattr(m, "raw_energia_punta_kwh", m.energia_punta_kwh)), 6),
            "E_fuera_punta_raw_kWh": round(float(getattr(m, "raw_energia_fuera_punta_kwh", m.energia_fuera_punta_kwh)), 6),
            "E_split_raw_total_kWh": round(float(getattr(m, "raw_split_total_kwh", m.energia_total_kwh)), 6),
            "E_total_activa_reportada_kWh": round(float(getattr(m, "reported_total_energia_activa", 0.0)), 6),
            "E_punta_cal_kWh": round(e_peak_cal, 6),
            "E_fuera_punta_cal_kWh": round(e_offpeak_cal, 6),
            "E_total_syn": round(e_total_syn, 6),
            "E_gest_kWh": round(e_gest_syn, 6),
            "E_ns_orig": round(e_ns_syn, 6),
            "scale_factor": round(e_med / e_total_syn, 9) if e_total_syn > 0.0 else 1.0,
            "E_non_shiftable_cal_kWh": round(e_ns_cal, 6),
            "E_cooling_elec_cal_kWh": round(e_cooling_elec_cal, 6),
            "E_dhw_elec_cal_kWh": round(e_dhw_elec_cal, 6),
            "E_controlled_model_kWh": round(e_controlled_model, 6),
            "E_controlled_used_kWh": round(e_controlled_used, 6),
            "controlled_energy_scale_min": round(controlled_scale_min, 9),
            "E_non_shiftable_residual_kWh": round(e_ns_cal, 6),
            "E_cal_tot": round(e_cal, 6),
            "delta_%": round(delta_pct, 9),
            "reported_total_delta_kWh": round(float(m.reported_total_delta_kwh), 6),
            "reported_total_delta_%": round(float(getattr(m, "reported_total_delta_pct", 0.0)), 9),
            "factor_carga": round(float(m.factor_carga), 9),
            "energia_reactiva_kvarh": round(float(getattr(m, "energia_reactiva_kvarh", 0.0)), 6),
            "total_facturado": round(float(getattr(m, "total_facturado", 0.0)), 6),
            "facturado_por_kWh_activo": round(
                float(getattr(m, "total_facturado", 0.0)) / max(float(m.energia_total_kwh), 1.0),
                9,
            ),
            "tariff_peak_to_offpeak_ratio": round(float(tariff_prices["tariff_peak_to_offpeak_ratio"]), 9),
            "tariff_peak_price": round(float(tariff_prices["tariff_peak_price"]), 9),
            "tariff_offpeak_price": round(float(tariff_prices["tariff_offpeak_price"]), 9),
            "tariff_cost_reconstructed": round(float(tariff_prices["tariff_cost_reconstructed"]), 6),
            "tariff_cost_delta": round(float(tariff_prices["tariff_cost_delta"]), 6),
            "tariff_cost_delta_%": round(float(tariff_prices["tariff_cost_delta_pct"]), 9),
            "active_energy_source": str(getattr(m, "active_energy_source", "energia_activa_punta_fuera")),
            "measurement_quality_flag": str(getattr(m, "measurement_quality_flag", "")),
            "tarifa": str(m.tarifa).strip(),
            "source_file": str(m.source_file),
            "record_type": str(getattr(m, "record_type", "measured")),
            "forecast_method": str(getattr(m, "forecast_method", "")),
            "forecast_scale_factor": round(float(getattr(m, "forecast_scale_factor", np.nan)), 9)
            if not pd.isna(getattr(m, "forecast_scale_factor", np.nan)) else np.nan,
            "forecast_reference_months": str(getattr(m, "forecast_reference_months", "")),
            "large_system_class": driver_meta["large_system_class"],
            "controlled_cooling_proxy": round(float(driver_meta["controlled_cooling_proxy"]), 6),
            "critical_load_proxy": round(float(driver_meta["critical_load_proxy"]), 6),
            "status": "ok",
        })

    report = pd.DataFrame(rows)
    if report.empty:
        return report

    if not dry_run and not report_only:
        df_out = df_orig.copy()
        df_out["non_shiftable_load"] = nsl_elec
        df_out["cooling_demand"] = cooling_elec * cop_act
        if "dhw_demand" in df_out.columns:
            df_out["dhw_demand"] = dhw_elec * cop_acs
        df_out.to_csv(csv_path, index=False, float_format="%.6f")

    return report


def _missing_months(measurements: pd.DataFrame, building_id: int) -> list[str]:
    present = {
        (int(row.year), int(row.month))
        for row in measurements[measurements["building_id"] == building_id].itertuples(index=False)
    }
    missing = []
    for year in (2023, 2024, 2025):
        for month in range(1, 13):
            if (year, month) not in present:
                missing.append(f"{year}-{month:02d}")
    return missing


def print_report(bldg_id: int, report: pd.DataFrame, dry_run: bool, report_only: bool) -> None:
    if report.empty:
        return

    name = str(report["building_name"].iloc[0])
    mode = "(DRY-RUN)" if dry_run else ("(SOLO REPORTE)" if report_only else "")
    print(f"\n{'=' * 110}")
    print(f"  B{bldg_id:02d} - {name} {mode}")
    print(f"{'=' * 110}")
    print(
        f"  {'Año':>4} {'Mes':>3} {'Medido':>12} {'Punta':>11} {'F.Punta':>11} "
        f"{'Ctrl.e':>11} {'NSL(res)':>11} {'Cool.e':>11} {'DHW.e':>10} {'Esc':>7} {'Delta%':>10}"
    )
    print("  " + "-" * 120)
    for _, row in report.iterrows():
        print(
            f"  {int(row['year']):>4} {int(row['mes']):>3} "
            f"{float(row['E_medido_kWh']):>12.2f} "
            f"{float(row['E_punta_medido_kWh']):>11.2f} "
            f"{float(row['E_fuera_punta_medido_kWh']):>11.2f} "
            f"{float(row['E_controlled_used_kWh']):>11.2f} "
            f"{float(row['E_non_shiftable_cal_kWh']):>11.2f} "
            f"{float(row['E_cooling_elec_cal_kWh']):>11.2f} "
            f"{float(row['E_dhw_elec_cal_kWh']):>10.2f} "
            f"{float(row['controlled_energy_scale_min']):>7.4f} "
            f"{float(row['delta_%']):>10.6f}"
        )

    max_delta = float(report["delta_%"].abs().max())
    print("  " + "-" * 120)
    print(f"  Max |delta| = {max_delta:.9f}%")
    print("  Regla: NSL(res) = Medido - Ctrl.e; Ctrl.e = cooling_demand/COP + dhw_demand/COP.")
    if not dry_run and not report_only:
        print("  -> Building CSV actualizado: non_shiftable_load, cooling_demand, dhw_demand")


def print_summary(
    reports: dict[int, pd.DataFrame],
    measurements: pd.DataFrame,
    dry_run: bool,
    report_only: bool,
) -> None:
    print(f"\n{'=' * 110}")
    print("  RESUMEN GLOBAL")
    print(f"{'=' * 110}")
    print(f"  {'B':>3} {'Meses':>5} {'Pron.':>6} {'Medido kWh':>14} {'Max |delta| %':>14} {'Faltantes':>10}  Edificio")
    print("  " + "-" * 100)
    for bid, report in sorted(reports.items()):
        if report.empty:
            continue
        missing = _missing_months(measurements, bid)
        total = float(report["E_medido_kWh"].sum())
        max_delta = float(report["delta_%"].abs().max())
        forecast_count = int((report["record_type"] == "forecast").sum()) if "record_type" in report.columns else 0
        name = str(report["building_name"].iloc[0])[:42]
        print(
            f"  {bid:>3} {len(report):>5} {forecast_count:>6} "
            f"{total:>14.2f} {max_delta:>14.9f} {len(missing):>10}  {name}"
        )

    action = "sin escritura" if dry_run or report_only else "archivos Building_1..Building_17 actualizados"
    print("  " + "-" * 100)
    print(f"  Accion: {action}")
    print("=" * 110)


def write_outputs(
    reports: dict[int, pd.DataFrame],
    inventory: dict[int, BuildingInventory],
    measurements: pd.DataFrame,
    dataset_dir: Path,
    report_path: Path,
) -> None:
    dataset_dir = _project_path(dataset_dir)
    report_path = _project_path(report_path)
    report_frames = [report for report in reports.values() if not report.empty]
    if report_frames:
        report_path.parent.mkdir(parents=True, exist_ok=True)
        pd.concat(report_frames, ignore_index=True).to_csv(report_path, index=False, float_format="%.9f")

    pricing_audit_records: list[dict[str, object]] = []
    pricing_path = dataset_dir / "pricing.csv"
    reference_csv = dataset_dir / "Building_1.csv"
    if reference_csv.exists() and not measurements.empty:
        reference = pd.read_csv(reference_csv, usecols=["month", "hour"])
        indexed = build_month_year_index(reference)
        pricing, pricing_audit = build_hourly_pricing_from_monthly_measurements(indexed, measurements, PEAK_HOURS)
        if not pricing.empty:
            if pricing.columns.tolist() != PRICING_COLUMNS:
                raise ValueError(f"pricing columns mismatch: {pricing.columns.tolist()}")
            pricing.to_csv(pricing_path, index=False, float_format="%.9f")
        if not pricing_audit.empty:
            pricing_audit_records = pricing_audit.round(9).to_dict(orient="records")

    metadata = {
        "source_inventory": _rel(BUILDINGCSV_DIR),
        "source_monthly_measurements": "CityLearn/data/buildingcsv/B_02.csv..B_17.csv",
        "dataset": _rel(dataset_dir),
        "building_1_policy": "Building_1.csv is not monthly-distilled because B_01.csv does not exist; its training CSV keeps the same 12-column/26304-row CityLearn structure as B2-B17.",
        "peak_hours_local": sorted(PEAK_HOURS),
        "energy_balance_rule": "For each measured month, EnergiaActivaHoraPunta and EnergiaActivaFueraPunta are the physical active-energy source when available and are allocated only to their corresponding hourly blocks. totalEnergiaActiva is audited and used as fallback only when the TOU active split is missing. Distillation is residual: non_shiftable_load equals selected measured active energy minus controllable loads represented in the training CSV (cooling_demand/COP and dhw_demand/COP). EV, BESS and PV are scenario DER/control assets and are not subtracted from historical building meter energy.",
        "pricing_rule": "TotalFacturado is a monthly monetary bill, not kWh. pricing.csv is rebuilt from monthly bills with C = p_peak*E_punta + p_offpeak*E_fuera_punta and p_peak = r_tariff*p_offpeak; the absolute level is calibrated to reproduce aggregate district monthly bills while keeping one CityLearn-compatible hourly electricity_pricing series.",
        "pricing_file": _rel(pricing_path) if pricing_path.exists() else None,
        "pricing_columns": PRICING_COLUMNS,
        "pricing_currency": "source billing currency per kWh",
        "pricing_monthly_audit": pricing_audit_records,
        "measurement_quality_by_building": {
            str(bid): {
                str(flag): int(count)
                for flag, count in measurements[measurements["building_id"] == bid]["measurement_quality_flag"]
                .fillna("")
                .value_counts()
                .sort_index()
                .items()
            }
            for bid in sorted(measurements["building_id"].unique())
            if "measurement_quality_flag" in measurements.columns
        },
        "buildings": inventory_as_records(inventory),
        "measurement_months_by_building": {
            str(bid): int((measurements["building_id"] == bid).sum()) for bid in sorted(measurements["building_id"].unique())
        },
        "forecast_months_by_building": {
            str(bid): [
                f"{int(row.year)}-{int(row.month):02d}"
                for row in measurements[
                    (measurements["building_id"] == bid)
                    & (measurements.get("record_type", "measured") == "forecast")
                ].itertuples(index=False)
            ]
            for bid in sorted(measurements["building_id"].unique())
        },
        "forecast_method": "calendar_month_mean_overlap_scaled",
        "distillation_status_by_building": {
            str(bid): {
                "months_processed": int(len(report)),
                "forecast_months_processed": int((report["record_type"] == "forecast").sum())
                if "record_type" in report.columns else 0,
                "missing_months": _missing_months(measurements, bid),
                "max_abs_delta_pct": float(report["delta_%"].abs().max()) if not report.empty else None,
            }
            for bid, report in sorted(reports.items())
        },
    }
    metadata_path = dataset_dir / "building_metadata.json"
    with metadata_path.open("w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Distill monthly buildingcsv meter data into hourly CityLearn building files."
    )
    parser.add_argument(
        "--buildings",
        nargs="+",
        type=int,
        default=BUILDINGS_WITH_DATA,
        help=f"Building ids to process. Default: {BUILDINGS_WITH_DATA}",
    )
    parser.add_argument("--buildingcsv-dir", type=Path, default=BUILDINGCSV_DIR)
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--dry-run", action="store_true", help="Compute reports without writing Building_X.csv.")
    parser.add_argument("--report-only", action="store_true", help="Only report; do not write any file.")
    parser.add_argument("--report-out", type=Path, default=DEFAULT_REPORT_PATH)
    args = parser.parse_args(list(argv) if argv is not None else None)
    args.buildingcsv_dir = _project_path(args.buildingcsv_dir)
    args.dataset_dir = _project_path(args.dataset_dir)
    args.report_out = _project_path(args.report_out)

    inventory = load_building_inventory(args.buildingcsv_dir)
    raw_measurements = load_monthly_measurements(args.buildingcsv_dir, buildings=DEFAULT_BUILDINGS_WITH_MONTHLY_DATA)
    measurements = forecast_missing_measurements(raw_measurements, buildings=DEFAULT_BUILDINGS_WITH_MONTHLY_DATA)
    available = set(int(x) for x in measurements["building_id"].unique()) if not measurements.empty else set()

    buildings = [bid for bid in args.buildings if bid in available]
    skipped = [bid for bid in args.buildings if bid not in available]
    if skipped:
        print(f"ADVERTENCIA: edificios omitidos sin medicion mensual aplicable: {skipped}")

    if not buildings:
        print("No hay edificios con medicion mensual para procesar.")
        return 0

    schema = load_schema(args.dataset_dir)
    t_out = load_weather(args.dataset_dir)

    print("=" * 110)
    print("DESTILACION COMPONENTE-A-COMPONENTE PARA CITYLEARN")
    print(f"  buildingcsv: {args.buildingcsv_dir}")
    print(f"  dataset:     {args.dataset_dir}")
    print(f"  edificios:   {buildings}")
    print(f"  pronostico:  {int((measurements['record_type'] == 'forecast').sum())} meses completados")
    print(f"  modo:        {'sin escritura' if args.dry_run or args.report_only else 'escritura'}")
    print("=" * 110)

    reports: dict[int, pd.DataFrame] = {}
    for bid in buildings:
        report = calibrate_building(
            bldg_id=bid,
            schema=schema,
            t_out=t_out,
            dry_run=args.dry_run,
            report_only=args.report_only,
            dataset_dir=args.dataset_dir,
            inventory=inventory,
            measurements=measurements,
        )
        reports[bid] = report
        print_report(bid, report, args.dry_run, args.report_only)

    print_summary(reports, measurements, args.dry_run, args.report_only)

    if not args.dry_run and not args.report_only:
        write_outputs(reports, inventory, measurements, args.dataset_dir, args.report_out)
        print(f"Reporte: {args.report_out}")
        print(f"Metadata: {args.dataset_dir / 'building_metadata.json'}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
