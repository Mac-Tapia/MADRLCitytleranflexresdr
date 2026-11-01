# Tareas — SPEC-002

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-002.1:** Objetos de valor y catálogo canónico — `uc3m/domain/objectives.py, configs/objective_policies.yaml`
- [x] **FR-002.3:** Escenarios, tarifa y restricciones separados — `uc3m/domain/scenarios.py, configs/scenarios.yaml, uc3m/application/configuration.py`
- [x] **FR-002.4:** Adaptador CityLearn corregido a las claves `flex`/`carbon`/`cost` que usa `ScenarioConfig`; la prueba de integración exige igualdad con los pesos fijos de CityLearn y con su ruta de catálogo canónico (`UC3M_SCENARIO_CATALOG`) en E1–E3 — `uc3m/adapters/citylearn/objectives.py, tests/integration/test_citylearn_objective_adapter.py`
- [ ] **FR-002.5:** Telemetría por término EV/BESS — `uc3m/reward/axes.py`
- [x] **FR-002.6:** Detector de deriva — `tools/ops/audit_objective_policy_drift.py`
- [ ] **FR-002.6:** Eliminar duplicados activos restantes reportados por el detector — `data/audits/objective_policy_drift.json`

**Aceptación:** `python -m pytest -q tests/unit/domain tests/contract/multiobjective`
