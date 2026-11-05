"""Budget custody must precede learning, not depend on an absent stage result.

Uses the real budget planner and real filesystem copies, with explicitly
synthetic optimizer evidence to exercise cut/reuse semantics without training.
"""
import json
from pathlib import Path

import pytest

from tests.fresh_training.test_attempt_acceptance import _stage_learner
from tests.fresh_training.test_stage_phases import MAAC_RULE
from uc3m.application.training import cli, drive_sync, fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'


def test_first_stage_cut_restores_and_reuses_completed_attempt_with_frozen_budget(tmp_path):
    source, drive, target = tmp_path/'source', tmp_path/'drive', tmp_path/'restored'
    manifest = fc.prepare_campaign(CONFIG, REPO, artifact_root=source)
    manifest_path = source/'campaign_manifest.json'
    config = fc.load_campaign_config(CONFIG, REPO)
    cli._stage_budget(manifest, source, config, {'ram_gib': 400.0, 'vram_gib': 200.0, 'cpu_count': 8},
                       'pilot', buffer_rules=MAAC_RULE)
    assert (source/'stages/pilot_budget.json').is_file()
    synthetic = _stage_learner(fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml'), 17)

    def cut_after_first_completed_treatment(row, root):
        if row['algorithm'] == 'MAAC':
            raise KeyboardInterrupt('runtime lost during second phase, before stage result')
        if row.get('phase_buffer') is not None:
            assert (root/'phase_budget.json').is_file(), 'proof must precede learning'
        return synthetic(row, root)

    with pytest.raises(KeyboardInterrupt):
        fc.run_stage(manifest_path, 'pilot', cut_after_first_completed_treatment, REPO,
                     authorized=True, workers=1)
    assert not (source/'stages/pilot_result.json').exists()
    assert len(list(source.rglob('completion.json'))) == 3
    assert not drive_sync.sync_finished_attempts(source, drive)['conflicts']
    restored = drive_sync.restore_finished_attempts(drive, target, manifest['campaign_id'])
    assert len(restored['restored_complete']) == 3 and not restored['rejected'], restored

    def no_retraining_of_the_restored_model(row, root):
        assert row['algorithm'] == 'MAAC', 'all three completed models must be reused after this cut'
        return synthetic(row, root)

    result = fc.run_stage(target/'campaign_manifest.json', 'pilot', no_retraining_of_the_restored_model,
                          REPO, authorized=True, workers=1)
    assert result['status'] == 'training_complete'
    assert sum(r['reused_verified_attempt'] for r in result['treatments']) == 3
    proof = json.loads(next((target/'pilot/matd3').rglob('phase_budget.json')).read_text(encoding='utf-8'))
    assert proof['campaign_id'] == manifest['campaign_id'] and proof['spec_hash'] == manifest['spec_hash']
