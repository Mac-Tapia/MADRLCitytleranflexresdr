"""SPEC-015 D-M3-5: the four MADRL keep the native capacity of their authors (owner 2026-11-06).

Every value below is read from the authors' code in external/, not retyped, so a drift on either
side fails the gate. A project value may differ from the author only where the year-long episode
needs it and it gives at least the author's capacity: a larger replay, a wider network, or a
lossless bound that still holds the whole run. The one reduction kept is the number of parallel
environment copies (owner 2026-11-06: the Colab plan is not changed), and it must be declared.
"""
import re
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
EXTERNAL = REPO/'external'
SCRIPTS = REPO/'CityLearn/scripts'
EPISODE = 8760
LONGEST_STAGE_EPISODES = 50
NATIVE = yaml.safe_load((REPO/'configs/algorithms/native.yaml').read_text(encoding='utf-8'))
ALGORITHMS = NATIVE['algorithms']
GRID_WIDTHS = NATIVE['hyperparameter_grid']['hidden_dimension']


def _text(path):
    return Path(path).read_text(encoding='utf-8')


def _argparse_default(source, flag):
    match = re.search(r'add_argument\(\s*["\']' + re.escape(flag) + r'["\'][^)]*?default\s*=\s*([A-Za-z_]+\([^)]*\)|[^,\s)]+)', source,
                      re.S)
    assert match, f'{flag} not found'
    return eval(match.group(1), {'int': int, 'float': float})  # literal defaults such as int(1e6)


def _assignment(source, name):
    match = re.search(r'args\.' + re.escape(name) + r'\s*=\s*([0-9.e]+)', source)
    assert match, name
    return float(match.group(1))


@pytest.fixture(scope='module')
def author():
    happo = yaml.safe_load(_text(EXTERNAL/'HARL/harl/configs/algos_cfgs/happo.yaml'))
    marl = _text(EXTERNAL/'MARL/src/common/arguments.py')
    mixer = marl[marl.index('def get_mixer_args'):marl.index('def get_centralv_args')]
    offpolicy = _text(EXTERNAL/'off-policy/offpolicy/config.py')
    maac = _text(EXTERNAL/'MAAC/main.py')
    return {
        'HAPPO': {'ppo_epoch': happo['algo']['ppo_epoch'], 'critic_epoch': happo['algo']['critic_epoch'],
                  'actor_num_mini_batch': happo['algo']['actor_num_mini_batch'],
                  'critic_num_mini_batch': happo['algo']['critic_num_mini_batch'],
                  'width': max(happo['model']['hidden_sizes']),
                  'n_rollout_threads': happo['train']['n_rollout_threads']},
        'MASAC': {'critic_batch_size': _assignment(mixer, 'critic_batch_size'),
                  'critic_train_steps': _assignment(mixer, 'critic_train_steps'),
                  'width': _assignment(mixer, 'rnn_hidden_dim'),
                  'buffer_size': _argparse_default(marl, '--buffer_size')},
        'MATD3': {'buffer_size': _argparse_default(offpolicy, '--buffer_size'),
                  'batch_size': _argparse_default(offpolicy, '--batch_size'),
                  'width': _argparse_default(offpolicy, '--hidden_size')},
        'MAAC': {'buffer_length': _argparse_default(maac, '--buffer_length'),
                 'batch_size': _argparse_default(maac, '--batch_size'),
                 'steps_per_update': _argparse_default(maac, '--steps_per_update'),
                 'num_updates': _argparse_default(maac, '--num_updates'),
                 'width': max(_argparse_default(maac, '--pol_hidden_dim'),
                              _argparse_default(maac, '--critic_hidden_dim')),
                 'n_rollout_threads': _argparse_default(maac, '--n_rollout_threads')},
    }


def test_no_algorithm_declares_a_buffer_reduction_or_a_clamp():
    # phases.phase_budget can shrink a buffer to fit a parallel RAM share when a phase_buffer rule is
    # declared. Native capacity forbids it: refusing the phase is the only answer to missing memory.
    for name, row in ALGORITHMS.items():
        assert 'phase_buffer' not in row and 'native_clamps' not in row, name


def test_every_grid_width_is_at_least_the_authors(author):
    for name in ALGORITHMS:
        assert min(GRID_WIDTHS) >= author[name]['width'], name


def test_happo_keeps_the_author_update(author):
    source = _text(SCRIPTS/'train_citylearn_v3_happo.py')
    assert ALGORITHMS['HAPPO']['fixed'] == {'action_grid_levels': 5}      # D-M3-10: interface, not capacity
    assert _argparse_default(source, '--ppo-epoch') == author['HAPPO']['ppo_epoch']
    assert _argparse_default(source, '--critic-epoch') == author['HAPPO']['critic_epoch']
    # Automatic minibatches are ceil(n_rollout_threads / 8): one copy gives the author's single minibatch.
    assert _argparse_default(source, '--num-mini-batch') == 0
    assert author['HAPPO']['actor_num_mini_batch'] == author['HAPPO']['critic_num_mini_batch'] == 1
    # One 8760-step episode per update holds more samples than the author's rollout.
    assert EPISODE >= author['HAPPO']['n_rollout_threads']*200


def test_masac_keeps_the_author_critic_and_a_lossless_buffer(author):
    fixed = ALGORITHMS['MASAC']['fixed']
    assert fixed['critic_batch_size'] == author['MASAC']['critic_batch_size']
    assert fixed['critic_train_steps'] == author['MASAC']['critic_train_steps']
    # buffer_size counts episodes: 50 holds every episode of the longest stage.
    assert fixed['buffer_size'] >= min(author['MASAC']['buffer_size'], LONGEST_STAGE_EPISODES)


def test_matd3_keeps_at_least_the_author_replay_and_batch(author):
    sys.path.insert(0, str(SCRIPTS)) if str(SCRIPTS) not in sys.path else None
    from citylearn_v3_training_common import effective_matd3_per_policy_buffer_size
    fixed = ALGORITHMS['MATD3']['fixed']
    per_policy = effective_matd3_per_policy_buffer_size(int(fixed['buffer_size']), num_agents=17)
    assert per_policy >= author['MATD3']['buffer_size']
    assert fixed['batch_size'] >= author['MATD3']['batch_size']


def test_maac_is_the_author_schema(author):
    fixed = ALGORITHMS['MAAC']['fixed']
    for key in ('buffer_length', 'batch_size', 'steps_per_update', 'num_updates'):
        assert fixed[key] == author['MAAC'][key], key
    for key in ('buffer_length', 'batch_size', 'steps_per_update', 'num_updates'):
        assert key in ALGORITHMS['MAAC']['fixed_flags'], key


def test_maac_lossless_bound_holds_the_whole_run():
    sys.path.insert(0, str(SCRIPTS)) if str(SCRIPTS) not in sys.path else None
    from train_citylearn_v3_maac import _effective_maac_buffer_length
    run = _effective_maac_buffer_length(ALGORITHMS['MAAC']['fixed']['buffer_length'],
                                        target_episodes=LONGEST_STAGE_EPISODES, episode_time_steps=EPISODE)
    assert run == LONGEST_STAGE_EPISODES*EPISODE + EPISODE


@pytest.mark.parametrize('name', ['HAPPO', 'MAAC'])
def test_the_single_environment_copy_is_declared(name, author):
    assert author[name]['n_rollout_threads'] > 1
    limitations = ' '.join(ALGORITHMS[name].get('declared_limitations', []))
    assert 'parallel environment' in limitations and str(author[name]['n_rollout_threads']) in limitations
    assert 'n_rollout_threads' not in ALGORITHMS[name]['fixed']


def test_maac_replay_on_the_active_dataset_fits_its_reservation():
    sys.path.insert(0, str(SCRIPTS)) if str(SCRIPTS) not in sys.path else None
    from citylearn_v3_training_common import CityLearnMAACVecEnv
    from uc3m.adapters.algorithms.native_entrypoint import RAM_FLOOR_GIB, requirement_from_estimate
    campaign = yaml.safe_load((REPO/'configs/experiments/iquitos.yaml').read_text(encoding='utf-8'))
    schema = REPO/campaign['dataset_root']/'splits/train_2023/schema.json'
    env = CityLearnMAACVecEnv(schema_path=str(schema), scenario='E1', seed=0, episode_time_steps=EPISODE,
                              action_bins=3, discrete_action_mode='axis', algorithm='MAAC')
    steps = LONGEST_STAGE_EPISODES*EPISODE + EPISODE
    obs = [int(space.shape[0]) for space in env.observation_space]
    actions = [int(space.n) for space in env.action_space]
    # external/MAAC/utils/buffer.py: float32 obs, next_obs, actions and reward; uint8 done.
    replay_gib = steps*sum((2*o + a + 1)*4 + 1 for o, a in zip(obs, actions))/2**30
    reservation = ALGORITHMS['MAAC']['runtime_requirements']['min_ram_gib']
    assert reservation >= requirement_from_estimate(replay_gib, RAM_FLOOR_GIB), replay_gib
