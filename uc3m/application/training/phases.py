"""Training phases inside a stage, bounded by measured resources.

Owner instruction 2026-11-01: the new CLI keeps the two phases of the retired
Colab launcher, {HAPPO, MASAC} then {MATD3, MAAC}, for an efficient use of
resources. Every function is pure except ``run_phases``, which only calls the
injected ``run_treatment``; nothing here measures hardware or trains.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import Any, Callable, Dict, List, Mapping, Sequence, Tuple, Union

Phases = Tuple[Tuple[str, ...], ...]


def validate_phases(phases: Sequence[Sequence[str]], algorithms: Sequence[str]) -> Phases:
    """Phases must be non-empty and cover every algorithm exactly once."""
    normalized = tuple(tuple(str(a) for a in phase) for phase in phases or ())
    if not normalized or any(not phase for phase in normalized):
        raise ValueError('training_phases must be non-empty phases')
    flat = [a for phase in normalized for a in phase]
    repeated = sorted({a for a in flat if flat.count(a) > 1})
    if repeated:
        raise ValueError(f'training_phases repeat algorithms: {repeated}')
    if set(flat) != set(algorithms):
        raise ValueError(f'training_phases must cover exactly {sorted(algorithms)}, got {sorted(flat)}')
    return normalized


def group_by_phase(treatments: Sequence[Mapping[str, Any]],
                   phases: Sequence[Sequence[str]]) -> List[Dict[str, Any]]:
    """Split a stage's treatments into phases, keeping the stage order inside each."""
    groups = [{'algorithms': tuple(phase), 'treatments': []} for phase in phases]
    owner = {a: index for index, phase in enumerate(phases) for a in phase}
    for treatment in treatments:
        index = owner.get(treatment['algorithm'])
        if index is None:
            raise ValueError(f"{treatment.get('treatment_id')}: algorithm {treatment['algorithm']} is in no phase")
        groups[index]['treatments'].append(treatment)
    return groups


def requirement_ceiling(requirement: Mapping[str, Any], what: str) -> float:
    """The most a worker of this algorithm may need. A per-candidate VRAM requirement reserves its
    largest candidate: any candidate of the grid may run in the phase, and none may count as zero."""
    by_candidate = requirement.get(f'min_{what}_gib_by_rnn_hidden_dim')
    if by_candidate:
        return max(float(v) for v in by_candidate.values())
    return float(requirement.get(f'min_{what}_gib', 0) or 0)


def worker_limit(algorithms_in_phase: Sequence[str], runtime_requirements: Mapping[str, Mapping[str, Any]],
                 measured: Mapping[str, Any], *, episode_time_steps: int) -> Dict[str, Any]:
    """Concurrent treatments of one phase that fit the measured RAM, VRAM and CPUs.

    Any mix of the phase's algorithms may run together, so each worker reserves
    the largest requirement among them. Requirements bind from
    ``applies_from_episode_time_steps``, as in the native entrypoint's check;
    below it only the CPU count bounds the phase.
    """
    cpus = int(measured.get('cpu_count') or 0)
    reasons, bounds = [], {'cpu': cpus}
    for what in ('ram', 'vram'):
        need, heaviest = 0.0, None
        for algorithm in algorithms_in_phase:
            requirement = dict(runtime_requirements.get(algorithm) or {})
            if int(episode_time_steps) < int(requirement.get('applies_from_episode_time_steps', 0)):
                continue
            value = requirement_ceiling(requirement, what)
            if value > need:
                need, heaviest = value, algorithm
        if need <= 0:
            continue
        have = measured.get(f'{what}_gib')
        bounds[what] = int(float(have)//need) if have is not None else 0
        if bounds[what] < 1:
            reasons.append(f'insufficient_resources:{heaviest}:{what}')
    if cpus < 1:
        reasons.append('insufficient_resources:cpu')
    workers = 0 if reasons else min(bounds.values())
    return {'workers': workers, 'reasons': reasons, 'bounds': bounds, 'measured': dict(measured)}


def _check_rule(algorithm: str, rule: Mapping[str, Any]) -> None:
    for key in ('key', 'flag', 'native', 'ram_gib_per_unit', 'base_ram_gib', 'min_value'):
        if key not in rule:
            raise ValueError(f'{algorithm} buffer rule lacks {key}')
    if not (0 < int(rule['min_value']) <= int(rule['native'])) or float(rule['ram_gib_per_unit']) <= 0:
        raise ValueError(f'{algorithm} buffer rule needs 0 < min_value <= native and a positive cost')


def phase_budget(algorithms_in_phase: Sequence[str], measured: Mapping[str, Any],
                 runtime_requirements: Mapping[str, Mapping[str, Any]],
                 buffer_rules: Mapping[str, Mapping[str, Any]], *, episode_time_steps: int,
                 treatments: int) -> Dict[str, Any]:
    """Workers of one phase and each worker's share, with runtime flags and buffers sized to it.

    Owner decision 2026-11-01 ("Ejecución + buffers"): concurrent workers split the
    measured RAM, VRAM and CPUs. An algorithm with a buffer rule reserves its floor
    (``base_ram_gib + min_value*ram_gib_per_unit``) instead of its native
    ``min_ram_gib``, so more workers fit; its buffer then takes the largest value
    the RAM share holds, never above native nor below the floor, and every
    reduction is listed in ``adjustments`` for the attempt evidence. VRAM needs
    (e.g. MASAC's critic update) are not buffers and still refuse the phase.
    """
    for algorithm, rule in buffer_rules.items():
        _check_rule(algorithm, rule)
    binding = {}
    for algorithm in algorithms_in_phase:
        requirement = dict(runtime_requirements.get(algorithm) or {})
        if int(episode_time_steps) >= int(requirement.get('applies_from_episode_time_steps', 0)):
            rule = buffer_rules.get(algorithm)
            if rule is not None:
                requirement['min_ram_gib'] = (float(rule['base_ram_gib'])
                                              + int(rule['min_value'])*float(rule['ram_gib_per_unit']))
            binding[algorithm] = requirement
    limit = worker_limit(algorithms_in_phase, binding, measured, episode_time_steps=episode_time_steps)
    workers = min(limit['workers'], max(0, int(treatments)))
    budget = {'workers': workers, 'reasons': limit['reasons'], 'bounds': limit['bounds'],
              'measured': dict(measured), 'share': None, 'algorithms': {}, 'adjustments': []}
    if workers < 1:
        return budget
    ram, vram = measured.get('ram_gib'), measured.get('vram_gib')
    share = {'ram_gib': None if ram is None else float(ram)/workers,
             'vram_gib': None if vram is None else float(vram)/workers,
             'cpu_count': int(measured['cpu_count'])//workers}
    budget['share'] = share
    threads = max(1, share['cpu_count'])
    for algorithm in algorithms_in_phase:
        rule, arguments, buffer = buffer_rules.get(algorithm), [], None
        if rule is not None:
            effective = int(rule['native'])
            if algorithm in binding and share['ram_gib'] is not None:
                fits = int((share['ram_gib'] - float(rule['base_ram_gib']))//float(rule['ram_gib_per_unit']))
                effective = max(int(rule['min_value']), min(effective, fits))
            buffer = {'key': rule['key'], 'flag': rule['flag'], 'native': int(rule['native']),
                      'effective': effective, 'reduced': effective < int(rule['native'])}
            arguments += [rule['flag'], str(effective)]
            if buffer['reduced']:
                budget['adjustments'].append({'algorithm': algorithm, 'key': rule['key'],
                                              'native': buffer['native'], 'effective': effective})
        arguments += ['--torch-threads', str(threads)]
        budget['algorithms'][algorithm] = {'buffer': buffer, 'torch_threads': threads,
                                           'cuda_memory_fraction': 1/workers, 'arguments': arguments}
    return budget


def run_phases(phases: Sequence[Mapping[str, Any]], run_treatment: Callable[[Mapping[str, Any]], Mapping[str, Any]],
               *, workers: Union[int, Sequence[int]],
               executor_factory: Callable[..., Any] = ThreadPoolExecutor) -> Dict[str, Any]:
    """Run each phase in parallel up to its worker limit; stop at the first incomplete phase.

    ``phases`` comes from ``group_by_phase``; ``workers`` is one limit for every
    phase or one per phase (from ``worker_limit``). A treatment that raises
    counts as not training_complete, so the next phase never starts on it.
    """
    limits = [int(workers)]*len(phases) if isinstance(workers, int) else [int(w) for w in workers]
    if len(limits) != len(phases):
        raise ValueError('one worker limit per phase is required')

    def guarded(treatment):
        try:
            return dict(run_treatment(treatment))
        except Exception as exc:  # noqa: BLE001 - recorded as a failed treatment
            return {'treatment_id': treatment.get('treatment_id'), 'training_complete': False,
                    'error': f'{type(exc).__name__}: {exc}'}

    report: Dict[str, Any] = {'phases': [], 'stopped_at_phase': None, 'status': 'training_complete'}
    for index, (phase, limit) in enumerate(zip(phases, limits)):
        entry = {'algorithms': list(phase['algorithms']), 'workers': limit, 'results': [], 'failed': []}
        report['phases'].append(entry)
        if limit < 1:
            report.update(stopped_at_phase=index, status='insufficient_resources')
            return report
        if phase['treatments']:
            with executor_factory(max_workers=limit) as executor:
                entry['results'] = list(executor.map(guarded, phase['treatments']))
        entry['failed'] = [r.get('treatment_id') for r in entry['results'] if r.get('training_complete') is not True]
        if entry['failed']:
            report.update(stopped_at_phase=index, status='incomplete')
            return report
    return report
