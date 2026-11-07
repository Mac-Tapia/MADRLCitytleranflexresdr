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
        # physical units never outnumber the vehicles (sockets may: a pickup keeps its socket, D-V6-42)
        assert 0 < sum(report[b]['physical_chargers'].values()) <= PLANS[b].vehicles
        assert report[b]['epbd_points'] == PLANS[b].chargers
        for name, entry in chargers.items():
            frame = pd.read_csv(out/entry['charger_simulation'])
            assert list(frame.columns) == list(q.CHARGER_COLUMNS) + [q.TRIP_COLUMN] and len(frame) == 8760, name
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
        assert len(b6.electric_vehicle_chargers) == len(written)
        pickups = [c for c in b6.electric_vehicle_chargers if c.max_discharging_power > 0]
        assert len(pickups) == sum(1 for e in written.values() if e['hardware']['vehicle_class'] == 'pickup')
        assert all(c.max_discharging_power == pytest.approx(6.6) for c in pickups)
    finally:
        env.close()


def test_charger_csv_names_follow_the_pattern_the_integrity_audit_reads(written):
    # The CSV integrity audit and the orphan cleaner only see charger_*.csv (failure of iquitos_v6_trial2).
    out, schema, _ = written
    referenced = {e['charger_simulation'] for b in (6, 11) for e in schema['buildings'][f'Building_{b}']['chargers'].values()}
    assert referenced and all(name.startswith('charger_') and name.endswith('.csv') for name in referenced)
    assert referenced <= {p.name for p in out.glob('charger_*.csv')}


def test_ev_battery_curves_are_fixed_so_the_departure_soc_is_reachable(written):
    # Without curves CityLearn draws random ones that cut the power near full (energy_model.py); P-V6-22 fixes
    # them flat at the class power and battery efficiency, the assumption the queue's charging time uses.
    _, schema, _ = written
    for ev in schema['electric_vehicles_def'].values():
        attributes = ev['battery']['attributes']
        assert attributes['capacity_power_curve'] == [[0.0, 1.0], [1.0, 1.0]]
        assert attributes['power_efficiency_curve'] == [[0.0, 0.92], [1.0, 0.92]]
    hardware = next(iter(schema['buildings']['Building_6']['chargers'].values()))['hardware']
    assert hardware['socket_count_per_physical_unit'] == RULES['charging_unit']['sockets_per_unit']['value']


def test_citylearn_v3_carries_the_real_soc_between_sessions(tmp_path):
    # D-V6-41: with electric_vehicle_arrival_soc = endogenous, a vehicle arrives with its last real SOC minus the
    # trip energy written by the queue (electric_vehicle_trip_kwh), not with the fixed SOC of the CSV, and no
    # random drift while away. With zero actions nothing charges, so each arrival is emptier than the last.
    from citylearn.v3.environment import make_citylearn_v3_env
    split = tmp_path/'train_2023'
    shutil.copytree(SPLIT, split)
    schema = json.loads((split/'schema.json').read_text(encoding='utf-8'))
    wv.write_ev_fleet(split, schema, plans={6: PLANS[6]}, registry=REGISTRY, rules=RULES, inventory=INVENTORY,
                      days=YEAR, keep_others=True)
    assert schema['electric_vehicle_arrival_soc'] == 'endogenous'
    (split/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    connections = []                                  # (hour, EV, trip kWh) of every moto connection
    for entry in schema['buildings']['Building_6']['chargers'].values():
        if entry['hardware']['vehicle_class'] != 'moto':
            continue
        frame = pd.read_csv(split/entry['charger_simulation'])
        assert 'electric_vehicle_trip_kwh' in frame.columns
        on = frame['electric_vehicle_charger_state'].to_numpy() == 1
        connections += [(t, frame['electric_vehicle_id'][t], float(frame['electric_vehicle_trip_kwh'][t]))
                        for t in range(1, 400) if on[t] and not on[t - 1]]
    connections.sort()
    ev_id = next(e for _, e, _ in connections if sum(1 for _, x, _ in connections if x == e) >= 2)
    (t1, _, _), (t2, _, trip) = [c for c in connections if c[1] == ev_id][:2]
    same = [t1, t2]
    capacity = RULES['classes']['moto']['battery_kwh']['value']
    env = make_citylearn_v3_env(schema_path=split/'schema.json', scenario='E1', seed=0, episode_time_steps=same[1] + 2)
    try:
        env.reset()
        zero = {a: np.zeros(env.action_space(a).shape, dtype=np.float32) for a in env.possible_agents}
        ev = next(v for v in env.env.electric_vehicles if v.name == ev_id)
        for _ in range(same[1] + 1):
            env.step(zero)
        soc = [float(x) for x in ev.battery.soc]
        # the arrival SOC is set on the step before the connection (the battery recomputes it on connecting)
        first_trip = next(trip_kwh for t, e, trip_kwh in connections if e == ev_id and t == same[0])
        assert soc[same[0] - 1] == pytest.approx(1.0 - first_trip/capacity, abs=1e-6)      # full before trip 1
        left = soc[same[1] - 2]                                                        # last real SOC, no drift
        assert left == pytest.approx(soc[same[0]], abs=0.02)                           # zero action: no charge
        assert soc[same[1] - 1] == pytest.approx(max(0.0, left - trip/capacity), abs=1e-6)
        assert soc[same[1] - 1] < soc[same[0] - 1]
    finally:
        env.close()


def test_pickup_discharge_never_exceeds_the_building_demand(tmp_path):
    # D-V6-28 and D-V6-32: V2B behind the meter, so the EV discharge of each hour is capped at the building's own
    # demand and never exported; schema electric_vehicle_discharge_limit = building_demand (v3 layer).
    from citylearn.v3.environment import make_citylearn_v3_env
    split = tmp_path/'train_2023'
    shutil.copytree(SPLIT, split)
    schema = json.loads((split/'schema.json').read_text(encoding='utf-8'))
    wv.write_ev_fleet(split, schema, plans={11: PLANS[11]}, registry=REGISTRY, rules=RULES, inventory=INVENTORY,
                      days=YEAR, keep_others=True)
    assert schema['electric_vehicle_discharge_limit'] == 'building_demand'
    (split/'schema.json').write_text(json.dumps(schema), encoding='utf-8')
    env = make_citylearn_v3_env(schema_path=split/'schema.json', scenario='E1', seed=0, episode_time_steps=72)
    try:
        env.reset()
        b11 = next(b for b in env.env.buildings if b.name == 'Building_11')
        agent = env.possible_agents[[b.name for b in env.env.buildings].index('Building_11')]
        names = list(b11.active_actions)
        action = np.zeros(env.action_space(agent).shape, dtype=np.float32)
        for i, n in enumerate(names):
            action[i] = -1.0 if 'electric_vehicle' in n else 0.0                # every charger discharges fully
        others = {a: np.zeros(env.action_space(a).shape, dtype=np.float32) for a in env.possible_agents}
        discharged = False
        for _ in range(70):
            env.step({**others, agent: action})
            t = env.env.time_step - 1
            ev_kw = sum(min(float(c.electricity_consumption[t]), 0.0) for c in b11.electric_vehicle_chargers)
            discharged |= ev_kw < -1e-6
            rest = float(b11.net_electricity_consumption[t]) - ev_kw              # building without EV discharge
            assert -ev_kw <= max(rest, 0.0) + 1e-6, (t, ev_kw, rest)
        assert discharged
    finally:
        env.close()
