"""Unit tests for intra-job Colab resume planning."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CityLearn" / "scripts"))

from citylearn_v3_training_common import (  # noqa: E402
    build_jobs_resume_report,
    discover_job_resume_plan,
    infer_completed_episodes_from_live_progress,
    job_counts_as_launcher_complete,
    job_has_final_results,
    preview_job_launcher_decision,
    resolve_job_run_dir,
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
    # global_step is the 0-indexed pre-increment counter: the final step of episode
    # index 49 is stored as 50*8760-1 and must count as 50 complete (the 49/50 bug).
    assert infer_completed_episodes_from_live_progress(
        {"global_step": 50 * 8760 - 1, "episode": 49, "episode_step": 8759},
        episode_time_steps=8760,
        algorithm="happo",
    ) == 50


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


def test_happo_recovered_from_timeseries_global_step_with_rollout_threads(tmp_path: Path):
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    rollout_threads = 12
    episode_time_steps = 8760
    target = 50
    max_gs = target * episode_time_steps
    rows = [
        {"episode": "0", "episode_step": "0", "global_step": str(max_gs), "all_done": "True"},
    ]
    import csv

    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "episodes_recorded": 1,
                "hyperparameters": {
                    "target_episodes": 50,
                    "episodes": 50,
                    "n_rollout_threads": rollout_threads,
                    "run_completed_with_salvage": True,
                },
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True
    assert (data / "job_launcher_complete.json").is_file()


def test_happo_fifty_episodes_at_all_done_boundary(tmp_path: Path):
    """Real HAPPO tail: max global_step is target*8760-1 and HAPPO writes all_done=False.

    Completion must be derived from the 0-indexed global_step budget, not the flag.
    """
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    rollout_threads = 12
    episode_time_steps = 8760
    target = 50
    last_episode = target - 1
    max_gs = (target * episode_time_steps) - 1
    import csv

    rows = [
        {
            "episode": str(last_episode),
            "episode_step": str(episode_time_steps - 1),
            "global_step": str(max_gs),
            "all_done": "False",
        },
    ]
    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "episodes_recorded": 49,
                "hyperparameters": {
                    "target_episodes": 50,
                    "episodes": 50,
                    "n_rollout_threads": rollout_threads,
                    "run_completed_with_salvage": True,
                },
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True
    dec = preview_job_launcher_decision(
        tmp_path,
        algorithm="happo",
        target_episodes=50,
        episode_time_steps=episode_time_steps,
        rollout_threads=rollout_threads,
    )
    assert dec["skip"] is True
    assert dec["action"] == "skip"
    assert "COMPLETO" in dec["status_line"]


def test_masac_salvage_fifty_episodes_at_all_done_boundary(tmp_path: Path):
    """MASAC salvage path must also recognize 50/50 at the global_step tail (no 49/50)."""
    data = tmp_path / "data"
    models = tmp_path / "checkpoints" / "models"
    data.mkdir(parents=True)
    models.mkdir(parents=True)
    (models / "100_rnn_net_params.pkl").write_bytes(b"x")
    (models / "100_qmix_net_params.pkl").write_bytes(b"x")
    episode_time_steps = 8760
    target = 50
    max_gs = (target * episode_time_steps) - 1
    import csv

    rows = [
        {
            "episode": str(target - 1),
            "episode_step": str(episode_time_steps - 1),
            "global_step": str(max_gs),
            "all_done": "False",
        },
    ]
    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MASAC",
                "status": "completed_with_salvage",
                "episodes_recorded": 49,
                "hyperparameters": {
                    "target_episodes": 50,
                    "episodes": 50,
                    "run_completed_with_salvage": True,
                },
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True


def test_happo_inflated_csv_resumes_from_global_step(tmp_path: Path):
    """CSV episode-index can claim 50 ep while global_step proves only 4 (rollout_threads=12)."""
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    rollout_threads = 12
    episode_time_steps = 8760
    max_gs = 4 * episode_time_steps
    import csv

    rows = [
        {"episode": "49", "episode_step": "0", "global_step": str(max_gs), "all_done": "True"},
    ]
    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "episodes_recorded": 4,
                "hyperparameters": {
                    "target_episodes": 50,
                    "episodes": 50,
                    "n_rollout_threads": rollout_threads,
                },
            }
        ),
        encoding="utf-8",
    )
    plan = discover_job_resume_plan(
        tmp_path,
        algorithm="happo",
        target_episodes=50,
        episode_time_steps=episode_time_steps,
        rollout_threads=rollout_threads,
    )
    assert plan["active"] is True
    assert plan["completed_episodes"] == 4
    assert plan["remaining_episodes"] == 46
    assert plan["note"] == "resume_from_checkpoint"


def test_preview_matches_skip_for_complete_masac(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MASAC",
                "episodes_recorded": 50,
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    dec = preview_job_launcher_decision(
        tmp_path, algorithm="masac", target_episodes=50, episode_time_steps=8760
    )
    assert dec["skip"] is True
    assert dec["action"] == "skip"
    assert "se omite" in dec["status_line"]


def test_preview_happo_salvage_resumes_not_complete(tmp_path: Path):
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    rollout_threads = 12
    max_gs = 4 * 8760
    import csv

    rows = [
        {"episode": "49", "episode_step": "0", "global_step": str(max_gs), "all_done": "True"},
    ]
    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "episodes_recorded": 4,
                "hyperparameters": {
                    "target_episodes": 50,
                    "episodes": 50,
                    "n_rollout_threads": rollout_threads,
                },
            }
        ),
        encoding="utf-8",
    )
    dec = preview_job_launcher_decision(
        tmp_path,
        algorithm="happo",
        target_episodes=50,
        episode_time_steps=8760,
        rollout_threads=rollout_threads,
    )
    assert dec["skip"] is False
    assert dec["action"] == "resume"
    assert dec["completed_episodes"] == 4
    assert "not skipping" in dec["launcher_line"]
    assert "COMPLETO" not in dec["status_line"]


def test_happo_stale_live_progress_does_not_inflate_resume(tmp_path: Path):
    """Stale live_progress.episode after preload must not block skip when artifacts prove 50/50."""
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    episode_time_steps = 8760
    target = 50
    max_gs = target * episode_time_steps
    import csv

    rows = [
        {
            "episode": str(target - 1),
            "episode_step": str(episode_time_steps - 1),
            "global_step": str(max_gs - 1),
            "all_done": "True",
        },
    ]
    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (tmp_path / "live_progress.json").write_text(
        json.dumps(
            {
                "global_step": max_gs - 1,
                "episode": target - 1,
                "episode_step": episode_time_steps - 1,
                "completed_episode_count": target,
                "algorithm": "HAPPO",
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=target) is True
    dec = preview_job_launcher_decision(
        tmp_path,
        algorithm="happo",
        target_episodes=target,
        episode_time_steps=episode_time_steps,
        rollout_threads=12,
    )
    assert dec["skip"] is True
    assert dec["action"] == "skip"


def test_happo_live_progress_episode_ahead_of_global_step(tmp_path: Path):
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    (tmp_path / "live_progress.json").write_text(
        json.dumps({"global_step": 35040, "episode": 49, "episode_step": 0}),
        encoding="utf-8",
    )
    plan = discover_job_resume_plan(
        tmp_path,
        algorithm="happo",
        target_episodes=50,
        episode_time_steps=8760,
        rollout_threads=12,
    )
    assert plan["active"] is True
    assert plan["completed_episodes"] == 4
    assert plan["remaining_episodes"] == 46


def test_build_jobs_resume_report_counts(tmp_path: Path):
    """build_jobs_resume_report aggregates skip/resume/pending across the 12 jobs."""
    import csv

    # MASAC/E1 complete (50/50) -> skip.
    masac = resolve_job_run_dir(tmp_path, "masac", "E1", 0)
    (masac / "data").mkdir(parents=True, exist_ok=True)
    (masac / "data" / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MASAC",
                "episodes_recorded": 50,
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )

    # HAPPO/E1 salvage at 4/50 -> resume.
    happo = resolve_job_run_dir(tmp_path, "happo", "E1", 0)
    (happo / "data").mkdir(parents=True, exist_ok=True)
    ckpt = happo / "checkpoints" / "gym" / "run"
    ckpt.mkdir(parents=True, exist_ok=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    with (happo / "data" / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["episode", "episode_step", "global_step", "all_done"])
        writer.writeheader()
        writer.writerow(
            {"episode": "49", "episode_step": "0", "global_step": str(4 * 8760), "all_done": "True"}
        )
    (happo / "data" / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "episodes_recorded": 4,
                "hyperparameters": {"target_episodes": 50, "episodes": 50, "n_rollout_threads": 12},
            }
        ),
        encoding="utf-8",
    )

    report = build_jobs_resume_report(
        tmp_path, target_episodes=50, episode_time_steps=8760, happo_rollout_threads=12
    )
    assert len(report["jobs"]) == 12
    assert report["completed"] == 1
    assert report["resumable"] == 1
    assert report["pending"] == 10
    assert report["episodes_done"] == 50 + 4
    assert report["episodes_target"] == 12 * 50


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
    with tempfile.TemporaryDirectory() as td:
        test_happo_recovered_from_timeseries_global_step_with_rollout_threads(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_happo_fifty_episodes_at_all_done_boundary(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_masac_salvage_fifty_episodes_at_all_done_boundary(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_happo_inflated_csv_resumes_from_global_step(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_preview_matches_skip_for_complete_masac(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_preview_happo_salvage_resumes_not_complete(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_happo_stale_live_progress_does_not_inflate_resume(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_happo_live_progress_episode_ahead_of_global_step(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_build_jobs_resume_report_counts(Path(td))
    print("OK: test_job_resume_state")
