"""SPEC-016 FR-016.3, D-V6-16 and D-V6-17: air-conditioning capacity from the inventory and EM.030.

Peruvian norms give no AC capacity (EM.050 has no figures). Capacity = splits x 18 000 BTU/h plus,
for a building with a large system, the EM.030 outdoor-air load (Vbz = Rp*Pz + Ra*Az, Table 01) and
the occupant gain. Health buildings use the air changes of MINSA NTS 110, Table 6. The bill
calibration (D-V6-14) checks the result; nothing comes from unverified W/m2 figures.
"""
import sys
from pathlib import Path

import numpy as np
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

from buildingcsv_inputs import load_building_inventory  # noqa: E402
from uc3m.application.dataset import hvac_capacity as hc  # noqa: E402

NORMS_PATH = REPO/'configs/dataset/hvac_norms.yaml'
ORIGINS = {'measured', 'cited', 'design_rule', 'assumption'}


@pytest.fixture(scope='module')
def norms():
    return hc.load_hvac_norms(NORMS_PATH)


def test_moist_air_enthalpy_matches_the_psychrometric_reference():
    # 24 C and 50 % RH at sea level: about 47.8 kJ/kg of dry air (ASHRAE Fundamentals ch. 1).
    assert hc.moist_air_enthalpy_kj_per_kg(24.0, 50.0, 101.325) == pytest.approx(47.8, abs=0.15)
    assert hc.moist_air_enthalpy_kj_per_kg(24.0, 0.0, 101.325) == pytest.approx(1.006*24.0)
    assert hc.station_pressure_kpa(0.0) == pytest.approx(101.325)
    assert hc.station_pressure_kpa(115.02) == pytest.approx(101.325*(1 - 2.25577e-5*115.02)**5.2559)


def test_outdoor_design_enthalpy_is_the_declared_percentile_of_the_hourly_weather():
    t = np.array([25.0, 30.0, 35.0, 28.0])
    rh = np.array([80.0, 70.0, 50.0, 90.0])
    hourly = [hc.moist_air_enthalpy_kj_per_kg(a, b, 100.0) for a, b in zip(t, rh)]
    assert hc.outdoor_design_enthalpy(t, rh, 100.0, percentile=99.0) == pytest.approx(np.percentile(hourly, 99.0))


def test_split_only_building_has_18000_btu_per_hour_per_unit(norms):
    estimate = hc.hvac_capacity_kw(area_m2=1000.0, use_type='Office', split_units=10, has_large_system=False,
                                   norms=norms, outdoor_enthalpy=80.0, indoor_enthalpy=48.0)
    assert estimate.kw_thermal == pytest.approx(10*18000*0.29307107/1000)
    assert estimate.components['ventilation_kw'] == 0.0 and estimate.components['occupants_kw'] == 0.0
    assert estimate.w_per_m2 == pytest.approx(estimate.kw_thermal*1000/1000.0)


def test_large_system_adds_the_em030_outdoor_air_and_the_occupants(norms):
    estimate = hc.hvac_capacity_kw(area_m2=1000.0, use_type='Office', split_units=0, has_large_system=True,
                                   norms=norms, outdoor_enthalpy=80.0, indoor_enthalpy=48.0)
    people = 5/100*1000.0*norms['occupied_fraction']['value']        # Rd = 5 per 100 m2
    vbz_l_s = 2.5*people + 0.3*1000.0                                  # Rp = 2.5, Ra = 0.3
    density = norms['air_density_kg_m3']['value']
    assert estimate.components['people'] == pytest.approx(people)
    assert estimate.components['outdoor_air_l_s'] == pytest.approx(vbz_l_s)
    assert estimate.components['ventilation_kw'] == pytest.approx(density*vbz_l_s/1000*(80.0 - 48.0))
    assert estimate.components['occupants_kw'] == pytest.approx(people*norms['occupant_gain_w']['value']/1000)
    assert estimate.source['ventilation'].startswith('EM.030')


def test_health_buildings_use_the_nts_110_air_changes(norms):
    estimate = hc.hvac_capacity_kw(area_m2=2000.0, use_type='Healthcare_Hospital', split_units=0,
                                   has_large_system=True, norms=norms, outdoor_enthalpy=80.0, indoor_enthalpy=48.0)
    health = norms['use_types']['Healthcare_Hospital']
    height = norms['ceiling_height_m']['value']
    flow_l_s = health['air_changes_per_hour']*2000.0*height*1000/3600
    assert estimate.components['outdoor_air_l_s'] == pytest.approx(flow_l_s)
    assert 'NTS 110' in estimate.source['ventilation']


def test_unknown_use_type_or_negative_input_is_rejected(norms):
    with pytest.raises(ValueError, match='use type'):
        hc.hvac_capacity_kw(area_m2=100.0, use_type='Spaceport', split_units=1, has_large_system=True,
                            norms=norms, outdoor_enthalpy=80.0, indoor_enthalpy=48.0)
    with pytest.raises(ValueError):
        hc.hvac_capacity_kw(area_m2=-1.0, use_type='Office', split_units=1, has_large_system=False,
                            norms=norms, outdoor_enthalpy=80.0, indoor_enthalpy=48.0)


def test_every_norm_value_declares_its_origin_and_cited_values_their_source():
    raw = yaml.safe_load(NORMS_PATH.read_text(encoding='utf-8'))
    entries = [v for k, v in raw.items() if isinstance(v, dict) and k != 'use_types']
    entries += list(raw['use_types'].values())
    for entry in entries:
        assert entry['origin'] in ORIGINS, entry
        if entry['origin'] == 'cited':
            assert entry.get('source'), entry


def test_every_inventory_use_type_has_a_norm_row(norms):
    inventory = load_building_inventory()
    assert len(inventory) == 17
    assert {b.tipo_uso_citylearn for b in inventory.values()} <= set(norms['use_types'])


def test_capacity_of_the_17_buildings_no_longer_follows_the_modeled_demand(norms):
    capacity = hc.district_capacity(load_building_inventory(), norms, outdoor_enthalpy=80.0, indoor_enthalpy=48.0)
    assert len(capacity) == 17 and all(np.isfinite(c.kw_thermal) and c.kw_thermal > 0 for c in capacity.values())
    # iquitos_v5 autosized from the modeled demand: B11 4.7 W/m2 with 120 splits, B04 175.6 W/m2.
    assert capacity[11].w_per_m2 > 4.7 and capacity[11].components['split_kw'] == pytest.approx(120*5.27527926)
    assert capacity[4].w_per_m2 < 175.6
