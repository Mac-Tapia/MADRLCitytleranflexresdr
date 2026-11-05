"""Build the dataset of a fresh campaign from primary sources only (T2).

Writes everything under data/campaigns/<storage_alias>/:
  raw/       copies of the approved bills and inventory, new weather and FX downloads
  dataset/   CityLearn files (Building_X.csv, chargers, weather, pricing, schema.json)
  audit/     calibration and DER sizing audit files
  provenance.json, quality_flags.csv, dataset_build_manifest.json, dataset_acceptance.json

Nothing is read from the prior hourly dataset, outputs/ or .cache/. Differences
from the earlier generation chain, each a defect for a fresh campaign:
  - weather: NASA POWER requested in UTC and converted to America/Lima for each
    observed year (the earlier request was UTC indexed as local time, 5 h shift,
    and the PV step used a repeated typical year);
  - monthly targets: missing months completed without crossing years
    (uc3m.application.dataset.construction); B_01.csv is project-generated and
    is not used as a measurement;
  - prices: billed amounts are in PEN and are converted to USD with the official
    annual rate of the World Bank (PA.NUS.FCRF), never relabelled.

Campaign v2 realism design (owner decisions 2026-11-01): one building-type
registry for every module (configs/dataset/building_types.yaml); heat pumps
calibrated with CityLearn's own COP and frozen in the schema; controlled machines
inside the bills; TOU blocks scaled to the printed total; one constant carbon
factor; rooftop PV and BESS sized by the MicroGrids LP on pvlib AC per kWp (all
buildings grid-connected, export credited at the purchase price, no curtailment);
EV only as a 2-motorcycle pilot at B01; bills closed against a no-control
CityLearn simulation of the train split.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
for path in (ROOT, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import requests  # noqa: E402

from uc3m.application.dataset import construction as cn  # noqa: E402
from uc3m.application.dataset import provenance as pv  # noqa: E402
from uc3m.application.dataset import tariff_crosscheck as tc  # noqa: E402
from uc3m.application.training.preflight import hash_files  # noqa: E402

BUSBAR_CSV = ROOT/'data/tariffs/osinergmin/busbar_electro_oriente.csv'
YEARS = (2023, 2024, 2025)
BUILDINGS = tuple(range(1, 18))
LAT, LON, TZ = -3.7491, -73.2538, 'America/Lima'
NASA_PARAMETERS = 'T2M,RH2M,ALLSKY_SFC_SW_DWN,ALLSKY_SFC_SW_DIFF,ALLSKY_SFC_SW_DNI,WS10M'
NASA_URL = ('https://power.larc.nasa.gov/api/temporal/hourly/point?parameters={p}&community=RE'
            '&longitude={lon}&latitude={lat}&start={start}&end={end}&format=JSON&time-standard=UTC')
FX_URL = 'https://api.worldbank.org/v2/country/PER/indicator/PA.NUS.FCRF?format=json&date=2023:2025'
NASA_FILL = -999.0
MAX_FILLED_GAP_HOURS = 3
BUILDINGCSV = ROOT/'CityLearn/data/buildingcsv'
MICROGRIDS = ROOT/'external/MicroGrids/MicroGrids'
GENERATED_BILLS = {1: 'tools/dataset/generate_b01_billing.py'}
# B01 primary source: measured monthly energy in the study workbook (sheet 8.ELOR).
REPORT_SOURCE = ROOT/'docs/thesis/resultados_preliminares.xlsx'
REPORT_SHEET = '8.ELOR'
# Owner decision 2026-11-01: B01 has no 2023 measurement and same-year Office
# peers do not represent a utility plant; 2023 follows the original B01 method
# (2024 measured monthly profile x 0.98) and is flagged as declared leakage.
DECLARED_BACKCASTS = {1: cn.DeclaredBackcast(year=2023, from_year=2024, scale=0.98,
                                             reason='original tools/dataset/generate_b01_billing.py method')}
BILLING_CURRENCY = 'PEN'  # Peruvian distributor bills (Electro Oriente, MT3)
PEAK_TO_OFFPEAK_RATIO_ASSUMPTION = 0.38/0.26


def _rel(path: Path) -> str:
    return Path(path).resolve().relative_to(ROOT).as_posix()


def _write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding='utf-8')


# ── raw sources ──────────────────────────────────────────────────────────────

def stage_billing(raw_dir: Path):
    target = raw_dir/'buildingcsv'
    target.mkdir(parents=True)
    entries = []
    for building in BUILDINGS:
        source = BUILDINGCSV/f'B_{building:02d}.csv'
        copy = target/source.name
        shutil.copyfile(source, copy)
        generated = GENERATED_BILLS.get(building)
        entries.append({'path': _rel(copy), 'source_type': 'project_generated_billing' if generated else 'measured_billing',
                        'generated_by': generated, 'source_uri': _rel(source), 'obtained_at': 'repository copy',
                        'available_at': 'monthly, after each billing period',
                        'license_or_access_note': 'owner-provided distributor bills',
                        'notes': f'billed amounts in {BILLING_CURRENCY}'})
    report = raw_dir/'thesis'/REPORT_SOURCE.name
    report.parent.mkdir(parents=True)
    shutil.copyfile(REPORT_SOURCE, report)
    entries.append({'path': _rel(report), 'source_type': 'measured_report_table', 'source_uri': _rel(REPORT_SOURCE),
                    'obtained_at': 'repository copy', 'available_at': 'monthly',
                    'license_or_access_note': 'owner-provided study workbook',
                    'notes': f'sheet {REPORT_SHEET}: B01 monthly active energy EA [kWh], 2024-01..2025-10, no TOU split'})
    inventory = target/'building.csv'
    shutil.copyfile(BUILDINGCSV/'building.csv', inventory)
    entries.append({'path': _rel(inventory), 'source_type': 'building_inventory', 'source_uri': _rel(BUILDINGCSV/'building.csv'),
                    'obtained_at': 'repository copy', 'available_at': 'static',
                    'license_or_access_note': 'owner-provided inventory'})
    return entries


def _nasa_year(year: int, raw_dir: Path):
    url = NASA_URL.format(p=NASA_PARAMETERS, lon=LON, lat=LAT, start=f'{year}0101', end=f'{year+1}0101')
    response = requests.get(url, timeout=300)
    response.raise_for_status()
    path = raw_dir/'weather'/f'nasa_power_{year}_utc.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    parameters = response.json()['properties']['parameter']
    keys = list(parameters['T2M'].keys())
    if any(set(parameters[name]) != set(keys) for name in parameters):
        raise ValueError(f'NASA POWER {year}: parameters do not cover the same hours')
    stamps = pd.to_datetime(keys, format='%Y%m%d%H', utc=True)
    frame = pd.DataFrame({name: [parameters[name][key] for key in keys] for name in parameters}, index=stamps)
    local = frame.tz_convert(TZ)
    local = local[local.index.year == year]
    expected = pd.date_range(f'{year}-01-01', periods=8784 if year == 2024 else 8760, freq='h', tz=TZ)
    if not local.index.equals(expected):
        raise ValueError(f'NASA POWER {year}: local hourly index is not complete')
    gaps = {}
    for column in local.columns:
        missing = local[column] <= NASA_FILL + 1e-9
        if missing.any():
            runs = (missing != missing.shift()).cumsum()[missing].value_counts()
            if runs.max() > MAX_FILLED_GAP_HOURS:
                raise ValueError(f'NASA POWER {year} {column}: gap of {runs.max()} h exceeds {MAX_FILLED_GAP_HOURS} h')
            local.loc[missing, column] = np.nan
            local[column] = local[column].interpolate(limit_direction='both')
            gaps[column] = int(missing.sum())
    weather = pd.DataFrame({'GHI': local['ALLSKY_SFC_SW_DWN'].clip(lower=0), 'DHI': local['ALLSKY_SFC_SW_DIFF'].clip(lower=0),
                            'DNI': local['ALLSKY_SFC_SW_DNI'].clip(lower=0), 'T2M': local['T2M'],
                            'RH2M': local['RH2M'], 'WS': local['WS10M'].clip(lower=0)}, index=expected)
    weather.to_parquet(raw_dir/'weather'/f'{year}.parquet')
    entry = {'path': _rel(path), 'source_type': 'weather_reanalysis', 'source_uri': url,
             'obtained_at': datetime.now(timezone.utc).isoformat(), 'available_at': 'observed hour (reanalysis)',
             'license_or_access_note': 'NASA POWER, public; https://power.larc.nasa.gov',
             'notes': f'UTC converted to {TZ}; filled hours (<= {MAX_FILLED_GAP_HOURS} h gaps): {gaps}'}
    return weather, entry, gaps


def stage_weather(raw_dir: Path):
    frames, entries, gaps = {}, [], {}
    for year in YEARS:
        frames[year], entry, gaps[year] = _nasa_year(year, raw_dir)
        entries.append(entry)
    return frames, entries, gaps


def stage_exchange_rate(raw_dir: Path):
    response = requests.get(FX_URL, timeout=120)
    response.raise_for_status()
    path = raw_dir/'fx'/'worldbank_pa_nus_fcrf_per.json'
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(response.content)
    rates = {int(row['date']): float(row['value']) for row in response.json()[1] if row['value'] is not None}
    missing = [y for y in YEARS if y not in rates]
    if missing:
        raise ValueError(f'official PEN/USD rate missing for {missing}')
    entry = {'path': _rel(path), 'source_type': 'official_statistic', 'source_uri': FX_URL,
             'obtained_at': datetime.now(timezone.utc).isoformat(), 'available_at': 'annual average',
             'license_or_access_note': 'World Bank WDI, CC BY 4.0',
             'notes': 'PA.NUS.FCRF official exchange rate, PEN per USD, period average'}
    return {y: rates[y] for y in YEARS}, entry


# ── monthly targets ──────────────────────────────────────────────────────────

def read_inventory(raw_dir: Path, registry=None):
    """Floor area from building.csv; the peer group from the canonical registry when given."""
    frame = pd.read_csv(raw_dir/'buildingcsv'/'building.csv')
    inventory = {int(str(row.ID_Edificio).split('_')[1]): {'area_m2': float(row.Area_Techada_m2),
                                                           'use_type': str(row.Tipo_Uso_CityLearn)}
                 for row in frame.itertuples(index=False)}
    if registry is not None:
        for building, row in inventory.items():
            row['use_type'] = registry['buildings'][building]['peer_group']
    return inventory


def read_tariffs(raw_dir: Path):
    tariffs = {}
    for building in BUILDINGS:
        if building in GENERATED_BILLS:
            continue
        # Column located by header (B_09 has a spare column) and ties broken by name, so
        # the label never depends on hash-randomized set ordering.
        lines = cn._read_text(raw_dir/'buildingcsv'/f'B_{building:02d}.csv').splitlines()
        header = [cn._key(h) for h in lines[0].split(';')]
        at = header.index('tarifa')
        values = [line.split(';')[at].strip() for line in lines[1:]
                  if line.count(';') >= at and line.split(';')[at].strip()]
        tariffs[building] = min(sorted(set(values)), key=lambda v: -values.count(v)) if values else 'MT3'
    return tariffs


def monthly_targets(raw_dir: Path, registry=None):
    records = []
    for building in BUILDINGS:
        if building in GENERATED_BILLS:
            continue
        rows = cn.parse_billing_csv(raw_dir/'buildingcsv'/f'B_{building:02d}.csv', building,
                                    scale_tou_to_printed_total=registry is not None)
        records.extend(r for r in rows if r.year in YEARS)
    inventory = read_inventory(raw_dir, registry)
    sheet = pd.read_excel(raw_dir/'thesis'/REPORT_SOURCE.name, sheet_name=REPORT_SHEET, header=None)
    report_rows = [(int(row[1]), int(row[2]), float(row[3])) for row in sheet.itertuples(index=False, name=None)
                   if str(row[0]).strip() == 'CONSUMOS ELOR' and int(row[1]) in YEARS]
    records.extend(cn.energy_only_records(1, report_rows, records, inventory,
                                          source_label=f'resultados_preliminares:{REPORT_SHEET}'))
    return records, cn.complete_monthly_targets(records, inventory, years=YEARS, buildings=BUILDINGS,
                                                declared_backcasts=DECLARED_BACKCASTS)


def measurements_frame(targets, tariffs, raw_dir: Path, fx):
    """Calibration input; billed amounts are converted to USD so no PEN value is relabelled."""
    rows = []
    for t in targets:
        rows.append({'building_id': t.building_id, 'year': t.year, 'month': t.month,
                     'source_name': f'Building_{t.building_id}', 'energia_punta_kwh': t.peak_kwh,
                     'energia_fuera_punta_kwh': t.offpeak_kwh, 'energia_total_kwh': t.energy_kwh,
                     'raw_energia_punta_kwh': t.peak_kwh, 'raw_energia_fuera_punta_kwh': t.offpeak_kwh,
                     'raw_split_total_kwh': t.energy_kwh, 'energia_reactiva_kvarh': 0.0,
                     'factor_carga': t.load_factor if t.load_factor is not None else 0.0,
                     'total_facturado': t.billed_amount/fx[t.year] if t.billed_amount is not None else 0.0,
                     'reported_total_energia_activa': t.energy_kwh, 'reported_total_delta_kwh': 0.0,
                     'reported_total_delta_pct': 0.0, 'active_energy_source': 'fresh_monthly_target',
                     'measurement_quality_flag': '|'.join((t.provenance,) + t.flags),
                     'tarifa': tariffs.get(t.building_id, 'MT3'),
                     'source_file': _rel(raw_dir/'buildingcsv'/f'B_{t.building_id:02d}.csv'),
                     'line_number': 0, 'record_type': 'measured' if t.provenance == 'measured' else 'forecast',
                     'forecast_method': '' if t.provenance == 'measured' else t.method,
                     'forecast_scale_factor': np.nan,
                     'forecast_reference_months': ';'.join(t.inputs)})
    return pd.DataFrame(rows).sort_values(['building_id', 'year', 'month']).reset_index(drop=True)


# ── exogenous signals ────────────────────────────────────────────────────────

def hourly_pricing_usd(index: pd.DatetimeIndex, measured, fx):
    """District price per month from that month's measured bills, PEN -> USD."""
    monthly = {}
    for record in measured:
        if record.billed_amount is None or record.billed_amount <= 0 or 'partial_month_suspect' in record.flags:
            continue
        entry = monthly.setdefault((record.year, record.month), [0.0, 0.0, 0.0])
        entry[0] += record.billed_amount
        entry[1] += record.energy_kwh
        entry[2] += record.peak_kwh
    price = np.empty(len(index))
    audit = []
    for (year, month), (amount, energy, peak) in sorted(monthly.items()):
        mask = (index.year == year) & (index.month == month)
        average_usd = amount/energy/fx[year]
        share = peak/energy
        offpeak = average_usd/(PEAK_TO_OFFPEAK_RATIO_ASSUMPTION*share + (1 - share))
        peak_price = offpeak*PEAK_TO_OFFPEAK_RATIO_ASSUMPTION
        price[mask] = np.where(np.isin(index.hour[mask], list(cn.PEAK_HOURS)), peak_price, offpeak)
        audit.append({'year': year, 'month': month, 'billed_pen': amount, 'energy_kwh': energy,
                      'pen_per_usd': fx[year], 'average_usd_per_kwh': average_usd,
                      'peak_usd_per_kwh': peak_price, 'offpeak_usd_per_kwh': offpeak})
    months = {(t.year, t.month) for t in index}
    if months - set(monthly):
        raise ValueError(f'no usable bill for months {sorted(months - set(monthly))}')

    def shifted(values, k):
        out = np.empty_like(values)
        out[:-k], out[-k:] = values[k:], values[-1]
        return out
    frame = pd.DataFrame({'electricity_pricing': price})
    for k in (1, 2, 3):  # kept for schema compatibility; T3 removes predicted fields from observations
        frame[f'electricity_pricing_predicted_{k}'] = shifted(price, k)
    return frame, audit


# ── official tariff (campaign v3, Osinergmin pliegos for sector Iquitos) ─────

PEAK_BLOCK_HOURS = tuple(sorted(cn.PEAK_HOURS))  # 18:00-23:00, the bills' peak block
B01_TARIFF_ASSUMPTION = 'MT2'  # label of the project-generated B_01.csv; no B01 bill exists


def stage_tariffs(raw_dir: Path):
    """Download every IQUITOS sheet in force during 2023-2025 (raw, verbatim) and parse it."""
    import osinergmin_pliegos as op
    from datetime import date
    entries = op.fetch_sheets(raw_dir/'osinergmin', date(YEARS[0], 1, 1), date(YEARS[-1], 12, 31))
    sheets, sources = {}, []
    for entry in entries:
        valid_from = date.fromisoformat(entry['valid_from'])
        sheets[valid_from] = op.parse_sheet(Path(entry['path']).read_bytes())
        sources.append({'path': _rel(entry['path']), 'source_type': 'official_tariff_sheet',
                        'source_uri': entry['source_uri'], 'obtained_at': entry['obtained_at'],
                        'available_at': f'in force from {entry["valid_from"]}',
                        'license_or_access_note': 'Osinergmin, Pliego Tarifario Maximo del Servicio Publico de '
                                                  'Electricidad, public web page (form postback)',
                        'notes': 'response labels ' + json.dumps(op.sheet_labels(Path(entry['path']).read_bytes()))
                                 + '; values without IGV'})
    return sheets, sources


def bill_details(raw_dir: Path):
    """Tariff label and reactive energy of every measured month, by header."""
    details = {}
    for building in BUILDINGS:
        if building in GENERATED_BILLS:
            continue
        lines = cn._read_text(raw_dir/'buildingcsv'/f'B_{building:02d}.csv').splitlines()
        header = [cn._key(h) for h in lines[0].split(';')]
        at = {name: header.index(name) for name in ('mes', 'tarifa', 'energiareactiva')}
        for line in lines[1:]:
            parts = line.split(';')
            if len(parts) <= max(at.values()) or not parts[at['mes']].strip() or not parts[at['mes'] + 1].strip():
                continue
            month = cn.MONTHS.get(parts[at['mes']].strip().casefold()[:3])
            year = int(parts[at['mes'] + 1].strip())
            details[(building, year, month)] = {'tariff': parts[at['tarifa']].strip(),
                                                'reactive_kvarh': cn._number(parts[at['energiareactiva']]) or 0.0}
    return details


def building_tariff(building, year, month, details, modes):
    row = details.get((building, year, month))
    if row and row['tariff']:
        return row['tariff'], 'bill'
    if building in modes:
        return modes[building], 'building_mode'
    return B01_TARIFF_ASSUMPTION, 'assumption'


def demand_rate_pen_kw(charges) -> float:
    """Peak-block capacity charge [PEN/kW-month]: HP generation + HP distribution (MT2/BT2) or
    the present-in-peak generation + distribution rates (MT3/MT4/BT3/BT4)."""
    if 'gen_hp_pen_kw' in charges:
        return charges['gen_hp_pen_kw'] + charges['dist_hp_pen_kw']
    if 'gen_present_peak_pen_kw' in charges:
        return charges['gen_present_peak_pen_kw'] + charges['dist_present_peak_pen_kw']
    return 0.0


def energy_rate_ctm(charges) -> np.ndarray:
    """One hourly rate per month: a sheet with a real peak/off-peak difference is refused (SPEC-013)."""
    rate = charges.get('energy_ctm_kwh', charges.get('energy_peak_ctm_kwh'))
    if not np.isclose(rate, charges.get('energy_offpeak_ctm_kwh', rate), rtol=0.0, atol=1e-9):
        raise ValueError(f'time-of-use energy charge is not modeled: {charges}')
    return rate


def tariff_signals(index: pd.DatetimeIndex, sheets, details, modes, fx):
    """Per building: hourly energy price [USD/kWh] and monthly peak-block demand charge [USD/kW-month].

    Each month uses the building's tariff of that month and the charges weighted by the
    days each sheet is in force (sheets change on the 4th of many months). Without IGV.
    """
    import osinergmin_pliegos as op
    out = {}
    for building in BUILDINGS:
        price = np.empty(len(index))
        demand, labels = {}, {}
        for (year, month) in sorted({(t.year, t.month) for t in index}):
            tariff, basis = building_tariff(building, year, month, details, modes)
            charges = op.weighted_charges(sheets, year, month, tariff)
            mask = (index.year == year) & (index.month == month)
            price[mask] = energy_rate_ctm(charges)/100.0/fx[year]
            demand[(year, month)] = demand_rate_pen_kw(charges)/fx[year]
            labels[(year, month)] = {'tariff': tariff, 'basis': basis,
                                     'sheets': op.month_coverage(sheets, year, month)}
        out[building] = {'energy_usd_kwh': price, 'demand_usd_kw_month': demand, 'tariff_by_month': labels}
    return out


def pricing_frame(price: np.ndarray) -> pd.DataFrame:
    def shifted(values, k):
        result = np.empty_like(values)
        result[:-k], result[-k:] = values[k:], values[-1]
        return result
    frame = pd.DataFrame({'electricity_pricing': price})
    for k in (1, 2, 3):  # kept for schema compatibility; the splits deactivate predicted fields
        frame[f'electricity_pricing_predicted_{k}'] = shifted(price, k)
    return frame


EXCLUDED_BILL_FLAGS = ('partial_month_suspect', 'printed_total_implausible')
PLAUSIBLE_RECONSTRUCTION_RATIO = (0.2, 5.0)  # recomputed/billed outside this: partial or mis-keyed bill


def _share_within(pred, billed, tolerance):
    error = np.abs(np.asarray(pred)/np.asarray(billed) - 1.0)
    return float((error <= tolerance).mean())


def tariff_bill_validation(measured, details, sheets, raw_dir: Path = None):
    """Recompute every measured bill from the official sheet, decompose the error and test hypotheses.

    Excluded from the statistics, with the reason: months flagged partial_month_suspect or
    printed_total_implausible, and months whose recomputed/billed ratio is outside 0.2..5.
    The capacity (demand) component is validated separately by a per-building regression
    billed = a*energy + b*capacity; it counts as validated only if every building's 90 %
    bootstrap interval of b contains 1.18 (IGV on the sheet charge) and excludes 0.
    """
    import statistics
    import osinergmin_pliegos as op
    rows = []
    for record in measured:
        detail = details.get((record.building_id, record.year, record.month))
        if detail is None or not record.billed_amount or not record.load_factor:
            continue
        bill = op.reconstruct_bill(tariff=detail['tariff'], year=record.year, month=record.month,
                                   peak_kwh=record.peak_kwh, offpeak_kwh=record.offpeak_kwh,
                                   reactive_kvarh=detail['reactive_kvarh'], load_factor=record.load_factor,
                                   sheets=sheets)
        ratio = bill['total_with_igv_pen']/record.billed_amount
        reason = next((f'flag {f}' for f in EXCLUDED_BILL_FLAGS if f in record.flags), None)
        if reason is None and not PLAUSIBLE_RECONSTRUCTION_RATIO[0] < ratio < PLAUSIBLE_RECONSTRUCTION_RATIO[1]:
            reason = f'recomputed/billed = {ratio:.2f} outside 0.2..5 (partial or mis-keyed bill)'
        rows.append({'building': record.building_id, 'year': record.year, 'month': record.month,
                     'tariff': detail['tariff'], 'billed_pen': record.billed_amount, **bill,
                     'error_with_igv': ratio - 1.0,
                     'error_without_igv': bill['subtotal_without_igv_pen']/record.billed_amount - 1.0,
                     'flags': list(record.flags), 'excluded_reason': reason})
    used = [r for r in rows if r['excluded_reason'] is None]
    billed = np.array([r['billed_pen'] for r in used])
    energy = np.array([r['energy_pen'] for r in used])
    capacity = np.array([r['capacity_pen'] for r in used])
    rest = np.array([r['fixed_pen'] + r['reactive_pen'] for r in used])
    sheet = energy + capacity + rest

    def variant(pred):
        return {'median_error': float(np.median(pred/billed - 1.0)),
                'share_within_10pct': _share_within(pred, billed, 0.10),
                'share_within_20pct': _share_within(pred, billed, 0.20)}
    history = {(r['building'], r['year'], r['month']): r['pmax_kw'] for r in rows}
    averaged = []
    for r in used:  # (c) capacity billed on the mean of the two highest Pmax of the last six months
        months = [(r['year'] - (1 if r['month'] - k < 1 else 0), (r['month'] - k - 1) % 12 + 1) for k in range(6)]
        values = sorted((history[(r['building'],) + m] for m in months if (r['building'],) + m in history),
                        reverse=True)
        averaged.append(r['capacity_pen']*float(np.mean(values[:2]))/r['pmax_kw'])
    hypotheses = {
        'baseline_sheet_with_igv': variant(sheet*1.18),
        'a_no_igv': variant(sheet),
        'b_capacity_half_of_E_over_LF_h': variant((energy + 0.5*capacity + rest)*1.18),
        'b_no_capacity_charge': variant((energy + rest)*1.18),
        'c_capacity_on_mean_of_two_highest_of_six_months': variant((energy + np.array(averaged) + rest)*1.18),
        'd_charges_outside_the_sheet': 'not testable: bills carry only TotalFacturado (no line items); extra charges '
                                       'would raise the bill, but with IGV the recomputed bill is already above it',
        'e_sector': 'confirmed from the response: DDLSE=IQUITOS, LBSector=2, LBInter=AISL in every sheet'}
    rng = np.random.default_rng(0)
    capacity_fit, validated = {}, bool(used)  # nothing usable is not a validation
    for building in sorted({r['building'] for r in used}):
        sel = [i for i, r in enumerate(used) if r['building'] == building]
        X = np.column_stack([energy[sel], capacity[sel]])
        coef, *_ = np.linalg.lstsq(X, billed[sel], rcond=None)
        boot = []
        for _ in range(500):
            k = rng.integers(0, len(sel), len(sel))
            boot.append(np.linalg.lstsq(X[k], billed[sel][k], rcond=None)[0][1])
        low, high = float(np.percentile(boot, 5)), float(np.percentile(boot, 95))
        ok = low <= 1.18 <= high and low > 0
        validated = validated and ok
        capacity_fit[str(building)] = {'energy_coefficient': float(coef[0]), 'capacity_coefficient': float(coef[1]),
                                       'capacity_coefficient_90pct': [low, high],
                                       'corr_energy_capacity': float(np.corrcoef(energy[sel], capacity[sel])[0, 1]),
                                       'consistent_with_sheet': ok}
    summary = {}
    for building in sorted({r['building'] for r in used}):
        mine = [r for r in used if r['building'] == building]
        errors = [r['error_with_igv'] for r in mine]
        ratio = [1.0/(1.0 + e) for e in errors]
        summary[str(building)] = {
            'months': len(mine),
            'excluded': sum(1 for r in rows if r['building'] == building and r['excluded_reason']),
            'tariffs': sorted({r['tariff'] for r in mine}),
            'median_error_with_igv': statistics.median(errors),
            'median_abs_error_with_igv': statistics.median(abs(e) for e in errors),
            'median_error_without_igv': statistics.median(r['error_without_igv'] for r in mine),
            'billed_over_recomputed_iqr': [float(np.percentile(ratio, 25)), float(np.percentile(ratio, 75))],
            'min_error_with_igv': min(errors), 'max_error_with_igv': max(errors)}
    sectors, definitions = {}, {}
    if raw_dir is not None:
        for path in sorted((raw_dir/'osinergmin').glob('pliego_iquitos_*.html')):
            payload = path.read_bytes()
            sectors[path.name] = op.sheet_labels(payload)
            for key, snippets in op.definitions_found(payload).items():
                definitions[key] = definitions.get(key, 0) + len(snippets)
    return {'method': 'fixed + energy (kWh x sheet charge) + capacity (Pmax = E/(LF*hours) x peak-block or '
                      'present-in-peak rate) + reactive (> 30 % of active), sheets weighted by days in force; IGV 18 %',
            'peak_block_hours_assumption': 'HP 18:00-23:00 every day (not defined in the downloaded sheets)',
            'present_in_peak_rule_assumption': '(E_peak/peak hours)/Pmax >= 0.5 (not defined in the downloaded sheets)',
            'definitions_search_in_sheets': {'keywords': list(op.DEFINITION_KEYWORDS), 'matches': definitions,
                                             'note': 'only charge labels match ("presentes en punta"); no peak-hour '
                                                     'block or qualification rule is printed'},
            'sheet_labels': sectors, 'months_total': len(rows), 'months_used': len(used),
            'excluded': [{k: r[k] for k in ('building', 'year', 'month', 'excluded_reason')}
                         for r in rows if r['excluded_reason']],
            'hypotheses': hypotheses,
            'conclusion': 'no single hypothesis closes the error: without IGV the bills are under-predicted, with IGV '
                          'over-predicted; billed/recomputed is stable for most MT buildings (systematic bias) and '
                          'its cause cannot be identified from bills without line items',
            'capacity_component': {
                'per_building_fit': capacity_fit, 'validated': validated,
                'status': 'validated' if validated else 'unverified',
                'note': '' if validated else 'energy and capacity are collinear within many buildings; the demand charge '
                                             'used for BESS sizing is the sheet value and is NOT verified against the bills'},
            'rows': rows, 'summary': summary}


# ── campaign v2 design inputs ────────────────────────────────────────────────

REGISTRY_PATH = ROOT/'configs/dataset/building_types.yaml'
ECONOMICS_PATH = ROOT/'configs/dataset/der_economics.yaml'
EV_PILOT_PATH = ROOT/'configs/dataset/ev_pilot.yaml'
EMISSIONS_PATH = ROOT/'configs/dataset/grid_emissions.yaml'
BESS_RULE_PATH = ROOT/'configs/dataset/bess_design_rule.yaml'
BESS_RULE_MIN_DELIVERED = 0.9  # of shaved_kw, every building and month: gate on the battery as sized
DHW_HEATER_EFFICIENCY = 0.85  # distill_building_loads.COP_ACS_DEF, the value the bills are closed with
DESIGN_YEAR = 2023  # DER sizing uses the training year only
CITYLEARN_BALANCE_RTOL = 0.005  # monthly energy, no-control CityLearn simulation vs bill
SENSITIVITY_SCALES = (0.7, 1.3)


def load_registry():
    import yaml
    return yaml.safe_load(REGISTRY_PATH.read_text(encoding='utf-8'))


def machine_baseline(frame: pd.DataFrame) -> np.ndarray:
    """As-billed machine load: each cycle starts at the first hour of its window.

    This is what CityLearn simulates when the washing-machine action is positive at
    every step (start at the window start), i.e. the no-control baseline.
    """
    start = frame['wm_start_time_step'].to_numpy(int)
    out = np.zeros(len(frame))
    for i in np.where(start == np.arange(len(frame)))[0]:
        profile = [float(x) for x in str(frame['load_profile'].iloc[i]).strip('[]').split(',') if x.strip()]
        for k, value in enumerate(profile):
            if i + k < len(out):
                out[i + k] += value
    return out


def as_billed_load(out: Path, building: int, schema, t_out) -> dict:
    """Hourly electricity of every bill component as CityLearn computes it."""
    import distill_building_loads as dl
    frame = pd.read_csv(out/f'Building_{building}.csv')
    attributes = schema['buildings'][f'Building_{building}']['cooling_device']['attributes']
    cop = dl.citylearn_cooling_cop(t_out, attributes['efficiency'], attributes['target_cooling_temperature'])
    dhw = schema['buildings'][f'Building_{building}'].get('dhw_device')
    dhw_eff = float(dhw['attributes']['efficiency']) if dhw else DHW_HEATER_EFFICIENCY
    machine = machine_baseline(pd.read_csv(out/f'Washing_Machine_{building}.csv'))
    parts = {'non_shiftable': frame['non_shiftable_load'].to_numpy(float),
             'cooling': frame['cooling_demand'].to_numpy(float)/cop,
             'dhw': frame['dhw_demand'].to_numpy(float)/dhw_eff, 'machines': machine}
    parts['total'] = sum(parts.values())
    return parts


def building_prices_usd(measured, fx, price_audit, year=DESIGN_YEAR):
    """Each building's own billed USD/kWh of the design year; district average where it has no bill."""
    district_energy = sum(r['energy_kwh'] for r in price_audit if r['year'] == year)
    district = sum(r['average_usd_per_kwh']*r['energy_kwh'] for r in price_audit if r['year'] == year)/district_energy
    prices = {}
    for building in BUILDINGS:
        rows = [r for r in measured if r.building_id == building and r.year == year and r.billed_amount
                and r.billed_amount > 0 and 'partial_month_suspect' not in r.flags]
        if rows:
            prices[building] = {'value': sum(r.billed_amount for r in rows)/sum(r.energy_kwh for r in rows)/fx[year],
                                'origin': 'derived', 'source': f'B_{building:02d}.csv TotalFacturado/kWh {year}, '
                                'World Bank PEN/USD', 'months': len(rows)}
        else:
            prices[building] = {'value': district, 'origin': 'derived', 'months': 0,
                                'source': f'district {year} billed average (building has no {year} bill amounts)'}
    return prices


# ── generation (injected port of the construction use case) ─────────────────

def make_generator(weather_frames, measured, targets, tariffs, fx, raw_dir: Path, audit_dir: Path, log, design):
    import generate_iquitos_dataset as gen
    import distill_building_loads as dl
    import dimension_ev_chargers as ev

    registry = design['registry']
    gen.apply_building_type_registry(registry)
    dl.configure_building_types(registry)
    ev.configure_building_types(registry)

    def generate(request: cn.GeneratorRequest) -> None:
        out = request.output_dir
        weather_full = pd.concat([weather_frames[y] for y in YEARS])
        zero_solar = pd.Series(np.zeros(len(weather_full)), index=weather_full.index)
        for building in request.buildings:
            gen.BuildingDataGenerator(building, weather_full, zero_solar).build().to_csv(
                out/f'Building_{building}.csv', index=False, float_format='%.6f')
        sfg = gen.SupportFilesGenerator()
        sfg.build_weather_csv(weather_frames).to_csv(out/'weather.csv', index=False, float_format='%.6f')
        ci_value, ci_derivation = gen.constant_carbon_intensity(EMISSIONS_PATH)
        design['carbon'] = ci_derivation
        sfg.build_constant_carbon_intensity(len(weather_full), ci_value).to_csv(
            out/'carbon_intensity.csv', index=False, float_format='%.9f')
        _, price_audit = hourly_pricing_usd(weather_full.index, measured, fx)  # bill-average audit only
        signals = design['tariff_signals']
        for building in request.buildings:  # official tariff: each building's own energy charge per hour
            pricing_frame(signals[building]['energy_usd_kwh']).to_csv(
                out/f'pricing_{building}.csv', index=False, float_format='%.9f')
        schema = gen.SchemaBuilder().build({}, {b: 0.0 for b in request.buildings}, {})
        chilled = float(registry['chilled_water_target_c']['value'])
        reference = (float(registry['reference_outdoor_temperature_c']) - chilled)/(chilled + 273.15)
        for building in request.buildings:
            config = schema['buildings'][f'Building_{building}']
            cop_design = float(registry['buildings'][building]['cooling_cop_design']['value'])
            config['cooling_device']['attributes'] = {'efficiency': round(cop_design*reference, 6),
                                                      'target_cooling_temperature': chilled}
            if 'dhw_device' in config:
                config['dhw_device'] = {'type': 'citylearn.energy_model.ElectricHeater', 'autosize': False,
                                        'attributes': {'nominal_power': config['dhw_device']['attributes']['nominal_power'],
                                                       'efficiency': DHW_HEATER_EFFICIENCY}}
            config.pop('electrical_storage', None)
            config.pop('chargers', None)
            config['pricing'] = f'pricing_{building}.csv'
        schema['electric_vehicles_def'] = {}
        # Net billing (user decision): with the community market off CityLearn keeps
        # cost = net x electricity_pricing[t], so an export hour is credited at that hour's
        # purchase price. No local peer market exists in Iquitos, so none is simulated.
        schema['community_market'] = {'enabled': False, 'export_settlement': 'net_billing_at_hourly_purchase_price'}
        _write_json(out/'schema.json', schema)
        import sync_controlled_machines as scm
        scm.configure(out)
        scm.sync_controlled_machines(out, out/'schema.json')
        log('base files, constant carbon factor, machines and schema written')

        frame = measurements_frame(targets, tariffs, raw_dir, fx)
        inventory = dl.load_building_inventory(raw_dir/'buildingcsv')
        schema = dl.load_schema(out)
        t_out = dl.load_weather(out)
        reports = {b: dl.calibrate_building(bldg_id=b, schema=schema, t_out=t_out, dataset_dir=out,
                                            inventory=inventory, measurements=frame,
                                            machine_elec=machine_baseline(pd.read_csv(out/f'Washing_Machine_{b}.csv')))
                   for b in request.buildings}
        dl.write_outputs(reports, inventory, frame, out, audit_dir/'distillation_report.csv')
        # write_outputs rebuilds a bill-average pricing.csv; the campaign price is the official tariff.
        (out/'pricing.csv').unlink(missing_ok=True)
        _write_json(audit_dir/'pricing_bill_average_audit.json', price_audit)
        metadata = json.loads((out/'building_metadata.json').read_text(encoding='utf-8'))
        metadata['building_types'] = {str(b): registry['buildings'][b]['canonical_type'] for b in request.buildings}
        metadata['building_type_registry'] = _rel(REGISTRY_PATH)
        _write_json(out/'building_metadata.json', metadata)
        log('loads calibrated with CityLearn heat-pump COP and machines inside the bills')

        design['der'] = size_der(out, audit_dir, weather_frames, inventory, measured, fx, price_audit, request,
                                 design, log)
        ev.write_pilot(out, audit_dir, ev.load_pilot_config(EV_PILOT_PATH))
        import fix_schema_cooling as fsc
        fsc.configure(out)
        fsc.main()
        log('PV and BESS (MicroGrids), B01 EV pilot and cooling autosize margin written')
        clean_orphans(out, audit_dir)
        import audit_citylearn_csv_integrity as integrity
        _write_json(audit_dir/'csv_integrity_manifest.json', integrity.audit(out))
        log('orphans moved out of the dataset and CSV integrity audited')

    return generate


def size_der(out: Path, audit_dir: Path, weather_frames, inventory, measured, fx, price_audit, request, design, log):
    import fix_solar_pvlib as fs
    import size_der_microgrids as sd
    economics = design['economics']
    registry = design['registry']
    schema = json.loads((out/'schema.json').read_text(encoding='utf-8'))
    import distill_building_loads as dl
    t_out = dl.load_weather(out)
    _, module = fs.select_sandia_module()
    module_kwp = float(module['Vmpo']*module['Impo']/1000.0)
    weather_design = weather_frames[DESIGN_YEAR]
    reference_modules = int(round(100.0/module_kwp))
    per_kwp = sd.pv_ac_w_per_kw(weather_design, reference_modules, module).to_numpy(float)/1000.0  # kWh per kWp
    signals = design['tariff_signals']
    usable = float(economics['pv']['usable_area_fraction']['value'])
    index_2023 = pd.date_range(f'{DESIGN_YEAR}-01-01', periods=8760, freq='h')
    peak_flag = np.isin(index_2023.hour, PEAK_BLOCK_HOURS).astype(int)
    workroot = audit_dir/'microgrids_runs'
    base, scaled = {}, {s: {} for s in SENSITIVITY_SCALES}
    rows = {}
    weather_full = pd.concat([weather_frames[y] for y in YEARS])
    for building in request.buildings:
        load = as_billed_load(out, building, schema, t_out)['total'][:8760]
        roof = sd.roof_bound_kwp(inventory[building].area_techada_m2, module, usable)
        energy = signals[building]['energy_usd_kwh'][:8760]
        tariff = {'energy_price': energy, 'period_month': index_2023.month.to_numpy(), 'peak_period': peak_flag,
                  'demand_charge': {m: signals[building]['demand_usd_kw_month'][(DESIGN_YEAR, m)] for m in range(1, 13)}}
        price = float(energy.mean())
        lp = sd.solve_microgrids(load, per_kwp, price, roof, economics, workroot/f'B{building:02d}', tariff=tariff)
        if lp['termination_condition'] != 'optimal':
            raise RuntimeError(f'B{building:02d}: MicroGrids LP {lp["termination_condition"]}')
        base[building] = lp
        for scale in SENSITIVITY_SCALES:
            scaled[scale][building] = sd.solve_microgrids(load, per_kwp, price, roof, economics,
                                                          workroot/f'B{building:02d}_capex{scale:.2f}', capex_scale=scale,
                                                          tariff=tariff)
        # The demand charge is not verified against the bills (audit/tariff_bill_validation.json):
        # the same LP without it shows how much of the BESS/PV decision depends on it.
        no_demand = sd.solve_microgrids(load, per_kwp, price, roof, economics, workroot/f'B{building:02d}_nodemand',
                                        tariff={**tariff, 'demand_charge': {m: 0.0 for m in range(1, 13)}})
        n_modules, kwp = sd.round_pv(lp['pv_kwp'], module, roof)
        if n_modules:
            solar = sd.pv_ac_w_per_kw(weather_full, n_modules, module).to_numpy(float)
        else:
            solar = np.zeros(len(weather_full))
        frame = pd.read_csv(out/f'Building_{building}.csv')
        frame['solar_generation'] = solar
        frame.to_csv(out/f'Building_{building}.csv', index=False, float_format='%.6f')
        pv_2023 = solar[:8760]*kwp/1000.0
        block_peaks = {str(m): float(max(0.0, (load - pv_2023)[(index_2023.month == m) & (peak_flag == 1)].max()))
                       for m in range(1, 13)}
        rule = design.get('bess_rule')
        rule_size = None
        if rule:
            rule_size = sd.bess_design_rule(max(block_peaks.values()), len(PEAK_BLOCK_HOURS), economics, rule)
            bess = rule_size['capacity_kwh']
        else:
            bess = sd.round_bess(lp['bess_kwh'])
        check = sd.prosumpy_check(load, pv_2023, bess, economics)
        config = schema['buildings'][f'Building_{building}']
        config['pv'] = {'type': 'citylearn.energy_model.PV', 'autosize': False, 'attributes': {'nominal_power': kwp}}
        bess_cfg = economics['bess']
        if bess > 0:
            config['electrical_storage'] = {'type': 'citylearn.energy_model.Battery', 'autosize': False, 'attributes': {
                'capacity': bess, 'nominal_power': round(bess/float(bess_cfg['max_discharge_time_h']['value']), 3),
                'efficiency': float(bess_cfg['charge_efficiency']['value'])*float(bess_cfg['discharge_efficiency']['value']),
                'depth_of_discharge': 1.0 - float(bess_cfg['minimum_soc_fraction']['value']),
                'initial_soc': float(bess_cfg['minimum_soc_fraction']['value']), 'loss_coefficient': 0.0,
                'capacity_loss_coefficient': 1e-5}}
            if rule:
                config['electrical_storage']['attributes'].update(sd.bess_rule_curves(
                    config['electrical_storage']['attributes']['efficiency'], rule))
        else:
            config.pop('electrical_storage', None)
        annual_load = float(load.sum())
        rows[str(building)] = {
            'building_type': registry['buildings'][building]['canonical_type'],
            'termination_condition': lp['termination_condition'], 'solve_seconds': lp['solve_seconds'],
            'price_usd_per_kwh': price,
            'price_source': {'source': 'Osinergmin sheets, sector IQUITOS, energy charge of the building tariff per '
                                       'month (without IGV), World Bank PEN/USD',
                             'tariff_by_month_2023': {f'{m:02d}': signals[building]['tariff_by_month'][(DESIGN_YEAR, m)]
                                                      for m in range(1, 13)}},
            'demand_charge_usd_kw_month_2023': {str(m): tariff['demand_charge'][m] for m in range(1, 13)},
            'roof_bound_kwp': roof, 'usable_area_fraction': usable,
            'roof_bound_basis': f'Area_Techada_m2 x {usable} (user decision: covered area used as available roof)',
            'roof_bound_binding': lp['pv_kwp'] >= roof - 1e-3,
            'pv_kwp_lp': lp['pv_kwp'], 'pv_modules': n_modules, 'pv_kwp': kwp, 'module_kwp': module_kwp,
            'bess_kwh_lp': lp['bess_kwh'], 'bess_kwh': bess,
            'bess_kw': round(bess/float(bess_cfg['max_discharge_time_h']['value']), 3) if bess else 0.0,
            'annual_load_kwh_2023': annual_load, 'peak_load_kw_2023': float(load.max()),
            'annual_pv_kwh_2023': float(pv_2023.sum()),
            'pv_to_load_ratio_2023': float(pv_2023.sum())/annual_load if annual_load else None,
            'lp': {k: v for k, v in lp.items() if k not in ('solver', 'battery_net_out_kwh_series')},
            'demand_charge_status': design['tariff_validation']['capacity_component']['status'],
            'without_demand_charge': {k: no_demand.get(k) for k in ('termination_condition', 'pv_kwp', 'bess_kwh',
                                                                    'npc_usd')},
            'no_bess_monthly_peak_block_max_kw': block_peaks,
            'prosumpy': check}
        if rule_size:
            rows[str(building)]['bess_rule'] = rule_size
        log(f'B{building:02d}: PV {kwp:.1f} kWp (bound {roof:.0f}), BESS {bess:.1f} kWh, '
            f'PV/load {rows[str(building)]["pv_to_load_ratio_2023"]:.2f}')
    _write_json(out/'schema.json', schema)
    threshold = float(economics['sensitivity']['material_change_threshold_relative'])
    report = {'solver': os.environ.get('MICROGRIDS_SOLVER', sd.DEFAULT_SOLVER), 'design_year': DESIGN_YEAR,
              'bess_sizing': design['bess_rule']['rule'] if design.get('bess_rule') else 'microgrids_lp',
              'module': {k: module[k] for k in ('Vmpo', 'Impo', 'Area')}, 'reference_array_modules': reference_modules,
              'economics': economics, 'buildings': rows,
              'sensitivity': {'capex_relative_change': [round(s - 1.0, 2) for s in SENSITIVITY_SCALES],
                              **sd.sensitivity(base, scaled, threshold)},
              'formulation': 'external/MicroGrids LP (Model_Creation + Constraints) with the export term '
                             '(CHANGES.md#exportacion-red) and the hourly price + monthly peak-block demand '
                             'charge (CHANGES.md#tarifa-horaria-demanda)',
              'tariff': 'Osinergmin pliegos, sector IQUITOS, energy charge per hour and peak-block (18:00-23:00) '
                        'demand charge per month, without IGV; export credited at the energy charge'}
    _write_json(audit_dir/'der_sizing_microgrids.json', report)
    shutil.rmtree(workroot, ignore_errors=True)
    return report


def clean_orphans(out: Path, audit_dir: Path) -> None:
    """Original step: files not referenced by schema.json leave the dataset."""
    import clean_dataset_orphans as orphans
    _write_json(audit_dir/'orphaned_dataset_files_manifest.json',
                orphans.clean_dataset_orphans(out, audit_dir/'orphaned_dataset_files'))


def balance_checks(out: Path, targets):
    """Hourly closure of every billed component, with CityLearn's own COP and the machine baseline."""
    import distill_building_loads as dl
    schema = dl.load_schema(out)
    t_out = dl.load_weather(out)
    index = pd.date_range('2023-01-01', periods=len(t_out), freq='h', tz=TZ)
    stamps = [stamp.isoformat() for stamp in index]
    hourly = {b: list(zip(stamps, as_billed_load(out, b, schema, t_out)['total'].tolist())) for b in BUILDINGS}
    return cn.check_monthly_balance(hourly, targets)


def citylearn_balance(campaign_root: Path, targets, log):
    """No-control CityLearn simulation of the train split against the bills.

    No-control: battery and EV actions 0, washing machines started at the first hour
    of their window (the as-billed behaviour). Compared quantity per building and
    month: cooling + heating + DHW + non-shiftable + washing-machine electricity,
    i.e. net consumption without PV, BESS and EV.
    """
    from citylearn.citylearn import CityLearnEnv
    from uc3m.adapters.citylearn import fresh_observations as fo
    from uc3m.application.dataset import splits as sp
    dataset = campaign_root/'dataset'
    scratch = campaign_root/'audit'/'_balance_split'
    if scratch.exists():
        shutil.rmtree(scratch)
    sizes = fo.design_device_sizes(dataset)
    sp.materialize_splits(dataset, scratch, campaign_id='balance_check', fixed_devices=sizes)
    env = CityLearnEnv(str(scratch/'train_2023'/'schema.json'))
    env.reset()
    names = env.action_names
    actions = [[1.0 if 'washing_machine' in n else 0.0 for n in agent] for agent in names]
    started = time.perf_counter()
    done = False
    while not done:
        result = env.step(actions)
        done = bool(result[2]) if len(result) < 5 else bool(result[2] or result[3])
    elapsed = time.perf_counter() - started
    index = pd.date_range('2023-01-01', periods=8760, freq='h', tz=TZ)
    by_target = {(t.building_id, t.month): t for t in targets if t.year == 2023}
    report = {'split': 'train_2023', 'tolerance_relative': CITYLEARN_BALANCE_RTOL, 'simulation_seconds': round(elapsed, 1),
              'controller': 'no-control: storage/EV actions 0, washing machines start at window start',
              'compared_quantity': 'cooling+heating+dhw+non_shiftable+washing_machines electricity (no PV/BESS/EV)',
              'unsimulated_hours_note': 'CityLearn records time_steps - 1 transitions; the last train hour '
                                        '(2023-12-31 23:00) is not simulated, so December is compared on the '
                                        'simulated hours with the bill pro-rated by hours',
              'buildings': {}, 'peak_check': {}}
    for building in env.buildings:
        b = int(building.name.split('_')[1])
        series = sum(np.asarray(getattr(building, name), dtype=float)[:8760] for name in (
            'cooling_electricity_consumption', 'heating_electricity_consumption', 'dhw_electricity_consumption',
            'non_shiftable_load_electricity_consumption', 'washing_machines_electricity_consumption'))
        simulated_hours = len(series)  # CityLearn steps T-1 transitions: the final hour is not simulated
        months, peaks = [], []
        for month in range(1, 13):
            mask = (index.month == month)[:simulated_hours]
            simulated = float(series[mask].sum())
            target = by_target[(b, month)]
            hours = int(mask.sum())
            expected = target.energy_kwh*hours/int((index.month == month).sum())
            error = (simulated - expected)/expected
            months.append({'month': month, 'bill_kwh': target.energy_kwh, 'simulated_hours': hours,
                           'bill_kwh_for_simulated_hours': expected, 'citylearn_kwh': simulated,
                           'relative_error': error, 'relative_error_vs_full_bill': (simulated - target.energy_kwh)/target.energy_kwh,
                           'provenance': target.provenance})
            if target.load_factor and target.load_factor > 0 and target.provenance == 'measured':
                implied = target.energy_kwh/(target.load_factor*int(mask.sum()))
                peaks.append({'month': month, 'load_factor': target.load_factor, 'bill_implied_pmax_kw': implied,
                              'hourly_peak_kw': float(series[mask].max()),
                              'ratio_hourly_to_implied': float(series[mask].max())/implied})
        worst = max(abs(m['relative_error']) for m in months)
        report['buildings'][str(b)] = {'months': months, 'max_relative_error': worst,
                                       'passed': worst <= CITYLEARN_BALANCE_RTOL}
        ratios = [p['ratio_hourly_to_implied'] for p in peaks]
        report['peak_check'][str(b)] = {'months': peaks, 'ratio_min': min(ratios) if ratios else None,
                                        'ratio_max': max(ratios) if ratios else None}
    close = getattr(env, 'close', None)
    if callable(close):
        close()
    shutil.rmtree(scratch, ignore_errors=True)
    log(f'CityLearn no-control balance: {sum(r["passed"] for r in report["buildings"].values())}/17 within '
        f'{CITYLEARN_BALANCE_RTOL:.1%} ({elapsed:.0f} s)')
    return report


def citylearn_peak_shaving(campaign_root: Path, der, log, design_rule=None):
    """CityLearn train-split check of every sized BESS: no control vs a peak-shaving rule.

    Rule: in the peak block (18:00-23:00) discharge what the no-control run imports above
    the monthly target (the LP's peak-block maximum, or the no-control maximum minus
    shaved_kw under a declared design rule); from 00:00 to 06:00 recharge evenly up to the
    state-of-charge ceiling; otherwise idle. CityLearn scales actions by nominal power.
    The rule knows the no-control series in advance: this checks what the battery can do,
    it is not a usable control policy. Recorded: monthly peak-block maximum import with
    and without the battery.
    """
    sized = {b: row for b, row in der['buildings'].items() if row['bess_kwh'] > 0}
    if not sized:
        log('peak-shaving check: no BESS sized by the LP in any building (nothing to verify)')
        return {'status': 'no_bess_sized', 'buildings': {}}
    from citylearn.citylearn import CityLearnEnv
    from uc3m.adapters.citylearn import fresh_observations as fo
    from uc3m.application.dataset import splits as sp
    dataset = campaign_root/'dataset'
    scratch = campaign_root/'audit'/'_peak_split'
    if scratch.exists():
        shutil.rmtree(scratch)
    sp.materialize_splits(dataset, scratch, campaign_id='peak_check', fixed_devices=fo.design_device_sizes(dataset))
    index = pd.date_range(f'{DESIGN_YEAR}-01-01', periods=8760, freq='h')
    results, uncontrolled = {}, {}
    ceiling = float(design_rule['soc_ceiling']['value']) if design_rule else 1.0

    def month_target(key, month):
        block = (index[:len(uncontrolled[key])].month == month) & np.isin(index[:len(uncontrolled[key])].hour, PEAK_BLOCK_HOURS)
        if 'bess_rule' in sized[key]:
            return max(0.0, float(uncontrolled[key][block].max()) - sized[key]['bess_rule']['shaved_kw'])
        targets = sized[key]['lp']['monthly_peak_block_max_kw']
        return targets[str(month)] if str(month) in targets else targets[month]

    for mode in ('no_control', 'rule'):
        env = CityLearnEnv(str(scratch/'train_2023'/'schema.json'))
        env.reset()
        done = False
        while not done:
            t = env.time_step
            actions = []
            for building, names in zip(env.buildings, env.action_names):
                row = []
                for name in names:
                    value = 1.0 if 'washing_machine' in name else 0.0
                    key = building.name.split('_')[1]
                    if name == 'electrical_storage' and mode == 'rule' and key in sized:
                        capacity, nominal = sized[key]['bess_kwh'], sized[key]['bess_kw']
                        hour, month = index[t].hour, index[t].month
                        if hour in PEAK_BLOCK_HOURS:
                            value = -min(1.0, max(0.0, uncontrolled[key][t] - month_target(key, month))/nominal)
                        elif hour < 6:
                            storage = building.electrical_storage
                            soc = float(storage.soc[t - 1]) if t else float(storage.soc[0])
                            needed = max(0.0, ceiling - soc)*capacity/float(storage.round_trip_efficiency)
                            value = min(1.0, needed/(6 - hour)/nominal)
                    row.append(value)
                actions.append(row)
            result = env.step(actions)
            done = bool(result[2]) if len(result) < 5 else bool(result[2] or result[3])
        for building in env.buildings:
            key = building.name.split('_')[1]
            if key not in sized:
                continue
            net = np.asarray(building.net_electricity_consumption, dtype=float)
            if mode == 'no_control':
                uncontrolled[key] = net
            hours = index[:len(net)]
            peaks = {str(m): float(net[(hours.month == m) & np.isin(hours.hour, PEAK_BLOCK_HOURS)].max())
                     for m in range(1, 13)}
            results.setdefault(key, {})[mode] = peaks
    shutil.rmtree(scratch, ignore_errors=True)
    for key, row in results.items():
        row['reduction_kw'] = {m: row['no_control'][m] - row['rule'][m] for m in row['no_control']}
        if 'bess_rule' in sized[key]:
            row['shaved_kw'] = sized[key]['bess_rule']['shaved_kw']
            row['delivered_fraction_worst_month'] = min(row['reduction_kw'].values())/row['shaved_kw']
    log(f'peak-shaving check on {len(results)} BESS buildings')
    return {'status': 'checked', 'rule': citylearn_peak_shaving.__doc__.split('\n\n')[1].strip(), 'buildings': results}


def _q(name, value, origin, *, scope='district', unit='', source='', reason='', assumption=None, **extra):
    entry = {'name': name, 'scope': scope, 'value': value, 'unit': unit, 'origin': origin,
             'assumption': bool(assumption if assumption is not None else origin == 'assumption')}
    if source:
        entry['source'] = source
    if reason:
        entry['reason'] = reason
    entry.update(extra)
    return entry


def _from_config(name, entry, scope='district', unit=''):
    origin = entry.get('origin') or {'repository_example': 'cited', 'design_rule': 'design_rule',
                                     'assumption_pending_user_verification': 'assumption'}.get(entry.get('status'), 'assumption')
    if origin == 'cited' and entry.get('status') == 'repository_example':
        reason = 'upstream MicroGrids example value, not Iquitos data; to be verified by the user'
        return _q(name, entry['value'], 'assumption', scope=scope, unit=unit, source=entry.get('source', ''),
                  reason=reason, status=entry.get('status'))
    return _q(name, entry.get('value'), origin, scope=scope, unit=unit, source=entry.get('source', ''),
              reason=entry.get('reason', '') or ('see ' + entry.get('reference_to_verify', 'config')),
              assumption=entry.get('assumption'), status=entry.get('status'))


def provenance_quantities(design, targets, campaign_root):
    registry, economics = design['registry'], design['economics']
    q = []
    measured = sum(t.provenance == 'measured' for t in targets)
    q.append(_q('monthly_energy_targets', {'measured': measured, 'modeled': len(targets) - measured}, 'measured',
                unit='kWh/month', source='raw/buildingcsv/B_XX.csv and raw/thesis/resultados_preliminares.xlsx',
                method='measured bills; missing months modeled without crossing years (quality_flags.csv)'))
    q.append(_q('tou_scaling_rule', 'scale TOU blocks to the printed total when they differ by >2 % '
                '(ratio 0.5..2), else keep registers', 'user_decision', reason='owner decision 2026-11-01 (d)'))
    q.append(_q('weather', 'NASA POWER hourly', 'model', source='raw/weather/nasa_power_<year>_utc.json',
                unit='reanalysis', reason='reanalysis, not a local station'))
    q.append(_q('pen_per_usd', 'World Bank PA.NUS.FCRF', 'measured', source='raw/fx/worldbank_pa_nus_fcrf_per.json'))
    for entry in design['tariff_sources']:
        q.append(_q('tariff_sheet', entry['available_at'], 'cited', source=entry['source_uri'],
                    reason=entry['notes'], valid_from=entry['available_at'].split()[-1],
                    obtained_at=entry['obtained_at'], raw_file=entry['path']))
    searched = design['tariff_validation']['definitions_search_in_sheets']
    q.append(_q('tariff_peak_block_hours', list(PEAK_BLOCK_HOURS), 'assumption',
                reason='HP block 18:00-23:00, the block of the bills TOU registers; not defined in any of the '
                       f'{len(design["tariff_sources"])} downloaded Osinergmin sheets (keyword search: '
                       f'{searched["matches"]}); source in the tariff-options norm still to be obtained',
                searched_keywords=searched['keywords']))
    q.append(_q('tariff_present_in_peak_rule', '(E_peak/peak hours)/Pmax >= 0.5', 'assumption',
                reason='qualification of MT3/MT4/BT3/BT4 users; not defined in the downloaded sheets (only the '
                       'charge labels "presentes en punta" appear); Osinergmin tariff-options norm, to be verified'))
    capacity = design['tariff_validation']['capacity_component']
    q.append(_q('demand_charge_validation', capacity['status'], 'derived', source='audit/tariff_bill_validation.json',
                reason=capacity['note'] or 'per-building capacity coefficient consistent with the sheet x IGV'))
    q.append(_q('tariff_bill_exclusions', len(design['tariff_validation']['excluded']), 'derived',
                source='audit/tariff_bill_validation.json',
                reason='months flagged partial_month_suspect/printed_total_implausible or with recomputed/billed '
                       'outside 0.2..5 are excluded from the validation statistics, each with its reason'))
    q.append(_q('tariff_without_igv', True, 'design_rule',
                reason='CityLearn prices and MicroGrids costs use the sheet values without IGV (18 %)'))
    q.append(_q('b01_tariff', B01_TARIFF_ASSUMPTION, 'assumption', scope='B01',
                reason='no B01 bill; label of the project-generated B_01.csv'))
    q.append(_q('demand_charge_rule', 'monthly max grid import in 18:00-23:00 x (HP generation + HP distribution) '
                'for MT2/BT2 or (present-in-peak generation + distribution) for MT3/MT4/BT3/BT4', 'design_rule',
                reason='user decision: block tariff + demand; the multi-month distribution averaging '
                       'and off-peak qualification are not modeled'))
    summary = design['tariff_validation']['summary']
    q.append(_q('tariff_bill_validation', {b: round(r['median_abs_error_with_igv'], 4) for b, r in summary.items()},
                'derived', source='audit/tariff_bill_validation.json',
                reason='median absolute error of the recomputed bill (with IGV) vs TotalFacturado per building'))
    q.append(_q('pv_usable_area_rule', economics['pv']['usable_area_fraction']['value'], 'user_decision',
                source=economics['pv']['usable_area_fraction']['source'],
                reason='área techada usada como techo disponible (Area_Techada_m2 x 0.63, base generator rule)'))
    carbon = dict(design['carbon'])
    q.append(_q('carbon_intensity', carbon['value'], 'model', unit='kgCO2/kWh', source=_rel(EMISSIONS_PATH),
                reason=carbon['reason'], assumption=True, formula=carbon['formula'], inputs=carbon['inputs']))
    import yaml
    emissions = yaml.safe_load(EMISSIONS_PATH.read_text(encoding='utf-8'))
    for key in ('fuel', 'fuel_co2_emission_factor_kg_per_tj', 'net_thermal_efficiency'):
        q.append(_from_config(key, emissions[key]))
    q.append(_q('chilled_water_target_c', registry['chilled_water_target_c']['value'], 'assumption', unit='C',
                reason=registry['chilled_water_target_c']['reason']))
    q.append(_q('dhw_heater_efficiency', DHW_HEATER_EFFICIENCY, 'assumption',
                reason='distill_building_loads.COP_ACS_DEF; written as ElectricHeater efficiency for B05/B11/B12'))
    for b, row in registry['buildings'].items():
        scope = f'B{int(b):02d}'
        q.append(_q('building_type', row['canonical_type'], 'design_rule', scope=scope, reason=row['justification'],
                    source=_rel(REGISTRY_PATH)))
        q.append(_q('schedule', row['schedule'], 'assumption', scope=scope,
                    reason=registry['schedules'][row['schedule']]['reason']))
        cop = row['cooling_cop_design']
        chilled = registry['chilled_water_target_c']['value']
        eta = round(cop['value']*(registry['reference_outdoor_temperature_c'] - chilled)/(chilled + 273.15), 6)
        q.append(_q('cooling_efficiency', eta, 'model', scope=scope, assumption=True,
                    reason=f'eta = COP_design {cop["value"]} x (28 - 8.5)/(8.5 + 273.15); ' + cop['reason'],
                    formula='CityLearn HeatPump cop = eta (T_target+273.15)/(T_out - T_target)'))
        for key in ('controlled_machine_cycle_kwh', 'generator_cooling_peak_kw', 'generator_non_shiftable_base_kw'):
            q.append(_q(key, row[key]['value'], 'assumption', scope=scope, reason=row[key]['reason']))
    for group, names in (('pv', ('capex_usd_per_wp', 'om_fraction_of_capex_per_year', 'lifetime_years')),
                         ('bess', ('capex_usd_per_wh', 'om_fraction_of_capex_per_year', 'replacement_year',
                                   'charge_efficiency', 'discharge_efficiency', 'minimum_soc_fraction',
                                   'max_charge_time_h', 'max_discharge_time_h')),
                         ('project', ('discount_rate', 'project_years', 'fraction_funded_by_loan'))):
        for name in names:
            q.append(_from_config(f'{group}_{name}', economics[group][name]))
    rule = design.get('bess_rule')
    if rule:
        q.append(_q('bess_design_rule', rule['rule'], 'user_decision', source=rule['source'],
                    reason=' '.join(rule['formula'].split())))
        q.append(_from_config('bess_shave_fraction_of_peak_block', rule['shave_fraction_of_peak_block']))
    export = economics['export']
    q.append(_q('export_credit_rule', {'price_ratio_to_purchase': export['price_ratio_to_purchase'],
                                       'curtailment_allowed': export['curtailment_allowed']},
                'user_decision', source=export['source'], reason=' '.join(export['reason'].split())))
    q.append(_q('export_settlement_citylearn', 'net_billing_at_hourly_purchase_price', 'user_decision',
                source='schema.json community_market.enabled = false',
                reason='exported energy credited at the building purchase price of each hour (net billing); no such '
                       'tariff scheme exists in Iquitos today; CityLearn keeps cost = net x electricity_pricing '
                       '(citylearn/building.py update_variables) when the community market is disabled; no local '
                       'peer market is simulated because none is documented for Iquitos'))
    q.append(_q('grid_supply_mapping', economics['grid_supply_mapping']['description'], 'design_rule',
                reason='MicroGrids generator stands for the public grid'))
    for b, row in design['der']['buildings'].items():
        scope = f'B{int(b):02d}'
        q.append(_q('pv_kwp', row['pv_kwp'], 'model', scope=scope, unit='kWp', assumption=True,
                    source='audit/der_sizing_microgrids.json',
                    reason='MicroGrids LP optimum on pvlib AC per kWp and the 2023 as-billed load; depends on '
                           'assumed economics; upper bound = covered built area (not a roof survey)'))
        if rule:
            q.append(_q('bess_kwh', row['bess_kwh'], 'design_rule', scope=scope, unit='kWh', assumption=True,
                        source=_rel(BESS_RULE_PATH), reason='declared peak-block shaving rule, not an economic '
                        f'optimum; the LP optimum was {row["bess_kwh_lp"]:.1f} kWh; capability checked in CityLearn '
                        '(audit/bess_peak_shaving_check.json)'))
        else:
            q.append(_q('bess_kwh', row['bess_kwh'], 'model', scope=scope, unit='kWh', assumption=True,
                        source='audit/der_sizing_microgrids.json', reason='MicroGrids LP optimum; verified with prosumpy'))
        q.append(_q('energy_price_usd_per_kwh', row['price_usd_per_kwh'], 'derived', scope=scope,
                    source=row['price_source']['source']))
    import yaml as _yaml
    pilot = _yaml.safe_load(EV_PILOT_PATH.read_text(encoding='utf-8'))['pilot']
    q.append(_q('ev_battery_kwh', pilot['battery_kwh']['value'], 'cited', scope='B01', unit='kWh',
                source=pilot['battery_kwh']['source']))
    q.append(_q('ev_vehicle_count', pilot['vehicle_count']['value'], 'design_rule', scope='B01',
                reason=pilot['vehicle_count']['reason']))
    for key in ('min_current_a', 'max_current_a'):
        q.append(_q(f'ev_charger_{key}', pilot['charger'][key]['value'], 'cited', scope='B01', unit='A',
                    source=pilot['charger'][key]['source']))
    q.append(_q('ev_charger_voltage_v', pilot['charger']['voltage_v']['value'], 'design_rule', scope='B01', unit='V',
                reason=pilot['charger']['voltage_v']['reason'], assumption=True))
    for key, entry in pilot['operation'].items():
        q.append(_q(f'ev_{key}', entry['value'], 'assumption', scope='B01', reason=entry['reason']))
    for key in ('battery_nominal_power_kw', 'battery_efficiency', 'battery_depth_of_discharge'):
        q.append(_q(f'ev_{key}', pilot[key]['value'], 'assumption', scope='B01', reason=pilot[key]['reason']))
    q.append(_q('ev_outside_b01', 0, 'user_decision', reason='Iquitos has no public charging stations and no mass EV fleet'))
    return q


def quality_flags(targets, weather_gaps, bess_method='MicroGrids LP, verified with prosumpy dispatch_max_sc'):
    rows = [{'scope': f'B{t.building_id:02d}', 'period': f'{t.year}-{t.month:02d}', 'variable': 'monthly_energy',
             'status': t.provenance, 'method': t.method, 'fit_scope': t.fit_scope,
             'flags': '|'.join(t.flags), 'inputs': '|'.join(t.inputs)} for t in targets]
    for year, gaps in weather_gaps.items():
        for column, count in gaps.items():
            rows.append({'scope': 'district', 'period': str(year), 'variable': column, 'status': 'interpolated',
                         'method': f'linear, gaps <= {MAX_FILLED_GAP_HOURS} h', 'fit_scope': 'same_year',
                         'flags': f'{count} hours', 'inputs': 'NASA POWER'})
    modeled_layers = [('pv_generation', 'modeled', 'pvlib ModelChain SAPM on observed-year NASA POWER; kWp from the MicroGrids LP'),
                      ('bess_sizing', 'modeled', bess_method),
                      ('ev_sessions', 'modeled', 'B01 pilot only: 2 service motorcycles, overnight depot charging'),
                      ('controlled_machines', 'modeled', 'registry cycle energy, subtracted from the bill'),
                      ('carbon_intensity', 'modeled', 'constant IPCC 2006 gas/diesel oil factor / assumed efficiency'),
                      ('electricity_pricing', 'cited', 'Osinergmin sheets sector IQUITOS, energy charge of each '
                                                       'building tariff (peak = off-peak in Iquitos), no IGV, '
                                                       'World Bank annual PEN/USD'),
                      ('demand_charge', 'cited', 'peak-block (18:00-23:00) capacity charge of the sheet; used by '
                                                 'the MicroGrids sizing, not by CityLearn')]
    rows.extend({'scope': 'district', 'period': '2023-2025', 'variable': name, 'status': status,
                 'method': method, 'fit_scope': 'documented_assumption', 'flags': '', 'inputs': ''}
                for name, status, method in modeled_layers)
    return pd.DataFrame(rows)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--campaign-id', required=True)
    parser.add_argument('--storage-alias', required=True)
    parser.add_argument('--bess-design-rule', action='store_true',
                        help=f'size every BESS with {BESS_RULE_PATH.name} instead of the MicroGrids LP optimum')
    args = parser.parse_args(argv)
    from uc3m.application.training.layout import storage_label
    campaign_root = ROOT/'data/campaigns'/storage_label(args.storage_alias)
    if campaign_root.parent.resolve() != ROOT.resolve()/'data'/'campaigns':
        raise SystemExit('data/campaigns resolves outside the repository; nothing written')
    if campaign_root.exists():
        raise SystemExit(f'{_rel(campaign_root)} already exists; choose a new campaign alias')
    raw_dir, audit_dir = campaign_root/'raw', campaign_root/'audit'
    raw_dir.mkdir(parents=True)
    log = lambda message: print(f'[{datetime.now().strftime("%H:%M:%S")}] {message}', flush=True)  # noqa: E731
    import size_der_microgrids as sd
    design = {'registry': load_registry(), 'economics': sd.load_economics(ECONOMICS_PATH)}
    design_inputs = [REGISTRY_PATH, ECONOMICS_PATH, EV_PILOT_PATH, EMISSIONS_PATH]
    limitations = list(LIMITATIONS)
    bess_parameter = 'MicroGrids LP with hourly tariff and peak-block demand charge; prosumpy and CityLearn peak-shaving checks'
    bess_method = 'MicroGrids LP, verified with prosumpy dispatch_max_sc'
    if args.bess_design_rule:
        import yaml
        design['bess_rule'] = yaml.safe_load(BESS_RULE_PATH.read_text(encoding='utf-8'))
        design_inputs.append(BESS_RULE_PATH)
        fraction = design['bess_rule']['shave_fraction_of_peak_block']['value']
        bess_parameter = (f'declared rule {design["bess_rule"]["rule"]}: shave {fraction} of each building peak-block '
                          'import; prosumpy and CityLearn peak-shaving checks')
        bess_method = f'declared rule {design["bess_rule"]["rule"]} ({fraction} of the peak block), not an LP optimum'
        limitations = [text.replace('PV and BESS are a declared design scenario sized by the MicroGrids LP',
                                    'PV is a declared design scenario sized by the MicroGrids LP') for text in limitations]
        limitations.append(f'BESS replaces the MicroGrids optimum with a declared design rule ({fraction} of each '
                           'building peak-block import, owner decision 2026-11-02): it is a scenario, not an economic '
                           'optimum and larger than what the LP chose. The percentage and the formula are project '
                           'design choices, not taken from the literature. Battery curves are fixed at the midpoints '
                           'of the CityLearn default draw, not a measured product.')

    entries = stage_billing(raw_dir)
    weather, weather_entries, weather_gaps = stage_weather(raw_dir)
    fx, fx_entry = stage_exchange_rate(raw_dir)
    sheets, tariff_entries = stage_tariffs(raw_dir)
    design['sheets'] = sheets
    design['tariff_sources'] = tariff_entries
    sources = pv.audit_raw_sources(entries + weather_entries + [fx_entry] + tariff_entries, root=ROOT)
    provenance = {**sources.as_dict(), 'campaign_id': args.campaign_id, 'billing_currency': BILLING_CURRENCY,
                  'dataset_currency': 'USD', 'pen_per_usd': fx, 'time_zone': TZ,
                  'design_inputs': [_rel(p) for p in design_inputs],
                  'excluded_inputs': ['CityLearn/data/datasets/citylearn_iquitos_2023_2025', 'outputs/', '.cache/weather'],
                  'limitations': limitations}
    _write_json(campaign_root/'provenance.json', provenance)
    log(f'{len(sources.sources)} raw sources audited')

    measured, targets = monthly_targets(raw_dir, design['registry'])
    tariffs = read_tariffs(raw_dir)
    import osinergmin_pliegos as op
    details = bill_details(raw_dir)
    full_index = pd.date_range('2023-01-01', periods=26304, freq='h', tz=TZ)
    design['tariff_signals'] = tariff_signals(full_index, sheets, details, tariffs, fx)
    coverage = {f'{y}-{m:02d}': op.sheet_for_month(sheets, y, m).isoformat() for y in YEARS for m in range(1, 13)}
    validation = tariff_bill_validation(measured, details, sheets, raw_dir)
    validation['sheet_in_force_on_day_1'] = coverage
    _write_json(audit_dir/'tariff_bill_validation.json', validation)
    busbar_report = tc.tariff_crosscheck_audit(BUSBAR_CSV, sheets)
    _write_json(audit_dir/'tariff_crosscheck.json', busbar_report)
    design['tariff_validation'] = validation
    log(f'{len(sheets)} Osinergmin sheets; {len(validation["rows"])} bills recomputed')
    generator_hash = hash_files(ROOT, [ROOT/'tools/dataset'/name for name in (
        'build_fresh_campaign_dataset.py', 'generate_iquitos_dataset.py', 'distill_building_loads.py',
        'buildingcsv_inputs.py', 'fix_solar_pvlib.py', 'dimension_ev_chargers.py', 'sync_controlled_machines.py',
        'fix_schema_cooling.py', 'size_der_microgrids.py', 'osinergmin_pliegos.py')]
        + [ROOT/'uc3m/application/dataset/construction.py']
        + design_inputs
        + [MICROGRIDS/name for name in ('Model_Creation.py', 'Constraints.py', 'Initialize.py', 'Model_Resolution.py')],
        normalize_newlines=True)
    config = cn.DatasetBuildConfig(campaign_id=args.campaign_id, years=YEARS, buildings=BUILDINGS,
                                   generation_seed=0, currency='USD', time_zone=TZ, parameters={
                                       'seed_policy': 'fixed per building id in the generators',
                                       'pv_capacity': 'MicroGrids LP (export credited, no curtailment) on pvlib '
                                                      'SAPM AC per kWp, bound = covered built area x 0.63',
                                       'bess': bess_parameter,
                                       'ev': 'B01 pilot only (configs/dataset/ev_pilot.yaml)',
                                       'carbon': 'constant (configs/dataset/grid_emissions.yaml)',
                                       'tou_rule': 'scale to printed total (0.5..2), else keep registers',
                                       'weather': 'NASA POWER hourly UTC->America/Lima, observed years',
                                       'pricing': 'Osinergmin sheets sector IQUITOS, energy charge of each '
                                                  'building tariff per month, no IGV, PEN->USD (World Bank annual)',
                                       'peak_to_offpeak_ratio': PEAK_TO_OFFPEAK_RATIO_ASSUMPTION})
    manifest = cn.build_dataset(sources, config, campaign_root/'dataset', project_root=ROOT,
                                generator=make_generator(weather, measured, targets, tariffs, fx,
                                                         raw_dir, audit_dir, log, design),
                                targets=targets, generator_hash=generator_hash,
                                balance=balance_checks, limitations=limitations)
    quality_flags(targets, weather_gaps, bess_method).to_csv(campaign_root/'quality_flags.csv', index=False)
    failed = [c for c in manifest.balance_checks if not c['passed']]
    simulated = citylearn_balance(campaign_root, targets, log)
    _write_json(audit_dir/'citylearn_balance.json', simulated)
    shaving = citylearn_peak_shaving(campaign_root, design['der'], log, design.get('bess_rule'))
    _write_json(audit_dir/'bess_peak_shaving_check.json', shaving)
    provenance['quantities'] = provenance_quantities(design, targets, campaign_root)
    _write_json(campaign_root/'provenance.json', provenance)
    schema = json.loads((campaign_root/'dataset'/'schema.json').read_text(encoding='utf-8'))
    gates = {'hourly_balance': not failed,
             'citylearn_balance': all(r['passed'] for r in simulated['buildings'].values()),
             'microgrids_optimal': all(r['termination_condition'] == 'optimal'
                                       for r in design['der']['buildings'].values()),
             'ev_pilot_only': all(not b.get('chargers') for k, b in schema['buildings'].items() if k != 'Building_1')
             and len(schema['buildings']['Building_1'].get('chargers', {})) == 2,
             'tariff_history_complete': len(coverage) == 36,
             'tariff_crosscheck': tc.tariff_crosscheck_gate(busbar_report),
             'bess_verified': shaving['status'] in ('no_bess_sized', 'checked')}
    if args.bess_design_rule:
        gates['bess_rule_shaves_peak'] = (
            shaving['status'] == 'checked' and len(shaving['buildings']) == len(BUILDINGS)
            and all(row['delivered_fraction_worst_month'] >= BESS_RULE_MIN_DELIVERED
                    for row in shaving['buildings'].values()))
    acceptance = {'campaign_id': args.campaign_id, 'dataset_hash': manifest.dataset_hash,
                  'source_manifest_hash': sources.manifest_hash, 'balance_checks': len(manifest.balance_checks),
                  'balance_failures': failed[:50], 'balance_failure_count': len(failed),
                  'modeled_monthly_targets': sum(t.provenance == 'modeled' for t in targets),
                  'measured_monthly_targets': sum(t.provenance == 'measured' for t in targets),
                  'gates': gates, 'dataset_verified': all(gates.values()), 'limitations': limitations,
                  'checked_at': datetime.now(timezone.utc).isoformat()}
    _write_json(campaign_root/'dataset_acceptance.json', acceptance)
    log(f'dataset_hash={manifest.dataset_hash} gates={gates} dataset_verified={acceptance["dataset_verified"]}')
    return 0 if acceptance['dataset_verified'] else 3


LIMITATIONS = [
    'B01: measured monthly energy only for 2024-01..2025-10 (study workbook, sheet 8.ELOR) with the peak split '
    'from same-year Office peers; 2025-11/12 are modeled from B01 2025 months. B_01.csv is project-generated '
    'and excluded.',
    'B01 2023 (training year) is a declared backcast: 2024 measured monthly profile x 0.98 (original method). '
    'It uses validation-year information; its months carry cross_year_leakage_declared and a sensitivity '
    'excluding modeled buildings is required.',
    'Missing months are modeled within the same year; hourly shapes are generated from registry schedules, not measured.',
    'TOU registers differing from the printed total by >2 % are scaled to the printed total (owner rule); printed '
    'totals outside 0.5..2 x the registers are treated as transcription errors and the registers kept (flagged).',
    'Weather is NASA POWER reanalysis for one grid point, not a local station.',
    'PEN/USD uses the annual official average (World Bank); monthly variation is not represented.',
    'Prices are the official Osinergmin sheets (sector IQUITOS, without IGV); recomputed bills differ from '
    'TotalFacturado (audit/tariff_bill_validation.json) because public lighting, rural-electrification '
    'contributions and multi-month demand averaging are not reproducible from a bill.',
    'CityLearn has no demand charge: the peak-block demand charge only enters the MicroGrids sizing.',
    'Carbon intensity is one constant: IPCC 2006 gas/diesel oil factor over an assumed 0.40 plant efficiency.',
    'PV and BESS are a declared design scenario sized by the MicroGrids LP with assumed economics and the '
    'official tariff; export is credited at the energy charge (net billing, not available in Iquitos today) and '
    'nothing is curtailed; the PV bound is the covered built area x 0.63 (user decision), not a roof survey.',
    'EV: only a declared 2-motorcycle pilot at B01; all other buildings have no EV and no charger.',
    'Controlled machine energy, cooling design COP and schedules are assumptions carried from the earlier tools.',
]


if __name__ == '__main__':
    raise SystemExit(main())
