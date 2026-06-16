"""Synchronize controlled shiftable machine datasets for all Iquitos buildings."""

from __future__ import annotations

import json
import sys
from pathlib import Path


sys.path.insert(0, str(Path(__file__).resolve().parent))

from generate_iquitos_dataset import (  # noqa: E402
    MADRL_BUILDING_CONSTANTS,
    N_HOURS_TOTAL,
    SupportFilesGenerator,
)


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
SCHEMA_PATH = DATASET_DIR / "schema.json"
LOG_PATH = DATASET_DIR / "controlled_machines_log.json"


def sync_controlled_machines(dataset_dir: Path = DATASET_DIR, schema_path: Path = SCHEMA_PATH) -> dict:
    generator = SupportFilesGenerator()
    rows = []

    for bldg_id in sorted(MADRL_BUILDING_CONSTANTS):
        df = generator.build_washing_machine(N_HOURS_TOTAL, bldg_id)
        filename = f"Washing_Machine_{bldg_id}.csv"
        df.to_csv(dataset_dir / filename, index=False)

        active = df["wm_start_time_step"].astype(int).ge(0)
        potential_kwh = 0.0
        seen_starts: set[int] = set()
        for _, row in df[active].iterrows():
            start = int(row["wm_start_time_step"])
            if start in seen_starts:
                continue
            seen_starts.add(start)
            try:
                profile = [float(x) for x in str(row["load_profile"]).strip("[]").split(",")]
            except Exception:
                profile = []
            potential_kwh += sum(profile)

        cfg = MADRL_BUILDING_CONSTANTS[bldg_id]
        rows.append({
            "building_id": bldg_id,
            "file": filename,
            "building_type": cfg["bldg_type"],
            "shiftable_cycle_kwh": float(cfg.get("shiftable", 0.0)),
            "active_window_rows": int(active.sum()),
            "potential_cycles": len(seen_starts),
            "potential_energy_kwh": round(potential_kwh, 6),
        })

    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    for bldg_id in sorted(MADRL_BUILDING_CONSTANTS):
        bkey = f"Building_{bldg_id}"
        schema["buildings"][bkey]["washing_machines"] = {
            f"washing_machine_{bldg_id}": {
                "type": "citylearn.energy_model.WashingMachine",
                "autosize": False,
                "washing_machine_energy_simulation": f"Washing_Machine_{bldg_id}.csv",
            }
        }
    schema_path.write_text(json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8")

    log = {
        "dataset_dir": str(dataset_dir.relative_to(ROOT)),
        "schema": str(schema_path.relative_to(ROOT)),
        "rule": (
            "One controlled shiftable load per building through CityLearn WashingMachine API. "
            "Cycle energy uses the supplied MADRL_BUILDING_CONSTANTS[building].shiftable value; "
            "operating windows follow building type."
        ),
        "rows": rows,
    }
    LOG_PATH.write_text(json.dumps(log, indent=2, ensure_ascii=False), encoding="utf-8")
    return log


def main() -> int:
    log = sync_controlled_machines()
    total_energy = sum(float(row["potential_energy_kwh"]) for row in log["rows"])
    print(f"Schema actualizado: {SCHEMA_PATH}")
    print(f"CSV cargas controladas: {len(log['rows'])}")
    print(f"Energia potencial controlada: {total_energy / 1000.0:.3f} MWh")
    print(f"Log: {LOG_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
