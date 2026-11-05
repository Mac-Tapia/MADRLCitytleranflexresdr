"""Native interval boundary: N dataset rows must permit N physical decisions."""
from pathlib import Path

import pytest

from uc3m.adapters.citylearn import policy_inference as pi
from uc3m.adapters.citylearn.fresh_observations import frozen_observation_limits, load_normalizer
from uc3m.adapters.algorithms.native_entrypoint import attempt_isolation

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT/'data/campaigns/iquitos_v5'


@pytest.mark.parametrize('intervals', [24, 48])
def test_native_runtime_processes_the_last_physical_interval(intervals, tmp_path):
    common = pi._common()
    policy = pi.RbcPolicy()
    with attempt_isolation(common, tmp_path), frozen_observation_limits(load_normalizer(DATA/'normalizer.json')):
        policy.build_env(common, DATA/'splits/train_2023/schema.json', 'E1', 901, intervals)
        observations = policy.reset(901)
        taken, done = 0, False
        while not done and taken <= intervals:
            observations, done = policy.step(policy.act(observations, deterministic=True))
            taken += 1
        assert done and taken == intervals
        core = pi._citylearn_env(policy.adapter)
        assert any(float(b.net_electricity_consumption[intervals-1]) != 0 for b in core.buildings)
        from citylearn.v3.objectives import evaluate_objectives
        assert isinstance(evaluate_objectives(core), dict)
