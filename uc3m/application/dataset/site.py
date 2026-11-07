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
# Older configurations use other words for the same origins (FR-017.5). An owner decision is a design rule; a
# pick made under the owner's delegation is an implementation rule; an upstream example value is an assumption
# (the builder already records it so, tools/dataset/build_fresh_campaign_dataset.py::_from_config).
ORIGIN_ALIASES = {'user_decision': 'design_rule', 'delegated_recommendation': 'implementation_rule'}
STATUS_ORIGINS = {'repository_example': 'assumption', 'design_rule': 'design_rule',
                  'assumption_pending_user_verification': 'assumption_pending_user_verification'}
METADATA_KEYS = frozenset({'schema_version', 'origin', 'status', 'source', 'note', 'reason', 'description'})


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


def declared_origin(entry) -> str | None:
    """Origin declared by a mapping, in the spec vocabulary (``origin``, or the legacy ``status``)."""
    if not isinstance(entry, dict):
        return None
    if 'origin' in entry:
        origin = str(entry['origin'])
        return ORIGIN_ALIASES.get(origin, origin)
    return STATUS_ORIGINS.get(entry.get('status'))


def undeclared_values(raw, path: str = '', inherited: bool = False) -> list:
    """Dotted paths of the numbers of a configuration that have no origin of their own, a parent's or a sibling's."""
    found = []
    if isinstance(raw, dict):
        here = inherited or declared_origin(raw) is not None
        for key, value in raw.items():
            key = str(key)
            if key in METADATA_KEYS or key.endswith('_origin'):
                continue
            sibling = f'{key}_origin' in raw
            found += undeclared_values(value, f'{path}.{key}' if path else key, here or sibling)
    elif isinstance(raw, list):
        for index, value in enumerate(raw):
            found += undeclared_values(value, f'{path}.{index}', inherited)
    elif isinstance(raw, (int, float)) and not isinstance(raw, bool) and not inherited:
        found.append(path)
    return found


def unknown_origins(raw, path: str = '') -> list:
    """Declared origins (``origin`` keys and ``<key>_origin`` siblings) outside the allowed vocabulary."""
    found = []
    if isinstance(raw, dict):
        for key, value in raw.items():
            key = str(key)
            if key == 'origin' or (key.endswith('_origin') and isinstance(value, str) and ' ' not in value):
                origin = ORIGIN_ALIASES.get(str(value), str(value))
                if origin not in ORIGINS:
                    found.append(f'{path or key}: {value}')
            elif isinstance(value, (dict, list)):
                found += unknown_origins(value, f'{path}.{key}' if path else key)
    elif isinstance(raw, list):
        for index, value in enumerate(raw):
            found += unknown_origins(value, f'{path}.{index}')
    return found
