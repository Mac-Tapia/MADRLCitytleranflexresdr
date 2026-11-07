"""Reproduce the 2023 cooling calibration of SPEC-016 D-V6-18/D-V6-19 on the 17 buildings.

Run: .venv39-citylearn-v3/Scripts/python.exe docs/audits/calibracion_refrigeracion_20261107/reproductions.py
"""
import json, sys, calendar
sys.path.insert(0, 'tools/dataset')
import numpy as np, pandas as pd, yaml
import distill_building_loads as dbl
from buildingcsv_inputs import load_building_inventory
from uc3m.application.dataset import hvac_capacity as hc, cooling_calibration as cc
inv = load_building_inventory()
dbl.configure_building_types(yaml.safe_load(open('configs/dataset/building_types.yaml', encoding='utf-8')))
norms = hc.load_hvac_norms('configs/dataset/hvac_norms.yaml')
d = json.load(open('data/campaigns/iquitos_v5/raw/weather/nasa_power_2023_utc.json'))
p = d['properties']['parameter']
idx = pd.to_datetime(list(p['T2M']), format='%Y%m%d%H') - pd.Timedelta(hours=5)
w = pd.DataFrame({'t': list(p['T2M'].values()), 'rh': list(p['RH2M'].values())}, index=idx)
w = w[w.index.year == 2023].replace(-999.0, np.nan).interpolate()
P = hc.station_pressure_kpa(d['geometry']['coordinates'][2])
h = np.array([hc.moist_air_enthalpy_kj_per_kg(a, b, P) for a, b in zip(w.t, w.rh)])
h_in = hc.moist_air_enthalpy_kj_per_kg(24, 50, P); h_des = float(np.percentile(h, 99))
cap = hc.district_capacity(inv, norms, outdoor_enthalpy=h_des, indoor_enthalpy=h_in)
eta = dbl._eta_by_building(inv)
hours = w.index.hour.to_numpy(); dtype = (w.index.dayofweek.to_numpy() + 1); month = w.index.month.to_numpy()
MES = {m: i+1 for i, m in enumerate('ene feb mar abr may jun jul ago sep oct nov dic'.split())}; MES['set'] = 9
for b in sorted(inv):
    bills = pd.read_csv(f'CityLearn/data/buildingcsv/B_{b:02d}.csv', sep=';', decimal=',', encoding='latin-1', low_memory=False).dropna(how='all')
    yc = next(c for c in bills.columns if c.startswith('A'))
    bills = bills[pd.to_numeric(bills[yc], errors='coerce') == 2023]
    bill = {MES[str(m).strip().lower()]: float(a + f) for m, a, f in zip(bills.Mes, bills.EnergiaActivaHoraPunta, bills.EnergiaActivaFueraPunta)}
    bill = {k: v for k, v in bill.items() if v > 0}
    keep = np.isin(month, list(bill))
    sched = dbl.operational_factor(inv[b], hours, dtype)
    plr = cc.part_load_ratio(h, indoor_enthalpy=h_in, design_enthalpy=h_des, schedule=np.clip(sched, 0, 1))
    cop = dbl.citylearn_cooling_cop(w.t.to_numpy(), eta[b], 24.0)
    r = cc.calibrate_cooling(capacity_kw_th=cap[b].kw_thermal, cop_h=cop[keep], plr_h=plr[keep], month_h=month[keep],
                             bill_kwh=bill, base_shape_h=np.clip(sched[keep], 0.05, None), base_floor_fraction=0.30)
    share = r.cooling_kwh.sum()/sum(bill.values())*100
    phys = sum(m['physical_cooling_kwh'] for m in r.monthly)/sum(bill.values())*100
    print(f"B{b:02d} meses={len(bill):2d} fis/fact={phys:6.1f}% refrig={share:5.1f}% capados={len(r.capped_months):2d} CV_base={r.base_cv_pct:5.1f}% {'recortado (declarado)' if r.capped_months else 'físico'}")
