"""Power tariff inside the dataset and hourly bill cost (SPEC-016 FR-016.7 and D-V6-8, owner decision D04).

The reward must not read project files: every building gets ``bill_tariff_Building_<b>.csv`` with the
official energy and demand rates of each hour and the 18:00-23:00 capacity block. The hourly cost is

    cost(t) = P(t) x energy rate + demand rate x max(0, P(t) - peak of the month so far in the block)

so that, summed over a month, it equals the bill without its fixed charge (net billing: an export
hour is credited at the energy rate). A missing rate is an error, never a zero.
"""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Mapping

import numpy as np
import pandas as pd

from uc3m.application.dataset.construction import PEAK_HOURS

COLUMNS = ('energy_usd_kwh', 'demand_usd_kw_month', 'peak_block')


def hourly_bill_tariff(rates: Mapping, *, building: int, year: np.ndarray, month: np.ndarray,
                       hour: np.ndarray) -> pd.DataFrame:
    year, month, hour = (np.asarray(a, dtype=int) for a in (year, month, hour))
    energy = np.empty(len(year))
    demand = np.empty(len(year))
    for y, m in sorted(set(zip(year.tolist(), month.tolist()))):
        rate = rates.get((int(building), y, m))
        if rate is None:
            raise ValueError(f'no official tariff for building {building} in {y}-{m:02d}')
        rows = (year == y) & (month == m)
        energy[rows] = rate.energy_usd_kwh
        demand[rows] = rate.demand_usd_kw_month
    return pd.DataFrame({'energy_usd_kwh': energy, 'demand_usd_kw_month': demand,
                         'peak_block': np.isin(hour, list(PEAK_HOURS)).astype(int)}, columns=list(COLUMNS))


def incremental_bill_cost(power_kw: float, *, energy_usd_kwh: float, demand_usd_kw_month: float,
                          peak_so_far_kw: float, in_block: bool) -> tuple[float, float]:
    """Cost of one hour and the month's block peak after it (D-V6-8). Reset the peak to 0 each month."""
    cost = float(power_kw)*energy_usd_kwh
    peak = float(peak_so_far_kw)
    if in_block and power_kw > peak:
        cost += demand_usd_kw_month*(float(power_kw) - max(peak, 0.0))
        peak = float(power_kw)
    return cost, peak


def write_bill_tariff_files(dataset_dir: Path, rates: Mapping, *, buildings: Iterable[int], year: np.ndarray,
                            month: np.ndarray, hour: np.ndarray) -> dict[int, Path]:
    written = {}
    for building in buildings:
        path = Path(dataset_dir)/f'bill_tariff_Building_{building}.csv'
        hourly_bill_tariff(rates, building=building, year=year, month=month, hour=hour).to_csv(path, index=False)
        written[int(building)] = path
    return written
