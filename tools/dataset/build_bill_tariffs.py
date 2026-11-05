"""Official bill rates per building and month (owner decision D02, SPEC-013).

Writes data/tariffs/osinergmin/bill_tariffs.csv from the raw sources of one campaign:
the Osinergmin sheets, each building's bill tariff and the World Bank exchange rate. It
reuses the dataset builder's rules, so the table cannot diverge from what sized the
dataset. Nothing under data/campaigns/ is written and no network is used.
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
for path in (ROOT, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import build_fresh_campaign_dataset as builder  # noqa: E402
import osinergmin_pliegos as op  # noqa: E402

COLUMNS = ('building', 'year', 'month', 'tariff', 'basis', 'energy_usd_kwh', 'demand_usd_kw_month', 'fixed_usd_month')


def exchange_rates(raw_dir: Path) -> dict:
    payload = json.loads((raw_dir/'fx/worldbank_pa_nus_fcrf_per.json').read_text(encoding='utf-8'))
    rates = {int(row['date']): float(row['value']) for row in payload[1] if row['value'] is not None}
    missing = [year for year in builder.YEARS if year not in rates]
    if missing:
        raise ValueError(f'official PEN/USD rate missing for {missing}')
    return rates


def table_rows(raw_dir: Path) -> list:
    sheets = {date.fromisoformat(item.stem.rsplit('_', 1)[1]): op.parse_sheet(item.read_bytes())
              for item in sorted((raw_dir/'osinergmin').glob('pliego_iquitos_*.html'))}
    details, modes, fx = builder.bill_details(raw_dir), builder.read_tariffs(raw_dir), exchange_rates(raw_dir)
    rows = []
    for building in builder.BUILDINGS:
        for year in builder.YEARS:
            for month in range(1, 13):
                tariff, basis = builder.building_tariff(building, year, month, details, modes)
                charges = op.weighted_charges(sheets, year, month, tariff)
                rows.append((building, year, month, tariff, basis,
                             f'{builder.energy_rate_ctm(charges)/100.0/fx[year]:.12f}',
                             f'{builder.demand_rate_pen_kw(charges)/fx[year]:.12f}',
                             f'{charges.get("fixed_pen_month", 0.0)/fx[year]:.12f}'))
    return rows


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument('--raw-dir', type=Path, default=ROOT/'data/campaigns/iquitos_v4/raw')
    parser.add_argument('--output', type=Path, default=ROOT/'data/tariffs/osinergmin/bill_tariffs.csv')
    args = parser.parse_args(argv)
    rows = table_rows(args.raw_dir)
    lines = [','.join(COLUMNS)] + [','.join(str(cell) for cell in row) for row in rows]
    args.output.write_bytes(('\n'.join(lines) + '\n').encode('utf-8'))
    print(f'{len(rows)} rates: {args.output}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
