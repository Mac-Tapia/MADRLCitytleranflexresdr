import ast
import json
from pathlib import Path


def test_colab_companion_reuses_setup_and_all_code_cells_compile():
    from tools.colab.build_modular_colab_notebook import build_notebook
    root = Path(__file__).resolve().parents[2]
    original = json.loads((root/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb').read_text(encoding='utf-8'))
    notebook = build_notebook(original, 'a'*64)
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            ast.parse(''.join(cell['source']))
    setup = next(''.join(cell['source']) for cell in original['cells']
                 if cell['cell_type'] == 'code' and '# 1.3 Instalar dependencias' in ''.join(cell['source']))
    assert setup in [''.join(cell['source']) for cell in notebook['cells']]
