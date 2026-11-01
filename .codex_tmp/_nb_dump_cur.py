import json
from pathlib import Path

nb = json.loads(Path("examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
for i in range(64, 72):
    c = nb["cells"][i]
    src = "".join(c.get("source", []))
    Path(f".codex_tmp/_cur_cell_{i}.txt").write_text(src, encoding="utf-8")
    Path(f".codex_tmp/_cur_cell_{i}_meta.txt").write_text(
        f"type={c['cell_type']}\nid={c.get('id')}\nlen={len(src)}\nhead={src[:150]!r}\n",
        encoding="utf-8",
    )
print("dumped 64-71")
