# Tareas — SPEC-003

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-003.3:** Módulos de entrenamiento extraídos — `uc3m/application/training/*.py`
- [x] **FR-003.1:** LearnerPort y ArtifactStore — `uc3m/ports/learner.py, uc3m/ports/artifact_store.py`
- [ ] **FR-003.1:** SimulatorPort y ExperimentTrackerPort — `uc3m/ports/simulator.py, uc3m/ports/experiment_tracker.py, tests/contract/test_ports_contract.py`
- [ ] **FR-003.2:** Conformidad explícita de NativeBackend — `uc3m/adapters/algorithms/native.py`
- [ ] **FR-003.4:** TrainingReportBuilder, tablas y FigureRenderer — `uc3m/application/evaluation/tables.py, uc3m/adapters/matplotlib_figures.py`
- [ ] **FR-003.5:** Prueba de cancelación de hijos y reanudación — `tests/integration/test_training_interruption.py`
- [ ] **FR-003.6:** Prueba de arquitectura de imports — `tests/contract/test_import_architecture.py`
- [ ] **FR-003:** Generar manifiesto de aceptación — `data/audits/orchestration_acceptance.json`

**Aceptación:** `powershell -ExecutionPolicy Bypass -File scripts/quality/run_orchestration_gates.ps1`
