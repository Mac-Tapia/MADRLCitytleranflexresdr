from __future__ import annotations

import json
from pathlib import Path

from uc3m.governance.foundation import validate_foundation_manifests


PROJECT_ROOT = Path(__file__).resolve().parents[2]


def test_real_foundation_manifests_preserve_dependency_blockers() -> None:
    result = validate_foundation_manifests(PROJECT_ROOT)

    assert result["schemas_valid"] is True
    assert result["closed_services_ok"] is True
    assert result["dependencies_ok"] is False
    assert result["ready"] is False
    assert result["status"] == "blocked_open_source_dependencies"
    assert result["dependency_blocker_count"] >= 1


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
