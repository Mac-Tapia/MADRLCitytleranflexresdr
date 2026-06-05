"""
Apply a minimal cooling autosize margin to the Iquitos CityLearn schema.

CityLearn autosizes HeatPump.nominal_power from the hourly cooling demand.
Without a margin, a peak demand can be equal to the computed maximum output
within floating-point precision and fail the strict demand limit assertion.
This script keeps autosize enabled and only adds a tiny safety factor.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = PROJECT_ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
SCHEMA_PATH = DATASET_DIR / "schema.json"
SAFETY_FACTOR = 1.000001


def main() -> None:
    with SCHEMA_PATH.open("r", encoding="utf-8") as file:
        schema = json.load(file)

    buildings = schema.get("buildings", {})
    if not isinstance(buildings, dict):
        raise TypeError("schema.json buildings must be a dictionary keyed by Building_X")

    print("=" * 78)
    print("FIX cooling_device autosize margin")
    print(f"  schema: {SCHEMA_PATH.relative_to(PROJECT_ROOT)}")
    print(f"  safety_factor: {SAFETY_FACTOR}")
    print("=" * 78)
    print(f"  {'Building':<12} {'peak_cooling_kWh':>18} {'autosize_factor':>18}")
    print(f"  {'-' * 50}")

    for building_key, building in buildings.items():
        cooling_device = building.setdefault("cooling_device", {})
        cooling_device["type"] = "citylearn.energy_model.HeatPump"
        cooling_device["autosize"] = True
        cooling_device.setdefault("attributes", {})
        autosize_attributes = cooling_device.get("autosize_attributes") or {}
        autosize_attributes["safety_factor"] = SAFETY_FACTOR
        cooling_device["autosize_attributes"] = autosize_attributes

        building_csv = DATASET_DIR / building["energy_simulation"]
        peak = pd.read_csv(building_csv, usecols=["cooling_demand"])["cooling_demand"].max()
        print(f"  {building_key:<12} {peak:>18.6f} {SAFETY_FACTOR:>18.6f}")

    with SCHEMA_PATH.open("w", encoding="utf-8") as file:
        json.dump(schema, file, indent=2, ensure_ascii=False)
        file.write("\n")

    print("=" * 78)
    print("  schema.json actualizado OK")


if __name__ == "__main__":
    main()
