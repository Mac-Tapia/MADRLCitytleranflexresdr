"""SPEC-016 FR-016.5, D-V6-6 and D-V6-21: chargers and vehicles per building from verified sources.

Spaces = parking area / area per space from RNE A.010 (half aisle included); charging points = 1 per
10 spaces above 20 (EPBD 2024 art. 14(2)); EVs = 5 % of the spaces (declared assumption); power by
vehicle class from D.S. 036-2023-EM at 220 V. Heavy-vehicle buildings count light spaces only.
"""
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

from buildingcsv_inputs import load_building_inventory  # noqa: E402
from uc3m.application.dataset import ev_sizing as es  # noqa: E402

RULES_PATH = REPO/'configs/dataset/ev_v6.yaml'


@pytest.fixture(scope='module')
def rules():
    return es.load_ev_rules(RULES_PATH)


def test_space_areas_derive_from_the_a010_dimensions(rules):
    space = rules['space_m2']
    assert space['car_public']['value'] == pytest.approx(2.50*(5.00 + 6.50/2))
    assert space['car_private']['value'] == pytest.approx(2.40*(5.00 + 6.00/2))
    assert space['moto_public']['value'] == pytest.approx(1.50*(2.50 + 6.50/2))
    assert space['moto_private']['value'] == pytest.approx(1.50*(2.50 + 6.00/2))


def test_vehicle_class_follows_the_predominant_type(rules):
    assert es.vehicle_class('Motos_Motokars') == 'moto' and es.vehicle_class('Mixed_Motos_Trucks') == 'moto'
    assert es.vehicle_class('Bicycles_Motos') == 'moto' and es.vehicle_class('Motos_Cars') == 'moto'
    for heavy in ('Military_Vehicles', 'Emergency_Trucks', 'Heavy_Cargo_Trucks', 'Heavy_Industrial_Cranes',
                  'Emergency_Ambulances', 'Medical_Pickups', 'Ambulances_Staff'):
        assert es.vehicle_class(heavy) == 'car', heavy


def test_chargers_are_one_per_ten_spaces_above_twenty(rules):
    plan = es.ev_plan(parking_m2=2000.0, use_type='Healthcare', vehicle_type='Ambulances_Staff', rules=rules)
    spaces = int(2000.0//rules['space_m2']['car_public']['value'])
    assert plan.spaces == spaces and plan.chargers == spaces//10
    assert plan.charger_kw == pytest.approx(220*32/1000) and plan.vehicle_class == 'car'
    small = es.ev_plan(parking_m2=200.0, use_type='MultiFamily_Hotel', vehicle_type='Motos_Cars', rules=rules)
    assert small.spaces == int(200.0//rules['space_m2']['moto_private']['value']) and small.spaces > 20
    tiny = es.ev_plan(parking_m2=100.0, use_type='Office', vehicle_type='Motos_Staff', rules=rules)
    assert tiny.spaces <= 20 and tiny.chargers == 0 and tiny.vehicles == 0


def test_vehicles_are_five_percent_of_the_spaces_and_never_exceed_the_chargers_share(rules):
    plan = es.ev_plan(parking_m2=9000.0, use_type='Commercial_Mall', vehicle_type='Motos_Motokars_Massive',
                      rules=rules)
    assert plan.vehicles == round(0.05*plan.spaces) and plan.vehicle_class == 'moto'
    assert plan.vehicles <= plan.chargers
    assert plan.charger_kw == pytest.approx(220*16/1000)
    assert plan.daily_kwh_per_vehicle == pytest.approx(rules['daily_energy_kwh']['moto']['value'])


def test_every_rule_value_declares_its_origin():
    raw = yaml.safe_load(RULES_PATH.read_text(encoding='utf-8'))
    entries = [v for group in ('space_m2', 'charger_kw', 'daily_energy_kwh') for v in raw[group].values()]
    entries += [raw['ev_share'], raw['charging_points']]
    for entry in entries:
        assert entry['origin'] in {'measured', 'cited', 'design_rule', 'assumption',
                                   'assumption_pending_user_verification'}, entry
        assert entry.get('source') or entry.get('note'), entry


def test_the_17_buildings_get_a_plan_and_heavy_fleets_are_declared(rules):
    plans = es.district_ev_plan(load_building_inventory(), rules)
    assert len(plans) == 17 and all(p.chargers >= 0 for p in plans.values())
    for b in (8, 9, 14, 16):
        assert plans[b].vehicle_class == 'car' and 'heavy vehicles excluded' in plans[b].note
    assert sum(p.chargers for p in plans.values()) > 2                      # replaces the 2-motorcycle pilot
