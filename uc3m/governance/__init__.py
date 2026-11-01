"""Governance contracts for the local open-source research platform."""

from uc3m.governance.open_source import (
    DependencyRecord,
    OpenSourcePolicy,
    PolicyDecision,
    classify_license_text,
)
from uc3m.governance.foundation import validate_foundation_manifests

__all__ = [
    "DependencyRecord",
    "OpenSourcePolicy",
    "PolicyDecision",
    "classify_license_text",
    "validate_foundation_manifests",
]
