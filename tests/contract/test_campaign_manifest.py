"""Contract tests for the full 4x3x3 experimental campaign configuration."""
import itertools
import json
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_PATH = ROOT / 'configs' / 'experiments' / 'full_campaign_4x3x3.yaml'


def test_campaign_config_covers_4x3x3():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    treatments = list(itertools.product(
        config['algorithms'], config['scenarios'], config['seeds'],
    ))
    assert len(treatments) == 36
    assert config['episode_time_steps'] == 8760
    assert config['episodes'] == 50


def test_campaign_config_algorithms_match_launchers():
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    expected = {'HAPPO', 'MASAC', 'MATD3', 'MAAC'}
    assert set(config['algorithms']) == expected


def test_campaign_config_scenarios_match_catalog():
    from uc3m.application.configuration import load_scenario_catalog
    config = yaml.safe_load(CONFIG_PATH.read_text(encoding='utf-8'))
    catalog = load_scenario_catalog(ROOT / 'configs' / 'scenarios.yaml')
    for sid in config['scenarios']:
        assert sid in catalog, f"Scenario {sid} not in catalog"
