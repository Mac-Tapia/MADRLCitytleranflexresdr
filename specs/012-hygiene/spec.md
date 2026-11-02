# SPEC-012 — Higiene y reorganización del repositorio

**Estado:** `pending`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Dejar el repositorio mantenible y listo para el nuevo entrenamiento: estructura por responsabilidad, sin temporales versionados, sin duplicados y sin nombres de herramientas de agentes en rutas, ramas, datos o código.

## Requisitos funcionales

- **FR-012.1** — Ninguna ruta, rama, manifiesto o identificador de código contiene `codex`, `claude`, `cursor` o `copilot`, salvo las carpetas de configuración que esas herramientas exigen (`.claude/`, `.cursor/`, `.github/`) y referencias documentales a la herramienta.
- **FR-012.2** — La raíz solo contiene archivos de proyecto (README, AGENTS, CLAUDE, pyproject, requirements, Dockerfile, configuraciones de calidad); scripts sueltos pasan a `scripts/` o `tools/`.
- **FR-012.3** — Temporales (`.codex_tmp/`, `_tmp_*`, `outputs/_tmp_*`, `~$*.docx`) fuera del índice y en `.gitignore`.
- **FR-012.4** — Duplicados y versiones obsoletas de documentos y scripts inventariados; se conserva una canónica y el resto se archiva fuera del árbol activo.
- **FR-012.5** — Cada eliminación se registra en `data/audits/repository_hygiene_manifest.json` con ruta, motivo y commit de origen; nada se reescribe del historial.
- **FR-012.6** — El Stop hook de autopublicación se desactiva o se limita por decisión explícita del usuario antes de cualquier cambio masivo.

## Criterios de aceptación

1. `tests/ops/test_repository_hygiene.py` pasa: sin etiquetas de agentes prohibidas, sin temporales rastreados y raíz conforme.
2. Suite completa de pruebas sin regresión respecto de la línea base (307 aprobadas).

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-000
- Bloquea: SPEC-008, SPEC-011 y nuevo entrenamiento
