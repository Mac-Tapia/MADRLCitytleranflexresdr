"""Map pyright diagnostics on extracted notebook to cell indices."""
import json
import re
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
extract = root / "_tmp_nb_extract.py"
result = subprocess.run(
    [sys.executable, "-m", "pyright", str(extract), "--outputjson"],
    capture_output=True,
    text=True,
    cwd=root,
)
d = json.loads(result.stdout)
lines = extract.read_text(encoding="utf-8").splitlines()
cell_at: dict[int, int] = {}
cur = 0
for i, ln in enumerate(lines, 1):
    m = re.match(r"# %% cell (\d+)", ln)
    if m:
        cur = int(m.group(1))
    cell_at[i] = cur

for x in d.get("generalDiagnostics", []):
    ln = x["range"]["start"]["line"]
    cell = cell_at.get(ln, -1)
    src = lines[ln - 1].strip()[:110] if ln <= len(lines) else ""
    print(f"cell={cell:3d} L{ln:4d} {x['rule']:32s} {src}".encode("ascii", "replace").decode())

print("---")
print(d.get("summary"))
