# Plan — SPEC-012

Contrato: [spec.md](spec.md). Fuente detallada: `Solicitud del usuario de 2026-10-31: proyecto limpio, sin archivos sueltos, duplicados u obsoletos y sin etiquetas de agentes`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/design/modernizacion.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Decisión sobre el Stop hook → Inventario y manifiesto de limpieza → Renombrados con git mv → Retirar temporales del índice → Prueba de higiene.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
python -m pytest -q tests/ops/test_repository_hygiene.py
```
