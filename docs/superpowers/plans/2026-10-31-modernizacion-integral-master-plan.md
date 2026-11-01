# Modernización Integral Open Source Master Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Coordinar la modernización completa del proyecto MADRL–CityLearn mediante cinco planes independientes, verificables y ordenados por sus contratos.

**Architecture:** Migración brownfield por estrangulamiento hacia un monolito modular con dominio propio, puertos y adaptadores. La ejecución actual permanece operativa mientras cada responsabilidad se extrae detrás de interfaces compatibles.

**Tech Stack:** Python 3.9, pytest, Ruff, Pyright, Spec Kit, PowerShell, JSON/YAML, herramientas open source con ejecución local.

**Spec:** `docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md`

## Conciliación de estado — 2026-10-31

Ver [SPEC-000–012 y pendientes](../../../specs/STATUS.md), índice común de los
cinco planes, del monitor local y de los cortes de flujo integral (SPEC-011) e
higiene (SPEC-012). Hay cortes de código implementados,
pero la aceptación integral sigue parcial/bloqueada: licencias, campaña,
reanudación exacta, reportes, tesis/jurado y mejor modelo no están cerrados.
No marcar todos los planes completos ni reconstruir RED/commits históricos
desconocidos. La preparación Colab no demuestra ejecución en un runtime real.

## Plan integral por fases

Revisión 2026-10-31. Integra los cinco planes por corte con los SPEC-000–012
materializados en `specs/` y con la meta pedida por el usuario: un solo proyecto
modular, limpio y listo para el nuevo entrenamiento, desde la creación del
dataset hasta la entrega. Cada fase cierra solo con su puerta en verde; una
fase posterior no se inicia si consume un contrato aún abierto.

| Fase | SPEC | Entregable | Puerta de salida |
|---|---|---|---|
| 0 — Higiene | 012 | Decisión sobre el Stop hook; sin etiquetas de agentes en rutas, ramas, datos ni código; temporales fuera del índice; raíz limpia; manifiesto de limpieza | `python -m pytest -q tests/ops/test_repository_hygiene.py` y suite sin regresión |
| 1 — Procedencia | 001 | Licencias ausentes y copyleft resueltas; SBOM local | `scripts/quality/run_foundation_gates.ps1` en 0 |
| 2 — Puertos y adaptadores | 002, 003 | `SimulatorPort`, `ExperimentTrackerPort`, `adapters/citylearn/{simulator,objectives}.py`, seguimiento local, conformidad explícita de `NativeBackend`, prueba de imports | `tests/contract`, `tests/integration/test_citylearn_objective_adapter.py`, `run_orchestration_gates.ps1` |
| 3 — Flujo dataset → entrega | 011 | `tools/dataset/` consolidado por etapas; CLI con subcomandos; encadenamiento por hash; humo end-to-end sin red ni GPU | `python -m pytest -q tests/acceptance/test_pipeline_smoke.py` |
| 4 — Continuidad y artefactos | 004, 008 | Reanudación exacta en los cuatro algoritmos; retención; respaldo/restauración por hash | `tests/integration/test_resume_trajectory_parity.py`, `tests/integration/test_artifact_restore.py` |
| 5 — Campaña y selección | 005 | `configs/experiments/madrl_4x3_multiseed.yaml`, campaña aprobada, informe estadístico, regla de selección | 12 tratamientos válidos y `tests/acceptance/test_model_selection.py` |
| 6 — Tesis y jurado | 006, 009 | Registro de evidencia, §3.1.3, APA, J-01–J-17 trazadas | `run_thesis_agent_gates.ps1`, `run_jury_observations_gates.ps1` |
| 7 — Harness | 007 | Skills legados migrados o retirados; invocación real y eficiencia medida | `python tools/skills/validate_skills.py --check-discovery`, `tests/skills` |
| 8 — Aceptación integral | todos | `data/audits/modernization_acceptance_manifest.json` | `tests/acceptance/test_modernization_acceptance.py` (Task 5) |

Paralelismo permitido: las fases 0 y 1 son independientes; dentro de la fase 2,
los puertos se fijan antes de escribir adaptadores, y luego cada adaptador tiene
un único dueño. Las fases 3–8 son secuenciales. La fase 5 exige aprobación
explícita de cómputo; ninguna fase autoriza compras, servicios cerrados ni
cambios en `CityLearn/` o `external/` sin registro de contribución.

## Global Constraints

- Trabajar solo en `D:\MADRLCitytleranflexresdr`; nunca leer ni modificar `D:\madrl_lima`.
- Ejecutar `scripts/verify_project_context.ps1` antes de cada edición o operación Git.
- Preservar los 226 cambios detectados en la línea base hasta identificar su propiedad y finalidad.
- No modificar `CityLearn/` ni `external/` sin autorización explícita vigente y registro de contribución.
- Admitir únicamente licencias abiertas verificadas; licencia ausente bloquea integración.
- No añadir servicios de pago, suscripción o backend cerrado al flujo requerido.
- Mantener resultados históricos inmutables y asociados a su política original.
- Implementar mediante TDD y commits pequeños; ninguna puerta crítica admite `skip` o `xfail`.

## Review Focus

- Trabajo local sin confirmar propietario: inventariar y preservar; nunca limpiar automáticamente.
- Resultado antiguo sin versión de política: clasificar como legado no promovible, no inferir pesos.
- Dependencia sin SPDX o con licencia de contenido: rechazar integración de código.
- Configuración que mezcla tarifa y pesos: exigir objetos y hashes independientes.
- Prueba que solo construye mocks: no usarla como aceptación de integración CityLearn.

---

## Dependencias entre planes

```text
Plan 1: Fundación abierta y Spec Kit
       ↓
Plan 2: Dominio multiobjetivo y evaluación
       ↓
Plan 3: Orquestación modular y artefactos
       ↓
Plan 4: Evidencia de tesis, skills y agentes
       ↓
Plan 5: Levantamiento de observaciones del jurado
```

El Plan 2 puede comenzar después de la política de licencias y la constitución del Plan 1. El Plan 3 consume los contratos de dominio del Plan 2. El Plan 4 solo consume evidencia promovida por los Planes 2 y 3. El Plan 5 audita la coherencia de esa evidencia contra las observaciones del jurado y no permite cerrar como documental una carencia que requiere nueva experimentación.

### Task 1: Ejecutar Plan 1 — Fundación abierta

**Files:**
- Read: `docs/superpowers/plans/2026-10-31-foundation-open-source-spec-kit-plan.md`
- Produce: `.specify/`, `specs/000-*`, `specs/001-*`, política SPDX y puertas locales

**Interfaces:**
- Consumes: diseño aprobado y estado actual del repositorio.
- Produces: `OpenSourcePolicy`, inventario de procedencia y línea base revisable.

- [ ] **Step 1: Ejecutar todas las tareas del Plan 1 en orden**

- [ ] **Step 2: Verificar la puerta de fundación**

Run: `powershell -ExecutionPolicy Bypass -File scripts/quality/run_foundation_gates.ps1`

Expected: exit code `0`, sin dependencia requerida cerrada, sin secretos versionados y con manifiesto válido.

- [ ] **Step 3: Revisar y aprobar el corte antes del Plan 2**

### Task 2: Ejecutar Plan 2 — Dominio multiobjetivo

**Files:**
- Read: `docs/superpowers/plans/2026-10-31-multiobjective-domain-plan.md`
- Produce: contratos de objetivos, escenarios, Pareto y pruebas 4×3

**Interfaces:**
- Consumes: `OpenSourcePolicy` y constitución del Plan 1.
- Produces: `RewardVector`, `ObjectivePolicy`, `TariffPolicy`, `ConstraintPolicy`, `ScenarioDefinition` y evaluación multiobjetivo.

- [ ] **Step 1: Ejecutar todas las tareas del Plan 2 en orden**

- [ ] **Step 2: Verificar la puerta científica**

Run: `python -m pytest -q tests/unit/domain tests/contract/multiobjective tests/integration/test_citylearn_objective_adapter.py`

Expected: PASS; 12 combinaciones de algoritmo–escenario válidas y cero deriva de pesos activos.

- [ ] **Step 3: Revisar y aprobar el corte antes del Plan 3**

### Task 3: Ejecutar Plan 3 — Orquestación y artefactos

**Files:**
- Read: `docs/superpowers/plans/2026-10-31-orchestration-artifacts-plan.md`
- Produce: puertos de entrenamiento, manifiestos, almacén local y fachada compatible

**Interfaces:**
- Consumes: contratos del Plan 2.
- Produces: `ExperimentSpec`, `RunIdentity`, `EvidenceManifest`, `ArtifactStore` y módulos extraídos del script común.

- [ ] **Step 1: Ejecutar todas las tareas del Plan 3 en orden**

- [ ] **Step 2: Verificar paridad e integridad**

Run: `python -m pytest -q CityLearn/tests/test_internal_refactor_parity.py CityLearn/tests/test_citylearn_v3_training_artifacts.py CityLearn/tests/test_citylearn_v3_job_completion.py tests/contract/experiments`

Expected: PASS; fachadas existentes preservadas y artefactos con hashes verificables.

- [ ] **Step 3: Revisar y aprobar el corte antes del Plan 4**

### Task 4: Ejecutar Plan 4 — Tesis y agentes

**Files:**
- Read: `docs/superpowers/plans/2026-10-31-thesis-agents-plan.md`
- Produce: evidencia documental trazable, skills locales y conectores abiertos

**Interfaces:**
- Consumes: `EvidenceManifest` promovido y evaluación aceptada.
- Produces: §3.1.3 coherente, referencias APA verificadas, DOCX renderizado y registro de skills.

- [ ] **Step 1: Ejecutar todas las tareas del Plan 4 en orden**

- [ ] **Step 2: Verificar tesis, skills y ausencia de servicios cerrados**

Run: `powershell -ExecutionPolicy Bypass -File scripts/quality/run_thesis_agent_gates.ps1`

Expected: exit code `0`; pesos coherentes, bibliografía completa, skills válidos y flujo requerido completamente local.

### Task 5: Aceptación integral

**Precondition:** ejecutar `docs/superpowers/plans/2026-10-31-jury-observations-remediation-plan.md` y producir estados verificables J-01–J-17.

**Files:**
- Create: `data/audits/modernization_acceptance_manifest.json`
- Create: `docs/audits/INFORME_ACEPTACION_MODERNIZACION_OPEN_SOURCE.md`
- Test: `tests/acceptance/test_modernization_acceptance.py`

**Interfaces:**
- Consumes: manifiestos de los cinco planes, incluida la aceptación de observaciones del jurado.
- Produces: `ModernizationAcceptance` con estados `implemented`, `verified`, `partial`, `blocked` y `pending`.

- [ ] **Step 1: Escribir la prueba fallida de aceptación integral**

Assert: rechaza cualquier plan sin manifiesto, licencia abierta, hash o puerta verificada.

- [ ] **Step 2: Ejecutar la prueba y confirmar FAIL**

Run: `python -m pytest tests/acceptance/test_modernization_acceptance.py -v`

Expected: FAIL porque el agregador todavía no existe.

- [ ] **Step 3: Implementar el agregador de aceptación**

Create: `tools/ops/build_modernization_acceptance.py`

Signature: `build_acceptance(project_root: Path) -> dict[str, object]`

- [ ] **Step 4: Ejecutar todas las puertas locales**

Run: `powershell -ExecutionPolicy Bypass -File scripts/quality/run_all_quality_gates.ps1`

Expected: exit code `0`; el informe no convierte estados parciales en completados.

- [ ] **Step 5: Commit**

```powershell
git add tools/ops/build_modernization_acceptance.py tests/acceptance/test_modernization_acceptance.py data/audits/modernization_acceptance_manifest.json docs/audits/INFORME_ACEPTACION_MODERNIZACION_OPEN_SOURCE.md
git commit -m "chore: add integral modernization acceptance gate"
```

