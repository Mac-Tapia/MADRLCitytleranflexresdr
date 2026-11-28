"""Keep recorded building tariffs in the project-owned CityLearn entry points."""
from contextlib import contextmanager
from dataclasses import replace
import logging
from pathlib import Path

from uc3m.application.configuration import load_scenario_catalog


logger = logging.getLogger(__name__)


def _shared_price(env, length):
    import numpy as np

    series = [np.asarray(building.pricing.electricity_pricing)[:length] for building in env.buildings]
    if not series or not all(np.array_equal(series[0], prices) for prices in series[1:]):
        return None
    return series[0]


@contextmanager
def recorded_tariff(catalog, scenario):
    """Scope the native tariff hooks to one run in its dedicated worker process."""
    if catalog is None or scenario is None:
        yield
        return
    policy = load_scenario_catalog(Path(catalog))[scenario].tariff_policy
    if policy.mode != 'recorded':
        yield
        return

    from citylearn.scenario_manager import ScenarioManager
    from citylearn.v3 import objectives

    original_scenarios = ScenarioManager.SCENARIOS
    original_apply = ScenarioManager.apply_scenario_modifications
    original_description = ScenarioManager.get_scenario_description
    original_district_price = objectives._district_price_signal

    def apply(manager, env):
        if manager.current_scenario != scenario:
            return original_apply(manager, env)
        logger.info('Scenario %s uses recorded tariffs for %d buildings.', scenario, len(env.buildings))

    def describe(manager):
        result = original_description(manager)
        if manager.current_scenario == scenario:
            result['tariff'] = 'RECORDED'
        return result

    selected = original_scenarios[scenario]
    ScenarioManager.SCENARIOS = {
        **original_scenarios,
        scenario: replace(selected, description=f'{selected.primary_kpi} with recorded tariffs'),
    }
    ScenarioManager.apply_scenario_modifications = apply
    ScenarioManager.get_scenario_description = describe
    objectives._district_price_signal = _shared_price
    try:
        yield
    finally:
        ScenarioManager.SCENARIOS = original_scenarios
        ScenarioManager.apply_scenario_modifications = original_apply
        ScenarioManager.get_scenario_description = original_description
        objectives._district_price_signal = original_district_price
