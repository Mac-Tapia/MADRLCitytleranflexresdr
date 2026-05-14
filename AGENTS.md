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
