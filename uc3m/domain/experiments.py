"""Scientific experiment identity independent of runtime timestamps and paths."""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Tuple

from uc3m.domain.scenarios import ScenarioDefinition


HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")
HEX_COMMIT = re.compile(r"^[0-9a-f]{7,64}$")


class RunStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    PARTIAL = "partial"
    VERIFIED = "verified"
    BLOCKED = "blocked"


@dataclass(frozen=True)
class ExperimentSpec:
    algorithm: str
    scenario: ScenarioDefinition
    seed: int
    dataset_sha256: str
    code_commit: str
    submodule_commits: Mapping[str, str]
    target_episodes: int
    episode_time_steps: int = 8760
    source_sha256: str = ''
    backend_args: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.algorithm.strip():
            raise ValueError("algorithm must not be empty")
        if not isinstance(self.seed, int) or isinstance(self.seed, bool) or self.seed < 0:
            raise ValueError("seed must be a non-negative integer")
        if not HEX_SHA256.fullmatch(self.dataset_sha256.casefold()):
            raise ValueError("dataset_sha256 must contain 64 hexadecimal characters")
        if not HEX_COMMIT.fullmatch(self.code_commit.casefold()):
            raise ValueError("code_commit must be a hexadecimal commit identifier")
        normalized_commits = {}
        for path, commit in sorted(self.submodule_commits.items()):
            if not str(path).strip() or not HEX_COMMIT.fullmatch(str(commit).casefold()):
                raise ValueError("submodule commits require a path and hexadecimal commit")
            normalized_commits[str(path)] = str(commit).casefold()
        if self.target_episodes <= 0:
            raise ValueError("target_episodes must be positive")
        if self.episode_time_steps <= 0:
            raise ValueError('episode_time_steps must be positive')
        protected = {'--scenario', '--seed', '--schema-path', '--output-dir',
                     '--episodes', '--epochs', '--episode-time-steps', '--num-env-steps', '--no-resume'}
        if any(str(arg).split('=', 1)[0] in protected for arg in self.backend_args):
            raise ValueError('backend args cannot override protected scientific inputs')
        object.__setattr__(self, 'backend_args', tuple(self.backend_args))
        object.__setattr__(self, "algorithm", self.algorithm.upper())
        object.__setattr__(self, "dataset_sha256", self.dataset_sha256.casefold())
        object.__setattr__(self, "code_commit", self.code_commit.casefold())
        object.__setattr__(
            self, "submodule_commits", MappingProxyType(normalized_commits)
        )

    def as_dict(self) -> Dict[str, object]:
        return {
            "algorithm": self.algorithm,
            "scenario_id": self.scenario.scenario_id,
            "scenario_fingerprint": self.scenario.fingerprint(),
            "seed": self.seed,
            "dataset_sha256": self.dataset_sha256,
            "code_commit": self.code_commit,
            "submodule_commits": dict(self.submodule_commits),
            "target_episodes": self.target_episodes,
            "episode_time_steps": self.episode_time_steps,
            "source_sha256": self.source_sha256,
            "backend_args": list(self.backend_args),
        }

    def fingerprint(self) -> str:
        serialized = json.dumps(
            self.as_dict(), ensure_ascii=True, sort_keys=True, separators=(",", ":")
        ).encode("utf-8")
        return hashlib.sha256(serialized).hexdigest()


@dataclass(frozen=True)
class RunIdentity:
    run_id: str
    experiment_fingerprint: str

    @classmethod
    def from_spec(cls, spec: ExperimentSpec) -> "RunIdentity":
        fingerprint = spec.fingerprint()
        algorithm = re.sub(r"[^a-z0-9]+", "-", spec.algorithm.casefold()).strip("-")
        scenario = re.sub(
            r"[^a-z0-9]+", "-", spec.scenario.scenario_id.casefold()
        ).strip("-")
        return cls(
            run_id=f"{algorithm}-{scenario}-s{spec.seed:03d}-{fingerprint[:12]}",
            experiment_fingerprint=fingerprint,
        )
