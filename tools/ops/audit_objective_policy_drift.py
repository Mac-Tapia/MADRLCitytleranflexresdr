"""Detect obsolete E1-E3 objective vectors without confusing unrelated 0.70 values."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from uc3m.application.configuration import load_scenario_catalog
from uc3m.domain.scenarios import ScenarioCatalog


PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENARIO_CONFIG = PROJECT_ROOT / "configs" / "scenarios.yaml"
TEXT_SUFFIXES = {".json", ".md", ".py", ".ps1", ".toml", ".yaml", ".yml"}
OBSOLETE_PATTERNS = {
    "E1": re.compile(r"\bE1\b[^\n]{0,200}?0\.70[^\n]{0,80}?0\.15[^\n]{0,80}?0\.15", re.IGNORECASE),
    "E2": re.compile(r"\bE2\b[^\n]{0,200}?0\.15[^\n]{0,80}?0\.70[^\n]{0,80}?0\.15", re.IGNORECASE),
    "E3": re.compile(r"\bE3\b[^\n]{0,200}?0\.25[^\n]{0,80}?0\.15[^\n]{0,80}?0\.60", re.IGNORECASE),
}


def _text_files(root: Path) -> Iterable[Path]:
    if not root.exists():
        return ()
    return (
        path
        for path in root.rglob("*")
        if path.is_file() and path.suffix.casefold() in TEXT_SUFFIXES
    )


def _find(root: Path, paths: Iterable[Path], classification: str) -> List[Dict[str, object]]:
    findings: List[Dict[str, object]] = []
    seen: set[Tuple[str, int, str]] = set()
    for path in sorted(set(paths)):
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            continue
        for line_number, line in enumerate(lines, start=1):
            for scenario_id, pattern in OBSOLETE_PATTERNS.items():
                if not pattern.search(line):
                    continue
                relative = path.relative_to(root).as_posix()
                key = (relative, line_number, scenario_id)
                if key in seen:
                    continue
                seen.add(key)
                findings.append(
                    {
                        "path": relative,
                        "line": line_number,
                        "scenario_id": scenario_id,
                        "classification": classification,
                        "reason": "obsolete_objective_vector",
                    }
                )
    return findings


def audit_policy_drift(
    project_root: Path, catalog: ScenarioCatalog
) -> Dict[str, object]:
    """Classify obsolete vectors as blocking, thesis-facing, or historical."""

    project_root = Path(project_root)
    active_files: List[Path] = []
    for relative in ("uc3m", "configs", "scripts", "tools"):
        active_files.extend(_text_files(project_root / relative))

    thesis_files: List[Path] = []
    for relative in ("docs/decisions", "docs/audits"):
        thesis_files.extend(_text_files(project_root / relative))

    legacy_files = list(_text_files(project_root / "data" / "audits"))
    docs_root = project_root / "docs"
    if docs_root.exists():
        legacy_files.extend(docs_root.glob("HISTORIA*"))

    active = _find(project_root, active_files, "active_blocker")
    thesis = _find(project_root, thesis_files, "thesis_review")
    legacy = _find(project_root, legacy_files, "legacy_non_blocking")
    fingerprints: Mapping[str, str] = {
        scenario_id: catalog[scenario_id].objective_policy.fingerprint()
        for scenario_id in catalog
    }
    return {
        "schema_version": "1.0",
        "ok": not active,
        "canonical_policy_fingerprints": dict(fingerprints),
        "active_blockers": active,
        "thesis_findings": thesis,
        "legacy_findings": legacy,
        "excluded_dependencies": ["CityLearn", "external"],
    }


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output",
        type=Path,
        default=PROJECT_ROOT / "data" / "audits" / "objective_policy_drift.json",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    catalog = load_scenario_catalog(SCENARIO_CONFIG)
    report = audit_policy_drift(PROJECT_ROOT, catalog)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
