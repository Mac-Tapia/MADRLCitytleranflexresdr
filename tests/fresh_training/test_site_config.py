"""SPEC-017 FR-017.1 and FR-017.5: site values live in a site configuration, never in the code.

Iquitos is the first site. The tariff block, time zone, elevation and the files of norms, fleet and
building types come from configs/sites/<site>.yaml, each value with its origin. No dataset module keeps
a site constant, so another site only needs another configuration.
"""
import re
from pathlib import Path

import pytest
import yaml

from uc3m.application.dataset import site as st

REPO = Path(__file__).resolve().parents[2]
IQUITOS = REPO/'configs/sites/iquitos.yaml'
ORIGINS = {'measured', 'cited', 'design_rule', 'assumption', 'assumption_pending_user_verification',
           'implementation_rule'}
SCANNED = sorted((REPO/'uc3m/application/dataset').glob('*.py')) + [
    REPO/'uc3m/application/evaluation/bill_cost.py',
    *[REPO/'tools/dataset'/name for name in ('distill_building_loads.py', 'evaluate_dataset.py',
                                             'generate_b01_billing.py', 'buildingcsv_inputs.py',
                                             'build_fresh_campaign_dataset.py')]]
HARD_CODED_BLOCK = re.compile(r'[({\[]\s*18\s*,\s*19\s*,\s*20\s*,\s*21\s*,\s*22\s*[)}\]]')


def test_iquitos_site_declares_its_values_with_origin():
    site = st.load_site(IQUITOS)
    assert site.name == 'iquitos' and site.peak_block_hours == frozenset({18, 19, 20, 21, 22})
    assert site.utc_offset_hours == -5 and site.elevation_m == pytest.approx(115.02)
    raw = yaml.safe_load(IQUITOS.read_text(encoding='utf-8'))
    for key in ('peak_block', 'time_zone', 'elevation_m'):
        assert raw[key]['origin'] in ORIGINS, key
        assert raw[key].get('source') or raw[key].get('note'), key
    for path in site.files.values():
        assert (REPO/path).is_file(), path


def test_the_default_site_is_selected_by_the_environment(monkeypatch, tmp_path):
    other = tmp_path/'other.yaml'
    raw = yaml.safe_load(IQUITOS.read_text(encoding='utf-8'))
    raw['name'] = 'other'
    raw['peak_block']['hours'] = [17, 18, 19]
    other.write_text(yaml.safe_dump(raw), encoding='utf-8')
    monkeypatch.setenv('UC3M_SITE_CONFIG', str(other))
    assert st.load_default_site().peak_block_hours == frozenset({17, 18, 19})
    monkeypatch.delenv('UC3M_SITE_CONFIG')
    assert st.load_default_site().name == 'iquitos'


def test_a_value_without_origin_is_rejected(tmp_path):
    raw = yaml.safe_load(IQUITOS.read_text(encoding='utf-8'))
    del raw['peak_block']['origin']
    bad = tmp_path/'bad.yaml'
    bad.write_text(yaml.safe_dump(raw), encoding='utf-8')
    with pytest.raises(ValueError, match='origin'):
        st.load_site(bad)


@pytest.mark.parametrize('path', SCANNED, ids=lambda p: p.name)
def test_no_dataset_module_hard_codes_the_tariff_block(path):
    assert not HARD_CODED_BLOCK.search(path.read_text(encoding='utf-8')), path


def test_vehicle_type_map_lives_in_the_fleet_configuration():
    source = (REPO/'uc3m/application/dataset/ev_sizing.py').read_text(encoding='utf-8')
    assert "'Motokars'" not in source and 'TOKEN_CLASS = {' not in source
    rules = yaml.safe_load((REPO/'configs/dataset/ev_v6.yaml').read_text(encoding='utf-8'))
    assert rules['vehicle_type_tokens']['Motokars'] == 'mototaxi'
    assert rules['vehicle_type_tokens_origin'] in ORIGINS
