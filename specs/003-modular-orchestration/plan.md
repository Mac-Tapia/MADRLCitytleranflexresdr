# Plan — SPEC-003

Contrato: [spec.md](spec.md). Fuente detallada: `docs/superpowers/plans/2026-10-31-orchestration-artifacts-plan.md`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Puertos faltantes con pruebas contractuales → Adaptador simulador CityLearn → Extraer reportes/figuras → Prueba de imports → Puerta de orquestación.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_orchestration_gates.ps1
```
