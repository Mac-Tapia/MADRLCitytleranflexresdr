"""
Load audited buildingcsv inputs for the Iquitos CityLearn dataset.

The files in CityLearn/data/buildingcsv are raw engineering inputs:
building.csv is the inventory source of truth and B_02.csv..B_17.csv are
monthly metered bills. They are not directly loadable by CityLearn.
"""

from __future__ import annotations

import csv
import re
import unicodedata
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT = Path(__file__).resolve().parent.parent
BUILDINGCSV_DIR = ROOT / "CityLearn" / "data" / "buildingcsv"
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"

YEARS = (2023, 2024, 2025)
DEFAULT_BUILDINGS_WITH_MONTHLY_DATA = tuple(range(1, 18))  # B_01 incluido desde 2026-06-06

MONTHS = {
    "ene": 1,
    "enero": 1,
    "feb": 2,
    "febrero": 2,
    "mar": 3,
    "marzo": 3,
    "abr": 4,
    "abril": 4,
    "may": 5,
    "mayo": 5,
    "jun": 6,
    "junio": 6,
    "jul": 7,
    "julio": 7,
    "ago": 8,
    "agosto": 8,
    "set": 9,
    "sep": 9,
    "sept": 9,
    "setiembre": 9,
    "septiembre": 9,
    "oct": 10,
    "octubre": 10,
    "nov": 11,
    "noviembre": 11,
    "dic": 12,
    "diciembre": 12,
}

ACTIVE_TOTAL_TOLERANCE_KWH = 1.0
ACTIVE_TOTAL_TOLERANCE_RATIO = 0.02
PEAK_HOURS_LOCAL = (18, 19, 20, 21, 22)
DEFAULT_TARIFF_PEAK_TO_OFFPEAK_RATIO = 0.38 / 0.26
PRICING_COLUMNS = [
    "electricity_pricing",
    "electricity_pricing_predicted_1",
    "electricity_pricing_predicted_2",
    "electricity_pricing_predicted_3",
]


@dataclass(frozen=True)
class BuildingInventory:
    building_id: int
    source_id: str
    name: str
    area_techada_m2: float
    tipo_uso_citylearn: str
    oficinas_locales: int
    sistemas_refrigeracion_grandes: str
    split_units: int
    area_estacionamiento_m2: float
    tipo_vehiculo_predominante: str

    @property
    def has_large_refrigeration(self) -> bool:
        value = self.sistemas_refrigeracion_grandes.strip().lower()
        return value not in {"", "none", "nan"}


def normalize_header(value: str) -> str:
    value = (value or "").strip()
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "", value.lower())


def parse_decimal(value: object, default: float = 0.0) -> float:
    if value is None:
        return default

    text = str(value).strip()
    if text == "":
        return default

    text = text.replace("\xa0", "").replace(" ", "")
    if "," in text and "." in text:
        text = text.replace(".", "").replace(",", ".")
    elif "," in text:
        text = text.replace(",", ".")

    try:
        return float(text)
    except ValueError:
        return default


def parse_int(value: object, default: int = 0) -> int:
    return int(round(parse_decimal(value, float(default))))


def tariff_peak_to_offpeak_ratio(tarifa: object) -> float:
    """Return the TOU peak/off-peak multiplier used to split monthly bills."""
    code = normalize_header(str(tarifa or ""))
    # The source files identify tariff families (MT2, MT3, MT4, BT2, BT3), but
    # not the regulated period-by-period unit rates. Keep the existing project
    # TOU shape and calibrate its absolute level with each measured bill.
    known = {"mt2", "mt3", "mt4", "bt2", "bt3"}
    if code in known:
        return DEFAULT_TARIFF_PEAK_TO_OFFPEAK_RATIO
    return DEFAULT_TARIFF_PEAK_TO_OFFPEAK_RATIO


def derive_tariff_period_prices(
    energia_punta_kwh: float,
    energia_fuera_punta_kwh: float,
    total_facturado: float,
    tarifa: object,
) -> dict[str, float]:
    """
    Split one monthly bill into peak and off-peak unit prices.

    TotalFacturado is a monetary value, not energy. The formula preserves the
    measured monthly bill while using the measured peak/off-peak kWh split:

        C_m = p_peak * E_peak + p_off * E_off
        p_peak = r_tariff * p_off
    """
    e_peak = max(float(energia_punta_kwh), 0.0)
    e_off = max(float(energia_fuera_punta_kwh), 0.0)
    cost = max(float(total_facturado), 0.0)
    ratio = max(float(tariff_peak_to_offpeak_ratio(tarifa)), 1.0)
    e_total = e_peak + e_off

    if cost <= 0.0 or e_total <= 0.0:
        p_peak = 0.0
        p_off = 0.0
    elif e_peak > 0.0 and e_off > 0.0:
        p_off = cost / (ratio * e_peak + e_off)
        p_peak = ratio * p_off
    elif e_peak > 0.0:
        p_peak = cost / e_peak
        p_off = p_peak / ratio
    else:
        p_off = cost / e_off
        p_peak = ratio * p_off

    reconstructed = p_peak * e_peak + p_off * e_off
    delta = reconstructed - cost
    delta_pct = delta / cost * 100.0 if cost > 0.0 else 0.0
    return {
        "tariff_peak_to_offpeak_ratio": ratio,
        "tariff_peak_price": p_peak,
        "tariff_offpeak_price": p_off,
        "tariff_cost_reconstructed": reconstructed,
        "tariff_cost_delta": delta,
        "tariff_cost_delta_pct": delta_pct,
    }


def _shift_values(values: list[float], horizon: int) -> list[float]:
    if not values:
        return []
    if horizon <= 0:
        return list(values)

    out = list(values)
    for index in range(len(values)):
        source = min(index + horizon, len(values) - 1)
        out[index] = values[source]
    return out


def build_hourly_pricing_from_monthly_measurements(
    hourly_index: pd.DataFrame,
    measurements: pd.DataFrame,
    peak_hours: Iterable[int] = PEAK_HOURS_LOCAL,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build CityLearn pricing.csv from monthly bills and TOU active-energy split.

    CityLearn expects one hourly `electricity_pricing` series. The project
    schema currently references the same pricing file from every building, so
    this function writes a district-level price signal calibrated to reproduce
    the aggregate monthly bill from all measured buildings.
    """
    if hourly_index.empty or measurements.empty:
        return pd.DataFrame(columns=PRICING_COLUMNS), pd.DataFrame()

    year_col = "_year" if "_year" in hourly_index.columns else "year"
    month_col = "_month" if "_month" in hourly_index.columns else "month"
    required_index = {year_col, month_col, "hour"}
    missing_index = required_index.difference(hourly_index.columns)
    if missing_index:
        raise ValueError(f"hourly_index missing columns: {sorted(missing_index)}")

    required_measurements = {
        "year",
        "month",
        "energia_punta_kwh",
        "energia_fuera_punta_kwh",
        "total_facturado",
        "tarifa",
    }
    missing_measurements = required_measurements.difference(measurements.columns)
    if missing_measurements:
        raise ValueError(f"measurements missing columns: {sorted(missing_measurements)}")

    peak_hours_set = {int(hour) for hour in peak_hours}
    price = [0.0 for _ in range(len(hourly_index))]
    audit_rows: list[dict[str, object]] = []

    indexed = hourly_index.reset_index(drop=True)
    measurement_rows = measurements.copy()
    measurement_rows["year"] = pd.to_numeric(measurement_rows["year"], errors="coerce").fillna(0).astype(int)
    measurement_rows["month"] = pd.to_numeric(measurement_rows["month"], errors="coerce").fillna(0).astype(int)

    for (year, month), frame in indexed.groupby([year_col, month_col], sort=True):
        year_i = int(year)
        month_i = int(month)
        rows = measurement_rows[
            (measurement_rows["year"] == year_i)
            & (measurement_rows["month"] == month_i)
        ]
        if rows.empty:
            audit_rows.append({
                "year": year_i,
                "month": month_i,
                "months_rows": 0,
                "tariffs": "",
                "E_punta_kWh": 0.0,
                "E_fuera_punta_kWh": 0.0,
                "total_facturado": 0.0,
                "price_peak": 0.0,
                "price_offpeak": 0.0,
                "cost_reconstructed": 0.0,
                "cost_delta": 0.0,
                "cost_delta_pct": 0.0,
                "status": "missing_measurement",
            })
            continue

        e_peak = pd.to_numeric(rows["energia_punta_kwh"], errors="coerce").fillna(0.0).clip(lower=0.0)
        e_off = pd.to_numeric(rows["energia_fuera_punta_kwh"], errors="coerce").fillna(0.0).clip(lower=0.0)
        costs = pd.to_numeric(rows["total_facturado"], errors="coerce").fillna(0.0).clip(lower=0.0)
        ratios = rows["tarifa"].map(tariff_peak_to_offpeak_ratio).astype(float)

        weighted_peak_ratio = float((e_peak * ratios).sum())
        e_peak_total = float(e_peak.sum())
        e_off_total = float(e_off.sum())
        cost_total = float(costs.sum())
        ratio = weighted_peak_ratio / e_peak_total if e_peak_total > 0.0 else DEFAULT_TARIFF_PEAK_TO_OFFPEAK_RATIO
        denom = weighted_peak_ratio + e_off_total

        if cost_total > 0.0 and denom > 0.0:
            price_off = cost_total / denom
            price_peak = ratio * price_off
        elif cost_total > 0.0 and (e_peak_total + e_off_total) > 0.0:
            price_off = cost_total / (e_peak_total + e_off_total)
            price_peak = price_off
        else:
            price_off = 0.0
            price_peak = 0.0

        reconstructed = price_peak * e_peak_total + price_off * e_off_total
        delta = reconstructed - cost_total
        delta_pct = delta / cost_total * 100.0 if cost_total > 0.0 else 0.0

        for idx, row in frame.iterrows():
            price[int(idx)] = price_peak if int(row["hour"]) in peak_hours_set else price_off

        audit_rows.append({
            "year": year_i,
            "month": month_i,
            "months_rows": int(len(rows)),
            "tariffs": ",".join(sorted({str(value).strip() for value in rows["tarifa"] if str(value).strip()})),
            "E_punta_kWh": e_peak_total,
            "E_fuera_punta_kWh": e_off_total,
            "total_facturado": cost_total,
            "tariff_peak_to_offpeak_ratio_weighted": ratio,
            "price_peak": price_peak,
            "price_offpeak": price_off,
            "cost_reconstructed": reconstructed,
            "cost_delta": delta,
            "cost_delta_pct": delta_pct,
            "status": "ok" if abs(delta_pct) <= 1e-7 else "revisar",
        })

    pricing = pd.DataFrame({
        "electricity_pricing": price,
        "electricity_pricing_predicted_1": _shift_values(price, 1),
        "electricity_pricing_predicted_2": _shift_values(price, 2),
        "electricity_pricing_predicted_3": _shift_values(price, 3),
    })
    return pricing, pd.DataFrame(audit_rows)


def resolve_active_energy(
    punta_kwh: float,
    fuera_punta_kwh: float,
    reported_total_kwh: float,
) -> dict[str, float | str]:
    """Choose the physical active-energy source and keep raw audit columns."""
    raw_split_total = float(punta_kwh) + float(fuera_punta_kwh)
    reported_total = float(reported_total_kwh)

    if raw_split_total > 0.0:
        delta = reported_total - raw_split_total if reported_total > 0.0 else 0.0
        delta_pct = delta / raw_split_total * 100.0 if raw_split_total > 0.0 else 0.0
        tolerance = max(
            ACTIVE_TOTAL_TOLERANCE_KWH,
            ACTIVE_TOTAL_TOLERANCE_RATIO * max(abs(raw_split_total), abs(reported_total), 1.0),
        )
        quality = (
            "split_matches_reported_total"
            if reported_total <= 0.0 or abs(delta) <= tolerance
            else "split_reported_total_mismatch"
        )
        return {
            "energia_punta_kwh": float(punta_kwh),
            "energia_fuera_punta_kwh": float(fuera_punta_kwh),
            "energia_total_kwh": raw_split_total,
            "raw_energia_punta_kwh": float(punta_kwh),
            "raw_energia_fuera_punta_kwh": float(fuera_punta_kwh),
            "raw_split_total_kwh": raw_split_total,
            "reported_total_energia_activa": reported_total,
            "reported_total_delta_kwh": delta,
            "reported_total_delta_pct": delta_pct,
            "active_energy_source": "energia_activa_punta_fuera",
            "measurement_quality_flag": quality,
        }

    if reported_total > 0.0:
        return {
            "energia_punta_kwh": 0.0,
            "energia_fuera_punta_kwh": reported_total,
            "energia_total_kwh": reported_total,
            "raw_energia_punta_kwh": float(punta_kwh),
            "raw_energia_fuera_punta_kwh": float(fuera_punta_kwh),
            "raw_split_total_kwh": raw_split_total,
            "reported_total_energia_activa": reported_total,
            "reported_total_delta_kwh": 0.0,
            "reported_total_delta_pct": 0.0,
            "active_energy_source": "total_energia_activa_fallback",
            "measurement_quality_flag": "reported_total_without_tou_split",
        }

    return {
        "energia_punta_kwh": 0.0,
        "energia_fuera_punta_kwh": 0.0,
        "energia_total_kwh": 0.0,
        "raw_energia_punta_kwh": float(punta_kwh),
        "raw_energia_fuera_punta_kwh": float(fuera_punta_kwh),
        "raw_split_total_kwh": raw_split_total,
        "reported_total_energia_activa": reported_total,
        "reported_total_delta_kwh": 0.0,
        "reported_total_delta_pct": 0.0,
        "active_energy_source": "missing_active_energy",
        "measurement_quality_flag": "missing_active_energy",
    }


def load_building_inventory(
    buildingcsv_dir: Path = BUILDINGCSV_DIR,
    include_building_1: bool = True,
) -> dict[int, BuildingInventory]:
    """Read building.csv and return inventory metadata keyed by building id."""
    path = buildingcsv_dir / "building.csv"
    if not path.exists():
        raise FileNotFoundError(f"building.csv not found: {path}")

    with path.open("r", encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    inventory: dict[int, BuildingInventory] = {}
    for row in rows:
        source_id = str(row.get("ID_Edificio", "")).strip()
        match = re.search(r"(\d+)", source_id)
        if match is None:
            continue

        bid = int(match.group(1))
        if bid == 1 and not include_building_1:
            continue

        inventory[bid] = BuildingInventory(
            building_id=bid,
            source_id=source_id,
            name=str(row.get("Nombre_Edificio", "")).strip(),
            area_techada_m2=parse_decimal(row.get("Area_Techada_m2")),
            tipo_uso_citylearn=str(row.get("Tipo_Uso_CityLearn", "")).strip(),
            oficinas_locales=parse_int(row.get("Cant_Estimada_Oficinas_Locales")),
            sistemas_refrigeracion_grandes=str(row.get("Sistemas_Refrigeracion_Grandes", "")).strip(),
            split_units=parse_int(row.get("Cant_Est_Unidades_Autonomas_Split")),
            area_estacionamiento_m2=parse_decimal(row.get("Area_Estacionamiento_m2")),
            tipo_vehiculo_predominante=str(row.get("Tipo_Vehiculo_Predominante_Estac", "")).strip(),
        )

    return inventory


def inventory_as_records(inventory: dict[int, BuildingInventory]) -> list[dict[str, object]]:
    return [asdict(inventory[bid]) for bid in sorted(inventory)]


def _monthly_csv_path(buildingcsv_dir: Path, building_id: int) -> Path:
    return buildingcsv_dir / f"B_{building_id:02d}.csv"


def _normalised_row(header: list[str], raw_row: list[str]) -> dict[str, str]:
    row: dict[str, str] = {}
    for index, name in enumerate(header):
        key = normalize_header(name) or f"blank{index}"
        value = raw_row[index] if index < len(raw_row) else ""
        if key in row:
            key = f"{key}{index}"
        row[key] = value.strip()
    return row


def _first_value(row: dict[str, str], keys: Iterable[str], default: str = "") -> str:
    for key in keys:
        if key in row and row[key] != "":
            return row[key]
    return default


def read_monthly_measurement_file(path: Path, building_id: int) -> list[dict[str, object]]:
    """Read one B_XX.csv file, tolerating Latin-1, empty rows and blank columns."""
    if not path.exists():
        return []

    records: list[dict[str, object]] = []
    with path.open("r", encoding="latin-1", newline="") as f:
        reader = csv.reader(f, delimiter=";")
        try:
            header = next(reader)
        except StopIteration:
            return records

        source_col_key = normalize_header(header[0]) if header else ""
        for line_number, raw_row in enumerate(reader, start=2):
            if not raw_row or not any(cell.strip() for cell in raw_row):
                continue

            row = _normalised_row(header, raw_row)
            year = parse_int(_first_value(row, ("ano", "anio", "year")), default=0)
            if year not in YEARS:
                continue

            month_text = normalize_header(_first_value(row, ("mes", "month")))
            month = MONTHS.get(month_text)
            if month is None:
                continue

            punta = parse_decimal(_first_value(row, ("energiaactivahorapunta",)))
            fuera_punta = parse_decimal(_first_value(row, ("energiaactivafuerapunta",)))
            reported_total = parse_decimal(_first_value(row, ("totalenergiaactiva",)), default=0.0)
            active_energy = resolve_active_energy(punta, fuera_punta, reported_total)
            if float(active_energy["energia_total_kwh"]) <= 0.0:
                continue

            records.append({
                "building_id": building_id,
                "year": year,
                "month": month,
                "source_name": row.get(source_col_key, ""),
                **active_energy,
                "energia_reactiva_kvarh": parse_decimal(_first_value(row, ("energiareactiva",))),
                "factor_carga": parse_decimal(_first_value(row, ("factorcarga",))),
                "total_facturado": parse_decimal(_first_value(row, ("totalfacturado",))),
                "tarifa": _first_value(row, ("tarifa",)),
                "source_file": path.name,
                "line_number": line_number,
            })

    return records


def load_monthly_measurements(
    buildingcsv_dir: Path = BUILDINGCSV_DIR,
    buildings: Iterable[int] = DEFAULT_BUILDINGS_WITH_MONTHLY_DATA,
) -> pd.DataFrame:
    records: list[dict[str, object]] = []
    for building_id in buildings:
        records.extend(read_monthly_measurement_file(_monthly_csv_path(buildingcsv_dir, building_id), building_id))

    columns = [
        "building_id",
        "year",
        "month",
        "source_name",
        "energia_punta_kwh",
        "energia_fuera_punta_kwh",
        "energia_total_kwh",
        "raw_energia_punta_kwh",
        "raw_energia_fuera_punta_kwh",
        "raw_split_total_kwh",
        "energia_reactiva_kvarh",
        "factor_carga",
        "total_facturado",
        "reported_total_energia_activa",
        "reported_total_delta_kwh",
        "reported_total_delta_pct",
        "active_energy_source",
        "measurement_quality_flag",
        "tarifa",
        "source_file",
        "line_number",
    ]
    df = pd.DataFrame(records, columns=columns)
    if not df.empty:
        df = df.sort_values(["building_id", "year", "month"]).reset_index(drop=True)
    return df


def measurements_to_total_dict(measurements: pd.DataFrame) -> dict[int, dict[int, dict[int, float]]]:
    data: dict[int, dict[int, dict[int, float]]] = {}
    if measurements.empty:
        return data

    for row in measurements.itertuples(index=False):
        bid = int(row.building_id)
        year = int(row.year)
        month = int(row.month)
        data.setdefault(bid, {}).setdefault(year, {})[month] = float(row.energia_total_kwh)
    return data
