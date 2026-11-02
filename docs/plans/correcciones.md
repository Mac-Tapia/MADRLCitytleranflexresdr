# Plan de remediación post-auditoría MADRL–CityLearn

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Resolver los 16 hallazgos de la auditoría independiente del 2026-10-31 en orden de dependencia, desde higiene del repositorio hasta campaña experimental completa y entrega del mejor modelo.

**Architecture:** Enfoque secuencial estricto — cada fase gate la siguiente. El monolito modular `uc3m/` se extiende sin reescribir CityLearn. Los launchers nativos en `CityLearn/scripts/` reciben extensiones de checkpointing en sus propios archivos sin romper la interfaz actual.

**Tech Stack:** Python 3.9, PyTorch/TensorFlow (según algoritmo), CityLearn fork, pytest, Git, PowerShell/Bash.

**Spec:** `docs/design/modernizacion.md`

## Global Constraints

- Entorno: `.venv39-citylearn-v3` exclusivamente.
- No SaaS, no pago, no suscripciones. Local-first.
- No modificar `D:\madrl_lima` ni mezclar datos/historial.
- Antes de toda operación Git: `scripts/verify_project_context.ps1`.
- `CityLearn/` es fork propio (Mac-Tapia/CityLearn.git) — modificable como contribución de tesis.
- Pushear submodulo CityLearn ANTES del repo padre.
- Constitución: `.specify/memory/constitution.md` — 10 principios no negociables.
- Tests sin `skip` ni `xfail` como aceptación.
- `scientific_acceptance` solo se promueve a `true` tras campaña completa verificada.

## Review Focus

1. **Resume con optimizador reinicializado:** un run pausado y resumido silenciosamente pierde momentum del optimizador; el test de paridad resume-vs-continuo (Tarea 3) lo detecta.
2. **Pesos hardcodeados fuera del YAML canónico:** cualquier archivo que defina `0.60/0.15/0.25` independientemente de `configs/objective_policies.yaml` es una fuente de drift; el test de drift (Tarea 2) debe fallar si se encuentra alguno.
3. **Stop hook auto-publica trabajo no revisado:** un Claude concurrente puede pushear archivos arbitrarios; la desactivación (Tarea 1) es prerrequisito para todo trabajo seguro.
4. **Campaña de 8 timesteps no es evidencia científica:** los smokes existentes verifican integración operativa; la campaña completa (Tarea 5) necesita horizonte completo (8760 pasos).
5. **Manifest `orchestration_acceptance.json` no existe:** citarlo como evidencia es un error; la Tarea 5 lo crea solo cuando la campaña completa termina.

---

### Tarea 1: Higiene y seguridad del repositorio

**Hallazgos:** H-06 (Stop hook), H-07 (.codex_tmp), H-08 (browser profile), H-16 (530 MB tracked)

**Files:**
- Modify: `.claude/settings.json` — eliminar hook Stop
- Modify: `.gitignore` — añadir `.codex_tmp/`, `tools/skills/notebooklm-mcp/data/browser_state/`
- Delete from tracking: `.codex_tmp/` (1,213 archivos), `tools/skills/notebooklm-mcp/data/browser_state/` (19 archivos)
- No test file (operaciones Git, no código)

**Interfaces:**
- Consumes: nada
- Produces: repositorio seguro para trabajo concurrente; `.gitignore` actualizado

- [ ] **Step 1: Verificar contexto del proyecto**

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
```
Expected: `[OK] Project context verified`

- [ ] **Step 2: Desactivar Stop hook en `.claude/settings.json`**

Reemplazar el contenido con `{}` (objeto vacío). No eliminar el archivo — solo vaciar hooks.

- [ ] **Step 3: Añadir exclusiones a `.gitignore`**

Añadir al final:
```
# Temporales de agentes y perfiles de navegador
.codex_tmp/
tools/skills/notebooklm-mcp/data/browser_state/
tools/skills/google-drive-mcp/
```

- [ ] **Step 4: Destrackear archivos temporales sin eliminarlos del disco**

```bash
git rm -r --cached .codex_tmp/
git rm -r --cached tools/skills/notebooklm-mcp/data/browser_state/
git rm --cached .git_commit_msg.tmp
```

- [ ] **Step 5: Verificar que no se eliminaron archivos del disco**

```powershell
Test-Path .codex_tmp  # debe ser True
Test-Path tools/skills/notebooklm-mcp/data/browser_state  # debe ser True
```

- [ ] **Step 6: Commit**

```bash
git add .claude/settings.json .gitignore
git commit -m "chore: disable auto-publish hook, untrack temp files and browser profiles

Addresses audit findings H-06, H-07, H-08. Files preserved locally
but excluded from git tracking to prevent credential leakage and
unreviewed publishing."
```

---

### Tarea 2: Consolidar fuente única de pesos (SPEC-002)

**Hallazgo:** H-05 (17+ archivos con pesos hardcodeados)

**Files:**
- Modify: `CityLearn/citylearn/scenario_manager.py:67-103` — leer de catálogo en vez de hardcodear
- Modify: `tools/training/verify_training_optimization.py:132-134` — importar de canónico
- Modify: `tools/colab/generate_colab_notebook.py:327-346` — importar de canónico
- Modify: `tools/colab/test_notebook_cells.py:321-323` — importar de canónico
- Create: `tests/contract/test_weight_single_source.py`

**Interfaces:**
- Consumes: `configs/objective_policies.yaml`, `uc3m/domain/objectives.py:canonical_objective_policies()`
- Produces: test contractual que falla si algún archivo Python/YAML fuera de las fuentes canónicas define pesos independientemente

- [ ] **Step 1: Escribir test que escanea el repositorio por pesos hardcodeados**

```python
# tests/contract/test_weight_single_source.py
import re
from pathlib import Path

CANONICAL_SOURCES = {
    'uc3m/domain/objectives.py',
    'configs/objective_policies.yaml',
}
WEIGHT_PATTERN = re.compile(r'0\.60.*0\.15.*0\.25|0\.25.*0\.60.*0\.15|0\.15.*0\.25.*0\.60')
EXCLUDED_DIRS = {'__pycache__', '.venv', '.git', 'node_modules', '.codex_tmp', 'outputs'}
EXCLUDED_SUFFIXES = {'.pyc', '.pt', '.pkl', '.zip', '.pdf', '.docx', '.xlsx', '.png', '.jpg'}

def test_no_hardcoded_weights_outside_canonical():
    root = Path(__file__).resolve().parents[2]
    violations = []
    for path in root.rglob('*'):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.suffix in EXCLUDED_SUFFIXES or not path.is_file():
            continue
        relative = path.relative_to(root).as_posix()
        if relative in CANONICAL_SOURCES:
            continue
        if '/fixtures/' in relative or '/test_' in path.name:
            continue
        try:
            text = path.read_text(encoding='utf-8', errors='ignore')
        except Exception:
            continue
        if WEIGHT_PATTERN.search(text):
            violations.append(relative)
    assert not violations, f"Hardcoded weights found in: {violations}"
```

- [ ] **Step 2: Ejecutar test para verificar que falla**

```bash
python -B -m pytest tests/contract/test_weight_single_source.py -v
```
Expected: FAIL con lista de ~17 archivos

- [ ] **Step 3: Modificar `CityLearn/citylearn/scenario_manager.py` para leer del catálogo**

En las líneas 67-103 donde están hardcodeados los pesos E1/E2/E3, reemplazar con lectura del YAML via variable de entorno `UC3M_SCENARIO_CATALOG` (ya inyectada por `NativeBackend.execute()`). Fallback a los valores actuales si la variable no está definida para compatibilidad.

- [ ] **Step 4: Reemplazar pesos hardcodeados en scripts de tools/**

En `tools/training/verify_training_optimization.py:132-134`, `tools/colab/generate_colab_notebook.py:327-346` y `tools/colab/test_notebook_cells.py:321-323`: importar `canonical_objective_policies()` o leer del YAML en vez de definir literales.

- [ ] **Step 5: Marcar documentación como referencia, no fuente activa**

En archivos `.md` que contienen los pesos (README.md, docs/estrategia.md, etc.), añadir comentario HTML `<!-- Fuente canónica: configs/objective_policies.yaml -->` junto a cada mención. Los documentos no son runtime; la nota previene drift futuro.

- [ ] **Step 6: Ejecutar test para verificar que pasa**

```bash
python -B -m pytest tests/contract/test_weight_single_source.py -v
```
Expected: PASS

- [ ] **Step 7: Ejecutar suite completa para verificar no-regresión**

```bash
python -B -m pytest tests/ -q --no-header
```
Expected: 307+ passed, 0 failed

- [ ] **Step 8: Commit (CityLearn primero)**

```bash
git -C CityLearn add citylearn/scenario_manager.py
git -C CityLearn commit -m "fix: read objective weights from catalog instead of hardcoding"
git -C CityLearn push mac-tapia HEAD
git add CityLearn tools/ tests/contract/test_weight_single_source.py README.md docs/
git commit -m "fix(spec-002): consolidate weights to single canonical source

17+ files hardcoded objective weights independently. Runtime paths
now read from configs/objective_policies.yaml via UC3M_SCENARIO_CATALOG.
Contract test scans repo for violations."
```

---

### Tarea 3: Persistencia de optimizador, RNG y replay (SPEC-003/004)

**Hallazgo:** H-02 (continuidad optimizador/RNG/replay no verificada)

**Files:**
- Create: `CityLearn/scripts/checkpoint_state.py` — utilidades de guardado/restauración
- Modify: `CityLearn/scripts/train_citylearn_v3_happo.py:349` — guardar estado completo
- Modify: `CityLearn/scripts/train_citylearn_v3_masac.py:404-406` — guardar estado completo
- Modify: `CityLearn/scripts/train_citylearn_v3_matd3.py` — guardar replay buffer
- Modify: `CityLearn/scripts/train_citylearn_v3_maac.py:104` — guardar estado completo
- Modify: `uc3m/application/training/resume.py` — verificar estado del optimizador
- Create: `tests/contract/test_resume_state_parity.py`

**Interfaces:**
- Consumes: `LearnerPort`, `NativeBackend`, los 4 launchers
- Produces: `save_training_state(path: Path, optimizers: list, rng_states: dict, replay=None) -> None`, `load_training_state(path: Path) -> dict`; `ResumePlan` extendido con verificación de `state.pt`

- [ ] **Step 1: Escribir test de paridad save/load del estado de entrenamiento**

```python
# tests/contract/test_resume_state_parity.py
import torch
import numpy as np
from pathlib import Path

def test_checkpoint_preserves_optimizer_rng_state(tmp_path):
    from CityLearn.scripts.checkpoint_state import save_training_state, load_training_state

    model = torch.nn.Linear(4, 2)
    optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)
    loss = model(torch.randn(1, 4)).sum()
    loss.backward()
    optimizer.step()

    torch_rng = torch.random.get_rng_state()
    np_rng = np.random.get_state()
    optim_state = optimizer.state_dict()

    save_training_state(tmp_path / 'state.pt', [optimizer], {
        'torch': torch_rng, 'numpy': np_rng,
    })
    loaded = load_training_state(tmp_path / 'state.pt')

    assert torch.equal(loaded['rng_states']['torch'], torch_rng)
    assert loaded['rng_states']['numpy'][1].tolist() == np_rng[1].tolist()
    for key in optim_state['state']:
        for k, v in optim_state['state'][key].items():
            if isinstance(v, torch.Tensor):
                assert torch.equal(loaded['optimizer_states'][0]['state'][key][k], v)
```

- [ ] **Step 2: Ejecutar test para verificar que falla**

```bash
python -B -m pytest tests/contract/test_resume_state_parity.py -v
```
Expected: FAIL con `ModuleNotFoundError: checkpoint_state`

- [ ] **Step 3: Implementar `CityLearn/scripts/checkpoint_state.py`**

Dos funciones: `save_training_state(path, optimizers, rng_states, replay=None)` y `load_training_state(path) -> dict`. Usa `torch.save` con dict `{'optimizer_states': [opt.state_dict() for opt in optimizers], 'rng_states': rng_states, 'replay': replay}`. Para replay, acepta `None` (on-policy) o un serializable.

- [ ] **Step 4: Ejecutar test para verificar que pasa**

```bash
python -B -m pytest tests/contract/test_resume_state_parity.py -v
```
Expected: PASS

- [ ] **Step 5: Integrar en los 4 launchers**

En cada launcher, junto al checkpoint de modelo existente, invocar `save_training_state`:
- **HAPPO** (línea 349): `runner.policy` optimizers, `torch.random.get_rng_state()` + `np.random.get_state()`. Sin replay (on-policy).
- **MASAC** (línea 406): `learner.policy_optimiser`, `learner.optimizer`, `learner.optimizer_2`, `learner.alpha_optimizer`; ambos RNG; replay buffer snapshot si disponible.
- **MATD3**: `policy.actor_optimizer`, `policy.critic_optimizer` por agente; numpy+TF random state; replay buffer.
- **MAAC** (línea 104): `model.critic_optimizer`, `agent.policy_optimizer`; ambos RNG; replay data.

Al restaurar en resume, cargar `state.pt` y restaurar estados antes de continuar entrenamiento.

- [ ] **Step 6: Extender `ResumePlan` para verificar estado completo**

En `uc3m/application/training/resume.py:plan_resume()`, antes de retornar `allowed=True`, verificar que al menos un artefacto tenga `kind='training_state'` o nombre `state.pt`. Si no existe, retornar `ResumePlan(False, 0, (), 'optimizer_state_missing')`.

- [ ] **Step 7: Ejecutar suite completa**

```bash
python -B -m pytest tests/ -q --no-header
```
Expected: 307+ passed (smokes de 8 pasos no usan resume, no se rompen)

- [ ] **Step 8: Commit (CityLearn primero, luego repo padre)**

```bash
git -C CityLearn add scripts/checkpoint_state.py scripts/train_citylearn_v3_*.py
git -C CityLearn commit -m "feat: save optimizer, RNG and replay state on checkpoint"
git -C CityLearn push mac-tapia HEAD
git add CityLearn uc3m/application/training/resume.py tests/contract/test_resume_state_parity.py
git commit -m "feat(spec-003): verify optimizer/RNG/replay continuity on resume

Extends ResumePlan to require training state artifact.
Contract test proves save/load round-trip preserves full state."
```

---

### Tarea 4: Materializar specs y completar orquestación (SPEC-001–009)

**Hallazgos:** H-10 (8 specs sin carpeta), H-09 (SimulatorPort), H-11 (training_report trivial), H-14 (sin acceptance tests), H-15 (adaptador CityLearn)

**Files:**
- Create: `specs/{001..006,008,009}-*/spec.md`, `plan.md`, `tasks.md` (8 carpetas × 3 archivos)
- Create: `uc3m/ports/simulator.py`
- Create: `uc3m/adapters/citylearn/objectives.py`
- Modify: `uc3m/application/evaluation/training_report.py`
- Create: `tests/acceptance/test_acceptance_gates.py`
- Modify: `tests/contract/test_spec_kit_consistency.py`
- Create: `docs/decisions/simulator.md`

**Interfaces:**
- Consumes: diseño aprobado, planes existentes en `docs/plans/`
- Produces: `SimulatorPort(Protocol)` con `reset() -> dict`, `step(actions) -> tuple`; `TrainingReportBuilder.build(evidence_root: Path) -> dict` con KPIs estructurados; acceptance gates por etapa constitucional

- [ ] **Step 1: Escribir test de consistencia extendido**

Extender `tests/contract/test_spec_kit_consistency.py` para verificar que carpetas SPEC-000 a SPEC-010 existen con `spec.md`, `plan.md`, `tasks.md`.

- [ ] **Step 2: Ejecutar test para verificar que falla**

```bash
python -B -m pytest tests/contract/test_spec_kit_consistency.py -v
```
Expected: FAIL (8 carpetas faltantes)

- [ ] **Step 3: Crear las 8 carpetas spec con contenido extraído del diseño**

Para cada SPEC (001–006, 008, 009): `specs/NNN-nombre/spec.md` con requisitos FR-NNN del diseño §9, criterios de aceptación y dependencias; `plan.md` enlazando al plan existente; `tasks.md` con checkboxes y estado de `specs/STATUS.md`.

- [ ] **Step 4: Implementar `SimulatorPort` y ADR de desviación**

```python
# uc3m/ports/simulator.py
from typing import Any, Dict, Protocol
import numpy as np

class SimulatorPort(Protocol):
    def reset(self) -> Dict[str, np.ndarray]: ...
    def step(self, actions: Dict[str, np.ndarray]) -> tuple: ...
    @property
    def observation_space(self) -> Any: ...
    @property
    def action_space(self) -> Any: ...
```

ADR en `docs/decisions/simulator.md`: la integración actual vía subprocess en `NativeBackend` se mantiene; puerto in-process diferido hasta descomposición de SPEC-003.

- [ ] **Step 5: Implementar adaptador CityLearn de objetivos**

`uc3m/adapters/citylearn/objectives.py`: lee `UC3M_SCENARIO_CATALOG`, proyecta `ObjectivePolicy` hacia `reward_weights` que CityLearn consume. Crea directorio `uc3m/adapters/citylearn/` con `__init__.py`.

- [ ] **Step 6: Extender `training_report.py` con `TrainingReportBuilder`**

Añadir clase que extraiga: KPIs por métrica, tabla resumen por algoritmo/escenario, episodios completados. Mantener `scientific_acceptance: False` hasta campaña completa.

- [ ] **Step 7: Crear tests de aceptación**

`tests/acceptance/test_acceptance_gates.py`: un test por gate constitucional (dataset, validación, escenarios, configuración, smoke, artefactos, KPI). Cada test verifica que el manifiesto correspondiente existe y es válido.

- [ ] **Step 8: Ejecutar suite completa**

```bash
python -B -m pytest tests/ -q --no-header
```
Expected: 307+ passed, nuevos tests pasan

- [ ] **Step 9: Commit**

```bash
git add specs/ uc3m/ports/simulator.py uc3m/adapters/citylearn/
git add uc3m/application/evaluation/training_report.py
git add tests/acceptance/ tests/contract/test_spec_kit_consistency.py
git add docs/decisions/simulator.md
git commit -m "feat: materialize all SPEC folders, add SimulatorPort and acceptance gates

All 11 SPECs now have spec.md/plan.md/tasks.md.
SimulatorPort defined as deferred Protocol with ADR.
TrainingReportBuilder extracts structured metrics.
Acceptance gates cover the constitutional flow."
```

---

### Tarea 5: Campaña experimental completa (SPEC-005)

**Hallazgo:** H-01 (sin campaña modular completa)

**Files:**
- Create: `configs/experiments/full_campaign_4x3x3.yaml`
- Create: `scripts/training/launch_full_campaign.py`
- Create: `tests/contract/test_campaign_manifest.py`
- Produce: `data/audits/orchestration_acceptance.json` (generado al completar)

**Interfaces:**
- Consumes: `ExperimentRunner`, `NativeBackend`, `configs/scenarios.yaml`, `configs/objective_policies.yaml`
- Produces: 36 directorios en `outputs/modular_training/`, `orchestration_acceptance.json` con `scientific_acceptance: true` solo si todas las puertas pasan

- [ ] **Step 1: Definir configuración de campaña**

```yaml
# configs/experiments/full_campaign_4x3x3.yaml
campaign_id: full_4x3x3_v1
algorithms: [HAPPO, MASAC, MATD3, MAAC]
scenarios: [E1, E2, E3]
seeds: [42, 123, 456]
episodes: 50
episode_time_steps: 8760
schema: data/citylearn/iquitos/schema.json
output_root: outputs/modular_training
```

- [ ] **Step 2: Escribir test de manifiesto de campaña**

```python
# tests/contract/test_campaign_manifest.py
import itertools, yaml
from pathlib import Path

def test_campaign_config_covers_4x3x3():
    config = yaml.safe_load(Path('configs/experiments/full_campaign_4x3x3.yaml').read_text())
    treatments = list(itertools.product(config['algorithms'], config['scenarios'], config['seeds']))
    assert len(treatments) == 36

def test_orchestration_acceptance_requires_all_treatments():
    """No se genera orchestration_acceptance.json sin 36 tratamientos verificados."""
    ...
```

- [ ] **Step 3: Implementar orquestador de campaña**

`scripts/training/launch_full_campaign.py`: itera 36 tratamientos con `ExperimentRunner` + `NativeBackend`, genera `orchestration_acceptance.json` solo si todos son `VERIFIED`, KPIs finitos y hashes verifican.

- [ ] **Step 4: Ejecutar test de configuración**

```bash
python -B -m pytest tests/contract/test_campaign_manifest.py::test_campaign_config_covers_4x3x3 -v
```
Expected: PASS

- [ ] **Step 5: Ejecutar campaña**

```bash
python scripts/training/launch_full_campaign.py --config configs/experiments/full_campaign_4x3x3.yaml --execute
```

**NOTA:** Esta ejecución toma días/semanas. Validar flujo con `--algorithms HAPPO --seeds 42 --episodes 2` primero. En Colab con `RUN_TRAINING=True`.

- [ ] **Step 6: Verificar evidencia**

```bash
python -B -m pytest tests/contract/test_campaign_manifest.py -v
```
Expected: PASS cuando 36 tratamientos completados

- [ ] **Step 7: Commit**

```bash
git add configs/experiments/ scripts/training/ tests/contract/test_campaign_manifest.py
git add data/audits/orchestration_acceptance.json
git commit -m "feat(spec-005): full 4x3x3 experimental campaign with acceptance gate"
```

---

### Tarea 6: Evaluación científica y selección del mejor modelo (SPEC-005)

**Hallazgo:** H-03 (sin mejor modelo seleccionado)

**Files:**
- Create: `uc3m/application/evaluation/scientific_evaluation.py`
- Create: `uc3m/application/evaluation/model_selection.py`
- Create: `uc3m/application/evaluation/baselines.py`
- Create: `tests/unit/application/test_scientific_evaluation.py`
- Create: `tests/unit/application/test_model_selection.py`
- Produce: `data/audits/scientific_evaluation.json`, `data/audits/best_model_selection.json`

**Interfaces:**
- Consumes: 36 manifiestos de Tarea 5, `uc3m/domain/pareto.py`
- Produces: `evaluate_campaign(evidence_root: Path) -> dict` con KPIs independientes, Pareto, IQM+CI; `select_best_model(evaluation: dict) -> dict` con algoritmo ganador, justificación, paquete hash

- [ ] **Step 1: Escribir tests de evaluación**

```python
# tests/unit/application/test_scientific_evaluation.py
def test_report_requires_all_kpi_dimensions():
    """Costo, CO2, pico, rampas, factor carga, PV, EV/BESS requeridos."""
    ...
def test_multiseed_statistics_require_minimum_3_seeds():
    ...
def test_pareto_front_computed_across_algorithms():
    ...
```

- [ ] **Step 2: Escribir tests de selección**

```python
# tests/unit/application/test_model_selection.py
def test_selection_rule_deterministic():
    ...
def test_selected_model_has_delivery_package():
    ...
def test_selection_rejects_incomplete_campaign():
    ...
```

- [ ] **Step 3: Ejecutar tests para verificar que fallan**

```bash
python -B -m pytest tests/unit/application/test_scientific_evaluation.py tests/unit/application/test_model_selection.py -v
```
Expected: FAIL

- [ ] **Step 4: Implementar `scientific_evaluation.py`**

Lee 36 `evidence.json`, extrae KPIs independientes, computa Pareto (hipervolumen, cobertura, dispersión), IQM con bootstrap CI, performance profiles. Usa `uc3m.domain.pareto` existente.

- [ ] **Step 5: Implementar `model_selection.py`**

Regla: mayor hipervolumen medio multisemilla, desempate menor varianza. Genera paquete: checkpoint, config, manifiesto, hash.

- [ ] **Step 6: Implementar `baselines.py`**

KPIs del Rule-Based Controller (RBC) de CityLearn sobre mismo dataset/horizonte.

- [ ] **Step 7: Ejecutar tests**

```bash
python -B -m pytest tests/unit/application/test_scientific_evaluation.py tests/unit/application/test_model_selection.py -v
```
Expected: PASS

- [ ] **Step 8: Ejecutar evaluación sobre evidencia**

```bash
python -m uc3m.application.evaluation.scientific_evaluation --evidence-root outputs/modular_training --output data/audits/scientific_evaluation.json
python -m uc3m.application.evaluation.model_selection --evaluation data/audits/scientific_evaluation.json --output data/audits/best_model_selection.json
```

- [ ] **Step 9: Commit**

```bash
git add uc3m/application/evaluation/ tests/unit/application/ data/audits/
git commit -m "feat(spec-005): scientific evaluation, baselines and best model selection

Independent KPIs, Pareto, multiseed IQM+CI, performance profiles,
RBC baseline. Selection: max hypervolume, min variance tiebreak."
```

---

### Tarea 7: Observaciones del jurado y evidencia de tesis (SPEC-006/009)

**Hallazgo:** H-04 (J-01–J-17 sin abordar)

**Files:**
- Create: `data/audits/jury_observations_manifest.json`
- Create: `uc3m/application/thesis/evidence_registry.py`
- Create: `tests/contract/test_jury_observations.py`

**Interfaces:**
- Consumes: `data/audits/best_model_selection.json`, `data/audits/scientific_evaluation.json`
- Produces: `jury_observations_manifest.json` con status por observación; `evidence_registry.py` que proyecta evidencia aceptada hacia tesis

- [ ] **Step 1: Formalizar manifiesto J-01–J-17**

```json
{
  "observations": [
    {"id": "J-01", "description": "...", "type": "documental|analytical|experimental",
     "correction": "...", "evidence_path": "...", "test": "...", "status": "pending"}
  ]
}
```

Clasificar según plan de jurado (`docs/plans/jurado.md`).

- [ ] **Step 2: Escribir test de completitud**

```python
# tests/contract/test_jury_observations.py
def test_all_17_observations_formalized():
    manifest = json.loads(Path('data/audits/jury_observations_manifest.json').read_text())
    assert len(manifest['observations']) == 17
    for obs in manifest['observations']:
        assert obs['type'] in ('documental', 'analytical', 'experimental')

def test_experimental_observations_require_campaign_evidence():
    ...
```

- [ ] **Step 3: Implementar registro de evidencia para tesis**

`uc3m/application/thesis/evidence_registry.py`: lee manifiestos de aceptación, genera referencias trazables para tablas/figuras. Solo promueve con `scientific_acceptance: true`.

- [ ] **Step 4: Abordar correcciones documentales y analíticas**

Cada J-xx documental: corrección en documento, registro con ruta y hash. Cada J-xx analítico: verificación estadística, §3.1.3 si aplica.

- [ ] **Step 5: Las experimentales se cierran con evidencia de campaña**

Enlazar J-xx experimentales a manifiestos de Tareas 5/6.

- [ ] **Step 6: Ejecutar tests**

```bash
python -B -m pytest tests/contract/test_jury_observations.py -v
```

- [ ] **Step 7: Commit**

```bash
git add data/audits/jury_observations_manifest.json uc3m/application/thesis/
git add tests/contract/test_jury_observations.py
git commit -m "feat(spec-009): formalize J-01 to J-17 with evidence traceability"
```

---

### Tarea 8: Limpieza final y cierre (SPEC-001/007/008)

**Hallazgos:** H-13 (skills legados), residuales de H-16

**Files:**
- Modify: `tools/skills/registry.yaml`
- Create: `.gitattributes` — LFS para futuros archivos grandes
- Modify: `specs/STATUS.md`
- Produce: `data/audits/final_acceptance.json`

**Interfaces:**
- Consumes: todo lo anterior
- Produces: `final_acceptance.json`, `specs/STATUS.md` actualizado

- [ ] **Step 1: Resolver skills legados**

Migrar o documentar exclusión de 4 skills de `agent-skills/`. Resolver colisión `iquitos-citylearn-dataset`.

- [ ] **Step 2: Configurar Git LFS para futuros archivos grandes**

```gitattributes
*.csv filter=lfs diff=lfs merge=lfs -text
*.pt filter=lfs diff=lfs merge=lfs -text
*.pkl filter=lfs diff=lfs merge=lfs -text
*.docx filter=lfs diff=lfs merge=lfs -text
*.xlsx filter=lfs diff=lfs merge=lfs -text
*.pdf filter=lfs diff=lfs merge=lfs -text
```

- [ ] **Step 3: Actualizar `specs/STATUS.md`**

Reflejar estado real post-remediación. Solo `verified` donde evidencia acreditada.

- [ ] **Step 4: Generar manifiesto final**

Solo cuando todas las puertas pasen.

- [ ] **Step 5: Suite completa final**

```bash
python -B -m pytest tests/ -q --no-header
```

- [ ] **Step 6: Commit**

```bash
git add -u
git commit -m "chore: final remediation — STATUS update, legacy skills, LFS, acceptance"
```

---

## Dependencias entre tareas

```
Tarea 1 (higiene) ───┐
                      ├──→ Tarea 2 (pesos) ──┐
                      ├──→ Tarea 3 (persist.) ┤
                      │                        ├──→ Tarea 4 (specs) ──→ Tarea 5 (campaña)
                      │                        │                              │
                      │                        │                        Tarea 6 (evaluación)
                      │                        │                              │
                      │                        │                        Tarea 7 (jurado)
                      │                        │                              │
                      └────────────────────────┴──────────────────────→ Tarea 8 (cierre)
```

Tareas 2 y 3 paralelas tras Tarea 1. Desde Tarea 4, estrictamente secuencial. Tarea 5 domina el tiempo total (semanas de cómputo).

## Estimación de esfuerzo

| Tarea | Dev | Cómputo | Bloqueo |
|---|---|---|---|
| 1. Higiene | 1h | — | — |
| 2. Pesos | 4h | — | — |
| 3. Persistencia | 8h | — | Acceso a frameworks HARL/MARL |
| 4. Specs/orquestación | 6h | — | — |
| 5. Campaña | 2h setup | **2-4 semanas GPU** | Hardware o Colab |
| 6. Evaluación | 6h | 1h | Depende de Tarea 5 |
| 7. Jurado | 8h | — | Depende de Tarea 6 |
| 8. Cierre | 2h | — | Todo |
| **Total** | **~37h dev** | **2-4 semanas** | |
