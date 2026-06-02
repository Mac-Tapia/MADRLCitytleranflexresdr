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
DEFAULT_BUILDINGS_WITH_MONTHLY_DATA = tuple(range(2, 18))

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
            active_total = punta + fuera_punta
            if active_total <= 0.0:
                continue

            reported_total = parse_decimal(_first_value(row, ("totalenergiaactiva",)), default=0.0)
            records.append({
                "building_id": building_id,
                "year": year,
                "month": month,
                "source_name": row.get(source_col_key, ""),
                "energia_punta_kwh": punta,
                "energia_fuera_punta_kwh": fuera_punta,
                "energia_total_kwh": active_total,
                "energia_reactiva_kvarh": parse_decimal(_first_value(row, ("energiareactiva",))),
                "factor_carga": parse_decimal(_first_value(row, ("factorcarga",))),
                "total_facturado": parse_decimal(_first_value(row, ("totalfacturado",))),
                "reported_total_energia_activa": reported_total,
                "reported_total_delta_kwh": reported_total - active_total if reported_total else 0.0,
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
        "energia_reactiva_kvarh",
        "factor_carga",
        "total_facturado",
        "reported_total_energia_activa",
        "reported_total_delta_kwh",
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
