"""SPEC-016 3b.4: the builder gains a v6 mode that wires the v6 pieces and leaves the v5 path untouched."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

import build_fresh_campaign_dataset as bf  # noqa: E402

SOURCE = (REPO/'tools/dataset/build_fresh_campaign_dataset.py').read_text(encoding='utf-8')


def test_the_builder_accepts_a_v6_mode_and_keeps_v5_by_default():
    assert "'--dataset-version'" in SOURCE and "choices=('v5', 'v6')" in SOURCE and "default='v5'" in SOURCE


def test_the_v6_mode_wires_every_v6_piece():
    for call in ('remove_washing_machines(', 'distill_v6(', 'capped_block_flags(', 'write_ev_fleet(',
                 'write_synthetic_bill(', 'synthetic_months(', 'write_bill_tariff_files(', 'peak_contrast(',
                 'size_v6_bess(', 'bess_attributes(', "design['ev_planned_kwh_h']"):
        assert call in SOURCE, call


def test_billed_load_of_a_building_without_washing_machines(tmp_path):
    hours = 48
    pd.DataFrame({'non_shiftable_load': np.ones(hours), 'cooling_demand': np.zeros(hours),
                  'dhw_demand': np.zeros(hours)}).to_csv(tmp_path/'Building_1.csv', index=False)
    schema = {'buildings': {'Building_1': {'cooling_device': {'attributes': {'efficiency': 0.3,
                                                                            'target_cooling_temperature': 8.5}}}}}
    parts = bf.as_billed_load(tmp_path, 1, schema, np.full(hours, 28.0))
    assert np.allclose(parts['machines'], 0.0) and np.allclose(parts['total'], 1.0)
