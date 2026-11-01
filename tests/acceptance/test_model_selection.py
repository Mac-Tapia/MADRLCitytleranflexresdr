"""SPEC-005 FR-005.6: acceptance of the existing best-model selection rule.

SYNTHETIC FIXTURES ONLY: hypervolume values are invented to exercise the rule
and are not campaign results.

Contract under test (``uc3m.application.evaluation.model_selection.select_best_model``):

* input: one evaluation mapping with ``campaign_complete`` and
  ``algorithms -> {mean_hypervolume, variance_hypervolume, ...}``;
* rule: highest ``mean_hypervolume``; ties broken by lowest ``variance_hypervolume``;
* refusal: ``ValueError`` when ``campaign_complete`` is false or absent.

What the contract does not model (reported as pending, not invented here):
per-run verification inside the selector (it trusts ``campaign_complete``),
a training/evaluation split (so leakage cannot be tested beyond the input
surface), a significance gate before naming the best model, and a rule for a
full tie on mean and variance (the result then depends on input order).
"""
from __future__ import annotations

import copy
import inspect
import json
from pathlib import Path
from typing import Dict, Sequence

import pytest

from uc3m.application.evaluation.model_selection import select_best_model
from uc3m.application.evaluation.results_catalog import discover_runs


def _evaluation() -> dict:
    return {
        "campaign_complete": True,
        "algorithms": {
            "HAPPO": {"mean_hypervolume": 0.45, "variance_hypervolume": 0.010, "n_seeds": 3},
            "MASAC": {"mean_hypervolume": 0.50, "variance_hypervolume": 0.020, "n_seeds": 3},
            "MATD3": {"mean_hypervolume": 0.55, "variance_hypervolume": 0.005, "n_seeds": 3},
            "MAAC": {"mean_hypervolume": 0.40, "variance_hypervolume": 0.030, "n_seeds": 3},
        },
    }


def test_selects_highest_mean_hypervolume_and_ranks_all_algorithms() -> None:
    result = select_best_model(_evaluation())

    assert result["best_algorithm"] == "MATD3"
    assert result["mean_hypervolume"] == pytest.approx(0.55)
    assert [row["algorithm"] for row in result["ranking"]] == ["MATD3", "MASAC", "HAPPO", "MAAC"]
    assert "highest mean hypervolume" in result["justification"]


def test_equal_mean_is_broken_by_lower_variance() -> None:
    evaluation = _evaluation()
    evaluation["algorithms"]["MASAC"]["mean_hypervolume"] = 0.55
    evaluation["algorithms"]["MASAC"]["variance_hypervolume"] = 0.001

    result = select_best_model(evaluation)

    assert result["best_algorithm"] == "MASAC"
    assert [row["algorithm"] for row in result["ranking"]][:2] == ["MASAC", "MATD3"]


def test_selection_does_not_depend_on_algorithm_order_without_full_ties() -> None:
    evaluation = _evaluation()
    reversed_eval = {
        "campaign_complete": True,
        "algorithms": dict(reversed(list(evaluation["algorithms"].items()))),
    }

    assert select_best_model(evaluation)["ranking"] == select_best_model(reversed_eval)["ranking"]


def test_selection_is_a_pure_function_of_the_evaluation_summary() -> None:
    evaluation = _evaluation()
    snapshot = copy.deepcopy(evaluation)

    first = select_best_model(evaluation)

    assert evaluation == snapshot
    assert select_best_model(evaluation) == first
    # The selector receives only the evaluation summary: no training data,
    # replay buffers or training rewards are part of its input surface.
    assert list(inspect.signature(select_best_model).parameters) == ["evaluation"]


@pytest.mark.parametrize("flag", [False, None, "absent"])
def test_incomplete_campaign_is_rejected(flag) -> None:
    evaluation = _evaluation()
    if flag == "absent":
        del evaluation["campaign_complete"]
    else:
        evaluation["campaign_complete"] = flag

    with pytest.raises(ValueError, match="incomplete"):
        select_best_model(evaluation)


# --- unverified runs through the results catalog -------------------------------------------------
# The glue below is TEST-ONLY: production code does not yet build the selector's
# evaluation mapping from the catalog (pending). It shows the fail-closed chain:
# a non-verified run is invisible to discover_runs, the campaign is incomplete,
# and the selector refuses.

ALGORITHMS = ("HAPPO", "MATD3")
SEEDS = (1, 2, 3)
SYNTHETIC_HV: Dict[str, Sequence[float]] = {"HAPPO": (0.40, 0.42, 0.44), "MATD3": (0.50, 0.52, 0.54)}


def _write_run(root: Path, algorithm: str, seed: int, status: str) -> None:
    run = root / f"{algorithm.lower()}-e1-s{seed:03d}-synthetic"
    (run / f"E1_s{seed}").mkdir(parents=True)
    (run / "experiment.json").write_text(
        json.dumps({"algorithm": algorithm, "scenario_id": "E1", "seed": seed}), encoding="utf-8"
    )
    (run / "evidence.json").write_text(
        json.dumps({"run_id": run.name, "status": status, "completed_episodes": 50, "target_episodes": 50}),
        encoding="utf-8",
    )


def _evaluation_from_catalog(root: Path) -> dict:
    verified = {(r.algorithm, r.seed) for r in discover_runs(root) if r.scenario == "E1"}
    complete = all((a, s) in verified for a in ALGORITHMS for s in SEEDS)
    algorithms = {}
    for algorithm in ALGORITHMS:
        values = [SYNTHETIC_HV[algorithm][i] for i, s in enumerate(SEEDS) if (algorithm, s) in verified]
        mean = sum(values) / len(values)
        variance = sum((v - mean) ** 2 for v in values) / (len(values) - 1) if len(values) > 1 else 0.0
        algorithms[algorithm] = {"mean_hypervolume": mean, "variance_hypervolume": variance, "n_seeds": len(values)}
    return {"campaign_complete": complete, "algorithms": algorithms}


def test_fully_verified_synthetic_campaign_is_selectable(tmp_path: Path) -> None:
    for algorithm in ALGORITHMS:
        for seed in SEEDS:
            _write_run(tmp_path, algorithm, seed, "verified")

    assert select_best_model(_evaluation_from_catalog(tmp_path))["best_algorithm"] == "MATD3"


def test_unverified_run_blocks_selection(tmp_path: Path) -> None:
    for algorithm in ALGORITHMS:
        for seed in SEEDS:
            _write_run(tmp_path, algorithm, seed, "partial" if (algorithm, seed) == ("MATD3", 2) else "verified")

    evaluation = _evaluation_from_catalog(tmp_path)

    assert evaluation["campaign_complete"] is False
    with pytest.raises(ValueError, match="incomplete"):
        select_best_model(evaluation)
