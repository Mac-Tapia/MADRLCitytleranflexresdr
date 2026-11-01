# Estado conciliado de las especificaciones

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

## Mapa SPEC-000–012

Todos los cortes tienen carpeta `spec.md/plan.md/tasks.md`. SPEC-011 y SPEC-012
se añadieron el 2026-10-31 a petición del usuario (flujo integral desde el
dataset y repositorio limpio). Los planes detallados en
`docs/superpowers/plans/` siguen siendo la fuente de pasos TDD; las carpetas
fijan contrato, estado y aceptación. En `tasks.md`, `[x]` solo significa que el
archivo existe en el árbol.

| SPEC | Estado y evidencia existente | Pendiente para cierre |
| --- | --- | --- |
| [000 — Constitución y línea base](000-foundation/spec.md) | `implemented` para identidad, custodia y trazabilidad: constitución, captura, manifiesto y tests contractuales. | FR-005 `partial` hasta cerrar SPEC-011. FR-007 bloqueado por SPEC-001. |
| [001 — Cadena abierta y procedencia](001-open-source-provenance/spec.md) | `verified_with_exceptions`: roles de submódulos con prueba contractual, licencias de paquetes verificadas (BSD-3-Clause), SBOM CycloneDX local, 0 hallazgos críticos y la puerta de fundación en verde. HARL, MARL y MATD3implementation siguen sin licencia en origen y operan bajo una excepción del propietario que vence el 2027-06-30. | Publicar los pedidos de licencia (`docs/research/license_requests.md`) tras aprobación; retirar la excepción si llega una licencia o sustituir el backend después de la tesis. No inventar licencias. |
| [002 — Política multiobjetivo única](002-multiobjective-policy/spec.md) | `implemented`: dominio, catálogo, adaptador CityLearn (`uc3m/adapters/citylearn/objectives.py`), test de fuente única y test de generadores; descomposición de la recompensa por término (flex/carbon/cost y EV/BESS aparte) que suma la recompensa real con tolerancia 1e-12 (`uc3m/reward/term_telemetry.py`). | Guardar la descomposición por paso en los registros de entrenamiento (requiere tocar el script común de CityLearn); depende del atributo privado `_last_component_breakdown`. |
| [003 — Orquestación modular](003-modular-orchestration/spec.md) | `partial`: layout, persistencia, completitud, reanudación, runner, CLI, `LearnerPort`, `ArtifactStore`, `NativeBackend`, `SimulatorPort` (deferred per ADR). | `ExperimentTrackerPort`, conformidad explícita de `NativeBackend`, cancelación de hijos y `orchestration_acceptance.json` (generado por campaña). |
| [004 — Manifiestos de ejecución](004-execution-manifests/spec.md) | `implemented`: identidad, custodia, `checkpoint_state.py` para optimizador/RNG/replay, `ResumePlan` requiere `training_state` (fail-closed). | Integración de `save_training_state` en los 4 launchers y manifiesto de runs históricos. |
| [005 — Evaluación científica](005-scientific-evaluation/spec.md) | `partial/pending_experiment`: campaña 4×3×3 configurada, launcher validado (dry-run 36 tratamientos), `scientific_evaluation.py`, `model_selection.py`, `TrainingReportBuilder`, acceptance gates; informe estadístico multisemilla (`tools/eval/build_campaign_statistical_report.py`: IQM, IC bootstrap estratificado por semilla, Kruskal-Wallis + Dunn-Holm, nunca declara superioridad si p ≥ α, falla cerrado ante tratamientos o semillas faltantes) y prueba de aceptación de la regla de selección; probado solo con datos sintéticos. | Ejecutar la campaña en Colab (50 ep × 8760 pasos). Defectos encontrados sin corregir: el IQM de `compute_multiseed_stats` devuelve la mediana con 3 semillas; `decide_oe_winner` declara ganador sin mirar la p de Kruskal-Wallis; `select_best_model` no exige significancia ni verifica el estado de las corridas. |
| [006 — Evidencia de tesis](006-thesis-evidence/spec.md) | `partial`: `uc3m/application/thesis/evidence_registry.py` con `EvidenceRegistry`. | Vista multiobjetivo, §3.1.3, APA y render de ambos DOCX canónicos. |
| [007 — Agentes y skills locales](007-local-agent-harness/spec.md) | `implemented/partial`: once skills con registro, hashes y licencias, validador, perfiles y enlaces locales. | Invocación real por cliente, medición de eficiencia, migración de cuatro skills legados y decisión sobre el hook heredado. |
| [008 — Artefactos y datos](008-artifacts-data/spec.md) | `partial`: almacén atómico y [ADR adoptado](../docs/decisions/ADR-OPEN-ARTIFACT-STORE.md); política de retención con 9 clases de artefacto (`governance/artifact_retention_policy.yaml`) y respaldo/restauración que verifican cada SHA-256 contra `evidence.json` y fallan cerrado (`uc3m/application/artifacts/`), probados con una corrida sintética. | Probar con una corrida real de Colab; reglas de `.gitignore` para `source_snapshot.zip` y `*.tmp` (FR-008.4); copia fuera de la máquina. |
| [009 — Observaciones del jurado](009-jury-observations/spec.md) | `partial`: manifiesto J-01–J-17 formalizado (`data/audits/jury_observations_manifest.json`), evidence registry. | Correcciones documentales, verdad estadística única, HAPPO 49/50, ejes UC3M; experimentales requieren campaña. |
| [010 — Panel local](010-local-training-panel/spec.md) | `implemented` como monitor de lectura: HTTP/HTML sin CDN, hashes, `/api/runs`, loopback. | Mantener límites; mejoras opcionales (HTML separado, curvas) no son requisito de cierre. |
| [011 — Flujo dataset → entrega](011-dataset-to-delivery-pipeline/spec.md) | `partial`: orquestador de 11 etapas y verificador de dataset; candado dataset → entrenamiento con huella independiente de la plataforma en `cli.py`, `colab.py` y el lanzador local; humo de punta a punta sin red ni GPU; herramientas de evaluación leen la campaña nueva mediante `uc3m/application/evaluation/results_catalog.py`. | Subcomandos por etapa en la CLI; 30 herramientas obsoletas de la campaña anterior y 16 que requieren decisión del propietario (`data/audits/evaluation_tools_inventory.json`). |
| [012 — Higiene del repositorio](012-repository-hygiene/spec.md) | `partial`: Stop hook desactivado, `.gitignore` actualizado (`.codex_tmp/`, browser_state, google-drive-mcp), LFS configurado para `*.pt`/`*.pkl`. | Ramas `codex/*`/`cursor/*`, duplicados restantes y prueba de higiene integral. |

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
4. **Colab:** [guía](../docs/architecture/ENTRENAMIENTO_MODULAR_COLAB.md), notebook
   y generador preservan instalación y argumentos. Pendientes: runtime real,
   wheels/CUDA, bloqueo Drive y desconexión/reanudación.
5. **Selección:** `model_selection.py` implementa regla determinista (max hypervolume,
   min variance tiebreak); ejecución pendiente de campaña completa.
6. **Higiene:** el Stop hook heredado, que publicaba todo al cerrar cada turno,
   se desactivó el 2026-10-31. Antes de eso confirmó y publicó sin revisión los
   commits automáticos `0c884b1`, `d85f9b7` y `495216d`; no se reescriben.

## Orden de continuación

El plan integral por fases está en el
[plan maestro](../docs/superpowers/plans/2026-10-31-modernizacion-integral-master-plan.md#plan-integral-por-fases).
El [plan de remediación post-auditoría](../docs/superpowers/plans/2026-10-31-post-audit-remediation-plan.md)
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
