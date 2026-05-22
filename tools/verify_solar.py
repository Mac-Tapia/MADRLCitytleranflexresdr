"""
verify_solar.py
===============
Verificación completa del cálculo de solar_generation:
  1. Área techada útil por edificio → n_módulos correcto
  2. Tensión de string ≤ 1000 V (IEC 61730)
  3. Zona horaria America/Lima en datos meteorológicos y ModelChain
  4. Ubicación geográfica Iquitos (lat=-3.7491, lon=-73.2538)
  5. Cross-check kWh/kWp/día vs referencia Iquitos (4.2–4.8 kWh/kWp/día)
  6. Perfil horario solar del mediodía (hora pico en zona UTC-5)
  7. Consistencia estacional (variación mensual GHI Iquitos ~10%)
"""

import math
import pvlib
import pandas as pd
import numpy as np

# ── Constantes del proyecto ──────────────────────────────────────────────────
AREA_TECHADA = {
    1: 14000, 2: 8000,  3: 6000,  4: 2500,  5: 9000,
    6: 20637, 7: 8300,  8: 21000, 9: 3500,  10: 5000,
    11: 12000,12: 6000, 13: 3000, 14: 5000, 15: 2500,
    16: 6500, 17: 5200,
}
NOMBRES = {
    1: "Electro Oriente S.A.",     2: "Complejo Champios",
    3: "Aeropuerto IQT",           4: "Hiperbodega Precio UNO",
    5: "Hotel El Dorado Plaza",    6: "Mall Aventura Iquitos",
    7: "UNAP Zungarococha",        8: "Escuela Técnica PNP",
    9: "Complejo CNI",            10: "Gobierno Regional Loreto",
    11: "Hospital Regional",       12: "EsSalud Hospital III",
    13: "Facultad Economía UNAP", 14: "Terminal Portuario ENAPU",
    15: "Colegio Nacional CNI",   16: "I.E. San Juan",
    17: "IEST Pedro del Águila",
}
AREA_UTIL_FACTOR = 0.63  # 0.70 techo útil × 0.90 packing
MPS = 15                  # módulos por string: 15×64.60V=969V ≤ 1000V (IEC 61730)
LAT, LON = -3.7491, -73.2538
TZ = "America/Lima"

# ── 1. Módulo Sandia seleccionado ────────────────────────────────────────────
print("=" * 80)
print("1. MÓDULO SANDIA SELECCIONADO")
print("=" * 80)
mods = pvlib.pvsystem.retrieve_sam("SandiaMod")
if mods.shape[0] < mods.shape[1]:
    mods = mods.T
mods["Pmp"] = mods["Vmpo"] * mods["Impo"]
mods["eta"] = mods["Pmp"] / (mods["Area"] * 1000)
cands = mods[
    ~mods.index.str.contains("CPV", case=False, na=False) &
    (mods["eta"] >= 0.15) &
    (mods["Area"].between(1.5, 2.6)) &
    (mods["Pmp"] >= 250)
].sort_values(["eta"], ascending=False)

MOD_KEY = cands.index[0]
MP = mods.loc[MOD_KEY]
pmp_w = MP.Vmpo * MP.Impo
eta   = pmp_w / (MP.Area * 1000)

print(f"  Clave:  {MOD_KEY}")
print(f"  Pmp     = {pmp_w:.1f} W")
print(f"  Área    = {MP.Area:.4f} m²")
print(f"  η_STC   = {eta:.2%}")
print(f"  Vmpo    = {MP.Vmpo:.2f} V   Impo = {MP.Impo:.3f} A")
print(f"  Voco    = {MP.Voco:.2f} V   Isco = {MP.Isco:.3f} A")
print(f"  Bvoco   = {MP.Bvoco:.5f} V/°C  (pérdida temperatura)")
print(f"  Voc por string ({MPS} mód): {MPS * MP.Voco:.1f} V  → {'OK ≤1000V' if MPS * MP.Voco <= 1000 else 'ERROR >1000V'}")

# ── 2. Ubicación y zona horaria ───────────────────────────────────────────────
print()
print("=" * 80)
print("2. UBICACIÓN IQUITOS Y ZONA HORARIA")
print("=" * 80)
loc = pvlib.location.Location(latitude=LAT, longitude=LON, tz=TZ, altitude=106)
print(f"  lat    = {loc.latitude}°  (Iquitos -3.7491°S ✓)")
print(f"  lon    = {loc.longitude}°  (Iquitos -73.2538°O ✓)")
print(f"  tz     = {loc.tz}  (UTC-5, Lima ✓)")
print(f"  alt    = {loc.altitude} m  (Iquitos ~106 m s.n.m. ✓)")

# Verificar que el amanecer/ocaso son correctos para Iquitos (Ecuador ~lat cero)
import datetime
sol = loc.get_sun_rise_set_transit(
    pd.DatetimeIndex([pd.Timestamp("2024-06-21", tz=TZ)])
)
sunrise_h = sol["sunrise"].iloc[0].hour + sol["sunrise"].iloc[0].minute / 60
sunset_h  = sol["sunset"].iloc[0].hour  + sol["sunset"].iloc[0].minute / 60
print(f"\n  Amanecer (21 jun 2024): {sol['sunrise'].iloc[0].strftime('%H:%M')} hora Lima")
print(f"  Ocaso   (21 jun 2024): {sol['sunset'].iloc[0].strftime('%H:%M')} hora Lima")
print(f"  Horas de sol: {sunset_h - sunrise_h:.1f} h  (Iquitos real: ~12.0 h)")

# ── 3. Datos meteorológicos — verificación tz y valores ──────────────────────
print()
print("=" * 80)
print("3. DATOS METEOROLÓGICOS — ZONA HORARIA Y VALORES")
print("=" * 80)
dfs = {}
for yr in [2023, 2024, 2025]:
    df = pd.read_parquet(f".cache/weather/{yr}.parquet")
    dfs[yr] = df
    ghi_nz  = int((df["GHI"] > 0).sum())
    t2m_ok  = df["T2M"].between(20, 38).all()
    n_exp   = 8784 if yr == 2024 else 8760
    tz_ok   = str(df.index.tz) == TZ
    print(f"  {yr}: tz={df.index.tz}  filas={len(df)}/{n_exp}  GHI_nz={ghi_nz}  "
          f"T2M={df['T2M'].mean():.1f}°C  tz_ok={tz_ok}  t2m_ok={t2m_ok}")
    print(f"       primer ts: {df.index[0]}  último: {df.index[-1]}")
    print(f"       GHI max={df['GHI'].max():.1f} W/m²  T2M min={df['T2M'].min():.1f}°C max={df['T2M'].max():.1f}°C")

weather_full = pd.concat([dfs[2023], dfs[2024], dfs[2025]])
print(f"\n  TOTAL: {len(weather_full)} filas (esperado 26304)")

# Verificar distribución horaria del GHI — pico debe estar en hora 11-13 (Lima UTC-5)
ghi_by_hour = weather_full.groupby(weather_full.index.hour)["GHI"].mean()
peak_hour   = int(ghi_by_hour.idxmax())
print(f"\n  Hora pico GHI promedio: {peak_hour:02d}:00 hora Lima (esperado 11-13) → "
      f"{'OK' if 10 <= peak_hour <= 14 else 'REVISAR'}")
print("  GHI promedio por hora:")
for h in range(5, 19):
    bar = "█" * int(ghi_by_hour.get(h, 0) / 30)
    print(f"    {h:02d}h: {ghi_by_hour.get(h, 0):6.1f} W/m²  {bar}")

# ── 4. Tabla de verificación por edificio ────────────────────────────────────
print()
print("=" * 80)
print("4. VERIFICACIÓN DE SIZING POR EDIFICIO")
print("=" * 80)
header = (
    f"{'B':>2}  {'Area_m2':>8}  {'Util_m2':>8}  {'N_mod':>6}  {'N_str':>6}  "
    f"{'Pdc_kW':>8}  {'Voc_str_V':>10}  {'kWp_util%':>10}"
)
print(header)
print("-" * 75)
for bid in range(1, 18):
    at    = AREA_TECHADA[bid]
    au    = at * AREA_UTIL_FACTOR
    n_mod = max(1, int(au // MP.Area))
    n_str = max(1, math.ceil(n_mod / MPS))
    pdc   = n_mod * pmp_w / 1000
    voc_s = MPS * MP.Voco
    # Porcentaje del área techada realmente cubierta por módulos
    area_mod = n_mod * MP.Area
    pct_util  = area_mod / au * 100
    print(f"{bid:>2}  {at:>8}  {au:>8.0f}  {n_mod:>6}  {n_str:>6}  "
          f"{pdc:>8.1f}  {voc_s:>10.1f}  {pct_util:>9.1f}%")
print()

# Verificación crítica: Voc < 1000V
if MPS * MP.Voco <= 1000:
    print(f"  Tensión por string: {MPS} módulos × {MP.Voco:.1f}V = {MPS*MP.Voco:.1f}V ≤ 1000V ✓ (IEC 61730)")
else:
    print(f"  ERROR: Tensión de string {MPS*MP.Voco:.1f}V > 1000V (IEC 61730)")

# ── 5. Cross-check kWh/kWp/día vs generación real en CSV ───────────────────
print()
print("=" * 80)
print("5. CROSS-CHECK kWh/kWp/día (referencia Iquitos: 4.2–4.8 kWh/kWp/día)")
print("=" * 80)
header2 = (
    f"{'B':>2}  {'Pdc_kWp':>8}  {'Ann_kWh/año':>12}  "
    f"{'kWh/kWp/día':>12}  {'Ratio':>7}  {'OK?':>6}"
)
print(header2)
print("-" * 60)
all_ok = True
for bid in range(1, 18):
    at    = AREA_TECHADA[bid]
    au    = at * AREA_UTIL_FACTOR
    n_mod = max(1, int(au // MP.Area))
    pdc   = n_mod * pmp_w / 1000

    csv_path = f"CityLearn/data/datasets/citylearn_iquitos_2023_2025/Building_{bid}.csv"
    df = pd.read_csv(csv_path)
    ann_kwh = df["solar_generation"].sum() / 3  # promedio anual (3 años)
    kwh_kwp_day = ann_kwh / pdc / 365

    ok = 2.5 <= kwh_kwp_day <= 6.5  # rango amplio (incluye días nublados)
    if not ok:
        all_ok = False
    ref_ok = "✓" if 4.0 <= kwh_kwp_day <= 5.5 else ("~OK" if 2.5 <= kwh_kwp_day <= 6.5 else "ERR")
    print(f"{bid:>2}  {pdc:>8.1f}  {ann_kwh:>12,.0f}  "
          f"{kwh_kwp_day:>12.3f}  {ref_ok:>7}  {'OK' if ok else 'REVISAR':>6}")

print()
if all_ok:
    print("  Todos los edificios dentro del rango físico esperado ✓")
else:
    print("  ADVERTENCIA: Algunos edificios fuera del rango esperado — revisar")

# ── 6. Perfil horario de un día soleado representativo ──────────────────────
print()
print("=" * 80)
print("6. PERFIL HORARIO solar_generation — Building_1 (día soleado típico)")
print("=" * 80)
df1 = pd.read_csv("CityLearn/data/datasets/citylearn_iquitos_2023_2025/Building_1.csv")
# Buscar un día de alta generación en 2024 (filas 8760–17543)
solar_b1  = df1["solar_generation"].values
# Buscar el mejor DÍA CALENDARIO de 2024 (inicio siempre en medianoche)
# 2024 comienza en row 8760; 366 días × 24 h = 8784 rows
best_day_start = 8760
best_sum = 0
for d in range(366):  # días calendario de 2024
    start = 8760 + d * 24
    if start + 24 > len(solar_b1):
        break
    s = solar_b1[start:start + 24].sum()
    if s > best_sum:
        best_sum = s
        best_day_start = start

# Calcular fecha correspondiente (best_day_start es siempre múltiplo de 24 desde 8760)
idx_start = best_day_start - 8760  # múltiplo exacto de 24 (=días × 24 h)
date_2024 = pd.Timestamp("2024-01-01", tz=TZ) + pd.Timedelta(hours=idx_start)
print(f"  Día analizado: {date_2024.strftime('%Y-%m-%d')} (índice {best_day_start})")
print(f"  Generación total del día: {best_sum:.1f} kWh")
print()
print(f"  {'Hora Lima':>9}  {'solar_gen kWh':>14}  {'Barra'}")
print(f"  {'-'*9}  {'-'*14}  {'-'*30}")
for h in range(24):
    val = solar_b1[best_day_start + h]
    bar = "█" * int(val / 60)
    print(f"  {h:02d}:00 Lima  {val:>14.1f}  {bar}")

# Verificar: generación debe ser 0 antes de ~5:30 y después de ~18:30 Lima
night_hours  = [0, 1, 2, 3, 4, 19, 20, 21, 22, 23]
night_nonzero = sum(1 for h in night_hours if solar_b1[best_day_start + h] > 0.01)
print(f"\n  Generación en horas nocturnas: {night_nonzero}/10 con valor >0 "
      f"→ {'OK' if night_nonzero == 0 else 'REVISAR'}")

# ── 7. Variación mensual GHI (estacionalidad) ────────────────────────────────
print()
print("=" * 80)
print("7. VARIACIÓN MENSUAL GHI PROMEDIO — Iquitos (debe ser ~10% variación)")
print("=" * 80)
ghi_by_month = weather_full.groupby(weather_full.index.month)["GHI"].mean()
meses = ["Ene","Feb","Mar","Abr","May","Jun","Jul","Ago","Sep","Oct","Nov","Dic"]
ghi_max_m = ghi_by_month.max()
for m in range(1, 13):
    val = ghi_by_month.get(m, 0)
    bar = "█" * int(val / 5)
    pct = val / ghi_max_m * 100
    print(f"  {meses[m-1]:>3}: {val:6.1f} W/m² ({pct:4.1f}%)  {bar}")
variacion = (ghi_by_month.max() - ghi_by_month.min()) / ghi_by_month.mean() * 100
print(f"\n  Variación mensual GHI: {variacion:.1f}% (Iquitos real: ~10–20%)")
print(f"  → {'OK' if variacion < 40 else 'REVISAR — variación alta'}")

print()
print("=" * 80)
print("VERIFICACIÓN COMPLETADA")
print("=" * 80)
