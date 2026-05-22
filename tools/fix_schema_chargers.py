"""
fix_schema_chargers.py
======================
Rebuilds the chargers section of schema.json with exactly 50 correct entries
and removes extra charger CSV files from disk.
"""
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DATASET_DIR = Path(r"d:\MADRLCitytleranflexresdr\CityLearn\data\datasets\citylearn_iquitos_2023_2025")
SCHEMA_PATH = DATASET_DIR / "schema.json"

# Correct charger counts and power per building (from generate_chargers.py CHARGER_CFG)
# Format: bldg_id -> list of charger_kw values (one per charger slot)
CHARGER_POWERS = {
    1:  [7.4, 7.4],                              # 2 camioneta
    2:  [1.0, 1.0, 1.0, 1.0],                   # 4 mototaxi
    3:  [7.4, 7.4, 1.0, 1.0],                   # 2 van + 2 mototaxi
    4:  [1.0, 1.0, 1.0],                         # 3 mototaxi
    5:  [7.4, 1.0, 1.0],                         # 1 van_hotel + 2 mototaxi
    6:  [7.4, 7.4, 7.4, 1.0, 1.0, 1.0, 1.0, 1.0],  # 3 camioneta + 5 mototaxi
    7:  [7.4, 1.0, 1.0],                         # 1 camioneta + 2 mototaxi
    8:  [7.4, 7.4],                              # 2 camioneta_pnp
    9:  [1.0, 1.0],                              # 2 mototaxi
    10: [7.4, 7.4, 7.4],                         # 3 camioneta
    11: [7.4, 7.4, 1.0, 1.0],                   # 2 van_hospital + 2 mototaxi
    12: [7.4, 7.4, 1.0],                         # 2 van_hospital + 1 mototaxi
    13: [1.0, 1.0],                              # 2 mototaxi
    14: [7.4, 7.4],                              # 2 camioneta_portuaria
    15: [1.0, 1.0],                              # 2 mototaxi
    16: [1.0],                                   # 1 mototaxi
    17: [1.0, 1.0],                              # 2 mototaxi
}

assert sum(len(v) for v in CHARGER_POWERS.values()) == 50, "Must be exactly 50 chargers"

def make_charger_entry(bldg_id: int, charger_idx: int, kw: float) -> dict:
    """Build a correct charger schema entry."""
    key = f"charger_{bldg_id}_{charger_idx}"
    is_bidirectional = kw > 1.0  # camioneta/van = bidirectional (V2G capable)
    charger_type = 1 if is_bidirectional else 0
    min_charge = 0.96 if kw >= 7.4 else round(kw * 0.10, 3)
    return {
        key: {
            "type": "citylearn.electric_vehicle_charger.Charger",
            "charger_simulation": f"{key}.csv",
            "autosize": False,
            "attributes": {
                "nominal_power": kw,
                "efficiency": 0.95,
                "charger_type": charger_type,
                "max_charging_power": kw,
                "min_charging_power": min_charge,
                "max_discharging_power": 0.0,
                "min_discharging_power": 0.0,
            }
        }
    }


# ── Load schema ───────────────────────────────────────────────────────────────
with open(SCHEMA_PATH, encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 70)
print("REBUILDING schema.json — chargers section")
print("=" * 70)

total_before = sum(len(b.get('chargers', {})) for b in schema['buildings'].values())
print(f"  Charger entries BEFORE: {total_before}")

# ── Rebuild chargers for each building ────────────────────────────────────────
for bldg_key, bldg_data in schema['buildings'].items():
    # Extract building number from key "Building_N"
    bldg_id = int(bldg_key.split('_')[1])
    powers = CHARGER_POWERS[bldg_id]

    new_chargers = {}
    for i, kw in enumerate(powers, start=1):
        entry = make_charger_entry(bldg_id, i, kw)
        new_chargers.update(entry)

    old_count = len(bldg_data.get('chargers', {}))
    bldg_data['chargers'] = new_chargers
    print(f"  Building_{bldg_id}: {old_count} -> {len(new_chargers)} chargers")

total_after = sum(len(b.get('chargers', {})) for b in schema['buildings'].values())
print(f"\n  Charger entries AFTER: {total_after}")
assert total_after == 50, f"Expected 50, got {total_after}"

# ── Save schema ───────────────────────────────────────────────────────────────
with open(SCHEMA_PATH, 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)
print(f"\n  schema.json saved OK")

# ── Delete extra charger CSV files ────────────────────────────────────────────
print("\n" + "=" * 70)
print("DELETING extra charger CSV files")
print("=" * 70)

deleted = []
kept = []
for csv_path in sorted(DATASET_DIR.glob("charger_*.csv")):
    name = csv_path.stem  # e.g. "charger_1_3"
    parts = name.split('_')
    if len(parts) != 3:
        continue
    bldg_id = int(parts[1])
    charger_idx = int(parts[2])
    correct_count = len(CHARGER_POWERS.get(bldg_id, []))
    if charger_idx > correct_count:
        csv_path.unlink()
        deleted.append(csv_path.name)
    else:
        kept.append(csv_path.name)

print(f"  Kept   : {len(kept)} charger CSV files")
print(f"  Deleted: {len(deleted)} extra charger CSV files")
if deleted:
    for name in deleted:
        print(f"    - {name}")

print("\n  DONE — schema.json has 50 chargers, disk has 50 CSV files")
