"""Build the requested plan from explicit local audit sources; never run training.

Run from the verified repository root. Copies only audit text/inventories, never
browser state, checkpoints or dependency contents. Does not mutate Git.
"""
import csv
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
PLAN = ROOT / 'docs/plans/remediacion_integrada.md'
MATRIX = ROOT / 'docs/plans/remediacion_integrada.json'
SESSION = '865ad199-53fa-4aa9-acc3-c3dfb37f0edd'
AUDIT_LOG = Path.home() / '.claude/projects/d--MADRLCitytleranflexresdr' / (SESSION + '.jsonl')
SCRATCH = Path.home() / 'AppData/Local/Temp/claude/d--MADRLCitytleranflexresdr' / SESSION / 'scratchpad'


def sha(path):
    value = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            value.update(block)
    return value.hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def task(id_, title, deps, files, tests, result, work, basis='L3', gate='G1'):
    return dict(id=id_, title=title, depends_on=deps.split(), files=files.split(),
                tests=tests.split(), acceptance=result, implementation=work,
                scientific_basis=basis.split(), gate=gate, status='planned')


TASKS = [
    task('I00', 'Fijar corte, responsables y cobertura real', '',
         'tools/ops/capture_modernization_baseline.py docs/plans/traspaso_sesiones.md specs/STATUS.md',
         'tests/ops/test_capture_modernization_baseline.py',
         'Corte con HEAD, árbol sucio, submódulos, hashes, fuentes e inventario por archivo; cada observación tiene estado y responsable de verificación.',
         'Comparar las tres auditorías sin sumar inventarios de ámbitos distintos. Incorporar el ledger semántico del Revisor A como pendiente; no convertir lectura EOF en revisión humana. Releer cada defecto antes de editar y registrar avances ya presentes. Acordar un escritor por archivo; los nombres de sesiones anteriores no garantizan propiedad vigente.', gate='G0'),
    task('I01', 'Cerrar la promoción incorrecta en todas las rutas', 'I00',
         'uc3m/application/training/fresh_acceptance.py uc3m/application/training/fresh_campaign.py uc3m/application/evaluation/results_catalog.py uc3m/application/training/drive_sync.py',
         'tests/fresh_training/test_attempt_acceptance.py tests/fresh_training/test_security_and_acceptance.py tests/fresh_training/test_campaign_integrity.py tests/fresh_training/test_fresh_results_catalog.py',
         'Cero pasos/updates, intento o seed ajenos, owners incompletos, checkpoint alterado, cobertura parcial e informe mínimo rechazan aceptación; caso software válido sin análisis conserva aceptación científica falsa.',
         'Reutilizar attempt_evidence_reasons desde treatment_trust_reasons y todas sus relecturas. Comparar el conjunto exacto de tratamientos planificados/completados, sin aceptar duplicados ni extras. Verificar identidad, hashes, cambios de parámetros y evidencia persistida del hijo. Ligar gate_report a campaña, commit+hash del árbol de fuentes, protocolo y SHA-256 del JUnit: rechazar reporte verde ajeno, alterado o de otro corte. Corregir la fixture que codifica evidencia débil, conservando un caso positivo realmente completo. Exigir informe enlazado a manifiesto de análisis y datos verificados; usar promotion_probe.json como casos adversariales, sin tratarlo como evidencia de aprendizaje. Ejecutar addendum_auditoria_20261101/reproductions.py caso P1 adaptando solo las llamadas si cambian firmas: debe rechazar. gate_report.py no parsea XML no verificado: comprobar el SHA-256 del JUnit antes de parsear o usar parser endurecido, con test de XML de expansión de entidades (C70). La fixture base de test_security_and_acceptance debe pasar el contrato estricto (C73).'),
    task('I02', 'Congelar el contrato PT–simulador y la tupla', 'I00',
         'configs/objective_policies.yaml configs/scenarios.yaml configs/experiments/iquitos.yaml configs/algorithms/native.yaml docs/design/entrenamiento.md',
         'tests/fresh_training/test_campaign_contract.py tests/fresh_training/test_temporal_contract.py tests/uc3m/test_reward_kpi_alignment.py',
         'Registro D01–D06 resuelto, contrato versionado con dimensiones y acciones por backend; PT y código tienen correspondencia explícita y ninguna equivalencia se infiere solo del nombre del algoritmo.',
         'Documentar M_e=<N,S,{A_i},P,r_e,{O_i},Z,rho_0,gamma,H>, estado físico frente a entrada del crítico e historial local de política. Declarar HVAC activo/inactivo, códigos EV frente a BACT, acciones continuas/discretas y restricciones de decodificación. Conservar pesos vigentes como decisiones del proyecto hasta la resolución metodológica; no reemplazarlos silenciosamente por los del PT. Especificar tarifa, mercado/net billing, términos de recompensa activos y comparación justa de capacidad/actualizaciones.', 'L1 L2 L4 L5'),
    task('I03', 'Conciliar dataset, procedencia temporal y facturación física', 'I00 I02',
         'tools/dataset/build_fresh_campaign_dataset.py uc3m/application/dataset/construction.py uc3m/application/dataset/provenance.py uc3m/application/dataset/splits.py uc3m/adapters/citylearn/fresh_observations.py uc3m/adapters/citylearn/policy_inference.py',
         'tests/fresh_training/test_dataset_provenance.py tests/fresh_training/test_der_sizing_inputs.py tests/fresh_training/test_temporal_contract.py tests/fresh_training/test_kpi_physical_contract.py',
         'Dataset elegido con identidad nueva si cambia contenido; splits, normalizador, flota/controles y tabla por variable trazables; factura analítica por edificio y sensibilidad a backcast sin fuga oculta.',
         'Distinguir v1 activo de v2/v3 disponibles, sus EV/cargadores, precios y carbono. Aplicar la puerta de sustitución D01 (S1–S11) antes de reenlazar config o eliminar v1. Mantener precios por edificio en la traza si son heterogéneos; verificar unidades, exportación y liquidación. Tratar B01 2023 derivado de 2024 como amenaza explícita con sensibilidad/exclusión predefinida. No rellenar resultados ni sobrescribir fuentes/splits existentes.', 'L1 L2 L5 L6'),
    task('I04', 'Verificar interfaces y capacidad de los cuatro backends', 'I01 I02 I03',
         'uc3m/adapters/algorithms/native_entrypoint.py uc3m/env/wrappers.py uc3m/algorithms/factory.py uc3m/adapters/citylearn/policy_inference.py',
         'tests/fresh_training/test_learning_observer.py tests/fresh_training/test_real_learning.py tests/uc3m/test_algorithm_factory.py',
         'Cuatro aprendices reales con owners/updates/cambios de parámetros, recarga consistente y contrato actor/crítico/acción registrado; placeholder y modo ilustrativo inelegibles.',
         'Comprobar wrapper heredado local/share_obs y número de entornos sin atribuir sus defectos al wrapper HAPPO nativo. Medir entrada de crítico por backend: 1652 común frente a 6069 padded de MATD3 en el corte auditado. Revisar 89 acciones axis y redundancia para agentes pequeños; elegir comparabilidad en D03, enmascarar/explicar acciones según contrato. No copiar entrenadores ni modificar CityLearn/external: si el ajuste exige dependencia protegida, emitir blocked_dependency_interface con parche propuesto y prueba.', 'L1 L2 L4 L5', 'G2'),
    task('I05', 'Presupuesto efectivo, recursos y protocolo HPO coherentes', 'I02 I03 I04',
         'uc3m/application/training/phases.py uc3m/application/training/fresh_campaign.py uc3m/application/training/fresh_tuning.py uc3m/adapters/algorithms/native_entrypoint.py configs/algorithms/native.yaml configs/experiments/iquitos.yaml',
         'tests/fresh_training/test_training_phases.py tests/fresh_training/test_stage_phases.py tests/fresh_training/test_tuning_protocol.py tests/fresh_training/test_campaign_contract.py',
         'DAG, freeze, pesos efectivos, replay/batch y presupuesto real coinciden; runtime insuficiente rechaza antes de lanzar; capacidad HPO y costes por backend están declarados.',
         'Recalcular DAG actual: el corte más reciente tiene 288 HPO sin clamp, frente a 252 de planes anteriores. Registrar 119941920 pasos como presupuesto del corte auditado, no compromiso ni ejecución. Medir pico de RAM/VRAM y rendimiento con microejecución autorizada; no asumir que 82 GiB requeridos caben en GPU de 80 GB. Separar reserva por tratamiento de disponibilidad instantánea; evitar que max de fase paralice injustificadamente todos los trabajos. Congelar buffers por etapa y registrar threads/fracción CUDA por ejecución.', 'L1 L2 L3', 'G2'),
    task('I06', 'Horizonte anual, inferencia congelada y KPI completos', 'I01 I03 I04',
         'uc3m/adapters/citylearn/policy_inference.py uc3m/adapters/citylearn/frozen_adapters.py uc3m/application/evaluation/frozen_evaluation.py uc3m/application/evaluation/kpi_contract.py',
         'tests/fresh_training/test_frozen_evaluation.py tests/fresh_training/test_frozen_evaluation_writer.py tests/fresh_training/test_kpi_physical_contract.py',
         '2023/2025 y 2024 bisiesto conservan intervalos/timestamps correctos, días completos, SOC/balances y pasos observados; recarga sin updates y test inaccesible antes de unlock válido.',
         'Definir filas/estados/acciones/energía terminal; corregir rows-1 sin inventar última hora ni eliminar días silenciosamente. Comparar políticas y baselines bajo iguales servicios EV/energía inicial/precios. Verificar contexto y hashes del unlock de test, protocolos congelados y manifiestos de evaluación. Separar contador observado de episodios*horizonte.', 'L1 L3 L5 L6', 'G2'),
    task('I07', 'Estadística y selección sin resultados ilustrativos promovidos', 'I01 I02',
         'uc3m/application/evaluation/fresh_analysis.py uc3m/application/evaluation/model_selection.py uc3m/application/evaluation/scientific_evaluation.py uc3m/domain/pareto.py uc3m/reward/hphi.py uc3m/application/thesis/evidence_registry.py uc3m/multicriteria/pipeline.py',
         'tests/fresh_training/test_statistical_input_gate.py tests/fresh_training/test_seed_statistics.py tests/fresh_training/test_evidence_promotion.py tests/uc3m/test_hphi.py tests/unit/application/test_model_selection.py',
         'NaN/Inf, réplicas duplicadas o cobertura incompleta rechazan; igualdad legítima no obliga ganador; IQM/hipervolumen únicos y leader descriptivo separado de ganador inferencial.',
         'Revalidar los avances P03/P08/P09 del Revisor A; no reimplementar lo ya correcto. Basar inferencia en semillas independientes y registrar familias de contrastes/IC. Prohibir accepted=True manual y aceptar solo evidencia existente con hash/contexto. Hacer relleno ilustrativo opt-in explícito y excluirlo del catálogo científico; conservar utilidad didáctica rotulada.', 'L1 L3 L6'),
    task('I08', 'Enlazar pipeline, análisis, catálogo y entrega', 'I01 I06 I07 I11',
         'uc3m/application/pipeline.py uc3m/application/training/fresh_acceptance.py uc3m/application/evaluation/results_catalog.py uc3m/presentation/training_panel.py tools/eval/report_fresh_campaign.py',
         'tests/fresh_training/test_pipeline.py tests/fresh_training/test_delivery_contract.py tests/fresh_training/test_fresh_results_catalog.py tests/integration/test_training_panel.py',
         'analyze→deliver consume gate_report y analysis_manifest explícitos; entrega válida acepta, informe ajeno/alterado rechaza y ausencia no produce paquete aceptado; panel de lectura refleja fase/seed/aceptación.',
         'Resolver análisis en analysis/<stage>_<split> frente a reports/scientific_report.json por referencia tipada única, no copiando un estado mínimo. Acordar esquema canónico con status/campaign_id y hashes frente a as_dict de FreshAnalysis. Propagar gate_report hasta verify_fresh_acceptance. Fijar contrato CLI explícito: resultados fallidos/rechazados de evaluate producen salida no cero y el cuaderno se detiene; incomplete se informa sin fingir hecho. Usar staging por identidad de análisis y publicación atómica; un .partial propio interrumpido debe poder diagnosticarse y recuperarse sin bloquear para siempre ni sobrescribir un resultado completo. Mantener status/freeze/evaluate/analyze/deliver sin segunda vía de entrenamiento y probar análisis válido→entrega, informe ajeno, fallos parciales y reintento.', 'L3', 'G2'),
    task('I09', 'Colab, Drive y recuperación de intentos', 'I01 I05 I08',
         'tools/colab/colab_session.py tools/colab/build_modular_colab_notebook.py uc3m/application/training/drive_sync.py examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb',
         'tests/ops/test_colab_session.py tests/ops/test_colab_notebook_cells.py tests/fresh_training/test_drive_sync.py',
         'Cuaderno regenerado reproduce C1–C11, propaga rechazos JSON, sincroniza intentos verificados y documenta pérdida potencial del intento activo; ensayo real Colab separado y trazable.',
         'Preservar CLI única y notebook como cliente. Verificar overlay por hash/checkout e identidad config/Drive. Publicar manifiesto atómico por cada intento copiado/verificado, no solo al final de toda la pasada. Simular corte tras copiar y antes del manifiesto: la siguiente ejecución debe verificar/adoptar o aislar explícitamente el residuo; no conflicto eterno. Conflictos/fallos salen no cero y detienen C4/C6. Aplicar contained_path a cada ruta del manifiesto, rechazando sub/../../outside.txt, rutas absolutas/drive y enlaces antes de escribir. Cambiar directory_digest a bloques preservando exactamente su resultado. Reutilizar solo intento completo estrictamente verificado; otro empieza en episodio 0. Registrar ensayo real de desconexión/restauración antes de cerrar P11; no basta una prueba local.', 'L3', 'G2'),
    task('I10', 'Privacidad, entradas remotas y riesgos aplicables', 'I00 I01',
         'uc3m/data/adapters/local_csv.py uc3m/data/adapters/remote_http.py tools/ops/audit_closed_services_and_secrets.py deploy/inference/app.py deploy/inference/model_loader.py deploy/docker-compose.yml',
         'tests/fresh_training/test_inference_demo_fence.py tests/uc3m/test_data_ingestion.py tests/uc3m/test_data_adapters_remote.py',
         'Estado de navegador excluido de cualquier paquete/imagen/copia de entrega; descargas contenidas y acotadas; avisos Bandit/OSV clasificados por API/exposición sin confundir pip check con seguridad.',
         'No abrir Login Data, state.json ni auth_info.json. Inventariar solo rutas/metadatos y probar exclusiones de Git, Docker y overlay. Diseñar ubicación externa configurable con migración recuperable: el traslado que pueda cerrar sesión requiere decisión explícita. Clasificar MD5 y cada torch.load/urlopen por confianza, timeout y cuotas; distinguir weights_only=False explícito del default variable con versión de torch y probar formatos reales de cada backend antes de cambiarlo. Corregir inferencia con test_action_clipping_is_request_local (last_clipped no compartido), test_missing_metadata_is_not_ready (ONNX sin metadatos→503) y test_internal_error_does_not_leak_details (500 sin texto interno; detalle solo en log local). Reconciliar si los avisos proceden de Ruff o Bandit y no afirmar ejecución sin log. Historial de secretos sigue sin acreditar; preparar análisis acotado sin mostrar valores. No ejecutar consultas externas/actualizaciones en esta entrega. Partir de addendum_auditoria_20261101/bandit.json (C69) y convertir la verificación del overlay sin rutas sensibles (C71) en prueba que regenera el zip y revisa el contexto Docker.', 'L3 L6'),
    task('I11', 'Gobernanza de dependencias, paquete y promesas de exportación', 'I00 I02',
         '.gitmodules pyproject.toml requirements.txt uv.lock governance/open_source_policy.yaml tools/colab/build_modular_colab_notebook.py tools/ops/audit_github_readiness.py .gitattributes',
         'tests/fresh_training/test_github_readiness.py tests/ops/test_open_source_dependency_audit.py',
         'off-policy tiene rol/procedencia/commit/licencia declarados; namespaces locales no se instalan como paquetes homónimos; wheel/checkout elegido funciona en instalación limpia; documentación LFS/ONNX veraz.',
         'Registrar external/off-policy como componente vendorizado o adoptar estrategia explícita sin modificarlo. Conciliar requirements/pyproject/uv.lock, local-dependencies y licencias/excepciones del overlay. Python 3.9 llegó a EOL el 2025-10-31 (PEP 596): documentar exposición/aislamiento y preparar matriz de migración a runtime soportado con cuatro backends, sin cambiar versión ni dependencias protegidas silenciosamente. Verificar si el producto soporta wheel autónomo o exige checkout; resolver import tools del pipeline. Cero archivos LFS no implica pérdida: contrastar reglas/punteros y STATUS. Para ONNX elegir D06: retirar promesa si fuera de alcance o implementar exportador con equivalencia numérica y contrato de cada backend; no exportar un ganador inexistente.', 'L3'),
    task('I12', 'Calidad, guardas, CI y documentación del flujo', 'I00 I01 I11',
         'scripts/verify_project_context.ps1 scripts/maintenance/consolidate_repository.ps1 .github/workflows/ci.yml tools/ops/verify_workflow_integrity.py docs/workflow_manifest.json tools/skills/registry.yaml pyrightconfig.json',
         'tests/fresh_training/test_duplicate_consolidation.py tests/fresh_training/test_github_readiness.py tests/contract/test_spec_kit_consistency.py tests/skills',
         'Cinco fallos generales tienen resolución específica; Ruff/skills/workflow/CI portable acreditan su ámbito; guarda más rápida conserva frontera, enlaces y rechazo de rutas ajenas.',
         'Diagnosticar PSModulePath/PowerShell lanzado desde Python antes de corregir Get-FileHash; no desactivar hash ni guarda. Medir repetidamente skills/perfil sin generalizar una muestra de 43 s; C74 sitúa 15 s en Select-String sobre el perfil de navegador: excluir solo directorios de datos no-skill, con test que siga rechazando una referencia global real. Mantener raíz/origin y defensa de junctions. Corregir Ruff, inventario historical_inventory y notebook desaparecido; habilitar tipos por alcance. Regenerar descubrimiento local y comprobar cliente. Verificar triggers CI en rama/PR de entrega, checks reales del mismo commit y protección aplicable; los 324/106 commits de divergencia y runs vacíos son datos reportados por el Revisor A, no actuales confirmados. Conciliar ramas es tarea de integración separada, sin merge/push automático. Incluir prueba de arquitectura y triage de dependencias en perfil portable; mantener SHA/permisos mínimos/no-skip ya adoptados. Revisar cumplimiento automático local con controles de solo lectura, nunca restaurar auto-stage. AGENTS prevalece sobre memorias contradictorias; actualizar documentación/traspaso sin editar memoria global.', 'L3'),
    task('I13', 'Cerrar revisión semántica por archivo y deuda de contratos', 'I00 I02',
         'uc3m/ports/simulator.py uc3m/algorithms/factory.py tools/thesis/generate_borrador_tesis_docx.py tools/thesis/validate_integral_word_50ep_4madrl.py tools/training/verify_training_optimization.py deploy/plant_adapter/modbus_adapter.py',
         'tests/contract/test_import_architecture.py tests/contract tests/unit tests/uc3m',
         'Cada archivo propio del alcance conciliado tiene revisión a EOF con hash, rol, consumidores, hallazgos y pruebas; registros pendientes siguen visibles. Código ajeno tiene frontera y revisión específica declaradas.',
         'Revisión compartida Revisor A/Revisor B según docs/audits/revision_semantica_20261102/README.md: build_lots.py genera ledger_revisor_a.csv (343 archivos/47966 líneas: L1, L3, L5 limpios y todo cambio en curso del Revisor B) y ledger_revisor_b.csv (333/82565: L2, L4 limpios y lo escrito por el Revisor A), un escritor por registro, con hallazgos R-<A|B>-NNN asignados a la tarea dueña del archivo; el revisor no corrige. Cierre: registros sin pendiente en corte estable y muestreo cruzado ≥10 % sin discrepancias sin explicar. Fronteras de la estimación previa: 773 entradas (722 sin docs/audits), L1 114/18022, L2 219/62182, L3 122/15186, L4 107/15561, L5 160/21883; L6 docs/audits y datos solo si se decide. Registrar por archivo hash, rol, consumidores, hallazgos, pruebas y revisor; el ejecutor no revisa su propio lote implementado. Incluir C72 (options sin usar en wrappers.reset) dentro de H11. Clasificar NotImplementedError/placeholder/TODO/pending_owner como abstracto válido, stub inelegible o deuda. Verificar SimulatorPort diferido y LearnerPort fuera de ruta canónica sin crear capa muerta. Reproducir ciclo fresh_analysis→multicriteria→results_catalog→fresh_analysis y eliminar dependencia inversa con contrato neutral; test_import_architecture debe cubrir imports relativos, puertos/tools y ambos órdenes de importación, además de entrar en CI. REGISTER_MAP vacío impide declarar operación. Clasificar cinco except silenciosos y fijar reporte de fallos. Dividir funciones 1096/445/195/149 líneas y stats_tests de 1916 solo con comportamiento fijado; longitud no demuestra cuello temporal.', 'L3'),
    task('I14', 'Paridad anterior, layout, obsoletos y conservación', 'I00 I11 I13 I15',
         'tools/ops/audit_repository_layout.py tools/ops/historical_inventory.py governance/repository_layout.yaml governance/naming.yaml data/audits/evaluation_tools_inventory.json README.md scripts/README.md tools/README.md Dockerfile',
         'tests/fresh_training/test_repository_layout.py tests/ops/test_repository_hygiene.py tests/unit/evaluation/test_tools_use_results_catalog.py tests/fresh_training/test_historical_retirement.py',
         'Mapa capacidad anterior→reemplazo→prueba o retiro razonado completo; enlaces activos válidos; PT en ubicación aprobada; ningún archivo único, dato/campaña, evidencia o dependencia eliminado por similitud.',
         'Reconciliar 209 rutas antiguas ausentes y 28 traslados exactos con capacidades y consumidores dinámicos. Clasificar 170 enlaces por activo/histórico/futuro antes de corregir los cuatro confirmados. Dar destino documentado a 27 herramientas obsoletas y 16 por decidir; comprobar herramientas manuales y dos scripts únicos. Revisar build/lib, inspection_cut, auditorías, nombres coincidentes y scripts fachada como roles distintos. Inventariar data/maintenance, cachés y temporales con referencias activas; para .git solo diagnóstico y mantenimiento Git autorizado, sin borrar objects ni reescribir historia. Actualizar Dockerfile que apunta a AWS retirado según producto adoptado.', 'L3'),
    task('I15', 'Pruebas independientes del scratch y cobertura real', 'I00 I01 I03 I04',
         'tests/fresh_training/conftest.py tests/fresh_training/test_real_learning.py tests/fresh_training/test_frozen_evaluation.py tests/fresh_training/test_frozen_evaluation_writer.py tests/fresh_training/test_three_level_game.py tests/uc3m/test_kpi_evaluator.py tests/uc3m/test_reward_axes.py pyproject.toml',
         'tests/fresh_training tests/ops/test_repository_hygiene.py deploy/inference/test_app.py tools/training/test_job_resume_state.py',
         'Clon/entorno limpio puede generar o recibir explícitamente checkpoints propios con identidad/hash; perfil estricto no omite ni xfail; pruebas fuera de tests tienen selección deliberada y aserciones de comportamiento.',
         'Eliminar dependencia implícita de tres rutas .superpowers mediante fixture nativa común o entrada de artefactos declarada, nunca checkpoints de campaña retirada. Mantener compilación de celdas como comprobación válida; añadir verificación observable a reset_pareto/set_baseline si hoy no verifica efecto. Clasificar cuatro tests exteriores por perfil y coste antes de moverlos/recogerlos. Desglosar duración de fixtures/guardas y simulación; optimizar sin omitir controles necesarios ni sustituir dependencias reales.', 'L3', 'G2'),
    task('I16', 'Aceptación nativa y campaña nueva autorizada', 'I01 I02 I03 I04 I05 I06 I07 I08 I09 I10 I11 I12 I13 I14 I15',
         'configs/experiments/iquitos.yaml scripts/quality/run_fresh_training_gates.ps1 uc3m/application/training/cli.py docs/architecture/runbook.md',
         'tests/fresh_training',
         'G2 con cuatro aprendices y perfil integral sin omisiones; G3/G4 solo con etapas autorizadas, HPO validación, confirmación multisemilla, sensibilidad, baselines y prueba final completos y verificados.',
         'Repetir primero microaprendizaje desde cero y evaluación congelada. Emitir presupuesto medido de tiempo/RAM/VRAM/costo y protocolo prerregistrado. Mantener authorized_stages vacío hasta decisión explícita; ejecutar en orden piloto→HPO→freeze→confirmación/sensibilidad→test. No elevar contratos ni microsmokes a resultados científicos; un resultado sin diferencias o sin ganador es válido. Cubrir escalabilidad/estrés del jurado según alcance factible registrado.', 'L1 L2 L3 L5 L6', 'G4'),
    task('I17', 'Tesis, bibliografía y observaciones J-01–J-17', 'I02 I06 I07 I08 I13 I14 I16',
         'data/audits/jury_observations_manifest.json uc3m/application/thesis/evidence_registry.py docs/chapters/ specs/STATUS.md docs/plans/traspaso_sesiones.md',
         'tests/contract/test_jury_observations.py tests/fresh_training/test_evidence_promotion.py',
         'Cada J-ID tiene evidencia específica y estado verificado; texto, tablas, anexos y Word reflejan el contrato y resultados reales, con preservación literal aprobada y revisión visual en copia nueva.',
         'Reparar rutas de 17 observaciones y separar historia de campaña nueva. Verificar correcciones bibliográficas del PT (autor/año/DOI) sin afirmar que se validaron los 50 antecedentes. Conservar síntesis por capítulo, costos/TRL/amenazas a validez y distinción liderazgo descriptivo/inferencia. La escritura del Word requiere encargo documental explícito; trabajar desde snapshot y nuevo nombre. No actualizar resultados antes de G4 ni cerrar jurado por una única suite.', 'L1 L2 L3 L4 L5 L6', 'G5'),
    task('I18', 'Frontera operacional y riesgos condicionados', 'I10 I16 I17',
         'deploy/inference/app.py deploy/inference/model_loader.py deploy/plant_adapter/modbus_adapter.py deploy/mosquitto.conf deploy/docker-compose.yml deploy/docker-compose.aws.yml deploy/aws/iac/variables.tf',
         'tests/fresh_training/test_inference_demo_fence.py deploy/inference/test_app.py',
         'Demo permanece inelegible para planta; cualquier aceptación operacional exige alcance y pruebas independientes de auth, límites, fallback, latencia, recuperación y escritura física autorizada.',
         'Reconciliar REGISTER_MAP, stub, readiness, permisos de escritura, exposición de Compose AWS y MQTT. Inventariar Terraform SSH/HTTP 0.0.0.0/0, auth de /act y /analytics, TLS/auth Mongo, securityContext/NetworkPolicy Kubernetes y usuario root en contenedores. Preparar configuraciones cerradas según alcance y prueba local, sin desplegar ni contratar. Preservar actions_for_plant y loopback ya correctos; una excepción de demo no habilita planta. Preparar protocolo de piloto/fallback RBC sin confundir convergencia con seguridad o TRL.', 'L2 L3', 'G6'),
]

# Atomic observations from both audit responses, JSONL lines 420 and 657.
# C IDs identify this integration, not identifiers invented by Revisor A.
C_ROWS = [
    ('C01', 'Cobertura semántica pendiente: unos 30 de 773 archivos / 140917 líneas', 'I00 I13', 'alcance declarado; no revisión integral'),
    ('C02', 'Estado autenticado de navegador dentro de tools/skills/notebooklm-mcp/data', 'I10 I12', 'metadatos; contenido sensible no abierto'),
    ('C03', '1088/1093 y cinco fallos, con cuatro microaprendizajes excluidos', 'I12 I14 I15', 'reutiliza el JUnit de nuestra auditoría; no segunda corrida'),
    ('C04', 'Tres incidencias Ruff en ámbito CI', 'I12', 'coincide con H16'),
    ('C05', 'Bandit: un aviso alto MD5 y seis medios torch.load/urlopen', 'I10', 'señales estáticas; severidad no implica explotación'),
    ('C06', 'reset_pareto y set_baseline sin aserción visible; compilación de celdas válida', 'I15', 'candidatos a revisión semántica'),
    ('C07', 'Puerta de aceptación, Drive y CI siguen pendientes según el Revisor A', 'I01 I09 I12', 'no sumar tres P0 nuevos sin reevaluar'),
    ('C08', '170 referencias rotas candidatas y cuatro activas confirmadas', 'I14', 'clasificar historia/rutas de ejecución/futuro'),
    ('C09', '11 planes con 519 tareas abiertas y specs con 34', 'I00 I12 I17', 'checkbox no acredita ausencia ni existencia de implementación'),
    ('C10', 'external/off-policy copiado sin registro gitmodules/local-dependencies', 'I11', '117 archivos y licencia según inventario; no editar dependencia'),
    ('C11', 'Promesa de export_winning_model_onnx.py sin herramienta', 'I11', 'decisión de alcance D06, sin ganador real'),
    ('C12', 'LFS anunciado con cero archivos LFS observados', 'I11 I14', 'reglas configuradas y uso efectivo son afirmaciones distintas'),
    ('C13', 'Rectificación: no se prueba ausencia de docs/failures; no hay notas versionadas', 'I00 I12', 'conservar rectificación; no repetir conclusión retirada'),
    ('C14', '51 carpetas vacías, principalmente scratch/perfil y cuatro caches CityLearn', 'I13 I14', 'vacío no implica defecto ni permiso de borrado'),
    ('C15', '53 NotImplementedError, 14 placeholder, 9 pending_owner y 2 TODO', 'I13', 'marcadores sin clasificar; pueden ser abstractos o terceros'),
    ('C16', 'SimulatorPort sin consumidores', 'I13 I04', 'contrastar ADR de integración diferida'),
    ('C17', 'REGISTER_MAP Modbus vacío', 'I13 I18', 'bloquea afirmar operación, no necesariamente entrenamiento offline'),
    ('C18', 'Guarda: 43 s; escaneo de perfil 15 s frente a casi cero sin él', 'I12', 'una medición, caché/confusores; requiere perfil repetido'),
    ('C19', 'Suite de 60 min; nombres/retiro histórico 1108 s, 31%', 'I12 I15', 'coste de fixtures/guardas, no perfil anual de GPU'),
    ('C20', 'directory_digest lee archivo entero; checkpoints 144–259 MiB', 'I09', 'cambiar a streaming preservando digest y contrato de Drive'),
    ('C21', '.git 5.6 GiB y blobs históricos retirados de 31 MiB', 'I14', 'no autoriza reescritura ni borrado de objetos'),
    ('C22', 'Memoria MASAC y reserva por fase', 'I05', 'ya H03/H04, no defecto independiente'),
    ('C23', '27 herramientas obsoletas presentes y 16 pendientes de decisión', 'I14', 'clasificación editorial no basta para eliminar'),
    ('C24', '48 scripts sin referencias, 21 de tesis; dos contienen material único', 'I13 I14', 'uso manual/dinámico; preservar archivos únicos'),
    ('C25', 'full_campaign, gates, workflow, tutorial v5 y Dockerfile AWS posiblemente antiguos', 'I12 I14', 'candidatos; Dockerfile requiere contrato actual de producto'),
    ('C26', '1090 grupos idénticos/2.3 GiB; 905 solo datos', 'I14', 'generaciones con procedencia diferente no deduplicables por hash'),
    ('C27', 'build/lib/uc3m idéntico a uc3m', 'I11 I14', 'derivado; verificar regeneración/consumidores antes de retirar'),
    ('C28', 'inspection_cut conserva 17 archivos versionados/copias de código', 'I14', 'evidencia de auditoría, no duplicado eliminable por defecto'),
    ('C29', 'Basenames repetidos de planes/documentos y test_model_selection', 'I14', 'rutas con roles distintos; mejorar índices antes de renombrar'),
    ('C30', 'Pares scripts/tools son fachadas válidas', 'I14', 'resultado negativo que debe preservarse'),
    ('C31', 'Cuatro tests fuera de tests no recogidos por defecto', 'I15', 'selección/perfil deliberado; revisar contrato pytest real'),
    ('C32', '15 archivos en raíz docs mezclan documentos/análisis/manifiestos', 'I14', 'organización candidata, no pérdida funcional'),
    ('C33', '10 scripts sueltos y solapamientos de función', 'I13 I14', 'clasificar launcher/fachada/herramienta antes de consolidar'),
    ('C34', 'Funciones build de 1096 líneas y run_checks de 445', 'I13', 'mantenibilidad; no prueba por sí sola cuello temporal'),
    ('C35', 'Auditorías ocupan 12 MiB con logs y copias de código', 'I14', 'política de custodia y paquete; no borrar evidencia'),
    ('C36', '.superpowers/sdd 2.9 GiB con tres tests dependientes', 'I15 I14', 'resolver consumidores antes de limpieza'),
    ('C37', 'data/maintenance 1.4 GiB ignorado y sin revisión de custodia', 'I14', 'inventariar referencias/valor probatorio; preservar'),
    ('C38', 'outputs/dataset_cache 360 MiB señalado como regenerable', 'I09 I14', 'verificar generador, identidad y uso activo'),
    ('C39', 'tmp_obj de Git 33 MiB', 'I14', 'solo diagnóstico Git; evitar eliminación de objetos manual'),
    ('C40', 'build, egg-info y ruff_cache derivados', 'I11 I14', 'comprobar proceso activo y reconstrucción'),
    ('C41', 'external/MAAC/.git_commit_msg.tmp ensucia dependencia', 'I14', 'dependencia protegida; no borrar como efecto lateral'),
    ('C42', 'pytest-cache-files y render_logs vacíos en CityLearn', 'I14', 'dependencia protegida; sin permiso de limpieza'),
    ('C43', 'Auditoría architecture_thesis de otra sesión sin confirmar', 'I00 I14', 'observación temporal de Git, no invalida evidencia ni autoriza stage'),
    ('C44', 'pip-audit no ejecutado; no aceptación de seguridad', 'I10 I11', 'OSV anterior es otro corte y no reemplaza triage actual'),
    ('C45', 'Inventario mecánico 14734 archivos/7.2 GiB, 20 enlaces sin seguir', 'I00 I13', 'ámbito más amplio que 4951 propios; no comparar como pérdidas'),
    ('C46', 'gate_report sin vínculo a commit/árbol/campaña ni SHA del JUnit', 'I01', 'lectura del Revisor A; reporte verde antiguo no acredita corte nuevo'),
    ('C47', 'Reporte legítimo carece status/campaign_id y ruta esperada por aceptación', 'I08 I01', 'amplía H21; validar esquema de FreshAnalysis.as_dict'),
    ('C48', 'Drive publica manifiesto al final; corte deja conflictos permanentes y salida 0', 'I09', 'reproducible con addendum_auditoria_20261101/reproductions.py caso P2 (d55c6c62)'),
    ('C49', 'pipeline evaluate termina con 0 ante tratamientos fallidos', 'I08', 'reproducible con reproductions.py caso P4; fijar contrato done/incomplete/rejected'),
    ('C50', '.partial interrumpido bloquea reintentos de analyze', 'I08', 'reproducible con reproductions.py caso P5; recuperación sin sobrescribir completos'),
    ('C51', 'restore Drive permite sub/../../outside.txt fuera de artifacts', 'I09 I10', 'reproducible con reproductions.py caso P3; contención antes de escribir'),
    ('C52', 'AWS/Terraform abiertos, endpoints sin auth, controles K8s ausentes y root', 'I10 I18', 'riesgo condicionado al despliegue; loopback local se preserva'),
    ('C53', 'Tres contratos de dependencias y runtime Python 3.9 fuera de soporte', 'I11 I12', 'EOL corroborado en PEP 596; migración sujeta a compatibilidad'),
    ('C54', 'CI solo master, sin runs en rama; divergencia 324/106 y sin protección', 'I12 I00', 'snapshot remoto reportado; revalidar sin merge/push automático'),
    ('C55', 'LearnerPort solo runner, fuera de la ruta canónica', 'I13 I04', 'contrastar ADR y necesidad, no añadir puertos cosméticos'),
    ('C56', 'Ciclo lazy fresh_analysis→multicriteria→results_catalog→fresh_analysis', 'I13', 'comprobar ambos órdenes de importación y dependencia inversa'),
    ('C57', 'test_import_architecture no cubre relativos/puertos/tools ni está en CI', 'I13 I12', 'ampliar cobertura semántica, no solo contar seis tests verdes'),
    ('C58', 'torch.load weights_only=False y default distinto según versión admitida', 'I10 I11', 'probar formatos nativos, especialmente MAAC, antes de cambiar carga'),
    ('C59', 'last_clipped compartido entre hilos de inferencia', 'I10', 'respuesta debe reflejar recorte de su propia petición'),
    ('C60', 'ONNX sin metadatos da ready 200 con dimensiones por defecto', 'I10 I11', 'metadatos/forma/contrato obligatorios antes de readiness'),
    ('C61', 'HTTP 500 expone texto interno de excepción', 'I10', 'respuesta saneada y detalle solo en registro local'),
    ('C62', 'stats_tests 1916 líneas, funciones 195/149 y cinco except silenciosos', 'I13', 'mantenibilidad y observabilidad; no perfil de rendimiento'),
    ('C63', 'Guarda obligatoria sin enforcement local automático/pre-commit', 'I12', 'controles de lectura; no restaurar hook auto-publicador'),
    ('C64', 'Sesiones escriben/prueban concurrentemente sin corte estable', 'I00 I12', 'no usar un resultado mezclado como aceptación integral'),
    ('C65', 'Memorias contradicen protección de CityLearn y estado del Stop hook', 'I00 I12 I17', 'AGENTS vigente prevalece; no editar memoria global sin encargo'),
    ('C66', 'Controles correctos: descarga, planta, CI, dominio, loopback y no shell=True', 'I10 I12 I13 I18', 'preservar regresiones; búsqueda limitada sin secretos no acredita historial limpio'),
    ('C67', 'Sin auditoría profunda de dependencias, datos ni historial de secretos', 'I00 I10 I13', 'fronteras de cobertura; no declarar esas áreas aceptadas'),
    ('C68', 'Revisor A reporta CI 36/36, arquitectura 6/6 y readiness 7/8', 'I00 I12', 'resultados de su corte; no sumarlos a nuestra suite ni repetir como actuales'),
    ('C69', 'Contradicción: dictamen dice Bandit no ejecutado; resumen rotula avisos Bandit', 'I00 I10', 'resuelta: no instalado en el venv, ejecutado vía uvx bandit 1.9.4; log en addendum_auditoria_20261101/bandit.json (1 alto, 7 medios)'),
    # Addendum of the Revisor A session (docs/audits/addendum_auditoria_20261101/README.md).
    ('C70', 'gate_report.py:39 nuevo de I01 parsea el JUnit con xml.etree (Bandit B314)', 'I01 I10', 'verificar hash del JUnit antes de parsear o parser endurecido; XML con expansión de entidades rechazado'),
    ('C71', 'overlay Colab 2683 entradas sin rutas de navegador/credenciales; Dockerfile raíz copia solo CityLearn, uc3m y tests', 'I10', 'evidencia positiva de un snapshot; convertir en prueba de regresión regenerando zip e imagen'),
    ('C72', 'vulture: uc3m/env/wrappers.py:106 options sin usar en reset', 'I13 I04', 'resolver dentro del contrato H11, no como limpieza aislada'),
    ('C73', 'Fixture _campaign de test_security_and_acceptance codificaba evidencia débil', 'I01', 'fixture base pasa attempt_evidence_reasons estricto; cuatro variantes de P1 como casos negativos'),
    ('C74', 'Guarda: Select-String sobre tools/skills 15 s con perfil de navegador y ~0 s sin él; git 124 ms', 'I12', 'una medición; repetir y excluir directorios de datos no-skill sin dejar de rechazar referencias reales'),
]
ADDENDUM = 'docs/audits/addendum_auditoria_20261101'
COORD_SKILLS = ['tools/skills/madrl-agent-coordination/SKILL.md',
                'tools/skills/task-coordination-strategies/SKILL.md',
                'tools/skills/task-coordination-strategies/references/task-decomposition.md',
                'tools/skills/task-coordination-strategies/references/dependency-graphs.md']
OUT_OF_SCOPE = ['archivos de otras tareas no cedidos en el traspaso', 'CityLearn/ y external/',
                'commits, push o stage global', 'entrenamiento, Colab o infraestructura de pago',
                'cambiar dependencias o el stack']


def coordination(tasks):
    """Waves, ancestors and shared files of the DAG, as task-coordination-strategies prescribes."""
    by_id = {t['id']: t for t in tasks}
    level, anc = {}, {}
    def walk(id_):
        if id_ not in level:
            deps = by_id[id_]['depends_on']
            anc[id_] = set(deps).union(*(walk(d) for d in deps))
            level[id_] = 1 + max((level[d] for d in deps), default=-1)
        return anc[id_]
    for id_ in by_id:
        walk(id_)
    owners = {}
    for t in tasks:
        for f in t['files']:
            owners.setdefault(f, []).append(t['id'])
    shared = {}
    for f, ids in sorted(owners.items()):
        if len(ids) < 2:
            continue
        unordered = [[a, b] for i, a in enumerate(ids) for b in ids[i+1:] if a not in anc[b] and b not in anc[a]]
        shared[f] = dict(tasks=ids, order=sorted(ids, key=lambda x: (level[x], x)), unordered_pairs=unordered)
    waves = [sorted(i for i in by_id if level[i] == n) for n in range(max(level.values()) + 1)]
    briefs = {t['id']: dict(objective=t['title'], wave=level[t['id']], owned_files=t['files'],
                            contract_inputs=t['depends_on'], acceptance=t['acceptance'], tests=t['tests'],
                            shared_with={f: [x for x in shared[f]['tasks'] if x != t['id']] for f in t['files'] if f in shared},
                            out_of_scope=OUT_OF_SCOPE, reviewer='el otro agente (auditoría cruzada)')
              for t in tasks}
    return dict(skills=COORD_SKILLS, waves=waves, shared_files=shared, briefs=briefs)


def coordination_section(coord):
    by_wave = {i: n for n, wave in enumerate(coord['waves']) for i in wave}
    lines = ['## Coordinación de agentes y descomposición', '',
             'Este apartado aplica dos skills locales registrados: `madrl-agent-coordination`, con las reglas y roles del proyecto (`.claude/agents/`), y `task-coordination-strategies` (wshobson/agents@7e2fb559, MIT), para descomponer por archivos, fijar contratos y ordenar el DAG. La ejecución en línea sigue `superpowers:executing-plans`. Las tablas siguientes se calculan desde `TASKS` en el generador. No autorizan subagentes: lanzar agentes sigue requiriendo la petición explícita del usuario.', '',
             '### Plantilla de encargo', '',
             'Cada tarea se entrega a un agente, o la asume uno, con estos cinco campos. Todos salen del propio plan, así que el encargo no inventa alcance:', '',
             '| Campo | Fuente en este plan |', '|---|---|',
             '| Objetivo | Título e «Implementación» de la tarea |',
             '| Archivos propios | «Archivos propios previstos», reservados en el traspaso; los compartidos se ceden por turnos |',
             '| Contrato de entrada | Actas hash-verificadas de las tareas de «Dependencias»; las firmas que otra tarea consume se publican antes de cambiarlas |',
             '| Criterio de aceptación | Comando pytest de la tarea más el criterio de cierre en negrita |',
             '| Fuera de alcance | '+'; '.join(OUT_OF_SCOPE)+' |', '',
             'El JSON guarda este encargo, ya relleno, en `coordination.briefs.<tarea>`.', '',
             '### Olas del DAG', '',
             'Una ola reúne las tareas cuyas dependencias están todas en olas anteriores. Es el inicio más temprano posible, no un calendario. Dentro de una ola solo se trabaja en paralelo si las tareas no comparten archivos, si sus decisiones D01–D06 están resueltas y si el usuario autorizó varios agentes.', '',
             '| Ola | Tareas | Archivos compartidos dentro de la ola |', '|---|---|---|']
    for n, wave in enumerate(coord['waves']):
        clash = sorted({f for f, v in coord['shared_files'].items() if len([t for t in v['tasks'] if t in wave]) > 1})
        lines.append(f'| {n} | {", ".join(wave)} | ' + (', '.join('`'+f+'`' for f in clash) or 'ninguno: paralelizable si no hay otro bloqueo') + ' |')
    lines += ['', '### Archivos con más de un escritor previsto', '',
              'Regla: escribe primero la tarea más temprana en el DAG y la siguiente parte de su acta cerrada. Cuando dos tareas no tienen orden en el DAG, el archivo se reserva por turnos en el traspaso y esas tareas no se ejecutan en paralelo.', '',
              '| Archivo | Orden de escritura | Pares sin orden en el DAG |', '|---|---|---|']
    for f, v in coord['shared_files'].items():
        pairs = ', '.join(a+'–'+b for a, b in v['unordered_pairs']) or 'ninguno'
        lines.append('| `'+f+'` | '+' → '.join(f'{t} (ola {by_wave[t]})' for t in v['order'])+' | '+pairs+' |')
    lines += ['', '### I13 por lotes: reparto y consolidación', '',
              '1. Dos revisores principales: Revisor A y Revisor B. Cada uno es dueño de un único registro (`ledger_revisor_a.csv`, `ledger_revisor_b.csv`) y de su archivo de hallazgos. Si el usuario autoriza subagentes, cada revisor puede repartir su parte entre auditores de solo lectura (perfil `madrl-auditor`, como máximo cuatro a la vez), pero sigue siendo el único que escribe su registro.',
              '2. `build_lots.py` regenera los registros por hash. Una revisión solo cuenta para el SHA-256 exacto que se revisó.',
              '3. Nadie revisa código que haya implementado en I00–I18. Si un hallazgo cae en un archivo reservado por otra tarea, se entrega a esa tarea y no se corrige dentro de I13.',
              '4. Los hallazgos contradictorios entre lotes los reconcilia el coordinador con evidencia, sin votación.', '',
              '### Medición de la mejora', '',
              'Para comprobar si la coordinación mejora el trabajo, y no suponerlo, cada acta añade a los campos comunes: `wave`, `files_reserved`, `shared_files_handoff`, `review_findings` (hallazgos del auditor cruzado después de que el ejecutor declarase la tarea lista), `rework_rounds` y `conflicts` (escrituras concurrentes o reservas violadas). Al cerrar cada puerta se comparan con las tareas ya cerradas sin esta plantilla. Esa es la línea base que `AGENT_HARNESS.md` deja pendiente.', '']
    return lines

H_MAP = {'H01':'I02 I04 I17','H02':'I03','H03':'I05','H04':'I05','H05':'I02 I03',
         'H06':'I02 I03','H07':'I03 I06','H08':'I02','H09':'I12 I14 I17',
         'H10':'I00 I12 I14 I17','H11':'I04','H12':'I16','H13':'I03',
         'H14':'I09','H15':'I14','H16':'I12','H17':'I17','H18':'I07',
         'H19':'I15','H20':'I01','H21':'I08','H22':'I06','H23':'I11'}
P_MAP = {'P00':['I00'], 'P01':['I01','I10'], 'P02':['I01','I04'],
         'P03':['I07'], 'P04':['I02','I05'], 'P05':['I04','I06'],
         'P06':['I06'], 'P07':['I03'], 'P08':['I07'], 'P09':['I07'],
         'P10':['I08'], 'P11':['I09'], 'P12':['I10','I18'],
         'P13':['I10','I11'], 'P14':['I12'], 'P15':['I13','I14'],
         'P16':['I16'], 'P17':['I17'], 'P18':['I18']}


def translated(row):
    return sorted({new for old in row['tasks'] for new in P_MAP[old]})


def review_findings(task_ids):
    """Per-task index of the I13 findings tables; the findings files stay the source."""
    out = {t: [] for t in task_ids}
    for path in sorted((ROOT/'docs/audits/revision_semantica_20261102').glob('hallazgos_revisor_*.md')):
        for line in path.read_text(encoding='utf-8').splitlines():
            cells = [c.strip() for c in line.split(' | ')]
            if not re.match(r'^\| R-[AB]-\d{3}$', cells[0]) or len(cells) < 6:
                continue
            for task in sorted(set(re.findall(r'I\d\d', cells[2]))):
                assert task in out, (cells[0], task)
                out[task].append(dict(id=cells[0][2:], severity=cells[1]))
    return out


def main():
    # Exact project session only; no broad session scan and no credential reads.
    source_lines = {}
    for number, line in enumerate(AUDIT_LOG.open(encoding='utf-8'), 1):
        if number in (420, 657):
            record = json.loads(line)
            parts = record['message']['content']
            source_lines[number] = '\n'.join(x.get('text', '') for x in parts if x.get('type') == 'text')
    if set(source_lines) != {420, 657} or not source_lines[657].startswith('# Inventario exhaustivo'):
        raise RuntimeError('Revisor A source changed: locate the explicit audit response again')
    if not source_lines[420].startswith('# Dictamen de auditoría'):
        raise RuntimeError('Revisor A initial audit changed')
    (OUT/'revision_final_auditoria.md').write_text(source_lines[657]+'\n', encoding='utf-8')
    (OUT/'dictamen_inicial_auditoria.md').write_text(source_lines[420]+'\n', encoding='utf-8')
    for original, target in [('inventory.json','inventario_auditoria.json'),('ledger.csv','ledger_auditoria.csv')]:
        shutil.copyfile(SCRATCH/original, OUT/target)
    old = json.loads((ROOT/'docs/plans/remediacion_cobertura.json').read_text(encoding='utf-8'))
    a_findings = json.loads((ROOT/'docs/audits/deep_20261101/findings.json').read_text(encoding='utf-8'))
    h_findings = list(csv.DictReader((ROOT/'docs/audits/architecture_thesis_20261101/findings.csv').open(encoding='utf-8-sig')))
    coverage = {
        'architecture_H': {r['id']:dict(tasks=H_MAP[r['id']].split(), severity=r['severity_type'],
                                      evidence=r['evidence_impact'], acceptance=r['acceptance'], status='requires_stable_cut_revalidation') for r in h_findings},
        'deep_A': {r['id']:dict(tasks=translated(old['coverage']['findings'][r['id']]), title=r['title'],
                              acceptance=r['acceptance'], status='historical_finding_revalidate_preserving_fixes') for r in a_findings},
        'auditoria_C': {id_:dict(title=title, tasks=tasks.split(), limitation=scope,
                             source_lines=([] if int(id_[1:])>=70 else [420,657] if id_=='C69' else ([420] if int(id_[1:])>=46 else [657])),
                             source_file=(ADDENDUM+'/README.md' if int(id_[1:])>=70 or id_ in ('C48','C49','C50','C51','C69') else None),
                             status='reported_by_audit_revalidate') for id_,title,tasks,scope in C_ROWS},
        'requirements_FR': {key:dict(tasks=translated(row), acceptance=row['acceptance']) for key,row in old['coverage']['requirements'].items()},
        'jury_J': {key:dict(tasks=translated(row), acceptance=row.get('acceptance',row.get('evidence',''))) for key,row in old['coverage']['jury'].items()},
        'legacy_tasks_P': {key:dict(tasks=value) for key,value in P_MAP.items()},
    }
    sources = [
        ROOT/'docs/audits/architecture_thesis_20261101/informe.md',
        ROOT/'docs/audits/architecture_thesis_20261101/findings.csv',
        ROOT/'docs/audits/architecture_thesis_20261101/validation.json',
        ROOT/'docs/audits/deep_20261101/findings.json',
        ROOT/'docs/plans/remediacion_auditoria.md',
        ROOT/'docs/plans/remediacion_cobertura.json',
        ROOT/'docs/plans/cuaderno_colab.md', ROOT/'docs/plans/traspaso_sesiones.md',
        OUT/'revision_final_auditoria.md', OUT/'dictamen_inicial_auditoria.md', OUT/'inventario_auditoria.json', OUT/'ledger_auditoria.csv',
        ROOT/ADDENDUM/'README.md', ROOT/ADDENDUM/'bandit.json', ROOT/ADDENDUM/'reproductions.py',
        *(ROOT/p for p in COORD_SKILLS),
        ROOT/'docs/audits/revision_semantica_20261102/README.md',
        ROOT/'docs/audits/revision_semantica_20261102/build_lots.py',
        ROOT/'docs/audits/revision_semantica_20261102/hallazgos_revisor_a.md',
    ]
    coord = coordination(TASKS)
    findings = review_findings([t['id'] for t in TASKS])
    source_rows = [dict(path=p.relative_to(ROOT).as_posix(), sha256=sha(p)) for p in sources]
    head = subprocess.run(['git','rev-parse','HEAD'],cwd=ROOT,capture_output=True,text=True,check=True).stdout.strip()
    matrix = dict(schema_version=1, created_at_utc=datetime.now(timezone.utc).isoformat(),
                  plan=PLAN.relative_to(ROOT).as_posix(), implementation_executed=False,
                  implementation_ready_for_training=False, scientific_acceptance=False,
                  operational_acceptance=False, head_observed=head,
                  audit_source=dict(session_id=SESSION, lines=[420,657], source_kind='assistant audit responses; not new user authority'),
                  tasks=TASKS, coverage=coverage, coordination=coord, review_findings=findings, source_hashes=source_rows)
    write_json(MATRIX, matrix)
    lines = HEADER.splitlines()
    cut = lines.index('## Tareas integradas')
    lines[cut:cut] = coordination_section(coord)
    for item in TASKS:
        refs = [key for group in list(coverage.values())[:3] for key,row in group.items() if item['id'] in row['tasks']]
        brief = coord['briefs'][item['id']]
        shared = '; '.join('`'+f+'` con '+', '.join(o) for f,o in brief['shared_with'].items())
        shared = shared+'. Escribe primero la tarea anterior en el DAG; sin orden, se reserva por turnos' if shared else 'ninguno'
        lines += ['', f'### {item["id"]}. {item["title"]}', '',
                  f'**Dependencias:** {", ".join(item["depends_on"]) or "ninguna"}. **Puerta:** {item["gate"]}. **Estado:** planned. **Fuentes:** {", ".join(item["scientific_basis"])}.', '',
                  f'**Encargo de coordinación:** ola {brief["wave"]}. Archivos compartidos: {shared}. Fuera de alcance: {"; ".join(OUT_OF_SCOPE)}.', '',
                  '**Observaciones:** '+', '.join(refs)+'.', '',
                  *(['**Hallazgos de la revisión I13 ([detalle](../audits/revision_semantica_20261102/hallazgos_revisor_a.md)):** '+', '.join(f['id'] for f in findings[item['id']])+'.', ''] if findings[item['id']] else []),
                  '**Archivos propios previstos:** '+', '.join('`'+f+'`' for f in item['files'])+'. Los que no existan deben registrarse como propuesta antes de crearse.', '',
                  '**Entradas:** contrato y evidencia hash-verificada de las tareas predecesoras; las fuentes específicas están en la matriz JSON. **Salida:** acta de tarea `data/maintenance/integracion/<cut_id>/'+item['id']+'/acceptance.json` con los campos comunes definidos abajo.', '',
                  '- [ ] Reproducir el hallazgo en el corte estable y fijar el comportamiento esperado; si ya está corregido, registrar la prueba actual sin inventar RED.',
                  '- [ ] '+item['implementation'],
                  '- [ ] Ejecutar la selección pertinente: `PY -B -X utf8 -m pytest '+ ' '.join(item['tests'])+' -q -p no:cacheprovider`. Verificar antes las rutas existentes y clasificar las propuestas; no sustituir una prueba ausente por éxito. Para pasos documentales revisar trazabilidad/diff; no añadir tests que solo repitan texto.',
                  '- [ ] Revisar diff y evidencia; cerrar exclusivamente si se cumple: **'+item['acceptance']+'**', '',
                  '**Continuidad del plan previo:** '+', '.join(k for k,v in P_MAP.items() if item['id'] in v)+'.' if any(item['id'] in v for v in P_MAP.values()) else '**Continuidad:** tarea nueva de integración.']
    lines += ['','## Matrices completas de cobertura','','Cada ID conserva su origen. **No son 123 defectos independientes:** varias observaciones coinciden y otras describen un alcance o un resultado negativo. Las tablas asignan trabajo; no certifican vigencia ni cierre. El JSON conserva evidencia/criterios del diagnóstico y hashes de las fuentes.','']
    for name,title in [('architecture_H','Auditoría arquitectura/PT: H01–H23'),('deep_A','Auditoría previa: A01–A31'),('auditoria_C','Auditoría independiente (Revisor A): C01–C74'),('requirements_FR','Requisitos FR-N01–N20'),('jury_J','Jurado J-01–J-17'),('legacy_tasks_P','Continuidad P00–P18')]:
        lines += ['### '+title,'','| Origen | Trabajo integrado | Evidencia, observación o límite |','|---|---|---|']
        for key,row in coverage[name].items():
            text = row.get('title',row.get('acceptance',row.get('severity','')))
            if row.get('limitation'):
                text += ' — '+row['limitation']
            lines.append('| '+key+' | '+', '.join(row['tasks'])+' | '+str(text).replace('|','/').replace('\n',' ')+' |')
        lines += ['']
    lines += FOOTER.splitlines()
    PLAN.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    matrix['plan_sha256'] = sha(PLAN)
    write_json(MATRIX,matrix)
    ids={t['id'] for t in TASKS}
    assert len(ids)==19
    assert {r['id'] for r in h_findings}==set(H_MAP)
    assert len(coverage['deep_A'])==31 and len(coverage['auditoria_C'])==74
    assert len(coverage['requirements_FR'])==20 and len(coverage['jury_J'])==17
    for group in coverage.values():
        for row in group.values():
            assert row['tasks'] and set(row['tasks'])<=ids
    by_id={t['id']:t for t in TASKS}
    completed=set()
    active=set()
    def visit(id_):
        assert id_ not in active,(id_,'dependency cycle')
        if id_ in completed:
            return
        active.add(id_)
        for dep in by_id[id_]['depends_on']:
            assert dep in ids,(id_,dep,'unknown dependency')
            visit(dep)
        active.remove(id_)
        completed.add(id_)
    for id_ in ids:
        visit(id_)
    seen = set()
    for wave in coord['waves']:
        for id_ in wave:
            assert set(by_id[id_]['depends_on']) <= seen, (id_, 'dependency in same or later wave')
        seen |= set(wave)
    assert seen == ids and set(coord['briefs']) == ids
    write_json(OUT/'coverage_validation.json',dict(plan_sha256=sha(PLAN),
        counts={key:len(value) for key,value in coverage.items()}, tasks=19,
        coordination=dict(waves=len(coord['waves']), shared_files=len(coord['shared_files']),
                          unordered_shared_files=sorted(f for f,v in coord['shared_files'].items() if v['unordered_pairs'])),
        missing_source_ids=[], unknown_task_ids=[], dependency_cycles=[],
        implementation_executed=False, scientific_acceptance=False))
    print(json.dumps({'plan':str(PLAN),'tasks':19,'coverage':{k:len(v) for k,v in coverage.items()}},ensure_ascii=True))


HEADER = r'''# Plan integrado de remediación y revisión MADRL–CityLearn — Implementation Plan

> Para ejecución futura: seguir `superpowers:executing-plans` tarea por tarea, con un escritor por archivo. Este documento no solicita ni autoriza subagentes, entrenamiento, cambios de dependencias, publicación o edición del Word.

**Goal:** Integrar todos los hallazgos documentados de la auditoría independiente (Revisor A), la auditoría arquitectura/PT y la remediación previa en una sola secuencia trazable, conservando avances reales y cerrando cada vacío mediante evidencia.

**Architecture:** Mantener el monolito modular, sus puertos/adaptadores y la CLI nativa única; Colab actúa como cliente. Reutilizar contratos de campaña, aceptación y catálogo existentes. La reorganización se decide por capacidad, consumidores y reproducibilidad; no se impone una nueva jerarquía ni se eliminan archivos por nombre/tamaño/hash.

**Tech Stack:** Python 3.9 del entorno `.venv39-citylearn-v3`, pytest, PyTorch y backends locales ya adoptados. Ninguna actualización de stack se deriva de escribir este plan.

**Spec:** [Estado de SPEC-000–012](../../specs/STATUS.md), [diseño de entrenamiento](../design/entrenamiento.md), [remediación P00–P18](remediacion_auditoria.md), [cuaderno Colab](cuaderno_colab.md), [traspaso](traspaso_sesiones.md), [informe arquitectura/PT](../audits/architecture_thesis_20261101/informe.md), [respuesta íntegra del Revisor A preservada](../audits/integracion_auditorias_20261101/revision_final_auditoria.md).

**Estado de esta entrega:** plan integrado único para Revisor A y Revisor B; la implementación avanza por tareas y su estado real está en las actas, no en las casillas. Fecha de integración: 2026-11-01, America/Lima. Los estados experimentales permanecen falsos. El HEAD observado y hashes exactos están en [la matriz](remediacion_integrada.json).

## Fuentes y reconciliación

1. H01–H23: auditoría actual arquitectura/PT, con simulador real acotado, pruebas adversariales y suite general 1088 aprobadas/5 fallidas/0 omitidas; cuatro microaprendizajes explícitamente excluidos. No fue aceptación fresh integral.
2. Auditoría independiente (Revisor A) `865ad199-53fa-4aa9-acc3-c3dfb37f0edd`, dictamen inicial en línea JSONL 420 y respuesta final en línea 657. Se preservan ambos textos, inventario y ledger, sin copiar historial general de chats, credenciales, modelos ni navegador. C01–C69 son identificadores creados aquí para desglosar las observaciones de ambas respuestas, incluidas rectificaciones, controles correctos y límites de cobertura. C70–C74 y la evidencia de C48–C51 y C69 proceden del [addendum del Revisor A](../audits/addendum_auditoria_20261101/README.md) (log Bandit, reproducciones en temporales y lotes de revisión), integrado aquí a petición del usuario para mantener un único plan.
3. A01–A31 y P00–P18: antecedentes de auditoría profunda y plan previo. Varios defectos ya tuvieron correcciones y tests focales en otras sesiones: revalidar y conservar, no reabrir por una frase histórica.
4. FR-N01–N20 y J-01–J-17: cobertura importada del plan previo con traducción explícita a tareas I00–I18. La cobertura de un ID no equivale a su implementación ni a la corrección semántica del requisito: I00 lo contrasta con SPEC/jurado original.

Las cifras 14734 archivos/7.2 GiB del Revisor A y 4951 archivos propios de nuestra auditoría usan fronteras diferentes. No se suman ni demuestran archivos perdidos. La lectura mecánica completa del Revisor A y sus unos 30 archivos revisados no acreditan revisión semántica de las 773 entradas. Las cinco pruebas fallidas citadas por el Revisor A proceden de nuestro mismo JUnit, no de una segunda ejecución independiente.

El informe del Revisor A deja consolidación «sin diagnosticar»; la auditoría actual aporta reproducción de `Get-FileHash` ausente al lanzar PowerShell desde Python. «Imports sin dependencia» se precisa en H23: mezcla namespaces locales, opcionales y distribuciones; no instalar paquetes homónimos. `historical_inventory.py` contiene una guarda de retiro, no necesariamente un consumidor de resultados antiguos. LFS configurado con cero punteros puede ser coherente: verificar la afirmación concreta. Los 170 enlaces y 48 scripts sin referencias siguen siendo candidatos, frente a cuatro enlaces activos confirmados y dos scripts de contenido único que se preservan.

El dictamen inicial añade defectos de restauración Drive (corte/manifiesto, contención y código de salida), vínculo del reporte de puerta al corte, estados de pipeline/.partial, ciclo de imports, CI remoto y controles de inferencia/despliegue. Se integran en C46–C68; C48–C51 ya cuentan con `reproductions.py` del addendum para repetirlas en cualquier corte. Su afirmación de ausencia de docs/failures queda sustituida por la rectificación C13. La contradicción de Bandit (C69) queda resuelta: no estaba instalado en el entorno canónico y se ejecutó aislado con `uvx bandit 1.9.4`; el log es `bandit.json` del addendum.

## Restricciones globales

- Única raíz `D:/MADRLCitytleranflexresdr`; origin `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`. Rige [AGENTS.md](../../AGENTS.md). No acceder ni mezclar otro proyecto excluido.
- Antes de cada lote de ediciones u operación Git ejecutar `powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1`; fallo detiene el trabajo. Su optimización no elimina esa obligación.
- `CityLearn/` y `external/` solo lectura. Si una corrección exige escribir ahí, entregar diagnóstico, propuesta de parche y test como `blocked_dependency_interface`; esperar instrucción explícita en ese turno. Registrar off-policy no autoriza editar su código ni convertirlo automáticamente en submódulo.
- Conservar datos originales, generaciones de dataset, resultados, Word, modelos, historial, parches y evidencia. Única excepción: `iquitos_v1` e `iquitos_v2`, según la puerta de sustitución D01. Ninguna tabla de candidatos autoriza borrado, `git clean`, eliminación de objetos Git, stage global o publicación.
- No tratar instrucciones o autorizaciones citadas en una sesión anterior del Revisor A como autorización vigente de ejecución. Este encargo es elaborar e integrar un plan.
- No leer el contenido de archivos de autenticación del navegador. Un traslado que invalide sesión se prepara de forma recuperable y requiere decisión explícita.
- Una sola fuente de entrenamiento: CLI nueva; cuaderno generado, nunca editado a mano. Intentos nuevos desde episodio 0; no reanudar ni sumar intentos parciales. Continuidad de optimizador/RNG/replay de un perfil legado se revisa solo si se mantiene como producto distinto.
- `authorized_stages` no se habilita por este plan. No iniciar campañas, sesiones Colab, GPU remota, servicios públicos ni infraestructura de pago. Cambios de protocolo/datos crean identidad nueva y requieren registro metodológico.
- Skills del proyecto locales en `tools/skills/`; no copiar ni usar duplicados globales. No alterar hooks, permisos o políticas para superar una prueba.
- `implemented`, `verified_contract`, `verified_native`, `pending_experiment`, `blocked`, `scientific_acceptance` y `operational_acceptance` son estados diferentes.

## Ejecución por Revisor A o Revisor B

Este es el único plan vigente para ambos agentes. Cualquiera de los dos puede implementar cualquier tarea I00–I18 siguiendo estas reglas; el otro actúa como auditor independiente de esa tarea.

1. **Reservar antes de editar.** El ejecutor registra la tarea, su agente/sesión y los archivos que va a escribir en `docs/plans/traspaso_sesiones.md` (o lo pide a la sesión dueña de ese archivo) y abre el acta `data/maintenance/integracion/<cut_id>/<tarea>/`. Una tarea con acta modificada en las últimas 24 h se considera en curso por su ejecutor.
2. **Un escritor por archivo.** Si un archivo previsto pertenece a otra sesión según el traspaso, pedirlo por mensaje antes de tocarlo; no editar en paralelo. Dependencias protegidas siguen bajo `blocked_dependency_interface`.
3. **Cierre con auditoría cruzada.** La tarea solo pasa a cerrada cuando el otro agente revisa el diff de forma adversarial, repite las pruebas y casos de `reproductions.py` aplicables, y su revisión queda enlazada en el campo `reviewer` del acta. Pruebas verdes del propio ejecutor no bastan.
4. **Este documento se regenera, no se edita a mano.** Cambios de tareas u observaciones van en `docs/audits/integracion_auditorias_20261101/integrar_plan.py`, que reescribe este Markdown, el JSON y `coverage_validation.json` con sus hashes. Avisar al otro agente tras regenerar.
5. **Sin commits ni push** salvo autorización explícita del usuario en esa sesión, y nunca stage global.

Situación al regenerar (2026-11-02, 06:30 America/Lima), según las evidencias en `data/maintenance/integracion/c20261101i01/`:

| Tareas | Ejecutor | Estado |
|---|---|---|
| I00, I01, I06, I07, I08, I09, I10, I11, I12, I15 | Revisor B | En curso: hay JUnit y JSON de evidencia (último a las 06:25), pero ninguna tiene aún `acceptance.json`. Ninguna está lista para la auditoría cruzada ni cerrada |
| I13, revisión semántica | Revisor A y Revisor B, a la vez | En curso con reparto cruzado; ver [revision_semantica_20261102](../audits/revision_semantica_20261102/README.md). Revisor A revisa 343 archivos (L1, L3, L5 y los cambios en curso del Revisor B). Revisor B revisa 333 (L2, L4 y lo escrito por el Revisor A) |
| Auditoría cruzada de cada tarea del Revisor B | Revisor A | Empieza cuando la tarea tenga `acceptance.json` con su `cut_id`. Repite `reproductions.py` y deja el resultado en `addendum_auditoria_20261101/audit_<tarea>.md` |
| Auditoría cruzada de lo escrito por el Revisor A | Revisor B | Skill instalado, generador del plan, addendum y `build_lots.py`. Resultado en `revision_semantica_20261102/hallazgos_revisor_b.md` |
| I02, I03, I05 | Bloqueadas por D02–D05 y por el alcance de D01 sobre flota y BESS | D01 ya decidió conservar v1 para comparar. Lo demás requiere decisión del propietario |
| Resto | Disponibles | Reservar según la regla 1 |

Riesgo de orden: I06, I08, I09 e I12 están en curso antes de que cierren sus predecesoras en el DAG (I01, I03, I04, I05, I07, I11). Se pueden preparar, pero solo se cierran tras volver a verificarlas contra las actas finales de esas predecesoras. Si una predecesora cambia una firma o un esquema, la tarea dependiente vuelve a abrirse.

Cambio fuera de tarea que debe revisarse: el 2026-11-02 Revisor A instaló el skill `task-coordination-strategies`. Añadió su entrada a `tools/skills/registry.yaml` (archivo de I12) y una línea LF a `.gitattributes` (archivo de I11). No tocó otras entradas. Revisor B debe validarlo dentro de I12/I11 con `python tools/skills/validate_skills.py --check-discovery` y `pytest tests/skills`.

## Decisiones de contrato que preceden a la implementación dependiente

| ID | Decisión concreta que debe registrarse | Evidencia y bloqueo |
|---|---|---|
| D01 | **Resuelta por el propietario el 2026-11-02:** `iquitos_v1` se conserva solo para comparar con el dataset nuevo (candidato: `iquitos_v3`) y se elimina cuando el nuevo cumpla lo mismo, según la puerta de sustitución de abajo. Falta fijar flota y controles (R-A-072) | I02/I03: config, schema y ficha PT coherentes; no reenlazar automáticamente por ser versión mayor |
| D02 | Tarifa plana/TOU, precio de exportación, mercado comunitario/net billing y KPI de costo | I02/I03: factura analítica y objetivos declarados; no prometer arbitraje temporal con precio constante |
| D03 | Comparación entre backends con acciones diferentes: equivalencia física o variantes explícitas con restricciones | I02/I04: mapa U→A, capacidad y máscaras; explicar discreto axis frente a continuo |
| D04 | Pesos/recompensa, HVAC/EV/BESS, dimensión y política reactiva/recurrente, horizonte y normalización | I02/I06: tupla y contrato con hashes; los coeficientes actuales no se atribuyen a literatura |
| D05 | HPO, buffers, fases, semillas, piloto y presupuesto medido; viabilidad de MASAC | I05/I16: protocolo versionado antes de autorizar etapas, sin conservar cifras 252 y 288 como simultáneamente vigentes |
| D06 | Alcance de distribución: checkout/wheel, LFS, ONNX y demo/piloto físico | I11/I18: producto verificable o promesa retirada; no declarar modelo ganador ni operación por defecto |

I02 registra propuestas y resolución metodológica; el implementador no elige silenciosamente una tesis diferente. Si la decisión modifica la pregunta experimental, el trabajo dependiente conserva estado `blocked_methodological_decision` hasta resolución del propietario.

### Puerta de sustitución del dataset (D01)

`iquitos_v3` terminó de construirse el 2026-11-01 a las 20:33 (America/Lima). Resultado medido el 2026-11-02 por el Revisor A, con lectura y sin modificar datos. `iquitos_v1` solo se elimina cuando todas las filas estén cumplidas:

| # | Condición | `iquitos_v3` |
|---|---|---|
| S1 | `dataset_verified`, puertas propias en verde y 0 fallos en 1836 balances | Cumple (error relativo máximo 2,4e-8) |
| S2 | Los 59 archivos coinciden con el manifiesto | Cumple (58 solo tras normalizar a LF, ver R-A-051) |
| S3 | Tres splits con 8760/8784/8760 filas y humo finito | Cumple |
| S4 | Pruebas de dataset en verde | Cumple (79 aprobadas en tariff, realism, temporal, sizing y provenance) |
| S5 | Igual cobertura de medidas que v1 | Cumple (590 medidas y 22 objetivos mensuales modelados) |
| S6 | Capacidad de control suficiente para estudiar flexibilidad, con decisión del propietario sobre flota y BESS | **No cumple:** la batería actúa sobre el 0,068 % del pico (20,1 % en v1). Falta decidir el escenario (R-A-072) |
| S7 | Escenarios E1/E2/E3 separables, o limitación declarada | **Pendiente** (R-A-005: correlación CO2–costo 0,993 sin control) |
| S8 | Precio por edificio correcto en recompensa, telemetría e inferencia | **Pendiente** (R-A-031, H07) |
| S9 | Configuración, cuadernos y pruebas reconectados al dataset nuevo, y campaña nueva preparada con su identidad | **Pendiente** (R-A-073) |
| S10 | Informe comparativo v1 frente al nuevo, con los mismos baselines sin control y RBC sobre los mismos splits, guardado con hashes | **Pendiente** (no ejecutado) |
| S11 | Ninguna referencia activa a `iquitos_v1` y ningún intento o resultado que dependa de él | **Pendiente** (88 menciones en 28 archivos) |

Eliminación: los CSV de v1 están ignorados por Git y su generador ya cambió, así que borrarlos no se puede deshacer. El paso se ejecuta una sola vez, con S1–S11 cumplidas, tras mostrar el informe S10 al propietario y recibir su confirmación final. Los JSON versionados en Git conservan la identidad y los hashes de v1. `iquitos_v2` (0 kWh de batería, superado por v3) sigue la misma puerta y el mismo paso de confirmación, por decisión del propietario del 2026-11-02. Esta tabla no autoriza entrenamiento, y ningún estado experimental cambia por ella.

## Secuencia y puertas

```mermaid
flowchart TD
  I00[Corte y conciliación I00] --> I01[Integridad de aceptación I01]
  I00 --> I02[Contrato PT y tupla I02]
  I02 --> I03[Dataset I03]
  I01 --> I04[Backends I04]
  I03 --> I04
  I04 --> I05[Recursos y HPO I05]
  I04 --> I06[Evaluación anual I06]
  I01 --> I07[Estadística I07]
  I00 --> I11[Paquete I11]
  I06 --> I08[Pipeline I08]
  I07 --> I08
  I11 --> I08
  I08 --> I09[Colab Drive I09]
  I05 --> I09
  I00 --> Q[Seguridad calidad revisión semántica y clon I10 a I15]
  I09 --> G2[Puerta nativa y campaña autorizada I16]
  Q --> G2
  G2 --> I17[Tesis y jurado I17]
  I17 -. alcance separado .-> I18[Operación futura I18]
```

El diagrama resume; el DAG exacto es `depends_on` en el JSON. No expresa autorización para agentes ni ejecución paralela.

| Puerta | Condición de cierre | Afirmación permitida |
|---|---|---|
| G0 | Corte estable, hashes, responsables y cobertura conciliada | Alcance conocido |
| G1 | Contratos estrictos, metodología, datos, seguridad aplicable, documentación operativa y calidad verificadas | Conformidad contractual del alcance |
| G2 | Cuatro aprendices reales, recarga/evaluación, instalación limpia y suite estricta sin omisiones | Preparación para entrenar el protocolo identificado |
| G3 | HPO validación, configuración congelada y presupuesto/etapas expresamente autorizados | Ejecutar confirmación definida |
| G4 | Cobertura completa, baselines, test, sensibilidad, inferencia válida y entrega hash-verificada | Aceptación científica del experimento, con o sin ganador |
| G5 | Evidencia específica de todos los J-ID y documentos estructural/visualmente revisados | Cierre de las observaciones acreditadas |
| G6 | Pruebas físicas, seguridad y operación independientes autorizadas | Aceptación operacional de ese piloto |

## Review Focus y evidencia común

1. Evidencia aparentemente válida de otra campaña/seed/intento o con cero actualizaciones: I01 debe rechazar en creación, reuso, catálogo, Drive, evaluación y entrega.
2. Última hora y año bisiesto: I06 debe conservar medición física sin relleno ni un día amputado.
3. Backend discreto con múltiples IDs equivalentes frente a control continuo: I04 debe medir y controlar el confusor antes de comparar resultados.
4. Interrupción, restauración conflictiva o dependencia de scratch: I09/I15 deben producir evidencia explícita y recuperación desde cero conforme al perfil.
5. Archivo aparentemente obsoleto pero de uso dinámico, manual o probatorio: I13/I14 deben preservar hasta verificar consumidores y recuperabilidad.

Cada acta de tarea contiene `task_id`, `cut_id`, `source_hashes`, `requirement_ids`, `input_artifacts`, `commands`, `exit_codes`, `duration_seconds`, `tests={passed,failed,errors,skipped,xfail,xpass}`, `native_scope`, `outputs`, `status`, `limitations`, `reviewer`. Debe enlazar JUnit/logs y hashes; ningún booleano aislado equivale a aceptación.

`PY` abrevia exclusivamente `.venv39-citylearn-v3/Scripts/python.exe`; ejecutar desde la raíz verificada. Los comandos siguientes son de ejecución futura, no resultados de esta entrega. Si un archivo de test fue retirado o renombrado, resolver su trazabilidad antes de ejecutar: ausencia no es aprobado. No hacer commits automáticos; preparar cambios por tarea y publicar solo con autorización aplicable.

## Tareas integradas
'''

FOOTER = r'''
## Fundamentación académica consultada en la web

Se consultaron fuentes primarias nuevamente para integrar este plan. No validan coeficientes concretos, tamaños de buffers, 12 semillas, una topología de carpetas ni un supuesto ganador. Esas son decisiones experimentales del proyecto. La lectura de fichas/resúmenes no se presenta como lectura íntegra de tesis.

| ID | Fuente y tipo | Uso y límite |
|---|---|---|
| L1 | Costea, C. C. (2026). *Multi-Agent Reinforcement Learning Building Energy Optimization: Taxonomy and Experimental Evaluation in CityLearn* [Maestría, Politecnico di Torino]. [Ficha y resumen](https://webthesis.biblio.polito.it/40396/) | Baselines/RBC, costo/carbono y KPI por edificio/distrito. Compara variantes PPO; no acredita nuestros cuatro backends ni pesos. Licencia de tesis no concede licencia a componentes de software |
| L2 | Charbonnier, F. V. J. (2023). *Multi-agent reinforcement learning for the coordination of residential energy flexibility* [Doctorado, Oxford]. [Ficha universitaria](https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5) | Contexto de coordinación energética distribuida; metadatos y resumen localizados, sin atribuir lectura integral ni validación física de Iquitos |
| L3 | Pineau, J., et al. (2021). Improving reproducibility in machine learning research. *JMLR, 22*(164), 1–20. [Editorial](https://www.jmlr.org/papers/v22/20-303.html) | Código, datos y procedimientos reproducibles; justifica trazabilidad/cortes y límites, no una arquitectura concreta |
| L4 | Oliehoek, F. A., Spaan, M. T. J., & Vlassis, N. (2008). Optimal and approximate Q-value functions for decentralized POMDPs. *JAIR, 32*, 289–353. [PDF primario](https://people.csail.mit.edu/fao/docs/Oliehoek08JAIR.pdf) | Tupla, distribución inicial e historias locales; generalización continua debe declararse. No prueba que concatenar observaciones produzca estado Markoviano |
| L5 | Nweye, K., et al. (2025; online 2024). CityLearn v2: Energy-flexible, resilient, occupant-centric, and carbon-aware management of grid-interactive communities. *Journal of Building Performance Simulation, 18*(1), 17–38. [DOI](https://doi.org/10.1080/19401493.2024.2418813) | Simulador, controles y evaluación. Editorial declara Scopus según la auditoría previa; reapertura actual devuelve 403, sin certificación nueva de indexación. No valida el fork ni sus datos privados |
| L6 | Kapoor, S., & Narayanan, A. (2023). Leakage and the reproducibility crisis in machine-learning-based science. *Patterns, 4*(9), 100804. [PubMed](https://pubmed.ncbi.nlm.nih.gov/37720327/) | Leakage y separación de evaluación; registro PubMed verificado, sin inferir otras bases ni extrapolarlo a las tesis |

Las tesis se citan como tesis universitarias; no se les atribuye indexación de revista. Los artículos editoriales y el registro PubMed aportan fuentes científicas verificables. La ingeniería concreta de guardas, limpieza y empaquetado se justifica adicionalmente por consumidores y pruebas del proyecto, no como receta supuestamente prescrita por las tesis.

Referencia técnica complementaria: [PEP 596, ciclo de Python 3.9](https://peps.python.org/pep-0596/) confirma fin de soporte el 2025-10-31. Esto motiva I11; no autoriza actualizar el runtime heredado sin matriz de compatibilidad y regresión nativa.

## Verificación y entrega de este plan

- [Matriz procesable](remediacion_integrada.json): 23 H, 31 A, 74 C, 20 FR, 17 J y continuidad de las 19 tareas P anteriores, sin ID huérfano.
- [Comprobación de cobertura](../audits/integracion_auditorias_20261101/coverage_validation.json): integridad de IDs, dependencias y hash del plan, olas coherentes con el DAG y archivos compartidos sin orden. No es aceptación del software.
- [Inventario Revisor A preservado](../audits/integracion_auditorias_20261101/inventario_auditoria.json), [ledger por archivo](../audits/integracion_auditorias_20261101/ledger_auditoria.csv), [dictamen inicial](../audits/integracion_auditorias_20261101/dictamen_inicial_auditoria.md) y [respuesta final original](../audits/integracion_auditorias_20261101/revision_final_auditoria.md).
- La secuencia comienza I00→I01/I02; I11/I10 preparan paquete/seguridad, e I13/I15 cierran revisión y reproducibilidad antes de concluir layout o habilitar campaña.
- Las casillas permanecen abiertas porque redactar el plan no implementa las correcciones. La verificación documental de esta entrega queda en `docs/audits/integracion_auditorias_20261101/validation.json`.
- Los planes previos permanecen conservados como detalle e historia. Para este encargo, I00–I18 es la secuencia de integración; al ejecutar, conciliar STATUS/traspasos y estados reales sin marcar tareas antiguas por mera existencia del código.
'''


if __name__ == '__main__':
    main()
