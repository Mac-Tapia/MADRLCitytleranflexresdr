"""T5: real native micro-training of the four backends on the fresh campaign.

Each backend runs as a child of uc3m.adapters.algorithms.native_entrypoint on
the frozen training split, from a brand-new attempt. The test accepts only
observed optimizer updates, changed parameters and a reloadable checkpoint;
missing data or dependencies fail, they never skip.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[2]
CAMPAIGN = REPO/'data/campaigns/iquitos_v1'
EPISODE_STEPS = 168
EPISODES = 2
EXTRA = {'MATD3': ['--batch-size', '64'], 'MAAC': ['--batch-size', '64'], 'MASAC': [], 'HAPPO': []}


def _cache_state(path):
    """Listing and mtimes of a directory; None when it does not exist."""
    if not path.exists():
        return None
    return sorted((p.relative_to(path).as_posix(), p.stat().st_mtime_ns, p.stat().st_size)
                  for p in path.rglob('*') if p.is_file())


def _micro_train(algorithm, attempt_root):
    schema = CAMPAIGN/'splits/train_2023/schema.json'
    assert schema.is_file(), 'fresh training split missing (T3 not complete)'
    native = ['--schema-path', str(schema), '--scenario', 'E1', '--seed', '901', '--episodes', str(EPISODES),
              '--episode-time-steps', str(EPISODE_STEPS), '--artifact-profile', 'efficient', '--cuda'] + EXTRA[algorithm]
    if algorithm in {'HAPPO', 'MATD3'}:
        native += ['--num-env-steps', str(EPISODES*EPISODE_STEPS)]
    command = [sys.executable, '-B', '-m', 'uc3m.adapters.algorithms.native_entrypoint', '--algorithm', algorithm,
               '--campaign-id', 'fresh_iquitos_20261101_v1', '--attempt-id', 'a001',
               '--attempt-root', str(attempt_root), '--normalizer', str(CAMPAIGN/'normalizer.json'), '--'] + native
    attempt_root.mkdir(parents=True, exist_ok=True)
    try:
        # Same wiring as the CLI learner: the reward reads its weights from the single catalog.
        env = dict(os.environ, UC3M_SCENARIO_CATALOG=str(REPO/'configs/scenarios.yaml'))
        completed = subprocess.run(command, cwd=REPO, capture_output=True, text=True, timeout=4*3600, env=env)
    except subprocess.TimeoutExpired as expired:
        (attempt_root/'child.log').write_text(str(expired.stdout or '')[-20000:] + str(expired.stderr or '')[-20000:],
                                              encoding='utf-8')
        raise
    (attempt_root/'child.log').write_text(completed.stdout[-20000:] + completed.stderr[-20000:], encoding='utf-8')
    evidence_path = attempt_root/'learning_evidence.json'
    assert evidence_path.is_file(), completed.stderr[-3000:]
    return completed.returncode, json.loads(evidence_path.read_text(encoding='utf-8'))


@pytest.mark.parametrize('algorithm', ['HAPPO', 'MASAC', 'MATD3', 'MAAC'])
def test_real_optimizer_updates_and_policy_reload(algorithm, tmp_path):
    retired_cache = REPO/'outputs/dataset_cache'
    before = _cache_state(retired_cache)
    code, evidence = _micro_train(algorithm, tmp_path/'attempt')
    assert evidence['verified'], evidence.get('reasons') or evidence.get('evidence_error')
    assert code == 0 and evidence['salvage'] is None and evidence['exit_code'] == 0
    assert evidence['successful_optimizer_updates_by_owner']
    assert all(count > 0 for count in evidence['successful_optimizer_updates_by_owner'].values())
    assert all(evidence['initial_parameter_hashes'][o] != evidence['final_parameter_hashes'][o]
               for o in evidence['successful_optimizer_updates_by_owner'])
    assert evidence['env_steps'] >= EPISODE_STEPS and evidence['checkpoint_files']
    # Reload: the bundle checker deserializes this attempt's own checkpoints and checks finiteness.
    from uc3m.adapters.algorithms.evidence import checkpoint_bundle
    assert checkpoint_bundle(tmp_path/'attempt'/'native', algorithm, 17)
    # The dependency cache stayed inside the attempt: the attempt cache was filled and the
    # retired root (which other sessions may have recreated) was not touched by this attempt.
    assert _cache_state(retired_cache) == before
    native_cache = tmp_path/'attempt'/'native_cache'
    assert native_cache.is_dir() and any(p.is_file() for p in native_cache.rglob('*'))
    # Runtime weights and supervision are part of the evidence.
    assert evidence['effective_axis_weights'] == {'flex': 0.60, 'carbon': 0.15, 'cost': 0.25}
    assert evidence['axis_weights_source']['kind'] == 'scenario_catalog'
    assert evidence['supervision']['constraint_dominance_ratio'] is not None
