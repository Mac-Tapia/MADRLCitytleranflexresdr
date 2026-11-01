# Plan — SPEC-011

Contrato: [spec.md](spec.md). Fuente detallada: `SPEC-000/FR-005 y solicitud del usuario de 2026-10-31 (flujo completo desde la creación del dataset)`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Inventariar scripts de tools/dataset y clasificar activos/obsoletos → Manifiesto por frontera → CLI por etapas → Humo end-to-end.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
python -m pytest -q tests/acceptance/test_pipeline_smoke.py
```
