"""
size_bess_optimal.py  (v2 — ventana diaria correcta)
=====================================================
Dimensiona BESS por edificio con balance energético real usando ventana
de 24 h (Hesse et al. 2017).

Problema con cumsum multi-año:
  Si load >> solar de forma continua, cumsum diverge → BESS irreal de GWh.
  Solución: aplicar cumsum dentro de cada día (24 h) y tomar el percentil 90
  de las excursiones diarias como E_raw.  Esto capta el peor día típico de
  almacenamiento solar sin acumular el déficit estructural de 3 años.

Fórmula por día d (Hesse et al. 2017 §3, adaptado ventana diaria):
  p_net[d,h]  = load_elec[d,h] - solar[d,h]
  surplus[d,h]= max(0, -p_net)   → excedente PV → carga BESS
  deficit[d,h]= max(0,  p_net)   → déficit carga → descarga BESS
  soc_d       = cumsum(surplus×η_c - deficit/η_d)  dentro del día d
  excursion_d = soc_d.max() - soc_d.min()          swing diario [kWh]

Sizing final:
  E_raw  = percentil 90 de excursion_d  (peor día típico, excluye outliers)
  E_bess = ceil(E_raw / DOD)
  P_bess = percentil 99 de |p_net|      (potencia pico, para carga y descarga)

Parámetros LFP fijos (Li-ion LFP CATL/BYD):
  DOD = 0.80   η_c = η_d = 0.95   η_RT = 0.9025
  loss_coeff = 1e-5   initial_soc = 0.50
"""
import json, sys, math
import numpy as np
import pandas as pd
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

DATASET_DIR = Path(r"d:\MADRLCitytleranflexresdr\CityLearn\data\datasets\citylearn_iquitos_2023_2025")
SCHEMA_PATH  = DATASET_DIR / "schema.json"
WEATHER_PATH = DATASET_DIR / "weather.csv"

# ── Parámetros LFP ────────────────────────────────────────────────────────────
DOD       = 0.80
ETA_C     = 0.95
ETA_D     = 0.95
ETA_RT    = round(ETA_C * ETA_D, 6)   # 0.9025
LOSS      = 1e-5
SOC_INI   = 0.50
COP_ACS   = 0.85          # ACS: calefón eléctrico (B5, B11, B12)
T_TARGET  = 8.5           # temperatura objetivo enfriamiento [°C]
PERC_EXCURSION = 90       # percentil diario para E_raw (p90 = peor día típico)
PERC_POWER     = 99       # percentil horario para P_nom (p99 = pico robusto)

weather = pd.read_csv(WEATHER_PATH)
T_out   = weather['outdoor_dry_bulb_temperature'].values   # 26 304 valores
schema  = json.load(open(SCHEMA_PATH, encoding='utf-8'))

print("=" * 82)
print("SIZING ÓPTIMO BESS — Balance Energético Diario (Hesse et al. 2017, ventana 24h)")
print(f"  DOD={DOD}  η_c={ETA_C}  η_d={ETA_D}  η_RT={ETA_RT}")
print(f"  E_raw = P{PERC_EXCURSION} excursión diaria | P_nom = P{PERC_POWER} |p_net| horario")
print("=" * 82)
print(f"\n  {'B':>3}  {'E_raw kWh':>10}  {'E_bess kWh':>10}  {'P_nom kW':>9}"
      f"  {'solar avg':>9}  {'load avg':>9}  {'PV/load%':>8}  {'#días':>5}")
print("  " + "-" * 77)

results = {}

for bkey in sorted(schema['buildings'].keys(), key=lambda k: int(k.split('_')[1])):
    bid   = int(bkey.split('_')[1])
    bdata = schema['buildings'][bkey]

    df    = pd.read_csv(DATASET_DIR / f"{bkey}.csv")
    nsl   = df['non_shiftable_load'].values      # kWh_elec/h
    cd    = df['cooling_demand'].values           # kWh_term/h
    dhw   = df['dhw_demand'].values               # kWh_term/h
    solar = df['solar_generation'].values         # kWh_elec/h

    # COP Carnot horario usando η del schema
    cd_dev = bdata.get('cooling_device', {})
    if cd_dev and cd_dev.get('attributes'):
        eta_carnot = cd_dev['attributes']['efficiency']
        cop_act = (T_TARGET + 273.15) * eta_carnot / (T_out - T_TARGET)
        cop_act = np.clip(cop_act, 0.5, 10.0)
    else:
        cop_act = np.full(len(df), 2.5)

    # Demanda eléctrica total horaria
    load_elec = nsl + cd / cop_act + dhw / COP_ACS
    load_elec = np.clip(load_elec, 0, None)

    # Balance neto horario
    p_net   = load_elec - solar
    surplus = np.clip(-p_net, 0, None)
    deficit = np.clip( p_net, 0, None)

    # ── Cumsum POR DÍA (24 h) — excursión SOC diaria ─────────────────────────
    n_hours = len(p_net)
    n_days  = n_hours // 24
    excursions = np.empty(n_days)
    for d in range(n_days):
        s = d * 24; e = s + 24
        soc_d = np.cumsum(surplus[s:e] * ETA_C - deficit[s:e] / ETA_D)
        excursions[d] = soc_d.max() - soc_d.min()

    # E_raw = percentil 90 de excursiones diarias
    E_raw  = float(np.percentile(excursions, PERC_EXCURSION))
    E_bess = math.ceil(E_raw / DOD)           # kWh (siempre entero)

    # P_nom = percentil 99 de |p_net| horario  (kW)
    P_nom  = math.ceil(float(np.percentile(np.abs(p_net), PERC_POWER)))

    # Mínimo operativo razonable
    E_bess = max(E_bess, 10)     # mín 10 kWh
    P_nom  = max(P_nom,  5)      # mín 5 kW

    solar_avg  = solar.mean()
    load_avg   = load_elec.mean()
    pv_ratio   = solar_avg / load_avg * 100 if load_avg > 0 else 0

    results[bkey] = {'E_bess': float(E_bess), 'P_nom': float(P_nom)}

    print(f"  {bid:>3}  {E_raw:>10.1f}  {E_bess:>10.0f}  {P_nom:>9.0f}"
          f"  {solar_avg:>9.2f}  {load_avg:>9.2f}  {pv_ratio:>8.1f}%  {n_days:>5}")

print("  " + "-" * 77)

# ── Actualizar schema.json ────────────────────────────────────────────────────
print("\nActualizando schema.json...")
print(f"\n  {'B':>3}  {'Capacidad anterior':>20}  {'→':>2}  {'Capacidad nueva':>15}  "
      f"{'P anterior':>12}  {'→':>2}  {'P nueva':>10}")
print("  " + "-" * 75)

for bkey, res in results.items():
    bid   = int(bkey.split('_')[1])
    bdata = schema['buildings'][bkey]
    old   = bdata.get('electrical_storage', {}).get('attributes', {})
    old_c = old.get('capacity', 0)
    old_p = old.get('nominal_power', 0)

    bdata['electrical_storage'] = {
        "type": "citylearn.energy_model.Battery",
        "autosize": False,
        "attributes": {
            "capacity":                  res['E_bess'],
            "nominal_power":             res['P_nom'],
            "depth_of_discharge":        DOD,
            "efficiency":                ETA_RT,
            "capacity_loss_coefficient": LOSS,
            "loss_coefficient":          0.0,
            "initial_soc":               SOC_INI,
        }
    }
    print(f"  {bid:>3}  {old_c:>18.1f} kWh  →  {res['E_bess']:>13.0f} kWh  "
          f"{old_p:>10.1f} kW  →  {res['P_nom']:>8.0f} kW")

json.dump(schema, open(SCHEMA_PATH, 'w', encoding='utf-8'),
          indent=2, ensure_ascii=False)

print(f"\n  schema.json guardado — {len(results)} edificios actualizados")
print("=" * 82)
