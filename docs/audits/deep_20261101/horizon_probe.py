"""Analytical reproduction of the default frozen-evaluation horizon contract."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path

from uc3m.application.evaluation import kpi_contract as kc

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


if __name__ == '__main__':
    schema = json.loads((ROOT/'data/campaigns/iquitos_v1/splits/train_2023/schema.json').read_text(encoding='utf-8'))
    time_steps = schema['simulation_end_time_step'] - schema['simulation_start_time_step'] + 1
    taken = min(time_steps, time_steps - 1)  # exact default expression in run_frozen_episode
    start = datetime(2023, 1, 1, tzinfo=timezone(timedelta(hours=-5)))
    stamps = tuple((start + timedelta(hours=t)).isoformat() for t in range(taken))
    power = tuple(float(1 + t % 24) for t in range(taken))
    trace = kc.PhysicalTrace(stamps, 3600, ('B1',), {'B1': {'net_power': power}},
        {'price': (0.2,)*taken, 'carbon_intensity': (0.79,)*taken},
        {'net_power': 'kW', 'price': 'USD/kWh', 'carbon_intensity': 'kgCO2/kWh'},
        'USD', 'AUDIT_SYNTHETIC_ONLY', 'AUDIT_SYNTHETIC_EXOGENOUS')
    catalog = kc.load_kpi_catalog(ROOT/'configs/evaluation/kpis.yaml')
    report = kc.compute_fresh_kpis(trace, trace, catalog)
    validation = kc.validate_kpi_report(report, catalog)
    result = {'native_training_launched': False, 'reproduction': 'analytical trace using the real declared split horizon',
        'time_steps': time_steps, 'default_taken': taken,
        'daily_primary_availability': {k: report.values[k] for k in ('district_daily_peak', 'one_minus_load_factor')},
        'kpi_validation_passed': validation.passed, 'validation_reasons': list(validation.reasons)}
    (OUT/'horizon_probe.json').write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(json.dumps(result, indent=2))
