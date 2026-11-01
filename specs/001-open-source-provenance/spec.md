# SPEC-001 — Cadena abierta y procedencia

**Estado:** `partial/blocked`  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Propósito

Garantizar que toda dependencia requerida tenga licencia OSI verificada, procedencia fijada a commit y que ningún servicio cerrado, de pago o secreto forme parte del flujo requerido.

## Requisitos funcionales

- **FR-001.1** — Política `governance/open_source_policy.yaml` evaluada por `uc3m/governance/open_source.py`; licencia ausente o ambigua bloquea.
- **FR-001.2** — Inventario de paquetes Python, submódulos y `external/` con SPDX, commit y propósito en `data/audits/open_source_dependency_manifest.json`.
- **FR-001.3** — SBOM local (CycloneDX o SPDX) generado sin red obligatoria.
- **FR-001.4** — Registro de repositorios de investigación rechazados (C-MORL, código SustainGym) con URL y causa en `docs/research/repository_registry.yaml`.
- **FR-001.5** — Escaneo de secretos y servicios cerrados con clasificación `critical`/`excluded_legacy`/`documentation_only`.

## Criterios de aceptación

1. `run_foundation_gates.ps1` termina en 0 sin dependencias requeridas de licencia desconocida.
2. Las tres licencias locales ausentes y las dos revisiones copyleft quedan resueltas o la dependencia queda fuera del flujo requerido.
3. Ningún secreto, perfil de navegador ni estado OAuth versionado.

Un `return_code=0`, un smoke o la convergencia numérica no cierran este SPEC.

## Dependencias

- Requiere: SPEC-000
- Bloquea: SPEC-000/FR-007, SPEC-005, SPEC-012
