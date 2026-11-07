"""Hourly cooling from physics with the bill as ceiling (SPEC-016 D-V6-14 and D-V6-18, FR-016.1/2).

The monthly bills of Iquitos cannot calibrate the cooling share, because the monthly mean temperature
spans only 1.94 C: they bound it. Cooling = capacity x part load / COP. A month above
bill x (1 - base floor) is cut to that ceiling and flags the building. Base = bill - cooling, spread
with its hourly shape. The implied daily base must be stable between months, otherwise the building
is flagged; a flagged building blocks the dataset gate.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Mapping

import numpy as np


def part_load_ratio(outdoor_enthalpy: np.ndarray, *, indoor_enthalpy: float, design_enthalpy: float,
                    schedule: np.ndarray) -> np.ndarray:
    """Load as a fraction of design: enthalpy difference over the design one, times the use schedule.

    Assumption declared in D-V6-18: the cooling load is dominated by the outdoor air.
    """
    span = float(design_enthalpy) - float(indoor_enthalpy)
    if span <= 0:
        raise ValueError('design enthalpy must exceed the indoor enthalpy')
    driver = np.clip((np.asarray(outdoor_enthalpy, dtype=float) - indoor_enthalpy)/span, 0.0, 1.0)
    return driver*np.clip(np.asarray(schedule, dtype=float), 0.0, 1.0)


@dataclass(frozen=True)
class CalibrationResult:
    month_h: np.ndarray
    cooling_kwh: np.ndarray
    base_kwh: np.ndarray
    monthly: list = field(default_factory=list)
    capped_months: list = field(default_factory=list)
    base_cv_pct: float = 0.0
    flags: list = field(default_factory=list)

    @property
    def passed(self) -> bool:
        return not self.flags


def calibrate_cooling(*, capacity_kw_th: float, cop_h: np.ndarray, plr_h: np.ndarray, month_h: np.ndarray,
                      bill_kwh: Mapping[int, float], base_shape_h: np.ndarray, base_floor_fraction: float,
                      base_cv_limit_pct: float) -> CalibrationResult:
    month_h = np.asarray(month_h)
    cop_h, plr_h = np.asarray(cop_h, dtype=float), np.asarray(plr_h, dtype=float)
    shape = np.asarray(base_shape_h, dtype=float)
    if not 0.0 < base_floor_fraction < 1.0:
        raise ValueError(f'base floor fraction must be in (0, 1), got {base_floor_fraction}')
    if np.any(shape <= 0) or not np.all(np.isfinite(shape)):
        raise ValueError('the base shape must be positive in every hour')
    if np.any(cop_h <= 0):
        raise ValueError('COP must be positive')
    missing = sorted(set(np.unique(month_h).tolist()) - set(bill_kwh))
    if missing:
        raise ValueError(f'no measured bill for months {missing}')

    physical = capacity_kw_th*plr_h/cop_h
    cooling = np.empty_like(physical)
    base = np.empty_like(physical)
    monthly, capped = [], []
    for month in np.unique(month_h).tolist():
        hours = month_h == month
        bill = float(bill_kwh[month])
        if bill <= 0:
            raise ValueError(f'month {month}: the bill must be positive, got {bill}')
        ceiling = bill*(1.0 - base_floor_fraction)
        modelled = float(physical[hours].sum())
        scale = 1.0
        if modelled > ceiling:
            scale = ceiling/modelled
            capped.append(month)
        cooling[hours] = physical[hours]*scale
        base_month = bill - float(cooling[hours].sum())
        base[hours] = base_month*shape[hours]/shape[hours].sum()
        monthly.append({'month': month, 'bill_kwh': bill, 'physical_cooling_kwh': modelled,
                        'cooling_kwh': float(cooling[hours].sum()), 'base_kwh': base_month,
                        'base_kwh_per_day': base_month/(hours.sum()/24), 'capped': scale < 1.0})

    per_day = np.array([m['base_kwh_per_day'] for m in monthly])
    cv = float(np.std(per_day, ddof=1)/np.mean(per_day)*100) if len(per_day) > 1 else 0.0
    flags = []
    if capped:
        flags.append(f'cooling capped at the bill ceiling in {len(capped)} months')
    if cv > base_cv_limit_pct:
        flags.append(f'implied daily base unstable: CV {cv:.1f} % > {base_cv_limit_pct} %')
    return CalibrationResult(month_h=month_h, cooling_kwh=cooling, base_kwh=base, monthly=monthly,
                             capped_months=capped, base_cv_pct=cv, flags=flags)
