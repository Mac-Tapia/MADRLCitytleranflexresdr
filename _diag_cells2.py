"""Per-cell error counts with examples pyrightconfig (nearest to notebook)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

root = Path(__file__).resolve().parent
project = root / "CityLearn/examples/pyrightconfig.json"
nb = json.loads((root / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
code_cells = [(i, c) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]

# cumulative
prev = 0
for end, (cell_i, _) in enumerate(code_cells):
    lines = []
    for j in range(end + 1):
        ci, cell = code_cells[j]
        lines.append(f"# %% cell {ci}")
        lines.append("".join(cell.get("source", [])))
        lines.append("")
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write("\n".join(lines))
        tmp = tf.name
    r = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(project), tmp, "--outputjson"],
        capture_output=True, text=True, cwd=root,
    )
    Path(tmp).unlink(missing_ok=True)
    n = len(json.loads(r.stdout).get("generalDiagnostics", []))
    if n > prev:
        print(f"cumulative after cell {cell_i}: {n} (+{n-prev})")
        prev = n
print("cumulative final:", prev)

# each cell alone
total = 0
rows = []
for cell_i, cell in code_cells:
    src = "".join(cell.get("source", []))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(src)
        tmp = tf.name
    r = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(project), tmp, "--outputjson"],
        capture_output=True, text=True, cwd=root,
    )
    Path(tmp).unlink(missing_ok=True)
    diags = json.loads(r.stdout).get("generalDiagnostics", [])
    if diags:
        rows.append((cell_i, diags))
        total += len(diags)

print(f"isolated cells with errors: {len(rows)} total diags {total}")
for cell_i, diags in rows:
    print(f"  cell {cell_i}: {len(diags)} -> {[d['rule'] for d in diags]}")
