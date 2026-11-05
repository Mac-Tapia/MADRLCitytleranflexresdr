"""Static readback of the current v1 workflow; no learner or service is started."""
from __future__ import annotations

import json
from pathlib import Path

from uc3m.application.dataset.provenance import contained_path
from uc3m.application.training.fresh_campaign import build_dag, load_campaign_config


def verify(root: Path):
    root = Path(root)
    workflow = json.loads((root/'docs/workflow_manifest.json').read_text(encoding='utf-8'))
    errors = []
    if workflow.get('schema_version') != 3:
        errors.append('workflow_is_not_current_v1_contract')
    for name, relative in (workflow.get('entrypoints') or {}).items():
        path = contained_path(root, relative)
        if not path.is_file():
            errors.append(f'missing_entrypoint:{name}')
    config = load_campaign_config(contained_path(root, workflow['config']), root)
    if config['dataset_root'] != workflow['dataset_root'] or config['campaign_id'] != workflow['campaign_id']:
        errors.append('workflow_configuration_mismatch')
    dataset = contained_path(root, workflow['dataset_root'])
    splits = json.loads((dataset/'split_manifest.json').read_text(encoding='utf-8'))
    normalizer = json.loads((dataset/'normalizer.json').read_text(encoding='utf-8'))
    recorded = {s['split_id']: s for s in splits['splits']}
    expected = {'train_2023': 8760, 'validation_2024': 8784, 'test_2025': 8760}
    if {name: row['rows'] for name, row in recorded.items()} != expected:
        errors.append('temporal_split_contract_mismatch')
    if normalizer.get('fit_scope') != 'train_2023' or normalizer.get('train_split_sha256') != recorded['train_2023']['sha256']:
        errors.append('normalizer_not_bound_to_training_split')
    for row in recorded.values():
        schema = contained_path(dataset, f"splits/{row['schema_path']}")
        if not schema.is_file():
            errors.append(f"missing_schema:{row['split_id']}")
        elif sum(b.get('include', True) for b in json.loads(schema.read_text(encoding='utf-8'))['buildings'].values()) != 17:
            errors.append(f"agent_count_mismatch:{row['split_id']}")
    notebook = contained_path(root, workflow['entrypoints']['colab'])
    if notebook.is_file():
        cells = json.loads(notebook.read_text(encoding='utf-8'))['cells']
        text = '\n'.join(''.join(c.get('source', [])) for c in cells)
        if 'uc3m.application.training.cli' not in text or 'configs/experiments/iquitos.yaml' not in text:
            errors.append('colab_not_wired_to_current_campaign')
    return {'schema_version': 3, 'ok': not errors, 'errors': errors,
            'scope': 'static_paths_config_split_metadata; not runtime or dataset-byte acceptance',
            'campaign_id': config['campaign_id'], 'budget': build_dag(config, root).budget(),
            'authorized_stages': config['resource_authorization']['authorized_stages'],
            'scientific_acceptance': False, 'operational_acceptance': False}
