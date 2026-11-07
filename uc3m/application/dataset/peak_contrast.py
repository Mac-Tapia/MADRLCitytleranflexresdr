"""Generated hourly peak against the peak each bill implies (SPEC-016 FR-016.8).

implied peak = monthly energy / (load factor x hours of the month), the maximum demand the distributor's load
factor stands for. A month counts when it is measured, has a load factor in (0, 1] and is not flagged as a
partial or mis-keyed bill. Synthetic months (B01, D-V6-36) are reported and kept out of the statistics. The
acceptance threshold is the owner's (implementation plan, decision table): without it the gate only reports.
"""
from __future__ import annotations

from typing import Mapping, Optional, Sequence

import numpy as np

EXCLUDED_FLAGS = ('partial_month_suspect', 'printed_total_implausible')
REPORTED_BANDS = (0.1, 0.2, 0.3, 0.5)
_TOL = 1e-9


def peak_contrast(hourly_kw: Mapping[int, np.ndarray], month_of_hour: np.ndarray, targets: Sequence) -> list:
    rows = []
    month_of_hour = np.asarray(month_of_hour)
    for t in sorted(targets, key=lambda r: (r.building_id, r.year, r.month)):
        if t.building_id not in hourly_kw or not t.load_factor or not 0 < t.load_factor <= 1:
            continue
        if any(f in t.flags for f in EXCLUDED_FLAGS) or t.provenance not in ('measured', 'synthetic'):
            continue
        mask = month_of_hour == t.month
        hours = int(mask.sum())
        if hours == 0:
            continue
        series = np.asarray(hourly_kw[t.building_id], dtype=float)[:len(month_of_hour)]
        implied = t.energy_kwh/(t.load_factor*hours)
        peak = float(series[mask].max())
        rows.append({'building_id': t.building_id, 'year': t.year, 'month': t.month, 'load_factor': t.load_factor,
                     'implied_peak_kw': implied, 'hourly_peak_kw': peak, 'ratio': peak/implied,
                     'synthetic': t.provenance == 'synthetic'})
    return rows


def summarize(rows: Sequence, *, threshold: Optional[float]) -> dict:
    counted = [r for r in rows if not r['synthetic']]
    deviation = np.array([abs(r['ratio'] - 1.0) for r in counted])
    share = {str(b): float((deviation <= b + _TOL).mean()) if len(counted) else 0.0 for b in REPORTED_BANDS}
    summary = {'months': len(counted), 'synthetic_months': len(rows) - len(counted), 'share_within': share,
               'median_ratio': float(np.median([r['ratio'] for r in counted])) if counted else None,
               'threshold': threshold}
    if threshold is None:
        return {**summary, 'status': 'threshold_pending_owner', 'passed': None, 'outside': []}
    outside = [r for r in counted if abs(r['ratio'] - 1.0) > threshold + _TOL]
    return {**summary, 'status': 'checked', 'passed': not outside, 'outside': outside}
