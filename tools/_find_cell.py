import json, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
nb = json.loads(pathlib.Path(r'd:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb').read_bytes().decode('utf-8-sig'))
ci = 40
src = ''.join(nb['cells'][ci].get('source', []))
print(src)
