"""SPEC-016 T1 of docs/plans/modulo3b_iquitos_v6.md: chargers and EVs of the queue into a CityLearn schema.

Every charger of the plan gets its ChargerSimulation CSV and its schema entry; every EV id in a CSV exists in
electric_vehicles_def with its class battery; only pickups discharge (V2L 6.6 kW, D-V6-32); mode, connector and
standard come from the class (D-V6-33); battery and charger parameters from D-V6-34; CityLearn v3 loads it.
"""
import json
import shutil
import sys
from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

from buildingcsv_inputs import load_building_inventory  # noqa: E402
import write_ev_v6 as wv  # noqa: E402
from uc3m.application.dataset import ev_queue as q  # noqa: E402
from uc3m.application.dataset import ev_sizing as es  # noqa: E402

RULES = es.load_ev_rules(REPO/'configs/dataset/ev_v6.yaml')
REGISTRY = yaml.safe_load((REPO/'configs/dataset/building_types.yaml').read_text(encoding='utf-8'))
INVENTORY = load_building_inventory()
PLANS = es.district_ev_plan(INVENTORY, RULES)
YEAR = [date(2023, 1, 1) + timedelta(days=d) for d in range(365)]
CAMPAIGN = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
SPLIT = REPO/CAMPAIGN['dataset_root']/'splits/train_2023'


def _schema(buildings):
    return {'buildings': {f'Building_{b}': {'chargers': {'old_charger': {}}} for b in buildings},
            'electric_vehicles_def': {'EV_OLD': {}}}


@pytest.fixture(scope='module')
def written(tmp_path_factory):
    out = tmp_path_factory.mktemp('ev')
    schema = _schema((6, 11))
    report = wv.write_ev_fleet(out, schema, plans={b: PLANS[b] for b in (6, 11)}, registry=REGISTRY, rules=RULES,
                               inventory=INVENTORY, days=YEAR)
    return out, schema, report


def test_every_charger_gets_its_csv_and_schema_entry_and_old_ones_are_replaced(written):
    out, schema, report = written
    for b in (6, 11):
        chargers = schema['buildings'][f'Building_{b}']['chargers']
        assert 'old_charger' not in chargers and len(chargers) == report[b]['chargers']
        assert 0 < report[b]['chargers'] <= PLANS[b].vehicles and report[b]['epbd_points'] == PLANS[b].chargers
        for name, entry in chargers.items():
            frame = pd.read_csv(out/entry['charger_simulation'])
            assert list(frame.columns) == list(q.CHARGER_COLUMNS) and len(frame) == 8760, name
    assert 'EV_OLD' not in schema['electric_vehicles_def']
    assert sum(report[6]['class_chargers'].values()) == report[6]['chargers'] and set(report[6]['load_factor']) == set(es.CLASSES)


def test_every_ev_in_a_csv_exists_with_its_class_battery(written):
    out, schema, _ = written
    evs = schema['electric_vehicles_def']
    assert len(evs) == PLANS[6].vehicles + PLANS[11].vehicles
    for b in (6, 11):
        for entry in schema['buildings'][f'Building_{b}']['chargers'].values():
            ids = set(pd.read_csv(out/entry['charger_simulation'])['electric_vehicle_id']) - {'NONE'}
            kind = entry['hardware']['vehicle_class']
            for ev in ids:
                battery = evs[ev]['battery']['attributes']
                assert battery['capacity'] == RULES['classes'][kind]['battery_kwh']['value'], ev
                assert battery['efficiency'] == 0.92 and battery['depth_of_discharge'] == 0.80
                assert battery['capacity_loss_coefficient'] == 1e-5


def test_only_pickups_discharge_and_equipment_follows_the_class(written):
    _, schema, _ = written
    for entry in schema['buildings']['Building_6']['chargers'].values():
        kind, hardware, attributes = entry['hardware']['vehicle_class'], entry['hardware'], entry['attributes']
        charging = RULES['classes'][kind]['charging']
        assert hardware['charging_mode'] == f"IEC_61851-1_Mode_{charging['mode']}_AC"
        assert hardware['connector'] == charging['connector'] and hardware['direction'] == charging['direction']
        assert attributes['max_charging_power'] == RULES['classes'][kind]['charge_kw']['value']
        assert attributes['efficiency'] == 0.95
        expected_discharge = 6.6 if kind == 'pickup' else 0.0
        assert attributes['max_discharging_power'] == pytest.approx(expected_discharge)
        assert attributes['min_charging_power'] == pytest.approx(1.32 if attributes['max_charging_power'] >= 1.32
                                                                 else 0.0)


def test_citylearn_v3_loads_and_steps_the_written_fleet(tmp_path):
    from citylearn.v3.environment import make_citylearn_v3_env
    split = tmp_path/'train_2023'
    shutil.copytree(SPLIT, split)
    schema = json.loads((split/'schema.json').read_text(encoding='utf-8'))
    wv.write_ev_fleet(split, schema, plans={6: PLANS[6]}, registry=REGISTRY, rules=RULES, inventory=INVENTORY,
                      days=YEAR, keep_others=True)
    (split/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    env = make_citylearn_v3_env(schema_path=split/'schema.json', scenario='E1', seed=0, episode_time_steps=24)
    try:
        observations, _ = env.reset()
        actions = {a: np.zeros(env.action_space(a).shape, dtype=np.float32) for a in env.possible_agents}
        _, rewards, _, _, _ = env.step(actions)
        assert all(np.isfinite(float(r)) for r in rewards.values())
        b6 = next(b for b in env.env.buildings if b.name == 'Building_6')
        written = schema['buildings']['Building_6']['chargers']
        assert len(b6.electric_vehicle_chargers) == len(written) < PLANS[6].vehicles
        pickups = [c for c in b6.electric_vehicle_chargers if c.max_discharging_power > 0]
        assert len(pickups) == sum(1 for e in written.values() if e['hardware']['vehicle_class'] == 'pickup')
        assert all(c.max_discharging_power == pytest.approx(6.6) for c in pickups)
    finally:
        env.close()
