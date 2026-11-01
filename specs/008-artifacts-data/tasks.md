# Tareas — SPEC-008

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-008.1:** Almacén atómico y ADR — `uc3m/adapters/local_artifacts.py, docs/decisions/ADR-OPEN-ARTIFACT-STORE.md`
- [x] **FR-008.2:** Política de retención — `governance/artifact_retention_policy.yaml`, validada por `uc3m/application/artifacts/retention.py`. Verificado 2026-11-01: cubre todos los `kind` emitidos por `uc3m/adapters` y `uc3m/ports` (escaneo en la prueba) y sus `gitignore_rules` existen en `.gitignore`. Pendiente (FR-008.4): `*.zip`, `*.tmp` y artefactos `other_artifacts` marcados `git_versioned: false` aún no tienen regla en `.gitignore`; el borrado tras promoción no está automatizado.
- [x] **FR-008.3:** Respaldo/restauración verificados por SHA-256 — `uc3m/application/artifacts/backup.py` (`backup_run`, `restore_run`, almacén inyectado por el puerto `ArtifactStore`), `tests/integration/test_artifact_restore.py`. Verificado 2026-11-01 con una corrida `verified` sintética en `tmp_path` (sin entrenamiento): respaldo → borrado → restauración reproduce todos los hashes de `evidence.json`; fallan cerrado byte alterado, archivo faltante, `evidence.json` alterado o no anclado y corrida no verificada o corrupta. Comando: `.venv39-citylearn-v3\Scripts\python.exe -m pytest -p no:cacheprovider -o addopts="" -q -rs tests/integration/test_artifact_restore.py tests/contract/test_import_architecture.py` → 13 passed, 0 skipped. No se ha respaldado ni restaurado aún una corrida real de Colab; el destino es local (sin copia externa ni recuperación de desastre).
- [ ] **FR-008.4:** Retirar temporales y outputs no promovidos del índice (sin borrar evidencia) — `.gitignore`

**Aceptación:** `python -m pytest -q tests/unit/adapters tests/integration`
