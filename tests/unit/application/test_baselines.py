from pathlib import Path

import pytest

from uc3m.application.evaluation.baselines import compute_rbc_baseline


def test_compute_rbc_baseline_delegates_to_injected_runner():
    calls = []

    def runner(schema_path, steps):
        calls.append((schema_path, steps))
        return {"cost_total": 1.0, "_meta": {"total_steps": steps}}

    kpis = compute_rbc_baseline("schema.json", runner, episode_time_steps=24)

    assert calls == [(Path("schema.json"), 24)]
    assert kpis["cost_total"] == 1.0


def test_compute_rbc_baseline_rejects_runner_without_provenance():
    with pytest.raises(ValueError, match="_meta"):
        compute_rbc_baseline("schema.json", lambda p, s: {"cost_total": 1.0})
