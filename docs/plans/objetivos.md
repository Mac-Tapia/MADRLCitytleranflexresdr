# Multiobjective Domain and Scientific Evaluation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establecer una fuente única y tipada para recompensa vectorial, políticas E1–E3, tarifas, restricciones y evaluación Pareto sin alterar la semántica histórica.

**Architecture:** El dominio vive en `uc3m/domain` y no importa CityLearn. `CityLearn/citylearn/reward_function.py` y `scenario_manager.py` se convierten gradualmente en adaptadores que consumen contratos del dominio, preservando sus APIs públicas.

**Tech Stack:** Python 3.9, dataclasses, NumPy, SciPy, PyYAML, pytest, MO-Gymnasium/MORL-Baselines solo después de un spike de compatibilidad y licencia.

**Spec:** `docs/design/modernizacion.md`

**Spec Kit slices covered:** `SPEC-002` and `SPEC-005`.

## Conciliación de estado — 2026-10-31

Ver [SPEC-000–010 y pendientes](../../specs/STATUS.md). Dominio, catálogo,
Pareto y sensibilidad dry-run existen; campaña y aceptación estadística siguen
pendientes. El backend rechaza políticas no soportadas: generar la rejilla
no implica poder entrenarla. La matriz del simulador no equivale a aprendizaje
real 4×3. No se acreditan RED/commits históricos por existir código actual.

## Global Constraints

- E1=`[0.60,0.15,0.25]`, E2=`[0.25,0.60,0.15]`, E3=`[0.15,0.25,0.60]` en orden flexibilidad, CO2, costo.
- La política es compensatoria jerárquica, no lexicográfica.
- `primary=0.60`, `secondary=0.25`, `residual=0.15`; suma 1 y `primary > secondary + residual`.
- EV/BESS permanecen fuera del simplex y se informan como términos de servicio/restricción.
- Un cambio de tarifa no puede atribuirse al peso sin experimento controlado.
- Resultados antiguos nunca cambian de `reward_policy_version`.

## Review Focus

- Orden de ejes intercambiado entre archivos: fallar antes de entrenar.
- Vector con NaN, infinito o peso negativo: rechazar.
- Escenario compuesto etiquetado como experimento de pesos: rechazar inferencia causal.
- EV/BESS incluidos dentro de las participaciones de los tres ejes: separar y reportar.
- Dataset o run antiguo sin versión: clasificar legado, no asignar versión por conjetura.

---

### Task 1: Crear los objetos de valor multiobjetivo

**Files:**
- Create: `uc3m/domain/__init__.py`
- Create: `uc3m/domain/objectives.py`
- Test: `tests/unit/domain/test_objectives.py`

**Interfaces:**
- Produces: `ObjectiveAxis`, `RewardVector`, `HierarchyLevels`, `ObjectivePolicy`.

- [ ] **Step 1: Escribir pruebas fallidas de construcción y validación**

Assertions: orden canónico, suma, mayoría estricta, balance cíclico, serialización estable y rechazo de NaN/negativos.

- [ ] **Step 2: Ejecutar y confirmar FAIL**

Run: `python -m pytest tests/unit/domain/test_objectives.py -v`

- [ ] **Step 3: Implementar interfaces exactas**

```python
class ObjectiveAxis(str, Enum):
    FLEXIBILITY = "flexibility"
    CO2_EMISSIONS = "co2_emissions"
    ENERGY_COST = "energy_cost"

@dataclass(frozen=True)
class RewardVector:
    flexibility: float
    co2_emissions: float
    energy_cost: float
    def as_array(self) -> np.ndarray: ...

@dataclass(frozen=True)
class HierarchyLevels:
    primary: float = 0.60
    secondary: float = 0.25
    residual: float = 0.15

@dataclass(frozen=True)
class ObjectivePolicy:
    policy_id: str
    weights: Mapping[ObjectiveAxis, float]
    method: str = "compensatory_hierarchical_weighted_sum"
    def scalarize(self, reward: RewardVector) -> float: ...
    def fingerprint(self) -> str: ...
```

Function: `canonical_objective_policies() -> Mapping[str, ObjectivePolicy]`.

- [ ] **Step 4: Ejecutar pruebas**

Expected: PASS; fingerprints estables ante orden de diccionario distinto.

- [ ] **Step 5: Commit**

```powershell
git add uc3m/domain tests/unit/domain/test_objectives.py
git commit -m "feat: add canonical multiobjective domain policy"
```

### Task 2: Separar escenario, tarifa y restricciones

**Files:**
- Create: `uc3m/domain/scenarios.py`
- Test: `tests/unit/domain/test_scenarios.py`

**Interfaces:**
- Consumes: `ObjectivePolicy`.
- Produces: `TariffPolicy`, `ConstraintPolicy`, `ScenarioDefinition`, `ScenarioCatalog`.

- [ ] **Step 1: Escribir pruebas fallidas**

Assertions: dos escenarios con iguales pesos y distinta tarifa tienen distintos fingerprints; `weights_only=True` exige tarifa idéntica; E1–E3 compuestos quedan rotulados como tales.

- [ ] **Step 2: Implementar interfaces**

```python
@dataclass(frozen=True)
class TariffPolicy:
    policy_id: str
    mode: Literal["rtp", "flat", "tou"]
    multiplier: float

@dataclass(frozen=True)
class ConstraintPolicy:
    policy_id: str
    ev_service_enabled: bool
    bess_limits_enabled: bool

@dataclass(frozen=True)
class ScenarioDefinition:
    scenario_id: str
    objective_policy: ObjectivePolicy
    tariff_policy: TariffPolicy
    constraint_policy: ConstraintPolicy
    study_kind: Literal["weights_only", "composite"]
    def fingerprint(self) -> str: ...
```

- [ ] **Step 3: Ejecutar pruebas**

Expected: PASS; la causalidad queda validada por construcción.

- [ ] **Step 4: Commit**

```powershell
git add uc3m/domain/scenarios.py tests/unit/domain/test_scenarios.py
git commit -m "feat: separate objective tariff and constraint policies"
```

### Task 3: Crear el catálogo canónico y proyecciones de configuración

**Files:**
- Create: `configs/objective_policies.yaml`
- Create: `configs/scenarios.yaml`
- Create: `uc3m/application/configuration.py`
- Test: `tests/contract/multiobjective/test_config_projection.py`

**Interfaces:**
- Consumes: objetos del dominio.
- Produces: `load_scenario_catalog(path: Path) -> ScenarioCatalog`, `project_runtime_config(definition) -> dict[str, object]`.

- [ ] **Step 1: Escribir prueba de deriva fallida**

Assert: YAML, catálogo Python y JSON proyectado producen los mismos fingerprints.

- [ ] **Step 2: Implementar cargador y proyección**

El YAML contiene datos; las reglas de validación permanecen en el dominio.

- [ ] **Step 3: Ejecutar pruebas**

Expected: PASS para E1–E3; rechazo de eje faltante y peso obsoleto 0.70.

- [ ] **Step 4: Commit**

```powershell
git add configs/objective_policies.yaml configs/scenarios.yaml uc3m/application/configuration.py tests/contract/multiobjective/test_config_projection.py
git commit -m "feat: add canonical scenario configuration projections"
```

### Task 4: Adaptar CityLearn a los contratos sin romper API

**Files:**
- Create: `uc3m/adapters/citylearn/__init__.py`
- Create: `uc3m/adapters/citylearn/objectives.py`
- Modify: `CityLearn/citylearn/reward_function.py:527`
- Modify: `CityLearn/citylearn/scenario_manager.py:22`
- Test: `tests/integration/test_citylearn_objective_adapter.py`
- Test: `CityLearn/tests/test_citylearn_v3_reward_hierarchy.py`

**Interfaces:**
- Consumes: `RewardVector`, `ObjectivePolicy`, `ScenarioDefinition`.
- Produces: `CityLearnObjectiveAdapter.vector_from_observation(...)`, `scalarize(...)`, metadatos compatibles.

- [ ] **Step 1: Registrar autorización y contribución CityLearn**

Modify: `docs/contributions/CityLearn/CHANGES.md` con motivo, archivos, pruebas y referencias.

- [ ] **Step 2: Escribir prueba de paridad antes del cambio**

Capturar salida actual para observaciones deterministas E1–E3, incluyendo términos EV/BESS y participaciones efectivas.

- [ ] **Step 3: Implementar adaptador**

`reward_function.py` conserva `CityLearnV3MADRLRewardFunction`; obtiene pesos y método desde el adaptador. `scenario_manager.py` conserva `ScenarioConfig`; proyecta `ScenarioDefinition`.

- [ ] **Step 4: Ejecutar pruebas de paridad e integración**

Run: `python -m pytest -q CityLearn/tests/test_citylearn_v3_reward_hierarchy.py tests/integration/test_citylearn_objective_adapter.py`

Expected: PASS; mismo cálculo aceptado y nuevos fingerprints presentes.

- [ ] **Step 5: Commit en submódulo y superproyecto según política**

No mezclar ambos commits; documentar SHA del submódulo en el superproyecto.

### Task 5: Añadir detección automática de duplicados activos

**Files:**
- Create: `tools/ops/audit_objective_policy_drift.py`
- Test: `tests/contract/multiobjective/test_objective_policy_drift.py`
- Produce: `data/audits/objective_policy_drift.json`

**Interfaces:**
- Produces: `audit_policy_drift(project_root: Path, catalog: ScenarioCatalog) -> dict[str, object]`.

- [ ] **Step 1: Escribir fixtures con pesos antiguos en código activo, historia y documento**

Assert: código/config activa bloquea; historia explícitamente marcada y resultado legado no bloquean; tesis activa se reporta para SPEC-006.

- [ ] **Step 2: Implementar auditoría estructural y textual acotada**

Buscar solo rutas declaradas; no escanear binarios como texto.

- [ ] **Step 3: Ejecutar auditoría real**

Expected: lista exacta de fuentes activas restantes; cero falsos “corregidos”.

- [ ] **Step 4: Commit**

```powershell
git add tools/ops/audit_objective_policy_drift.py tests/contract/multiobjective/test_objective_policy_drift.py data/audits/objective_policy_drift.json
git commit -m "test: gate objective policy drift"
```

### Task 6: Incorporar métricas Pareto sin acoplar una librería externa

**Files:**
- Create: `uc3m/domain/pareto.py`
- Modify: `uc3m/multicriteria/pipeline.py`
- Modify: `uc3m/multicriteria/artifacts.py`
- Test: `tests/unit/domain/test_pareto.py`
- Test: `tests/uc3m/test_madrl_multicriteria.py`

**Interfaces:**
- Produces: `dominates`, `non_dominated_indices`, `hypervolume_3d`, `expected_utility`, `sparsity`.

- [ ] **Step 1: Escribir pruebas contra frentes pequeños calculables a mano**

Assertions: orientación minimizar/maximizar explícita; duplicados y puntos dominados; referencia inválida rechazada.

- [ ] **Step 2: Implementar funciones puras**

No copiar MORL-Baselines. Comparar resultados con la librería solo en un spike opcional.

- [ ] **Step 3: Ejecutar tests**

Expected: PASS y resultados deterministas.

- [ ] **Step 4: Evaluar spike MO-Gymnasium/MORL-Baselines**

Create only if approved: `experiments/spikes/morl_compatibility/README.md`.

Promote dependency únicamente si aporta una función no cubierta y supera Python 3.9, licencia y pruebas; de lo contrario conservar referencia.

- [ ] **Step 5: Commit**

```powershell
git add uc3m/domain/pareto.py uc3m/multicriteria tests/unit/domain/test_pareto.py tests/uc3m/test_madrl_multicriteria.py
git commit -m "feat: add auditable Pareto evaluation"
```

### Task 7: Diseñar sensibilidad y matriz multisemilla

**Files:**
- Create: `uc3m/application/sensitivity.py`
- Create: `configs/experiments/objective_weight_sensitivity.yaml`
- Test: `tests/unit/application/test_sensitivity.py`
- Create: `tools/eval/run_objective_weight_sensitivity.py`

**Interfaces:**
- Produces: `generate_weight_grid(levels, step) -> tuple[ObjectivePolicy, ...]`, `ExperimentMatrix`.

- [ ] **Step 1: Escribir pruebas de rejilla y presupuesto**

Assert: pesos suman uno, incluye E1–E3, no duplica fingerprints y separa `weights_only` de `composite`.

- [ ] **Step 2: Implementar generador determinista**

- [ ] **Step 3: Implementar CLI en modo `--dry-run` primero**

Salida: manifiesto de tratamientos, semillas y costo estimado; no lanza entrenamiento por defecto.

- [ ] **Step 4: Ejecutar dry-run y tests**

Expected: matriz revisable antes de consumir GPU.

- [ ] **Step 5: Commit**

```powershell
git add uc3m/application/sensitivity.py configs/experiments/objective_weight_sensitivity.yaml tests/unit/application/test_sensitivity.py tools/eval/run_objective_weight_sensitivity.py
git commit -m "feat: plan multi-seed objective sensitivity experiments"
```

### Task 8: Validar las 12 combinaciones sin entrenamiento largo

**Files:**
- Create: `tests/contract/multiobjective/test_algorithm_scenario_matrix.py`
- Modify: `CityLearn/scripts/validate_citylearn_v3_reward_profiles.py`
- Produce: `data/audits/algorithm_scenario_contract_matrix.json`

**Interfaces:**
- Consumes: catálogo y factory de algoritmos.
- Produces: matriz 4 algoritmos × 3 escenarios con fingerprints.

- [ ] **Step 1: Escribir test parametrizado 4×3**

Assertions: construcción, metadatos, pesos, tarifa, restricciones y ausencia de NaN.

- [ ] **Step 2: Añadir modo contractual al validador**

No entrena; construye el entorno real con dataset Iquitos y ejecuta un paso seguro por backend cuando sea posible.

- [ ] **Step 3: Ejecutar suite contractual**

Expected: 12/12 válidas; fallos de dependencia se reportan como bloqueos, no skips exitosos.

- [ ] **Step 4: Commit**

```powershell
git add tests/contract/multiobjective/test_algorithm_scenario_matrix.py CityLearn/scripts/validate_citylearn_v3_reward_profiles.py data/audits/algorithm_scenario_contract_matrix.json
git commit -m "test: validate full algorithm scenario contract matrix"
```

