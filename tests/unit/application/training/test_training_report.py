def test_report_does_not_promote_missing_or_nonfinite_kpis():
    from uc3m.application.evaluation.training_report import build_training_report
    report = build_training_report({'algorithm': 'HAPPO', 'citylearn_v3_report': {'all_values': {'cost': float('nan')}}})
    assert report['kpi_status'] == 'invalid'
    assert report['scientific_acceptance'] is False
    report = build_training_report({'algorithm': 'HAPPO', 'citylearn_v3_report': {'all_values': {'cost': 1.5}}})
    assert report['kpi_rows'] == [{'metric': 'cost', 'value': 1.5}]
    assert report['scientific_acceptance'] is False
