import json
from pathlib import Path

nb = json.loads(Path("examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    if "Sección 9: Evaluación estadística" in src:
        print(f"FOUND markdown at {i}")
        Path(f".codex_tmp/_nb_cell_{i}_full.txt").write_text(src, encoding="utf-8")
        print(repr(src[:200]))
    if src.startswith("import subprocess") and "9.1  Ranking OE-completo" in src:
        print(f"FOUND code 9.1/9.2 at {i}")
    if "Sección 9b: Selección multicriterio" in src:
        print(f"FOUND 9b at {i}")
    if "### 9.3 Selección dual" in src:
        print(f"FOUND dual 9.3 at {i}")
print("total cells", len(nb["cells"]))
