"""Per-cell cumulative pyright diagnostics using workspace-root config (IDE default)."""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from collections import Counter
from pathlib import Path

root = Path(__file__).resolve().parent
nb = json.loads((root / "CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))

code_cells = [(i, c) for i, c in enumerate(nb["cells"]) if c["cell_type"] == "code"]
all_diags: list[dict] = []

for end_idx, (cell_i, _) in enumerate(code_cells):
    lines: list[str] = []
    for j in range(end_idx + 1):
        ci, cell = code_cells[j]
        lines.append(f"# %% cell {ci}")
        lines.append("".join(cell.get("source", [])))
        lines.append("")
    snippet = "\n".join(lines)
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(snippet)
        tmp_path = tf.name
    result = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(root / "pyrightconfig.json"), tmp_path, "--outputjson"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    Path(tmp_path).unlink(missing_ok=True)
    data = json.loads(result.stdout)
    diags = data.get("generalDiagnostics", [])
    if diags:
        prev = len(all_diags)
        all_diags = diags  # cumulative file always supersedes
        new_count = len(diags) - prev if end_idx else len(diags)
        if new_count > 0 or end_idx == len(code_cells) - 1:
            print(f"after cell {cell_i}: total={len(diags)} (+{max(new_count,0)})")

print(f"\nFINAL cumulative (root config): {len(all_diags)}")
for rule, n in Counter(x["rule"] for x in all_diags).most_common():
    print(f"  {n} {rule}")
for x in all_diags:
    print(f"  L{x['range']['start']['line']} {x['rule']}: {x.get('message','')[:100]}")

# isolated per-cell (no prior context) - count cells with errors
iso_total = 0
iso_by_cell = []
for cell_i, cell in code_cells:
    src = "".join(cell.get("source", []))
    with tempfile.NamedTemporaryFile("w", suffix=".py", delete=False, encoding="utf-8") as tf:
        tf.write(src)
        tmp_path = tf.name
    result = subprocess.run(
        [sys.executable, "-m", "pyright", "--project", str(root / "pyrightconfig.json"), tmp_path, "--outputjson"],
        capture_output=True,
        text=True,
        cwd=root,
    )
    Path(tmp_path).unlink(missing_ok=True)
    diags = json.loads(result.stdout).get("generalDiagnostics", [])
    if diags:
        iso_by_cell.append((cell_i, len(diags)))
        iso_total += len(diags)
print(f"\nIsolated per-cell total: {iso_total} across {len(iso_by_cell)} cells")
for cell_i, n in iso_by_cell[:20]:
    print(f"  cell {cell_i}: {n}")
