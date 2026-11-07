"""Reproduce the change-point feasibility test of SPEC-016 FR-016.1 (2026-11-07).

Fits the ASHRAE Guideline 14 three-parameter cooling model, E/day = b0 + b1*max(0, T - Tb),
to the measured monthly bills (peak + off-peak, D-V6-15) of the 17 buildings against the monthly
mean NASA POWER temperature (UTC-5) of 2023-2025, and prints the fitted cooling share.

Run: .venv39-citylearn-v3/Scripts/python.exe docs/audits/cambio_punto_iquitos_20261107/reproductions.py
"""
import calendar
import glob
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
WEATHER = ROOT/'data/campaigns/iquitos_v5/raw/weather'
BILLS = ROOT/'CityLearn/data/buildingcsv'
MONTHS = {m: i + 1 for i, m in enumerate('ene feb mar abr may jun jul ago sep oct nov dic'.split())}


def monthly_temperatures():
    temps = {}
    for year in (2023, 2024, 2025):
        data = json.loads((WEATHER/f'nasa_power_{year}_utc.json').read_text(encoding='utf-8'))
        series = pd.Series(data['properties']['parameter']['T2M'])
        series.index = pd.to_datetime(series.index, format='%Y%m%d%H') - pd.Timedelta(hours=5)
        series = series[series > -900]
        for (y, m), value in series.groupby([series.index.year, series.index.month]).mean().items():
            if y == year:
                temps[(y, m)] = float(value)
    return temps


def fit(path, temps):
    bills = pd.read_csv(path, sep=';', decimal=',', encoding='latin-1', low_memory=False).dropna(how='all')
    year_col = next(c for c in bills.columns if c.startswith('A'))
    bills = bills[bills['Mes'].astype(str).str.strip().str.lower().isin(MONTHS)]
    energy = (bills['EnergiaActivaHoraPunta'] + bills['EnergiaActivaFueraPunta']).to_numpy(float)
    keys = [(int(y), MONTHS[m.strip().lower()]) for y, m in zip(bills[year_col], bills['Mes'])]
    days = np.array([calendar.monthrange(y, m)[1] for y, m in keys])
    temp = np.array([temps.get(k, np.nan) for k in keys])
    ok = np.isfinite(temp) & (energy > 0)
    y, x = energy[ok]/days[ok], temp[ok]
    best = None
    for balance in np.linspace(x.min(), x.max(), 41)[2:-2]:
        design = np.c_[np.ones(ok.sum()), np.clip(x - balance, 0, None)]
        coef = np.linalg.lstsq(design, y, rcond=None)[0]
        sse = float(((y - design@coef)**2).sum())
        if best is None or sse < best[0]:
            best = (sse, balance, coef, design)
    sse, balance, coef, design = best
    n = len(y)
    se = np.sqrt(sse/(n - 3)*np.linalg.inv(design.T@design)[1, 1])
    return {'n': n, 'balance_c': balance, 'slope': coef[1], 't': coef[1]/se,
            'cv_rmse_pct': np.sqrt(sse/(n - 3))/y.mean()*100,
            'cooling_share_pct': (design[:, 1]*coef[1]).sum()/(design@coef).sum()*100}


if __name__ == '__main__':
    temps = monthly_temperatures()
    values = np.array(list(temps.values()))
    print(f'monthly mean T: {values.min():.2f}-{values.max():.2f} C (range {np.ptp(values):.2f}), n={len(values)}')
    for path in sorted(glob.glob(str(BILLS/'B_*.csv'))):
        r = fit(path, temps)
        print(f"{Path(path).stem} n={r['n']} Tb={r['balance_c']:.2f} slope={r['slope']:+.1f} t={r['t']:+.2f} "
              f"CV(RMSE)={r['cv_rmse_pct']:.1f}% cooling={r['cooling_share_pct']:.0f}%")
