"""Fresh campaign acceptance from strict, re-read, hash-bound evidence."""
from __future__ import annotations

from pathlib import Path
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from uc3m.application.training.attempt_evidence import _count, _inside, _read, attempt_evidence_reasons
from uc3m.application.training.attempt_trust import (
    load_trust_contract, select_trusted_attempt, treatment_trust_reasons,
)
from uc3m.application.training.gate_report import verify_gate_report
from uc3m.domain.campaigns import canonical_hash

FRESH_PREFIX = 'fresh_'
__all__ = ['AcceptanceReport', 'attempt_evidence_reasons', 'select_trusted_attempt',
           'treatment_trust_reasons', 'load_trust_contract', 'verify_fresh_acceptance']


@dataclass(frozen=True)
class AcceptanceReport:
    campaign_id: Optional[str]
    status: str
    software_acceptance: bool
    scientific_acceptance: bool
    checks: Dict[str, bool]
    reasons: Tuple[str, ...]

    def as_dict(self):
        return {'campaign_id': self.campaign_id, 'status': self.status,
                'software_acceptance': self.software_acceptance,
                'scientific_acceptance': self.scientific_acceptance,
                'checks': dict(self.checks), 'reasons': list(self.reasons)}


def verify_fresh_acceptance(manifest_path: Path, *, gate_report: Optional[Path] = None,
                            analysis_manifest: Optional[Path] = None) -> AcceptanceReport:
    manifest_path = Path(manifest_path)
    artifacts = manifest_path.parent
    manifest = _read(manifest_path) or {}
    campaign_id = manifest.get('campaign_id')
    reasons, checks = [], {}
    identity = manifest.get('identity')
    checks['fresh_identity'] = (manifest.get('schema_version') == 1 and isinstance(campaign_id, str)
                                and campaign_id.startswith(FRESH_PREFIX) and isinstance(identity, dict))
    if not checks['fresh_identity']:
        reasons.append('not_a_fresh_campaign')
    claim = _read(artifacts/'campaign.json') if _inside(artifacts/'campaign.json', artifacts) else {}
    checks['campaign_claim'] = bool(claim and claim.get('campaign_id') == campaign_id
                                    and claim.get('spec_hash') == manifest.get('spec_hash'))
    if not checks['campaign_claim']:
        reasons.append('campaign_claim_mismatch')
    try:
        checks['spec_hash'] = checks['fresh_identity'] and canonical_hash(identity) == manifest.get('spec_hash')
        contract = load_trust_contract(artifacts, campaign_id)
    except (ValueError, TypeError):
        return AcceptanceReport(campaign_id, 'rejected', False, False, checks, ('malformed_campaign_contract',))
    if not checks['spec_hash']:
        reasons.append('spec_hash_mismatch')
    checks['stage_manifests'] = not contract.reasons
    reasons.extend(contract.reasons)
    checks['gate_clean'] = bool(gate_report and verify_gate_report(gate_report, manifest))
    if not checks['gate_clean']:
        reasons.append('gate_not_clean')

    verified_models, stages_complete = 0, bool(contract.stages)
    model_reasons = []
    for stage, planned in contract.stages.items():
        result_path = artifacts/'stages'/f'{stage}_result.json'
        result = _read(result_path) if _inside(result_path, artifacts) else None
        if not result:
            stages_complete = False
            if result_path.exists():
                model_reasons.append(f'invalid_stage_result:{stage}')
            continue
        if result.get('campaign_id') != campaign_id or result.get('stage') != stage:
            model_reasons.append(f'foreign_stage_result:{stage}')
            stages_complete = False
            continue
        treatments = result.get('treatments')
        if not isinstance(treatments, list) or any(not isinstance(row, dict) for row in treatments):
            model_reasons.append(f'treatment_coverage_mismatch:{stage}')
            stages_complete = False
            continue
        names = [row.get('treatment_id') for row in treatments]
        completed = sum(row.get('training_complete') is True for row in treatments)
        exact = (all(isinstance(name, str) for name in names) and len(names) == len(set(names))
                 and set(names) == set(planned) and _count(result.get('planned_treatments'))
                 and result['planned_treatments'] == len(planned)
                 and _count(result.get('completed_treatments')) and result['completed_treatments'] == completed)
        complete = exact and completed == len(planned) and result.get('status') == 'training_complete'
        if not exact or (result.get('status') == 'training_complete' and not complete):
            model_reasons.append(f'treatment_coverage_mismatch:{stage}')
        stages_complete = stages_complete and complete
        for treatment in treatments:
            if treatment.get('training_complete') is not True:
                continue
            found = treatment_trust_reasons(artifacts, campaign_id, treatment, contract=contract)
            model_reasons.extend(found)
            verified_models += not found
    checks['trusted_models'] = not model_reasons
    reasons.extend(model_reasons)
    software = all(checks.values())
    from uc3m.application.evaluation.analysis_acceptance import verify_scientific_analysis
    scientific_report = verify_scientific_analysis(manifest_path, analysis_manifest=analysis_manifest)
    if not verified_models:
        status = 'not_ready_no_model'
        reasons.append('no_verified_model')
    elif not stages_complete or not scientific_report:
        status = 'trained_not_evaluated'
        reasons.append('scientific_evaluation_pending')
    else:
        status = 'scientifically_complete'
    if not software:
        status = 'rejected'
    return AcceptanceReport(campaign_id, status, software, software and status == 'scientifically_complete',
                            checks, tuple(reasons))
