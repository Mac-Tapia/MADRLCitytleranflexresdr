"""Recompute monthly energy closure and source targets without generating data."""
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from tools.dataset import build_fresh_campaign_dataset as builder  # noqa: E402


if __name__ == '__main__':
    campaign = ROOT/'data/campaigns/iquitos_v1'
    measured, targets = builder.monthly_targets(campaign/'raw')
    checks = builder.balance_checks(campaign/'dataset', targets)
    failed = [row for row in checks if not row['passed']]
    report = {'read_only': True, 'targets_reconstructed_from_raw': len(targets),
              'measured_input_records': len(measured), 'checks_recomputed': len(checks),
              'failures': len(failed), 'failed_checks': failed,
              'max_relative_error': max(c['relative_error'] or 0 for c in checks),
              'limitation': 'Uses the project COP reconstruction, not an independent meter or native whole-year energy validation.'}
    output = Path(__file__).parent/'physical_checks.json'
    output.write_text(json.dumps(report, indent=2), encoding='utf-8')
    print(json.dumps(report, indent=2))
