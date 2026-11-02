"""T12-B: the three tutorial notebooks of examples_madrl_v3/ are reconnected to the CLI.

Owner decision 2026-11-01: the existing notebooks are kept (not recreated) and
only rewired. Training is launched only through the fresh campaign CLI
(governance/repository_layout.yaml, section ``launch``); a notebook never names a
retired launcher, a historical output root or a resume flag, and it never trains
by merely running all cells.
"""
import json
import re
from pathlib import Path

import nbformat
import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
LAYOUT = yaml.safe_load((REPO/'governance/repository_layout.yaml').read_text(encoding='utf-8'))
NOTEBOOKS = ('examples_madrl_v3/madrl_citylearn_v3_cli.ipynb',
             'examples_madrl_v3/madrl_citylearn_v3_quickstart.ipynb',
             'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb')
CLI_MODULE = 'uc3m.application.training.cli'
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
    # A cell invokes a stage when an uncommented line names --stage.
    stage_cells = [s for s in _code(_load(relative)) if any('--stage' in line for line in _uncommented(s))]
    assert stage_cells, f'{relative} must show how the campaign CLI is called'
    for source in stage_cells:
        assert CLI_MODULE in source and CAMPAIGN_CONFIG in source
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
        assert all('if EXECUTE_STAGE' in line for line in live), live


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


def test_tutorial_keeps_the_setup_cell_reused_by_the_colab_companion():
    # tools/colab/build_modular_colab_notebook.py copies this cell literally.
    sources = _code(_load(NOTEBOOKS[2]))
    assert sum('# 1.3 Instalar dependencias' in s for s in sources) == 1
