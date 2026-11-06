"""Read-only: per-building electric consumption by component, no-control run on train_2023 of iquitos_v5.

Same no-control policy as tools/dataset/build_fresh_campaign_dataset.py::citylearn_balance:
battery and EV actions 0, washing machines started at the first hour of their window.
Controllable today: battery, washing machine, EV chargers (B01). Controllable in v6: cooling.
"""
import json
import time
from pathlib import Path

import numpy as np
from citylearn.citylearn import CityLearnEnv

ROOT = Path(r'D:\MADRLCitytleranflexresdr')
schema = ROOT/'data/campaigns/iquitos_v5/splits/train_2023/schema.json'
env = CityLearnEnv(str(schema))
env.reset()
actions = [[1.0 if 'washing_machine' in n else 0.0 for n in agent] for agent in env.action_names]
start, done = time.time(), False
while not done:
    result = env.step(actions)
    done = bool(result[2]) if len(result) < 5 else bool(result[2] or result[3])
balance = json.loads((ROOT/'data/campaigns/iquitos_v5/audit/citylearn_balance.json').read_text(encoding='utf-8'))


def total(values):
    return float(np.nansum(np.asarray(values, dtype=float)))


rows = []
for b in env.buildings:
    idx = b.name.split('_')[1]
    cooling = total(b.cooling_electricity_consumption)
    heating = total(getattr(b, 'heating_electricity_consumption', [0.0]))
    dhw = total(b.dhw_electricity_consumption)
    nsl = total(b.non_shiftable_load_electricity_consumption if hasattr(b, 'non_shiftable_load_electricity_consumption')
                else b.energy_simulation.non_shiftable_load)
    wm = total(getattr(b, 'washing_machines_electricity_consumption', [0.0]))
    ev = total(getattr(b, 'chargers_electricity_consumption', [0.0]))
    pv = -total(b.solar_generation)
    bill = sum(m['bill_kwh'] for m in balance['buildings'][idx]['months'])
    rows.append(dict(b=b.name, cooling=cooling, heating=heating, dhw=dhw, nsl=nsl, wm=wm, ev=ev, pv=pv, bill=bill,
                     bess_kwh=float(b.electrical_storage.capacity)))
print(f'simulated {time.time()-start:.0f} s')
print(f"{'building':12} {'bill MWh':>9} {'cool':>7} {'nsl':>7} {'dhw':>6} {'wm':>6} {'sum':>8} {'sum/bill':>8} "
      f"{'ctrl%':>6} {'ev(+)':>6} {'pv':>7} {'bessMWh':>7}")
tot = {k: 0.0 for k in ('bill', 'cooling', 'nsl', 'dhw', 'wm', 'heating', 'ev', 'pv')}
for r in rows:
    in_bill = r['cooling'] + r['heating'] + r['nsl'] + r['dhw'] + r['wm']
    ctrl = r['cooling'] + r['wm']  # controllable demand in v6 (cooling) plus the shiftable machine
    for k in tot:
        tot[k] += r[k]
    print(f"{r['b']:12} {r['bill']/1e3:9.1f} {r['cooling']/1e3:7.1f} {r['nsl']/1e3:7.1f} {r['dhw']/1e3:6.1f} "
          f"{r['wm']/1e3:6.2f} {in_bill/1e3:8.1f} {in_bill/r['bill']:8.4f} {100*ctrl/in_bill:6.1f} "
          f"{r['ev']/1e3:6.2f} {r['pv']/1e3:7.1f} {r['bess_kwh']/1e3:7.2f}")
in_bill = tot['cooling'] + tot['heating'] + tot['nsl'] + tot['dhw'] + tot['wm']
print(f"{'DISTRICT':12} {tot['bill']/1e3:9.1f} {tot['cooling']/1e3:7.1f} {tot['nsl']/1e3:7.1f} {tot['dhw']/1e3:6.1f} "
      f"{tot['wm']/1e3:6.2f} {in_bill/1e3:8.1f} {in_bill/tot['bill']:8.4f} "
      f"{100*(tot['cooling']+tot['wm'])/in_bill:6.1f} {tot['ev']/1e3:6.2f} {tot['pv']/1e3:7.1f}")
