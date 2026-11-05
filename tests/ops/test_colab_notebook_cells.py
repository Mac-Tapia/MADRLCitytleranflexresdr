"""Cell-by-cell contract of the modular Colab notebook (plan docs/plans/cuaderno_colab.md).

The notebook is built in memory from tools/colab/build_modular_colab_notebook.py, never
read from a hand-edited .ipynb. Code cells are located by their marker ``# [Cn] <title>``
(C1..C11). These tests define what an operational cell must do; the generator owner makes
them pass (Tasks 2-6, 8, 9 of the plan).
"""
import ast
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.colab import build_modular_colab_notebook as builder  # noqa: E402

MARKER = re.compile(r'^# \[C(\d+)\] ')
CONFIG = REPO/'configs/experiments/iquitos.yaml'


def _source(cell):
    return ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']


@pytest.fixture(scope='module')
def notebook():
    campaign = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    acceptance = json.loads((REPO/campaign['dataset_root']/'dataset_acceptance.json').read_text(encoding='utf-8'))
    original = json.loads(builder.ORIGINAL.read_text(encoding='utf-8'))
    return builder.build_notebook(original, acceptance['dataset_hash'])


@pytest.fixture(scope='module')
def cells(notebook):
    found = {}
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            match = MARKER.match(_source(cell))
            if match:
                found[f'C{match.group(1)}'] = _source(cell)
    # Without the 11 marked cells every per-cell check below would pass vacuously.
    assert sorted(found, key=lambda m: int(m[1:])) == [f'C{n}' for n in range(1, 12)], \
        f'marked code cells found: {sorted(found)}'
    return found


def _markdown_before(notebook, marker):
    previous = None
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code' and _source(cell).startswith(f'# [{marker}] '):
            return previous or ''
        if cell['cell_type'] == 'markdown':
            previous = _source(cell)
    return ''


def _calls(source):
    tree = ast.parse(source)
    return {node.func.attr if isinstance(node.func, ast.Attribute) else getattr(node.func, 'id', '')
            for node in ast.walk(tree) if isinstance(node, ast.Call)}


# --- Task 2: identity, markers, manifest -------------------------------------------------------------

def test_every_code_cell_has_a_marker(notebook):
    markers = [MARKER.match(_source(c)) for c in notebook['cells'] if c['cell_type'] == 'code']
    assert all(markers), 'every code cell starts with # [Cn] <title>'
    assert [f'C{m.group(1)}' for m in markers] == [f'C{n}' for n in range(1, 12)]


def test_every_code_cell_compiles(cells):
    for marker, source in cells.items():
        ast.parse(source, filename=marker)


def test_bundle_alias_comes_from_config():
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    identity = builder.campaign_identity(REPO)
    assert identity['alias'] == config['storage_alias']
    assert identity['campaign_id'] == config['campaign_id']
    assert identity['dataset_root'] == config['dataset_root']
    assert list(identity['splits']) == list(config['splits'])


def test_no_literal_alias_in_cells_or_generator(cells):
    assert not any('iquitos_v5' in source for source in cells.values())
    assert 'iquitos_v5' not in Path(builder.__file__).read_text(encoding='utf-8')


def test_manifest_lists_every_bundled_file_with_sha256(tmp_path):
    import hashlib
    import zipfile
    bundle_path = tmp_path/'bundle.zip'
    builder.main(['--output', str(bundle_path), '--notebook', str(tmp_path/'nb.ipynb')])
    with zipfile.ZipFile(bundle_path) as bundle:
        manifest = json.loads(bundle.read('colab_bundle_manifest.json'))
        members = {n for n in bundle.namelist() if not n.endswith('/')}
        assert set(manifest['files']) == members - {'colab_bundle_manifest.json', 'colab_session.py'}
        for name, digest in manifest['files'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == digest
        assert 'colab_session.py' in members
    for key in ('commit', 'submodules', 'dataset_hash', 'source_sha256', 'source_scope', 'campaign_id', 'alias'):
        assert key in manifest


# --- Task 3: C1 exact checkout ------------------------------------------------------------------------

def test_c1_uses_session_helpers_and_stops_on_reasons(cells):
    source = cells['C1']
    assert {'apply_overlay', 'verify_checkout'} <= _calls(source)
    assert 'infolist' not in source
    tree = ast.parse(source)
    guarded = [n for n in ast.walk(tree) if isinstance(n, ast.If)
               and any(isinstance(s, ast.Raise) for s in ast.walk(n))]
    assert guarded, 'C1 raises when verify_checkout reports reasons'


# --- Task 4: C2 install, C3 identity ------------------------------------------------------------------

def test_c2_pins_torch_and_uv(cells):
    source = cells['C2']
    assert 'torch==2.8.0' in source and 'torchvision==0.23.0' in source
    assert 'https://astral.sh/uv/0.12.17/install.sh' in source
    assert 'astral.sh/uv/install.sh' not in source


def test_c2_base_deps_pinned_to_lock(cells):
    tree = ast.parse(cells['C2'])
    base = next(node.value for node in ast.walk(tree) if isinstance(node, ast.Assign)
                and any(getattr(t, 'id', None) == 'BASE_DEPS' for t in node.targets))
    requirements = [elt.value for elt in base.elts if isinstance(elt, ast.Constant)]
    lock = (REPO/'uv.lock').read_text(encoding='utf-8')
    # uv.lock may resolve one package several times (per Python marker); the pin must be one of them.
    locked = {}
    for name, version in re.findall(r'\nname = "([^"]+)"\nversion = "([^"]+)"', lock):
        locked.setdefault(name.lower(), set()).add(version)
    for requirement in requirements:
        assert '==' in requirement, requirement
        name, version = requirement.split('==', 1)
        if name.lower() in locked:
            assert version in locked[name.lower()], (requirement, sorted(locked[name.lower()]))


@pytest.mark.parametrize('name', ['numpy', 'gymnasium', 'pettingzoo'])
def test_lock_resolves_the_simulator_stack_to_the_pinned_versions(name):
    # CityLearn needs numpy==1.23.5; a lock on another version describes an environment that cannot run it.
    pinned = re.search(rf'^{name}==(\S+)', (REPO/'requirements.txt').read_text(encoding='utf-8'), re.M).group(1)
    lock = (REPO/'uv.lock').read_text(encoding='utf-8')
    assert re.findall(rf'\nname = "{name}"\nversion = "([^"]+)"', lock) == [pinned]


def test_gym_stays_out_of_the_lock_so_it_cannot_pin_a_version_the_project_does_not_run():
    # uv cannot build gym==0.20.0; see [tool.uv] in pyproject.toml. requirements.txt pins it instead.
    assert re.search(r'^gym==0\.20\.0$', (REPO/'requirements.txt').read_text(encoding='utf-8'), re.M)
    assert '\nname = "gym"\n' not in (REPO/'uv.lock').read_text(encoding='utf-8')


def test_c2_messages_reference_existing_markers(cells):
    source = cells['C2']
    for stale in ('celda 1.2', '1.2b', 'Celda 1.3'):
        assert stale not in source


def test_c3_reads_splits_python_and_drive_from_identity(cells):
    source = cells['C3']
    assert "CAMPAIGN['splits']" in source
    assert {'project_python', 'drive_root'} <= _calls(source)
    assert '.venv39-citylearn-v3/bin/python' not in source
    assert "('train_2023', 'validation_2024', 'test_2025')" not in source


def test_c3_refuses_dataset_mismatch(cells):
    source = cells['C3']
    assert "BUNDLE_MANIFEST['dataset_hash']" in source and "BUNDLE_MANIFEST['source_sha256']" in source
    assert 'raise' in source


# --- Task 5: C4 restore, C5 prepare -------------------------------------------------------------------

def test_c4_stops_on_conflicts(cells):
    source = cells['C4']
    assert 'run_cli' in _calls(source)
    assert "['conflicts']" in source and "['rejected']" in source and 'raise' in source


def test_cells_never_use_check_true_with_captured_output(cells):
    for marker, source in cells.items():
        assert not ('check=True' in source and 'capture_output=True' in source), marker


def test_c5_prints_budget_and_status(cells):
    source = cells['C5']
    assert 'run_cli' in _calls(source)
    assert "['status']" in source and "['budget']" in source


# --- Task 6: C6 run stage ------------------------------------------------------------------------------

def test_c6_defaults_to_no_training(cells):
    source = cells['C6']
    assert re.search(r'^RUN_STAGE = None\b', source, re.MULTILINE)
    assert 'if RUN_STAGE' in source


def test_c6_uses_run_stage_with_sync_and_reports_returncode(cells):
    source = cells['C6']
    assert 'run_stage_with_sync' in _calls(source)
    assert 'returncode' in source and "['status']" in source
    assert 'communicate(' not in source


def test_markdown_states_interrupted_attempt_policy(notebook):
    before_c6 = _markdown_before(notebook, 'C6').lower()
    assert 'completion.json' in before_c6 and 'desde cero' in before_c6
    for cell in notebook['cells']:
        if cell['cell_type'] == 'markdown':
            assert 'queda como evidencia fallida' not in _source(cell).lower()


# --- Task 8: C7-C11 after training ---------------------------------------------------------------------

@pytest.mark.parametrize('marker, command', [('C7', 'status'), ('C8', 'freeze'), ('C9', 'evaluate'),
                                             ('C10', 'analyze'), ('C11', 'deliver')])
def test_post_training_cells_call_pipeline_subcommands(cells, marker, command):
    source = cells[marker]
    assert 'uc3m.application.pipeline' in source and f"'{command}'" in source and "'--manifest'" in source


def test_c9_defaults_to_validation_split_and_parallel_workers(cells, notebook):
    source = cells['C9']
    assert "'validation_2024'" in source and "'--workers'" in source
    assert 'test_unlock.json' in _markdown_before(notebook, 'C9')


@pytest.mark.parametrize('marker, flag', [('C8', 'RUN_FREEZE'), ('C9', 'RUN_EVALUATION'),
                                          ('C10', 'RUN_ANALYSIS'), ('C11', 'RUN_DELIVERY')])
def test_post_training_cells_guarded_by_flags(cells, marker, flag):
    source = cells[marker]
    assert re.search(rf'^{flag} = False\b', source, re.MULTILINE) and f'if {flag}' in source


# --- Task 9: texts and sources ------------------------------------------------------------------------

def test_intro_states_masac_resource_refusal(notebook):
    intro = _source(notebook['cells'][0]).lower()
    assert 'masac' in intro and '80 gb' in intro and 'incompleta' in intro


def test_sources_match_verified_references(notebook):
    final = _source(notebook['cells'][-1])
    assert 'https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5' in final
