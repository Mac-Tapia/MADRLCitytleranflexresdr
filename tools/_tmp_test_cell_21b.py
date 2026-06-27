"""Validate notebook cell 2.1b: robust + SYMMETRIC across all 4 MADRL.

- Notebook valid JSON; cell parses as Python.
- Simulated fake OUTPUT_ROOT exercises ALL 12 jobs (4 algos x 3 scenarios) so we
  prove the cell treats HAPPO/MASAC/MATD3/MAAC identically (no algo preference),
  resolves the launcher's canonical UPPERCASE dir, and classifies correctly.
"""
import ast
import io
import json
import sys
import tempfile
from contextlib import redirect_stdout
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NB = ROOT / "CityLearn" / "examples" / "madrl_citylearn_v3_tutorial.ipynb"
failures = []


def check(name, cond):
    print(f"[{'OK ' if cond else 'FAIL'}] {name}")
    if not cond:
        failures.append(name)


nb = json.loads(NB.read_text(encoding="utf-8"))
check("notebook valid json", True)
cell = next(c for c in nb["cells"] if c.get("id") == "d4fc71c1")
src = "".join(cell["source"])
try:
    ast.parse(src)
    check("cell 2.1b parses as python", True)
except SyntaxError as exc:
    check(f"cell 2.1b parses ({exc})", False)

check("iterates all 4 MADRL", "['happo', 'masac', 'matd3', 'maac']" in src)
check("symmetric uppercase resolution", "algo.upper()" in src)
check("no algo-specific special-casing in resolver",
      "if algo ==" not in src.split("def _find_dir")[1].split("def _has_results")[0])

ALGOS = ["happo", "masac", "matd3", "maac"]
SCENS = ["E1", "E2", "E3"]

with tempfile.TemporaryDirectory() as tmp:
    out = Path(tmp) / "madrl_v3_test"
    # For EACH algo: E1=COMPLETO (uppercase data/results.json),
    #               E2=REANUDABLE (checkpoint .pt), E3=PENDIENTE (empty)
    for a in ALGOS:
        A = a.upper()
        (out / A / "E1" / "data").mkdir(parents=True)
        (out / A / "E1" / "data" / "results.json").write_text("{}", encoding="utf-8")
        (out / A / "E2" / "checkpoints" / "models").mkdir(parents=True)
        (out / A / "E2" / "checkpoints" / "models" / "agent0.pt").write_text("x", encoding="utf-8")
        (out / A / "E3").mkdir(parents=True)

    g = {
        "OUTPUT_ROOT": str(out),
        "RESUME_OUTPUT_ROOT": str(out),
        "N_EPISODES": 50,
        "EPISODE_STEPS": 8760,
        "CODE_ROOT": str(ROOT),
        "REPO": str(ROOT),
        "__name__": "__cell_21b__",
    }
    buf = io.StringIO()
    ran = True
    try:
        with redirect_stdout(buf):
            exec(compile(src, "cell_2_1b", "exec"), g, g)
    except Exception as exc:  # noqa: BLE001
        ran = False
        print("    EXC:", type(exc).__name__, exc)
    output = buf.getvalue()
    print("---- cell output ----\n" + output + "\n---------------------")
    check("cell executed without crash", ran)

    # Symmetry: every algo must show COMPLETO for E1, REANUDABLE for E2, PENDIENTE for E3.
    for a in ALGOS:
        A = a.upper()
        for esc, expect in (("E1", "COMPLETO"), ("E2", "REANUDABLE"), ("E3", "PENDIENTE")):
            line = next((ln for ln in output.splitlines()
                         if ln.strip().startswith(f"{A:<6} {esc}".strip())
                         or ln.strip().startswith(f"{A} {esc}")
                         or (A in ln and f" {esc} " in ln)), "")
            check(f"{A}/{esc} -> {expect}", expect in line)

    check("totals: COMPLETOS=4", "COMPLETOS=4" in output)
    check("totals: REANUDABLES=4", "REANUDABLES=4" in output)
    check("totals: PENDIENTES=4", "PENDIENTES=4" in output)
    # 4 complete jobs * 50 ep = 200 / 600 = 33.3%
    check("global progress ~200/600", "200/600" in output)

if failures:
    print("\nFAILURES:", failures)
    sys.exit(1)
print("\nALL CHECKS PASSED")
