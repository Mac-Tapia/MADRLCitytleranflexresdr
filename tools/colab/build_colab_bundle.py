"""Build the Colab overlay bundle used by the training tutorial.

The only training notebook is examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb (owner
decision 2026-11-28); its cell 1.2 applies this bundle in /content. The bundle carries the
current code, configs and the frozen campaign dataset with a sha256 per file, plus
tools/colab/colab_session.py; it never carries outputs, environments or credentials.

    python tools/colab/build_colab_bundle.py [--output ZIP] [--config YAML]
"""
from __future__ import annotations

import argparse
import hashlib
import json
import zipfile
from pathlib import Path

from uc3m.application.training.context import repository_revision
from uc3m.application.training.preflight import (_FRESH_FOLDERS, _FRESH_ROOT_FILES, _FRESH_SUFFIXES,
                                                 fresh_source_paths, source_snapshot)

ROOT = Path(__file__).resolve().parents[2]
TUTORIAL = ROOT/'examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb'
BUNDLE = ROOT/'outputs/colab_delivery/colab_modular_overlay.zip'
CAMPAIGN_CONFIG = ROOT/'configs/experiments/iquitos.yaml'
SESSION_MODULE = ROOT/'tools/colab/colab_session.py'


def campaign_identity(root: Path) -> dict:
    """alias, campaign_id, dataset_root and splits of the campaign config (single source)."""
    import yaml
    payload = yaml.safe_load((Path(root)/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
    return {'alias': str(payload['storage_alias']), 'campaign_id': str(payload['campaign_id']),
            'dataset_root': str(payload['dataset_root']), 'splits': list(payload['splits'])}


def campaign_from_config(config_path: Path):
    """(storage_alias, dataset_root) of a campaign config file."""
    import yaml
    payload = yaml.safe_load(Path(config_path).read_text(encoding='utf-8'))
    return str(payload['storage_alias']), str(payload['dataset_root'])


def bundle_paths(root: Path, dataset_root: str):
    """Code, configs and the frozen campaign (dataset, splits, normalizer, manifests); no raw or outputs."""
    campaign = Path(root)/dataset_root
    paths = set(fresh_source_paths(root))
    for path in campaign.rglob('*'):
        relative = path.relative_to(campaign).parts
        if path.is_file() and relative and relative[0] not in {'raw', 'audit'}:
            paths.add(path)
    return sorted(paths)


def source_scope():
    """What colab_session.apply_overlay/verify_checkout treat as source (same rule as fresh_source_paths)."""
    return {'prefixes': list(_FRESH_FOLDERS) + list(_FRESH_ROOT_FILES), 'suffixes': sorted(_FRESH_SUFFIXES),
            'json_prefixes': [folder for folder in _FRESH_FOLDERS if folder.endswith('configs')]}


def main(argv=None):
    import yaml

    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--output', type=Path, default=BUNDLE)
    parser.add_argument('--config', type=Path, default=CAMPAIGN_CONFIG)
    args = parser.parse_args(argv)
    commit, submodules = repository_revision(ROOT)
    identity = campaign_identity(ROOT)
    alias, dataset_root = campaign_from_config(args.config)
    acceptance = json.loads((ROOT/dataset_root/'dataset_acceptance.json').read_text(encoding='utf-8'))
    paths = bundle_paths(ROOT, dataset_root)
    config = yaml.safe_load(args.config.read_text(encoding='utf-8'))
    if 'bill_tariffs' in config:
        from uc3m.application.dataset.provenance import contained_path
        paths = sorted({*paths, contained_path(ROOT, config['bill_tariffs'])})
    files = {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    scope = source_scope()
    manifest = {'commit': commit, 'submodules': submodules, 'dataset_hash': acceptance['dataset_hash'],
                'source_sha256': source_snapshot(ROOT, scope='fresh'), 'source_scope': scope['prefixes'],
                'source_suffixes': scope['suffixes'], 'source_json_prefixes': scope['json_prefixes'],
                'files': files, 'campaign_id': identity['campaign_id'], 'alias': alias,
                'dataset_root': dataset_root}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as bundle:
        bundle.writestr('colab_bundle_manifest.json', json.dumps(manifest, indent=2))
        bundle.write(SESSION_MODULE, 'colab_session.py')
        for path in paths:
            bundle.write(path, path.relative_to(ROOT).as_posix())
    print(json.dumps({'bundle': str(args.output), 'bundle_bytes': args.output.stat().st_size,
                      'files': len(files)}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
