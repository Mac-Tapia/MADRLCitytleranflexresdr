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


def validate_zone(th, tc, zone: pd.DataFrame, wx: pd.DataFrame) -> dict:
    from scipy.optimize import least_squares
    zone = zone.reindex(wx.index)
    valid = zone.notna().all(axis=1).to_numpy()
    ac_max = float(np.nanpercentile(zone['ac_kw'], 99))
    on = (zone['ac_kw'].fillna(0.0) > AC_ON_FRACTION*ac_max).to_numpy()
    train = (wx.index < TRAIN_END) & valid
    test = (wx.index >= TRAIN_END) & valid
    w_in_rh = 50.0

    def simulate(x):
        envelope, aperture, fraction, cop = x
        area = FLOOR_AREA_M2*fraction            # the share of the floor this zone conditions (fitted)
        inputs, filled = build_inputs(th, zone, wx, on, area)
        flow = (OFFICE_RP*OFFICE_RD/100*area + OFFICE_RA*area)/1000.0
        p = th.iso13790_parameters(floor_area_m2=area, envelope_w_m2k=envelope, solar_aperture_fraction=aperture,
                                   ventilation_w_k=th.ventilation_conductance_w_k(flow), mass_class='medium')
        points = filled['temp'].to_numpy(float)
        w_in = np.array([th.humidity_ratio(t, w_in_rh, inputs.pressure_kpa) for t in points]).mean()
        series = th.ideal_cooling_series(p, inputs, set_point=points, ventilation_m3_s=flow, w_in=w_in)
        return (series['sensible_w'] + series['latent_w'])/1000.0/cop, p, inputs, flow, w_in

    target = zone['ac_kw'].to_numpy(float)
    scale = max(float(np.nanmean(target[train])), 1e-6)
    fit = least_squares(lambda x: (simulate(x)[0] - np.nan_to_num(target))[train]/scale,
                        x0=np.array([1.5, 0.05, 1.0/ZONES_PER_FLOOR, 3.0]),
                        bounds=(np.array([0.05, 0.0, 0.02, 1.5]), np.array([25.0, 0.5, 1.0, 6.0])), x_scale='jac')
    predicted, p, inputs, flow, w_in = simulate(fit.x)
    month = (wx.index.year*12 + wx.index.month).to_numpy()
    energy = {'train': tc.criteria(np.nan_to_num(target), predicted, month, train),
              'test': tc.criteria(np.nan_to_num(target), predicted, month, test)}
    delivered = np.nan_to_num(zone['ac_kw'].interpolate(limit_direction='both').to_numpy(float))*fit.x[3]
    theta = th.simulate_delivered(p, inputs, delivered, ventilation_m3_s=flow, w_in=w_in,
                                  theta_m0=float(zone['temp'].dropna().iloc[0]))
    measured = zone['temp'].to_numpy(float)
    error = (theta - measured)[test]
    persistence = (np.roll(measured, 1) - measured)[test & np.roll(valid, 1)]
    names = ('envelope_w_m2k', 'solar_aperture_fraction', 'conditioned_fraction', 'cop')
    at_bound = [n for n, v, lo, hi in zip(names, fit.x, fit.active_mask, fit.active_mask) if lo != 0]
    return {'parameters': dict(zip(names, (float(v) for v in fit.x))), 'at_bound': at_bound,
            'hours': {'train': int(train.sum()), 'test': int(test.sum()), 'conditioned_share': float(on[valid].mean())},
            'energy_g14': energy,
            'temperature_test': {'rmse_c': float(np.sqrt(np.mean(error**2))), 'bias_c': float(np.mean(error)),
                                 'within_1c_share': float(np.mean(np.abs(error) <= 1.0)),
                                 'persistence_rmse_c': float(np.sqrt(np.mean(persistence**2)))}}


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
            print(key, 'G14 test', r['energy_g14']['test']['passed'],
                  {k: round(v, 1) for k, v in r['energy_g14']['test']['hourly'].items() if k != 'n'},
                  'T rmse', round(r['temperature_test']['rmse_c'], 2), flush=True)
    passed = sum(r['energy_g14']['test']['passed'] for r in results.values())
    report = {'dataset': 'CU-BEMS (CC BY 4.0), figshare 10.6084/m9.figshare.11726517', 'weather': 'NASA POWER hourly',
              'train': '2018-07-01 to 2019-06-30', 'test': '2019-07-01 to 2019-12-31',
              'criteria': tc.CRITERIA, 'zones': results,
              'summary': {'zones': len(results), 'energy_g14_test_passed': int(passed),
                          'median_temperature_rmse_c': float(np.median([r['temperature_test']['rmse_c']
                                                                         for r in results.values()]))},
              'scope': 'validates the 5R1C method in an analogous tropical office, not the Iquitos parameters'}
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'validation_5r1c.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report['summary']))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
