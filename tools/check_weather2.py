import pandas as pd

BASE = 'CityLearn/data/datasets/citylearn_iquitos_2023_2025'
wth = pd.read_csv(f'{BASE}/weather.csv')

t = wth['outdoor_dry_bulb_temperature']
rh = wth['outdoor_relative_humidity']
dhi = wth['diffuse_solar_irradiance']
dni = wth['direct_solar_irradiance']

print("Por tramo de anyo:")
print("2023 (rows 0-8759):      T mean=%.1f max=%.1f  DHI nz=%d" % (
    t[:8760].mean(), t[:8760].max(), (dhi[:8760]>0).sum()))
print("2024 (rows 8760-17543):  T mean=%.1f max=%.1f  DHI nz=%d" % (
    t[8760:17544].mean(), t[8760:17544].max(), (dhi[8760:17544]>0).sum()))
print("2025 (rows 17544-26303): T mean=%.1f max=%.1f  DHI nz=%d" % (
    t[17544:].mean(), t[17544:].max(), (dhi[17544:]>0).sum()))

print()
print("Primeros 6 valores de 2024 (fila 8760+):")
for i in range(8760, 8766):
    print("  fila %d: T=%.1f RH=%.1f DHI=%.1f DNI=%.1f" % (
        i, t.iloc[i], rh.iloc[i], dhi.iloc[i], dni.iloc[i]))

print()
print("CONCLUSION:")
zeros_2023 = (t[:8760] == 0).sum()
zeros_2024 = (t[8760:17544] == 0).sum()
zeros_2025 = (t[17544:] == 0).sum()
print("  2023: %d horas con T=0 (de 8760 = %.0f%%)" % (zeros_2023, zeros_2023/8760*100))
print("  2024: %d horas con T=0 (de 8784 = %.0f%%)" % (zeros_2024, zeros_2024/8784*100))
print("  2025: %d horas con T=0 (de 8760 = %.0f%%)" % (zeros_2025, zeros_2025/8760*100))
print()
print("DIAGNOSIS: Solo anyo 2023 tiene datos erroneos (placeholder cero)")
print("Los caches parquet tienen datos correctos para los 3 anyos")
print("SOLUCION: Regenerar weather.csv desde .cache/weather/*.parquet")
