"""Single local benchmark with scalar mathematical parity, not an SLA."""
import json
from pathlib import Path
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from uc3m.application.evaluation.fresh_analysis import bootstrap_ci, iqm  # noqa: E402


def main():
    values = np.array([0.3*i-0.75 for i in range(12)])
    results = []
    for name, statistic in (('mean', np.mean), ('median', np.median), ('iqm', iqm)):
        rng = np.random.default_rng(7001)
        before = time.perf_counter()
        samples = [statistic(values[rng.integers(0, len(values), len(values))]) for _ in range(10000)]
        expected = np.quantile(samples, [0.025, 0.975])
        scalar_seconds = time.perf_counter()-before
        before = time.perf_counter()
        result = bootstrap_ci(values, statistic=name)
        batch_seconds = time.perf_counter()-before
        np.testing.assert_allclose(result, expected, rtol=0, atol=1e-14)
        results.append({'statistic': name, 'n_seeds': 12, 'resamples': 10000,
                        'scalar_seconds': scalar_seconds, 'batch_seconds': batch_seconds,
                        'ratio_scalar_over_batch': scalar_seconds/batch_seconds,
                        'parity_atol': 1e-14})
    output = ROOT/'data/maintenance/integracion/c20261101i01/I07/bootstrap_benchmark.json'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({'scope': 'one local timing under concurrent load, not a capacity guarantee',
                                  'results': results}, indent=2), encoding='utf-8')
    print(json.dumps(results))


if __name__ == '__main__':
    main()
