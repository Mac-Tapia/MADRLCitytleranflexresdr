from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
INFRASTRUCTURE = {
    "citylearn",
    "gym",
    "gymnasium",
    "harl",
    "marllib",
    "pandas",
    "ray",
    "stable_baselines3",
    "torch",
}
OUTER_LAYERS = (
    "uc3m.adapters",
    "uc3m.algorithms",
    "uc3m.application",
    "uc3m.env",
    "uc3m.ports",
    "uc3m.presentation",
)
# Composition roots wire concrete adapters into application use cases.
COMPOSITION_ROOTS = {"uc3m/application/training/cli.py", "uc3m/application/training/colab.py"}


def _imports(module: Path):
    for node in ast.walk(ast.parse(module.read_text(encoding="utf-8"))):
        if isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            yield node.module
        elif isinstance(node, ast.Import):
            yield from (alias.name for alias in node.names)


def _violations(package: str, forbidden_prefixes, exempt=frozenset()):
    found = []
    for module in sorted((PROJECT_ROOT / package).rglob("*.py")):
        relative = module.relative_to(PROJECT_ROOT).as_posix()
        if relative in exempt:
            continue
        for name in _imports(module):
            if name.split(".")[0] in INFRASTRUCTURE or name.startswith(forbidden_prefixes):
                found.append(f"{relative}: {name}")
    return found


def test_domain_depends_on_no_infrastructure_or_outer_layer() -> None:
    assert _violations("uc3m/domain", OUTER_LAYERS) == []


def test_application_reaches_adapters_only_through_composition_roots() -> None:
    assert _violations("uc3m/application", ("uc3m.adapters",), COMPOSITION_ROOTS) == []
