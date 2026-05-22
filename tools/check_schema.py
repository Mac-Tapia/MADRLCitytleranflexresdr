import json
import pandas as pd
import numpy as np
from pathlib import Path

BASE = Path('CityLearn/data/datasets/citylearn_iquitos_2023_2025')

with open(BASE / 'schema.json') as f:
    schema = json.load(f)

buildings = schema['buildings']
print("Total buildings en schema.json:", len(buildings))
print()

# Compute actual max cooling_demand from each Building CSV
print("%-30s %8s %8s %8s %8s %s" % ("Building", "NomPow", "MaxCD", "Ratio", "Autosize", "Status"))
print("-" * 80)

all_ok = True
for b in buildings:
    name = b['name']
    bfile = BASE / b['energy_simulation']
    cd = b.get('cooling_device', {})

    nom_pow = cd.get('nominal_power', None)
    autosize = cd.get('autosize', False)

    if bfile.exists():
        df = pd.read_csv(bfile)
        max_cd = df['cooling_demand'].max() if 'cooling_demand' in df.columns else 0
    else:
        max_cd = 0

    if nom_pow is not None and not autosize:
        ratio = max_cd / nom_pow if nom_pow > 0 else 999
        ok = ratio <= 1.0
        status = "OK" if ok else "ERROR demand>capacity"
        if not ok:
            all_ok = False
    else:
        ratio = 0
        status = "AUTOSIZE" if autosize else "NO_CD"

    print("%-30s %8s %8.1f %8.2f %8s  %s" % (
        name, str(nom_pow), max_cd, ratio, str(autosize), status))

print()
print("Schema.json cooling devices ALL OK:", all_ok)
print()

# Check first building detail
b0 = buildings[0]
print("Detalle del primer edificio:")
print(json.dumps({
    'name': b0['name'],
    'cooling_device': b0.get('cooling_device', 'NOT FOUND'),
    'electrical_storage': b0.get('electrical_storage', 'NOT FOUND'),
    'pv_system': b0.get('pv_system', 'NOT FOUND')
}, indent=2))
