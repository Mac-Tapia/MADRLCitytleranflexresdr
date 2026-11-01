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

El manifiesto real es
[`modular_training_acceptance.json`](../data/audits/modular_training_acceptance.json):
cuatro smokes nativos E1 de ocho pasos, `four_algorithm_smoke_verified=true`,
`scientific_acceptance=false` y `full_plan_complete=false`.
`data/audits/orchestration_acceptance.json`, nombrado en el plan original,
todavía no existe: no citarlo como evidencia generada.

## Mapa SPEC-000–012

Todos los cortes tienen carpeta `spec.md/plan.md/tasks.md`. SPEC-011 y SPEC-012
se añadieron el 2026-10-31 a petición del usuario (flujo integral desde el
dataset y repositorio limpio). Los planes detallados en
`docs/superpowers/plans/` siguen siendo la fuente de pasos TDD; las carpetas
fijan contrato, estado y aceptación. En `tasks.md`, `[x]` solo significa que el
archivo existe en el árbol.

| SPEC | Estado y evidencia existente | Pendiente para cierre |
|---|---|---|
| [000 — Constitución y línea base](000-foundation/spec.md) | `implemented` para identidad, custodia y trazabilidad: constitución, captura, manifiesto y tests contractuales. | FR-005 `partial` hasta cerrar SPEC-011. FR-007 bloqueado por SPEC-001. |
| [001 — Cadena abierta y procedencia](001-open-source-provenance/spec.md) | `partial/blocked`: política, auditor de dependencias, registro de repositorios y auditor de secretos. | Tres licencias locales ausentes, dos revisiones copyleft y SBOM. No inventar licencias ni editar dependencias sin autorización. |
| [002 — Política multiobjetivo única](002-multiobjective-policy/spec.md) | `implemented` en dominio y catálogo: `uc3m/domain/objectives.py`, `scenarios.py`, YAML canónicos y detector de deriva. | Falta `uc3m/adapters/citylearn/objectives.py` y su prueba de integración; telemetría EV/BESS por término; duplicados activos restantes. |
| [003 — Orquestación modular](003-modular-orchestration/spec.md) | `partial`: layout, persistencia, completitud, reanudación, runner, CLI, `LearnerPort`, `ArtifactStore` y `NativeBackend`. | `SimulatorPort`, `ExperimentTrackerPort`, conformidad explícita de `NativeBackend`, tablas y figuras, cancelación de hijos, prueba de imports y `orchestration_acceptance.json`. |
| [004 — Manifiestos de ejecución](004-execution-manifests/spec.md) | `implemented` para identidad y custodia: `domain/experiments.py`, `domain/evidence.py`, `training/preflight.py`. | Continuidad de optimizador/RNG/replay en los cuatro algoritmos y manifiesto de runs históricos. |
| [005 — Evaluación científica](005-scientific-evaluation/spec.md) | `partial/pending_experiment`: Pareto puro, diseño de sensibilidad y dry-run. | Configuración y ejecución de la campaña 4×3 multisemilla, informe estadístico, regla de selección y `tests/acceptance/`. |
| [006 — Evidencia de tesis](006-thesis-evidence/spec.md) | `pending`: no existe `uc3m/application/thesis/`. | Registro de evidencia, vista multiobjetivo, §3.1.3, APA y render de ambos DOCX canónicos. |
| [007 — Agentes y skills locales](007-local-agent-harness/spec.md) | `implemented/partial`: once skills con registro, hashes y licencias, validador, perfiles y enlaces locales. | Invocación real por cliente, medición de eficiencia, migración de cuatro skills legados y decisión sobre el hook heredado. |
| [008 — Artefactos y datos](008-artifacts-data/spec.md) | `partial`: almacén atómico y [ADR adoptado](../docs/decisions/ADR-OPEN-ARTIFACT-STORE.md). | Política de retención, respaldo/restauración probados y retiro de artefactos grandes y temporales del índice. |
| [009 — Observaciones del jurado](009-jury-observations/spec.md) | `pending`: plan J-01–J-17 sin manifiesto. | Manifiesto, verdad estadística única, HAPPO 49/50, ejes UC3M, anexos y puerta del jurado. |
| [010 — Panel local](010-local-training-panel/spec.md) | `implemented` como monitor de lectura: HTTP/HTML sin CDN, hashes, `/api/runs`, loopback. | Mantener límites; mejoras opcionales (HTML separado, curvas) no son requisito de cierre. |
| [011 — Flujo dataset → entrega](011-dataset-to-delivery-pipeline/spec.md) | `partial`: orquestador y verificador de dataset, puerto `DatasetSource`, CLI de entrenamiento. | Consolidar los 21 scripts de `tools/dataset/`, CLI por etapas, encadenamiento por hash y humo end-to-end. |
| [012 — Higiene del repositorio](012-repository-hygiene/spec.md) | `pending`: manifiestos `*.codex_*.json` renombrados a `*.audit_*.json`; Stop hook desactivado. | Ramas `codex/*`/`cursor/*`, `.codex_tmp/` (1 213 archivos rastreados), raíz, duplicados y prueba de higiene. |

## Conciliación técnica

1. **Persistencia:** las fachadas nativas delegan layout y escritura atómica;
   `ResumePlan` exige fingerprint y archivos verificados. No demuestra igualdad
   de trayectorias al restaurar optimizador, RNG y replay.
2. **Adaptadores:** `NativeBackend` invoca los launchers HAPPO/MASAC/MATD3/MAAC
   existentes y cumple `LearnerPort` solo por tipado estructural. SPEC-003 adopta
   un único backend nativo en lugar de los cuatro archivos por algoritmo del plan
   original; falta `SimulatorPort`.
3. **Reportes:** `application/evaluation/training_report.py` proyecta KPI
   finitos; no equivale a `TrainingReportBuilder` ni `FigureRenderer`.
4. **Colab:** [guía](../docs/architecture/ENTRENAMIENTO_MODULAR_COLAB.md), notebook
   y generador preservan instalación y argumentos. Pendientes: runtime real,
   wheels/CUDA, bloqueo Drive y desconexión/reanudación.
5. **Selección:** no existe mejor modelo final aceptado.
6. **Higiene:** el Stop hook heredado, que publicaba todo al cerrar cada turno,
   se desactivó el 2026-10-31. Antes de eso confirmó y publicó sin revisión los
   commits automáticos `0c884b1`, `d85f9b7` y `495216d`; no se reescriben.

## Orden de continuación

El plan integral por fases está en el
[plan maestro](../docs/superpowers/plans/2026-10-31-modernizacion-integral-master-plan.md#plan-integral-por-fases).

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

- Charbonnier, F. V. J. (2023). *Multi-agent reinforcement learning for the coordination of residential energy flexibility* [Tesis doctoral, University of Oxford]. Oxford University Research Archive. https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5
- Costea, C. C. (2026). *Multi-agent reinforcement learning building energy optimization: Taxonomy and experimental evaluation in CityLearn* [Tesis de maestría, Politecnico di Torino]. WebThesis. https://webthesis.biblio.polito.it/40396/
- Pineau, J., Vincent-Lamarre, P., Sinha, K., Larivière, V., Beygelzimer, A., d'Alché-Buc, F., Fox, E., & Larochelle, H. (2021). Improving reproducibility in machine learning research (A report from the NeurIPS 2019 reproducibility program). *Journal of Machine Learning Research, 22*(164), 1–20. https://www.jmlr.org/papers/v22/20-303.html

Fuentes primarias consultadas el 31 de octubre de 2026. La ficha ORA se
contrastó mediante resultado indexado; la apertura directa devolvió 403.
