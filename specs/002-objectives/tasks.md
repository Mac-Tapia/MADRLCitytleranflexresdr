# Tareas — SPEC-002

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-002.1:** Objetos de valor y catálogo canónico — `uc3m/domain/objectives.py, configs/objective_policies.yaml`
- [x] **FR-002.3:** Escenarios, tarifa y restricciones separados — `uc3m/domain/scenarios.py, configs/scenarios.yaml, uc3m/application/configuration.py`
- [x] **FR-002.4:** Adaptador CityLearn corregido a las claves `flex`/`carbon`/`cost` que usa `ScenarioConfig`; la prueba de integración exige igualdad con los pesos fijos de CityLearn y con su ruta de catálogo canónico (`UC3M_SCENARIO_CATALOG`) en E1–E3 — `uc3m/adapters/citylearn/objectives.py, tests/integration/test_citylearn_objective_adapter.py`
- [x] **FR-002.5:** Descomposición por término (2026-11-01): `RewardTermDecomposition` (`axis_weights`, `axis_contributions` flex/carbon/cost, `service_terms` ev/bess_cycle fuera del simplex, `total`) reconstruida desde el desglose que ya registra `CityLearnV3MADRLRewardFunction`, propagando `reward_scale`, la mezcla de equipo y el agente central. Pruebas: el total iguala la recompensa existente (tol. 1e-12) en E1–E3, por agente y central; EV/BESS no nulos y separados; pesos iguales al catálogo canónico; la telemetría no altera estado ni recompensas siguientes. Solo telemetría: pesos y recompensa sin cambios; CityLearn no modificado — `uc3m/reward/term_telemetry.py, tests/uc3m/test_reward_term_telemetry.py`
- [ ] **FR-002.5:** Persistir la descomposición por paso en los registros de entrenamiento/evaluación (requiere tocar launchers o `tools/`, fuera de este alcance); `RewardAxes` 7-D (`uc3m/reward/axes.py`) usado por `uc3m/env/uc3m_env.py`, no tiene términos EV y no es la recompensa `CityLearnV3MADRLRewardFunction` descompuesta aquí
- [x] **FR-002.6:** Detector de deriva — `tools/ops/audit_objective_policy_drift.py`
- [ ] **FR-002.6:** Eliminar duplicados activos restantes reportados por el detector — `data/audits/objective_policy_drift.json`

**Aceptación:** `python -m pytest -q tests/unit/domain tests/contract/multiobjective`
