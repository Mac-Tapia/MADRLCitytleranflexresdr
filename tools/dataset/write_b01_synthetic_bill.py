"""Price the synthetic B01 months with the official Osinergmin sheet and write them as a bill CSV (D-V6-36).

The CSV has the columns of the distributor bills (CityLearn/data/buildingcsv/B_xx.csv), so the builder reads
it like any measured bill, and an audit records the provenance of every month: provenance ``synthetic``.
"""
from __future__ import annotations

from pathlib import Path
from typing import Mapping, Sequence

import osinergmin_pliegos as op

MONTHS_ES = {1: 'ene', 2: 'feb', 3: 'mar', 4: 'abr', 5: 'may', 6: 'jun', 7: 'jul', 8: 'ago', 9: 'set', 10: 'oct',
             11: 'nov', 12: 'dic'}
HEADER = ('Edificio1;Mes;Año;EnergiaActivaHoraPunta;EnergiaActivaFueraPunta;EnergiaReactiva;FactorCarga;'
          'totalEnergiaActiva;TotalFacturado;Tarifa')


def _fmt(value: float, digits: int) -> str:
    return f'{value:.{digits}f}'.replace('.', ',')


def write_synthetic_bill(path: Path, months: Sequence, *, sheets: Mapping, tariff: str,
                         name: str = 'ELECTRO ORIENTE S.A.') -> tuple:
    lines, audit = [HEADER], []
    for m in months:
        bill = op.reconstruct_bill(tariff=tariff, year=m.year, month=m.month, peak_kwh=m.peak_kwh,
                                   offpeak_kwh=m.offpeak_kwh, reactive_kvarh=m.reactive_kvarh,
                                   load_factor=m.load_factor, sheets=sheets)
        lines.append(';'.join((name, MONTHS_ES[m.month], str(m.year), _fmt(m.peak_kwh, 4), _fmt(m.offpeak_kwh, 4),
                               _fmt(m.reactive_kvarh, 4), _fmt(m.load_factor, 6), _fmt(m.energy_kwh, 4),
                               _fmt(bill['total_with_igv_pen'], 2), tariff)))
        audit.append({'year': m.year, 'month': m.month, 'provenance': 'synthetic', 'decision': 'D-V6-36',
                      'energy_provenance': m.energy_provenance, 'energy_inputs': list(m.inputs),
                      'load_factor': m.load_factor, 'load_factor_peers': list(m.load_factor_peers),
                      'max_demand_kw': m.max_demand_kw, 'reactive_kvarh': m.reactive_kvarh, 'tariff': tariff,
                      'billed_pen_with_igv': bill['total_with_igv_pen'], 'bill_components_pen': bill})
    Path(path).write_text('\n'.join(lines) + '\n', encoding='latin-1')
    return Path(path), {'building_id': 1, 'months': audit,
                        'note': 'synthetic bill: B01 has no distributor bill (D-V6-36, P-V6-18, P-V6-19)'}
