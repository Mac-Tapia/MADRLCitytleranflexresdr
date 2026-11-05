"""L2-001/002/004/007/008/009/011/015: maintenance tools on disposable trees only.

Every written path lives under pytest's tmp_path. The only roots outside it are
paths that are asserted not to exist and are handed to a read-only Plan phase
with an empty manifest. Word documents are replaced by an in-memory stub: no
.docx is ever opened. Scripts with a mutating phase run against a sandbox tree
or a sandbox copy of the script, never against repository content.
"""
import hashlib
import importlib.util
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from tools.ops import audit_duplicate_files as adf
from tools.ops import historical_inventory as hi

REPO = Path(__file__).resolve().parents[2]
RENAME = REPO/'scripts/maintenance/rename_paths.ps1'
RETIRE = REPO/'scripts/maintenance/retire_historical_outputs.ps1'
PRUNE = REPO/'tools/training/prune_artifacts.ps1'
ORCHESTRATE = REPO/'tools/dataset/orchestrate_citylearn_dataset.py'
NO_PROCESSES = lambda: ()  # noqa: E731 - explicit empty process snapshot
POWERSHELL = ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File']


def _write(path, payload=b'x'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload if isinstance(payload, bytes) else payload.encode('utf-8'))
    return path


def _junction(target, link):
    import _winapi
    link.parent.mkdir(parents=True, exist_ok=True)
    _winapi.CreateJunction(str(target), str(link))
    return link


# --- L2-001 rename_paths.ps1: -Root containment ---------------------------------

def _rename_plan(tmp_path, root, moves=()):
    manifest = _write(tmp_path/'manifest'/f'{uuid.uuid4().hex}.json', json.dumps({
        'schema_version': 1, 'root': str(root), 'moves': list(moves), 'references': [],
        'duplicates': [], 'cleanup_directories': []}))
    return subprocess.run([*POWERSHELL, str(RENAME), '-Phase', 'Plan', '-Root', str(root),
                           '-Manifest', str(manifest)],
                          capture_output=True, text=True, cwd=REPO, timeout=300)


@pytest.mark.parametrize('kind', ['other_drive_root', 'repository_sibling', 'temp_sibling'])
def test_l2_001_root_outside_repository_and_temp_is_refused(tmp_path, kind):
    token = f'i13_l2_absent_{uuid.uuid4().hex}'
    temp = Path(tempfile.gettempdir()).resolve()
    root = {'other_drive_root': Path(REPO.anchor)/token,
            'repository_sibling': Path(f'{REPO}_{token}'),
            'temp_sibling': Path(f'{temp}_{token}')}[kind]
    assert not root.exists()
    result = _rename_plan(tmp_path, root)
    assert not root.exists()
    assert result.returncode != 0, result.stdout
    assert 'neither this repository nor' in result.stderr
    assert 'Ready:' not in result.stdout


def test_l2_001_temp_root_reached_through_a_link_is_refused(tmp_path):
    real = tmp_path/'elsewhere'
    _write(real/'project/old.md')
    link = _junction(real, tmp_path/'linked')
    digest = hashlib.sha256(b'x').hexdigest()
    result = _rename_plan(tmp_path, link/'project', [
        {'old_path': 'old.md', 'new_path': 'new.md', 'source_hash': digest}])
    assert result.returncode != 0, result.stdout
    assert 'Linked path rejected' in result.stderr


def test_l2_001_real_temp_root_still_plans(tmp_path):
    root = tmp_path/'project'
    _write(root/'old.md')
    digest = hashlib.sha256(b'x').hexdigest()
    result = _rename_plan(tmp_path, root, [
        {'old_path': 'old.md', 'new_path': 'new.md', 'source_hash': digest}])
    assert result.returncode == 0, result.stderr
    assert 'Ready: 1 moves' in result.stdout
    assert (root/'old.md').is_file() and not (root/'new.md').exists()


# --- L2-002 close_multicriteria.py: rankings from the current run ---------------

_spec = importlib.util.spec_from_file_location('i13_l2_close_multicriteria',
                                               REPO/'scripts/close_multicriteria.py')
cm = importlib.util.module_from_spec(_spec)
sys.modules[_spec.name] = cm
_spec.loader.exec_module(cm)
FIXED_NUMBERS = ('0,9538', '0,8805', '0,8679')
LEGACY_TEXT = 'El ranking evaluate_v2 4/4 sitúa a MAAC primero (0,9538).'
CURRENT = {'MASAC': 0.7123, 'MAAC': 0.6, 'HAPPO': 0.25, 'MATD3': 0.5}
CURRENT_TEXT = 'MASAC 0,7123 > MAAC 0,6000 > MATD3 0,5000 > HAPPO 0,2500'


def _regen(**extra):
    return {'source': 'synthetic', 'algorithms': sorted(CURRENT), 'topsis_winner': 'MASAC',
            'old_figure_sha256': {}, 'new_figure_sha256': {name: name for name in cm.MC_FIGS}, **extra}


@pytest.fixture
def word(monkeypatch, tmp_path):
    """Run main() against an in-memory document; nothing opens a real .docx."""
    state = SimpleNamespace(paragraphs=[SimpleNamespace(text=LEGACY_TEXT)], saves=0, media_calls=0, patch_calls=0,
                            regen=_regen(evaluate_v2_ranking=dict(CURRENT)))

    def _document(_path):
        def save(_target):
            state.saves += 1
        return SimpleNamespace(paragraphs=state.paragraphs, save=save)

    def _media(_path, _mapping):
        state.media_calls += 1
        return {'backup': 'none', 'replaced': [], 'n_replaced': 3}

    real_patch = cm.patch_text

    def _patch(*args):
        state.patch_calls += 1
        return real_patch(*args)

    monkeypatch.setattr(cm, 'Document', _document)
    monkeypatch.setattr(cm, 'REPO', tmp_path)
    monkeypatch.setattr(cm, 'CANONS', (tmp_path/'synthetic_canon.docx',))
    monkeypatch.setattr(cm, 'REPORT', tmp_path/'cierre.json')
    monkeypatch.setattr(cm, 'BACKUP_DIR', tmp_path/'backups')
    monkeypatch.setattr(cm, 'regenerate_artefacts', lambda: state.regen)
    monkeypatch.setattr(cm, 'replace_media_in_docx', _media)
    monkeypatch.setattr(cm, 'patch_text', _patch)
    monkeypatch.setattr(cm, 'force_replace_mc_images_by_caption',
                        lambda _path: pytest.fail('fallback must not run with synthetic media'))
    return state


def test_l2_002_word_text_comes_from_the_current_run(word):
    assert cm.main() == 0
    text = word.paragraphs[0].text
    assert CURRENT_TEXT in text
    assert not any(number in text for number in FIXED_NUMBERS)
    assert word.saves == 1


def test_l2_002_refuses_before_touching_word_without_a_current_ranking(word):
    word.regen = _regen()
    assert cm.main() != 0
    assert word.media_calls == 0 and word.patch_calls == 0 and word.saves == 0
    assert word.paragraphs[0].text == LEGACY_TEXT


@pytest.mark.parametrize('scores', [
    {'MAAC': 0.9},
    {**CURRENT, 'MAAC': float('nan')},
    {**CURRENT, 'MAAC': True},
    {**CURRENT, 'OTHER': 0.1},
])
def test_l2_002_refuses_a_ranking_that_does_not_match_the_run(word, scores):
    word.regen = _regen(evaluate_v2_ranking=scores)
    assert cm.main() != 0
    assert word.media_calls == 0 and word.saves == 0
    assert word.paragraphs[0].text == LEGACY_TEXT


def test_l2_002_stale_fixed_ranking_in_word_is_not_accepted(word):
    word.paragraphs[0].text = 'El ranking evaluate_v2 4/4 sitúa a MAAC 0,9538 > MATD3 0,8805 > MASAC 0,8679 > HAPPO 0,0000.'
    assert cm.main() != 0
    report = json.loads(cm.REPORT.read_text(encoding='utf-8'))
    assert report['ok'] is False


def test_l2_002_regeneration_publishes_only_what_the_pipeline_returned(monkeypatch, tmp_path):
    figures = tmp_path/'figures'
    for name in cm.MC_FIGS:
        _write(figures/name, name)
    monkeypatch.setattr(cm, 'FIG_DIR', figures)
    monkeypatch.setattr(cm, 'OUT_DIR', tmp_path)
    monkeypatch.setattr(cm, 'REPO', tmp_path)
    result = {'source': 'real_drive_50ep_c1c6', 'provenance': {'MAAC': {'C1': 'real'}},
              'decision_matrix': {'MAAC': {}}, 'ranking_consistency': {'topsis_winner': 'MAAC'}, 'extras': {}}
    fake = SimpleNamespace(run_selection_pipeline=lambda **_kwargs: result)
    monkeypatch.setitem(sys.modules, 'uc3m.multicriteria.pipeline', fake)
    assert cm.regenerate_artefacts()['evaluate_v2_ranking'] is None
    result['extras'] = {'evaluate_v2_ranking': {'MAAC': 0.5}}
    assert cm.regenerate_artefacts()['evaluate_v2_ranking'] == {'MAAC': 0.5}


# --- L2-004 retire_historical_outputs.ps1: ancestors right before each removal --

def test_l2_004_ancestor_swapped_to_link_after_verification_blocks_removal(tmp_path):
    root = tmp_path/'project'
    _write(root/'outputs/_drive_madrl/data.json', b'first target')
    second = 'citylearn_v3_madrl_full_20260615_074011_v4'
    _write(root/f'outputs/{second}/ckpt/actor.pt', b'second target')
    _write(root/'outputs/README.md', b'# outputs')
    plan = hi.inventory_historical_outputs(root, process_lister=NO_PROCESSES)
    assert plan.deletion_order[:2] == ('R-01', 'R-02')
    plan_path = tmp_path/'plan.json'
    plan_path.write_text(json.dumps(plan.as_dict(), indent=2), encoding='utf-8')
    moved = tmp_path/'moved_outputs'
    log = tmp_path/'retire.log'
    with open(log, 'wb') as stream:
        process = subprocess.Popen([*POWERSHELL, str(RETIRE), '-Phase', 'Execute', '-Manifest', str(plan_path),
                                    '-ProjectRoot', str(root)], cwd=REPO, stdout=stream, stderr=stream)
        try:
            # The first removal happens after the Python verifier has already
            # accepted every target; the ancestor changes inside that window.
            deadline = time.monotonic() + 300
            while (root/'outputs/_drive_madrl').exists():
                assert process.poll() is None, log.read_text(errors='replace')
                assert time.monotonic() < deadline
                time.sleep(0.001)
            while not moved.exists():
                try:
                    os.rename(root/'outputs', moved)
                except PermissionError:
                    assert time.monotonic() < deadline
                    time.sleep(0.001)
            _junction(moved, root/'outputs')
            swapped_in_time = (moved/second/'ckpt/actor.pt').is_file()
            process.wait(timeout=300)
        finally:
            if process.poll() is None:
                process.kill()
    assert swapped_in_time, 'the script reached the second target before the swap; window not exercised'
    try:
        assert (moved/second/'ckpt/actor.pt').read_bytes() == b'second target'
        outcome = {t['target_id']: t for t in json.loads(
            (tmp_path/'retirement_result.json').read_text(encoding='utf-8'))['targets']}
        assert outcome['R-01']['status'] == 'deleted'
        assert outcome['R-02']['status'] == 'failed'
        assert any('reparse' in reason for reason in outcome['R-02']['reasons'])
    finally:
        os.rmdir(root/'outputs')  # removes the junction itself, never its target


# --- L2-007 audit_duplicate_files.py: consumers at verification time -------------

GENERATOR = 'import math\n\n\ndef build(values):\n    total = sum(values)\n    return math.sqrt(total)\n'
CANONICAL = 'tools/colab/build_notebook.py'
REDUNDANT = 'tools/colab/build_notebook_old.py'


def _consolidation_tree(tmp_path, files):
    root = tmp_path/'project'
    for rel, payload in files.items():
        _write(root/rel, payload)
    registry = _write(root/'governance/repository_layout.yaml', yaml.safe_dump({
        'schema_version': 1,
        'consolidation': {'canonical_sources': {'notebook.generator': CANONICAL}}}))
    inventory = adf.find_duplicate_candidates(root, registry)
    return root, registry, adf.build_canonicalization_plan(inventory, []).as_dict()


@pytest.mark.parametrize('rel,text', [
    ('tools/new_consumer.py', 'from tools.colab.build_notebook_old import build\n'),
    ('docs/guide.md', f'Run `{REDUNDANT}` first.\n'),
    ('scripts/run.ps1', f'& python {REDUNDANT.replace("/", chr(92))}\n'),
])
def test_l2_007_consumer_added_after_plan_blocks_delete(tmp_path, rel, text):
    root, registry, plan = _consolidation_tree(tmp_path, {CANONICAL: GENERATOR, REDUNDANT: GENERATOR})
    [before] = adf.verify_plan(plan, root, registry)
    assert before['decision'] == 'delete', before['reasons']
    _write(root/rel, text)
    [after] = adf.verify_plan(plan, root, registry)
    assert after['decision'] == 'blocked'
    assert after['absolute_path'] is None
    assert any('active consumers' in reason and rel in reason for reason in after['reasons'])


def test_l2_007_records_and_unchanged_group_members_are_not_new_consumers(tmp_path):
    third = 'tools/colab/build_notebook_bak.py'
    payload = GENERATOR + f'# clones: {REDUNDANT} {third}\n'
    root, registry, plan = _consolidation_tree(tmp_path, {CANONICAL: payload, REDUNDANT: payload, third: payload})
    assert sorted(row['path'] for row in plan['removed_paths']) == [third, REDUNDANT]
    _write(root/'docs/audits/note.md', f'Historical mention of {REDUNDANT}.\n')
    assert [d['decision'] for d in adf.verify_plan(plan, root, registry)] == ['delete', 'delete']


def test_l2_007_group_member_edited_to_consume_is_blocked(tmp_path):
    third = 'tools/colab/build_notebook_bak.py'
    root, registry, plan = _consolidation_tree(tmp_path, {CANONICAL: GENERATOR, REDUNDANT: GENERATOR,
                                                          third: GENERATOR})
    _write(root/third, GENERATOR + f'# now depends on {REDUNDANT}\n')
    decisions = {d['path']: d for d in adf.verify_plan(plan, root, registry)}
    assert decisions[third]['decision'] == 'blocked'
    assert decisions[REDUNDANT]['decision'] == 'blocked'


# --- L2-008 / L2-009 historical_inventory.py ------------------------------------

@pytest.fixture
def no_read_spies(monkeypatch):
    calls = []
    real_walk, real_hash = hi._walk_files, hi._sha256_file

    def walk(top):
        calls.append(('walk', Path(top)))
        return real_walk(top)

    def digest(path):
        calls.append(('hash', Path(path)))
        return real_hash(path)

    monkeypatch.setattr(hi, '_walk_files', walk)
    monkeypatch.setattr(hi, '_sha256_file', digest)
    return calls


def test_l2_008_reparse_ancestor_stops_walk_and_hash(tmp_path, no_read_spies):
    root = tmp_path/'project'
    root.mkdir()
    elsewhere = tmp_path/'elsewhere'
    _write(elsewhere/'_drive_madrl/secret.bin', b'external bytes')
    _write(elsewhere/'orchestration-tests.xml', b'<external/>')
    _junction(elsewhere, root/'outputs')
    plan = hi.inventory_historical_outputs(root, process_lister=NO_PROCESSES)
    by_id = {t.target_id: t for t in plan.targets}
    for target_id in ('R-01', 'R-07'):
        assert by_id[target_id].decision == 'blocked'
        assert 'reparse_point_ancestor' in by_id[target_id].reasons
        assert by_id[target_id].files == () and by_id[target_id].total_bytes == 0
    assert no_read_spies == []


def test_l2_008_regular_tree_is_still_inventoried(tmp_path, no_read_spies):
    root = tmp_path/'project'
    _write(root/'outputs/_drive_madrl/data.json', b'bytes')
    target = {t.target_id: t for t in hi.inventory_historical_outputs(root, process_lister=NO_PROCESSES).targets}['R-01']
    assert target.decision == 'delete' and target.total_bytes == 5
    assert [kind for kind, _ in no_read_spies] == ['walk', 'hash']


def test_l2_009_scan_consumers_does_not_follow_file_links(tmp_path, monkeypatch):
    root = tmp_path/'project'
    outside = _write(tmp_path/'elsewhere/secret.py', "ROOT = 'outputs/_drive_madrl'\n")
    _write(root/'tools/real_consumer.py', "ROOT = 'outputs/_drive_madrl'\n")
    link = root/'tools/linked_consumer.py'
    try:
        os.symlink(outside, link)
    except OSError:
        # Creating file symlinks needs a privilege this account may lack. The
        # regular file then stands for the link: only the link test identifies it.
        shutil.copyfile(outside, link)
        real_is_reparse = hi._is_reparse
        monkeypatch.setattr(hi, '_is_reparse', lambda path: Path(path) == link or real_is_reparse(path))
    found = hi.scan_consumers(root, (('R-01', 'outputs/_drive_madrl'),))
    assert [row['path'] for row in found] == ['tools/real_consumer.py']


# --- L2-011 prune_artifacts.ps1: mirrors deleted only on equal content ----------

def _prune_sandbox(tmp_path):
    """A full repository-shaped tree with its own copy of the script."""
    project = tmp_path/'project'
    script = project/'tools/training/prune_artifacts.ps1'
    script.parent.mkdir(parents=True)
    shutil.copyfile(PRUNE, script)
    output_root = project/'outputs/run'
    runs = {}
    metadata = json.dumps({'timeseries_csv_root': 'timeseries.csv', 'trace_csv_root': 'trace.csv',
                           'results_json_root': 'results.json'})
    canonical = ['data/results.json', 'data/training_summary.json', 'data/checkpoint_manifest.json',
                 'data/artifact_audit.json', 'data/timeseries.csv', 'data/trace.csv',
                 'figures/figures_manifest.json', 'figures/tables/episode_summary.csv',
                 'figures/tables/axis_baseline_comparison.csv', 'figures/tables/agent_reward_summary.md']
    for algorithm in ('happo', 'masac', 'matd3', 'maac'):
        for scenario in ('E1', 'E2', 'E3'):
            run = output_root/algorithm/f'{scenario}_seed_0'
            runs[algorithm, scenario] = run
            for rel in canonical:
                _write(run/rel, metadata if rel.endswith('.json') else f'{rel}\n')
            for episode in range(1, 6):
                _write(run/f'checkpoints/checkpoint_episode_{episode}.pt', b'weights')
    return script, runs


def _prune(script, *args):
    return subprocess.run([*POWERSHELL, str(script), '-OutputRoot', 'outputs\\run', *args],
                          capture_output=True, text=True, cwd=script.parents[2], timeout=300)


def test_l2_011_divergent_mirror_survives_apply_and_identical_is_removed(tmp_path):
    script, runs = _prune_sandbox(tmp_path)
    run = runs['happo', 'E1']
    divergent = _write(run/'timeseries.csv', 'unique version of the series\n')
    divergent_json = _write(run/'results.json', '{"unique": "version", "statistical_comparison_dir": "kept"}')
    identical = _write(run/'trace.csv', (run/'data/trace.csv').read_bytes())
    canonical_series = (run/'data/timeseries.csv').read_bytes()
    result = _prune(script, '-Apply')
    assert result.returncode == 0, result.stdout + result.stderr
    assert divergent.read_text() == 'unique version of the series\n'
    assert divergent_json.read_text() == '{"unique": "version", "statistical_comparison_dir": "kept"}'
    assert not identical.exists()
    assert (run/'data/timeseries.csv').read_bytes() == canonical_series
    payload = json.loads((run/'data/results.json').read_text(encoding='utf-8-sig'))
    assert payload['timeseries_csv_root'] == 'timeseries.csv'
    assert payload['results_json_root'] == 'results.json'
    assert payload['trace_csv_root'] is None
    other = json.loads((runs['maac', 'E3']/'data/results.json').read_text(encoding='utf-8-sig'))
    assert other['timeseries_csv_root'] is None


def test_l2_011_dry_run_lists_only_identical_mirrors(tmp_path):
    script, runs = _prune_sandbox(tmp_path)
    run = runs['masac', 'E2']
    divergent = _write(run/'timeseries.csv', 'different\n')
    identical = _write(run/'trace.csv', (run/'data/trace.csv').read_bytes())
    result = _prune(script)
    assert result.returncode == 0, result.stdout + result.stderr
    assert 'Candidates: 1 ' in result.stdout
    assert divergent.is_file() and identical.is_file()


# --- L2-015 orchestrate_citylearn_dataset.py: one dataset per build --------------

def _orchestrate(tmp_path, *args):
    manifest = tmp_path/'evidence/manifest.json'
    result = subprocess.run([sys.executable, '-B', str(ORCHESTRATE), '--dry-run', '--skip-project-context-check',
                             '--manifest-out', str(manifest), *args],
                            capture_output=True, text=True, cwd=REPO, timeout=120)
    return result, manifest


def test_l2_015_custom_dataset_dir_is_refused_before_any_stage(tmp_path):
    custom = tmp_path/'campaign/dataset'
    result, manifest = _orchestrate(tmp_path, '--dataset-dir', str(custom))
    assert result.returncode != 0, result.stdout
    assert '--dataset-dir' in result.stderr
    assert not manifest.exists() and not custom.exists()


@pytest.mark.parametrize('args', [(), ('--dataset-dir', 'CityLearn/data/datasets/citylearn_iquitos_2023_2025'),
                                  ('--dataset-dir', 'CityLearn\\data\\datasets\\citylearn_iquitos_2023_2025')])
def test_l2_015_default_dataset_dir_still_plans_every_stage(tmp_path, args):
    result, manifest = _orchestrate(tmp_path, *args)
    assert result.returncode == 0, result.stderr
    stages = json.loads(manifest.read_text(encoding='utf-8'))['stages']
    assert stages and all(stage['status'] == 'dry_run' for stage in stages)
