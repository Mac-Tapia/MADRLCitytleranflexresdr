"""Delivery of a fresh campaign: its own manifests, acceptance and statistics, with hashes (T11).

    python tools/eval/report_fresh_campaign.py --manifest outputs/campaigns/iquitos_v1/campaign_manifest.json \
        --destination outputs/campaigns/iquitos_v1/delivery --gate-report data/maintenance/gates/fresh_profile_X.json \
        [--seed-rows outputs/campaigns/iquitos_v1/reports/seed_rows.json]

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
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Sequence, Tuple

import yaml

from uc3m.application.evaluation.fresh_analysis import FrozenProtocol, SeedTable, analyze_campaign
from uc3m.application.training.fresh_acceptance import verify_fresh_acceptance

REPO = Path(__file__).resolve().parents[2]
DELIVERY_FILE = 'delivery_manifest.json'


@dataclass(frozen=True)
class DeliveryCheck:
    accepted: bool
    reasons: Tuple[str, ...]


def _sha256(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _retired_roots() -> Tuple[str, ...]:
    layout = yaml.safe_load((REPO/'governance/repository_layout.yaml').read_text(encoding='utf-8'))
    return tuple(layout.get('retired_historical_roots', {}).values()) + tuple(layout.get('forbidden_input_roots', []))


def _write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, default=str), encoding='utf-8')


def build_fresh_delivery(manifest_path: Path, destination: Path, *, gate_report: Optional[Path] = None,
                         seed_rows: Optional[Sequence[dict]] = None) -> dict:
    manifest_path, destination = Path(manifest_path), Path(destination)
    artifacts = manifest_path.parent
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    campaign_id = manifest.get('campaign_id')
    if not isinstance(campaign_id, str) or not campaign_id:
        raise ValueError('a delivery needs the campaign_id of its manifest')
    if destination.exists():
        raise FileExistsError(f'{destination} exists; a delivery is never overwritten')
    sources = [manifest_path, artifacts/'campaign.json']
    for stage, record in (manifest.get('stages') or {}).items():
        sources.append(artifacts/record['path'])
        result = artifacts/'stages'/f'{stage}_result.json'
        if result.is_file():
            sources.append(result)
    freezes = (manifest.get('configuration_freezes') or {}).get('path')
    if freezes:
        sources.append(artifacts/freezes)
    retired = _retired_roots()
    for source in sources:
        text = source.read_text(encoding='utf-8') if source.is_file() else ''
        named = [root for root in retired if root in text.replace('\\\\', '/').replace('\\', '/')]
        if named:
            raise PermissionError(f'{source.name} names retired roots {named}; not delivered')
    acceptance = verify_fresh_acceptance(manifest_path, gate_report=gate_report)
    destination.mkdir(parents=True)
    for source in sources:
        if source.is_file():
            target = destination/source.relative_to(artifacts)
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
    _write(destination/'acceptance.json', acceptance.as_dict())
    if seed_rows is not None:
        table = SeedTable.from_rows(seed_rows)
        if {r['campaign_id'] for r in table.rows} - {campaign_id}:
            raise ValueError('seed rows belong to another campaign')
        _write(destination/'seed_table.json', {'campaign_id': campaign_id, 'rows': [dict(r) for r in table.rows]})
        _write(destination/'scientific_report.json',
               {'campaign_id': campaign_id, **analyze_campaign(table, FrozenProtocol.default()).as_dict()})
    if not acceptance.software_acceptance:
        state = 'rejected'
    elif acceptance.scientific_acceptance:
        state = 'new_campaign_scientifically_complete'
    elif acceptance.status == 'trained_not_evaluated':
        state = 'trained_not_scientifically_complete'
    else:
        state = 'implementation_ready_for_training'
    files = sorted(p for p in destination.rglob('*') if p.is_file())
    delivery = {'schema_version': 1, 'campaign_id': campaign_id, 'state': state,
                'trained': acceptance.status in ('trained_not_evaluated', 'scientifically_complete'),
                'acceptance': acceptance.as_dict(),
                'files': [{'path': p.relative_to(destination).as_posix(), 'sha256': _sha256(p)} for p in files]}
    _write(destination/DELIVERY_FILE, delivery)
    return delivery


def verify_delivery(destination: Path) -> DeliveryCheck:
    destination = Path(destination)
    delivery = json.loads((destination/DELIVERY_FILE).read_text(encoding='utf-8'))
    reasons = []
    for row in delivery['files']:
        path = destination/row['path']
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
    parser.add_argument('--seed-rows', type=Path, default=None)
    args = parser.parse_args(argv)
    rows = json.loads(args.seed_rows.read_text(encoding='utf-8')) if args.seed_rows else None
    delivery = build_fresh_delivery(args.manifest, args.destination, gate_report=args.gate_report, seed_rows=rows)
    print(json.dumps({'state': delivery['state'], 'files': len(delivery['files'])}))
    return 0 if delivery['state'] != 'rejected' else 1


if __name__ == '__main__':
    raise SystemExit(main())
