# -*- coding: utf-8 -*-
import json
from pathlib import Path

nb_path = Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb")
out_path = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_audit_map.txt")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cells = nb["cells"]
lines = []
lines.append(f"Total cells: {len(cells)}")
lines.append(f"nbformat: {nb.get('nbformat')}.{nb.get('nbformat_minor')}")
lines.append("---")
for i, c in enumerate(cells):
    src = "".join(c.get("source", []))
    first_lines = [ln for ln in src.strip().splitlines() if ln.strip()]
    first = first_lines[0][:140] if first_lines else "(empty)"
    nlines = len(src.splitlines())
    ctype = c.get("cell_type")
    # hash-ish fingerprint of first 500 chars for duplicate detection
    fp = " ".join(src[:800].split())[:200]
    lines.append(f"{i:03d} [{ctype:8}] L={nlines:4} | {first}")
    lines.append(f"     FP: {fp}")
out_path.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {out_path} with {len(cells)} cells")
