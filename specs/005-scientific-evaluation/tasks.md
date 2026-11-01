# Tareas — SPEC-005

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-005.2:** Pareto puro — `uc3m/domain/pareto.py`
- [x] **FR-005.3:** Diseño de sensibilidad y dry-run — `uc3m/application/sensitivity.py, data/audits/objective_weight_sensitivity_dry_run.json`
- [ ] **FR-005.4:** Configuración de campaña 4×3 multisemilla — `configs/experiments/madrl_4x3_multiseed.yaml`
- [ ] **FR-005.4:** Ejecutar campaña de horizonte completo (requiere aprobación de cómputo) — `outputs/<campaña>`
- [ ] **FR-005.5:** Informe rliable/estadístico — `tools/eval/build_rliable_report.py`
- [ ] **FR-005.6:** Regla de selección y prueba de aceptación — `tests/acceptance/test_model_selection.py`

**Aceptación:** `python -m pytest -q tests/contract/multiobjective tests/contract/training tests/acceptance`
