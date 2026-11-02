# Tareas — SPEC-004

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-004.1:** Identidad y especificación — `uc3m/domain/experiments.py`
- [x] **FR-004.2:** Manifiesto de evidencia — `uc3m/domain/evidence.py`
- [x] **FR-004.3:** Preflight — `uc3m/application/training/preflight.py`
- [ ] **FR-004.4:** Continuidad exacta en los 4 algoritmos — `tests/integration/test_resume_trajectory_parity.py`
- [ ] **FR-004.5:** Manifiesto de runs históricos — `data/audits/historical_runs_manifest.json`

**Aceptación:** `python -m pytest -q tests/unit/domain tests/contract/training`
