import json
from pathlib import Path

nb = json.loads(Path("examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
out = []
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    head = src[:300].replace("\n", " | ")
    keys = ("Sección 9", "### 9.", "9b", "Selección OG", "TOPSIS", "8.1a", "dual")
    if any(k in src[:600] for k in keys) or (63 <= i <= 72):
        out.append(f"--- cell {i} ({c['cell_type']}) len={len(src)} ---")
        out.append(head)
        out.append("")

Path(".codex_tmp/_nb_sec9_index.txt").write_text("\n".join(out), encoding="utf-8")
print(f"wrote {len(out)} lines; cells={sum(1 for x in out if x.startswith('---'))}")
