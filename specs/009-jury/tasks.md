# Tareas — SPEC-009

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [ ] **FR-009.1:** Manifiesto y prueba — `data/audits/jury_observations_manifest.json, tests/acceptance/test_jury_observations_manifest.py`
- [ ] **FR-009.2:** Consistencia de hipótesis — `tests/thesis/test_hypothesis_decision_consistency.py`
- [ ] **FR-009.3:** Clasificación HAPPO — `docs/chapters/cap5.md`
- [ ] **FR-009.5:** Anexos — `docs/chapters/Anexo_Reproducibilidad.md, docs/thesis/SECURITY_PRIVACY_DEPLOYMENT.md`
- [ ] **FR-009:** Puerta del jurado — `scripts/quality/run_jury_observations_gates.ps1`

**Aceptación:** `powershell -ExecutionPolicy Bypass -File scripts/quality/run_jury_observations_gates.ps1`
