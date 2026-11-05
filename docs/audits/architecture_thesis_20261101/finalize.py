"""Summarize actual audit artifacts, without changing any project source."""
import argparse
import collections
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def write_json(name, payload):
    (OUT/name).write_text(json.dumps(payload, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--pytest-exit-code', type=int, required=True)
    args = parser.parse_args()
    findings = []
    for line in (OUT/'informe.md').read_text(encoding='utf-8').splitlines():
        if line.startswith('| H') and line[3:5].isdigit():
            values = [part.strip() for part in line.strip('|').split('|')]
            findings.append(dict(id=values[0], severity_type=values[1], evidence_impact=values[2], acceptance=values[3]))
    with (OUT/'findings.csv').open('w', newline='', encoding='utf-8-sig') as stream:
        writer = csv.DictWriter(stream, fieldnames=list(findings[0]))
        writer.writeheader()
        writer.writerows(findings)
    inventory = list(csv.DictReader((OUT/'files.csv').open(encoding='utf-8-sig')))
    folders = list(csv.DictReader((OUT/'folders.csv').open(encoding='utf-8-sig')))
    tree = []
    for row in sorted(folders, key=lambda r: r['path'].casefold()):
        prefix = row['path'].rstrip('/')+'/'
        count = sum(r['path'].startswith(prefix) for r in inventory)
        tree.append('  '*row['path'].count('/')+row['path'].split('/')[-1]+f'/ [{row["scope"]}; {count} archivos]')
    (OUT/'tree.txt').write_text('\n'.join(tree)+'\n', encoding='utf-8')
    selected = [r for r in inventory if r.get('sha256') and (
        r['path'].startswith(('uc3m/', 'configs/', 'tests/', 'tools/', 'scripts/', 'governance/'))
        or r['path'] in {'README.md', 'pyproject.toml', 'requirements.txt', 'uv.lock', 'docs/workflow_manifest.json',
                         'PT_TAPIA_ZAMBRANO_v6_Iquitos_2.docx'}
        or r['path'].startswith('docs/architecture/') or r['path'].endswith('.docx'))]
    drift = []
    for row in selected:
        path = ROOT/row['path']
        actual = hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
        if actual != row['sha256']:
            drift.append({'path': row['path'], 'before': row['sha256'], 'after': actual})
    write_json('source_drift.json', {'checked_files': len(selected), 'changed': drift,
                                    'at_utc': datetime.now(timezone.utc).isoformat(),
                                    'scope': 'code/config/tests/governance/architecture/root contract and PT; not all dataset bytes'})
    xml_path = OUT/'pytest.xml'
    if not xml_path.is_file():
        raise RuntimeError('No final JUnit: do not claim the general test suite completed')
    xml = ET.parse(xml_path).getroot()
    suites = list(xml.findall('testsuite')) if xml.tag == 'testsuites' else [xml]
    counts = {key: sum(int(s.attrib.get(key, 0)) for s in suites) for key in ('tests', 'failures', 'errors', 'skipped')}
    counts['passed'] = counts['tests'] - counts['failures'] - counts['errors'] - counts['skipped']
    failures = []
    for case in xml.iter('testcase'):
        for tag in ('failure', 'error', 'skipped'):
            for item in case.findall(tag):
                failures.append({'class': case.get('classname'), 'name': case.get('name'), 'outcome': tag,
                                  'message': item.get('message'), 'detail': (item.text or '')[:30000]})
    write_json('test_failures.json', failures)
    slowest = sorted(({'class': c.get('classname'), 'name': c.get('name'), 'seconds': float(c.get('time', 0))}
                       for c in xml.iter('testcase')), key=lambda r: r['seconds'], reverse=True)[:15]
    write_json('slowest_tests.json', {'scope': 'JUnit elapsed including fixture phases; not a CPU/GPU profile', 'tests': slowest})
    counts['duration_seconds'] = sum(float(s.get('time', 0)) for s in suites)
    summary = {'pytest_exit_code': args.pytest_exit_code, 'tests': counts,
               'excluded_native_microtrainings': 4,
               'excluded_file': 'tests/fresh_training/test_real_learning.py',
               'fresh_profile_acceptance': False, 'scientific_acceptance': False,
               'findings': dict(collections.Counter(r['severity_type'].split(' / ')[0] for r in findings)),
               'source_drift': len(drift), 'thesis_unchanged': not any(r['path'].endswith('.docx') for r in drift)}
    write_json('validation.json', summary)
    lines = [
        '# Verificación final de la auditoría', '',
        'Comando ejecutado desde la raíz con el Python canónico:', '',
        '```powershell',
        '.\\.venv39-citylearn-v3\\Scripts\\python.exe -B -X utf8 -m pytest tests -q -p no:cacheprovider --ignore=tests/fresh_training/test_real_learning.py --junitxml=docs/audits/architecture_thesis_20261101/pytest.xml',
        '```', '',
        f'Código de salida observado: **{args.pytest_exit_code}**. Contadores JUnit: **{counts["passed"]} aprobadas, {counts["failures"]} fallidas, {counts["errors"]} errores, {counts["skipped"]} omitidas; {counts["tests"]} en total**.', '',
        f'Duración JUnit: {counts["duration_seconds"]:.2f} s. Cambios de fuente en el ámbito revalidado: {len(drift)} / {len(selected)} archivos. Ver `source_drift.json`.', '',
        '**Alcance:** suite propia general, con cuatro microentrenamientos nativos excluidos explícitamente. Incluye simulador e inferencia con dependencias locales; varios tests de evaluación usan checkpoints de `.superpowers`, por lo que no acredita un clon limpio. No se ejecutó la puerta integral fresh sin omisiones ni una campaña anual nueva. Los contadores verdes de este ámbito no cierran H20.', '',
        'El JUnit y `pytest.log` son la evidencia de esta ejecución. Las discrepancias se detallan en `test_failures.json`.', '',
        '## Resultados que requieren atención', '',
    ]
    lines.extend(f'- `{r["class"]}::{r["name"]}` — {r["outcome"]}: {(r["message"] or "").replace(chr(10), " ")[:400]}' for r in failures)
    lines.extend(['', '## Dictamen conservado', '',
                  f'{len(findings)} hallazgos: '+', '.join(f'{n} {p}' for p,n in sorted(summary['findings'].items()))+'.',
                  'Layout, workflow, descubrimiento y lint siguen rechazados conforme a sus logs. Aceptación científica: **false**.', ''])
    (OUT/'validation.md').write_text('\n'.join(lines), encoding='utf-8')
    artifact_rows = []
    for path in sorted(OUT.rglob('*')):
        if path.is_file() and path.name != 'artifact_manifest.json':
            artifact_rows.append({'path': path.relative_to(OUT).as_posix(), 'bytes': path.stat().st_size,
                                  'sha256': hashlib.sha256(path.read_bytes()).hexdigest()})
    write_json('artifact_manifest.json', {'scope': 'audit deliverable integrity only, not scientific acceptance', 'files': artifact_rows})
    print(json.dumps(summary, ensure_ascii=True))


if __name__ == '__main__':
    main()
