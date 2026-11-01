---
name: madrl-agent-coordination
description: Coordinate explicitly requested MADRL implementer and auditor agents with bounded ownership, minimal context and evidence-based handoffs.
---

Read AGENTS.md and `docs/architecture/AGENT_HARNESS.md`. Use delegation only when authorized and useful; do not spawn agents for every small edit. A skill never grants new permissions, tools, subscriptions or API credits.

Coordinator sends each implementer a requirement ID, allowed files, inputs, expected outputs, exact acceptance command and forbidden side effects. One writer owns each file. Share interfaces before parallel work. Provide fresh bounded context rather than the full chat where supported. Reuse an existing worker for a correction; do not multiply duplicate agents.

Implementer reads the selected plan, preserves unrelated work, writes a failing test before new behavior and reports the diff and actual results. No commit/push or dependency change unless explicitly authorized. Run the project-context check before every edit and Git operation.

Independent auditor reviews implementation and requirements in read-only mode. Return findings ordered by impact, evidence and residual risk; do not silently fix the implementer's files. Coordinator reruns acceptance and records partial or blocked outcomes without promoting smokes to thesis results.

Backend: use `tools/skills/fastapi-templates/SKILL.md` only for an approved FastAPI change; preserve the current stdlib panel otherwise. Architecture: `tools/skills/architecture-patterns/SKILL.md`; maintain the modular monolith, no unsolicited microservices. Frontend: `tools/skills/frontend-design/SKILL.md` and `tools/skills/webapp-testing/SKILL.md`. Deployment: Docker skills only for requested container work, never cloud purchases. Harness: `tools/skills/harness-engineering/SKILL.md`.

Verification helpers are repository-relative. No closed connector is required. Do not edit global agent settings, browser profiles or credentials. Stop after the bounded deliverable; performance improvements require measurement, not a larger skill count.
