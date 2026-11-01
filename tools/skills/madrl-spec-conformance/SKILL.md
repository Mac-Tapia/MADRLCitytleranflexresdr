---
name: madrl-spec-conformance
description: Reconcile MADRL requirements, tasks, implementation and test evidence when updating project specifications or reviewing a completed implementation.
---

Read AGENTS.md, specs/STATUS.md and the selected spec/plan. Before editing or Git operations run `powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1` and stop on failure.

Inputs: explicit requirement IDs, bounded file scope and available test/audit artifacts.
Output: requirement → implementation → command/result → evidence → gap, with implemented, verified, partial, blocked or pending status.

Do not check off historical TDD or commits from the mere existence of code. A simulator 4×3 test is not four learners trained in three scenarios. Four eight-step smokes are not scientific acceptance. Preserve `scientific_acceptance=false` until the acceptance gates actually pass.

Use `data/audits/modular_training_acceptance.json` for the existing training audit. Keep outstanding Colab runtime acceptance, optimizer/RNG/replay parity, provenance, multiseed evaluation, full reporting, best-model selection and jury observations visible. Do not change scientific results, external dependencies, or DOCX as a side effect of a spec review.

Verification: run relevant tests and `python tools/skills/validate_skills.py`. Cite current source lines and actual command output; avoid claims based on another agent's assertion alone. Scientific rationale and its limits: `docs/architecture/AGENT_HARNESS.md`.
