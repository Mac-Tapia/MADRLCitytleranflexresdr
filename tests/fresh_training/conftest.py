"""Strict profile for the fresh campaign: an omitted check is not a passed check.

Any skip, xfail or xpass of a test collected from this directory turns the
session exit status non-zero, so a missing dependency or a missing input can
never be read as acceptance of the new campaign.
"""
from pathlib import Path

import pytest

_HERE = Path(__file__).resolve().parent
_NOT_ACCEPTED = []


def _in_fresh_profile(nodeid_path):
    try:
        return Path(nodeid_path).resolve().is_relative_to(_HERE)
    except AttributeError:  # pragma: no cover - Python < 3.9 has no is_relative_to
        return str(Path(nodeid_path).resolve()).startswith(str(_HERE))


def pytest_runtest_logreport(report):
    path = report.fspath if hasattr(report, 'fspath') else report.location[0]
    if not _in_fresh_profile(path):
        return
    if report.skipped and hasattr(report, 'wasxfail'):
        _NOT_ACCEPTED.append((report.nodeid, 'xfail'))
    elif report.skipped:
        _NOT_ACCEPTED.append((report.nodeid, 'skip'))
    elif report.when == 'call' and report.passed and hasattr(report, 'wasxfail'):
        _NOT_ACCEPTED.append((report.nodeid, 'xpass'))


def pytest_terminal_summary(terminalreporter):
    for nodeid, outcome in _NOT_ACCEPTED:
        terminalreporter.write_line(f'FRESH-PROFILE REJECTED {outcome}: {nodeid}', red=True)


def pytest_sessionfinish(session, exitstatus):
    if _NOT_ACCEPTED and session.exitstatus == 0:
        session.exitstatus = pytest.ExitCode.TESTS_FAILED


@pytest.fixture(scope='session')
def native_attempts():
    """Four new native learners; no dependency on another session's scratch.

    Only the bounded pilot is authorized here (2 x 168 steps per backend).
    Its independently hashed configuration is never the annual experiment.
    """
    import json
    import subprocess
    import uuid
    import yaml
    from uc3m.application.training import fresh_campaign as fc
    from uc3m.application.training.cli import native_learner
    from uc3m.application.evaluation.results_catalog import discover_attempts
    from tests.fresh_training.test_real_learning import _cache_state
    repo = _HERE.parents[1]
    subprocess.run(['powershell', '-ExecutionPolicy', 'Bypass', '-File',
                    'scripts/verify_project_context.ps1'], cwd=repo, check=True)
    owned = repo/'.superpowers/sdd/remediacion_integrada'/('native_' + uuid.uuid4().hex)
    owned.mkdir(parents=True)
    config = yaml.safe_load((repo/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
    algorithms = yaml.safe_load((repo/config['algorithm_config']).read_text(encoding='utf-8'))
    for name, flag in [('MATD3', 'buffer_size'), ('MAAC', 'buffer_length')]:
        algorithms['algorithms'][name]['fixed'].update(batch_size=64, **{flag: 504})
    algorithm_path = owned/'native.yaml'
    algorithm_path.write_text(yaml.safe_dump(algorithms), encoding='utf-8')
    config['algorithm_config'] = algorithm_path.relative_to(repo).as_posix()
    config['stages'] = {'pilot': {'episodes': 2, 'episode_time_steps': 168,
                                  'seeds': [901], 'scenarios': ['E1']}}
    config['resource_authorization'] = {'authorized_stages': ['pilot']}
    config_path = owned/'micro.yaml'
    config_path.write_text(yaml.safe_dump(config), encoding='utf-8')
    fc.prepare_campaign(config_path, repo, artifact_root=owned/'campaign')
    manifest_path = owned/'campaign/campaign_manifest.json'
    cache = repo/'outputs/dataset_cache'
    before = _cache_state(cache)
    result = fc.run_stage(manifest_path, 'pilot', native_learner(repo, config['campaign_id'],
                          repo/config['dataset_root']), repo, authorized=True, workers=1)
    assert _cache_state(cache) == before, 'native fixture changed the retired cache'
    (owned/'micro_result.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    attempts = {a.algorithm: a.attempt_root for a in discover_attempts(manifest_path)}
    assert result['status'] == 'training_complete' and len(attempts) == 4, (owned, result)
    return attempts
