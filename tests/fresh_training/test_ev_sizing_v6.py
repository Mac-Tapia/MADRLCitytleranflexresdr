"""SPEC-016 FR-016.5, D-V6-6 and D-V6-21: chargers and vehicles per building from verified sources.

Spaces = parking area / area per space from RNE A.010 (half aisle included); charging points = 1 per
10 spaces above 20 (EPBD 2024 art. 14(2)); EVs = 5 % of the spaces (declared assumption); power by
vehicle class from D.S. 036-2023-EM at 220 V. Heavy-vehicle buildings count light spaces only.
D-V6-23 and D-V6-26: three classes (motorcycles, mototaxis, V2G pickups) in every building, the classes
named by the predominant type sharing 80 % and the others 20 %, with largest-remainder rounding.
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


def test_named_classes_follow_the_predominant_type(rules):
    assert es.named_classes('Motos_Motokars') == ['moto', 'mototaxi']
    assert es.named_classes('Mixed_Motos_Trucks') == ['moto', 'pickup']
    assert es.named_classes('Motos_Taxis_Buses') == ['moto', 'mototaxi']          # buses are heavy, left out
    assert es.named_classes('Bicycles_Motos') == ['moto'] and es.named_classes('Motos_Students') == ['moto']
    for light in ('Military_Vehicles', 'Emergency_Trucks', 'Heavy_Cargo_Trucks', 'Heavy_Industrial_Cranes',
                  'Emergency_Ambulances', 'Medical_Pickups', 'Ambulances_Staff'):
        assert es.named_classes(light) == ['pickup'], light
    assert es.space_class('Motos_Cars') == 'moto' and es.space_class('Medical_Pickups') == 'car'


@pytest.mark.parametrize('vehicle_type, n, expected', [
    ('Motos_Motokars_Massive', 52, {'moto': 21, 'mototaxi': 21, 'pickup': 10}),
    ('Emergency_Ambulances', 11, {'moto': 1, 'mototaxi': 1, 'pickup': 9}),
    ('Motos_Students', 7, {'moto': 5, 'mototaxi': 1, 'pickup': 1}),
    ('Motos_Cars', 1, {'moto': 1, 'mototaxi': 0, 'pickup': 0}),
    ('Motos_Taxis_Buses', 32, {'moto': 13, 'mototaxi': 13, 'pickup': 6}),
])
def test_fleet_split_gives_80_percent_to_the_named_classes(rules, vehicle_type, n, expected):
    fleet = es.fleet_split(vehicle_type, n, rules)
    assert fleet == expected and sum(fleet.values()) == n


def test_chargers_are_one_per_ten_spaces_above_twenty(rules):
    plan = es.ev_plan(parking_m2=2000.0, use_type='Healthcare', vehicle_type='Ambulances_Staff', rules=rules)
    spaces = int(2000.0//rules['space_m2']['car_public']['value'])
    assert plan.spaces == spaces and plan.chargers == spaces//10
    assert plan.space_class == 'car' and plan.fleet['pickup'] >= plan.fleet['moto']
    small = es.ev_plan(parking_m2=200.0, use_type='MultiFamily_Hotel', vehicle_type='Motos_Cars', rules=rules)
    assert small.spaces == int(200.0//rules['space_m2']['moto_private']['value']) and small.spaces > 20
    tiny = es.ev_plan(parking_m2=100.0, use_type='Office', vehicle_type='Motos_Staff', rules=rules)
    assert tiny.spaces <= 20 and tiny.chargers == 0 and tiny.vehicles == 0


def test_vehicles_are_five_percent_of_the_spaces_and_never_exceed_the_chargers_share(rules):
    plan = es.ev_plan(parking_m2=9000.0, use_type='Commercial_Mall', vehicle_type='Motos_Motokars_Massive',
                      rules=rules)
    assert plan.vehicles == round(0.05*plan.spaces) and plan.space_class == 'moto'
    assert plan.vehicles <= plan.chargers
    assert plan.fleet == {'moto': 21, 'mototaxi': 21, 'pickup': 10}


def test_only_pickups_are_bidirectional(rules):
    classes = rules['classes']
    assert set(classes) == {'moto', 'mototaxi', 'pickup'}
    assert classes['pickup']['v2g'] is True and classes['pickup']['discharge_kw']['value'] > 0
    assert classes['moto']['v2g'] is False and classes['mototaxi']['v2g'] is False


def test_every_rule_value_declares_its_origin():
    raw = yaml.safe_load(RULES_PATH.read_text(encoding='utf-8'))
    entries = list(raw['space_m2'].values()) + [raw['ev_share'], raw['charging_points'], raw['fleet_split']]
    for params in raw['classes'].values():
        entries += [v for k, v in params.items() if isinstance(v, dict)]
    for entry in entries:
        assert entry['origin'] in {'measured', 'cited', 'design_rule', 'assumption',
                                   'assumption_pending_user_verification'}, entry
        assert entry.get('source') or entry.get('note'), entry


def test_the_17_buildings_get_a_plan_and_heavy_fleets_are_declared(rules):
    plans = es.district_ev_plan(load_building_inventory(), rules)
    assert len(plans) == 17 and all(p.chargers >= 0 for p in plans.values())
    for b in (8, 9, 14, 16):
        assert plans[b].space_class == 'car' and 'heavy vehicles excluded' in plans[b].note
    totals = {c: sum(p.fleet[c] for p in plans.values()) for c in ('moto', 'mototaxi', 'pickup')}
    assert totals == {'moto': 72, 'mototaxi': 52, 'pickup': 78}
    assert all(min(p.fleet.values()) >= 0 for p in plans.values())
    assert sum(p.chargers for p in plans.values()) > 2                      # replaces the 2-motorcycle pilot
