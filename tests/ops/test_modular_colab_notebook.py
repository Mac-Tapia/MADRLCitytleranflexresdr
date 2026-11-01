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


def test_campaign_cell_takes_seeds_from_the_campaign_config():
    from tools.colab.build_modular_colab_notebook import build_notebook
    root = Path(__file__).resolve().parents[2]
    original = json.loads((root/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb').read_text(encoding='utf-8'))
    sources = [''.join(cell['source']) for cell in build_notebook(original, 'a'*64)['cells']]
    campaign = next(source for source in sources if 'uc3m.application.training.colab' in source)
    assert 'configs/experiments/full_campaign_4x3x3.yaml' in campaign
    assert "CAMPAIGN['seeds']" in campaign
    assert 'SEEDS = [0]' not in campaign
    launch_doc = next(source for source in sources if source.startswith('## 5.'))
    assert 'Fase 1:** HAPPO + MASAC' in launch_doc and 'Fase 2:** MATD3 + MAAC' in launch_doc


def test_notebook_records_the_dataset_digest_it_expects():
    from tools.colab.build_modular_colab_notebook import build_notebook
    root = Path(__file__).resolve().parents[2]
    original = json.loads((root/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb').read_text(encoding='utf-8'))
    assert build_notebook(original, 'b'*64)['metadata']['expected_dataset_sha256'] == 'b'*64
