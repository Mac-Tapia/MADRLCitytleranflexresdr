from __future__ import annotations

from pathlib import Path

import citylearn.scenario_manager as citylearn_scenarios
import pytest

from uc3m.adapters.citylearn.objectives import project_reward_weights

PROJECT_ROOT = Path(__file__).resolve().parents[2]
SCENARIOS = ("E1", "E2", "E3")


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_projection_matches_citylearn_builtin_weights(scenario: str) -> None:
    builtin = citylearn_scenarios.ScenarioManager.SCENARIOS[scenario].reward_weights

    assert project_reward_weights(scenario) == pytest.approx(builtin)


@pytest.mark.parametrize("scenario", SCENARIOS)
def test_projection_matches_citylearn_canonical_catalog_path(
    scenario: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("UC3M_SCENARIO_CATALOG", str(PROJECT_ROOT / "configs/scenarios.yaml"))

    selected = citylearn_scenarios.ScenarioManager().select_scenario(scenario)

    assert project_reward_weights(scenario) == pytest.approx(selected.reward_weights)
