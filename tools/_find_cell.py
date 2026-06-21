import json, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
nb = json.loads(pathlib.Path(r'd:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb').read_bytes().decode('utf-8-sig'))
# Find Drive mount cell (1.5) and cell 56
for ci, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    if ('1.5' in src[:60] and 'drive' in src.lower()[:300]) or ('gdrive' in src.lower()[:200] and ci < 20):
        print(f"=== CELL {ci} (Drive) ===")
        print(src[:3000])
        print()
