"""Evaluated cost: the bill with capacity charge (owner decision D02, 2026-11-04).

The bill is computed from the physical trace and the official tariff table, not from
the price the simulator used, which a scenario may flatten. Per building and month:

    energy = sum_t P(t) dt x energy rate      net billing: export credited (owner, 2026-11-01)
    demand = max(0, max P(t) in 18:00-23:00) x demand rate
    fixed  = fixed charge, once per calendar month in the trace

Without IGV. Not modeled: reactive energy, public lighting, rural electrification and the
regulation's multi-month averaging of distribution capacity. A month only partly in the
trace pays the whole demand and fixed charge, so only complete splits are scientific
results. A missing rate makes the bill unavailable, never zero.
"""
from __future__ import annotations

import csv
import math
import re
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Callable, Dict, Mapping, Optional, Tuple

from uc3m.application.dataset.construction import PEAK_HOURS

RateKey = Tuple[int, int, int]  # building, year, month
_BUILDING = re.compile(r'Building_(\d+)')


@dataclass(frozen=True)
class BillRate:
    tariff: str
    energy_usd_kwh: float
    demand_usd_kw_month: float
    fixed_usd_month: float

    def __post_init__(self):
        for value in (self.energy_usd_kwh, self.demand_usd_kw_month, self.fixed_usd_month):
            if not math.isfinite(value) or value < 0:
                raise ValueError(f'{self.tariff}: a bill rate must be finite and non-negative, got {value}')


def load_bill_tariffs(path: Path) -> Dict[RateKey, BillRate]:
    rates: Dict[RateKey, BillRate] = {}
    with open(path, newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            key = (int(row['building']), int(row['year']), int(row['month']))
            if key in rates:
                raise ValueError(f'duplicate bill rate {key}')
            rates[key] = BillRate(row['tariff'], float(row['energy_usd_kwh']), float(row['demand_usd_kw_month']),
                                  float(row['fixed_usd_month']))
    return rates


def bill_components(trace, rates: Mapping[RateKey, BillRate]) -> Optional[Dict[str, float]]:
    dt = trace.hours_per_step
    energy = demand = fixed = 0.0
    moments = [datetime.fromisoformat(stamp) for stamp in trace.timestamps]
    months = sorted({(moment.year, moment.month) for moment in moments})
    for name in trace.building_ids:
        found = _BUILDING.fullmatch(name)
        if found is None:
            return None
        power = trace.series_by_building[name]['net_power']
        for year, month in months:
            rate = rates.get((int(found.group(1)), year, month))
            if rate is None:
                return None
            steps = [t for t, moment in enumerate(moments) if (moment.year, moment.month) == (year, month)]
            energy += math.fsum(power[t] for t in steps)*dt*rate.energy_usd_kwh
            block_peak = max((power[t] for t in steps if moments[t].hour in PEAK_HOURS), default=0.0)
            demand += max(0.0, block_peak)*rate.demand_usd_kw_month
            fixed += rate.fixed_usd_month
    return {'energy_usd': energy, 'demand_usd': demand, 'fixed_usd': fixed, 'total_usd': energy + demand + fixed}


def bill_measures(rates: Mapping[RateKey, BillRate]) -> Dict[str, Callable]:
    """KPI measures for kpi_contract.compute_fresh_kpis(extra_measures=...)."""
    def part(key):
        def measure(trace):
            parts = bill_components(trace, rates)
            return None if parts is None else parts[key]
        return measure
    return {'bill_cost': part('total_usd'), 'bill_energy_cost': part('energy_usd'),
            'bill_demand_charge': part('demand_usd')}
