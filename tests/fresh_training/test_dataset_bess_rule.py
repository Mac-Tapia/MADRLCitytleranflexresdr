"""Declared BESS design rule of campaign iquitos_v4 (owner decision 2026-11-02, scenario A).

With net billing at the purchase price the MicroGrids LP has no reason to install a
battery, so v3 ended with 44.3 kWh in one building. The rule keeps net billing and the
LP's PV, and sizes each battery to shave a declared fraction of the building's own
peak-block import. Unit tests use synthetic inputs; integration tests read
data/campaigns/iquitos_v4 and fail (never skip) when it is absent.
"""
import json
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))
CAMPAIGN = REPO/'data/campaigns/iquitos_v4'
RULE_PATH = REPO/'configs/dataset/bess_design_rule.yaml'


def _json(path):
    assert path.is_file(), f'{path.relative_to(REPO)} missing: build iquitos_v4 first'
    return json.loads(path.read_text(encoding='utf-8'))


def _rule():
    return yaml.safe_load(RULE_PATH.read_text(encoding='utf-8'))


# ── unit ─────────────────────────────────────────────────────────────────────

def test_rule_is_declared_and_not_attributed_to_literature():
    rule = _rule()
    assert rule['origin'] == 'user_decision' and rule['status'] == 'design_rule'
    fraction = rule['shave_fraction_of_peak_block']
    assert fraction['status'] == 'assumption_pending_user_verification'
    assert fraction['value'] == 0.20 and fraction['source'] and fraction['reason']


def test_rule_sizes_power_and_energy_from_the_peak_block():
    import size_der_microgrids as sd
    sized = sd.bess_design_rule(100.0, 5, sd.load_economics(), _rule())
    assert sized['shaved_kw'] == pytest.approx(20.0)
    # 20 kW sustained for 5 h, through discharge efficiency 0.95 and the 0.20-0.88 usable window.
    assert sized['capacity_kwh'] == pytest.approx(round(20.0*5/(0.95*0.68), 1))
    assert sized['nominal_power_kw'] == pytest.approx(round(sized['capacity_kwh']/5, 3))


def test_soc_ceiling_is_where_the_curve_still_allows_the_sustained_power():
    import numpy as np
    import size_der_microgrids as sd
    rule = _rule()
    sized = sd.bess_design_rule(100.0, 5, sd.load_economics(), rule)
    x, y = zip(*rule['capacity_power_curve']['value'])
    ceiling = rule['soc_ceiling']['value']
    assert np.interp(ceiling, x, y)*sized['nominal_power_kw'] >= sized['shaved_kw']
    assert np.interp(ceiling + 0.02, x, y)*sized['nominal_power_kw'] < sized['shaved_kw']


def test_rule_declares_every_curve_so_nothing_is_drawn_from_the_seed():
    import size_der_microgrids as sd
    curves = sd.bess_rule_curves(0.9025, _rule())
    assert curves['capacity_power_curve'][-1] == [1.0, 0.25]
    assert curves['power_efficiency_curve'][3] == [0.8, pytest.approx(0.9025)]


def test_rule_gives_no_battery_without_a_peak_block_import():
    import size_der_microgrids as sd
    sized = sd.bess_design_rule(0.0, 5, sd.load_economics(), _rule())
    assert sized == {'shaved_kw': 0.0, 'capacity_kwh': 0.0, 'nominal_power_kw': 0.0}


# ── built dataset (integration) ──────────────────────────────────────────────

def test_every_building_with_peak_import_has_its_rule_battery():
    sizing = _json(CAMPAIGN/'audit/der_sizing_microgrids.json')
    schema = _json(CAMPAIGN/'dataset/schema.json')
    assert sizing['bess_sizing'] == 'peak_block_shaving'
    for b in range(1, 18):
        row = sizing['buildings'][str(b)]
        block = max(row['no_bess_monthly_peak_block_max_kw'].values())
        assert row['bess_rule']['shaved_kw'] == pytest.approx(0.20*block, rel=1e-9)
        battery = schema['buildings'][f'Building_{b}']['electrical_storage']['attributes']
        assert battery['capacity'] == pytest.approx(row['bess_kwh'])
        assert battery['nominal_power'] == pytest.approx(row['bess_kw'])
        assert 'bess_kwh_lp' in row  # the LP optimum stays visible next to the rule


def test_rule_battery_lowers_the_peak_block_in_citylearn():
    shaving = _json(CAMPAIGN/'audit/bess_peak_shaving_check.json')
    assert shaving['status'] == 'checked' and len(shaving['buildings']) == 17
    for b, row in shaving['buildings'].items():
        assert min(row['reduction_kw'].values()) >= 0.9*row['shaved_kw'], b  # every month, as sized
    acceptance = _json(CAMPAIGN/'dataset_acceptance.json')
    assert acceptance['gates']['bess_rule_shaves_peak'] is True and acceptance['dataset_verified'] is True


def test_battery_physics_does_not_depend_on_the_training_seed():
    from citylearn.citylearn import CityLearnEnv
    schema = CAMPAIGN/'splits/train_2023/schema.json'
    assert schema.is_file(), 'iquitos_v4 splits not materialized yet'
    draws = []
    for seed in (901, 1001):
        env = CityLearnEnv(str(schema), random_seed=seed)
        env.reset()
        draws.append([(b.electrical_storage.capacity_power_curve.tolist(),
                       b.electrical_storage.power_efficiency_curve.tolist(),
                       b.electrical_storage.nominal_power, b.electrical_storage.capacity_loss_coefficient)
                      for b in env.buildings])
    assert draws[0] == draws[1]


def test_rule_is_recorded_as_design_rule_in_provenance():
    provenance = _json(CAMPAIGN/'provenance.json')
    quantities = provenance['quantities']
    rules = [q for q in quantities if q['name'] == 'bess_shave_fraction_of_peak_block']
    assert rules and rules[0]['assumption'] is True
    assert all(q['origin'] == 'design_rule' for q in quantities if q['name'] == 'bess_kwh')
    assert any('bess_design_rule.yaml' in p for p in provenance['design_inputs'])
