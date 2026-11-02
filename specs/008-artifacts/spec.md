# SPEC-008 — Artefactos y datos

**Estado:** `partial`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Código y manifiestos en Git; artefactos grandes (checkpoints, series, renders) fuera del historial principal con hash, procedencia, retención y restauración verificada.

## Requisitos funcionales

- **FR-008.1** — Almacén local atómico `uc3m/adapters/local_artifacts.py` detrás de `ArtifactStore`.
- **FR-008.2** — Política de retención por tipo de artefacto (activo, promovido, histórico, temporal).
- **FR-008.3** — Respaldo y restauración verificados por hash.
- **FR-008.4** — `outputs/` y temporales fuera de Git salvo manifiestos y evidencia promovida.
- **FR-008.5** — DVC/MLflow solo tras spike aprobado; no se adoptan simultáneamente.

## Criterios de aceptación

1. Restauración de un run promovido reproduce todos los hashes.
2. `git ls-files` no contiene artefactos binarios grandes nuevos.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-004
- Bloquea: SPEC-005, SPEC-012
