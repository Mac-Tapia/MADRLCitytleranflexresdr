from __future__ import annotations

import configparser
import re
from pathlib import Path

import yaml


PROJECT_ROOT = Path(__file__).resolve().parents[2]
ROLES = PROJECT_ROOT / "governance/dependency_roles.yaml"
RUNTIME_SOURCES = ("uc3m", "CityLearn/citylearn", "CityLearn/scripts")


def _roles() -> dict:
    return yaml.safe_load(ROLES.read_text(encoding="utf-8"))["submodules"]


def _gitmodule_paths() -> set:
    parser = configparser.ConfigParser()
    parser.read(PROJECT_ROOT / ".gitmodules", encoding="utf-8")
    return {parser.get(section, "path") for section in parser.sections()}


def test_every_submodule_has_one_declared_role_with_evidence() -> None:
    roles = _roles()
    assert set(roles) == _gitmodule_paths()
    for path, entry in roles.items():
        assert entry["role"] in {"runtime", "reference_only"}, path
        assert str(entry.get("evidence", "")).strip(), path


def test_reference_only_submodules_are_not_imported_by_runtime_code() -> None:
    reference_only = [path for path, entry in _roles().items() if entry["role"] == "reference_only"]
    patterns = []
    for path in reference_only:
        name = Path(path).name
        patterns.append(re.compile(re.escape(path).replace("/", r"[/\\]")))
        patterns.append(re.compile(rf"^\s*(?:import|from)\s+{re.escape(name.lower())}\b", re.M))

    offending = []
    for source in RUNTIME_SOURCES:
        for file in (PROJECT_ROOT / source).rglob("*.py"):
            text = file.read_text(encoding="utf-8", errors="replace")
            if any(pattern.search(text) for pattern in patterns):
                offending.append(file.relative_to(PROJECT_ROOT).as_posix())
    assert offending == []
