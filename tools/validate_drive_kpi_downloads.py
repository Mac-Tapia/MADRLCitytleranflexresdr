#!/usr/bin/env python3
"""Validate KPI exports under outputs/_drive_madrl/kpis match filename algo/scenario."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
DEFAULT_KPIS_DIR = REPO / "outputs" / "_drive_madrl" / "kpis"
ALGOS = ("happo", "masac", "matd3", "maac")
SCENARIOS = ("E1", "E2", "E3")
STEM_RE = re.compile(r"^(?P<algo>[a-z][a-z0-9]*)_(?P<scen>E[123])_(?P<kind>.+)$", re.IGNORECASE)


def _parse_export_stem(path: Path) -> tuple[str, str, str] | None:
    match = STEM_RE.match(path.stem)
    if not match:
        return None
    return match.group("algo").lower(), match.group("scen").upper(), match.group("kind")


def validate_results_json(path: Path) -> dict:
    parsed = _parse_export_stem(path)
    if not parsed:
        return {"path": str(path), "ok": False, "detail": "unrecognized filename pattern"}
    file_algo, file_scen, _kind = parsed
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        return {"path": str(path), "ok": False, "detail": f"invalid json: {exc}"}

    payload_algo = str(payload.get("algorithm") or "").lower()
    payload_scen = str(payload.get("scenario") or "").upper()
    output_dir = str(payload.get("output_dir") or "").rstrip("/")

    mismatches: list[str] = []
    if payload_algo and payload_algo != file_algo:
        mismatches.append(f"filename algo={file_algo} vs payload.algorithm={payload_algo}")
    if payload_scen and payload_scen != file_scen:
        mismatches.append(f"filename scenario={file_scen} vs payload.scenario={payload_scen}")
    if output_dir and not output_dir.endswith(f"/{file_scen}"):
        mismatches.append(f"output_dir does not end with /{file_scen}: {output_dir}")

    has_kpis = bool((payload.get("citylearn_v3_report") or {}).get("all_values"))
    recorded = payload.get("episodes_recorded")
    resume_slice = payload.get("episodes")

    return {
        "path": str(path),
        "file_algo": file_algo,
        "file_scenario": file_scen,
        "payload_scenario": payload_scen or None,
        "output_dir": output_dir or None,
        "episodes_recorded": recorded,
        "resume_slice_episodes": resume_slice,
        "has_audited_kpis": has_kpis,
        "ok": not mismatches,
        "mismatches": mismatches,
    }


def missing_exports(kpis_dir: Path) -> list[dict]:
    missing: list[dict] = []
    for algo in ALGOS:
        for scen in SCENARIOS:
            results_path = kpis_dir / f"{algo}_{scen}_results.json"
            if results_path.is_file():
                row = validate_results_json(results_path)
                if row.get("ok"):
                    continue
                missing.append(
                    {
                        "algorithm": algo.upper(),
                        "scenario": scen,
                        "issue": "mislabeled or invalid export",
                        "path": str(results_path),
                        "mismatches": row.get("mismatches"),
                    }
                )
            else:
                missing.append(
                    {
                        "algorithm": algo.upper(),
                        "scenario": scen,
                        "issue": "results.json not downloaded",
                        "expected": str(results_path),
                    }
                )
    return missing


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--kpis-dir",
        type=Path,
        default=DEFAULT_KPIS_DIR,
        help=f"KPI export folder (default: {DEFAULT_KPIS_DIR})",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable report")
    args = parser.parse_args()

    kpis_dir = args.kpis_dir.resolve()
    if not kpis_dir.is_dir():
        print(f"ERROR: not a directory: {kpis_dir}", file=sys.stderr)
        return 2

    rows = [validate_results_json(p) for p in sorted(kpis_dir.glob("*_results.json"))]
    bad = [r for r in rows if not r.get("ok")]
    missing = missing_exports(kpis_dir)

    summary = {
        "kpis_dir": str(kpis_dir),
        "results_exports": len(rows),
        "valid_exports": len(rows) - len(bad),
        "mislabeled_exports": bad,
        "missing_or_invalid_jobs": missing,
        "drive_conclusion": {
            "complete_e1_e2": ["MATD3", "MAAC", "MASAC"],
            "complete_e3": ["MATD3"],
            "incomplete": ["HAPPO (49/50 ep, no KPIs)", "MAAC E3", "MASAC E3"],
            "redownload_hint": (
                "From Drive .../MAAC/E3/data/results.json save as maac_E3_results.json; "
                "same for MASAC/E3 -> masac_E3_results.json. Verify output_dir ends with /E3."
            ),
        },
    }

    if args.json:
        print(json.dumps(summary, indent=2, ensure_ascii=False))
    else:
        print(f"KPI dir: {kpis_dir}")
        print(f"Valid exports: {summary['valid_exports']}/{summary['results_exports']}")
        for row in bad:
            print(f"  MISLABELED {Path(row['path']).name}:")
            for m in row.get("mismatches") or []:
                print(f"    - {m}")
            if not row.get("mismatches") and row.get("detail"):
                print(f"    - {row['detail']}")
        if missing:
            print("Missing or invalid jobs:")
            for item in missing:
                print(f"  - {item['algorithm']}/{item['scenario']}: {item['issue']}")
                if item.get("expected"):
                    print(f"      expected: {item['expected']}")
                if item.get("mismatches"):
                    for m in item["mismatches"]:
                        print(f"      {m}")

    return 0 if not bad and not missing else 1


if __name__ == "__main__":
    raise SystemExit(main())
