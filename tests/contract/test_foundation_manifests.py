from __future__ import annotations

import json
from pathlib import Path

from uc3m.governance.foundation import validate_foundation_manifests


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_real_foundation_manifests_report_owner_accepted_license_exceptions() -> None:
    # HARL, MARL and MATD3implementation have no upstream license; the owner
    # accepted a scoped, expiring exception (governance/open_source_policy.yaml).
    result = validate_foundation_manifests(PROJECT_ROOT)

    assert result["schemas_valid"] is True
    assert result["closed_services_ok"] is True
    assert result["dependencies_ok"] is True
    assert result["dependency_blocker_count"] == 0
    assert result["accepted_exception_count"] == 3
    assert result["status"] == "verified_with_exceptions"


def _write_manifests(tmp_path: Path, dependencies: dict) -> None:
    audit_dir = tmp_path / "data/audits"
    audit_dir.mkdir(parents=True)
    (audit_dir / "modernization_baseline.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "repository": {},
                "working_tree": {},
                "submodules": [],
                "canonical_files": {},
            }
        ),
        encoding="utf-8",
    )
    base = {"schema_version": "1.0", "packages": [], "submodules": [], "research_repositories": []}
    (audit_dir / "open_source_dependency_manifest.json").write_text(
        json.dumps({**base, **dependencies}), encoding="utf-8"
    )
    (audit_dir / "closed_services_and_secrets.json").write_text(
        json.dumps({"schema_version": "1.0", "ok": True, "findings": [], "summary": {}}),
        encoding="utf-8",
    )


def test_accepted_exceptions_never_report_plain_verified(tmp_path: Path) -> None:
    _write_manifests(
        tmp_path,
        {"ok": True, "blockers": [], "accepted_exceptions": [{"name": "external/backend"}]},
    )

    result = validate_foundation_manifests(tmp_path)

    assert result["ready"] is True
    assert result["accepted_exception_count"] == 1
    assert result["status"] == "verified_with_exceptions"


def test_no_exceptions_and_no_blockers_is_verified(tmp_path: Path) -> None:
    _write_manifests(tmp_path, {"ok": True, "blockers": []})

    result = validate_foundation_manifests(tmp_path)

    assert result["accepted_exception_count"] == 0
    assert result["status"] == "verified"


def test_foundation_rejects_manifest_that_claims_ok_with_critical_findings(
    tmp_path: Path,
) -> None:
    audit_dir = tmp_path / "data/audits"
    audit_dir.mkdir(parents=True)
    (audit_dir / "modernization_baseline.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "repository": {"root": "D:/MADRLCitytleranflexresdr"},
                "working_tree": {"total": 0},
                "submodules": [],
                "canonical_files": {},
            }
        ),
        encoding="utf-8",
    )
    (audit_dir / "open_source_dependency_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "ok": True,
                "packages": [],
                "submodules": [],
                "research_repositories": [],
                "blockers": [],
            }
        ),
        encoding="utf-8",
    )
    (audit_dir / "closed_services_and_secrets.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "ok": True,
                "findings": [
                    {
                        "path": "runtime.py",
                        "path_sha256": "a" * 64,
                        "category": "critical",
                        "kind": "wandb",
                    }
                ],
                "summary": {
                    "critical": 1,
                    "excluded_legacy": 0,
                    "documentation_only": 0,
                },
            }
        ),
        encoding="utf-8",
    )

    result = validate_foundation_manifests(tmp_path)

    assert result["schemas_valid"] is True
    assert result["closed_services_ok"] is False
    assert result["ready"] is False
    assert result["status"] == "blocked_closed_services_or_secrets"
