"""Pure scientific domain contracts independent of simulators and backends."""

from uc3m.domain.objectives import (
    HierarchyLevels,
    ObjectiveAxis,
    ObjectivePolicy,
    RewardVector,
    canonical_objective_policies,
)
from uc3m.domain.scenarios import (
    ConstraintPolicy,
    ScenarioCatalog,
    ScenarioDefinition,
    TariffPolicy,
)
from uc3m.domain.pareto import (
    dominates,
    expected_utility,
    hypervolume_3d,
    non_dominated_indices,
    sparsity,
)
from uc3m.domain.experiments import ExperimentSpec, RunIdentity, RunStatus
from uc3m.domain.evidence import ArtifactRef, EvidenceManifest, verify_artifact

__all__ = [
    "HierarchyLevels",
    "ObjectiveAxis",
    "ObjectivePolicy",
    "RewardVector",
    "canonical_objective_policies",
    "ConstraintPolicy",
    "ScenarioCatalog",
    "ScenarioDefinition",
    "TariffPolicy",
    "dominates",
    "expected_utility",
    "hypervolume_3d",
    "non_dominated_indices",
    "sparsity",
    "ExperimentSpec",
    "RunIdentity",
    "RunStatus",
    "ArtifactRef",
    "EvidenceManifest",
    "verify_artifact",
]
