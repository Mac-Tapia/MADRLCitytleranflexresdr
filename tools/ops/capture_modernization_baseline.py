"""Capture a content-safe, reproducible modernization baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any, Sequence


EXPECTED_ROOT = "D:/MADRLCitytleranflexresdr"
EXPECTED_ORIGIN = "https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git"
CANONICAL_FILES = (
    "README.md",
    "pyproject.toml",
    "docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md",
    "docs/superpowers/plans/2026-10-31-modernizacion-integral-master-plan.md",
)


def _git(project_root: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=project_root,
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return completed.stdout.strip()


def _normalized_root(path: Path) -> str:
    return path.resolve().as_posix().rstrip("/")


def _working_tree_counts(status_text: str) -> dict[str, int]:
    counts = {
        "tracked_modified": 0,
        "tracked_deleted": 0,
        "tracked_added": 0,
        "untracked": 0,
        "renamed": 0,
        "conflicted": 0,
        "total": 0,
    }
    for line in status_text.splitlines():
        if not line:
            continue
        counts["total"] += 1
        code = line[:2]
        if code == "??":
            counts["untracked"] += 1
        elif "U" in code or code in {"AA", "DD"}:
            counts["conflicted"] += 1
        elif "R" in code:
            counts["renamed"] += 1
        elif "A" in code:
            counts["tracked_added"] += 1
        elif "D" in code:
            counts["tracked_deleted"] += 1
        else:
            counts["tracked_modified"] += 1
    return counts


def _submodules(project_root: Path) -> list[dict[str, str]]:
    text = _git(project_root, "submodule", "status", "--recursive")
    records: list[dict[str, str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        fields = stripped.lstrip("-+U").split()
        if len(fields) < 2:
            continue
        records.append(
            {
                "path": Path(fields[1]).as_posix(),
                "commit": fields[0].lower(),
                "state": line[0] if line[0] in "-+U " else " ",
            }
        )
    return sorted(records, key=lambda record: record["path"])


def _canonical_hashes(project_root: Path) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for relative_name in CANONICAL_FILES:
        path = project_root / relative_name
        if not path.is_file():
            continue
        payload = path.read_bytes()
        records[relative_name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        }
    return records


def capture_baseline(project_root: Path) -> dict[str, object]:
    """Return repository metadata without reading file contents that may be secrets."""

    root = _normalized_root(project_root)
    if root.casefold() != EXPECTED_ROOT.casefold():
        raise ValueError(f"Unexpected project root: {root}")

    origin = _git(project_root, "remote", "get-url", "origin")
    if origin != EXPECTED_ORIGIN:
        raise ValueError(f"Unexpected origin: {origin}")

    status = _git(project_root, "status", "--porcelain=v1", "--untracked-files=all")
    return {
        "schema_version": "1.0",
        "repository": {
            "root": EXPECTED_ROOT,
            "origin": origin,
            "branch": _git(project_root, "branch", "--show-current"),
            "head_commit": _git(project_root, "rev-parse", "HEAD"),
        },
        "working_tree": _working_tree_counts(status),
        "submodules": _submodules(project_root),
        "canonical_files": _canonical_hashes(project_root),
    }


def _parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = _parse_args(argv)
    project_root = Path(__file__).resolve().parents[2]
    payload = capture_baseline(project_root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
