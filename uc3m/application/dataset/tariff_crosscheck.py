"""Cross-check of the busbar PDFs against the end-user tariff sheets of the same dates.

The ratio band is a project criterion derived from the observed values, not a
regulation. Coverage is declared; a date without a document is never filled from
another date.
"""
from __future__ import annotations

import csv
import hashlib
from datetime import date
from pathlib import Path
from typing import Mapping

from uc3m.domain.tariffs import BusbarPrice, BusbarSheet

RATIO_BAND = (1.005, 1.030)
CSV_COLUMNS = ('valid_from', 'resolutions', 'barra_power', 'barra_peak', 'barra_offpeak', 'efectivo_power',
               'efectivo_peak', 'efectivo_offpeak', 'sheet_mt3_energy', 'ratio_mt3_efectivo')


def _energy(charges: Mapping[str, float]):
    return (charges.get('energy_peak_ctm_kwh', charges.get('energy_ctm_kwh')),
            charges.get('energy_offpeak_ctm_kwh', charges.get('energy_ctm_kwh')))


def crosscheck(sheets: Mapping[date, BusbarSheet], charges: Mapping[date, Mapping[str, Mapping[str, float]]],
               *, tariff: str = 'MT3') -> dict:
    rows, failures = [], []

    def fail(day, reason):
        failures.append({'valid_from': day.isoformat(), 'reason': reason})
    for day in sorted(set(sheets) & set(charges)):
        sheet = sheets[day]
        peak, offpeak = _energy(charges[day].get(tariff, {}))
        if peak is None or offpeak is None:
            fail(day, 'missing_energy_charge')
            continue
        if not (sheet.barra.is_flat and sheet.efectivo.is_flat):
            fail(day, 'non_flat_busbar')
        if peak != offpeak:
            fail(day, 'non_flat_sheet')
        ratio = peak/sheet.efectivo.energy_peak_ctm_kwh
        if not RATIO_BAND[0] <= ratio <= RATIO_BAND[1]:
            fail(day, 'ratio_out_of_band')
        rows.append({'valid_from': day.isoformat(), 'sheet_energy_ctm_kwh': peak,
                     'efectivo_energy_ctm_kwh': sheet.efectivo.energy_peak_ctm_kwh, 'ratio': ratio})
    return {'tariff': tariff, 'ratio_band': list(RATIO_BAND), 'rows': rows, 'failures': failures,
            'pdf_only': [d.isoformat() for d in sorted(set(sheets) - set(charges))],
            'sheet_only': [d.isoformat() for d in sorted(set(charges) - set(sheets))]}


def sheets_from_csv(path: Path, *, system: str = 'Electro Oriente') -> dict:
    """Busbar sheets from the versioned CSV written by tools/dataset/ingest_osinergmin_pba.py."""
    out = {}
    with open(path, newline='', encoding='utf-8') as handle:
        for row in csv.DictReader(handle):
            day = date.fromisoformat(row['valid_from'])
            out[day] = BusbarSheet(day, system, tuple(filter(None, row['resolutions'].split(';'))),
                                   BusbarPrice(float(row['barra_power']), float(row['barra_peak']),
                                               float(row['barra_offpeak'])),
                                   BusbarPrice(float(row['efectivo_power']), float(row['efectivo_peak']),
                                               float(row['efectivo_offpeak'])))
    return out


def tariff_crosscheck_audit(busbar_csv: Path, charges: Mapping[date, Mapping[str, Mapping[str, float]]],
                            *, tariff: str = 'MT3') -> dict:
    """Report of one dataset build; without the busbar CSV the report fails closed."""
    busbar_csv = Path(busbar_csv)
    if not busbar_csv.is_file():
        return {'tariff': tariff, 'rows': [], 'pdf_only': [], 'sheet_only': [],
                'failures': [{'valid_from': None, 'reason': 'busbar_csv_missing'}]}
    report = crosscheck(sheets_from_csv(busbar_csv), charges, tariff=tariff)
    report['busbar_csv_sha256'] = hashlib.sha256(busbar_csv.read_bytes()).hexdigest()
    return report


def tariff_crosscheck_gate(report: Mapping) -> bool:
    return bool(report['rows']) and not report['failures']
