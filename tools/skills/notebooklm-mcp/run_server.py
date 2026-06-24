#!/usr/bin/env python3
"""
Launcher del servidor MCP NotebookLM.
Crea/activa el venv local y ejecuta server.py con el Python correcto.
"""

import subprocess
import sys
from pathlib import Path


def venv_python(skill_dir: Path) -> Path:
    if sys.platform == "win32":
        return skill_dir / ".venv" / "Scripts" / "python.exe"
    return skill_dir / ".venv" / "bin" / "python"


def main() -> int:
    skill_dir = Path(__file__).parent.resolve()
    py = venv_python(skill_dir)

    if not py.exists():
        setup = skill_dir / "scripts" / "setup_environment.py"
        rc = subprocess.run([sys.executable, str(setup)], check=False).returncode
        if rc != 0 or not py.exists():
            print("Error: no se pudo crear el entorno virtual.", file=sys.stderr)
            return 1

    server = skill_dir / "server.py"
    return subprocess.run([str(py), str(server)], check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
