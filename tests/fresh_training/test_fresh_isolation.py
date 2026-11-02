"""T1: identity of a fresh campaign and isolation from prior-run inputs.

Every tree is new under tmp_path and every forbidden input is a sentinel file;
no historical data is loaded.
"""
import json
from pathlib import Path

import pytest

from tests.fresh_training.factories import fresh_spec, treatment_key
from uc3m.application.training import fresh_policy as fp
from uc3m.domain.campaigns import AttemptIdentity


def _write(path, payload=b'sentinel'):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


@pytest.fixture()
def project(tmp_path):
    root = tmp_path/'project'
    layout = Path(__file__).resolve().parents[2]/'governance/repository_layout.yaml'
    _write(root/'governance/repository_layout.yaml', layout.read_bytes())
    return root


def test_rejects_prior_run_input(project):
    spec = fresh_spec()
    roots = fp.create_campaign_roots(spec, project)
    retired = _write(project/'outputs/citylearn_v3_madrl_full_20260615_074011_v4/policy_0/actor.pt')
    with pytest.raises(fp.RetiredHistoricalInput):
        fp.assert_campaign_input(retired, 'checkpoint', spec, project_root=project)
    # A retired root is refused even after it was deleted from disk.
    with pytest.raises(fp.RetiredHistoricalInput):
        fp.assert_campaign_input(project/'outputs/_drive_madrl/kpis/a.csv', 'artifact', spec,
                                 project_root=project)
    old_dataset = _write(project/'CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json')
    with pytest.raises(fp.ForeignCampaignInput):
        fp.assert_campaign_input(old_dataset, 'dataset', spec, project_root=project)
    other = _write(project/'outputs/campaigns/other_campaign_v1/confirm/x/results.json')
    with pytest.raises(fp.ForeignCampaignInput):
        fp.assert_campaign_input(other, 'artifact', spec, project_root=project)
    pointer = _write(roots.artifacts/'latest_visible_training_output_root.txt')
    with pytest.raises(fp.ForeignCampaignInput):
        fp.assert_campaign_input(pointer, 'artifact', spec, project_root=project)
    ok = _write(roots.dataset/'dataset/schema.json', b'{}')
    assert fp.assert_campaign_input(ok, 'dataset', spec, project_root=project) == ok.resolve()
    with pytest.raises(fp.ForeignCampaignInput):
        fp.assert_campaign_input(ok, 'not_a_role', spec, project_root=project)


def test_rejects_symlink_escape(project, tmp_path):
    import _winapi
    spec = fresh_spec()
    roots = fp.create_campaign_roots(spec, project)
    outside = _write(tmp_path/'elsewhere/schema.json', b'{}')
    _winapi.CreateJunction(str(outside.parent), str(roots.dataset/'splits'))
    with pytest.raises(fp.ForeignCampaignInput) as raised:
        fp.assert_campaign_input(roots.dataset/'splits/schema.json', 'split', spec, project_root=project)
    assert 'link' in str(raised.value)


def test_fresh_root_must_not_exist(project):
    spec = fresh_spec()
    fp.create_campaign_roots(spec, project)
    with pytest.raises(fp.CampaignRootExists):
        fp.create_campaign_roots(spec, project)
    other = fresh_spec(campaign_id='fresh_test_v2', storage_alias='other_test')
    (project/'outputs/campaigns/other_test').mkdir(parents=True)
    with pytest.raises(fp.CampaignRootExists):
        fp.create_campaign_roots(other, project)
    assert not (project/'data/campaigns/other_test').exists()


def test_retry_starts_at_zero(project):
    spec = fresh_spec()
    roots = fp.create_campaign_roots(spec, project)
    key = treatment_key(spec)
    first, first_root = fp.create_attempt(roots, key)
    assert first == AttemptIdentity(key.treatment_id, 'a001', 1001)
    _write(first_root/'native/training_state.pt', b'episode 37 state')
    _write(first_root/'live_progress.json', json.dumps({'completed_episodes': 37}).encode())
    second, second_root = fp.create_attempt(roots, key)
    assert second.attempt_id == 'a002'
    assert second.initial_episode == 0 and second.fresh_start is True
    assert [p.name for p in second_root.iterdir()] == ['attempt.json']
    recorded = json.loads((second_root/'attempt.json').read_text(encoding='utf-8'))
    assert recorded['initial_episode'] == 0 and recorded['treatment'] == key.as_dict()
    # The interrupted attempt is preserved untouched as evidence.
    assert (first_root/'native/training_state.pt').read_bytes() == b'episode 37 state'
    with pytest.raises(ValueError):
        AttemptIdentity(key.treatment_id, 'a003', 1001, initial_episode=37)


def test_archive_covers_builders_evaluators_and_lockfile(tmp_path):
    from uc3m.application.training.preflight import archive_sources, fresh_source_paths
    root = tmp_path/'repo'
    expected = ['uc3m/domain/x.py', 'uc3m/application/training/cli.py', 'tools/dataset/build.py',
                'tools/eval/report.py', 'uv.lock', 'requirements.txt', 'configs/experiments/a.yaml',
                'governance/repository_layout.yaml', 'scripts/quality/run_gates.ps1']
    for name in expected:
        _write(root/name, b'content\r\n')
    forbidden = ['.env', 'configs/secrets.yaml', 'outputs/campaigns/c/results.json',
                 'tools/eval/token.key', 'data/campaigns/c/dataset/schema.json']
    for name in forbidden:
        _write(root/name, b'secret')
    paths = {p.relative_to(root).as_posix() for p in fresh_source_paths(root)}
    assert set(expected) <= paths
    assert not paths & set(forbidden)
    import zipfile
    from uc3m.application.training.preflight import source_snapshot
    digest = archive_sources(root, tmp_path/'snapshot.zip', scope='fresh')
    with zipfile.ZipFile(tmp_path/'snapshot.zip') as archive:
        assert set(archive.namelist()) == paths
        assert archive.read('uv.lock') == b'content\r\n'  # raw bytes are preserved
    # The archive digest is the run identity even on a CRLF (Windows) checkout.
    assert digest == source_snapshot(root, scope='fresh')
    assert source_snapshot(root) != digest  # the legacy scope is unchanged and narrower
