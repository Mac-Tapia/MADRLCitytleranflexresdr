"""
calibrate_buildings.py
======================
Calibra los 17 Building CSV para que la energia total del modelo
coincida con los consumos reales medidos (GD-Iquitos V3) o con
benchmarks de intensidad energetica por tipo de edificio.

Columnas escaladas: non_shiftable_load, cooling_demand, dhw_demand
Columnas intactas:  month, hour, day_type, daylight_savings_status,
                    indoor_dry_bulb_temperature,
                    average_unmet_cooling_setpoint_difference,
                    indoor_relative_humidity, heating_demand,
                    solar_generation

Estrategia por edificio
-----------------------
B1  ELOR            NSL solo x18.9 (utility ops: SCADA + servidores 24h)
B7  UNAP Zungar.    Total x0.590  (metro parcial; benchmark 50 kWh/m2/ano)
B8  Esc. PNP        Sin cambio    (metro parcial; 35.5 kWh/m2/ano ok)
B10 Gobierno Reg.   NSL solo x4.70 (edificio subestimado)
B11 Hosp. Regional  Total x0.516  (facturacion hospitalaria completa)
B12 EsSalud III     Total x0.557  (facturacion hospitalaria completa)
B13 UNAP FACEN      Total x0.586  (small faculty, real billing)
B14 ENAPU           Total x0.720  (port terminal, comprehensive)
B15 Colegio CNI     Sin cambio    (ratio 1.06, practicamente perfecto)
B2,3,4,5,6,9,16,17 Sin cambio    (sin datos reales disponibles)
"""

import pandas as pd
import numpy as np
from pathlib import Path
import shutil

BASE = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
BACKUP = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025_backup")

# ── Parametros de calibracion: (nsl_scale, cd_scale, dhw_scale, nsl_floor_kw)
# nsl_floor_kw = carga critica minima 24h del edificio (kW)
CALIB = {
    1:  {'nsl_scale': 18.9,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  17.7,  'reason': 'ELOR utility ops (SCADA+servers 24h)'},
    2:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   3.76, 'reason': 'sin datos reales'},
    3:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  55.3,  'reason': 'sin datos reales'},
    4:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  14.8,  'reason': 'sin datos reales'},
    5:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   5.4,  'reason': 'sin datos reales'},
    6:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  78.5,  'reason': 'sin datos reales'},
    7:  {'nsl_scale':  0.59, 'cd_scale': 0.59,  'dhw_scale': 1.0,   'nsl_floor':   9.5,  'reason': 'metro parcial; benchmark 50 kWh/m2/ano'},
    8:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   6.9,  'reason': 'metro parcial; 35.5 kWh/m2/ano razonable'},
    9:  {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   2.18, 'reason': 'sin datos reales'},
    10: {'nsl_scale':  4.70, 'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':  12.43, 'reason': 'gobierno subestimado'},
    11: {'nsl_scale':  0.516,'cd_scale': 0.516, 'dhw_scale': 0.516, 'nsl_floor': 195.0,  'reason': 'hospital facturacion completa 2 medidores'},
    12: {'nsl_scale':  0.557,'cd_scale': 0.557, 'dhw_scale': 0.557, 'nsl_floor': 125.0,  'reason': 'hospital EsSalud facturacion completa'},
    13: {'nsl_scale':  0.586,'cd_scale': 0.586, 'dhw_scale': 1.0,   'nsl_floor':   1.75, 'reason': 'UNAP FACEN real billing'},
    14: {'nsl_scale':  0.720,'cd_scale': 0.720, 'dhw_scale': 1.0,   'nsl_floor':  15.7,  'reason': 'ENAPU terminal portuario'},
    15: {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   2.76, 'reason': 'ratio 1.06, practicamente perfecto'},
    16: {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   4.55, 'reason': 'sin datos reales'},
    17: {'nsl_scale':  1.0,  'cd_scale': 1.0,   'dhw_scale': 1.0,   'nsl_floor':   4.2,  'reason': 'sin datos reales'},
}

REAL_KWH_DAY = {1: 16091, 7: 436, 8: 297, 10: 3358, 11: 9971, 12: 6407, 13: 412, 14: 973, 15: 472}
COP          = {1:2.8, 7:2.8, 8:2.5, 10:2.8, 11:2.5, 12:2.5, 13:2.8, 14:2.5, 15:2.5}

NAMES = {
    1:'Electro Oriente S.A.', 2:'Municipalidad San Juan Bautista', 3:'Aeropuerto IQT',
    4:'Tottus Oriente Precio UNO', 5:'Hotel El Dorado', 6:'Mall Aventura',
    7:'UNAP Zungarococha', 8:'Escuela PNP', 9:'Complejo CNI',
    10:'Gobierno Regional', 11:'Hospital Regional', 12:'EsSalud Hospital',
    13:'Fac. Economia UNAP', 14:'ENAPU', 15:'Colegio CNI',
    16:'SIMA Iquitos', 17:'Asociacion Civil Selva Amazonica',
}

# ── Backup del dataset original ──────────────────────────────────────────────
print("=" * 80)
print("CALIBRACION DE BUILDING CSV — Iquitos 2023-2025")
print("=" * 80)

if not BACKUP.exists():
    shutil.copytree(BASE, BACKUP)
    print(f"  Backup creado en: {BACKUP}")
else:
    print(f"  Backup ya existe en: {BACKUP}")

# ── Verificar que el floor de NSL sea >= nsl_floor tras el escalado ──────────
print()
print("VERIFICACION PREVIA DE FLOORS:")
print("-" * 60)
for bid in range(1, 18):
    c = CALIB[bid]
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    nsl_min_new = df['non_shiftable_load'].min() * c['nsl_scale']
    floor = c['nsl_floor']
    status = "OK" if nsl_min_new >= floor else f"FLOOR aplicado (min_new={nsl_min_new:.2f} < floor={floor:.2f})"
    if c['nsl_scale'] != 1.0:
        print(f"  B{bid:2d} {NAMES[bid][:25]:<25}: scale={c['nsl_scale']:.3f}  min_new={nsl_min_new:.2f}  floor={floor:.2f}  {status}")

# ── Aplicar calibracion a cada Building CSV ──────────────────────────────────
print()
print("APLICANDO CALIBRACION:")
print("-" * 80)

results = []

for bid in range(1, 18):
    c = CALIB[bid]
    fpath = BASE / f"Building_{bid}.csv"
    df = pd.read_csv(fpath)

    nsl_before = df['non_shiftable_load'].mean() * 24
    cd_before  = df['cooling_demand'].mean() * 24
    dhw_before = df['dhw_demand'].mean() * 24

    # Escalar columnas de energia
    nsl_new = df['non_shiftable_load'] * c['nsl_scale']
    cd_new  = df['cooling_demand']     * c['cd_scale']
    dhw_new = df['dhw_demand']         * c['dhw_scale']

    # Aplicar floor al NSL (nunca puede bajar de la carga critica)
    floor_kwh_h = c['nsl_floor']  # kW = kWh/h para paso horario
    nsl_new = nsl_new.clip(lower=floor_kwh_h)

    # Asegurar que no hay negativos (por seguridad)
    nsl_new = nsl_new.clip(lower=0)
    cd_new  = cd_new.clip(lower=0)
    dhw_new = dhw_new.clip(lower=0)

    # Asignar columnas calibradas
    df['non_shiftable_load'] = nsl_new
    df['cooling_demand']     = cd_new
    df['dhw_demand']         = dhw_new

    # Guardar CSV calibrado
    df.to_csv(fpath, index=False)

    # Calcular energia post-calibracion
    cop_bid = COP.get(bid, 2.8)
    nsl_after = df['non_shiftable_load'].mean() * 24
    cd_after  = df['cooling_demand'].mean() * 24
    dhw_after = df['dhw_demand'].mean() * 24

    cd_elec_after  = cd_after / cop_bid
    dhw_elec_after = dhw_after / 0.85 if dhw_after > 0 else 0
    model_after    = nsl_after + cd_elec_after + dhw_elec_after

    real_day = REAL_KWH_DAY.get(bid, None)
    ratio_after = model_after / real_day if real_day else None

    changed = (c['nsl_scale'] != 1.0 or c['cd_scale'] != 1.0)
    tag = "CALIBRADO" if changed else "sin cambio"

    ratio_str = f"ratio={ratio_after:.2f}" if ratio_after else "sin ref."
    print(f"  B{bid:2d} {NAMES[bid][:25]:<25} [{tag}]:  "
          f"NSL/dia={nsl_after:.0f}  CD_elec/dia={cd_elec_after:.0f}  "
          f"Total/dia={model_after:.0f}  {ratio_str}")

    results.append({
        'bid': bid, 'name': NAMES[bid],
        'nsl_day': nsl_after, 'cd_elec_day': cd_elec_after,
        'dhw_elec_day': dhw_elec_after, 'model_day': model_after,
        'real_day': real_day, 'ratio': ratio_after,
    })

# ── Validacion post-calibracion ───────────────────────────────────────────────
print()
print("=" * 80)
print("VALIDACION POST-CALIBRACION")
print("=" * 80)

ALL_COLS = ['month','hour','day_type','daylight_savings_status',
            'indoor_dry_bulb_temperature','average_unmet_cooling_setpoint_difference',
            'indoor_relative_humidity','non_shiftable_load','dhw_demand',
            'cooling_demand','heating_demand','solar_generation']

BLDG_CFG = {
    1:{'dhw':False,'nsl_floor':17.7},  2:{'dhw':False,'nsl_floor':3.76},
    3:{'dhw':False,'nsl_floor':55.3},  4:{'dhw':False,'nsl_floor':14.8},
    5:{'dhw':True, 'nsl_floor':5.4},   6:{'dhw':False,'nsl_floor':78.5},
    7:{'dhw':False,'nsl_floor':9.5},   8:{'dhw':False,'nsl_floor':6.9},
    9:{'dhw':False,'nsl_floor':2.18},  10:{'dhw':False,'nsl_floor':12.43},
    11:{'dhw':True, 'nsl_floor':195.0},12:{'dhw':True, 'nsl_floor':125.0},
    13:{'dhw':False,'nsl_floor':1.75}, 14:{'dhw':False,'nsl_floor':15.7},
    15:{'dhw':False,'nsl_floor':2.76}, 16:{'dhw':False,'nsl_floor':4.55},
    17:{'dhw':False,'nsl_floor':4.2},
}

all_ok = True
print()
for bid in range(1, 18):
    df = pd.read_csv(BASE / f"Building_{bid}.csv")
    cfg = BLDG_CFG[bid]
    errs = []

    if len(df) != 26304:
        errs.append(f'rows={len(df)}')
    if df.isna().sum().sum() > 0:
        errs.append('NaN')
    if df['non_shiftable_load'].min() < 0:
        errs.append('NSL<0')
    if df['non_shiftable_load'].max() == 0:
        errs.append('NSL=0')
    if df['non_shiftable_load'].min() < cfg['nsl_floor'] * 0.95:  # 5% tolerancia
        errs.append(f"NSL_below_floor(min={df['non_shiftable_load'].min():.2f}<{cfg['nsl_floor']:.2f})")
    if df['cooling_demand'].min() < 0:
        errs.append('CD<0')
    if df['cooling_demand'].max() == 0:
        errs.append('CD=0')
    if df['dhw_demand'].min() < 0:
        errs.append('DHW<0')
    if cfg['dhw'] and df['dhw_demand'].max() == 0:
        errs.append('DHW_expected_nonzero')
    if df['heating_demand'].max() != 0:
        errs.append('heating!=0')
    if df['solar_generation'].min() < 0:
        errs.append('solar<0')

    status = "OK" if not errs else "REVISAR: " + ",".join(errs)
    if errs:
        all_ok = False
    print(f"  B{bid:2d} {NAMES[bid][:28]:<28}: {status}")

print()
print("=" * 80)
print("RESUMEN COMPARATIVO ANTES vs DESPUES")
print("=" * 80)
print()
print("%-5s %-25s %10s %10s %10s %8s" % ("B", "Edificio", "Real/dia", "Model_PREV", "Model_CALIB", "Ratio"))
print("-" * 75)

PREV_MODEL = {
    1:2029, 7:1927, 8:2042, 10:1363, 11:19309, 12:11503, 13:703, 14:1352, 15:498
}
for r in results:
    bid = r['bid']
    real = r['real_day']
    if real is None:
        continue
    prev = PREV_MODEL.get(bid, '-')
    print("%-5d %-25s %10.0f %10s %10.0f %8.2f" % (
        bid, r['name'][:25], real, str(prev), r['model_day'], r['ratio'] or 0))

print()
if all_ok:
    print("CALIBRACION COMPLETADA — Todos los Building CSV son validos")
else:
    print("CALIBRACION COMPLETADA con advertencias — revisar los edificios marcados")

# ── Validacion CityLearnEnv ───────────────────────────────────────────────────
print()
print("=" * 80)
print("VALIDACION CityLearnEnv")
print("=" * 80)
try:
    import sys
    sys.path.insert(0, str(Path("CityLearn")))
    from citylearn.citylearn import CityLearnEnv

    env = CityLearnEnv(schema=str(BASE / 'schema.json'))
    obs, _ = env.reset()
    print(f"  env.reset() OK — {len(obs)} agentes")

    for step in range(100):
        actions = [env.action_space[i].sample() for i in range(len(env.buildings))]
        obs, rewards, done, truncated, info = env.step(actions)
        if done:
            break

    kpis = env.evaluate()
    print(f"  100 pasos OK — {len(kpis)} KPIs calculados")
    print("  CityLearnEnv VALIDADO OK")
except Exception as e:
    print(f"  ERROR CityLearnEnv: {e}")
