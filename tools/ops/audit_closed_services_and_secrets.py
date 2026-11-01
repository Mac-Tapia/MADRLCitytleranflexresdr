"""Detect repository secrets and required closed services without exposing values."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEXT_SUFFIXES = {
    ".cfg",
    ".ini",
    ".json",
    ".md",
    ".ps1",
    ".py",
    ".rst",
    ".toml",
    ".txt",
    ".yaml",
    ".yml",
}
DOCUMENT_SUFFIXES = {".md", ".rst", ".txt"}
SKIP_DIRS = {
    ".tmp",
    ".git",
    ".pytest_cache",
    ".superpowers",
    "__pycache__",
    "build",
    "dist",
    "htmlcov",
    "node_modules",
    "outputs",
}
SECRET_NAMES = {
    "cookies",
    "credentials.json",
    "local state",
    "storage_state.json",
    "token.json",
}
LEGACY_PREFIXES = (
    "citylearn/",
    "external/",
    "tools/skills/google-drive-mcp/",
    "tools/skills/notebooklm-mcp/",
    "tools/drive/",
    "tools/colab/",
    "tools/thesis/",
)
SERVICE_PATTERNS = (
    ("wandb", re.compile(r"(?:^|\n)\s*(?:import|from)\s+wandb\b|wandb\.init\s*\(")),
    ("notebooklm", re.compile(r"\bnotebooklm\b", re.IGNORECASE)),
    ("google_drive", re.compile(r"\bgoogle\s+drive\b|drive\.google\.com", re.IGNORECASE)),
)


def _relative(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def _path_hash(relative_path: str) -> str:
    return hashlib.sha256(relative_path.encode("utf-8")).hexdigest()


def _is_legacy(relative_path: str) -> bool:
    lowered = relative_path.casefold()
    return lowered.startswith(tuple(prefix.casefold() for prefix in LEGACY_PREFIXES))


def _files(root: Path) -> Iterable[Path]:
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        relative_parts = path.relative_to(root).parts
        if path.relative_to(root).as_posix() == "data/audits/closed_services_and_secrets.json":
            continue
        if any(
            part in SKIP_DIRS or part.startswith(".venv") for part in relative_parts[:-1]
        ):
            continue
        yield path


def _finding(relative_path: str, category: str, kind: str) -> Dict[str, str]:
    return {
        "path": relative_path,
        "path_sha256": _path_hash(relative_path),
        "category": category,
        "kind": kind,
    }


def audit_closed_services(project_root: Path) -> Dict[str, Any]:
    findings: List[Dict[str, str]] = []
    seen = set()

    for path in _files(project_root):
        relative_path = _relative(path, project_root)
        legacy = _is_legacy(relative_path)
        filename = path.name.casefold()
        is_example = ".example." in filename or filename.endswith(".example")

        if filename in SECRET_NAMES and not is_example:
            category = "excluded_legacy" if legacy else "critical"
            key = (relative_path, "secret_file")
            if key not in seen:
                findings.append(_finding(relative_path, category, "secret_file"))
                seen.add(key)

        if path.suffix.casefold() not in TEXT_SUFFIXES or path.stat().st_size > 1_000_000:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for service, pattern in SERVICE_PATTERNS:
            if not pattern.search(text):
                continue
            lowered_path = relative_path.casefold()
            if relative_path == "tools/ops/audit_closed_services_and_secrets.py":
                continue
            if legacy or "drive" in lowered_path or "colab" in lowered_path:
                category = "excluded_legacy"
            elif lowered_path.startswith(("docs/", "tests/")):
                category = "documentation_only"
            elif path.suffix.casefold() in DOCUMENT_SUFFIXES:
                category = "documentation_only"
            else:
                category = "critical"
            key = (relative_path, service)
            if key not in seen:
                findings.append(_finding(relative_path, category, service))
                seen.add(key)

    findings.sort(key=lambda item: (item["path"], item["kind"]))
    return {
        "schema_version": "1.0",
        "ok": not any(item["category"] == "critical" for item in findings),
        "findings": findings,
        "summary": {
            category: sum(item["category"] == category for item in findings)
            for category in ("critical", "excluded_legacy", "documentation_only")
        },
    }


def _parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parse_args(argv)
    manifest = audit_closed_services(PROJECT_ROOT)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
