"""Real dependency regressions: ValueNorm state and terminal settlement."""
import importlib.util
import io
from pathlib import Path
from types import SimpleNamespace

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parents[2]


def test_harl_valuenorm_registers_state_after_dtype_conversion_and_roundtrip():
    spec = importlib.util.spec_from_file_location(
        '_audited_harl_valuenorm', ROOT/'external/HARL/harl/common/valuenorm.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    before_dtype = torch.get_default_dtype()
    try:
        # Real dtype conversion reproduces the registration bug on CPU, too.
        torch.set_default_dtype(torch.float64)
        norm = module.ValueNorm(1, device=torch.device('cpu'))
        norm.update(np.asarray([[1.0], [2.0], [3.0]], dtype=np.float32))
        names = {'running_mean', 'running_mean_sq', 'debiasing_term'}
        assert set(norm.state_dict()) == names
        payload = io.BytesIO()
        torch.save(norm.state_dict(), payload)
        payload.seek(0)
        restored = module.ValueNorm(1, device=torch.device('cpu'))
        restored.load_state_dict(torch.load(payload, map_location='cpu', weights_only=False))
        for name in names:
            value = getattr(restored, name)
            assert value.dtype == torch.float32 and not value.requires_grad
            assert torch.isfinite(value).all()
            torch.testing.assert_close(value, getattr(norm, name))
        x = np.asarray([[4.0]], dtype=np.float32)
        np.testing.assert_allclose(restored.denormalize(norm.normalize(x)), x, atol=1e-5)
    finally:
        torch.set_default_dtype(before_dtype)


@pytest.mark.parametrize('horizon', [24, 48])
def test_terminal_settlement_includes_every_real_interval_and_rejects_short_prices(horizon):
    from uc3m.adapters.citylearn import policy_inference as pi
    pi._common()
    from citylearn.internal.kpi import CityLearnKPIService
    # Analytical bill, explicitly separate from native-learning acceptance.
    buildings = [SimpleNamespace(name=name, net_electricity_consumption=np.ones(horizon),
                 pricing=SimpleNamespace(electricity_pricing=np.full(horizon, price)))
                 for name, price in [('A', 0.1), ('B', 0.2)]]
    env = SimpleNamespace(buildings=buildings, time_step=horizon, time_steps=horizon)
    conditions = {b.name: SimpleNamespace(value='') for b in buildings}
    service = CityLearnKPIService(env)
    costs, district = service._condition_settled_cost_totals(condition_by_building=conditions)
    assert costs == pytest.approx({'A': 0.1*horizon, 'B': 0.2*horizon})
    assert district == pytest.approx(0.3*horizon)
    buildings[0].pricing.electricity_pricing = np.full(horizon-1, 0.1)
    with pytest.raises(IndexError):
        service._condition_settled_cost_totals(condition_by_building=conditions)
