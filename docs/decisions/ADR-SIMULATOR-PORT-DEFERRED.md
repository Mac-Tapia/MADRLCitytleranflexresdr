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
