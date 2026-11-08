# Tareas — SPEC-012

**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

`[x]` = archivo verificado en el árbol el 2026-10-31; no implica aceptación.

- [x] **FR-012.1:** Renombrar manifiestos `*.codex_*.json` a `*.audit_*.json` — `data/dataset_audit/`
- [x] **FR-012.6:** Stop hook desactivado por decisión del usuario (2026-10-31) — `.claude/settings.json`
- [x] **FR-012.1:** Ramas `codex/*` y `cursor/*` renombradas en el repositorio, en `CityLearn` y en las siete forks de `external/`; Colab actualizado (27abc4b, CityLearn b9c53062). El PR #6 quedó cerrado por el renombrado — `data/audits/repository_hygiene_manifest.json`
- [x] **FR-012.1:** Autoría local del repositorio y submódulos puesta a nombre del propietario; la configuración global no se modificó — `git config --local`
- [x] **FR-012.2:** `uc3m/env/` ya no lo ignora el patrón `env/`: los clones pueden importar `uc3m` (8fcb91b); la prueba de higiene falla si un `uc3m/*.py` queda ignorado — `.gitignore, uc3m/env/`
- [x] **FR-012.1:** `.codex\skills` en `verify_project_context.ps1` queda exento: es la ruta global real que se vigila para cumplir AGENTS.md (ver `exemptions` del manifiesto) — `scripts/verify_project_context.ps1`
- [x] **FR-012.3:** `.codex_tmp/` (1 213 archivos, 340,5 MB) y 6 temporales sueltos eliminados con objeto Git de recuperación; reglas de ignorado y carpeta temporal `.tmp/` — `.gitignore, data/audits/repository_hygiene_manifest.json`
- [x] **FR-012.2:** `LANZAR_ENTRENAMIENTO_V4.bat` movido a `scripts/` sin ruta fija; la raíz solo contiene archivos de proyecto — `scripts/LANZAR_ENTRENAMIENTO_V4.bat`
- [ ] **FR-012.4:** Parcial (2026-11-08, decisión del propietario): retiradas 5 herramientas obsoletas y 21 rutas de docs/ (15 documentos obsoletos y 6 copias idénticas); tools/ y scripts/ sin duplicados exactos fuera de los paquetes de `tools/skills/`. Falta: decisión del propietario sobre el inventario de `outputs/` (1 archivo rastreado) y `.superpowers/` (ignorada), los 3 pares idénticos de registros entre auditorías que sus propios informes citan, y los casos dudosos de docs/ (`docs/plans/` cerrados, `docs/historia.md`, `docs/architecture/control_ilustrado.png`, `control_simbolos.png`, `plano.pdf`) — `data/audits/repository_hygiene_manifest.json`
- [x] **FR-012:** Prueba de higiene: 4 pruebas; suite completa 311 recolectadas, código de salida 0 — `tests/ops/test_repository_hygiene.py`

**Aceptación:** `python -m pytest -q tests/ops/test_repository_hygiene.py`
