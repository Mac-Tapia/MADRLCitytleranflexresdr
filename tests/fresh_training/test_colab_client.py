"""The Colab notebook is a client of the fresh campaign CLI (owner decision).

It keeps the existing notebook and its original setup cell, but trains only
through `python -m uc3m.application.training.cli --config ... --stage ...`,
verifies the fresh dataset by hash, never resumes, and copies finished
attempts to Drive because /content is lost on disconnect.
"""
import json
import re
import sys

import pytest
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/colab'))

import build_modular_colab_notebook as builder  # noqa: E402

NOTEBOOK = REPO/'examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb'


def _built():
    original = json.loads(builder.ORIGINAL.read_text(encoding='utf-8'))
    return builder.build_notebook(original, 'f'*64)


def _code(notebook):
    return '\n'.join(''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code')


def test_notebook_trains_only_through_the_campaign_cli():
    code = _code(_built())
    assert "'-m', 'uc3m.application.training.cli'" in code
    assert "CONFIG = 'configs/experiments/iquitos.yaml'" in code and "'--config', CONFIG" in code
    for retired in ('uc3m.application.training.colab', '--resume', 'citylearn_iquitos_2023_2025',
                    'full_campaign_4x3x3', 'train_citylearn_v3_'):
        assert retired not in code, retired
    assert 'RUN_STAGE = None' in code  # nothing trains by running all cells


def test_notebook_verifies_the_fresh_dataset_and_syncs_attempts_to_drive():
    notebook = _built()
    code = _code(notebook)
    assert notebook['metadata']['expected_dataset_sha256'] == 'f'*64
    assert "CAMPAIGN['storage_alias']" in code and 'dataset_acceptance.json' in code and 'dataset_verified' in code
    assert 'iquitos_v1' not in code                    # the alias comes from configs/experiments/iquitos.yaml
    assert 'uc3m.application.training.drive_sync' in code and 'MyDrive' in code
    assert "'--restore'" in code and "'--sync'" in code and 'run_stage_with_sync' in code
    assert code.index("'--restore'") < code.index("'--stage', 'prepare'") < code.index("'--execute'")
    for cell in notebook['cells']:
        if cell['cell_type'] == 'code':
            compile(''.join(cell['source']), 'cell', 'exec')


def test_committed_notebook_is_the_built_client():
    committed = json.loads(NOTEBOOK.read_text(encoding='utf-8'))
    assert "'-m', 'uc3m.application.training.cli'" in _code(committed)
    acceptance = json.loads((REPO/'data/campaigns/iquitos_v1/dataset_acceptance.json').read_text(encoding='utf-8'))
    assert committed['metadata']['expected_dataset_sha256'] == acceptance['dataset_hash']


def test_bundle_carries_the_frozen_campaign_and_no_retired_root():
    paths = {p.relative_to(REPO).as_posix() for p in builder.bundle_paths(REPO, builder.campaign_from_config(builder.CAMPAIGN_CONFIG)[1])}
    assert 'data/campaigns/iquitos_v1/splits/train_2023/schema.json' in paths
    assert 'data/campaigns/iquitos_v1/normalizer.json' in paths
    assert 'configs/experiments/iquitos.yaml' in paths and 'uc3m/application/training/cli.py' in paths
    assert 'uc3m/application/training/drive_sync.py' in paths
    assert not any(p.startswith(('outputs/', 'CityLearn/data/datasets/', 'data/campaigns/iquitos_v1/raw/'))
                   for p in paths)


# --- Review 2026-11-01 and plan docs/plans/cuaderno_colab.md (cells located by marker) -------------------

def _cells():
    return [''.join(c['source']) for c in _built()['cells']]


def _cell(marker):
    return next(source for source in _cells() if source.startswith(f'# [{marker}] '))


def test_bundle_alias_and_dataset_come_from_the_campaign_config(tmp_path):
    root = tmp_path/'project'
    (root/'configs/experiments').mkdir(parents=True)
    (root/'configs/experiments/iquitos.yaml').write_text(
        'storage_alias: other_v9\ncampaign_id: fresh_other_v9\ndataset_root: data/campaigns/other_v9\n'
        'splits: [train_2023]\n', encoding='utf-8')
    dataset = root/'data/campaigns/other_v9'
    (dataset/'splits/train_2023').mkdir(parents=True)
    (dataset/'dataset_acceptance.json').write_text('{"dataset_hash": "x"}', encoding='utf-8')
    (dataset/'splits/train_2023/schema.json').write_text('{}', encoding='utf-8')
    alias, dataset_root = builder.campaign_from_config(root/'configs/experiments/iquitos.yaml')
    assert (alias, dataset_root) == ('other_v9', 'data/campaigns/other_v9')
    assert builder.campaign_identity(root)['campaign_id'] == 'fresh_other_v9'
    paths = {p.relative_to(root).as_posix() for p in builder.bundle_paths(root, dataset_root)}
    assert 'data/campaigns/other_v9/splits/train_2023/schema.json' in paths
    assert not any('iquitos_v1' in p for p in paths)


def test_overlay_is_applied_and_verified_through_the_session_module():
    c1 = _cell('C1')
    assert "bundle.read('colab_session.py')" in c1 and 'cs.apply_overlay' in c1 and 'cs.verify_checkout' in c1
    c3 = _cell('C3')
    assert "BUNDLE_MANIFEST['source_sha256']" in c3 and "source_snapshot(Path('.'), scope='fresh')" in c3


def test_status_cell_lists_every_treatment_with_reasons():
    c7 = _cell('C7')
    assert "'status', '--manifest'" in c7 and "row.get('reasons')" in c7


def test_setup_messages_point_to_cells_of_this_notebook_and_python_is_reused():
    setup = _cell('C2')
    assert 'celda 1.2b' not in setup and 'celda 1.2.' not in setup and 'Celda 1.3' not in setup
    assert ".venv39-citylearn-v3/bin/python" not in _cell('C3') and 'PROJECT_PYTHON' in _cell('C3')


def test_sources_cite_verifiable_links_only():
    sources = _cells()[-1]
    assert '10.5287/ora-ovzyxredj' not in sources
    assert 'https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5' in sources


def test_masac_refusal_on_80gb_gpus_is_stated_as_expected():
    intro = _cells()[0]
    assert '82 GiB' in intro and '96 GB' in intro and '80 GB' in intro and 'esperado' in intro


def test_setup_pins_dependencies_to_lock_then_environment():
    import importlib.metadata as metadata
    setup = _cell('C2')
    locked = builder.locked_versions()
    torch = metadata.version('torch').split('+')[0]
    vision = metadata.version('torchvision').split('+')[0]
    assert f"TORCH_PACKAGES = ('torch=={torch}', 'torchvision=={vision}')" in setup
    for name in builder.PINNED_FROM_LOCK_OR_ENV:
        version = locked.get(name.lower()) or metadata.version(name)
        assert f"'{name}=={version}'" in setup, name
    assert "'tqdm==" + locked['tqdm'] + "'" in setup            # uv.lock wins (plan)
    assert "'requests==2.32.5'" in setup                         # the Python < 3.10 entry of uv.lock
    assert "'tensorboard'" not in setup
    assert 'https://astral.sh/uv/install.sh' not in setup and 'https://astral.sh/uv/0.' in setup


def test_splits_come_from_the_split_manifest_and_drive_is_per_campaign():
    c3 = _cell('C3')
    assert "split_manifest.json" in c3 and "CAMPAIGN['splits']" in c3
    assert 'cs.drive_root(' in c3 and 'CAMPAIGN_ID' in c3


def test_restore_stops_on_conflicts_or_rejections():
    c4 = _cell('C4')
    assert "if restored['conflicts'] or restored['rejected']:" in c4
    assert 'raise RuntimeError' in c4.split("if restored['conflicts'] or restored['rejected']:")[1]


def test_run_cell_uses_the_session_runner_and_explicit_codes():
    c6 = _cell('C6')
    assert 'cs.run_stage_with_sync(' in c6 and "SYNC + ['--sync']" in c6
    assert 'returncode == 2' in c6 and 'returncode == 1' in c6 and 'NO es un éxito' in c6


def test_evaluation_workers_are_bounded_by_measured_ram():
    c9 = _cell('C9')
    assert 'max(1, min((os.cpu_count() or 2) - 1, int(available // EVAL_RAM_GIB)))' in c9
    assert builder.EVAL_RAM_GIB is not None and builder.EVAL_RAM_MEASUREMENT    # measured, not assumed
    assert repr(builder.EVAL_RAM_GIB) in c9


def test_markdown_states_one_rule_for_interrupted_attempts():
    texts = [c for c in _cells() if c.lstrip().startswith('#') and 'interrumpido' in c]
    assert texts
    for text in texts:
        assert 'desde cero' in text and 'reanuda' in text
        assert 'evidencia fallida y se vuelve a lanzar' not in text


def test_phase_reports_are_displayed_from_the_cli_json_only():
    c5, c6 = _cell('C5'), _cell('C6')
    assert 'cs.phase_plan_lines(prepared, STAGE)' in c5 and "STAGE = 'pilot'" in c5
    assert 'cs.stage_result_lines(report, stage_result)' in c6
    assert "_result.json" in c6
    after = c6.split("report.get('status') == 'insufficient_resources'")[1]
    assert 'raise RuntimeError' in after and 'stopped_at_phase' in after


def test_one_stage_variable_drives_plan_and_launch():
    c5, c6 = _cell('C5'), _cell('C6')
    assert re.search(r"^STAGE = 'pilot'", c5, re.MULTILINE) and 'PLAN_STAGE' not in c5
    assert re.search(r'^EXECUTE_STAGE = False\b', c6, re.MULTILINE)
    assert re.search(r'^RUN_STAGE = None\b', c6, re.MULTILINE)          # name the plan contract expects
    guard = ('if EXECUTE_STAGE:\n    RUN_STAGE = STAGE\n'
             'if RUN_STAGE and RUN_STAGE != STAGE:\n    raise RuntimeError(')
    assert guard in c6
    namespace = {'STAGE': 'pilot', 'EXECUTE_STAGE': False}
    runnable = guard + "'x')\n"
    exec('RUN_STAGE = None\n' + runnable, namespace)
    assert namespace['RUN_STAGE'] is None                             # nothing trains by default
    launched = {'STAGE': 'pilot', 'EXECUTE_STAGE': True}
    exec('RUN_STAGE = None\n' + runnable, launched)
    assert launched['RUN_STAGE'] == 'pilot'                           # C6 uses the stage shown in C5
    with pytest.raises(RuntimeError):
        exec("RUN_STAGE = 'hpo'\n" + runnable, {'STAGE': 'pilot', 'EXECUTE_STAGE': False})
