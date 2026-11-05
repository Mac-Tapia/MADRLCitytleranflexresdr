"""Module 1 (SPEC-013): official Osinergmin busbar tariff PDFs and their cross-check.

Unit tests use text copied from the 04/07/2025 PDF and fake sessions, without network.
The artifact tests read the versioned data/tariffs/osinergmin files and fail (never
skip) when they are absent.
"""
import csv
import hashlib
import json
import sys
from datetime import date
from pathlib import Path

import pytest
import requests

from uc3m.adapters.osinergmin import pba_pdf
from uc3m.adapters.osinergmin.pba_pdf import (PbaFormatError, SourceChangedError, candidate_dates, candidate_names,
                                              fetch_pba, parse_pba_text)
from uc3m.application.dataset.tariff_crosscheck import (crosscheck, sheets_from_csv, tariff_crosscheck_audit,
                                                        tariff_crosscheck_gate)
from uc3m.domain.tariffs import BusbarPrice, BusbarSheet

REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(REPO/'tools/dataset'))

ROW_B = 'Electro Oriente MT 32,12 78,58 78,58 Electro Oriente MT 32,12 78,58 78,58 32,12 78,58 78,58 8,11 78,58 86,69'
ROW_E = 'Electro Oriente MT 32,12 34,71 34,71 Electro Oriente MT 32,12 34,71 34,71 32,12 34,71 34,71 8,11 34,71 42,82'
HEAD = 'TARIFAS EN BARRA (Res. N° 048-2025-OS/CD y N° 109-2025-OS/CD)\nACTUALIZADO AL 04/Julio/2025 CON REDONDEO\n'
D, E = date(2025, 7, 4), date(2025, 8, 4)
TARIFFS_ROOT = REPO/'data/tariffs/osinergmin'
SHEET_ONLY = ['2023-05-01', '2023-05-26', '2023-11-01', '2024-05-01', '2024-11-01', '2025-01-01', '2025-05-01',
              '2025-11-01']


def sheet(effective, valid_from=D):
    return BusbarSheet(valid_from, 'Electro Oriente', ('048-2025',), BusbarPrice(32.12, 78.58, 78.58),
                       BusbarPrice(32.12, effective, effective))


def charges(peak, offpeak=None):
    return {'MT3': {'energy_peak_ctm_kwh': peak, 'energy_offpeak_ctm_kwh': peak if offpeak is None else offpeak}}


# ── extraction ───────────────────────────────────────────────────────────────

def test_parse_real_rows():
    parsed = parse_pba_text(HEAD + ROW_B + '\n' + ROW_E)
    assert parsed.valid_from == date(2025, 7, 4)
    assert parsed.resolutions == ('048-2025', '109-2025')
    assert parsed.barra == BusbarPrice(32.12, 78.58, 78.58)
    assert parsed.efectivo == BusbarPrice(32.12, 34.71, 34.71)
    assert parsed.barra.is_flat


def test_updated_column_wins_over_base():
    row = 'Electro Oriente MT 32,12 25,18 25,18 Electro Oriente MT 32,13 25,19 25,19'
    assert parse_pba_text(HEAD + ROW_B + '\n' + row).efectivo == BusbarPrice(32.13, 25.19, 25.19)


@pytest.mark.parametrize('body', ['', ROW_B, ROW_B + '\n' + ROW_E + '\n' + ROW_E, 'Electro Oriente MT\n' + ROW_E,
                                  ROW_B + '\nElectro Oriente MT Electro Oriente MT'])
def test_wrong_row_count_or_empty_row_is_rejected(body):
    with pytest.raises(PbaFormatError):
        parse_pba_text(HEAD + body)


def test_missing_date_is_rejected():
    with pytest.raises(PbaFormatError):
        parse_pba_text(ROW_B + '\n' + ROW_E)


def test_other_system_is_selected_by_name():
    row = 'Seal MT 32,12 104,01 104,01 Seal MT 32,72 105,94 105,94 32,72 105,94 105,94 8,26 105,94 114,20'
    text = HEAD + ROW_B + '\n' + row + '\n' + ROW_E + '\n' + row
    assert parse_pba_text(text, system='Seal').barra == BusbarPrice(32.72, 105.94, 105.94)


@pytest.mark.parametrize('values', [(0.0, 1.0, 1.0), (1.0, -1.0, 1.0), (1.0, 1.0, float('nan')),
                                    (1.0, float('inf'), 1.0)])
def test_invalid_price_is_rejected(values):
    with pytest.raises(ValueError):
        BusbarPrice(*values)


def test_time_of_use_price_is_not_flat():
    assert not BusbarPrice(1.0, 2.0, 1.5).is_flat


# ── download ─────────────────────────────────────────────────────────────────

class FakeResponse:
    def __init__(self, status, content=b''):
        self.status_code, self.content = status, content

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(str(self.status_code))


class FakeSession:
    def __init__(self, default, by_suffix=None):
        self.default, self.by_suffix, self.urls = default, by_suffix or {}, []

    def get(self, url, **_):
        self.urls.append(url)
        for suffix, response in self.by_suffix.items():
            if url.endswith(suffix):
                return response
        return self.default


PDF = b'%PDF-1.7 fake'


@pytest.fixture
def parsed_as(monkeypatch):
    def install(valid_from):
        monkeypatch.setattr(pba_pdf, 'parse_pba', lambda payload, system='Electro Oriente': sheet(34.71, valid_from))
    return install


def test_candidate_names_in_order():
    assert candidate_names(date(2022, 12, 4)) == ('1 PBA04122022.pdf', 'PBA04122022.pdf')


def test_first_variant_404_second_200(tmp_path, parsed_as):
    day = date(2022, 12, 4)
    parsed_as(day)
    session = FakeSession(FakeResponse(404), {'/PBA04122022.pdf': FakeResponse(200, PDF)})
    entry = fetch_pba(day, tmp_path, session=session, pause_s=0)
    assert entry['source_uri'].endswith('/PBA04122022.pdf') and '1%20PBA04122022.pdf' in session.urls[0]
    assert Path(entry['path']).read_bytes() == PDF
    assert entry['sha256'] == hashlib.sha256(PDF).hexdigest() and entry['valid_from'] == '2022-12-04'


def test_all_404_is_missing(tmp_path):
    assert fetch_pba(D, tmp_path, session=FakeSession(FakeResponse(404)), pause_s=0) is None
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize('status', [403, 500])
def test_other_http_error_stops(status, tmp_path):
    with pytest.raises(requests.HTTPError):
        fetch_pba(D, tmp_path, session=FakeSession(FakeResponse(status)), pause_s=0)
    assert list(tmp_path.iterdir()) == []


def test_html_with_200_is_rejected(tmp_path):
    with pytest.raises(PbaFormatError):
        fetch_pba(D, tmp_path, session=FakeSession(FakeResponse(200, b'<html>login</html>')), pause_s=0)
    assert list(tmp_path.iterdir()) == []


def test_pdf_of_other_date_is_rejected(tmp_path, parsed_as):
    parsed_as(E)
    with pytest.raises(PbaFormatError):
        fetch_pba(D, tmp_path, session=FakeSession(FakeResponse(200, PDF)), pause_s=0)
    assert list(tmp_path.iterdir()) == []


def test_changed_source_keeps_original(tmp_path, parsed_as):
    parsed_as(D)
    entry = fetch_pba(D, tmp_path, session=FakeSession(FakeResponse(200, PDF)), pause_s=0)
    with pytest.raises(SourceChangedError):
        fetch_pba(D, tmp_path, session=FakeSession(FakeResponse(200, PDF + b'x')), pause_s=0)
    with pytest.raises(SourceChangedError):
        fetch_pba(D, tmp_path, session=FakeSession(FakeResponse(200, PDF)), known_sha256='0'*64, pause_s=0)
    assert Path(entry['path']).read_bytes() == PDF


def test_candidate_dates_union():
    assert candidate_dates(date(2024, 3, 1), date(2024, 3, 31), [date(2024, 3, 15), date(2024, 4, 4)]) == \
        [date(2024, 3, 4), date(2024, 3, 15)]


# ── cross-check ──────────────────────────────────────────────────────────────

def test_common_date_in_band_has_no_failure():
    out = crosscheck({D: sheet(34.71)}, {D: charges(35.10)})
    assert out['failures'] == [] and out['rows'][0]['ratio'] == pytest.approx(35.10/34.71)


def test_out_of_band_and_non_flat_are_reported():
    high = crosscheck({D: sheet(34.71)}, {D: charges(40.0)})
    assert high['failures'] == [{'valid_from': D.isoformat(), 'reason': 'ratio_out_of_band'}]
    tou = crosscheck({D: sheet(34.71)}, {D: charges(35.1, 30.0)})
    assert {'valid_from': D.isoformat(), 'reason': 'non_flat_sheet'} in tou['failures']


def test_non_flat_busbar_is_reported():
    parsed = BusbarSheet(D, 'Electro Oriente', (), BusbarPrice(32.12, 78.58, 70.0), BusbarPrice(32.12, 34.71, 34.71))
    assert {'valid_from': D.isoformat(), 'reason': 'non_flat_busbar'} in crosscheck({D: parsed}, {D: charges(35.1)})['failures']


def test_missing_energy_charge_is_reported():
    out = crosscheck({D: sheet(34.71)}, {D: {'MT2': {}}})
    assert out['failures'] == [{'valid_from': D.isoformat(), 'reason': 'missing_energy_charge'}]


def test_coverage_is_declared_and_never_filled():
    out = crosscheck({D: sheet(34.71)}, {E: charges(35.1)})
    assert out['pdf_only'] == [D.isoformat()] and out['sheet_only'] == [E.isoformat()] and out['rows'] == []


def test_mt4_energy_key_is_accepted():
    out = crosscheck({D: sheet(34.71)}, {D: {'MT4': {'energy_ctm_kwh': 35.10}}}, tariff='MT4')
    assert out['failures'] == [] and len(out['rows']) == 1


# ── tool ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def tool(monkeypatch):
    import ingest_osinergmin_pba as module
    monkeypatch.setattr(pba_pdf, 'parse_pba', lambda payload, system='Electro Oriente': sheet(34.71))
    monkeypatch.setattr(module, 'parse_pba', lambda payload, system='Electro Oriente': sheet(34.71))
    monkeypatch.setattr(module.op, 'parse_sheet', lambda payload: charges(35.10))
    return module


def _offline_tree(tmp_path, ratio_html=b'x'):
    root, sheets_dir = tmp_path/'root', tmp_path/'sheets'
    (root/'raw').mkdir(parents=True)
    sheets_dir.mkdir()
    (root/'raw/pba_2025-07-04.pdf').write_bytes(PDF)
    (sheets_dir/'pliego_iquitos_2025-07-04.html').write_bytes(ratio_html)
    (root/'pba_manifest.json').write_text(json.dumps({'files': {'2025-07-04': {
        'path': 'raw/pba_2025-07-04.pdf', 'source_uri': 'u', 'sha256': hashlib.sha256(PDF).hexdigest(),
        'obtained_at': 't', 'source_type': 'official_tariff_sheet'}}, 'missing': []}), encoding='utf-8')
    return root, sheets_dir


def test_offline_rebuild_writes_artifacts(tmp_path, tool):
    root, sheets_dir = _offline_tree(tmp_path)
    assert tool.main(['--offline', '--root', str(root), '--sheets-dir', str(sheets_dir)]) == 0
    manifest = json.loads((root/'pba_manifest.json').read_text(encoding='utf-8'))
    assert manifest['system'] == 'Electro Oriente' and manifest['crosscheck']['failures'] == []
    assert manifest['files']['2025-07-04']['obtained_at'] == 't'
    with open(root/'busbar_electro_oriente.csv', newline='', encoding='utf-8') as handle:
        rows = list(csv.DictReader(handle))
    assert rows[0]['valid_from'] == '2025-07-04' and float(rows[0]['efectivo_peak']) == 34.71


def test_offline_rebuild_rejects_changed_pdf(tmp_path, tool):
    root, sheets_dir = _offline_tree(tmp_path)
    (root/'raw/pba_2025-07-04.pdf').write_bytes(PDF + b'x')
    assert tool.main(['--offline', '--root', str(root), '--sheets-dir', str(sheets_dir)]) == 2


def test_offline_without_manifest_is_rejected(tmp_path, tool):
    assert tool.main(['--offline', '--root', str(tmp_path/'none'), '--sheets-dir', str(tmp_path)]) == 2


def test_crosscheck_failure_exits_3(tmp_path, tool, monkeypatch):
    root, sheets_dir = _offline_tree(tmp_path)
    monkeypatch.setattr(tool.op, 'parse_sheet', lambda payload: charges(40.0))
    assert tool.main(['--offline', '--root', str(root), '--sheets-dir', str(sheets_dir)]) == 3


# ── real artifacts ───────────────────────────────────────────────────────────

def test_versioned_csv_matches_published_row():
    sheets = sheets_from_csv(TARIFFS_ROOT/'busbar_electro_oriente.csv')
    assert sheets[D].barra == BusbarPrice(32.12, 78.58, 78.58)
    assert sheets[D].efectivo == BusbarPrice(32.12, 34.71, 34.71)
    assert all(s.barra.is_flat and s.efectivo.is_flat for s in sheets.values())


def test_versioned_manifest_declares_coverage_and_no_failures():
    manifest = json.loads((TARIFFS_ROOT/'pba_manifest.json').read_text(encoding='utf-8'))
    report = manifest['crosscheck']
    assert report['failures'] == []
    assert report['pdf_only'] == ['2023-05-04', '2024-03-04', '2025-01-04']
    assert report['sheet_only'] == SHEET_ONLY
    assert len(manifest['files']) == 37 and len(report['rows']) == 34
    assert {entry['source_type'] for entry in manifest['files'].values()} == {'official_tariff_sheet'}
    assert any('criterio del proyecto' in text for text in manifest['limitations'])


# ── connection with the dataset builder ──────────────────────────────────────

def test_energy_rate_refuses_time_of_use_sheet():
    import build_fresh_campaign_dataset as builder
    with pytest.raises(ValueError):
        builder.energy_rate_ctm({'energy_peak_ctm_kwh': 35.1, 'energy_offpeak_ctm_kwh': 30.0})


@pytest.mark.parametrize('charge, expected', [({'energy_peak_ctm_kwh': 35.1, 'energy_offpeak_ctm_kwh': 35.1}, 35.1),
                                              ({'energy_ctm_kwh': 35.1}, 35.1)])
def test_energy_rate_keeps_flat_sheets(charge, expected):
    import build_fresh_campaign_dataset as builder
    assert builder.energy_rate_ctm(charge) == expected


def test_gate_requires_rows_and_no_failures():
    assert tariff_crosscheck_gate({'failures': [], 'rows': [{}]}) is True
    assert tariff_crosscheck_gate({'failures': [{'valid_from': '2025-07-04', 'reason': 'ratio_out_of_band'}],
                                   'rows': [{}]}) is False
    assert tariff_crosscheck_gate({'failures': [], 'rows': []}) is False


def test_audit_without_csv_fails_closed(tmp_path):
    report = tariff_crosscheck_audit(tmp_path/'absent.csv', {D: charges(35.1)})
    assert report['failures'] == [{'valid_from': None, 'reason': 'busbar_csv_missing'}]
    assert tariff_crosscheck_gate(report) is False


def test_audit_records_csv_hash(tmp_path):
    path = tmp_path/'busbar.csv'
    path.write_text('valid_from,resolutions,barra_power,barra_peak,barra_offpeak,efectivo_power,efectivo_peak,'
                    'efectivo_offpeak,sheet_mt3_energy,ratio_mt3_efectivo\n'
                    '2025-07-04,048-2025,32.12,78.58,78.58,32.12,34.71,34.71,35.1,1.0112\n', encoding='utf-8')
    report = tariff_crosscheck_audit(path, {D: charges(35.1)})
    assert report['failures'] == [] and report['busbar_csv_sha256'] == hashlib.sha256(path.read_bytes()).hexdigest()


def test_audit_passes_on_the_sheets_a_build_would_use():
    import osinergmin_pliegos as op
    sheets = {date.fromisoformat(path.stem.rsplit('_', 1)[1]): op.parse_sheet(path.read_bytes())
              for path in (REPO/'data/campaigns/iquitos_v4/raw/osinergmin').glob('*.html')}
    report = tariff_crosscheck_audit(TARIFFS_ROOT/'busbar_electro_oriente.csv', sheets)
    assert tariff_crosscheck_gate(report) and len(report['rows']) == 34


@pytest.mark.parametrize('tariff', ['MT2', 'MT3', 'MT4', 'BT2', 'BT3'])
def test_every_tariff_used_by_the_dataset_is_flat_in_every_sheet(tariff):
    import build_fresh_campaign_dataset as builder
    import osinergmin_pliegos as op
    paths = sorted((REPO/'data/campaigns/iquitos_v4/raw/osinergmin').glob('*.html'))
    assert len(paths) == 42
    for path in paths:
        assert builder.energy_rate_ctm(op.parse_sheet(path.read_bytes())[tariff]) > 0, path.name
