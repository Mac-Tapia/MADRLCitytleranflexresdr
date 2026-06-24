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

## Cursor Cloud specific instructions

This runs on a Linux VM. The Windows-only `scripts/verify_project_context.ps1` guard above does not apply here; skip it.

### Python environment
- Python **3.9** is required (the RL stack pins `numpy==1.23.5`, `ray[rllib]==1.8.0`, `gym==0.20.0`). The venv lives at `.venv39-citylearn-v3/` (created with `uv`). Activate it: `source .venv39-citylearn-v3/bin/activate`.
- `pip` must stay **< 24.1** (pinned to 24.0). pip ≥ 24.1 rejects `gym==0.20.0`'s invalid sdist metadata (`opencv-python>=3.`). Do not upgrade pip in this venv.
- `gym==0.20.0` only builds with old build tooling (`setuptools==65.5.1`, `wheel==0.38.4`, `packaging==21.3`) plus `--no-build-isolation`. It is already built/installed; avoid forcing a rebuild.
- The `CityLearn` submodule pins `numpy>=1.26.4` and pulls heavy extras (`openstudio`, `doe_xstock`) that conflict with the project's `numpy==1.23.5`. Install it with `pip install --no-deps -e ./CityLearn`; the parent `requirements.txt` is the single source of truth for runtime deps. The resulting `citylearn ... requires numpy>=1.26.4, but you have numpy 1.23.5` pip warning is expected and intentional.
- No GPU on this VM: `torch` runs on CPU. The `--index-url .../whl/cu126` torch step from the docs is GPU-only and is skipped here.

### Submodules
- Only the `CityLearn` submodule is needed to run/test the core. The `external/*` submodules (HARL, MAAC, MARLlib, ...) are only needed for the full algorithm backends and are not initialized by default.

### Running / testing
- Lint: `ruff check uc3m tests` (config in `pyproject.toml`).
- Tests that pass standalone: `pytest tests/citylearn_v3`.
- Simulator smoke run: build `citylearn.citylearn.CityLearnEnv` from `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json` (17 buildings, Iquitos). Each step is ~2.4 s, so use a short horizon (e.g. 24 steps) for smoke tests.

### KNOWN BLOCKER — missing `uc3m/env/` package
- `uc3m/__init__.py` imports `uc3m.env.uc3m_env.UC3MEnv` and `uc3m.env.bact`, but `uc3m/env/` is **not committed**: the `.gitignore` `env/` pattern excluded it. As a result `import uc3m` fails, so **all `tests/uc3m/*` and `python -m uc3m.train` cannot run** until that package is provided.
- `.gitignore` now has a `!uc3m/env/` exception so the owner can commit the local `uc3m/env/` source. Until those files are committed, only the CityLearn simulator layer is runnable here.
