"""Unit tests for intra-job Colab resume planning."""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CityLearn" / "scripts"))

from citylearn_v3_training_common import (  # noqa: E402
    build_jobs_resume_report,
    clamp_happo_n_rollout_threads,
    discover_job_resume_plan,
    infer_completed_episodes_from_live_progress,
    job_counts_as_launcher_complete,
    job_has_final_results,
    job_run_dir_for_launcher,
    preview_job_launcher_decision,
    recommend_happo_rollout_threads,
    resolve_existing_job_run_dir,
    resolve_job_rollout_threads,
    resolve_job_run_dir,
)


def test_clamp_happo_rollout_threads():
    assert recommend_happo_rollout_threads(usable_vcpus=12) == 2
    assert recommend_happo_rollout_threads(usable_vcpus=26) == 4
    assert clamp_happo_n_rollout_threads(12, usable_vcpus=12) == 2
    assert clamp_happo_n_rollout_threads(12, fallback=2, usable_vcpus=48) == 4


def test_resolve_job_rollout_threads_clamps_salvage(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "hyperparameters": {"n_rollout_threads": 12},
            }
        ),
        encoding="utf-8",
    )
    assert resolve_job_rollout_threads(tmp_path, "happo", fallback=2) == 2


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
                "citylearn_v3_report": {"all_values": {"cost": 1.0}},
                "artifact_audit": {"episode_summaries": [{}] * 50},
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True


def test_happo_results_json_trusted_when_timeseries_low(tmp_path: Path):
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "episodes_recorded": 50,
                "citylearn_v3_report": {"all_values": {"cost": 1.0}},
                "artifact_audit": {"episode_summaries": [{}] * 50},
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True


def test_maac_complete_without_per_episode_checkpoints(tmp_path: Path):
    # MAAC finished (results.json + KPI audit) but only a rolling model.pt remains.
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
                "citylearn_v3_report": {"all_values": {"cost": 1.0}},
                "artifact_audit": {"episode_summaries": [{}] * 50},
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


def test_salvage_results_json_complete_with_checkpoints(tmp_path: Path):
    data = tmp_path / "data"
    ckpt = tmp_path / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "episodes_recorded": 50,
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
    dec = preview_job_launcher_decision(
        tmp_path, algorithm="happo", target_episodes=50, episode_time_steps=8760
    )
    assert dec["skip"] is True
    assert dec["action"] == "skip"


def test_happo_colab_salvage_49_inferred_launcher_exit0(tmp_path: Path):
    """Reproduce Colab 2.1b: salvage + inferred 49 + launcher exit 0 must skip (not 49/50 loop)."""
    import csv

    run_root = tmp_path / "madrl_v3_20260627_164047"
    job_dir = run_root / "happo" / "E1_seed_0"
    data = job_dir / "data"
    ckpt = job_dir / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")

    ets = 8760
    target = 50
    max_gs = target * ets - 2
    rows = [
        {
            "episode": str(target - 1),
            "episode_step": str(ets - 2),
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
                    "n_rollout_threads": 12,
                    "run_completed_with_salvage": True,
                },
            }
        ),
        encoding="utf-8",
    )
    (job_dir / "live_progress.json").write_text(
        json.dumps(
            {
                "global_step": max_gs,
                "episode": target - 1,
                "episode_step": ets - 2,
                "completed_episode_count": 49,
                "algorithm": "HAPPO",
            }
        ),
        encoding="utf-8",
    )
    (run_root / "official_full_status.json").write_text(
        json.dumps(
            {
                "episodes": target,
                "jobs": [
                    {
                        "name": "happo",
                        "scenario": "E1",
                        "exit_code": 0,
                        "completed_at": "2026-06-27T16:40:47Z",
                        "skipped": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert job_counts_as_launcher_complete(
        job_dir, target_episodes=target, output_root=run_root
    ) is False
    dec = preview_job_launcher_decision(
        job_dir,
        algorithm="happo",
        target_episodes=target,
        episode_time_steps=ets,
        rollout_threads=12,
        output_root=run_root,
    )
    assert dec["skip"] is False, dec
    assert dec["action"] == "resume"
    assert "COMPLETO" not in dec["status_line"]
    assert not dec["blockers"]


def test_happo_salvage_49_tail_without_launcher_manifest(tmp_path: Path):
    """Salvage stuck at 49/50 must skip even when official_full_status.json is missing."""
    import csv

    job_dir = tmp_path / "happo" / "E1_seed_0"
    data = job_dir / "data"
    ckpt = job_dir / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")

    ets = 8760
    target = 50
    max_gs = target * ets - 2
    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(
            fh, fieldnames=["episode", "episode_step", "global_step", "all_done"]
        )
        writer.writeheader()
        writer.writerow(
            {
                "episode": str(target - 1),
                "episode_step": str(ets - 2),
                "global_step": str(max_gs),
                "all_done": "False",
            }
        )
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
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

    assert job_counts_as_launcher_complete(job_dir, target_episodes=target) is False
    dec = preview_job_launcher_decision(
        job_dir, algorithm="happo", target_episodes=target, episode_time_steps=ets
    )
    assert dec["skip"] is False
    assert dec["action"] == "resume"


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
                "citylearn_v3_report": {"all_values": {"cost": 1.0}},
                "artifact_audit": {"episode_summaries": [{}] * 50},
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
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "hyperparameters": {
                    "target_episodes": target,
                    "episodes": target,
                    "n_rollout_threads": 12,
                },
            }
        ),
        encoding="utf-8",
    )
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


def test_happo_launcher_manifest_skips_stuck_49_of_50(tmp_path: Path):
    """Flow B / cell 2.1b: stale live_progress at 49/50 must skip when launcher recorded exit=0."""
    import csv

    run_root = tmp_path / "madrl_run"
    job_dir = run_root / "happo" / "E1_seed_0"
    data = job_dir / "data"
    ckpt = job_dir / "checkpoints" / "gym" / "run"
    data.mkdir(parents=True)
    ckpt.mkdir(parents=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")

    ets = 8760
    target = 50
    rows = []
    for ep in range(49):
        for step in range(ets):
            gs = ep * ets + step
            rows.append(
                {
                    "episode": str(ep),
                    "episode_step": str(step),
                    "global_step": str(gs),
                    "all_done": "False",
                }
            )
    for step in range(8460):
        gs = 49 * ets + step
        rows.append(
            {
                "episode": "49",
                "episode_step": str(step),
                "global_step": str(gs),
                "all_done": "False",
            }
        )
    with (data / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)
    (job_dir / "live_progress.json").write_text(
        json.dumps(
            {
                "global_step": 49 * ets + 8459,
                "episode": 49,
                "episode_step": 8459,
                "completed_episode_count": 49,
                "algorithm": "HAPPO",
                "episode_time_steps": ets,
            }
        ),
        encoding="utf-8",
    )
    (run_root / "official_full_status.json").write_text(
        json.dumps(
            {
                "episodes": target,
                "jobs": [
                    {
                        "name": "happo",
                        "scenario": "E1",
                        "exit_code": 0,
                        "completed_at": "2026-06-29T00:00:00Z",
                        "skipped": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    dec = preview_job_launcher_decision(
        job_dir,
        algorithm="happo",
        target_episodes=target,
        episode_time_steps=ets,
        output_root=run_root,
    )
    assert dec["skip"] is True, dec["status_line"]
    assert dec["action"] == "skip"

    report = build_jobs_resume_report(
        run_root,
        target_episodes=target,
        algorithms=["happo"],
        scenarios=["E1"],
        episode_time_steps=ets,
    )
    row = report["jobs"][0]
    assert row["action"] == "skip"
    assert "COMPLETO" in row["status_line"]


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


def test_kpi_audited_results_skip_without_checkpoints(tmp_path: Path):
    data = tmp_path / "data"
    data.mkdir(parents=True)
    (data / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MASAC",
                "episodes_recorded": 50,
                "citylearn_v3_report": {"all_values": {"cost": 1.0}},
                "artifact_audit": {"episode_summaries": [{}] * 50},
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )
    assert job_counts_as_launcher_complete(tmp_path, target_episodes=50) is True
    dec = preview_job_launcher_decision(
        tmp_path, algorithm="masac", target_episodes=50, episode_time_steps=8760
    )
    assert dec["skip"] is True
    assert dec["action"] == "skip"


def test_resolve_existing_prefers_legacy_with_artifacts(tmp_path: Path):
    """Empty canonical HAPPO/E1 must not hide populated happo/E1_seed_0 on Drive."""
    run_root = tmp_path / "madrl_v3_run"
    empty_canonical = run_root / "HAPPO" / "E1"
    legacy = run_root / "happo" / "E1_seed_0"
    empty_canonical.mkdir(parents=True)
    data = legacy / "data"
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

    resolved = resolve_existing_job_run_dir(run_root, "happo", "E1", 0)
    assert resolved == legacy

    launcher_dir = job_run_dir_for_launcher(run_root, "happo", "E1", 0, create_if_missing=False)
    assert launcher_dir == legacy
    assert job_counts_as_launcher_complete(
        legacy, target_episodes=50, output_root=run_root
    ) is False  # minimal results without KPI audit — still finds the right folder


def test_launcher_run_dir_finds_legacy_not_empty_canonical(tmp_path: Path):
    """run_dir() must attach to the artifact tree, not an empty canonical stub."""
    import colab_a100_official_launcher as launcher

    run_root = tmp_path / "madrl_v3_20260627_164047"
    (run_root / "MASAC" / "E1").mkdir(parents=True)
    legacy = run_root / "masac" / "E1_seed_0" / "data"
    legacy.mkdir(parents=True)
    (legacy / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MASAC",
                "episodes_recorded": 50,
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )

    path = launcher.run_dir(run_root, "masac", "E1", 0)
    assert path.name == "E1_seed_0" or "E1_seed_0" in str(path)


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
                "citylearn_v3_report": {"all_values": {"cost": 1.0}},
                "artifact_audit": {"episode_summaries": [{}] * 50},
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


def test_select_best_resume_prefers_artifacts_over_empty_newer_run(tmp_path: Path):
    """Empty madrl_v3_* stubs must not beat a run with real MADRL checkpoints."""
    import csv

    parent = tmp_path / "outputs"
    parent.mkdir(parents=True)
    canonical = parent / "madrl_v3_20260627_164047"
    empty_new = parent / "madrl_v3_20260704_232255"
    empty_new.mkdir(parents=True)
    (empty_new / "run_context_manifest.json").write_text("{}", encoding="utf-8")

    happo = resolve_job_run_dir(canonical, "happo", "E1", 0)
    (happo / "data").mkdir(parents=True, exist_ok=True)
    ckpt = happo / "checkpoints" / "gym" / "run"
    ckpt.mkdir(parents=True, exist_ok=True)
    (ckpt / "actor_agent0.pt").write_bytes(b"x")
    with (happo / "data" / "timeseries.csv").open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=["episode", "episode_step", "global_step", "all_done"])
        writer.writeheader()
        writer.writerow(
            {"episode": "49", "episode_step": "0", "global_step": str(49 * 8760), "all_done": "True"}
        )

    from citylearn_v3_training_common import pick_colab_output_root

    picked = pick_colab_output_root(
        parent,
        run_label="madrl_v3_test",
        auto_resume_latest=True,
        print_audit=False,
    )
    assert picked["output_root"] == str(canonical)
    assert picked["created_new_run"] is False


def test_plan_duplicate_run_cleanup_keeps_active_and_best(tmp_path: Path):
    parent = tmp_path / "outputs"
    parent.mkdir(parents=True)
    best = parent / "madrl_v3_20260627_164047"
    empty = parent / "madrl_v3_20260704_232255"
    empty.mkdir(parents=True)
    (empty / "run_context_manifest.json").write_text("{}", encoding="utf-8")
    masac = resolve_job_run_dir(best, "masac", "E1", 0)
    (masac / "data").mkdir(parents=True, exist_ok=True)
    (masac / "data" / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "MASAC",
                "episodes_recorded": 50,
                "citylearn_v3_report": {"all_values": {"cost": 1.0}},
                "artifact_audit": {"episode_summaries": [{}] * 50},
                "hyperparameters": {"target_episodes": 50, "episodes": 50},
            }
        ),
        encoding="utf-8",
    )

    from citylearn_v3_training_common import plan_madrl_duplicate_run_cleanup

    plan = plan_madrl_duplicate_run_cleanup(parent, active_output_root=best, target_episodes=50)
    assert str(best) in plan["keep"]
    assert str(empty) in plan["delete"]


def test_stub_only_run_not_selected_as_restorable(tmp_path: Path):
    parent = tmp_path / "outputs"
    parent.mkdir(parents=True)
    stub = parent / "madrl_v3_20260704_232255"
    happo = resolve_job_run_dir(stub, "happo", "E1", 0)
    (happo / "data").mkdir(parents=True, exist_ok=True)
    (happo / "data" / "results.json").write_text(
        json.dumps(
            {
                "algorithm": "HAPPO",
                "status": "completed_with_salvage",
                "salvage_reason": "NameError: VecEnvWrapper",
            }
        ),
        encoding="utf-8",
    )

    from citylearn_v3_training_common import audit_madrl_drive_output_runs, pick_colab_output_root

    audit = audit_madrl_drive_output_runs(parent, target_episodes=50)
    assert audit["runs_with_artifacts"] == 0
    assert audit["summaries"][0]["stub_only"] is True

    try:
        pick_colab_output_root(
            parent,
            run_label="madrl_v3_new",
            auto_resume_latest=True,
            print_audit=False,
        )
        raise AssertionError("expected RuntimeError for stub-only Drive")
    except RuntimeError as exc:
        assert "STUB" in str(exc)


def test_list_madrl_runs_on_colab_mount_finds_nested_outputs(tmp_path: Path):
    mount = tmp_path / "drive"
    outputs = mount / "MyDrive" / "MADRLCitytleranflexresdr" / "outputs"
    canonical = outputs / "madrl_v3_20260627_164047"
    canonical.mkdir(parents=True)
    happo = resolve_job_run_dir(canonical, "happo", "E1", 0)
    (happo / "checkpoints" / "gym" / "run").mkdir(parents=True)
    (happo / "checkpoints" / "gym" / "run" / "actor_agent0.pt").write_bytes(b"x")

    from citylearn_v3_training_common import list_madrl_runs_on_colab_mount

    found = list_madrl_runs_on_colab_mount(mount)
    assert [p.name for p in found] == ["madrl_v3_20260627_164047"]


def test_bind_colab_drive_workspace_selects_restorable_run(tmp_path: Path):
    mount = tmp_path / "drive"
    repo = tmp_path / "repo"
    (repo / "outputs").mkdir(parents=True)
    (repo / "outputs" / "latest_colab_output_root.txt").write_text(
        "outputs/madrl_v3_20260627_164047\n",
        encoding="utf-8",
    )
    outputs = mount / "MyDrive" / "MADRLCitytleranflexresdr" / "outputs"
    stub = outputs / "madrl_v3_20260704_232255"
    canonical = outputs / "madrl_v3_20260627_164047"
    stub.mkdir(parents=True)
    canonical.mkdir(parents=True)
    (stub / "run_context_manifest.json").write_text("{}", encoding="utf-8")
    stub_happo = resolve_job_run_dir(stub, "happo", "E1", 0)
    (stub_happo / "data").mkdir(parents=True)
    (stub_happo / "data" / "results.json").write_text(
        json.dumps({"algorithm": "HAPPO", "status": "completed_with_salvage"}),
        encoding="utf-8",
    )
    happo = resolve_job_run_dir(canonical, "happo", "E1", 0)
    (happo / "checkpoints" / "gym" / "run").mkdir(parents=True)
    (happo / "checkpoints" / "gym" / "run" / "actor_agent0.pt").write_bytes(b"x")

    from citylearn_v3_training_common import bind_colab_drive_workspace

    binding = bind_colab_drive_workspace(
        mount,
        repo=repo,
        allow_drive_api_shortcut=False,
    )
    assert binding["is_correct_drive"] is True
    assert binding["output_root"] == str(canonical)
    assert "madrl_v3_20260704_232255" in binding["stub_runs"]


def test_validate_canonical_skip_plan_from_drive_kpis(tmp_path: Path):
    kpi_dir = Path("outputs/_drive_madrl/kpis")
    if not kpi_dir.is_dir():
        return
    run_root = tmp_path / "madrl_v3_20260627_164047"
    copied = 0
    for algo in ("happo", "masac", "matd3", "maac"):
        for scen in ("E1", "E2", "E3"):
            src = kpi_dir / f"{algo}_{scen}_results.json"
            if not src.is_file():
                continue
            dest = run_root / algo.upper() / scen / "data"
            dest.mkdir(parents=True, exist_ok=True)
            dest.joinpath("results.json").write_text(src.read_text(encoding="utf-8"), encoding="utf-8")
            copied += 1
            if algo == "happo":
                ckpt = run_root / algo.upper() / scen / "checkpoints" / "gym" / "run" / "models"
                ckpt.mkdir(parents=True, exist_ok=True)
                (ckpt / "actor_agent0.pt").write_bytes(b"x")
                (ckpt / "critic_agent.pt").write_bytes(b"x")
    assert copied >= 12

    from citylearn_v3_training_common import (
        assert_canonical_colab_skip_plan,
        build_jobs_resume_report,
        validate_canonical_colab_skip_plan,
    )

    report = build_jobs_resume_report(run_root, target_episodes=50, happo_rollout_threads=2)
    validation = validate_canonical_colab_skip_plan(report)
    assert validation["ok"] is True
    assert validation["completed"] == 9
    assert validation["resumable"] == 3
    assert_canonical_colab_skip_plan(report)


if __name__ == "__main__":
    test_infer_completed_episodes()
    test_clamp_happo_rollout_threads()
    import tempfile

    with tempfile.TemporaryDirectory() as td:
        test_resolve_job_rollout_threads_clamps_salvage(Path(td))
    test_discover_resume_without_artifacts(Path("outputs/_test_resume_empty"))

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
        test_kpi_audited_results_skip_without_checkpoints(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_resolve_existing_prefers_legacy_with_artifacts(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_launcher_run_dir_finds_legacy_not_empty_canonical(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_build_jobs_resume_report_counts(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_select_best_resume_prefers_artifacts_over_empty_newer_run(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_plan_duplicate_run_cleanup_keeps_active_and_best(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_stub_only_run_not_selected_as_restorable(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_list_madrl_runs_on_colab_mount_finds_nested_outputs(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_bind_colab_drive_workspace_selects_restorable_run(Path(td))
    with tempfile.TemporaryDirectory() as td:
        test_validate_canonical_skip_plan_from_drive_kpis(Path(td))
    print("OK: test_job_resume_state")
