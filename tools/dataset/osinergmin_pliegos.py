"""Official Osinergmin tariff sheets (pliegos tarifarios) for the Iquitos sector.

Source: https://www.osinergmin.gob.pe/Tarifas/Electricidad/PliegoTarifario.aspx?Id=160000
(Electro Oriente, Loreto). The page is an ASP.NET form with a sector list (DDLSE)
and a list of validity dates (DDLFecha); each sheet is obtained with the page's own
form postback for sector IQUITOS and one date. Every response is stored verbatim as
a raw source; nothing is retyped. Values are without IGV.

A sheet is in force from its validity date until the next one; the sheet that
applies to a billing month is the last one in force on the first day of that month
(``sheet_for_month``) and the share of days under each sheet is recorded
(``month_coverage``) because Osinergmin often updates on the 4th of a month.
"""
from __future__ import annotations

import re
import time
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Dict, List, Mapping, Tuple

URL = 'https://www.osinergmin.gob.pe/Tarifas/Electricidad/PliegoTarifario.aspx?Id=160000'
POST_URL = 'https://www.osinergmin.gob.pe/Tarifas/Electricidad/PliegoTarifario?Id=160000'  # the form action
SECTOR = 'IQUITOS'
MONTHS = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
          'set': 9, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}
HEADERS = {'User-Agent': 'Mozilla/5.0 (MADRL Iquitos thesis; dataset provenance)'}
PAUSE_S = 1.5  # polite spacing between requests


def parse_date(label: str) -> date:
    day, month, year = label.strip().split('/')
    return date(int(year), MONTHS[month.strip().casefold()[:3]], int(day))


def _hidden(html: str) -> Dict[str, str]:
    return {name: value for name, value in re.findall(
        r'<input type="hidden" name="([^"]+)" id="[^"]*" value="([^"]*)"', html)}


def _options(html: str, name: str) -> List[Tuple[str, bool]]:
    block = html[html.index(f'name="{name}"'):]
    block = block[:block.index('</select>')]
    return [(value, 'selected' in attrs) for attrs, value in re.findall(r'<option([^>]*)value="([^"]*)"', block)]


def _selected(html: str, name: str) -> str:
    return next(value for value, chosen in _options(html, name) if chosen).strip()


def fetch_sheets(target_dir: Path, start: date, end: date, *, session=None) -> List[dict]:
    """Download every sheet of the IQUITOS sector valid from ``start`` (the one in force) to ``end``.

    Raises on HTTP errors (e.g. 403): a blocked server is reported, never bypassed.
    """
    import html as html_lib
    import requests
    session = session or requests.Session()
    target_dir = Path(target_dir)
    target_dir.mkdir(parents=True, exist_ok=True)
    first = session.get(URL, headers=HEADERS, timeout=60)
    first.raise_for_status()
    page = first.text
    sector_value = next(v for v, _ in _options(page, 'DDLSE') if v.strip() == SECTOR)
    dates = [v for v, _ in _options(page, 'DDLFecha')]
    parsed = sorted(((parse_date(v), v) for v in dates), key=lambda item: item[0])
    in_force = [d for d, _ in parsed if d <= start]
    lower = in_force[-1] if in_force else parsed[0][0]
    wanted = [(d, v) for d, v in parsed if lower <= d <= end]
    entries = []
    for valid_from, raw_value in wanted:
        time.sleep(PAUSE_S)
        form = {k: html_lib.unescape(v) for k, v in _hidden(page).items()}
        textbox = re.search(r'name="TextBox1" type="text" value="([^"]*)"', page)
        form.update({'__EVENTTARGET': 'DDLFecha', '__EVENTARGUMENT': '', '__LASTFOCUS': '',
                     'DDLSE': html_lib.unescape(sector_value), 'DDLFecha': raw_value,
                     'TextBox1': html_lib.unescape(textbox.group(1)) if textbox else ''})
        response = session.post(POST_URL, data=form, headers={**HEADERS, 'Referer': URL}, timeout=60)
        response.raise_for_status()
        text = response.text
        if _selected(text, 'DDLSE') != SECTOR or parse_date(_selected(text, 'DDLFecha')) != valid_from:
            raise ValueError(f'{valid_from}: the response is not the IQUITOS sheet of that date')
        path = target_dir/f'pliego_iquitos_{valid_from.isoformat()}.html'
        path.write_bytes(response.content)
        entries.append({'path': path, 'valid_from': valid_from.isoformat(),
                        'obtained_at': datetime.now(timezone.utc).isoformat(), 'source_uri': URL,
                        'form': {'DDLSE': SECTOR, 'DDLFecha': raw_value.strip()}})
        page = text
    return entries


_CHARGES = {
    # (tariff, normalized label prefix) -> key
    'cargo fijo mensual': 'fixed_pen_month',
    'cargo por energia activa en punta': 'energy_peak_ctm_kwh',
    'cargo por energia activa fuera de punta': 'energy_offpeak_ctm_kwh',
    'cargo por energia activa': 'energy_ctm_kwh',
    'cargo por potencia activa de generacion en hp': 'gen_hp_pen_kw',
    'cargo por potencia activa de distribucion en hp': 'dist_hp_pen_kw',
    'cargo por exceso de potencia activa de distribucion en hfp': 'dist_excess_hfp_pen_kw',
    'cargo por energia reactiva': 'reactive_ctm_kvarh',
}


def _norm(text: str) -> str:
    import unicodedata
    text = unicodedata.normalize('NFKD', text)
    return re.sub(r'\s+', ' ', ''.join(c for c in text if not unicodedata.combining(c))).strip().casefold()


def decode(payload: bytes) -> str:
    """The server labels the page UTF-8 but sends Windows-1252 accented letters."""
    try:
        return payload.decode('utf-8')
    except UnicodeDecodeError:
        return payload.decode('cp1252')


def parse_sheet(html) -> Dict[str, Dict[str, float]]:
    """Charges per tariff (MT2..BT5B) from one sheet; numbers as printed, without IGV."""
    if isinstance(html, bytes):
        html = decode(html)
    text = re.sub(r'<[^>]+>', '\n', html)
    import html as html_lib
    lines = [html_lib.unescape(line).strip() for line in text.splitlines()]
    lines = [line for line in lines if line and line != '\xa0']
    tariffs: Dict[str, Dict[str, float]] = {}
    current = None
    pending = None  # 'gen' / 'dist' for the two-row "Presentes en / Fuera de Punta" blocks
    i = 0
    number = re.compile(r'^-?\d+(?:[.,]\d+)?$')

    def next_number(j):
        while j < len(lines) and not number.match(lines[j]):
            j += 1
        return (float(lines[j].replace(',', '.')), j) if j < len(lines) else (None, j)
    while i < len(lines):
        line = lines[i]
        found = re.match(r'^TARIFA (MT\d|BT\d[A-Z]?)\b', line)
        if found:
            current = found.group(1)
            tariffs.setdefault(current, {})
            pending = None
            i += 1
            continue
        if current is None:
            i += 1
            continue
        key = _norm(line)
        if key.startswith('cargo por potencia activa de generacion para usuarios') or \
                key.startswith('cargo por potencia de generacion para usuarios') or \
                key.startswith('cargo por potencia activa de generacion para usuarios'):
            pending = 'gen'
        elif key.startswith('cargo por potencia activa de redes de distribucion para usuarios') or \
                key.startswith('cargo por potencia de redes de distribucion para usuarios'):
            pending = 'dist'
        elif pending and key.startswith('presentes en punta'):
            value, i = next_number(i + 1)
            tariffs[current][f'{pending}_present_peak_pen_kw'] = value
            continue
        elif pending and key.startswith('presentes fuera de punta'):
            value, i = next_number(i + 1)
            tariffs[current][f'{pending}_present_offpeak_pen_kw'] = value
            continue
        else:
            for prefix, name in _CHARGES.items():
                if key.startswith(prefix) and name not in tariffs[current]:
                    if prefix == 'cargo por energia activa' and ('punta' in key):
                        continue
                    value, i = next_number(i + 1)
                    tariffs[current][name] = value
                    pending = None
                    break
            else:
                i += 1
                continue
            continue
        i += 1
    return {k: v for k, v in tariffs.items() if v}


def sheet_for_month(sheets: Mapping[date, dict], year: int, month: int) -> date:
    """Validity date of the sheet in force on the first day of the month."""
    first = date(year, month, 1)
    candidates = [d for d in sheets if d <= first]
    if not candidates:
        raise ValueError(f'no sheet in force on {first}')
    return max(candidates)


def month_coverage(sheets: Mapping[date, dict], year: int, month: int) -> Dict[str, float]:
    """Share of the month's days under each sheet in force during it."""
    import calendar
    days = calendar.monthrange(year, month)[1]
    out: Dict[str, float] = {}
    for day in range(1, days + 1):
        current = max(d for d in sheets if d <= date(year, month, day))
        out[current.isoformat()] = out.get(current.isoformat(), 0.0) + 1.0/days
    return out


# ── bill reconstruction (validation of sector and months) ───────────────────

IGV = 0.18  # Peru general sales tax; the sheet values are "Sin IGV"
PEAK_HOURS_PER_DAY = 5  # 18:00-23:00 (assumption: the block is not printed on the sheet)
PRESENT_IN_PEAK_RATIO = 0.5  # qualification rule (assumption, Osinergmin tariff-options norm, not on the sheet)


def weighted_charges(sheets: Mapping[date, dict], year: int, month: int, tariff: str) -> Dict[str, float]:
    """Charges of one tariff weighted by the days each sheet is in force in the month."""
    out: Dict[str, float] = {}
    for valid_from, share in month_coverage(sheets, year, month).items():
        charges = sheets[date.fromisoformat(valid_from)].get(tariff)
        if charges is None:
            raise KeyError(f'{tariff} missing in sheet {valid_from}')
        for key, value in charges.items():
            out[key] = out.get(key, 0.0) + share*float(value)
    return out


def reconstruct_bill(*, tariff: str, year: int, month: int, peak_kwh: float, offpeak_kwh: float,
                     reactive_kvarh: float, load_factor: float, sheets: Mapping[date, dict]) -> Dict[str, float]:
    """Monthly bill [PEN] from the sheet: fixed + energy + capacity + reactive, without and with IGV.

    Pmax = E/(LF*hours). Present in peak when (E_peak/peak hours)/Pmax >= 0.5. MT2/BT2:
    generation and distribution HP charges on Pmax (HP maximum assumed = monthly
    maximum, excess-HFP term 0). MT3/MT4/BT3/BT4: generation and distribution on
    Pmax at the present-in-peak or off-peak rate. Distribution is billed on the
    month's maximum (the regulation's multi-month averaging is not reproducible
    from a bill). Other bill items (public lighting, rural electrification
    contribution, interest, rounding) are not in the sheet and stay in the residual.
    """
    import calendar
    charges = weighted_charges(sheets, year, month, tariff)
    hours = calendar.monthrange(year, month)[1]*24
    energy = peak_kwh + offpeak_kwh
    pmax = energy/(load_factor*hours) if load_factor and load_factor > 0 else float('nan')
    peak_hours = calendar.monthrange(year, month)[1]*PEAK_HOURS_PER_DAY
    present = (peak_kwh/peak_hours)/pmax >= PRESENT_IN_PEAK_RATIO if pmax == pmax and pmax > 0 else True
    if 'energy_ctm_kwh' in charges:
        energy_pen = energy*charges['energy_ctm_kwh']/100.0
    else:
        energy_pen = (peak_kwh*charges['energy_peak_ctm_kwh'] + offpeak_kwh*charges['energy_offpeak_ctm_kwh'])/100.0
    if 'gen_hp_pen_kw' in charges:
        capacity_pen = pmax*(charges['gen_hp_pen_kw'] + charges['dist_hp_pen_kw'])
        rate = charges['gen_hp_pen_kw'] + charges['dist_hp_pen_kw']
    else:
        tag = 'peak' if present else 'offpeak'
        rate = charges[f'gen_present_{tag}_pen_kw'] + charges[f'dist_present_{tag}_pen_kw']
        capacity_pen = pmax*rate
    reactive_pen = max(0.0, reactive_kvarh - 0.3*energy)*charges.get('reactive_ctm_kvarh', 0.0)/100.0
    subtotal = charges.get('fixed_pen_month', 0.0) + energy_pen + capacity_pen + reactive_pen
    return {'pmax_kw': pmax, 'present_in_peak': bool(present), 'energy_pen': energy_pen, 'capacity_pen': capacity_pen,
            'capacity_rate_pen_kw': rate, 'reactive_pen': reactive_pen, 'fixed_pen': charges.get('fixed_pen_month', 0.0),
            'subtotal_without_igv_pen': subtotal, 'total_with_igv_pen': subtotal*(1 + IGV),
            'energy_rate_ctm_kwh': charges.get('energy_ctm_kwh', charges.get('energy_peak_ctm_kwh'))}


def sheet_labels(payload: bytes) -> Dict[str, str]:
    """Identity printed in the response: selected sector and date, sector type label and system label."""
    text = decode(payload)
    sector = re.search(r'id="LBSector"[^>]*>([^<&]*)', text)
    inter = re.search(r'id="LBInter"[^>]*>([^<&]*)', text)
    return {'DDLSE': _selected(text, 'DDLSE'), 'DDLFecha': _selected(text, 'DDLFecha'),
            'LBSector': sector.group(1).strip() if sector else '', 'LBInter': inter.group(1).strip() if inter else ''}


DEFINITION_KEYWORDS = ('horas de punta', 'hora punta', 'horas punta', 'calificacion', 'presente en punta',
                       'presentes en punta', '18:00', '23:00')


def definitions_found(payload: bytes) -> Dict[str, List[str]]:
    """Search one sheet for peak-block and qualification definitions (context snippets)."""
    import html as html_lib
    text = _norm(html_lib.unescape(re.sub(r'<[^>]+>', ' ', decode(payload))))
    found: Dict[str, List[str]] = {}
    for keyword in DEFINITION_KEYWORDS:
        for match in re.finditer(re.escape(keyword), text):
            found.setdefault(keyword, []).append(text[max(0, match.start() - 80): match.start() + 120])
    return found
