"""Fix MATD3 replay_buffer_size in cell 32."""
import json, pathlib, sys
sys.stdout.reconfigure(encoding='utf-8')

NB_PATH = pathlib.Path(
    r'd:/MADRLCitytleranflexresdr/CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb'
)
nb = json.loads(NB_PATH.read_bytes().decode('utf-8-sig'))
src = ''.join(nb['cells'][32]['source'])

old = '        "replay_buffer_size": 1_000_000, # transiciones (~6 GiB RAM con 167GiB disponibles, 114 episodios diversidad)'
new = '        "replay_buffer_size": 2_000_000, # transiciones (~14 GiB RAM/instancia; 3x42=42 GiB total << 167 GiB; 228 ep diversidad)'

if old in src:
    src = src.replace(old, new, 1)
    print('OK: MATD3 replay_buffer_size 1M → 2M')
else:
    print('NOTFOUND')

lines = src.split('\n')
nb['cells'][32]['source'] = [l + '\n' for l in lines[:-1]] + ([lines[-1]] if lines[-1] else [])
NB_PATH.write_text(json.dumps(nb, ensure_ascii=False, indent=1), encoding='utf-8')
print('Guardado.')
