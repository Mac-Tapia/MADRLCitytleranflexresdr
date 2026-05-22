import pandas as pd
import numpy as np

BASE = 'CityLearn/data/datasets/citylearn_iquitos_2023_2025'

wth = pd.read_csv(f'{BASE}/weather.csv')
idx = pd.date_range('2023-01-01', periods=26304, freq='h', tz='America/Lima')
wth.index = idx

t_col = 'outdoor_dry_bulb_temperature'
rh_col = 'outdoor_relative_humidity'

print("=== TEMPERATURA EXTERIOR — distribucion mensual ===")
monthly = wth.groupby(wth.index.month)[t_col].agg(['min','mean','max'])
meses = ['Ene','Feb','Mar','Abr','May','Jun','Jul','Ago','Sep','Oct','Nov','Dic']
print(f"  {'Mes':<5} {'Min':>6} {'Media':>7} {'Max':>7}")
for m in range(1, 13):
    if m in monthly.index:
        r = monthly.loc[m]
        mn, me, mx = r['min'], r['mean'], r['max']
        print(f"  {meses[m-1]:<5} {mn:>6.1f} {me:>7.1f} {mx:>7.1f}")

print()
print("Iquitos esperado: min~24C, mean~27C, max~33C")
print(f"T < 10 deg: {(wth[t_col] < 10).sum()} horas")
print(f"T <  0 deg: {(wth[t_col] < 0).sum()} horas (fisicamente imposible para Iquitos)")
print(f"T > 35 deg: {(wth[t_col] > 35).sum()} horas")

print()
print("=== PRIMERAS 24 HORAS (2023-01-01) ===")
print(f"  {'Timestamp':<20} {'T':>5} {'RH':>5} {'DHI':>6} {'DNI':>6}")
for i in range(24):
    print(f"  {str(idx[i])[:16]:<20} {wth[t_col].iloc[i]:>5.1f} {wth[rh_col].iloc[i]:>5.1f} {wth['diffuse_solar_irradiance'].iloc[i]:>6.1f} {wth['direct_solar_irradiance'].iloc[i]:>6.1f}")

print()
print("=== VERANO PERUANO — muestra mediodía 2023-01-15 (dia 15) ===")
for i in range(24*14, 24*15):
    h = i % 24
    if 8 <= h <= 16:
        print(f"  hora {h:02d}: T={wth[t_col].iloc[i]:.1f}C  RH={wth[rh_col].iloc[i]:.1f}%  DHI={wth['diffuse_solar_irradiance'].iloc[i]:.1f}  DNI={wth['direct_solar_irradiance'].iloc[i]:.1f}")

# Comparar con datos del cache .cache/weather si existen
import pathlib
cache_path = pathlib.Path('.cache/weather/2023.parquet')
if cache_path.exists():
    print()
    print("=== CACHE NASA POWER 2023.parquet — temperaturas reales descargadas ===")
    cache = pd.read_parquet(cache_path)
    print(f"  Columnas: {list(cache.columns)}")
    if 'T2M' in cache.columns:
        t2m = cache['T2M']
        print(f"  T2M: min={t2m.min():.1f}  max={t2m.max():.1f}  mean={t2m.mean():.1f} C")
        print(f"  T2M muestras (primeros 10 valores):")
        for i in range(10):
            print(f"    {i:02d}h: {t2m.iloc[i]:.2f} C")
else:
    print()
    print("Cache .cache/weather/2023.parquet no encontrado")
    # Buscar cache en otros directorios
    for p in pathlib.Path('.').rglob('*.parquet'):
        print(f"  Parquet encontrado: {p}")
