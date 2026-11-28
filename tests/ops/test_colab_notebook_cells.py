"""Colab overlay bundle, dependency lock and launch-tutorial cell contracts.

The only training notebook is examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb (owner
decision 2026-11-28); tools/colab/build_colab_bundle.py builds the ZIP its cell 1.2 applies.
The modular companion notebook and its generator were removed; their per-cell checks live
on in the tutorial tests below and in tests/fresh_training/test_tutorial_notebooks.py.
"""
import json
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO))

from tools.colab import build_colab_bundle as builder  # noqa: E402

MARKER = re.compile(r'^# \[C(\d+)\] ')
CONFIG = REPO/'configs/experiments/iquitos.yaml'


def _source(cell):
    return ''.join(cell['source']) if isinstance(cell['source'], list) else cell['source']


def test_bundle_alias_comes_from_config():
    config = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    identity = builder.campaign_identity(REPO)
    assert identity['alias'] == config['storage_alias']
    assert identity['campaign_id'] == config['campaign_id']
    assert identity['dataset_root'] == config['dataset_root']
    assert list(identity['splits']) == list(config['splits'])


def test_no_literal_alias_in_the_bundle_builder():
    assert 'iquitos_v5' not in Path(builder.__file__).read_text(encoding='utf-8')


def test_manifest_lists_every_bundled_file_with_sha256(tmp_path):
    import hashlib
    import zipfile
    bundle_path = tmp_path/'bundle.zip'
    builder.main(['--output', str(bundle_path)])
    with zipfile.ZipFile(bundle_path) as bundle:
        manifest = json.loads(bundle.read('colab_bundle_manifest.json'))
        members = {n for n in bundle.namelist() if not n.endswith('/')}
        assert set(manifest['files']) == members - {'colab_bundle_manifest.json', 'colab_session.py'}
        for name, digest in manifest['files'].items():
            assert hashlib.sha256(bundle.read(name)).hexdigest() == digest
        assert 'colab_session.py' in members
    for key in ('commit', 'submodules', 'dataset_hash', 'source_sha256', 'source_scope', 'campaign_id', 'alias'):
        assert key in manifest


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


def test_launch_tutorial_can_prepare_a_colab_runtime_with_insufficient_vram(capsys):
    tutorial = json.loads(builder.TUTORIAL.read_text(encoding='utf-8'))
    source = next(_source(cell) for cell in tutorial['cells'] if _source(cell).startswith('# 1.1 '))
    namespace = {'IN_COLAB': True, 'RAM_FREE_GIB': 80.56, 'VRAM_FREE_GIB': 39.49}

    exec(compile(source, 'tutorial-1.1', 'exec'), namespace)

    assert namespace['COLAB_READY'] is True
    assert '39.49' in capsys.readouterr().out


def test_launch_tutorial_reports_a_blocked_stage_without_dispatching(capsys, tmp_path):
    from types import SimpleNamespace

    tutorial = json.loads(builder.TUTORIAL.read_text(encoding='utf-8'))
    source = next(_source(cell) for cell in tutorial['cells'] if _source(cell).startswith('# 7.2 '))
    source = source.replace('EXECUTE_STAGE = False', 'EXECUTE_STAGE = True').replace(
        "OWNER_DECISION = ''", "OWNER_DECISION = 'decision registrada'")
    phase = {'algorithms': ['HAPPO', 'MASAC'], 'workers': 0,
             'reasons': ['insufficient_resources:MASAC:vram']}

    def refuse_dispatch(*args, **kwargs):
        pytest.fail('A stage with zero workers must not dispatch')

    namespace = {'PROJECT_ROOT': tmp_path, 'PYTHON': sys.executable, 'IN_COLAB': True,
                 'SYNC_COMMAND': ['sync'], 'ARTIFACT_ROOT': tmp_path,
                 'cs': SimpleNamespace(run_cli=lambda *args, **kwargs: SimpleNamespace(
                     report={'phase_plan': {'hpo': [phase]}}), phase_plan_lines=lambda *args: [],
                     run_stage_with_sync=refuse_dispatch)}

    exec(compile(source, 'tutorial-7.2', 'exec'), namespace)

    assert namespace['STAGE_TRAINING_COMPLETE'] is False
    assert 'insufficient_resources:MASAC:vram' in capsys.readouterr().out


def test_launch_tutorial_contains_guarded_post_training_workflow():
    tutorial = json.loads(builder.TUTORIAL.read_text(encoding='utf-8'))
    workflow = {}
    for cell in tutorial['cells']:
        source = _source(cell)
        if cell['cell_type'] == 'code' and source.startswith('# [C'):
            match = MARKER.match(source)
            if match and match[1] in {'8', '9', '10', '11'}:
                workflow[match[1]] = source

    assert list(workflow) == ['9', '8', '10', '11']

    class InactiveCli:
        def __getattr__(self, name):
            pytest.fail(f'The default cells must not invoke {name}')

    namespace = {'cs': InactiveCli()}
    for marker, commands in {
        '9': ('evaluate',), '8': ('freeze',), '10': ('analyze', 'select'), '11': ('deliver',),
    }.items():
        source = workflow[marker]
        assert 'uc3m.application.pipeline' in source
        assert 'MANIFEST_PATH' in source and 'SYNC_COMMAND' in source
        assert all(f"'{command}'" in source for command in commands)
        exec(compile(source, f'tutorial-C{marker}', 'exec'), namespace)

    assert (namespace['EVAL_STAGE'], namespace['EVAL_SPLIT']) == ('pilot', 'validation_2024')


def test_launch_tutorial_displays_all_kpi_catalog_sections():
    tutorial = json.loads(builder.TUTORIAL.read_text(encoding='utf-8'))
    catalog = yaml.safe_load((REPO/'configs/evaluation/kpis.yaml').read_text(encoding='utf-8'))
    summary = next(_source(cell) for cell in tutorial['cells'] if _source(cell).startswith('## Sección 8: KPIs'))
    source = next(_source(cell) for cell in tutorial['cells'] if '8.1  Catalogo de KPIs' in _source(cell))
    displayed = []

    exec(compile(source, 'tutorial-8.1', 'exec'), {'PROJECT_ROOT': REPO, 'display': displayed.append})

    table_rows = '\n'.join(line for line in summary.splitlines() if line.startswith('| **E'))
    assert re.findall(r'`([^`]+)`', table_rows) == catalog['primary_endpoints']
    assert len(displayed) == 3
    for frame, key in zip(displayed, ('definitions', 'citylearn_v3_kpis', 'thesis_indicators')):
        assert frame['name'].tolist() == [entry['name'] for entry in catalog[key]]
        assert not frame.isna().any().any()

    frame = displayed[0].set_index('name')
    assert frame.loc['bill_cost_total', 'axis'] == 'energy_cost'
    assert bool(frame.loc['bill_cost_total', 'primary'])
    assert not bool(frame.loc['import_energy', 'primary'])
    assert not bool(frame.loc['price_signal_deviation', 'primary'])
