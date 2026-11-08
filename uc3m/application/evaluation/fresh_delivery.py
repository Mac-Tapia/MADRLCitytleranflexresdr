"""Delivery of a fresh campaign: its own manifests, acceptance and statistics, with hashes (T11).

    python tools/eval/report_fresh_campaign.py --manifest outputs/campaigns/<alias>/campaign_manifest.json \
        --destination outputs/campaigns/<alias>/delivery --gate-report data/maintenance/gates/fresh_profile_X.json \
        [--seed-rows outputs/campaigns/<alias>/reports/seed_rows.json]

Nothing is looked up by name or date: every input is an explicit path of the
campaign. A file that names a retired historical root stops the delivery. The
state is one of rejected, implementation_ready_for_training,
trained_not_scientifically_complete or new_campaign_scientifically_complete; a
prepared campaign is never reported as trained and no single winner is required.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.evaluation.fresh_analysis import FrozenProtocol, SeedTable, analyze_campaign
from uc3m.application.training.fresh_acceptance import verify_fresh_acceptance
from uc3m.domain.campaigns import canonical_hash

DELIVERY_FILE = 'delivery_manifest.json'


@dataclass(frozen=True)
class DeliveryCheck:
    accepted: bool
    reasons: Tuple[str, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _retired_roots(manifest) -> Tuple[str, ...]:
    policy = manifest.get('input_policy')
    if (not isinstance(policy, dict) or canonical_hash(policy) != manifest.get('identity', {}).get('input_policy_sha256')
            or not isinstance(policy.get('retired_roots'), list)
            or not all(isinstance(root, str) and root for root in policy['retired_roots'])):
        raise ValueError('delivery needs the hash-bound input policy of the prepared campaign')
    return tuple(policy['retired_roots'])


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')


def build_fresh_delivery(manifest_path: Path, destination: Path, *, gate_report: Optional[Path] = None,
                         seed_rows: Optional[Sequence[dict]] = None, analysis_manifest: Optional[Path] = None) -> dict:
    manifest_path, destination = Path(manifest_path).resolve(), Path(destination).absolute()
    artifacts = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    campaign_id = manifest.get('campaign_id')
    if not isinstance(campaign_id, str) or not campaign_id:
        raise ValueError('a delivery needs the campaign_id of its manifest')
    if destination.exists():
        raise FileExistsError(f'{destination} exists; a delivery is never overwritten')
    # Acceptance resolves this explicit registry entry too. Resolve it here
    # before collecting inputs, so API/CLI never omit the accepted analysis.
    analyses = manifest.get('analyses', {})
    if not isinstance(analyses, dict):
        raise ValueError('analysis registry must be a mapping')
    analysis_record = analyses.get('confirm:test_2025')
    if 'confirm:test_2025' in analyses:
        if not isinstance(analysis_record, dict) or not {'path', 'sha256'} <= set(analysis_record):
            raise ValueError('registered analysis needs its explicit path and digest')
        registered_analysis = contained_path(artifacts, analysis_record['path'])
        if analysis_manifest is None:
            analysis_manifest = registered_analysis
        elif registered_analysis != Path(analysis_manifest).resolve():
            raise ValueError('delivery analysis differs from the registered confirmatory analysis')
        if not registered_analysis.is_file() or _sha256(registered_analysis) != analysis_record['sha256']:
            raise ValueError('registered analysis missing or modified')
    sources = [manifest_path, artifacts/'campaign.json']
    for stage, stage_record in (manifest.get('stages') or {}).items():
        sources.append(contained_path(artifacts, stage_record['path']))
        result = artifacts/'stages'/f'{stage}_result.json'
        if result.is_file():
            sources.append(result)
    freezes = (manifest.get('configuration_freezes') or {}).get('path')
    if freezes:
        sources.append(contained_path(artifacts, freezes))
    if analysis_manifest is not None:
        analysis_manifest = contained_path(artifacts, Path(analysis_manifest).resolve().relative_to(artifacts.resolve()).as_posix())
        analysis = json.loads(analysis_manifest.read_text(encoding='utf-8'))
        if analysis.get('campaign_id') != campaign_id or analysis.get('spec_hash') != manifest.get('spec_hash'):
            raise ValueError('analysis belongs to another campaign or protocol')
        if analysis_record is not None and (analysis.get('stage') != 'confirm' or analysis.get('split') != 'test_2025'):
            raise ValueError('registered analysis is not confirm:test_2025')
        analysis_files = analysis.get('files')
        if not isinstance(analysis_files, dict) or set(analysis_files) != {'scientific_report.json', 'seed_table.json'}:
            raise ValueError('analysis bundle requires scientific_report.json and seed_table.json')
        sources.append(analysis_manifest)
        for name, digest in analysis_files.items():
            path = contained_path(analysis_manifest.parent, name)
            if not path.is_file() or _sha256(path) != digest:
                raise ValueError('analysis artifact missing or modified')
            sources.append(path)
    retired = _retired_roots(manifest)
    for source in sources:
        text = source.read_text(encoding='utf-8') if source.is_file() else ''
        if source == manifest_path:
            payload = dict(manifest)
            payload.pop('input_policy', None)  # a prohibition is not an input to the experiment
            text = json.dumps(payload)
        named = [root for root in retired if root.casefold() in text.replace('\\\\', '/').replace('\\', '/').casefold()]
        if named:
            raise PermissionError(f'{source.name} names retired roots {named}; not delivered')
    acceptance = verify_fresh_acceptance(manifest_path, gate_report=gate_report, analysis_manifest=analysis_manifest)
    table_payload, report_payload = None, None
    if analysis_manifest is not None:
        table_payload = json.loads((analysis_manifest.parent/'seed_table.json').read_text(encoding='utf-8'))
        report_payload = json.loads((analysis_manifest.parent/'scientific_report.json').read_text(encoding='utf-8'))
        if seed_rows is not None and canonical_hash(list(seed_rows)) != canonical_hash(table_payload.get('rows')):
            raise ValueError('delivery seed rows differ from the registered analysis')
    elif seed_rows is not None:
        table = SeedTable.from_rows(seed_rows)
        if {r['campaign_id'] for r in table.rows} - {campaign_id}:
            raise ValueError('seed rows belong to another campaign')
        table_payload = {'campaign_id': campaign_id, 'rows': [dict(r) for r in table.rows]}
        report_payload = {'campaign_id': campaign_id, **analyze_campaign(table, FrozenProtocol.default()).as_dict()}
    staging = destination.with_name(destination.name + '.partial_' + uuid.uuid4().hex)
    staging.mkdir(parents=True)
    for source in sources:
        if source.is_file():
            target = staging/source.relative_to(artifacts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    _write(staging/'acceptance.json', acceptance.as_dict())
    if table_payload is not None:
        _write(staging/'seed_table.json', table_payload)
        _write(staging/'scientific_report.json', report_payload)
    if not acceptance.software_acceptance:
        state = 'rejected'
    elif acceptance.scientific_acceptance:
        state = 'new_campaign_scientifically_complete'
    elif acceptance.status == 'trained_not_evaluated':
        state = 'trained_not_scientifically_complete'
    else:
        state = 'implementation_ready_for_training'
    files = sorted(p for p in staging.rglob('*') if p.is_file())
    delivery = {'schema_version': 1, 'campaign_id': campaign_id, 'state': state,
                'payload_scope': 'manifests_and_statistics; native checkpoints remain in their attempt storage',
                'trained': acceptance.status in ('trained_not_evaluated', 'scientifically_complete'),
                'acceptance': acceptance.as_dict(),
                'files': [{'path': p.relative_to(staging).as_posix(), 'sha256': _sha256(p)} for p in files]}
    _write(staging/DELIVERY_FILE, delivery)
    if not verify_delivery(staging).accepted:
        raise ValueError('delivery readback failed; unpublished staging preserved')
    if destination.exists():
        raise FileExistsError(f'{destination} exists; a delivery is never overwritten')
    staging.rename(destination)
    return delivery


def verify_delivery(destination: Path) -> DeliveryCheck:
    destination = Path(destination)
    delivery = json.loads((destination/DELIVERY_FILE).read_text(encoding='utf-8'))
    reasons = []
    for row in delivery['files']:
        try:
            path = contained_path(destination, row['path'])
        except (ValueError, TypeError):
            reasons.append(f"untrusted_path:{row.get('path')}")
            continue
        if not path.is_file() or path.is_symlink():
            reasons.append(f"missing:{row['path']}")
        elif _sha256(path) != row['sha256']:
            reasons.append(f"hash_mismatch:{row['path']}")
    return DeliveryCheck(not reasons, tuple(reasons))


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--destination', type=Path, required=True)
    parser.add_argument('--gate-report', type=Path, default=None)
    parser.add_argument('--analysis-manifest', type=Path, default=None)
    parser.add_argument('--seed-rows', type=Path, default=None)
    args = parser.parse_args(argv)
    rows = json.loads(args.seed_rows.read_text(encoding='utf-8')) if args.seed_rows else None
    delivery = build_fresh_delivery(args.manifest, args.destination, gate_report=args.gate_report, seed_rows=rows,
                                    analysis_manifest=args.analysis_manifest)
    print(json.dumps({'state': delivery['state'], 'files': len(delivery['files'])}))
    return 0 if delivery['state'] != 'rejected' else 1


if __name__ == '__main__':
    raise SystemExit(main())
