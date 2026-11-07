"""BESS of iquitos_v6: store the solar surplus and charge the vehicles (SPEC-016 D-V6-7, FR-016.6).

On the design-year day with the largest PV surplus:
    energy = (daily surplus + daily EV energy not covered directly by PV) / (efficiency x depth of discharge)
    power  = max(largest hourly surplus of that day, EV charging power)
D-V6-30 (owner 2026-11-07): the battery also cuts peaks and shifts energy from the 18:00-23:00 block to
off-peak hours. shaved = shift fraction x largest hourly block import of the year; the shifted energy is
shaved x block hours. Energy = max(surplus + EV term, shifted energy) and power = max(surplus, EV, shaved),
so one battery serves both functions and the agents decide each hour by the three axes.
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
    shaved_kw: float = 0.0
    sizing_function: str = 'surplus_ev'


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
              model: BatteryModel, block_import_kwh_h: np.ndarray | None = None,
              peak_block_h: np.ndarray | None = None, shift_fraction: float = 0.0) -> BessSize:
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
    usable = model.efficiency*model.depth_of_discharge
    surplus_kwh = (days_surplus[day].sum() + uncovered_ev)/usable
    shaved_kw = shift_kwh = 0.0
    if block_import_kwh_h is not None and shift_fraction > 0:
        block = np.asarray(peak_block_h, dtype=bool)
        imports = np.clip(np.asarray(block_import_kwh_h, dtype=float), 0.0, None)
        if imports.shape != surplus.shape or block.shape != surplus.shape:
            raise ValueError('block import and block mask must be aligned with the surplus')
        shaved_kw = float(shift_fraction)*float(imports[block].max()) if block.any() else 0.0
        block_hours = int(block[:24].sum())
        shift_kwh = shaved_kw*block_hours/usable
    required_kwh = max(surplus_kwh, shift_kwh)
    function = 'peak_shift' if shift_kwh > surplus_kwh else 'surplus_ev'
    required_kw = max(float(days_surplus[day].max()), float(ev_charging_power_kw), shaved_kw)
    if required_kwh <= 0 and required_kw <= 0:
        units = 0
    else:
        units = math.ceil(max(required_kwh/model.capacity_kwh, required_kw/model.nominal_power_kw))
    return BessSize(model=model, design_day=day, required_kwh=float(required_kwh), required_kw=required_kw,
                    units=units, capacity_kwh=units*model.capacity_kwh, nominal_power_kw=units*model.nominal_power_kw,
                    shaved_kw=shaved_kw, sizing_function=function)
