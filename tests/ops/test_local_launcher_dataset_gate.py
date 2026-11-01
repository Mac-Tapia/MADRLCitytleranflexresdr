"""FR-011.4: the local Windows launcher must pass the dataset gate before training."""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LAUNCHER_PS1 = ROOT / "scripts" / "restart_happo_masac_v3.ps1"
LAUNCHER_BAT = ROOT / "scripts" / "LANZAR_ENTRENAMIENTO_V4.bat"
SCHEMA = "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
LAUNCH_PATTERN = r"launch_citylearn_v3_official_training|train_citylearn_v3_"


def _code_lines(path: Path) -> list:
    """Return non-comment lines so a commented-out gate does not count."""
    return [line for line in path.read_text(encoding="utf-8-sig").splitlines()
            if not line.lstrip().startswith("#")]


def _first_index(lines: list, pattern: str) -> int:
    for index, line in enumerate(lines):
        if re.search(pattern, line):
            return index
    return -1


def test_bat_delegates_to_the_gated_powershell_launcher() -> None:
    text = LAUNCHER_BAT.read_text(encoding="utf-8")
    assert "scripts\\restart_happo_masac_v3.ps1" in text
    assert "launch_citylearn_v3_official_training" not in text
    assert "train_citylearn_v3_" not in text


def test_ps1_is_readable_by_windows_powershell() -> None:
    # powershell.exe 5.1 decodes BOM-less files as ANSI; a UTF-8 em dash then
    # becomes a closing quote and the whole launcher (gate included) fails to parse.
    raw = LAUNCHER_PS1.read_bytes()
    assert raw.startswith(b"\xef\xbb\xbf") or raw.isascii(), \
        "non-ASCII launcher must be saved as UTF-8 with BOM for powershell.exe"


def test_ps1_runs_dataset_gate_before_any_training_launch() -> None:
    lines = _code_lines(LAUNCHER_PS1)
    gate = _first_index(lines, r"require_validated_dataset")
    launch = _first_index(lines, LAUNCH_PATTERN)
    assert gate >= 0, "launcher never calls require_validated_dataset"
    assert launch >= 0, "launcher no longer launches training; update this test"
    assert gate < launch, "dataset gate must run before the training launch"


def test_ps1_gate_uses_project_python_and_the_trained_schema() -> None:
    text = "\n".join(_code_lines(LAUNCHER_PS1))
    assert ".venv39-citylearn-v3\\Scripts\\python.exe" in text
    assert "DEFAULT_READY_MANIFEST" in text
    assert SCHEMA.replace("/", "\\") in text or SCHEMA in text


def test_ps1_aborts_with_nonzero_exit_when_gate_fails() -> None:
    lines = _code_lines(LAUNCHER_PS1)
    gate = _first_index(lines, r"require_validated_dataset")
    launch = _first_index(lines, LAUNCH_PATTERN)
    assert 0 <= gate < launch
    between = "\n".join(lines[gate:launch])
    assert "$LASTEXITCODE" in between, "gate exit code is not read"
    failure_block = re.search(r"if\s*\(\s*\$\w+\s+-ne\s+0\s*\)\s*\{(?P<body>[^}]*)\}", between)
    assert failure_block, "gate exit code is not checked before the launch"
    assert re.search(r"\bexit\s+[1-9]\d*\b", failure_block.group("body")), \
        "a failed gate must abort with a non-zero exit code"
