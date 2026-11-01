"""Patch notebook: Sección 9 dual district+building selection."""
from __future__ import annotations

import json
from pathlib import Path

NB = Path("examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb")
nb = json.loads(NB.read_text(encoding="utf-8"))

MD_SEC9 = """## Sección 9: Evaluación estadística — OG / OE.1 / OE.2 / OE.3, dual distrito+edificio y Capa A (HE/H0G)

Protocolo alineado al título de tesis (desempeño algorítmico MADRL a **nivel distrito y edificio**) y a Cap. III–V / CityLearn v3 (`objectives.py`, **54 KPIs** OE):

1. **Baseline** — `evaluate_v2` embebido en cada corrida (mismo dataset Iquitos que el entrenamiento).
2. **Score descriptivo por escenario** — media del *signed relative gain* vs baseline (E1→OE.1, E2→OE.2, E3→OE.3).
3. **Ganador OE.k / OG** — ranking descriptivo distrito (celdas 9.1/9.2; no sustituye hipótesis).
4. **Selección dual distrito + edificio (9.3)** — `tools/eval/select_best_madrl_district_building.py` sobre `kpi_rankings_drive50/` (mejor MADRL distrito OG, ganadores OE, mejor MADRL edificio, coherencia).
5. **Capa A (9.4, decisión HE/H0G)** — Shapiro–Wilk → **Friedman pareado + Kendall W + Wilcoxon/Holm** (principal); Kruskal–Wallis / Mann–Whitney solo exploratorio. Unidad = KPI-gains (no episodios como réplicas).
6. **Salidas** — `{OUTPUT_ROOT}/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` + `pe_answers_audit.json`.

> Con `SEED=0` (campaña canónica) la inferencia es **exploratoria**. `MULTI_SEED_TRAINING=True` habilita réplicas independientes (`N_SEEDS=12`).
"""

MD_93 = """### 9.3 Selección dual distrito + edificio

Responde al título de tesis: qué MADRL (HAPPO / MASAC / MATD3 / MAAC) gestiona mejor energía multiobjetivo a **nivel distrito** y a **nivel edificio**.

- **Distrito:** ganador por escenario OE desde `district_ranking_by_scenario.csv`; OG = mayoría de victorias OE (desempate E1).
- **Edificio:** por cada edificio×OE el MADRL con mejor KPI primario; ganador global = más victorias en 17×3.
- **Artefactos:** `best_madrl_district_building_report.json`, `madrl_wins_per_building.csv`, `madrl_building_win_counts.csv` bajo `kpi_rankings_drive50/`.

Requiere tablas Drive-50 (`compute_drive50_district_building_kpi_rankings.py` o Sección 8 completa). Si faltan, la celda avisa sin fallar el notebook.
"""

CODE_93 = r'''# ── 9.3  Selección dual distrito + edificio (tesis) ───────────────────────────
# Mejor MADRL a nivel distrito (OG + OE) y a nivel edificio (victorias 17×3).
import importlib.util
import sys
from pathlib import Path

_repo = Path(str(globals().get("REPO", globals().get("REPO_DIR", Path.cwd()))))
if not (_repo / "tools" / "eval" / "select_best_madrl_district_building.py").is_file():
    for _cand in (Path.cwd(), Path.cwd().parent, _repo.parent):
        if (_cand / "tools" / "eval" / "select_best_madrl_district_building.py").is_file():
            _repo = _cand
            break

_out = Path(str(globals().get("OUTPUT_ROOT", _repo / "outputs" / "madrl_v3_20260627_164047")))
_script = _repo / "tools" / "eval" / "select_best_madrl_district_building.py"
_rank_dir = _out / "resumen_comparativo" / "multiobjetivo" / "kpi_rankings_drive50"
_need = (
    _rank_dir / "district_ranking_by_scenario.csv",
    _rank_dir / "building_kpis_4madrl.csv",
)

print("=" * 68)
print("9.3  SELECCIÓN DUAL MADRL — DISTRITO + EDIFICIO")
print("=" * 68)
print(f"  OUTPUT_ROOT : {_out}")
print(f"  rankings    : {_rank_dir}")

if not _script.is_file():
    print(f"[9.3] AVISO: no se encontró {_script}")
elif not all(p.is_file() for p in _need):
    missing = [str(p.name) for p in _need if not p.is_file()]
    print("[9.3] Faltan tablas kpi_rankings_drive50:", ", ".join(missing))
    print("      Ejecuta tools/eval/compute_drive50_district_building_kpi_rankings.py")
    print("      o completa Sección 8 / post-proceso Drive-50 antes de 9.3.")
else:
    if str(_repo) not in sys.path:
        sys.path.insert(0, str(_repo))
    _spec = importlib.util.spec_from_file_location(
        "select_best_madrl_district_building", _script
    )
    _mod = importlib.util.module_from_spec(_spec)
    assert _spec.loader is not None
    _spec.loader.exec_module(_mod)
    _report = _mod.run_selection(output_root=_out)
    _v = _report["veredicto"]
    print(f"  Distrito OG : {_v['mejor_madrl_distrito_OG']}")
    for _sc, _w in (_v.get("ganadores_OE_distrito") or {}).items():
        print(f"  Distrito {_sc}: {_w}")
    print(f"  Edificio    : {_v['mejor_madrl_edificio']}")
    print(f"  Coherente   : {_v['coherente_distrito_edificio']}")
    _arts = _report.get("_artifacts", {})
    print(f"  Report      : {_arts.get('report_json')}")
    print(f"  Wins CSV    : {_arts.get('wins_per_building_csv')}")
    print(f"  Counts CSV  : {_arts.get('win_counts_csv')}")
    globals()["BEST_MADRL_DUAL_REPORT"] = _report
    globals()["BEST_MADRL_DISTRICT_OG"] = _v.get("mejor_madrl_distrito_OG")
    globals()["BEST_MADRL_BUILDING"] = _v.get("mejor_madrl_edificio")
print("=" * 68)
'''


def to_source_lines(text: str) -> list[str]:
    if not text.endswith("\n"):
        text += "\n"
    lines = text.splitlines(keepends=True)
    return lines


# --- locate cells ---
idx_md = idx_code = idx_9b = None
for i, c in enumerate(nb["cells"]):
    src = "".join(c.get("source", []))
    if src.startswith("## Sección 9:") and "OG / OE" in src:
        idx_md = i
    if "9.1  Ranking OE-completo" in src and src.lstrip().startswith("import subprocess"):
        idx_code = i
    if src.startswith("## Sección 9b:"):
        idx_9b = i

assert idx_md is not None, "Sección 9 markdown not found"
assert idx_code is not None, "9.1/9.2 code not found"
assert idx_9b is not None, "9b not found"
assert idx_code == idx_md + 1, (idx_md, idx_code)
assert idx_9b == idx_code + 1 or "### 9.3 Selección dual" in "".join(
    nb["cells"][idx_code + 1].get("source", [])
), (idx_code, idx_9b)

# 1) Update Sección 9 markdown
nb["cells"][idx_md]["source"] = to_source_lines(MD_SEC9)

# 2) Renumber Capa A 9.3 -> 9.4 inside ranking code cell
code_src = "".join(nb["cells"][idx_code]["source"])
replacements = [
    (
        "la inferencia HE/H0G es Capa A (9.3) sobre KPI-gains",
        "la inferencia HE/H0G es Capa A (9.4) sobre KPI-gains",
    ),
    (
        "# ── 9.3  Capa A Cap.5: HE/H0G desde results del entrenamiento (mismo OUTPUT_ROOT) ──",
        "# ── 9.4  Capa A Cap.5: HE/H0G desde results del entrenamiento (mismo OUTPUT_ROOT) ──",
    ),
    ('print(f"[9.3] AVISO:', 'print(f"[9.4] AVISO:'),
    ('print("[9.3] Pipeline', 'print("[9.4] Pipeline'),
    ('print(f"[9.3] OK Capa A', 'print(f"[9.4] OK Capa A'),
    ('print(f"[9.3] Decisiones', 'print(f"[9.4] Decisiones'),
    ('print(f"[9.3] pe_answers', 'print(f"[9.4] pe_answers'),
    ('print(f"[9.3] No se pudo', 'print(f"[9.4] No se pudo'),
    ('print(f"[9.3] FALLO', 'print(f"[9.4] FALLO'),
    (
        'print("[9.3] RUN_CAPA_A_HYPOTHESIS=False',
        'print("[9.4] RUN_CAPA_A_HYPOTHESIS=False',
    ),
]
for old, new in replacements:
    if old not in code_src:
        raise SystemExit(f"Missing expected snippet in code cell:\n{old}")
    code_src = code_src.replace(old, new)
nb["cells"][idx_code]["source"] = to_source_lines(code_src)

# 3) Insert or replace dual 9.3 cells before 9b
insert_at = idx_code + 1
already = False
if insert_at < len(nb["cells"]):
    nxt = "".join(nb["cells"][insert_at].get("source", []))
    if "### 9.3 Selección dual distrito + edificio" in nxt:
        already = True
        nb["cells"][insert_at]["source"] = to_source_lines(MD_93)
        if insert_at + 1 < len(nb["cells"]) and "9.3  SELECCIÓN DUAL" in "".join(
            nb["cells"][insert_at + 1].get("source", [])
        ):
            nb["cells"][insert_at + 1]["source"] = to_source_lines(CODE_93)
        else:
            nb["cells"].insert(
                insert_at + 1,
                {
                    "cell_type": "code",
                    "metadata": {},
                    "source": to_source_lines(CODE_93),
                    "outputs": [],
                    "execution_count": None,
                },
            )

if not already:
    nb["cells"].insert(
        insert_at,
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": to_source_lines(MD_93),
            "id": "sec93_dual_md",
        },
    )
    nb["cells"].insert(
        insert_at + 1,
        {
            "cell_type": "code",
            "metadata": {},
            "source": to_source_lines(CODE_93),
            "outputs": [],
            "execution_count": None,
            "id": "sec93_dual_code",
        },
    )

# 4) Optional intro tighten: Ranking row mentions dual selection
intro = "".join(nb["cells"][0].get("source", []))
old_rank = "| Ranking | *signed relative gain* vs baseline; **OG** = media de scores E1/E2/E3 |\n"
new_rank = (
    "| Ranking | *signed relative gain* vs baseline; **OG** distrito; "
    "**dual distrito+edificio** (9.3) |\n"
)
if old_rank in intro:
    intro = intro.replace(old_rank, new_rank)
    nb["cells"][0]["source"] = to_source_lines(intro)

# 5) Supervision / closing refs: Capa A sección 9.3 -> 9.4
for c in nb["cells"]:
    src = "".join(c.get("source", []))
    if "sección **9.3** → `problemas_objetivos_hipotesis/" in src:
        src = src.replace(
            "sección **9.3** → `problemas_objetivos_hipotesis/",
            "sección **9.4** → `problemas_objetivos_hipotesis/",
        )
        c["source"] = to_source_lines(src)

NB.write_text(json.dumps(nb, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

# Verify
nb2 = json.loads(NB.read_text(encoding="utf-8"))
found = []
for i, c in enumerate(nb2["cells"]):
    s = "".join(c.get("source", []))
    if "### 9.3 Selección dual" in s:
        found.append(("md93", i))
    if "9.3  SELECCIÓN DUAL MADRL" in s:
        found.append(("code93", i))
    if "Selección dual distrito + edificio (9.3)" in s:
        found.append(("sec9md", i))
    if "# ── 9.4  Capa A Cap.5" in s:
        found.append(("capa94", i))
print("OK patched:", found)
print("total cells:", len(nb2["cells"]))
