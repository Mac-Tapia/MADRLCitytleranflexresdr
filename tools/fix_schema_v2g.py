"""
fix_schema_v2g.py
=================
Corrige max_discharging_power / min_discharging_power para chargers
bidireccionales (charger_type=1) en schema.json.

- charger_type 0 (mototaxi unidireccional, 1.0 kW):
    max_discharging_power = 0.0   ← correcto, no cambia

- charger_type 1 (camioneta V2G, 7.4 kW):
    max_discharging_power = nominal_power (7.4 kW)
    min_discharging_power = 0.96 kW   (mismo umbral minimo que carga)

La proteccion contra danio de bateria en CityLearn la provee:
  - EV.depth_of_discharge  (limita cuanto se puede descargar)
  - electric_vehicle_required_soc_departure en charger CSV (SOC minimo al partir)
  El agente MADRL aprende a respetar estas restricciones via reward penalty.
"""
import json, sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

SCHEMA_PATH = Path(r"d:\MADRLCitytleranflexresdr\CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json")

with open(SCHEMA_PATH, encoding='utf-8') as f:
    schema = json.load(f)

print("=" * 65)
print("FIX V2G — max_discharging_power para cargadores bidireccionales")
print("=" * 65)

fixed = 0
for bkey, bdata in schema['buildings'].items():
    for ckey, cval in bdata.get('chargers', {}).items():
        at = cval['attributes']
        ct = at['charger_type']
        nom = at['nominal_power']

        if ct == 1:  # bidireccional V2G
            old_disch = at['max_discharging_power']
            at['max_discharging_power'] = nom       # = 7.4 kW
            at['min_discharging_power'] = 0.96      # umbral minimo (igual que min_charging)
            print(f"  {ckey}: max_disch {old_disch} -> {nom} kW  min_disch 0.0 -> 0.96 kW")
            fixed += 1
        # charger_type 0 no cambia (0.0 es correcto para unidireccional)

print()
print(f"  Cargadores bidireccionales corregidos: {fixed} (charger_type=1, 7.4 kW)")
print(f"  Cargadores unidireccionales sin cambio: {50 - fixed} (charger_type=0, 1.0 kW)")

with open(SCHEMA_PATH, 'w', encoding='utf-8') as f:
    json.dump(schema, f, indent=2, ensure_ascii=False)

print()
print("  schema.json guardado OK")
print("=" * 65)
