"""
analyze_support_files.py
========================
Analiza todos los archivos de soporte del dataset CityLearn Iquitos 2023-2025:
  - charger_X_Y.csv (conteo dinamico desde el dataset activo)
  - carbon_intensity.csv
  - pricing.csv
  - Washing_Machine_X.csv por edificio
  - weather.csv
"""

import pandas as pd
from pathlib import Path

BASE = Path("CityLearn/data/datasets/citylearn_iquitos_2023_2025")
EXPECTED_ROWS = 26304

# ── 1. CHARGER FILES ─────────────────────────────────────────────────────────
print("=" * 80)
print("1. ANALISIS CHARGER_X_Y.CSV")
print("=" * 80)

charger_files = sorted(BASE.glob("charger_*.csv"))
print(f"  Total charger files encontrados: {len(charger_files)}")

issues_charger = []
summary = {}

for f in charger_files:
    df = pd.read_csv(f)
    rows = len(df)
    cols = list(df.columns)

    n_rows_ok = rows == EXPECTED_ROWS
    n_cols_ok = len(cols) == 6

    state_col = 'electric_vehicle_charger_state'
    if state_col in df.columns:
        n_sessions = int((df[state_col] == 1).sum())
        state_values = set(df[state_col].dropna().unique())
        state_ok = state_values.issubset({1, 2, 3, 1.0, 2.0, 3.0})
    else:
        n_sessions = -1
        state_ok = False

    soc_arr_col = 'electric_vehicle_estimated_soc_arrival'
    if soc_arr_col in df.columns:
        soc_vals = df[soc_arr_col].dropna()
        soc_range_ok = bool((soc_vals >= 0).all() and (soc_vals <= 1).all()) if len(soc_vals) > 0 else True
        soc_mean = float(soc_vals.mean()) if len(soc_vals) > 0 else 0
    else:
        soc_range_ok = False
        soc_mean = 0

    soc_req_col = 'electric_vehicle_required_soc_departure'
    if soc_req_col in df.columns:
        soc_req_vals = df[soc_req_col].dropna()
        soc_req_ok = bool((soc_req_vals >= 0).all() and (soc_req_vals <= 1).all()) if len(soc_req_vals) > 0 else True
    else:
        soc_req_ok = True

    ok = n_rows_ok and n_cols_ok and state_ok and soc_range_ok and soc_req_ok
    status = "OK" if ok else "REVISAR"
    if not ok:
        issues_charger.append((f.name, n_rows_ok, n_cols_ok, state_ok, soc_range_ok, soc_req_ok))

    session_pct = n_sessions / EXPECTED_ROWS * 100 if n_sessions >= 0 else 0
    summary[f.name] = {
        'rows': rows, 'cols': len(cols), 'sessions': n_sessions,
        'session_pct': round(session_pct, 1), 'soc_mean': round(soc_mean, 3),
        'status': status
    }

print(f"\n  {'Archivo':<22} {'Filas':>6} {'Cols':>5} {'Sesiones':>9} {'%Activo':>8} {'SOCprom':>8} {'Estado':>8}")
print("  " + "-" * 73)
for fname, s in summary.items():
    print(f"  {fname:<22} {s['rows']:>6} {s['cols']:>5} {s['sessions']:>9} {s['session_pct']:>7.1f}% {s['soc_mean']:>8.3f} {s['status']:>8}")

print(f"\n  Total archivos: {len(charger_files)}")
if issues_charger:
    print("  PROBLEMAS ENCONTRADOS:")
    for item in issues_charger:
        print(f"    {item}")
else:
    print("  Todos los charger files: OK")

# ── 2. CARBON_INTENSITY.CSV ───────────────────────────────────────────────────
print()
print("=" * 80)
print("2. CARBON_INTENSITY.CSV")
print("=" * 80)

ci_path = BASE / "carbon_intensity.csv"
if ci_path.exists():
    ci = pd.read_csv(ci_path)
    print(f"  Filas: {len(ci)} (esperado: {EXPECTED_ROWS}) → {'OK' if len(ci) == EXPECTED_ROWS else 'ERROR'}")
    print(f"  Columnas: {list(ci.columns)}")
    ci_col = ci.columns[0]
    print(f"  Columna principal: '{ci_col}'")
    print(f"  Min: {ci[ci_col].min():.4f}  Max: {ci[ci_col].max():.4f}  Mean: {ci[ci_col].mean():.4f}")
    print("  Rango esperado: 0.672 – 0.790 kg CO2/kWh (diesel Iquitos con solar)")
    in_range = (ci[ci_col] >= 0.60) & (ci[ci_col] <= 0.95)
    print(f"  Valores fuera de rango fisico [0.60-0.95]: {(~in_range).sum()}")
    nan_count = ci[ci_col].isna().sum()
    print(f"  NaN: {nan_count}")
    # Variacion horaria
    zero_count = (ci[ci_col] == 0).sum()
    print(f"  Valores == 0: {zero_count} {'(ERROR — no deberia haber ceros)' if zero_count > 0 else '(OK)'}")
    # Muestras
    print("\n  Muestra de valores (primeras 6 horas):")
    for i in range(6):
        print(f"    hora {i:02d}: {ci[ci_col].iloc[i]:.4f} kg CO2/kWh")
    print("\n  Muestra mediodía (hora 12):")
    print(f"    hora 12 (fila 12): {ci[ci_col].iloc[12]:.4f}")
    print(f"    hora 19 (punta): {ci[ci_col].iloc[19]:.4f}")
else:
    print("  ERROR: archivo no encontrado")

# ── 3. PRICING.CSV ───────────────────────────────────────────────────────────
print()
print("=" * 80)
print("3. PRICING.CSV")
print("=" * 80)

pr_path = BASE / "pricing.csv"
if pr_path.exists():
    pr = pd.read_csv(pr_path)
    print(f"  Filas: {len(pr)} (esperado: {EXPECTED_ROWS}) → {'OK' if len(pr) == EXPECTED_ROWS else 'ERROR'}")
    print(f"  Columnas ({len(pr.columns)}): {list(pr.columns)}")
    pr_col = pr.columns[0]
    print(f"\n  Columna principal: '{pr_col}'")
    print(f"  Min: {pr[pr_col].min():.4f}  Max: {pr[pr_col].max():.4f}  Mean: {pr[pr_col].mean():.4f}")
    nan_count = pr[pr_col].isna().sum()
    zero_count = (pr[pr_col] == 0).sum()
    print(f"  NaN: {nan_count}   Zeros: {zero_count}")

    # Verificar patron TOU: punta 18-22 deberia ser mayor
    # Construir hora del dia (0-23)
    horas = pr.index % 24
    punta_mask = (horas >= 18) & (horas < 23)
    fp_mask = ~punta_mask
    precio_punta = pr[pr_col][punta_mask].mean()
    precio_fp = pr[pr_col][fp_mask].mean()
    print(f"\n  Precio promedio PUNTA (18-22h): {precio_punta:.4f} USD/kWh")
    print(f"  Precio promedio FUERA PUNTA:    {precio_fp:.4f} USD/kWh")
    diferencial = (precio_punta - precio_fp) / precio_fp * 100
    print(f"  Diferencial punta/fp: {diferencial:.1f}%  (esperado ~46%)")

    print("\n  Muestra patron TOU horas 16-23 (fila 16-23 del dia 1):")
    for h in range(16, 24):
        print(f"    hora {h:02d}: {pr[pr_col].iloc[h]:.4f} USD/kWh  {'<-- PUNTA' if 18<=h<23 else ''}")
else:
    print("  ERROR: archivo no encontrado")

# ── 4. WASHING_MACHINE_X.CSV ─────────────────────────────────────────────────
print()
print("=" * 80)
print("4. WASHING_MACHINE_X.CSV")
print("=" * 80)

wm_files = sorted(BASE.glob("Washing_Machine_*.csv"))
print(f"  Total washing machine files encontrados: {len(wm_files)}")

if wm_files:
    wm_path = wm_files[0]
    wm = pd.read_csv(wm_path)
    print(f"  Muestra auditada: {wm_path.name}")
    print(f"  Filas: {len(wm)} (esperado: {EXPECTED_ROWS}) → {'OK' if len(wm) == EXPECTED_ROWS else 'ERROR'}")
    print(f"  Columnas ({len(wm.columns)}): {list(wm.columns)}")
    nan_total = wm.isna().sum().sum()
    print(f"  NaN total: {nan_total}")

    # Verificar columnas esperadas
    expected_cols = ['day_type', 'hour', 'wm_start_time_step', 'wm_end_time_step', 'load_profile']
    for col in expected_cols:
        if col in wm.columns:
            vals = wm[col].dropna()
            print(f"  {col}: min={vals.min():.2f} max={vals.max():.2f} nz={( vals != 0).sum()}")
        else:
            print(f"  {col}: FALTA")

    # Ciclos activos (load_profile distinto de lista vacia)
    if 'load_profile' in wm.columns:
        active = (~wm['load_profile'].astype(str).isin(["[]", "0", "0.0", "nan"])).sum()
        print(f"\n  Horas con ciclo activo (load_profile no vacio): {active}")

    print("\n  Muestra fila 1-3:")
    print(wm.head(3).to_string())
else:
    print("  ERROR: archivos Washing_Machine_X.csv no encontrados")

# ── 5. WEATHER.CSV ──────────────────────────────────────────────────────────
print()
print("=" * 80)
print("5. WEATHER.CSV")
print("=" * 80)

wth_path = BASE / "weather.csv"
if wth_path.exists():
    wth = pd.read_csv(wth_path)
    print(f"  Filas: {len(wth)} (esperado: {EXPECTED_ROWS}) → {'OK' if len(wth) == EXPECTED_ROWS else 'ERROR'}")
    print(f"  Columnas ({len(wth.columns)}): {len(wth.columns)} (esperado 16)")
    print(f"  Nombres: {list(wth.columns)}")
    nan_total = wth.isna().sum()
    print("\n  NaN por columna (top 5):")
    top_nan = nan_total.sort_values(ascending=False).head(5)
    for col, n in top_nan.items():
        print(f"    {col}: {n} NaN")

    # Temperatura exterior
    t_col = 'outdoor_dry_bulb_temperature'
    if t_col in wth.columns:
        print(f"\n  T_exterior: min={wth[t_col].min():.1f}C  max={wth[t_col].max():.1f}C  mean={wth[t_col].mean():.1f}C")
        print("  Esperado Iquitos: 24-33°C")

    # Irradiancia difusa
    dhi_col = 'diffuse_solar_irradiance'
    if dhi_col in wth.columns:
        print(f"\n  DHI: min={wth[dhi_col].min():.1f}  max={wth[dhi_col].max():.1f}  mean={wth[dhi_col].mean():.1f} W/m2")
        zero_dhi = (wth[dhi_col] == 0).sum()
        print(f"  DHI==0 horas: {zero_dhi} (esperado ~13000+ horas nocturnas)")

    # Irradiancia directa
    dni_col = 'direct_solar_irradiance'
    if dni_col in wth.columns:
        print(f"\n  DNI: min={wth[dni_col].min():.1f}  max={wth[dni_col].max():.1f}  mean={wth[dni_col].mean():.1f} W/m2")

    # Humedad relativa
    rh_col = 'outdoor_relative_humidity'
    if rh_col in wth.columns:
        print(f"\n  RH exterior: min={wth[rh_col].min():.1f}%  max={wth[rh_col].max():.1f}%  mean={wth[rh_col].mean():.1f}%")
        print("  Esperado Iquitos: 75-98%")

    # Verificar predicciones (shift)
    pred_cols = [c for c in wth.columns if '_predicted_' in c]
    print(f"\n  Columnas de prediccion: {len(pred_cols)} (esperado 12)")
    if pred_cols:
        nan_preds = wth[pred_cols].isna().sum()
        print("  NaN en predicciones:")
        for col, n in nan_preds.items():
            if n > 0:
                print(f"    {col}: {n} NaN")
        if nan_preds.sum() == 0:
            print("    Sin NaN (OK)")
else:
    print("  ERROR: archivo no encontrado")

print()
print("=" * 80)
print("ANALISIS COMPLETADO")
print("=" * 80)
