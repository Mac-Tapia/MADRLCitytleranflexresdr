# Plan — SPEC-005

Contrato: [spec.md](spec.md). Fuente detallada: `docs/plans/objetivos.md (tareas 6–8) y plan del jurado (tarea 5)`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Matriz 12/12 sin entrenamiento largo → Configuración de campaña → Ejecución aprobada → Informe estadístico → Selección.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
python -m pytest -q tests/contract/multiobjective tests/contract/training tests/acceptance
```
