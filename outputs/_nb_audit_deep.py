# -*- coding: utf-8 -*-
"""Deep audit of madrl_citylearn_v3_tutorial.ipynb for duplicates/redundancy."""
import json
import re
from pathlib import Path
from collections import defaultdict

nb_path = Path(r"D:\MADRLCitytleranflexresdr\CityLearn\examples\madrl_citylearn_v3_tutorial.ipynb")
out_path = Path(r"D:\MADRLCitytleranflexresdr\outputs\_nb_audit_deep.txt")
nb = json.loads(nb_path.read_text(encoding="utf-8"))
cells = nb["cells"]

def src(i):
    return "".join(cells[i].get("source", []))

report = []
report.append("=" * 72)
report.append("DEEP AUDIT REPORT")
report.append("=" * 72)

# 1. Section headers
report.append("\n## SECTION HEADERS")
for i, c in enumerate(cells):
    if c["cell_type"] != "markdown":
        continue
    s = src(i)
    for ln in s.splitlines()[:5]:
        if ln.startswith("#"):
            report.append(f"  cell {i:03d}: {ln[:100]}")
            break

# 2. Key config variables and where defined/overwritten
KEYS = [
    "N_EPISODES", "LAUNCH_MODE", "TWO_PHASE", "two_phase", "PHASE",
    "ALGORITHMS", "OUTPUT_ROOT", "REPO_ROOT", "SCHEMA_PATH",
    "LAUNCH_FULL_TRAINING", "HAPPO_KPI_MODE", "RESCUE_MODE",
    "QUICK_TEST", "N_PARALLEL", "parallel_jobs", "TRAINING_PROFILE",
    "USE_GOOGLE_DRIVE", "PROJECT_PYTHON", "LAUNCHER",
]
report.append("\n## KEY VARIABLE MENTIONS")
for key in KEYS:
    hits = []
    for i, c in enumerate(cells):
        if c["cell_type"] != "code":
            continue
        s = src(i)
        if re.search(rf"\b{re.escape(key)}\b", s):
            # find assignment lines
            assigns = []
            for ln in s.splitlines():
                if re.search(rf"^\s*{re.escape(key)}\s*=", ln) or re.search(rf"\b{re.escape(key)}\s*=", ln):
                    assigns.append(ln.strip()[:120])
            hits.append((i, assigns[:5]))
    if hits:
        report.append(f"\n  {key}:")
        for i, assigns in hits:
            report.append(f"    cell {i:03d}: {assigns if assigns else '(referenced only)'}")

# 3. Duplicate function definitions across cells
report.append("\n## FUNCTION DEFINITIONS (code cells)")
func_map = defaultdict(list)
for i, c in enumerate(cells):
    if c["cell_type"] != "code":
        continue
    for m in re.finditer(r"^def\s+(\w+)\s*\(", src(i), re.M):
        func_map[m.group(1)].append(i)
for name, idxs in sorted(func_map.items()):
    if len(idxs) > 1:
        report.append(f"  DUPLICATE def {name}: cells {idxs}")
    elif name in ("render_mermaid", "load_all_results", "run_cmd", "monitor"):
        report.append(f"  def {name}: cell {idxs[0]}")

# 4. Import blocks - find repeated heavy import patterns
report.append("\n## REPEATED IMPORT PATTERNS")
import_sigs = defaultdict(list)
for i, c in enumerate(cells):
    if c["cell_type"] != "code":
        continue
    s = src(i)
    imps = sorted(set(re.findall(r"^(?:import|from)\s+[\w\.]+", s, re.M)))
    if len(imps) >= 4:
        sig = tuple(imps[:8])
        import_sigs[sig].append(i)
for sig, idxs in import_sigs.items():
    if len(idxs) > 1:
        report.append(f"  cells {idxs}: {list(sig)[:5]}...")

# 5. Look for contradictory comments / stale paths
report.append("\n## STALE / CONTRADICTORY PATTERNS")
PATTERNS = [
    (r"madrl_lima", "madrl_lima reference"),
    (r"citylearn_v2(?!_)", "v2 leftover?"),
    (r"TODO|FIXME|XXX|HACK", "TODO/FIXME"),
    (r"deprecated|obsoleto|legacy|LEGACY", "deprecated/legacy"),
    (r"no longer|ya no|borrar|eliminar esta", "removal language"),
    (r"duplicat|redundan", "duplicate mention"),
    (r"N_EPISODES\s*=\s*\d+", "N_EPISODES assignment"),
    (r"two_phase|TWO_PHASE|fase\s*[12]|phase\s*[12]", "two-phase mention"),
    (r"from.?scratch|desde.?cero|entrenamiento.?completo", "from-scratch mention"),
    (r"49.?50|complet[ae]r HAPPO", "HAPPO 49->50 one-off"),
]
for pat, label in PATTERNS:
    hits = []
    for i, c in enumerate(cells):
        s = src(i)
        ms = list(re.finditer(pat, s, re.I))
        if ms:
            hits.append((i, len(ms), ms[0].group(0)[:60]))
    if hits:
        report.append(f"\n  [{label}]")
        for i, n, sample in hits:
            report.append(f"    cell {i:03d} x{n}: ...{sample}...")

# 6. Cell size outliers and empty cells
report.append("\n## CELL SIZES / EMPTY")
for i, c in enumerate(cells):
    s = src(i).strip()
    n = len(s.splitlines())
    if not s:
        report.append(f"  EMPTY cell {i:03d}")
    elif n > 400:
        report.append(f"  LARGE cell {i:03d} [{c['cell_type']}] L={n}")

# 7. Outputs present? (bloat)
report.append("\n## CELLS WITH OUTPUTS")
with_out = 0
for i, c in enumerate(cells):
    outs = c.get("outputs") or []
    if outs:
        with_out += 1
        # summarize
        types = [o.get("output_type") for o in outs]
        report.append(f"  cell {i:03d}: {len(outs)} outputs types={types[:5]}")
report.append(f"  TOTAL with outputs: {with_out}/{len(cells)}")

# 8. Extract two-phase related snippets from cells 40-50
report.append("\n## TWO-PHASE / TRAINING CONFIG SNIPPETS")
for i in [40, 41, 42, 43, 44, 45, 46, 48, 49, 50]:
    s = src(i)
    report.append(f"\n--- cell {i:03d} ({cells[i]['cell_type']}) first/relevant ---")
    # print lines with phase/episode/algo/launch
    relevant = []
    for ln in s.splitlines():
        if re.search(r"phase|fase|N_EPISODES|LAUNCH|ALGORITH|two_phase|parallel|HAPPO|MASAC|MATD3|MAAC|PROFILE|SKIP|skip.completed", ln, re.I):
            relevant.append(ln[:140])
    for ln in relevant[:40]:
        report.append(f"  {ln}")
    if not relevant:
        report.append("  (no phase-related lines; showing first 15)")
        for ln in s.splitlines()[:15]:
            report.append(f"  {ln[:140]}")

out_path.write_text("\n".join(report), encoding="utf-8")
print(f"Wrote {out_path}")
print(f"Report lines: {len(report)}")
