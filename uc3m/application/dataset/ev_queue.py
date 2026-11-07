"""Stochastic charging by a FIFO queue per vehicle class, in CityLearn's charger format (SPEC-016).

- Presence (D-V6-39): each vehicle comes each day with probability = the building's day factor (Bernoulli,
  fixed seed). Arrival hour (D-V6-29): random within its window (first hours after opening; mototaxi stops).
- Daily km (D-V6-40, P-V6-21): lognormal around the class mean, truncated to the autonomy; the energy of the
  trip lowers the SOC carried from the last departure (D-V6-31), so the arrival SOC varies by vehicle and day.
- Queue (D-V6-27): vehicles of a class wait in arrival order (FIFO) for a socket of their class. A socket
  rests ``gap_h`` hours between sessions, so CityLearn sees each departure and the next arrival.
- Charging time (D-V6-31): what the battery needs at connection, (1 - SOC) x battery / (power x efficiency),
  in whole hours and cut at the departure. Motos and mototaxis release the socket when full; a bidirectional
  pickup stays connected until it leaves (D-V6-42), available for V2B through V2L.
- Sockets (D-V6-37, D-V6-43): per class, the fewest that serve every session (no unserved, no trip without
  energy, every session full), taken at the 95th percentile of 20 drawn years.
- Load factor (D-V6-27 (5)): delivered energy / (sockets x power x hours).
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date
from typing import Mapping, Optional, Sequence

import numpy as np

CHARGER_COLUMNS = ('electric_vehicle_charger_state', 'electric_vehicle_id', 'electric_vehicle_departure_time',
                   'electric_vehicle_required_soc_departure', 'electric_vehicle_estimated_arrival_time',
                   'electric_vehicle_estimated_soc_arrival')
TRIP_COLUMN = 'electric_vehicle_trip_kwh'   # D-V6-41: trip energy before each connection, read by the v3 layer
CONNECTED, INCOMING, AWAY = 1, 2, 3


@dataclass(frozen=True)
class VehicleClass:
    name: str
    battery_kwh: float
    charge_kw: float
    session_kwh: float                 # mean energy of one session's trip
    efficiency: float = 1.0            # charger x battery efficiency: share of the power that reaches the battery
    stays_connected: bool = False      # bidirectional pickups keep the socket until departure (D-V6-42)

    @property
    def battery_power_kw(self) -> float:
        return self.charge_kw*self.efficiency

    def charging_hours(self, arrival_soc: float) -> int:
        return max(1, math.ceil((1.0 - arrival_soc)*self.battery_kwh/self.battery_power_kw - 1e-9))

    @property
    def arrival_soc(self) -> float:
        soc = 1.0 - self.session_kwh/self.battery_kwh
        if not 0.0 <= soc < 1.0:
            raise ValueError(f'{self.name}: session energy {self.session_kwh} kWh does not fit the battery')
        return soc


@dataclass(frozen=True)
class Session:
    vehicle: int
    arrival: int                       # absolute hour index
    departure: int                     # absolute hour index, exclusive
    trip_kwh: Optional[float] = None   # energy of the trip before this session; None = class mean


@dataclass(frozen=True)
class Assignment:
    vehicle: int
    charger: int
    arrival: int
    connect: int
    disconnect: int                    # exclusive
    arrival_soc: float = 0.0
    departure_soc: float = 0.0
    trip_kwh: float = 0.0
    full_at: int = 0                   # exclusive hour when the battery is full (<= disconnect)


@dataclass
class QueueResult:
    assignments: list = field(default_factory=list)
    unserved: list = field(default_factory=list)
    waiting_hours: list = field(default_factory=list)
    depleted: int = 0                  # trips that needed more energy than the battery held on departure


def _day_kind(day: date) -> int:
    return 0 if day.weekday() < 5 else (1 if day.weekday() == 5 else 2)


def draw_daily_km(rng: np.random.Generator, *, mean_km: float, sigma_ln: float, max_km: float, size) -> np.ndarray:
    """Lognormal daily km with the given mean (mu = ln(mean) - sigma^2/2), truncated to the autonomy."""
    mu = math.log(mean_km) - sigma_ln**2/2
    return np.minimum(rng.lognormal(mu, sigma_ln, size=size), max_km)


def class_sessions(vehicle_class: VehicleClass, *, vehicles: int, schedule: Mapping, rule: Mapping,
                   days: Sequence[date], rng: np.random.Generator, km: Optional[Mapping] = None,
                   kwh_per_km: Optional[float] = None, mean_km: Optional[float] = None,
                   max_km: Optional[float] = None) -> list:
    """Sessions of every vehicle of a class: Bernoulli presence by day factor, random arrival, drawn km."""
    opening, closing = (int(h) for h in schedule['occupied_hours'])
    factors = schedule['day_factors_weekday_saturday_sunday']
    stops = rule['stops'] if rule['kind'] == 'stops' else None
    if rule['kind'] not in ('opening', 'stops'):
        raise ValueError(f"{vehicle_class.name}: unknown arrival rule {rule['kind']!r}")
    sessions = []
    for d, day in enumerate(days):
        base, p = 24*d, float(factors[_day_kind(day)])
        for vehicle in range(vehicles):
            if rng.random() >= p:
                continue
            trips = len(stops) if stops else 1
            trip = None
            if km is not None:
                daily = float(draw_daily_km(rng, mean_km=mean_km, sigma_ln=float(km['sigma_ln']['value']),
                                            max_km=max_km, size=1)[0])
                trip = daily*kwh_per_km/trips
            if stops is None:
                window = int(rule['window_h'])
                sessions.append(Session(vehicle, base + opening + int(rng.integers(window)), base + closing, trip))
            else:
                for start, end in stops:
                    arrival = int(start) + int(rng.integers(int(end) - int(start)))
                    sessions.append(Session(vehicle, base + arrival, base + int(end), trip))
    return sessions


def fifo_queue(sessions: Sequence[Session], *, chargers: int, vehicle_class: VehicleClass,
               gap_h: int = 0) -> QueueResult:
    """FIFO queue: each session, in arrival order, takes the socket that frees first (after ``gap_h`` rest)."""
    result = QueueResult()
    vehicle_class.arrival_soc                                   # validates that a mean trip fits the battery
    left_with = {}                                              # SOC of each vehicle at its last departure
    free_at = [0]*chargers
    for session in sorted(sessions, key=lambda s: (s.arrival, s.vehicle)):
        trip = vehicle_class.session_kwh if session.trip_kwh is None else session.trip_kwh
        remaining = left_with.get(session.vehicle, 1.0) - trip/vehicle_class.battery_kwh
        if remaining < -1e-12:
            result.depleted += 1
        soc_in = max(0.0, remaining)
        charger = min(range(chargers), key=lambda c: (max(free_at[c], session.arrival), c)) if chargers > 0 else None
        connect = max(free_at[charger], session.arrival) if charger is not None else session.departure
        if connect >= session.departure:
            result.unserved.append(session)
            left_with[session.vehicle] = soc_in
            continue
        full_at = min(connect + vehicle_class.charging_hours(soc_in), session.departure)
        disconnect = session.departure if vehicle_class.stays_connected else full_at
        soc_out = min(1.0, soc_in + vehicle_class.battery_power_kw*(full_at - connect)/vehicle_class.battery_kwh)
        free_at[charger] = disconnect + gap_h
        left_with[session.vehicle] = soc_out
        result.assignments.append(Assignment(session.vehicle, charger, session.arrival, connect, disconnect,
                                             soc_in, soc_out, trip, full_at))
        result.waiting_hours.append(connect - session.arrival)
    return result


def serves_everyone(result: QueueResult) -> bool:
    """D-V6-37: no session without a socket, no trip without energy and every served session leaves full."""
    return (not result.unserved and result.depleted == 0
            and all(a.departure_soc >= 1.0 - 1e-9 for a in result.assignments))


def required_chargers(sessions: Sequence[Session], vehicle_class: VehicleClass, *, gap_h: int = 0) -> int:
    """D-V6-37: the fewest sockets of a class with which the FIFO queue serves every session of the horizon."""
    if not sessions:
        return 0
    vehicles = len({s.vehicle for s in sessions})
    for n in range(1, vehicles + 1):
        if serves_everyone(fifo_queue(sessions, chargers=n, vehicle_class=vehicle_class, gap_h=gap_h)):
            return n
    return vehicles                                             # one per vehicle: every vehicle has its own socket


def socket_percentile(needs: Sequence[int], percentile: float) -> int:
    """D-V6-43: the sockets that serve every session in ``percentile`` % of the drawn years."""
    return int(math.ceil(float(np.percentile(np.asarray(needs, dtype=float), percentile)) - 1e-9)) if needs else 0


def charger_tables(result: QueueResult, *, chargers: int, hours: int, vehicle_class: VehicleClass,
                   ids: Sequence[str]) -> list:
    """Hourly ChargerSimulation columns of each socket (SOC in percent, as the CityLearn data loader reads).

    The row before a connection is ``incoming`` (state 2, estimated arrival 0 steps, as in CityLearn's
    reference dataset) when the socket is free there.
    """
    tables = []
    for charger in range(chargers):
        state = np.full(hours, AWAY, dtype=int)
        ev_id = np.full(hours, 'NONE', dtype=object)
        departure = np.full(hours, -1.0)
        required = np.full(hours, -0.1)
        eta = np.full(hours, -1.0)
        arrival = np.full(hours, -0.1)
        trips = np.zeros(hours)
        own = sorted((a for a in result.assignments if a.charger == charger), key=lambda a: a.connect)
        for a in own:
            soc_in, soc_out = 100.0*a.arrival_soc, 100.0*a.departure_soc
            for pos in range(a.connect, min(a.disconnect, hours)):
                state[pos], ev_id[pos] = CONNECTED, ids[a.vehicle]
                departure[pos] = float(a.disconnect - 1 - pos)
                required[pos], arrival[pos] = soc_out, soc_in
            if a.connect < hours:
                trips[a.connect] = a.trip_kwh
        for a in own:
            pre = a.connect - 1
            if 0 <= pre < hours and state[pre] == AWAY:
                state[pre], ev_id[pre], eta[pre] = INCOMING, ids[a.vehicle], 0.0
                arrival[pre] = 100.0*a.arrival_soc
        tables.append({**dict(zip(CHARGER_COLUMNS, (state, ev_id, departure, required, eta, arrival))), TRIP_COLUMN: trips})
    return tables


def delivered_kwh(result: QueueResult, vehicle_class: VehicleClass) -> float:
    """Energy drawn by the sockets [kWh]: battery energy gained / efficiency."""
    return sum((a.departure_soc - a.arrival_soc)*vehicle_class.battery_kwh for a in result.assignments) \
        / vehicle_class.efficiency


def planned_charging_kwh(result: QueueResult, *, hours: int, vehicle_class: VehicleClass) -> np.ndarray:
    """Grid energy each hour if every session charges at nominal power until full (input of D-V6-30 sizing)."""
    planned = np.zeros(hours)
    for a in result.assignments:
        need = (a.departure_soc - a.arrival_soc)*vehicle_class.battery_kwh/vehicle_class.efficiency
        for hour in range(a.connect, min(a.full_at, hours)):
            step = min(vehicle_class.charge_kw, need)
            planned[hour] += step
            need -= step
            if need <= 1e-12:
                break
    return planned


def load_factor(result: QueueResult, *, chargers: int, hours: int, vehicle_class: VehicleClass) -> float:
    if chargers <= 0 or hours <= 0:
        return 0.0
    return delivered_kwh(result, vehicle_class)/(chargers*vehicle_class.charge_kw*hours)


def _value(entry):
    return float(entry['value']) if isinstance(entry, Mapping) else float(entry)


def vehicle_class(kind: str, rules: Mapping) -> VehicleClass:
    """Class parameters of configs/dataset/ev_v6.yaml; the daily energy is shared among the day's sessions."""
    params, rule, common = rules['classes'][kind], rules['arrivals'][kind], rules['battery_and_charger']
    sessions = len(rule['stops']) if rule['kind'] == 'stops' else 1
    daily = _value(params['kwh_per_km'])*_value(params['km_per_day'])
    efficiency = _value(common['charger_efficiency'])*_value(common['battery_efficiency'])
    return VehicleClass(kind, battery_kwh=_value(params['battery_kwh']), charge_kw=_value(params['charge_kw']),
                        session_kwh=daily/sessions, efficiency=efficiency,
                        stays_connected=_value(params['discharge_kw']) > 0)


def _sessions(kind: str, spec: VehicleClass, rules: Mapping, *, vehicles: int, schedule: Mapping,
              days: Sequence[date], rng: np.random.Generator) -> list:
    params, common = rules['classes'][kind], rules['battery_and_charger']
    kwh_per_km = _value(params['kwh_per_km'])
    autonomy = _value(params['battery_kwh'])*_value(common['battery_depth_of_discharge'])/kwh_per_km
    return class_sessions(spec, vehicles=vehicles, schedule=schedule, rule=rules['arrivals'][kind], days=days,
                          rng=rng, km=rules['daily_km'], kwh_per_km=kwh_per_km,
                          mean_km=_value(params['km_per_day']), max_km=autonomy)


@dataclass(frozen=True)
class BuildingCharging:
    chargers: list          # (socket name, class, ChargerSimulation columns)
    vehicles: list          # EV ids
    vehicle_class: Mapping  # EV id -> class
    load_factor: Mapping    # class -> delivered / (sockets x power x hours)
    unserved: Mapping       # class -> sessions that left without connecting
    mean_wait_h: Mapping    # class -> mean hours in the queue of the served sessions
    depleted: Mapping       # class -> trips that needed more than the battery held (D-V6-31)
    installed_kw: float
    coincidence_cap_kw: float
    epbd_points: int = 0                 # EPBD 2024 art. 14(2) minimum, reported only (D-V6-37)
    required_sockets: Mapping = None     # class -> sockets at the P95 of the drawn years (D-V6-43)
    physical_chargers: Mapping = None    # class -> dual-socket units (D-V6-38)
    sockets_by_seed: Mapping = None      # class -> minimum sockets of each drawn year
    planned_kwh_h: np.ndarray = None     # grid energy of the building's EV charging at nominal power, per hour


def building_charging(building: int, plan, *, schedule: Mapping, rules: Mapping, days: Sequence[date],
                      use_type: str) -> BuildingCharging:
    """Stochastic FIFO queue of every class of a building and its CityLearn charger tables.

    Sockets per class: the 95th percentile over ``socket_sizing.seeds`` drawn years of the fewest that serve
    every session (D-V6-43), rounded up to dual-socket units (D-V6-38). The dataset's own year is the draw
    with ``queue_rules.seed``. The EPBD points of the plan are reported, not simulated.
    """
    from uc3m.application.dataset.ev_sizing import CLASSES, coincidence_cap_kw

    queue, sizing = rules['queue_rules'], rules['socket_sizing']
    gap = int(_value(queue['free_hours_between_sessions']))
    seeds, percentile = int(_value(sizing['seeds'])), _value(sizing['percentile'])
    per_unit = int(_value(rules['charging_unit']['sockets_per_unit']))
    hours = 24*len(days)
    chargers, vehicles, owner, factors, unserved, waits, depleted = [], [], {}, {}, {}, {}, {}
    needed, units_by_class, by_seed = {}, {}, {}
    planned = np.zeros(24*len(days))
    installed = 0.0
    for index, kind in enumerate(CLASSES):
        spec = vehicle_class(kind, rules)
        n_vehicles = int(plan.fleet[kind])
        ids = [f'B{building:02d}_{kind}_{v + 1:02d}' for v in range(n_vehicles)]
        vehicles += ids
        owner.update({i: kind for i in ids})
        draws = [_sessions(kind, spec, rules, vehicles=n_vehicles, schedule=schedule, days=days,
                           rng=np.random.default_rng([int(_value(queue['seed'])) + k, int(building), index]))
                 for k in range(seeds)]
        by_seed[kind] = [required_chargers(s, spec, gap_h=gap) for s in draws]
        needed[kind] = socket_percentile(by_seed[kind], percentile)
        units = -(-needed[kind]//per_unit)
        units_by_class[kind] = units
        n_sockets = units*per_unit          # every socket of a unit is simulated (D-V6-38)
        result = fifo_queue(draws[0], chargers=n_sockets, vehicle_class=spec, gap_h=gap)
        tables = charger_tables(result, chargers=n_sockets, hours=hours, vehicle_class=spec, ids=ids)
        chargers += [(f'B{building:02d}_{kind}_unit_{c//per_unit + 1:02d}_socket_{c % per_unit + 1}', kind, t)
                     for c, t in enumerate(tables)]
        factors[kind] = load_factor(result, chargers=n_sockets, hours=hours, vehicle_class=spec)
        planned += planned_charging_kwh(result, hours=hours, vehicle_class=spec)
        unserved[kind] = len(result.unserved)
        depleted[kind] = result.depleted
        waits[kind] = float(np.mean(result.waiting_hours)) if result.waiting_hours else 0.0
        installed += n_sockets*spec.charge_kw
    return BuildingCharging(chargers, vehicles, owner, factors, unserved, waits, depleted, installed,
                            coincidence_cap_kw(installed, use_type, rules), int(plan.chargers), needed,
                            units_by_class, by_seed, planned)
