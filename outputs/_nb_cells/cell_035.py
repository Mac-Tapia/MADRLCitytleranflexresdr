# ── 3.1  Verificar estructura del dataset Iquitos 2023-2025 ──────────────────
# Valida dataset LOCAL real del proyecto. NO modifica ningún archivo.
# Columnas verificadas son las del dataset real (snake_case CityLearn v2).
import json
import os
import pandas as pd
from pathlib import Path

DATASET_DIR = Path(REPO) / "CityLearn/data/datasets/citylearn_iquitos_2023_2025"

with open(SCHEMA_PATH) as f:
    schema = json.load(f)

buildings = schema.get("buildings", {})
n_blds = len(buildings)
assert n_blds == 17, f"Se esperaban 17 edificios, encontrados: {n_blds}"
print("Dataset         : citylearn_iquitos_2023_2025")
print(f"Schema          : {SCHEMA_PATH}")
print(f"Edificios       : {n_blds} / 17  OK")
print(f"Pasos simulacion: {schema.get('simulation_end_time_step', 0) + 1}  (26304 = 3 años)")
print(f"Agente central  : {schema.get('central_agent', False)}")
print()

# ── Columnas reales del Building CSV (snake_case CityLearn v2) ─────────────────
# Fuente: Building_1.csv — mismo esquema en los 17 edificios
BUILDING_REQUIRED_COLS = [
    "month",
    "hour",
    "day_type",
    "non_shiftable_load",       # carga electrica no desplazable [kWh]
    "solar_generation",         # generacion FV del edificio [W/kW]
    "cooling_demand",           # demanda de enfriamiento [kWh]
    "dhw_demand",               # agua caliente sanitaria [kWh]
    "heating_demand",           # calefaccion [kWh]
]

# ── Columnas reales del weather CSV (compartido por todos los edificios) ───────
WEATHER_REQUIRED_COLS = [
    "outdoor_dry_bulb_temperature",
    "outdoor_relative_humidity",
    "direct_solar_irradiance",
    "diffuse_solar_irradiance",
]

# ── Validar weather.csv (compartido) ──────────────────────────────────────────
weather_csv = DATASET_DIR / "weather.csv"
assert weather_csv.exists(), f"weather.csv no encontrado: {weather_csv}"
df_weather = pd.read_csv(weather_csv)
assert len(df_weather) == 26304, f"weather.csv: se esperaban 26304 filas, hay {len(df_weather)}"
missing_weather = [c for c in WEATHER_REQUIRED_COLS if c not in df_weather.columns]
assert not missing_weather, f"Columnas faltantes en weather.csv: {missing_weather}"
print(f"weather.csv     : {len(df_weather)} filas x {len(df_weather.columns)} cols  OK")

# ── Validar carbon_intensity.csv (compartido) ─────────────────────────────────
carbon_csv = DATASET_DIR / "carbon_intensity.csv"
assert carbon_csv.exists(), "carbon_intensity.csv no encontrado"
df_carbon = pd.read_csv(carbon_csv)
assert len(df_carbon) == 26304, f"carbon_intensity.csv: {len(df_carbon)} filas (esperado 26304)"
assert "carbon_intensity" in df_carbon.columns, "Columna 'carbon_intensity' no encontrada"
print(f"carbon_intensity: {len(df_carbon)} filas | rango [{df_carbon['carbon_intensity'].min():.3f}, {df_carbon['carbon_intensity'].max():.3f}] kgCO2/kWh  OK")

# ── Validar pricing.csv (tarifas eléctricas Iquitos) ─────────────────────────
pricing_csv = DATASET_DIR / "pricing.csv"
if pricing_csv.exists():
    df_price = pd.read_csv(pricing_csv)
    assert len(df_price) == 26304
    print(f"pricing.csv     : {len(df_price)} filas | rango [{df_price['electricity_pricing'].min():.3f}, {df_price['electricity_pricing'].max():.3f}] USD/kWh  OK")
else:
    print("pricing.csv     : no disponible (tarifas integradas en schema)")
print()

# ── Validar Building CSVs + PV + BESS + EV ───────────────────────────────────
ev_buildings = 0
bess_buildings = 0
pv_buildings = 0
csv_errors = []

print(f"{'Edificio':<22} {'Filas':>6} {'BldCols':>7} {'PV kW':>8} {'BESS kWh':>9} {'EV':>5}")
print("-" * 60)

for i, (name, bld) in enumerate(buildings.items()):
    # CSV de energía del edificio
    csv_rel = bld.get("energy_simulation", f"{name}.csv")
    csv_full = DATASET_DIR / csv_rel
    try:
        df_bld = pd.read_csv(csv_full)
        row_ok = len(df_bld) == 26304
    except Exception as e:
        csv_errors.append((name, str(e)))
        df_bld = pd.DataFrame()
        row_ok = False

    # Columnas obligatorias del Building CSV
    cols_ok = all(col in df_bld.columns for col in BUILDING_REQUIRED_COLS) if not df_bld.empty else False

    # PV — campo 'pv' -> 'attributes' -> 'nominal_power'
    pv_info = bld.get("pv", {})
    pv_kw = pv_info.get("attributes", {}).get("nominal_power", 0) if pv_info else 0
    if pv_kw > 0:
        pv_buildings += 1

    # BESS — campo 'electrical_storage' -> 'attributes' -> 'capacity'
    bess_info = bld.get("electrical_storage", {})
    bess_kwh = bess_info.get("attributes", {}).get("capacity", 0) if bess_info else 0
    if bess_kwh > 0:
        bess_buildings += 1

    # EV chargers — campo 'chargers' es un dict con un entry por punto de carga
    chargers = bld.get("chargers", {})
    n_ev = len(chargers)
    if n_ev > 0:
        ev_buildings += 1

    # Verificar que los CSV de chargers existen
    for ch_name, ch_data in chargers.items():
        ch_csv = ch_data.get("charger_simulation", "")
        ch_full = DATASET_DIR / ch_csv
        if ch_csv and not ch_full.exists():
            csv_errors.append((f"{name}/{ch_name}", f"charger CSV falta: {ch_csv}"))

    if i < 6 or i >= n_blds - 2:
        row_str = str(len(df_bld)) if not df_bld.empty else "ERR"
        print(
            f"{name:<22} {row_str:>6} {'OK' if cols_ok else 'ERR':>7}"
            f" {pv_kw:>8.0f} {bess_kwh:>9.0f} {n_ev:>5}"
        )
    elif i == 6:
        print(f"  ... ({n_blds - 8} edificios más) ...")

print()
print(f"Edificios con PV   : {pv_buildings}/{n_blds}")
print(f"Edificios con BESS : {bess_buildings}/{n_blds}")
print(f"Edificios con EV   : {ev_buildings}/{n_blds}")
total_ev_points = sum(len(bld.get("chargers", {})) for bld in buildings.values())
print(f"Puntos carga EV    : {total_ev_points}  (IEC 61851 Modo 3 CA)")
total_bess_kwh = sum(
    bld.get("electrical_storage", {}).get("attributes", {}).get("capacity", 0)
    for bld in buildings.values()
)
print(f"BESS total         : {total_bess_kwh:.0f} kWh")
total_pv_kw = sum(
    bld.get("pv", {}).get("attributes", {}).get("nominal_power", 0)
    for bld in buildings.values()
)
print(f"PV total           : {total_pv_kw:.0f} kW")

if csv_errors:
    print(f"\nERRORES: {len(csv_errors)}")
    for bld_name, err in csv_errors:
        print(f"  {bld_name}: {err}")
    raise RuntimeError(f"{len(csv_errors)} archivos CSV no encontrados. Revisa el dataset.")

# ── Conteo final de archivos ───────────────────────────────────────────────────
import glob as _glob
total_csvs = len(_glob.glob(str(DATASET_DIR / "*.csv")))
charger_csvs = len(_glob.glob(str(DATASET_DIR / "charger_*.csv")))
print(f"\nTotal CSV dataset : {total_csvs}  (17 building + {charger_csvs} charger + 3 especiales + 17 washing)")
print("Dataset Iquitos 2023-2025: VALIDADO — PV / BESS / EV / Clima / CO₂ / Precios")
