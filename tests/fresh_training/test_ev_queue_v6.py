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
OFFICE = {'occupied_hours': [7, 17], 'day_factors_weekday_saturday_sunday': [1.0, 0.0, 0.0]}
H24 = {'occupied_hours': [0, 24], 'day_factors_weekday_saturday_sunday': [1.0, 1.0, 1.0]}
MOTO = q.VehicleClass('moto', battery_kwh=2.7, charge_kw=0.6, session_kwh=1.56)
TAXI = q.VehicleClass('mototaxi', battery_kwh=8.6, charge_kw=3.52, session_kwh=4.78/2)
OPENING = {'kind': 'opening', 'window_h': 2}
STOPS = {'kind': 'stops', 'stops': [[12, 14], [18, 20]]}


def test_opening_arrivals_fall_in_the_first_two_hours_and_leave_at_closing():
    sessions = q.class_sessions(MOTO, vehicles=3, schedule=OFFICE, rule=OPENING, days=DAYS,
                                rng=np.random.default_rng(0))
    assert len(sessions) == 3*5                                       # weekdays only: Saturday 0.08, Sunday 0.03
    for s in sessions:
        assert s.arrival % 24 in (7, 8) and s.departure % 24 == 17 and s.departure // 24 == s.arrival // 24


def test_a_24_hour_building_receives_vehicles_every_day_and_mototaxis_stop_twice():
    assert len(q.class_sessions(MOTO, vehicles=1, schedule=H24, rule=OPENING, days=DAYS,
                                rng=np.random.default_rng(0))) == 7
    stops = q.class_sessions(TAXI, vehicles=1, schedule=H24, rule=STOPS, days=DAYS,
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
    # estimated arrival 0 steps on the incoming row, as CityLearn's reference dataset (charger_10_1.csv)
    assert table['electric_vehicle_estimated_arrival_time'][6] == 0 and table['electric_vehicle_id'][13] == 'NONE'


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
        # D-V6-37: the queue's chargers, never more than the vehicles they serve
        units = sum(charging.physical_chargers.values())
        assert (0 < units <= plan.vehicles) if plan.vehicles else not charging.chargers
        assert all(len(t['electric_vehicle_charger_state']) == 24*365 for _, _, t in charging.chargers)
        assert sorted(charging.vehicles) == sorted(set(charging.vehicles)) and len(charging.vehicles) == plan.vehicles
        for kind, factor in charging.load_factor.items():
            assert 0.0 <= factor <= 1.0, (building, kind)
        assert set(charging.unserved) == set(charging.depleted) == {'moto', 'mototaxi', 'pickup'}
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


def test_connection_time_depends_on_the_battery_state_at_charging():
    # D-V6-31: the connection lasts what the battery needs at that moment, (target - SOC) x battery / power.
    # The SOC carries over: a vehicle that left half charged arrives emptier and stays longer the next time.
    sessions = [q.Session(vehicle=0, arrival=7, departure=9),            # cut: 2 h of the 3 h it needs
                q.Session(vehicle=0, arrival=24 + 7, departure=24 + 17)]
    result = q.fifo_queue(sessions, chargers=1, vehicle_class=MOTO)
    first, second = result.assignments
    assert first.arrival_soc == pytest.approx(1 - 1.56/2.7)
    assert first.departure_soc == pytest.approx(1 - 1.56/2.7 + 2*0.6/2.7)
    assert second.arrival_soc == pytest.approx(first.departure_soc - 1.56/2.7)
    needed_h = (1 - second.arrival_soc)*2.7/0.6
    assert second.disconnect - second.connect == int(np.ceil(needed_h - 1e-9)) > 3
    assert second.departure_soc == pytest.approx(1.0)


def test_an_unserved_vehicle_arrives_emptier_and_never_below_zero():
    sessions = [q.Session(vehicle=v, arrival=7, departure=8) for v in range(2)] + \
               [q.Session(vehicle=1, arrival=24 + 7, departure=24 + 17)]
    result = q.fifo_queue(sessions, chargers=1, vehicle_class=MOTO)
    assert [s.vehicle for s in result.unserved] == [1]
    later = result.assignments[-1]
    assert later.vehicle == 1 and later.arrival_soc == pytest.approx(max(0.0, 1 - 2*1.56/2.7))
    assert result.depleted == 1                                      # its trip needed more than it had


def test_required_chargers_is_the_minimum_that_serves_every_session():
    # D-V6-37: chargers of a class = the fewest with which the FIFO queue leaves no vehicle unserved, no trip
    # without energy and every session full over the whole horizon; EPBD points are only reported.
    sessions = [q.Session(vehicle=v, arrival=7, departure=17) for v in range(7)]   # 7 motos, 3 h each, 10 h day
    n = q.required_chargers(sessions, MOTO)
    assert n == 3                                               # 3 chargers serve 3+3+1 in 10 h; 2 serve only 6
    assert q.fifo_queue(sessions, chargers=n, vehicle_class=MOTO).unserved == []
    short = q.fifo_queue(sessions, chargers=n - 1, vehicle_class=MOTO)   # the 7th connects at 16 for 1 h
    assert not q.serves_everyone(short) and q.serves_everyone(q.fifo_queue(sessions, chargers=n, vehicle_class=MOTO))
    assert q.required_chargers([], MOTO) == 0


def test_the_district_has_fewer_chargers_than_vehicles_and_serves_them_all():
    rules, registry, inventory, plans = _district()
    chargers = vehicles = 0
    for building, plan in plans.items():
        schedule = registry['schedules'][registry['buildings'][building]['schedule']]
        charging = q.building_charging(building, plan, schedule=schedule, rules=rules, days=YEAR,
                                       use_type=inventory[building].tipo_uso_citylearn)
        assert sum(charging.unserved.values()) == 0 and sum(charging.depleted.values()) == 0, building
        assert charging.epbd_points == plan.chargers
        chargers += sum(charging.physical_chargers.values())
        vehicles += len(charging.vehicles)
    assert 0 < chargers < vehicles


def test_every_physical_charger_has_two_sockets():
    # D-V6-38: chargers are dual-socket units; the queue's sockets are rounded up to whole units and every
    # socket of a unit is simulated (one action per socket), each at its class power (P-V6-20).
    rules, registry, inventory, plans = _district()
    assert rules['charging_unit']['sockets_per_unit']['value'] == 2
    for building in (1, 6, 11):
        schedule = registry['schedules'][registry['buildings'][building]['schedule']]
        charging = q.building_charging(building, plans[building], schedule=schedule, rules=rules, days=YEAR[:28],
                                       use_type=inventory[building].tipo_uso_citylearn)
        for kind in ('moto', 'mototaxi', 'pickup'):
            sockets = [name for name, k, _ in charging.chargers if k == kind]
            units = charging.physical_chargers[kind]
            assert len(sockets) == 2*units, (building, kind)
            assert units == -(-charging.required_sockets[kind]//2)
            assert all(f'_unit_{u:02d}_socket_' in ' '.join(sockets) for u in range(1, units + 1))


def test_daily_presence_is_bernoulli_with_the_day_factor():
    # D-V6-39: each vehicle comes each day with probability = the building's day factor (fixed seed).
    office = {'occupied_hours': [7, 17], 'day_factors_weekday_saturday_sunday': [1.0, 0.25, 0.0]}
    year = [date(2023, 1, 2) + timedelta(days=d) for d in range(364)]                # 52 full weeks
    sessions = q.class_sessions(MOTO, vehicles=20, schedule=office, rule=OPENING, days=year,
                                rng=np.random.default_rng(1))
    by_kind = {0: 0, 1: 0, 2: 0}
    for s in sessions:
        by_kind[q._day_kind(year[s.arrival//24])] += 1
    assert by_kind[0] == 20*52*5 and by_kind[2] == 0
    assert abs(by_kind[1]/(20*52) - 0.25) < 0.05


def test_daily_km_are_lognormal_around_the_class_mean_and_never_exceed_autonomy():
    # D-V6-40 and P-V6-21: lognormal km with sigma_ln from the 34-45 km/day range of Abaya et al. (2019).
    km = q.draw_daily_km(np.random.default_rng(0), mean_km=40.0, sigma_ln=0.0716, max_km=50.0, size=20000)
    assert abs(km.mean() - 40.0) < 0.2 and km.max() <= 50.0 and km.std() > 1.0
    capped = q.draw_daily_km(np.random.default_rng(0), mean_km=40.0, sigma_ln=0.5, max_km=45.0, size=5000)
    assert capped.max() == pytest.approx(45.0)


def test_charging_time_uses_the_power_that_reaches_the_battery():
    lossy = q.VehicleClass('moto', battery_kwh=2.7, charge_kw=0.6, session_kwh=1.56, efficiency=0.95*0.92)
    assert lossy.charging_hours(1 - 1.56/2.7) == int(np.ceil(1.56/(0.6*0.95*0.92) - 1e-9))   # 3 h -> 3 h
    result = q.fifo_queue([q.Session(0, 7, 17)], chargers=1, vehicle_class=lossy)
    assert result.assignments[0].departure_soc == pytest.approx(1.0)


def test_a_socket_rests_one_hour_between_sessions_so_citylearn_sees_each_departure():
    sessions = [q.Session(vehicle=v, arrival=7, departure=17) for v in range(2)]
    result = q.fifo_queue(sessions, chargers=1, vehicle_class=MOTO, gap_h=1)
    first, second = result.assignments
    assert second.connect == first.disconnect + 1
    table = q.charger_tables(result, chargers=1, hours=24, vehicle_class=MOTO, ids=['a', 'b'])[0]
    assert table['electric_vehicle_charger_state'][first.disconnect] == 2            # incoming, not 1
    assert table['electric_vehicle_estimated_arrival_time'][first.disconnect] == 0.0


def test_a_bidirectional_pickup_stays_connected_until_it_leaves():
    # D-V6-42: the pickup keeps its socket while parked, so it can discharge through V2L (V2B).
    pickup = q.VehicleClass('pickup', battery_kwh=98.4, charge_kw=7.04, session_kwh=10.68, stays_connected=True)
    a = q.fifo_queue([q.Session(0, 9, 22)], chargers=1, vehicle_class=pickup).assignments[0]
    assert (a.connect, a.disconnect) == (9, 22) and a.departure_soc == pytest.approx(1.0)


def test_sockets_are_the_95th_percentile_of_twenty_seeds():
    # D-V6-43: per class, the minimum serving every session in each of 20 drawn years; P95 of those.
    rules, registry, inventory, plans = _district()
    schedule = registry['schedules'][registry['buildings'][6]['schedule']]
    spec = q.vehicle_class('moto', rules)
    needs = [q.required_chargers(q.class_sessions(spec, vehicles=21, schedule=schedule, rule=rules['arrivals']['moto'],
                                                   days=YEAR[:28], rng=np.random.default_rng([k, 6, 0]),
                                                   km=rules['daily_km'], kwh_per_km=0.039, mean_km=40.0,
                                                   max_km=2.7*0.8/0.039), spec, gap_h=1)
             for k in range(20)]
    assert q.socket_percentile(needs, 95) == int(np.ceil(np.percentile(needs, 95)))
    assert rules['socket_sizing']['seeds']['value'] == 20 and rules['socket_sizing']['percentile']['value'] == 95
