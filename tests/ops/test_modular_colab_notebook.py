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
    copied = [source for source in (''.join(cell['source']) for cell in notebook['cells']) if setup in source]
    assert len(copied) == 1


def test_copied_setup_cell_imports_every_stdlib_module_it_uses():
    # In the tutorial an earlier cell imports some modules; the companion runs
    # the setup cell on its own, so it must be self-contained (e.g. platform).
    from tools.colab.build_modular_colab_notebook import STDLIB_MODULES, build_notebook
    root = Path(__file__).resolve().parents[2]
    original = json.loads((root/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb').read_text(encoding='utf-8'))
    notebook = build_notebook(original, 'a'*64)
    setup = next(''.join(cell['source']) for cell in notebook['cells']
                 if cell['cell_type'] == 'code' and '# 1.3 Instalar dependencias' in ''.join(cell['source']))
    tree = ast.parse(setup)
    imported = {alias.asname or alias.name.split('.')[0] for node in ast.walk(tree)
                if isinstance(node, (ast.Import, ast.ImportFrom)) for alias in node.names}
    imported |= {node.module.split('.')[0] for node in ast.walk(tree)
                 if isinstance(node, ast.ImportFrom) and node.module}
    used = {node.value.id for node in ast.walk(tree)
            if isinstance(node, ast.Attribute) and isinstance(node.value, ast.Name)}
    assert (used & STDLIB_MODULES) - imported == set()


def test_notebook_records_the_dataset_digest_it_expects():
    from tools.colab.build_modular_colab_notebook import build_notebook
    root = Path(__file__).resolve().parents[2]
    original = json.loads((root/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb').read_text(encoding='utf-8'))
    assert build_notebook(original, 'b'*64)['metadata']['expected_dataset_sha256'] == 'b'*64
