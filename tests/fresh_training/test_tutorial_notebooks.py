"""T12-B: the three tutorial notebooks of examples_madrl_v3/ are reconnected to the CLI.

Owner decision 2026-11-01: the existing notebooks are kept (not recreated) and
only rewired. Training is launched only through the fresh campaign CLI
(governance/repository_layout.yaml, section ``launch``); a notebook never names a
retired launcher, a historical output root or a resume flag, and it never trains
by merely running all cells.
"""
import ast
import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock

import nbformat
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
LAYOUT = yaml.safe_load((REPO/'governance/repository_layout.yaml').read_text(encoding='utf-8'))
NOTEBOOKS = ('examples_madrl_v3/madrl_citylearn_v3_cli.ipynb',
             'examples_madrl_v3/madrl_citylearn_v3_quickstart.ipynb',
             'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb')
CLI_MODULE = 'uc3m.application.training.cli'
PIPELINE_MODULE = 'uc3m.application.pipeline'
CAMPAIGN_CONFIG = 'configs/experiments/iquitos.yaml'
FRESH_OUTPUTS = 'outputs/campaigns/'

# Retired names that are not plain paths of the registry (launch scripts that live
# in the protected dependency, flags and protocol names of the previous launcher).
RETIRED_PATTERNS = (
    r'(train|launch|monitor)_citylearn_v3_\w+\.(py|ps1)',
    r'\buc3m\.train\b(?!ing)', r'uc3m/train\.py',
    r'scripts/colab_', r'colab_a100_', r'colab_protocol_guard',
    r'launch_citylearn_v3_multiseed_campaign', r'scripts/benchmark_', r'benchmark_citylearn_v2',
    r'run_madrl_multicriteria_selection', r'generate_thesis_objective_evidence',
    r'compare_citylearn_v2_vs_v3_madrl', r'--resume', r'--skip-completed', r'two_phase_happo_masac',
    r'outputs/madrl_v3_', r'madrl_v3_\d', r'rescued_happo', r'latest_colab_output_root',
    r'latest_visible_training_output_root', r'thesis_objective_evidence',
    r'citylearn_v2_original_benchmark', r'colab_project_context', r'dataset_cache',
    r'citylearn_iquitos_2023_2025', r'DEFAULT_17_BUILDING_EV_SCHEMA', r'make_citylearn_v3_project_env',
    r'citylearn_v3_madrl',
)
RETIRED_SEEDS = re.compile(r'(?<![\w.])(42|123|456)(?![\w.])')
RETIRED_DESIGN = re.compile(r'4\s*[x×]\s*3\s*[x×]\s*3(?!\d)')
REPO_PATH = re.compile(r"(?<![\w./-])((?:CityLearn|configs|data|docs|examples_madrl_v3|external|governance|outputs"
                       r"|scripts|specs|tests|tools|uc3m)/[\w./-]*)")


def _registry_retired():
    names = list(LAYOUT['launch']['retired']) + list(LAYOUT['retired_historical_roots'].values())
    names += list(LAYOUT['forbidden_input_roots']) + list(LAYOUT.get('forbidden_pointer_names') or [])
    return [name.rstrip('/') for name in names]


def _load(relative):
    return json.loads((REPO/relative).read_text(encoding='utf-8'))


def _source(cell):
    source = cell['source']
    return source if isinstance(source, str) else ''.join(source)


def _code(notebook):
    return [_source(c) for c in notebook['cells'] if c['cell_type'] == 'code']


def _uncommented(source):
    return [line for line in source.splitlines() if not line.lstrip().startswith(('#', '!', '%'))]


@pytest.mark.parametrize('relative', NOTEBOOKS)
def test_valid_nbformat4_without_outputs(relative):
    raw = (REPO/relative).read_bytes()
    raw.decode('utf-8')
    notebook = nbformat.reads(raw.decode('utf-8'), as_version=4)
    nbformat.validate(notebook)
    assert notebook.nbformat == 4
    raw_cells = json.loads(raw.decode('utf-8'))['cells']
    ids = [cell.get('id') for cell in raw_cells]
    if notebook.nbformat_minor >= 5:  # nbformat 4.5 requires a unique id per cell
        assert all(ids) and len(set(ids)) == len(ids), relative
    for cell in notebook.cells:
        if cell.cell_type == 'code':
            assert cell.outputs == [] and cell.execution_count is None, relative


@pytest.mark.parametrize('relative', NOTEBOOKS)
def test_every_code_cell_compiles(relative):
    for index, source in enumerate(_code(_load(relative))):
        text = '\n'.join('' if line.lstrip().startswith(('!', '%')) else line for line in source.splitlines())
        compile(text, f'{relative}#code{index}', 'exec')


@pytest.mark.parametrize('relative', NOTEBOOKS)
def test_no_retired_launcher_root_or_resume_flag(relative):
    notebook = _load(relative)
    offenders = []
    for index, cell in enumerate(notebook['cells']):
        text = _source(cell)
        offenders += [(index, p) for p in RETIRED_PATTERNS if re.search(p, text)]
        offenders += [(index, name) for name in _registry_retired() if name in text]
    assert offenders == []


@pytest.mark.parametrize('relative', NOTEBOOKS)
def test_training_invocations_go_through_the_campaign_cli(relative):
    # A cell invokes a stage when an uncommented line names --stage. The post-training
    # pipeline (uc3m.application.pipeline evaluate/freeze/...) also takes --stage to pick
    # which finished stage it reads; it never trains, so it is checked apart.
    code = _code(_load(relative))
    stage_cells = [s for s in code if any('--stage' in line for line in _uncommented(s))]
    training_cells = [s for s in stage_cells if PIPELINE_MODULE not in s]
    assert training_cells, f'{relative} must show how the campaign CLI is called'
    for source in training_cells:
        assert CLI_MODULE in source and CAMPAIGN_CONFIG in source
    for source in stage_cells:
        assert 'native_entrypoint' not in source
    assert (REPO/CAMPAIGN_CONFIG).is_file()
    assert (REPO/(CLI_MODULE.replace('.', '/') + '.py')).is_file()


@pytest.mark.parametrize('relative', NOTEBOOKS)
def test_execute_is_only_an_explicit_opt_in(relative):
    for source in _code(_load(relative)):
        live = [line for line in _uncommented(source) if '--execute' in line]
        if not live:
            continue
        assert re.search(r'^EXECUTE_STAGE\s*=\s*False\b', source, re.M), 'execution flag must default to False'
        # Every '--execute' literal sits inside an if/elif whose test reads EXECUTE_STAGE,
        # even when the call spans several lines.
        assert _unguarded_execute(source) == [], live


def _unguarded_execute(source):
    tree = ast.parse('\n'.join('' if line.lstrip().startswith(('!', '%')) else line
                               for line in source.splitlines()))
    guarded = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.If, ast.IfExp)) and any(isinstance(n, ast.Name) and n.id == 'EXECUTE_STAGE'
                                                         for n in ast.walk(node.test)):
            for child in (node.body if isinstance(node, ast.If) else [node.body]):
                guarded |= {id(n) for n in ast.walk(child)}
    return [node.lineno for node in ast.walk(tree)
            if isinstance(node, ast.Constant) and node.value == '--execute' and id(node) not in guarded]


@pytest.mark.parametrize('relative', NOTEBOOKS)
def test_referenced_repository_paths_exist(relative):
    missing = []
    for source in _code(_load(relative)):
        for match in REPO_PATH.findall(source):
            path = match.rstrip('./')
            if path.startswith(FRESH_OUTPUTS.rstrip('/')):
                continue
            if not (REPO/path).exists():
                missing.append(path)
    assert missing == []


@pytest.mark.parametrize('relative', NOTEBOOKS)
def test_markdown_states_the_fresh_campaign_design(relative):
    for cell in _load(relative)['cells']:
        if cell['cell_type'] != 'markdown':
            continue
        text = _source(cell)
        assert not RETIRED_SEEDS.search(text), text[:200]
        assert not RETIRED_DESIGN.search(text), text[:200]


def test_tutorial_has_a_single_setup_cell():
    # The tutorial is the only training notebook (owner decision 2026-11-28).
    sources = _code(_load(NOTEBOOKS[2]))
    assert sum('# 1.3 Instalar dependencias' in s for s in sources) == 1


def test_tutorial_launch_uses_uploaded_bundle_and_campaign_sync():
    sources = _code(_load(NOTEBOOKS[2]))
    checkout = next(s for s in sources if '1.2  Clonar' in s)
    assert '/content/colab_modular_overlay.zip' in checkout
    assert 'files.upload()' not in checkout
    assert checkout.index('verify_remote_revision()\n') < checkout.index('cs.apply_overlay(')
    stage = next(s for s in sources if 'EXECUTE_STAGE = False' in s)
    assert "RUN_STAGE = 'hpo'" in stage
    assert '--owner-authorized' in stage and 'run_stage_with_sync' in stage
    assert 'copytree' not in stage
    assert any('drive_root(' in s and "'--restore'" in s for s in sources)


def test_tutorial_first_drive_restore_creates_the_campaign_folder(tmp_path):
    from tools.colab.colab_session import drive_root
    from uc3m.application.training.drive_sync import restore_finished_attempts

    campaign_id = 'fresh_test'
    alias = 'trial_test'
    config = {'campaign_id': campaign_id, 'storage_alias': alias,
              'dataset_root': 'dataset', 'algorithms': ['HAPPO'], 'stages': {'hpo': {}}}
    config_path = tmp_path / CAMPAIGN_CONFIG
    config_path.parent.mkdir(parents=True)
    config_path.write_text(yaml.safe_dump(config), encoding='utf-8')
    dataset = tmp_path / 'dataset'
    dataset.mkdir()
    (dataset / 'dataset_acceptance.json').write_text(
        json.dumps({'dataset_verified': True, 'dataset_hash': 'expected'}), encoding='utf-8',
    )
    client = Mock()
    client.project_python.return_value = 'remote-python'
    client.drive_root.side_effect = drive_root

    def restore(command, *, cwd):
        artifacts = Path(command[command.index('--artifacts') + 1])
        drive = Path(command[command.index('--drive') + 1])
        return SimpleNamespace(report=restore_finished_attempts(drive, artifacts, campaign_id))

    client.run_cli.side_effect = restore
    cell = next(s for s in _code(_load(NOTEBOOKS[2])) if 'restored = cs.run_cli' in s)
    bundle = {'campaign_id': campaign_id, 'alias': alias, 'dataset_root': 'dataset', 'dataset_hash': 'expected'}
    exec(cell, {'IN_COLAB': True, 'PROJECT_DIR': str(tmp_path), 'PROJECT_PYTHON': 'remote-python',
                'cs': client, 'bundle_manifest': bundle, 'DRIVE_BASE': tmp_path / 'drive'})
    assert (drive_root(tmp_path / 'drive', alias, campaign_id) / '.sync.lock').is_file()


def test_tutorial_reports_free_memory_against_masac_before_colab_setup(capsys):
    # Commit 97a849de: preparation continues below the MASAC reference; the CLI refuses
    # per phase (insufficient_resources) before training. The cell reports the shortfall.
    native = yaml.safe_load((REPO / 'configs/algorithms/native.yaml').read_text(encoding='utf-8'))
    masac = native['algorithms']['MASAC']['runtime_requirements']
    ram = masac['min_ram_gib']
    vram = max(masac['min_vram_gib_by_rnn_hidden_dim'].values())
    cell = next(s for s in _code(_load(NOTEBOOKS[2])) if s.startswith('# 1.1 '))
    for available_ram, available_vram in ((ram - 1, vram), (ram, vram - 1), (ram, None)):
        state = {'IN_COLAB': True, 'RAM_FREE_GIB': available_ram, 'VRAM_FREE_GIB': available_vram}
        exec(cell, state)
        assert state['COLAB_READY']
        assert f'{ram} GiB de RAM y {vram} GiB de VRAM' in capsys.readouterr().out
    state = {'IN_COLAB': True, 'RAM_FREE_GIB': ram, 'VRAM_FREE_GIB': vram}
    exec(cell, state)
    assert state['COLAB_READY'] and 'dentro de la referencia' in capsys.readouterr().out
