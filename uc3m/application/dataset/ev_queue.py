"""Charging by a FIFO queue per vehicle class (SPEC-016 D-V6-27 and D-V6-29), in CityLearn's charger format.

- Arrivals (D-V6-29): motorcycles and pickups arrive in the first hours after the building opens and leave
  at closing; mototaxis make short stops. Hours are drawn with a fixed seed.
- Queue (D-V6-27 (1)): the vehicles of a class wait in arrival order (FIFO) for a charger of their class;
  there may be more vehicles than chargers. A vehicle that cannot connect before it leaves is unserved.
- Charging time (D-V6-27 (2)): a connection lasts the energy of the session / the nominal power of the
  class's mode, rounded up to whole hours and cut at the departure; the agent decides the power inside it.
- Load factor (D-V6-27 (5)): delivered energy / (chargers x power x hours).

Implementation rules pending the owner (SPEC-016 P-V6-14 to P-V6-16): a day is open when its day factor is
at least ``open_day_min_factor``; a vehicle arrives having used one session's energy and asks for a full
battery (only what nominal power can reach inside a cut connection); the charger is released when the
charging time ends.
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Mapping, Sequence

import numpy as np

CHARGER_COLUMNS = ('electric_vehicle_charger_state', 'electric_vehicle_id', 'electric_vehicle_departure_time',
                   'electric_vehicle_required_soc_departure', 'electric_vehicle_estimated_arrival_time',
                   'electric_vehicle_estimated_soc_arrival')
CONNECTED, INCOMING, AWAY = 1, 2, 3


@dataclass(frozen=True)
class VehicleClass:
    name: str
    battery_kwh: float
    charge_kw: float
    session_kwh: float

    @property
    def charging_hours(self) -> int:
        return max(1, math.ceil(self.session_kwh/self.charge_kw - 1e-9))

    @property
    def arrival_soc(self) -> float:
        soc = 1.0 - self.session_kwh/self.battery_kwh
        if not 0.0 <= soc < 1.0:
            raise ValueError(f'{self.name}: session energy {self.session_kwh} kWh does not fit the battery')
        return soc


@dataclass(frozen=True)
class Session:
    vehicle: int
    arrival: int        # absolute hour index
    departure: int      # absolute hour index, exclusive


@dataclass(frozen=True)
class Assignment:
    vehicle: int
    charger: int
    arrival: int
    connect: int
    disconnect: int     # exclusive


@dataclass(frozen=True)
class QueueResult:
    assignments: list = field(default_factory=list)
    unserved: list = field(default_factory=list)
    waiting_hours: list = field(default_factory=list)


def _day_kind(day: date) -> int:
    return 0 if day.weekday() < 5 else (1 if day.weekday() == 5 else 2)


def class_sessions(vehicle_class: VehicleClass, *, vehicles: int, schedule: Mapping, rule: Mapping,
                   days: Sequence[date], open_day_min_factor: float, rng: np.random.Generator) -> list:
    """Sessions of every vehicle of a class on the open days of its building (D-V6-29)."""
    opening, closing = (int(h) for h in schedule['occupied_hours'])
    factors = schedule['day_factors_weekday_saturday_sunday']
    sessions = []
    for d, day in enumerate(days):
        if factors[_day_kind(day)] < open_day_min_factor:
            continue
        base = 24*d
        for vehicle in range(vehicles):
            if rule['kind'] == 'opening':
                window = int(rule['window_h'])
                arrival = opening + int(rng.integers(window))
                sessions.append(Session(vehicle, base + arrival, base + closing))
            elif rule['kind'] == 'stops':
                for start, end in rule['stops']:
                    arrival = int(start) + int(rng.integers(int(end) - int(start)))
                    sessions.append(Session(vehicle, base + arrival, base + int(end)))
            else:
                raise ValueError(f"{vehicle_class.name}: unknown arrival rule {rule['kind']!r}")
    return sessions


def fifo_queue(sessions: Sequence[Session], *, chargers: int, vehicle_class: VehicleClass) -> QueueResult:
    """FIFO M/D/c queue: each session, in arrival order, takes the charger that frees first."""
    result = QueueResult()
    if chargers <= 0:
        result.unserved.extend(sessions)
        return result
    free_at = [0]*chargers
    for session in sorted(sessions, key=lambda s: (s.arrival, s.vehicle)):
        charger = min(range(chargers), key=lambda c: (max(free_at[c], session.arrival), c))
        connect = max(free_at[charger], session.arrival)
        if connect >= session.departure:
            result.unserved.append(session)
            continue
        disconnect = min(connect + vehicle_class.charging_hours, session.departure)
        free_at[charger] = disconnect
        result.assignments.append(Assignment(session.vehicle, charger, session.arrival, connect, disconnect))
        result.waiting_hours.append(connect - session.arrival)
    return result


def _required_soc(vehicle_class: VehicleClass, hours: int) -> float:
    return min(1.0, vehicle_class.arrival_soc + vehicle_class.charge_kw*hours/vehicle_class.battery_kwh)


def charger_tables(result: QueueResult, *, chargers: int, hours: int, vehicle_class: VehicleClass,
                   ids: Sequence[str]) -> list:
    """Hourly ChargerSimulation columns of each charger (SOC in percent, as the CityLearn data loader reads)."""
    tables = []
    for charger in range(chargers):
        state = np.full(hours, AWAY, dtype=int)
        ev_id = np.full(hours, 'NONE', dtype=object)
        departure = np.full(hours, -1.0)
        required = np.full(hours, -0.1)
        eta = np.full(hours, -1.0)
        arrival = np.full(hours, -0.1)
        own = sorted((a for a in result.assignments if a.charger == charger), key=lambda a: a.connect)
        for a in own:
            span = range(a.connect, min(a.disconnect, hours))
            soc_in = 100.0*vehicle_class.arrival_soc
            soc_out = 100.0*_required_soc(vehicle_class, a.disconnect - a.connect)
            for pos in span:
                state[pos], ev_id[pos] = CONNECTED, ids[a.vehicle]
                departure[pos] = float(a.disconnect - 1 - pos)
                required[pos], arrival[pos] = soc_out, soc_in
        for a in own:
            pre = a.connect - 1
            if 0 <= pre < hours and state[pre] == AWAY:
                state[pre], ev_id[pre], eta[pre] = INCOMING, ids[a.vehicle], 1.0
                arrival[pre] = 100.0*vehicle_class.arrival_soc
        tables.append(dict(zip(CHARGER_COLUMNS, (state, ev_id, departure, required, eta, arrival))))
    return tables


def delivered_kwh(result: QueueResult, vehicle_class: VehicleClass) -> float:
    return sum(min(vehicle_class.session_kwh, vehicle_class.charge_kw*(a.disconnect - a.connect))
               for a in result.assignments)


def load_factor(result: QueueResult, *, chargers: int, hours: int, vehicle_class: VehicleClass) -> float:
    if chargers <= 0 or hours <= 0:
        return 0.0
    return delivered_kwh(result, vehicle_class)/(chargers*vehicle_class.charge_kw*hours)


def _value(entry):
    return float(entry['value']) if isinstance(entry, Mapping) else float(entry)


def vehicle_class(kind: str, rules: Mapping) -> VehicleClass:
    """Class parameters of configs/dataset/ev_v6.yaml; the daily energy is shared among the day's sessions."""
    params, rule = rules['classes'][kind], rules['arrivals'][kind]
    sessions = len(rule['stops']) if rule['kind'] == 'stops' else 1
    daily = _value(params['kwh_per_km'])*_value(params['km_per_day'])
    return VehicleClass(kind, battery_kwh=_value(params['battery_kwh']), charge_kw=_value(params['charge_kw']),
                        session_kwh=daily/sessions)


@dataclass(frozen=True)
class BuildingCharging:
    chargers: list          # (charger name, class, ChargerSimulation columns)
    vehicles: list          # EV ids
    vehicle_class: Mapping  # EV id -> class
    load_factor: Mapping    # class -> delivered / (chargers x power x hours)
    unserved: Mapping       # class -> sessions that left without connecting
    mean_wait_h: Mapping    # class -> mean hours in the queue of the served sessions
    installed_kw: float
    coincidence_cap_kw: float


def building_charging(building: int, plan, *, schedule: Mapping, rules: Mapping, days: Sequence[date],
                      use_type: str) -> BuildingCharging:
    """FIFO queue of every class of a building and its CityLearn charger tables (D-V6-27, D-V6-29)."""
    from uc3m.application.dataset.ev_sizing import CLASSES, coincidence_cap_kw

    queue = rules['queue_rules']
    hours = 24*len(days)
    chargers, vehicles, owner, factors, unserved, waits = [], [], {}, {}, {}, {}
    installed = 0.0
    for index, kind in enumerate(CLASSES):
        spec = vehicle_class(kind, rules)
        n_vehicles, n_chargers = int(plan.fleet[kind]), int(plan.class_chargers[kind])
        ids = [f'B{building:02d}_{kind}_{v + 1:02d}' for v in range(n_vehicles)]
        vehicles += ids
        owner.update({i: kind for i in ids})
        rng = np.random.default_rng([int(queue['seed']), int(building), index])
        sessions = class_sessions(spec, vehicles=n_vehicles, schedule=schedule, rule=rules['arrivals'][kind],
                                  days=days, open_day_min_factor=float(queue['open_day_min_factor']), rng=rng)
        result = fifo_queue(sessions, chargers=n_chargers, vehicle_class=spec)
        tables = charger_tables(result, chargers=n_chargers, hours=hours, vehicle_class=spec, ids=ids)
        chargers += [(f'B{building:02d}_{kind}_charger_{c + 1:02d}', kind, t) for c, t in enumerate(tables)]
        factors[kind] = load_factor(result, chargers=n_chargers, hours=hours, vehicle_class=spec)
        unserved[kind] = len(result.unserved)
        waits[kind] = float(np.mean(result.waiting_hours)) if result.waiting_hours else 0.0
        installed += n_chargers*spec.charge_kw
    return BuildingCharging(chargers, vehicles, owner, factors, unserved, waits, installed,
                            coincidence_cap_kw(installed, use_type, rules))
