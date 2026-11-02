# ADR: SimulatorPort — In-Process Integration Deferred

**Status:** Accepted  
**Date:** 2026-10-31  
**Context:** SPEC-003 defines modular orchestration with a `SimulatorPort` protocol for environment interaction.

## Decision

The `SimulatorPort` protocol is defined in `uc3m/ports/simulator.py` as a `typing.Protocol` with `reset()`, `step()`, `observation_space` and `action_space`. However, the **in-process integration is deferred**.

The current architecture uses `NativeBackend` which delegates to CityLearn launcher scripts via subprocess. This subprocess boundary provides isolation and matches the existing training infrastructure.

## Rationale

1. The 4 CityLearn launchers (`train_citylearn_v3_{happo,masac,matd3,maac}.py`) manage their own environment lifecycle internally.
2. Refactoring them to accept an injected `SimulatorPort` would require significant changes to working training code with no scientific benefit for the thesis.
3. The port definition enables future in-process integration without breaking the current architecture.

## Consequences

- `SimulatorPort` exists as a typed contract for future adapters.
- Current training continues via subprocess delegation in `NativeBackend`.
- A future decomposition of SPEC-003 can implement a `CityLearnSimulator` adapter that satisfies `SimulatorPort`.
- `LearnerPort`, `ArtifactStore` and `SimulatorPort` are `runtime_checkable`; `tests/contract/test_ports_contract.py` verifies that `NativeBackend` and `LocalArtifactStore` satisfy their ports and that ports import only the standard library and the domain.

## Addendum 2026-11-01: ExperimentTrackerPort also deferred

The design (§6) lists an `ExperimentTrackerPort`. No use case consumes one today: run telemetry is the persisted `EvidenceManifest`, heartbeat and KPI files written by the runner, which the local panel reads. Adding a port and a local adapter without a caller would be untested dead code, and MLflow/DVC spikes remain deferred (SPEC-008). The port is introduced together with its first consumer, for example when campaign metrics need streaming beyond the persisted manifests.
