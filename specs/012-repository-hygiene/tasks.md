# Tareas — SPEC-012

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-012.1:** Renombrar manifiestos `*.codex_*.json` a `*.audit_*.json` — `data/dataset_audit/`
- [x] **FR-012.6:** Stop hook desactivado por decisión del usuario (2026-10-31) — `.claude/settings.json`
- [ ] **FR-012.1:** Renombrar ramas `codex/*` y `cursor/*` (local y remoto, con confirmación) — `git`
- [x] **FR-012.1:** `.codex\skills` en `verify_project_context.ps1` queda exento: es la ruta global real que se vigila para cumplir AGENTS.md (ver `exemptions` del manifiesto) — `scripts/verify_project_context.ps1`
- [x] **FR-012.3:** `.codex_tmp/` (1 213 archivos, 340,5 MB) y 6 temporales sueltos eliminados con objeto Git de recuperación; reglas de ignorado y carpeta temporal `.tmp/` — `.gitignore, data/audits/repository_hygiene_manifest.json`
- [x] **FR-012.2:** `LANZAR_ENTRENAMIENTO_V4.bat` movido a `scripts/` sin ruta fija; la raíz solo contiene archivos de proyecto — `scripts/LANZAR_ENTRENAMIENTO_V4.bat`
- [ ] **FR-012.4:** Inventario de duplicados en docs/ (77 entradas) y outputs/ (2 648 archivos rastreados, junto con SPEC-008) — `data/audits/repository_hygiene_manifest.json`
- [x] **FR-012:** Prueba de higiene: 4 pruebas; suite completa 311 recolectadas, código de salida 0 — `tests/ops/test_repository_hygiene.py`

**Aceptación:** `python -m pytest -q tests/ops/test_repository_hygiene.py`
