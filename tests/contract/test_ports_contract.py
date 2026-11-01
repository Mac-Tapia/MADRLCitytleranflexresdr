from __future__ import annotations

import ast
from pathlib import Path

from uc3m.adapters.algorithms.native import NativeBackend
from uc3m.adapters.local_artifacts import LocalArtifactStore
from uc3m.ports import ArtifactStore, LearnerPort, SimulatorPort


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PORTS_DIR = PROJECT_ROOT / "uc3m/ports"
STDLIB_ALLOWED = {"__future__", "abc", "dataclasses", "pathlib", "typing"}


class _FakeSimulator:
    observation_space = None
    action_space = None

    def reset(self):
        return {}

    def step(self, actions):
        return {}, {}, {}, {}


def test_native_backend_satisfies_learner_port(tmp_path: Path) -> None:
    backend = NativeBackend(PROJECT_ROOT, tmp_path / "schema.json")
    assert isinstance(backend, LearnerPort)


def test_local_artifact_store_satisfies_artifact_store_port(tmp_path: Path) -> None:
    store = LocalArtifactStore(tmp_path, producer="contract-test")
    assert isinstance(store, ArtifactStore)


def test_simulator_port_is_checkable_structurally() -> None:
    assert isinstance(_FakeSimulator(), SimulatorPort)
    assert not isinstance(object(), SimulatorPort)


def test_ports_depend_only_on_stdlib_and_the_domain() -> None:
    offending = []
    for module in sorted(PORTS_DIR.glob("*.py")):
        tree = ast.parse(module.read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                names = [node.module or ""]
            elif isinstance(node, ast.Import):
                names = [alias.name for alias in node.names]
            else:
                continue
            for name in names:
                root = name.split(".")[0]
                allowed = root in STDLIB_ALLOWED or name.startswith(("uc3m.domain", "uc3m.ports"))
                if not allowed:
                    offending.append(f"{module.name}: {name}")
    assert offending == []
