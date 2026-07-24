# -*- coding: utf-8 -*-
"""Extract full source of key cells for review."""
import json
from pathlib import Path

nb_path = Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb")
out_dir = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_cells")
out_dir.mkdir(exist_ok=True)
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cells = nb["cells"]

# Extract all cells as individual files for review
index_lines = []
for i, c in enumerate(cells):
    src = "".join(c.get("source", []))
    ext = "md" if c["cell_type"] == "markdown" else "py"
    fp = out_dir / f"cell_{i:03d}.{ext}"
    fp.write_text(src, encoding="utf-8")
    first = src.strip().splitlines()[0][:80] if src.strip() else "(empty)"
    index_lines.append(f"{i:03d} [{c['cell_type']}] {first}")

(out_dir / "INDEX.txt").write_text("\n".join(index_lines), encoding="utf-8")
print(f"Extracted {len(cells)} cells to {out_dir}")
