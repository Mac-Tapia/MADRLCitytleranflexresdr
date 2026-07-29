#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Orquestador del pipeline Word → 2 canónicos (Tesis + Informe).

Por defecto NO regenera la Tesis completa (protege ediciones manuales).
Use --regenerate para reconstruir desde generate_tesis_doctoral_final_docx.

Pasos:
  1) (opcional) regenerate Tesis
  2) update PG/PE/OE/H en los 2 canons
  3) patch Cap.3 cuasiexperimental en los 2 canons
  4) (opcional) update_word_quantitative → Informe
  5) sync Cap.5 Tesis → Informe
  6) verify --all-canons
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_THESIS_DIR = Path(__file__).resolve().parent
REPO = _THESIS_DIR.parents[1]
PY = sys.executable


def run_step(label: str, script: str, extra: list[str] | None = None) -> int:
    cmd = [PY, "-B", str(_THESIS_DIR / script), *(extra or [])]
    print(f"\n=== {label} ===")
    print(" ".join(cmd))
    proc = subprocess.run(cmd, cwd=str(REPO))
    return int(proc.returncode)


def main() -> int:
    parser = argparse.ArgumentParser(description="Pipeline Word tesis (2 canons)")
    parser.add_argument(
        "--regenerate",
        action="store_true",
        help="Regenerar Tesis desde generate_tesis_doctoral_final_docx (destructivo)",
    )
    parser.add_argument("--skip-generate", action="store_true", default=True, help=argparse.SUPPRESS)
    parser.add_argument("--sync-only", action="store_true", help="Solo sync Cap.5 + verify")
    parser.add_argument("--verify-only", action="store_true", help="Solo verify --all-canons")
    parser.add_argument("--with-quantitative", action="store_true", help="Correr update_word_quantitative")
    parser.add_argument("--dry-run-sync", action="store_true", help="Sync Cap.5 en dry-run")
    args = parser.parse_args()

    if args.verify_only:
        return run_step("verify all canons", "verify_tesis_doctoral_docx.py", ["--all-canons"])

    if args.sync_only:
        sync_args = ["--dry-run"] if args.dry_run_sync else []
        rc = run_step("sync Cap.5", "sync_cap5_to_canon_words.py", sync_args)
        if rc != 0:
            return rc
        return run_step("verify all canons", "verify_tesis_doctoral_docx.py", ["--all-canons"])

    steps: list[tuple[str, str, list[str]]] = []
    if args.regenerate:
        steps.append(("regenerate Tesis", "generate_tesis_doctoral_final_docx.py", []))
    steps.extend(
        [
            ("update PG/PE/OE/H", "update_pg_pe_oe_h_exact_docx.py", []),
            ("patch Cap.3 cuasiexperimental", "patch_cap3_cuasiexperimental_docx.py", []),
            ("patch Cap.4 implementación/validación", "patch_cap4_implementacion_docx.py", []),
        ]
    )
    if args.with_quantitative:
        steps.append(("update quantitative Informe", "update_word_quantitative_50episodes.py", []))
    sync_args = ["--dry-run"] if args.dry_run_sync else []
    steps.append(("sync Cap.5", "sync_cap5_to_canon_words.py", sync_args))
    steps.append(("verify all canons", "verify_tesis_doctoral_docx.py", ["--all-canons"]))

    for label, script, extra in steps:
        rc = run_step(label, script, extra)
        if rc != 0:
            print(f"FALLO en paso: {label} (exit={rc})")
            return rc
    print("\nPipeline OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
