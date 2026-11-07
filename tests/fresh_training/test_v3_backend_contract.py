"""SPEC-017 FR-017.3: a universal MADRL backend contract on the CityLearn v3 layer.

The layer declares what any MADRL gets (per-agent spaces, local observations, CTDE state, rewards) and a
registry where a backend declares its action interface, reward kind, use of the global state and adapter.
The four native backends are built in; a new one is registered and runs an episode without editing the layer.
"""
from pathlib import Path

import numpy as np
import pytest
import yaml

from citylearn.v3 import backend_contract as bc
from citylearn.v3.environment import make_citylearn_v3_env

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SCHEMA = REPO/CAMPAIGN['dataset_root']/'splits/train_2023/schema.json'


@pytest.fixture(scope='module')
def env():
    environment = make_citylearn_v3_env(schema_path=SCHEMA, scenario='E1', seed=0, episode_time_steps=24)
    yield environment
    environment.close()


def test_the_four_native_backends_are_built_in_with_their_interface():
    backends = bc.registered_backends()
    assert {'HAPPO', 'MASAC', 'MATD3', 'MAAC'} <= set(backends)
    assert backends['HAPPO'].action_interface == 'continuous' and backends['MATD3'].action_interface == 'continuous'
    assert backends['MASAC'].action_interface == 'discrete_masked' and backends['MAAC'].action_interface == 'discrete_masked'
    for name in ('HAPPO', 'MASAC', 'MATD3', 'MAAC'):
        assert bc.resolve_adapter(name).__name__ == backends[name].adapter.split(':')[1], name


def test_the_layer_satisfies_the_contract_any_backend_relies_on(env):
    report = bc.check_contract(env)
    assert report.passed, report.failures
    assert report.n_agents == 17 and report.state_dim == sum(report.observation_dims.values())


def test_a_new_backend_registers_and_runs_without_editing_the_layer(env):
    def random_policy(environment, seed):
        rng = np.random.default_rng(seed)
        return lambda observations: {agent: rng.uniform(environment.action_space(agent).low,
                                                        environment.action_space(agent).high)
                                     for agent in observations}

    spec = bc.MADRLBackend(name='REFERENCE_RANDOM', action_interface='continuous', reward='per_agent',
                           uses_global_state=False, adapter='citylearn.dec_pomdp:CityLearnDecPOMDPEnv',
                           policy_factory=random_policy, source='test reference backend')
    bc.register_backend(spec)
    try:
        result = bc.run_smoke_episode(env, 'REFERENCE_RANDOM', steps=12, seed=3)
        assert result.steps == 12 and np.isfinite(result.total_reward) and result.agents == 17
    finally:
        bc.unregister_backend('REFERENCE_RANDOM')
    assert 'REFERENCE_RANDOM' not in bc.registered_backends()


def test_an_invalid_backend_declaration_is_rejected():
    with pytest.raises(ValueError, match='action interface'):
        bc.register_backend(bc.MADRLBackend(name='BAD', action_interface='telepathic', reward='team',
                                            uses_global_state=True, adapter='x:y'))
    with pytest.raises(ValueError, match='already registered'):
        bc.register_backend(bc.registered_backends()['HAPPO'])


def test_operational_gate_runs_every_native_adapter_on_a_built_dataset():
    # FR-017.4: the dataset loads in v3, meets the contract and every registered backend's own adapter steps.
    result = bc.operational_gate(SCHEMA, steps=2, seed=0)
    assert result.passed, result.failures
    assert set(result.backends) >= {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}
    assert all(r['steps'] == 2 and np.isfinite(r['reward']) for r in result.backends.values())
    assert result.contract.n_agents == 17


def test_operational_gate_fails_closed_on_a_broken_dataset(tmp_path):
    broken = tmp_path/'schema.json'
    broken.write_text('{"buildings": {}}', encoding='utf-8')
    result = bc.operational_gate(broken, steps=1, seed=0)
    assert not result.passed and result.failures


def test_every_dataset_build_ends_with_the_operational_gate():
    # FR-017.4: the builder's dataset_verified includes the v3 operational gate and records its result.
    builder = (REPO/'tools/dataset/build_fresh_campaign_dataset.py').read_text(encoding='utf-8')
    assert "'v3_operational'" in builder and 'operational_gate(' in builder
    assert "v3_operational_gate.json" in builder
