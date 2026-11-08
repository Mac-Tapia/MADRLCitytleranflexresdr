"""Ingest the Osinergmin busbar tariff PDFs and cross-check them (SPEC-013).

Writes under data/tariffs/osinergmin/: raw/*.pdf (ignored by Git, public and
registered by hash), busbar_electro_oriente.csv and pba_manifest.json (versioned).
Nothing under data/campaigns/ is written. --offline regenerates the two versioned
files from the registered PDFs and checks their hashes, without network.

Exit code: 0 correct, 2 source refused, 3 cross-check failures.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TOOLS = Path(__file__).resolve().parent
for path in (ROOT, TOOLS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

import osinergmin_pliegos as op  # noqa: E402
import requests  # noqa: E402
import yaml  # noqa: E402

from uc3m.adapters.osinergmin.pba_pdf import (DEFAULT_SYSTEM, PbaFormatError, SourceChangedError,  # noqa: E402
                                              candidate_dates, fetch_pba, parse_pba)
from uc3m.application.dataset.tariff_crosscheck import CSV_COLUMNS, crosscheck, tariff_crosscheck_gate  # noqa: E402

LIMITATIONS = ['La banda de contraste es criterio del proyecto, derivado de lo observado; no es una norma.',
               'La causa del escalón de la razón MT3/efectivo en 2023-11 no está identificada.',
               'Punta igual a fuera de punta en todas las vigencias: no hay señal horaria oficial para este sistema.',
               'Una vigencia sin PDF no hereda valores: consta en sheet_only.',
               'La fila de Electro Oriente se atribuye a Iquitos porque el pliego rotula el sector como aislado y la '
               'razón con el pliego es estable; el PDF no nombra Iquitos.']


def _write_atomic(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    partial = path.with_suffix(path.suffix + '.tmp')
    partial.write_bytes(text.encode('utf-8'))
    os.replace(partial, path)


def _load_charges(sheets_dir: Path) -> dict:
    charges = {}
    for item in sorted(Path(sheets_dir).glob('pliego_iquitos_*.html')):
        charges[date.fromisoformat(item.stem.rsplit('_', 1)[1])] = op.parse_sheet(item.read_bytes())
    return charges


def _load_manifest(root: Path) -> dict:
    target = root/'pba_manifest.json'
    return json.loads(target.read_text(encoding='utf-8')) if target.is_file() else {}


def _check_registered(root: Path, day: str, entry: dict) -> bytes:
    payload = (root/entry['path']).read_bytes()
    if hashlib.sha256(payload).hexdigest() != entry['sha256']:
        raise SourceChangedError(f'{day}: source_changed, {entry["path"]} differs from the manifest')
    return payload


def _download(root: Path, previous: dict, start: date, end: date, charges: dict) -> tuple:
    files, missing = {}, []
    registered = previous.get('files', {})
    session = requests.Session()
    for day in candidate_dates(start, end, charges):
        key = day.isoformat()
        known = registered.get(key)
        entry = fetch_pba(day, root/'raw', session=session, known_sha256=known['sha256'] if known else None)
        if entry is None:
            if known:
                _check_registered(root, key, known)
                files[key] = known  # withdrawn from the site: the registered copy stays
            else:
                missing.append(key)
            continue
        print(f'{key}: {entry["source_uri"]}', flush=True)
        files[key] = known or {'path': f'raw/pba_{key}.pdf', 'source_uri': entry['source_uri'],
                               'sha256': entry['sha256'], 'obtained_at': entry['obtained_at'],
                               'source_type': 'official_tariff_sheet'}
    return files, missing


def _csv_text(sheets: dict, report: dict) -> str:
    by_date = {row['valid_from']: row for row in report['rows']}
    lines = [','.join(CSV_COLUMNS)]
    for day in sorted(sheets):
        sheet, row = sheets[day], by_date.get(day.isoformat())
        cells = [day.isoformat(), ';'.join(sheet.resolutions), sheet.barra.power_pen_kw_month,
                 sheet.barra.energy_peak_ctm_kwh, sheet.barra.energy_offpeak_ctm_kwh, sheet.efectivo.power_pen_kw_month,
                 sheet.efectivo.energy_peak_ctm_kwh, sheet.efectivo.energy_offpeak_ctm_kwh,
                 row['sheet_energy_ctm_kwh'] if row else '', f'{row["ratio"]:.6f}' if row else '']
        lines.append(','.join(str(cell) for cell in cells))
    return '\n'.join(lines) + '\n'


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--start', type=date.fromisoformat, default=date(2022, 12, 1))
    parser.add_argument('--end', type=date.fromisoformat, default=date(2025, 12, 31))
    parser.add_argument('--root', type=Path, default=ROOT/'data/tariffs/osinergmin')
    active = yaml.safe_load((ROOT/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))['dataset_root']
    parser.add_argument('--sheets-dir', type=Path, default=ROOT/active/'raw/osinergmin')
    parser.add_argument('--offline', action='store_true')
    args = parser.parse_args(argv)
    previous = _load_manifest(args.root)
    charges = _load_charges(args.sheets_dir)
    try:
        if args.offline:
            if not previous:
                raise SourceChangedError(f'{args.root}: no manifest to rebuild from')
            files, missing = previous['files'], previous.get('missing', [])
        else:
            files, missing = _download(args.root, previous, args.start, args.end, charges)
        sheets = {date.fromisoformat(day): parse_pba(_check_registered(args.root, day, entry))
                  for day, entry in files.items()}
    except (PbaFormatError, SourceChangedError, requests.RequestException, OSError) as error:
        print(f'refused: {error}', file=sys.stderr)
        return 2
    report = crosscheck(sheets, charges)
    manifest = {'schema_version': 1, 'system': DEFAULT_SYSTEM, 'files': dict(sorted(files.items())),
                'missing': missing, 'crosscheck': report, 'limitations': LIMITATIONS}
    _write_atomic(args.root/'busbar_electro_oriente.csv', _csv_text(sheets, report))
    _write_atomic(args.root/'pba_manifest.json', json.dumps(manifest, indent=2, ensure_ascii=False) + '\n')
    print(f'{len(sheets)} validity dates, {len(report["rows"])} cross-checked, {len(report["failures"])} failures, '
          f'pdf_only={report["pdf_only"]}, sheet_only={report["sheet_only"]}')
    return 0 if tariff_crosscheck_gate(report) else 3


if __name__ == '__main__':
    sys.exit(main())
