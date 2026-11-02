"""T0: inventory and retirement of R-01..R-07 on disposable trees only.

No test here touches the real historical outputs: every tree is built fresh
under pytest's tmp_path, and the PowerShell mutation path is exercised against
that sandbox.
"""
import json
import subprocess
from pathlib import Path

import pytest

from tools.ops import historical_inventory as hi

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO/'scripts/maintenance/retire_historical_outputs.ps1'
NO_PROCESSES = lambda: ()  # noqa: E731 - explicit empty process snapshot


def _write(path, payload=b'x'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _sandbox(tmp_path):
    root = tmp_path/'project'
    _write(root/'outputs/_drive_madrl/full_data/HAPPO/E1/data/results.json', b'{"a": 1}')
    _write(root/'outputs/citylearn_v3_madrl_full_20260615_074011_v4/ckpt/actor.pt', b'weights')
    _write(root/'outputs/orchestration-tests.xml', b'<testsuites/>')
    _write(root/'outputs/README.md', b'# outputs')
    _write(root/'governance/repository_layout.yaml',
           (REPO/'governance/repository_layout.yaml').read_bytes())
    return root


def _execute(root, plan_path):
    return subprocess.run(
        ['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', str(SCRIPT),
         '-Phase', 'Execute', '-Manifest', str(plan_path), '-ProjectRoot', str(root)],
        cwd=REPO, capture_output=True, text=True, timeout=600)


def _plan(root, **kwargs):
    kwargs.setdefault('process_lister', NO_PROCESSES)
    return hi.inventory_historical_outputs(root, **kwargs)


def _save(plan, path):
    path.write_text(json.dumps(plan.as_dict(), indent=2), encoding='utf-8')
    return path


def _result(plan_path):
    return json.loads((plan_path.parent/'retirement_result.json').read_text(encoding='utf-8'))


def test_only_allowlisted_historical_roots_can_be_deleted(tmp_path):
    root = _sandbox(tmp_path)
    keep = _write(root/'outputs/other_run/results.json')
    plan = _plan(root)
    assert {t.target_id for t in plan.targets} == {target_id for target_id, _ in hi.ALLOWLIST}
    assert all(not t.relative_path.startswith('outputs/other_run') for t in plan.targets)
    completed = _execute(root, _save(plan, tmp_path/'plan.json'))
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert not (root/'outputs/_drive_madrl').exists()
    assert keep.is_file()

    # A plan widened by hand to another output root is refused before any deletion.
    forged = plan.as_dict()
    forged['targets'][0]['relative_path'] = 'outputs/other_run'
    forged_path = tmp_path/'forged'/'plan.json'
    forged_path.parent.mkdir()
    forged_path.write_text(json.dumps(forged), encoding='utf-8')
    refused = _execute(root, forged_path)
    assert refused.returncode != 0
    assert keep.is_file()


def test_protected_primary_and_new_paths_survive(tmp_path):
    root = _sandbox(tmp_path)
    protected = [
        _write(root/'CityLearn/data/buildingcsv/B01.csv'),
        _write(root/'data/campaigns/fresh_x/provenance.json'),
        _write(root/'outputs/campaigns/fresh_x/campaign_manifest.json'),
        _write(root/'docs/tesis.docx'),
        root/'outputs/README.md',
    ]
    plan_path = _save(_plan(root), tmp_path/'plan.json')
    completed = _execute(root, plan_path)
    assert completed.returncode == 0, completed.stdout + completed.stderr
    assert all(path.is_file() for path in protected)
    result = _result(plan_path)
    assert result['protected_paths_verified'] is True
    states = {t['target_id']: t['status'] for t in result['targets']}
    assert states['R-01'] == 'deleted' and states['R-03'] == 'already_absent'


def test_reparse_point_escape_rejected(tmp_path):
    import _winapi
    root = _sandbox(tmp_path)
    outside = _write(tmp_path/'elsewhere/precious.csv')
    link = root/'outputs/madrl_v3_20260627_164047'
    _winapi.CreateJunction(str(outside.parent), str(link))
    nested_outside = _write(tmp_path/'elsewhere2/precious.csv')
    _winapi.CreateJunction(str(nested_outside.parent),
                           str(root/'outputs/citylearn_v3_madrl_full_20260615_074011_v4/linked'))
    plan = _plan(root)
    by_id = {t.target_id: t for t in plan.targets}
    assert by_id['R-03'].decision == 'blocked' and 'reparse_point' in by_id['R-03'].reasons
    assert by_id['R-02'].decision == 'blocked' and 'reparse_point_descendant' in by_id['R-02'].reasons
    completed = _execute(root, _save(plan, tmp_path/'plan.json'))
    assert completed.returncode != 0  # blocked targets keep the retirement incomplete
    assert outside.is_file() and nested_outside.is_file()
    assert link.exists()


def test_changed_inventory_blocks_delete(tmp_path):
    root = _sandbox(tmp_path)
    plan_path = _save(_plan(root), tmp_path/'plan.json')
    changed = root/'outputs/citylearn_v3_madrl_full_20260615_074011_v4/ckpt/actor.pt'
    changed.write_bytes(b'concurrent writer')
    completed = _execute(root, plan_path)
    assert completed.returncode != 0
    assert changed.is_file()
    states = {t['target_id']: t for t in _result(plan_path)['targets']}
    assert states['R-02']['status'] == 'blocked'
    assert 'inventory_changed' in states['R-02']['reasons']


def test_retired_inputs_not_opened(tmp_path, monkeypatch):
    from uc3m.application.training.fresh_policy import RetiredHistoricalInput, assert_campaign_input
    from tests.fresh_training.factories import fresh_spec
    root = _sandbox(tmp_path)
    _write(root/'outputs/dataset_cache/citylearn_csv_0.pkl', b'not a pickle')
    retired = root/'outputs/dataset_cache/citylearn_csv_0.pkl'
    opened = []
    real_open = Path.open
    monkeypatch.setattr(Path, 'open', lambda self, *a, **k: opened.append(self) or real_open(self, *a, **k))
    spec = fresh_spec()
    with pytest.raises(RetiredHistoricalInput) as raised:
        assert_campaign_input(retired, 'dataset', spec, project_root=root)
    assert raised.value.code == 'retired_historical_input'
    assert retired not in opened

    # The inventory hashes bytes but never deserializes a pickle or a checkpoint.
    import pickle
    import torch
    monkeypatch.setattr(pickle, 'load', lambda *a, **k: pytest.fail('pickle.load called'))
    monkeypatch.setattr(torch, 'load', lambda *a, **k: pytest.fail('torch.load called'))
    plan = _plan(root)
    assert any(t.target_id == 'R-06' and t.files for t in plan.targets)


def test_duplicate_nested_targets_not_double_deleted(tmp_path):
    root = _sandbox(tmp_path)
    nested = (('R-01', 'outputs/_drive_madrl'), ('R-01b', 'outputs/_drive_madrl/full_data'))
    plan = _plan(root, allowlist=nested)
    by_id = {t.target_id: t for t in plan.targets}
    assert by_id['R-01b'].decision == 'covered_by_parent'
    assert plan.deletion_order == ('R-01',)
    # Only the canonical closed list can be executed.
    completed = _execute(root, _save(plan, tmp_path/'plan.json'))
    assert completed.returncode != 0
    assert (root/'outputs/_drive_madrl/full_data').is_dir()


def test_active_consumer_blocks_its_target(tmp_path):
    root = _sandbox(tmp_path)
    _write(root/'outputs/dataset_cache/citylearn_csv_0.pkl')
    _write(root/'scripts/quality/run_gates.ps1',
           b"$report = Join-Path $root 'outputs/orchestration-tests.xml'\n")
    _write(root/'tools/eval/old_analysis.py', b"ROOT = 'outputs/_drive_madrl'\n")
    _write(root/'governance/retention.yaml', b'note: "gitignore excludes outputs/_drive_madrl/**"\n')
    trainer = lambda: ({'pid': 4242, 'name': 'python.exe',  # noqa: E731
                        'command_line': 'python -B train_citylearn_v3_matd3.py --episodes 2'},)
    plan = _plan(root, process_lister=trainer)
    by_id = {t.target_id: t for t in plan.targets}
    assert by_id['R-07'].decision == 'blocked' and 'active_profile_consumer' in by_id['R-07'].reasons
    assert by_id['R-06'].decision == 'blocked' and 'active_process' in by_id['R-06'].reasons
    # Archival tools outside the fresh DAG are recorded but do not block deletion.
    assert by_id['R-01'].decision == 'delete'
    archival = [c for c in plan.consumers if c['path'] == 'tools/eval/old_analysis.py']
    assert archival and archival[0]['classification'] == 'archival_tool'
    # A registry note naming a retired root is recorded, it does not read or write it.
    registry = [c for c in plan.consumers if c['path'] == 'governance/retention.yaml']
    assert registry and registry[0]['classification'] == 'registry'
    # Command lines are not persisted, only the matching token and PID.
    assert 'command_line' not in json.dumps(plan.as_dict())
