"""R-A-144: a frozen episode never falls back to CityLearn's legacy composite tariff."""
from pathlib import Path

import pytest

from uc3m.adapters.citylearn import policy_inference as pi

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = REPO / "data/campaigns/iquitos_v4"


def test_scenario_without_catalog_is_rejected_before_building_an_environment():
    policy = pi.RbcPolicy()
    with pytest.raises(ValueError, match="scenario catalog"):
        pi.run_frozen_episode(CAMPAIGN / "splits/validation_2024", policy, CAMPAIGN, steps=1, scenario="E1")
    assert getattr(policy, "adapter", None) is None
