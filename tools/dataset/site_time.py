"""Hourly local index of a site's years (SPEC-017 FR-017.2). Kept in tools: the application layer has no pandas."""
from __future__ import annotations

import pandas as pd


def hourly_index(years, time_zone: str) -> pd.DatetimeIndex:
    """Hourly local index of whole calendar years (leap days included)."""
    years = sorted(int(y) for y in years)
    return pd.date_range(f'{years[0]}-01-01', f'{years[-1] + 1}-01-01', freq='h', tz=time_zone, inclusive='left')
