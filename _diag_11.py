"""Find diagnostics matching ~11 problems under common IDE configs."""
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

scenarios = {
    "std_no_stub_no_suppress": {
        "include": ["."],
        "extraPaths": ["CityLearn", "CityLearn/scripts", "tools"],
        "venvPath": ".",
        "venv": ".venv39-citylearn-v3",
        "pythonVersion": "3.9",
        "typeCheckingMode": "standard",
    },
    "std_with_stub": {
        "include": ["."],
        "extraPaths": ["CityLearn", "CityLearn/scripts", "tools"],
        "stubPath": "CityLearn/examples/typings",
        "venvPath": ".",
        "venv": ".venv39-citylearn-v3",
        "pythonVersion": "3.9",
        "typeCheckingMode": "standard",
    },
    "std_vscode_extraPaths_only": {
        "include": ["."],
        "extraPaths": ["CityLearn", "CityLearn/scripts", "tools"],
        "stubPath": "CityLearn/examples/typings",
        "venvPath": ".",
        "venv": ".venv39-citylearn-v3",
        "pythonVersion": "3.9",
        "typeCheckingMode": "standard",
        "reportMissingModuleSource": "none",
    },
    "root_plus_scripts_extra": {
        "include": ["uc3m", "tests", "CityLearn/examples"],
        "exclude": ["**/__pycache__", ".venv*", "external", "outputs"],
        "extraPaths": ["tools", "CityLearn", "CityLearn/scripts"],
        "stubPath": "CityLearn/examples/typings",
        "venvPath": ".",
        "venv": ".venv39-citylearn-v3",
        "pythonVersion": "3.9",
        "typeCheckingMode": "standard",
        "reportMissingModuleSource": "none",
    },
}

for name, cfg in scenarios.items():
    cfg_path = root / "_tmp_pyright.json"
    cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(cfg_path), str(extract), "--outputjson"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    diags = json.loads(result.stdout).get("generalDiagnostics", [])
    print(f"{name}: {len(diags)}")
    if 8 <= len(diags) <= 14:
        for x in diags:
            ln = x["range"]["start"]["line"]
            print(f"  L{ln} {x['rule']}: {x.get('message','')[:95]}")

# per-cell cumulative with standard + stub (count new per cell)
code_cells = [(i, c) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]
cfg = scenarios["std_with_stub"]
cfg_path = root / "_tmp_pyright.json"
cfg_path.write_text(json.dumps(cfg), encoding="utf-8")
prev_n = 0
cell_new: list[tuple[int, int]] = []
import tempfile
for end_idx, (cell_i, _) in enumerate(code_cells):
    chunk = []
    for j in range(end_idx + 1):
        ci, cell = code_cells[j]
        chunk.append(f"# %% cell {ci}")
        chunk.append("".join(cell.get("source", [])))
        chunk.append("")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write("\n".join(chunk))
        tmp = tf.name
    result = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(cfg_path), tmp, "--outputjson"],
        capture_output=True, text=True, cwd=root,
    )
    Path(tmp).unlink(missing_ok=True)
    n = len(json.loads(result.stdout).get("generalDiagnostics", []))
    if n > prev_n:
        cell_new.append((cell_i, n - prev_n))
    prev_n = n
print("\nNew errors introduced per cell (std+stub):")
for cell_i, dn in cell_new:
    print(f"  cell {cell_i}: +{dn}")
print(f"  total: {prev_n}")
