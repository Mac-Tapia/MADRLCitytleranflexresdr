# Tareas — SPEC-006

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [ ] **FR-006.1:** Capa thesis y registro — `uc3m/application/thesis/__init__.py, uc3m/application/thesis/evidence_registry.py`
- [ ] **FR-006.2:** Vista multiobjetivo — `uc3m/application/thesis/multiobjective_view.py, tools/thesis/build_multiobjective_evidence.py`
- [ ] **FR-006.3:** Prueba de consistencia §3.1.3 — `tests/thesis/test_cap313_multiobjective_consistency.py`
- [ ] **FR-006.4:** Fuentes APA — `docs/research/multiobjective_sources.yaml`
- [ ] **FR-006.5:** Puerta de tesis — `scripts/quality/run_thesis_agent_gates.ps1`

**Aceptación:** `powershell -ExecutionPolicy Bypass -File scripts/quality/run_thesis_agent_gates.ps1`
