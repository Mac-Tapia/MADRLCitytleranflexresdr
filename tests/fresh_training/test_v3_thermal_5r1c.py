"""SPEC-016 D-V6-52 / FR-016.4: ISO 13790 simple hourly method (5R1C, Annex C) in the CityLearn v3 layer.

Physics checks of citylearn.v3.thermal: steady-state energy balance, the ideal load that holds the set point, the
linearity the norm's ideal-load procedure relies on, the mass parameters of ISO 13790 Table 12 and a falsified
case. The calibration and the CityLearn building are checked in test_v3_thermal_building.py.
"""
import numpy as np
import pytest

from citylearn.v3 import thermal as th


def _params(area=1000.0, h_env=1.0, k_sol=0.05, mass='medium', ventilation_w_k=400.0):
    return th.iso13790_parameters(floor_area_m2=area, envelope_w_m2k=h_env, solar_aperture_fraction=k_sol,
                                  ventilation_w_k=ventilation_w_k, mass_class=mass)


def test_table_12_mass_classes_and_fixed_coefficients():
    p = _params(mass='medium')
    assert p.a_m == pytest.approx(2.5*1000) and p.c_m == pytest.approx(165_000*1000)
    heavy = _params(mass='heavy')
    assert heavy.a_m == pytest.approx(3.0*1000) and heavy.c_m == pytest.approx(260_000*1000)
    assert p.a_t == pytest.approx(4.5*1000)
    assert p.h_tr_is == pytest.approx(3.45*p.a_t) and p.h_tr_ms == pytest.approx(9.1*p.a_m)
    with pytest.raises(ValueError, match='mass class'):
        _params(mass='granite')


def test_steady_state_losses_equal_the_gains():
    p = _params()
    state = th.ThermalState(theta_m=24.0)
    gains_w, theta_e = 30_000.0, 30.0
    for _ in range(20_000):                                      # far beyond the time constant
        out = th.step(p, state, theta_e=theta_e, phi_int_w=gains_w, phi_sol_w=0.0, phi_hc_w=0.0)
        state = out.state
    losses = (p.h_ve*(out.theta_air - theta_e) + p.h_tr_w*(out.theta_s - theta_e)
              + p.h_tr_em*(out.theta_m - theta_e))
    # ISO 13790 eq. C.2 leaves the share h_tr_w / (9.1 A_t) of the surface gains out of phi_st: lost through windows.
    delivered = gains_w - p.h_tr_w/(th.H_MS*p.a_t)*(0.5*gains_w)
    assert losses == pytest.approx(delivered, rel=1e-6)
    assert out.theta_air > theta_e


def test_the_ideal_cooling_load_holds_the_set_point_exactly():
    p = _params()
    state = th.ThermalState(theta_m=26.0)
    for hour in range(48):
        theta_e = 27.0 + 5.0*np.sin(2*np.pi*hour/24)
        need = th.ideal_load_w(p, state, theta_e=theta_e, phi_int_w=20_000.0, phi_sol_w=8_000.0, set_point=24.0)
        assert need <= 0.0                                           # cooling
        out = th.step(p, state, theta_e=theta_e, phi_int_w=20_000.0, phi_sol_w=8_000.0, phi_hc_w=need)
        assert out.theta_air == pytest.approx(24.0, abs=1e-9)
        state = out.state


def test_the_air_temperature_is_linear_in_the_hvac_power():
    """ISO 13790 C.4 finds the ideal load from two evaluations; it relies on this linearity."""
    p = _params()
    state = th.ThermalState(theta_m=25.0)
    a = th.step(p, state, theta_e=30.0, phi_int_w=10_000.0, phi_sol_w=0.0, phi_hc_w=0.0).theta_air
    b = th.step(p, state, theta_e=30.0, phi_int_w=10_000.0, phi_sol_w=0.0, phi_hc_w=-5_000.0).theta_air
    c = th.step(p, state, theta_e=30.0, phi_int_w=10_000.0, phi_sol_w=0.0, phi_hc_w=-10_000.0).theta_air
    assert b - a == pytest.approx(c - b, rel=1e-9) and c < b < a


def test_without_cooling_the_building_warms_above_the_set_point():
    p = _params()
    state = th.ThermalState(theta_m=24.0)
    temps = []
    for _ in range(24):
        out = th.step(p, state, theta_e=31.0, phi_int_w=25_000.0, phi_sol_w=10_000.0, phi_hc_w=0.0)
        temps.append(out.theta_air)
        state = out.state
    assert temps[-1] > 24.0 + 2.0 and all(b >= a - 1e-9 for a, b in zip(temps, temps[1:]))


def test_invalid_inputs_are_refused():
    with pytest.raises(ValueError):
        _params(area=0.0)
    with pytest.raises(ValueError):
        _params(h_env=-1.0)
    with pytest.raises(ValueError):
        _params(ventilation_w_k=-5.0)
