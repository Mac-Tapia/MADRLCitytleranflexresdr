"""SPEC-015 D-M3-9/D-M3-10 (3 agents: the original attention squeeze needs more than 2): MAAC with one categorical branch per equipment (external/MAAC, owner-authorized edit).

Policy: K independent categoricals of L levels; log pi and entropy are sums over branches. Critic: Q(s, a) is the
mean over branches of Q_k(s, a_k); the policy baseline is the matching mean of expectations. Without a
multi-discrete action space MAAC keeps its original single-categorical head.
"""
import sys
from pathlib import Path

import pytest
import torch
from gymnasium import spaces

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope='module')
def maac():
    sys.path.insert(0, str(REPO/'external/MAAC'))
    for name in [m for m in list(sys.modules) if m == 'utils' or m.startswith(('utils.', 'algorithms'))]:
        del sys.modules[name]
    from algorithms.attention_sac import AttentionSAC
    yield AttentionSAC
    sys.path.remove(str(REPO/'external/MAAC'))
    for name in [m for m in list(sys.modules) if m == 'utils' or m.startswith(('utils.', 'algorithms'))]:
        del sys.modules[name]


class _Env:
    def __init__(self, action_space, obs=6):
        self.action_space = action_space
        self.observation_space = [spaces.Box(-1, 1, shape=(obs,)) for _ in action_space]


class _Log:
    def add_scalar(self, *a, **k):
        pass

    def add_scalars(self, *a, **k):
        pass


def _sample(model, batch=8, obs=6):
    sizes = [a.policy.fc3.out_features for a in model.agents]
    o = [torch.randn(batch, obs) for _ in sizes]
    acs = []
    for agent, size in zip(model.agents, sizes):
        acs.append(agent.policy(o[len(acs)], sample=True).detach())
    r = [torch.randn(batch) for _ in sizes]
    d = [torch.zeros(batch) for _ in sizes]
    return o, acs, r, [torch.randn(batch, obs) for _ in sizes], d


def test_the_branched_policy_samples_one_level_per_equipment(maac):
    torch.manual_seed(0)
    model = maac.init_from_env(_Env([spaces.MultiDiscrete([5, 5, 5]), spaces.MultiDiscrete([5])]), attend_heads=1,
                               critic_hidden_dim=16, pol_hidden_dim=16)
    assert model.init_dict['branches'] == [(3, 5), (1, 5)]
    policy = model.agents[0].policy
    policy.eval()
    obs = torch.randn(4, 6)
    act, probs, log_pi, _, ent = policy(obs, return_all_probs=True, return_log_pi=True, regularize=True,
                                        return_entropy=True)
    assert act.shape == (4, 15) and probs.shape == (4, 15)
    blocks = act.view(4, 3, 5)
    assert torch.all(blocks.sum(dim=2) == 1)                                  # one level per equipment
    p = probs.view(4, 3, 5)
    assert torch.allclose(p.sum(dim=2), torch.ones(4, 3), atol=1e-6)
    chosen = (p*blocks).sum(dim=2)
    assert torch.allclose(log_pi.squeeze(1), chosen.log().sum(dim=1), atol=1e-5)
    assert float(ent) == pytest.approx(float(-(p*p.log()).sum(dim=(1, 2)).mean()), rel=1e-4)


def test_the_critic_takes_the_mean_over_branches_of_the_chosen_levels(maac):
    torch.manual_seed(1)
    model = maac.init_from_env(_Env([spaces.MultiDiscrete([5, 5]), spaces.MultiDiscrete([5, 5]), spaces.MultiDiscrete([5])]), attend_heads=1,
                               critic_hidden_dim=16, pol_hidden_dim=16)
    model.critic.eval()
    o, acs, *_ = _sample(model)
    q, all_q = model.critic(list(zip(o, acs)), return_all_q=True)[0]
    expected = (all_q.view(-1, 2, 5)*acs[0].view(-1, 2, 5)).sum(dim=2).mean(dim=1, keepdim=True)
    assert torch.allclose(q, expected, atol=1e-6)


def test_one_update_of_critic_and_policies_runs_and_changes_parameters(maac):
    torch.manual_seed(2)
    model = maac.init_from_env(_Env([spaces.MultiDiscrete([5, 5, 5]), spaces.MultiDiscrete([5]),
                                     spaces.MultiDiscrete([5, 5])]), attend_heads=1,
                               critic_hidden_dim=16, pol_hidden_dim=16)
    model.prep_training(device='cpu')
    before = [p.detach().clone() for p in model.agents[0].policy.parameters()]
    sample = _sample(model)
    model.update_critic(sample, logger=None)
    model.update_policies(sample, logger=_Log())
    after = list(model.agents[0].policy.parameters())
    assert any(not torch.allclose(a, b) for a, b in zip(after, before))


def test_a_discrete_action_space_keeps_the_original_head(maac):
    model = maac.init_from_env(_Env([spaces.Discrete(7), spaces.Discrete(4)]), attend_heads=1,
                               critic_hidden_dim=16, pol_hidden_dim=16)
    assert model.init_dict['branches'] is None and model.agents[0].policy.branches is None
    act = model.agents[0].policy(torch.randn(3, 6))
    assert act.shape == (3, 7) and torch.all(act.sum(dim=1) == 1)
