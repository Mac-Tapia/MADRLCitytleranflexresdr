"""Strict configuration boundary for multiobjective scenario definitions."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Mapping

import yaml

from uc3m.domain.objectives import (
    ObjectiveAxis,
    ObjectivePolicy,
    canonical_objective_policies,
)
from uc3m.domain.scenarios import (
    ConstraintPolicy,
    ScenarioCatalog,
    ScenarioDefinition,
    TariffPolicy,
)


def _mapping(value: object, label: str) -> Mapping[str, Any]:
    if not isinstance(value, Mapping):
        raise ValueError(f"{label} must be a mapping")
    return value


def _load_yaml_mapping(path: Path) -> Mapping[str, Any]:
    if not path.is_file():
        raise ValueError(f"Configuration file does not exist: {path}")
    payload = yaml.safe_load(path.read_text(encoding="utf-8"))
    return _mapping(payload, str(path))


def _load_objective_policies(path: Path) -> Dict[str, ObjectivePolicy]:
    payload = _load_yaml_mapping(path)
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported objective policy schema_version")

    raw_policies = _mapping(payload.get("policies"), "policies")
    policies: Dict[str, ObjectivePolicy] = {}
    for policy_id, raw_policy_value in raw_policies.items():
        raw_policy = _mapping(raw_policy_value, f"policy {policy_id}")
        raw_weights = _mapping(raw_policy.get("weights"), f"weights for {policy_id}")
        try:
            weights = {
                ObjectiveAxis(str(axis)): float(weight)
                for axis, weight in raw_weights.items()
            }
        except (TypeError, ValueError) as exc:
            raise ValueError(f"Invalid objective axis or weight for {policy_id}") from exc
        policies[str(policy_id)] = ObjectivePolicy(
            policy_id=str(policy_id),
            method=str(
                raw_policy.get(
                    "method", "compensatory_hierarchical_weighted_sum"
                )
            ),
            weights=weights,
        )

    canonical = canonical_objective_policies()
    for policy_id, canonical_policy in canonical.items():
        if policy_id in policies and (
            policies[policy_id].fingerprint() != canonical_policy.fingerprint()
        ):
            raise ValueError(f"canonical policy {policy_id} drift")
    return policies


def load_scenario_catalog(path: Path) -> ScenarioCatalog:
    """Load a scenario catalog and reject canonical policy drift.

    Paths referenced from the catalog are resolved relative to the catalog,
    keeping the configuration portable across workstations and CI.
    """

    path = Path(path)
    payload = _load_yaml_mapping(path)
    if payload.get("schema_version") != 1:
        raise ValueError("Unsupported scenario schema_version")

    policy_file = payload.get("objective_policies_file")
    if not isinstance(policy_file, str) or not policy_file:
        raise ValueError("objective_policies_file must be a relative file name")
    policy_path = (path.parent / policy_file).resolve()
    if path.parent.resolve() not in policy_path.parents:
        raise ValueError("objective_policies_file must stay inside the config directory")
    policies = _load_objective_policies(policy_path)

    raw_tariffs = _mapping(payload.get("tariff_policies"), "tariff_policies")
    tariffs: Dict[str, TariffPolicy] = {}
    for policy_id, raw_value in raw_tariffs.items():
        raw = _mapping(raw_value, f"tariff policy {policy_id}")
        tariffs[str(policy_id)] = TariffPolicy(
            policy_id=str(policy_id),
            mode=str(raw.get("mode")),  # type: ignore[arg-type]
            multiplier=float(raw.get("multiplier")),
        )

    raw_constraints = _mapping(
        payload.get("constraint_policies"), "constraint_policies"
    )
    constraints: Dict[str, ConstraintPolicy] = {}
    for policy_id, raw_value in raw_constraints.items():
        raw = _mapping(raw_value, f"constraint policy {policy_id}")
        ev_enabled = raw.get("ev_service_enabled")
        bess_enabled = raw.get("bess_limits_enabled")
        if not isinstance(ev_enabled, bool) or not isinstance(bess_enabled, bool):
            raise ValueError(f"constraint policy {policy_id} flags must be booleans")
        constraints[str(policy_id)] = ConstraintPolicy(
            policy_id=str(policy_id),
            ev_service_enabled=ev_enabled,
            bess_limits_enabled=bess_enabled,
        )

    raw_scenarios = _mapping(payload.get("scenarios"), "scenarios")
    definitions = []
    for scenario_id, raw_value in raw_scenarios.items():
        raw = _mapping(raw_value, f"scenario {scenario_id}")
        objective_id = str(raw.get("objective_policy"))
        tariff_id = str(raw.get("tariff_policy"))
        constraint_id = str(raw.get("constraint_policy"))
        try:
            objective_policy = policies[objective_id]
            tariff_policy = tariffs[tariff_id]
            constraint_policy = constraints[constraint_id]
        except KeyError as exc:
            raise ValueError(
                f"scenario {scenario_id} references unknown policy {exc.args[0]}"
            ) from exc
        definitions.append(
            ScenarioDefinition(
                scenario_id=str(scenario_id),
                objective_policy=objective_policy,
                tariff_policy=tariff_policy,
                constraint_policy=constraint_policy,
                study_kind=str(raw.get("study_kind")),  # type: ignore[arg-type]
            )
        )
    return ScenarioCatalog(definitions)


def project_runtime_config(definition: ScenarioDefinition) -> Dict[str, object]:
    """Project one validated scenario into a JSON-serializable runtime contract."""

    policy = definition.objective_policy
    axes = list(policy.weights)
    return {
        "scenario": {
            "id": definition.scenario_id,
            "study_kind": definition.study_kind,
            "fingerprint": definition.fingerprint(),
        },
        "reward": {
            "policy_id": policy.policy_id,
            "policy_version": policy.fingerprint(),
            "policy_fingerprint": policy.fingerprint(),
            "method": policy.method,
            "axes": [axis.value for axis in axes],
            "lambdas": [policy.weights[axis] for axis in axes],
        },
        "pricing": {
            "policy_id": definition.tariff_policy.policy_id,
            "mode": definition.tariff_policy.mode,
            "multiplier": definition.tariff_policy.multiplier,
            "fingerprint": definition.tariff_policy.fingerprint(),
        },
        "constraints": {
            "policy_id": definition.constraint_policy.policy_id,
            "ev_service_enabled": definition.constraint_policy.ev_service_enabled,
            "bess_limits_enabled": definition.constraint_policy.bess_limits_enabled,
            "fingerprint": definition.constraint_policy.fingerprint(),
        },
    }
