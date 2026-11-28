"""The Colab overlay bundle carries the frozen campaign and no retired root.

The only training notebook is examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb
(owner decision 2026-11-28); tools/colab/build_colab_bundle.py builds the ZIP that its
cell 1.2 applies. The tutorial cells are covered by tests/fresh_training/test_tutorial_notebooks.py
and tests/ops/test_colab_notebook_cells.py.
"""
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/colab'))

import build_colab_bundle as builder  # noqa: E402


def test_bundle_carries_the_frozen_campaign_and_no_retired_root():
    paths = {p.relative_to(REPO).as_posix() for p in builder.bundle_paths(REPO, builder.campaign_from_config(builder.CAMPAIGN_CONFIG)[1])}
    config = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
    active = (REPO/config['dataset_root']).relative_to(REPO).as_posix()
    assert f'{active}/splits/train_2023/schema.json' in paths
    assert f'{active}/normalizer.json' in paths
    assert 'configs/experiments/iquitos.yaml' in paths and 'uc3m/application/training/cli.py' in paths
    assert 'uc3m/application/training/drive_sync.py' in paths
    assert not any(p.startswith(('outputs/', 'CityLearn/data/datasets/', f'{active}/raw/'))
                   for p in paths)


def test_bundle_alias_and_dataset_come_from_the_campaign_config(tmp_path):
    root = tmp_path/'project'
    (root/'configs/experiments').mkdir(parents=True)
    (root/'configs/experiments/iquitos.yaml').write_text(
        'storage_alias: other_v9\ncampaign_id: fresh_other_v9\ndataset_root: data/campaigns/other_v9\n'
        'splits: [train_2023]\n', encoding='utf-8')
    dataset = root/'data/campaigns/other_v9'
    (dataset/'splits/train_2023').mkdir(parents=True)
    (dataset/'dataset_acceptance.json').write_text('{"dataset_hash": "x"}', encoding='utf-8')
    (dataset/'splits/train_2023/schema.json').write_text('{}', encoding='utf-8')
    alias, dataset_root = builder.campaign_from_config(root/'configs/experiments/iquitos.yaml')
    assert (alias, dataset_root) == ('other_v9', 'data/campaigns/other_v9')
    assert builder.campaign_identity(root)['campaign_id'] == 'fresh_other_v9'
    paths = {p.relative_to(root).as_posix() for p in builder.bundle_paths(root, dataset_root)}
    assert 'data/campaigns/other_v9/splits/train_2023/schema.json' in paths
    assert not any('iquitos_v5' in p for p in paths)


def test_no_second_training_notebook_exists():
    notebooks = sorted(p.name for p in (REPO/'examples_madrl_v3').glob('*.ipynb'))
    assert 'madrl_citylearn_v3_modular_colab.ipynb' not in notebooks
    assert builder.TUTORIAL.is_file()
