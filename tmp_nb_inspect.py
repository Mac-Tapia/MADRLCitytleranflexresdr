import json, io, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
nb = json.load(open(r'CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb', encoding='utf-8'))
cells = nb['cells']
out = []
out.append('TOTAL CELLS: %d' % len(cells))
for i, c in enumerate(cells):
    src = ''.join(c['source'])
    preview = src[:240].replace('\n', ' | ')
    out.append(f'--- [{i}] {c["cell_type"]} ({len(c["source"])} lines) ---')
    out.append(preview)
open('tmp_nb_cells.txt','w',encoding='utf-8').write('\n'.join(out))
print('done')
