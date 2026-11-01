# SPEC-009 — Levantamiento de observaciones del jurado

**Estado:** `pending`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Trazar cada observación J-01–J-17 hacia evidencia, corrección, prueba y artefacto, separando correcciones documentales, validaciones analíticas y experimentos nuevos.

## Requisitos funcionales

- **FR-009.1** — Manifiesto `data/audits/jury_observations_manifest.json` con ID, severidad, fuente, estado, evidencia, acción, responsable y criterio de cierre.
- **FR-009.2** — Única verdad estadística PE/OE/HE generada desde CSV de decisiones.
- **FR-009.3** — Contradicción HAPPO 49/50 resuelta con evidencia.
- **FR-009.4** — Ejes UC3M ejecutados separados de los propuestos.
- **FR-009.5** — Anexos de reproducibilidad, validez de datos, seguridad/privacidad y TRL.
- **FR-009.6** — Observaciones experimentales permanecen `pending_experiment` hasta producir artefactos.

## Criterios de aceptación

1. `run_jury_observations_gates.ps1` termina en 0.
2. Suma por estado coincide con el informe Markdown.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-005, SPEC-006
- Bloquea: aceptación integral
