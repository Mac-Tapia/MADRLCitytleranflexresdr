#!/usr/bin/env python3
"""
Environment setup for Google Drive MCP skill.
"""

import os
import subprocess
import sys
import venv
from pathlib import Path


class SkillEnvironment:
    def __init__(self) -> None:
        self.skill_dir = Path(__file__).parent.parent
        self.venv_dir = self.skill_dir / ".venv"
        self.requirements_file = self.skill_dir / "requirements.txt"

        if os.name == "nt":
            self.venv_python = self.venv_dir / "Scripts" / "python.exe"
            self.venv_pip = self.venv_dir / "Scripts" / "pip.exe"
        else:
            self.venv_python = self.venv_dir / "bin" / "python"
            self.venv_pip = self.venv_dir / "bin" / "pip"

    def ensure_venv(self) -> bool:
        if not self.venv_dir.exists():
            print(f"Creating virtual environment in {self.venv_dir.name}/")
            try:
                venv.create(self.venv_dir, with_pip=True)
            except Exception as exc:
                print(f"Failed to create venv: {exc}")
                return False

        if not self.requirements_file.exists():
            return True

        print("Installing dependencies...")
        try:
            subprocess.run(
                [str(self.venv_pip), "install", "--upgrade", "pip"],
                check=True,
                capture_output=True,
                text=True,
            )
            subprocess.run(
                [str(self.venv_pip), "install", "-r", str(self.requirements_file)],
                check=True,
                capture_output=True,
                text=True,
            )
            print("Dependencies installed.")
            return True
        except subprocess.CalledProcessError as exc:
            print(f"Failed to install dependencies: {exc}")
            return False


def main() -> int:
    env = SkillEnvironment()
    if env.ensure_venv():
        print(f"Environment ready: {env.venv_python}")
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
