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
BELOW_NOTE = ('the bill maximum demand is a 15-minute value and the dataset is hourly, so an hourly peak below it '
              'is expected and reported, not corrected (SPEC-016 D-V6-48)')
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
    # D-V6-48: only a generated peak above (1 + threshold) x the bill's fails; below is expected (hourly vs 15 min)
    outside = [r for r in counted if r['ratio'] > 1.0 + threshold + _TOL]
    below = [r for r in counted if r['ratio'] < 1.0 - threshold - _TOL]
    return {**summary, 'status': 'checked', 'passed': not outside, 'outside': outside, 'below': below,
            'below_note': BELOW_NOTE}


def _scaled(base: np.ndarray, block: np.ndarray, alpha: float) -> np.ndarray:
    out = np.empty_like(base)
    for mask in (block, ~block):
        if mask.any():
            mean = base[mask].mean()
            out[mask] = mean + alpha*(base[mask] - mean)
    return out


def _alpha_max(base: np.ndarray, block: np.ndarray) -> float:
    """Largest stretch that keeps the base load non-negative in both blocks."""
    limit = np.inf
    for mask in (block, ~block):
        if mask.any():
            mean, dev = base[mask].mean(), base[mask] - base[mask].mean()
            negative = dev < -1e-12
            if negative.any():
                limit = min(limit, float(np.min(mean/(-dev[negative]))))
    return float(limit) if np.isfinite(limit) else 50.0


def reshape_month(base_kw: np.ndarray, other_kw: np.ndarray, peak_block: np.ndarray, *,
                  target_peak_kw: float, steps: int = 2000) -> tuple:
    """FR-016.8: stretch or flatten the base load of one month so that max(base + other) = target.

    base' = block mean + alpha x (base - block mean) inside each bill block (peak and off-peak), so each block's
    energy is kept exactly (D-V6-15); alpha is the one closest to 1 that reaches the target, never making the
    base negative. If no alpha reaches it the month is 'unresolved' and the base is returned unchanged.
    """
    base, other = np.asarray(base_kw, dtype=float), np.asarray(other_kw, dtype=float)
    block = np.asarray(peak_block, dtype=bool)

    def peak(alpha):
        return float((_scaled(base, block, alpha) + other).max())

    current = peak(1.0)
    if abs(current - target_peak_kw) <= 1e-9*max(1.0, target_peak_kw):
        return base.copy(), 'resolved'
    grid = (np.linspace(1.0, 0.0, steps) if target_peak_kw < current
            else np.linspace(1.0, _alpha_max(base, block), steps))
    hit = next((a for a in grid[1:] if (peak(a) <= target_peak_kw) == (target_peak_kw < current)), None)
    if hit is None:
        return base.copy(), 'unresolved'
    lo, hi = 1.0, float(hit)                       # peak(lo) on the original side, peak(hi) past the target
    for _ in range(100):
        mid = 0.5*(lo + hi)
        if (peak(mid) <= target_peak_kw) == (target_peak_kw < current):
            hi = mid
        else:
            lo = mid
    return _scaled(base, block, hi), 'resolved'
