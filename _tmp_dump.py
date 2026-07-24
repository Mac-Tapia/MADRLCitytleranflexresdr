import json
from pathlib import Path
raw = Path(r"D:\MADRLCitytleranflexresdr\_tmp_basic_out.json").read_text(encoding="utf-8").strip()
data = json.loads(raw[raw.find("{"):])
diags = data.get("generalDiagnostics") or []
out = []
for d in diags:
    ln = d.get("range", {}).get("start", {}).get("line", -1) + 1
    col = d.get("range", {}).get("start", {}).get("character", -1) + 1
    out.append(f"{Path(d['file']).name}:{ln}:{col} [{d.get('rule')}] {d.get('message')}")
Path(r"D:\MADRLCitytleranflexresdr\_tmp_basic_msgs.txt").write_text("\n".join(out), encoding="utf-8")
print(f"wrote {len(out)} msgs")
