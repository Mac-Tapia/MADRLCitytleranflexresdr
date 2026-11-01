"""Contract test: training state checkpoint preserves optimizer, RNG and replay."""
import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'CityLearn' / 'scripts'))


def test_checkpoint_preserves_optimizer_rng_state(tmp_path):
    from checkpoint_state import save_training_state, load_training_state

    model = torch.nn.Linear(4, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss = model(torch.randn(1, 4)).sum()
    loss.backward()
    optimizer.step()

    torch_rng = torch.random.get_rng_state()
    np_rng = np.random.get_state()
    optim_state = optimizer.state_dict()

    save_training_state(tmp_path / 'state.pt', [optimizer], {
        'torch': torch_rng, 'numpy': np_rng,
    })
    loaded = load_training_state(tmp_path / 'state.pt')

    assert torch.equal(loaded['rng_states']['torch'], torch_rng)
    assert loaded['rng_states']['numpy'][1].tolist() == np_rng[1].tolist()
    for key in optim_state['state']:
        for k, v in optim_state['state'][key].items():
            if isinstance(v, torch.Tensor):
                assert torch.equal(loaded['optimizer_states'][0]['state'][key][k], v)


def test_checkpoint_preserves_replay_buffer(tmp_path):
    from checkpoint_state import save_training_state, load_training_state

    model = torch.nn.Linear(2, 1)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)
    replay = {'obs': np.random.randn(100, 4), 'act': np.random.randn(100, 2)}

    save_training_state(tmp_path / 'state.pt', [optimizer], {
        'torch': torch.random.get_rng_state(),
        'numpy': np.random.get_state(),
    }, replay=replay)
    loaded = load_training_state(tmp_path / 'state.pt')

    assert loaded['replay'] is not None
    np.testing.assert_array_equal(loaded['replay']['obs'], replay['obs'])
    np.testing.assert_array_equal(loaded['replay']['act'], replay['act'])


def _trained_specs(seed):
    torch.manual_seed(seed)
    specs = []
    for owner in ("actor_agent0", "critic"):
        module = torch.nn.Linear(3, 1)
        optimizer = torch.optim.Adam(module.parameters(), lr=1e-3)
        module(torch.randn(2, 3)).sum().backward()
        optimizer.step()
        specs.append({"owner": owner, "module": module, "optimizer": optimizer})
    return specs


def test_owner_checkpoint_restores_optimizers_and_rng(tmp_path):
    from checkpoint_state import restore_owner_training_state, save_owner_training_state

    saved = _trained_specs(0)
    path = save_owner_training_state(tmp_path, saved, backend="test")
    expected_torch = torch.rand(3)
    expected_numpy = np.random.rand(3)

    fresh = [
        {"owner": s["owner"], "optimizer": torch.optim.Adam(torch.nn.Linear(3, 1).parameters(), lr=1e-3)}
        for s in saved
    ]
    torch.manual_seed(999)
    np.random.seed(999)
    report = restore_owner_training_state(tmp_path, fresh)

    assert path.name == "training_state.pt"
    assert report["restored_owners"] == ["actor_agent0", "critic"]
    assert torch.equal(torch.rand(3), expected_torch)
    np.testing.assert_array_equal(np.random.rand(3), expected_numpy)
    for before, after in zip(saved, fresh):
        state_before = before["optimizer"].state_dict()["state"][0]["exp_avg"]
        state_after = after["optimizer"].state_dict()["state"][0]["exp_avg"]
        assert torch.equal(state_before, state_after)


def test_owner_restore_fails_closed_when_state_missing(tmp_path):
    from checkpoint_state import TrainingStateError, restore_owner_training_state

    with pytest.raises(TrainingStateError, match="training_state.pt"):
        restore_owner_training_state(tmp_path, _trained_specs(0))


def test_owner_restore_fails_closed_on_owner_mismatch(tmp_path):
    from checkpoint_state import TrainingStateError, restore_owner_training_state, save_owner_training_state

    save_owner_training_state(tmp_path, _trained_specs(0), backend="test")
    other = [{"owner": "actor_agent7", "optimizer": _trained_specs(1)[0]["optimizer"]}]

    with pytest.raises(TrainingStateError, match="actor_agent7"):
        restore_owner_training_state(tmp_path, other)


def test_wrap_save_writes_state_after_every_backend_save(tmp_path):
    from checkpoint_state import wrap_save_with_training_state

    calls = []

    class Backend:
        def save(self):
            calls.append("weights")

    backend = Backend()
    wrap_save_with_training_state(backend, "save", lambda: tmp_path, lambda: _trained_specs(0), backend="test")
    backend.save()

    assert calls == ["weights"]
    assert (tmp_path / "training_state.pt").is_file()


def test_checkpoint_without_replay(tmp_path):
    from checkpoint_state import save_training_state, load_training_state

    model = torch.nn.Linear(2, 1)
    optimizer = torch.optim.SGD(model.parameters(), lr=0.01)

    save_training_state(tmp_path / 'state.pt', [optimizer], {
        'torch': torch.random.get_rng_state(),
        'numpy': np.random.get_state(),
    })
    loaded = load_training_state(tmp_path / 'state.pt')
    assert loaded['replay'] is None
