"""Fail-closed policy for required software and service dependencies."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Optional, Tuple

import yaml


@dataclass(frozen=True)
class DependencyRecord:
    """Auditable dependency facts supplied by an inventory adapter."""

    name: str
    license_spdx: Optional[str]
    version: Optional[str] = None
    source_url: Optional[str] = None
    requires_payment: bool = False
    requires_saas: bool = False
    required: bool = True


@dataclass(frozen=True)
class PolicyDecision:
    """Decision that never equates review with permission to integrate."""

    status: str
    allowed: bool
    reasons: Tuple[str, ...]


class OpenSourcePolicy:
    """Evaluate dependency facts against an explicit SPDX allowlist."""

    def __init__(
        self,
        *,
        allow: Tuple[str, ...],
        review: Tuple[str, ...],
        block: Tuple[str, ...],
    ) -> None:
        self._allow = frozenset(allow)
        self._review = frozenset(review)
        self._block = frozenset(block)

    @classmethod
    def from_yaml(cls, path: Path) -> "OpenSourcePolicy":
        payload: Mapping[str, Any] = yaml.safe_load(path.read_text(encoding="utf-8"))
        return cls(
            allow=tuple(str(value) for value in payload.get("allow", ())),
            review=tuple(str(value) for value in payload.get("review", ())),
            block=tuple(str(value) for value in payload.get("block", ())),
        )

    def evaluate(self, record: DependencyRecord) -> PolicyDecision:
        reasons = []
        if record.requires_payment:
            reasons.append("payment_required")
        if record.requires_saas:
            reasons.append("saas_required")

        license_spdx = record.license_spdx
        if license_spdx is None or not license_spdx.strip():
            reasons.append("missing_license")
        elif license_spdx == "NOASSERTION":
            reasons.append("unknown_license")
        elif license_spdx.startswith("LicenseRef-Proprietary"):
            reasons.append("proprietary_license")
        elif license_spdx in self._block:
            reasons.append("policy_blocklist")
        elif license_spdx in self._review:
            if reasons:
                return PolicyDecision("block", False, tuple(reasons))
            return PolicyDecision(
                "review", False, ("copyleft_compatibility_review",)
            )
        elif license_spdx not in self._allow:
            reasons.append("license_not_allowlisted")

        if reasons:
            return PolicyDecision("block", False, tuple(reasons))
        return PolicyDecision("allow", True, ())
