#!/usr/bin/env python3
"""Forced robustness tests for the CityLearn v3 MADRL training pipeline.

These tests prove — without a GPU or the heavy RL backends — that the failure mode
that killed MASAC E1/E2/E3 (headless matplotlib at finalization + no salvage) cannot
recur, and that the dynamic backfill scheduler keeps the validated concurrency cap.

Run:  python tools/test_madrl_robustness.py
Exit: 0 if every assertion passes, 1 otherwise.
"""
from __future__ import annotations

import json
import sys
import tempfile
import threading
import time
import types
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "CityLearn" / "scripts"
sys.path.insert(0, str(SCRIPTS))

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, condition: bool, detail: str = "") -> None:
    if condition:
        PASSED.append(name)
        print(f"  [PASS] {name}")
    else:
        FAILED.append(f"{name} :: {detail}")
        print(f"  [FAIL] {name} :: {detail}")


# ---------------------------------------------------------------------------
# Test 1 — matplotlib forced to the headless Agg backend on import.
# This is the exact defense against the MASAC plt.savefig() crash in Colab Popen.
# ---------------------------------------------------------------------------
def test_matplotlib_agg() -> None:
    print("\n[1] matplotlib headless backend")
    import citylearn_v3_training_common  # noqa: F401  (import side effect sets Agg)
    import matplotlib

    backend = matplotlib.get_backend().lower()
    check("training_common forces Agg backend", backend == "agg", f"backend={backend!r}")

    import os as _os

    check(
        "MPLBACKEND env is Agg",
        _os.environ.get("MPLBACKEND", "").lower() == "agg",
        f"MPLBACKEND={_os.environ.get('MPLBACKEND')!r}",
    )


# ---------------------------------------------------------------------------
# Test 2 — salvage results.json is always written, even when the artifact
# writer fails. Without it a near-complete job is treated as failed and a
# relaunch would discard all trained progress.
# ---------------------------------------------------------------------------
def test_salvage_results_json() -> None:
    print("\n[2] guaranteed salvage results.json")
    from citylearn_v3_training_common import write_minimal_results_json

    args = types.SimpleNamespace(scenario="E2", seed=0, episode_time_steps=8760)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "masac" / "E2_seed_0"
        out.mkdir(parents=True)
        path = write_minimal_results_json(
            output_dir=out,
            algorithm="MASAC",
            backend="external/MADRL-MASAC",
            args=args,
            hyperparameters={"episodes": 50},
            report={"project_axis_metrics": {"ok": True}},
            error=RuntimeError("simulated plt failure"),
        )
        data_results = out / "data" / "results.json"
        root_results = out / "results.json"
        check("results.json written in data/", data_results.is_file())
        check("results.json mirrored at run root", root_results.is_file())
        payload = json.loads(data_results.read_text(encoding="utf-8"))
        check(
            "salvage status flagged",
            payload.get("status") == "completed_with_salvage",
            str(payload.get("status")),
        )
        check(
            "salvage records the error reason",
            "simulated plt failure" in str(payload.get("salvage_reason")),
            str(payload.get("salvage_reason")),
        )
        check("returned path equals data results.json", Path(path) == data_results)


# ---------------------------------------------------------------------------
# Test 3 — MASAC periodic checkpoint is frequent (resume always possible) and the
# runtime patch installs the headless guard.
# ---------------------------------------------------------------------------
def test_masac_checkpoint_and_patch() -> None:
    print("\n[3] MASAC periodic checkpoint + patch")
    masac_train = (SCRIPTS / "train_citylearn_v3_masac.py").read_text(encoding="utf-8")
    check(
        "MASAC sets save-every to 1 (checkpoint per QMIX update)",
        "citylearn_masac_save_every_steps = 1" in masac_train,
    )
    check(
        "MASAC wraps runner.run in salvage try/except",
        "Salvaging trained model" in masac_train,
    )

    patch_src = (SCRIPTS / "masac_runtime_optimizations.py").read_text(encoding="utf-8")
    check("patch reads configurable save_every", "citylearn_masac_save_every_steps" in patch_src)
    check("patch forces Agg backend", 'matplotlib.use("Agg"' in patch_src)

    import masac_runtime_optimizations as mro

    check("patch module exposes installer", hasattr(mro, "install_masac_runtime_optimizations"))


# ---------------------------------------------------------------------------
# Test 4b — SIGKILL exit codes trigger OOM retry path (empty logs on Linux OOM killer).
# ---------------------------------------------------------------------------
def test_sigkill_exit_detection() -> None:
    print("\n[4b] SIGKILL exit code detection")
    import colab_a100_official_launcher as launcher

    check("137 is sigkill", launcher.is_sigkill_exit(137))
    check("247 is sigkill", launcher.is_sigkill_exit(247))
    check("0 is not sigkill", not launcher.is_sigkill_exit(0))


# ---------------------------------------------------------------------------
# Test 4 — every train script writes a salvage results.json on artifact failure.
# ---------------------------------------------------------------------------
def test_all_algos_have_salvage() -> None:
    print("\n[4] all MADRL train scripts salvage on failure")
    for algo in ("happo", "masac", "matd3", "maac"):
        src = (SCRIPTS / f"train_citylearn_v3_{algo}.py").read_text(encoding="utf-8")
        check(f"{algo}: imports write_minimal_results_json", "write_minimal_results_json" in src)
        check(f"{algo}: calls salvage on artifact failure", "minimal salvage results.json" in src)
        if algo == "matd3":
            check("matd3: replay RAM preflight", "estimate_matd3_replay_ram_gib" in src)


# ---------------------------------------------------------------------------
# Test 5 — dynamic backfill scheduler: concurrency cap respected, all 12 jobs
# run, phase-2 backfilled lightest-first (MAAC before MATD3), failures propagate.
# ---------------------------------------------------------------------------
def test_dynamic_backfill_scheduler() -> None:
    print("\n[5] dynamic backfill scheduler")
    import colab_a100_official_launcher as launcher

    args = launcher.parse_args(
        [
            "--scenario", "ALL",
            "--episodes", "50",
            "--episode-time-steps", "8760",
            "--no-cuda",
            "--no-require-a100",
            "--skip-gpu-preflight",
        ]
    )
    launcher._sync_six_job_masac_defaults(args)
    root = ROOT
    output_root = ROOT / "outputs" / "_test_backfill"
    schema_arg = "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
    jobs = launcher.build_jobs(args, root, output_root, schema_arg)
    check("build_jobs yields 12 jobs", len(jobs) == 12, f"got {len(jobs)}")

    lock = threading.Lock()
    state = {"running": 0, "max_running": 0}
    start_order: list[tuple[str, str]] = []

    def fake_run(*, root, manifest, status_path, job, output_root, log_dir, args, **kw):
        with lock:
            state["running"] += 1
            state["max_running"] = max(state["max_running"], state["running"])
            start_order.append((str(job["name"]), str(job["scenario"])))
        time.sleep(0.03)
        with lock:
            state["running"] -= 1
        return 0

    original = launcher.run_job_with_retry
    launcher.run_job_with_retry = fake_run
    try:
        with tempfile.TemporaryDirectory() as tmp:
            rc = launcher.run_dynamic_backfill_jobs(
                root=root,
                manifest={"jobs": []},
                status_path=Path(tmp) / "status.json",
                jobs=jobs,
                output_root=output_root,
                log_dir=Path(tmp),
                args=args,
            )
    finally:
        launcher.run_job_with_retry = original

    check("scheduler returns 0 when all jobs succeed", rc == 0, f"rc={rc}")
    check("all 12 jobs executed", len(start_order) == 12, f"ran {len(start_order)}")
    check(
        "concurrency never exceeds phase-1 cap (6)",
        state["max_running"] <= 6,
        f"max_running={state['max_running']}",
    )

    phase2 = [(n, s) for (n, s) in start_order if n in ("matd3", "maac")]
    expected = [
        ("maac", "E1"), ("maac", "E2"), ("maac", "E3"),
        ("matd3", "E1"), ("matd3", "E2"), ("matd3", "E3"),
    ]
    check(
        "phase-2 backfilled lightest-first (MAAC before MATD3)",
        phase2 == expected,
        f"got {phase2}",
    )

    # Failure propagation: one job fails -> overall rc != 0.
    def fake_run_fail(*, job, **kw):
        return 1 if (job["name"] == "masac" and job["scenario"] == "E1") else 0

    launcher.run_job_with_retry = fake_run_fail
    try:
        with tempfile.TemporaryDirectory() as tmp:
            rc2 = launcher.run_dynamic_backfill_jobs(
                root=root,
                manifest={"jobs": []},
                status_path=Path(tmp) / "status.json",
                jobs=jobs,
                output_root=output_root,
                log_dir=Path(tmp),
                args=args,
            )
    finally:
        launcher.run_job_with_retry = original

    check("scheduler surfaces a job failure (rc != 0)", rc2 != 0, f"rc2={rc2}")


def test_backfill_skip_completed_omits_jobs() -> None:
    """Completed MASAC jobs must not enter the thread pool when --skip-completed."""
    print("\n[5b] backfill skip-completed omits complete jobs")
    import json as _json

    import colab_a100_official_launcher as launcher

    with tempfile.TemporaryDirectory() as tmp:
        output_root = Path(tmp) / "madrl_v3_skip_test"
        masac = output_root / "MASAC" / "E1" / "data"
        masac.mkdir(parents=True)
        (masac / "results.json").write_text(
            _json.dumps(
                {
                    "algorithm": "MASAC",
                    "episodes_recorded": 50,
                    "hyperparameters": {"target_episodes": 50, "episodes": 50},
                }
            ),
            encoding="utf-8",
        )

        args = launcher.parse_args(
            [
                "--scenario", "E1",
                "--episodes", "50",
                "--episode-time-steps", "8760",
                "--no-cuda",
                "--no-require-a100",
                "--skip-gpu-preflight",
                "--skip-completed",
            ]
        )
        launcher._sync_six_job_masac_defaults(args)
        root = ROOT
        schema_arg = "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
        jobs = launcher.build_jobs(args, root, output_root, schema_arg)
        started: list[tuple[str, str]] = []

        def fake_run(*, job, **kw):
            started.append((str(job["name"]), str(job["scenario"])))
            return 0

        original = launcher.run_job_with_retry
        launcher.run_job_with_retry = fake_run
        try:
            rc = launcher.run_dynamic_backfill_jobs(
                root=root,
                manifest={"jobs": []},
                status_path=output_root / "status.json",
                jobs=jobs,
                output_root=output_root,
                log_dir=output_root / "logs",
                args=args,
            )
        finally:
            launcher.run_job_with_retry = original

        check("skip backfill returns 0", rc == 0, f"rc={rc}")
        check(
            "MASAC/E1 not submitted when complete",
            ("masac", "E1") not in started,
            f"started={started}",
        )
        check("other E1 jobs still run", len(started) >= 1, f"started={started}")


# ---------------------------------------------------------------------------
# Test 6 — Drive durability helpers + resume safety. Proves recent checkpoints
# get flushed to durable storage and that a resume never proceeds without real
# restorable weights (which previously caused a silent fresh restart on Colab).
# ---------------------------------------------------------------------------
def test_drive_durability_and_resume_safety() -> None:
    print("\n[6] Drive durability + resume safety")
    import citylearn_v3_training_common as common

    check("flush_filesystem_buffers exists", callable(getattr(common, "flush_filesystem_buffers", None)))
    check("fsync_file exists", callable(getattr(common, "fsync_file", None)))

    try:
        common.flush_filesystem_buffers()
        flush_ok = True
    except Exception:
        flush_ok = False
    check("flush_filesystem_buffers runs without error (no-op off-Colab)", flush_ok)

    src = (SCRIPTS / "citylearn_v3_training_common.py").read_text(encoding="utf-8")
    check("live_progress write is fsync'd", "fsync_file(self.live_progress_path)" in src)
    check("heartbeat flushes buffers to Drive", "Flush buffered checkpoint" in src)

    patch_src = (SCRIPTS / "masac_runtime_optimizations.py").read_text(encoding="utf-8")
    check("MASAC flushes after checkpoint save", "_sync()" in patch_src)

    # Resume safety: live_progress present (episode>0) but NO checkpoints -> must NOT
    # resume (would otherwise train fewer episodes from random weights).
    import json as _json

    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "happo" / "E1_seed_0"
        out.mkdir(parents=True)
        (out / "live_progress.json").write_text(
            _json.dumps({"episode": 35, "global_step": 313800}), encoding="utf-8"
        )
        plan = common.discover_job_resume_plan(
            out,
            algorithm="happo",
            target_episodes=50,
            episode_time_steps=8760,
            allow_resume=True,
        )
        check(
            "resume inactive when weights are missing",
            plan.get("active") is False,
            f"active={plan.get('active')}",
        )
        check(
            "resume note flags missing weights",
            "without_weights" in str(plan.get("note")),
            str(plan.get("note")),
        )


def main() -> int:
    print("=" * 72)
    print("FORCED ROBUSTNESS TESTS — CityLearn v3 MADRL")
    print("=" * 72)
    test_matplotlib_agg()
    test_salvage_results_json()
    test_masac_checkpoint_and_patch()
    test_sigkill_exit_detection()
    test_all_algos_have_salvage()
    test_dynamic_backfill_scheduler()
    test_backfill_skip_completed_omits_jobs()
    test_drive_durability_and_resume_safety()

    print("\n" + "=" * 72)
    print(f"RESULT: {len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        for f in FAILED:
            print(f"  FAILED -> {f}")
        print("=" * 72)
        return 1
    print("ALL ROBUSTNESS TESTS PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
