"""Small auditable report projection; scientific promotion remains separate."""
from uc3m.adapters.algorithms.evidence import finite_kpis


def build_training_report(payload):
    metrics = payload.get('citylearn_v3_report', {}).get('all_values', {})
    valid = finite_kpis(metrics)
    return {
        'algorithm': payload.get('algorithm'),
        'scenario': payload.get('scenario'),
        'kpi_status': 'finite' if valid else 'invalid',
        'kpi_rows': [{'metric': key, 'value': value} for key, value in sorted(metrics.items())] if valid else [],
        'scientific_acceptance': False,
        'acceptance_note': 'Requires full-horizon independent evaluation, baselines and multiseed statistics.',
    }
