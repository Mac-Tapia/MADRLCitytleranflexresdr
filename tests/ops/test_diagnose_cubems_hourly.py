"""Pure parts of the training-only CU-BEMS diagnosis (card thermal-g14). No raw data needed."""
import importlib.util
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

PATH = Path(__file__).resolve().parents[2]/'tools/validation/diagnose_cubems_hourly.py'
spec = importlib.util.spec_from_file_location('diagnose_cubems_hourly', PATH)
tool = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)


def test_hide_test_removes_every_test_period_row():
    index = pd.date_range('2019-06-30 22:00', periods=4, freq='h')
    kept = tool.hide_test(pd.DataFrame({'a': range(4)}, index=index))
    assert kept.index.max() < pd.Timestamp('2019-07-01') and len(kept) == 2


def test_g14_matches_the_definition_with_one_degree_of_freedom_removed():
    stats = tool.g14([2.0, 4.0, 6.0], [1.0, 4.0, 6.0])
    assert stats['nmbe_pct'] == pytest.approx(100*1/(2*4))
    assert stats['cvrmse_pct'] == pytest.approx(100*np.sqrt(1/2)/4)


def test_profile_benchmark_learns_only_from_the_fit_hours():
    fit_index = pd.date_range('2019-03-04', periods=24*7, freq='h')
    fit = pd.Series(np.arange(24*7, dtype=float), index=fit_index)
    target_index = fit_index + pd.Timedelta(days=7)
    pred = tool.profile_benchmark(fit, pd.Series(1e6, index=target_index))
    assert np.array_equal(pred.to_numpy(), fit.to_numpy())


def test_day_scaled_oracle_matches_daily_energy_and_keeps_zero_days_at_zero():
    index = pd.date_range('2019-04-01', periods=48, freq='h')
    profile = pd.Series(np.ones(48), index=index)
    measured = pd.Series(np.r_[np.full(24, 2.0), np.zeros(24)], index=index)
    out = tool.day_scaled(profile, measured)
    assert out.iloc[:24].sum() == pytest.approx(48.0) and out.iloc[24:].sum() == 0.0


def test_cycling_counts_transitions_only_in_steady_hours():
    index = pd.date_range('2019-04-01', periods=120, freq='min')
    power = np.ones(120)*10.0
    power[59] = 0.0                                             # hour 0: one dip, 59 of 60 min on
    power[60:90] = 0.0                                          # hour 1: only 30 min on, not steady
    result = tool.within_hour_cycling(pd.DataFrame({'u': power}, index=index), ['u'])
    assert result['unit_hours'] == 1 and result['transitions_per_hour'] == 1.0
