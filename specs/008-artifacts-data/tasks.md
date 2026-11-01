# Tareas — SPEC-008

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-008.1:** Almacén atómico y ADR — `uc3m/adapters/local_artifacts.py, docs/decisions/ADR-OPEN-ARTIFACT-STORE.md`
- [ ] **FR-008.2:** Política de retención — `governance/artifact_retention_policy.yaml`
- [ ] **FR-008.3:** Prueba de respaldo/restauración — `tests/integration/test_artifact_restore.py`
- [ ] **FR-008.4:** Retirar temporales y outputs no promovidos del índice (sin borrar evidencia) — `.gitignore`

**Aceptación:** `python -m pytest -q tests/unit/adapters tests/integration`
