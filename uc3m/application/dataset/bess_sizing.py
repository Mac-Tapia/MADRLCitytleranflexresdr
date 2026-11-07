"""BESS of iquitos_v6: store the solar surplus and charge the vehicles (SPEC-016 D-V6-7, FR-016.6).

On the design-year day with the largest PV surplus:
    energy = (daily surplus + daily EV energy not covered directly by PV) / (efficiency x depth of discharge)
    power  = max(largest hourly surplus of that day, EV charging power)
The battery is a commercial model of CityLearn's catalog (data/misc/battery_choices.yaml, each with its
datasheet URL): the first model that declares efficiency, depth of discharge and loss coefficient.
Units are connected in parallel until both energy and power are covered.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import yaml


@dataclass(frozen=True)
class BatteryModel:
    name: str
    capacity_kwh: float
    nominal_power_kw: float
    efficiency: float
    depth_of_discharge: float
    loss_coefficient: float


@dataclass(frozen=True)
class BessSize:
    model: BatteryModel
    design_day: int
    required_kwh: float
    required_kw: float
    units: int
    capacity_kwh: float
    nominal_power_kw: float


def load_battery_catalog(path: Path) -> dict:
    return yaml.safe_load(Path(path).read_text(encoding='utf-8'))


def select_catalog_model(catalog: dict) -> BatteryModel:
    for name, entry in catalog.items():
        a = entry['attributes']
        if all(a.get(k) is not None for k in ('efficiency', 'depth_of_discharge', 'loss_coefficient')):
            return BatteryModel(name, float(a['capacity']), float(a['nominal_power']), float(a['efficiency']),
                                float(a['depth_of_discharge']), float(a['loss_coefficient']))
    raise ValueError('no catalog battery declares efficiency, depth of discharge and loss coefficient')


def size_bess(*, surplus_kwh_h: np.ndarray, ev_kwh_h: np.ndarray, ev_charging_power_kw: float,
              model: BatteryModel) -> BessSize:
    surplus = np.asarray(surplus_kwh_h, dtype=float)
    ev = np.asarray(ev_kwh_h, dtype=float)
    if surplus.shape != ev.shape or len(surplus) % 24:
        raise ValueError('surplus and EV series must be aligned and cover whole days')
    if np.any(surplus < 0) or np.any(ev < 0) or ev_charging_power_kw < 0:
        raise ValueError('surplus, EV energy and charging power must be non-negative')
    days_surplus = surplus.reshape(-1, 24)
    days_ev = ev.reshape(-1, 24)
    day = int(np.argmax(days_surplus.sum(axis=1)))
    uncovered_ev = np.clip(days_ev[day] - days_surplus[day], 0.0, None).sum()
    required_kwh = (days_surplus[day].sum() + uncovered_ev)/(model.efficiency*model.depth_of_discharge)
    required_kw = max(float(days_surplus[day].max()), float(ev_charging_power_kw))
    if required_kwh <= 0 and required_kw <= 0:
        units = 0
    else:
        units = math.ceil(max(required_kwh/model.capacity_kwh, required_kw/model.nominal_power_kw))
    return BessSize(model=model, design_day=day, required_kwh=float(required_kwh), required_kw=required_kw,
                    units=units, capacity_kwh=units*model.capacity_kwh, nominal_power_kw=units*model.nominal_power_kw)
