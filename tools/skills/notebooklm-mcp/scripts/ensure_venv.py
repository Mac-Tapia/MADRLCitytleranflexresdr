#!/usr/bin/env python3
"""Crea el venv del MCP si no existe (usado por el launcher)."""

import subprocess
import sys
from pathlib import Path


def main() -> int:
    skill_dir = Path(__file__).parent.parent
    setup = skill_dir / "scripts" / "setup_environment.py"
    result = subprocess.run([sys.executable, str(setup)], check=False)
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
