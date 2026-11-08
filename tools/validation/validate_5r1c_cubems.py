"""Validate the ISO 13790 5R1C method of citylearn.v3.thermal on measured tropical data (SPEC-016 D-V6-53).

CU-BEMS (Pipattanasomporn et al. 2020, Scientific Data 7:241, CC BY 4.0, figshare 10.6084/m9.figshare.11726517):
a seven-storey 11 700 m2 office building in Bangkok with, per zone and minute, the electricity of each air
conditioner, lighting and plugs, and the indoor temperature and humidity (July 2018 to December 2019). Outdoor
weather: NASA POWER hourly at the site, the same source as Iquitos.

The method is the one of the Iquitos buildings, with the same code: one 5R1C conditioned zone whose envelope
conductance, solar aperture and conditioned fraction of the floor area are fitted, here with the air conditioner's
COP as a fourth parameter (unknown for these units). Two checks, fitted on July 2018 to June 2019 and tested on
July to December 2019:

- energy (ASHRAE Guideline 14): the cooling that holds the measured indoor temperature in the hours the air
  conditioner runs, divided by the COP, against the measured air-conditioning electricity;
- dynamics: the indoor temperature the model gives under the measured air-conditioning electricity x COP, against
  the measured temperature (G14 has no temperature criterion: RMSE, bias and the share of hours within 1 C are
  reported, with a persistence reference).

What this validates is the method in an analogous tropical building, not the parameters of the Iquitos buildings.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT/'data/validation/cubems/raw'
OUT = ROOT/'data/validation/cubems'
FLOOR_AREA_M2 = 11700.0/7          # paper: 11 700 m2 over seven floors (equal split, declared)
ZONES_PER_FLOOR = 5                # floors 3-7 (paper Fig. 2): the zone's share of the floor is fitted
OFFICE_RD = 5.0                    # people per 100 m2, the EM.030 office row of configs/dataset/hvac_norms.yaml
OFFICE_RP, OFFICE_RA = 2.5, 0.3    # L/s per person and per m2, same row
LOCAL_UTC_OFFSET_H = 7             # Bangkok (ICT); CU-BEMS stamps are local, NASA POWER is UTC
AC_ON_FRACTION = 0.05              # an hour counts as conditioned when the zone AC draws > 5 % of its maximum
TRAIN_END = pd.Timestamp('2019-07-01')
SET_FLOORS = (3, 4, 5, 6, 7)
SET_ZONES = (1, 2, 4, 5)


def weather() -> pd.DataFrame:
    data = json.loads((RAW/'nasa_power_bangkok_2018_2019_utc.json').read_text(encoding='utf-8'))
    p = data['properties']['parameter']
    index = pd.to_datetime(list(p['T2M'].keys()), format='%Y%m%d%H') + pd.Timedelta(hours=LOCAL_UTC_OFFSET_H)
    frame = pd.DataFrame({'t': list(p['T2M'].values()), 'rh': list(p['RH2M'].values()),
                          'ghi': list(p['ALLSKY_SFC_SW_DWN'].values())}, index=index)
    frame = frame.replace(-999.0, np.nan).interpolate(limit_direction='both')
    return frame.assign(ghi=frame['ghi'].clip(lower=0.0))


def floor_hourly(floor: int) -> pd.DataFrame:
    parts = []
    for year in (2018, 2019):
        frame = pd.read_csv(RAW/f'{year}Floor{floor}.csv')
        stamps = pd.to_datetime(frame.pop('Date'), errors='coerce')
        frame = frame.apply(pd.to_numeric, errors='coerce').set_index(stamps)
        frame = frame[frame.index.notna()]
        parts.append(frame.resample('1h').mean())
    return pd.concat(parts).sort_index()


def zone_series(hourly: pd.DataFrame, zone: int) -> pd.DataFrame:
    ac = [c for c in hourly.columns if c.startswith(f'z{zone}_AC')]
    temp = f'z{zone}_S1(degC)'
    if not ac or temp not in hourly.columns:
        return None
    return pd.DataFrame({'ac_kw': hourly[ac].sum(axis=1, min_count=len(ac)),
                         'gain_kw': hourly[[f'z{zone}_Light(kW)', f'z{zone}_Plug(kW)']].sum(axis=1, min_count=2),
                         'temp': hourly[temp]})


def build_inputs(th, zone: pd.DataFrame, wx: pd.DataFrame, on: np.ndarray, area: float):
    """Drivers on a gap-free hourly series (gaps interpolated for the simulation, never scored)."""
    pressure = 101.325*(1 - 2.25577e-5*8.0)**5.2559          # NASA POWER elevation of the point, 8 m
    filled = zone.interpolate(limit_direction='both')
    people = OFFICE_RD/100*area
    return th.ThermalInputs(theta_e=wx['t'].to_numpy(float), rh_e=wx['rh'].to_numpy(float),
                            irradiance_w_m2=wx['ghi'].to_numpy(float),
                            electric_gain_w=filled['gain_kw'].clip(lower=0).to_numpy(float)*1000.0,
                            occupants=np.where(on, people, 0.0), pressure_kpa=pressure), filled


def _metrics(err):
    err = np.asarray(err, dtype=float)
    return {'rmse_c': float(np.sqrt(np.mean(err**2))), 'bias_c': float(np.mean(err)),
            'within_1c_share': float(np.mean(np.abs(err) <= 1.0)), 'hours': int(err.size)}


def validate_zone(th, tc, zone: pd.DataFrame, wx: pd.DataFrame) -> dict:
    """Output-error identification, the practice for grey-box RC models: the 5 parameters are fitted on the
    measured indoor temperature under the measured AC electricity and, jointly, on the AC electricity that holds
    the measured temperature. Temperature is scored at 1 h, 24 h and free run, each with its persistence."""
    from scipy.optimize import least_squares
    zone = zone.reindex(wx.index)
    valid = zone.notna().all(axis=1).to_numpy()
    ac_max = float(np.nanpercentile(zone['ac_kw'], 99))
    on = (zone['ac_kw'].fillna(0.0) > AC_ON_FRACTION*ac_max).to_numpy()
    train = (wx.index < TRAIN_END) & valid
    test = (wx.index >= TRAIN_END) & valid
    measured = zone['temp'].to_numpy(float)
    target = zone['ac_kw'].to_numpy(float)
    delivered_e = np.nan_to_num(zone['ac_kw'].interpolate(limit_direction='both').to_numpy(float))
    escale = max(float(np.nanmean(target[train])), 1e-6)
    t0 = float(zone['temp'].dropna().iloc[0])

    def model(x):
        envelope, aperture, fraction, cop, capacity = x
        area = FLOOR_AREA_M2*fraction            # the share of the floor this zone conditions (fitted)
        inputs, filled = build_inputs(th, zone, wx, on, area)
        flow = (OFFICE_RP*OFFICE_RD/100*area + OFFICE_RA*area)/1000.0
        p = th.iso13790_parameters(floor_area_m2=area, envelope_w_m2k=envelope, solar_aperture_fraction=aperture,
                                   ventilation_w_k=th.ventilation_conductance_w_k(flow), mass_class='medium',
                                   heat_capacity_factor=capacity)
        w_in = th.humidity_ratio(float(np.nanmean(measured)), 50.0, inputs.pressure_kpa)
        return p, inputs, filled, flow, w_in

    def outputs(x):
        p, inputs, filled, flow, w_in = model(x)
        theta = th.simulate_delivered(p, inputs, delivered_e*x[3], ventilation_m3_s=flow, w_in=w_in, theta_m0=t0)
        series = th.ideal_cooling_series(p, inputs, set_point=filled['temp'].to_numpy(float), ventilation_m3_s=flow,
                                         w_in=w_in)
        return theta, (series['sensible_w'] + series['latent_w'])/1000.0/x[3]

    def residuals(x):
        theta, energy = outputs(x)
        return np.concatenate([(theta - measured)[train],                       # 1 C weighs as 1
                               (energy - np.nan_to_num(target))[train]/escale])  # the mean AC power weighs as 1

    names = ('envelope_w_m2k', 'solar_aperture_fraction', 'conditioned_fraction', 'cop', 'heat_capacity_factor')
    low = np.array([0.05, 0.0, 0.02, 1.5, 0.2])
    high = np.array([25.0, 0.5, 1.0, 6.0, 5.0])
    fit = least_squares(residuals, x0=np.array([1.5, 0.05, 1.0/ZONES_PER_FLOOR, 3.0, 1.0]), bounds=(low, high),
                        x_scale='jac', max_nfev=200)
    theta, predicted = outputs(fit.x)
    month = (wx.index.year*12 + wx.index.month).to_numpy()
    energy = {'train': tc.criteria(np.nan_to_num(target), predicted, month, train),
              'test': tc.criteria(np.nan_to_num(target), predicted, month, test)}

    # 1 h and 24 h ahead: the mass node restarts from the measured air temperature at the start of the horizon
    p, inputs, filled, flow, w_in = model(fit.x)
    net = th.Network(p)

    def sensible(h):
        return max(0.0, delivered_e[h]*fit.x[3]*1000.0 - th.latent_w(inputs, h, ventilation_m3_s=flow, w_in=w_in))

    one_h, day = np.full(len(measured), np.nan), np.full(len(measured), np.nan)
    for h in range(1, len(measured)):
        if np.isfinite(measured[h - 1]):
            phi_int, phi_sol = th.gains_w(p, inputs, h)
            one_h[h], _ = net.air(float(measured[h - 1]), float(inputs.theta_e[h]), phi_int, phi_sol, -sensible(h))
    for s0 in np.flatnonzero((wx.index.hour == 0) & np.isfinite(measured)):
        theta_m = float(measured[s0])
        for h in range(s0, min(s0 + 24, len(measured))):
            phi_int, phi_sol = th.gains_w(p, inputs, h)
            day[h], theta_m = net.air(theta_m, float(inputs.theta_e[h]), phi_int, phi_sol, -sensible(h))
    prev_h, prev_d = np.roll(measured, 1), np.roll(measured, 24)
    ok1 = test & np.isfinite(one_h) & np.isfinite(prev_h)
    ok24 = test & np.isfinite(day) & np.isfinite(prev_d)
    at_bound = [n for n, v, lo, hi in zip(names, fit.x, low, high) if np.isclose(v, lo) or np.isclose(v, hi)]
    return {'parameters': dict(zip(names, (float(v) for v in fit.x))), 'at_bound': at_bound,
            'hours': {'train': int(train.sum()), 'test': int(test.sum()), 'conditioned_share': float(on[valid].mean())},
            'energy_g14': energy,
            'temperature_test': {
                'one_hour': {**_metrics((one_h - measured)[ok1]), 'persistence': _metrics((prev_h - measured)[ok1])},
                'day_ahead': {**_metrics((day - measured)[ok24]),
                              'same_hour_yesterday': _metrics((prev_d - measured)[ok24])},
                'free_run': _metrics((theta - measured)[test])}}


def main(argv=None) -> int:
    import sys
    sys.path.insert(0, str(ROOT/'CityLearn'))
    from citylearn.v3 import thermal as th
    from citylearn.v3 import thermal_calibration as tc
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--floors', type=int, nargs='*', default=list(SET_FLOORS))
    args = parser.parse_args(argv)
    wx = weather()
    wx = wx[(wx.index >= '2018-07-01') & (wx.index < '2020-01-01')]
    results = {}
    for floor in args.floors:
        hourly = floor_hourly(floor)
        for z in SET_ZONES:
            zone = zone_series(hourly, z)
            if zone is None:
                continue
            key = f'floor{floor}_zone{z}'
            results[key] = validate_zone(th, tc, zone, wx)
            r = results[key]
            t = r['temperature_test']
            print(key, 'monthly', {k: round(v, 1) for k, v in r['energy_g14']['test']['monthly'].items() if k != 'n'},
                  'hourly', {k: round(v, 1) for k, v in r['energy_g14']['test']['hourly'].items() if k != 'n'},
                  'T1h', round(t['one_hour']['rmse_c'], 2), '/', round(t['one_hour']['persistence']['rmse_c'], 2),
                  'T24h', round(t['day_ahead']['rmse_c'], 2), '/',
                  round(t['day_ahead']['same_hour_yesterday']['rmse_c'], 2),
                  'free', round(t['free_run']['rmse_c'], 2), r['at_bound'], flush=True)
    passed = sum(r['energy_g14']['test']['passed'] for r in results.values())
    report = {'dataset': 'CU-BEMS (CC BY 4.0), figshare 10.6084/m9.figshare.11726517', 'weather': 'NASA POWER hourly',
              'train': '2018-07-01 to 2019-06-30', 'test': '2019-07-01 to 2019-12-31',
              'criteria': tc.CRITERIA, 'zones': results,
              'summary': {'zones': len(results), 'energy_g14_test_passed': int(passed),
                          'median_rmse_c': {h: float(np.median([r['temperature_test'][h]['rmse_c']
                                                                for r in results.values()]))
                                            for h in ('one_hour', 'day_ahead', 'free_run')}},
              'scope': 'validates the 5R1C method in an analogous tropical office, not the Iquitos parameters'}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'validation_5r1c.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report['summary']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
