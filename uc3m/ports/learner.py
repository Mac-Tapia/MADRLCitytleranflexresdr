"""Process-level learner port; adapters own native backend training semantics."""
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, Tuple, runtime_checkable

from uc3m.domain.evidence import ArtifactRef
from uc3m.domain.experiments import ExperimentSpec


@dataclass(frozen=True)
class TrainingResult:
    return_code: int
    completed_episodes: int
    artifacts: Tuple[ArtifactRef, ...]


@runtime_checkable
class LearnerPort(Protocol):
    def execute(self, spec: ExperimentSpec, run_root: Path, resume: bool) -> TrainingResult: ...
