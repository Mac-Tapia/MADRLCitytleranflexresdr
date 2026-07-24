import json, collections
from pathlib import Path
root = Path(r"D:\MADRLCitytleranflexresdr")
raw = (root / "_tmp_basic_out.json").read_text(encoding="utf-8").strip()
start = raw.find("{")
data = json.loads(raw[start:])
diags = data.get("generalDiagnostics") or []
by = collections.Counter(); codes = collections.Counter()
for d in diags:
    by[d.get("file", "")] += 1
    codes[d.get("rule", "") or ""] += 1
print("TOTAL", len(diags))
for f, c in by.most_common():
    print(f"{c:5d}  {f}")
print("--- rules ---")
for r, c in codes.most_common():
    print(f"{c:5d}  {r}")
for d in diags[:50]:
    m = d.get("message", "")[:140]
    ln = d.get("range", {}).get("start", {}).get("line", -1) + 1
    print(f"{Path(d['file']).name}:{ln} [{d.get('rule')}] {m}")
