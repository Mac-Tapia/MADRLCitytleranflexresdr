"""SPEC-016 D-V6-27 and D-V6-29: charging by a FIFO queue per vehicle class, in CityLearn's charger format.

Vehicles of a class arrive by the building's schedule and wait in a FIFO queue for a charger of their class;
there may be more vehicles than chargers. A connection lasts the charging time at the nominal power of the
class's mode (energy of the session / power). Each charger gets an hourly table in the ChargerSimulation
format, and the load factor of the chargers is reported.
"""
from datetime import date, timedelta

import numpy as np
import pytest

from uc3m.application.dataset import ev_queue as q

DAYS = [date(2023, 1, 2) + timedelta(days=d) for d in range(7)]     # Monday .. Sunday
OFFICE = {'occupied_hours': [7, 17], 'day_factors_weekday_saturday_sunday': [1.0, 0.08, 0.03]}
H24 = {'occupied_hours': [0, 24], 'day_factors_weekday_saturday_sunday': [1.0, 0.98, 0.95]}
MOTO = q.VehicleClass('moto', battery_kwh=2.7, charge_kw=0.6, session_kwh=1.56)
TAXI = q.VehicleClass('mototaxi', battery_kwh=8.6, charge_kw=3.52, session_kwh=4.78/2)
OPENING = {'kind': 'opening', 'window_h': 2}
STOPS = {'kind': 'stops', 'stops': [[12, 14], [18, 20]]}


def test_opening_arrivals_fall_in_the_first_two_hours_and_leave_at_closing():
    sessions = q.class_sessions(MOTO, vehicles=3, schedule=OFFICE, rule=OPENING, days=DAYS, open_day_min_factor=0.5,
                                rng=np.random.default_rng(0))
    assert len(sessions) == 3*5                                       # weekdays only: Saturday 0.08, Sunday 0.03
    for s in sessions:
        assert s.arrival % 24 in (7, 8) and s.departure % 24 == 17 and s.departure // 24 == s.arrival // 24


def test_a_24_hour_building_receives_vehicles_every_day_and_mototaxis_stop_twice():
    assert len(q.class_sessions(MOTO, vehicles=1, schedule=H24, rule=OPENING, days=DAYS, open_day_min_factor=0.5,
                                rng=np.random.default_rng(0))) == 7
    stops = q.class_sessions(TAXI, vehicles=1, schedule=H24, rule=STOPS, days=DAYS, open_day_min_factor=0.5,
                             rng=np.random.default_rng(0))
    assert len(stops) == 14
    assert {(s.arrival % 24 in (12, 13), s.departure % 24) for s in stops} <= {(True, 14), (False, 20)}


def test_fifo_queue_serves_in_arrival_order_and_waiting_vehicles_connect_when_a_charger_frees():
    # 3 motos at 7:00, one charger, 3 h each at 0.6 kW: they connect at 7, 10 and 13 and leave at closing (17)
    sessions = [q.Session(vehicle=v, arrival=7, departure=17) for v in range(3)]
    result = q.fifo_queue(sessions, chargers=1, vehicle_class=MOTO)
    assert [(a.vehicle, a.charger, a.connect, a.disconnect) for a in result.assignments] == [
        (0, 0, 7, 10), (1, 0, 10, 13), (2, 0, 13, 16)]
    assert result.unserved == [] and result.waiting_hours == [0, 3, 6]


def test_a_vehicle_that_cannot_connect_before_leaving_is_reported_unserved_and_a_late_one_is_truncated():
    sessions = [q.Session(vehicle=v, arrival=7, departure=12) for v in range(3)]
    result = q.fifo_queue(sessions, chargers=1, vehicle_class=MOTO)
    assert [(a.vehicle, a.connect, a.disconnect) for a in result.assignments] == [(0, 7, 10), (1, 10, 12)]
    assert [s.vehicle for s in result.unserved] == [2]


def test_charger_table_follows_citylearn_charger_simulation():
    sessions = [q.Session(vehicle=0, arrival=7, departure=17), q.Session(vehicle=1, arrival=8, departure=17)]
    result = q.fifo_queue(sessions, chargers=1, vehicle_class=MOTO)
    table = q.charger_tables(result, chargers=1, hours=24, vehicle_class=MOTO, ids=['moto_a', 'moto_b'])[0]
    assert list(table) == list(q.CHARGER_COLUMNS)
    state = table['electric_vehicle_charger_state']
    assert state[6] == 2 and list(state[7:13]) == [1]*6 and state[13] == 3 and state[0] == 3
    assert table['electric_vehicle_id'][7] == 'moto_a' and table['electric_vehicle_id'][10] == 'moto_b'
    arrival_soc = 100*(1 - 1.56/2.7)
    assert table['electric_vehicle_estimated_soc_arrival'][10] == pytest.approx(arrival_soc)
    assert table['electric_vehicle_required_soc_departure'][7] == pytest.approx(100.0)
    assert list(table['electric_vehicle_departure_time'][7:10]) == [2, 1, 0]
    assert table['electric_vehicle_estimated_arrival_time'][6] == 1 and table['electric_vehicle_id'][13] == 'NONE'


def test_a_truncated_connection_asks_only_the_soc_it_can_reach_at_nominal_power():
    result = q.fifo_queue([q.Session(0, 7, 9)], chargers=1, vehicle_class=MOTO)
    table = q.charger_tables(result, chargers=1, hours=24, vehicle_class=MOTO, ids=['m'])[0]
    reachable = 100*(1 - 1.56/2.7 + 2*0.6/2.7)
    assert table['electric_vehicle_required_soc_departure'][7] == pytest.approx(reachable)


def test_load_factor_is_delivered_energy_over_installed_power_by_hours():
    sessions = [q.Session(vehicle=v, arrival=7, departure=17) for v in range(3)]
    result = q.fifo_queue(sessions, chargers=2, vehicle_class=MOTO)
    assert q.load_factor(result, chargers=2, hours=24, vehicle_class=MOTO) == pytest.approx(3*1.56/(2*0.6*24))


def _district():
    import sys
    from pathlib import Path

    import yaml
    repo = Path(__file__).resolve().parents[2]
    sys.path.insert(0, str(repo/'tools/dataset'))
    from buildingcsv_inputs import load_building_inventory

    from uc3m.application.dataset import ev_sizing as es
    rules = es.load_ev_rules(repo/'configs/dataset/ev_v6.yaml')
    registry = yaml.safe_load((repo/'configs/dataset/building_types.yaml').read_text(encoding='utf-8'))
    inventory = load_building_inventory()
    return rules, registry, inventory, es.district_ev_plan(inventory, rules)


YEAR = [date(2023, 1, 1) + timedelta(days=d) for d in range(365)]


def test_session_energy_comes_from_the_class_distance_and_consumption():
    rules = _district()[0]
    assert q.vehicle_class('moto', rules).session_kwh == pytest.approx(0.039*40.0)
    assert q.vehicle_class('mototaxi', rules).session_kwh == pytest.approx(0.125*38.25/2)   # 2 stops a day
    pickup = q.vehicle_class('pickup', rules)
    assert pickup.charge_kw == pytest.approx(7.04) and pickup.battery_kwh == pytest.approx(98.4)


def test_every_building_gets_one_table_per_charger_and_a_report_per_class():
    rules, registry, inventory, plans = _district()
    for building, plan in plans.items():
        schedule = registry['schedules'][registry['buildings'][building]['schedule']]
        charging = q.building_charging(building, plan, schedule=schedule, rules=rules, days=YEAR,
                                       use_type=inventory[building].tipo_uso_citylearn)
        assert len(charging.chargers) == plan.chargers
        assert all(len(t['electric_vehicle_charger_state']) == 24*365 for _, _, t in charging.chargers)
        assert sorted(charging.vehicles) == sorted(set(charging.vehicles)) and len(charging.vehicles) == plan.vehicles
        for kind, factor in charging.load_factor.items():
            assert 0.0 <= factor <= 1.0, (building, kind)
        assert set(charging.unserved) == {'moto', 'mototaxi', 'pickup'}
        assert charging.coincidence_cap_kw <= charging.installed_kw + 1e-9
        used = {t['electric_vehicle_id'][i] for _, _, t in charging.chargers
                for i in range(0, 24*365, 7) if t['electric_vehicle_id'][i] != 'NONE'}
        assert used <= set(charging.vehicles)


def test_the_queue_is_reproducible_with_its_fixed_seed():
    rules, registry, inventory, plans = _district()
    schedule = registry['schedules'][registry['buildings'][6]['schedule']]
    runs = [q.building_charging(6, plans[6], schedule=schedule, rules=rules, days=YEAR[:14],
                                use_type=inventory[6].tipo_uso_citylearn) for _ in range(2)]
    first, second = (r.chargers[0][2]['electric_vehicle_id'] for r in runs)
    assert list(first) == list(second)
