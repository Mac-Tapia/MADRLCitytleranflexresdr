"""SPEC-015 FR-015.7 (D03, owner decision D-M3-6): native action interfaces with masks.

Actions are padded to the largest equipment count of the district. On iquitos_v5, 16 of the 17
buildings have 2 of the 4 padded actuators, so 4 of the 9 discrete axis actions moved equipment
that does not exist and acted as a no-op. A discrete agent must never choose an action without
equipment; the equipment behind every action comes from the schema's action_names.
"""
import re
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO/'CityLearn/scripts'
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SCHEMA = REPO/CAMPAIGN['dataset_root']/'splits/train_2023/schema.json'
KWARGS = dict(schema_path=str(SCHEMA), scenario='E1', seed=0, episode_time_steps=24, action_bins=3,
              discrete_action_mode='axis')


def _common():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    import citylearn_v3_training_common as common
    return common


@pytest.fixture(scope='module')
def masac_env():
    return _common().CityLearnSMACDiscreteEnv(algorithm='MASAC', **KWARGS)


@pytest.fixture(scope='module')
def maac_env():
    return _common().CityLearnMAACVecEnv(algorithm='MAAC', **KWARGS)


def _moves_only_real_equipment(row, dim):
    return not np.any(np.asarray(row)[dim:])


def test_valid_rows_are_exactly_the_actions_of_real_equipment(masac_env):
    adapter = masac_env.adapter
    table = np.asarray(adapter.discrete_action_table)
    for agent in adapter.agents:
        dim = adapter.action_dims[agent]
        expected = [r for r in range(len(table)) if _moves_only_real_equipment(table[r], dim)]
        assert adapter.discrete_action_rows_by_agent[agent] == expected, agent
        assert expected[0] == 0 and not np.any(table[0])                  # the no-op is always available
        assert len(adapter.action_names_by_agent[agent]) == dim           # every real actuator is named
    counts = sorted(len(rows) for rows in adapter.discrete_action_rows_by_agent.values())
    assert counts[-1] == len(table)                                        # the largest building uses all rows
    assert counts[0] < len(table)                                          # smaller buildings are masked


def test_masac_never_sees_an_action_without_equipment(masac_env):
    adapter = masac_env.adapter
    for index, agent in enumerate(adapter.agents):
        mask = np.asarray(masac_env.get_avail_agent_actions(index))
        assert mask.shape == (masac_env.n_actions,)
        assert set(np.flatnonzero(mask)) == set(adapter.discrete_action_rows_by_agent[agent]), agent


def test_maac_agents_get_spaces_of_their_real_size(maac_env):
    adapter = maac_env.adapter
    table = np.asarray(adapter.discrete_action_table)
    for index, agent in enumerate(adapter.agents):
        rows = adapter.discrete_action_rows_by_agent[agent]
        assert maac_env.action_space[index].n == len(rows), agent
        for local, row in enumerate(rows):
            one_hot = np.eye(len(rows))[local]
            assert maac_env.global_discrete_index(index, one_hot) == row
            assert _moves_only_real_equipment(table[row], adapter.action_dims[agent])


def test_maac_steps_with_its_own_spaces(maac_env):
    maac_env.reset()
    actions = [[np.eye(space.n)[space.n - 1] for space in maac_env.action_space]]
    observations, rewards, dones, _ = maac_env.step(actions)
    assert np.asarray(observations).shape[1] == maac_env.n_agents and np.isfinite(np.asarray(rewards)).all()


def test_the_action_map_names_the_equipment_of_every_action(masac_env):
    adapter = masac_env.adapter
    mapping = adapter.discrete_action_map()
    assert set(mapping) == set(adapter.agents)
    for agent, rows in mapping.items():
        assert [entry['index'] for entry in rows] == adapter.discrete_action_rows_by_agent[agent]
        assert rows[0]['equipment'] is None and rows[0]['value'] == 0.0
        names = adapter.action_names_by_agent[agent]
        assert all(entry['equipment'] in names for entry in rows[1:]), agent


def test_continuous_outputs_without_equipment_are_inert_and_declared(masac_env):
    adapter = masac_env.adapter
    for agent in adapter.agents:
        padded = np.ones(adapter.max_action_dim, dtype=np.float32)
        assert adapter._continuous_action_for_agent(agent, padded).shape == (adapter.action_dims[agent],)
    native = yaml.safe_load((REPO/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))['algorithms']
    for name in ('HAPPO', 'MATD3'):
        assert any('D03' in item and 'inert' in item for item in native[name]['declared_limitations']), name


def test_equipment_names_are_the_schema_action_names_of_all_17_buildings(masac_env):
    adapter = masac_env.adapter
    schema_names = adapter._core_env().action_names
    assert len(adapter.agents) == 17
    for index, agent in enumerate(adapter.agents):
        assert adapter.action_names_by_agent[agent] == list(schema_names[index]), agent
        assert not any(name.startswith('action_') for name in adapter.action_names_by_agent[agent]), agent


def test_continuous_action_map_declares_every_padded_output(masac_env):
    adapter = masac_env.adapter
    mapping = adapter.continuous_action_map()
    assert set(mapping) == set(adapter.agents)
    for agent, entries in mapping.items():
        dim, names = adapter.action_dims[agent], adapter.action_names_by_agent[agent]
        assert [entry['index'] for entry in entries] == list(range(adapter.max_action_dim))
        assert [entry['equipment'] for entry in entries[:dim]] == names, agent
        assert all(entry['equipment'] is None and entry['inert'] for entry in entries[dim:]), agent
        assert not any(entry['inert'] for entry in entries[:dim]), agent
    assert any(len(entries) > adapter.action_dims[agent] for agent, entries in mapping.items())


@pytest.mark.parametrize('launcher, key', [('happo', 'continuous_action_map'), ('matd3', 'continuous_action_map'),
                                           ('masac', 'discrete_action_map'), ('maac', 'discrete_action_map')])
def test_every_launcher_records_the_action_map_of_its_backend(launcher, key):
    source = (SCRIPTS/f'train_citylearn_v3_{launcher}.py').read_text(encoding='utf-8')
    assert re.search(rf'"{key}":\s*[\w.]*adapter\.{key}\(\)', source), launcher


def test_frozen_masac_evaluation_uses_the_same_mask():
    source = (REPO/'uc3m/adapters/citylearn/policy_inference.py').read_text(encoding='utf-8')
    assert 'get_avail_agent_actions' in source
    assert 'available = np.ones(n_actions' not in source
