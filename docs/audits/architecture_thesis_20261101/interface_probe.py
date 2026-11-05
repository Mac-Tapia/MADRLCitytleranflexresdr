"""Read-only interface and dataset-generation comparison; no environment steps."""
import hashlib
import json
from pathlib import Path
import sys

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))


def main():
    from uc3m.adapters.algorithms.native_entrypoint import load_native_common
    common = load_native_common(ROOT)
    measured = json.loads((OUT/'runtime_probe.json').read_text(encoding='utf-8'))['environments'][0]['contract']
    table, metadata = common.build_discrete_action_table(action_bins=3, action_dim=measured['max_action_dim'], mode='axis')
    action = {'source': 'actual native build_discrete_action_table; defaults of MASAC/MAAC parsers',
              'metadata': metadata, 'max_nonzero_components': int(np.count_nonzero(table, axis=1).max()),
              'projection_before_clipping': {str(dim): {'unique_vectors': len(np.unique(table[:, :dim], axis=0)),
                  'zero_vector_ids': int(np.sum(np.count_nonzero(table[:, :dim], axis=1) == 0))}
                  for dim in sorted(set(measured['action_dims'].values()))}}
    datasets = []
    for alias in ('iquitos_v1', 'iquitos_v2', 'iquitos_v3'):
        path = ROOT/'data/campaigns'/alias/'dataset/schema.json'
        schema = json.loads(path.read_text(encoding='utf-8'))
        datasets.append({'alias': alias, 'schema_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'chargers': sum(len(b.get('chargers', {})) for b in schema['buildings'].values()),
            'vehicles': len(schema.get('electric_vehicles_def', {})),
            'market_enabled': schema.get('community_market', {}).get('enabled'),
            'active_action_types': [a for a,v in schema['actions'].items() if v.get('active')]})
    result = {'scope': 'interface cardinality and schema metadata; not learning or physical acceptance',
              'discrete_actions': action, 'datasets': datasets}
    (OUT/'interface_probe.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps({'datasets': datasets, 'discrete_table_shape': list(table.shape),
                     'max_nonzero': action['max_nonzero_components'],
                     'five_dim_projection': action['projection_before_clipping']['5']}, indent=2))


if __name__ == '__main__':
    main()
