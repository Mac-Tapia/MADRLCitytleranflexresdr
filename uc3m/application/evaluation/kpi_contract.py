"""KPI of the fresh campaign computed from physical traces, with checked units.

The trace (per step, per building) is the only source: aggregated scalars of
native reports and the estimated UC3M evaluator are not inputs. Missing data is
reported as unavailable with its cause, never as zero. Deltas are
``control - baseline``; gains of minimized quantities are
``(baseline - control) / |baseline|`` and are undefined for a zero baseline.

Conventions (project derivations, not standards):
- district power is the coincident sum of building net power before any peak;
  flexibility treats it as bidirectional: daily peak of |P|, ramp of |dP| and
  load factor 1 - mean(|P|)/max(|P|), so an injection peak counts like an
  import peak (the isolated grid must absorb it);
- net billing (owner decision 2026-11-01): cost = building net consumption x
  price, export credited at the purchase price; CO2 = building net consumption
  x carbon intensity, exported energy displaces thermal generation (negative);
  the same convention as citylearn.v3.reward (fresh_kpi_aligned_v6_net_billing);
- throughput and export are exposures, without a gain.
"""
from __future__ import annotations

import math
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Mapping, Optional, Sequence, Tuple

import yaml

from uc3m.domain.campaigns import canonical_hash

SENSES = ('minimize', 'maximize', 'exposure')
WINDOWS = ('total', 'daily', 'episode')
AGGREGATIONS = ('sum', 'mean', 'daily_mean')
BASE_UNITS = {'net_power': 'kW', 'carbon_intensity': 'kgCO2/kWh', 'battery_throughput': 'kWh'}


def _check_series(name, values, length):
    values = tuple(values)
    if len(values) != length:
        raise ValueError(f'series {name} has {len(values)} steps, expected {length}')
    for value in values:
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise ValueError(f'series {name} contains a non-finite or non-numeric value: {value!r}')
    return tuple(float(v) for v in values)


@dataclass(frozen=True)
class PhysicalTrace:
    timestamps: Tuple[str, ...]
    seconds_per_step: int
    building_ids: Tuple[str, ...]
    series_by_building: Mapping[str, Mapping[str, Sequence[float]]]
    district_series: Mapping[str, Sequence[float]]
    units: Mapping[str, str]
    currency: str
    currency_provenance: str
    exogenous_hash: str

    def __post_init__(self) -> None:
        length = len(self.timestamps)
        if length == 0 or self.seconds_per_step <= 0:
            raise ValueError('a trace needs steps and a positive step duration')
        if not self.currency or not self.currency_provenance:
            raise ValueError('currency and its provenance are required')
        expected = dict(BASE_UNITS, price=f'{self.currency}/kWh')
        for name, unit in self.units.items():
            if name in expected and unit != expected[name]:
                raise ValueError(f'unit of {name} must be {expected[name]}, got {unit}')
        if set(self.series_by_building) != set(self.building_ids):
            raise ValueError('series_by_building must cover exactly building_ids')
        buildings = {}
        for building in self.building_ids:
            buildings[building] = {name: _check_series(f'{building}.{name}', values, length)
                                   for name, values in self.series_by_building[building].items()}
            for name in buildings[building]:
                if name not in self.units:
                    raise ValueError(f'series {name} has no declared unit')
        district = {name: _check_series(name, values, length) for name, values in self.district_series.items()}
        object.__setattr__(self, 'timestamps', tuple(self.timestamps))
        object.__setattr__(self, 'building_ids', tuple(self.building_ids))
        object.__setattr__(self, 'series_by_building', buildings)
        object.__setattr__(self, 'district_series', district)

    @property
    def hours_per_step(self) -> float:
        return self.seconds_per_step/3600.0

    def as_dict(self):
        return {'timestamps': list(self.timestamps), 'seconds_per_step': self.seconds_per_step,
                'building_ids': list(self.building_ids),
                'series_by_building': {b: {k: list(v) for k, v in s.items()}
                                       for b, s in self.series_by_building.items()},
                'district_series': {k: list(v) for k, v in self.district_series.items()},
                'units': dict(self.units), 'currency': self.currency,
                'currency_provenance': self.currency_provenance,
                'exogenous_hash': self.exogenous_hash}

    def trace_hash(self) -> str:
        return canonical_hash(self.as_dict())


@dataclass(frozen=True)
class KpiDefinition:
    name: str
    quantity: str
    unit: str
    sense: str
    level: str
    window: str
    aggregation: Optional[str] = None
    axis: Optional[str] = None
    primary: bool = False
    provenance: str = 'trace'
    convention: str = 'project_derivation'
    # The CityLearn v3 KPI (configs/evaluation/kpis.yaml citylearn_v3_kpis) this
    # physical-trace value cross-checks; the trace is a verification, not a catalog.
    citylearn_v3_name: Optional[str] = None

    def __post_init__(self) -> None:
        if self.sense not in SENSES or self.window not in WINDOWS:
            raise ValueError(f'{self.name}: invalid sense or window')
        aggregation = self.aggregation or {'total': 'sum', 'daily': 'daily_mean', 'episode': 'mean'}[self.window]
        if aggregation not in AGGREGATIONS:
            raise ValueError(f'{self.name}: invalid aggregation')
        if self.window == 'total' and aggregation != 'sum':
            raise ValueError(f'{self.name}: a total is a sum over the window, never a mean of daily values')
        if self.provenance != 'trace':
            raise ValueError(f'{self.name}: only trace-derived KPI are accepted, not {self.provenance}')
        if self.primary and self.sense == 'exposure':
            raise ValueError(f'{self.name}: an exposure cannot be a primary endpoint')
        object.__setattr__(self, 'aggregation', aggregation)


@dataclass(frozen=True)
class KpiCatalog:
    definitions: Tuple[KpiDefinition, ...]
    primary_endpoints: Tuple[str, ...]
    axes: Mapping[str, Tuple[str, ...]]
    currency: str
    balance_atol: float = 1e-6
    balance_rtol: float = 1e-6

    def __post_init__(self) -> None:
        names = [d.name for d in self.definitions]
        if len(names) != len(set(names)):
            raise ValueError('duplicate KPI names in catalog')
        by_name = {d.name: d for d in self.definitions}
        if set(self.primary_endpoints) != {d.name for d in self.definitions if d.primary}:
            raise ValueError('primary_endpoints must list exactly the primary definitions')
        for axis, members in self.axes.items():
            if any(by_name.get(m) is None or by_name[m].axis != axis or not by_name[m].primary
                   for m in members):
                raise ValueError(f'axis {axis} must group primary definitions declared on it')

    def by_name(self) -> Dict[str, KpiDefinition]:
        return {d.name: d for d in self.definitions}


def load_citylearn_v3_kpis(path: Path) -> Tuple[Mapping[str, object], ...]:
    """The CityLearn v3 KPI list of the catalog (names, axes, senses, ratio_to_baseline)."""
    payload = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    return tuple(payload.get('citylearn_v3_kpis') or ())


def load_thesis_indicators(path: Path) -> Tuple[Mapping[str, object], ...]:
    """Layer A of the catalog: the thesis indicators (3 axes x 3 dimensions and pending extras)."""
    payload = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    return tuple(payload.get('thesis_indicators') or ())


def _ratio_or_none(value, base):
    if value is None or base is None or base == 0:
        return None
    return value/base


def thesis_indicator_values(values: Mapping[str, Mapping[str, object]],
                            indicators: Sequence[Mapping[str, object]]) -> List[Dict[str, object]]:
    """Layer A values from the trace cross-check entries; pending indicators stay None with their status."""
    rows, ratios = [], {}
    for indicator in indicators:
        source = indicator.get('value_from') or ''
        value = baseline = None
        if source.startswith('trace:'):
            name = source[len('trace:'):]
            delta = name.endswith('.delta')
            entry = values.get(name[:-len('.delta')] if delta else name) or {}
            control, base = entry.get('value'), entry.get('baseline')
            if delta:
                value, baseline = entry.get('delta'), 0.0 if entry.get('delta') is not None else None
            elif indicator['axis'] == 'flexibility':
                value, baseline = _ratio_or_none(control, base), 1.0      # CityLearn ratio to baseline
                ratios[indicator['name']] = value
            else:
                value, baseline = control, base
        elif source == 'derived:layer_a_ratios':
            parts = [ratios.get(n) for n in ('peak_average', 'ramping_average', 'one_minus_load_factor_average')]
            value, baseline = (None, None) if any(v is None for v in parts) else (sum(parts)/3.0, 1.0)
        rows.append({'name': indicator['name'], 'axis': indicator['axis'], 'dimension': indicator.get('dimension'),
                     'value': value, 'baseline': baseline, 'available': value is not None,
                     'definition_status': indicator.get('definition_status'), 'source': indicator.get('source')})
    return rows


DEFAULT_CATALOG = Path(__file__).resolve().parents[3]/'configs/evaluation/kpis.yaml'
AXIS_OF_OBJECTIVE = {'OE1': 'flexibility', 'OE2': 'co2_emissions', 'OE3': 'energy_cost'}


def _paired_baseline_name(name: str) -> Optional[str]:
    for control, baseline in (('_daily_average_control', '_daily_average_baseline'), ('_control', '_baseline')):
        if name.endswith(control):
            return name[:-len(control)] + baseline
    return None


def comparable_kpi_names(catalog_path: Path = DEFAULT_CATALOG) -> Dict[str, Tuple[str, Tuple[str, ...]]]:
    """axis -> (scenario, names) of the structurally comparable CityLearn v3 KPIs.

    Read from the catalog (citylearn_v3_kpis, objective_scenarios), which copies
    citylearn/v3/objectives.py 1:1; the rule mirrors objectives._baseline_for and
    tests/fresh_training/test_kpi_catalog_complete.py fixes both against CityLearn:
    a *_control twin with its *_baseline, a *_delta (baseline 0), a ratio to the
    baseline (baseline 1) or price_signal_deviation (its baseline); *_baseline excluded.
    """
    payload = yaml.safe_load(Path(catalog_path).read_text(encoding='utf-8'))
    rows = payload.get('citylearn_v3_kpis') or ()
    scenarios = payload['objective_scenarios']
    names = {row['name'] for row in rows} | {'price_signal_deviation_baseline'}
    out = {}
    for objective, axis in AXIS_OF_OBJECTIVE.items():
        kept = []
        for row in rows:
            name = row['name']
            if row['objective'] != objective or name.endswith('_baseline'):
                continue
            paired = _paired_baseline_name(name)
            if ((paired is not None and paired in names) or name.endswith('_delta') or row.get('ratio_to_baseline')
                    or name == 'price_signal_deviation'):
                kept.append(name)
        out[axis] = (scenarios[objective], tuple(kept))
    return out


def lower_is_better(name: str, catalog_path: Path = DEFAULT_CATALOG) -> bool:
    payload = yaml.safe_load(Path(catalog_path).read_text(encoding='utf-8'))
    sense = {row['name']: row.get('sense') for row in payload.get('citylearn_v3_kpis') or ()}
    return sense.get(name) != 'maximize'


def oriented_gain(value, baseline, lower_is_better):
    """tools/eval/objective_analysis.py objective_kpi_rows: KPI-gain orientado (positive favours the policy)."""
    delta = value - baseline
    signed = -delta if lower_is_better else delta
    denominator = abs(baseline)
    if denominator < 1.0e-12:
        denominator = max(abs(value), 1.0)
    return signed/denominator


def comparable_kpi_gain_rows(objectives_report: Optional[Mapping[str, object]]) -> List[Dict[str, object]]:
    """kpi_report.json ``comparable_kpi_gains``: one row per comparable CityLearn v3 KPI.

    Row format: {name, axis, value, baseline, lower_is_better, gain, available}, values from
    ``citylearn.v3.objectives.evaluate_objectives(env)``; a KPI without a value in the run
    stays in the list with available false and gain None.
    """
    axis_code = {axis: objective for objective, axis in AXIS_OF_OBJECTIVE.items()}
    axes = (objectives_report or {}).get('axes') or {}
    rows = []
    for axis, (_, names) in comparable_kpi_names().items():
        for name in names:
            item = ((axes.get(axis_code[axis]) or {}).get('kpis') or {}).get(name) or {}
            comparison = item.get('comparison') or {}
            value, baseline = item.get('value'), comparison.get('baseline')
            finite = all(isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(v)
                         for v in (value, baseline))
            available = bool(comparison.get('available')) and finite
            lower = lower_is_better(name)
            rows.append({'name': name, 'axis': axis, 'value': value if finite else None,
                         'baseline': baseline if finite else None, 'lower_is_better': lower,
                         'gain': oriented_gain(float(value), float(baseline), lower) if available else None,
                         'available': available})
    return rows


def load_kpi_catalog(path: Path) -> KpiCatalog:
    payload = yaml.safe_load(Path(path).read_text(encoding='utf-8'))
    if payload.get('schema_version') != 1:
        raise ValueError('unsupported KPI catalog schema_version')
    tolerances = payload.get('tolerances', {})
    return KpiCatalog(tuple(KpiDefinition(**item) for item in payload['definitions']),
                      tuple(payload['primary_endpoints']),
                      {axis: tuple(members) for axis, members in payload['axes'].items()},
                      payload['currency'], float(tolerances.get('balance_atol', 1e-6)),
                      float(tolerances.get('balance_rtol', 1e-6)))


@dataclass(frozen=True)
class KpiReport:
    context: Mapping[str, object]
    values: Mapping[str, Mapping[str, object]]
    trace_hash: str
    baseline_trace_hash: str
    balance_checks: Mapping[str, Mapping[str, object]]
    axis_gains: Mapping[str, Optional[float]] = field(default_factory=dict)
    thesis_indicators: Tuple[Mapping[str, object], ...] = ()
    comparable_kpi_gains: Tuple[Mapping[str, object], ...] = ()

    def as_dict(self):
        return {'schema_version': 1, 'context': dict(self.context),
                'thesis_indicators': [dict(row) for row in self.thesis_indicators],
                'comparable_kpi_gains': [dict(row) for row in self.comparable_kpi_gains],
                'values': {k: dict(v) for k, v in self.values.items()},
                'trace_hash': self.trace_hash, 'baseline_trace_hash': self.baseline_trace_hash,
                'balance_checks': {k: dict(v) for k, v in self.balance_checks.items()},
                'axis_gains': dict(self.axis_gains)}


@dataclass(frozen=True)
class ValidationResult:
    passed: bool
    checks: Tuple[str, ...]
    reasons: Tuple[str, ...]


class _Unavailable(Exception):
    def __init__(self, cause):
        super().__init__(cause)
        self.cause = cause


def _district_power(trace: PhysicalTrace) -> List[float]:
    return [sum(trace.series_by_building[b]['net_power'][t] for b in trace.building_ids)
            for t in range(len(trace.timestamps))]


def _require(trace: PhysicalTrace, name: str, district=False):
    if district:
        if name not in trace.district_series:
            raise _Unavailable(f'missing_series:{name}')
        return trace.district_series[name]
    if any(name not in trace.series_by_building[b] for b in trace.building_ids):
        raise _Unavailable(f'missing_series:{name}')
    return {b: trace.series_by_building[b][name] for b in trace.building_ids}


def _days(trace: PhysicalTrace) -> List[List[int]]:
    per_day = 86400/trace.seconds_per_step
    if per_day != int(per_day):
        raise _Unavailable('step_does_not_divide_day')
    groups: 'OrderedDict[str, List[int]]' = OrderedDict()
    for index, stamp in enumerate(trace.timestamps):
        groups.setdefault(datetime.fromisoformat(stamp).date().isoformat(), []).append(index)
    days = list(groups.values())
    if any(len(day) != int(per_day) for day in days):
        raise _Unavailable('incomplete_days')
    return days


def _quantity(trace: PhysicalTrace, quantity: str) -> float:
    _require(trace, 'net_power')
    dt = trace.hours_per_step
    power = {b: trace.series_by_building[b]['net_power'] for b in trace.building_ids}
    if quantity == 'district_daily_peak':
        district = _district_power(trace)
        days = _days(trace)
        return sum(max(abs(district[i]) for i in day) for day in days)/len(days)
    if quantity == 'district_ramping':
        district = _district_power(trace)
        if len(district) < 2:
            raise _Unavailable('single_step')
        return sum(abs(b - a) for a, b in zip(district, district[1:]))/(len(district) - 1)/dt
    if quantity == 'one_minus_load_factor':
        district = _district_power(trace)
        values = []
        for day in _days(trace):
            peak = max(abs(district[i]) for i in day)
            if peak <= 0:
                raise _Unavailable('non_positive_daily_peak')
            values.append(1 - (sum(abs(district[i]) for i in day)/len(day))/peak)
        return sum(values)/len(values)
    if quantity == 'co2_emissions':
        intensity = _require(trace, 'carbon_intensity', district=True)
        return sum(p[t]*intensity[t]*dt for p in power.values() for t in range(len(intensity)))
    if quantity == 'energy_cost':
        price = _require(trace, 'price', district=True)
        return sum(p[t]*price[t]*dt for p in power.values() for t in range(len(price)))
    if quantity == 'ci_weighted_import':
        intensity = _require(trace, 'carbon_intensity', district=True)
        return sum(max(p[t], 0.0)*intensity[t]*dt for p in power.values() for t in range(len(intensity)))
    if quantity == 'price_signal_deviation':   # CityLearn v3 formula: injected as an extra measure
        raise _Unavailable('requires_injected_citylearn_rule')
    if quantity == 'import_energy':
        return sum(max(v, 0.0)*dt for p in power.values() for v in p)
    if quantity == 'export_energy':
        return sum(max(-v, 0.0)*dt for p in power.values() for v in p)
    if quantity == 'battery_throughput':
        return sum(sum(series) for series in _require(trace, 'battery_throughput').values())
    raise ValueError(f'unknown KPI quantity: {quantity}')


def _measure(trace, definition, extra_measures=None):
    measure = (extra_measures or {}).get(definition.quantity)
    if measure is not None:
        value = measure(trace)
        return (None, f'{definition.quantity}_undefined') if value is None else (float(value), None)
    try:
        return _quantity(trace, definition.quantity), None
    except _Unavailable as missing:
        return None, missing.cause


def _energy_balance(trace: PhysicalTrace, catalog: KpiCatalog):
    dt = trace.hours_per_step
    values = [v for b in trace.building_ids for v in trace.series_by_building[b]['net_power']]
    imported = sum(max(v, 0.0) for v in values)*dt
    exported = sum(max(-v, 0.0) for v in values)*dt
    net = sum(values)*dt
    magnitude = max(abs(imported), abs(exported), abs(net))
    passed = abs((imported - exported) - net) <= catalog.balance_atol + catalog.balance_rtol*magnitude
    return {'import_minus_export_kwh': imported - exported, 'net_kwh': net, 'passed': passed}


def compute_fresh_kpis(trace: PhysicalTrace, baseline: PhysicalTrace, catalog: KpiCatalog,
                       context: Optional[Mapping[str, object]] = None, *,
                       thesis_indicators: Optional[Sequence[Mapping[str, object]]] = None,
                       citylearn_v3_report: Optional[Mapping[str, object]] = None,
                       extra_measures: Optional[Mapping[str, object]] = None) -> KpiReport:
    """Trace cross-check, Layer A thesis indicators and Layer B CityLearn v3 KPI-gains.

    ``citylearn_v3_report`` is ``citylearn.v3.objectives.evaluate_objectives(env)`` of the
    control run; without it every Layer B row is reported unavailable, never dropped.
    """
    for item in (trace, baseline):
        if item.currency != catalog.currency:
            raise ValueError(f'trace currency {item.currency} differs from catalog {catalog.currency}; '
                             'convert with a documented source instead of relabelling')
    if trace.seconds_per_step != baseline.seconds_per_step or trace.timestamps != baseline.timestamps:
        raise ValueError('control and baseline must cover the same window and step')
    if trace.building_ids != baseline.building_ids:
        raise ValueError('control and baseline must cover the same buildings')
    values = {}
    for definition in catalog.definitions:
        value, cause = _measure(trace, definition, extra_measures)
        base, base_cause = _measure(baseline, definition, extra_measures)
        entry = {'name': definition.name, 'value': value, 'baseline': base, 'delta': None, 'gain': None,
                 'unit': definition.unit, 'sense': definition.sense, 'level': definition.level,
                 'window': definition.window, 'aggregation': definition.aggregation,
                 'axis': definition.axis, 'primary': definition.primary,
                 'citylearn_v3_name': definition.citylearn_v3_name,
                 'provenance': 'trace', 'convention': definition.convention,
                 'availability': 'available', 'cause': None}
        if value is None:
            entry.update(availability='unavailable', cause=cause)
        elif base is None:
            entry.update(availability='undefined', cause=f'baseline_{base_cause}')
        else:
            entry['delta'] = value - base
            if definition.sense != 'exposure':
                if base == 0:
                    entry.update(availability='undefined', cause='baseline_zero')
                else:
                    sign = 1.0 if definition.sense == 'minimize' else -1.0
                    entry['gain'] = sign*(base - value)/abs(base)
        values[definition.name] = entry
    axis_gains = {}
    for axis, members in catalog.axes.items():
        gains = [values[m]['gain'] for m in members]
        axis_gains[axis] = None if any(g is None for g in gains) else sum(gains)/len(gains)
    indicators = tuple(thesis_indicator_values(values, thesis_indicators or ()))
    return KpiReport(dict(context or {}), values, trace.trace_hash(), baseline.trace_hash(),
                     {'energy': _energy_balance(trace, catalog),
                      'baseline_energy': _energy_balance(baseline, catalog)}, axis_gains,
                     indicators, tuple(comparable_kpi_gain_rows(citylearn_v3_report)))


def validate_kpi_report(report: KpiReport, catalog: KpiCatalog) -> ValidationResult:
    checks, reasons = [], []
    definitions = catalog.by_name()
    for name in catalog.primary_endpoints:
        entry = report.values.get(name)
        checks.append(f'primary:{name}')
        if entry is None:
            reasons.append(f'{name}: missing from report')
            continue
        if entry.get('provenance') != 'trace':
            reasons.append(f'{name}: provenance {entry.get("provenance")} is not a trace')
        if entry.get('unit') != definitions[name].unit:
            reasons.append(f'{name}: unit {entry.get("unit")} differs from {definitions[name].unit}')
        if entry.get('availability') == 'unavailable':
            reasons.append(f'{name}: unavailable ({entry.get("cause")})')
        value = entry.get('value')
        if value is not None and (isinstance(value, bool) or not math.isfinite(value)):
            reasons.append(f'{name}: non-finite value')
    for label, balance in report.balance_checks.items():
        checks.append(f'balance:{label}')
        if not balance.get('passed'):
            reasons.append(f'{label}: energy balance does not close')
    return ValidationResult(not reasons, tuple(checks), tuple(reasons))
