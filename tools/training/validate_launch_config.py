#!/usr/bin/env python3
"""Static + logic validation for the two_phase_happo_masac dynamic-backfill launcher.

Runs WITHOUT numpy/torch/CityLearn (Colab-only deps). Validates:
  1. build_jobs yields the 12 (4 algos x 3 escenarios) jobs with the expected,
     v4-aligned / GPU-tuned hyperparameters for HAPPO, MASAC, MATD3, MAAC.
  2. Dynamic backfill: phase-1 (HAPPO+MASAC) starts first; as each slot frees a
     phase-2 (MATD3/MAAC, lightest-first) job is admitted; concurrency cap == 6.
  3. The manifest strategy string passes colab_protocol_guard.

Exit 0 if every assertion passes, 1 otherwise.
"""
from __future__ import annotations

import sys
import tempfile
import threading
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCRIPTS = ROOT / "CityLearn" / "scripts"
sys.path.insert(0, str(SCRIPTS))

# Stub the heavy CityLearn module (numpy/torch/citylearn) with only the pure-path
# helpers the launcher needs, so the two-phase/backfill logic is validated offline.
# Mirrors citylearn_v3_training_common.normalize_*/resolve_job_run_dir exactly.
import types as _types  # noqa: E402

if "numpy" not in sys.modules:
    try:
        import numpy  # noqa: F401
    except ModuleNotFoundError:
        _stub = _types.ModuleType("citylearn_v3_training_common")

        def normalize_algorithm_dir(algorithm: str) -> str:
            return algorithm.strip().upper()

        def normalize_scenario_dir(scenario: str, seed: int = 0) -> str:
            scenario = scenario.strip().upper()
            seed = int(seed)
            return scenario if seed == 0 else f"{scenario}_s{seed}"

        def resolve_job_run_dir(base, algorithm, scenario, seed):
            base = Path(base)
            return base / normalize_algorithm_dir(algorithm) / normalize_scenario_dir(scenario, seed)

        def resolve_existing_job_run_dir(base, algorithm, scenario, seed):
            return None

        _stub.normalize_algorithm_dir = normalize_algorithm_dir
        _stub.normalize_scenario_dir = normalize_scenario_dir
        _stub.resolve_job_run_dir = resolve_job_run_dir
        _stub.resolve_existing_job_run_dir = resolve_existing_job_run_dir
        sys.modules["citylearn_v3_training_common"] = _stub
        print("[validate] numpy ausente -> usando stub de citylearn_v3_training_common (solo paths)")

PASSED: list[str] = []
FAILED: list[str] = []


def check(name: str, cond: bool, detail: str = "") -> None:
    if cond:
        PASSED.append(name)
        print(f"  [PASS] {name}")
    else:
        FAILED.append(f"{name} :: {detail}")
        print(f"  [FAIL] {name} :: {detail}")


def arg_after(args, flag):
    a = [str(x) for x in args]
    return a[a.index(flag) + 1] if flag in a else None


def main() -> int:
    print("=" * 72)
    print("LAUNCH CONFIG VALIDATION - two_phase_happo_masac dynamic backfill")
    print("=" * 72)

    import colab_a100_official_launcher as L

    args = L.parse_args(
        [
            "--scenario", "ALL",
            "--episodes", "50",
            "--episode-time-steps", "8760",
            "--no-cuda",
            "--no-require-a100",
            "--skip-gpu-preflight",
        ]
    )
    if hasattr(L, "_sync_six_job_masac_defaults"):
        L._sync_six_job_masac_defaults(args)

    schema = "CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
    out_root = ROOT / "outputs" / "_validate_cfg"
    jobs = L.build_jobs(args, ROOT, out_root, schema)

    # ---- 1. Job set ----
    print("\n[1] build_jobs: 12 jobs (4 algos x 3 escenarios)")
    check("12 jobs", len(jobs) == 12, f"got {len(jobs)}")
    by_algo = {}
    for j in jobs:
        by_algo.setdefault(j["name"], []).append(j["scenario"])
    for algo in ("happo", "masac", "matd3", "maac"):
        check(f"{algo}: 3 escenarios", sorted(by_algo.get(algo, [])) == ["E1", "E2", "E3"],
              str(by_algo.get(algo)))

    # ---- 2. Per-algo hyperparameters (post phase patch, as the scheduler runs them) ----
    print("\n[2] hiperparametros por algoritmo (tras patch de fase)")

    def patched(algo):
        j = next(x for x in jobs if x["name"] == algo)
        patcher = L._ALGO_A100_PATCHERS.get(algo)
        return patcher(j, args)["args"] if patcher else j["args"]

    h = patched("happo")
    check("HAPPO ppo_epoch=10", arg_after(h, "--ppo-epoch") == "10", arg_after(h, "--ppo-epoch"))
    check("HAPPO critic_epoch=10", arg_after(h, "--critic-epoch") == "10", arg_after(h, "--critic-epoch"))
    check("HAPPO hidden=512", arg_after(h, "--hidden-size") == "512", arg_after(h, "--hidden-size"))

    m = patched("masac")
    check("MASAC preload=auto", arg_after(m, "--masac-preload-batch-device") == "auto",
          arg_after(m, "--masac-preload-batch-device"))

    t = patched("matd3")
    check("MATD3 buffer=4096 (v4)", arg_after(t, "--buffer-size") == "4096", arg_after(t, "--buffer-size"))
    check("MATD3 batch=256 (v4)", arg_after(t, "--batch-size") == "256", arg_after(t, "--batch-size"))
    check("MATD3 hidden=256 (v4)", arg_after(t, "--hidden-size") == "256", arg_after(t, "--hidden-size"))
    check("MATD3 train_interval=100 (v4)", arg_after(t, "--train-interval") == "100",
          arg_after(t, "--train-interval"))

    a = patched("maac")
    check("MAAC presente", a is not None and len(a) > 0)

    # ---- 3. Dynamic backfill scheduler ----
    print("\n[3] backfill dinamico: cap=6, fase2 al liberar slot (lightest-first)")
    lock = threading.Lock()
    state = {"running": 0, "max_running": 0}
    order: list[tuple[str, str]] = []

    def fake_run(*, root, manifest, status_path, job, output_root, log_dir, args, **kw):
        with lock:
            state["running"] += 1
            state["max_running"] = max(state["max_running"], state["running"])
            order.append((str(job["name"]), str(job["scenario"])))
        time.sleep(0.02)
        with lock:
            state["running"] -= 1
        return 0

    original = L.run_job_with_retry
    L.run_job_with_retry = fake_run
    try:
        with tempfile.TemporaryDirectory() as tmp:
            rc = L.run_dynamic_backfill_jobs(
                root=ROOT, manifest={"jobs": []}, status_path=Path(tmp) / "s.json",
                jobs=jobs, output_root=out_root, log_dir=Path(tmp), args=args,
            )
    finally:
        L.run_job_with_retry = original

    check("scheduler rc=0", rc == 0, f"rc={rc}")
    check("12 jobs ejecutados", len(order) == 12, f"ran {len(order)}")
    check("cap concurrencia <= 6", state["max_running"] <= 6, f"max={state['max_running']}")
    first6 = order[:6]
    p1_first = all(n in ("happo", "masac") for n, _ in first6)
    check("primeros 6 = fase 1 (HAPPO+MASAC)", p1_first, str(first6))

    # Admission order is deterministic (lightest-first); thread *start* order races
    # due to the lock, so assert the real contract: the backfill queue ordering.
    phase2_jobs = L._prepare_two_phase_jobs(
        jobs, L.TWO_PHASE_P2_HM, args=args, phase_threads=2,
        perf_env={},
    )
    admission = [(j["name"], j["scenario"])
                 for j in sorted(phase2_jobs, key=L._job_backfill_weight)]
    expected_p2 = [("maac", "E1"), ("maac", "E2"), ("maac", "E3"),
                   ("matd3", "E1"), ("matd3", "E2"), ("matd3", "E3")]
    check("admision fase 2 por escenario (MAAC luego MATD3)",
          admission == expected_p2, str(admission))
    ran_p2 = sorted((n, s) for (n, s) in order if n in ("matd3", "maac"))
    check("los 6 jobs fase 2 corrieron", ran_p2 == sorted(expected_p2), str(ran_p2))

    # Failure propagation
    def fake_fail(*, job, **kw):
        return 1 if (job["name"] == "happo" and job["scenario"] == "E1") else 0

    L.run_job_with_retry = fake_fail
    try:
        with tempfile.TemporaryDirectory() as tmp:
            rc2 = L.run_dynamic_backfill_jobs(
                root=ROOT, manifest={"jobs": []}, status_path=Path(tmp) / "s.json",
                jobs=jobs, output_root=out_root, log_dir=Path(tmp), args=args,
            )
    finally:
        L.run_job_with_retry = original
    check("falla de job propaga rc!=0", rc2 != 0, f"rc2={rc2}")

    # ---- 4. Manifest strategy passes protocol guard ----
    print("\n[4] estrategia del manifiesto pasa colab_protocol_guard")
    import colab_protocol_guard as G

    setattr(args, "_detected_vram_gib", 96.0)
    manifest = L.make_manifest(
        args=args, root=ROOT, output_root=out_root, schema_arg=schema,
        schema_resolved=Path(schema), env_info={}, gpu_info={"memory_total_gib": 96.0},
        torch_info={"torch_version": "2.x"}, import_info=None,
    )
    par = dict(manifest.get("parallelization") or {})
    try:
        G.validate_parallelization_strategy(par.get("strategy", ""), parallelization=par)
        check("strategy valida (guard)", True)
    except Exception as exc:  # noqa: BLE001
        check("strategy valida (guard)", False, str(exc))
    check("dynamic_backfill=True", par.get("dynamic_backfill") is True, str(par.get("dynamic_backfill")))
    check("execution two_phase_happo_masac",
          manifest.get("execution") == "two_phase_happo_masac", str(manifest.get("execution")))

    print("\n" + "=" * 72)
    print(f"RESULT: {len(PASSED)} passed, {len(FAILED)} failed")
    if FAILED:
        for f in FAILED:
            print(f"  FAILED -> {f}")
        print("=" * 72)
        return 1
    print("ALL LAUNCH CONFIG CHECKS PASSED")
    print("=" * 72)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
