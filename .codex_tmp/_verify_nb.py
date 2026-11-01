import json
from pathlib import Path

nb = json.loads(Path("examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
out = []
for i in (0, 66, 67, 68, 69, 70):
    src = "".join(nb["cells"][i].get("source", []))
    out.append(f"===== CELL {i} ({nb['cells'][i]['cell_type']}) =====")
    out.append(src[:600])
    out.append("")
Path(".codex_tmp/_verify_nb_sec93.txt").write_text("\n".join(out), encoding="utf-8")
print("ok")
