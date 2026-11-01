from __future__ import annotations

from pathlib import Path

import pytest

from uc3m.governance.open_source import DependencyRecord, OpenSourcePolicy


POLICY_PATH = Path(__file__).resolve().parents[3] / "governance/open_source_policy.yaml"


@pytest.mark.parametrize(
    "license_spdx",
    ["MIT", "Apache-2.0", "BSD-2-Clause", "BSD-3-Clause"],
)
def test_permissive_osi_licenses_are_allowed(license_spdx: str) -> None:
    policy = OpenSourcePolicy.from_yaml(POLICY_PATH)

    decision = policy.evaluate(
        DependencyRecord(name="candidate", license_spdx=license_spdx)
    )

    assert decision.status == "allow"
    assert decision.allowed is True
    assert decision.reasons == ()


@pytest.mark.parametrize(
    "license_spdx", ["GPL-3.0-only", "AGPL-3.0-only", "EUPL-1.1"]
)
def test_copyleft_licenses_require_compatibility_review(license_spdx: str) -> None:
    policy = OpenSourcePolicy.from_yaml(POLICY_PATH)

    decision = policy.evaluate(
        DependencyRecord(name="candidate", license_spdx=license_spdx)
    )

    assert decision.status == "review"
    assert decision.allowed is False
    assert "copyleft_compatibility_review" in decision.reasons


@pytest.mark.parametrize(
    "record,reason",
    [
        (DependencyRecord(name="missing", license_spdx=None), "missing_license"),
        (
            DependencyRecord(name="unknown", license_spdx="NOASSERTION"),
            "unknown_license",
        ),
        (
            DependencyRecord(
                name="proprietary", license_spdx="LicenseRef-Proprietary"
            ),
            "proprietary_license",
        ),
        (
            DependencyRecord(
                name="paid", license_spdx="MIT", requires_payment=True
            ),
            "payment_required",
        ),
        (
            DependencyRecord(name="saas", license_spdx="MIT", requires_saas=True),
            "saas_required",
        ),
    ],
)
def test_closed_or_unverifiable_dependencies_are_blocked(
    record: DependencyRecord, reason: str
) -> None:
    policy = OpenSourcePolicy.from_yaml(POLICY_PATH)

    decision = policy.evaluate(record)

    assert decision.status == "block"
    assert decision.allowed is False
    assert reason in decision.reasons


def test_unknown_spdx_identifier_fails_closed() -> None:
    policy = OpenSourcePolicy.from_yaml(POLICY_PATH)

    decision = policy.evaluate(
        DependencyRecord(name="mystery", license_spdx="Future-License-9.9")
    )

    assert decision.status == "block"
    assert decision.reasons == ("license_not_allowlisted",)
