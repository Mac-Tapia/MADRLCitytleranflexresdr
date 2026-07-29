#!/usr/bin/env python
"""Compat shim: CityLearn launch scripts still call tools/check_training_dataset_ready.py."""
from __future__ import annotations

import runpy
from pathlib import Path

_TARGET = Path(__file__).resolve().parent / "dataset" / "check_training_dataset_ready.py"
runpy.run_path(str(_TARGET), run_name="__main__")
