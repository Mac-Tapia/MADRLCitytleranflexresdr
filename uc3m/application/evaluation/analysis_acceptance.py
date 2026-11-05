"""Readback of an explicitly registered analysis, backed by verified KPI rows."""
from __future__ import annotations

import dataclasses
import hashlib
import json
from pathlib import Path

from uc3m.application.dataset.provenance import contained_path
from uc3m.domain.campaigns import ALGORITHMS, canonical_hash


def protocol_for_stage(manifest_path: Path, stage: str, split: str):
    from uc3m.application.evaluation.fresh_analysis import FrozenProtocol
    from uc3m.application.training.attempt_trust import load_trust_contract
    manifest = json.loads(Path(manifest_path).read_text(encoding='utf-8'))
    contract = load_trust_contract(Path(manifest_path).parent, manifest['campaign_id'])
    rows = [r for r in contract.rows.values() if r['stage'] == stage]
    if contract.reasons or not rows:
        raise ValueError('analysis requires a verified nonempty stage plan')
    algorithms, scenarios = {r['algorithm'] for r in rows}, {r['scenario'] for r in rows}
    default = FrozenProtocol.default()
    from uc3m.application.evaluation.endpoint_applicability import not_applicable_endpoints
    return dataclasses.replace(default, split=split,
                               algorithms=tuple(a for a in ALGORITHMS if a in algorithms),
                               seeds=tuple(sorted({r['seed'] for r in rows})),
                               endpoints=tuple(e for e in default.endpoints if e[0] in scenarios),
                               confirmatory_endpoints=tuple(e for e in default.confirmatory_endpoints
                                                           if e[0] in scenarios),
                               not_applicable_endpoints=tuple(e for e in not_applicable_endpoints(manifest)
                                                              if e[0] in scenarios))


def verify_scientific_analysis(manifest_path: Path, *, analysis_manifest=None) -> bool:
    try:
        manifest_path = Path(manifest_path)
        root = manifest_path.parent
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        from uc3m.application.evaluation.test_access import verify_test_unlock
        verify_test_unlock(manifest_path)
        record = (manifest.get('analyses') or {}).get('confirm:test_2025')
        if not isinstance(record, dict):
            return False
        path = contained_path(root, record['path'])
        if analysis_manifest is not None and path != Path(analysis_manifest).resolve():
            return False
        if hashlib.sha256(path.read_bytes()).hexdigest() != record['sha256']:
            return False
        analysis = json.loads(path.read_text(encoding='utf-8'))
        if (analysis.get('campaign_id') != manifest.get('campaign_id')
                or analysis.get('spec_hash') != manifest.get('spec_hash')
                or analysis.get('stage') != 'confirm' or analysis.get('split') != 'test_2025'):
            return False
        files = analysis.get('files') or {}
        if set(files) != {'scientific_report.json', 'seed_table.json'}:
            return False
        for name, digest in files.items():
            file = contained_path(path.parent, name)
            if hashlib.sha256(file.read_bytes()).hexdigest() != digest:
                return False
        report = json.loads((path.parent/'scientific_report.json').read_text(encoding='utf-8'))
        table = json.loads((path.parent/'seed_table.json').read_text(encoding='utf-8'))
        if (report.get('campaign_id') != manifest['campaign_id']
                or report.get('status') != 'scientifically_complete'
                or report.get('coverage', {}).get('complete') is not True
                or report.get('decisions', {}).get('scientifically_complete') is not True
                or table.get('campaign_id') != manifest['campaign_id']):
            return False
        # Imports are delayed until a complete registered bundle exists; no model is loaded.
        from uc3m.application.evaluation.fresh_analysis import analyze_campaign
        from uc3m.application.evaluation.results_catalog import build_seed_table
        protocol = protocol_for_stage(manifest_path, 'confirm', 'test_2025')
        from uc3m.application.evaluation.fresh_analysis import FrozenProtocol
        from uc3m.application.evaluation.endpoint_applicability import not_applicable_endpoints
        if protocol != dataclasses.replace(FrozenProtocol.default(), split='test_2025',
                                           not_applicable_endpoints=not_applicable_endpoints(manifest)):
            return False
        if analysis.get('protocol') != json.loads(json.dumps(dataclasses.asdict(protocol))):
            return False
        actual = build_seed_table(manifest_path, stage='confirm', split='test_2025', require_full_split=True)
        if not actual.rows or canonical_hash([dict(r) for r in actual.rows]) != canonical_hash(table.get('rows')):
            return False
        expected = analyze_campaign(actual, protocol).as_dict()
        return (expected['decisions'].get('scientifically_complete') is True
                and canonical_hash({key: report.get(key) for key in expected}) == canonical_hash(expected))
    except (OSError, ValueError, KeyError, TypeError, AttributeError, RuntimeError):
        return False
