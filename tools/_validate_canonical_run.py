"""One-off: validate 9 SKIP + 3 REANUDA on local Drive mirror of canonical run."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "CityLearn" / "scripts"))

from citylearn_v3_training_common import (  # noqa: E402
    assert_canonical_colab_skip_plan,
    build_jobs_resume_report,
    preview_job_launcher_decision,
)

candidates = [
    ROOT / "outputs/_drive_madrl/outputs/madrl_v3_20260627_164047",
    ROOT / "outputs/madrl_v3_20260627_164047",
]
run = next((p for p in candidates if p.is_dir()), None)
if run is None:
    raise SystemExit("Run canonico madrl_v3_20260627_164047 no encontrado localmente")

print(f"RUN={run}")
report = build_jobs_resume_report(
    run, target_episodes=50, episode_time_steps=8760, happo_rollout_threads=2
)
skip = resume = fresh = 0
for job in report["jobs"]:
    decision = preview_job_launcher_decision(job)
    action = decision["action"]
    if action == "skip":
        skip += 1
    elif action == "resume":
        resume += 1
    else:
        fresh += 1
    ep = int(job.get("completed_episodes") or 0)
    print(f"  {job['algorithm'].upper():5} {job['scenario']}  ep={ep:2}/50  -> {action.upper()}")

print(f"\nRESUMEN: SKIP={skip} RESUME={resume} FRESH={fresh}")
assert_canonical_colab_skip_plan(report, output_root=run)
print("OK: plan canonico validado")
