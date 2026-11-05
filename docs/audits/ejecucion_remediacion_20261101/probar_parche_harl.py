"""Real Torch CPU/dtype/CUDA roundtrip, original versus in-memory candidate.

No external file is edited. This is a serialization regression, not training.
"""
import hashlib
import io
import json
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
preflight = json.loads((OUT/'harl_patch_preflight.json').read_text(encoding='utf-8'))


def inspect(source, device, default_dtype):
    scope = {'__name__': 'audited_valuenorm'}
    exec(compile(source, 'audited_valuenorm', 'exec'), scope)
    dtype_before = torch.get_default_dtype()
    try:
        torch.set_default_dtype(default_dtype)
        norm = scope['ValueNorm'](1, device=torch.device(device))
        norm.update(np.asarray([[1.0], [2.0], [3.0]], dtype=np.float32))
        keys = sorted(norm.state_dict())
        expected = ['debiasing_term', 'running_mean', 'running_mean_sq']
        if keys != expected:
            return {'accepted': False, 'keys': keys, 'reason': 'unregistered_normalizer_state'}
        saved = io.BytesIO()
        torch.save(norm.state_dict(), saved)
        saved.seek(0)
        restored = scope['ValueNorm'](1, device=torch.device(device))
        restored.load_state_dict(torch.load(saved, map_location=device, weights_only=False))
        for name in expected:
            torch.testing.assert_close(getattr(norm, name), getattr(restored, name))
            assert torch.isfinite(getattr(restored, name)).all()
            assert not getattr(restored, name).requires_grad
        x = np.asarray([[4.0]], dtype=np.float32)
        np.testing.assert_allclose(restored.denormalize(norm.normalize(x)), x, atol=1e-5)
        return {'accepted': True, 'keys': keys, 'roundtrip_and_denormalization_equal': True}
    finally:
        torch.set_default_dtype(dtype_before)


def main():
    original = (ROOT/preflight['target']).read_text(encoding='utf-8')
    applied = hashlib.sha256(original.encode('utf-8')).hexdigest() == preflight['after_sha256_lf']
    if applied:
        application = json.loads((OUT/'dependency_application.json').read_text(encoding='utf-8'))
        receipt = next(row for row in application if row['target'] == preflight['target'])
        original = (ROOT/receipt['original_bytes_backup']).read_text(encoding='utf-8')
    candidate = (ROOT/preflight['candidate_path']).read_text(encoding='utf-8')
    assert hashlib.sha256(original.encode('utf-8')).hexdigest() == preflight['before_sha256_lf']
    assert hashlib.sha256(candidate.encode('utf-8')).hexdigest() == preflight['after_sha256_lf']
    assert torch.cuda.is_available(), 'This explicit GPU probe requires real CUDA; no skip or mock.'
    rows = []
    for device, dtype in [('cpu', torch.float32), ('cpu', torch.float64), ('cuda', torch.float32)]:
        rows.append({'device': device, 'default_dtype': str(dtype),
                     'original': inspect(original, device, dtype),
                     'candidate': inspect(candidate, device, dtype)})
    assert rows[0]['original']['accepted'] is True
    assert rows[1]['original']['accepted'] is False and rows[2]['original']['accepted'] is False
    assert all(row['candidate']['accepted'] for row in rows)
    result = {'dependency_modified_by_probe': False, 'candidate_applied_on_disk': applied,
              'torch_version': torch.__version__,
              'gpu': torch.cuda.get_device_name(0), 'comparisons': rows}
    filename = 'harl_valuenorm_applied_probe.json' if applied else 'harl_valuenorm_probe.json'
    target = ROOT/'data/maintenance/integracion/c20261101i01/I15'/filename
    target.write_text(json.dumps(result, indent=2)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
