"""Site configuration (SPEC-017 FR-017.1 and FR-017.5): every site value comes from a file, not the code.

The default site is configs/sites/iquitos.yaml; ``UC3M_SITE_CONFIG`` selects another one. A value without
its origin is rejected, so nothing enters a dataset without a declared source.
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Mapping

import yaml

REPO = Path(__file__).resolve().parents[3]
DEFAULT_SITE = REPO/'configs/sites/iquitos.yaml'
ORIGINS = frozenset({'measured', 'cited', 'design_rule', 'assumption', 'assumption_pending_user_verification',
                     'implementation_rule'})
_DECLARED = ('peak_block', 'time_zone', 'elevation_m')


@dataclass(frozen=True)
class SiteConfig:
    name: str
    peak_block_hours: frozenset
    utc_offset_hours: float
    elevation_m: float
    files: Mapping[str, str] = field(default_factory=dict)


def load_site(path: Path) -> SiteConfig:
    raw = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    for key in _DECLARED:
        entry = raw.get(key) or {}
        if entry.get('origin') not in ORIGINS:
            raise ValueError(f'site value {key!r} of {path} has no valid origin')
        if not (entry.get('source') or entry.get('note')):
            raise ValueError(f'site value {key!r} of {path} has no source or note')
    hours = frozenset(int(h) for h in raw['peak_block']['hours'])
    if not hours or not hours <= set(range(24)):
        raise ValueError(f'peak block hours of {path} must be within 0-23, got {sorted(hours)}')
    return SiteConfig(name=str(raw['name']), peak_block_hours=hours,
                      utc_offset_hours=float(raw['time_zone']['utc_offset_hours']),
                      elevation_m=float(raw['elevation_m']['value']), files=dict(raw.get('files') or {}))


def load_default_site() -> SiteConfig:
    return load_site(Path(os.environ.get('UC3M_SITE_CONFIG') or DEFAULT_SITE))
