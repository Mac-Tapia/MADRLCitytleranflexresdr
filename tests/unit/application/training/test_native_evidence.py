import torch


def test_happo_requires_all_actors_critic_and_normalizer(tmp_path):
    from uc3m.adapters.algorithms.evidence import checkpoint_bundle
    for name in ('actor_agent0.pt', 'critic_agent.pt', 'value_normalizer.pt'):
        torch.save({'weight': torch.tensor([1.0])}, tmp_path/name)
    assert checkpoint_bundle(tmp_path, 'HAPPO', 2) == ()
    torch.save({'weight': torch.tensor([1.0])}, tmp_path/'actor_agent1.pt')
    assert len(checkpoint_bundle(tmp_path, 'HAPPO', 2)) == 4
    torch.save({'weight': torch.tensor([float('nan')])}, tmp_path/'actor_agent1.pt')
    assert checkpoint_bundle(tmp_path, 'HAPPO', 2) == ()


def test_nonfinite_kpi_never_passes_audit():
    from uc3m.adapters.algorithms.evidence import finite_kpis
    assert finite_kpis({'cost': 1.0})
    assert not finite_kpis({'cost': float('inf')})
    assert not finite_kpis({'cost': 'invalid'})
