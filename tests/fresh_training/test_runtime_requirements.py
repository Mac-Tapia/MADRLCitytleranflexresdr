"""SPEC-015: resource requirements follow the active dataset and each HPO candidate.

The requirements were fixed numbers from iquitos_v1 (1 850 EVs). Nobody recomputed them when the
campaign moved to iquitos_v5, whose observations are ten times smaller, so the guard would have
refused MASAC everywhere. These tests measure the real training environments of the configured
campaign and bind every declared requirement to the project's own estimators.
"""
import math
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

from uc3m.adapters.algorithms import native_entrypoint as ne

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO/'CityLearn/scripts'
EPISODE = 8760


def _yaml(path):
    return yaml.safe_load((REPO/path).read_text(encoding='utf-8'))


NATIVE = _yaml('configs/algorithms/native.yaml')
CAMPAIGN = _yaml('configs/experiments/iquitos.yaml')
SCHEMA = REPO/CAMPAIGN['dataset_root']/'splits/train_2023/schema.json'
GRID = NATIVE['hyperparameter_grid']['hidden_dimension']


def _scripts():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))


@pytest.fixture(scope='module')
def masac_dims():
    _scripts()
    from citylearn_v3_training_common import CityLearnSMACDiscreteEnv
    info = CityLearnSMACDiscreteEnv(schema_path=str(SCHEMA), scenario='E1', seed=0, episode_time_steps=EPISODE,
                                    action_bins=3, discrete_action_mode='axis', algorithm='MASAC').get_env_info()
    return {k: int(info[k]) for k in ('n_agents', 'obs_shape', 'state_shape', 'n_actions')}


@pytest.fixture(scope='module')
def matd3_dims():
    _scripts()
    import citylearn_v3_training_common as common
    sys.path.insert(0, str(REPO/'external/off-policy'))
    from offpolicy.utils.util import get_dim_from_space
    env = common.CityLearnOffPolicyVecEnv(schema_path=str(SCHEMA), scenario='E1', seed=0,
                                          episode_time_steps=EPISODE, algorithm='MATD3')
    return {'num_agents': int(env.num_agents), 'obs_dim': int(env.observation_space[0].shape[0]),
            'share_obs_dim': int(env.share_observation_space[0].shape[0]),
            'act_dim': int(np.sum(get_dim_from_space(env.action_space[0])))}


def test_the_rule_reproduces_the_margin_of_the_previous_numbers():
    # The v1 replay estimate of 65.3 GiB was declared as 72: the same 10 % margin.
    assert ne.requirement_from_estimate(65.3, ne.RAM_FLOOR_GIB) == 72
    assert ne.requirement_from_estimate(1.0, ne.RAM_FLOOR_GIB) == ne.RAM_FLOOR_GIB
    assert ne.requirement_from_estimate(0.5, ne.VRAM_FLOOR_GIB) == ne.VRAM_FLOOR_GIB


def test_masac_requirements_follow_the_active_dataset_and_every_candidate(masac_dims):
    _scripts()
    import train_citylearn_v3_masac as masac
    fixed = NATIVE['algorithms']['MASAC']['fixed']
    declared = NATIVE['algorithms']['MASAC']['runtime_requirements']
    replay = masac.estimate_replay_buffer_gib(buffer_size=fixed['buffer_size'], episode_limit=EPISODE, **masac_dims)
    assert declared['min_ram_gib'] == ne.requirement_from_estimate(replay, ne.RAM_FLOOR_GIB)
    by_candidate = {int(k): v for k, v in declared['min_vram_gib_by_rnn_hidden_dim'].items()}
    assert set(by_candidate) == set(GRID)
    for rnn in GRID:
        critic = masac.estimate_masac_critic_gpu_gib(
            batch_episodes=fixed['critic_batch_size'], episode_limit=EPISODE, rnn_hidden_dim=rnn,
            qmix_hidden_dim=rnn//2, hyper_hidden_dim=rnn, n_agents=masac_dims['n_agents'],
            obs_shape=masac_dims['obs_shape'], n_actions=masac_dims['n_actions'],
            state_shape=masac_dims['state_shape'])
        assert by_candidate[rnn] == ne.requirement_from_estimate(critic, ne.VRAM_FLOOR_GIB), rnn


def test_the_tuned_matd3_reservation_covers_the_active_dataset(matd3_dims):
    # 40 GiB is the per-worker reservation tuned for the Colab campaign (owner 2026-11-06: not to be
    # changed); it sets the phase-2 parallelism. It must still cover what the active dataset needs.
    _scripts()
    from citylearn_v3_training_common import effective_matd3_per_policy_buffer_size, estimate_matd3_replay_ram_gib
    row = NATIVE['algorithms']['MATD3']
    per_policy = effective_matd3_per_policy_buffer_size(int(row['fixed']['buffer_size']),
                                                        num_agents=matd3_dims['num_agents'])
    replay = estimate_matd3_replay_ram_gib(per_policy_buffer=per_policy, **matd3_dims)
    assert row['runtime_requirements'] == {'min_ram_gib': 40, 'min_vram_gib': 4,
                                           'applies_from_episode_time_steps': 1000}
    assert row['runtime_requirements']['min_ram_gib'] >= ne.requirement_from_estimate(replay, ne.RAM_FLOOR_GIB)


def test_native_capacity_is_unchanged():
    algorithms = NATIVE['algorithms']
    assert algorithms['MASAC']['fixed'] == {'buffer_size': 50, 'critic_batch_size': 32, 'critic_train_steps': 1}
    assert algorithms['MATD3']['fixed']['buffer_size'] == 744600
    assert int(algorithms['MAAC']['fixed']['buffer_length']) == 5*EPISODE


def _masac_check(native_args, ram=500.0, vram=200.0, steps=EPISODE):
    return ne.check_runtime_resources('MASAC', NATIVE['algorithms']['MASAC']['runtime_requirements'],
                                      episode_time_steps=steps, native_args=native_args,
                                      measure=lambda: {'ram_gib': ram, 'vram_gib': vram})


def test_the_guard_applies_the_vram_of_the_attempts_candidate():
    by_candidate = {int(k): v for k, v in
                    NATIVE['algorithms']['MASAC']['runtime_requirements']['min_vram_gib_by_rnn_hidden_dim'].items()}
    small, large = min(GRID), max(GRID)
    between = (by_candidate[small] + by_candidate[large])/2
    assert _masac_check(['--rnn-hidden-dim', str(small)], vram=between)['accepted'] is True
    refused = _masac_check(['--rnn-hidden-dim', str(large)], vram=between)
    assert refused['accepted'] is False and 'insufficient_resources:MASAC:vram' in refused['reasons']
    assert refused['requirements']['min_vram_gib'] == by_candidate[large]


@pytest.mark.parametrize('native_args', [['--rnn-hidden-dim', '64'], [], ['--rnn-hidden-dim', 'wide']])
def test_a_candidate_without_a_declared_requirement_is_refused(native_args):
    check = _masac_check(native_args)
    assert check['accepted'] is False
    assert any(reason.startswith('unsupported_candidate:MASAC:rnn_hidden_dim') for reason in check['reasons'])


def test_a_short_smoke_is_not_refused_for_its_candidate():
    assert _masac_check(['--rnn-hidden-dim', '64'], steps=168)['accepted'] is True


def test_every_requirement_is_finite_and_at_least_the_floor():
    for name, row in NATIVE['algorithms'].items():
        req = row['runtime_requirements']
        values = [req['min_ram_gib']] + ([req['min_vram_gib']] if 'min_vram_gib' in req
                                         else list(req['min_vram_gib_by_rnn_hidden_dim'].values()))
        assert all(math.isfinite(v) and v >= ne.VRAM_FLOOR_GIB for v in values), name
        assert req['min_ram_gib'] >= ne.RAM_FLOOR_GIB, name


def test_a_phase_reserves_the_largest_candidate_not_zero():
    # Any candidate of the grid may run in the phase. Reading a missing min_vram_gib as 0 would let
    # MASAC reserve no VRAM and plan about 20 concurrent workers on an 80 GB GPU instead of 1.
    from uc3m.application.training.phases import worker_limit
    requirements = {name: row['runtime_requirements'] for name, row in NATIVE['algorithms'].items()}
    largest = max(requirements['MASAC']['min_vram_gib_by_rnn_hidden_dim'].values())
    plan = worker_limit(['HAPPO', 'MASAC'], requirements, {'ram_gib': 500.0, 'vram_gib': 80.0, 'cpu_count': 32},
                        episode_time_steps=EPISODE)
    assert plan['bounds']['vram'] == int(80.0//largest) == 1 and plan['workers'] == 1
    short = worker_limit(['HAPPO', 'MASAC'], requirements, {'ram_gib': 500.0, 'vram_gib': largest - 1, 'cpu_count': 32},
                         episode_time_steps=EPISODE)
    assert short['workers'] == 0 and 'insufficient_resources:MASAC:vram' in short['reasons']
