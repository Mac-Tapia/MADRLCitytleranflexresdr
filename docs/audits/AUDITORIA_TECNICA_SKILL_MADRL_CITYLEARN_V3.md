# Auditoria Tecnica Vigente CityLearn v3 MADRL

**Fecha:** 2026-06-12 (actualizada tras inspeccion completa)
**Proyecto:** `MADRLCitytleranflexresdr`
**Dataset activo:** `citylearn_iquitos_2023_2025`
**Salida activa:** `outputs/latest_visible_training_output_root.txt` → `outputs\citylearn_v3_madrl_oficial_v6`

## Resultado Principal

**Infraestructura lista para entrenamiento. Sin cuellos de botella tecnicos.**

El entrenamiento previo (HAPPO E1, sesion `v6`) fue **interrumpido en paso 3,000/43,800** (episodio 0, ~34% del primer episodio). La GPU RTX 4060 esta libre (0 MiB en uso). El dataset, entorno, reward function y todos los scripts de validacion estan operativos y pasan todas las comprobaciones.

Estado de la sesion `v6`:

- `official_full_status.json` → status: "running" (stale — proceso terminado)
- Solo HAPPO/E1 fue lanzado; MASAC, MATD3, MAAC y los escenarios E2/E3 pendientes
- Los datos de `live_progress.json` confirman que la recompensa opera correctamente: reward_mean=-0.619, carbono=0.790 kg/kWh, perfiles de eje activos

Para nuevo entrenamiento: lanzar con `run_citylearn_v3_full_training_visible.ps1` o `launch_citylearn_v3_official_training.ps1 -Scenario ALL`. El launcher creara una nueva sesion `v7` o sobrescribira `v6`.

## Configuracion Vigente

| Parametro | Valor |
|---|---:|
| Dataset | `citylearn_iquitos_2023_2025` |
| Escenarios | E1, E2, E3 |
| Algoritmos | HAPPO, MASAC, MATD3, MAAC |
| Episodios por corrida | 5 |
| Pasos por episodio | 8,760 |
| Seed | 0 |
| CUDA | True |
| Perfil GPU | `local4060_fast` |
| Torch threads | 8 |
| LiveOutput por defecto | False |
| Paralelismo de escenarios | True |
| Max escenarios concurrentes | 2 |
| Max etapas pesadas MASAC/MAAC | 1 |
| Output root | `<OutputRoot>` resuelto desde `outputs/latest_visible_training_output_root.txt` |

## Dataset Validado

| Componente | Valor |
|---|---:|
| CSV activos auditados | 222 |
| NaN/Inf | 0 |
| Edificios | 17 |
| Cargadores EV | 185 |
| Unidades fisicas Mode 3 | 96 |
| EV en pool de simulacion | 1,850 |
| Maquinas controladas | 17 |
| PV total | 48,790.9 kWp |
| BESS total | 26,266.0 kWh / 6,648.0 kW |

Manifiestos de control:

- `outputs/dataset_audit/csv_integrity_manifest.json`
- `outputs/dataset_audit/training_dataset_ready_manifest.json`
- `outputs/dataset_audit/der_sizing_audit.csv`
- `outputs/dataset_audit/ev_charger_sizing_audit.csv`

## Ajustes Aplicados

- El dataset se construye por orquestacion con `tools/orchestrate_citylearn_dataset.py`.
- La validacion acepta cargadores EV con estados activos del esquema vigente.
- Las maquinas controladas se detectan como `Washing_Machine_*.csv` por edificio.
- Los reportes de dataset usan conteos dinamicos de cargadores y maquinas; no quedan conteos fijos antiguos en esos scripts.
- Los documentos vigentes ya no deben usar corridas largas externas ni artefactos historicos como evidencia del proyecto actual.

## Reglas Operativas

1. Antes de editar o hacer operaciones Git, ejecutar `scripts\verify_project_context.ps1`.
2. No usar rutas ni artefactos de `D:\madrl_lima`.
3. No reportar KPIs finales si no existen `results.json`, `timeseries.csv` y `trace.csv` para el algoritmo y escenario.
4. No normalizar ni entrenar antes de que el dataset completo real este auditado.
5. No editar `CityLearn/` ni `external/` salvo solicitud explicita.

## Verificacion Recomendada

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1
python tools/audit_citylearn_csv_integrity.py
python CityLearn\scripts\check_citylearn_v3_training_ready.py --strict --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E1
```

El entrenamiento vigente debe producir, por cada MADRL y escenario, estos artefactos:

```text
data/results.json
data/timeseries.csv
data/trace.csv
```
