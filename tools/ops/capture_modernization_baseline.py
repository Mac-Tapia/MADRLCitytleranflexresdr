"""Capture a content-safe, reproducible modernization baseline."""

from __future__ import annotations

import argparse
import hashlib
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping, Sequence


EXPECTED_ROOT = "D:/MADRLCitytleranflexresdr"
EXPECTED_ORIGIN = "https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git"
CANONICAL_FILES = (
    "README.md",
    "pyproject.toml",
    "docs/design/modernizacion.md",
    "docs/plans/modernizacion.md",
)
SOURCE_ROOTS = ("uc3m", "tests", "tools", "configs", "scripts", "governance")
SOURCE_SUFFIXES = frozenset({".py", ".yaml", ".yml", ".toml", ".ps1", ".json", ".cfg", ".ini"})
TEXT_SUFFIXES = SOURCE_SUFFIXES
DEPENDENCY_FILES = ("pyproject.toml", "requirements.txt", "uv.lock")


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
    return _file_hashes(project_root, CANONICAL_FILES)


def _file_hashes(
    project_root: Path, names: Sequence[str]
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for relative_name in names:
        path = project_root / relative_name
        if not path.is_file():
            continue
        payload = path.read_bytes()
        records[relative_name] = {
            "sha256": hashlib.sha256(payload).hexdigest(),
            "size_bytes": len(payload),
        }
    return records


def hash_sources(
    project_root: Path, *, roots: Sequence[str] = SOURCE_ROOTS
) -> dict[str, str]:
    """Hash source/config/test files; text identity normalizes CRLF to LF."""

    digests: dict[str, str] = {}
    for root_name in roots:
        root = project_root / root_name
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix.lower() not in SOURCE_SUFFIXES:
                continue
            if "__pycache__" in path.parts:
                continue
            payload = path.read_bytes()
            if path.suffix.lower() in TEXT_SUFFIXES:
                payload = payload.replace(b"\r\n", b"\n")
            digests[path.relative_to(project_root).as_posix()] = hashlib.sha256(
                payload
            ).hexdigest()
    return digests


def _aggregate_digest(digests: Mapping[str, str]) -> str:
    joined = "".join(
        f"{name}\0{digest}\n" for name, digest in sorted(digests.items())
    )
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


def compare_cut(
    before: Mapping[str, str], after: Mapping[str, str], *, suite_passed: bool
) -> dict[str, object]:
    """An integral suite is accepted only if sources did not change while it ran."""

    changed = sorted(
        name
        for name in set(before) | set(after)
        if before.get(name) != after.get(name)
    )
    stable = not changed
    return {
        "source_state_stable": stable,
        "integral_suite_accepted": bool(stable and suite_passed),
        "changed_paths": changed,
        "source_digest": _aggregate_digest(after),
        "source_file_count": len(after),
    }


def capture_baseline(project_root: Path) -> dict[str, object]:
    """Return repository metadata without reading file contents that may be secrets."""

    root = _normalized_root(project_root)
    if root.casefold() != EXPECTED_ROOT.casefold():
        raise ValueError(f"Unexpected project root: {root}")

    origin = _git(project_root, "remote", "get-url", "origin")
    if origin != EXPECTED_ORIGIN:
        raise ValueError(f"Unexpected origin: {origin}")

    started_at = datetime.now(timezone.utc).isoformat()
    sources_before = hash_sources(project_root)
    status = _git(project_root, "status", "--porcelain=v1", "--untracked-files=all")
    payload: dict[str, object] = {
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
        "dependency_files": _file_hashes(project_root, DEPENDENCY_FILES),
    }
    sources_after = hash_sources(project_root)
    cut = compare_cut(sources_before, sources_after, suite_passed=False)
    payload["sources"] = {
        "roots": list(SOURCE_ROOTS),
        "digest": cut["source_digest"],
        "file_count": cut["source_file_count"],
        "files": sources_after,
        "source_state_stable": cut["source_state_stable"],
        "changed_paths": cut["changed_paths"],
    }
    payload["captured"] = {
        "started_at": started_at,
        "finished_at": datetime.now(timezone.utc).isoformat(),
    }
    return payload


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
