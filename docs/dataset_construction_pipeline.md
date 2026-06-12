# Construccion Vigente del Dataset CityLearn v3 Iquitos 2023-2025

**Proyecto:** `MADRLCitytleranflexresdr`
**Dataset activo:** `citylearn_iquitos_2023_2025`
**Ultima actualizacion:** 2026-06-12
**Fuente canonica dataset:** `python tools/orchestrate_citylearn_dataset.py`
**Fuente canonica flujo completo:** `docs/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md`

Este documento reemplaza las tablas historicas del pipeline. La fuente valida del dataset es la orquestacion actual y sus auditorias en `outputs/dataset_audit/`; no se deben usar resultados, conteos ni salidas de corridas antiguas.

## Estado Vigente

| Componente | Valor validado |
|---|---:|
| Edificios reales | 17 |
| Horizonte horario | 26,304 horas (2023-2025) |
| CSV auditados | 222 |
| Celdas NaN/Inf | 0 |
| Cargadores EV controlables | 185 |
| Unidades fisicas Mode 3 | 96 |
| Sockets Mode 3 | 192 |
| Potencia EV instalada | 749.4 kW |
| PV instalado | 48,790.9 kWp |
| Energia PV anualizada 2023-2025 | 148,802.2 MWh |
| BESS instalado | 26,266.0 kWh / 6,648.0 kW |
| Maquinas controladas | 17 |
| Energia anualizada de maquinas controladas | 876.6 MWh |

Auditorias vigentes:

- `outputs/dataset_audit/csv_integrity_manifest.json`
- `outputs/dataset_audit/training_dataset_ready_manifest.json`
- `outputs/dataset_audit/der_sizing_audit.csv`
- `outputs/dataset_audit/ev_charger_sizing_audit.csv`
- `outputs/dataset_audit/training_dataset_validation.csv`

## Orden Correcto de Ejecucion

1. `powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1`
2. `python tools/orchestrate_citylearn_dataset.py`
3. `python tools/audit_citylearn_csv_integrity.py`
4. `python CityLearn\scripts\check_citylearn_v3_training_ready.py --strict --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E1`
5. `python CityLearn\scripts\run_citylearn_v3_env_smoke.py --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json --scenario E1 --episode-time-steps 4 --steps 3`

La normalizacion y el entrenamiento solo deben iniciarse despues de que el dataset real completo este generado, sincronizado y auditado.

## Reglas de Orquestacion

El orquestador debe mantener sincronizados estos bloques antes de entregar el dataset a CityLearn v3:

- `weather.csv`, `carbon_intensity.csv`, `pricing.csv`
- `Building_1.csv` a `Building_17.csv`
- `charger_X_Y.csv` para 185 tomas EV controlables
- `Washing_Machine_1.csv` a `Washing_Machine_17.csv`
- `schema.json`
- auditorias de integridad, DER, EV y readiness

El dimensionamiento BESS usa balance por edificio con generacion solar, carga del edificio, carga EV, cargas controladas y red publica. La generacion solar prioriza carga EV y carga del edificio; el BESS prioriza recarga EV en la ventana operativa de cada edificio hasta el horario de cierre. Todos los calculos son individuales por edificio.

## Archivos Generados

```text
CityLearn/data/datasets/citylearn_iquitos_2023_2025/
  schema.json
  weather.csv
  carbon_intensity.csv
  pricing.csv
  Building_1.csv ... Building_17.csv
  charger_*.csv                 # 185 archivos
  Washing_Machine_*.csv          # 17 archivos
```

## Entrenamiento Oficial Vigente

La corrida vigente usa GPU local. El `OutputRoot` activo debe tomarse de `outputs/latest_visible_training_output_root.txt`; para una corrida nueva:

```powershell
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$root = "outputs\citylearn_v3_madrl_full_$ts"
Set-Content outputs\latest_visible_training_output_root.txt $root -Encoding UTF8

powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts\run_citylearn_v3_full_training_visible.ps1 `
  -OutputRoot $root `
  -Scenario ALL `
  -Seed 0 `
  -EpisodeTimeSteps 8760 `
  -Episodes 5 `
  -TorchThreads 8 `
  -LiveProgressInterval 1000 `
  -ArtifactProfile efficient `
  -TraceRecordInterval 10 `
  -TraceDetail compact `
  -GpuProfile local4060_fast `
  -LiveOutput `
  -Cuda
```

Cada corrida valida debe producir:

```text
<OutputRoot>/<madrl>/<scenario>_seed_0/
  data/results.json
  data/timeseries.csv
  data/trace.csv
```

No se deben reportar KPIs de entrenamiento si esos tres artefactos no existen para el algoritmo y escenario correspondiente.
