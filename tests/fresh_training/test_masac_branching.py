"""SPEC-015 D-M3-9/D-M3-10: MASAC with one categorical branch per equipment.

The learner math lives in CityLearn/scripts/masac_runtime_optimizations.py (which replaces the author's train_actor
and train_critic) and the action choice, rollout and buffer in external/MARL (owner-authorized edit). With one
branch every formula is the author's; with K branches the policy is a softmax per branch and the Q of a joint action
is the mean over branches of the chosen levels.
"""
import sys
import types
from pathlib import Path

import numpy as np
import pytest
import torch
import torch.nn.functional as F

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def patch():
    sys.path.insert(0, str(REPO/'CityLearn/scripts'))
    import masac_runtime_optimizations as m
    return m


def _learner(n_actions, branches=None, n_agents=2):
    args = types.SimpleNamespace(n_actions=n_actions, action_branches=branches)
    return types.SimpleNamespace(args=args, n_actions=n_actions, n_agents=n_agents)


def test_one_branch_is_the_authors_formula(patch):
    torch.manual_seed(0)
    self = _learner(6)
    q = torch.randn(3, 4, 2, 6)
    u = torch.randint(0, 6, (3, 4, 2, 1))
    assert torch.allclose(patch._taken_q(self, q, u), torch.gather(q, dim=3, index=u).squeeze(3))
    logits, avail = torch.randn(6, 6), torch.ones(6, 6)
    avail[0, 2] = 0
    probs, log_probs = patch._branch_policy(self, logits.clone(), avail, 3)
    masked = logits.clone()
    masked[avail == 0] = -1e11
    assert torch.allclose(probs.view(6, 6), F.softmax(masked, dim=1), atol=1e-7)
    assert probs.view(6, 6)[0, 2] == 0


def test_branches_take_a_softmax_each_and_the_mean_q(patch):
    torch.manual_seed(1)
    self = _learner(6, branches=(2, 3))
    probs, _ = patch._branch_policy(self, torch.randn(4, 6), torch.ones(4, 6), 2)
    assert torch.allclose(probs.view(4, 2, 3).sum(dim=-1), torch.ones(4, 2), atol=1e-6)
    q = torch.randn(5, 2, 6)
    u = torch.tensor([[[0, 2], [1, 1]]]*5)
    taken = patch._taken_q(self, q, u)
    expected = 0.5*(q.view(5, 2, 2, 3)[..., 0, :].gather(-1, u[..., :1]).squeeze(-1)
                    + q.view(5, 2, 2, 3)[..., 1, :].gather(-1, u[..., 1:]).squeeze(-1))
    assert torch.allclose(taken, expected)


def test_a_padded_branch_has_a_single_available_level(patch):
    self = _learner(6, branches=(2, 3))
    avail = torch.tensor([[1, 1, 1, 1, 0, 0.]])
    probs, log_probs = patch._branch_policy(self, torch.randn(1, 6), avail, 1)
    assert torch.allclose(probs.view(2, 3)[1], torch.tensor([1.0, 0.0, 0.0]))
    assert float((probs*log_probs).view(2, 3)[1].sum()) == pytest.approx(0.0, abs=1e-6)   # no entropy


def test_the_agent_chooses_one_level_per_branch():
    sys.path.insert(0, str(REPO/'external/MARL/src'))
    from agent.agent_msac_mcsac import Agents
    from common.action_branches import action_branches
    args = types.SimpleNamespace(n_actions=10, n_agents=2, state_shape=4, obs_shape=3, last_action=True,
                                 reuse_network=True, alg='qmix', cuda=False, rnn_hidden_dim=8, temp=1.0,
                                 action_branches=(2, 5))
    assert action_branches(args) == (2, 5)
    agents = Agents(args)
    agents.init_hidden(1)
    avail = np.ones(10)
    avail[6:] = 0                                    # second branch padded: only its level 0
    for evaluate in (False, True):
        action = agents.choose_action(np.zeros(3), np.zeros(10), 0, avail, 0.0, None, evaluate)
        assert np.asarray(action).shape == (2,) and int(action[1]) == 0 and 0 <= int(action[0]) < 5
    del args.action_branches
    assert action_branches(args) == (1, 10)
