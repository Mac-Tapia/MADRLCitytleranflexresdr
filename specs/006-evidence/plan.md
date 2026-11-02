# Plan — SPEC-006

Contrato: [spec.md](spec.md). Fuente detallada: `docs/plans/agentes.md (tareas 1–4, 9)`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Registro de evidencia → Vista multiobjetivo → Consolidar §3.1.3 → APA → Render y comparación DOCX.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
powershell -ExecutionPolicy Bypass -File scripts/quality/run_thesis_agent_gates.ps1
```
