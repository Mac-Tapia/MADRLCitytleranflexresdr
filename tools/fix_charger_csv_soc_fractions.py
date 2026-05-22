"""
fix_charger_csv_soc_fractions.py
=================================
Convierte los valores SOC en los 50 archivos charger_X_Y.csv de porcentaje
(0–100) a fracción (0.0–1.0) tal como exige CityLearn v2.

Referencia CityLearn (runtime.py línea 269):
    if 0.0 <= candidate <= 1.0:
        soc_value = float(candidate)   # solo acepta fracciones

Columnas afectadas por archivo:
    electric_vehicle_estimated_soc_arrival    → dividir /100
    electric_vehicle_required_soc_departure   → dividir /100

Columnas NO modificadas:
    electric_vehicle_charger_state            (0/1 — sin cambio)
    electric_vehicle_id                       (ID numérico — sin cambio)
    electric_vehicle_departure_time           (hora 0–23 — sin cambio)
    electric_vehicle_estimated_arrival_time   (hora 0–23 — sin cambio)
"""
import sys, pandas as pd, numpy as np
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DATASET_DIR = Path(
    r"d:\MADRLCitytleranflexresdr\CityLearn\data\datasets"
    r"\citylearn_iquitos_2023_2025"
)
SOC_COLS = [
    'electric_vehicle_estimated_soc_arrival',
    'electric_vehicle_required_soc_departure',
]

csv_files = sorted(DATASET_DIR.glob('charger_*.csv'))

print("=" * 70)
print("CONVERSIÓN SOC: porcentaje → fracción — 50 archivos charger_X_Y.csv")
print("  Divisor: /100 para columnas SOC con valores > 1.0")
print("=" * 70)
print(f"  {'Archivo':<22}  {'soc_arr antes':>13}  {'soc_arr después':>15}"
      f"  {'soc_req antes':>13}  {'soc_req después':>15}")
print("  " + "-" * 85)

fixed = 0
already_ok = 0
errors = []

for csv_path in csv_files:
    try:
        df = pd.read_csv(csv_path)

        # Verificar que existen las columnas SOC
        missing = [c for c in SOC_COLS if c not in df.columns]
        if missing:
            errors.append(f"  AVISO {csv_path.name}: faltan columnas {missing}")
            continue

        # Detectar si necesita conversión (máximo > 1.0 implica porcentaje)
        arr_max = df[SOC_COLS[0]].max(skipna=True)
        req_max = df[SOC_COLS[1]].max(skipna=True)

        needs_fix = (arr_max > 1.0) or (req_max > 1.0)

        arr_before = f"[{df[SOC_COLS[0]].min(skipna=True):.1f},{arr_max:.1f}]"
        req_before = f"[{df[SOC_COLS[1]].min(skipna=True):.1f},{req_max:.1f}]"

        if needs_fix:
            for col in SOC_COLS:
                df[col] = (df[col] / 100.0).round(4)
            df.to_csv(csv_path, index=False)
            fixed += 1
            status = "CONVERTIDO"
        else:
            already_ok += 1
            status = "OK"

        arr_after = f"[{df[SOC_COLS[0]].min(skipna=True):.3f},{df[SOC_COLS[0]].max(skipna=True):.3f}]"
        req_after = f"[{df[SOC_COLS[1]].min(skipna=True):.3f},{df[SOC_COLS[1]].max(skipna=True):.3f}]"

        print(f"  {csv_path.name:<22}  {arr_before:>13}  {arr_after:>15}"
              f"  {req_before:>13}  {req_after:>15}  {status}")

    except Exception as e:
        errors.append(f"  ERROR {csv_path.name}: {e}")

print("  " + "-" * 85)
if errors:
    for msg in errors:
        print(msg)

print(f"\n  RESUMEN:")
print(f"    Archivos convertidos  : {fixed}")
print(f"    Archivos ya correctos : {already_ok}")
print(f"    Total procesados      : {fixed + already_ok}")
print(f"\n  Formato correcto para CityLearn: SOC ∈ [0.0, 1.0]")
print("=" * 70)
