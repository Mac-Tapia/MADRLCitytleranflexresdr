"""Summarize this execution's evidence without adding overlapping test totals.

Run only after the project guard; reads explicit project sources and this
execution's JUnit files. Never traverses browser state, models or other repos.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import xml.etree.ElementTree as ET
import argparse

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
EVIDENCE = ROOT/'data/maintenance/integracion/c20261101i01'

NOTES = {
    'I00': 'Corte y guard estricto registrados; trabajo previo conservado. La revisión semántica y propiedad por archivo siguen parciales.',
    'I01': 'Lector común estricto: cobertura exacta, propietarios, parámetros nativos/congelados y gate JUnit/código/campaña. La cobertura integral exige el perfil final.',
    'I02': 'Decisión v1, diferencias PT, tupla, confusores y bibliografía documentados. Word conservado; dimensiones atribuidas al corte medido.',
    'I03': 'Costo/precios por edificio y huella exógena corregidos. No se transforma costo firmado en factura comercial; procedencia temporal v1 conserva sus límites.',
    'I04': 'Contrato con hash, argumentos releídos, interacciones reales y corrección autorizada de persistencia ValueNorm GPU. Acciones diferentes siguen como confusor v1.',
    'I05': 'Prueba de presupuesto por intento antes del aprendiz. Sin calibración anual; memoria estimada MASAC supera este equipo y algunas GPU de 80 GB.',
    'I06': 'Parche CityLearn y límite de liquidación autorizados; 24/48 acciones y evaluación terminal nativa verificadas. Sin evaluación anual real nueva.',
    'I07': 'Ilustrativos solo con opción explícita; incertidumbre no disponible para una réplica; inferencia por semilla, bootstrap acotado e inaplicabilidad estructural congelada.',
    'I08': 'Análisis registrado, entrega preparada/releída, gates explícitos y CLI con error no cero. Sin análisis anual final real.',
    'I09': 'Snapshots inmutables por streaming, diario de copia interrumpida, restauración contenida y postprocesamiento/test añadidos. Falta desconexión real Colab.',
    'I10': 'Inferencia validada y clipping por petición; panel de solo lectura drena cuerpos hasta4KiB con plazo total2s y rechazo405. Sin ONNX real ni OT.',
    'I11': 'Namespace offpolicy declarado/acotado, wheel del núcleo instalado y probado, licencias con excepciones previas limitadas. Entrenamiento nativo aún requiere checkout.',
    'I12': 'Flujo estático v1, disparadores CI de ramas/manuales, Ruff y descubrimiento local corregidos. Sin ejecución alojada de Actions.',
    'I13': 'Rutas críticas revisadas independientemente y defectos adversariales reproducidos. No se acredita revisión semántica completa de 773 archivos.',
    'I14': 'Referencias activas corregidas, README/workflow originales archivados y fallos base corregidos. Conservados obsoletos y archivos con propietario por resolver.',
    'I15': 'Fixtures crean microcampañas vinculadas nuevas, sin scratch anterior. JUnit vigente determina aceptación; cortes fallidos/cancelados no son modelos aprobados.',
    'I16': 'Campaña anual sin autorización: authorized_stages canónico vacío. Sin infraestructura pagada ni aprendiz anual iniciado.',
    'I17': 'Cierre empírico de tesis/jurado necesita campaña final y validación Word; documentos conservados.',
    'I18': 'Piloto físico/SIL/HIL/OT sin ejecución ni aceptación.'}

# Actual implementation paths supplement, rather than rewrite, the original plan.
IMPLEMENTED = {
    'I00': ['tools/ops/capture_modernization_baseline.py'],
    'I01': ['uc3m/application/training/attempt_evidence.py', 'uc3m/application/training/attempt_trust.py',
            'uc3m/application/training/fresh_acceptance.py', 'uc3m/application/training/gate_report.py'],
    'I02': ['docs/decisions/contrato_v1_pt.md'],
    'I03': ['uc3m/application/evaluation/kpi_contract.py', 'uc3m/adapters/citylearn/policy_inference.py',
            'tools/dataset/size_der_microgrids.py'],
    'I04': ['uc3m/adapters/algorithms/native_entrypoint.py', 'uc3m/application/training/cli.py',
            'external/HARL/harl/common/valuenorm.py'],
    'I05': ['uc3m/application/training/budget_evidence.py', 'uc3m/application/training/fresh_campaign.py'],
    'I06': ['CityLearn/citylearn/citylearn.py', 'CityLearn/citylearn/internal/runtime.py',
            'CityLearn/citylearn/internal/kpi.py',
            'uc3m/application/evaluation/frozen_evaluation.py', 'uc3m/application/evaluation/test_access.py'],
    'I07': ['uc3m/application/evaluation/endpoint_applicability.py',
            'uc3m/application/evaluation/fresh_analysis.py', 'uc3m/multicriteria/artifacts.py'],
    'I08': ['uc3m/application/pipeline.py', 'uc3m/application/evaluation/results_catalog.py',
            'uc3m/application/evaluation/fresh_delivery.py', 'uc3m/application/evaluation/analysis_acceptance.py'],
    'I09': ['uc3m/application/training/drive_sync.py'],
    'I10': ['deploy/inference/model_loader.py', 'deploy/inference/app.py', 'uc3m/presentation/training_panel.py'],
    'I11': ['pyproject.toml', 'tools/eval/report_fresh_campaign.py'],
    'I12': ['scripts/verify_project_context.ps1', 'scripts/quality/skill_instruction_paths.ps1',
            'scripts/quality/run_fresh_training_gates.ps1', '.github/workflows/ci.yml', 'tools/ops/fresh_workflow.py'],
    'I13': ['docs/audits/ejecucion_remediacion_20261101/arbol_actual.json'],
    'I14': ['README.md', 'data/audits/evaluation_tools_inventory.json',
            'scripts/maintenance/consolidate_repository.ps1'],
    'I15': ['tests/fresh_training/conftest.py', 'tests/fresh_training/test_real_learning.py',
            'tests/fresh_training/test_dependency_persistence_regressions.py',
            'tests/fresh_training/test_annual_runtime_boundary.py', 'tests/fresh_training/test_panel_http_protocol.py'],
    'I16': [], 'I17': [], 'I18': []}

RUNS = {
    'I01': ['campaign_contract_final.xml', 'I01/readback.xml'],
    'I03': ['integrated_core.xml', 'I12/pv_binary_final.xml'], 'I05': ['budget_cut_final.xml'],
    'I04': ['I15/dependency_green.xml'], 'I06': ['I06/native_boundary_green.xml', 'I15/dependency_green.xml'],
    'I07': ['scientific_chain_final.xml', 'I07/seed_contracts_final.xml'],
    'I08': ['scientific_chain_final.xml', 'I08/delivery.xml'],
    'I09': ['budget_cut_final.xml', 'I09/general_failures_current.xml', 'I09/postprocessing.xml'],
    'I10': ['I10/inference.xml', 'I10/panel_deadline_green.xml'], 'I11': ['I11/package.xml'],
    'I15': ['I15/dependency_green.xml'],
    'I12': ['I12/maintenance.xml'], 'I14': ['I12/maintenance.xml']}


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fresh-gate', type=Path, help='Explicit final gate; never discover the newest report.')
    parser.add_argument('--native-summary', type=Path, help='Explicit strict native readback summary, if completed.')
    args = parser.parse_args()
    gate = None
    if args.fresh_gate:
        gate_path = args.fresh_gate.resolve()
        gate_path.relative_to(ROOT)
        gate = {'path': gate_path.relative_to(ROOT).as_posix(), 'sha256': sha(gate_path),
                'report': json.loads(gate_path.read_text(encoding='utf-8-sig'))}
    plan = json.loads((ROOT/'docs/plans/remediacion_integrada.json').read_text(encoding='utf-8'))
    junit = []
    junit_paths = set(EVIDENCE.rglob('*.xml'))
    junit_paths.add(ROOT/'data/maintenance/gates/fresh_profile_20261102T055542017Z.xml')
    if gate:
        gate_junit = (gate_path.parent/gate['report']['junit']).resolve()
        gate_junit.relative_to(ROOT)
        if sha(gate_junit) != gate['report']['junit_sha256']:
            raise ValueError('Explicit fresh gate JUnit hash does not match')
        junit_paths.add(gate_junit)
    for path in sorted(junit_paths):
        suites = ET.parse(path).getroot()
        cases = list(suites.iter('testcase'))
        failed = [c.get('name') for c in cases if c.find('failure') is not None]
        errors = [c.get('name') for c in cases if c.find('error') is not None]
        skipped = [c.get('name') for c in cases if c.find('skipped') is not None]
        junit.append({'path': path.relative_to(ROOT).as_posix(), 'sha256': sha(path), 'tests': len(cases),
            'passed': len(cases)-len(failed)-len(errors)-len(skipped),
            'failed': failed, 'errors': errors, 'skipped': skipped})
    tasks = []
    for task in plan['tasks']:
        status = ('blocked' if task['id'] == 'I16' else 'pending' if task['id'] in ('I17', 'I18') else 'partial')
        tasks.append({'task_id': task['id'], 'title': task['title'], 'status': status,
            'notes': NOTES[task['id']], 'planned_files': task['files'], 'planned_tests': task['tests'],
            'implementation_files': {p: sha(ROOT/p) for p in IMPLEMENTED[task['id']]},
            'verification_runs': [str((EVIDENCE/p).relative_to(ROOT).as_posix()) for p in RUNS.get(task['id'], [])],
            'gate': task['gate'], 'reviewer': 'coordinator plus bounded independent read-only review'})
    owned = ['uc3m/application/training/attempt_trust.py', 'uc3m/application/training/attempt_evidence.py',
        'uc3m/application/training/fresh_acceptance.py', 'uc3m/application/training/gate_report.py',
        'uc3m/application/training/drive_sync.py', 'uc3m/application/training/fresh_campaign.py',
        'uc3m/application/training/cli.py', 'uc3m/adapters/algorithms/native_entrypoint.py',
        'uc3m/application/training/integrity.py', 'uc3m/application/training/budget_evidence.py',
        'tools/dataset/size_der_microgrids.py',
        'uc3m/application/evaluation/endpoint_applicability.py', 'uc3m/application/evaluation/fresh_analysis.py',
        'uc3m/multicriteria/artifacts.py', 'uc3m/multicriteria/pipeline.py',
        'deploy/inference/model_loader.py', 'deploy/inference/app.py',
        'scripts/verify_project_context.ps1', 'scripts/quality/skill_instruction_paths.ps1',
        'scripts/quality/run_fresh_training_gates.ps1', 'tools/ops/fresh_workflow.py',
        'tools/ops/verify_workflow_integrity.py', 'tools/ops/audit_github_readiness.py',
        'tools/ops/capture_modernization_baseline.py',
        'uc3m/adapters/citylearn/policy_inference.py', 'uc3m/application/pipeline.py',
        'uc3m/application/evaluation/analysis_acceptance.py', 'uc3m/application/evaluation/test_access.py',
        'uc3m/application/evaluation/fresh_delivery.py', 'uc3m/application/evaluation/frozen_evaluation.py',
        'uc3m/application/evaluation/kpi_contract.py', 'uc3m/application/evaluation/results_catalog.py',
        'CityLearn/citylearn/citylearn.py', 'CityLearn/citylearn/internal/runtime.py']
    owned += ['CityLearn/citylearn/internal/kpi.py', 'external/HARL/harl/common/valuenorm.py',
              'uc3m/presentation/training_panel.py']
    record = {'schema_version': 1, 'cut_id': 'c20261101i01', 'at_utc': datetime.now(timezone.utc).isoformat(),
        'implementation_executed': True, 'implementation_ready_for_training': False,
        'software_acceptance': bool(gate and gate['report'].get('software_acceptance') is True),
        'scientific_acceptance': False, 'operational_acceptance': False,
        'methodological_decision': 'preserve v1 and document PT differences',
        'native_authorization': 'three CityLearn files and HARL ValueNorm expressly authorized; bounded microtests, no annual campaign',
        'source_hashes': {p: sha(ROOT/p) for p in owned},
        'original_plan_sha256': sha(ROOT/'docs/plans/remediacion_integrada.json'),
        'fresh_software_gate': gate,
        'native_micro_summary': ({'path': args.native_summary.resolve().relative_to(ROOT).as_posix(),
            'sha256': sha(args.native_summary), 'report': json.loads(args.native_summary.read_text(encoding='utf-8'))}
            if args.native_summary else None),
        'previous_failed_native_profile': {'path': 'data/maintenance/gates/fresh_profile_20261102T055542017Z.json',
            'report': json.loads((ROOT/'data/maintenance/gates/fresh_profile_20261102T055542017Z.json').read_text(encoding='utf-8-sig'))},
        'interrupted_profile_reports': {
            p: {'sha256': sha(ROOT/p), 'report': json.loads((ROOT/p).read_text(encoding='utf-8-sig'))}
            for p in ['data/maintenance/gates/fresh_profile_20261102T053551244Z.json',
                      'data/maintenance/gates/fresh_profile_20261102T055329077Z.json']},
        'requirement_mapping': plan['coverage'], 'tasks': tasks, 'junit': junit,
        'test_accounting': 'Each JUnit is a separate run; cases overlap and must not be summed.',
        'limitations': ['Read original logs for interrupted runs without JUnit.',
            'No full semantic file-by-file completion, real Colab recovery, annual campaign or OT acceptance.',
            'Three existing license exceptions allow local reproduction, not general redistribution.']}
    (OUT/'estado_ejecucion.json').write_text(json.dumps(record, indent=2, ensure_ascii=True)+'\n', encoding='utf-8')
    lines = ['# Evidencia y estado por tarea', '',
             'Generado desde plan y JUnit originales. Las filas no suman pruebas de ejecuciones superpuestas.', '',
             '| Tarea | Estado integral | Evidencia y límite |', '|---|---|---|']
    lines += [f"| {t['task_id']} | {t['status']} | {t['notes']} |" for t in tasks]
    lines += ['', '| JUnit | Aprobadas | Fallos | Errores | Omisiones |', '|---|---:|---:|---:|---:|']
    for row in junit:
        label = row['path'].removeprefix('data/maintenance/integracion/c20261101i01/')
        lines.append(f"| {label} | {row['passed']} | {len(row['failed'])} | {len(row['errors'])} | {len(row['skipped'])} |")
    (OUT/'evidencia.md').write_text('\n'.join(lines)+'\n', encoding='utf-8')
    print(json.dumps({'tasks': len(tasks), 'junit_runs': len(junit), 'scientific_acceptance': False}))


if __name__ == '__main__':
    main()
