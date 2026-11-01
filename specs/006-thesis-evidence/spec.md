# SPEC-006 — Evidencia de tesis

**Estado:** `pending`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Tablas, figuras, cifras y citas de la tesis se generan únicamente desde evidencia promovida; §3.1.3 concentra la coordinación multiobjetivo sin contradicciones.

## Requisitos funcionales

- **FR-006.1** — Registro de evidencia promovida en `uc3m/application/thesis/evidence_registry.py` y `docs/thesis/evidence_registry.yaml`.
- **FR-006.2** — Vista multiobjetivo trazable generada por `tools/thesis/build_multiobjective_evidence.py`.
- **FR-006.3** — §3.1.3 coherente con la política canónica; búsqueda de pesos obsoletos sin hallazgos activos.
- **FR-006.4** — Bibliografía APA 7 verificada en `docs/research/multiobjective_sources.yaml`.
- **FR-006.5** — Respaldo, reapertura y render de los DOCX canónicos antes de aceptar.

## Criterios de aceptación

1. `run_thesis_agent_gates.ps1` termina en 0.
2. Ninguna cifra de tesis sin procedencia verificable.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-005
- Bloquea: SPEC-009
