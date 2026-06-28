"""Unit tests for intra-job Colab resume planning."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CityLearn" / "scripts"))

from citylearn_v3_training_common import (  # noqa: E402
    discover_job_resume_plan,
    infer_completed_episodes_from_live_progress,
    job_counts_as_launcher_complete,
    job_has_final_results,
)


def test_infer_completed_episodes():
    assert infer_completed_episodes_from_live_progress(
        {"global_step": 0, "episode": 0}, episode_time_steps=8760
    ) == 0
    assert infer_completed_episodes_from_live_progress(
        {"global_step": 8760, "episode": 1, "episode_step": 0}, episode_time_steps=8760
    ) == 1
    assert infer_completed_episodes_from_live_progress(
        {"global_step": 13000, "episode": 1, "episode_step": 4240}, episode_time_steps=8760
    ) == 1


def test_discover_resume_without_artifacts(tmp_path: Path):
    plan = discover_job_resume_plan(
        tmp_path,
        algorithm="happo",
        target_episodes=50,
        episode_time_steps=8760,
    )
    assert plan["active"] is False


def test_discover_resume_with_live_progress(tmp_path: Path):
    (tmp_path / "live_progress.json").write_text(
        json.dumps({"global_step": 87600, "episode": 10, "episode_step": 0}),
        encoding="utf-8",
    )
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    plan = discover_job_resume_plan(
        tmp_path,
        algorithm="happo",
        target_episodes=50,
        episode_time_steps=8760,
    )
    assert plan["active"] is True
    assert plan["completed_episodes"] == 10
    assert plan["remaining_episodes"] == 40


def test_job_complete_blocks_resume(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "results.json").write_text("{}", encoding="utf-8")
    assert job_has_final_results(tmp_path)
    plan = discover_job_resume_plan(
        tmp_path,
        algorithm="happo",
        target_episodes=50,
        episode_time_steps=8760,
    )
    assert plan["active"] is False


def test_maac_inflated_results_json_not_complete(tmp_path: Path):
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    for episode in range(1, 10):
        (ckpt / f"checkpoint_episode_{episode}.pt").write_bytes(b"x")
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MAAC",
                "episodes_recorded": 50,
                "episode_summaries": [{"episode": i, "steps": 8760} for i in range(50)],
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is False
    plan = discover_job_resume_plan(
        tmp_path,
        algorithm="maac",
        target_episodes=50,
        episode_time_steps=8760,
    )
    assert plan["active"] is True
    assert plan["completed_episodes"] == 9
    assert plan["remaining_episodes"] == 41


def test_maac_full_checkpoints_count_as_complete(tmp_path: Path):
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "checkpoint_episode_50.pt").write_bytes(b"x")
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MAAC",
                "episodes_recorded": 50,
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True


def test_happo_results_json_trusted_when_timeseries_low(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "episodes_recorded": 50,
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    # No timeseries/checkpoints: non-MAAC should still trust a clean results.json.
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True


def test_maac_complete_without_per_episode_checkpoints(tmp_path: Path):
    # MAAC finished (results.json valid) but only a rolling model.pt remains (no
    # checkpoint_episode_N.pt). max_ckpt==0 -> trust results.json instead of demoting.
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "model.pt").write_bytes(b"x")
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MAAC",
                "episodes_recorded": 50,
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True


def test_salvage_results_json_not_complete(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "episodes_recorded": 50,
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is False


if __name__ == "__main__":
    test_infer_completed_episodes()
    test_discover_resume_without_artifacts(Path("outputs/_test_resume_empty"))
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_discover_resume_with_live_progress(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_job_complete_blocks_resume(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_maac_inflated_results_json_not_complete(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_maac_full_checkpoints_count_as_complete(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_happo_results_json_trusted_when_timeseries_low(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_maac_complete_without_per_episode_checkpoints(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_salvage_results_json_not_complete(Path(td))
    print("OK: test_job_resume_state")
