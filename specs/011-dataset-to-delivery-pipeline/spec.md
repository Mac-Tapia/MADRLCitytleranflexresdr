# SPEC-011 — Flujo integral dataset → entrega

**Estado:** `partial`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Un único flujo ejecutable y verificable: generación del dataset Iquitos → validación → preflight → entrenamiento → evaluación → selección → entrega, con un comando por etapa y manifiesto de entrada/salida en cada frontera.

## Requisitos funcionales

- **FR-011.1** — Generación: `tools/dataset/orchestrate_citylearn_dataset.py` produce schema y CSV CityLearn con manifiesto de procedencia.
- **FR-011.2** — Validación: `tools/dataset/check_training_dataset_ready.py` emite `data/dataset_audit/training_dataset_ready_manifest.json` fail-closed.
- **FR-011.3** — Puerto `DatasetSource` (`uc3m/data/ports.py`) es la única vía de lectura del dataset desde entrenamiento.
- **FR-011.4** — CLI única `python -m uc3m.application.training.cli` con subcomandos por etapa; los launchers .bat/.ps1 delegan en ella.
- **FR-011.5** — Cada etapa rechaza la entrada si el hash del manifiesto previo no coincide.
- **FR-011.6** — Prueba de humo end-to-end con dataset reducido en `tests/acceptance/test_pipeline_smoke.py`.

## Criterios de aceptación

1. El humo end-to-end pasa sin red ni GPU.
2. Un cambio de un byte en el dataset bloquea el entrenamiento hasta revalidar.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-002, SPEC-003, SPEC-004
- Bloquea: SPEC-005
