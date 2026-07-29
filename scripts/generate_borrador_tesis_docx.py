# -*- coding: utf-8 -*-
"""Compatibility entrypoint for borrador DOCX generator.

Compatibility wrapper after consolidation into tools/thesis/.
Canonical implementation: tools/thesis/generate_borrador_tesis_docx.py
"""
from __future__ import annotations

import runpy
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
_TARGET = _REPO / "tools/thesis/generate_borrador_tesis_docx.py"
if not _TARGET.is_file():
    raise SystemExit(f"Canonical script missing: {_TARGET}")
sys.argv[0] = str(_TARGET)
runpy.run_path(str(_TARGET), run_name="__main__")
