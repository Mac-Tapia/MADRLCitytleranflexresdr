"""Contract validation for the local-first foundation gate."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Mapping


def _load(path: Path) -> Mapping[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_foundation_manifests(project_root: Path) -> Dict[str, Any]:
    audit_dir = project_root / "data/audits"
    try:
        baseline = _load(audit_dir / "modernization_baseline.json")
        dependencies = _load(audit_dir / "open_source_dependency_manifest.json")
        closed = _load(audit_dir / "closed_services_and_secrets.json")
        schemas_valid = all(
            payload.get("schema_version") == "1.0"
            for payload in (baseline, dependencies, closed)
        )
        schemas_valid = schemas_valid and all(
            key in baseline
            for key in ("repository", "working_tree", "submodules", "canonical_files")
        )
        schemas_valid = schemas_valid and all(
            key in dependencies
            for key in ("packages", "submodules", "research_repositories", "blockers")
        )
        schemas_valid = schemas_valid and all(
            key in closed for key in ("findings", "summary")
        )
    except (FileNotFoundError, json.JSONDecodeError, TypeError, AttributeError):
        return {
            "schemas_valid": False,
            "closed_services_ok": False,
            "dependencies_ok": False,
            "dependency_blocker_count": 0,
            "accepted_exception_count": 0,
            "ready": False,
            "status": "invalid_or_missing_manifest",
        }

    critical_count = sum(
        finding.get("category") == "critical" for finding in closed["findings"]
    )
    closed_services_ok = bool(closed.get("ok")) and critical_count == 0
    blocker_count = len(dependencies["blockers"])
    exception_count = len(dependencies.get("accepted_exceptions") or [])
    dependencies_ok = bool(dependencies.get("ok")) and blocker_count == 0
    ready = schemas_valid and closed_services_ok and dependencies_ok

    if not schemas_valid:
        status = "invalid_or_missing_manifest"
    elif not closed_services_ok:
        status = "blocked_closed_services_or_secrets"
    elif not dependencies_ok:
        status = "blocked_open_source_dependencies"
    elif exception_count:
        # An owner-accepted exception is not a verified open-source license.
        status = "verified_with_exceptions"
    else:
        status = "verified"

    return {
        "schemas_valid": schemas_valid,
        "closed_services_ok": closed_services_ok,
        "dependencies_ok": dependencies_ok,
        "dependency_blocker_count": blocker_count,
        "accepted_exception_count": exception_count,
        "ready": ready,
        "status": status,
    }
