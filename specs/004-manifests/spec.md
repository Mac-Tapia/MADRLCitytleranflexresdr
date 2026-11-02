# SPEC-004 — Manifiestos de ejecución

**Estado:** `implemented` (identidad) / `partial` (continuidad)  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Cada ejecución queda ligada a commit, submódulos, dataset, política de recompensa, semillas, entorno y artefactos con hash, y puede reanudarse sin alterar la trayectoria.

## Requisitos funcionales

- **FR-004.1** — `RunIdentity`/`ExperimentSpec` con commit, hashes SHA-256 y `reward_policy_version`.
- **FR-004.2** — `EvidenceManifest`/`ArtifactRef` con hash, tamaño y tipo; rutas fuera del run rechazadas.
- **FR-004.3** — Preflight fail-closed antes de lanzar.
- **FR-004.4** — Reanudación restaura optimizador, RNG y replay; prueba de igualdad de trayectoria por algoritmo.
- **FR-004.5** — Resultados históricos inmutables y clasificados con su política original.

## Criterios de aceptación

1. Prueba de continuidad pasa para HAPPO, MASAC, MATD3 y MAAC en horizonte corto.
2. Ningún run histórico reetiquetado con la nueva política.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-003
- Bloquea: SPEC-005, SPEC-008
