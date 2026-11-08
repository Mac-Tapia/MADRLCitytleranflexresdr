"""Leakage-free monthly targets and the dataset build use case.

Monthly targets are the measured bills, completed without crossing years: a
missing month is modeled only from the same building's measured months of the
same year (on that year's cross-building seasonal shape) or, when the building
has no measurement that year, from same-year measured peers of the same use
type scaled by floor area. No value of a held-out year enters a training-year
target. The hourly generation itself is an injected port (the dataset tools),
so this module stays free of simulator and dataframe libraries.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from uc3m.application.dataset.provenance import RawSourceManifest, contained_path
from uc3m.application.dataset.site import load_default_site

PEAK_HOURS = load_default_site().peak_block_hours  # site configuration (SPEC-017 FR-017.1)
MONTHS = {'ene': 1, 'feb': 2, 'mar': 3, 'abr': 4, 'may': 5, 'jun': 6, 'jul': 7, 'ago': 8,
          'set': 9, 'sep': 9, 'oct': 10, 'nov': 11, 'dic': 12}
PARTIAL_LOAD_FACTOR_RATIO = 0.5  # of the building's same-year median load factor
BALANCE_RTOL = 1e-4  # 0.01 % monthly energy closure (design section 7)
FORBIDDEN_OUTPUT_PREFIXES = ('CityLearn/', 'external/', 'outputs/')


@dataclass(frozen=True)
class MonthlyRecord:
    building_id: int
    year: int
    month: int
    energy_kwh: float
    peak_kwh: float
    offpeak_kwh: float
    provenance: str
    method: str
    fit_scope: str
    inputs: Tuple[str, ...]
    flags: Tuple[str, ...] = ()
    load_factor: Optional[float] = None
    billed_amount: Optional[float] = None

    @property
    def label(self) -> str:
        return f'B{self.building_id:02d}:{self.year}-{self.month:02d}'

    def as_row(self):
        return {'building_id': self.building_id, 'year': self.year, 'month': self.month,
                'energy_kwh': repr(self.energy_kwh), 'peak_kwh': repr(self.peak_kwh),
                'offpeak_kwh': repr(self.offpeak_kwh), 'provenance': self.provenance,
                'method': self.method, 'fit_scope': self.fit_scope, 'inputs': '|'.join(self.inputs),
                'flags': '|'.join(self.flags),
                'load_factor': '' if self.load_factor is None else repr(self.load_factor),
                'billed_amount': '' if self.billed_amount is None else repr(self.billed_amount)}


def _number(text: str) -> Optional[float]:
    text = (text or '').strip().replace('.', '').replace(',', '.') if ',' in (text or '') else (text or '').strip()
    if not text:
        return None
    return float(text)


def _read_text(path: Path) -> str:
    raw = Path(path).read_bytes()
    for encoding in ('utf-8-sig', 'cp1252'):
        try:
            return raw.decode(encoding)
        except UnicodeDecodeError:
            continue
    raise ValueError(f'{path}: unsupported text encoding')


def _key(header: str) -> str:
    return ''.join(ch for ch in header.casefold() if ch.isalnum())


_COLUMNS = {'peak': 'energiaactivahorapunta', 'offpeak': 'energiaactivafuerapunta',
            'load_factor': 'factorcarga', 'total': 'totalenergiaactiva', 'amount': 'totalfacturado'}


TOU_TOTAL_RTOL = 0.02  # printed total vs time-of-use registers
PLAUSIBLE_PRINTED_TOTAL_RATIO = (0.5, 2.0)  # outside this the printed total is a transcription error
# D-V6-57: a printed-total column misaligned with its registers. Design rule, not a measurement: the kWh tolerance
# absorbs rounding of two-decimal totals, and most rows must agree so that coincidences cannot trigger it.
SHIFTED_TOTAL_MATCH_KWH = 1.0
SHIFTED_TOTAL_MIN_SHARE = 0.9
SHIFTED_TOTAL_MIN_ROWS = 12
SHIFTED_TOTAL_MAX_OFFSET = 12


def printed_total_offset(registers: Sequence[float], totals: Sequence[float]) -> int:
    """D-V6-57: rows between a printed total and the registers it equals; 0 when the column is aligned or unclear."""
    def share(offset):
        pairs = [(registers[i], totals[i + offset]) for i in range(len(registers)) if 0 <= i + offset < len(totals)]
        hits = sum(abs(a - b) <= SHIFTED_TOTAL_MATCH_KWH for a, b in pairs)
        return len(pairs), (hits/len(pairs) if pairs else 0.0)
    if share(0)[1] >= 0.5:
        return 0
    for distance in range(1, SHIFTED_TOTAL_MAX_OFFSET + 1):
        for offset in (distance, -distance):
            rows, agreeing = share(offset)
            if rows >= SHIFTED_TOTAL_MIN_ROWS and agreeing >= SHIFTED_TOTAL_MIN_SHARE:
                return offset
    return 0


def parse_billing_csv(path: Path, building_id: int, *,
                      scale_tou_to_printed_total: bool = False) -> List[MonthlyRecord]:
    """Measured monthly bills, columns located by header (files differ in spare columns).

    With ``scale_tou_to_printed_total`` (owner decision 2026-11-01, campaign v2) a
    month whose time-of-use registers differ from the printed total by more than
    2 % keeps the register split but is scaled to the printed total and flagged.
    A printed total outside 0.5..2 times the registers (e.g. 156.8 kWh printed for
    2 252.8 kWh registered) is treated as a transcription error: registers kept,
    flagged ``printed_total_implausible``. A printed-total column that equals the
    registers of other rows at a fixed distance (D-V6-57) says nothing about its own
    month: registers kept, flagged ``printed_total_column_shifted``.
    """
    records = []
    reader = csv.reader(_read_text(path).splitlines(), delimiter=';')
    header = [_key(h) for h in next(reader, [])]
    if 'mes' not in header:
        raise ValueError(f'{path}: no Mes column')
    index = {name: header.index(key) for name, key in _COLUMNS.items() if key in header}
    missing = set(_COLUMNS) - set(index)
    if missing:
        raise ValueError(f'{path}: missing billing columns {sorted(missing)}')
    month_at = header.index('mes')
    year_at = month_at + 1  # the year header is mis-encoded in the source files
    rows = [row for row in reader
            if len(row) > max(index.values()) and row[month_at].strip() and row[year_at].strip()]
    numbers = [tuple(_number(row[index[k]]) for k in ('peak', 'offpeak', 'total')) for row in rows]
    complete = [n for n in numbers if None not in n]
    shifted = printed_total_offset([p + o for p, o, _ in complete], [t for _, _, t in complete]) != 0
    # D-V6-57: reactive energy and load factor follow the registers; the printed total and, in several files, the
    # billed amount do not, so every row of a shifted file is flagged and its amount never validates a tariff.
    for row in rows:
        month = MONTHS.get(row[month_at].strip().casefold()[:3])
        if month is None:
            raise ValueError(f'{path}: unknown month {row[month_at]!r}')
        year = int(row[year_at].strip())
        peak, offpeak, total = (_number(row[index[k]]) for k in ('peak', 'offpeak', 'total'))
        load_factor, amount = _number(row[index['load_factor']]), _number(row[index['amount']])
        if peak is None or offpeak is None or total is None or peak + offpeak <= 0:
            raise ValueError(f'{path}: incomplete energy fields for {year}-{month:02d}')
        flags = ['printed_total_column_shifted'] if shifted else []
        if abs(peak + offpeak - total) > TOU_TOTAL_RTOL*max(total, 1.0):
            flags.append('total_mismatch')
            if not shifted and scale_tou_to_printed_total:
                ratio = total/(peak + offpeak)
                low, high = PLAUSIBLE_PRINTED_TOTAL_RATIO
                if low <= ratio <= high:
                    peak, offpeak = peak*ratio, offpeak*ratio
                    flags.append('tou_scaled_to_printed_total')
                else:
                    flags.append('printed_total_implausible')
        # Physical active energy is the time-of-use register split (as the audited
        # buildingcsv_inputs.resolve_active_energy rule); without the v2 option the
        # printed total is audit only.
        record = MonthlyRecord(building_id, year, month, peak + offpeak, peak, offpeak,
                               'measured', 'billing', 'measured',
                               (f'B{building_id:02d}:{year}-{month:02d}',), tuple(flags),
                               load_factor, amount)
        records.append(record)
    keys = [(r.year, r.month) for r in records]
    if len(keys) != len(set(keys)):
        raise ValueError(f'{path}: duplicate monthly records')
    return records


def add_second_supply(targets: Sequence[MonthlyRecord], building_id: int,
                      rows: Mapping[Tuple[int, int], Tuple[float, float]], *, source_label: str) -> List[MonthlyRecord]:
    """D-V6-58: a building's bills cover one supply and a report table measures a second one (kWh, kW by month).

    A measured month adds the table's value. Any other month is modeled with the energy ratio of the months both
    supplies were measured, because the campaign years must describe the same building. The peak/off-peak split is the
    bill's, and the load factor combines both supplies by their demand (sum of each maximum, not coincident).
    """
    from dataclasses import replace
    from calendar import monthrange
    own = {(t.year, t.month): t for t in targets if t.building_id == building_id}
    overlap = [key for key in rows if key in own and own[key].energy_kwh > 0 and rows[key][0] > 0]
    if not overlap:
        raise ValueError(f'B{building_id:02d}: no month measures both supplies')
    ratio = sum(rows[k][0] for k in overlap)/sum(own[k].energy_kwh for k in overlap)
    factors = sorted(rows[k][0]/(rows[k][1]*24*monthrange(*k)[1]) for k in overlap if rows[k][1] > 0)
    typical_factor = factors[len(factors)//2]
    out = []
    for target in targets:
        key = (target.year, target.month)
        if target.building_id != building_id:
            out.append(target)
            continue
        measured = key in rows and rows[key][0] > 0
        second = rows[key][0] if measured else target.energy_kwh*ratio
        second_factor = (rows[key][0]/(rows[key][1]*24*monthrange(*key)[1])
                         if measured and rows[key][1] > 0 else typical_factor)
        scale = (target.energy_kwh + second)/target.energy_kwh
        factor = target.load_factor
        if factor:
            factor = (target.energy_kwh + second)/(target.energy_kwh/factor + second/second_factor)
        both_measured = measured and target.provenance == 'measured'
        out.append(replace(target, energy_kwh=target.energy_kwh + second, peak_kwh=target.peak_kwh*scale,
                           offpeak_kwh=target.offpeak_kwh*scale,
                           provenance='measured' if both_measured else 'modeled',
                           method=f'{target.method}+second_supply',
                           fit_scope='measured' if both_measured else target.fit_scope,
                           inputs=target.inputs + (f'{source_label}:{key[0]}-{key[1]:02d}' if measured
                                                   else f'{source_label}:ratio={ratio:.6f}',),
                           flags=target.flags + ('second_supply_measured' if measured else 'second_supply_modeled',),
                           load_factor=factor, billed_amount=None))
    return out


def energy_only_records(building_id: int, rows: Sequence[Tuple[int, int, float]],
                        records: Sequence[MonthlyRecord], inventory: Mapping[int, Mapping[str, object]],
                        *, source_label: str) -> List[MonthlyRecord]:
    """Measured monthly energy without a time-of-use split (e.g. a compiled report table).

    The energy stays measured; only the peak/off-peak split is modeled, from the
    same-month same-year bills of peers with the same use type.
    """
    use_type = inventory[building_id]['use_type']
    by_key = {(r.building_id, r.year, r.month): r for r in records}
    out = []
    for year, month, energy in rows:
        peers = sorted(b for b in inventory if b != building_id and inventory[b]['use_type'] == use_type
                       and (b, year, month) in by_key)
        if not peers:
            raise ValueError(f'B{building_id:02d}:{year}-{month:02d} has no same-year {use_type} peer for its split')
        peer_rows = [by_key[(b, year, month)] for b in peers]
        share = sum(r.peak_kwh for r in peer_rows)/sum(r.energy_kwh for r in peer_rows)
        out.append(MonthlyRecord(building_id, year, month, float(energy), energy*share, energy*(1 - share),
                                 'measured', 'energy_only_report', 'measured',
                                 (f'{source_label}:{year}-{month:02d}',) + tuple(f'split:{r.label}' for r in peer_rows),
                                 ('tou_split_modeled',)))
    return out


def _flag_partial_months(measured):
    """A month whose load factor is under half its building's same-year median looks partial."""
    from dataclasses import replace
    flagged = dict(measured)
    groups: Dict[Tuple[int, int], List[MonthlyRecord]] = {}
    for record in measured.values():
        groups.setdefault((record.building_id, record.year), []).append(record)
    for rows in groups.values():
        factors = sorted(r.load_factor for r in rows if r.load_factor is not None and r.load_factor > 0)
        if len(factors) < 3:
            continue
        median = factors[len(factors)//2] if len(factors) % 2 else 0.5*(factors[len(factors)//2 - 1] + factors[len(factors)//2])
        for record in rows:
            if record.load_factor is not None and record.load_factor < PARTIAL_LOAD_FACTOR_RATIO*median:
                flagged[(record.building_id, record.year, record.month)] = replace(
                    record, flags=record.flags + ('partial_month_suspect',))
    return flagged


def _fit_usable(record: MonthlyRecord) -> bool:
    return record.provenance == 'measured' and 'partial_month_suspect' not in record.flags


def _year_shape(measured: Mapping[Tuple[int, int, int], MonthlyRecord], year: int) -> Tuple[Dict[int, float], Tuple[str, ...]]:
    """Mean normalized monthly profile of buildings fully measured in that year."""
    by_building: Dict[int, Dict[int, MonthlyRecord]] = {}
    for (building, y, month), record in measured.items():
        if y == year:
            by_building.setdefault(building, {})[month] = record
    complete = sorted(b for b, months in by_building.items()
                      if len(months) == 12 and all(_fit_usable(r) for r in months.values()))
    if not complete:
        raise ValueError(f'no building is fully measured in {year}; the seasonal shape is undefined')
    shape = {}
    for month in range(1, 13):
        ratios = []
        for building in complete:
            months = by_building[building]
            mean = sum(r.energy_kwh for r in months.values())/12.0
            ratios.append(months[month].energy_kwh/mean)
        shape[month] = sum(ratios)/len(ratios)
    return shape, tuple(f'B{b:02d}:{year}' for b in complete)


@dataclass(frozen=True)
class DeclaredBackcast:
    """An owner-approved exception that fills a year from another year's measurements.

    It is the only path that crosses years, and every value it produces is
    flagged cross_year_leakage_declared so evaluation can exclude it.
    """
    year: int
    from_year: int
    scale: float
    reason: str


def _backcast(building, year, month, rule, measured):
    sources = [measured.get((building, rule.from_year, m)) for m in range(1, 13)]
    if any(s is None for s in sources):
        raise ValueError(f'B{building:02d}: a declared backcast needs all 12 measured months of {rule.from_year}')
    source = sources[month - 1]
    energy = rule.scale*source.energy_kwh
    share = source.peak_kwh/source.energy_kwh
    return MonthlyRecord(building, year, month, energy, energy*share, energy*(1 - share), 'modeled',
                         'declared_backcast', 'declared_cross_year_leakage',
                         (source.label, f'scale:{rule.scale}'), ('cross_year_leakage_declared',))


def complete_monthly_targets(records: Iterable[MonthlyRecord], inventory: Mapping[int, Mapping[str, object]],
                             *, years: Sequence[int], buildings: Sequence[int],
                             declared_backcasts: Optional[Mapping[int, DeclaredBackcast]] = None) -> List[MonthlyRecord]:
    measured = {}
    for record in records:
        key = (record.building_id, record.year, record.month)
        if key in measured:
            raise ValueError(f'duplicate measured record {record.label}')
        measured[key] = record
    measured = _flag_partial_months(measured)
    targets = []
    for year in years:
        shape, shape_inputs = _year_shape(measured, year)
        for building in buildings:
            own = [measured[(building, year, m)] for m in range(1, 13) if (building, year, m) in measured]
            fit = [r for r in own if _fit_usable(r)]
            for month in range(1, 13):
                key = (building, year, month)
                if key in measured:
                    targets.append(measured[key])
                    continue
                rule = (declared_backcasts or {}).get(building)
                if rule is not None and rule.year == year:
                    targets.append(_backcast(building, year, month, rule, measured))
                    continue
                if fit:
                    scale = sum(r.energy_kwh/shape[r.month] for r in fit)/len(fit)
                    share = sum(r.peak_kwh for r in fit)/sum(r.energy_kwh for r in fit)
                    energy = scale*shape[month]
                    targets.append(MonthlyRecord(
                        building, year, month, energy, energy*share, energy*(1 - share), 'modeled',
                        'same_year_shape_scaling', 'same_building_same_year',
                        tuple(r.label for r in fit) + tuple(f'shape:{item}' for item in shape_inputs)))
                    continue
                use_type = inventory[building]['use_type']
                peers = sorted(b for b in buildings if b != building
                               and inventory[b]['use_type'] == use_type
                               and (b, year, month) in measured and _fit_usable(measured[(b, year, month)]))
                if not peers:
                    raise ValueError(f'B{building:02d}:{year}-{month:02d} has no measurement and no '
                                     f'same-year {use_type} peer; it cannot be modeled without leakage')
                peer_records = [measured[(b, year, month)] for b in peers]
                intensity = sum(r.energy_kwh for r in peer_records)/sum(float(inventory[b]['area_m2']) for b in peers)
                share = sum(r.peak_kwh for r in peer_records)/sum(r.energy_kwh for r in peer_records)
                energy = intensity*float(inventory[building]['area_m2'])
                targets.append(MonthlyRecord(
                    building, year, month, energy, energy*share, energy*(1 - share), 'modeled',
                    'peer_intensity_same_year', 'same_year_observed_peers',
                    tuple(r.label for r in peer_records)))
    return targets


def write_monthly_targets(path: Path, targets: Sequence[MonthlyRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    columns = list(MonthlyRecord(0, 0, 0, 0.0, 0.0, 0.0, '', '', '', ()).as_row())
    with open(path, 'w', encoding='utf-8', newline='') as stream:
        writer = csv.DictWriter(stream, fieldnames=columns, lineterminator='\n')
        writer.writeheader()
        for record in sorted(targets, key=lambda r: (r.building_id, r.year, r.month)):
            writer.writerow(record.as_row())


def check_monthly_balance(hourly_by_building: Mapping[int, Sequence[Tuple[str, float]]],
                          targets: Sequence[MonthlyRecord], *, rtol: float = BALANCE_RTOL):
    """Close monthly total, peak and off-peak energy of the hourly series against targets."""
    sums: Dict[Tuple[int, int, int], List[float]] = {}
    for building, rows in hourly_by_building.items():
        for stamp, kwh in rows:
            moment = datetime.fromisoformat(stamp)
            entry = sums.setdefault((building, moment.year, moment.month), [0.0, 0.0])
            entry[0 if moment.hour in PEAK_HOURS else 1] += float(kwh)
    checks = []
    for target in targets:
        peak, offpeak = sums.get((target.building_id, target.year, target.month), [0.0, 0.0])
        for name, actual, expected in (('energy', peak + offpeak, target.energy_kwh),
                                       ('peak', peak, target.peak_kwh), ('offpeak', offpeak, target.offpeak_kwh)):
            error = abs(actual - expected)
            checks.append({'target': target.label, 'quantity': name, 'expected_kwh': expected,
                           'actual_kwh': actual, 'relative_error': error/abs(expected) if expected else None,
                           'passed': error <= rtol*abs(expected) + 1e-6, 'provenance': target.provenance})
    return checks


@dataclass(frozen=True)
class DatasetBuildConfig:
    campaign_id: str
    years: Tuple[int, ...]
    buildings: Tuple[int, ...]
    generation_seed: int
    currency: str
    time_zone: str
    parameters: Mapping[str, object] = field(default_factory=dict)

    def as_dict(self):
        return {'campaign_id': self.campaign_id, 'years': list(self.years), 'buildings': list(self.buildings),
                'generation_seed': self.generation_seed, 'currency': self.currency,
                'time_zone': self.time_zone, 'parameters': dict(self.parameters)}

    def config_hash(self) -> str:
        body = json.dumps(self.as_dict(), sort_keys=True, separators=(',', ':'), default=str)
        return hashlib.sha256(body.encode('utf-8')).hexdigest()


@dataclass(frozen=True)
class GeneratorRequest:
    output_dir: Path
    buildings: Tuple[int, ...]
    years: Tuple[int, ...]
    generation_seed: int
    targets_path: Path
    parameters: Mapping[str, object]


@dataclass(frozen=True)
class DatasetBuildManifest:
    campaign_id: str
    source_hashes: str
    generator_hash: str
    config_hash: str
    files: Mapping[str, str]
    dataset_hash: str
    quality_flags_path: str
    balance_checks: Tuple[Mapping[str, object], ...]
    limitations: Tuple[str, ...]
    generated_at: str

    def as_dict(self):
        return {'schema_version': 1, 'campaign_id': self.campaign_id, 'source_hashes': self.source_hashes,
                'generator_hash': self.generator_hash, 'config_hash': self.config_hash,
                'files': dict(self.files), 'dataset_hash': self.dataset_hash,
                'quality_flags_path': self.quality_flags_path,
                'balance_checks': [dict(c) for c in self.balance_checks],
                'limitations': list(self.limitations), 'generated_at': self.generated_at}


def hash_directory(root: Path) -> Tuple[Dict[str, str], str]:
    root = contained_path(Path(root), '.')
    files = {}
    # os.walk without following links still lists junctions/symlinks. Validate
    # every listed entry before descending or reading a linked regular file.
    paths = []
    for directory, dirs, names in os.walk(root, followlinks=False):
        for name in sorted(dirs + names):
            path = contained_path(root, (Path(directory)/name).relative_to(root).as_posix())
            if path.is_file():
                paths.append(path)
    for path in sorted(paths):
        path = contained_path(root, path.relative_to(root).as_posix())
        if path.is_file():
            payload = path.read_bytes()
            if path.suffix.casefold() in {'.csv', '.json', '.txt'}:
                payload = payload.replace(b'\r\n', b'\n')
            files[path.relative_to(root).as_posix()] = hashlib.sha256(payload).hexdigest()
    body = json.dumps(files, sort_keys=True, separators=(',', ':'))
    return files, hashlib.sha256(body.encode('utf-8')).hexdigest()


def build_dataset(sources: RawSourceManifest, config: DatasetBuildConfig, output_dir: Path, *,
                  project_root: Path, generator: Callable[[GeneratorRequest], None],
                  targets: Sequence[MonthlyRecord], generator_hash: str = '',
                  balance: Optional[Callable[[Path, Sequence[MonthlyRecord]], Sequence[Mapping]]] = None,
                  limitations: Sequence[str] = ()) -> DatasetBuildManifest:
    """Generate a new frozen dataset into a campaign root, never into a dependency."""
    root = Path(os.path.abspath(project_root))
    output = Path(os.path.abspath(output_dir))
    try:
        relative = output.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError(f'dataset output must live inside the project root: {output}') from exc
    output = contained_path(root, relative)
    components = tuple(part.casefold() for part in output.relative_to(root.resolve()).parts)
    if len(components) < 3 or components[:2] != ('data', 'campaigns'):
        raise ValueError(f'{relative}: a fresh dataset is written only under data/campaigns/<campaign>/')
    if output.exists():
        raise FileExistsError(f'{relative} already exists; a built dataset is never overwritten')
    output.mkdir(parents=True)
    output = contained_path(root, relative)
    targets_path = output/'monthly_targets.csv'
    write_monthly_targets(targets_path, targets)
    generator(GeneratorRequest(output, tuple(config.buildings), tuple(config.years),
                               config.generation_seed, targets_path, dict(config.parameters)))
    checks = tuple(balance(output, targets)) if balance else ()
    files, dataset_hash = hash_directory(output)
    manifest = DatasetBuildManifest(config.campaign_id, sources.manifest_hash, generator_hash,
                                    config.config_hash(), files, dataset_hash,
                                    (output.parent/'quality_flags.csv').relative_to(root).as_posix(),
                                    checks, tuple(limitations), datetime.now(timezone.utc).isoformat())
    (output.parent/'dataset_build_manifest.json').write_text(json.dumps(manifest.as_dict(), indent=2),
                                                            encoding='utf-8')
    return manifest
