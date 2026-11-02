"""Bounded audit reproductions; synthetic inputs stay in TemporaryDirectory.

No training, network calls, checkpoint loading or edits to campaign inputs.
Run using the canonical environment from the repository root.
"""
import dataclasses
import hashlib
import json
from pathlib import Path
import tempfile
import warnings
import zipfile
import xml.etree.ElementTree as ET

import pandas as pd

from uc3m.application.training import fresh_campaign as fc
from uc3m.application.dataset.construction import hash_directory
from uc3m.application.dataset.provenance import sha256_file
from uc3m.application.evaluation.fresh_analysis import SeedTable, FrozenProtocol, analyze_campaign

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
CAMPAIGN = ROOT/'data/campaigns/iquitos_v1'


def save(name, value):
    (OUT/name).write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False), encoding='utf-8')


def main():
    results = {}
    config = fc.load_campaign_config(ROOT/'configs/experiments/iquitos.yaml', ROOT)
    dag = fc.build_dag(config, ROOT)
    confirm = next(t for t in dag.treatments if t.stage == 'confirm' and t.algorithm == 'HAPPO')
    sensitivity = next(t for t in dag.treatments if t.stage == 'sensitivity' and t.algorithm == 'HAPPO')
    results['hpo_and_sensitivity'] = {
        'confirm_hyperparameters': confirm.hyperparameters,
        'hpo_candidates': len(dag.candidates), 'confirm_weights': list(confirm.weights),
        'sensitivity_weights': list(sensitivity.weights),
        'identical_native_arguments': list(confirm.native_arguments) == list(sensitivity.native_arguments),
        'sensitivity_requires': list(sensitivity.requires),
        'note': 'DAG arguments before run_stage materialization. Identical arguments alone do not test the runtime catalog; compare with the source revision and focused contract tests.'}

    with tempfile.TemporaryDirectory(prefix='madrl_audit_') as temporary:
        artifacts = Path(temporary)/'campaign'
        fc.prepare_campaign(ROOT/'configs/experiments/iquitos.yaml', ROOT, artifact_root=artifacts)
        path = artifacts/'stages/pilot.json'
        payload = json.loads(path.read_text(encoding='utf-8'))
        payload['treatments'][0]['native_arguments'] += ['--audit-synthetic-tamper']
        path.write_text(json.dumps(payload), encoding='utf-8')
        manifest = json.loads((artifacts/'campaign_manifest.json').read_text(encoding='utf-8'))
        calls = []

        def learner(row, attempt):
            calls.append(row['treatment_id'])
            return None  # a probe, not training evidence

        try:
            result = fc.run_stage(artifacts/'campaign_manifest.json', 'pilot', learner, ROOT, authorized=True)
            results['stage_integrity'] = {'tampered_sha_differs': hashlib.sha256(path.read_bytes()).hexdigest()
                != manifest['stages']['pilot']['sha256'], 'learner_calls': len(calls),
                'rejected_before_learner': False, 'result_status': result['status']}
        except Exception as exc:
            results['stage_integrity'] = {'error': type(exc).__name__, 'learner_calls': len(calls)}

        manifest['configuration_freezes'] = {'unverified_audit_marker': True}
        (artifacts/'campaign_manifest.json').write_text(json.dumps(manifest), encoding='utf-8')
        # Reduce synthetic workload only; no source or genuine manifest is changed.
        stage_path = artifacts/'stages/sensitivity.json'
        sensitivity_rows = json.loads(stage_path.read_text(encoding='utf-8'))
        sensitivity_rows['treatments'] = sensitivity_rows['treatments'][:1]
        stage_path.write_text(json.dumps(sensitivity_rows), encoding='utf-8')
        calls.clear()
        try:
            result = fc.run_stage(artifacts/'campaign_manifest.json', 'sensitivity', learner, ROOT, authorized=True)
            results['freeze_and_derived_catalog'] = {'learner_calls': len(calls),
                'unverified_freeze_accepted': bool(calls), 'derived_scenario_catalog_provided': False,
                'result_status': result['status']}
        except Exception as exc:
            results['freeze_and_derived_catalog'] = {'error': type(exc).__name__, 'learner_calls': len(calls)}

    protocol = dataclasses.replace(FrozenProtocol.default(), resamples=20)
    rows = [{'campaign_id': 'AUDIT_SYNTHETIC_INVALID', 'algorithm': a, 'scenario': s, 'seed': seed,
             'split': protocol.split, 'endpoint': axis, 'value': float('nan'), 'kpi_report_sha256': 'not-a-hash'}
            for a in protocol.algorithms for s, axis in protocol.endpoints for seed in protocol.seeds]
    with warnings.catch_warnings(record=True) as recorded:
        report = analyze_campaign(SeedTable.from_rows(rows), protocol)
    results['nonfinite_statistics'] = {'input': '144 synthetic rows with NaN and invalid report hashes',
        'coverage_complete': report.coverage['complete'], 'decisions': report.decisions,
        'warning_count': len(recorded), 'rejects_invalid_data': False}
    save('probes.json', results)
    print(json.dumps(results, indent=2))

    acceptance = json.loads((CAMPAIGN/'dataset_acceptance.json').read_text(encoding='utf-8'))
    build = json.loads((CAMPAIGN/'dataset_build_manifest.json').read_text(encoding='utf-8'))
    provenance = json.loads((CAMPAIGN/'provenance.json').read_text(encoding='utf-8'))
    split = json.loads((CAMPAIGN/'split_manifest.json').read_text(encoding='utf-8'))
    normalizer = json.loads((CAMPAIGN/'normalizer.json').read_text(encoding='utf-8'))
    actual_files, actual_hash = hash_directory(CAMPAIGN/'dataset')
    raw_mismatches = [s['path'] for s in provenance['sources']
                      if not (ROOT/s['path']).is_file() or sha256_file(ROOT/s['path']) != s['sha256']]
    data = {'acceptance': {k: acceptance[k] for k in ('campaign_id', 'dataset_hash', 'dataset_verified',
        'balance_checks', 'balance_failure_count', 'modeled_monthly_targets', 'measured_monthly_targets')},
        'actual_dataset_hash': actual_hash, 'dataset_hash_matches': actual_hash == acceptance['dataset_hash'],
        'file_table_matches': actual_files == build['files'], 'file_count': len(actual_files),
        'raw_sources': len(provenance['sources']), 'raw_source_hash_mismatches': raw_mismatches,
        'normalizer_fit_scope': normalizer['fit_scope'], 'splits': []}
    for s in split['splits']:
        directory = CAMPAIGN/'splits'/s['directory']
        _, digest = hash_directory(directory)
        schema = json.loads((directory/'schema.json').read_text(encoding='utf-8'))
        data['splits'].append({'id': s['split_id'], 'rows': s['rows'], 'hash_matches': digest == s['sha256'],
            'active_predicted_fields': [n for n, v in schema['observations'].items()
                                        if v.get('active') and '_predicted_' in n],
            'autosized_devices': [b + ':' + n for b, value in schema['buildings'].items()
                                  for n, device in value.items() if isinstance(device, dict) and device.get('autosize')]})
    targets = pd.read_csv(CAMPAIGN/'dataset/monthly_targets.csv')
    data['monthly_targets_columns'] = list(targets.columns)
    data['monthly_targets_provenance'] = targets['provenance'].value_counts().to_dict()
    flags = pd.read_csv(CAMPAIGN/'quality_flags.csv').fillna('')
    data['declared_leakage_rows'] = int(flags['flags'].str.contains('cross_year_leakage_declared').sum())
    data['declared_leakage_scopes'] = flags.loc[flags['flags'].str.contains('cross_year_leakage_declared'), 'scope'].unique().tolist()
    save('dataset_checks.json', data)
    print(json.dumps({k: data[k] for k in ('dataset_hash_matches', 'file_table_matches',
        'raw_source_hash_mismatches', 'declared_leakage_rows')}, indent=2))

    jury = json.loads((ROOT/'data/audits/jury_observations_manifest.json').read_text(encoding='utf-8'))
    status = []
    for entry in jury['observations']:
        old = entry['evidence_path']
        candidate = old.replace('docs/tesis_capitulos/', 'docs/chapters/')
        mapping = {'tools/eval/run_problem_objective_hypothesis_statistical_analysis.py': 'tools/eval/hypothesis.py',
                   'tools/eval/run_complete_drive_kpi_objective_analysis.py': 'tools/eval/objective_analysis.py'}
        candidate = mapping.get(candidate, candidate)
        status.append({**entry, 'declared_path_exists': (ROOT/old).exists(),
                       'candidate_current_path': candidate, 'candidate_exists': (ROOT/candidate).exists()})
    save('jury_paths.json', {'source': jury['source'], 'source_exists': (ROOT/jury['source']).exists(),
                            'observations': status})

    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
    doc_rows = []
    patterns = {'security_privacy': r'seguridad|privacidad|ciberseguridad',
                'source_code_url': r'github\.com/Mac-Tapia/MADRLCitytleranflexresdr',
                'general_introduction': r'introducci[oó]n general',
                'old_campaign': r'madrl_v3_20260627|49/50|50 episodios|600 episodios',
                'no_reject': r'no se rechaza|no rechazar',
                'seven_axes': r'siete ejes|7 ejes'}
    import re
    for name in ('tesis.docx', 'informe.docx', 'auditoria_tesis.docx'):
        path = ROOT/'docs'/name
        if not path.is_file():
            doc_rows.append({'path': 'docs/' + name, 'exists': False})
            continue
        with zipfile.ZipFile(path) as archive:
            xml = ET.fromstring(archive.read('word/document.xml'))
            paragraphs = [''.join(t.text or '' for t in p.findall('.//w:t', ns)) for p in xml.findall('.//w:p', ns)]
        text = '\n'.join(paragraphs)
        doc_rows.append({'path': 'docs/' + name, 'exists': True, 'sha256': sha256_file(path),
            'paragraphs': len(paragraphs), 'terms': {k: len(re.findall(v, text, re.I)) for k, v in patterns.items()},
            'review': 'XML textual extraction only; no rendering, pagination or validation of scientific claims'})
        (OUT/(name + '.txt')).write_text(text, encoding='utf-8')
    save('word_checks.json', doc_rows)


if __name__ == '__main__':
    main()
