# Tareas — SPEC-012

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-012.1:** Renombrar manifiestos `*.codex_*.json` a `*.audit_*.json` — `data/dataset_audit/`
- [ ] **FR-012.6:** Decisión del usuario sobre el Stop hook — `.claude/settings.json`
- [ ] **FR-012.1:** Renombrar ramas `codex/*` y `cursor/*` (local y remoto, con confirmación) — `git`
- [ ] **FR-012.1:** Retirar `.codex` de los scripts de registro y contexto — `scripts/skills/register_local_skills.ps1, scripts/verify_project_context.ps1`
- [ ] **FR-012.3:** Retirar `.codex_tmp/` (1 213 archivos) del índice — `.gitignore`
- [ ] **FR-012.2:** Mover `LANZAR_ENTRENAMIENTO_V4.bat` y archivos sueltos de la raíz — `scripts/`
- [ ] **FR-012.4:** Inventario de duplicados en docs/ (77 entradas) y outputs/ (59 entradas) — `data/audits/repository_hygiene_manifest.json`
- [ ] **FR-012:** Prueba de higiene — `tests/ops/test_repository_hygiene.py`

**Aceptación:** `python -m pytest -q tests/ops/test_repository_hygiene.py`
