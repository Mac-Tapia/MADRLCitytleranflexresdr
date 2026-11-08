"""The reward is a three-level cooperative game, and each of the four MADRL backends receives it.

Level 1 (agent = building i): local terms on the three axes plus EV/BESS penalties.
Level 3 (preference = scenario): the 3x3 matrix W of configs/objective_policies.yaml
scalarizes the axes; row E1/E2/E3 is the one the reward applies at runtime.
Level 2 (team = district): team_mean gives every agent the same payoff, an
identical-interest game whose global optimum is a Nash equilibrium.
The backends are exercised through their own environment adapters with the
fresh micro-trained policies of this campaign (no mocks).
"""
from pathlib import Path

import numpy as np
import pytest
import yaml

from uc3m.adapters.citylearn import policy_inference as pi

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = (lambda c: REPO/c['dataset_root'])(__import__('yaml').safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8')))   # the active campaign dataset (configs/experiments/iquitos.yaml)
SCHEMA = CAMPAIGN/'splits/validation_2024/schema.json'
AXIS_KEYS = {'flexibility': 'flex', 'co2_emissions': 'carbon', 'energy_cost': 'cost'}


def _matrix():
    policies = yaml.safe_load((REPO/'configs/objective_policies.yaml').read_text(encoding='utf-8'))['policies']
    return {s: {AXIS_KEYS[a]: float(w) for a, w in policies[s]['weights'].items()} for s in ('E1', 'E2', 'E3')}


def _reward_function(dec_pomdp_env):
    core = dec_pomdp_env.env
    return getattr(core, 'unwrapped', core).reward_function


def test_weight_matrix_is_a_3x3_row_stochastic_preference():
    w = _matrix()
    assert set(w) == {'E1', 'E2', 'E3'} and all(set(r) == {'flex', 'carbon', 'cost'} for r in w.values())
    assert all(abs(sum(r.values()) - 1.0) < 1e-12 for r in w.values())
    # Each scenario has its own dominant axis: the rows are a cyclic permutation of one profile.
    assert [max(r, key=r.get) for r in (w['E1'], w['E2'], w['E3'])] == ['flex', 'carbon', 'cost']


@pytest.mark.parametrize('scenario', ['E1', 'E2', 'E3'])
def test_local_reward_applies_the_scenario_row_and_team_mean_pays_everyone(scenario, monkeypatch):
    from citylearn.v3 import make_citylearn_v3_env
    assert SCHEMA.is_file(), 'fresh validation split missing'
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(REPO/'configs/scenarios.yaml'))
    env = make_citylearn_v3_env(schema_path=str(SCHEMA), scenario=scenario, seed=0, episode_time_steps=6,
                                madrl_algorithm='MATD3', normalize_observations=True)
    env.reset()
    row = _matrix()[scenario]
    for _ in range(3):
        rewards = env.step({agent: env.action_space(agent).sample()*0 for agent in env.possible_agents})[1]
        breakdown = _reward_function(env)._last_component_breakdown
        assert {k: pytest.approx(v, abs=1e-12) for k, v in breakdown['axis_weights'].items()} == row   # level 3
        scale = float(breakdown['reward_scale'])
        locals_ = []
        for c in breakdown['components']:                                                             # level 1
            expected = scale*(row['flex']*c['flex'] + row['carbon']*c['carbon'] + row['cost']*c['cost']
                              + c['ev'] + c['bess_cycle'])
            assert c['local_reward'] == pytest.approx(expected, rel=1e-9, abs=1e-12)
            locals_.append(c['local_reward'])
        team = float(np.mean(locals_))
        assert breakdown['team_reward'] == pytest.approx(team, rel=1e-12, abs=1e-15)
        assert env.reward_aggregation == 'team_mean'                                                  # level 2
        assert len(rewards) == 17
        # The Dec-POMDP hands rewards out as float32: equality up to float32 precision.
        assert all(float(r) == pytest.approx(team, rel=1e-6, abs=1e-9) for r in rewards.values())


def _received(algorithm, step_result):
    """The reward exactly as the backend adapter hands it to the learner."""
    if algorithm == 'HAPPO':                      # (obs, state, [[r] per agent], dones, infos, avail)
        return [float(r[0]) for r in step_result[2]]
    if algorithm == 'MASAC':                      # (team reward, terminated, info) -> QMIX mixer
        return [float(step_result[0])]
    return [float(r) for r in np.asarray(step_result[1], dtype=float).ravel()]   # MATD3/MAAC per agent


@pytest.mark.parametrize('algorithm', ['HAPPO', 'MASAC', 'MATD3', 'MAAC'])
def test_each_backend_learns_from_the_team_payoff(algorithm, monkeypatch, native_attempts):
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(REPO/'configs/scenarios.yaml'))
    policy = pi.load_native_policy(algorithm, native_attempts[algorithm])
    env = policy.build_env(pi._common(), SCHEMA, policy.resolve_scenario('E1'), 2024, 6)
    observations = policy.reset(2024)
    captured = []
    original = env.step

    def recorded_step(*args, **kwargs):
        result = original(*args, **kwargs)
        captured.append(result)
        return result
    monkeypatch.setattr(env, 'step', recorded_step)
    for _ in range(3):
        observations, _ = policy.step(policy.act(observations))
        received = _received(algorithm, captured[-1])
        team = _reward_function(policy.adapter.env)._last_component_breakdown['team_reward']
        expected_count = 1 if algorithm == 'MASAC' else len(policy.adapter.agents)
        assert len(received) == expected_count
        # Every agent (or the single mixed-value learner of MASAC) is paid the same team value.
        assert all(r == pytest.approx(team, rel=1e-6, abs=1e-9) for r in received), (received, team)
