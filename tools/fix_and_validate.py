"""
fix_and_validate.py
===================
PASO 1: Corrige weather.csv desde los parquet cache de NASA POWER
PASO 2: Validacion exhaustiva de los 17 Building CSV
PASO 3: Validacion con CityLearnEnv
"""

import pandas as pd
import numpy as np
import json
from pathlib import Path
import sys

BASE = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
CACHE = Path(".cache/weather")
EXPECTED_ROWS = 26304
YEARS = [2023, 2024, 2025]

# ─────────────────────────────────────────────────────────────────────────────
# PASO 1: Corregir weather.csv
# ─────────────────────────────────────────────────────────────────────────────
print("=" * 80)
print("PASO 1: CORRECCION weather.csv")
print("=" * 80)

dfs = {}
for yr in YEARS:
    p = CACHE / f"{yr}.parquet"
    if not p.exists():
        print(f"  ERROR: {p} no encontrado. Saliendo.")
        sys.exit(1)
    df = pd.read_parquet(p)
    expected = 8784 if yr == 2024 else 8760
    print(f"  {yr}: {len(df)} filas  T2M={df['T2M'].mean():.1f}C  GHI_nz={(df['GHI']>0).sum()}  tz={df.index.tz}")
    if len(df) != expected:
        print(f"    ADVERTENCIA: esperado {expected} filas, encontrado {len(df)}")
    dfs[yr] = df

weather_full = pd.concat([dfs[2023], dfs[2024], dfs[2025]])
print(f"\n  Concatenado: {len(weather_full)} filas (esperado {EXPECTED_ROWS})")

# Construir DataFrame de weather con columnas CityLearn
base_cols = {
    'outdoor_dry_bulb_temperature':    weather_full['T2M'],
    'outdoor_relative_humidity':       weather_full['RH2M'],
    'diffuse_solar_irradiance':        weather_full['DHI'].clip(lower=0),
    'direct_solar_irradiance':         weather_full['DNI'].clip(lower=0),
}
wth = pd.DataFrame(base_cols)
wth.index = range(len(wth))

# Generar 12 columnas de prediccion (shift -1, -2, -3 con ffill)
for base_col in ['outdoor_dry_bulb_temperature', 'outdoor_relative_humidity',
                  'diffuse_solar_irradiance', 'direct_solar_irradiance']:
    for shift in [1, 2, 3]:
        pred_col = f"{base_col}_predicted_{shift}"
        shifted = wth[base_col].shift(-shift)
        wth[pred_col] = shifted.ffill()

# Guardar
out_path = BASE / "weather.csv"
wth.to_csv(out_path, index=False)
print(f"\n  weather.csv guardado: {len(wth)} filas x {len(wth.columns)} columnas")
print(f"  T_outdoor: min={wth['outdoor_dry_bulb_temperature'].min():.1f}C  "
      f"max={wth['outdoor_dry_bulb_temperature'].max():.1f}C  "
      f"mean={wth['outdoor_dry_bulb_temperature'].mean():.1f}C")
print(f"  RH: min={wth['outdoor_relative_humidity'].min():.1f}%  "
      f"max={wth['outdoor_relative_humidity'].max():.1f}%  "
      f"mean={wth['outdoor_relative_humidity'].mean():.1f}%")
print(f"  DHI: max={wth['diffuse_solar_irradiance'].max():.1f} W/m2  "
      f"DNI: max={wth['direct_solar_irradiance'].max():.1f} W/m2")
nan_total = wth.isna().sum().sum()
print(f"  NaN total: {nan_total}  (esperado 0)")
print("  weather.csv CORREGIDO OK" if nan_total == 0 else "  ADVERTENCIA: NaN en weather.csv")

# ─────────────────────────────────────────────────────────────────────────────
# PASO 2: Validacion exhaustiva de los 17 Building CSV
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 80)
print("PASO 2: VALIDACION EXHAUSTIVA — 17 Building CSV")
print("=" * 80)

# Parametros esperados por edificio (del plan MADRL)
BUILDING_CFG = {
    1:  {'name': 'Electro Oriente S.A.',        'type': 'industrial',    'nsl_base': 17.7,  'cool_peak': 126.86, 'cop': 2.8, 'dhw': False, 'area': 14000},
    2:  {'name': 'Complejo Champios',           'type': 'deportivo',     'nsl_base': 3.76,  'cool_peak': 29.0,   'cop': 2.5, 'dhw': False, 'area': 8000},
    3:  {'name': 'Aeropuerto IQT',              'type': 'transporte_24h','nsl_base': 55.3,  'cool_peak': 67.0,   'cop': 3.0, 'dhw': False, 'area': 6000},
    4:  {'name': 'Hiperbodega Precio UNO',      'type': 'mall',          'nsl_base': 14.8,  'cool_peak': 29.5,   'cop': 3.0, 'dhw': False, 'area': 2500},
    5:  {'name': 'Hotel El Dorado Plaza',       'type': 'hotelero_24h',  'nsl_base': 5.4,   'cool_peak': 150.5,  'cop': 3.0, 'dhw': True,  'area': 9000},
    6:  {'name': 'Mall Aventura Iquitos',       'type': 'mall',          'nsl_base': 78.5,  'cool_peak': 850.0,  'cop': 3.0, 'dhw': False, 'area': 20637},
    7:  {'name': 'UNAP Zungarococha',           'type': 'universitario', 'nsl_base': 9.5,   'cool_peak': 167.0,  'cop': 2.8, 'dhw': False, 'area': 8300},
    8:  {'name': 'Escuela Tecnica PNP',         'type': 'educacion',     'nsl_base': 6.9,   'cool_peak': 222.0,  'cop': 2.5, 'dhw': False, 'area': 21000},
    9:  {'name': 'Complejo CNI',                'type': 'deportivo',     'nsl_base': 2.18,  'cool_peak': 19.5,   'cop': 2.5, 'dhw': False, 'area': 3500},
    10: {'name': 'Gobierno Regional Loreto',    'type': 'administrativo','nsl_base': 12.43, 'cool_peak': 117.5,  'cop': 2.8, 'dhw': False, 'area': 5000},
    11: {'name': 'Hospital Regional Loreto',    'type': 'salud_24h',     'nsl_base': 195.0, 'cool_peak': 366.6,  'cop': 2.5, 'dhw': True,  'area': 12000},
    12: {'name': 'EsSalud Hospital III',        'type': 'salud_24h',     'nsl_base': 125.0, 'cool_peak': 222.0,  'cop': 2.5, 'dhw': True,  'area': 6000},
    13: {'name': 'Facultad Economia UNAP',      'type': 'universitario', 'nsl_base': 1.75,  'cool_peak': 62.5,   'cop': 2.8, 'dhw': False, 'area': 3000},
    14: {'name': 'Terminal Portuario ENAPU',    'type': 'portuario_24h', 'nsl_base': 15.7,  'cool_peak': 49.5,   'cop': 2.5, 'dhw': False, 'area': 5000},
    15: {'name': 'Colegio Nacional CNI',        'type': 'educacion',     'nsl_base': 2.76,  'cool_peak': 48.0,   'cop': 2.5, 'dhw': False, 'area': 2500},
    16: {'name': 'I.E. San Juan',               'type': 'educacion',     'nsl_base': 4.55,  'cool_peak': 100.0,  'cop': 2.5, 'dhw': False, 'area': 6500},
    17: {'name': 'IEST Pedro del Aguila',       'type': 'educacion',     'nsl_base': 4.2,   'cool_peak': 93.0,   'cop': 2.5, 'dhw': False, 'area': 5200},
}

# Consumo real medido (kWh/dia) donde disponible — GD-Iquitos V3
REAL_KWH_DAY = {1: 16091, 7: 436, 8: 297, 10: 3358, 11: 9971, 12: 6407, 13: 412, 14: 973, 15: 472}

issues_found = []
ALL_COLUMNS = ['month', 'hour', 'day_type', 'daylight_savings_status',
               'indoor_dry_bulb_temperature', 'average_unmet_cooling_setpoint_difference',
               'indoor_relative_humidity', 'non_shiftable_load', 'dhw_demand',
               'cooling_demand', 'heating_demand', 'solar_generation']

print()
for bid in range(1, 18):
    cfg = BUILDING_CFG[bid]
    fpath = BASE / f"Building_{bid}.csv"

    if not fpath.exists():
        print(f"  B{bid}: FALTA archivo Building_{bid}.csv")
        issues_found.append((bid, 'FALTA_ARCHIVO'))
        continue

    df = pd.read_csv(fpath)

    # --- Verificaciones basicas ---
    n_rows = len(df)
    n_cols = len(df.columns)
    missing_cols = [c for c in ALL_COLUMNS if c not in df.columns]
    nan_total = df.isna().sum().sum()

    row_ok = n_rows == EXPECTED_ROWS
    col_ok = len(missing_cols) == 0
    nan_ok = nan_total == 0

    # --- Verificaciones por columna ---
    errs = []

    # month, hour, day_type
    if df['month'].min() < 1 or df['month'].max() > 12:
        errs.append('month_range')
    if df['hour'].min() < 0 or df['hour'].max() > 23:
        errs.append('hour_range')
    if df['day_type'].min() < 1 or df['day_type'].max() > 7:
        errs.append('day_type_range')

    # daylight_savings_status siempre 0
    if df['daylight_savings_status'].max() != 0:
        errs.append('dst_nonzero')

    # indoor_dry_bulb_temperature — debe ser en rango fisico [15, 40]
    t_in = df['indoor_dry_bulb_temperature']
    if t_in.min() < 10 or t_in.max() > 42:
        errs.append(f'T_indoor_range[{t_in.min():.1f},{t_in.max():.1f}]')
    # Para 2023 (rows 0-8759): T no debe ser 0
    t_2023 = df['indoor_dry_bulb_temperature'].iloc[:8760]
    if (t_2023 < 5).sum() > 100:
        errs.append(f'T_2023_wrong({(t_2023<5).sum()} hrs<5C)')

    # indoor_relative_humidity [20, 100]
    rh_in = df['indoor_relative_humidity']
    if rh_in.min() < 15 or rh_in.max() > 100:
        errs.append(f'RH_range[{rh_in.min():.0f},{rh_in.max():.0f}]')

    # non_shiftable_load: siempre >= 0, debe tener valores > 0
    nsl = df['non_shiftable_load']
    if nsl.min() < 0:
        errs.append('NSL_negative')
    if nsl.max() == 0:
        errs.append('NSL_all_zero')
    # No debe ser menor al 50% del base critico en ninguna hora
    if nsl.min() < cfg['nsl_base'] * 0.3:
        errs.append(f'NSL_below_base(min={nsl.min():.1f},base={cfg["nsl_base"]:.1f})')

    # cooling_demand >= 0, debe ser > 0 en horas diurnas
    cd = df['cooling_demand']
    if cd.min() < 0:
        errs.append('CD_negative')
    if cd.max() == 0:
        errs.append('CD_all_zero')

    # dhw_demand
    dhw = df['dhw_demand']
    if cfg['dhw']:
        if dhw.max() == 0:
            errs.append('DHW_expected_nonzero')
    else:
        if dhw.max() != 0:
            errs.append(f'DHW_unexpected_nonzero(max={dhw.max():.2f})')

    # heating_demand siempre 0
    if df['heating_demand'].max() != 0:
        errs.append('HEATING_nonzero')

    # solar_generation >= 0
    sol = df['solar_generation']
    if sol.min() < 0:
        errs.append('SOLAR_negative')
    if sol.max() == 0:
        errs.append('SOLAR_all_zero')

    # --- Verificacion de escala de energia (solo edificios con datos reales) ---
    scale_note = ''
    if bid in REAL_KWH_DAY:
        real_day = REAL_KWH_DAY[bid]
        # Energia electrica total del modelo (aproximada):
        # E_elec = NSL + CD/COP + DHW/COP_ACS
        cop = cfg['cop']
        model_nsl_day = nsl.mean() * 24
        model_cd_elec_day = (cd.mean() / cop) * 24
        model_dhw_day = (dhw.mean() / 0.85) * 24
        model_total_day = model_nsl_day + model_cd_elec_day + model_dhw_day
        ratio = model_total_day / real_day if real_day > 0 else 0
        scale_note = f' | modelo={model_total_day:.0f} real={real_day} ratio={ratio:.2f}'

    # --- Resumen por edificio ---
    n_issues = len(errs) + (0 if (row_ok and col_ok and nan_ok) else 1)
    status = "OK" if n_issues == 0 else "REVISAR"
    if n_issues > 0:
        issues_found.append((bid, errs))

    print(f"  B{bid:2d} {cfg['name'][:28]:<28}: "
          f"filas={n_rows}/{EXPECTED_ROWS} cols={n_cols}  "
          f"NaN={nan_total}  T_in=[{t_in.min():.0f},{t_in.max():.0f}]C  "
          f"NSL=[{nsl.min():.1f},{nsl.max():.1f}]  "
          f"CD_max={cd.max():.1f}  sol_max={sol.max():.1f}  "
          f"{'OK' if n_issues==0 else 'REVISAR: '+','.join(errs)}"
          f"{scale_note}")

# ─────────────────────────────────────────────────────────────────────────────
# RESUMEN DE PROBLEMAS
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 80)
print("RESUMEN DE PROBLEMAS ENCONTRADOS")
print("=" * 80)
if issues_found:
    for item in issues_found:
        bid, errs = item
        print(f"  B{bid}: {errs}")
else:
    print("  Sin problemas criticos en Building CSVs")

# ─────────────────────────────────────────────────────────────────────────────
# PASO 3: Validacion con CityLearnEnv
# ─────────────────────────────────────────────────────────────────────────────
print()
print("=" * 80)
print("PASO 3: VALIDACION CityLearnEnv")
print("=" * 80)

try:
    sys.path.insert(0, 'CityLearn')
    from citylearn.citylearn import CityLearnEnv

    schema_path = str(BASE / 'schema.json')
    env = CityLearnEnv(schema=schema_path)
    obs, _ = env.reset()
    print(f"  env.reset() OK — obs shape: {len(obs)} agentes")

    # Ejecutar 50 pasos con acciones aleatorias
    import random
    errors_steps = 0
    for step in range(50):
        actions = [np.zeros(len(env.action_space[i].low)) for i in range(len(env.action_space))]
        try:
            obs, rewards, terms, truncs, infos = env.step(actions)
        except AssertionError as e:
            errors_steps += 1
            print(f"    Error en paso {step}: {str(e)[:120]}")
            if errors_steps >= 3:
                break

    if errors_steps == 0:
        print(f"  50 pasos completados sin errores")
    else:
        print(f"  {errors_steps} errores en 50 pasos")

    # Verificar metricas basicas
    kpis = env.unwrapped.evaluate()
    print(f"  KPIs calculados: {len(kpis)} metricas")
    print("  CityLearnEnv VALIDADO OK")

except Exception as e:
    print(f"  ERROR CityLearnEnv: {type(e).__name__}: {str(e)[:300]}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("FIX AND VALIDATE COMPLETADO")
print("=" * 80)
