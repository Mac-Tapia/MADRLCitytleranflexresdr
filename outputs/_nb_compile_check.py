# -*- coding: utf-8 -*-
import json
from pathlib import Path

nb = json.loads(Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
fails = []
n_code = 0
for i, c in enumerate(nb["cells"]):
    if c["cell_type"] != "code":
        continue
    n_code += 1
    s = "".join(c.get("source", []))
    try:
        compile(s, f"cell{i}", "exec")
    except SyntaxError as e:
        fails.append(f"cell {i}: {e}")

text = "\n".join(fails) if fails else f"ALL_CODE_CELLS_COMPILE_OK n={n_code} total_cells={len(nb['cells'])}"
Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_compile.txt").write_text(text, encoding="utf-8")
print(text)
