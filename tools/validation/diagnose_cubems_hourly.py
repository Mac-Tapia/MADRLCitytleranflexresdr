"""Training-only diagnosis of the hourly AC electricity of CU-BEMS (card thermal-g14; G14 is informative, owner decision).

Everything from 2019-07-01 on is cut when the data are loaded, so this script cannot see the test period. The benchmark
is the mean by weekday and hour of Jul 2018 to Mar 2019, scored on Apr to Jun 2019, the validation slice. It is a
reference, not a 5R1C variant. Statistics use the formula of citylearn.v3.thermal_calibration.ashrae_g14 with p = 1.
Usage: python -P tools/validation/diagnose_cubems_hourly.py
"""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'data/validation/cubems/raw'
OUT = ROOT/'data/validation/cubems/diagnosis_hourly_train_only.json'
TEST_START = pd.Timestamp('2019-07-01')
VALIDATION_START = pd.Timestamp('2019-04-01')
FLOORS = range(1, 8)
PRIOR_FLOORS, PRIOR_ZONES = (3, 4, 5, 6, 7), (1, 2, 4, 5)   # the 20 zones of validate_5r1c_cubems.py
ON_FRACTION = 0.05          # same rule as validate_5r1c_cubems.AC_ON_FRACTION, applied per unit
OFF_DAY_ZONE_SHARE = 0.5    # a weekday counts as building-wide off when under half of the zones ran
DAY_ON_FRACTION = 0.1       # a zone ran that day when its energy exceeds 10 % of its 90th percentile day (diagnostic)


def g14(measured, simulated) -> dict:
    m, s = np.asarray(measured, dtype=float), np.asarray(simulated, dtype=float)
    dof, mean = len(m) - 1, float(m.mean())
    return {'nmbe_pct': float(100*(m - s).sum()/(dof*mean)),
            'cvrmse_pct': float(100*np.sqrt(((m - s)**2).sum()/dof)/mean), 'n': int(len(m))}


def hide_test(frame):
    return frame[frame.index < TEST_START]


def hour_of_week(index) -> np.ndarray:
    return index.dayofweek*24 + index.hour


def profile_benchmark(fit: pd.Series, target: pd.Series) -> pd.Series:
    """Mean of the fit hours by weekday and hour, evaluated on the target hours."""
    means = fit.groupby(hour_of_week(fit.index)).mean()
    return pd.Series(hour_of_week(target.index), index=target.index).map(means).fillna(0.0)


def day_scaled(profile: pd.Series, measured: pd.Series) -> pd.Series:
    """Oracle, never a model: the profile rescaled to each day's measured energy. Leaves the shape error only."""
    days = measured.index.normalize()
    ratio = measured.groupby(days).transform('sum')/profile.groupby(days).transform('sum').replace(0.0, np.nan)
    return (profile*ratio).fillna(0.0)


def load_minutes(floor: int) -> pd.DataFrame:
    parts = []
    for year in (2018, 2019):
        frame = pd.read_csv(RAW/f'{year}Floor{floor}.csv')
        stamps = pd.to_datetime(frame.pop('Date'), errors='coerce')
        frame = frame.apply(pd.to_numeric, errors='coerce').set_index(stamps)
        parts.append(hide_test(frame[frame.index.notna()]))
    return pd.concat(parts).sort_index()


def within_hour_cycling(minutes: pd.DataFrame, units: list) -> dict:
    """On/off transitions per unit and hour in the hours it ran at least 50 min, the hours where cycling would show."""
    on = (minutes[units] > ON_FRACTION*minutes[units].quantile(.99)).astype(float).where(minutes[units].notna())
    share = on.resample('1h').mean().to_numpy().ravel()
    flips = (on.diff().abs() > 0).astype(float).resample('1h').sum().to_numpy().ravel()
    steady = share >= 50/60
    return {'unit_hours': int(steady.sum()), 'transitions_per_hour': float(flips[steady].mean())}


def diagnose_zone(ac: pd.Series, off_days) -> dict:
    fit, val = ac[ac.index < VALIDATION_START].dropna(), ac[ac.index >= VALIDATION_START].dropna()
    pred = profile_benchmark(fit, val)
    sq = (val - pred)**2
    days = val.index.normalize()
    months = val.index.to_period('M')
    hourly = g14(val, pred)
    monthly = g14(val.groupby(months).sum(), pred.groupby(months).sum())
    bins = pd.cut(val/max(float(fit.quantile(.99)), 1e-9), [-np.inf, .05, .25, .5, .75, np.inf],
                  labels=['<5%', '5-25%', '25-50%', '50-75%', '>75%'])
    blocks = {'07': [7], '08-11': [8, 9, 10, 11], '12': [12], '13-16': [13, 14, 15, 16]}
    return {'hours_fit': len(fit), 'hours_validation': len(val), 'mean_kw_validation': float(val.mean()),
            'hourly': hourly, 'monthly': monthly,
            'hourly_passes': bool(abs(hourly['nmbe_pct']) <= 10 and hourly['cvrmse_pct'] <= 30),
            'monthly_passes': bool(abs(monthly['nmbe_pct']) <= 5 and monthly['cvrmse_pct'] <= 15),
            'day_energy_oracle_cvrmse_pct': g14(val, day_scaled(pred, val))['cvrmse_pct'],
            'sq_error_share': {
                'off_days': float(sq[days.isin(off_days)].sum()/sq.sum()),
                'weekend': float(sq[val.index.dayofweek >= 5].sum()/sq.sum()),
                'monday': float(sq[val.index.dayofweek == 0].sum()/sq.sum()),
                'hour_block': {k: float(sq[np.isin(val.index.hour, v)].sum()/sq.sum()) for k, v in blocks.items()},
                'part_load_of_p99': {str(k): float(v/sq.sum())
                                     for k, v in sq.groupby(bins, observed=True).sum().items()}}}


def main() -> int:
    zones, cycling = {}, {}
    for floor in FLOORS:
        minutes = load_minutes(floor)
        hourly = minutes.resample('1h').mean()
        for zone in sorted({c.split('_')[0] for c in hourly.columns}):
            units = [c for c in hourly.columns if c.startswith(f'{zone}_AC')]
            if units:
                key = f'floor{floor}_{zone}'
                zones[key] = hourly[units].sum(axis=1, min_count=len(units))
                cycling[key] = within_hour_cycling(minutes, units)
    ac = pd.DataFrame(zones)
    day = ac.resample('D').sum(min_count=12)
    ran = (day > DAY_ON_FRACTION*day.quantile(.9)).astype(float).where(day.notna())
    weekday_share = ran[ran.index.dayofweek < 5].mean(axis=1)
    off_days = weekday_share.index[weekday_share < OFF_DAY_ZONE_SHARE]
    results = {k: {**diagnose_zone(ac[k], off_days), 'cycling': cycling[k]} for k in ac.columns}
    prior = [f'floor{f}_z{z}' for f in PRIOR_FLOORS for z in PRIOR_ZONES]

    def median(fn):
        return float(np.median([fn(results[k]) for k in prior]))

    histogram = np.histogram(weekday_share.dropna(), bins=[0, .1, .3, .5, .7, .9, 1.01])[0].tolist()
    report = {'scope': 'training period only; the test period was never loaded; no 5R1C variant was fitted or selected',
              'fit': '2018-07-01 to 2019-03-31', 'validation': '2019-04-01 to 2019-06-30',
              'weekday_zone_share_histogram': histogram,
              'building_wide_off_weekdays': [d.strftime('%Y-%m-%d') for d in off_days],
              'summary_20_zones': {
                  'benchmark_hourly_passes': sum(results[k]['hourly_passes'] for k in prior),
                  'benchmark_monthly_passes': sum(results[k]['monthly_passes'] for k in prior),
                  'benchmark_median_hourly_cvrmse_pct': median(lambda r: r['hourly']['cvrmse_pct']),
                  'oracle_median_hourly_cvrmse_pct': median(lambda r: r['day_energy_oracle_cvrmse_pct']),
                  'median_off_day_sq_error_share': median(lambda r: r['sq_error_share']['off_days']),
                  'median_monday_sq_error_share': median(lambda r: r['sq_error_share']['monday']),
                  'median_hour_08_11_sq_error_share': median(lambda r: r['sq_error_share']['hour_block']['08-11']),
                  'median_hour_13_16_sq_error_share': median(lambda r: r['sq_error_share']['hour_block']['13-16']),
                  'median_transitions_per_steady_unit_hour': median(lambda r: r['cycling']['transitions_per_hour'])},
              'zones': results}
    OUT.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps({k: report[k] for k in ('weekday_zone_share_histogram', 'building_wide_off_weekdays',
                                             'summary_20_zones')}, indent=1))
    for k in prior:
        r = results[k]
        print(k, round(r['hourly']['cvrmse_pct'], 1), round(r['hourly']['nmbe_pct'], 1),
              round(r['monthly']['cvrmse_pct'], 1), round(r['monthly']['nmbe_pct'], 1),
              round(r['day_energy_oracle_cvrmse_pct'], 1), round(r['sq_error_share']['off_days'], 2),
              round(r['cycling']['transitions_per_hour'], 3), r['hours_validation'])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
