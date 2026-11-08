"""Peruvian national holidays and how each building function treats them (SPEC-016 D-V6-60).

A holiday does not stop every building: the rule of its schedule says what happens. ``closed`` and ``like_sunday``
functions run that day as on a Sunday of their own schedule, ``unchanged`` ones (24 h services) keep the calendar day.
"""
from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path
from typing import Mapping, Set

import yaml

CONFIG = Path(__file__).resolve().parents[3]/'configs/dataset/peru_holidays.yaml'
RULES = ('closed', 'like_sunday', 'unchanged')


def easter_sunday(year: int) -> date:
    """Gregorian Easter (anonymous Gregorian algorithm)."""
    a, b, c = year % 19, year//100, year % 100
    d, e = b//4, b % 4
    f = (b + 8)//25
    g = (b - f + 1)//3
    h = (19*a + b - d - g + 15) % 30
    i, k = c//4, c % 4
    m = (32 + 2*e + 2*i - h - k) % 7
    n = (a + 11*h + 22*m)//451
    month, day = divmod(h + m - 7*n + 114, 31)
    return date(year, month, day + 1)


def peru_holidays(year: int, config: Mapping = None) -> Set[date]:
    """The national holidays in force that year; days a decree makes non-working for the public sector are not included."""
    config = config or yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    days = {date(year, int(row['month']), int(row['day'])) for row in config['fixed']
            if year >= int(row.get('from_year', 0))}
    easter = easter_sunday(year)
    return days | {easter + timedelta(days=int(offset)) for offset in config['easter_offsets_days']}


def runs_as_sunday(day: date, schedule: Mapping, holidays: Set[date]) -> bool:
    """Whether a building of this function runs this holiday as a Sunday of its schedule."""
    rule = schedule.get('holiday_rule', 'unchanged')
    if rule not in RULES:
        raise ValueError(f'unknown holiday_rule {rule!r}')
    return day in holidays and rule != 'unchanged'
