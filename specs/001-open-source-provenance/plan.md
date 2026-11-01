# Plan — SPEC-001

Contrato: [spec.md](spec.md). Fuente detallada: `docs/superpowers/plans/2026-10-31-foundation-open-source-spec-kit-plan.md (tareas 3–5)`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Reejecutar auditoría de dependencias → Resolver licencias ausentes sin inventarlas → Generar SBOM → Escaneo de secretos → Puerta de fundación.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_foundation_gates.ps1
```
