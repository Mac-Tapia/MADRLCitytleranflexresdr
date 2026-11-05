"""Seed-level statistics of the fresh campaign (design section 8).

The replication unit is one independent training per seed: hours, buildings,
episodes or different KPI never add replicas. Endpoints are the axis gains of
their own scenario (flexibility in E1, CO2 in E2, cost in E3). Families are
fixed in advance: 3 Friedman omnibus tests, 18 paired Wilcoxon post hoc
comparisons (6 pairs x 3 axes) and 12 one-sample contrasts against the fresh
RBC baseline (4 algorithms x 3 axes), each with its own Holm correction.
A complete study with no detected difference is scientifically complete.
"""
from __future__ import annotations

import itertools
import math
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import numpy as np

ROW_KEYS = {'campaign_id', 'algorithm', 'scenario', 'seed', 'split', 'endpoint', 'value', 'kpi_report_sha256'}
HV_REFERENCE = (-1.0, -1.0, -1.0)
AXES = ('flexibility', 'co2_emissions', 'energy_cost')


OBJECTIVE_OF_AXIS = {'flexibility': 'OE1', 'co2_emissions': 'OE2', 'energy_cost': 'OE3'}


def comparable_kpis() -> Dict[str, Tuple[str, Tuple[str, ...]]]:
    """axis -> (scenario, KPI names with a comparable baseline): 12/5/9 = 26 for CityLearn v3.

    The single derivation is kpi_contract.comparable_kpi_names (catalog copy of
    citylearn/v3/objectives.py, fixed against CityLearn by test_kpi_catalog_complete).
    """
    from uc3m.application.evaluation.kpi_contract import comparable_kpi_names
    return comparable_kpi_names()


def rows_from_kpi_report(report: Mapping[str, object], *, report_sha256: str) -> List[Dict[str, object]]:
    """Seed rows of one fresh KPI report: the axis gain and every comparable KPI gain of the
    objective formulated for the report's scenario (OE1/E1, OE2/E2, OE3/E3)."""
    context = report['context']
    base = {'campaign_id': context['campaign_id'], 'algorithm': context['algorithm'],
            'scenario': context['scenario'], 'seed': int(context['seed']), 'split': context['split'],
            'kpi_report_sha256': report_sha256}
    gains = {row['name']: row for row in report.get('comparable_kpi_gains') or []}
    rows = []
    for axis, (scenario, kpis) in comparable_kpis().items():
        if scenario != context['scenario']:
            continue
        rows.append(dict(base, endpoint=axis, value=(report.get('axis_gains') or {}).get(axis)))
        for kpi in kpis:
            item = gains.get(kpi) or {}
            rows.append(dict(base, endpoint=kpi, value=item.get('gain') if item.get('available') else None))
    return rows


@dataclass(frozen=True)
class SeedTable:
    rows: Tuple[Mapping[str, object], ...]

    @classmethod
    def from_rows(cls, rows: Iterable[Mapping[str, object]]) -> 'SeedTable':
        rows = [dict(r) for r in rows]
        seen = set()
        for row in rows:
            if set(row) != ROW_KEYS:
                raise ValueError(f'a seed row has exactly {sorted(ROW_KEYS)}; got {sorted(row)}')
            value = row['value']
            if value is not None and (isinstance(value, bool) or not isinstance(value, (int, float))
                                      or not math.isfinite(float(value))):
                raise ValueError(f'seed row value must be a finite real or None (missing); got {value!r}')
            seed = row['seed']
            if isinstance(seed, bool) or not isinstance(seed, int) or seed <= 0:
                raise ValueError(f'seed must be a positive integer; got {seed!r}')
            digest = row['kpi_report_sha256']
            if not (isinstance(digest, str) and len(digest) == 64 and all(c in '0123456789abcdef' for c in digest)):
                raise ValueError(f'kpi_report_sha256 must be a lowercase SHA-256 digest; got {digest!r}')
            key = (row['campaign_id'], row['algorithm'], row['scenario'], row['seed'], row['split'], row['endpoint'])
            if key in seen:
                raise ValueError(f'duplicate seed row {key}')
            seen.add(key)
        if len({r['campaign_id'] for r in rows}) > 1:
            raise ValueError('a seed table never mixes campaigns')
        return cls(tuple(rows))

    def values(self, algorithm, scenario, endpoint, split='validation_2024') -> Dict[int, Optional[float]]:
        return {int(r['seed']): r['value'] for r in self.rows if r['algorithm'] == algorithm
                and r['scenario'] == scenario and r['endpoint'] == endpoint and r['split'] == split}

    def n_seeds(self, algorithm, scenario, endpoint, split='validation_2024') -> int:
        return sum(1 for v in self.values(algorithm, scenario, endpoint, split).values() if v is not None)


def iqm(values: Sequence[float]) -> float:
    """Interquartile mean with fractional weights at the 25 % and 75 % cuts."""
    data = sorted(float(v) for v in values)
    n = len(data)
    cut = 0.25*n
    weights = []
    for i in range(n):
        lo, hi = max(i, cut), min(i + 1, n - cut)
        weights.append(max(0.0, hi - lo))
    return sum(w*x for w, x in zip(weights, data))/sum(weights)


def _statistic(name):
    return {'mean': np.mean, 'median': np.median, 'iqm': iqm}[name]


def bootstrap_ci(values: Sequence[float], *, statistic='mean', resamples=10000, seed=7001, level=0.95):
    """Percentile CI resampling whole seeds (blocks), never hours or episodes."""
    data = np.asarray(values, dtype=float)
    if (data.ndim != 1 or not data.size or not np.all(np.isfinite(data))
            or type(resamples) is not int or resamples <= 0
            or isinstance(level, bool) or not isinstance(level, (int, float)) or not 0 < level < 1
            or statistic not in ('mean', 'median', 'iqm')):
        raise ValueError('invalid finite seed vector or confidence protocol')
    rng = np.random.default_rng(seed)
    # Same seed draws and percentile rule as the scalar reference; bounded
    # batches avoid 10,000 Python/NumPy calls for every endpoint/algorithm.
    draws = np.empty(resamples, dtype=float)
    batch = max(1, min(resamples, 1_000_000//data.size))
    n = data.size
    indices = np.arange(n, dtype=float)
    cut = 0.25*n
    weights = np.maximum(0.0, np.minimum(indices+1, n-cut)-np.maximum(indices, cut))
    for start in range(0, resamples, batch):
        stop = min(resamples, start+batch)
        samples = data[rng.integers(0, n, size=(stop-start, n))]
        if statistic == 'mean':
            draws[start:stop] = np.mean(samples, axis=1)
        elif statistic == 'median':
            draws[start:stop] = np.median(samples, axis=1)
        else:
            draws[start:stop] = np.sum(np.sort(samples, axis=1)*weights, axis=1)/weights.sum()
    alpha = (1 - level)/2
    return float(np.quantile(draws, alpha)), float(np.quantile(draws, 1 - alpha))


def holm(p_values: Sequence[Optional[float]]) -> List[Optional[float]]:
    indexed = [(p, i) for i, p in enumerate(p_values) if p is not None]
    adjusted: List[Optional[float]] = [None]*len(p_values)
    running = 0.0
    m = len(indexed)
    for rank, (p, i) in enumerate(sorted(indexed)):
        running = max(running, min(1.0, (m - rank)*p))
        adjusted[i] = running
    return adjusted


def clip_gains(gains: Sequence[float]):
    clipped = tuple(min(1.0, max(-1.0, float(g))) for g in gains)
    saturated = tuple(AXES[i] for i, (a, b) in enumerate(zip(gains, clipped)) if a != b)
    return clipped, saturated


def hypervolume(points: Sequence[Sequence[float]], reference=HV_REFERENCE) -> float:
    """Exact 3-D hypervolume (maximization) of the union of boxes [reference, point]."""
    boxes = [tuple(max(r, p) for r, p in zip(reference, clip_gains(point)[0])) for point in points]
    grids = [sorted({reference[d]} | {b[d] for b in boxes}) for d in range(3)]
    volume = 0.0
    for i, j, k in itertools.product(*(range(len(g) - 1) for g in grids)):
        cell = (grids[0][i + 1], grids[1][j + 1], grids[2][k + 1])
        if any(all(cell[d] <= b[d] for d in range(3)) for b in boxes):
            volume += ((grids[0][i + 1] - grids[0][i])*(grids[1][j + 1] - grids[1][j])*(grids[2][k + 1] - grids[2][k]))
    return volume


@dataclass(frozen=True)
class FrozenProtocol:
    algorithms: Tuple[str, ...]
    seeds: Tuple[int, ...]
    endpoints: Tuple[Tuple[str, str], ...]   # (scenario, axis or KPI): every analysed endpoint
    split: str
    alpha: float
    resamples: int
    bootstrap_seed: int
    topsis_weights: Tuple[float, float, float]
    # The confirmatory families of the plan (3 omnibus, 18 pairs, 12 versus RBC) use the axis
    # endpoints; every comparable KPI is analysed in its own per-objective families.
    confirmatory_endpoints: Tuple[Tuple[str, str], ...] = (('E1', 'flexibility'), ('E2', 'co2_emissions'),
                                                           ('E3', 'energy_cost'))
    not_applicable_endpoints: Tuple[Tuple[str, str], ...] = ()

    @classmethod
    def default(cls) -> 'FrozenProtocol':
        kpi_endpoints = tuple((scenario, kpi) for scenario, kpis in comparable_kpis().values() for kpi in kpis)
        axes = (('E1', 'flexibility'), ('E2', 'co2_emissions'), ('E3', 'energy_cost'))
        return cls(('HAPPO', 'MASAC', 'MATD3', 'MAAC'), tuple(range(1001, 1013)), axes + kpi_endpoints,
                   'validation_2024', 0.05, 10000, 7001, (1/3, 1/3, 1/3), axes)


@dataclass
class ScientificReport:
    coverage: Dict[str, object]
    seed_statistics: List[Dict[str, object]] = field(default_factory=list)
    test_families: Dict[str, List[Dict[str, object]]] = field(default_factory=dict)
    decisions: Dict[str, object] = field(default_factory=dict)
    limitations: List[str] = field(default_factory=list)
    kpi_families: Dict[str, Dict[str, List[Dict[str, object]]]] = field(default_factory=dict)
    battery: List[Dict[str, object]] = field(default_factory=list)

    def as_dict(self):
        return {'schema_version': 1, 'coverage': self.coverage, 'seed_statistics': self.seed_statistics,
                'test_families': self.test_families, 'kpi_families': self.kpi_families, 'battery': self.battery,
                'decisions': self.decisions, 'limitations': self.limitations}


def kendall_w(matrix) -> Optional[float]:
    """Kendall's W of a seeds x algorithms matrix (concordance of the Friedman ranks)."""
    from scipy.stats import rankdata
    data = np.asarray(matrix, dtype=float)
    if data.ndim != 2 or not np.all(np.isfinite(data)):
        raise ValueError('Kendall W requires a finite seeds x algorithms matrix')
    n, k = data.shape
    if n < 2 or k < 2 or np.all(data == data.flat[0]):
        return 0.0
    ranks = np.apply_along_axis(rankdata, 1, data)
    spread = np.sum((ranks.sum(axis=0) - n*(k + 1)/2.0)**2)
    # Each tied group of size t reduces the available rank variation by t^3-t.
    # This gives W = corrected Friedman chi-square / (n*(k-1)).
    ties = 0
    for row in data:
        counts = np.unique(row, return_counts=True)[1]
        ties += int(np.sum(counts**3 - counts))
    denominator = n**2*(k**3 - k) - n*ties
    if denominator == 0:  # every seed ties all algorithms, even at different levels
        return 0.0
    return float(12.0*spread/denominator)


def describe(values) -> Dict[str, object]:
    """Descriptive statistics of one algorithm's seed values (seeds are the replicas)."""
    from scipy import stats
    x = np.asarray(values, dtype=float)
    if x.ndim != 1 or not x.size or not np.all(np.isfinite(x)):
        raise ValueError('descriptive statistics require a nonempty finite vector')
    q1, median, q3 = (float(v) for v in np.percentile(x, [25, 50, 75]))
    mean = float(np.mean(x))
    std = float(np.std(x, ddof=1)) if x.size > 1 else None
    constant = bool(np.all(x == x[0]))
    return {'n': int(x.size), 'mean': mean, 'median': median, 'std': std,
            'variance': float(np.var(x, ddof=1)) if x.size > 1 else None,
            'uncertainty_status': 'estimated' if x.size > 1 else 'insufficient_replicas',
            'min': float(np.min(x)), 'max': float(np.max(x)), 'q1': q1, 'q3': q3, 'iqr': q3 - q1,
            'cv': std/abs(mean) if std is not None and abs(mean) > 1e-12 else None,
            'skewness': None if constant else float(stats.skew(x, bias=False)),
            'kurtosis_excess': None if constant else float(stats.kurtosis(x, bias=False)),
            'iqm': iqm(x)}


def normality(values) -> Dict[str, object]:
    """Normality of one algorithm's seed values: Shapiro-Wilk (thesis), Anderson-Darling and
    D'Agostino-Pearson K2 (complementary). Informative only: inference is non-parametric."""
    from scipy import stats
    x = np.asarray(values, dtype=float)
    if x.size < 3 or np.all(x == x[0]):
        return {'status': 'not_testable', 'reason': 'fewer than 3 values or constant'}
    shapiro = stats.shapiro(x)
    anderson = stats.anderson(x, dist='norm')
    out = {'status': 'ok', 'shapiro_wilk': {'statistic': float(shapiro.statistic), 'p_value': float(shapiro.pvalue)},
           'anderson_darling': {'statistic': float(anderson.statistic),
                                'critical_values': [float(v) for v in anderson.critical_values],
                                'significance_levels_pct': [float(v) for v in anderson.significance_level]}}
    if x.size >= 8:
        k2 = stats.normaltest(x)
        out['dagostino_pearson'] = {'statistic': float(k2.statistic), 'p_value': float(k2.pvalue),
                                    'note': 'kurtosis test is approximate for n < 20'}
    return out


def nonparametric_battery(matrix, algorithms, seeds, *, alpha: float) -> Dict[str, object]:
    """The project's full non-parametric battery (uc3m.multicriteria.stats_tests), one canonical
    implementation: independent-sample view and paired seed-block view of the same values."""
    from uc3m.multicriteria import stats_tests as st
    groups = {a: [float(v) for v in matrix[:, i]] for i, a in enumerate(algorithms)}
    blocks = {f'seed_{s}': {a: float(matrix[r, i]) for i, a in enumerate(algorithms)} for r, s in enumerate(seeds)}
    independent = st.run_oe_battery(groups, higher_is_better=True, alpha=alpha, complementary=True,
                                    expected_n_seeds=len(seeds))
    paired = {'friedman': st.friedman_test(blocks, alpha=alpha, higher_is_better=True),
              'nemenyi': st.nemenyi_posthoc(blocks, alpha=alpha, higher_is_better=True),
              'quade': st.quade_test(blocks, alpha=alpha, higher_is_better=True),
              'wilcoxon_pairs': st.pairwise_wilcoxon(groups, alpha=alpha)}
    return {'independent_view': independent, 'paired_seed_blocks': paired,
            'note': 'gains are oriented (higher favours the MADRL); seeds are the replicas; '
                    'decisions use the paired Friedman/Wilcoxon families with Holm'}


def _degenerate(test, *args) -> bool:
    """The one identified case where no test is defined: no variation at all in what is compared."""
    data = [np.asarray(a, dtype=float) for a in args]
    if test == 'friedmanchisquare':   # all algorithm columns identical: every seed block is a tie
        return all(np.array_equal(data[0], column) for column in data[1:])
    if test == 'wilcoxon':
        differences = data[0] - data[1] if len(data) == 2 else data[0]
        return bool(np.all(differences == 0.0))
    return False


def _p_or_none(test, *args):
    """p-value of a SciPy test; p = 1 only for the identified degenerate case, checked on the data."""
    from scipy import stats
    if _degenerate(test, *args):
        return 1.0     # every compared value is equal: no evidence of a difference
    result = getattr(stats, test)(*args)   # any other SciPy error propagates
    p = float(result.pvalue)
    if math.isnan(p):
        raise ValueError(f'{test} returned a NaN p-value on data with real differences')
    return p


def _check_protocol(table: SeedTable, protocol: FrozenProtocol) -> None:
    endpoints = set(protocol.endpoints)
    structural_na = set(protocol.not_applicable_endpoints)
    if (not structural_na <= {('E3', 'price_signal_deviation')}
            or not structural_na <= endpoints or structural_na & set(protocol.confirmatory_endpoints)):
        raise ValueError('invalid structural endpoint inapplicability')
    for row in table.rows:
        problems = []
        if row['algorithm'] not in protocol.algorithms:
            problems.append(f"algorithm {row['algorithm']}")
        if row['seed'] not in protocol.seeds:
            problems.append(f"seed {row['seed']}")
        if row['split'] != protocol.split:
            problems.append(f"split {row['split']}")
        if (row['scenario'], row['endpoint']) not in endpoints:
            problems.append(f"endpoint {row['scenario']}/{row['endpoint']}")
        if (row['scenario'], row['endpoint']) in structural_na and row['value'] is not None:
            problems.append('a structurally undefined endpoint cannot have a numeric value')
        if problems:
            raise ValueError(f"seed row outside the frozen protocol ({', '.join(problems)}): it is not an "
                             'extra replica')


def analyze_campaign(table: SeedTable, protocol: FrozenProtocol) -> ScientificReport:
    _check_protocol(table, protocol)
    applicable = tuple(e for e in protocol.endpoints if e not in protocol.not_applicable_endpoints)
    missing = [f'{a}/{s}/seed_{seed}' for a in protocol.algorithms for s in sorted({s for s, _ in applicable})
               for seed in protocol.seeds if any(table.values(a, s, axis, protocol.split).get(seed) is None
                                                 for scen, axis in applicable if scen == s)]
    coverage = {'complete': not missing, 'missing': missing, 'expected_seeds': len(protocol.seeds),
                'replication_unit': 'independent training seed',
                'not_applicable_endpoints': [list(e) for e in protocol.not_applicable_endpoints]}
    report = ScientificReport(coverage, limitations=[
        'n=12 seeds per cell: limited power; absence of significance is not evidence of equivalence.',
        'One district and modeled climate/loads: no external geographic validation.'])
    if missing:
        report.decisions = {'scientifically_complete': False, 'algorithm_difference': 'not_evaluated',
                            'reason': 'missing treatments block acceptance'}
        return report
    from uc3m.multicriteria.stats_tests import cliffs_delta
    families = {}            # family -> {'omnibus': [...], 'pairwise': [...], 'versus_baseline': [...]}
    confirmatory = set(protocol.confirmatory_endpoints)
    kpi_family = {kpi: OBJECTIVE_OF_AXIS[axis] for axis, (_, kpis) in comparable_kpis().items() for kpi in kpis}
    batteries = []
    for scenario, endpoint in applicable:
        name = 'confirmatory' if (scenario, endpoint) in confirmatory else f'kpi_{kpi_family.get(endpoint, "other")}'
        family = families.setdefault(name, {'omnibus': [], 'pairwise': [], 'versus_baseline': []})
        matrix = np.array([[table.values(a, scenario, endpoint, protocol.split)[seed] for a in protocol.algorithms]
                           for seed in protocol.seeds], dtype=float)
        for index, algorithm in enumerate(protocol.algorithms):
            column = matrix[:, index]
            report.seed_statistics.append({
                'family': name, 'algorithm': algorithm, 'scenario': scenario, 'endpoint': endpoint,
                **describe(column), 'normality': normality(column),
                'ci95_mean': bootstrap_ci(column, statistic='mean', resamples=protocol.resamples,
                                          seed=protocol.bootstrap_seed)})
            family['versus_baseline'].append({'algorithm': algorithm, 'scenario': scenario, 'endpoint': endpoint,
                                              'p_value': _p_or_none('wilcoxon', column)})
        family['omnibus'].append({'scenario': scenario, 'endpoint': endpoint, 'kendall_w': kendall_w(matrix),
                                  'p_value': _p_or_none('friedmanchisquare', *matrix.T)})
        for (i, a), (j, b) in itertools.combinations(enumerate(protocol.algorithms), 2):
            family['pairwise'].append({'pair': f'{a}-{b}', 'scenario': scenario, 'endpoint': endpoint,
                                       'cliffs_delta': cliffs_delta(matrix[:, i], matrix[:, j]),
                                       'p_value': _p_or_none('wilcoxon', matrix[:, i], matrix[:, j])})
        if not np.all(matrix == matrix.flat[0]):
            batteries.append({'family': name, 'scenario': scenario, 'endpoint': endpoint,
                              **nonparametric_battery(matrix, protocol.algorithms, protocol.seeds,
                                                      alpha=protocol.alpha)})
    for family in families.values():          # Holm within each family and test type
        for rows in family.values():
            for row, adjusted in zip(rows, holm([r['p_value'] for r in rows])):
                row['p_holm'] = adjusted
        omnibus_by_endpoint = {(r['scenario'], r['endpoint']): r['p_holm'] for r in family['omnibus']}
        for row in family['pairwise']:      # confirmatory only when its omnibus is significant after Holm
            row['confirmatory'] = (row['p_holm'] < protocol.alpha
                                   and omnibus_by_endpoint[(row['scenario'], row['endpoint'])] < protocol.alpha)
    main = families.get('confirmatory', {'omnibus': [], 'pairwise': [], 'versus_baseline': []})
    report.test_families = main
    report.kpi_families = {k: v for k, v in families.items() if k != 'confirmatory'}
    report.battery = batteries
    detected = any(r['p_holm'] < protocol.alpha for r in main['omnibus'])
    report.decisions = {'scientifically_complete': True,
                        'algorithm_difference': 'detected' if detected else 'not_detected',
                        'kpi_differences_detected': sorted(
                            f"{r['scenario']}/{r['endpoint']}" for name, fam in families.items()
                            if name != 'confirmatory' for r in fam['omnibus'] if r['p_holm'] < protocol.alpha),
                        'winner_forced': False}
    return report
