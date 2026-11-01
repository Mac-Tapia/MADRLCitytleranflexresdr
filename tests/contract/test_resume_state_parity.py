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
