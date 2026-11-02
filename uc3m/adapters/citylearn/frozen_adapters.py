"""CityLearn adapters of the frozen evaluation, wired by composition roots.

uc3m.application.evaluation.frozen_evaluation.evaluate_frozen receives this bundle so
that the application layer never imports CityLearn or the adapters itself.
"""
from __future__ import annotations

from types import SimpleNamespace


def _price_signal_deviation(trace):
    """CityLearn v3 price_signal_deviation of a physical trace (district net power vs price)."""
    from citylearn.v3.objectives import price_signal_deviation
    steps = len(trace.timestamps)
    district = [sum(trace.series_by_building[b]['net_power'][t] for b in trace.building_ids) for t in range(steps)]
    value = price_signal_deviation(district, list(trace.district_series['price'])[:steps])
    return None if value is None else float(value)


def citylearn_frozen_adapters() -> SimpleNamespace:
    from uc3m.adapters.citylearn.policy_inference import RbcPolicy, load_native_policy, run_frozen_episode
    return SimpleNamespace(load_native_policy=load_native_policy, run_frozen_episode=run_frozen_episode,
                           rbc_policy=RbcPolicy,
                           extra_measures={'price_signal_deviation': _price_signal_deviation})
