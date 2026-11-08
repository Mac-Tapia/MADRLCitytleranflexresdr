# Estado conciliado de las especificaciones

> Corte de implementación 2026-11-01: rige [el contrato actual v1](../docs/decisions/contrato_v1_pt.md). La ejecución y sus verificaciones se registran en [remediación integrada](../docs/plans/remediacion_integrada.md) y `data/maintenance/integracion/c20261101i01/`. Las tablas históricas inferiores conservan estados de cortes anteriores y no constituyen aceptación actual. El DAG vigente contiene pilot=4, HPO=288, confirm=144 y sensibilidad=72 tratamientos; 119941920 pasos planificados. `authorized_stages=[]`; aceptación científica y operacional siguen falsas.

Revisión: 2026-10-31 (materialización de SPEC-001–012). Este índice concilia los
planes con archivos y manifiestos existentes; no sustituye pruebas ni acredita la
secuencia histórica RED→GREEN. Los checkboxes sin evidencia permanecen abiertos.
Código implementado no equivale a aceptación científica, cierre del jurado o
modelo ganador.

## Convenciones y evidencia

- `implemented`: existe el corte indicado; no implica aceptación integral.
- `partial`: existe parte del contrato, con deuda o verificación pendiente.
- `blocked`: una puerta explícita rechaza la promoción.
- `pending`: no se acredita el entregable o experimento requerido.
- `verified_smoke`: integridad operativa corta, no aprendizaje demostrado.

**Resultados históricos retirados (2026-11-01).** Por decisión del propietario,
los resultados de campañas anteriores ya no cuentan: corrida v4 de 50
episodios, madrl_v3, espejo de Drive, smokes modulares, benchmark CityLearn v2
y evidencia de objetivos. Se retiraron de la rama y del disco; lo que estuvo en
Git se recupera desde `387a237` (etiqueta local
`archive/resultados-historicos-2026-11-01`). Por eso
[`modular_training_acceptance.json`](../data/audits/modular_training_acceptance.json)
describe smokes cuyos artefactos ya no están y se hicieron con la identidad de
dataset anterior: no es evidencia vigente. Toda evidencia nueva sale del
entrenamiento nuevo en Colab. `data/audits/orchestration_acceptance.json`,
nombrado en el plan original, no existe: no citarlo.

## Campaña nueva `fresh_iquitos_20261101_v1` (FR-N01–N18)

Plan `docs/plans/entrenamiento.md`; runbook `docs/architecture/runbook.md`. Estados
separados: `implementation_ready_for_training` y `scientific_acceptance`. Ningún
smoke, micro-entrenamiento o DAG preparado acredita entrenamiento ni ganador.

| Requisito | Archivos principales | Prueba / comando | Evidencia | Estado |
| --- | --- | --- | --- | --- |
| FR-N13 retiro R-01..R-07 | `tools/ops/historical_inventory.py`, `scripts/maintenance/retire_historical_outputs.ps1` | `tests/fresh_training/test_historical_retirement.py` | `data/maintenance/historicos/retirement_result.json` (R-06/R-07 borrados, R-01..R-05 ausentes) | implemented; regenerador R-06 mitigado por la entrada nativa nueva |
| FR-N01 cero artefactos previos | `uc3m/domain/campaigns.py`, `uc3m/application/training/fresh_policy.py`, `governance/repository_layout.yaml` | `test_fresh_isolation.py`, `test_single_launch_path.py` | lanzadores antiguos y AWS retirados (registro `launch`) | implemented |
| FR-N02 dataset nuevo | `tools/dataset/build_fresh_campaign_dataset.py`, `uc3m/application/dataset/{provenance,construction}.py` | `test_dataset_provenance.py`, `test_der_sizing_inputs.py` | `data/campaigns/iquitos_v1/dataset_acceptance.json`: `dataset_verified=true`, 1836 cierres, hash `6adc312c…` | verified (B01 2023 retroproyección declarada) |
| FR-N03 splits sin futuro | `uc3m/application/dataset/splits.py`, `uc3m/adapters/citylearn/fresh_observations.py`, `tools/dataset/split_campaign.py` | `test_temporal_contract.py` | `split_manifest.json`, `normalizer.json` (train_2023), `split_smoke.json` | verified |
| FR-N04 KPI desde trazas | `uc3m/application/evaluation/kpi_contract.py`, `configs/evaluation/kpis.yaml` | `test_kpi_physical_contract.py`, `test_frozen_evaluation.py` | casos analíticos; trazas reales con baselines | partial |
| FR-N05 aprendices reales | `uc3m/adapters/algorithms/{native_entrypoint,learning_observer}.py` | `test_learning_observer.py`, `test_real_learning.py` | HAPPO y MASAC verificados (actualizaciones observadas, parámetros cambiados, checkpoints) | partial: MATD3/MAAC en curso |
| FR-N06/N07 configuración y reinicio | `configs/experiments/iquitos.yaml`, `configs/algorithms/native.yaml`, `uc3m/application/training/{fresh_campaign,cli}.py` | `test_campaign_contract.py` | DAG 144/252/72 (HPO MASAC: 4 configuraciones efectivas, ver auditoría); `--no-resume` forzado; salvage rechazado; confirm/sensibilidad corren la configuración congelada (`configuration_freezes.json`) o se rechazan | implemented |
| FR-N08 evaluación congelada | `uc3m/adapters/citylearn/policy_inference.py` | `test_frozen_evaluation.py` | baselines RBC y sin almacenamiento; cargadores nativos pendientes | partial |
| FR-N09 HPO/sensibilidad | `fresh_campaign.py` (`freeze_configuration`, `write_configuration_freezes`, `write_derived_scenario_catalog`), `uc3m/domain/campaigns.py` (`ConfigurationFreeze`) | `test_campaign_contract.py` | contrato de congelado y catálogos derivados con hash; selección sobre validación (cargadores nativos T7-2) no implementada | partial: contrato implementado, selección pendiente (T8) |
| FR-N10 estadística por semilla | `uc3m/application/evaluation/fresh_analysis.py` | `test_seed_statistics.py` | contratos matemáticos | implemented (sin datos reales) |
| FR-N11 aceptación sin omisiones | `tests/fresh_training/conftest.py`, `scripts/quality/run_fresh_training_gates.ps1` | puerta del perfil nuevo | `data/maintenance/gates/` | partial: pruebas de seguridad pendientes |
| FR-N12 entrega | `docs/architecture/runbook.md` | — | — | partial |
| FR-N14 incidente HAPPO | `native_entrypoint.py` (salvage por `job_directory`) | `test_real_learning.py[HAPPO]`, `test_campaign_contract.py` | HAPPO entrena, reporta, guarda y cierra sin NameError | verified |
| FR-N15/N16 árbol y canónicas | `governance/{repository_layout,naming}.yaml` | `test_names.py`, `test_single_launch_path.py` | `data/maintenance/layout/consolidation_*.json` (D-02, D-06), nombres 0 candidatos | partial: Word y notebooks tutoriales pendientes |
| FR-N17/N18 programación y GitHub | — | — | — | pending (T13) |

`implementation_ready_for_training`: false hasta cerrar FR-N05 (4 backends) y la
puerta del perfil nuevo. `scientific_acceptance`: false.

### Auditoría de recompensa, pesos e hiperparámetros (2026-11-01)

Correcciones con pruebas (RED observado antes de implementar); ninguna es evidencia de entrenamiento.

| Defecto | Corrección | Prueba |
| --- | --- | --- |
| confirm/sensibilidad con defaults nativos | `ConfigurationFreeze` con hiperparámetros y hash ligado; `configuration_freezes.json` con sha256 en el manifiesto; `run_stage` materializa los argumentos desde el congelado, rechaza ausente/alterado/no candidato; la identidad del tratamiento incluye congelado, hiperparámetros efectivos y hash del catálogo | `test_campaign_contract.py` |
| pesos de sensibilidad no llegaban a la recompensa | la recompensa lee `axis_weights` del catálogo de `UC3M_SCENARIO_CATALOG` (`scenario_catalog_axis_weights`); sensibilidad genera un catálogo derivado con hash bajo `stages/sensitivity_catalogs/`; `scenario_manager` ya no rechaza políticas derivadas; pesos efectivos registrados en la evidencia y comparados con `treatment.weights` | `test_campaign_contract.py`, `tests/uc3m/test_reward_kpi_alignment.py`, `test_learning_observer.py` (simulador real, 3 pasos) |
| réplica MATD3 500 transiciones | `--buffer-size 148920` (total, 8760 por política = 1 episodio, ~6,3 GiB); MAAC `--buffer-length 43800`; `--batch-size 256` explícito. **Sustituido** (SPEC-015 D-M3-5, 2026-11-06): MATD3 744 600 y lote 256; MAAC con el esquema de su autor: búfer 10⁶, lote 1 024 y 4 actualizaciones cada 100 pasos | `test_replay_and_batch_are_declared_for_off_policy_backends`, `test_author_capacity.py` |
| grilla MASAC colapsada | `native_clamps` (rnn_hidden_dim ≤ 64 si T ≥ 1000) aplicado en el DAG; candidatos idénticos fusionados (c1/c3, c2/c4, c5/c7, c6/c8); HPO 252 tratamientos, 22 075 200 pasos (total 116 683 200) | `test_masac_grid_has_no_duplicate_effective_configuration` |
| MASAC 1 actualización/episodio | `--critic-train-steps 1` declarado; limitación declarada en `native.yaml` y en el manifiesto (`declared_limitations`): el lanzador nativo fuerza 1 para T ≥ 1000; no se editó | `test_masac_single_update_per_episode_is_declared` |
| recompensa (mezcla muerta, tanh, importación ×4, incentivos EV) | perfil `fresh_kpi_aligned_v5`: términos locales y pago común por `team_mean`; pico cuadrático y rampa lineal sobre potencia neta distrital; CO2 y costo lineales en importación × intensidad/precio sin offsets; EV/BESS solo penalizaciones fuera del vector ponderado; desglose raw/norm/bounded/sat/weighted/local | `tests/uc3m/test_reward_kpi_alignment.py`, `test_reward_term_telemetry.py`, `CityLearn/tests/test_citylearn_v3_reward_hierarchy.py` |
| supervisión | `RewardSupervisor` en la entrada nativa: `supervision.json` por intento (medias por eje, dominancia EV+BESS, saturación, dispersión de acciones por agente, pesos efectivos, agregación); `attempt_completion` rechaza dominancia > `supervision.max_constraint_dominance_ratio` (1,0; criterio del proyecto) | `test_learning_observer.py`, `test_effective_weights_and_dominance_gate_completion` |
| suite regeneraba `outputs/dataset_cache` | `tests/conftest.py` redirige `_CSV_CACHE_DIR` a un tmp de sesión; `test_real_learning.py` compara el estado antes/después y exige `native_cache` no vacío | `test_cache_isolation.py` |

Huecos: la réplica MATD3 no cubre varios episodios dentro de 16 GB; el presupuesto HPO
de MASAC (4 configuraciones) difiere del resto; el resto de presupuestos de
actualización y espacios de acción por backend sigue siendo un confusor declarado;
`test_real_learning.py` no se re-ejecutó tras estos cambios; scripts heredados
(`tools/training/verify_training_optimization.py`,
`CityLearn/scripts/validate_citylearn_v3_reward_profiles.py`) y textos de tesis siguen
describiendo el perfil v4 (0,70/0,30).

## Mapa SPEC-000–012

Todos los cortes tienen carpeta `spec.md/plan.md/tasks.md`. SPEC-011 y SPEC-012
se añadieron el 2026-10-31 a petición del usuario (flujo integral desde el
dataset y repositorio limpio). Los planes detallados en
`docs/plans/` siguen siendo la fuente de pasos TDD; las carpetas
fijan contrato, estado y aceptación. En `tasks.md`, `[x]` solo significa que el
archivo existe en el árbol.

| SPEC | Estado y evidencia existente | Pendiente para cierre |
| --- | --- | --- |
| [000 — Constitución y línea base](000-foundation/spec.md) | `implemented` para identidad, custodia y trazabilidad: constitución, captura, manifiesto y tests contractuales. | FR-005 `partial` hasta cerrar SPEC-011. FR-007 bloqueado por SPEC-001. |
| [001 — Cadena abierta y procedencia](001-provenance/spec.md) | `verified_with_exceptions`: roles de submódulos con prueba contractual, licencias de paquetes verificadas (BSD-3-Clause), SBOM CycloneDX local, 0 hallazgos críticos y la puerta de fundación en verde. HARL, MARL y MATD3implementation siguen sin licencia en origen y operan bajo una excepción del propietario que vence el 2027-06-30. | Publicar los pedidos de licencia (`docs/research/license_requests.md`) tras aprobación; retirar la excepción si llega una licencia o sustituir el backend después de la tesis. No inventar licencias. |
| [002 — Política multiobjetivo única](002-objectives/spec.md) | `implemented`: dominio, catálogo, adaptador CityLearn (`uc3m/adapters/citylearn/objectives.py`), test de fuente única y test de generadores; descomposición de la recompensa por término (flex/carbon/cost y EV/BESS aparte) que suma la recompensa real con tolerancia 1e-12 (`uc3m/reward/term_telemetry.py`); en los registros de entrenamiento, por edificio y con cuadre por paso (SPEC-015 FR-015.6, `a9b5620c`). | Descomposición por paso en el episodio de evaluación congelada (FR-002.5, módulo 5). |
| [003 — Orquestación modular](003-orchestration/spec.md) | `partial`: layout, persistencia, completitud, reanudación, runner, CLI, `LearnerPort`, `ArtifactStore`, `NativeBackend`, `SimulatorPort` (deferred per ADR). | `ExperimentTrackerPort`, extracción de reportes y `FigureRenderer` (FR-003.4, módulo 5) y `orchestration_acceptance.json` (generado por campaña). Conformidad de `NativeBackend` y cancelación de hijos cerradas por SPEC-015 FR-015.4 (`a2740ac1`). |
| [004 — Manifiestos de ejecución](004-manifests/spec.md) | `implemented`: identidad, custodia, `checkpoint_state.py` para optimizador/RNG/replay, `ResumePlan` requiere `training_state` (fail-closed). | Manifiesto de runs históricos. `save_training_state` en los 4 lanzadores cerrado por SPEC-015 FR-015.5 (`646b2f8d`). |
| [005 — Evaluación científica](005-evaluation/spec.md) | `partial/pending_experiment`: campaña 4×3×3 configurada, launcher validado (dry-run 36 tratamientos), `scientific_evaluation.py`, `model_selection.py`, `TrainingReportBuilder`, acceptance gates; informe estadístico multisemilla (`tools/eval/build_campaign_statistical_report.py`: IQM, IC bootstrap estratificado por semilla, Kruskal-Wallis + Dunn-Holm, nunca declara superioridad si p ≥ α, falla cerrado ante tratamientos o semillas faltantes) y prueba de aceptación de la regla de selección; probado solo con datos sintéticos. | Ejecutar la campaña en Colab (50 ep × 8760 pasos). Defectos encontrados sin corregir: el IQM de `compute_multiseed_stats` devuelve la mediana con 3 semillas; `decide_oe_winner` declara ganador sin mirar la p de Kruskal-Wallis; `select_best_model` no exige significancia ni verifica el estado de las corridas. |
| [006 — Evidencia de tesis](006-evidence/spec.md) | `partial`: `uc3m/application/thesis/evidence_registry.py` con `EvidenceRegistry`. | Vista multiobjetivo, §3.1.3, APA y render de ambos DOCX canónicos. |
| [007 — Agentes y skills locales](007-agents/spec.md) | `implemented/partial`: once skills con registro, hashes y licencias, validador, perfiles y enlaces locales. | Invocación real por cliente, medición de eficiencia, migración de cuatro skills legados y decisión sobre el hook heredado. |
| [008 — Artefactos y datos](008-artifacts/spec.md) | `partial`: almacén atómico y [ADR adoptado](../docs/decisions/artifact_store.md); política de retención con 9 clases de artefacto (`governance/artifact_retention_policy.yaml`) y respaldo/restauración que verifican cada SHA-256 contra `evidence.json` y fallan cerrado (`uc3m/application/artifacts/`), probados con una corrida sintética. | Probar con una corrida real de Colab; reglas de `.gitignore` para `source_snapshot.zip` y `*.tmp` (FR-008.4); copia fuera de la máquina. |
| [009 — Observaciones del jurado](009-jury/spec.md) | `partial`: manifiesto J-01–J-17 formalizado (`data/audits/jury_observations_manifest.json`), evidence registry. | Correcciones documentales, verdad estadística única, HAPPO 49/50, ejes UC3M; experimentales requieren campaña. |
| [010 — Panel local](010-panel/spec.md) | `implemented` como monitor de lectura: HTTP/HTML sin CDN, hashes, `/api/runs`, loopback. | Mantener límites; mejoras opcionales (HTML separado, curvas) no son requisito de cierre. |
| [011 — Flujo dataset → entrega](011-pipeline/spec.md) | `partial`: orquestador de 11 etapas y verificador de dataset; candado dataset → entrenamiento con huella independiente de la plataforma en `cli.py`, `colab.py` y el lanzador local; humo de punta a punta sin red ni GPU; herramientas de evaluación leen la campaña nueva mediante `uc3m/application/evaluation/results_catalog.py`. | Subcomandos por etapa en la CLI; 30 herramientas obsoletas de la campaña anterior y 16 que requieren decisión del propietario (`data/audits/evaluation_tools_inventory.json`). |
| [012 — Higiene del repositorio](012-hygiene/spec.md) | `partial`: Stop hook desactivado, `.gitignore` actualizado (`.codex_tmp/`, browser_state, google-drive-mcp), LFS configurado para `*.pt`/`*.pkl`. | Ramas `codex/*`/`cursor/*`, duplicados restantes y prueba de higiene integral. |
| [013 — Módulo 1: tarifas oficiales](013-modulo1-tarifas/spec.md) | `implemented`: ingesta de PDF PBA de Osinergmin y contraste con los pliegos (37 vigencias, 34 contrastadas, 0 fallos; `data/tariffs/osinergmin/`), puerta `tariff_crosscheck` en el constructor y factura con cargo por potencia como eje de costo (D02, 612 tarifas). [Plan](../docs/plans/modulo1_tarifas.md). No cambia ningún dataset, el precio del simulador ni la recompensa. Puerta completa aprobada sobre `0e7657bc` (1 577 pruebas), sin aceptación científica. | Decisión D04 (recompensar la factura); ejecutar la puerta en una construcción nueva; localizar PDF de 8 vigencias sin documento; cargo por potencia `unverified` frente a facturas. |
| [014 — Módulo 2: dataset físico y reconexión](014-modulo2-dataset/spec.md) | `implemented`: `iquitos_v5` con 10 de 10 puertas, FV/carga ≤ 1,0 por edificio, `csv_integrity` bloqueante, sensibilidad sin B01 en la evaluación y configuración reconectada (S9). Línea base: factura −0,44 %, CO₂ +0,69 %, pico −1,95 %. `authorized_stages=[]`, sin aceptación científica. | Entrenar sin B01 para la fuga de 2023; recompensa de la factura (D04); supuestos económicos `assumption_pending_user_verification`; picos horarios sin contraste (D3-008). |
| [015 — Módulo 3: algoritmos y recursos](015-modulo3-algoritmos/spec.md) | `implemented` (2026-11-06): requisitos de memoria ligados al dataset activo y por candidato; capacidad nativa de los 4 MADRL (D-M3-5); conformidad de `NativeBackend` y cancelación de hijos; `training_state.pt` en los 4 lanzadores; recompensa por edificio con cuadre por paso; D03 con máscaras discretas (MASAC, MAAC) y salidas continuas inertes declaradas (HAPPO, MATD3), mapa acción → equipo en cada intento. Revisión independiente: 3 hallazgos importantes corregidos en `e5ae4d4f` (mapa de acciones exigido al cargar MASAC y MAAC; confusión continuo/discreto declarada); 7 menores diferidos al módulo 3b. Puerta `Repository` aprobada sobre `e5ae4d4f` (1 663 pruebas; `data/maintenance/gates/Repository_profile_20261107T041716877Z.json`). Sin aceptación científica. | — |
| [016 — `iquitos_v6`](016-iquitos-v6/spec.md) | `in_progress` (2026-11-08): decisiones D-V6-1 a D-V6-55. Dataset activo `iquitos_v6_trial10` (12/12 puertas, hash `b8466b46…`). Capa v3: cola de vehículos, SOC real, V2B acotado, observación por clase de cargador, recompensa con cargo por potencia (D-V6-50), aire acondicionado como acción con modelo ISO 13790 5R1C anclado a la factura (D-V6-52/53; no validado con ASHRAE G14 por falta de datos medidos), confort no peor que hoy (D-V6-54) y re-destilación de picos con la refrigeración (D-V6-55). Rejilla común de 5 niveles por equipo para los 4 MADRL, con MASAC y MAAC ramificados (SPEC-015 D-M3-9/10). Pruebas de la tupla, trazabilidad y humo de los 4 con `training_state.pt`. | Etiquetar las decisiones implementadas sin etiqueta; confirmar P-V6-15 a P-V6-25 y P-017-1 a P-017-6; datos medidos de temperatura interior o del aire acondicionado para validar el 5R1C. |
| [017 — Universalidad](017-universalidad/spec.md) | `draft` (propietario, 2026-11-07): cualquier edificio, cualquier lugar, cualquier MADRL en v3, dataset operativo al crearse. | FR-017.1 a FR-017.5 implementados (sitio, cualquier edificio, contrato de backend, puerta de operatividad, origen de cada valor). Pendiente: criterio 1 (sitio sintético de 2 edificios) sobre el constructor `iquitos_v6` (3b.4) y confirmar P-017-1 a P-017-6. |

## Conciliación técnica

1. **Persistencia:** las fachadas nativas delegan layout y escritura atómica;
   `ResumePlan` exige fingerprint, archivos verificados y `training_state` (fail-closed).
   `checkpoint_state.py` en CityLearn provee save/load de optimizador, RNG y replay.
2. **Adaptadores:** `NativeBackend` invoca los launchers HAPPO/MASAC/MATD3/MAAC
   existentes y cumple `LearnerPort` solo por tipado estructural. SPEC-003 adopta
   un único backend nativo en lugar de los cuatro archivos por algoritmo del plan
   original; `SimulatorPort` definido como Protocol con ADR de integración diferida.
3. **Reportes:** `training_report.py` proyecta KPI finitos; `TrainingReportBuilder`
   añadido con KPIs estructurados. `scientific_evaluation.py` y `model_selection.py`
   implementados. Falta `FigureRenderer`.
4. **Colab:** [guía](../docs/architecture/colab.md), notebook
   y generador preservan instalación y argumentos. Pendientes: runtime real,
   wheels/CUDA, bloqueo Drive y desconexión/reanudación.
5. **Selección:** `model_selection.py` implementa regla determinista (max hypervolume,
   min variance tiebreak); ejecución pendiente de campaña completa.
6. **Higiene:** el Stop hook heredado, que publicaba todo al cerrar cada turno,
   se desactivó el 2026-10-31. Antes de eso confirmó y publicó sin revisión los
   commits automáticos `0c884b1`, `d85f9b7` y `495216d`; no se reescriben.

## Orden de continuación

El plan integral por fases está en el
[plan maestro](../docs/plans/modernizacion.md#plan-integral-por-fases).
El [plan de remediación post-auditoría](../docs/plans/correcciones.md)
detalla las 8 tareas TDD derivadas de los 16 hallazgos de la auditoría independiente.

- [x] Materializar SPEC-007 con contrato, plan y tareas.
- [x] Materializar SPEC-001–006, SPEC-008–009 y los nuevos SPEC-011–012.
- [ ] Fase 0 — Higiene (SPEC-012); Stop hook ya desactivado.
- [ ] Fase 1 — Procedencia y licencias (SPEC-001).
- [ ] Fase 2 — Puertos y adaptadores faltantes (SPEC-002, SPEC-003).
- [ ] Fase 3 — Flujo dataset → entrega con humo end-to-end (SPEC-011).
- [ ] Fase 4 — Continuidad, retención y artefactos (SPEC-004, SPEC-008).
- [ ] Fase 5 — Campaña aprobada 4×3 multisemilla y selección (SPEC-005).
- [ ] Fase 6 — Evidencia de tesis y observaciones del jurado (SPEC-006, SPEC-009).
- [ ] Fase 7 — Skills legados y eficiencia medida (SPEC-007).
- [ ] Fase 8 — Aceptación integral; completar solo con todas las puertas acreditadas.

## Sustento y límites (APA 7)

Separar costo, emisiones, indicadores de red y baselines es coherente con
Costea (2026). Charbonnier (2023) aporta el contexto de coordinación energética
MARL. La custodia de código, datos y procedimientos responde al problema de
reproducibilidad tratado por Pineau et al. (2021). Estas fuentes fundamentan
evaluación y trazabilidad; no prescriben este servidor, no validan los pesos
exactos ni garantizan rendimiento de skills o agentes.

- Charbonnier, F. V. J. (2023). *Multi-agent reinforcement learning for the coordination of residential energy flexibility* [Tesis doctoral, University of Oxford]. Oxford University Research Archive. <https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5>
- Costea, C. C. (2026). *Multi-agent reinforcement learning building energy optimization: Taxonomy and experimental evaluation in CityLearn* [Tesis de maestría, Politecnico di Torino]. WebThesis. <https://webthesis.biblio.polito.it/40396/>
- Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d'Alché-Buc, F., Fox, E., & Larochelle, H. (2021). Improving reproducibility in machine learning research (A report from the NeurIPS 2019 reproducibility program). *Journal of Machine Learning Research, 22*(164), 1–20. <https://www.jmlr.org/papers/v22/20-303.html>

Fuentes primarias consultadas el 31 de octubre de 2026. La ficha ORA se
contrastó mediante resultado indexado; la apertura directa devolvió 403.
