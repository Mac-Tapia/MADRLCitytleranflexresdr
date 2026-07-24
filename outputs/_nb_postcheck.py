# -*- coding: utf-8 -*-
"""Post-cleanup sanity check."""
import json
import re
from pathlib import Path

nb = json.loads(Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb").read_text(encoding="utf-8"))
cells = nb["cells"]
out = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_postcheck.txt")
lines = []
lines.append(f"cells={len(cells)}")

def src(i):
    return "".join(cells[i].get("source", []))

# Critical invariants
checks = []
# Find 6.1
idx61 = next(i for i, c in enumerate(cells) if c["cell_type"]=="code" and "EXECUTION_MODE = 'two_phase_happo_masac'" in src(i))
s61 = src(idx61)
checks.append(("N_EPISODES=50", "N_EPISODES      = 50" in s61))
checks.append(("two_phase mode", "EXECUTION_MODE = 'two_phase_happo_masac'" in s61))
checks.append(("QUICK_TEST False", "QUICK_TEST      = False" in s61))
checks.append(("SCHEMA reuse", "globals().get(" in s61 and "SCHEMA_PATH" in s61))
checks.append(("MASAC SIX_JOB align", "replay_buffer_size\": SIX_JOB_MASAC_BUF" in s61 or "replay_buffer_size\": SIX_JOB_MASAC_BUF" in s61.replace('"', '"')))
checks.append(("MASAC SIX_JOB buf ref", "SIX_JOB_MASAC_BUF" in s61 and "HYPERPARAMS" in s61))
checks.append(("MATD3 SIX_JOB", "SIX_JOB_MATD3_BATCH" in s61))
checks.append(("MAAC SIX_JOB", "SIX_JOB_MAAC_BATCH" in s61))
checks.append(("HAPPO rollout auto", "HAPPO_ROLLOUT_THREADS" in s61 and '"n_rollout_threads"' in s61))

idx72 = next(i for i, c in enumerate(cells) if c["cell_type"]=="code" and "LAUNCH_FULL_TRAINING = True" in src(i))
s72 = src(idx72)
checks.append(("7.2 launch true", "LAUNCH_FULL_TRAINING = True" in s72))
checks.append(("7.2 phase1", "('happo', 'masac')" in s72))
checks.append(("7.2 phase2", "('matd3', 'maac')" in s72))

idx23 = next(i for i, c in enumerate(cells) if c["cell_type"]=="code" and "HAPPO_KPI_MODE" in src(i))
s23 = src(idx23)
checks.append(("2.3 default skip", "HAPPO_KPI_MODE = 'skip'" in s23))
checks.append(("2.3 not dry_run default", "HAPPO_KPI_MODE = 'dry_run'" not in s23.split("HAPPO_KPI_MODE = 'skip'")[0] + "HAPPO_KPI_MODE = 'skip'"))

# Section uniqueness: no duplicate ## Seccion / ## Sección headers
headers = []
for i, c in enumerate(cells):
    if c["cell_type"] != "markdown":
        continue
    for ln in src(i).splitlines():
        if ln.startswith("## "):
            headers.append((i, ln.strip()))
            break
# count duplicates
from collections import Counter
# normalize accents for duplicate detect
norm = [re.sub(r"[áéíóúñ]", lambda m: {"á":"a","é":"e","í":"i","ó":"o","ú":"u","ñ":"n"}[m.group()], h[1].lower()) for h in headers]
# check Paso 1-7 gone
s001 = src(1)
checks.append(("no Paso 1-7 dup", "### Paso 1 — Seleccionar runtime" not in s001))
checks.append(("Flujo A present", "Flujo A" in s001 or "DESDE CERO" in s001))
checks.append(("Flujo B present", "REANUD" in s001.upper() or "Flujo B" in s001))

# section 6 unique
sec6 = [h for h in headers if "sección 6" in h[1].lower() or "seccion 6" in h[1].lower()]
checks.append(("one Seccion 6 header", len(sec6) == 1))

# imports fixed
checks.append(("1.1 has sys", "import sys" in src(16)))
checks.append(("1.1b has os", "import os" in src(17)))

# orphan empty?
empties = [i for i, c in enumerate(cells) if not src(i).strip()]
checks.append(("no empty cells", len(empties) == 0))

# stale hard-coded run in 2.3 md
idx23md = next(i for i, c in enumerate(cells) if c["cell_type"]=="markdown" and "2.3" in src(i)[:40])
checks.append(("no hard-coded run in 2.3", "madrl_v3_20260627" not in src(idx23md)))

# 7.4 and 10 markdown
checks.append(("7.4 md present", any("7.4" in src(i)[:80] and c["cell_type"]=="markdown" for i,c in enumerate(cells))))
checks.append(("Seccion 10 md", any("Sección 10" in src(i) or "Seccion 10" in src(i) for i,c in enumerate(cells) if c["cell_type"]=="markdown")))

# escenario_2 stale
checks.append(("no escenario_2", not any("escenario_2" in src(i) for i in range(len(cells)))))

lines.append("CHECKS:")
all_ok = True
for name, ok in checks:
    lines.append(f"  [{'OK' if ok else 'FAIL'}] {name}")
    if not ok:
        all_ok = False

lines.append("")
lines.append("SECTION HEADERS:")
for i, h in headers:
    lines.append(f"  {i:03d}: {h}")

# Extract key snippets
lines.append("")
lines.append(f"--- cell 033 HAPPO_KPI head ---")
lines.append("\n".join(src(idx23).splitlines()[:12]))
lines.append(f"--- cell {idx61} SCHEMA/EXEC ---")
for ln in s61.splitlines():
    if "SCHEMA_PATH" in ln or "EXECUTION_MODE" in ln or "N_EPISODES" in ln or "QUICK_TEST" in ln:
        lines.append(ln)

lines.append(f"ALL_OK={all_ok}")
out.write_text("\n".join(lines), encoding="utf-8")
print(f"ALL_OK={all_ok} wrote {out}")
for name, ok in checks:
    if not ok:
        print("FAIL:", name)
