# Tareas — SPEC-011

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-011.1:** Orquestador de dataset existente — `tools/dataset/orchestrate_citylearn_dataset.py`
- [x] **FR-011.2:** Verificador de dataset listo — `tools/dataset/check_training_dataset_ready.py`
- [ ] **FR-011.1:** Consolidar los 21 scripts de tools/dataset en etapas; retirar fix_*/one-off ya aplicados — `tools/dataset/`
- [ ] **FR-011.4:** Subcomandos por etapa en la CLI — `uc3m/application/training/cli.py`
- [ ] **FR-011.5:** Encadenamiento por hash entre etapas — `uc3m/application/pipeline.py`
- [ ] **FR-011.6:** Humo end-to-end — `tests/acceptance/test_pipeline_smoke.py`

**Aceptación:** `python -m pytest -q tests/acceptance/test_pipeline_smoke.py`
