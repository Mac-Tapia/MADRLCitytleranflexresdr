"""Count missing-import diagnostics per cell (root config, no suppressions)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
cfg = {
    "include": ["."],
    "extraPaths": ["CityLearn", "tools"],
    "venvPath": ".",
    "venv": ".venv39-citylearn-v3",
    "pythonVersion": "3.9",
    "typeCheckingMode": "basic",
}
cfg_path = root / "_tmp_pyright.json"
cfg_path.write_text(json.dumps(cfg))

nb = json.loads((root / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
total = 0
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] != "code":
        continue
    src = "".join(cell.get("source", []))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(src)
        tmp = tf.name
    r = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(cfg_path), tmp, "--outputjson"],
        capture_output=True, text=True, cwd=root,
    )
    Path(tmp).unlink(missing_ok=True)
    diags = [d for d in json.loads(r.stdout).get("generalDiagnostics", []) if d["rule"] == "reportMissingImports"]
    if diags:
        has_colab = "google.colab" in src
        has_common = "citylearn_v3_training_common" in src
        print(f"cell {i}: {len(diags)} missing-import colab={has_colab} common={has_common}")
        total += len(diags)
print("total missing-import isolated:", total)

# cumulative root config
lines = []
for i, cell in enumerate(nb["cells"]):
    if cell["cell_type"] == "code":
        lines.append(f"# %% cell {i}")
        lines.append("".join(cell.get("source", [])))
        lines.append("")
extract = root / "_tmp_nb_extract.py"
extract.write_text("\n".join(lines), encoding="utf-8")
r = subprocess.run(
    [sys.executable, "-m", "pyright", "--project", str(cfg_path), str(extract), "--outputjson"],
    capture_output=True, text=True, cwd=root,
)
diags = json.loads(r.stdout).get("generalDiagnostics", [])
print("cumulative missing-import:", sum(1 for d in diags if d["rule"] == "reportMissingImports"))
for d in diags:
    if d["rule"] == "reportMissingImports":
        print(" ", d.get("message", "")[:100])
