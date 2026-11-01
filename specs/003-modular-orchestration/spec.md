# SPEC-003 — Orquestación modular

**Estado:** `partial`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Extraer el script común de entrenamiento (>9 000 líneas) a módulos de `uc3m` detrás de puertos, conservando los launchers HAPPO/MASAC/MATD3/MAAC y sus argumentos.

## Requisitos funcionales

- **FR-003.1** — Puertos `SimulatorPort`, `LearnerPort` (`runtime_checkable`), `ArtifactStore` y `ExperimentTrackerPort` como `typing.Protocol`.
- **FR-003.2** — `NativeBackend` declara y verifica la conformidad con `LearnerPort`.
- **FR-003.3** — Layout, persistencia, completitud, reanudación, lock, runner y CLI en `uc3m/application/training/`.
- **FR-003.4** — Reportes, tablas y figuras extraídos a `uc3m/application/evaluation/` y `uc3m/adapters/matplotlib_figures.py`.
- **FR-003.5** — Cancelación de procesos hijos al morir el padre y continuidad tras interrupción.
- **FR-003.6** — Grafo de dependencias sin importación del dominio hacia CityLearn ni `external/`.

## Criterios de aceptación

1. `run_orchestration_gates.ps1` termina en 0 y escribe `data/audits/orchestration_acceptance.json`.
2. Los launchers existentes siguen ejecutando el smoke de 8 pasos para los cuatro algoritmos.
3. Prueba de arquitectura de imports pasa.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-002
- Bloquea: SPEC-004, SPEC-005, SPEC-011
