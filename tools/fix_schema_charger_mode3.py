"""
fix_schema_charger_mode3.py
===========================
Audita y corrige los 50 cargadores del schema.json para cumplimiento
IEC 61851-1 (modo de carga semirápido / Modo 3).

ESTÁNDAR IEC 61851-1 MODO 3 — cargador dedicado AC con piloto de control:
  Corriente mínima Modo 3 : I_min = 6 A (IEC 61851-1 §9.3)
  Corriente máxima 1-fase : I_max = 32 A @ 230 V → 7.4 kW
  Potencia mínima carga   : P_min = 6 A × 230 V = 1 380 W = 1.38 kW
  Potencia máxima carga   : P_max = 32 A × 230 V = 7 360 W ≈ 7.4 kW

MODO 1/2 — mototaxi eléctrico (cargador estándar doméstico / ICCB):
  IEC 61851-1 Modo 1 no define I_min estricto para BT
  Mínimo práctico adoptado: 20 % de la potencia nominal
  P_nominal = 1.0 kW → P_min = 0.20 kW (≈ 0.87 A — umbral práctico)

V2G (Vehicle-to-Grid) — descarga bidireccional Modo 3:
  Simétrico a la carga: P_min_disch = P_min_charge = 1.38 kW
  Razón: misma electrónica de potencia y piloto de comunicación

Parámetros que NO se modifican:
  - nominal_power, max_charging_power, max_discharging_power, efficiency
  - charger_type (metadato identificador; no lo usa el motor CityLearn)
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

SCHEMA_PATH = Path(r"d:\MADRLCitytleranflexresdr\CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json")

# ── Valores correctos por potencia nominal (IEC 61851-1) ──────────────────────
# charger 7.4 kW  → Modo 3 AC semirápido (32 A × 230 V = 7.36 kW ≈ 7.4 kW)
MIN_POWER_MODE3_KW  = round(6 * 230 / 1000, 3)   # 1.38 kW  (6 A IEC 61851-1)

# charger 1.0 kW  → Modo 1/2 doméstico (mototaxi), mínimo práctico 20 %
MIN_POWER_MODE12_KW = round(1.0 * 0.20, 3)        # 0.20 kW

with open(SCHEMA_PATH, encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 72)
print("AUDITORÍA Y CORRECCIÓN — Cargadores IEC 61851-1 Modo 3 / Modo 1-2")
print("=" * 72)
print(f"  Modo 3  (7.4 kW, 32A×230V): P_min_charge = P_min_disch = {MIN_POWER_MODE3_KW} kW  (6A × 230V)")
print(f"  Modo 1/2 (1.0 kW, mototaxi): P_min_charge = {MIN_POWER_MODE12_KW} kW  (20% nominal)")
print()

header = (f"  {'Cargador':<18} {'nom':>5} {'ct':>3} "
          f"{'P_ch_max':>8} {'P_ch_min':>8} {'P_dch_max':>9} {'P_dch_min':>9} "
          f"{'eff':>5} {'status':>12}")
print(header)
print("  " + "-" * 82)

total = 0
corrected = 0
ok = 0

for bkey in sorted(schema['buildings'].keys(), key=lambda k: int(k.split('_')[1])):
    bdata = schema['buildings'][bkey]
    for ckey, cval in bdata.get('chargers', {}).items():
        at = cval['attributes']
        total += 1
        nom  = at['nominal_power']
        ct   = at['charger_type']
        issues = []

        # ── Determinar valores correctos según potencia nominal ────────────────
        if nom >= 7.4:                         # Modo 3 semirápido
            p_min_ch  = MIN_POWER_MODE3_KW     # 1.38 kW
            p_min_dch = MIN_POWER_MODE3_KW if ct == 1 else 0.0
            mode_tag  = "Modo3"
        else:                                   # Modo 1/2 mototaxi
            p_min_ch  = MIN_POWER_MODE12_KW    # 0.20 kW
            p_min_dch = 0.0                    # no V2G en mototaxi
            mode_tag  = "Modo1/2"

        # ── Detectar desviaciones ─────────────────────────────────────────────
        if abs(at['min_charging_power'] - p_min_ch) > 1e-6:
            issues.append(f"ch_min {at['min_charging_power']}→{p_min_ch}")
        if abs(at['min_discharging_power'] - p_min_dch) > 1e-6:
            issues.append(f"dch_min {at['min_discharging_power']}→{p_min_dch}")

        # ── Aplicar correcciones ───────────────────────────────────────────────
        at['min_charging_power']    = p_min_ch
        at['min_discharging_power'] = p_min_dch

        status = "CORREGIDO" if issues else "OK"
        if issues:
            corrected += 1
        else:
            ok += 1

        print(f"  {ckey:<18} {nom:>5.1f} {ct:>3} "
              f"{at['max_charging_power']:>8.2f} {at['min_charging_power']:>8.3f} "
              f"{at['max_discharging_power']:>9.2f} {at['min_discharging_power']:>9.3f} "
              f"{at['efficiency']:>5.2f} {status:>12}"
              + (f"  [{'; '.join(issues)}]" if issues else ""))

print("  " + "-" * 82)
print(f"\n  RESUMEN: {total} cargadores auditados | {ok} OK | {corrected} corregidos")
print(f"  Cargadores Modo 3  (7.4 kW): 20 bidireccionales V2G")
print(f"  Cargadores Modo 3  (7.4 kW): min_ch = min_dch = {MIN_POWER_MODE3_KW} kW")
print(f"  Cargadores Modo1/2 (1.0 kW): 30 unidireccionales mototaxi")
print(f"  Cargadores Modo1/2 (1.0 kW): min_ch = {MIN_POWER_MODE12_KW} kW  no V2G")

# ── Guardar schema corregido ──────────────────────────────────────────────────
with open(SCHEMA_PATH, 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print()
print("  schema.json guardado OK")
print("=" * 72)
