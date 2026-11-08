"""SPEC-016 D-V6-59 and D-V6-60: weather of the place, and temperature and calendar by building function."""
import sys
from datetime import date
from pathlib import Path

import numpy as np
import pandas as pd
import pytest
import yaml

from uc3m.application.dataset import ev_queue as q
from uc3m.application.dataset import holidays as hd
from uc3m.application.dataset import weather_correction as wc

REPO = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(REPO/'tools/dataset'), str(REPO/'CityLearn')]
import build_v6_parts as v6  # noqa: E402

REGISTRY = yaml.safe_load((REPO/'configs/dataset/building_types.yaml').read_text(encoding='utf-8'))
SCHEDULES = REGISTRY['schedules']


def test_national_holidays_follow_the_law_in_force_each_year():
    days = hd.peru_holidays(2024)
    assert len(days) == 16
    assert date(2024, 3, 28) in days and date(2024, 3, 29) in days      # Holy Thursday and Good Friday
    assert {date(2024, 6, 7), date(2024, 7, 23), date(2024, 8, 6), date(2024, 12, 9)} <= days
    assert date(2023, 6, 7) not in hd.peru_holidays(2023)                # Ley 31788 came after that date


@pytest.mark.parametrize('year, easter', [(2023, date(2023, 4, 9)), (2024, date(2024, 3, 31)), (2025, date(2025, 4, 20))])
def test_easter(year, easter):
    assert hd.easter_sunday(year) == easter


@pytest.mark.parametrize('function, stops', [('office_daytime', True), ('school_daytime', True), ('university_daytime', True),
                                             ('industrial_shift', True), ('retail_extended', True), ('port_extended', True),
                                             ('healthcare_24h', False), ('laboratory_24h', False), ('hotel_24h', False),
                                             ('airport_extended', False), ('office_24h', False)])
def test_a_holiday_depends_on_the_function_of_the_building(function, stops):
    holiday = date(2024, 7, 29)    # a Monday
    assert hd.runs_as_sunday(holiday, SCHEDULES[function], {holiday}) is stops
    assert hd.runs_as_sunday(date(2024, 7, 30), SCHEDULES[function], {holiday}) is False
    assert q._day_kind(holiday, SCHEDULES[function], {holiday}) == (2 if stops else 0)


def test_fewer_vehicles_come_to_a_closed_office_on_a_holiday_but_not_to_a_hospital():
    holiday, normal = date(2024, 7, 29), date(2024, 7, 30)
    office, hospital = SCHEDULES['office_daytime'], SCHEDULES['healthcare_24h']
    factors = office['day_factors_weekday_saturday_sunday']
    assert factors[q._day_kind(holiday, office, {holiday})] < factors[q._day_kind(normal, office, {holiday})]
    factors = hospital['day_factors_weekday_saturday_sunday']
    assert factors[q._day_kind(holiday, hospital, {holiday})] == factors[q._day_kind(normal, hospital, {holiday})]


def test_weather_correction_keeps_the_dew_point_and_needs_every_cell():
    index = pd.date_range('2023-01-01', periods=48, freq='H')
    frame = pd.DataFrame({'T2M': 25.0, 'RH2M': 80.0}, index=index)
    deltas = np.zeros((12, 24))
    deltas[0, 15] = 2.0
    out = wc.correct_weather(frame, deltas.tolist())
    afternoon = out.index.hour == 15
    assert (out['T2M'][afternoon] == 27.0).all() and (out['T2M'][~afternoon] == 25.0).all()
    before = 0.8*wc._saturation_kpa(25.0)
    assert out['RH2M'][afternoon].iloc[0]/100*wc._saturation_kpa(27.0) == pytest.approx(before)
    with pytest.raises(ValueError, match='288'):
        wc.fit_month_hour_deltas(frame['T2M'], frame['T2M'])


def test_the_committed_correction_improves_the_years_it_was_not_fitted_on():
    table = wc.load_table()
    assert np.asarray(table['deltas_c_month_hour']).shape == (12, 24) and '2023' in table['fitted_on']
    for year in ('2024', '2025'):
        row = table['out_of_sample'][year]
        assert row['corrected']['rmse_c'] < row['reanalysis']['rmse_c']
        gap = row['reanalysis']['station_mean_daily_max_c']
        assert abs(row['corrected']['mean_daily_max_c'] - gap) < abs(row['reanalysis']['mean_daily_max_c'] - gap)


def _building(tmp_path, *, hours=24*28, cooling=30.0, day_types=None):
    t = np.arange(hours)
    day = np.asarray(day_types if day_types is not None else 1 + (t//24) % 7)
    pd.DataFrame({'month': 1, 'hour': t % 24, 'day_type': day, 'non_shiftable_load': 60.0, 'cooling_demand': cooling,
                  'dhw_demand': 0.0, 'occupant_count': 20.0, 'indoor_dry_bulb_temperature': 24.0,
                  'indoor_relative_humidity': 98.0}).to_csv(tmp_path/'Building_1.csv', index=False)
    weather = pd.DataFrame({'outdoor_dry_bulb_temperature': 30.0, 'outdoor_relative_humidity': 75.0,
                            'diffuse_solar_irradiance': 100.0*((t % 24 >= 7) & (t % 24 < 17)),
                            'direct_solar_irradiance': 300.0*((t % 24 >= 7) & (t % 24 < 17))})
    schema = {'buildings': {'Building_1': {'dynamics': {'type': 'citylearn.v3.thermal.ISO13790Dynamics', 'attributes': {
        'floor_area_m2': 800.0, 'envelope_w_m2k': 2.0, 'solar_aperture_fraction': 0.05, 'ventilation_m3_s': 0.3,
        'mass_class': 'medium', 'set_point': 24.0, 'pressure_kpa': 100.0, 'indoor_rh_pct': 50.0,
        'electric_gain_fraction': 0.5}}}}}
    return schema, weather


def _hold(tmp_path, schedule, schema, weather):
    cop = np.full(len(weather), 3.0)
    return v6.hold_temperature_by_schedule(tmp_path, schema, weather, buildings=(1,), schedules={1: schedule},
                                           cooling_cop=lambda b: cop, max_set_point_c=25.0)


@pytest.mark.parametrize('function', ['office_daytime', 'school_daytime', 'healthcare_24h'])
def test_temperature_is_held_in_the_operating_hours_of_each_function(tmp_path, function):
    schedule = SCHEDULES[function]
    schema, weather = _building(tmp_path)
    before = pd.read_csv(tmp_path/'Building_1.csv')
    report = _hold(tmp_path, schedule, schema, weather)
    v6.write_indoor_temperature(tmp_path, schema, weather, buildings=(1,), band_c=2.0, comfort_limit_c=25.0)
    out = pd.read_csv(tmp_path/'Building_1.csv')
    operating = v6.operating_hours(out, schedule)
    theta = out['indoor_dry_bulb_temperature'].to_numpy()
    point = min(float(schedule['cooling_setpoint_c']), 25.0)
    assert theta[operating].max() <= point + 0.05 and report[1]['set_point_c'] == point
    assert out['cooling_demand'][~operating].sum() == 0.0                        # the equipment follows the function
    # the bill of the month does not change
    electric = out['non_shiftable_load'] + out['cooling_demand']/3.0
    assert electric.sum() == pytest.approx((before['non_shiftable_load'] + before['cooling_demand']/3.0).sum(), rel=1e-4)
    assert out['indoor_relative_humidity'][operating].max() < 70.0
    limit = out['indoor_dry_bulb_temperature_cooling_set_point'][operating] + 2.0
    assert limit.max() <= 25.0 + 0.05 or theta[operating].max() > 23.0


def test_a_closed_day_of_an_office_has_no_cooling_but_a_hospital_keeps_it(tmp_path):
    frame = pd.DataFrame({'hour': [10, 10, 10, 3], 'day_type': [1, 6, 7, 1]})
    assert v6.operating_hours(frame, SCHEDULES['office_daytime']).tolist() == [True, False, False, False]
    assert v6.operating_hours(frame, SCHEDULES['healthcare_24h']).tolist() == [True, True, True, True]
    assert v6.operating_hours(frame, SCHEDULES['port_extended']).tolist() == [True, True, True, False]


def test_a_month_with_little_electricity_shrinks_the_zone_instead_of_breaking_the_bill(tmp_path):
    schema, weather = _building(tmp_path, cooling=3.0)
    frame = pd.read_csv(tmp_path/'Building_1.csv')
    frame['non_shiftable_load'] = 2.0
    frame.to_csv(tmp_path/'Building_1.csv', index=False)
    report = _hold(tmp_path, SCHEDULES['healthcare_24h'], schema, weather)
    out = pd.read_csv(tmp_path/'Building_1.csv')
    assert report[1]['zone_scale'] < 1.0
    assert (out['non_shiftable_load'] > 0).all()
    assert (out['non_shiftable_load'] + out['cooling_demand']/3.0).sum() == pytest.approx((2.0 + 1.0)*len(out), rel=1e-4)


def test_the_peak_block_of_the_bill_keeps_its_energy(tmp_path):
    schema, weather = _building(tmp_path, cooling=20.0)
    frame = pd.read_csv(tmp_path/'Building_1.csv')
    frame['non_shiftable_load'] = np.where(frame['hour'].isin([18, 19, 20, 21, 22]), 2.0, 40.0)
    frame.to_csv(tmp_path/'Building_1.csv', index=False)
    block = frame['hour'].isin([18, 19, 20, 21, 22])
    before = frame['non_shiftable_load'] + frame['cooling_demand']/3.0
    cop = np.full(len(weather), 3.0)
    v6.hold_temperature_by_schedule(tmp_path, schema, weather, buildings=(1,), schedules={1: SCHEDULES['healthcare_24h']},
                                    cooling_cop=lambda b: cop, max_set_point_c=25.0, peak_hours={18, 19, 20, 21, 22})
    out = pd.read_csv(tmp_path/'Building_1.csv')
    after = out['non_shiftable_load'] + out['cooling_demand']/3.0
    assert after[block].sum() == pytest.approx(before[block].sum(), rel=1e-5)
    assert after[~block].sum() == pytest.approx(before[~block].sum(), rel=1e-5)


def test_the_zone_cannot_need_more_than_the_peak_of_the_bill(tmp_path):
    schema, weather = _building(tmp_path, cooling=60.0)
    cop = np.full(len(weather), 3.0)
    report = v6.hold_temperature_by_schedule(tmp_path, schema, weather, buildings=(1,), schedules={1: SCHEDULES['healthcare_24h']},
                                             cooling_cop=lambda b: cop, max_set_point_c=25.0,
                                             peak_caps=lambda b: np.full(len(weather), 1.0))
    out = pd.read_csv(tmp_path/'Building_1.csv')
    assert report[1]['zone_scale'] < 1.0 and (out['cooling_demand']/3.0).max() <= 1.0


def test_settling_keeps_the_zone_of_the_schema(tmp_path):
    schema, weather = _building(tmp_path)
    _hold(tmp_path, SCHEDULES['healthcare_24h'], schema, weather)
    area = schema['buildings']['Building_1']['dynamics']['attributes']['floor_area_m2']
    cop = np.full(len(weather), 3.0)
    report = v6.hold_temperature_by_schedule(tmp_path, schema, weather, buildings=(1,), schedules={1: SCHEDULES['healthcare_24h']},
                                             cooling_cop=lambda b: cop, max_set_point_c=25.0, fit_zone=False)
    assert report[1]['zone_scale'] == 1.0
    assert schema['buildings']['Building_1']['dynamics']['attributes']['floor_area_m2'] == pytest.approx(area)


def test_shortfall_moves_inside_the_month_and_keeps_its_energy():
    months = np.array([1, 1, 1, 1, 2, 2])
    out = v6._move_within_month(np.array([-1.0, 5.0, 5.0, 5.0, 1.0, 1.0]), months)
    assert out[:4].sum() == pytest.approx(14.0) and out.min() > 0.0 and out[4:].tolist() == [1.0, 1.0]
    with pytest.raises(ValueError, match='exceeds'):
        v6._move_within_month(np.array([-1.0, 0.5]), np.array([1, 1]))


def test_opening_windows_cools_a_hot_closed_building_and_only_when_it_helps():
    from citylearn.v3 import thermal as th
    hours = 24*7
    t = np.arange(hours)
    sun = 500.0*((t % 24 >= 7) & (t % 24 < 17))
    inputs = th.ThermalInputs(theta_e=np.full(hours, 30.0), rh_e=np.full(hours, 75.0), irradiance_w_m2=sun,
                              electric_gain_w=np.zeros(hours), occupants=np.zeros(hours), pressure_kpa=100.0)
    p = th.iso13790_parameters(floor_area_m2=500.0, envelope_w_m2k=2.0, solar_aperture_fraction=0.1,
                               ventilation_w_k=th.ventilation_conductance_w_k(0.1))
    closed = th.simulate_delivered(p, inputs, np.zeros(hours), ventilation_m3_s=0.1, w_in=0.009, theta_m0=30.0)
    opened = th.simulate_delivered(p, inputs, np.zeros(hours), ventilation_m3_s=0.1, w_in=0.009, theta_m0=30.0,
                                   natural_ventilation_m3_s=2.0)
    assert opened.max() < closed.max() - 2.0 and opened.min() >= 30.0 - 1e-6
    cool = th.ThermalInputs(theta_e=np.full(hours, 35.0), rh_e=np.full(hours, 75.0), irradiance_w_m2=np.zeros(hours),
                            electric_gain_w=np.zeros(hours), occupants=np.zeros(hours), pressure_kpa=100.0)
    same = th.simulate_delivered(p, cool, np.zeros(hours), ventilation_m3_s=0.1, w_in=0.009, theta_m0=24.0,
                                 natural_ventilation_m3_s=2.0)
    assert np.allclose(same, th.simulate_delivered(p, cool, np.zeros(hours), ventilation_m3_s=0.1, w_in=0.009, theta_m0=24.0))


def test_rounding_of_the_csv_does_not_keep_the_windows_closed():
    from citylearn.v3 import thermal as th
    hours = 24*7
    inputs = th.ThermalInputs(theta_e=np.full(hours, 28.0), rh_e=np.full(hours, 75.0), irradiance_w_m2=np.full(hours, 300.0),
                              electric_gain_w=np.zeros(hours), occupants=np.ones(hours), pressure_kpa=100.0)
    p = th.iso13790_parameters(floor_area_m2=300.0, envelope_w_m2k=2.0, solar_aperture_fraction=0.1,
                               ventilation_w_k=th.ventilation_conductance_w_k(0.1))
    points = np.full(hours, 99.0)
    series = th.ideal_cooling_series(p, inputs, set_point=points, ventilation_m3_s=0.1, w_in=0.009, theta_m0=24.0,
                                     natural_ventilation_m3_s=1.0)
    delivered = np.round(series['latent_w']/1000.0, 6)     # only the latent load, as a CSV writes it
    theta = th.simulate_delivered(p, inputs, delivered, ventilation_m3_s=0.1, w_in=0.009, theta_m0=24.0,
                                  natural_ventilation_m3_s=1.0)
    assert np.allclose(theta, series['theta_air'], atol=1e-3)


def test_the_gate_detects_a_sealed_box_off_hours(tmp_path):
    schema, weather = _building(tmp_path)
    frame = pd.read_csv(tmp_path/'Building_1.csv')
    office = {1: SCHEDULES['office_daytime']}
    frame['indoor_dry_bulb_temperature'] = np.where(v6.operating_hours(frame, office[1]), 24.0, 39.0)
    frame.to_csv(tmp_path/'Building_1.csv', index=False)
    outdoor = weather['outdoor_dry_bulb_temperature'].to_numpy()
    args = dict(buildings=(1,), schedules=office, low_c=18.0, high_c=25.0, outdoor_c=outdoor)
    assert v6.indoor_temperature_gate(tmp_path, schema, off_hours_excess_c=6.0, **args)['passed'] is False    # 39 - 30 is 9
    assert v6.indoor_temperature_gate(tmp_path, schema, off_hours_excess_c=10.0, **args)['passed'] is True


def test_the_gate_rejects_the_extremes_found_in_trial11(tmp_path):
    schema, _ = _building(tmp_path)
    frame = pd.read_csv(tmp_path/'Building_1.csv')
    good = {1: SCHEDULES['healthcare_24h']}
    frame['indoor_dry_bulb_temperature'] = 22.0
    frame.to_csv(tmp_path/'Building_1.csv', index=False)
    assert v6.indoor_temperature_gate(tmp_path, schema, buildings=(1,), schedules=good, low_c=18.0, high_c=25.0)['passed']
    for extreme in (60.4, -12.9):
        frame['indoor_dry_bulb_temperature'] = extreme
        frame.to_csv(tmp_path/'Building_1.csv', index=False)
        assert not v6.indoor_temperature_gate(tmp_path, schema, buildings=(1,), schedules=good, low_c=18.0, high_c=25.0)['passed']
