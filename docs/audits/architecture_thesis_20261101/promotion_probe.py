"""Synthetic acceptance boundary probes in disposable temporaries, no learning.

Reuses the existing gate test's minimal campaign fixture. Its checkpoint is
opaque bytes; the acceptance code hashes it and never deserializes it here.
"""
import hashlib
import json
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent


def main():
    from tests.fresh_training.test_security_and_acceptance import _campaign, _passed_gate, CAMPAIGN_ID
    from uc3m.application.training.fresh_acceptance import verify_fresh_acceptance
    reports = {}
    with tempfile.TemporaryDirectory(prefix='madrl_promotion_audit_') as temp:
        base = Path(temp)
        manifest = _campaign(base)
        gate = _passed_gate(base)
        root = manifest.parent
        reports['baseline_minimal_fixture'] = verify_fresh_acceptance(manifest, gate_report=gate).as_dict()
        evidence = next(root.rglob('learning_evidence.json'))
        payload = json.loads(evidence.read_text(encoding='utf-8'))
        payload['successful_optimizer_updates_by_owner'] = {'actor_agent0': 0}
        payload['env_steps'] = 0
        payload['completed_episodes'] = 0
        payload['attempt_id'] = 'another_attempt'
        evidence.write_text(json.dumps(payload), encoding='utf-8')
        reports['zero_updates_steps_and_foreign_attempt'] = verify_fresh_acceptance(manifest, gate_report=gate).as_dict()
        (root/'reports').mkdir()
        (root/'reports/scientific_report.json').write_text(json.dumps({
            'campaign_id': CAMPAIGN_ID, 'status': 'scientifically_complete'}), encoding='utf-8')
        reports['minimal_scientific_report_no_statistics'] = verify_fresh_acceptance(manifest, gate_report=gate).as_dict()
        stage = root/'stages/confirm.json'
        data = json.loads(stage.read_text(encoding='utf-8'))
        data['treatments'].append({'treatment_id': 'planned_but_never_run'})
        stage.write_text(json.dumps(data), encoding='utf-8')
        meta = json.loads(manifest.read_text(encoding='utf-8'))
        meta['stages']['confirm'].update(treatments=2, sha256=hashlib.sha256(stage.read_bytes()).hexdigest())
        manifest.write_text(json.dumps(meta), encoding='utf-8')
        reports['two_planned_one_reported'] = verify_fresh_acceptance(manifest, gate_report=gate).as_dict()
        from uc3m.application.pipeline import deliver
        fresh = _campaign(base/'pipeline_delivery')
        # No KPI reports: the seed table is legitimately empty and the report
        # will describe missing evidence. The CLI path also has no gate input.
        delivery = deliver(fresh, base/'delivery')
        reports['pipeline_deliver_without_gate_input'] = {
            'status': delivery['state'],
            'software_acceptance': delivery['acceptance']['software_acceptance'],
            'scientific_acceptance': delivery['acceptance']['scientific_acceptance'],
            'reasons': delivery['acceptance']['reasons']}
    result = {'scope': 'synthetic local contract probes only; not a campaign or a trained model', 'reports': reports}
    (OUT/'promotion_probe.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({name: {'status': row['status'], 'software_acceptance': row['software_acceptance'],
                           'scientific_acceptance': row['scientific_acceptance']} for name, row in reports.items()}, indent=2))


if __name__ == '__main__':
    main()
