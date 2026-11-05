"""Official busbar prices of one system, as Osinergmin prints them (no IGV, no conversion)."""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date
from typing import Tuple


@dataclass(frozen=True)
class BusbarPrice:
    power_pen_kw_month: float
    energy_peak_ctm_kwh: float
    energy_offpeak_ctm_kwh: float

    def __post_init__(self):
        for value in (self.power_pen_kw_month, self.energy_peak_ctm_kwh, self.energy_offpeak_ctm_kwh):
            if not math.isfinite(value) or value <= 0:
                raise ValueError(f'busbar price must be finite and positive, got {value}')

    @property
    def is_flat(self) -> bool:
        return self.energy_peak_ctm_kwh == self.energy_offpeak_ctm_kwh


@dataclass(frozen=True)
class BusbarSheet:
    """One validity date: the busbar price and the effective price of the same system."""
    valid_from: date
    system: str
    resolutions: Tuple[str, ...]
    barra: BusbarPrice
    efectivo: BusbarPrice
