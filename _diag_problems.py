"""Enumerate pyright diagnostics on cumulative notebook code (IDE-like)."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
nb_path = root / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb"
nb = json.loads(nb_path.read_text(encoding="utf-8"))
lines: list[str] = []
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        lines.append(f"# %% cell {i}")
        lines.append("".join(cell.get("source", [])))
        lines.append("")
extract = root / "_tmp_nb_extract.py"
extract.write_text("\n".join(lines), encoding="utf-8")

configs = {
    "examples_pyrightconfig": root / "CityLearn/examples/pyrightconfig.json",
    "workspace_root": root / "pyrightconfig.json",
    "standard_no_suppress": None,
}

for label, cfg_path in configs.items():
    if cfg_path is None:
        cfg = {
            "include": ["."],
            "extraPaths": ["CityLearn", "CityLearn/scripts", "tools"],
            "stubPath": "CityLearn/examples/typings",
            "venvPath": ".",
            "venv": ".venv39-citylearn-v3",
            "pythonVersion": "3.9",
            "typeCheckingMode": "standard",
        }
        tmp = root / "_tmp_pyright.json"
        tmp.write_text(json.dumps(cfg), encoding="utf-8")
        project = str(tmp)
    else:
        project = str(cfg_path)
    result = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", project, str(extract), "--outputjson"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    data = json.loads(result.stdout)
    diags = data.get("generalDiagnostics", [])
    print(f"\n=== {label}: {len(diags)} ===")
    for rule, count in Counter(x["rule"] for x in diags).most_common():
        print(f"  {count} {rule}")
    src_lines = extract.read_text(encoding="utf-8").splitlines()
    for x in diags:
        ln = x["range"]["start"]["line"]
        src = src_lines[ln - 1].strip()[:100] if ln <= len(src_lines) else ""
        print(f"  L{ln} {x['rule']}: {src}")

# notebook file directly
for project in (str(root / "CityLearn/examples/pyrightconfig.json"), str(root / "pyrightconfig.json")):
    result = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", project,
         str(nb_path), "--outputjson"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    data = json.loads(result.stdout)
    diags = data.get("generalDiagnostics", [])
    name = Path(project).parent.name
    print(f"\n=== ipynb via {name}: {len(diags)} ===")
    for x in diags[:15]:
        print(f"  {x['rule']}: {x.get('message','')[:90]}")
