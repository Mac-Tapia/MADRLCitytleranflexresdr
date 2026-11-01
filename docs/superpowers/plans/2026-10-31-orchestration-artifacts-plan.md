# Modular Orchestration and Reproducible Artifacts Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Descomponer gradualmente `citylearn_v3_training_common.py`, introducir identidad reproducible de ejecuciones y garantizar artefactos verificables sin romper launchers existentes.

**Architecture:** Nuevos casos de uso y puertos viven en `uc3m`; el script CityLearn conserva fachadas delegantes durante toda la migración. La extracción se hace por cohesión —identidad, rutas, completitud, persistencia, reportes y backends— con pruebas de paridad antes de cada movimiento.

**Tech Stack:** Python 3.9, dataclasses, pathlib, hashlib, JSON/CSV, pytest, PowerShell; MLflow/DVC solo tras puertas de necesidad y siempre locales.

**Spec:** `docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md`

**Spec Kit slices covered:** `SPEC-003`, `SPEC-004`, and `SPEC-008`.

## Conciliación de estado — 2026-10-31

Ver [SPEC-000–010 y pendientes](../../../specs/STATUS.md). Identidad, almacén,
layout, persistencia, runner y adaptador nativo compartido existen. Reportes
completos y continuidad optimizador/RNG/replay siguen pendientes. El manifiesto
real es `data/audits/modular_training_acceptance.json`, no
`orchestration_acceptance.json`. El ADR adopta almacén simple y aplaza spikes
DVC/MLflow; no los declara ejecutados. No confundir smokes con aceptación
científica ni acreditar RED/commits históricos desconocidos.

## Global Constraints

- No reescribir de una vez el archivo de más de 9 000 líneas.
- Cada función extraída mantiene una fachada importable desde su ubicación anterior durante una versión de transición.
- No cambiar nombres de directorios o semántica de reanudación sin migración y prueba de paridad.
- `return_code=0` no prueba completitud; se requieren episodios, KPI, checkpoints y artefactos.
- Escrituras de manifiestos son atómicas y verificables por hash.
- Google Drive/Colab puede permanecer como legado opcional, pero el camino requerido debe funcionar localmente.

## Review Focus

- Proceso termina con éxito pero faltan KPI o checkpoint: estado parcial.
- Reanudación desde directorio parecido pero de otra política: rechazar por fingerprint.
- JSON truncado durante interrupción: conservar último manifiesto válido.
- Artefacto cambia después de registrar hash: bloquear promoción.
- Ruta Drive o Colab ausente: ejecución local sigue siendo funcional.

---

### Task 1: Introducir identidad de ejecución y especificación experimental

**Files:**
- Create: `uc3m/domain/experiments.py`
- Test: `tests/unit/domain/test_experiments.py`

**Interfaces:**
- Consumes: `ScenarioDefinition` del Plan 2.
- Produces: `ExperimentSpec`, `RunIdentity`, `RunStatus`.

- [ ] **Step 1: Escribir pruebas fallidas de identidad**

Assertions: mismo spec produce mismo fingerprint; semilla, commit, dataset o política distinta produce otro; timestamps no participan en identidad científica.

- [ ] **Step 2: Implementar interfaces**

```python
class RunStatus(str, Enum):
    PLANNED = "planned"
    RUNNING = "running"
    PARTIAL = "partial"
    VERIFIED = "verified"
    BLOCKED = "blocked"

@dataclass(frozen=True)
class ExperimentSpec:
    algorithm: str
    scenario: ScenarioDefinition
    seed: int
    dataset_sha256: str
    code_commit: str
    submodule_commits: Mapping[str, str]
    target_episodes: int
    def fingerprint(self) -> str: ...

@dataclass(frozen=True)
class RunIdentity:
    run_id: str
    experiment_fingerprint: str
```

- [ ] **Step 3: Ejecutar tests**

Expected: PASS y serialización estable.

- [ ] **Step 4: Commit**

```powershell
git add uc3m/domain/experiments.py tests/unit/domain/test_experiments.py
git commit -m "feat: add reproducible experiment identity"
```

### Task 2: Definir manifiesto de evidencia y referencias de artefactos

**Files:**
- Create: `uc3m/domain/evidence.py`
- Test: `tests/unit/domain/test_evidence.py`

**Interfaces:**
- Consumes: `RunIdentity`.
- Produces: `ArtifactRef`, `EvidenceManifest`, `verify_artifact(path, expected_sha256) -> bool`.

- [ ] **Step 1: Escribir pruebas fallidas**

Assertions: ruta relativa normalizada, SHA-256, tamaño, tipo, productor; cambio de bytes invalida; artefacto faltante bloquea `VERIFIED`.

- [ ] **Step 2: Implementar dataclasses y verificación**

- [ ] **Step 3: Ejecutar pruebas**

Expected: PASS; no se aceptan rutas fuera de la raíz del run.

- [ ] **Step 4: Commit**

```powershell
git add uc3m/domain/evidence.py tests/unit/domain/test_evidence.py
git commit -m "feat: add hashed evidence manifests"
```

### Task 3: Crear puerto y almacén local atómico

**Files:**
- Create: `uc3m/ports/__init__.py`
- Create: `uc3m/ports/artifact_store.py`
- Create: `uc3m/adapters/local_artifacts.py`
- Test: `tests/unit/adapters/test_local_artifact_store.py`

**Interfaces:**
- Produces: protocolo `ArtifactStore` y `LocalArtifactStore`.

- [ ] **Step 1: Escribir pruebas de escritura atómica y fallo simulado**

Assertions: usa temporal en mismo filesystem, reemplazo atómico, último JSON válido permanece tras excepción.

- [ ] **Step 2: Implementar protocolo**

```python
class ArtifactStore(Protocol):
    def write_bytes(self, relative_path: str, payload: bytes) -> ArtifactRef: ...
    def write_json(self, relative_path: str, payload: Mapping[str, object]) -> ArtifactRef: ...
    def verify(self, artifact: ArtifactRef) -> bool: ...
```

- [ ] **Step 3: Implementar `LocalArtifactStore`**

- [ ] **Step 4: Ejecutar tests**

- [ ] **Step 5: Commit**

```powershell
git add uc3m/ports uc3m/adapters/local_artifacts.py tests/unit/adapters/test_local_artifact_store.py
git commit -m "feat: add atomic local artifact store"
```

### Task 4: Extraer rutas y layout de jobs

**Files:**
- Create: `uc3m/application/training/__init__.py`
- Create: `uc3m/application/training/layout.py`
- Modify: `CityLearn/scripts/citylearn_v3_training_common.py:724`
- Test: `CityLearn/tests/test_internal_refactor_parity.py`
- Test: `tests/unit/application/training/test_layout.py`

**Interfaces:**
- Produces: `normalize_algorithm_dir`, `normalize_scenario_dir`, `job_run_relative_parts`, `resolve_job_run_dir`, `ensure_artifact_layout`.

- [ ] **Step 1: Añadir casos de paridad para seed 0 y seed no cero**

- [ ] **Step 2: Mover lógica pura a `layout.py`**

El script anterior reexporta o delega; no duplicar implementaciones.

- [ ] **Step 3: Ejecutar paridad**

Run: `python -m pytest -q tests/unit/application/training/test_layout.py CityLearn/tests/test_internal_refactor_parity.py`

- [ ] **Step 4: Commit separado en CityLearn y superproyecto**

### Task 5: Extraer persistencia JSON/CSV y heartbeat

**Files:**
- Create: `uc3m/application/training/persistence.py`
- Modify: `CityLearn/scripts/citylearn_v3_training_common.py:876`
- Test: `tests/unit/application/training/test_persistence.py`
- Test: `CityLearn/tests/test_incremental_resume_persistence.py`

**Interfaces:**
- Produces: `write_json_atomic`, `write_csv_atomic`, `append_csv_stable_schema`, `ProgressHeartbeat`.

- [ ] **Step 1: Escribir pruebas de interrupción, schema drift y fsync opcional**

- [ ] **Step 2: Implementar módulo sin dependencias Colab**

- [ ] **Step 3: Delegar desde fachadas existentes**

- [ ] **Step 4: Ejecutar pruebas**

Expected: PASS en Windows local; MyDrive queda adaptador opcional.

- [ ] **Step 5: Commit**

### Task 6: Extraer evaluación de completitud y reanudación

**Files:**
- Create: `uc3m/application/training/completion.py`
- Create: `uc3m/application/training/resume.py`
- Modify: `CityLearn/scripts/citylearn_v3_training_common.py:1483`
- Test: `tests/unit/application/training/test_completion.py`
- Test: `tests/unit/application/training/test_resume.py`
- Test: `CityLearn/tests/test_citylearn_v3_job_completion.py`

**Interfaces:**
- Produces: `CompletionEvidence`, `CompletionDecision`, `ResumePlan`.

- [ ] **Step 1: Escribir tabla de casos fallidos**

Casos: exit 0 sin KPI; episodios completos sin checkpoint; checkpoint sin resultados; HAPPO tail recuperable; fingerprint distinto; artefacto corrupto.

- [ ] **Step 2: Implementar evaluador puro**

```python
def evaluate_completion(
    spec: ExperimentSpec,
    manifest: EvidenceManifest | None,
    discovered: Mapping[str, object],
) -> CompletionDecision: ...
```

- [ ] **Step 3: Implementar plan de reanudación**

Nunca reanudar desde run con fingerprint distinto.

- [ ] **Step 4: Delegar desde funciones actuales**

- [ ] **Step 5: Ejecutar suite de completitud y persistencia**

Expected: PASS; ningún estado parcial se cuenta como completo.

- [ ] **Step 6: Commit**

### Task 7: Extraer reportes, KPI y figuras del núcleo de entrenamiento

**Files:**
- Create: `uc3m/application/evaluation/training_report.py`
- Create: `uc3m/application/evaluation/tables.py`
- Create: `uc3m/adapters/matplotlib_figures.py`
- Modify: `CityLearn/scripts/citylearn_v3_training_common.py:5605`
- Test: `tests/unit/application/evaluation/test_training_report.py`
- Test: `CityLearn/tests/test_citylearn_v3_training_artifacts.py`

**Interfaces:**
- Produces: `TrainingReportBuilder`, tablas puras y `FigureRenderer`.

- [ ] **Step 1: Congelar fixtures dorados pequeños de reportes actuales**

No versionar artefactos masivos; usar datos mínimos deterministas.

- [ ] **Step 2: Extraer transformaciones puras**

- [ ] **Step 3: Separar render de figuras mediante adaptador**

- [ ] **Step 4: Ejecutar comparación estructural**

Expected: mismas claves, unidades y filas; nuevas columnas de fingerprints permitidas.

- [ ] **Step 5: Commit**

### Task 8: Introducir puertos de simulador y backend de aprendizaje

**Files:**
- Create: `uc3m/ports/simulator.py`
- Create: `uc3m/ports/learner.py`
- Create: `uc3m/adapters/citylearn/simulator.py`
- Create: `uc3m/adapters/algorithms/{happo,masac,matd3,maac}.py`
- Modify: `CityLearn/scripts/citylearn_v3_training_common.py:7569`
- Test: `tests/contract/training/test_backend_contract.py`

**Interfaces:**
- Produces: `SimulatorPort`, `LearnerPort`, `TrainingResult`.

- [ ] **Step 1: Definir pruebas contractuales comunes**

Assertions: reset/step, seed, checkpoint save/load, métricas finitas, cierre y descripción de capacidades.

- [ ] **Step 2: Implementar puertos sin importar backends**

- [ ] **Step 3: Envolver las clases actuales en adaptadores**

No copiar código de los submódulos; delegar.

- [ ] **Step 4: Ejecutar contrato para los cuatro backends disponibles**

Dependencia ausente = `blocked` explícito; no PASS por skip.

- [ ] **Step 5: Commit por adaptador**

### Task 9: Añadir `ExperimentRunner` y fachada compatible

**Files:**
- Create: `uc3m/application/training/runner.py`
- Modify: `uc3m/train.py`
- Modify: `CityLearn/scripts/citylearn_v3_training_common.py`
- Test: `tests/integration/test_experiment_runner.py`

**Interfaces:**
- Consumes: ports, `ExperimentSpec`, `ArtifactStore`.
- Produces: `ExperimentRunner.run(spec) -> EvidenceManifest`.

- [ ] **Step 1: Escribir integración con simulador mínimo real y learner determinista**

No usar mocks para la escritura/lectura de artefactos.

- [ ] **Step 2: Implementar runner con estados transaccionales**

Orden: validar → marcar running → ejecutar → persistir → verificar → promover o partial/blocked.

- [ ] **Step 3: Conectar CLI preservando flags existentes**

- [ ] **Step 4: Ejecutar integración y paridad**

- [ ] **Step 5: Commit**

### Task 10: Evaluar almacenamiento grande y tracking local

**Files:**
- Create: `docs/decisions/ADR-OPEN-ARTIFACT-STORE.md`
- Create: `experiments/spikes/local_tracking/README.md`
- Test: `tests/acceptance/test_local_tracking_offline.py`

**Interfaces:**
- Produces: decisión entre almacén simple, DVC local y MLflow local; no instala por defecto.

- [ ] **Step 1: Medir requisitos reales**

Registrar tamaño, número, frecuencia, mutabilidad y restauración de artifacts; excluir `.git` y entornos.

- [ ] **Step 2: Probar en spike desechable tres alternativas**

1. `LocalArtifactStore` puro.
2. DVC con remoto de filesystem local.
3. MLflow con SQLite y artifacts locales.

- [ ] **Step 3: Verificar operación sin red y restauración por hash**

- [ ] **Step 4: Escribir ADR con una sola elección**

YAGNI: si el almacén puro cubre el proyecto, no añadir DVC/MLflow.

- [ ] **Step 5: Commit solo ADR y pruebas de la opción elegida**

### Task 11: Puerta integral de orquestación

**Files:**
- Create: `scripts/quality/run_orchestration_gates.ps1`
- Create: `data/audits/orchestration_acceptance.json`
- Modify: `.github/workflows/ci.yml`

**Interfaces:**
- Produces: aceptación de paridad, completitud, persistencia, contratos y artefactos.

- [ ] **Step 1: Implementar script local**

- [ ] **Step 2: Ejecutar suite enfocada**

Run: `powershell -ExecutionPolicy Bypass -File scripts/quality/run_orchestration_gates.ps1`

Expected: PASS; reporte con funciones pendientes de extraer, sin declararlas completadas.

- [ ] **Step 3: Ejecutar smoke real HAPPO E1 y contrato 4×3**

Expected: manifiestos verificables; el smoke no sustituye entrenamiento final.

- [ ] **Step 4: Commit**

```powershell
git add scripts/quality/run_orchestration_gates.ps1 data/audits/orchestration_acceptance.json .github/workflows/ci.yml
git commit -m "ci: gate modular training orchestration"
```

