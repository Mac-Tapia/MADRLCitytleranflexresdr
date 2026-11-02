# SPEC-002 — Política multiobjetivo única

**Estado:** `implemented` (dominio) / `partial` (adaptador)  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Una sola fuente tipada para `RewardVector`, `ObjectivePolicy` E1–E3, `TariffPolicy` y `ConstraintPolicy`, proyectada hacia CityLearn, launchers, notebooks y tesis sin duplicación activa.

## Requisitos funcionales

- **FR-002.1** — E1=[0.60,0.15,0.25], E2=[0.25,0.60,0.15], E3=[0.15,0.25,0.60]; suma 1, mayoría estricta, balance cíclico.
- **FR-002.2** — Etiqueta `compensatory_hierarchical_weighted_sum`; prohibido rotularla lexicográfica.
- **FR-002.3** — Pesos, tarifa y restricciones en objetos y fingerprints independientes; escenario compuesto rotulado.
- **FR-002.4** — Adaptador `uc3m/adapters/citylearn/objectives.py` proyecta la política sin que el dominio importe CityLearn.
- **FR-002.5** — EV/BESS fuera del simplex reportados como términos de servicio/restricción separados.
- **FR-002.6** — Detector de deriva sin ponderaciones activas duplicadas fuera de fixtures e historia.

## Criterios de aceptación

1. Pruebas de dominio y `tests/contract/multiobjective` pasan.
2. `tests/integration/test_citylearn_objective_adapter.py` pasa con cálculo idéntico al aceptado.
3. `data/audits/objective_policy_drift.json` sin fuentes activas duplicadas.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-001 (política de licencias)
- Bloquea: SPEC-003, SPEC-005, SPEC-006
