---
name: madrl-experiment-evidence-audit
description: Audit MADRL training artifacts and promotion claims against manifests, policy and dataset hashes; use for readiness or best-model evidence reviews, not to launch training.
---

Operate read-only. Read AGENTS.md and the run's manifest before metrics. Inputs: explicit run IDs and experiment specification; never choose the newest folder implicitly.

Check source/dataset/policy hashes, algorithm, scenario, seed, horizon, completed steps, finite KPI values, complete native checkpoint bundles and expected artifacts. Separate interrupted, resumed, complete and scientifically verified states. Treat pickle-based checkpoints as trusted-local-only; do not deserialize downloaded unknown files.

E1=[0.60,0.15,0.25], E2=[0.25,0.60,0.15], E3=[0.15,0.25,0.60] in flexibility/CO2/cost order. These are compensatory priorities, not lexicographic optimization. Literature does not validate these exact coefficients.

Output: checks and missing evidence by run; distinguish local persistence from optimizer/RNG/replay continuity and real Colab disconnect recovery. Reject promotion based only on return code, checkpoint existence, or eight-step smoke. No writes, deletion, training launch or Git mutation. Request a separate implementer task for corrections.

Use `data/audits/modular_training_acceptance.json` and `specs/STATUS.md`; scientific rationale: `docs/architecture/AGENT_HARNESS.md`.
