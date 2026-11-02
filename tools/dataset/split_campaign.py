"""Freeze the splits and the train-only normalizer of a fresh campaign (T3).

Reads data/campaigns/<alias>/dataset and writes, next to it:
  splits/{train_2023,validation_2024,test_2025}/   self-contained CityLearn datasets
  split_manifest.json                              hashes, windows and fit scope
  normalizer.json                                  observation bounds fitted on train_2023 only
  split_smoke.json                                 reset/step evidence on every split
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from uc3m.adapters.citylearn import fresh_observations as fo  # noqa: E402
from uc3m.application.dataset import splits as sp  # noqa: E402
from uc3m.application.training.layout import storage_label  # noqa: E402


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--storage-alias', required=True)
    args = parser.parse_args(argv)
    root = ROOT/'data/campaigns'/storage_label(args.storage_alias)
    acceptance = json.loads((root/'dataset_acceptance.json').read_text(encoding='utf-8'))
    if not acceptance.get('dataset_verified'):
        raise SystemExit('dataset_verified is false; splits are frozen only on an accepted dataset')
    sizes = fo.design_device_sizes(root/'dataset')
    manifest = sp.materialize_splits(root/'dataset', root/'splits', campaign_id=acceptance['campaign_id'],
                                     fixed_devices=sizes)
    payload = manifest.as_dict()
    payload['dataset_hash'] = acceptance['dataset_hash']
    payload['fixed_device_sizes'] = sizes
    (root/'split_manifest.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    spec = sp.fit_normalizer(manifest, fo.citylearn_limits, fo.citylearn_periodic_limits)
    (root/'normalizer.json').write_text(json.dumps(spec.as_dict(), indent=2), encoding='utf-8')
    smoke = fo.smoke_splits(root)
    (root/'split_smoke.json').write_text(json.dumps(smoke, indent=2), encoding='utf-8')
    print(json.dumps({'splits': [(s.split_id, s.rows, s.sha256[:12]) for s in manifest.splits],
                      'normalizer': spec.train_fit_hash, 'smoke': smoke}))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
