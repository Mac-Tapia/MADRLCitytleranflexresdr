"""Seed-resampling parity against a transparent scalar reference."""
import numpy as np
import pytest

from uc3m.application.evaluation.fresh_analysis import bootstrap_ci, iqm


@pytest.mark.parametrize('statistic', ['mean', 'median', 'iqm'])
@pytest.mark.parametrize('count', [3, 7, 12])
def test_seed_bootstrap_matches_the_scalar_resampling_rule(statistic, count):
    values = np.array([0.3*i-0.75 for i in range(count)])
    rng = np.random.default_rng(701)
    statistic_fn = {'mean': np.mean, 'median': np.median, 'iqm': iqm}[statistic]
    samples = [statistic_fn(values[rng.integers(0, count, count)]) for _ in range(211)]
    expected = tuple(float(v) for v in np.quantile(samples, [0.025, 0.975]))
    assert bootstrap_ci(values, statistic=statistic, resamples=211, seed=701) == pytest.approx(expected, abs=1e-14)


@pytest.mark.parametrize('parameters', [{'resamples': 0}, {'resamples': False}, {'level': 0.0},
    {'level': 1.0}, {'level': float('nan')}, {'statistic': 'unregistered'}])
def test_invalid_confidence_protocol_is_refused(parameters):
    with pytest.raises(ValueError):
        bootstrap_ci([0.1, 0.2, 0.3], **parameters)
