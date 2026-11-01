from __future__ import annotations

import re
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCER = PROJECT_ROOT / "tools/dataset/distill_building_loads.py"
CONSUMER = PROJECT_ROOT / "tools/dataset/check_training_dataset_ready.py"
ROOT_JOIN = re.compile(r'ROOT((?:\s*/\s*"[^"]+")+)')


def _report_paths(script: Path) -> set:
    paths = set()
    for chain in ROOT_JOIN.findall(script.read_text(encoding="utf-8")):
        parts = re.findall(r'"([^"]+)"', chain)
        if parts and parts[-1] == "distillation_report.csv":
            paths.add("/".join(parts))
    return paths


def test_distillation_report_has_one_canonical_existing_location() -> None:
    produced = _report_paths(PRODUCER)
    consumed = _report_paths(CONSUMER)

    assert produced == consumed == {"tools/dataset/dataset_docs/distillation_report.csv"}
    assert (PROJECT_ROOT / next(iter(produced))).is_file()
