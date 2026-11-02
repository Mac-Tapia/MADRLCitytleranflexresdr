"""Training phases: {HAPPO, MASAC} then {MATD3, MAAC}, bounded by measured resources.

Owner instruction 2026-11-01: the new CLI keeps the phases of the retired Colab
launcher for an efficient use of resources. Phase 2 starts only when every
treatment of phase 1 is training_complete; concurrency never exceeds the
worker limit computed from configs/algorithms/native.yaml and the measurement.
"""
import threading
import time

import pytest

from uc3m.application.training.phases import (
    group_by_phase, phase_budget, run_phases, validate_phases, worker_limit)

ALGORITHMS = ['HAPPO', 'MASAC', 'MATD3', 'MAAC']
PHASES = [['HAPPO', 'MASAC'], ['MATD3', 'MAAC']]


def _treatments():
    return [{'treatment_id': f'confirm/{a.lower()}/{s}/seed_{seed}', 'algorithm': a}
            for a in ALGORITHMS for s in ('e1', 'e2', 'e3') for seed in (1001, 1002)]


def test_validate_phases_accepts_the_two_phase_split():
    assert validate_phases(PHASES, ALGORITHMS) == (('HAPPO', 'MASAC'), ('MATD3', 'MAAC'))


@pytest.mark.parametrize('phases', [
    [['HAPPO', 'MASAC'], ['MATD3']],                 # MAAC missing
    [['HAPPO', 'MASAC'], ['MATD3', 'MAAC', 'HAPPO']],  # HAPPO twice
    [['HAPPO', 'MASAC'], ['MATD3', 'MAAC', 'QMIX']],   # unknown algorithm
    [['HAPPO', 'MASAC', 'MATD3', 'MAAC'], []],       # empty phase
    [],
])
def test_validate_phases_rejects_incomplete_or_repeated_phases(phases):
    with pytest.raises(ValueError):
        validate_phases(phases, ALGORITHMS)


def test_group_by_phase_keeps_stage_order_inside_each_phase():
    groups = group_by_phase(_treatments(), PHASES)
    assert [g['algorithms'] for g in groups] == [('HAPPO', 'MASAC'), ('MATD3', 'MAAC')]
    assert [len(g['treatments']) for g in groups] == [12, 12]
    assert {t['algorithm'] for t in groups[0]['treatments']} == {'HAPPO', 'MASAC'}
    assert groups[1]['treatments'][0]['treatment_id'] == 'confirm/matd3/e1/seed_1001'


def test_group_by_phase_rejects_a_treatment_outside_every_phase():
    with pytest.raises(ValueError):
        group_by_phase(_treatments() + [{'treatment_id': 'x', 'algorithm': 'QMIX'}], PHASES)


REQUIREMENTS = {
    'HAPPO': {'min_ram_gib': 8, 'min_vram_gib': 4, 'applies_from_episode_time_steps': 1000},
    'MASAC': {'min_ram_gib': 72, 'min_vram_gib': 82, 'applies_from_episode_time_steps': 1000},
    'MATD3': {'min_ram_gib': 40, 'min_vram_gib': 4, 'applies_from_episode_time_steps': 1000},
    'MAAC': {'min_ram_gib': 8, 'min_vram_gib': 4, 'applies_from_episode_time_steps': 1000},
}


def test_worker_limit_takes_the_tightest_resource_for_the_heaviest_algorithm():
    # Phase 2 on 167 GiB RAM / 79 GiB VRAM / 12 CPUs: RAM 167 // 40 = 4 is the bound.
    limit = worker_limit(['MATD3', 'MAAC'], REQUIREMENTS,
                         {'ram_gib': 167.0, 'vram_gib': 79.0, 'cpu_count': 12}, episode_time_steps=8760)
    assert limit['workers'] == 4 and limit['reasons'] == []
    # Same measurement, 3 CPUs: the CPU count binds.
    limit = worker_limit(['MATD3', 'MAAC'], REQUIREMENTS,
                         {'ram_gib': 167.0, 'vram_gib': 79.0, 'cpu_count': 3}, episode_time_steps=8760)
    assert limit['workers'] == 3


def test_worker_limit_is_zero_with_reason_when_not_even_one_fits():
    # MASAC needs 82 GiB VRAM; an 80 GB GPU (74.5 GiB) cannot hold one worker.
    limit = worker_limit(['HAPPO', 'MASAC'], REQUIREMENTS,
                         {'ram_gib': 167.0, 'vram_gib': 74.5, 'cpu_count': 12}, episode_time_steps=8760)
    assert limit['workers'] == 0
    assert limit['reasons'] == ['insufficient_resources:MASAC:vram']
    unmeasured = worker_limit(['MATD3', 'MAAC'], REQUIREMENTS,
                              {'ram_gib': 167.0, 'vram_gib': None, 'cpu_count': 12}, episode_time_steps=8760)
    assert unmeasured['workers'] == 0 and 'insufficient_resources:MATD3:vram' in unmeasured['reasons']


def test_worker_limit_below_the_binding_horizon_is_bounded_by_cpus_only():
    # Requirements bind from applies_from_episode_time_steps, as in check_runtime_resources.
    limit = worker_limit(['HAPPO', 'MASAC'], REQUIREMENTS,
                         {'ram_gib': 16.0, 'vram_gib': None, 'cpu_count': 4}, episode_time_steps=24)
    assert limit['workers'] == 4 and limit['reasons'] == []


# Owner decision 2026-11-01 ("Ejecución + buffers"): inside a phase the runtime flags
# and the replay buffers are sized to each worker's share, and every reduction is
# recorded. Rule numbers are derived from the estimates in configs/algorithms/native.yaml.
BUFFER_RULES = {
    'MASAC': {'key': 'buffer_size', 'flag': '--buffer-size', 'native': 50,
              'ram_gib_per_unit': 1.306, 'base_ram_gib': 6.7, 'min_value': 32},
    'MAAC': {'key': 'buffer_length', 'flag': '--buffer-length', 'native': 43800,
             'ram_gib_per_unit': 2.2/43800, 'base_ram_gib': 5.8, 'min_value': 8760},
}
LOOSE_VRAM = {a: dict(r, min_vram_gib=4) for a, r in REQUIREMENTS.items()}


def test_phase_budget_shrinks_buffers_to_each_worker_share_and_records_it():
    # 180 GiB RAM: native MASAC (72 GiB) fits 2 workers, at the MASAC floor
    # (6.7 + 32 x 1.306 = 48.5 GiB) 3 workers fit; RAM share 60 GiB -> (60 - 6.7) // 1.306 = 40 episodes.
    budget = phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 180.0, 'vram_gib': 79.0, 'cpu_count': 12},
                          LOOSE_VRAM, BUFFER_RULES, episode_time_steps=8760, treatments=6)
    assert budget['workers'] == 3 and budget['reasons'] == []
    assert budget['share'] == {'ram_gib': 60.0, 'vram_gib': pytest.approx(79.0/3), 'cpu_count': 4}
    masac = budget['algorithms']['MASAC']
    assert masac['buffer'] == {'key': 'buffer_size', 'flag': '--buffer-size', 'native': 50,
                               'effective': 40, 'reduced': True}
    assert masac['arguments'] == ['--buffer-size', '40', '--torch-threads', '4']
    assert budget['algorithms']['HAPPO'] == {'buffer': None, 'torch_threads': 4,
                                             'cuda_memory_fraction': pytest.approx(1/3),
                                             'arguments': ['--torch-threads', '4']}
    assert budget['adjustments'] == [{'algorithm': 'MASAC', 'key': 'buffer_size', 'native': 50, 'effective': 40}]


def test_phase_budget_keeps_native_buffers_when_the_share_holds_them():
    budget = phase_budget(['MATD3', 'MAAC'], {'ram_gib': 167.0, 'vram_gib': 79.0, 'cpu_count': 12},
                          REQUIREMENTS, BUFFER_RULES, episode_time_steps=8760, treatments=12)
    assert budget['workers'] == 4  # MATD3 (40 GiB, no rule) binds RAM
    assert budget['algorithms']['MAAC']['buffer']['effective'] == 43800
    assert budget['algorithms']['MAAC']['buffer']['reduced'] is False
    assert budget['adjustments'] == []


def test_phase_budget_never_runs_more_workers_than_treatments():
    budget = phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 500.0, 'vram_gib': 79.0, 'cpu_count': 12},
                          LOOSE_VRAM, BUFFER_RULES, episode_time_steps=8760, treatments=2)
    assert budget['workers'] == 2 and budget['algorithms']['MASAC']['buffer']['reduced'] is False


def test_phase_budget_refuses_below_the_buffer_floor_and_keeps_vram_refusals():
    # 40 GiB cannot hold MASAC at its floor (48.5 GiB): refused, not shrunk further.
    low_ram = phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 40.0, 'vram_gib': 79.0, 'cpu_count': 12},
                           LOOSE_VRAM, BUFFER_RULES, episode_time_steps=8760, treatments=6)
    assert low_ram['workers'] == 0 and low_ram['reasons'] == ['insufficient_resources:MASAC:ram']
    # MASAC's 82 GiB is its critic update, not the buffer: buffers cannot fix it.
    a100 = phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 167.0, 'vram_gib': 74.5, 'cpu_count': 12},
                        REQUIREMENTS, BUFFER_RULES, episode_time_steps=8760, treatments=6)
    assert a100['workers'] == 0 and a100['reasons'] == ['insufficient_resources:MASAC:vram']


def test_phase_budget_below_the_binding_horizon_keeps_native_buffers():
    budget = phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 16.0, 'vram_gib': None, 'cpu_count': 4},
                          REQUIREMENTS, BUFFER_RULES, episode_time_steps=24, treatments=6)
    assert budget['workers'] == 4 and budget['adjustments'] == []
    assert budget['algorithms']['MASAC']['buffer']['effective'] == 50


def test_phase_budget_rejects_an_incoherent_buffer_rule():
    rules = {'MASAC': dict(BUFFER_RULES['MASAC'], min_value=60)}  # floor above native
    with pytest.raises(ValueError):
        phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 180.0, 'vram_gib': 79.0, 'cpu_count': 12},
                     LOOSE_VRAM, rules, episode_time_steps=8760, treatments=6)


# Owner decision 2026-11-01 ("Congelar por etapa"): a relaunch passes the frozen buffer
# as native and floor, so only the worker count is refit and a smaller runtime refuses.
def test_a_frozen_buffer_is_reused_or_refused_never_resized():
    frozen = {'MASAC': dict(BUFFER_RULES['MASAC'], native=40, min_value=40)}
    fits = phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 177.0, 'vram_gib': 79.0, 'cpu_count': 12},
                        LOOSE_VRAM, frozen, episode_time_steps=8760, treatments=6)
    assert fits['workers'] == 3 and fits['algorithms']['MASAC']['buffer']['effective'] == 40
    smaller = phase_budget(['HAPPO', 'MASAC'], {'ram_gib': 58.0, 'vram_gib': 79.0, 'cpu_count': 12},
                           LOOSE_VRAM, frozen, episode_time_steps=8760, treatments=6)
    assert smaller['workers'] == 0 and smaller['reasons'] == ['insufficient_resources:MASAC:ram']


def _complete(treatment):
    return {'treatment_id': treatment['treatment_id'], 'training_complete': True}


def test_phase_two_does_not_start_when_a_phase_one_run_fails():
    started = []

    def run(treatment):
        started.append(treatment['algorithm'])
        return {'treatment_id': treatment['treatment_id'],
                'training_complete': treatment['treatment_id'] != 'confirm/masac/e2/seed_1001'}

    report = run_phases(group_by_phase(_treatments(), PHASES), run, workers=2)
    assert set(started) == {'HAPPO', 'MASAC'} and len(started) == 12
    assert report['status'] == 'incomplete' and report['stopped_at_phase'] == 0
    assert report['phases'][0]['failed'] == ['confirm/masac/e2/seed_1001']
    assert len(report['phases']) == 1


def test_observed_parallelism_never_exceeds_the_worker_limit():
    lock, active, peak = threading.Lock(), [0], [0]

    def run(treatment):
        with lock:
            active[0] += 1
            peak[0] = max(peak[0], active[0])
        time.sleep(0.01)
        with lock:
            active[0] -= 1
        return _complete(treatment)

    report = run_phases(group_by_phase(_treatments(), PHASES), run, workers=[3, 2])
    assert report['status'] == 'training_complete' and report['stopped_at_phase'] is None
    assert [p['workers'] for p in report['phases']] == [3, 2]
    assert 1 < peak[0] <= 3


def test_zero_workers_stops_before_running_the_phase():
    ran = []
    report = run_phases(group_by_phase(_treatments(), PHASES), lambda t: ran.append(t) or _complete(t),
                        workers=[0, 2])
    assert ran == [] and report['status'] == 'insufficient_resources' and report['stopped_at_phase'] == 0


def test_a_crashing_treatment_counts_as_failed_and_stops_the_campaign():
    def run(treatment):
        if treatment['algorithm'] == 'HAPPO':
            raise RuntimeError('backend exploded')
        return _complete(treatment)

    report = run_phases(group_by_phase(_treatments(), PHASES), run, workers=2)
    assert report['status'] == 'incomplete' and len(report['phases']) == 1
    assert len(report['phases'][0]['failed']) == 6
    assert 'backend exploded' in report['phases'][0]['results'][0]['error']
