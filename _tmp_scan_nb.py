# -*- coding: utf-8 -*-
import json
import re
from pathlib import Path

nb_path = Path(r"D:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
print(f"Total cells: {len(nb['cells'])}")

# Dump all markdown + comment-heavy code cells for review
out = Path(r"D:/MADRLCitytleranflexresdr/_tmp_nb_scan_out.txt")
lines = []
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    first = src.strip().split("\n")[0][:120] if src.strip() else "(empty)"
    lines.append(f"\n{'='*80}\nCELL {i} [{c['cell_type']}] lines={len(src.splitlines())}\nFIRST: {first}\n{'='*80}")
    if c["cell_type"] == "markdown":
        lines.append(src)
    else:
        # extract significant # comments (not shebang-like short ones only)
        comments = []
        for ln in src.splitlines():
            s = ln.strip()
            if s.startswith("#") and len(s) > 3:
                comments.append(ln)
        if comments:
            lines.append("--- COMMENTS ---")
            lines.append("\n".join(comments))
        # also show top docstring / header block
        header = []
        for ln in src.splitlines()[:40]:
            header.append(ln)
        lines.append("--- HEADER (first 40 lines) ---")
        lines.append("\n".join(header))

out.write_text("\n".join(lines), encoding="utf-8")
print(f"Wrote {out} ({out.stat().st_size} bytes)")

# Flag stale patterns
stale_patterns = [
    r"MAPPO",
    r"reduced",
    r"3.?KPI",
    r"KPI.?reducid",
    r"subset",
    r"Paso [1-7]",
    r"N_EPISODES\s*=\s*(?!50)\d+",
    r"episodios?\s*=?\s*(100|200|30|20)\b",
    r"FASE 1: HAPPO \+ MATD3",
    r"baseline.*MAPPO",
    r"MAPPO.*baseline",
    r"3 KPIs",
    r"KPIs?\s+reducid",
    r"only.?3",
    r"ramping.?1.?2",
    r"carbon.?emissions.?cost",
    r"LAUNCH_FULL_TRAINING\s*=\s*False",
    r"from.?scratch|desde.?cero",
]
print("\n=== STALE HITS ===")
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    for pat in stale_patterns:
        for m in re.finditer(pat, src, re.I):
            # context line
            start = src.rfind("\n", 0, m.start()) + 1
            end = src.find("\n", m.end())
            if end < 0:
                end = len(src)
            line = src[start:end].strip()[:160]
            print(f"cell {i:3d} [{c['cell_type'][:2]}] /{pat}/ :: {line}")
