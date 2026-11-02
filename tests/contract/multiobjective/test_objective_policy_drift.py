from __future__ import annotations

from pathlib import Path

from tools.ops.audit_objective_policy_drift import audit_policy_drift
from uc3m.application.configuration import load_scenario_catalog


PROJECT_ROOT = Path(__file__).resolve().parents[3]


def test_policy_drift_classifies_active_thesis_and_legacy_sources(tmp_path: Path) -> None:
    (tmp_path / "uc3m").mkdir()
    (tmp_path / "uc3m" / "active.py").write_text(
        'E1 = [0.70, 0.15, 0.15]\n', encoding="utf-8"
    )
    (tmp_path / "docs" / "decisions").mkdir(parents=True)
    (tmp_path / "docs" / "decisions" / "method.md").write_text(
        "| E2 | 0.15 | 0.70 | 0.15 |\n", encoding="utf-8"
    )
    (tmp_path / "docs").mkdir(exist_ok=True)
    (tmp_path / "docs" / "historia.md").write_text(
        "E3 = (0.25, 0.15, 0.60)\n", encoding="utf-8"
    )
    (tmp_path / "data" / "audits").mkdir(parents=True)
    (tmp_path / "data" / "audits" / "old.json").write_text(
        '{"E1": [0.70, 0.15, 0.15]}\n', encoding="utf-8"
    )

    catalog = load_scenario_catalog(PROJECT_ROOT / "configs" / "scenarios.yaml")
    report = audit_policy_drift(tmp_path, catalog)

    assert report["ok"] is False
    assert [item["path"] for item in report["active_blockers"]] == [
        "uc3m/active.py"
    ]
    assert [item["path"] for item in report["thesis_findings"]] == [
        "docs/decisions/method.md"
    ]
    assert {item["path"] for item in report["legacy_findings"]} == {
        "data/audits/old.json",
        "docs/historia.md",
    }


def test_real_canonical_config_has_no_active_policy_drift() -> None:
    catalog = load_scenario_catalog(PROJECT_ROOT / "configs" / "scenarios.yaml")
    report = audit_policy_drift(PROJECT_ROOT, catalog)

    assert all(
        finding["path"] not in {"configs/objective_policies.yaml", "configs/scenarios.yaml"}
        for finding in report["active_blockers"]
    )
