# Traspaso entre sesiones — remediación MADRL (2026-11-01)

Nota para cualquier sesión (Claude, Codex u otra) que retome este trabajo. Describe
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
`uc3m/application/training/integrity.py`, `uc3m/application/training/fresh_campaign.py` y `cli.py` (traspasados por `-d8`), `uc3m/application/pipeline.py`, `uc3m/application/evaluation/results_catalog.py`, `model_selection.py`, `scientific_evaluation.py`, `uc3m/application/thesis/evidence_registry.py`, `uc3m/multicriteria/stats_tests.py`, `uc3m/domain/pareto.py`, `uc3m/reward/hphi.py`, `uc3m/algorithms/factory.py`, `uc3m/data/adapters/{local_csv,remote_http}.py`, `deploy/inference/{app,model_loader,test_app}.py`, `deploy/plant_adapter/modbus_adapter.py`, `deploy/docker-compose.yml`, `tools/ops/capture_modernization_baseline.py`, `tools/eval/build_campaign_statistical_report.py`; tests `tests/fresh_training/{test_campaign_integrity,test_attempt_acceptance,test_fresh_results_catalog,test_pipeline,test_statistical_input_gate,test_evidence_promotion,test_inference_demo_fence}.py`, `tests/ops/test_colab_notebook_cells.py`.

**Sesión `-d8`:** `fresh_analysis.py`, `fresh_acceptance.py`, `fresh_tuning.py`, `frozen_evaluation.py`, `kpi_contract.py`, `policy_inference.py`, `native_entrypoint.py`, `drive_sync.py`, `uc3m/application/dataset/provenance.py`, `configs/` (salvo el bloque `optimizer_owners`, consumido por `-ff`), generador Colab `tools/colab/*`, el `.ipynb`, CI y `pyproject.toml`.

**Sesión `-73`:** `uc3m/application/training/phases.py` (en curso).

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

## Entrada propia de la sesión `-e0`: módulo 1, 2026-11-04

- **Orden del propietario (2026-11-04):** «desbloquea y termina». Se toma como cesión de `tools/dataset/build_fresh_campaign_dataset.py` para el cambio acotado de SPEC-013. El resto de la reserva del Revisor A no cambia.
- **Hecho, sin commits:** SPEC-013 y su plan; `uc3m/domain/tariffs.py`, `uc3m/adapters/osinergmin/`, `uc3m/application/dataset/tariff_crosscheck.py`, `tools/dataset/ingest_osinergmin_pba.py`, `data/tariffs/osinergmin/`. En el constructor: importación, `BUSBAR_CSV`, rechazo en `energy_rate_ctm`, `audit/tariff_crosscheck.json` y puerta `tariff_crosscheck`.
- **Efecto para otras sesiones:** una construcción nueva requiere `data/tariffs/osinergmin/busbar_electro_oriente.csv`; sin él, `dataset_verified` es falso. `iquitos_v1` a `iquitos_v4` no se tocaron y `authorized_stages` sigue vacío.
- **Sin ejecutar:** el constructor completo con la puerta nueva.
