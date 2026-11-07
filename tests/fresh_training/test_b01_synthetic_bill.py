"""SPEC-016 D-V6-36: synthetic bill of B01 (Electro Oriente), which has no bill.

Energy: the measured EA of resultados_preliminares.xlsx (sheet 8.ELOR) and the months v5 already declares
(2023 backcast x 0.98, 2025-11/12 scaled), with the peak split of v5. Load factor: median of the measured
bills of the same month of the 24 h peers B09, B11, B12 and B17. Max demand = E / (hours x LF). Reactive:
peers' median reactive/active ratio (P-V6-18). Amount: the official Osinergmin sheet, tariff MT3 (P-V6-19).
"""
import statistics
import sys
from datetime import date
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

import write_b01_synthetic_bill as wb  # noqa: E402
from uc3m.application.dataset import b01_synthetic as bs  # noqa: E402
from uc3m.application.dataset import construction as cn  # noqa: E402

RAW = REPO/'data/campaigns/iquitos_v5/raw'
RULES = yaml.safe_load((REPO/'configs/dataset/b01_synthetic_bill.yaml').read_text(encoding='utf-8'))
PEERS = tuple(RULES['peers']['value'])


@pytest.fixture(scope='module')
def peers_measured():
    records = []
    for b in PEERS:
        records += cn.parse_billing_csv(RAW/'buildingcsv'/f'B_{b:02d}.csv', b, scale_tou_to_printed_total=True)
    return records


def test_the_rule_names_the_24h_peers_chosen_by_the_owner():
    assert PEERS == (9, 11, 12, 17) and RULES['peers']['origin'] == 'design_rule'
    assert 'D-V6-36' in RULES['peers']['source']


def test_load_factor_is_the_median_of_the_same_month_peers(peers_measured):
    value, used = bs.peer_load_factor(2024, 3, peers_measured, peers=PEERS)
    expected = statistics.median(r.load_factor for r in peers_measured
                                 if (r.year, r.month) == (2024, 3) and r.load_factor and 0 < r.load_factor <= 1)
    assert value == pytest.approx(expected) and 0 < value <= 1 and set(used) <= set(PEERS)


def test_an_implausible_peer_load_factor_is_left_out():
    bad = [cn.MonthlyRecord(9, 2024, 1, 100.0, 20.0, 80.0, 'measured', 'billing', 'measured', ('x',), (), 1280.3, 1.0),
           cn.MonthlyRecord(11, 2024, 1, 100.0, 20.0, 80.0, 'measured', 'billing', 'measured', ('x',), (), 0.7, 1.0)]
    value, used = bs.peer_load_factor(2024, 1, bad, peers=PEERS)
    assert value == pytest.approx(0.7) and used == [11]
    with pytest.raises(ValueError, match='no measured peer'):
        bs.peer_load_factor(2024, 2, bad, peers=PEERS)


def test_max_demand_closes_with_energy_hours_and_load_factor(peers_measured):
    target = cn.MonthlyRecord(1, 2024, 2, 463037.0, 46562.4, 416474.6, 'measured', 'energy_only_report', 'measured',
                              ('r',), ('tou_split_modeled',))
    month = bs.synthetic_months([target], peers_measured, peers=PEERS, reactive={})[0]
    assert month.max_demand_kw == pytest.approx(463037.0/(29*24*month.load_factor))
    assert month.energy_provenance == 'measured' and month.reactive_kvarh == 0.0


def test_the_synthetic_bill_is_priced_with_the_official_sheet(tmp_path, peers_measured):
    import osinergmin_pliegos as op
    sheets = {date.fromisoformat(p.stem.split('_')[-1]): op.parse_sheet(p.read_bytes())
              for p in sorted((RAW/'osinergmin').glob('pliego_iquitos_*.html'))}
    targets = [cn.MonthlyRecord(1, 2024, m, 460000.0, 50000.0, 410000.0, 'measured', 'energy_only_report', 'measured',
                                ('r',), ()) for m in (1, 2)]
    months = bs.synthetic_months(targets, peers_measured, peers=PEERS, reactive={})
    path, audit = wb.write_synthetic_bill(tmp_path/'B_01.csv', months, sheets=sheets, tariff=RULES['tariff']['value'])
    records = cn.parse_billing_csv(path, 1)
    assert [(r.year, r.month) for r in records] == [(2024, 1), (2024, 2)]
    for record, month, row in zip(records, months, audit['months']):
        bill = op.reconstruct_bill(tariff='MT3', year=month.year, month=month.month, peak_kwh=month.peak_kwh,
                                   offpeak_kwh=month.offpeak_kwh, reactive_kvarh=month.reactive_kvarh,
                                   load_factor=month.load_factor, sheets=sheets)
        assert record.billed_amount == pytest.approx(bill['total_with_igv_pen'], abs=0.01)
        assert record.load_factor == pytest.approx(month.load_factor, abs=1e-6)
        assert row['provenance'] == 'synthetic' and row['decision'] == 'D-V6-36'
