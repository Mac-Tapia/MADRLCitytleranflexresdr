"""Remove generated dataset files that are not referenced by schema.json.

Files are moved out of the active CityLearn dataset directory into
outputs/dataset_audit/orphaned_dataset_files so they cannot be accidentally
loaded or counted as training inputs. Stale schema backups are also archived
because only the active schema.json should remain in the training dataset.
"""

from __future__ import annotations

import argparse
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET_DIR = ROOT / "CityLearn" / "data" / "datasets" / "citylearn_iquitos_2023_2025"
ARCHIVE_ROOT = ROOT / "outputs" / "dataset_audit" / "orphaned_dataset_files"
LOG_PATH = ROOT / "outputs" / "dataset_audit" / "orphaned_dataset_files_manifest.json"


def _rel(path: Path) -> str:
    try:
        return str(path.resolve().relative_to(ROOT))
    except ValueError:
        return str(path)


def _schema_references(schema_path: Path) -> tuple[set[str], set[str]]:
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    charger_refs: set[str] = set()
    machine_refs: set[str] = set()

    for bdata in (schema.get("buildings") or {}).values():
        for cfg in (bdata.get("chargers") or {}).values():
            sim_name = cfg.get("charger_simulation")
            if sim_name:
                charger_refs.add(str(sim_name))

        for cfg in (bdata.get("washing_machines") or {}).values():
            sim_name = cfg.get("washing_machine_energy_simulation")
            if sim_name:
                machine_refs.add(str(sim_name))

    return charger_refs, machine_refs


def clean_dataset_orphans(dataset_dir: Path, archive_root: Path, dry_run: bool = False) -> dict[str, Any]:
    dataset_dir = dataset_dir.resolve()
    schema_path = dataset_dir / "schema.json"
    if not schema_path.exists():
        raise FileNotFoundError(f"schema.json not found: {schema_path}")

    charger_refs, machine_refs = _schema_references(schema_path)
    charger_files = {path.name: path for path in dataset_dir.glob("charger_*.csv")}
    machine_files = {path.name: path for path in dataset_dir.glob("Washing_Machine_*.csv")}
    stale_schema_files: dict[str, Path] = {}
    for pattern in ("schema*.bak", "schema*.backup", "schema_old*.json", "schema_backup*.json"):
        stale_schema_files.update({path.name: path for path in dataset_dir.glob(pattern) if path.name != "schema.json"})

    orphan_files: dict[str, Path] = {
        name: charger_files[name] for name in sorted(set(charger_files) - charger_refs)
    }
    orphan_files.update({
        name: machine_files[name] for name in sorted(set(machine_files) - machine_refs)
    })
    orphan_files.update(stale_schema_files)

    orphan_names = sorted(orphan_files)
    archive_dir = archive_root / datetime.now().strftime("%Y%m%d_%H%M%S")
    moved: list[dict[str, str]] = []

    for name in orphan_names:
        source = orphan_files[name].resolve()
        if not str(source).lower().startswith(str(dataset_dir).lower()):
            raise RuntimeError(f"Refusing to move path outside dataset: {source}")

        destination = archive_dir / name
        moved.append({"source": _rel(source), "destination": _rel(destination)})

        if not dry_run:
            archive_dir.mkdir(parents=True, exist_ok=True)
            shutil.move(str(source), str(destination))

    missing_chargers = sorted(charger_refs - set(charger_files))
    missing_machines = sorted(machine_refs - set(machine_files))
    result = {
        "dataset_dir": _rel(dataset_dir),
        "archive_dir": _rel(archive_dir),
        "dry_run": dry_run,
        "orphan_count": len(orphan_names),
        "moved": moved,
        "stale_schema_backup_files": sorted(stale_schema_files),
        "missing_charger_refs": missing_chargers,
        "missing_machine_refs": missing_machines,
        "schema_charger_refs": len(charger_refs),
        "schema_machine_refs": len(machine_refs),
        "active_charger_files": len(set(charger_files) - set(orphan_names)),
        "active_machine_files": len(set(machine_files) - set(orphan_names)),
    }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Move unreferenced generated dataset CSV files out of active dataset.")
    parser.add_argument("--dataset-dir", type=Path, default=DATASET_DIR)
    parser.add_argument("--archive-root", type=Path, default=ARCHIVE_ROOT)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    result = clean_dataset_orphans(args.dataset_dir, args.archive_root, dry_run=args.dry_run)
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")

    print(f"Dataset: {result['dataset_dir']}")
    print(f"Orphan files moved: {result['orphan_count']}")
    print(f"Active charger files: {result['active_charger_files']}")
    print(f"Active machine files: {result['active_machine_files']}")
    print(f"Manifest: {_rel(LOG_PATH)}")

    if result["missing_charger_refs"] or result["missing_machine_refs"]:
        print("Missing schema references detected.")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
