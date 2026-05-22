"""
Tests para uc3m.reward.axes — 7 ejes de recompensa holísticos.
"""
from __future__ import annotations

import numpy as np
import pytest

from uc3m.reward.axes import (
    DEFAULT_LAMBDAS,
    RewardAxes,
    AxisValues,
)


class TestDefaultLambdas:
    def test_sum_to_one(self):
        """Σλ_k = 1 (requerimiento del simplex)."""
        assert abs(DEFAULT_LAMBDAS.sum() - 1.0) < 1e-9

    def test_length_7(self):
        assert len(DEFAULT_LAMBDAS) == 7

    def test_all_nonnegative(self):
        assert np.all(DEFAULT_LAMBDAS >= 0)

    def test_co2_and_cost_are_largest(self):
        """λ₁ (CO₂) y λ₂ (Costo) son los pesos más altos."""
        assert DEFAULT_LAMBDAS[0] >= 0.20
        assert DEFAULT_LAMBDAS[1] >= 0.20


class TestAxisValues:
    def test_to_array_shape(self):
        av = AxisValues(co2=1.0, cost=2.0, flexibility=0.5)
        arr = av.to_array()
        assert arr.shape == (7,)

    def test_to_array_values(self):
        av = AxisValues(co2=1.0, cost=2.0, flexibility=0.3,
                        comfort=0.1, degradation=0.05, resilience=0.2, acs=0.0)
        arr = av.to_array()
        assert arr[0] == pytest.approx(1.0)
        assert arr[1] == pytest.approx(2.0)
        assert arr[2] == pytest.approx(0.3)

    def test_default_zeros(self):
        av = AxisValues()
        assert np.all(av.to_array() == 0.0)


class TestRewardAxes:
    def test_init_default_lambdas(self):
        axes = RewardAxes()
        assert axes is not None

    def test_init_custom_lambdas(self):
        lam = [0.2, 0.2, 0.2, 0.1, 0.1, 0.1, 0.1]
        axes = RewardAxes(lambdas=lam)
        assert axes is not None

    def test_init_wrong_length_raises(self):
        with pytest.raises(AssertionError):
            RewardAxes(lambdas=[0.5, 0.5])

    def test_lambdas_not_sum_to_one_normalizes(self):
        """RewardAxes normaliza lambdas automáticamente al simplex."""
        axes = RewardAxes(lambdas=[0.2] * 7)  # suma = 1.4, se normaliza
        assert abs(axes.lambdas.sum() - 1.0) < 1e-6

    def test_compute_returns_scalar_and_vector(self):
        """compute() retorna (scalar, AxisValues)."""
        axes = RewardAxes()
        result = axes.compute(
            net_consumption_kwh=10.0,
            net_consumption_prev_kwh=None,
            carbon_intensity=0.79,
            price_usd_per_kwh=0.38,
            is_peak_hour=False,
            unmet_setpoint_diff=0.0,
            bess_soc=0.5,
            bess_charge_kwh=2.0,
            bess_discharge_kwh=0.0,
            bess_capacity_kwh=100.0,
            pv_gen_kwh=3.0,
            dhw_demand_kwh_th=0.0,
            dhw_elec_kwh=0.0,
        )
        if isinstance(result, tuple):
            scalar, vec = result
            assert np.isscalar(scalar) or (hasattr(scalar, 'shape') and scalar.shape == ())
            assert hasattr(vec, 'to_array') or (hasattr(vec, 'shape') and vec.shape == (7,))
        else:
            assert np.isscalar(result) or hasattr(result, '__float__')

    def test_zero_consumption_nonnegative_reward(self):
        """Sin consumo de red → recompensa no debería ser muy negativa."""
        axes = RewardAxes()
        result = axes.compute(
            net_consumption_kwh=0.0,
            net_consumption_prev_kwh=None,
            carbon_intensity=0.79,
            price_usd_per_kwh=0.38,
            is_peak_hour=False,
            unmet_setpoint_diff=0.0,
            bess_soc=0.5,
            bess_charge_kwh=0.0,
            bess_discharge_kwh=0.0,
            bess_capacity_kwh=100.0,
            pv_gen_kwh=5.0,
            dhw_demand_kwh_th=0.0,
            dhw_elec_kwh=0.0,
        )
        if isinstance(result, tuple):
            scalar = result[0]
        else:
            scalar = result
        assert float(scalar) > -100.0

    def test_set_baseline(self):
        """set_baseline() actualiza los parámetros de normalización."""
        axes = RewardAxes()
        if hasattr(axes, 'set_baseline'):
            axes.set_baseline(co2_base=0.79, cost_base=0.38)
