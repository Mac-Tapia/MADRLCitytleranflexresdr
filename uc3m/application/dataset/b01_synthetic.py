"""Synthetic monthly bill of B01, which has no distributor bill (SPEC-016 D-V6-36).

The energy of each month is the target v5 already builds (measured EA of the study workbook, or the declared
backcast and scaling), with its peak / off-peak split. The load factor is the median of the measured bills of
the same month of the 24 h peers; the maximum demand follows as E / (hours x LF). The reactive energy uses the
peers' median reactive / active ratio of the same month (P-V6-18). Pricing with the official sheet lives in
tools/dataset/write_b01_synthetic_bill.py.
"""
from __future__ import annotations

import calendar
import statistics
from dataclasses import dataclass
from typing import Mapping, Sequence

EXCLUDED_FLAGS = ('partial_month_suspect', 'printed_total_implausible')


@dataclass(frozen=True)
class SyntheticMonth:
    year: int
    month: int
    energy_kwh: float
    peak_kwh: float
    offpeak_kwh: float
    load_factor: float
    max_demand_kw: float
    reactive_kvarh: float
    energy_provenance: str
    load_factor_peers: tuple
    inputs: tuple


def _usable(record, year: int, month: int, peers) -> bool:
    return (record.building_id in peers and (record.year, record.month) == (year, month)
            and record.provenance == 'measured' and not any(f in record.flags for f in EXCLUDED_FLAGS))


def peer_load_factor(year: int, month: int, measured: Sequence, *, peers, bounds=(0.0, 1.0)) -> tuple:
    rows = [r for r in measured if _usable(r, year, month, peers)
            and r.load_factor is not None and bounds[0] < r.load_factor <= bounds[1]]
    if not rows:
        raise ValueError(f'B01 {year}-{month:02d}: no measured peer load factor among {sorted(peers)}')
    return statistics.median(r.load_factor for r in rows), sorted(r.building_id for r in rows)


def peer_reactive_ratio(year: int, month: int, measured: Sequence, *, peers, reactive: Mapping) -> float:
    ratios = [reactive[(r.building_id, r.year, r.month)]/r.energy_kwh for r in measured
              if _usable(r, year, month, peers) and (r.building_id, r.year, r.month) in reactive and r.energy_kwh > 0]
    return statistics.median(ratios) if ratios else 0.0


def synthetic_months(targets: Sequence, measured: Sequence, *, peers, reactive: Mapping,
                     bounds=(0.0, 1.0)) -> list:
    months = []
    for target in sorted(targets, key=lambda t: (t.year, t.month)):
        factor, used = peer_load_factor(target.year, target.month, measured, peers=peers, bounds=bounds)
        hours = calendar.monthrange(target.year, target.month)[1]*24
        ratio = peer_reactive_ratio(target.year, target.month, measured, peers=peers, reactive=reactive)
        months.append(SyntheticMonth(target.year, target.month, target.energy_kwh, target.peak_kwh, target.offpeak_kwh,
                                     factor, target.energy_kwh/(hours*factor), target.energy_kwh*ratio,
                                     target.provenance, tuple(used), tuple(target.inputs)))
    return months
