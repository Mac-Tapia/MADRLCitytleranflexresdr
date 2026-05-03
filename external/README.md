# External MADRL Backends

This directory contains the source-backed upstream backends used by the
CityLearn v3 MADRL layer. They are intentionally kept outside
`CityLearn/citylearn/agents` so the project does not maintain duplicate or
invented implementations of the algorithms.

## Role in This Project

CityLearn v2 remains the simulator and environment source of truth. The v3
layer in `CityLearn/citylearn/v3` adapts that simulator to Dec-POMDP, CTDE and
MARLlib/RLlib-facing interfaces. The repositories in this directory provide the
source-backed algorithm implementations for thesis-grade experiments.

## Included Sources

- `HARL`: HAPPO/HARL official implementation.
- `MARL`: MASAC/mSAC paper repository.
- `MATD3implementation`: MATD3 author repository.
- `off-policy`: PyTorch MATD3/RMATD3 reference backend from `marlbenchmark`.
- `MAAC`: original MAAC repository.
- `MARLlib`: MARL framework used for environment/algorithm orchestration.

## MATD3 Boundary

The author repository for MATD3 is `MATD3implementation`; it is the paper
source, but it targets Python 3.6, TensorFlow 1.x and Gym 0.10. The
`off-policy` backend is added for Python 3.9 PyTorch training because it
contains MLP MATD3 and recurrent RMATD3 implementations and imports in the
validated CityLearn v3 environment. It must be cited as a compatible PyTorch
reference backend, not as the original author repository.

## Integration Rule

Do not copy algorithm internals into `citylearn.agents`. Integration should be
done through adapters, launch scripts, dependency locks or isolated backend
environments. This keeps CityLearn v3 reproducible and traceable to the
scientific source of each algorithm.

## Reproducibility Note

Some upstream repositories target older Python, TensorFlow, Gym or Linux-only
stacks. When a backend cannot run inside the main CityLearn environment, use an
isolated environment and keep the CityLearn v3 environment contract unchanged.
