# Project Boundary: MADRLCitytleranflexresdr

This repository is only for `D:\MADRLCitytleranflexresdr`.

Expected git root: `D:/MADRLCitytleranflexresdr`
Expected origin: `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`

Hard rules:
- Do not read, edit, commit, push, or use `D:\madrl_lima` for this project.
- Do not mix prompts, notes, results, notebooks, commits, branches, or remotes from `D:\madrl_lima`.
- Before any file edit or git operation, run `powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1`.
- If the context check fails, stop and ask the user.
- Do not edit submodules or dependencies unless the user explicitly asks in the same turn.
- Treat `CityLearn/` and `external/` as external dependencies unless explicitly instructed otherwise.
- Keep project-specific skills local to this repository under `tools/skills/`.
- Do not install, copy, reference, or use project-specific skills from global user skill folders such as `%USERPROFILE%\.agents\skills` or `%USERPROFILE%\.codex\skills`.
- If a local skill has the same name as an active global skill, disable the global duplicate or stop and ask the user before continuing.
- Skill helper commands inside this repository must use repo-relative paths, not absolute global skill paths.

## Local skills and coordination

- Canonical inventory: `tools/skills/registry.yaml`; workflow and risks: `docs/architecture/AGENT_HARNESS.md`.
- For spec reconciliation read `tools/skills/madrl-spec-conformance/SKILL.md`; for evidence review read `tools/skills/madrl-experiment-evidence-audit/SKILL.md`; for scientific claims read `tools/skills/madrl-scientific-literature-audit/SKILL.md`.
- When the user explicitly requests agents, read `tools/skills/madrl-agent-coordination/SKILL.md`. Give implementers disjoint write ownership and auditors a read-only brief. Do not parallelize dependent writes.
- Backend, frontend, architecture, Docker and harness skills are optional task guidance, not permission to change the stack or launch paid infrastructure.
- Validate with `python tools/skills/validate_skills.py`; register local discovery with `powershell -ExecutionPolicy Bypass -File scripts/skills/register_local_skills.ps1`.
- Do not publish unrelated work. Existing automatic save hooks are not authorization to stage the entire dirty worktree.
