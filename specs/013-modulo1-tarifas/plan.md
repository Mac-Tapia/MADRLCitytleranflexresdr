# Plan — SPEC-013

Contrato: [spec.md](spec.md). Pasos TDD: [modulo1_tarifas.md](../../docs/plans/modulo1_tarifas.md).  
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`  
**Estado conciliado:** [STATUS](../STATUS.md)  
**Revisión:** 2026-11-04

## Secuencia

Dominio y extracción de PDF → Descarga e inmutabilidad → Contraste, herramienta y artefactos reales → Conexión con el constructor (bloqueada).

## Reglas

- Prueba roja antes de cada comportamiento nuevo; ninguna puerta crítica admite `skip` o `xfail`.
- `CityLearn/`, `external/` y `data/campaigns/` no se modifican.
- `tools/dataset/build_fresh_campaign_dataset.py` queda en solo lectura hasta que conste la cesión del Revisor A.
- Ejecutar `scripts/verify_project_context.ps1` antes de editar o usar Git; commits con rutas explícitas y solo con autorización.

## Verificación

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest -p no:cacheprovider -q tests/fresh_training/test_tariff_busbar.py
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/dataset/ingest_osinergmin_pba.py --offline
```
