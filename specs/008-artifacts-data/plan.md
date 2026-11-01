# Plan — SPEC-008

Contrato: [spec.md](spec.md). Fuente detallada: `docs/decisions/ADR-OPEN-ARTIFACT-STORE.md y plan de orquestación (tarea 10)`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Inventario de tamaño → Política de retención → Prueba de respaldo/restauración → Reglas .gitignore.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
python -m pytest -q tests/unit/adapters tests/integration
```
