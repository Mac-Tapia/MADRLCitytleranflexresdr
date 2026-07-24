import json
from pathlib import Path

nb = json.loads(Path(r"D:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
out = Path(r"D:/MADRLCitytleranflexresdr/_tmp_diagrams_and_stale.txt")
parts = []

# Diagram cells 6-14 full source
for i in range(6, 15):
    src = "".join(nb["cells"][i].get("source", []))
    parts.append(f"\n{'='*80}\nCELL {i}\n{'='*80}\n{src}\n")

# Cell 4 markdown
parts.append(f"\n{'='*80}\nCELL 4 RAW\n{'='*80}\n{''.join(nb['cells'][4].get('source',[]))}\n")

# Cell 59 full
parts.append(f"\n{'='*80}\nCELL 59\n{'='*80}\n{''.join(nb['cells'][59].get('source',[]))}\n")

# Cell 63 key strings around KPI counts
src63 = "".join(nb["cells"][63].get("source", []))
parts.append(f"\n{'='*80}\nCELL 63 (first 200 lines)\n{'='*80}\n" + "\n".join(src63.splitlines()[:200]))

# Cell 66 key parts
src66 = "".join(nb["cells"][66].get("source", []))
parts.append(f"\n{'='*80}\nCELL 66 (first 250 lines)\n{'='*80}\n" + "\n".join(src66.splitlines()[:250]))

# Cell 70 - search MAPPO / 54 / KPI
src70 = "".join(nb["cells"][70].get("source", []))
parts.append(f"\n{'='*80}\nCELL 70 FULL\n{'='*80}\n{src70}")

# Stale pattern search across all cells
import re
patterns = [
    r"3.?KPI", r"KPI.?reducid", r"reduced.?KPI", r"average_daily_peak|ramping_average|net_electricity_consumption",
    r"MAPPO.*baseline|baseline.*MAPPO|MAPPO como", r"9\+3", r"Paso [1-7]",
    r"100 episodios|N_EPISODES\s*=\s*100|episodios?\s*=\s*100",
    r"OE1.*=.*3|solo 3 KPI|subset", r"flexibilidad, carbono y costo \(3",
]
parts.append("\n===== STALE PATTERN HITS =====\n")
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    for pat in patterns:
        for m in re.finditer(pat, src, re.I):
            start = max(0, m.start()-80)
            end = min(len(src), m.end()+80)
            snippet = src[start:end].replace("\n", " | ")
            parts.append(f"CELL {i}: /{pat}/ -> ...{snippet}...")

out.write_text("\n".join(parts), encoding="utf-8")
print(f"wrote {out} bytes={out.stat().st_size}")
