"""CityLearn adapters of the frozen evaluation, wired by composition roots.

uc3m.application.evaluation.frozen_evaluation.evaluate_frozen receives this bundle so
that the application layer never imports CityLearn or the adapters itself.
"""
from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

BILL_TARIFFS = Path(__file__).resolve().parents[3]/'data/tariffs/osinergmin/bill_tariffs.csv'


def _price_signal_deviation(trace):
    """CityLearn v3 price_signal_deviation of a physical trace (district net power vs price).

    Unavailable with several tariffs: a district formula over one building's price would
    be wrong, and how to weigh several prices is an open methodological decision (D02).
    """
    from citylearn.v3.objectives import price_signal_deviation
    if 'price' not in trace.district_series:
        return None
    steps = len(trace.timestamps)
    district = [sum(trace.series_by_building[b]['net_power'][t] for b in trace.building_ids) for t in range(steps)]
    value = price_signal_deviation(district, list(trace.district_series['price'])[:steps])
    return None if value is None else float(value)


def citylearn_frozen_adapters() -> SimpleNamespace:
    from uc3m.adapters.citylearn.policy_inference import RbcPolicy, load_native_policy, run_frozen_episode
    from uc3m.application.dataset.provenance import sha256_file
    from uc3m.application.evaluation.bill_cost import bill_measures, load_bill_tariffs
    return SimpleNamespace(load_native_policy=load_native_policy, run_frozen_episode=run_frozen_episode,
                           rbc_policy=RbcPolicy, bill_tariffs_sha256=sha256_file(BILL_TARIFFS),
                           extra_measures={'price_signal_deviation': _price_signal_deviation,
                                           **bill_measures(load_bill_tariffs(BILL_TARIFFS))})
