"""
fix_schema_cooling.py
=====================
Corrige cooling_device en todos los edificios del schema.json:
  - autosize: false
  - efficiency = factor Carnot que reproduce el COP del plan en condiciones Iquitos
  - nominal_power = capacidad electrica real para cubrir pico de cooling_demand
                    a la temperatura exterior maxima registrada en el dataset

Formula CityLearn HeatPump (cooling):
  COP_act = (t_target_cooling + 273.15) * efficiency / (T_out - t_target_cooling)
  max_thermal_output = nominal_power * COP_act

Calibracion:
  T_out_avg = 28degC, t_target_cooling = 8.5degC (default midpoint 7-10degC)
  cop_factor_avg = (8.5 + 273.15) / (28 - 8.5) = 14.44
  efficiency = COP_plan / cop_factor_avg

Sizing:
  T_out_max = temperatura exterior maxima del weather.csv real
  COP_worst = (t_target + 273.15) * efficiency / (T_out_max - t_target)
  nominal_power = ceil(peak_cooling_demand / COP_worst * SAFETY_FACTOR)
  donde peak_cooling_demand = max(Building_X.csv['cooling_demand'])
"""
import json, sys, math
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding='utf-8')

DATASET_DIR = Path(r"d:\MADRLCitytleranflexresdr\CityLearn\data\datasets\citylearn_iquitos_2023_2025")
SCHEMA_PATH = DATASET_DIR / "schema.json"
WEATHER_PATH = DATASET_DIR / "weather.csv"

# COP del plan por edificio (fijo a condiciones diseno T_avg=28degC)
COP_PLAN = {
    1: 2.8,   # industrial (oficinas con VRF)
    2: 2.5,   # deportivo
    3: 3.0,   # transporte_24h (aeropuerto VRF alta eficiencia)
    4: 3.0,   # mall
    5: 3.0,   # hotelero
    6: 3.0,   # mall
    7: 2.8,   # universitario
    8: 2.5,   # educacion
    9: 2.5,   # deportivo
    10: 2.8,  # administrativo
    11: 2.5,  # salud_24h (chiller hospitalario)
    12: 2.5,  # salud_24h
    13: 2.8,  # universitario
    14: 2.5,  # portuario
    15: 2.5,  # educacion
    16: 2.5,  # educacion
    17: 2.5,  # educacion
}

# Factor Carnot en condiciones promedio Iquitos
T_OUT_AVG     = 28.0
T_TARGET_COOL = 8.5   # midpoint CityLearn default 7-10degC
COP_FACTOR_AVG = (T_TARGET_COOL + 273.15) / (T_OUT_AVG - T_TARGET_COOL)  # 14.44

# Factor de seguridad para nominal_power (cubre variabilidad de carga y temperatura)
SAFETY_FACTOR = 1.10  # +10% sobre el pico de demanda a T_out_max

# ── Leer temperatura exterior maxima del dataset real ─────────────────────────
weather = pd.read_csv(WEATHER_PATH)
T_OUT_MAX = weather['outdoor_dry_bulb_temperature'].max()

print("=" * 70)
print("FIX cooling_device — schema.json")
print(f"  T_out_avg={T_OUT_AVG}degC  T_out_max={T_OUT_MAX:.2f}degC  T_target={T_TARGET_COOL}degC")
print(f"  cop_factor_avg={COP_FACTOR_AVG:.4f}  safety_factor={SAFETY_FACTOR}")
print("=" * 70)
print(f"  {'B':>3}  {'COP_avg':>7}  {'COP_worst':>9}  {'eta':>8}  {'peak_cd':>9}  {'nom_pwr':>9}  {'check':>8}")
print(f"  {'-'*65}")

# ── Load schema ────────────────────────────────────────────────────────────────
with open(SCHEMA_PATH, encoding='utf-8') as f:
    schema = json.load(f)

for bkey, bdata in schema['buildings'].items():
    bid = int(bkey.split('_')[1])
    cop   = COP_PLAN[bid]
    eta   = round(cop / COP_FACTOR_AVG, 6)   # Carnot efficiency factor

    # COP en condiciones peores (T_out_max del dataset real)
    cop_worst = (T_TARGET_COOL + 273.15) * eta / (T_OUT_MAX - T_TARGET_COOL)

    # Pico real de cooling_demand del CSV
    bldg_csv = DATASET_DIR / f"{bkey}.csv"
    peak_cd = pd.read_csv(bldg_csv)['cooling_demand'].max()

    # nominal_power = capacidad electrica necesaria para cubrir pico a T_out_max
    nom_pwr = math.ceil(peak_cd / cop_worst * SAFETY_FACTOR)

    # Verificacion: max_thermal_output >= peak_cooling_demand
    max_th = nom_pwr * cop_worst
    margin = max_th - peak_cd
    check = f"+{margin:.1f}" if margin >= 0 else f"FAIL{margin:.1f}"

    bdata['cooling_device'] = {
        "type": "citylearn.energy_model.HeatPump",
        "autosize": False,
        "attributes": {
            "nominal_power": float(nom_pwr),
            "efficiency": eta,
            "target_cooling_temperature": T_TARGET_COOL,
        }
    }
    print(f"  {bid:>3}  {cop:>7.3f}  {cop_worst:>9.4f}  {eta:>8.6f}  {peak_cd:>9.2f}  {nom_pwr:>9.1f}  {check:>8}")

# ── Save ───────────────────────────────────────────────────────────────────────
with open(SCHEMA_PATH, 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print()
print("  schema.json guardado OK")
print(f"  Nota: nominal_power = ceil(peak_cooling_demand / COP_at_{T_OUT_MAX:.1f}degC * {SAFETY_FACTOR})")
print("=" * 70)
