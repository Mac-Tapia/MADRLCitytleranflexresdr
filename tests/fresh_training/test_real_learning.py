"""T5: real native micro-training of the four backends on the fresh campaign.

Each backend runs as a child of uc3m.adapters.algorithms.native_entrypoint on
the frozen training split, from a brand-new attempt. The test accepts only
observed optimizer updates, changed parameters and a reloadable checkpoint;
missing data or dependencies fail, they never skip.
"""
import json
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


@pytest.mark.parametrize('algorithm', ['HAPPO', 'MASAC', 'MATD3', 'MAAC'])
def test_real_optimizer_updates_and_policy_reload(algorithm, native_attempts):
    attempt_root = native_attempts[algorithm]
    evidence = json.loads((attempt_root/'learning_evidence.json').read_text(encoding='utf-8'))
    assert evidence['verified'], evidence.get('reasons') or evidence.get('evidence_error')
    assert evidence['salvage'] is None and evidence['exit_code'] == 0
    assert evidence['successful_optimizer_updates_by_owner']
    assert all(count > 0 for count in evidence['successful_optimizer_updates_by_owner'].values())
    assert all(evidence['initial_parameter_hashes'][o] != evidence['final_parameter_hashes'][o]
               for o in evidence['successful_optimizer_updates_by_owner'])
    assert evidence['env_steps'] >= EPISODE_STEPS and evidence['checkpoint_files']
    # Reload: the bundle checker deserializes this attempt's own checkpoints and checks finiteness.
    from uc3m.adapters.algorithms.evidence import checkpoint_bundle
    assert checkpoint_bundle(attempt_root/'native', algorithm, 17)
    from uc3m.adapters.citylearn.policy_inference import load_native_policy
    assert load_native_policy(algorithm, attempt_root).algorithm == algorithm
    assert evidence['env_steps_source'] == 'observed_native_interactions_including_internal_evaluation'
    assert sum(n == EPISODE_STEPS for n in evidence['trajectory_episode_steps']) >= EPISODES
    # The dependency cache stayed inside the attempt: the attempt cache was filled and the
    # retired root (which other sessions may have recreated) was not touched by this attempt.
    native_cache = attempt_root/'native_cache'
    assert native_cache.is_dir() and any(p.is_file() for p in native_cache.rglob('*'))
    # Runtime weights and supervision are part of the evidence.
    assert evidence['effective_axis_weights'] == {'flex': 0.60, 'carbon': 0.15, 'cost': 0.25}
    assert evidence['axis_weights_source']['kind'] == 'scenario_catalog'
    assert evidence['supervision']['constraint_dominance_ratio'] is not None
