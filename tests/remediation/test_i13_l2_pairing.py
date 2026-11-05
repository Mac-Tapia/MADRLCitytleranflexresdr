"""L2-003: real seed identity, final-episode selection and paired API boundary."""
import importlib.util
import json
from pathlib import Path
import sys

import numpy as np
import pandas as pd
import pytest

REPO = Path(__file__).resolve().parents[2]
PATH = REPO / "scripts/run_madrl_nonparametric_battery.py"
spec = importlib.util.spec_from_file_location("i13_l2_battery", PATH)
tool = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = tool
spec.loader.exec_module(tool)
ALGOS = ("HAPPO", "MAAC", "MASAC", "MATD3")


def _frame(seeds=range(3), *, mismatch=False):
    rows = []
    for scenario in ("E1", "E2", "E3"):
        for index, algorithm in enumerate(ALGOS):
            actual = [s + 1 for s in seeds] if mismatch and algorithm == "MAAC" else list(seeds)
            for seed in actual:
                for episode in (1, 2):
                    rows.append(dict(algorithm=algorithm, scenario=scenario, seed=seed, episode=episode,
                                     reward_mean=seed + index + episode/10,
                                     district_emission=100 + seed + index + episode/10,
                                     district_cost=200 + seed + index + episode/10))
    return pd.DataFrame(rows)


def _csv(tmp_path, frame):
    path = tmp_path / "episodes.csv"
    frame.to_csv(path, index=False)
    return path


def test_l2_equal_n12_different_seed_sets_never_reaches_paired_cli(tmp_path):
    path = _csv(tmp_path, _frame(range(12), mismatch=True))
    out = tmp_path / "output"
    assert tool.main(["--episodes-csv", str(path), "--n-seeds", "12", "--output-dir", str(out)]) == 2
    assert not (out / "nonparametric_battery.json").exists()


def test_l2_mismatched_seed_sets_are_explicit_in_metadata(tmp_path):
    groups, meta = tool.load_oe_groups_from_episodes(_csv(tmp_path, _frame(range(12), mismatch=True)),
                                                    expected_n_seeds=12)
    assert len(groups["OE.1"]["HAPPO"]) == len(groups["OE.1"]["MAAC"]) == 12
    assert meta["seed_ids"]["OE.1"]["HAPPO"] == list(range(12))
    assert meta["seed_ids"]["OE.1"]["MAAC"] == list(range(1, 13))
    assert not meta["pairing_eligible"]
    with pytest.raises(ValueError, match="seed"):
        tool.run_nonparametric_battery(groups, sampling=meta, expected_n_seeds=12)


def test_l2_shuffled_identical_seed_ids_are_sorted_and_retained(tmp_path):
    frame = _frame(range(1001, 1013)).sample(frac=1, random_state=8)
    groups, meta = tool.load_oe_groups_from_episodes(_csv(tmp_path, frame), expected_n_seeds=12)
    assert meta["pairing_eligible"]
    assert meta["seed_ids"]["OE.1"]["HAPPO"] == list(range(1001, 1013))
    assert groups["OE.1"]["HAPPO"] == pytest.approx(np.arange(1001, 1013) + 0.2)
    assert meta["selection"]["OE.1"]["final_episode"] == 2
    result = tool.run_nonparametric_battery(groups, sampling=meta, expected_n_seeds=12)
    assert result["sampling"]["aligned_seed_ids"]["OE.1"] == list(range(1001, 1013))
    assert result["scientific_acceptance"] is False


def test_l2_direct_api_requires_ids_instead_of_positional_pairing():
    groups = tool._illustrative_oe_groups(n_per_algo=3)
    with pytest.raises(ValueError, match="seed IDs"):
        tool.run_nonparametric_battery(groups, expected_n_seeds=3)


def test_l2_direct_api_aligns_values_by_seed_identity_not_list_position(tmp_path):
    groups, meta = tool.load_oe_groups_from_episodes(_csv(tmp_path, _frame()), expected_n_seeds=3)
    for oe in groups:
        # Give two algorithms identical seed-linked values, but opposite storage order.
        groups[oe]["MAAC"] = list(reversed(groups[oe]["HAPPO"]))
        meta["seed_ids"][oe]["MAAC"] = list(reversed(meta["seed_ids"][oe]["HAPPO"]))
    result = tool.run_nonparametric_battery(groups, sampling=meta, expected_n_seeds=3, complementary=True)
    pair = next(r for r in result["oe"]["OE.1"]["complementary"]["wilcoxon_paired"]
                if r["algorithm_a"] == "HAPPO" and r["algorithm_b"] == "MAAC")
    assert pair["status"] == "identical_samples" and pair["n"] == 0


@pytest.mark.parametrize("defect", ["gap", "nan_final", "missing_final"])
def test_l2_missing_seed_or_final_metric_is_not_filled(tmp_path, defect):
    frame = _frame()
    target = (frame.algorithm == "MAAC") & (frame.scenario == "E1") & (frame.seed == 1)
    if defect == "gap":
        frame = frame.loc[~target]
    elif defect == "nan_final":
        frame.loc[target & (frame.episode == 2), "reward_mean"] = np.nan
    else:
        frame = frame.loc[~(target & (frame.episode == 2))]
    groups, meta = tool.load_oe_groups_from_episodes(_csv(tmp_path, frame), expected_n_seeds=3)
    assert meta["missing"] and not meta["pairing_eligible"]
    assert 1 not in meta["seed_ids"]["OE.1"]["MAAC"]
    with pytest.raises(ValueError, match="seed"):
        tool.run_nonparametric_battery(groups, sampling=meta, expected_n_seeds=3)


@pytest.mark.parametrize("defect", ["duplicate", "fractional_seed", "negative_seed", "duplicate_without_episode"])
def test_l2_seed_and_episode_identity_must_be_unambiguous(tmp_path, defect):
    frame = _frame()
    if defect == "duplicate":
        frame = pd.concat([frame, frame.iloc[[0]]], ignore_index=True)
    elif defect == "fractional_seed":
        frame.loc[0, "seed"] = 0.5
    elif defect == "negative_seed":
        frame.loc[0, "seed"] = -1
    else:
        frame = frame.drop(columns="episode")
    with pytest.raises(ValueError, match="seed|episode"):
        tool.load_oe_groups_from_episodes(_csv(tmp_path, frame), expected_n_seeds=3)


@pytest.mark.parametrize("modular", [False, True])
def test_l2_run_root_preserves_arbitrary_declared_seed_ids(tmp_path, modular):
    root = tmp_path / "campaign"
    for algorithm in ALGOS:
        for scenario in ("E1", "E2", "E3"):
            for seed in (1001, 1002, 1003):
                if modular:
                    run = root / f"{algorithm}_{scenario}_{seed}"
                    data = run / f"{scenario}_s{seed}" / "data"
                    data.mkdir(parents=True)
                    (run / "experiment.json").write_text(json.dumps(dict(algorithm=algorithm, scenario_id=scenario, seed=seed)))
                    (run / "evidence.json").write_text(json.dumps(dict(status="verified")))
                else:
                    data = root / algorithm / f"{scenario}_seed_{seed}" / "data"
                    data.mkdir(parents=True)
                (data / "results.json").write_text(json.dumps(dict(seed=seed, reward_mean=seed,
                                                                   district_emission=seed + 100,
                                                                   district_cost=seed + 200)))
    loader = tool.load_oe_groups_from_results_root if modular else tool.load_oe_groups_from_run_root
    groups, meta = loader(root, expected_n_seeds=3)
    assert meta["seed_ids"]["OE.1"]["HAPPO"] == [1001, 1002, 1003]
    assert groups["OE.1"]["HAPPO"] == [1001, 1002, 1003]
    assert meta["pairing_eligible"]
    with pytest.raises(ValueError, match="seed"):
        loader(root, expected_n_seeds=3, seeds=[1001, 1001, 1002])


def test_l2_legacy_three_seed_cli_and_json_preserve_identity(tmp_path):
    assert tool.N_SEEDS == 3
    path = _csv(tmp_path, _frame())
    out = tmp_path / "real"
    assert tool.main(["--episodes-csv", str(path), "--output-dir", str(out)]) == 0
    result = json.loads((out / "nonparametric_battery.json").read_text())
    assert result["meta"]["seed_ids"]["OE.1"]["HAPPO"] == [0, 1, 2]
    assert result["sampling"]["aligned_seed_ids"]["OE.1"] == [0, 1, 2]


def test_l2_illustrative_is_opt_in_and_not_scientific_evidence(tmp_path):
    out = tmp_path / "illustrative"
    assert tool.main(["--illustrative-only", "--n-seeds", "3", "--output-dir", str(out)]) == 0
    result = json.loads((out / "nonparametric_battery.json").read_text())
    assert result["meta"]["source"] == "illustrative_synthetic"
    assert result["meta"]["unit"] == "illustrative_draw"
    assert result["scientific_acceptance"] is False


def test_aggregator_friedman_pairs_blocks_by_seed_not_position(tmp_path):
    from tools.eval.aggregate_multiseed_seed_kpis import write_seed_unit_poh
    rows = [dict(scenario="E1", algorithm=algo, seed=seed, has_kpis=True, score=seed*10.0)
            for algo, seeds in (("HAPPO", (0, 1, 2, 3)), ("MAAC", (0, 1, 2, 3)), ("MASAC", (1, 2, 3)))
            for seed in seeds]
    write_seed_unit_poh(tmp_path, rows)
    decisions = pd.read_csv(tmp_path / "decisiones_problemas_objetivos_hipotesis_seed.csv")
    row = decisions[decisions.scenario == "E1"].iloc[0]
    assert row.n_seeds == 3
    # Same score on each common seed, so there is no difference. By position MASAC would look ahead.
    assert not float(row.friedman_chi2) > 1.0


def test_confirmatory_cannot_be_reduced_or_run_on_a_partial_algorithm_set(tmp_path):
    frame = _frame(range(1001, 1013))
    seeds = ["--seeds", *map(str, range(1001, 1013))]
    out = tmp_path / "v1"
    with pytest.raises(SystemExit) as error:
        tool.main(["--episodes-csv", str(_csv(tmp_path, frame)), "--confirmatory-v1", "--n-seeds", "12", *seeds,
                   "--max-seeds", "2", "--output-dir", str(out)])
    assert error.value.code == 2
    partial = _csv(tmp_path, frame[frame.algorithm != "MATD3"])
    assert tool.main(["--episodes-csv", str(partial), "--confirmatory-v1", "--n-seeds", "12", *seeds,
                      "--output-dir", str(out)]) == 2
    assert not (out / "nonparametric_battery.json").exists()


def test_l2_confirmatory_v1_requires_explicit_n_and_seed_ids(tmp_path):
    path = _csv(tmp_path, _frame(range(1001, 1013)))
    out = tmp_path / "v1"
    with pytest.raises(SystemExit) as error:
        tool.main(["--episodes-csv", str(path), "--confirmatory-v1", "--output-dir", str(out)])
    assert error.value.code == 2
    assert tool.main(["--episodes-csv", str(path), "--confirmatory-v1", "--n-seeds", "12",
                      "--seeds", *map(str, range(1001, 1013)), "--output-dir", str(out)]) == 0
    result = json.loads((out / "nonparametric_battery.json").read_text())
    assert result["sampling"]["aligned_seed_ids"]["OE.1"] == list(range(1001, 1013))
    assert result["scientific_acceptance"] is False
