# -*- coding: utf-8 -*-
import json
from pathlib import Path

nb = json.loads(Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
out = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_cells")
for i in [1, 16, 17, 30, 32, 33, 40, 41, 42, 43, 49, 61, 69]:
    s = "".join(nb["cells"][i]["source"])
    (out / f"cell_{i:03d}_live.txt").write_text(s, encoding="utf-8")
    print(f"wrote {i} len={len(s)}")
