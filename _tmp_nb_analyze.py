import json
import re
from pathlib import Path

nb_path = Path("CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
nb = json.loads(nb_path.read_text(encoding="utf-8"))

patterns = [
    r"mirror",
    r"FUSE_MIRROR",
    r"SKIP_FUSE",
    r"bootstrap",
    r"legacy",
    r"^[\s]*#",
    r"import sys",
    r"prepare_colab",
    r"audit_colab",
    r"pick_colab",
]

for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    first = src.strip().split("\n")[0][:100] if src.strip() else "(empty)"
    print(f"\n=== Cell {i} ({c['cell_type']}) ===")
    print(f"FIRST: {first.encode('ascii', 'replace').decode()}")
    if c["cell_type"] == "code":
        # count commented lines
        commented = [ln for ln in src.splitlines() if ln.strip().startswith("#") and not ln.strip().startswith("#!")]
        if len(commented) > 3:
            print(f"  commented lines: {len(commented)}")
        dup_sys = len(re.findall(r"^\s*import sys", src, re.M))
        if dup_sys > 1:
            print(f"  duplicate import sys: {dup_sys}")
        for pat in ["mirror", "FUSE_MIRROR", "SKIP_FUSE", "legacy", "bootstrap"]:
            if re.search(pat, src, re.I):
                print(f"  matches {pat}")
