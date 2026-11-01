# SPEC-005 — Evaluación científica

**Estado:** `partial/pending_experiment`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Aceptar modelos solo por KPI independientes, Pareto y estadística multisemilla, nunca por recompensa acumulada ni por un `return_code=0`.

## Requisitos funcionales

- **FR-005.1** — KPI separados: costo, CO2, pico, rampas, factor de carga, autoconsumo PV, cumplimiento EV/BESS.
- **FR-005.2** — Hipervolumen, cobertura y dispersión del frente de Pareto.
- **FR-005.3** — Sensibilidad de pesos con tarifa, dataset, horizonte y semillas constantes.
- **FR-005.4** — Campaña 4×3 multisemilla en `configs/experiments/madrl_4x3_multiseed.yaml` con baselines.
- **FR-005.5** — Intervalos y pruebas estadísticas; `descriptive_leader` separado de `inferential_decision`.
- **FR-005.6** — Regla de selección explícita y evaluación independiente sin fuga.

## Criterios de aceptación

1. 12 tratamientos válidos con semillas declaradas y manifiestos verificables.
2. Informe estadístico reproducible; ningún líder descriptivo presentado como superior si p ≥ α.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-002, SPEC-003, SPEC-004, SPEC-011
- Bloquea: SPEC-006, SPEC-009
