"""SPEC-016 D-V6-52: calibration of the 5R1C model and its ASHRAE Guideline 14 validation (CityLearn v3 layer).

- the ASHRAE Guideline 14 statistics follow their definitions (NMBE and CV(RMSE) with n - p);
- the fast ideal-load series equals the step-by-step ISO 13790 procedure of citylearn.v3.thermal;
- the fit recovers known parameters from a synthetic target and passes the criteria out of sample;
- a falsified validation year fails the criteria (the gate is not vacuous).
"""
import numpy as np
import pytest

from citylearn.v3 import thermal as th
from citylearn.v3 import thermal_calibration as tc

HOURS = 24*60


def _inputs(hours=HOURS, seed=0):
    rng = np.random.default_rng(seed)
    t = np.arange(hours)
    day = (t % 24)
    occupied = ((day >= 8) & (day < 18)).astype(float)
    return th.ThermalInputs(
        theta_e=27.0 + 4.0*np.sin(2*np.pi*(day - 9)/24) + rng.normal(0, 0.5, hours),
        rh_e=np.clip(80 - 15*np.sin(2*np.pi*(day - 9)/24) + rng.normal(0, 3, hours), 30, 100),
        irradiance_w_m2=np.clip(900*np.sin(np.pi*(day - 6)/12), 0, None),
        electric_gain_w=20_000.0 + 15_000.0*occupied,
        occupants=60.0*occupied,
        pressure_kpa=100.0)


def test_ashrae_guideline_14_statistics():
    measured = np.array([10.0, 12.0, 14.0, 16.0])
    simulated = np.array([11.0, 11.0, 15.0, 15.0])
    stats = tc.ashrae_g14(measured, simulated, n_params=1)
    mean = measured.mean()
    assert stats['nmbe_pct'] == pytest.approx(100*(measured - simulated).sum()/((4 - 1)*mean))
    assert stats['cvrmse_pct'] == pytest.approx(100*np.sqrt(((measured - simulated)**2).sum()/(4 - 1))/mean)
    assert tc.CRITERIA == {'monthly': {'nmbe_pct': 5.0, 'cvrmse_pct': 15.0},
                           'hourly': {'nmbe_pct': 10.0, 'cvrmse_pct': 30.0}}


def test_the_fast_ideal_series_equals_the_iso_procedure_step_by_step():
    inputs = _inputs(hours=24*5)
    p = th.iso13790_parameters(floor_area_m2=2000.0, envelope_w_m2k=1.5, solar_aperture_fraction=0.04,
                               ventilation_w_k=th.ventilation_conductance_w_k(0.5), mass_class='medium')
    fast = th.ideal_cooling_series(p, inputs, set_point=24.0, ventilation_m3_s=0.5, w_in=th.humidity_ratio(24, 50, 100.0))
    state = th.ThermalState(theta_m=24.0)
    for h in range(len(inputs.theta_e)):
        phi_int, phi_sol = th.gains_w(p, inputs, h)
        load = th.ideal_load_w(p, state, theta_e=inputs.theta_e[h], phi_int_w=phi_int, phi_sol_w=phi_sol,
                               set_point=24.0) if inputs.occupants[h] > 0 else 0.0
        load = min(load, 0.0)
        out = th.step(p, state, theta_e=inputs.theta_e[h], phi_int_w=phi_int, phi_sol_w=phi_sol, phi_hc_w=load)
        assert fast['sensible_w'][h] == pytest.approx(-load, rel=1e-9, abs=1e-6)
        assert fast['theta_air'][h] == pytest.approx(out.theta_air, abs=1e-9)
        state = out.state


@pytest.fixture(scope='module')
def synthetic():
    inputs = _inputs()
    truth = dict(envelope_w_m2k=2.0, solar_aperture_fraction=0.03)
    kwargs = dict(floor_area_m2=3000.0, ventilation_m3_s=0.8, mass_class='medium', set_point=24.0,
                  w_in=th.humidity_ratio(24, 50, 100.0))
    target = tc.simulate_cooling_kwh(inputs=inputs, **truth, **kwargs)
    return inputs, truth, kwargs, target


def test_the_fit_recovers_known_parameters_and_passes_out_of_sample(synthetic):
    inputs, truth, kwargs, target = synthetic
    month = np.arange(HOURS)//(24*15)                         # four 15-day "months"
    train = month < 2
    result = tc.calibrate(target_kwh=target, inputs=inputs, month=month, train=train, **kwargs)
    assert result.envelope_w_m2k == pytest.approx(truth['envelope_w_m2k'], rel=0.02)
    assert result.solar_aperture_fraction == pytest.approx(truth['solar_aperture_fraction'], rel=0.05)
    assert result.validation['passed'] is True
    assert set(result.validation) >= {'train', 'test', 'passed'}


def test_a_falsified_validation_target_fails_the_criteria(synthetic):
    inputs, truth, kwargs, target = synthetic
    month = np.arange(HOURS)//(24*15)
    train = month < 2
    bent = np.where(train, target, 1.4*target)
    result = tc.calibrate(target_kwh=bent, inputs=inputs, month=month, train=train, **kwargs)
    assert result.validation['passed'] is False
    assert abs(result.validation['test']['monthly']['nmbe_pct']) > 5.0


def test_the_delivered_series_follows_the_iso_step_with_latent_first():
    inputs = _inputs(hours=48)
    p = th.iso13790_parameters(floor_area_m2=2000.0, envelope_w_m2k=1.5, solar_aperture_fraction=0.04,
                               ventilation_w_k=th.ventilation_conductance_w_k(0.5), mass_class='medium')
    w_in = th.humidity_ratio(24, 50, 100.0)
    delivered = np.linspace(0, 60, 48)
    temps = th.simulate_delivered(p, inputs, delivered, ventilation_m3_s=0.5, w_in=w_in, theta_m0=24.0)
    state = th.ThermalState(theta_m=24.0)
    for h in range(48):
        phi_int, phi_sol = th.gains_w(p, inputs, h)
        sensible = max(0.0, delivered[h]*1000 - th.latent_w(inputs, h, ventilation_m3_s=0.5, w_in=w_in))
        out = th.step(p, state, theta_e=inputs.theta_e[h], phi_int_w=phi_int, phi_sol_w=phi_sol, phi_hc_w=-sensible)
        assert temps[h] == pytest.approx(out.theta_air, abs=1e-9)
        state = out.state


def test_the_conditioned_zone_fit_recovers_a_known_fraction():
    inputs = _inputs()
    kwargs = dict(ventilation_m3_s=0.8, mass_class='medium', set_point=24.0, w_in=th.humidity_ratio(24, 50, 100.0))
    fraction = 0.4
    target = tc.simulate_cooling_kwh(inputs=tc.zone_inputs(inputs, fraction), envelope_w_m2k=2.0,
                                     solar_aperture_fraction=0.03, floor_area_m2=3000.0*fraction,
                                     **{**kwargs, 'ventilation_m3_s': 0.8*fraction})
    month = np.arange(HOURS)//(24*15)
    zone = tc.calibrate_conditioned_zone(target_kwh=target, inputs=inputs, month=month, train=month < 2,
                                         floor_area_m2=3000.0, **kwargs)
    assert zone.conditioned_fraction == pytest.approx(fraction, rel=0.05)
    assert zone.statistics['gate'] is False and zone.statistics['test']['passed'] is True
