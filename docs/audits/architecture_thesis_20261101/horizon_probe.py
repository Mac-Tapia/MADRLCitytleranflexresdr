"""Analytical horizon/KPI boundary probe; no annual simulation or learning."""
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
OUT = Path(__file__).resolve().parent


def main():
    from uc3m.application.evaluation import kpi_contract as kc
    catalog = kc.load_kpi_catalog(ROOT/'configs/evaluation/kpis.yaml')
    manifest = json.loads((ROOT/'data/campaigns/iquitos_v1/split_manifest.json').read_text(encoding='utf-8'))
    results = []
    for split in manifest['splits']:
        rows = int(split['rows'])
        taken = rows - 1  # exact default in policy_inference.run_frozen_episode:242
        start = datetime.fromisoformat(split['start'])
        stamps = tuple((start + timedelta(hours=t)).isoformat() for t in range(taken))
        power = tuple(float(1+t % 24) for t in range(taken))
        trace = kc.PhysicalTrace(stamps, 3600, ('B1',), {'B1': {'net_power': power}},
                  {'price': (0.2,)*taken, 'carbon_intensity': (0.79,)*taken},
                  {'net_power': 'kW', 'price': 'USD/kWh', 'carbon_intensity': 'kgCO2/kWh'},
                  'USD', 'AUDIT_SYNTHETIC_ANALYTICAL_ONLY', '0'*64)
        report = kc.compute_fresh_kpis(trace, trace, catalog)
        validation = kc.validate_kpi_report(report, catalog)
        results.append({'split': split['split_id'], 'rows': rows, 'default_actions': taken,
                        'passed': validation.passed, 'reasons': list(validation.reasons),
                        'daily_primaries': {k: report.values[k] for k in ('district_daily_peak', 'one_minus_load_factor')}})
    payload = {'scope': 'analytical synthetic trace under the real default horizon; no annual run', 'results': results}
    (OUT/'horizon_probe.json').write_text(json.dumps(payload, indent=2), encoding='utf-8')
    print(json.dumps([{'split':r['split'], 'rows':r['rows'], 'actions':r['default_actions'],
                       'passed':r['passed'], 'reasons':r['reasons']} for r in results], indent=2))


if __name__ == '__main__':
    main()
