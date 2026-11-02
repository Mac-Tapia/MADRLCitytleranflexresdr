"""Identity of a fresh campaign, its treatments and their attempts.

A treatment (stage, algorithm, scenario, seed and the resolved inputs it is
trained on) never changes when it is retried: a retry is a new attempt that
starts at episode zero and never concatenates the trajectory of another one.
"""

from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Dict, Mapping, Optional, Tuple

SCHEMA_VERSION = 1
ALGORITHMS = ("HAPPO", "MASAC", "MATD3", "MAAC")
SCENARIOS = ("E1", "E2", "E3")
STAGES = ("pilot", "hpo", "confirm", "sensitivity")
CAMPAIGN_ID = re.compile(r"^[a-z][a-z0-9_]*_v[0-9]+$")
ATTEMPT_ID = re.compile(r"^a[0-9]{3}$")
HEX_SHA256 = re.compile(r"^[0-9a-f]{64}$")


def canonical_hash(payload: object) -> str:
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def _require_sha256(value: str, name: str) -> str:
    if not isinstance(value, str) or not HEX_SHA256.fullmatch(value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hex digest")
    return value


def _freeze(mapping: Mapping) -> Mapping:
    return MappingProxyType({key: (_freeze(value) if isinstance(value, Mapping) else value)
                             for key, value in mapping.items()})


def _thaw(value):
    if isinstance(value, Mapping):
        return {key: _thaw(item) for key, item in value.items()}
    if isinstance(value, tuple):
        return [_thaw(item) for item in value]
    return value


class CampaignStatus(str, Enum):
    PLANNED = "planned"
    REPOSITORY_LAYOUT_VERIFIED = "repository_layout_verified"
    DATASET_VERIFIED = "dataset_verified"
    IMPLEMENTATION_VERIFIED = "implementation_verified"
    LEARNING_VERIFIED = "learning_verified"
    TRAINING_COMPLETE = "training_complete"
    EVALUATION_COMPLETE = "evaluation_complete"
    SCIENTIFIC_ACCEPTANCE = "scientific_acceptance"


@dataclass(frozen=True)
class CampaignSpec:
    campaign_id: str
    algorithms: Tuple[str, ...]
    scenarios: Tuple[str, ...]
    development_seeds: Tuple[int, ...]
    confirmatory_seeds: Tuple[int, ...]
    stage_budgets: Mapping[str, Mapping[str, object]]
    split_ids: Tuple[str, ...]
    policy_hash: str
    resource_authorization: Mapping[str, object] = field(default_factory=dict)
    storage_alias: Optional[str] = None

    def __post_init__(self) -> None:
        if not CAMPAIGN_ID.fullmatch(self.campaign_id):
            raise ValueError("campaign_id must look like <name>_v<N> in lowercase")
        algorithms = tuple(str(a).upper() for a in self.algorithms)
        if not algorithms or len(set(algorithms)) != len(algorithms) or set(algorithms) - set(ALGORITHMS):
            raise ValueError(f"algorithms must be distinct members of {ALGORITHMS}")
        scenarios = tuple(self.scenarios)
        if not scenarios or len(set(scenarios)) != len(scenarios) or set(scenarios) - set(SCENARIOS):
            raise ValueError(f"scenarios must be distinct members of {SCENARIOS}")
        for name in ("development_seeds", "confirmatory_seeds"):
            seeds = tuple(getattr(self, name))
            if not seeds or len(set(seeds)) != len(seeds) or any(
                    isinstance(s, bool) or not isinstance(s, int) or s < 0 for s in seeds):
                raise ValueError(f"{name} must be distinct non-negative integers")
            object.__setattr__(self, name, seeds)
        if set(self.development_seeds) & set(self.confirmatory_seeds):
            raise ValueError("development and confirmatory seeds must be disjoint")
        if set(self.stage_budgets) - set(STAGES):
            raise ValueError(f"stage_budgets keys must be members of {STAGES}")
        if len(self.split_ids) != 3 or len(set(self.split_ids)) != 3:
            raise ValueError("split_ids must name three distinct splits (train, validation, test)")
        _require_sha256(self.policy_hash, "policy_hash")
        object.__setattr__(self, "algorithms", algorithms)
        object.__setattr__(self, "scenarios", scenarios)
        object.__setattr__(self, "split_ids", tuple(self.split_ids))
        object.__setattr__(self, "stage_budgets", _freeze(self.stage_budgets))
        object.__setattr__(self, "resource_authorization", _freeze(self.resource_authorization))

    def as_dict(self) -> Dict[str, object]:
        return {
            "schema_version": SCHEMA_VERSION,
            "campaign_id": self.campaign_id,
            "algorithms": list(self.algorithms),
            "scenarios": list(self.scenarios),
            "development_seeds": list(self.development_seeds),
            "confirmatory_seeds": list(self.confirmatory_seeds),
            "stage_budgets": _thaw(self.stage_budgets),
            "split_ids": list(self.split_ids),
            "policy_hash": self.policy_hash,
            "resource_authorization": _thaw(self.resource_authorization),
            "storage_alias": self.storage_alias,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "CampaignSpec":
        if payload.get("schema_version", SCHEMA_VERSION) != SCHEMA_VERSION:
            raise ValueError("unsupported campaign schema_version")
        return cls(payload["campaign_id"], tuple(payload["algorithms"]), tuple(payload["scenarios"]),
                   tuple(payload["development_seeds"]), tuple(payload["confirmatory_seeds"]),
                   dict(payload["stage_budgets"]), tuple(payload["split_ids"]),
                   payload["policy_hash"], dict(payload.get("resource_authorization", {})),
                   payload.get('storage_alias'))

    def spec_hash(self) -> str:
        identity = self.as_dict()
        identity.pop('storage_alias')
        return canonical_hash(identity)

    def stage_authorized(self, stage: str) -> bool:
        return stage in tuple(self.resource_authorization.get("authorized_stages", ()))


@dataclass(frozen=True)
class TreatmentKey:
    """Everything that defines what a treatment learns from; retries share it."""

    campaign_id: str
    stage: str
    algorithm: str
    scenario: str
    seed: int
    resolved_config_hash: str
    observation_action_contract_hash: str
    normalizer_hash: str
    dataset_hash: str
    source_hash: str

    def __post_init__(self) -> None:
        if self.stage not in STAGES:
            raise ValueError(f"stage must be one of {STAGES}")
        if self.algorithm not in ALGORITHMS or self.scenario not in SCENARIOS:
            raise ValueError("unknown algorithm or scenario")
        for name in ("resolved_config_hash", "observation_action_contract_hash",
                     "normalizer_hash", "dataset_hash", "source_hash"):
            _require_sha256(getattr(self, name), name)

    def as_dict(self) -> Dict[str, object]:
        return {name: getattr(self, name) for name in self.__dataclass_fields__}

    def fingerprint(self) -> str:
        return canonical_hash(self.as_dict())

    @property
    def treatment_id(self) -> str:
        return (f"{self.algorithm.lower()}-{self.scenario.lower()}-s{self.seed}-"
                f"{self.fingerprint()[:12]}")


@dataclass(frozen=True)
class AttemptIdentity:
    treatment_id: str
    attempt_id: str
    seed: int
    initial_episode: int = 0
    fresh_start: bool = True

    def __post_init__(self) -> None:
        if not ATTEMPT_ID.fullmatch(self.attempt_id):
            raise ValueError("attempt_id must look like a001")
        if self.initial_episode != 0 or self.fresh_start is not True:
            raise ValueError("a fresh attempt always starts at episode zero from a new state")

    def as_dict(self) -> Dict[str, object]:
        return {"treatment_id": self.treatment_id, "attempt_id": self.attempt_id, "seed": self.seed,
                "initial_episode": self.initial_episode, "fresh_start": self.fresh_start}


@dataclass(frozen=True)
class CampaignManifest:
    spec: CampaignSpec
    spec_hash: str
    source_hash: str
    data_manifest_path: str
    artifact_root: str
    stage_manifests: Mapping[str, str]
    status: CampaignStatus = CampaignStatus.PLANNED

    def __post_init__(self) -> None:
        if self.spec_hash != self.spec.spec_hash():
            raise ValueError("spec_hash does not match the campaign spec")
        _require_sha256(self.source_hash, "source_hash")
        object.__setattr__(self, "status", CampaignStatus(self.status))
        object.__setattr__(self, "stage_manifests", _freeze(self.stage_manifests))

    def as_dict(self) -> Dict[str, object]:
        return {"schema_version": SCHEMA_VERSION, "spec": self.spec.as_dict(),
                "spec_hash": self.spec_hash, "source_hash": self.source_hash,
                "data_manifest_path": self.data_manifest_path, "artifact_root": self.artifact_root,
                "stage_manifests": dict(self.stage_manifests), "status": self.status.value}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "CampaignManifest":
        return cls(CampaignSpec.from_dict(payload["spec"]), payload["spec_hash"], payload["source_hash"],
                   payload["data_manifest_path"], payload["artifact_root"],
                   dict(payload.get("stage_manifests", {})), payload.get("status", "planned"))


@dataclass(frozen=True)
class ConfigurationFreeze:
    """One algorithm's configuration, selected on validation and reused unchanged.

    ``config_hash`` binds the algorithm and the frozen hyperparameters: a freeze
    whose hash does not match its own values, or that carries no values, is
    rejected, so a confirmatory stage can never run on native defaults.
    """

    campaign_id: str
    algorithm: str
    config_hash: str
    validation_manifest_hashes: Tuple[str, ...]
    selection_rule: str
    frozen_at: str
    candidates: Tuple[str, ...] = ()
    reason: str = ""
    hyperparameters: Mapping[str, float] = field(default_factory=dict)

    @staticmethod
    def config_hash_for(algorithm: str, hyperparameters: Mapping[str, float]) -> str:
        return canonical_hash({"algorithm": algorithm,
                               "hyperparameters": {k: hyperparameters[k] for k in sorted(hyperparameters)}})

    def __post_init__(self) -> None:
        if self.algorithm not in ALGORITHMS:
            raise ValueError("unknown algorithm")
        _require_sha256(self.config_hash, "config_hash")
        if not self.validation_manifest_hashes:
            raise ValueError("a freeze requires the validation evidence it was selected on")
        for value in self.validation_manifest_hashes:
            _require_sha256(value, "validation_manifest_hashes")
        if not self.hyperparameters:
            raise ValueError("a freeze must carry the hyperparameters it freezes")
        if self.config_hash != self.config_hash_for(self.algorithm, self.hyperparameters):
            raise ValueError("config_hash does not match the frozen hyperparameters")
        object.__setattr__(self, "validation_manifest_hashes", tuple(self.validation_manifest_hashes))
        object.__setattr__(self, "candidates", tuple(self.candidates))
        object.__setattr__(self, "hyperparameters", _freeze(dict(self.hyperparameters)))

    def as_dict(self) -> Dict[str, object]:
        return {"campaign_id": self.campaign_id, "algorithm": self.algorithm,
                "config_hash": self.config_hash,
                "validation_manifest_hashes": list(self.validation_manifest_hashes),
                "selection_rule": self.selection_rule, "frozen_at": self.frozen_at,
                "candidates": list(self.candidates), "reason": self.reason,
                "hyperparameters": dict(self.hyperparameters)}

    @classmethod
    def from_dict(cls, payload: Mapping[str, object]) -> "ConfigurationFreeze":
        return cls(payload["campaign_id"], payload["algorithm"], payload["config_hash"],
                   tuple(payload["validation_manifest_hashes"]), payload["selection_rule"],
                   payload["frozen_at"], tuple(payload.get("candidates", ())), payload.get("reason", ""),
                   dict(payload.get("hyperparameters") or {}))

    def freeze_hash(self) -> str:
        return canonical_hash(self.as_dict())
