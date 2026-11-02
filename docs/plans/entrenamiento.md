# Entrenamiento MADRL nuevo sin resultados históricos — Implementation Plan

> **For agentic workers:** Use `superpowers:executing-plans` para implementar secuencialmente este plan. No delegar por defecto. Si el usuario pide agentes, leer primero `tools/skills/madrl-agent-coordination/SKILL.md` y asignar un solo escritor por archivo. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Construir y verificar una campaña nueva reproducible, sin consumir artefactos de entrenamientos previos, preparada para entrenamiento independiente y evidencia científica nueva.

**Architecture:** Monolito modular del padre con adaptadores nativos de solo lectura. Un manifiesto de campaña enlaza fuentes, splits, configuración, intentos, evaluación y reportes; ningún consumidor descubre históricos implícitamente. Los intentos interrumpidos se reinician desde cero.

**Tech Stack:** Python 3.9 del entorno `.venv39-citylearn-v3`, PyTorch y CityLearn/backends ya disponibles, NumPy/Pandas/SciPy, YAML, pytest, PowerShell. No cambiar stack ni añadir SaaS.

**Spec:** `docs/design/entrenamiento.md` (leer completa antes de implementar).

**Anexo obligatorio de retiro y causas:** `docs/audits/historicos.md`. Contiene rutas verificadas R-01..R-07, exclusiones, consumidores, incidente HAPPO y correcciones H-01..H-12. La instrucción posterior del usuario sustituye la preservación inicial: ahora se debe ejecutar el retiro local dentro de esa lista, con inventario y controles previos.

**Árbol y unicidad obligatorios:** §12 de la especificación fija el árbol objetivo, los duplicados D-01..D-07, la selección por completitud y la puerta `repository_layout_verified`. T12 consolida y elimina clones redundantes; un contador basado solo en nombres/hash no acredita conservación de contenido.

**Buenas prácticas y GitHub:** §13/T13 fijan empaquetado, límites de capas, workflows seguros y checks verificables. Mantener layout plano con prueba de instalación, no migrarlo por apariencia. GitHub local, GitHub remoto y aceptación científica son estados independientes; no publicar ni configurar la cuenta por este encargo.

**Nombres simples, instrucción posterior:** `docs/plans/renombrar_rutas.md` y §14 del diseño fijan el mapa de renombramiento. Sus destinos cortos sustituyen los nombres/rutas propuestos en ejemplos anteriores cuando se implemente T14; los IDs científicos completos siguen en manifiestos. No mover ahora una ruta que otro agente esté usando ni cambiar hashes de una campaña congelada. Empezar por el mapa vigente, no ejecutar ciegamente nombres antiguos de esta versión del plan.

## Global Constraints

- Raíz única `D:/MADRLCitytleranflexresdr`; remoto `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`.
- Antes de cada edición u operación Git: `powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1`. Si falla, detener esa operación.
- Fuentes primarias auditadas permitidas; dataset horario previo, resultados, checkpoints, normalizadores, replay y rankings históricos prohibidos como entradas o fixtures científicos. T0 permite lectura limitada para diagnóstico/inventario/retiro, sin deserializar modelos ni reutilizar métricas como evidencia nueva.
- `CityLearn/` y `external/` no se editan. Todo cambio de implementación queda en el padre. Si una interfaz nativa impide un requisito, registrar el bloqueo concreto, sin simular éxito.
- Preservar fuentes primarias, Word, dependencias y parches concurrentes. Limpiar y eliminar únicamente los históricos R-01..R-07 mediante T0; no recrearlos como dependencia de la campaña nueva. No stage global, commit o push automático.
- Para duplicados de código/config/documentación/activos del padre, la instrucción nueva autoriza T12: una canónica por responsabilidad, integración del contenido único válido y eliminación posterior del clon. No elegir por tamaño/fecha ni borrar facades necesarios, representaciones distintas o contenido único de Word protegido. No declarar árbol desplegado sin inspección del filesystem.
- Entorno `.venv39-citylearn-v3` exclusivamente. No crear otro venv ni actualizar librerías por conveniencia.
- Dataset nuevo `data/campaigns/{storage_alias}/`; resultados nuevos `outputs/campaigns/{storage_alias}/`; rechazar raíces existentes en creación.
- `campaign_id=fresh_iquitos_20261101_v1` es el identificador propuesto, no una carpeta actualmente producida por este plan.
- Confirmación 4 algoritmos ×3 escenarios ×12 semillas 1001..1012; 50×8760 pasos; train/val/test 2023/2024/2025 con 8760/8784/8760 horas.
- `--no-resume` obligatorio. Interrupción: conservar intento fallido, nuevo intento desde cero, nunca concatenar trayectorias.
- Ningún smoke, `return_code=0`, checkpoint existente o test de importación prueba aprendizaje ni aceptación científica.
- No gasto, despliegue, hardware real ni edición Word. Implementar y medir preparación; ejecución larga requiere presupuesto/recursos autorizados, no autorización inferida de este documento.
- Todos los archivos/comandos señalados como nuevos abajo son entregables por implementar. Los comandos futuros no son ejecutables hoy por la existencia de este plan.

## Review Focus

1. Un path relativo, enlace o variable heredada puede resolver a outputs previos: rechazar antes de lectura, incluso en reintento (T1).
2. Una transformación puede filtrar valores de validación/prueba hacia train aunque el split exista: comprobar dependencias, normalizador y observaciones efectivas (T2/T3).
3. Un backend puede finalizar sin ninguna actualización: observar optimizadores reales y comprobar cambio/recarga de política (T5).
4. Un escalar finito puede tener unidad equivocada, alias duplicado o baseline cero: usar trazas y contratos dimensionales (T4/T8).
5. Una ejecución parcial o sin modelo puede parecer saludable: estados estrictos, sin `skip`/`xfail` ni fallback y sin ganador obligatorio (T6/T10/T11).

## Mapa de archivos y responsabilidades

| Propiedad | Archivos principales nuevos o modificados |
|---|---|
| Retiro histórico | Nuevos `tools/ops/historical_inventory.py`, `scripts/maintenance/retire_historical_outputs.ps1`, `tests/fresh_training/test_historical_retirement.py`; actualizar consumidores autorizados |
| Árbol/canónicas | Nuevos `governance/repository_layout.yaml`, `tools/ops/{audit_repository_layout,audit_duplicate_files}.py`, `scripts/maintenance/consolidate_repository.ps1`, dos tests de árbol/consolidación |
| Programación/GitHub | Nuevos `tools/ops/audit_github_readiness.py`, `scripts/quality/verify_ci_checkout.py`, `tests/fresh_training/test_github_readiness.py`; ajustar empaquetado/CI/ignores y documentación de colaboración |
| Identidad/aislamiento | Nuevos `uc3m/domain/campaigns.py`, `uc3m/application/training/fresh_policy.py`; extender `domain/experiments.py` |
| Construcción | Nuevos `tools/dataset/build_fresh_campaign_dataset.py`, `uc3m/application/dataset/{provenance,construction,splits}.py`; refactor acotado de herramientas del padre |
| Configuración | Nuevos `configs/experiments/iquitos.yaml`, `configs/algorithms/native.yaml`, `configs/evaluation/kpis.yaml` |
| Instrumentación | Nuevos `uc3m/adapters/algorithms/native_entrypoint.py`, `learning_observer.py`; extender `native.py` y `evidence.py` |
| KPI/evaluación | Nuevos `uc3m/application/evaluation/{kpi_contract,frozen_evaluation,baselines}.py`, `uc3m/adapters/citylearn/policy_inference.py` |
| Campaña | Nuevos `uc3m/application/training/fresh_campaign.py`, `uc3m/application/evaluation/fresh_analysis.py`; extender preflight/completion/reportes |
| Aceptación | Nuevos `tests/fresh_training/`, `scripts/quality/run_fresh_training_gates.ps1`, `docs/architecture/FRESH_TRAINING_RUNBOOK.md` |

Los tipos públicos definidos en una tarea se reutilizan en las posteriores. Su módulo propietario y campos mínimos están fijados en §11 de la especificación. Evitar crear otra jerarquía de puertos para funciones puras. Mantener `LearnerPort`, `ExperimentRunner` y el almacén de artefactos cuando sus contratos permitan la extensión; no duplicar el orquestador completo.

## T0. Diagnóstico de HAPPO y eliminación controlada de históricos

**Depende de:** fase A antes de T1; fase B después de verificar T1 y antes de T2/T5. **SPEC relacionadas:** 004/008/011/012.

**Files:** crear `tools/ops/historical_inventory.py`, `scripts/maintenance/retire_historical_outputs.ps1`, `tests/fresh_training/test_historical_retirement.py`; actualizar `docs/workflow_manifest.json`, `README.md`, `outputs/README.md` y los consumidores activos identificados en §4 del anexo. Evidencia nueva en `data/maintenance/historicos/`, fuera de las raíces a eliminar. No modificar Word, CityLearn ni external.

**Interfaces:** `inventory_historical_outputs(project_root: Path) -> RetirementPlan` en `tools/ops/historical_inventory.py`; `RetirementPlan` contiene base root, allowlist IDs, paths resueltos, inventario por archivo/hash, estado Git, protected paths, consumer findings y diagnostic records. `RetirementResult` registra deleted/already_absent/blocked/failed por objetivo. El script PowerShell recibe `-Phase Inventory|Plan|Execute -Manifest <ruta>`; predeterminado Inventory, sin borrado. No mezclar shells en las mutaciones.

- [ ] **Fase A:** releer el anexo y verificar R-01..R-07. Capturar evidencia mínima del `NameError VecEnvWrapper`, la distinción 49 previos/1 reanudado/50 declarados y los hashes antes de borrar. No registrar OOM, ausencia de aprendizaje o una fase causal concreta sin pruebas. Verificar que el wrapper actual ya contiene compatibilidad; no repetir un parche supuesto.
- [ ] Escribir pruebas `test_only_allowlisted_historical_roots_can_be_deleted`, `test_protected_primary_and_new_paths_survive`, `test_reparse_point_escape_rejected`, `test_changed_inventory_blocks_delete`, `test_retired_inputs_not_opened`, `test_duplicate_nested_targets_not_double_deleted`, `test_active_consumer_blocks_its_target`. Usar árboles temporales nuevos; no probar borrado sobre los históricos reales.
- [ ] Ejecutar `.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest tests/fresh_training/test_historical_retirement.py -q`; comprobar RED inicial y después implementar inventario/plan. No ejecutar Execute hasta que T1 esté en verde.
- [ ] **Fase B, tras T1:** verificar contención absoluta bajo el `outputs/` de esta raíz, ausencia de enlaces, hashes vigentes y consumidores/procesos activos; desacoplar punteros, defaults, notebooks y tests. No matar procesos ajenos. Un destino nuevo ambiguo queda blocked, sin ampliar allowlist.
- [ ] Ejecutar pruebas temporales y comprobar PASS. Ejecutar el retiro real autorizado con contexto verificado antes de cada borrado, `Remove-Item -LiteralPath` y lista exacta. No usar wildcard, `git clean`, reset, borrado del padre outputs, purga Git/LFS ni servicios remotos. La autorización del usuario cubre esta lista; no pedir confirmación genérica otra vez.
- [ ] Verificar ausencia de R-01..R-07 y presencia de exclusiones; guardar `retirement_result.json`. Para rutas ya ausentes registrar already_absent. No recrear resultados para satisfacer tests heredados. No afirmar que hashes sustituyen un respaldo de bytes ignorados; no crear copia completa por defecto.
- [ ] Vincular H-01..H-12 a las pruebas correctivas de T3..T10. Solo declarar `historical_retirement_complete` si no quedan destinos blocked/failed ni consumidores activos que regeneren esos históricos. Registrar borrados versionados para revisión, sin stage/commit/push automático.

## T1. Identidad nueva y aislamiento de procedencia

**Depende de:** ninguna. **SPEC relacionadas:** 000/004/008/011.

**Files:** crear `uc3m/domain/campaigns.py`, `uc3m/application/training/fresh_policy.py`, `tests/fresh_training/conftest.py`, `tests/fresh_training/test_fresh_isolation.py`; extender `uc3m/domain/experiments.py`, `uc3m/application/training/preflight.py`.

**Interfaces:** `CampaignSpec` incluye ID, fases, semillas, splits, presupuesto y policy hash. `assert_campaign_input(path: Path, role: str, manifest: CampaignSpec) -> Path`; `create_attempt(campaign, treatment_id: str) -> AttemptIdentity`. Identidad incluye configuración resuelta, acción/observación, normalizador, dataset, código, fase y semilla; el intento no cambia la definición del tratamiento.

- [ ] Escribir pruebas `test_rejects_prior_run_input`, `test_rejects_symlink_escape`, `test_fresh_root_must_not_exist`, `test_retry_starts_at_zero`, `test_archive_covers_builders_evaluators_and_lockfile`. Usar directorios temporales nuevos y sentinelas; nunca cargar datos históricos reales.
- [ ] Ejecutar `.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest tests/fresh_training/test_fresh_isolation.py -q`; observar el fallo inicial por contratos ausentes.
- [ ] Implementar política por roles: raw explícitamente aprobado, dataset/split/artefactos solo de la campaña e intento declarados, checkpoint solo tras hash. Rechazar enlaces/salidas ajenas y punteros `latest`. Ampliar snapshot a generadores, evaluadores, CLI, lockfiles y configuración sin incluir secretos ni outputs.
- [ ] Ejecutar el mismo archivo y verificar todos PASS. El `conftest.py` fija código de salida no cero ante skip/xfail/xpass en la suite nueva.
- [ ] Registrar archivos/resultados/diff en el handoff. Si se solicita commit, verificar contexto y añadir solo la lista exacta de esta tarea; no publicar.

## T2. Dataset nuevo, procedencia y balances

**Depende de:** T1. **SPEC relacionadas:** 001/011.

**Files:** crear `uc3m/application/dataset/__init__.py`, `provenance.py`, `construction.py`, `tools/dataset/build_fresh_campaign_dataset.py`, `tests/fresh_training/test_dataset_provenance.py`; modificar de forma acotada `tools/dataset/{buildingcsv_inputs,distill_building_loads,generate_iquitos_dataset,fix_solar_pvlib,dimension_ev_chargers,size_bess_optimal,sync_controlled_machines}.py` solo donde requieran entradas/salidas explícitas.

**Interfaces:** `audit_raw_sources(paths: Sequence[Path]) -> RawSourceManifest`; `build_dataset(sources: RawSourceManifest, config: DatasetBuildConfig, output_dir: Path) -> DatasetBuildManifest`. Tipos definidos en `provenance.py`/`construction.py`; manifiesto registra hashes, clasificación y parámetros por variable.

- [ ] Pruebas `test_generated_bill_is_not_measured_source`, `test_b01_has_explicit_modeled_provenance`, `test_b06_fit_excludes_heldout_years`, `test_monthly_and_peak_energy_close`, `test_no_write_inside_dependency`, `test_same_raw_and_seed_reproduce_dataset_hash`.
- [ ] Ejecutar el archivo y confirmar RED para los contratos nuevos.
- [ ] Construir desde fuentes primarias verificadas y clima nuevo; parametrizar herramientas para que no escriban en CityLearn ni reutilicen caches de outputs anteriores. Registrar calidad de B01/B06 y capas PV/EV/máquina. No usar una auditoría previa como prueba de construcción nueva.
- [ ] Verificar pruebas y ejecutar construcción real únicamente bajo raíz nueva autorizada. Guardar `provenance.json`, banderas de calidad, balance y hashes; sin inventar fuentes cuando no estén disponibles.
- [ ] Registrar limitaciones de modelado y cualquier fuente bloqueada. No marcar `dataset_verified` si falta procedencia de una primaria usada.

## T3. Splits, observaciones sin futuro y normalización congelada

**Depende de:** T2. **SPEC relacionadas:** 002/005/011.

**Files:** crear `uc3m/application/dataset/splits.py`, `uc3m/adapters/citylearn/fresh_observations.py`, `tests/fresh_training/test_temporal_contract.py`.

**Interfaces:** `materialize_splits(build: DatasetBuildManifest, output_dir: Path) -> SplitManifest`; `fit_normalizer(train_schema: Path) -> NormalizerSpec`; `apply_frozen_normalizer(observations, normalizer: NormalizerSpec)`. Dataclasses con timestamps, índices, hashes y `fit_scope`, sin dimensión fija 29.

- [ ] Pruebas `test_split_lengths_8760_8784_8760`, `test_split_schema_self_contained`, `test_heldout_perturbation_does_not_change_train_scaler`, `test_no_predicted_fields_in_effective_actor_input`, `test_scaler_shared_with_inference`.
- [ ] Ejecutar archivo y comprobar RED.
- [ ] Materializar los tres splits. Desactivar predicciones perfectas en schema y wrapper efectivo. Aplicar normalización propia ajustada solo en train; desactivar/reemplazar la normalización nativa que infiera límites con datos retenidos. Preservar codificación temporal, padding y dimensiones por agente/algoritmo como contrato serializado.
- [ ] Probar con CityLearn real en cada split: reset/step y observaciones finitas. La prueba de perturbación usa copias temporales de datos nuevos, no edita datasets congelados.
- [ ] Congelar `split_manifest.json` y `normalizer.json`; señalar cualquier dato modelado usado en cada split.

## T4. Catálogo de KPI desde trazas, con unidades verificables

**Depende de:** T1/T3. **SPEC relacionadas:** 002/005.

**Files:** crear `uc3m/application/evaluation/kpi_contract.py`, `configs/evaluation/kpis.yaml`, `tests/fresh_training/test_kpi_physical_contract.py`; modificar `uc3m/application/evaluation/training_report.py` para aceptar este contrato. La campaña nueva excluye `uc3m/kpis/evaluator.py` estimado y los alias agregados defectuosos de dependencia.

**Interfaces:** `compute_fresh_kpis(trace: PhysicalTrace, baseline: PhysicalTrace, catalog: KpiCatalog) -> KpiReport`; `validate_kpi_report(report: KpiReport) -> ValidationResult`. Definir esos tipos en `kpi_contract.py`; entradas incluyen dt, moneda, nivel, nombres y unidad de cada serie.

- [ ] Pruebas `test_total_delta_is_control_minus_baseline`, `test_total_never_averages_daily_value`, `test_district_peak_is_coincident_sum`, `test_export_does_not_erase_import_cost`, `test_baseline_zero_is_undefined`, `test_missing_not_zero`, `test_rejects_bool_nan_inf`, `test_throughput_is_not_unconditional_benefit`, `test_currency_provenance_required`, `test_no_estimated_savings_as_measured_kpi`.
- [ ] Verificar RED con `pytest tests/fresh_training/test_kpi_physical_contract.py -q` usando el Python canónico.
- [ ] Implementar fórmulas/tolerancias de §7 del diseño. Usar casos analíticos pequeños nuevos para comprobar matemáticas y trazas nuevas del simulador real para comprobar integración. No usar valores de ninguna campaña previa como expected.
- [ ] Verificar PASS y cierre mensual, total/diario, edificio/distrito y control/baseline. Guardar primarias y diagnósticos separados; no inflar la muestra estadística con métricas equivalentes.
- [ ] Documentar cuáles métricas son convencionales de CityLearn y cuáles derivaciones del proyecto; no declarar estándares implementados sin contrato y prueba.

## T5. Un único entrenamiento nativo verificable

**Depende de:** T1/T3/T4. **SPEC relacionadas:** 003/004/005.

**Files:** crear `uc3m/adapters/algorithms/{native_entrypoint,learning_observer}.py`, `tests/fresh_training/test_real_learning.py`; extender `uc3m/adapters/algorithms/native.py`, `evidence.py`, `uc3m/train.py` y `uc3m/algorithms/factory.py` únicamente para cerrar rutas que anuncien entrenamiento sin aprender.

**Interfaces:** `observe_native_learning(optimizer_specs, output_dir: Path) -> LearningObserver`; `LearningObserver.finalize() -> LearningEvidence` con pasos, actualizaciones exitosas, hashes inicial/final, no finitos y checkpoint. Entrada nueva de subproceso: `python -m uc3m.adapters.algorithms.native_entrypoint --algorithm ... --campaign-manifest ... --attempt-root ...`.

- [ ] Pruebas reales parametrizadas para los cuatro backends: `test_real_optimizer_updates_and_policy_reload`, `test_no_updates_cannot_complete`, `test_placeholder_training_rejected`, `test_instrumentation_preserves_step_semantics`. Añadir HAPPO `test_happo_current_wrapper_contract` y `test_happo_vector_env_report_reload_close`: cubrir SubprocVecEnv/unwrapped, actualización, reporte, persistencia, recarga y cierre sin NameError. Verificar al menos una actualización útil y recarga; fijar semilla y presupuesto suficiente para warmup según config, no ocho pasos.
- [ ] Ejecutar y confirmar fallo de las puertas nuevas antes de implementar. Dependencias ausentes son fallo de aceptación, no skip.
- [ ] Wrapper del padre importa el launcher nativo en proceso hijo limpio, instala observación acotada alrededor de los optimizadores expuestos por los guards existentes, preserva su comportamiento y registra el resultado. Registrar cambios efectivos de parámetros y pasos válidos, no simplemente llamadas al wrapper. HAPPO requiere cubrir también su guard HARL.
- [ ] Encaminar o rechazar explícitamente la ruta antigua `uc3m.train`; nunca devolver éxito desde entrenamiento/evaluación aleatoria. Prohibir cargar checkpoint en fase train de un intento nuevo. No reimplementar HAPPO/MASAC/MATD3/MAAC.
- [ ] Ejecutar microentrenamiento real/recarga de los cuatro y PASS. Si la interfaz observacional no está disponible, registrar el bloqueo exacto sin editar dependencias ni promover `learning_verified`.

## T6. Configuración efectiva, pesos y ejecución de campaña

**Depende de:** T1..T5. **SPEC relacionadas:** 002/003/004.

**Files:** crear `configs/experiments/iquitos.yaml`, `configs/algorithms/native.yaml`, `uc3m/application/training/fresh_campaign.py`, `tests/fresh_training/test_campaign_contract.py`; extender `uc3m/domain/objectives.py`, `uc3m/application/configuration.py`, `training/completion.py`, `training/runner.py` y CLI solo para compartir contratos, sin romper los anteriores.

**Interfaces:** `prepare_campaign(config_path: Path) -> CampaignManifest`; `run_stage(manifest_path: Path, stage: str, learner: LearnerPort) -> StageResult`. La lógica vive en `fresh_campaign.py` y recibe el puerto inyectado. Un único parser/composition root en `uc3m/application/training/cli.py`: CLI futuro `python -m uc3m.application.training.cli --config ... --stage prepare|pilot|hpo|confirm|sensitivity --execute`; omitir `--execute` solo prepara. Los wrappers/aliases existentes delegan sin mantener otro parser o bucle científico. No invocar detección GPU para generar el DAG en modo prepare sin GPU.

- [ ] Pruebas `test_144_unique_confirmatory_treatments`, `test_all_treatments_force_no_resume`, `test_interrupted_attempt_never_promotes`, `test_salvage_is_not_training_complete`, `test_episode_claim_cannot_replace_trajectory`, `test_weights_only_keeps_tariff_and_assets_equal`, `test_resolved_config_matches_backend`, `test_unknown_hyperparameter_fails`, `test_fresh_args_cannot_override_identity`, `test_prepare_needs_no_gpu`.
- [ ] Ejecutar pruebas y verificar RED.
- [ ] Implementar esquema de config estricto y resolución explícita de flags nativos; usar como fuente de pesos un único YAML. Añadir manifiestos por fase/intento. Rechazar `completed_with_salvage`, cuentas de episodios reconstruidas, estado faltante y artefactos parciales como completitud nueva.
- [ ] Validar conteos: 144 confirmatorios/63 072 000 pasos; 288 HPO/25 228 800; 72 sensibilidad/31 536 000. Cuentas y tiempos de evaluación se muestran aparte. Presupuesto medido, sin clamp silencioso de replay: cualquier cambio requiere nueva configuración resuelta antes de entrenar.
- [ ] Ejecutar `prepare` solamente y verificar DAG, comandos y manifests. No iniciar trabajo largo por ejecutar esta tarea.

## T7. Baselines nuevos y evaluación de políticas congeladas

**Depende de:** T3..T6. **SPEC relacionadas:** 005.

**Files:** crear `uc3m/application/evaluation/{baselines,frozen_evaluation}.py`, `uc3m/adapters/citylearn/policy_inference.py`, `tests/fresh_training/test_frozen_evaluation.py`.

**Interfaces:** `load_native_policy(algorithm: str, bundle: VerifiedCheckpointBundle, contract: ObservationActionContract) -> FrozenPolicy`; `FrozenPolicy.reset(seed: int)`, `FrozenPolicy.act(observations, deterministic: bool = True)`; `evaluate_frozen(policy, split, exogenous_seed, baseline_spec) -> EvaluationManifest`.

- [ ] Pruebas `test_loaded_actions_match_saved_policy`, `test_eval_has_no_optimizer_steps`, `test_recurrent_state_resets`, `test_same_ev_services_and_initial_energy`, `test_test_split_locked_until_freeze`, `test_no_model_fails_closed`.
- [ ] Ejecutar y verificar RED. Usar checkpoints del microentrenamiento nuevo T5, no modelos descargados/históricos ni mocks como aceptación nativa.
- [ ] Implementar carga/inferencia específica de cada backend usando clases y discretizadores originales. Registrar la tabla de acciones, orden de agentes, dimensiones heterogéneas y transformación física; no construir observaciones tomando primeras columnas numéricas con ceros.
- [ ] Ejecutar RBC y referencia sin optimización de almacenamiento, ambos nuevos y con los mismos servicios. Registrar energía almacenada inicial/final, pérdidas y restricciones. Mantener facturación y emisiones por paso con sus unidades reales.
- [ ] Verificar PASS y generar evaluación nueva en validación. La prueba 2025 se desbloquea solo con freeze firmado por hashes, no con un booleano arbitrario.

## T8. Piloto, HPO y sensibilidad trazables

**Depende de:** T6/T7. **SPEC relacionadas:** 002/005.

**Files:** crear `uc3m/application/training/fresh_tuning.py`, `tests/fresh_training/test_tuning_protocol.py`; conectar `fresh_campaign.py`. Reutilizar funciones puras de sensibilidad si respetan este diseño; no usar el launcher histórico como entrada de campaña.

**Interfaces:** `select_hyperparameters(validation_rows, protocol: CampaignSpec) -> ConfigurationFreeze`; `build_weight_sensitivity(protocol) -> Sequence[ExperimentSpec]`. `ConfigurationFreeze` definido en `domain/campaigns.py`, incluye hashes, regla, candidatos y razón de selección.

- [ ] Pruebas `test_equal_hpo_budget_across_algorithms`, `test_only_new_validation_can_select`, `test_no_test_or_historical_score_in_selection`, `test_all_infeasible_blocks_selection`, `test_weight_extremes_preserve_cyclic_order`, `test_pilot_not_counted_as_confirmation`.
- [ ] Ejecutar y verificar RED.
- [ ] Implementar las ocho configuraciones por algoritmo y las reglas de §5. La configuración común por algoritmo se congela antes de confirmación; no cambiar hiperparámetros entre E1/E2/E3 para mejorar retrospectivamente el resultado.
- [ ] Piloto real: después de T12-B, medir RAM/VRAM/tiempo en hardware autorizado, funcionamiento del guard y costos de evaluación. Presentar presupuesto de las fases completas y estado `ready_to_launch`; no iniciar campaña larga si falta autorización de recursos.
- [ ] Ejecutar HPO/confirmación/sensibilidad solo cuando su etapa esté autorizada, predecesores aceptados y T12-C haya acreditado estructura/unicidad a nivel software. El código de estas fases se prepara y prueba antes, sin necesitar una campaña completa para validar el layout de implementación. Reportar cada etapa separada; no afirmar entrenamientos a partir del DAG preparado.

## T9. Estadística por semilla y selección sin ganador forzado

**Depende de:** T4/T7/T8. **SPEC relacionadas:** 005/006.

**Files:** crear `uc3m/application/evaluation/fresh_analysis.py`, `tests/fresh_training/test_seed_statistics.py`; corregir/reutilizar `scientific_evaluation.py`, `model_selection.py`, `tools/eval/aggregate_multiseed_seed_kpis.py` para recibir contratos nuevos explícitos sin búsquedas históricas.

**Interfaces:** `aggregate_seed_results(manifest: CampaignManifest) -> SeedTable`; `analyze_campaign(seed_table, frozen_protocol) -> ScientificReport`; `select_candidate(validation_report) -> CandidateDecision`, que puede devolver `no_unique_candidate` o `infeasible`.

- [ ] Pruebas `test_nested_native_report_extracts_new_kpis`, `test_duplicate_seed_rejected`, `test_episode_rows_do_not_increase_n`, `test_fractional_iqm`, `test_bootstrap_by_seed`, `test_common_hv_reference`, `test_missing_treatment_blocks_acceptance`, `test_negative_results_can_be_scientifically_complete`.
- [ ] Ejecutar y verificar RED. Para unidades matemáticas, usar arrays nuevos de solución conocida; para integración, solo artefactos nuevos del piloto/campaña.
- [ ] Implementar resultados por semilla, IC 95% con 10000 remuestreos/seed7001 y familias separadas de tres omnibus, 18 pares y 12 impactos vs RBC con Holm como fija §8. Reportar incertidumbre y potencia limitada; no usar KPI distintos como bloques de réplica del algoritmo.
- [ ] Congelar referencia/orientación/normalización de hipervolumen y regla TOPSIS antes de prueba; no exigir superioridad estadística para aceptar la integridad de un estudio negativo. Separar diferencia entre algoritmos y efecto vs RBC.
- [ ] Validar coherencia contra trazas y publicación de todas las semillas, incluidas fallidas/reintentadas. No combinar estudios con distinto fingerprint.

## T10. Seguridad, CI y puerta de aceptación sin omisiones

**Depende de:** T1..T9 para aceptación integral; los controles unitarios pueden desarrollarse antes de campaña. **SPEC relacionadas:** 001/003/005/007/008/010.

**Files:** crear `tests/fresh_training/test_security_and_acceptance.py`, `scripts/quality/run_fresh_training_gates.ps1`; extender `uc3m/application/training/completion.py`, `uc3m/application/thesis/evidence_registry.py`, `.github/workflows/ci.yml` solo en alcance nuevo. Revisar, sin desplegar, `deploy/inference/{app,model_loader}.py` si se reutilizan para evaluar: preferir evaluación offline sin servicio.

**Interfaces:** `verify_fresh_acceptance(manifest_path: Path) -> AcceptanceReport` con checks y razones verificables. `register_verified_evidence(path, expected_hash, campaign_id, phase)` verifica contenido antes de aceptar. Separar aceptación de software y aceptación científica.

- [ ] Pruebas `test_skips_xfail_xpass_fail_new_acceptance`, `test_old_manifest_cannot_promote_new_campaign`, `test_hash_tamper_blocks_promotion`, `test_no_model_is_not_ready`, `test_panel_loopback_read_only`, `test_checkpoint_must_be_trusted_new_artifact`.
- [ ] Ejecutar y confirmar RED. No hacer pruebas de explotación remota, cargar pickle no confiable ni registrar secretos.
- [ ] Implementar puertas y ejecutar pruebas de seguridad sobre temporales locales. El pipeline principal no llama API demo, broker ni planta. Resolver descubrimiento de skills mediante el helper local autorizado; no copiar skills a carpetas globales.
- [ ] CI alojado ejecuta contratos puros nuevos y declara su alcance. Mantener la frontera local exacta; no desactivar `verify_project_context.ps1` para simular aceptación remota. T13 valida aparte el checkout CPU de Actions, sin habilitar entrenamiento nativo en otro path. La integración nativa completa se acredita en la raíz autorizada; no se provisiona un runner alternativo por este plan.
- [ ] El gate nuevo no requiere datasets históricos. Las pruebas históricas se inventarían en un perfil archivístico separado y fuera de aceptación nueva; no borrarlas ni convertir su ausencia en PASS. No afirmar suite general sin omisiones si solo pasó el perfil nuevo.
- [ ] Ejecutar script de gates y guardar comandos, duraciones, exit codes, contadores y hashes. Promoción científica solo tras evaluación/campaña/sensibilidad completas.

## T11. Entrega, reproducibilidad y trazabilidad de tesis

**Depende de:** T1..T10. **SPEC relacionadas:** 006/009/011.

**Files:** crear `docs/architecture/FRESH_TRAINING_RUNBOOK.md`, `tools/eval/report_fresh_campaign.py`, `tests/fresh_training/test_delivery_contract.py`; actualizar `specs/STATUS.md` y requisitos pertinentes con estados demostrados. Generar reportes solo bajo raíz nueva.

**Interfaces:** `build_fresh_delivery(manifest_path: Path, destination: Path) -> DeliveryManifest`. Exporta manifiestos, configuraciones, tablas, figuras, trazas y política candidata con hashes; no exige candidato único cuando el estudio no lo soporta.

- [ ] Pruebas `test_report_requires_campaign_id`, `test_delivery_contains_no_prior_result_reference`, `test_report_values_match_seed_table`, `test_status_never_equates_prepared_with_trained`, `test_evidence_registry_rechecks_hashes`.
- [ ] Ejecutar y confirmar RED; implementar entrega sin fallback a rutas estadísticas antiguas.
- [ ] Documentar comandos de preparación, piloto, etapas, revisión de fallos y recuperación desde cero. Mantener dos estados de entrega: `implementation_ready_for_training` y `new_campaign_scientifically_complete`.
- [ ] Crear matriz requisito -> archivo -> test/comando -> evidencia -> estado. Conservar sin resolver los pendientes ajenos (Word/render, privacidad documental completa, validación física, producción, licencias no resueltas), indicando alcance en vez de cerrarlos por redacción.
- [ ] Ejecutar validaciones documentales/contratos y gates nuevos. No editar DOCX ni insertar conclusiones hasta disponer de resultados nuevos aceptados y encargo documental explícito.

## T12. Árbol real, archivo más completo y eliminación de duplicados

**Depende de:** fase A junto a T0-A; fase B después de implementar T1..T7 y antes del piloto de T8; fase C tras T9..T11 de software y antes de lanzar HPO/confirmación/sensibilidad. La aceptación de software usa paths de su fase, sin exigir outputs científicos todavía inexistentes. **SPEC relacionadas:** 003/006/007/011/012.

**Files:** crear `governance/repository_layout.yaml`, `tools/ops/audit_repository_layout.py`, `tools/ops/audit_duplicate_files.py`, `scripts/maintenance/consolidate_repository.ps1`, `tests/fresh_training/test_repository_layout.py`, `tests/fresh_training/test_duplicate_consolidation.py`; actualizar `tools/README.md`, `scripts/README.md`, `docs/00_INDEX.md`, `.gitignore` y consumidores efectivamente migrados. Conciliar `specs/012-hygiene/spec.md` FR-012.4 y `specs/011-pipeline/spec.md` con la instrucción vigente: una canónica activa y eliminación del clon comprobado, sin copiarlo a otro archivo activo. No editar Word ni dependencias en esta tarea técnica.

**Interfaces:** `audit_repository_layout(root: Path, registry_path: Path, phase: str) -> LayoutReport`; `find_duplicate_candidates(root: Path, registry_path: Path) -> DuplicateInventory` en los módulos homónimos. `build_canonicalization_plan(inventory: DuplicateInventory, coverage_rows) -> CanonicalizationPlan` en `audit_duplicate_files.py`. Tipos serializables allí definidos con schema_version, logical_role, source/canonical paths, hashes, coverage, consumers, classification y reasons. `LayoutReport` añade actual_tree, required/missing paths y active_broken_references. `CanonicalizationPlan` exige coverage_verified para cada removed_path, no una elección por tamaño.

- [ ] **Fase A:** inspeccionar árbol real sin seguir junctions ni entrar en dependencias/env/Git; repetir hash exacto y candidatos semánticos. Confirmar D-01..D-07 de §12; registrar archivos, alcances excluidos y contenido único antes de cualquier consolidación. Un nombre repetido no demuestra clon.
- [ ] Escribir pruebas `test_required_layout_exists_for_phase`, `test_one_canonical_implementation_per_role`, `test_same_name_different_roles_are_not_duplicates`, `test_facade_contains_no_business_logic`, `test_partial_versions_merge_unique_capabilities`, `test_largest_file_is_not_automatically_canonical`, `test_no_active_broken_reference_after_move`, `test_generated_asset_keeps_one_source`, `test_protected_word_unique_content_blocks_deletion`, `test_semantically_distinct_data_identity_preserved`.
- [ ] Ejecutar con el Python canónico los dos archivos de tests y observar RED. Implementar auditores de solo lectura y registro explícito de roles/paths. AST/hash/similitud proponen candidatos; la cobertura y los consumidores deciden. No ignorar una carpeta de código duplicado para pasar el gate.
- [ ] **Fase B:** consolidar configuración en `configs/`, manteniendo las capacidades propias de extensiones sin duplicar la tabla E1/E2/E3. Un único parser en `training/cli.py`, casos de uso inyectados en `fresh_campaign.py`, una implementación Word en `tools/thesis/` y un generador de notebook de campaña en `tools/colab/build_modular_colab_notebook.py`. Integrar celdas/capacidades válidas del tutorial anterior, sin usarlo como archivo de resultados ni copiar salidas de ejecución; actualizar instalador, contrato de argumentos, notebook y tests. Retirar versiones de la misma finalidad tras cobertura demostrada. Funciones didácticas distintas requieren rol propio registrado, no otra campaña activa.
- [ ] Para D-01/D-02, conservar las rutas propuestas en §12, mantener atribución, actualizar enlaces/generadores y eliminar las tres copias redundantes solo tras revalidar hashes y consumidores. Para facades llamados por dependencias protegidas, preservar únicamente el puente necesario registrado; ningún algoritmo, peso, parser o estadística se implementa dos veces. Para Word, producir matriz de cobertura y estado de consolidación sin borrar texto único ni originales protegidos.
- [ ] Ejecutar prueba de consolidación en temporales: destino fuera de raíz/enlace, fuente cambiada, consumidor roto o pérdida de un requisito bloquean eliminación. En el árbol real usar el mismo contexto/contención/manifiesto de T0 y cmdlets nativos; no borrado por wildcard ni por basename. No desplegar placeholders para completar el dibujo del árbol.
- [ ] **Fase C:** generar `repository_tree.json`, `duplicate_inventory.json`, `canonicalization_plan.json`, `consolidation_result.json` y `repository_layout_acceptance.json` bajo `data/maintenance/repository_layout_20261101/`; reconstruir índices reales y ejecutar tests de importación, contratos y gates nuevos. Verificar que no hay referencias activas rotas, dos configuraciones activas equivalentes ni funciones clonadas sin consolidar. El código debe encontrar las fuentes por registro/configuración explícitos, no por buscar el archivo más nuevo.
- [ ] Declarar `repository_layout_verified=true` solo para el alcance/fase verificados: cero clones redundantes sin justificar, cero pérdida de contenido único, una canónica por rol y paths obligatorios presentes. Una excepción requiere función/procedencia distinta, no una excusa genérica. Reportar `blocked_unique_content` y faltantes; no afirmar ausencia universal de duplicados si no se resolvieron. `implementation_ready_for_training` y el lanzamiento largo dependen de esta puerta.

## T13. Buenas prácticas de programación y preparación para GitHub

**Depende de:** T12-C y contratos T1..T11 implementados para aceptación local. El inventario CI/metadata puede empezar junto a T12-A. La verificación remota espera publicación autorizada; no se exige ejecutarla por redactar el plan. **SPEC relacionadas:** 000/001/003/007/012.

**Files:** crear `tools/ops/audit_github_readiness.py`, `scripts/quality/verify_ci_checkout.py`, `tests/fresh_training/test_github_readiness.py`; ajustar `.github/workflows/ci.yml`, `pyproject.toml`, `.gitignore`, `.gitattributes`, README y calidad. Conciliar/crear una sola versión de LICENSE, CONTRIBUTING, SECURITY y `.github/CODEOWNERS` conforme a derechos/identidad reales, sin inventar licencias de dependencias o propietarios.

**Interfaces:** `audit_github_readiness(root: Path, candidate_tree, layout_report) -> GithubReadinessReport` en el auditor; `verify_ci_checkout(root: Path, expected_repository: str, expected_commit: str) -> ValidationResult` en el helper CI. El segundo verifica identidad/commit del checkout CPU; no autoriza cambios de proyecto o entrenamiento fuera de la raíz local. `GithubReadinessReport` contiene los campos de §13.4 y distingue ejecución local/remota.

- [ ] Escribir pruebas `test_flat_package_build_contains_only_declared_sources`, `test_installed_import_does_not_depend_on_repo_cwd`, `test_explicit_config_is_portable`, `test_declared_dependencies_cover_runtime_imports`, `test_workflow_checks_are_unique_and_paths_exist`, `test_actions_pin_full_commit_and_read_only_permissions`, `test_untrusted_pr_has_no_write_or_secrets`, `test_generated_checkpoints_not_in_candidate_tree`, `test_github_blob_size_limits_are_mib`, `test_unrun_workflow_cannot_claim_remote_acceptance`, `test_local_training_guard_remains_strict`.
- [ ] Ejecutar con Python canónico el archivo de tests y observar RED. Build/importación usan herramientas autorizadas y temporales de build ignorados, sin segundo venv en la raíz ni publicación. Si falta un entorno aislado o dependencia, registrar el procedimiento y su estado; no fingir clean-install.
- [ ] Implementar auditores y corregir metadata/importación/configuración sin cambiar stack. Resolver coherencia pyproject/requirements/lock y dependencias usadas; no actualizar versiones científicas por conveniencia. Probar compatibilidad anunciada y declarar restricciones del runtime heredado.
- [ ] Ajustar los cinco checks §13.3: permisos read-only, SHA de acciones verificados, versiones resueltas, timeouts y sin publicación ni código PR con secretos. Sustituir el uso improcedente del guard local en runner hosted por contratos CPU/helper de checkout; no relajar el guard local ni llamar a eso aceptación de learner nativo.
- [ ] Ejecutar lint, contratos, build/contenido/importación, validación de workflow y auditoría de árbol candidato. Reportar >50 MiB y rechazar nuevos blobs Git ordinarios >100 MiB; no borrar historia ni copiar pesos a LFS sin decisión explícita. Modelos/datos generados fuera del paquete y del árbol Git nuevo.
- [ ] Entregar `github_readiness.json` y nombres de checks de PR. Mantener `remote_verified=false`/`pending_remote` sin Actions del mismo commit; no hacer push/merge/settings ni contratar recursos. Una verificación futura autorizada adjunta URLs/resultados, sin equipararlos con aceptación científica.

## T14. Nombres simples y migración de rutas sin pérdida

**Depende de:** inventario actualizado T0-A/T12-A y clasificación de canónicas T12; coordinar antes de crear nuevos archivos/configs y antes del freeze. Para rutas en uso, ejecutar después de cierre del escritor; no interrumpirlo. **Plan detallado:** `docs/plans/renombrar_rutas.md` N1–N7. **SPEC relacionadas:** 004/008/011/012.

**Files:** crear `governance/naming.yaml`, `tools/ops/audit_names.py`, `scripts/maintenance/rename_paths.ps1`, `tests/fresh_training/test_names.py`; modificar solo las rutas y consumidores del mapa comprobado. Los destinos de docs/control y las carpetas SPEC se fijan en el plan de renombramiento; no hacer cambios masivos de nombres en dependencias o entorno.

**Interfaces:** `NamingInventory`, `RenameMap`, `ReferenceUpdatePlan` y funciones de N1–N5; evidencias `data/maintenance/names/{inventory,map,results,aliases,acceptance}.json`. Nombres cortos de almacenamiento desacoplados de los IDs de `ExperimentSpec`.

- [ ] Repetir inventario vigente y emitir mapa old→new: existing/planned/retired/blocked; consolidar T12 primero. Contratos RED/GREEN para nombres reservados, colisiones, contenido único y consumidores.
- [ ] Aplicar `lower_snake_case`, objetivo 24 caracteres por carpeta/40 por archivo, sin fechas largas ni hashes visibles; nombres obligatorios y dependencias tienen excepciones concretas. Mantener semillas reales como `seed_1001`, IDs SPEC/FR y todo el fingerprint en manifests.
- [ ] Usar directamente los destinos cortos para archivos todavía no creados; para existentes, actualizar imports, CLI, YAML/JSON, tests, notebooks, índices, recursos y rutas documentales en lotes coordinados. No duplicar ambas ramas ni mantener copias `_old`.
- [ ] Ejecutar movimientos solo sin actividad concurrente, con verificación de contexto/contención/bytes/destino libre y cmdlets PowerShell nativos. Una ruta bloqueada no habilita matar procesos o sobrescribir trabajo de otro agente.
- [ ] Verificar bytes y comportamiento; recalcular hashes que incluyan paths antes del freeze, sin falsificar identidades antiguas ni reanudar desde ellas. Registrar movimientos pendientes/errores con causa precisa.
- [ ] Actualizar T12/T13 y los documentos de control a las rutas finales, y acreditar `naming_verified` con cero nombres largos no justificados/refs rotas en el alcance. No afirmar renombramiento ejecutado por existir el mapa.

## Comandos de entrega al implementador

Comandos existentes para empezar:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe tools/skills/validate_skills.py
```

Comandos futuros, **solo después de implementar sus módulos**:

```powershell
# Solo preparar y revisar el DAG; no entrena.
.\.venv39-citylearn-v3\Scripts\python.exe -B -m uc3m.application.training.cli --config configs/experiments/iquitos.yaml --stage prepare

# Perfil nuevo estricto, sin datos anteriores.
powershell -ExecutionPolicy Bypass -File scripts/quality/run_fresh_training_gates.ps1

# Ejecutar únicamente con recursos autorizados y puertas precedentes verificadas.
.\.venv39-citylearn-v3\Scripts\python.exe -B -m uc3m.application.training.cli --config configs/experiments/iquitos.yaml --stage pilot --execute
```

El CLI deberá aceptar el manifiesto producido y rechazar cambios de hash posteriores. Para hpo/confirm/sensitivity, se usa la misma forma con la fase correspondiente, nunca un comando histórico. La evaluación y reportes reciben `--campaign-manifest` explícito según sus módulos implementados.

## Matriz de cobertura y puertas

| Requisito nuevo | Tarea | Evidencia de cierre |
|---|---|---|
| FR-N01 cero artefactos de entrenamiento previos | T1/T6/T11 | Política de lectura + pruebas sentinela + DAG íntegro |
| FR-N02 dataset regenerado y calidad por variable | T2 | Procedencia, balances, manifest nuevo |
| FR-N03 separación temporal sin futuro | T3 | Splits autocontenidos + prueba de perturbación + actor contract |
| FR-N04 KPI dimensionalmente correctos | T4 | Casos analíticos + cierre con trazas nuevas |
| FR-N05 cuatro aprendices nativos reales | T5 | Optimizer updates + parámetros + checkpoint recargado |
| FR-N06 pesos/hiperparámetros efectivos únicos | T6/T8 | Config resuelta y fingerprint de backend |
| FR-N07 interrupción sin mezclar historia | T1/T6 | Intento fallido intacto + reinicio desde cero |
| FR-N08 evaluación congelada y baseline justo | T7 | Cero actualizaciones + exógenas/servicios pareados |
| FR-N09 protocolo y sensibilidad nuevos | T8 | Freeze, 144 confirmatorios y 72 extremos aceptados |
| FR-N10 estadística por semillas y referencia común | T9 | Seed table, IC, contrastes y decision manifest |
| FR-N11 seguridad y aceptación sin skips | T10 | Gate estricto + límites de rutas/modelos/panel |
| FR-N12 entrega independiente de Word/históricos | T11 | Delivery manifest y runbook reproducibles |
| FR-N13 retiro local autorizado de resultados anteriores | T0-A/T1/T0-B | Inventario + consumidores resueltos + retirement_result con ausencia verificada |
| FR-N14 prevención del incidente HAPPO sin falsa completitud | T5/T6 | Regresión nativa de wrapper/reporte/recarga/cierre + rechazo de salvage |
| FR-N15 árbol efectivamente desplegado por fase | T12 | Actual tree + required paths + enlaces/imports/índices válidos |
| FR-N16 una canónica completa por responsabilidad | T12 | Comparación de cobertura + consolidación + cero clones redundantes sin justificar |
| FR-N17 programación mantenible y paquete portable | T12/T13 | Límites de capas + build/importación/configuración y dependencias coherentes |
| FR-N18 preparación GitHub con evidencia separada | T13 | Cinco checks locales; remoto solo si se verificó Actions para el mismo commit |
| FR-N19 nombres simples por contenido y sin IDs largos visibles | T14 | Naming policy + mapa old/new y excepciones justificadas |
| FR-N20 migración íntegra de referencias e identidades | T14/T12/T13 | Hashes, consumidores, contratos y manifiesto de rename verificados |

Secuencia de implementación: T0-A/T12-A -> T1 -> T0-B -> T2 -> T3 -> T4 -> T5 -> T6 -> T7 -> T12-B -> T8 -> T9 -> T10 -> T11 -> T12-C -> T13 local. T8 implementa las fases y permite piloto autorizado después de T12-B; los trabajos largos esperan T12-C de software y recursos autorizados. La aceptación científica exige sus resultados reales y revalidación del árbol generado. T13 remoto espera publicación/CI autorizados; su ausencia no invalida una campaña local rigurosa ni permite afirmar aprobación GitHub. T4 puede empezar con casos analíticos tras T1, pero su aceptación depende de T3. No microentrenar antes del retiro ni paralelizar escrituras dependientes.

## Autorrevisión y estado de este documento

- Cobertura FR-N01..20 asignada a tareas y evidencia verificable.
- T14 se coordina desde el inventario inicial y antes de congelación; sus destinos cortos prevalecen sobre los nombres extensos todavía propuestos en este documento. Las rutas actuales no se alteran hasta verificar el lote y sus consumidores.
- Árbol basado en prácticas Python/ingeniería y checks GitHub oficiales; no se afirma que GitHub exija `src/` ni que ya haya aprobado Actions.
- Árbol real/unicidad son requisitos T12, no una declaración basada en nombres. Dos grupos de imágenes idénticas se verificaron; Word, wrappers y módulos de capas distintas requieren comparación por rol y contenido.
- Configuración científica, presupuestos y etapas están en la especificación enlazada; los valores son decisiones del plan, no resultados ni garantías.
- No se prescribe un parche a submódulos; el bloqueo por interfaz externa está definido y no puede sustituirse por mock o entrenamiento aleatorio.
- El enfoque inicial sin resume evita afirmar paridad inexistente; una futura reanudación requerirá otro contrato y pruebas nativas de continuidad.
- Se distingue piloto, HPO, confirmación, sensibilidad y evaluación; no se eleva un smoke a aceptación.
- La lectura histórica se limita a inventario/diagnóstico/retiro de T0; no alimenta las fases científicas nuevas. La regresión matemática usa datos nuevos analíticos y la aceptación HAPPO usa un modelo nuevo.
- Este documento entrega un plan: todas las tareas permanecen abiertas. No se ha preparado el runtime nuevo, construido el dataset ni entrenado un algoritmo por redactarlo.
