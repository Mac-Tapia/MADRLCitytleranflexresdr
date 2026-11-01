# Estado conciliado de las especificaciones

Revisión: 2026-10-31. Este índice concilia los planes con archivos y manifiestos
existentes; no sustituye pruebas ni acredita la secuencia histórica RED→GREEN.
Los checkboxes originales sin evidencia permanecen abiertos. Código
implementado no equivale a aceptación científica, cierre del jurado o modelo ganador.

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

## Mapa SPEC-000–010

SPEC-001–009 están definidos en el
[diseño aprobado](../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md),
pero salvo SPEC-007 todavía no tienen cada uno su carpeta completa `spec.md/plan.md/tasks.md`.
Hasta materializarlas, sus contratos viven en los planes enlazados. Esta
correspondencia permite continuar, pero no cierra esa deuda documental.

| SPEC | Estado y evidencia existente | Pendiente para cierre |
|---|---|---|
| [000 — Constitución y línea base](000-foundation/spec.md) | `implemented` para identidad, custodia y trazabilidad inicial: constitución, captura, manifiesto y tests contractuales. | FR-005 sigue `partial` hasta completar dataset→evaluación→selección→entrega. FR-007 tiene política implementada, pero aceptación bloqueada por SPEC-001. |
| 001 — Cadena abierta y procedencia | `partial/blocked`: política, auditorías y registro; [plan de fundación](../docs/superpowers/plans/2026-10-31-foundation-open-source-spec-kit-plan.md). | Resolver tres licencias locales ausentes, dos revisiones copyleft e inventario de paquetes. No inventar licencias ni editar dependencias sin autorización vigente. |
| 002 — Política multiobjetivo única | `implemented` en dominio y catálogo: `uc3m/domain/objectives.py`, `scenarios.py`, YAML canónicos; [plan multiobjetivo](../docs/superpowers/plans/2026-10-31-multiobjective-domain-plan.md). | Consolidar proyecciones documentales y registrar adaptador nativo real. No existe `uc3m/adapters/citylearn/objectives.py`; sensibilidad arbitraria aún no entrenable por backend actual. |
| 003 — Orquestación modular | `partial`: layout, persistencia, completitud, reanudación, runner, CLI, `LearnerPort` y `NativeBackend`; [plan de orquestación](../docs/superpowers/plans/2026-10-31-orchestration-artifacts-plan.md). | Extraer reportes/figuras; documentar desviaciones de puertos; probar continuidad de entrenamiento y cancelación de hijos tras muerte del padre. |
| 004 — Manifiestos de ejecución | `implemented` para identidad y custodia local: `domain/experiments.py`, `domain/evidence.py`, `training/preflight.py`, hashes y snapshot ZIP. | Acreditar continuidad de optimizador/RNG/replay en los cuatro algoritmos y custodia de campañas completas; no reinterpretar resultados históricos. |
| 005 — Evaluación científica | `partial/pending_experiment`: Pareto puro, diseño de sensibilidad y dry-run presupuestado. | Campaña completa 4×3 multisemilla, baselines, KPI independientes y aceptación estadística. La matriz del simulador no demuestra aprendizaje real 4×3. |
| 006 — Evidencia de tesis | `pending` para cierre integrado: [plan de tesis y agentes](../docs/superpowers/plans/2026-10-31-thesis-agents-plan.md). | Evidencia promovida, tablas/figuras trazables, coherencia única en §3.1.3, APA, reapertura y render de ambos DOCX canónicos. No reemplazar experimentos por redacción. |
| [007 — Agentes y skills locales](007-local-agent-harness/spec.md) | `implemented/partial`: siete skills de terceros, cuatro propios, registro/hash/licencias, validador, perfiles Claude y enlaces locales; [guía](../docs/architecture/AGENT_HARNESS.md). | Invocación real en cada cliente, medición de eficiencia, revisión/migración de cuatro skills legados y decisión sobre hook heredado de publicación. Instalar instrucciones no acredita ganancias de rendimiento. |
| 008 — Artefactos y datos | `partial`: almacén atómico y [ADR adoptado](../docs/decisions/ADR-OPEN-ARTIFACT-STORE.md); ZIP Colab reproducible. | Retención, respaldo/restauración y separación sostenible de artefactos grandes de Git. Spikes DVC/MLflow aplazados, no ejecutados. No borrar evidencia o reescribir historia para cerrar. |
| 009 — Observaciones del jurado | `pending`: [plan J-01–J-17](../docs/superpowers/plans/2026-10-31-jury-observations-remediation-plan.md). | Observación→corrección→prueba→artefacto; separar documentos, análisis y experimentos. Falta aceptación integral verificable. |
| [010 — Panel local](010-local-training-panel/spec.md) | `implemented` como monitor de lectura: HTTP/HTML sin CDN, hashes, `/api/runs`, loopback; [plan](010-local-training-panel/plan.md), [tareas](010-local-training-panel/tasks.md). | Mantener límites: no lanzamiento HTTP, exposición externa o aceptación científica inferida. No es plataforma de producción. |

## Conciliación técnica

1. **Persistencia:** las fachadas nativas delegan layout y escritura atómica;
   `ResumePlan` exige fingerprint y archivos verificados. No demuestra igualdad
   de trayectorias al restaurar optimizador, RNG y replay. Recuperar prefijos
   materializa memoria; falta medir el costo con horizonte completo.
2. **Adaptadores:** `NativeBackend` invoca los launchers HAPPO/MASAC/MATD3/MAAC
   existentes. No existen el `SimulatorPort` ni los cuatro archivos separados
   del plan original: registrar la alternativa o mantener esa deuda explícita.
3. **Reportes:** `application/evaluation/training_report.py` proyecta KPI
   finitos; no equivale a extraer todas las tablas/figuras ni a implementar
   `TrainingReportBuilder` y `FigureRenderer` del plan original.
4. **Colab:** [guía](../docs/architecture/ENTRENAMIENTO_MODULAR_COLAB.md), notebook
   y generador preservan instalación y argumentos originales. Pendientes:
   runtime real, wheels/CUDA, bloqueo Drive y desconexión/reanudación.
   `RUN_TRAINING=False` prepara sin lanzar. No exige compra, pero recursos
   gratuitos suficientes no están garantizados.
5. **Selección:** no existe mejor modelo final aceptado. Faltan regla explícita
   de selección, evaluación independiente y entrega reproducible sin fuga.

## Orden de continuación

- [x] Materializar SPEC-007 con contrato, plan y tareas de skills/harness.
- [ ] Materializar SPEC-001–006 y SPEC-008–009 con contratos y criterios actuales.
- [ ] Resolver procedencia/licencias y formalizar capacidades/roles locales sin secretos ni suscripciones requeridas.
- [ ] Validar Colab real y continuidad tras interrupción; registrar recursos e hiperparámetros efectivos.
- [ ] Completar reportes y evaluación independiente reproducible.
- [ ] Ejecutar campaña aprobada de horizonte completo, sensibilidad y multisemilla.
- [ ] Seleccionar/entregar modelo aceptado y promover evidencia hacia tesis/jurado.
- [ ] Ejecutar agregación integral; completar solo con todas las puertas exigidas acreditadas.

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
