"""Module 8 prerequisites found by its plan: the pilot must be launchable and authorizing a stage must keep the campaign.

- SPEC-015 D-M3-8: MASAC's guard refuses an attempt without its rnn_hidden_dim candidate; the pilot has no grid values,
  so it runs with the single width MASAC searches. Otherwise phase 1 never ends and MATD3 and MAAC never start.
- The YAML is a hashed input of the campaign: editing authorized_stages between stages would invalidate the campaign
  and its configuration freezes. Authorization is an explicit option of each launch, recorded outside the identity.
"""
import json
from collections import defaultdict
from pathlib import Path

import pytest
import yaml

from uc3m.adapters.algorithms import native_entrypoint as ne
from uc3m.application.training import fresh_campaign as fc

REPO = Path(__file__).resolve().parents[2]
CONFIG = REPO/'configs/experiments/iquitos.yaml'
NATIVE = yaml.safe_load((REPO/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))


@pytest.fixture(scope='module')
def pilot():
    config = fc.load_campaign_config(CONFIG, REPO)
    return [t for t in fc.build_dag(config, REPO).treatments if t.stage == 'pilot']


def test_the_masac_pilot_runs_with_the_width_it_searches_and_the_guard_accepts_it(pilot):
    masac = next(t for t in pilot if t.algorithm == 'MASAC')
    args = list(masac.native_arguments)
    searched = NATIVE['algorithms']['MASAC']['hyperparameter_grid_override']['hidden_dimension']
    assert args[args.index('--rnn-hidden-dim') + 1] == str(searched[0])
    check = ne.check_runtime_resources('MASAC', NATIVE['algorithms']['MASAC']['runtime_requirements'],
                                       episode_time_steps=8760, native_args=args,
                                       measure=lambda: {'ram_gib': 83.0, 'vram_gib': 74.5})
    assert check['accepted'] is True, check


def test_the_masac_pilot_is_labelled_with_the_width_it_runs(pilot):
    assert next(t for t in pilot if t.algorithm == 'MASAC').hyperparameter_source == 'single_searched_candidate'
    assert {t.hyperparameter_source for t in pilot if t.algorithm != 'MASAC'} == {'native_default'}


def test_a_blank_decision_does_not_authorize(tmp_path, monkeypatch, capsys):
    code, seen, artifacts = _launch(tmp_path, monkeypatch, '--owner-authorized', '   ')
    assert code == 2 and seen['authorized'] is False
    assert not (artifacts/'stages'/'owner_authorizations.jsonl').exists()
    capsys.readouterr()


def test_a_first_session_prepares_after_restoring_from_an_empty_drive(tmp_path, monkeypatch, capsys):
    # C4 restores (creating an empty root) and then C5 prepares.
    from uc3m.application.training import cli, drive_sync as ds
    artifacts, drive = tmp_path/'campaign', tmp_path/'drive'
    drive.mkdir()
    report = ds.restore_finished_attempts(drive, artifacts, 'any_campaign')
    assert report['conflicts'] == [] and artifacts.is_dir()
    monkeypatch.setattr(cli, '_artifact_root', lambda root, cfg: artifacts)
    monkeypatch.setattr(cli, '_measured_resources', lambda: {'ram_gib': 83.0, 'vram_gib': 74.5, 'cpu_count': 12})
    assert cli.main(['--config', str(CONFIG), '--stage', 'prepare']) == 0
    assert (artifacts/'campaign_manifest.json').is_file()
    capsys.readouterr()
    with pytest.raises(FileExistsError):
        fc.prepare_campaign(CONFIG, REPO, artifact_root=artifacts)


def test_the_resource_probe_holds_no_gpu_in_this_process(monkeypatch):
    # The child ends and frees its CUDA context before any trainer starts.
    import subprocess

    from uc3m.application.training import cli
    calls = []

    class Done:
        returncode, stderr = 0, ''
        stdout = 'noise\n{"ram_gib": 83.0, "vram_gib": 74.5}\n'

    def run(argv, **kwargs):
        calls.append(argv)
        return Done
    monkeypatch.setattr(subprocess, 'run', run)
    assert cli._probe_resources() == {'ram_gib': 83.0, 'vram_gib': 74.5} and len(calls) == 1


def test_execution_limits_reach_the_trainer_and_the_resource_check():
    environ = {'UC3M_TORCH_THREADS': '5', 'UC3M_WORKER_RAM_GIB': '41.5', 'UC3M_WORKER_VRAM_GIB': '37.2'}
    assert ne.thread_arguments(['--seed', '1'], environ) == ['--torch-threads', '5']
    assert ne.thread_arguments(['--torch-threads', '2'], environ) == []
    assert ne.thread_arguments([], {}) == []
    measured = ne.measure_worker_resources(environ, measure=lambda: {'ram_gib': 83.0, 'vram_gib': 20.0})
    assert measured['ram_gib'] == 41.5 and measured['machine_ram_gib'] == 83.0 and measured['vram_gib'] == 20.0
    for algorithm in NATIVE['algorithms']:
        assert '--torch-threads' in ne.trainer_script(REPO, algorithm).read_text(encoding='utf-8'), algorithm


def test_the_other_pilots_do_not_gain_a_width(pilot):
    for treatment in pilot:
        if treatment.algorithm != 'MASAC':
            assert '--rnn-hidden-dim' not in treatment.native_arguments
            assert '--hidden-size' not in treatment.native_arguments, treatment.algorithm


def _launch(tmp_path, monkeypatch, *extra):
    from uc3m.application.training import cli
    artifacts = tmp_path/'campaign'
    seen = {}
    monkeypatch.setattr(cli, '_artifact_root', lambda root, cfg: artifacts)
    monkeypatch.setattr(cli, '_measured_resources', lambda: {'ram_gib': 83.0, 'vram_gib': 74.5, 'cpu_count': 12})
    monkeypatch.setattr(cli, 'native_learner', lambda *a, **k: None)

    def run_stage(manifest_path, stage, learner, root, *, authorized, **kwargs):
        seen['authorized'] = authorized
        if not authorized:
            raise PermissionError(f'{stage} is not authorized')
        return defaultdict(int, stage=stage, status='stub')
    monkeypatch.setattr(fc, 'run_stage', run_stage)
    code = cli.main(['--config', str(CONFIG), '--stage', 'pilot', '--execute', *extra])
    return code, seen, artifacts


def test_without_the_option_an_empty_yaml_refuses_the_stage(tmp_path, monkeypatch, capsys):
    code, seen, artifacts = _launch(tmp_path, monkeypatch)
    assert code == 2 and seen['authorized'] is False
    assert json.loads(capsys.readouterr().out.strip().splitlines()[-1])['status'] == 'not_authorized'
    assert not (artifacts/'stages'/'owner_authorizations.jsonl').exists()


def test_the_option_authorizes_one_launch_and_records_it_without_touching_the_identity(tmp_path, monkeypatch, capsys):
    before = CONFIG.read_bytes()
    _, seen, artifacts = _launch(tmp_path, monkeypatch, '--owner-authorized', 'traspaso 2026-12-01 pilot')
    capsys.readouterr()
    assert seen['authorized'] is True
    row = json.loads((artifacts/'stages'/'owner_authorizations.jsonl').read_text(encoding='utf-8').splitlines()[-1])
    assert row['stage'] == 'pilot' and row['via'] == '--owner-authorized' and row['authorized_at']
    assert row['decision'] == 'traspaso 2026-12-01 pilot'
    assert CONFIG.read_bytes() == before
    from uc3m.application.training.integrity import verify_campaign_inputs
    assert verify_campaign_inputs(artifacts/'campaign_manifest.json', REPO).accepted
