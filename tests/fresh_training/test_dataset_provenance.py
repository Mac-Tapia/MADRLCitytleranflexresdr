"""T2: provenance of raw sources and leakage-free monthly targets.

All inputs are tiny synthetic billing files written under tmp_path; nothing
is read from the prior hourly dataset or from earlier outputs.
"""
import json
from pathlib import Path

import pytest

from uc3m.application.dataset import construction as cn
from uc3m.application.dataset import provenance as pv

MONTHS = ['ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic']
HEADER = 'Edificio;Mes;Año;EnergiaActivaHoraPunta;EnergiaActivaFueraPunta;EnergiaReactiva;FactorCarga;totalEnergiaActiva;TotalFacturado;Tarifa\n'


def _bill(path, rows):
    lines = [HEADER]
    for year, month, peak, offpeak, load_factor in rows:
        total = peak + offpeak
        lines.append(f'X;{MONTHS[month-1]};{year};{peak:.1f}'.replace('.', ',') +
                     f';{offpeak:.1f}'.replace('.', ',') + f';0;{load_factor}'.replace('.', ',') +
                     f';{total:.1f}'.replace('.', ',') + ';0;MT3\n')
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(lines), encoding='utf-8')
    return path


def _full_year(year, level, share=0.2, lf=0.6):
    return [(year, m, level*(1 + 0.1*m)*share, level*(1 + 0.1*m)*(1 - share), lf) for m in range(1, 13)]


INVENTORY = {1: {'area_m2': 1000.0, 'use_type': 'Office'}, 2: {'area_m2': 500.0, 'use_type': 'Office'},
             3: {'area_m2': 2000.0, 'use_type': 'Retail'}, 6: {'area_m2': 4000.0, 'use_type': 'Commercial_Mall'}}


def _records(tmp_path, b06_2024_level=900.0):
    raw = tmp_path/'raw'
    files = {
        2: _bill(raw/'B_02.csv', _full_year(2023, 100) + _full_year(2024, 110)),
        3: _bill(raw/'B_03.csv', _full_year(2023, 300) + _full_year(2024, 320)),
        6: _bill(raw/'B_06.csv', [(2023, m, 160.0, 640.0, 0.15 if m == 9 else 0.6) for m in range(9, 13)]
                 + _full_year(2024, b06_2024_level)),
    }
    records = []
    for bid, path in files.items():
        records.extend(cn.parse_billing_csv(path, bid))
    return records


def test_generated_bill_is_not_measured_source(tmp_path):
    bill = _bill(tmp_path/'raw/B_01.csv', _full_year(2023, 50))
    entries = [{'path': 'raw/B_01.csv', 'source_type': 'project_generated_billing',
                'generated_by': 'tools/dataset/generate_b01_billing.py', 'source_uri': 'local',
                'obtained_at': '2026-11-01', 'available_at': 'unknown',
                'license_or_access_note': 'project file'}]
    manifest = pv.audit_raw_sources(entries, root=tmp_path)
    source = manifest.sources[0]
    assert source.measured is False and source.approved_role == 'excluded_modeled_input'
    assert source.sha256 == pv.sha256_file(bill)
    with pytest.raises(ValueError):  # a generated bill cannot be declared as a measurement
        pv.audit_raw_sources([{**entries[0], 'source_type': 'measured_billing'}], root=tmp_path)
    with pytest.raises(ValueError):
        pv.audit_raw_sources([{**entries[0], 'source_type': 'training_artifact', 'generated_by': None}],
                             root=tmp_path)
    leaked = tmp_path/'outputs/old_run/results.json'
    leaked.parent.mkdir(parents=True)
    leaked.write_text('{}', encoding='utf-8')
    with pytest.raises(ValueError):
        pv.audit_raw_sources([{**entries[0], 'path': 'outputs/old_run/results.json',
                               'source_type': 'measured_billing', 'generated_by': None}], root=tmp_path)


def test_b01_has_explicit_modeled_provenance(tmp_path):
    targets = cn.complete_monthly_targets(_records(tmp_path), INVENTORY, years=(2023, 2024),
                                          buildings=(1, 2, 3, 6))
    b01 = [t for t in targets if t.building_id == 1]
    assert len(b01) == 24
    assert all(t.provenance == 'modeled' and t.method == 'peer_intensity_same_year' for t in b01)
    jan = next(t for t in b01 if (t.year, t.month) == (2023, 1))
    peer = next(t for t in targets if (t.building_id, t.year, t.month) == (2, 2023, 1))
    assert jan.energy_kwh == pytest.approx(peer.energy_kwh/500.0*1000.0)  # only same-year Office peer
    assert jan.inputs == ('B02:2023-01',)


def test_b06_fit_excludes_heldout_years(tmp_path):
    base = {(t.year, t.month): t for t in cn.complete_monthly_targets(
        _records(tmp_path/'a'), INVENTORY, years=(2023, 2024), buildings=(2, 3, 6)) if t.building_id == 6}
    perturbed = {(t.year, t.month): t for t in cn.complete_monthly_targets(
        _records(tmp_path/'b', b06_2024_level=5000.0), INVENTORY, years=(2023, 2024),
        buildings=(2, 3, 6)) if t.building_id == 6}
    modeled = [(2023, m) for m in range(1, 9)]
    assert all(base[k].provenance == 'modeled' and base[k].fit_scope == 'same_building_same_year'
               for k in modeled)
    # Changing the 2024 bills does not move any 2023 value of the training year.
    assert all(base[k].energy_kwh == pytest.approx(perturbed[k].energy_kwh) for k in modeled)
    assert all('2024' not in item for k in modeled for item in base[k].inputs)
    # The partial September (load factor 0.15) stays measured but is not used to fit.
    assert base[(2023, 9)].provenance == 'measured' and 'partial_month_suspect' in base[(2023, 9)].flags
    assert all('B06:2023-09' not in base[k].inputs for k in modeled)


def _shifted_bill(path, offset, rows=24):
    registers = [1000.0 + 137.0*i for i in range(rows)]
    totals = [registers[i - offset] if 0 <= i - offset < rows else 5000.0 for i in range(rows)]
    months = ('ene', 'feb', 'mar', 'abr', 'may', 'jun', 'jul', 'ago', 'set', 'oct', 'nov', 'dic')
    lines = ['Edificio;Mes;Anio;EnergiaActivaHoraPunta;EnergiaActivaFueraPunta;EnergiaReactiva;FactorCarga;'
             'totalEnergiaActiva;TotalFacturado;Tarifa']
    for i, (register, total) in enumerate(zip(registers, totals)):
        lines.append(f'X;{months[i % 12]};{2023 + i//12};{register*0.2:.2f};{register*0.8:.2f};0;0,5;{total:.2f};100;MT3')
    path.write_text('\n'.join(lines).replace('.', ','), encoding='utf-8')
    return registers


@pytest.mark.parametrize('offset', [7, -5])
def test_a_shifted_printed_total_never_moves_energy_between_months(tmp_path, offset):
    # D-V6-57: B11, January 2023 went from 51 660 to the 83 749 kWh of another row.
    registers = _shifted_bill(tmp_path/'bill.csv', offset)
    records = cn.parse_billing_csv(tmp_path/'bill.csv', 11, scale_tou_to_printed_total=True)
    assert [r.energy_kwh for r in records] == pytest.approx(registers, abs=0.02)
    assert all('tou_scaled_to_printed_total' not in r.flags for r in records)
    assert all('printed_total_column_shifted' in r.flags for r in records)


def test_the_offset_needs_most_rows_to_agree():
    registers = [1000.0 + 137.0*i for i in range(24)]
    assert cn.printed_total_offset(registers, registers) == 0
    assert cn.printed_total_offset(registers, [1.0]*24) == 0
    few = registers[:8]
    assert cn.printed_total_offset(few, [9.0]*3 + few[:5]) == 0                      # too few rows to decide
    mostly_wrong = [registers[i - 7] if i % 2 and i >= 7 else 9.0 for i in range(24)]
    assert cn.printed_total_offset(registers, mostly_wrong) == 0


def _target(month, energy, factor=0.5, year=2025):
    return cn.MonthlyRecord(11, year, month, energy, energy*0.2, energy*0.8, 'measured', 'bill', 'measured',
                            (f'B11:{year}-{month:02d}',), (), factor, 100.0)


def test_a_second_supply_adds_measured_months_and_models_the_rest_by_its_ratio():
    # D-V6-58, with the shape of B11: two months measure both supplies, one month only the bill.
    other = cn.MonthlyRecord(3, 2025, 2, 50.0, 10.0, 40.0, 'measured', 'bill', 'measured', ('B03',), (), 0.4, 9.0)
    targets = [_target(2, 100.0), _target(3, 200.0), _target(4, 300.0, year=2023), other]
    rows = {(2025, 2): (250.0, 2.0), (2025, 3): (500.0, 2.0)}
    out = cn.add_second_supply(targets, 11, rows, source_label='sheet')
    assert out[3] == other
    assert out[0].energy_kwh == pytest.approx(350.0) and out[0].provenance == 'measured'
    assert 'second_supply_measured' in out[0].flags
    assert out[2].energy_kwh == pytest.approx(300.0*(1 + 2.5)) and out[2].provenance == 'modeled'
    assert 'second_supply_modeled' in out[2].flags and 'sheet:ratio=2.500000' in out[2].inputs
    assert out[2].peak_kwh + out[2].offpeak_kwh == pytest.approx(out[2].energy_kwh)
    assert out[2].peak_kwh/out[2].energy_kwh == pytest.approx(0.2)
    assert all(0 < r.load_factor <= 1 for r in out) and out[0].billed_amount is None


def test_a_second_supply_needs_a_month_measured_on_both():
    with pytest.raises(ValueError, match='no month measures both'):
        cn.add_second_supply([_target(2, 100.0)], 11, {(2025, 9): (10.0, 1.0)}, source_label='sheet')


BILLS = Path(__file__).resolve().parents[2]/'CityLearn/data/buildingcsv'


@pytest.mark.skipif(not BILLS.is_dir(), reason='source bills not present')
def test_exactly_the_six_shifted_bills_are_detected():
    shifted = set()
    for building in [b for b in range(2, 18)]:
        records = cn.parse_billing_csv(BILLS/f'B_{building:02d}.csv', building, scale_tou_to_printed_total=True)
        if any('printed_total_column_shifted' in r.flags for r in records):
            shifted.add(building)
            assert not any('tou_scaled_to_printed_total' in r.flags for r in records), building
    assert shifted == {2, 4, 9, 11, 16, 17}


def test_billing_columns_by_header_and_relative_partial_months(tmp_path):
    # B_09 style: an empty spare column after the (mis-encoded) year header.
    path = tmp_path/'B_09.csv'
    lines = ['Edificio9;Mes;A�o;;EnergiaActivaHoraPunta;EnergiaActivaFueraPunta;EnergiaReactiva;'
             'FactorCarga;totalEnergiaActiva;TotalFacturado;Tarifa\n']
    for m in range(1, 13):
        lines.append(f'X;{MONTHS[m-1]};2023;;100,0;400,0;0;0,25;500,0;250,0;MT2\n')
    path.write_text(''.join(lines), encoding='utf-8')
    records = cn.parse_billing_csv(path, 9)
    assert len(records) == 12 and records[0].energy_kwh == 500.0 and records[0].billed_amount == 250.0
    targets = cn.complete_monthly_targets(records, {9: {'area_m2': 1.0, 'use_type': 'Office'}},
                                          years=(2023,), buildings=(9,))
    # A low but stable load factor is the building's regime, not a partial month.
    assert all('partial_month_suspect' not in t.flags for t in targets)


def test_energy_only_records_get_same_year_peer_split(tmp_path):
    records = _records(tmp_path)
    b01 = cn.energy_only_records(1, [(2024, m, 1000.0 + m) for m in range(1, 11)], records, INVENTORY,
                                 source_label='report:8.ELOR')
    assert len(b01) == 10 and all(r.provenance == 'measured' for r in b01)
    assert all('tou_split_modeled' in r.flags for r in b01)
    peer = next(r for r in records if (r.building_id, r.year, r.month) == (2, 2024, 3))
    march = next(r for r in b01 if r.month == 3)
    assert march.peak_kwh/march.energy_kwh == pytest.approx(peer.peak_kwh/peer.energy_kwh)
    assert march.inputs == ('report:8.ELOR:2024-03', 'split:B02:2024-03')
    targets = cn.complete_monthly_targets(records + b01, INVENTORY, years=(2023, 2024), buildings=(1, 2, 3, 6))
    by = {(t.year, t.month): t for t in targets if t.building_id == 1}
    assert by[(2024, 11)].method == 'same_year_shape_scaling'
    assert all('2023' not in item for item in by[(2024, 11)].inputs)
    assert by[(2023, 5)].method == 'peer_intensity_same_year'  # no 2024 value enters 2023


def test_declared_backcast_is_labelled_cross_year_leakage(tmp_path):
    records = _records(tmp_path)
    b01 = cn.energy_only_records(1, [(2024, m, 1000.0*m) for m in range(1, 13)], records, INVENTORY,
                                 source_label='report:8.ELOR')
    backcast = {1: cn.DeclaredBackcast(year=2023, from_year=2024, scale=0.98,
                                       reason='owner decision: original B01 method')}
    targets = cn.complete_monthly_targets(records + b01, INVENTORY, years=(2023, 2024), buildings=(1, 2, 3, 6),
                                          declared_backcasts=backcast)
    by = {(t.year, t.month): t for t in targets if t.building_id == 1}
    total_2024 = sum(1000.0*m for m in range(1, 13))
    assert by[(2023, 5)].energy_kwh == pytest.approx(0.98*total_2024*(5000.0/total_2024))
    assert by[(2023, 5)].method == 'declared_backcast' and 'cross_year_leakage_declared' in by[(2023, 5)].flags
    assert by[(2023, 5)].inputs[0] == 'B01:2024-05'
    # The backcast applies only where it is declared; other buildings never cross years.
    assert all('cross_year_leakage_declared' not in t.flags for t in targets if t.building_id != 1)
    with pytest.raises(ValueError):  # a backcast needs a complete measured source year
        cn.complete_monthly_targets(records + b01[:6], INVENTORY, years=(2023, 2024), buildings=(1, 2, 3, 6),
                                    declared_backcasts=backcast)


def test_monthly_and_peak_energy_close(tmp_path):
    target = cn.MonthlyRecord(2, 2023, 1, 744.0, 155.0, 589.0, 'measured', 'billing', 'measured', ())
    hourly = []
    from datetime import datetime, timedelta
    t0 = datetime.fromisoformat('2023-01-01T00:00:00-05:00')
    for h in range(744):
        stamp = t0 + timedelta(hours=h)
        hourly.append((stamp.isoformat(), 1.0))
    ok = cn.check_monthly_balance({2: hourly}, [target])
    assert all(check['passed'] for check in ok), ok
    off = [(stamp, value*1.0002) for stamp, value in hourly]  # 0.02 % > 0.01 % tolerance
    assert not all(check['passed'] for check in cn.check_monthly_balance({2: off}, [target]))


def _fake_generator(request):
    import random
    rng = random.Random(request.generation_seed)
    for building in request.buildings:
        rows = [f'{rng.random():.6f}' for _ in range(24)]
        (request.output_dir/f'Building_{building}.csv').write_text('load\n' + '\n'.join(rows) + '\n')
    (request.output_dir/'schema.json').write_text(json.dumps({'buildings': list(request.buildings)}))


def _config(seed=7):
    return cn.DatasetBuildConfig(campaign_id='fresh_test_v1', years=(2023,), buildings=(2, 3),
                                 generation_seed=seed, currency='USD', time_zone='America/Lima',
                                 parameters={'pv_method': 'synthetic'})


def test_no_write_inside_dependency(tmp_path):
    sources = pv.RawSourceManifest((), 'x'*64)
    for forbidden in ('CityLearn/data/datasets/new', 'external/HARL/data', 'outputs/old'):
        with pytest.raises(ValueError):
            cn.build_dataset(sources, _config(), tmp_path/forbidden, project_root=tmp_path,
                             generator=_fake_generator, targets=())


def test_same_raw_and_seed_reproduce_dataset_hash(tmp_path):
    sources = pv.RawSourceManifest((), 'a'*64)
    out = lambda name: tmp_path/'data/campaigns'/name/'dataset'  # noqa: E731
    first = cn.build_dataset(sources, _config(), out('fresh_a_v1'), project_root=tmp_path,
                             generator=_fake_generator, targets=())
    second = cn.build_dataset(sources, _config(), out('fresh_b_v1'), project_root=tmp_path,
                              generator=_fake_generator, targets=())
    other = cn.build_dataset(sources, _config(seed=8), out('fresh_c_v1'), project_root=tmp_path,
                             generator=_fake_generator, targets=())
    assert first.dataset_hash == second.dataset_hash != other.dataset_hash
    assert first.config_hash == second.config_hash
    with pytest.raises(FileExistsError):  # a frozen dataset is never overwritten
        cn.build_dataset(sources, _config(), out('fresh_a_v1'), project_root=tmp_path,
                         generator=_fake_generator, targets=())


@pytest.mark.parametrize('relative', ['C:/Windows/win.ini', 'D:\other\bill.csv', '\\server\share\bill.csv',
                                      'C:bill.csv'])
def test_windows_absolute_and_unc_sources_rejected(tmp_path, relative):
    entry = {'path': relative, 'source_type': 'measured_billing', 'source_uri': 'x', 'obtained_at': '2026-01-01'}
    with pytest.raises(ValueError):
        pv.audit_raw_sources([entry], root=tmp_path)


def test_source_under_parent_junction_rejected(tmp_path):
    import os
    outside = tmp_path/'outside'
    outside.mkdir()
    (outside/'bill.csv').write_text('a\n', encoding='utf-8')
    root = tmp_path/'root'
    (root/'raw').mkdir(parents=True)
    if os.name == 'nt':
        import _winapi
        _winapi.CreateJunction(str(outside), str(root/'raw/linked'))
    else:  # pragma: no cover
        os.symlink(outside, root/'raw/linked', target_is_directory=True)
    entry = {'path': 'raw/linked/bill.csv', 'source_type': 'measured_billing', 'source_uri': 'x',
             'obtained_at': '2026-01-01'}
    with pytest.raises(ValueError, match='link'):
        pv.audit_raw_sources([entry], root=root)
