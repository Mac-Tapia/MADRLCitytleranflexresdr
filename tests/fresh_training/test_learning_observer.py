"""T5 (unit part): learning is observed at real optimizer steps, not inferred.

Uses a real small torch optimizer behind the native finite-gradient guard; no
mock learner. The native micro-training of the four backends lives in
test_real_learning.py and needs the fresh campaign splits.
"""
import json
import math
from pathlib import Path

import pytest
import torch

from uc3m.adapters.algorithms import learning_observer as lo
from uc3m.adapters.algorithms import native_entrypoint as ne

REPO = Path(__file__).resolve().parents[2]


def _native_guard(specs, audit_path=None):
    """Same contract as citylearn_v3_training_common.install_finite_optimizer_step_guard."""
    for spec in specs:
        optimizer, module = spec['optimizer'], spec['module']
        original = optimizer.step

        def guarded(*a, _o=optimizer, _m=module, _orig=original, **k):
            if any(p.grad is not None and not torch.isfinite(p.grad).all() for p in _m.parameters()):
                _o.zero_grad()
                return None
            return _orig(*a, **k)
        optimizer.step = guarded
    return {'installed_optimizers': len(specs)}


def _spec():
    module = torch.nn.Linear(3, 1)
    return {'owner': 'actor_agent0', 'module': module, 'optimizer': torch.optim.SGD(module.parameters(), lr=0.1)}


def _train_step(spec, poison=False):
    spec['optimizer'].zero_grad()
    loss = spec['module'](torch.ones(1, 3)).sum()
    if poison:
        loss = loss*float('nan')
    loss.backward()
    spec['optimizer'].step()


def test_observer_counts_only_guard_passed_updates(tmp_path):
    observer = lo.LearningObserver(campaign_id='fresh_test_v1', attempt_id='a001')
    install = observer.wrap_guard_installer(_native_guard)
    spec = _spec()
    install([spec], None)
    _train_step(spec)
    _train_step(spec, poison=True)
    _train_step(spec)
    evidence = observer.finalize(env_steps=96, checkpoint_bundle_hash='0'*64)
    assert evidence.successful_optimizer_updates_by_owner == {'actor_agent0': 2}
    assert evidence.nonfinite_events == 1
    assert evidence.initial_parameter_hashes['actor_agent0'] != evidence.final_parameter_hashes['actor_agent0']
    assert evidence.verified is True


def test_no_updates_cannot_complete():
    observer = lo.LearningObserver(campaign_id='fresh_test_v1', attempt_id='a001')
    observer.wrap_guard_installer(_native_guard)([_spec()], None)
    evidence = observer.finalize(env_steps=96, checkpoint_bundle_hash='0'*64)
    assert evidence.verified is False and 'no_successful_update:actor_agent0' in evidence.reasons
    observer = lo.LearningObserver(campaign_id='fresh_test_v1', attempt_id='a002')
    spec = _spec()
    observer.wrap_guard_installer(_native_guard)([spec], None)
    _train_step(spec)
    assert 'no_checkpoint' in observer.finalize(env_steps=96, checkpoint_bundle_hash=None).reasons
    with pytest.raises(RuntimeError):
        lo.LearningObserver('fresh_test_v1', 'a003').finalize(env_steps=0, checkpoint_bundle_hash=None)


def test_instrumentation_preserves_step_semantics():
    observed, plain = _spec(), _spec()
    plain['module'].load_state_dict(observed['module'].state_dict())
    observer = lo.LearningObserver('fresh_test_v1', 'a001')
    observer.wrap_guard_installer(_native_guard)([observed], None)
    _native_guard([plain], None)
    for _ in range(3):
        _train_step(observed)
        _train_step(plain)
    for a, b in zip(observed['module'].parameters(), plain['module'].parameters()):
        assert torch.equal(a, b)


def test_native_cache_redirected_per_attempt(tmp_path):
    common = ne.load_native_common(REPO)
    original = common._CSV_CACHE_DIR
    with ne.attempt_isolation(common, tmp_path/'attempt'):
        assert common._CSV_CACHE_DIR == tmp_path/'attempt'/'native_cache'
        assert not common._CSV_CACHE_DIR.exists() or not any(common._CSV_CACHE_DIR.iterdir())
    assert common._CSV_CACHE_DIR == original
    assert 'outputs/dataset_cache' in ne.REDIRECTED_DEPENDENCY_CACHES.values()


def test_salvage_is_read_from_the_native_job_directory(tmp_path):
    native = ['--scenario', 'E1', '--seed', '901', '--episodes', '2']
    job = ne.job_directory(tmp_path/'native', native)
    assert job == tmp_path/'native'/'E1_s901'
    (job/'data').mkdir(parents=True)
    (job/'data/results.json').write_text(json.dumps({'hyperparameters': {
        'run_completed_with_salvage': True, 'run_error': 'AssertionError: demand is greater'}}), encoding='utf-8')
    common = ne.load_native_common(REPO)
    assert ne.salvage_reason(common.read_job_results_json(job)) == 'AssertionError: demand is greater'
    assert ne.salvage_reason({'status': 'completed'}) is None


def test_placeholder_training_rejected():
    with pytest.raises(ValueError):
        ne.trainer_script(REPO, 'RANDOM')
    with pytest.raises(ValueError):
        ne.native_arguments(['--resume'])  # every fresh attempt starts from zero
    assert '--no-resume' in ne.native_arguments(['--episodes', '2'])
    for algorithm in ('HAPPO', 'MASAC', 'MATD3', 'MAAC'):
        assert ne.trainer_script(REPO, algorithm).is_file()


# --- Audit 2026-11-01 (items 2, 7): runtime weights and supervision of every step -------------------

def _breakdown_obs(step):
    return [{'net_electricity_consumption': 10.0 + step, 'electricity_pricing': 0.17, 'carbon_intensity': 0.5,
             'electrical_storage_soc': 0.2 + 0.1*step},
            {'net_electricity_consumption': -3.0, 'electricity_pricing': 0.17, 'carbon_intensity': 0.5}]


def test_reward_supervision_hooks_the_dec_pomdp_step(monkeypatch):
    from citylearn.dec_pomdp import CityLearnDecPOMDPEnv
    from citylearn.v3.reward import CityLearnV3MADRLRewardFunction

    class Core:
        reward_function = CityLearnV3MADRLRewardFunction({'central_agent': False}, algorithm='MAAC',
                                                         scenario='E3')
        steps = 0

    def fake_step(self, actions):
        self.env.reward_function.calculate(_breakdown_obs(self.env.steps))
        self.env.steps += 1
        return {}, {}, {}, {}, {}

    def fake_reset(self, seed=None, options=None):
        self.env.reward_function.reset()
        return {}, {}
    monkeypatch.setattr(CityLearnDecPOMDPEnv, 'step', fake_step)
    monkeypatch.setattr(CityLearnDecPOMDPEnv, 'reset', fake_reset)
    env = CityLearnDecPOMDPEnv.__new__(CityLearnDecPOMDPEnv)
    env.env, env.reward_aggregation = Core(), 'team_mean'
    supervisor = ne.RewardSupervisor()
    with supervisor.installed():
        for episode in range(2):
            env.reset()
            for _ in range(3):
                env.step({'agent_0': [0.1*episode, 0.3], 'agent_1': [0.0, 0.0]})
    assert CityLearnDecPOMDPEnv.step is fake_step          # hooks removed afterwards
    report = supervisor.report()
    assert report['effective_axis_weights'] == pytest.approx({'flex': 0.15, 'carbon': 0.25, 'cost': 0.60})
    assert report['reward_aggregation'] == ['team_mean']
    assert report['supervision']['episodes'] == 2 and report['supervision']['steps'] == 6
    assert report['supervision']['constraint_dominance_ratio'] >= 0
    detail = report['supervision']['episodes_detail']
    assert set(detail[0]['action_std_by_agent']) == {'agent_0', 'agent_1'}


def test_inconsistent_runtime_weights_are_reported():
    supervisor = ne.RewardSupervisor()
    supervisor.observe_reward({'flex': 0.6, 'carbon': 0.15, 'cost': 0.25}, {'kind': 'scenario_catalog'})
    supervisor.observe_reward({'flex': 0.55, 'carbon': 0.16875, 'cost': 0.28125}, {'kind': 'scenario_catalog'})
    report = supervisor.report()
    assert report['effective_axis_weights'] is None and len(report['effective_axis_weights_seen']) == 2


def test_real_environment_reward_reads_the_derived_catalog(monkeypatch, tmp_path):
    """Micro real-simulator check: the reward built by the v3 factory reads UC3M_SCENARIO_CATALOG."""
    from citylearn.v3 import make_citylearn_v3_env
    from uc3m.application.training.fresh_campaign import write_derived_scenario_catalog
    schema = REPO/'data/campaigns/iquitos_v1/splits/train_2023/schema.json'
    assert schema.is_file(), 'fresh training split missing'
    derived = write_derived_scenario_catalog(REPO/'configs/scenarios.yaml', 'E3', (0.13125, 0.21875, 0.65),
                                             'p065', tmp_path/'catalog')
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(derived['path']))
    env = make_citylearn_v3_env(schema_path=str(schema), scenario='E3', seed=0, episode_time_steps=24,
                                madrl_algorithm='MATD3', normalize_observations=True)
    supervisor = ne.RewardSupervisor()
    with supervisor.installed():
        env.reset()
        for _ in range(3):
            env.step({agent: env.action_space(agent).sample()*0 for agent in env.possible_agents})
    report = supervisor.report()
    assert report['effective_axis_weights'] == pytest.approx({'flex': 0.13125, 'carbon': 0.21875, 'cost': 0.65},
                                                             abs=1e-12)
    assert report['axis_weights_source']['sha256'] == derived['sha256']
    assert report['reward_aggregation'] == ['team_mean']
    assert report['supervision']['steps'] == 3


def test_supervision_records_every_kpi_layer_per_episode(monkeypatch):
    """Two short real v3 episodes: Layer A (district + buildings) and Layer B per episode, plus trend."""
    from citylearn.v3 import make_citylearn_v3_env
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(REPO/'configs/scenarios.yaml'))
    schema = REPO/'data/campaigns/iquitos_v1/splits/train_2023/schema.json'
    env = make_citylearn_v3_env(schema_path=str(schema), scenario='E1', seed=0, episode_time_steps=24,
                                madrl_algorithm='MATD3', normalize_observations=True)
    supervisor = ne.RewardSupervisor()
    with supervisor.installed():
        for _ in range(2):
            env.reset()
            for _ in range(23):
                env.step({agent: env.action_space(agent).sample() for agent in env.possible_agents})
    report = supervisor.report()['supervision']
    assert report['episodes'] == 2
    nine = ('peak_average', 'ramping_average', 'one_minus_load_factor_average', 'carbon_emissions_total',
            'carbon_emissions_delta', 'ci_weighted_consumption', 'electricity_cost_total',
            'electricity_cost_delta', 'peak_billing')
    for episode in report['episodes_detail']:
        indicators = episode['thesis_indicators']
        assert set(nine) <= set(indicators['district'])
        assert len(indicators['buildings']) == 17
        assert all(set(nine) <= set(b) for b in indicators['buildings'].values())
        assert indicators['district']['peak_billing'] is None and 'peak_billing' in indicators['pending']
        layer_b = episode['citylearn_v3']
        assert layer_b['error'] is None, layer_b['error']
        assert len(layer_b['gains']) == 26 and layer_b['building_objective_kpis']
    trend = report['kpi_trend']
    assert set(nine) <= set(trend) and any(k.startswith('citylearn_v3:') for k in trend)
