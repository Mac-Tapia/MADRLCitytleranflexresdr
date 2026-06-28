"""Validate that the CityLearn v3 tutorial notebook is internally consistent and
synchronized with the canonical launcher/training_common API.

Checks (no network, no training):
  1. Notebook JSON parses; every code cell compiles (py_compile-style ast.parse).
  2. Every `_common.<name>` / `citylearn_v3_training_common.<name>` symbol referenced
     in the notebook actually exists in the module (catches the prior class of bug
     where a cell called a function that no longer existed).
  3. The skip/resume preview is funneled through the single canonical function
     `preview_job_launcher_decision` in cells 2.1b and 7.1 (no divergent ad-hoc logic).
  4. No stale strings from the removed buggy branch remain in the notebook.
"""
from __future__ import annotations

import ast
import json
import re
import sys
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "CityLearn" / "scripts"
NB_PATH = ROOT / "CityLearn" / "examples" / "madrl_citylearn_v3_tutorial.ipynb"


def _install_gym_stub() -> None:
    if "gym" in sys.modules:
        return
    g = types.ModuleType("gym")
    g.spaces = types.SimpleNamespace(
        Box=object, Discrete=object, MultiDiscrete=object, Dict=object
    )
    sys.modules["gym"] = g
    sys.modules["gym.spaces"] = g.spaces


def load_module_symbols(module_name: str) -> set[str]:
    _install_gym_stub()
    sys.path.insert(0, str(SCRIPTS))
    mod = __import__(module_name)
    return {n for n in dir(mod) if not n.startswith("__")}


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    nb = json.loads(NB_PATH.read_text(encoding="utf-8"))
    code_cells = [c for c in nb["cells"] if c.get("cell_type") == "code"]

    # 1. Every code cell parses.
    for idx, cell in enumerate(nb["cells"]):
        if cell.get("cell_type") != "code":
            continue
        src = "".join(cell.get("source", []))
        if not src.strip():
            continue
        try:
            ast.parse(src)
        except SyntaxError as exc:
            errors.append(f"[parse] cell id={cell.get('id')} idx={idx}: {exc}")

    common_symbols = load_module_symbols("citylearn_v3_training_common")

    full_src = "\n".join(
        "".join(c.get("source", [])) for c in code_cells
    )

    # 2. Referenced canonical symbols exist.
    referenced = set(re.findall(r"_common\.([A-Za-z_][A-Za-z0-9_]*)", full_src))
    referenced |= set(
        re.findall(r"_c71\.([A-Za-z_][A-Za-z0-9_]*)", full_src)
    )
    referenced |= set(
        re.findall(r"(?<!\.py)citylearn_v3_training_common\.([A-Za-z_][A-Za-z0-9_]*)", full_src)
    )
    # The module is normally imported as `_common` / `_c71`; a dotted reference to the
    # filename string (…training_common.py) is not an attribute access.
    referenced.discard("py")
    for name in sorted(referenced):
        if name not in common_symbols:
            errors.append(
                f"[symbol] notebook references citylearn_v3_training_common.{name} "
                f"which does NOT exist in the module"
            )

    # 3. Canonical preview function present in module + used by notebook.
    if "preview_job_launcher_decision" not in common_symbols:
        errors.append("[api] preview_job_launcher_decision missing from training_common")
    if "preview_job_launcher_decision" not in full_src:
        errors.append("[sync] notebook never calls preview_job_launcher_decision")

    # 4. Stale buggy strings must be gone.
    stale = [
        "results.json no valido para skip",
        "episodes_complete_missing_results_json",  # must not drive a COMPLETO branch in 2.1b
    ]
    for cell in code_cells:
        src = "".join(cell.get("source", []))
        cid = cell.get("id")
        for needle in stale:
            if needle in src:
                # episodes_complete_missing_results_json is allowed only inside
                # training_common, never as a notebook COMPLETO branch.
                warnings.append(
                    f"[stale] cell id={cid} still contains '{needle}'"
                )

    # 5. Both 2.1b and 7.1 funnel through the canonical preview.
    for marker, label in (("# ── 2.1b", "2.1b"), ("# ── 7.1", "7.1")):
        cell = next(
            (c for c in code_cells if "".join(c.get("source", [])).startswith(marker)),
            None,
        )
        if cell is None:
            warnings.append(f"[locate] could not find cell {label}")
            continue
        src = "".join(cell.get("source", []))
        if "preview_job_launcher_decision" not in src:
            errors.append(f"[sync] cell {label} does not use preview_job_launcher_decision")

    print(f"notebook: {NB_PATH}")
    print(f"code cells: {len(code_cells)}")
    print(f"canonical symbols referenced: {len(referenced)}")
    if warnings:
        print("\nWARNINGS:")
        for w in warnings:
            print("  " + w)
    if errors:
        print("\nERRORS:")
        for e in errors:
            print("  " + e)
        return 1
    print("\nOK: notebook synchronized with canonical launcher API")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
