"""SPEC-017 FR-017.2: the builder takes 1..N buildings of any declared type, and the site's years and place.

The building set comes from the site's building registry, never from a constant. A building whose schedule
or whose use type has no norm row is rejected by name, never filled in.
"""
from pathlib import Path

import pytest
import yaml

from uc3m.application.dataset import site as st

import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[2]/'tools/dataset'))
from site_time import hourly_index  # noqa: E402

REPO = Path(__file__).resolve().parents[2]
REGISTRY = yaml.safe_load((REPO/'configs/dataset/building_types.yaml').read_text(encoding='utf-8'))
NORMS = yaml.safe_load((REPO/'configs/dataset/hvac_norms.yaml').read_text(encoding='utf-8'))
BUILDER = (REPO/'tools/dataset/build_fresh_campaign_dataset.py').read_text(encoding='utf-8')


def _registry(buildings):
    return {'schedules': REGISTRY['schedules'], 'buildings': buildings}


def test_iquitos_site_declares_its_years_and_place_with_origin():
    site = st.load_site(REPO/'configs/sites/iquitos.yaml')
    assert site.years == (2023, 2024, 2025)
    assert site.latitude == pytest.approx(-3.7491) and site.longitude == pytest.approx(-73.2538)
    assert site.time_zone_name == 'America/Lima'


def test_the_building_set_comes_from_the_registry():
    assert st.site_buildings(REGISTRY, NORMS) == tuple(range(1, 18))
    two = _registry({7: REGISTRY['buildings'][7], 3: REGISTRY['buildings'][3]})
    assert st.site_buildings(two, NORMS) == (3, 7)


def test_a_building_without_schedule_or_norm_is_rejected_by_name():
    no_schedule = dict(REGISTRY['buildings'][1], schedule='night_market')
    with pytest.raises(ValueError, match=r"building 1.*night_market"):
        st.site_buildings(_registry({1: no_schedule}), NORMS)
    no_norm = dict(REGISTRY['buildings'][1], peer_group='Stadium')
    with pytest.raises(ValueError, match=r"building 1.*Stadium"):
        st.site_buildings(_registry({1: no_norm}), NORMS)
    with pytest.raises(ValueError, match='no buildings'):
        st.site_buildings(_registry({}), NORMS)


def test_the_hourly_index_follows_the_years_and_leap_days():
    index = hourly_index((2023, 2024, 2025), 'America/Lima')
    assert len(index) == 26304 == st.hours_in_years((2023, 2024, 2025)) and str(index.tz) == 'America/Lima'
    assert len(hourly_index((2024,), 'UTC')) == 8784 == st.hours_in_years((2024,))


def test_the_builder_keeps_no_building_year_or_place_constant():
    for literal in ('tuple(range(1, 18))', 'YEARS = (2023', '-3.7491', "'America/Lima'", '26304',
                    '8784 if year == 2024', '/17 within'):
        assert literal not in BUILDER, literal
    assert 'site_buildings(' in BUILDER and 'SITE.years' in BUILDER


@pytest.mark.parametrize('name', ['fix_solar_pvlib.py', 'dimension_ev_chargers.py'])
def test_the_helpers_of_the_builder_take_the_place_and_years_from_the_site(name):
    source = (REPO/'tools/dataset'/name).read_text(encoding='utf-8')
    for literal in ('-3.7491', "'America/Lima'", '"America/Lima"', '106\n', 'YEARS = [2023', 'year == 2024'):
        assert literal not in source, (name, literal)
    assert 'load_default_site()' in source, name
