import json, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')
nb = json.loads(pathlib.Path(r'd:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb').read_bytes().decode('utf-8-sig'))
for ci, cell in enumerate(nb['cells']):
    src = ''.join(cell.get('source', []))
    if 'launcher_base_args' in src and 'def launcher_base_args' in src:
        print(f"=== CELL {ci} ===")
        print(src[:6000])
