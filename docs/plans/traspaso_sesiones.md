# Traspaso entre sesiones — remediación MADRL (2026-11-01)

Nota para cualquier sesión (Revisor A, Revisor B u otra) que retome este trabajo. Describe
quién escribe qué, los contratos acordados entre sesiones, el estado verificado y lo
pendiente. No sustituye a [specs/STATUS.md](../../specs/STATUS.md) ni acredita
aceptación científica: `implementation_ready_for_training=false`,
`scientific_acceptance=false`.

## Reglas que siguen vigentes

- Ejecutar `powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1` antes de editar u operar con Git.
- **Un solo escritor por archivo.** Antes de tocar un archivo de otra sesión, pedirlo por mensaje (`ListAgents` → `SendMessage`).
- **Sin commits ni push** salvo autorización explícita del usuario en esa sesión. El árbol tiene cientos de cambios concurrentes: nunca `git add -A`.
- `resource_authorization.authorized_stages` está vacío: no se entrena, ni local ni en Colab, sin autorización del usuario.
- **Deriva de fuentes:** `run_stage` y la CLI recalculan la identidad de entradas (`uc3m/application/training/integrity.py`). Mientras otra sesión edita fuentes, los tests que preparan y luego ejecutan una etapa pueden fallar con `campaign inputs refused: source_changed`. Es el comportamiento correcto; se repite el test aislado. La suite integral solo vale sobre un corte estable.

## Planes

| Plan | Ejecutor | Estado |
|---|---|---|
| [remediacion_auditoria.md](remediacion_auditoria.md) (P00–P18) | sesión `madrlcitytleranflexresdr-ff` | P00, P02, P03, P08, P09, P12 hechos; P01, P10, P11 parciales; P16–P18 bloqueados por autorización |
| [entrenamiento.md](entrenamiento.md) (T0–T14) | sesión `madrlcitytleranflexresdr-d8` | en curso (ver esa sesión) |
| [cuaderno_colab.md](cuaderno_colab.md) | `-ff` (Tarea 7 y contrato) + agente del generador de `-d8` | Tarea 7 hecha; contrato 29/29 en verde con el generador actual |

Registro detallado de decisiones (`Ruling:`) de `-ff`: `.superpowers/sdd/remediacion_auditoria/progress.md` (ignorado por Git, local).

## Propiedad de archivos

**Sesión `-ff` (esta nota):**
`uc3m/application/training/integrity.py`, `uc3m/application/training/fresh_campaign.py` y `cli.py` (traspasados por `-d8`), `model_selection.py`, `scientific_evaluation.py`, `uc3m/application/thesis/evidence_registry.py`, `uc3m/multicriteria/stats_tests.py`, `uc3m/domain/pareto.py`, `uc3m/reward/hphi.py`, `uc3m/algorithms/factory.py`, `uc3m/data/adapters/{local_csv,remote_http}.py`, `deploy/inference/{app,model_loader,test_app}.py`, `deploy/plant_adapter/modbus_adapter.py`, `deploy/docker-compose.yml`, `tools/ops/capture_modernization_baseline.py`, `tools/eval/build_campaign_statistical_report.py`; tests `tests/fresh_training/{test_campaign_integrity,test_attempt_acceptance,test_fresh_results_catalog,test_pipeline,test_statistical_input_gate,test_evidence_promotion,test_inference_demo_fence}.py`, `tests/ops/test_colab_notebook_cells.py`.

**Sesión `-d8`:** `fresh_analysis.py`, `fresh_acceptance.py`, `fresh_tuning.py`, `frozen_evaluation.py`, `kpi_contract.py`, `policy_inference.py`, `native_entrypoint.py`, `drive_sync.py`, `uc3m/application/dataset/provenance.py`, `configs/` (salvo el bloque `optimizer_owners`, consumido por `-ff`), generador Colab `tools/colab/*`, el `.ipynb`, CI y `pyproject.toml`.

**Sesión `-73`:** `uc3m/application/training/phases.py` (en curso).

**Revisor B (I08, plan [remediacion_integrada.md](remediacion_integrada.md)):** `uc3m/application/pipeline.py` y `uc3m/application/evaluation/results_catalog.py`, cedidos por `-ff` el 2026-11-01 por decisión del usuario (opción a). `-ff` queda como auditor cruzado de I08 en solo lectura: al recibir el `cut_id`, ejecuta `docs/audits/addendum_auditoria_20261101/reproductions.py` (P1, P4, P5) y revisa el diff. `deploy/inference/*` y `remote_http.py` siguen siendo de `-ff`.

## Contratos acordados (no cambiar sin avisar a la otra parte)

- **Entradas de campaña:** `prepare_campaign` registra `manifest['inputs'] = {nombre: {kind, path, sha256}}`; `run_stage` y la CLI rechazan si algo cambió (`campaign_inputs_changed`, exit 2).
- **Evidencia de intento:** la única válida es `<attempt_root>/learning_evidence.json` escrita por el proceso hijo; ausente o distinta de lo devuelto → `evidence_not_persisted`. Regla única: `fresh_acceptance.attempt_evidence_reasons(...)`; owners esperados en `configs/algorithms/native.yaml` → `optimizer_owners` (HAPPO `actor_agent{i}`+`critic`, MASAC 4 compartidos, MATD3 `policy_{i}/actor`+`policy_{i}/critic`, MAAC `maac_agent{i}_policy`+`maac_critic`).
- **Relanzamiento (Colab/Drive):** `run_stage` reutiliza el intento completo que pasa `fresh_acceptance.treatment_trust_reasons`; el resto recibe `try_NN` nuevo desde el episodio 0. `completion.json` y `<etapa>_result.json` se publican con `write_json_atomic`.
- **Evaluación:** `<attempt_root>/evaluation/<split>/kpi_report.json` + `evaluation_manifest.json = {"files": {"kpi_report.json": sha256}}`; `context = {campaign_id, treatment_id, algorithm, scenario, seed, split}`. `evaluate_frozen(..., adapters=citylearn_frozen_adapters())`.
- **Pipeline posentrenamiento:** `python -m uc3m.application.pipeline {status|freeze|evaluate|analyze|deliver} --manifest M [--stage] [--split] [--config] [--destination] [--workers N]`; última línea JSON; exit 0 ok/incomplete, 2 rechazo. `pipeline.py` es raíz de composición; nunca entrena.
- **Cuaderno Colab:** celdas con marcador `# [C1]…# [C11]`; contrato en `tests/ops/test_colab_notebook_cells.py`.
- **Presupuesto por fase (decisiones del usuario «Ejecución + buffers», «Congelar por etapa», «No congelar» paralelismo):** los buffers ajustados al reparto en paralelo (`phases.phase_budget`, reglas `phase_buffer` de `native.yaml`) se congelan por etapa en `stages/<etapa>_budget.json` en el primer `--execute` autorizado y son identidad del tratamiento; nunca se redimensionan (un runtime que no los soporta rechaza la fase con `insufficient_resources`). Trabajadores, `torch_threads`, fracción CUDA y parte de RAM/VRAM se recalculan en cada runtime, no son identidad, viajan al hijo por `UC3M_TORCH_THREADS`, `UC3M_CUDA_MEMORY_FRACTION`, `UC3M_WORKER_RAM_GIB`, `UC3M_WORKER_VRAM_GIB` y quedan en `resolved_treatment.json` (`execution`) y en `<etapa>_result.json` (`launch_history`). Pendiente de `-d8`: valores `phase_buffer` y que `native_entrypoint` use esas variables.

## Pendiente

1. ~~Fases de entrenamiento~~ **hecho (`-ff`)**: `training_phases: [[HAPPO, MASAC], [MATD3, MAAC]]` en `configs/experiments/iquitos.yaml`, validado en `load_campaign_config` y registrado en el manifiesto. `run_stage(..., workers=int|lista por fase)` ejecuta con `phases.run_phases`, omite fases sin tratamientos en la etapa, no arranca la Fase 2 si la Fase 1 no quedó completa y serializa `create_attempt`/`treatments.json` con un `threading.Lock`. `cli --stage prepare` imprime `phase_plan` (tratamientos y trabajadores por fase) y `measured_resources`; `--execute` usa esos trabajadores. Un error dentro del learner queda como tratamiento fallido (`error`), no como excepción. Tests: `tests/fresh_training/test_stage_phases.py`.
2. Suite integral `tests/fresh_training` sobre un corte de fuentes estable (pedirlo a `-d8`).
3. P10 restante: columnas de fase/semilla/aceptación en `uc3m/presentation/training_panel.py` (respetar loopback, solo GET, `no-store`, 404 ante traversal).
4. `deploy/docker-compose.aws.yml` sigue publicando puertos en todas las interfaces: decisión del usuario (infraestructura pública).
5. Requieren autorización del usuario: P16 (campañas), ensayo real de desconexión/restauración en Colab (P11), P17 (Word), P18 (operación).

## Entrada propia del Revisor A: dataset v4 y relevo, 2026-11-02

- **Orden del propietario (2026-11-02):** hacer la opción A y continuar lo que estaba haciendo el Revisor B. Revisor A pasa a ser el único escritor de las tareas del Revisor B mientras esa sesión no retome. Última escritura observada del Revisor B en este repositorio: 08:43 (America/Lima). Si esa sesión retoma, debe leer esta entrada y coordinar antes de escribir.
- **Alcance reservado para el dataset:** `configs/dataset/bess_design_rule.yaml`, `tools/dataset/{build_fresh_campaign_dataset,size_der_microgrids,compare_campaign_baselines}.py`, `tests/fresh_training/{test_dataset_bess_rule,test_dataset_realism,test_temporal_contract}.py`, `tests/remediation/test_d01_baseline_compare.py`, `data/campaigns/iquitos_v4/`.
- **Alcance tomado del Revisor B:** puerta de pruebas R008 (`uc3m/application/training/{gate_report,gate_pytest}.py`, `scripts/quality/run_fresh_training_gates.ps1`), L2-003, S8, mantenimiento L2 y validación integrada.
- **Estado:** en curso. Sin commits. `iquitos_v4` construido: `dataset_hash` `eb75eaa0d755…`, 7 puertas en verde, recorte entregado al 100 % en los 17 edificios en la verificación con serie conocida. `iquitos_v1`, `iquitos_v2` e `iquitos_v3` no se tocan. `authorized_stages` sigue vacío.
- **Bloqueo:** S7 no se cumple (R-A-142, R-A-143). Responsable: propietario, decisión D02. No reconectar la configuración a v4 (S9) antes de esa decisión.
- **Siguiente acción:** terminar los baselines de S10 con el catálogo declarado, reproducir los cuatro fallos de `test_same_ev_services_and_initial_energy` y ejecutar la puerta real sobre un corte estable.

## Entrada propia del Revisor B: c20261101i01, actualización 2026-11-02

- **Proyecto y corte:** `D:/MADRLCitytleranflexresdr`, origen esperado verificado, worktree `.`, rama `fix/madrl-traceability-docs`, HEAD `d55c6c6286a0f66e4909f76fc3f342ae150d703f`. El árbol contiene cambios anteriores y actuales; esta entrada no atribuye al Revisor B todos los cambios observados.
- **Responsable:** Revisor B `/root`, integrador y único escritor canónico del plan por decisión expresa del usuario. Asignaciones anteriores de archivos propios del plan quedan cedidas a esta sesión; se conservan aquí como historia. `/root/final_review` revisa sin escrituras. Implementadores aislados: `/root/i13_data_impl` posee solo cuatro módulos Stage de datos y sus pruebas; `/root/i13_stats_impl` posee seis módulos Stage estadísticos y sus pruebas. Root posee wrappers, RBC, telemetry, KPI auxiliar, gate, freezes y delivery. Stage: `.superpowers/sdd/remediacion_integrada/i13_stage`; no hay escritores concurrentes de un mismo archivo.
- **Estado:** en curso, implementación I13 tras revisión semántica L1 de 122 archivos propios (19 hallazgos adicionales). El corte canónico ya terminó; los parches nuevos se preparan aislados, se revisan y solo root los integra verificando SHA contra seed_manifest. Se preservan cambios previos y evidencia. No se declara revisión semántica completa de los 773 archivos del alcance general.
- **Decisiones y permiso:** se conserva v1 y se documentan las diferencias con el PT. El usuario autorizó expresamente cambios acotados en `CityLearn/citylearn/citylearn.py`, `CityLearn/citylearn/internal/runtime.py`, `CityLearn/citylearn/internal/kpi.py` y `external/HARL/harl/common/valuenorm.py`. Fueron aplicados con respaldo/hash. Permite las regresiones y microentrenamientos; `authorized_stages=[]` canónico sigue sin autorizar campañas anuales. No cubre otros archivos externos, Word, infraestructura pagada ni publicación.
- **Puerta de validación:** `data/maintenance/gates/fresh_profile_20261102T112634787Z.{xml,json,sources.json}` terminó con 632 casos, 628 aprobados, cuatro fallos de igualdad de entradas exógenas, cero errores y cero omitidos; fuentes estables. Los cuatro aprendices completaron el microentrenamiento, pero la puerta de software fue rechazada. Corregir y revalidar, sin promover este resultado a aceptación científica.
- **Evidencia y entrega:** [informe de ejecución](../audits/ejecucion_remediacion_20261101/informe.md), [acta por tarea](../audits/ejecucion_remediacion_20261101/evidencia.md), [recibos de dependencias](../audits/ejecucion_remediacion_20261101/dependency_application.json) y [fundamento científico](../audits/ejecucion_remediacion_20261101/fundamento.md). Las pruebas focalizadas pasan; el perfil completo anterior de627casos quedó rechazado y se conserva. La aceptación científica y operacional permanece falsa.
- **Protocolo global leído:** `C:/Users/Lenovo Legion/.agents/COORDINATION.md` y `C:/Users/Lenovo Legion/.agents/skills/team-agent-orchestration/SKILL.md`, por nueva instrucción del usuario. Cualquier encargo posterior debe incluir esas rutas, responsable, alcance y evidencia; la lectura no crea permiso para nuevos agentes o cambios ajenos.
- **Siguiente acción del Revisor B:** corregir guard del test S3 (incidente contenido y limpieza acotada autorizada completada; recibos I13/incident_s3), reproducir/corregir I13, revisar parches y ejecutar validación integrada. Las campañas anuales, Colab real, Word y operación conservan sus límites y no se autorizan por esta cesión.

## Entrada propia de la sesión `-e0`: módulo 1, 2026-11-04

- **Orden del propietario (2026-11-04):** «desbloquea y termina». Se toma como cesión de `tools/dataset/build_fresh_campaign_dataset.py` para el cambio acotado de SPEC-013. El resto de la reserva del Revisor A no cambia.
- **Hecho, sin commits:** SPEC-013 y su plan; `uc3m/domain/tariffs.py`, `uc3m/adapters/osinergmin/`, `uc3m/application/dataset/tariff_crosscheck.py`, `tools/dataset/ingest_osinergmin_pba.py`, `data/tariffs/osinergmin/`. En el constructor: importación, `BUSBAR_CSV`, rechazo en `energy_rate_ctm`, `audit/tariff_crosscheck.json` y puerta `tariff_crosscheck`.
- **Efecto para otras sesiones:** una construcción nueva requiere `data/tariffs/osinergmin/busbar_electro_oriente.csv`; sin él, `dataset_verified` es falso. `iquitos_v1` a `iquitos_v4` no se tocaron y `authorized_stages` sigue vacío.
- **Sin ejecutar:** el constructor completo con la puerta nueva.
- **Factura D02 (2026-11-04):** decisión del propietario. `uc3m/application/evaluation/bill_cost.py` y `data/tariffs/osinergmin/bill_tariffs.csv` (612 tarifas) dan el eje de costo `bill_cost_total`. **Efecto para otras sesiones:** `compute_fresh_kpis` sin `extra_measures=bill_measures(...)` deja el KPI primario no disponible y el informe rechazado; `frozen_adapters` ya las inyecta. La recompensa no cambia (D04).
- **Puerta completa (2026-11-05):** una corrida quedó 8,6 h sin resultado porque Windows suspendió el equipo por inactividad de 00:15:59 a 07:08:52. La puerta ahora evita esa suspensión, escribe `data/maintenance/gates/<corte>.execution.progress.jsonl` mientras corre y corta una prueba tras 2 h, dejando la pila en `<corte>.execution.hang.txt`. Sin suspensión tarda 1 h 2 min con 1 573 pruebas. No cerrar la tapa durante una corrida: suspende igual, aunque queda registrado como hueco.
- **Dependencias:** `gymnasium` y `pettingzoo` se declaran en los extras `train` y `all`. `uv.lock` se regeneró porque fijaba `numpy` 2.x contra `numpy<2.0` y no tenía `pypdf`. Ahora fija `numpy` 1.23.5, como `CityLearn`. `gym` queda fuera del bloqueo a propósito: `uv` no puede construir `gym==0.20.0`, que siguen fijando `requirements.txt` y el notebook (`[tool.uv]` en `pyproject.toml`).
- **Cierre del módulo 1 (2026-11-05):** puerta `-Scope Repository` aprobada sobre `0e7657bc`, 1 577 pruebas en 1 h 45 min (`data/maintenance/gates/Repository_profile_20261105T155129670Z.json`). El tiempo depende de la carga del equipo: 61 min con menos procesos concurrentes y más del doble compartiendo memoria con otro proyecto. Siguiente: módulo 2.
- **Publicación:** se excluyen `data/maintenance/integracion/*/D01/discarded/` (facturas crudas; el repositorio es público) y `external/MAAC/.git_commit_msg.tmp`.

## Entrada propia de la sesión `-e0`: módulo 2, 2026-11-05

- **Hecho:** SPEC-014. `iquitos_v5` (`fresh_iquitos_20261105_v5`) es la campaña activa en `configs/experiments/iquitos.yaml`; `iquitos_v1` a `iquitos_v4` no se tocaron.
- **Efecto para otras sesiones:** las pruebas leen `data/campaigns/iquitos_v5`, que no se versiona salvo sus JSON. Una copia sin ese dataset debe reconstruirlo con el runbook (unos 50 min con red) y `split_campaign.py`.
- **Decisión que acota otras del propietario:** `pv.max_pv_to_load_ratio = 1.0` (D-M2-1). El área de 0,63 y el crédito de exportación 1:1 siguen; subir el valor relaja el límite.
- **Defecto de Linux corregido:** `fresh_policy._under` rechazaba toda entrada de campaña en rutas absolutas POSIX. Afectaba a Colab.
- **Pendiente:** entrenar sin B01 (fuga de 2023), D04 y los supuestos económicos sin fuente.
- **Cierre del módulo 2 (2026-11-06):** puerta aprobada sobre `f27b8592`, 1 612 pruebas en 46 min. S6, S8 y S9 cumplen; S10 y S11 parciales (tabla de `remediacion_integrada.md`).
