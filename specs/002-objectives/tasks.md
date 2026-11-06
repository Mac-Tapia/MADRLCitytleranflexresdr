# Tareas — SPEC-002

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-002.1:** Objetos de valor y catálogo canónico — `uc3m/domain/objectives.py, configs/objective_policies.yaml`
- [x] **FR-002.3:** Escenarios, tarifa y restricciones separados — `uc3m/domain/scenarios.py, configs/scenarios.yaml, uc3m/application/configuration.py`
- [x] **FR-002.4:** Adaptador CityLearn corregido a las claves `flex`/`carbon`/`cost` que usa `ScenarioConfig`; la prueba de integración exige igualdad con los pesos fijos de CityLearn y con su ruta de catálogo canónico (`UC3M_SCENARIO_CATALOG`) en E1–E3 — `uc3m/adapters/citylearn/objectives.py, tests/integration/test_citylearn_objective_adapter.py`
- [x] **FR-002.5:** Descomposición por término (2026-11-01): `RewardTermDecomposition` (`axis_weights`, `axis_contributions` flex/carbon/cost, `service_terms` ev/bess_cycle fuera del simplex, `total`) reconstruida desde el desglose que ya registra `CityLearnV3MADRLRewardFunction`, propagando `reward_scale`, la mezcla de equipo y el agente central. Pruebas: el total iguala la recompensa existente (tol. 1e-12) en E1–E3, por agente y central; EV/BESS no nulos y separados; pesos iguales al catálogo canónico; la telemetría no altera estado ni recompensas siguientes. Solo telemetría: pesos y recompensa sin cambios; CityLearn no modificado — `uc3m/reward/term_telemetry.py, tests/uc3m/test_reward_term_telemetry.py`
- [x] **FR-002.5, entrenamiento (2026-11-06, SPEC-015 FR-015.6):** el supervisor del intento (`native_entrypoint.RewardSupervisor` → `RewardTelemetryRecorder`) descompone la recompensa en cada paso, sin tocar los lanzadores.
  - **Registro por episodio**, en `supervision.json`: los términos escalados de los 17 edificios (`building_reward_terms`: flex, carbon, cost, ev, bess_cycle y total) y su media (`reward_terms_mean`, que con `team_mean` es la recompensa que recibió cada agente).
  - **Cuadre en cada paso:**
    - los términos deben igualar `local_reward`, con una tolerancia de 1e-9;
    - la agregación de los totales locales debe igualar la recompensa devuelta por `CityLearnDecPOMDPEnv`, con una tolerancia relativa de 1e-5 por el paso a float32.
  - **Efecto en el intento:** un paso que no cuadra, o uno cuya recompensa no se pudo comprobar, lo deja sin verificar (`reward_terms_do_not_reconcile`).
  - **Pruebas:** `tests/fresh_training/test_learning_observer.py`, con el simulador real y un caso falsificado, y `test_real_learning.py`, sobre la corrida real de los 4 algoritmos.
  - **Por qué por episodio y no por paso:** guardar cada paso de cada edificio serían 438 000 × 17 filas por intento. El cuadre sí se comprueba en cada paso.
- [ ] **FR-002.5, evaluación:** la evaluación congelada calcula los KPI desde la traza física y no registra la recompensa. La descomposición por paso del episodio de evaluación queda asignada al módulo 5 ([hoja de ruta](../../docs/plans/hoja_ruta_modulos.md)).
- **Nota:** `RewardAxes` 7-D (`uc3m/reward/axes.py`), que usa `uc3m/env/uc3m_env.py`, no tiene términos EV y no es la recompensa `CityLearnV3MADRLRewardFunction` que se descompone aquí.
- [x] **FR-002.6:** Detector de deriva — `tools/ops/audit_objective_policy_drift.py`
- [ ] **FR-002.6:** Eliminar duplicados activos restantes reportados por el detector — `data/audits/objective_policy_drift.json`

**Aceptación:** `python -m pytest -q tests/unit/domain tests/contract/multiobjective`
