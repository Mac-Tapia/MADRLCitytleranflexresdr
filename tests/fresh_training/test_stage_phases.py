"""Stages train by phases: {HAPPO, MASAC} then {MATD3, MAAC} (owner, 2026-11-01).

Inside a phase treatments run in parallel up to a worker limit derived from measured
GPU, RAM and CPU; the next phase starts only when every treatment of the previous one
is training_complete. Phases are declared in the campaign YAML, validated, recorded in
the manifest, and change nothing else: verified attempts are still reused and every
new attempt still starts from episode zero.
"""
import json
import threading
from pathlib import Path

import pytest
import yaml

from tests.fresh_training.test_attempt_acceptance import _stage_learner
from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'
PHASES = [['HAPPO', 'MASAC'], ['MATD3', 'MAAC']]


def _config_copy(tmp_path, phases):
    payload = yaml.safe_load(CONFIG.read_text(encoding='utf-8'))
    payload['training_phases'] = phases
    path = tmp_path/'iquitos.yaml'
    path.write_text(yaml.safe_dump(payload), encoding='utf-8')
    return path


def test_campaign_config_declares_the_two_phases():
    config = fc.load_campaign_config(CONFIG, REPO)
    assert [list(p) for p in config['training_phases']] == PHASES


@pytest.mark.parametrize('phases', [[['HAPPO'], ['MATD3', 'MAAC']], [['HAPPO', 'MASAC', 'HAPPO'], ['MATD3', 'MAAC']],
                                    [[], ['HAPPO', 'MASAC', 'MATD3', 'MAAC']], []])
def test_invalid_phases_are_refused(tmp_path, phases):
    with pytest.raises(ValueError):
        fc.load_campaign_config(_config_copy(tmp_path, phases), REPO)


def _prepared(tmp_path):
    fc.prepare_campaign(CONFIG, REPO, artifact_root=tmp_path/'campaign')
    return tmp_path/'campaign/campaign_manifest.json'


def test_manifest_records_the_phases(tmp_path):
    manifest = json.loads(_prepared(tmp_path).read_text(encoding='utf-8'))
    assert manifest['training_phases'] == PHASES


def test_second_phase_never_starts_after_a_failure(tmp_path):
    manifest_path = _prepared(tmp_path)
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    good = _stage_learner(algorithm_config, 17)
    called = []

    def learner(treatment, attempt_root):
        called.append(treatment['algorithm'])
        if treatment['algorithm'] == 'MASAC':
            raise RuntimeError('native launcher crashed')
        return good(treatment, attempt_root)

    result = fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True)
    assert sorted(called) == ['HAPPO', 'MASAC']
    assert result['status'] == 'incomplete' and result['stopped_at_phase'] == 0
    by_algorithm = {t['treatment_id'].split('/')[1]: t for t in result['treatments']}
    assert by_algorithm['happo']['training_complete'] is True
    assert by_algorithm['masac']['training_complete'] is False
    assert by_algorithm['matd3']['attempts'] == [] and by_algorithm['maac']['attempts'] == []
    assert [p['algorithms'] for p in result['phases']] == [['HAPPO', 'MASAC']]


def test_treatments_of_a_phase_run_in_parallel_with_unique_attempts(tmp_path):
    manifest_path = _prepared(tmp_path)
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    good = _stage_learner(algorithm_config, 17)
    barrier = threading.Barrier(2, timeout=30)

    def learner(treatment, attempt_root):
        barrier.wait()  # both treatments of the phase are inside the learner at once
        return good(treatment, attempt_root)

    result = fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True, workers=[2, 2])
    assert result['status'] == 'training_complete' and result['completed_treatments'] == 4
    roots = [t['attempts'][0]['path'] for t in result['treatments']]
    assert len(set(roots)) == 4
    assert [p['workers'] for p in result['phases']] == [2, 2]
    registry = json.loads((manifest_path.parent/'treatments.json').read_text(encoding='utf-8'))
    assert len(registry['treatments']) == 4


def test_no_worker_fits_means_no_training(tmp_path):
    manifest_path = _prepared(tmp_path)
    called = []
    result = fc.run_stage(manifest_path, 'pilot', lambda t, r: called.append(t), REPO, authorized=True,
                          workers=[0, 1])
    assert called == [] and result['status'] == 'insufficient_resources'
    assert result['completed_treatments'] == 0


def test_prepare_prints_the_plan_per_phase(tmp_path, monkeypatch, capsys):
    from uc3m.application.training import cli
    monkeypatch.setattr(cli, '_artifact_root', lambda root, cfg: tmp_path/'campaign')
    monkeypatch.setattr(cli, '_measured_resources', lambda: {'ram_gib': 100.0, 'vram_gib': 100.0, 'cpu_count': 8})
    assert cli.main(['--config', str(CONFIG), '--stage', 'prepare']) == 0
    report = json.loads(capsys.readouterr().out.strip().splitlines()[-1])
    plan = report['phase_plan']
    pilot = plan['pilot']
    assert [p['algorithms'] for p in pilot] == PHASES
    assert [p['treatments'] for p in pilot] == [2, 2]
    # Pilot episodes are full years: MASAC's 72 GiB RAM / 82 GiB VRAM leave room for one
    # phase-1 worker; MATD3's 40 GiB RAM allows two, capped by the two phase-2 treatments.
    assert [p['workers'] for p in pilot] == [1, 2]
    assert pilot[0]['episode_time_steps'] == 8760
    confirm = plan['confirm']
    assert [p['treatments'] for p in confirm] == [72, 72]
    assert confirm[0]['workers'] >= 1 and 'bounds' in confirm[0] and 'reasons' in confirm[0]
    assert report['measured_resources']['cpu_count'] == 8


def test_pilot_on_an_80_gb_gpu_fits_one_masac_worker_and_keeps_phase_two(tmp_path, monkeypatch, capsys):
    # A100 80 GB exposes ~74.5 GiB. On iquitos_v1, MASAC needed 82 GiB and phase 1 had no worker.
    # On iquitos_v5 its largest candidate needs 71 GiB (SPEC-015): one worker fits. Phase 2 keeps
    # the tuned Colab plan of two workers (owner 2026-11-06: not to be changed).
    from uc3m.application.training import cli
    monkeypatch.setattr(cli, '_artifact_root', lambda root, cfg: tmp_path/'campaign')
    monkeypatch.setattr(cli, '_measured_resources', lambda: {'ram_gib': 83.0, 'vram_gib': 74.5, 'cpu_count': 12})
    assert cli.main(['--config', str(CONFIG), '--stage', 'prepare']) == 0
    pilot = json.loads(capsys.readouterr().out.strip().splitlines()[-1])['phase_plan']['pilot']
    assert pilot[0]['workers'] == 1 and pilot[0]['reasons'] == []
    assert pilot[1]['workers'] == 2


def test_a_40_gb_gpu_still_refuses_masac_with_its_reason(tmp_path, monkeypatch, capsys):
    from uc3m.application.training import cli
    monkeypatch.setattr(cli, '_artifact_root', lambda root, cfg: tmp_path/'campaign')
    monkeypatch.setattr(cli, '_measured_resources', lambda: {'ram_gib': 83.0, 'vram_gib': 37.25, 'cpu_count': 12})
    assert cli.main(['--config', str(CONFIG), '--stage', 'prepare']) == 0
    pilot = json.loads(capsys.readouterr().out.strip().splitlines()[-1])['phase_plan']['pilot']
    assert pilot[0]['workers'] == 0 and 'insufficient_resources:MASAC:vram' in pilot[0]['reasons']


# --- Phase budget: buffers sized to the parallel share, frozen per stage ------------------------------

MAAC_RULE = {'MAAC': {'key': 'buffer_length', 'flag': '--buffer-length', 'native': 43800,
                      'ram_gib_per_unit': 2.2/43800, 'base_ram_gib': 5.8, 'min_value': 8760},
             'MATD3': {'key': 'buffer_size', 'flag': '--buffer-size', 'native': 744600,
                       'ram_gib_per_unit': 35.8/744600, 'base_ram_gib': 4.2, 'min_value': 148920}}


def _stage_budget(tmp_path, monkeypatch, measured, rules=MAAC_RULE):
    from uc3m.application.training import cli
    manifest_path = _prepared(tmp_path)
    config = fc.load_campaign_config(CONFIG, REPO)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    return cli, manifest_path, cli._stage_budget(manifest, manifest_path.parent, config, measured, 'pilot',
                                                 buffer_rules=rules)


def test_first_execute_freezes_buffers_and_records_adjustments(tmp_path, monkeypatch):
    # 20 GiB hold one phase-2 worker at MATD3's floor; its replay shrinks from 744 600 to what
    # 20 GiB hold, never below one episode per policy, and the reduction is recorded.
    cli, manifest_path, budget = _stage_budget(tmp_path, monkeypatch,
                                               {'ram_gib': 20.0, 'vram_gib': 100.0, 'cpu_count': 8})
    frozen = json.loads((manifest_path.parent/'stages/pilot_budget.json').read_text(encoding='utf-8'))
    matd3 = frozen['buffers']['MATD3']
    assert matd3['native'] == 744600 and 148920 <= matd3['effective'] < 744600 and matd3['reduced'] is True
    assert {'algorithm': 'MATD3', 'key': 'buffer_size', 'native': 744600,
            'effective': matd3['effective']} in budget['adjustments']
    # Phase 1 fits one worker: MASAC's largest candidate needs 9 GiB RAM and 71 GiB VRAM here.
    assert budget['phases'][1]['workers'] == 1 and budget['phases'][0]['workers'] == 1
    assert 'HAPPO' not in frozen['buffers'] and 'MASAC' not in frozen['buffers']
    execution = budget['execution']['MATD3']
    assert execution['torch_threads'] >= 1 and 0 < execution['cuda_memory_fraction'] <= 1
    assert execution['worker_ram_gib'] > 0


def test_relaunch_keeps_frozen_buffers_and_only_refits_workers(tmp_path, monkeypatch):
    cli, manifest_path, first = _stage_budget(tmp_path, monkeypatch,
                                              {'ram_gib': 20.0, 'vram_gib': 100.0, 'cpu_count': 8})
    frozen = json.loads((manifest_path.parent/'stages/pilot_budget.json').read_text(encoding='utf-8'))
    config = fc.load_campaign_config(CONFIG, REPO)
    manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
    more = cli._stage_budget(manifest, manifest_path.parent, config,
                             {'ram_gib': 400.0, 'vram_gib': 100.0, 'cpu_count': 8}, 'pilot', buffer_rules=MAAC_RULE)
    assert more['buffers']['MATD3']['effective'] == frozen['buffers']['MATD3']['effective']  # never regrown
    tight = cli._stage_budget(manifest, manifest_path.parent, config,
                              {'ram_gib': 6.0, 'vram_gib': 100.0, 'cpu_count': 8}, 'pilot', buffer_rules=MAAC_RULE)
    phase2 = tight['phases'][1]
    assert phase2['workers'] == 0 and any(r.startswith('insufficient_resources') for r in phase2['reasons'])


def test_run_stage_applies_frozen_buffer_once_and_keeps_execution_out_of_identity(tmp_path):
    manifest_path = _prepared(tmp_path)
    (manifest_path.parent/'stages/pilot_budget.json').write_text(json.dumps(
        {'stage': 'pilot', 'buffers': {'MAAC': {'key': 'buffer_length', 'flag': '--buffer-length', 'native': 43800,
                                                'effective': 8760, 'reduced': True}}}), encoding='utf-8')
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    good = _stage_learner(algorithm_config, 17)
    seen = {}

    def learner(treatment, attempt_root):
        seen[treatment['algorithm']] = treatment.get('execution')
        return good(treatment, attempt_root)

    execution = {a: {'torch_threads': 4, 'cuda_memory_fraction': 0.5, 'worker_ram_gib': 10.0, 'worker_vram_gib': 40.0}
                 for a in ('HAPPO', 'MASAC', 'MATD3', 'MAAC')}
    result = fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True, execution=execution)
    assert result['status'] == 'training_complete' and result['budget_sha256']
    assert seen['MAAC']['torch_threads'] == 4
    maac = next(t for t in result['treatments'] if '/maac/' in t['treatment_id'])
    resolved = json.loads((manifest_path.parent/maac['attempts'][0]['path']/'resolved_treatment.json')
                          .read_text(encoding='utf-8'))
    arguments = resolved['native_arguments']
    assert arguments.count('--buffer-length') == 1
    assert arguments[arguments.index('--buffer-length') + 1] == '8760'
    assert resolved['phase_buffer']['effective'] == 8760 and resolved['execution']['torch_threads'] == 4
    # Other execution parameters on a relaunch keep the identity: the verified attempts are reused.
    other = {a: dict(v, torch_threads=1, cuda_memory_fraction=1.0) for a, v in execution.items()}
    again = fc.run_stage(manifest_path, 'pilot', learner, REPO, authorized=True, execution=other)
    assert all(t['reused_verified_attempt'] for t in again['treatments'])


def test_execution_share_reaches_the_child_as_environment_only():
    from uc3m.application.training import cli
    env = cli._execution_env({'torch_threads': 4, 'cuda_memory_fraction': 0.5, 'worker_ram_gib': 41.5,
                              'worker_vram_gib': None, 'unrelated': 'x'})
    assert env == {'UC3M_TORCH_THREADS': '4', 'UC3M_CUDA_MEMORY_FRACTION': '0.5', 'UC3M_WORKER_RAM_GIB': '41.5'}


def test_stage_result_keeps_a_history_of_execution_per_launch(tmp_path):
    # Buffers are frozen per stage; parallelism and threads may change between runtimes and
    # every launch is recorded so that variation is visible in the stage result.
    manifest_path = _prepared(tmp_path)
    algorithm_config = fc.load_algorithm_config(REPO/'configs/algorithms/native.yaml')
    good = _stage_learner(algorithm_config, 17)
    first = {a: {'torch_threads': 8, 'cuda_memory_fraction': 1.0, 'worker_ram_gib': 80.0, 'worker_vram_gib': 70.0}
             for a in ('HAPPO', 'MASAC', 'MATD3', 'MAAC')}
    second = {a: dict(v, torch_threads=4, cuda_memory_fraction=0.5) for a, v in first.items()}
    fc.run_stage(manifest_path, 'pilot', good, REPO, authorized=True, workers=[1, 1], execution=first)
    result = fc.run_stage(manifest_path, 'pilot', good, REPO, authorized=True, workers=[2, 2], execution=second)
    history = result['launch_history']
    assert [launch['workers'] for launch in history] == [[1, 1], [2, 2]]
    assert [launch['execution']['MAAC']['torch_threads'] for launch in history] == [8, 4]
    assert result['execution_may_vary_between_launches'] is True
