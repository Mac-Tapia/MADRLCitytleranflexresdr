"""Regression of unsafe defaults and import order, independent of native training."""
import inspect
import subprocess
import sys

import pytest


def test_multicriteria_requires_explicit_illustrative_opt_in():
    from uc3m.multicriteria.pipeline import run_selection_pipeline
    from uc3m.multicriteria.artifacts import load_decision_matrix
    for function in (run_selection_pipeline, load_decision_matrix):
        assert inspect.signature(function).parameters['allow_illustrative_fill'].default is False


def test_fresh_analysis_can_be_imported_before_legacy_pipeline():
    code = ('from uc3m.application.evaluation.fresh_analysis import FrozenProtocol; '
            'from uc3m.multicriteria import run_selection_pipeline; '
            'assert callable(run_selection_pipeline) and FrozenProtocol.default()')
    completed = subprocess.run([sys.executable, '-B', '-c', code], capture_output=True,
                               text=True, timeout=90)
    assert completed.returncode == 0, completed.stderr


def test_one_seed_describes_the_value_without_inventing_variance():
    from uc3m.application.evaluation.fresh_analysis import describe
    result = describe([0.25])
    assert result['mean'] == result['iqm'] == 0.25
    assert result['std'] is result['variance'] is result['cv'] is None
    assert result['uncertainty_status'] == 'insufficient_replicas'
    with pytest.raises(ValueError):
        describe([])
