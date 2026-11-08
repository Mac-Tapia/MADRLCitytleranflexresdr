"""SPEC-016 3b.4: the builder gains a v6 mode that wires the v6 pieces and leaves the v5 path untouched."""
import sys
from pathlib import Path

import numpy as np
import pytest
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

import build_fresh_campaign_dataset as bf  # noqa: E402

SOURCE = (REPO/'tools/dataset/build_fresh_campaign_dataset.py').read_text(encoding='utf-8')


def test_the_builder_accepts_a_v6_mode_and_keeps_v5_by_default():
    assert "'--dataset-version'" in SOURCE and "choices=('v5', 'v6')" in SOURCE and "default='v5'" in SOURCE


def test_a_v6_build_always_sizes_by_the_rule_and_gates_its_peak_shaving():
    """A v6 build without --bess-design-rule sized the BESS by the rule but dropped bess_rule_shaves_peak."""
    from argparse import Namespace
    assert bf.bess_rule_applies(Namespace(bess_design_rule=False, dataset_version='v6'))
    assert bf.bess_rule_applies(Namespace(bess_design_rule=True, dataset_version='v5'))
    assert not bf.bess_rule_applies(Namespace(bess_design_rule=False, dataset_version='v5'))
    assert SOURCE.count('if bess_rule_applies(args):') == 2        # sizing and the gate


def test_the_v6_mode_wires_every_v6_piece():
    for call in ('remove_washing_machines(', 'distill_v6(', 'capped_block_flags(', 'write_ev_fleet(',
                 'write_synthetic_bill(', 'synthetic_months(', 'write_bill_tariff_files(', 'peak_contrast(',
                 'size_v6_bess(', 'bess_attributes(', "design['ev_planned_kwh_h']", 'redistill_peaks(',
                 "gates['peak_contrast']", 'DATASET_GATES_PATH'):
        assert call in SOURCE, call


def test_billed_load_of_a_building_without_washing_machines(tmp_path):
    hours = 48
    pd.DataFrame({'non_shiftable_load': np.ones(hours), 'cooling_demand': np.zeros(hours),
                  'dhw_demand': np.zeros(hours)}).to_csv(tmp_path/'Building_1.csv', index=False)
    schema = {'buildings': {'Building_1': {'cooling_device': {'attributes': {'efficiency': 0.3,
                                                                            'target_cooling_temperature': 8.5}}}}}
    parts = bf.as_billed_load(tmp_path, 1, schema, np.full(hours, 28.0))
    assert np.allclose(parts['machines'], 0.0) and np.allclose(parts['total'], 1.0)


def test_the_v6_shaving_check_uses_the_catalog_power_in_the_schema():
    # iquitos_v6_trial3: with bess_kw = capacity / max discharge time (v5) the check normalized its actions by a
    # power 2.4 times smaller than the schema's and B04/B05 delivered 78 % and 49 % of the shave; with the
    # catalog power all 17 delivered 100 % (rerun of citylearn_peak_shaving on trial3).
    assert "round(v6_size.nominal_power_kw, 3) if v6_size is not None" in SOURCE


def test_the_shaving_fraction_is_measured_against_what_each_month_can_shave():
    """A month whose whole peak-block import is below the rule's shave and goes to 0 delivers all it can."""
    shaved = 6.84
    no_control = {'3': 9.15, '4': 6.01}
    assert bf.delivered_fraction_worst_month(no_control, {'3': 2.31, '4': 0.0}, shaved) == pytest.approx(1.0, abs=1e-3)
    assert bf.delivered_fraction_worst_month(no_control, {'3': 5.0, '4': 0.0}, shaved) == pytest.approx(4.15/6.84)
    assert bf.delivered_fraction_worst_month({'1': 9.0}, {'1': 9.0}, shaved) == 0.0
