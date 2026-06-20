"""Actualiza el comentario de celda 17: lista correcta de 9 submódulos."""
import json
from pathlib import Path

NB = Path("d:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb")
with open(NB, "r", encoding="utf-8") as f:
    nb = json.load(f)

src = nb["cells"][17]["source"]
if isinstance(src, list):
    src = "".join(src)

OLD = """\
# ── 1.2  Clonar repositorio completo y dejar CityLearn en rama viva ─────────
# El repo padre (MADRLCitytleranflexresdr) contiene scripts, tools, uc3m, data
# y los submódulos HARL, off-policy, MAAC, MARL como dependencias fijadas.
# El submódulo CityLearn/ se clona primero desde el pinned commit del padre y
# luego se sube a la punta de su rama propia (citylearn-v3-madrl) para que el
# código esté siempre actualizado y NO en detached HEAD.\
"""

NEW = """\
# ── 1.2  Clonar repositorio completo + todos los submódulos ─────────────────
# Repo padre: scripts/, tools/, uc3m/, docs/, outputs/, deploy/
# Submódulos fijados (pinned commits en .gitmodules):
#   CityLearn        → github.com/Mac-Tapia/CityLearn           (citylearn-v3-madrl)
#   external/HARL    → github.com/Mac-Tapia/HARL
#   external/MAAC    → github.com/Mac-Tapia/MAAC
#   external/MARL    → github.com/Mac-Tapia/MARL
#   external/MARLlib → github.com/Mac-Tapia/MARLlib
#   external/MATD3implementation → github.com/Mac-Tapia/MATD3implementation
#   external/MicroGrids  → github.com/Mac-Tapia/MicroGrids
#   external/evcc        → github.com/evcc-io/evcc
#   external/prosumpy    → github.com/Mac-Tapia/prosumpy
# CityLearn se lleva a su rama viva (sale del detached HEAD del clone).\
"""

if OLD not in src:
    print("ERROR: texto no encontrado en celda 17")
    print(repr(src[:300]))
    exit(1)

src = src.replace(OLD, NEW)
nb["cells"][17]["source"] = src

with open(NB, "w", encoding="utf-8") as f:
    json.dump(nb, f, ensure_ascii=False, indent=1)

# Verify
with open(NB, "r", encoding="utf-8") as f:
    nb2 = json.load(f)
src2 = "".join(nb2["cells"][17]["source"])
assert "MARLlib" in src2
assert "MATD3implementation" in src2
assert "MicroGrids" in src2
assert "evcc" in src2
assert "prosumpy" in src2
assert "9 submódulos" not in src2  # no forzamos texto, solo verificamos contenido
print("OK: comentario de celda 17 actualizado con los 9 submódulos")
print(f"Total celdas: {len(nb2['cells'])}")
