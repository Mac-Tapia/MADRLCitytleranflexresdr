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

## Sustento

Consultado el 2026-11-01 en el cuaderno NotebookLM del proyecto (34 fuentes). NotebookLM se usó como herramienta de búsqueda, no como fuente: cada afirmación debe citarse al documento primario antes de llevarla a la tesis.

| Decisión | Fuentes | Qué sostienen | Verificado en la fuente primaria |
| --- | --- | --- | --- |
| Fijar el contenido exacto del dataset antes de comparar algoritmos | Hu et al. (2023), MARLlib, *JMLR*; Nweye, Liu, Stone & Nagy (2022), *Energy and AI* | En MARL los entornos son muy configurables y una variación no controlada de los datos impide comparar algoritmos; se piden entornos y datasets estandarizados | No |
| Separar entrenamiento y evaluación en el tiempo, sin contaminación entre ventanas | Nweye, Sankaranarayanan & Nagy (2023), MERLIN, *Applied Energy*; Nweye (2024), tesis doctoral, UT Austin | Particiones temporales disjuntas y evaluación en meses no vistos | No; el detalle "entrenar agosto–diciembre y evaluar enero–julio" lo dio NotebookLM y debe comprobarse |
| Procedencia de los datos de edificios | Nweye et al. (2024), CityLearn v2, *Journal of Building Performance Simulation* | Los datos de CityLearn v2 derivan de perfiles de carga estandarizados y mediciones reales | No |

Límite: estas fuentes fundamentan la reproducibilidad y la separación de datos. **No prescriben** un hash SHA-256: el digest es la decisión de ingeniería de este proyecto para hacer cumplir esas condiciones.
