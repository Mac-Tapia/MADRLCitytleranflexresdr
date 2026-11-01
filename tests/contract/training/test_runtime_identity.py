from dataclasses import replace
from pathlib import Path


def test_training_horizon_changes_identity():
    from uc3m.domain.experiments import ExperimentSpec
    from uc3m.application.configuration import load_scenario_catalog
    root = Path(__file__).resolve().parents[3]
    scenario = load_scenario_catalog(root/'configs/scenarios.yaml')['E1']
    spec = ExperimentSpec('HAPPO', scenario, 0, 'a'*64, 'b'*40, {}, 2)
    assert replace(spec, episode_time_steps=8).fingerprint() != spec.fingerprint()


def test_citylearn_consumes_catalog_tariff_when_explicitly_selected(monkeypatch):
    from citylearn.scenario_manager import ScenarioManager
    root = Path(__file__).resolve().parents[3]
    monkeypatch.setenv('UC3M_SCENARIO_CATALOG', str(root/'configs/scenarios.yaml'))
    config = ScenarioManager().select_scenario('E1')
    assert not config.use_real_time_pricing
    assert not config.use_time_of_use
    assert config.reward_weights == {'flex': 0.6, 'carbon': 0.15, 'cost': 0.25}
