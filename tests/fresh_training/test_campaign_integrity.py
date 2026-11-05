"""P01: every campaign input is verified before a learner or an evaluator runs.

A recorded hash that nobody recomputes is not identity. The manifest records
config, algorithm config, scenario catalog with its policies, KPI catalog,
dataset tree, dataset acceptance, split manifest, every split tree, normalizer
and own sources; a stage or an evaluation starts only after all of them are
recomputed and equal. Paths are contained by every ancestor, not by a prefix.
"""
import json
import os
import shutil
from pathlib import Path

import pytest
import yaml

from uc3m.application.training import fresh_campaign as fc
from uc3m.application.training import integrity
from uc3m.domain.campaigns import canonical_hash

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'
INPUTS = ('config', 'algorithm_config', 'scenario_catalog', 'objective_policies', 'kpi_catalog', 'dataset',
          'dataset_acceptance', 'split_manifest', 'split:train_2023', 'split:validation_2024',
          'split:test_2025', 'normalizer', 'source')


def _write(path: Path, text: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


def _synthetic_root(root: Path):
    """A minimal project tree with every kind of campaign input."""
    _write(root/'configs/experiments/c.yaml', 'campaign_id: x\n')
    _write(root/'configs/algorithms/native.yaml', 'algorithms: {}\n')
    _write(root/'configs/scenarios.yaml', yaml.safe_dump({'objective_policies_file': 'policies.yaml'}))
    _write(root/'configs/policies.yaml', 'E1: [0.6, 0.15, 0.25]\n')
    _write(root/'configs/evaluation/kpis.yaml', 'kpis: []\n')
    dataset = root/'data/campaigns/x'
    _write(dataset/'dataset/Building_1.csv', 'a,b\n1,2\n')
    _write(dataset/'dataset_acceptance.json', json.dumps({'dataset_verified': True}))
    splits = []
    for split in ('train_2023', 'validation_2024', 'test_2025'):
        _write(dataset/'splits'/split/'Building_1.csv', f'{split}\n')
        splits.append({'split_id': split, 'directory': split,
                       'sha256': integrity.tree_sha256(dataset/'splits'/split)})
    _write(dataset/'split_manifest.json', json.dumps({'splits': splits}))
    _write(dataset/'normalizer.json', json.dumps({'fit_scope': 'train_2023'}))
    _write(root/'uc3m/module.py', 'VALUE = 1\n')
    config = {'_path': str(root/'configs/experiments/c.yaml'), 'algorithm_config': 'configs/algorithms/native.yaml',
              'scenario_catalog': 'configs/scenarios.yaml', 'kpi_catalog': 'configs/evaluation/kpis.yaml',
              'dataset_root': 'data/campaigns/x', 'splits': ['train_2023', 'validation_2024', 'test_2025']}
    manifest = {'inputs': integrity.campaign_inputs(config, root)}
    manifest['identity'] = {'input_manifest_sha256': canonical_hash(manifest['inputs'])}
    manifest_path = _write(root/'outputs/campaigns/x/campaign_manifest.json', json.dumps(manifest))
    return manifest_path


def test_expected_input_hashes_cannot_be_rebound_without_changing_frozen_identity(tmp_path):
    manifest_path = _synthetic_root(tmp_path)
    (tmp_path/'uc3m/module.py').write_text('VALUE = 2\n', encoding='utf-8')
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    manifest['inputs']['source']['sha256'] = integrity.source_snapshot(tmp_path, scope='fresh')
    manifest_path.write_text(json.dumps(manifest), encoding='utf-8')
    result = integrity.verify_campaign_inputs(manifest_path, tmp_path)
    assert not result.accepted and 'input_manifest_mismatch' in result.reasons


_TAMPER = {
    'config': 'configs/experiments/c.yaml',
    'algorithm_config': 'configs/algorithms/native.yaml',
    'scenario_catalog': 'configs/scenarios.yaml',
    'objective_policies': 'configs/policies.yaml',
    'kpi_catalog': 'configs/evaluation/kpis.yaml',
    'dataset': 'data/campaigns/x/dataset/Building_1.csv',
    'dataset_acceptance': 'data/campaigns/x/dataset_acceptance.json',
    'split_manifest': 'data/campaigns/x/split_manifest.json',
    'split:train_2023': 'data/campaigns/x/splits/train_2023/Building_1.csv',
    'split:validation_2024': 'data/campaigns/x/splits/validation_2024/Building_1.csv',
    'split:test_2025': 'data/campaigns/x/splits/test_2025/Building_1.csv',
    'normalizer': 'data/campaigns/x/normalizer.json',
    'source': 'uc3m/module.py',
}


def test_untampered_inputs_are_accepted_with_every_hash(tmp_path):
    manifest_path = _synthetic_root(tmp_path)
    result = integrity.verify_campaign_inputs(manifest_path, tmp_path)
    assert result.accepted, result.reasons
    assert set(result.verified_hashes) == set(INPUTS)
    assert result.reasons == ()
    assert set(result.checks) >= set(INPUTS)


@pytest.mark.parametrize('name', sorted(_TAMPER))
def test_tampered_input_blocks_before_learner(tmp_path, name):
    manifest_path = _synthetic_root(tmp_path)
    target = tmp_path/_TAMPER[name]
    target.write_bytes(target.read_bytes() + b' ')
    result = integrity.verify_campaign_inputs(manifest_path, tmp_path)
    assert result.accepted is False
    assert f'{name}_changed' in result.reasons


def test_missing_input_record_is_not_acceptance(tmp_path):
    manifest_path = _synthetic_root(tmp_path)
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    del payload['inputs']['normalizer']
    manifest_path.write_text(json.dumps(payload), encoding='utf-8')
    result = integrity.verify_campaign_inputs(manifest_path, tmp_path)
    assert result.accepted is False and 'normalizer_unrecorded' in result.reasons
    del payload['inputs']
    manifest_path.write_text(json.dumps(payload), encoding='utf-8')
    assert 'inputs_unrecorded' in integrity.verify_campaign_inputs(manifest_path, tmp_path).reasons


def test_file_changing_during_verification_is_rejected(tmp_path, monkeypatch):
    manifest_path = _synthetic_root(tmp_path)
    config = tmp_path/_TAMPER['config']
    real = integrity._file_sha256
    calls = {'n': 0}

    def changing(path):
        digest = real(path)
        if Path(path) == config.resolve():
            calls['n'] += 1
            if calls['n'] == 1:
                config.write_text('campaign_id: changed\n', encoding='utf-8')
        return digest

    monkeypatch.setattr(integrity, '_file_sha256', changing)
    result = integrity.verify_campaign_inputs(manifest_path, tmp_path)
    assert result.accepted is False
    assert 'config_changed_during_verification' in result.reasons


@pytest.mark.parametrize('relative', ['C:/Windows/win.ini', 'D:\\other\\x.yaml', '\\\\server\\share\\x.yaml',
                                      '//server/share/x.yaml', '/etc/passwd', 'configs/../../x.yaml',
                                      'C:relative.yaml'])
def test_windows_absolute_unc_and_drive_paths_rejected(tmp_path, relative):
    with pytest.raises(ValueError):
        integrity.contained_path(tmp_path, relative)


def _make_junction(link: Path, target: Path):
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(target), str(link))
    else:  # pragma: no cover - POSIX hosts use a symlink
        os.symlink(target, link, target_is_directory=True)


def test_windows_absolute_unc_and_parent_junction_rejected(tmp_path):
    outside = tmp_path/'outside'
    _write(outside/'x.yaml', 'a: 1\n')
    root = tmp_path/'root'
    (root/'configs').mkdir(parents=True)
    _make_junction(root/'configs/linked', outside)
    # The file itself is a regular file; only an ancestor is a junction.
    assert (root/'configs/linked/x.yaml').is_file()
    with pytest.raises(ValueError, match='link'):
        integrity.contained_path(root, 'configs/linked/x.yaml')
    assert integrity.contained_path(root, 'configs') == (root/'configs').resolve()


def test_input_reached_through_junction_is_rejected(tmp_path):
    manifest_path = _synthetic_root(tmp_path)
    real = tmp_path/'elsewhere_split'
    shutil.move(str(tmp_path/'data/campaigns/x/splits/test_2025'), str(real))
    _make_junction(tmp_path/'data/campaigns/x/splits/test_2025', real)
    result = integrity.verify_campaign_inputs(manifest_path, tmp_path)
    assert result.accepted is False
    assert any(reason.startswith('split:test_2025_path_refused') for reason in result.reasons)


# --- Integration with the stage runner, the CLI and the evaluator ----------------------------------

def _counting_learner():
    calls = []

    def learner(treatment, attempt_root):
        calls.append(treatment['treatment_id'])
        return None
    return learner, calls


def test_prepared_manifest_records_every_input(tmp_path):
    manifest = fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    prices = manifest['endpoint_applicability']['price_files']
    assert set(manifest['inputs']) == set(INPUTS) | {f'endpoint_price:{i}' for i in range(len(prices))}
    assert canonical_hash(manifest['inputs']) == manifest['identity']['input_manifest_sha256']
    for index, price in enumerate(prices):
        assert manifest['inputs'][f'endpoint_price:{index}']['sha256'] == price['sha256']
    result = integrity.verify_campaign_inputs(tmp_path/'campaign/campaign_manifest.json', REPO)
    assert result.accepted, result.reasons


def test_tampered_recorded_input_blocks_stage_with_zero_learner_calls(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    manifest_path = tmp_path/'campaign/campaign_manifest.json'
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    payload['inputs']['split:train_2023']['sha256'] = '0'*64
    manifest_path.write_text(json.dumps(payload), encoding='utf-8')
    learner, calls = _counting_learner()
    attempts = REPO/'data/campaigns/iquitos_v5/attempts'
    before = sorted(attempts.rglob('try_*')) if attempts.exists() else []
    with pytest.raises(PermissionError, match='split:train_2023_changed'):
        fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True)
    assert calls == []
    after = sorted(attempts.rglob('try_*')) if attempts.exists() else []
    assert after == before


def test_campaign_config_outside_the_project_is_refused(tmp_path):
    config = fc.load_campaign_config(CONFIG, REPO)
    outside = tmp_path/'iquitos.yaml'
    outside.write_text(CONFIG.read_text(encoding='utf-8'), encoding='utf-8')
    with pytest.raises(ValueError, match='outside the project root'):
        integrity.campaign_inputs(dict(config, _path=str(outside)), REPO)


def test_cli_does_not_reuse_identity_of_changed_yaml(tmp_path, monkeypatch, capsys):
    # The YAML of a prepared campaign changed: its recorded hash no longer matches.
    from uc3m.application.training import cli
    artifacts = tmp_path/'campaign'
    monkeypatch.setattr(cli, '_artifact_root', lambda root, cfg: artifacts)
    assert cli.main(['--config', str(CONFIG), '--stage', 'prepare']) == 0
    capsys.readouterr()
    manifest_path = artifacts/'campaign_manifest.json'
    payload = json.loads(manifest_path.read_text(encoding='utf-8'))
    payload['inputs']['config']['sha256'] = '0'*64
    manifest_path.write_text(json.dumps(payload), encoding='utf-8')
    assert cli.main(['--config', str(CONFIG), '--stage', 'prepare']) == 2
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    assert report['status'] == 'campaign_inputs_changed'
    assert 'config_changed' in report['reasons']


def test_tampered_split_blocks_frozen_evaluation_before_environment(tmp_path, monkeypatch):
    from uc3m.adapters.citylearn import policy_inference
    campaign_root = tmp_path/'data/campaigns/x'
    _synthetic_root(tmp_path)
    split = campaign_root/'splits/validation_2024'
    (split/'Building_1.csv').write_text('changed\n', encoding='utf-8')
    built = []
    monkeypatch.setattr(policy_inference, 'load_normalizer', lambda path: built.append(path))
    with pytest.raises(PermissionError, match='split'):
        policy_inference.run_frozen_episode(split, object(), campaign_root)
    assert built == []
