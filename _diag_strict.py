"""Strict pyright on notebook with examples paths but NO suppressions."""
from __future__ import annotations

import json
import subprocess
import sys
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
nb = json.loads((root / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
lines = []
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        lines.append(f"# %% cell {i}")
        lines.append("".join(cell.get("source", [])))
        lines.append("")
extract = root / "_tmp_nb_extract.py"
extract.write_text("\n".join(lines), encoding="utf-8")

for mode in ("basic", "standard"):
    cfg = {
        "include": ["."],
        "extraPaths": ["CityLearn", "CityLearn/scripts", "tools"],
        "stubPath": "CityLearn/examples/typings",
        "venvPath": ".",
        "venv": ".venv39-citylearn-v3",
        "pythonVersion": "3.9",
        "typeCheckingMode": mode,
    }
    p = root / "_tmp_pyright.json"
    p.write_text(json.dumps(cfg))
    r = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(p), str(extract), "--outputjson"],
        capture_output=True, text=True, cwd=root,
    )
    diags = json.loads(r.stdout).get("generalDiagnostics", [])
    print(f"\n{mode}: {len(diags)}")
    for rule, n in Counter(d["rule"] for d in diags).most_common():
        print(f"  {n} {rule}")
    src = extract.read_text(encoding="utf-8").splitlines()
    for d in diags:
        ln = d["range"]["start"]["line"]
        print(f"  L{ln} {d['rule']}: {src[ln-1].strip()[:90]}")
