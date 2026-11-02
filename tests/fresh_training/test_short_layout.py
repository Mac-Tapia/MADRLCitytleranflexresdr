"""Storage labels cannot replace or silently merge scientific identities."""
from dataclasses import replace
import json

import pytest

from tests.fresh_training.factories import fresh_spec, treatment_key
from uc3m.application.training import fresh_policy as fp
from uc3m.application.training import layout
from uc3m.domain.campaigns import CampaignSpec


def project(tmp_path):
    from pathlib import Path
    root = tmp_path/'project'
    (root/'governance').mkdir(parents=True)
    origin = Path(__file__).resolve().parents[2]/'governance/repository_layout.yaml'
    (root/'governance/repository_layout.yaml').write_bytes(origin.read_bytes())
    return root


def test_short_path_retains_real_seed_and_scenario(tmp_path):
    path = layout.treatment_path(tmp_path, 'confirm', 'HAPPO', 'E1', 1001, 1)
    assert path.relative_to(tmp_path).as_posix() == 'confirm/happo/e1/seed_1001/try_01'
    assert layout.treatment_path(tmp_path, 'hpo', 'HAPPO', 'E1', 901, 2, 'config_01').relative_to(tmp_path).as_posix() == 'hpo/happo/e1/config_01/seed_901/try_02'


@pytest.mark.parametrize('part', ['../escape', 'config_20260101', 'config/other'])
def test_candidate_cannot_escape_or_reintroduce_long_names(tmp_path, part):
    with pytest.raises(ValueError):
        layout.treatment_path(tmp_path, 'hpo', 'HAPPO', 'E1', 901, 1, part)


def test_campaign_alias_is_explicit_and_identity_independent(tmp_path):
    spec = fresh_spec()
    first = replace(spec, storage_alias='iquitos')
    second = replace(spec, storage_alias='iquitos_ev')
    assert first.spec_hash() == second.spec_hash()
    assert CampaignSpec.from_dict(first.as_dict()).storage_alias == 'iquitos'
    assert layout.campaign_path(first, tmp_path) == tmp_path/'iquitos'


def test_same_alias_other_fingerprint_rejected(tmp_path):
    root = project(tmp_path)
    spec = replace(fresh_spec(), storage_alias='iquitos')
    fp.create_campaign_roots(spec, root)
    other = replace(spec, campaign_id='other_campaign_v1')
    with pytest.raises(fp.CampaignRootExists):
        fp.create_campaign_roots(other, root)
    with pytest.raises(fp.ForeignCampaignInput):
        fp.open_campaign_roots(other, root)


def test_two_treatments_never_share_output(tmp_path):
    root = project(tmp_path)
    spec = replace(fresh_spec(), storage_alias='iquitos')
    roots = fp.create_campaign_roots(spec, root)
    first = treatment_key(spec, stage='hpo', seed=901)
    second = replace(first, resolved_config_hash='b'*64)
    _, one = fp.create_attempt(roots, first)
    _, two = fp.create_attempt(roots, second)
    assert one != two and 'config_01' in one.parts and 'config_02' in two.parts
    first_id, again = fp.create_attempt(roots, first)
    assert again.parent == one.parent and again.name == 'try_02'
    assert first_id.attempt_id == 'a002'
    assert json.loads((one/'attempt.json').read_text())['treatment'] == first.as_dict()


def test_confirm_treatment_conflict_cannot_be_renamed_away(tmp_path):
    root = project(tmp_path)
    spec = replace(fresh_spec(), storage_alias='iquitos')
    roots = fp.create_campaign_roots(spec, root)
    first = treatment_key(spec)
    fp.create_attempt(roots, first)
    with pytest.raises(ValueError, match='conflict'):
        fp.create_attempt(roots, replace(first, resolved_config_hash='b'*64))


def test_renaming_cannot_mutate_frozen_run(tmp_path):
    root = project(tmp_path)
    spec = replace(fresh_spec(), storage_alias='iquitos')
    roots = fp.create_campaign_roots(spec, root)
    manifest = roots.artifacts/'campaign.json'
    payload = json.loads(manifest.read_text())
    payload['frozen_at'] = '2026-11-01T00:00:00Z'
    manifest.write_text(json.dumps(payload))
    with pytest.raises(ValueError, match='frozen'):
        fp.create_attempt(roots, treatment_key(spec))


def test_path_based_digest_is_recomputed_before_freeze(tmp_path):
    from uc3m.application.training.preflight import hash_files
    before = tmp_path/'long.py'
    before.write_bytes(b'unchanged source\r\n')
    digest = hash_files(tmp_path, [before])
    after = tmp_path/'short.py'
    after.write_bytes(before.read_bytes())
    assert before.read_bytes() == after.read_bytes()
    assert hash_files(tmp_path, [after]) != digest


def test_tampered_treatment_path_cannot_escape_campaign(tmp_path):
    root = project(tmp_path)
    spec = replace(fresh_spec(), storage_alias='iquitos')
    roots = fp.create_campaign_roots(spec, root)
    key = treatment_key(spec)
    fp.create_attempt(roots, key)
    registry = roots.artifacts/'treatments.json'
    data = json.loads(registry.read_text())
    data['treatments'][0]['path'] = '../../../escaped'
    registry.write_text(json.dumps(data))
    with pytest.raises(ValueError, match='registry|path'):
        fp.create_attempt(roots, key)
    assert not (root/'escaped').exists()


def test_attempt_file_collision_returns_error(tmp_path):
    import subprocess
    import sys
    root = project(tmp_path)
    spec = replace(fresh_spec(), storage_alias='iquitos')
    roots = fp.create_campaign_roots(spec, root)
    key = treatment_key(spec)
    base = fp.attempt_base(roots, key)
    base.mkdir(parents=True)
    (base/'try_01').write_bytes(b'occupied by another role')
    code = ('from dataclasses import replace; from pathlib import Path; '
            'from tests.fresh_training.factories import fresh_spec,treatment_key; '
            'from uc3m.application.training import fresh_policy as f; '
            's=replace(fresh_spec(),storage_alias="iquitos"); '
            'r=f.open_campaign_roots(s,Path(__import__("sys").argv[1])); '
            'f.create_attempt(r,treatment_key(s))')
    result = subprocess.run([sys.executable, '-B', '-c', code, str(root)],
                            capture_output=True, text=True, timeout=5)
    assert result.returncode != 0 and 'occupied' in result.stderr
