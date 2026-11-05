"""Osinergmin busbar tariff PDFs (PBA): names, download and extraction.

Page 1 lists, for each isolated system, one row in "Precios en Barra" and one in
"Precios Efectivos". Each row prints the base values and then the updated ones; the
updated values are the ones in force on the printed date. A blocked server is
reported, never bypassed, and a source already registered is never overwritten.
"""
from __future__ import annotations

import hashlib
import io
import os
import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Iterable, List, Optional, Tuple
from urllib.parse import quote

from uc3m.domain.tariffs import BusbarPrice, BusbarSheet

BASE_URL = 'https://www.osinergmin.gob.pe/seccion/centro_documental/gart/PliegosTarifarios/'
HEADERS = {'User-Agent': 'Mozilla/5.0 (MADRL Iquitos thesis; dataset provenance)'}
DEFAULT_SYSTEM = 'Electro Oriente'
MONTHS = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
          'set': 9, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}
_NUMBER = r'(\d+,\d+)'
_DATE = re.compile(r'ACTUALIZADO\s+AL\s+(\d{1,2})[/ ]+([^\W\d_]+)[/ ]+(\d{4})', re.IGNORECASE)
_RESOLUTION = re.compile(r'(\d{3}-\d{4})-OS/CD')


class PbaFormatError(ValueError):
    """The document is not the expected PBA, or does not hold the expected rows."""


class SourceChangedError(ValueError):
    """A registered source no longer has the registered content."""


def _number(text: str) -> float:
    return float(text.replace(',', '.'))


def _printed_date(text: str) -> date:
    found = _DATE.search(text)
    if not found:
        raise PbaFormatError('no "ACTUALIZADO AL" date in the document')
    month = MONTHS.get(found.group(2).casefold()[:3])
    if month is None:
        raise PbaFormatError(f'unknown month {found.group(2)!r}')
    return date(int(found.group(3)), month, int(found.group(1)))


def parse_pba_text(text: str, *, system: str = DEFAULT_SYSTEM) -> BusbarSheet:
    """Busbar and effective rows of ``system``; exactly two rows or the document is refused."""
    valid_from = _printed_date(text)
    name = r'\s+'.join(re.escape(word) for word in system.split()) + r'\s+MT\s+'
    values = r'\s+'.join([_NUMBER]*3)
    rows = re.findall(name + values + r'\s+' + name + values, text)
    if len(rows) != 2:
        raise PbaFormatError(f'{valid_from}: expected 2 rows of {system}, found {len(rows)}')
    barra, efectivo = (BusbarPrice(*(_number(cell) for cell in row[3:])) for row in rows)
    return BusbarSheet(valid_from, system, tuple(sorted(set(_RESOLUTION.findall(text)))), barra, efectivo)


def parse_pba(payload: bytes, *, system: str = DEFAULT_SYSTEM) -> BusbarSheet:
    from pypdf import PdfReader
    return parse_pba_text(PdfReader(io.BytesIO(payload)).pages[0].extract_text() or '', system=system)


def candidate_names(valid_from: date) -> Tuple[str, str]:
    stamp = valid_from.strftime('%d%m%Y')
    return f'1 PBA{stamp}.pdf', f'PBA{stamp}.pdf'


def candidate_dates(start: date, end: date, sheet_dates: Iterable[date]) -> List[date]:
    """Dates of the tariff sheets in range plus the 4th of each month, the usual update day."""
    found = {d for d in sheet_dates if start <= d <= end}
    year, month = start.year, start.month
    while (year, month) <= (end.year, end.month):
        fourth = date(year, month, 4)
        if start <= fourth <= end:
            found.add(fourth)
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return sorted(found)


def fetch_pba(valid_from: date, raw_dir: Path, *, session, known_sha256: Optional[str] = None,
              pause_s: float = 1.5, system: str = DEFAULT_SYSTEM) -> Optional[dict]:
    """Store the PBA of one validity date verbatim; ``None`` when every name variant gives 404."""
    for name in candidate_names(valid_from):
        url = BASE_URL + quote(name)
        time.sleep(pause_s)
        response = session.get(url, headers=HEADERS, timeout=90)
        if response.status_code == 404:
            continue
        response.raise_for_status()
        return _store(response.content, url, valid_from, Path(raw_dir), known_sha256, system)
    return None


def _store(payload: bytes, url: str, valid_from: date, raw_dir: Path, known_sha256: Optional[str], system: str) -> dict:
    if not payload.startswith(b'%PDF'):
        raise PbaFormatError(f'{valid_from}: the response is not a PDF')
    printed = parse_pba(payload, system=system).valid_from
    if printed != valid_from:
        raise PbaFormatError(f'{valid_from}: the document is dated {printed}')
    digest = hashlib.sha256(payload).hexdigest()
    target = raw_dir/f'pba_{valid_from.isoformat()}.pdf'
    if known_sha256 is not None and known_sha256 != digest:
        raise SourceChangedError(f'{valid_from}: source_changed, registered {known_sha256}, received {digest}')
    if target.exists():
        if hashlib.sha256(target.read_bytes()).hexdigest() != digest:
            raise SourceChangedError(f'{valid_from}: source_changed, {target.name} differs from the response')
    else:
        raw_dir.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix('.tmp')
        partial.write_bytes(payload)
        os.replace(partial, target)
    return {'path': str(target), 'source_uri': url, 'sha256': digest,
            'obtained_at': datetime.now(timezone.utc).isoformat(), 'valid_from': valid_from.isoformat()}
