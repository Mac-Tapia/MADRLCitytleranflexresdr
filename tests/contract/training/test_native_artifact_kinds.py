import json
from pathlib import Path
from types import SimpleNamespace

import torch

from uc3m.adapters.algorithms.native import NativeBackend
from uc3m.application.training.layout import normalize_scenario_dir


def test_recover_indexes_training_state_for_resume(tmp_path):
    schema = tmp_path / "schema.json"
    schema.write_text(json.dumps({"buildings": {"B1": {"include": True}}}), encoding="utf-8")
    spec = SimpleNamespace(
        algorithm="MAAC",
        scenario=SimpleNamespace(scenario_id="E1"),
        seed=42,
        target_episodes=2,
        episode_time_steps=24,
    )
    run_root = tmp_path / "run"
    checkpoints = run_root / normalize_scenario_dir("E1", 42) / "checkpoints"
    checkpoints.mkdir(parents=True)
    torch.save({"schema": "madrl.training_state.v1"}, checkpoints / "training_state.pt")

    result = NativeBackend(Path.cwd(), schema).recover(spec, run_root)

    kinds = {Path(a.relative_path).name: a.kind for a in result.artifacts}
    assert kinds["training_state.pt"] == "training_state"
