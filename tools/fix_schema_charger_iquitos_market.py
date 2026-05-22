"""
fix_schema_charger_iquitos_market.py
=====================================
Actualiza las potencias de los 30 cargadores de vehículos ligeros (charger_type=0)
según el mercado real de movilidad eléctrica de Iquitos, Perú.

Mercado real Iquitos (dato confirmado por usuario):
  - Motolineal eléctrica : cargador 3 kW (uso personal/institucional)
  - Mototaxi eléctrico   : cargador 4 kW (transporte público urbano)

Clasificación por edificio:
  4 kW MOTOTAXI (acceso público, visitantes, usuarios de transporte):
    B2  Complejo Champios    — aficionados deportivos
    B4  Hiperbodega          — clientes retail
    B5  Hotel El Dorado      — huéspedes
    B6  Mall Aventura        — clientes mall
    B9  Complejo CNI         — aficionados estadio
    B15 Colegio CNI          — alumnos/padres

  3 kW MOTOLINEAL (personal institucional, docentes, staff salud/académico):
    B3  Aeropuerto           — personal de operaciones
    B7  UNAP Zungarococha    — docentes/investigadores
    B11 Hospital Regional    — personal médico/admin
    B12 EsSalud Hospital III — personal médico/admin
    B13 Facultad FACEN UNAP  — docentes/alumnos
    B16 I.E. San Juan        — docentes/personal
    B17 IEST Pedro del Águila — docentes/alumnos técnicos

Mínimo de carga (IEC 61851-1 Modo 3 para todos):
  min_charging_power = 6 A × 230 V = 1.38 kW
  (aplica igual a 3 kW y 4 kW — mismo protocolo Mode 3)

Los cargadores charger_type=1 (7.4 kW bidireccional V2G) NO se modifican.
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

SCHEMA_PATH = Path(
    r"d:\MADRLCitytleranflexresdr\CityLearn\data\datasets"
    r"\citylearn_iquitos_2023_2025\schema.json"
)

# ── Potencias mercado Iquitos ─────────────────────────────────────────────────
KW_MOTOTAXI   = 4.0    # mototaxi eléctrico (transporte público urbano)
KW_MOTOLINEAL = 3.0    # motolineal / moto personal eléctrica
MIN_MODE3_KW  = round(6 * 230 / 1000, 3)   # 1.38 kW — IEC 61851-1 Modo 3 (6 A mín.)

# ── Asignación de potencia por edificio (solo charger_type=0) ─────────────────
# Formato: {bldg_id: kW_por_cargador_ligero}
LIGHT_CHARGER_POWER = {
    # 4 kW mototaxi — usuarios transporte público / visitantes
    2:  KW_MOTOTAXI,    # Complejo Champios (deportivo)
    4:  KW_MOTOTAXI,    # Hiperbodega Precio UNO (retail)
    5:  KW_MOTOTAXI,    # Hotel El Dorado (hotelero)
    6:  KW_MOTOTAXI,    # Mall Aventura (mall)
    9:  KW_MOTOTAXI,    # Complejo CNI (estadio)
    15: KW_MOTOTAXI,    # Colegio CNI (educación pública)
    # 3 kW motolineal — personal institucional / docentes / staff
    3:  KW_MOTOLINEAL,  # Aeropuerto (personal operaciones)
    7:  KW_MOTOLINEAL,  # UNAP Zungarococha (docentes)
    11: KW_MOTOLINEAL,  # Hospital Regional (personal médico)
    12: KW_MOTOLINEAL,  # EsSalud Hospital III (personal médico)
    13: KW_MOTOLINEAL,  # Facultad Economía UNAP (docentes/alumnos)
    16: KW_MOTOLINEAL,  # I.E. San Juan (docentes)
    17: KW_MOTOLINEAL,  # IEST Pedro del Águila (docentes/alumnos técnicos)
}

with open(SCHEMA_PATH, encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 76)
print("ACTUALIZACIÓN CARGADORES VEHÍCULOS LIGEROS — Mercado Real Iquitos, Perú")
print(f"  Mototaxi eléctrico (acceso público) : {KW_MOTOTAXI} kW")
print(f"  Motolineal / personal institucional : {KW_MOTOLINEAL} kW")
print(f"  Mínimo IEC 61851-1 Modo 3           : {MIN_MODE3_KW} kW  (6 A × 230 V)")
print("=" * 76)

header = (f"  {'Cargador':<18}  {'tipo':>4}  {'ant.kW':>6} → {'nuevo.kW':>8}"
          f"  {'min_ch':>7}  {'max_dch':>7}  {'estado':>12}")
print(header)
print("  " + "-" * 72)

total = 0
updated = 0
skipped_v2g = 0
errors = []

for bkey in sorted(schema['buildings'].keys(), key=lambda k: int(k.split('_')[1])):
    bid   = int(bkey.split('_')[1])
    bdata = schema['buildings'][bkey]

    for ckey, cval in bdata.get('chargers', {}).items():
        at = cval['attributes']
        ct = at['charger_type']
        total += 1

        if ct == 1:
            # V2G bidireccional 7.4 kW — NO se modifica
            skipped_v2g += 1
            continue

        # Cargador ligero (charger_type=0)
        if bid not in LIGHT_CHARGER_POWER:
            errors.append(f"  AVISO: {ckey} (B{bid}) charger_type=0 no en LIGHT_CHARGER_POWER")
            continue

        new_kw   = LIGHT_CHARGER_POWER[bid]
        old_kw   = at['nominal_power']

        at['nominal_power']         = new_kw
        at['max_charging_power']    = new_kw
        at['min_charging_power']    = MIN_MODE3_KW   # 1.38 kW IEC 61851-1 Modo 3
        at['max_discharging_power'] = 0.0            # unidireccional → sin descarga
        at['min_discharging_power'] = 0.0

        status = "ACTUALIZADO" if abs(old_kw - new_kw) > 1e-6 else "SIN_CAMBIO"
        if abs(old_kw - new_kw) > 1e-6:
            updated += 1

        print(f"  {ckey:<18}  {ct:>4}  {old_kw:>6.1f} → {new_kw:>8.1f} kW"
              f"  {MIN_MODE3_KW:>7.3f}  {0.0:>7.1f}  {status:>12}")

print("  " + "-" * 72)

if errors:
    for msg in errors:
        print(msg)

print(f"\n  RESUMEN:")
print(f"    Total cargadores en schema  : {total}")
print(f"    V2G bidireccionales (7.4 kW): {skipped_v2g}  → sin cambio")
print(f"    Cargadores ligeros actualizados: {updated}")
print(f"    Mototaxi  4 kW (acceso público)  : B2×4, B4×3, B5×2, B6×5, B9×2, B15×2 = 18")
print(f"    Motolineal 3 kW (institucional)  : B3×2, B7×2, B11×2, B12×1, B13×2, B16×1, B17×2 = 12")
print(f"    Total vehículos ligeros          : 30  ✓")

# ── Guardar schema ────────────────────────────────────────────────────────────
with open(SCHEMA_PATH, 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print(f"\n  schema.json guardado OK")
print("=" * 76)
