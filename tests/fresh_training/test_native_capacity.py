"""Native capacity without silent clamps (owner instruction 2026-11-01).

"los MADRL entrenan a su máxima potencia y su naturaleza sin restricciones":
each backend runs with its author/native capacity on 8760-step episodes on the
Colab GPUs of the modular notebook. Nothing is shrunk silently: when the
measured resources cannot hold the configuration, the run is refused before
training, with the numbers.
"""
import importlib
import sys
from pathlib import Path

import pytest
import yaml

REPO = Path(__file__).resolve().parents[2]
SCRIPTS = REPO/'CityLearn/scripts'
NATIVE = REPO/'configs/algorithms/native.yaml'
EPISODE = 8760
# Measured on data/campaigns/iquitos_v1/splits/train_2023 (CityLearnV3BackendAdapter):
AGENTS, OBS, STATE, JOINT_OBS, ACT, N_DISCRETE = 17, 357, 1652, 6069, 44, 89


def _masac():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    return importlib.import_module('train_citylearn_v3_masac')


def _native():
    return yaml.safe_load(NATIVE.read_text(encoding='utf-8'))


# --- MASAC: no clamps at T=8760 ---------------------------------------------------------------------

def test_masac_capacity_is_not_clamped_on_year_long_episodes():
    masac = _masac()
    resolved = masac.resolve_masac_capacity(
        episode_limit=EPISODE, configured_episodes=50, critic_batch_size=32, critic_train_steps=1,
        actor_sample_times=5, rnn_hidden_dim=256, qmix_hidden_dim=None, hyper_hidden_dim=None, buffer_size=50)
    assert resolved['critic_batch_size'] == 32 and resolved['critic_train_steps'] == 1
    assert resolved['rnn_hidden_dim'] == 256
    # Author ratio of external/MARL (rnn 64 / qmix 32 / hyper 64): qmix = rnn/2, hyper = rnn.
    assert resolved['qmix_hidden_dim'] == 128 and resolved['hyper_hidden_dim'] == 256
    assert resolved['buffer_size'] == 50
    assert not any('clamp' in note for note in resolved['notes'])
    explicit = masac.resolve_masac_capacity(
        episode_limit=EPISODE, configured_episodes=50, critic_batch_size=32, critic_train_steps=4,
        actor_sample_times=5, rnn_hidden_dim=128, qmix_hidden_dim=96, hyper_hidden_dim=200, buffer_size=50)
    assert (explicit['critic_train_steps'], explicit['qmix_hidden_dim'], explicit['hyper_hidden_dim']) == (4, 96, 200)


def test_masac_buffer_never_exceeds_the_run_and_records_it():
    resolved = _masac().resolve_masac_capacity(
        episode_limit=168, configured_episodes=2, critic_batch_size=32, critic_train_steps=1,
        actor_sample_times=5, rnn_hidden_dim=128, qmix_hidden_dim=None, hyper_hidden_dim=None, buffer_size=50)
    assert resolved['buffer_size'] == 2 and resolved['buffer_size_requested'] == 50
    assert any('holds every episode of the run' in note for note in resolved['notes'])


def test_masac_launcher_has_no_silent_clamp_left():
    source = (SCRIPTS/'train_citylearn_v3_masac.py').read_text(encoding='utf-8')
    assert 'clamped' not in source
    assert 'backend_args.buffer_size -= 1' not in source


def test_masac_refuses_with_numbers_instead_of_shrinking():
    masac = _masac()
    gpu_256 = masac.estimate_masac_critic_gpu_gib(
        batch_episodes=32, episode_limit=EPISODE, n_agents=AGENTS, obs_shape=OBS, n_actions=N_DISCRETE,
        state_shape=STATE, rnn_hidden_dim=256, qmix_hidden_dim=128, hyper_hidden_dim=256)
    gpu_128 = masac.estimate_masac_critic_gpu_gib(
        batch_episodes=32, episode_limit=EPISODE, n_agents=AGENTS, obs_shape=OBS, n_actions=N_DISCRETE,
        state_shape=STATE, rnn_hidden_dim=128, qmix_hidden_dim=64, hyper_hidden_dim=128)
    assert gpu_256 > gpu_128 > 1.0
    with pytest.raises(MemoryError, match=r'replay .* GiB .* available'):
        masac.check_masac_capacity(replay_gib=65.0, available_ram_gib=12.0, critic_gpu_gib=gpu_128,
                                   free_vram_gib=80.0)
    with pytest.raises(MemoryError, match=r'critic .* GiB .* free VRAM'):
        masac.check_masac_capacity(replay_gib=1.0, available_ram_gib=80.0, critic_gpu_gib=gpu_256,
                                   free_vram_gib=10.0)
    masac.check_masac_capacity(replay_gib=1.0, available_ram_gib=80.0, critic_gpu_gib=gpu_128,
                               free_vram_gib=80.0)


# --- native.yaml ----------------------------------------------------------------------------------------

def test_native_config_has_no_clamps_and_declares_runtime_requirements():
    native = _native()
    for name, row in native['algorithms'].items():
        assert 'native_clamps' not in row, name
        requirements = row['runtime_requirements']
        # MASAC declares VRAM per candidate (SPEC-015); every other backend has one value.
        vram = 'min_vram_gib_by_rnn_hidden_dim' if name == 'MASAC' else 'min_vram_gib'
        assert set(requirements) >= {'min_ram_gib', vram}, name
        assert requirements['min_ram_gib'] > 0
        assert row['optimizer_owners'], name          # owned by another session, kept
    masac = native['algorithms']['MASAC']
    assert masac['fixed']['critic_batch_size'] == 32 and masac['fixed']['critic_train_steps'] == 1
    assert masac['fixed']['buffer_size'] >= 50


def test_off_policy_replay_holds_five_episodes_or_the_whole_run():
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    from citylearn_v3_training_common import effective_matd3_per_policy_buffer_size
    native = _native()['algorithms']
    total = int(native['MATD3']['fixed']['buffer_size'])
    assert total == 5*EPISODE*AGENTS == 744600
    per_policy = effective_matd3_per_policy_buffer_size(total, num_agents=AGENTS)
    assert per_policy == 5*EPISODE
    # MAAC keeps its author's 1e6 transitions (SPEC-015 D-M3-5); the launcher's lossless bound
    # still holds the whole 50-episode run.
    assert int(native['MAAC']['fixed']['buffer_length']) >= 50*EPISODE + EPISODE


def test_the_estimators_reproduce_the_historical_iquitos_v1_numbers():
    # With the v1 dims above the estimators give the numbers that were declared then; the current
    # requirements are bound to the ACTIVE dataset in test_runtime_requirements.py.
    if str(SCRIPTS) not in sys.path:
        sys.path.insert(0, str(SCRIPTS))
    from citylearn_v3_training_common import effective_matd3_per_policy_buffer_size, estimate_matd3_replay_ram_gib
    per_policy = effective_matd3_per_policy_buffer_size(744600, num_agents=AGENTS)
    assert estimate_matd3_replay_ram_gib(per_policy_buffer=per_policy, num_agents=AGENTS, obs_dim=OBS,
                                         share_obs_dim=JOINT_OBS, act_dim=ACT) == pytest.approx(35.8, abs=0.05)
    replay = _masac().estimate_replay_buffer_gib(buffer_size=50, episode_limit=EPISODE, n_agents=AGENTS,
                                                 n_actions=N_DISCRETE, obs_shape=OBS, state_shape=STATE)
    assert replay == pytest.approx(65.3, abs=0.05)


# --- pre-launch resource check ----------------------------------------------------------------------

def _requirements():
    return {name: row['runtime_requirements'] for name, row in _native()['algorithms'].items()}


def test_resource_check_refuses_insufficient_ram_and_vram():
    from uc3m.adapters.algorithms import native_entrypoint as ne
    requirements = _requirements()['MASAC']
    candidate = ['--rnn-hidden-dim', '128']
    low_ram = ne.check_runtime_resources('MASAC', requirements, episode_time_steps=EPISODE, native_args=candidate,
                                         measure=lambda: {'ram_gib': 4.0, 'vram_gib': 200.0})
    assert not low_ram['accepted'] and 'insufficient_resources:MASAC:ram' in low_ram['reasons']
    low_vram = ne.check_runtime_resources('MASAC', requirements, episode_time_steps=EPISODE, native_args=candidate,
                                          measure=lambda: {'ram_gib': 500.0, 'vram_gib': 8.0})
    assert 'insufficient_resources:MASAC:vram' in low_vram['reasons']
    no_gpu = ne.check_runtime_resources('MASAC', requirements, episode_time_steps=EPISODE, native_args=candidate,
                                        measure=lambda: {'ram_gib': 500.0, 'vram_gib': None})
    assert 'insufficient_resources:MASAC:vram' in no_gpu['reasons']
    ok = ne.check_runtime_resources('MASAC', requirements, episode_time_steps=EPISODE, native_args=candidate,
                                    measure=lambda: {'ram_gib': 500.0, 'vram_gib': 200.0})
    assert ok['accepted'] and ok['reasons'] == [] and ok['measured']['ram_gib'] == 500.0


def test_resource_check_does_not_bind_short_smoke_episodes():
    from uc3m.adapters.algorithms import native_entrypoint as ne
    check = ne.check_runtime_resources('MATD3', _requirements()['MATD3'], episode_time_steps=168,
                                       measure=lambda: {'ram_gib': 12.0, 'vram_gib': None})
    assert check['accepted'] and check['enforced'] is False
    assert check['measured'] == {'ram_gib': 12.0, 'vram_gib': None}


def test_measure_runtime_resources_reports_real_numbers():
    from uc3m.adapters.algorithms import native_entrypoint as ne
    measured = ne.measure_runtime_resources()
    assert measured['ram_gib'] > 0
    assert measured['vram_gib'] is None or measured['vram_gib'] > 0
