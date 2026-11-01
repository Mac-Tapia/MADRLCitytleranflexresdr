# Plan — SPEC-002

Contrato: [spec.md](spec.md). Fuente detallada: `docs/superpowers/plans/2026-10-31-multiobjective-domain-plan.md`.  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Diseño:** [aprobado](../../docs/superpowers/specs/2026-10-31-modernizacion-integral-open-source-design.md) · **Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-10-31

## Secuencia

Contrato de adaptador (prueba roja) → Adaptador CityLearn → Registro de contribución en docs/contributions/CityLearn/CHANGES.md → Auditoría de deriva.

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/` y `external/` solo mediante adaptadores y con contribución registrada.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits pequeños por tarea.

## Verificación

```powershell
python -m pytest -q tests/unit/domain tests/contract/multiobjective
```
