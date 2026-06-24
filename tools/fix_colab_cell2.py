"""Fix cell 2: add direct Colab URL (line was lost due to backtick bash expansion)."""
import json
from pathlib import Path

NB = Path("d:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
with open(NB, "r", encoding="utf-8") as f:
    nb = json.load(f)

COLAB_URL = (
    "https://colab.research.google.com/github/Mac-Tapia/CityLearn"
    "/blob/codex/iquitos-distillation-madrl-docs/examples/madrl_citylearn_v3_tutorial.ipynb"
)

src2 = "".join(nb["cells"][2]["source"])

# Fix the broken line "> " -> "> `URL`"
OLD_LINE = "> Haz clic en el badge del titulo o accede directamente:\n> \n"
NEW_LINE = (
    "> Haz clic en el badge del titulo o accede directamente:\n"
    f"> [`{COLAB_URL}`]({COLAB_URL})\n"
)

if OLD_LINE in src2:
    nb["cells"][2]["source"] = src2.replace(OLD_LINE, NEW_LINE)
    print("Fix applied: URL restored in cell 2")
else:
    # Check what's actually there and patch more aggressively
    lines = src2.split("\n")
    for i, line in enumerate(lines):
        if line == "> ":
            lines[i] = f"> [`{COLAB_URL}`]({COLAB_URL})"
            print(f"Fix applied: replaced empty '> ' at line {i}")
            break
    nb["cells"][2]["source"] = "\n".join(lines)

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

# Verify
with open(NB, "r", encoding="utf-8") as f:
    nb2 = json.load(f)
src2_check = "".join(nb2["cells"][2]["source"])
assert COLAB_URL in src2_check, "URL NOT FOUND after fix"
print(f"Verified: URL present in cell 2")
print(f"Total cells: {len(nb2['cells'])}")
