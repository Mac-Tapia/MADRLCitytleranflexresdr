"""Governance contracts for the local open-source research platform."""

from uc3m.governance.open_source import (
    DependencyRecord,
    OpenSourcePolicy,
    PolicyDecision,
)
from uc3m.governance.foundation import validate_foundation_manifests

__all__ = [
    "DependencyRecord",
    "OpenSourcePolicy",
    "PolicyDecision",
    "validate_foundation_manifests",
]
