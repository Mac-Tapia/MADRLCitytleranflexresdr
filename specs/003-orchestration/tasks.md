# Tareas — SPEC-003

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-003.3:** Módulos de entrenamiento extraídos — `uc3m/application/training/*.py`
- [x] **FR-003.1:** LearnerPort y ArtifactStore — `uc3m/ports/learner.py, uc3m/ports/artifact_store.py`
- [x] **FR-003.1:** `SimulatorPort` sin numpy y los tres puertos `runtime_checkable` y exportados; `ExperimentTrackerPort` aplazado hasta tener consumidor (ADR) — `uc3m/ports/*.py, docs/decisions/simulator.md`
- [x] **FR-003.2:** Conformidad verificada de `NativeBackend` con `LearnerPort` y de `LocalArtifactStore` con `ArtifactStore` — `tests/contract/test_ports_contract.py`
- [ ] **FR-003.4:** TrainingReportBuilder, tablas y FigureRenderer — `uc3m/application/evaluation/tables.py, uc3m/adapters/matplotlib_figures.py`
- [ ] **FR-003.5:** Prueba de cancelación de hijos y reanudación — `tests/integration/test_training_interruption.py`
- [x] **FR-003.6:** Prueba de arquitectura: el dominio no importa infraestructura ni capas externas, y la aplicación solo llega a adaptadores desde `cli.py`/`colab.py`; `finite_kpis` se movió del adaptador al dominio para cumplirla — `tests/contract/test_import_architecture.py, uc3m/domain/evidence.py`
- [ ] **FR-003:** El manifiesto real de la puerta es `data/audits/modular_training_acceptance.json` (escrito por `tools/ops/audit_modular_training.py`); no se crea un segundo `orchestration_acceptance.json`. Cierre pendiente de FR-003.4 y FR-003.5 — `scripts/quality/run_orchestration_gates.ps1`

**Aceptación:** `powershell -ExecutionPolicy Bypass -File scripts/quality/run_orchestration_gates.ps1`
