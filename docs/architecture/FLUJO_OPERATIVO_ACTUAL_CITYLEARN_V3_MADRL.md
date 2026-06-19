# Flujo operativo actual CityLearn v3 MADRL

Actualizado: 2026-06-17
Fuente machine-readable: `docs/workflow_manifest.json`

Este documento fija el flujo vigente del proyecto desde la creacion del dataset hasta los resultados finales. Reemplaza referencias historicas a carpetas fijas como `outputs/citylearn_v3_madrl_oficial_v4`, `outputs/citylearn_v3_madrl_oficial_v5` o relanzamientos con fecha 20260602.

## Estado de Corridas Oficiales (2026-06-17)

| Corrida | Ruta | Estado | Inicio | Fin | Notas |
|---|---|:---:|---|---|---|
| v3 | `outputs/citylearn_v3_madrl_full_20260613_010234` | **COMPLETADA** | 2026-06-15 00:46 | 2026-06-15 06:20 | 12/12 jobs exitosos. HAPPO+MASAC preexistentes. MATD3+MAAC completados. Perfil recompensa v3. |
| v4 | `outputs/citylearn_v3_madrl_full_20260615_074011_v4` | **COMPLETADA** | 2026-06-15 07:40 | 2026-06-16 22:44 | Re-run definitivo con penalidad BESS + urgencia EV. 12/12 jobs exitosos; artefactos canónicos reparados y sin duplicados raíz. |

La corrida v4 es el re-run definitivo con la funcion de recompensa actualizada (penalidad degradacion BESS C-rate/Arrhenius + urgencia EV). Los KPIs de tesis deben tomarse de v4, siempre desde los artefactos canónicos bajo `data/`.

## Tiempos Reales por Algoritmo (GPU RTX 4060 Laptop 8 GB, 5 episodios 8760 pasos)

| Algoritmo | Escenario | Concurrencia | Duracion real | Corrida fuente |
|---|---|:---:|:---:|---|
| HAPPO | E1 | paralelo con E2 | 66.5 min | v4 |
| HAPPO | E2 | paralelo con E1 | 66.15 min | v4 |
| HAPPO | E3 | secuencial | 57.75 min | v4 |
| MASAC | E1 | secuencial | 125.88 min | v4 |
| MASAC | E2 | secuencial | 148.33 min | v4 |
| MASAC | E3 | secuencial | 135.72 min | v4 |
| MATD3 | E1 | paralelo con E2 | 95.13 min | v3 |
| MATD3 | E2 | paralelo con E1 | 95.30 min | v3 |
| MATD3 | E3 | secuencial | 80.70 min | v3 |
| MAAC | E1 | secuencial | 52.33 min | v3 |
| MAAC | E2 | secuencial | 51.74 min | v3 |
| MAAC | E3 | secuencial | 54.16 min | v3 |

**Tiempo total estimado para corrida completa:** ~10-11 horas en RTX 4060 Laptop (HAPPO ~3h, MASAC ~5h, MATD3 ~4.5h paralelo, MAAC ~2.7h).

## Regla Canonica

La corrida activa se obtiene asi:

1. Leer `outputs/latest_visible_training_output_root.txt`.
2. Si no existe, usar la carpeta mas reciente en `outputs/` que contenga `official_full_status.json` con `status = completed`.
3. No reportar KPIs finales si `official_full_status.json` no esta en `completed` o si falta algun artefacto requerido por job.

La salida recomendada para nuevos lanzamientos es:

```text
outputs/citylearn_v3_madrl_full_<yyyyMMdd_HHmmss>
```

## Flujo Completo

```text
verify_project_context.ps1
  -> tools/orchestrate_citylearn_dataset.py
  -> outputs/dataset_audit/*
  -> check_training_dataset_ready.py
  -> run_citylearn_v3_env_smoke.py
  -> launch_citylearn_v3_official_training.ps1 / run_citylearn_v3_full_training_visible.ps1
  -> official_full_status.json + live_progress.json transitorio + logs
  -> data/results.json + data/timeseries.csv + data/trace.csv
  -> figures/ + figures/tables/
  -> benchmark_citylearn_v2_agents.py
  -> compare_citylearn_v2_vs_v3_madrl.py
  -> generate_thesis_objective_evidence.py
```

## Dataset

El dataset activo es:

```text
CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json
```

Auditorias canonicas:

- `outputs/dataset_audit/training_dataset_ready_manifest.json`
- `outputs/dataset_audit/csv_integrity_manifest.json`
- `outputs/dataset_audit/training_dataset_validation.json`
- `outputs/dataset_audit/der_sizing_audit.json`
- `outputs/dataset_audit/ev_charger_sizing_audit.json`
- `outputs/dataset_audit/workflow_integrity_manifest.json`

Estado auditado vigente:

- 17 edificios, 26,304 horas y 222 CSV activos sin NaN/Inf.
- 185 tomas EV Mode 3, 96 equipos fisicos doble toma, 1,850 EV en pool y 749.4 kW nominales.
- BESS recalculado despues de EV: 26,266 kWh / 6,648 kW.
- PV vigente: 48,790.9 kWp con PVGIS TMY/pvlib.

Comandos:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\orchestrate_citylearn_dataset.py `
  --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\check_training_dataset_ready.py `
  --manifest-out outputs\dataset_audit\training_dataset_ready_manifest.json
```

## Carga y Smoke

Antes de entrenar se debe comprobar que CityLearn carga el dataset crudo:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\check_citylearn_v3_training_ready.py `
  --strict `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1

.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\run_citylearn_v3_env_smoke.py `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1 `
  --episode-time-steps 8760 `
  --steps 3

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\verify_workflow_integrity.py `
  --manifest-out outputs\dataset_audit\workflow_integrity_manifest.json
```

Los smoke tests con `episode_time_steps=4` pueden no representar el episodio anual completo y no deben usarse como evidencia de entrenamiento final.

## Entrenamiento

Lanzamiento visible recomendado (usar `pwsh.exe` — PowerShell 7, validado para la ruta operativa):

```powershell
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$root = "outputs\citylearn_v3_madrl_full_$ts"
Set-Content outputs\latest_visible_training_output_root.txt $root -Encoding UTF8

pwsh.exe -NoProfile -ExecutionPolicy Bypass `
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
  -Cuda
```

Nota: el script `scripts\run_citylearn_v3_full_training_visible.ps1` es el wrapper visible raiz. Internamente invoca `CityLearn\scripts\launch_citylearn_v3_official_training.ps1`.

Contrato:

- 4 algoritmos: HAPPO, MASAC, MATD3 y MAAC.
- 3 escenarios: E1 flexibilidad, E2 CO2, E3 costos.
- 12 jobs: `4 x 3`.
- 5 episodios por job.
- 8760 pasos por episodio.
- 43800 pasos de entorno por job.
- CUDA activo con perfil `local4060_fast` (RTX 4060 Laptop, 8188 MiB, driver 560.94).
- Torch 2.8.0+cu126.
- Fraccion CUDA efectiva: 0.812 (`cuda_memory_fraction`).
- Artefactos `efficient`, traza compacta cada 10 pasos.

En RTX 4060 Laptop 8 GB, el launcher no fuerza toda la concurrencia a 1 por VRAM: el modo operativo usa monitor visible y permite hasta 2 escenarios concurrentes, manteniendo MASAC/MAAC en 1 por ser etapas pesadas. Si se activa `LiveOutput`, solo ese modo de display rico ejecuta en secuencia para mantener una salida legible.

## Monitor y Estado

Monitor:

```powershell
$root = Get-Content outputs\latest_visible_training_output_root.txt
powershell -NoProfile -ExecutionPolicy Bypass `
  -File CityLearn\scripts\monitor_citylearn_v3_official_training.ps1 `
  -OutputRoot $root `
  -IntervalSeconds 5 `
  -LogTail 12
```

Archivos de estado:

- `<OutputRoot>/official_full_status.json`
- `<OutputRoot>/official_full_manifest.json`
- `<OutputRoot>/<algo>/<scenario>_seed_0/live_progress.json` solo mientras el job esta activo
- `<OutputRoot>/logs/*.log`
- `<OutputRoot>/logs/*.stderr.log`

## Artefactos Requeridos Por Job

Cada job valido debe producir:

```text
<OutputRoot>/<algo>/<scenario>_seed_0/
  data/results.json
  data/training_summary.json
  data/timeseries.csv
  data/trace.csv
  data/checkpoint_manifest.json
  data/artifact_audit.json
  checkpoints/
  figures/figures_manifest.json
  figures/tables/
```

No se aceptan duplicados raíz (`results.json`, `timeseries.csv`, `trace.csv`, etc.) como fuente primaria. La ruta `data/` es canónica; `statistical_comparison/` y espejos raíz solo se generan con flags heredados explícitos.

Figuras esperadas:

- `reward_timeseries.png`
- `convergence_returns.png`
- `episode_reward_summary.png`
- `learning_efficiency.png`
- `citylearn_v2_district_timeseries.png`
- `axis_baseline_comparison.png`
- `baseline_gain_by_kpi.png`
- `core_kpis.png`
- `OE1_flexibility_kpis.png`
- `OE2_co2_kpis.png`
- `OE3_cost_kpis.png`

## Comparacion Final

Benchmark v2 (el script usa por defecto el dataset Iquitos `citylearn_iquitos_2023_2025/schema.json`):

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\benchmark_citylearn_v2_agents.py `
  --scenario ALL `
  --episode-time-steps 8760 `
  --agents baseline hour_rbc `
  --output-dir outputs\citylearn_v2_original_benchmark `
  --continue-on-error
```

Comparador v2 vs v3:

```powershell
$root = Get-Content outputs\latest_visible_training_output_root.txt
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\compare_citylearn_v2_vs_v3_madrl.py `
  --v2-root outputs\citylearn_v2_original_benchmark `
  --v3-root $root `
  --output-dir outputs\comparison_citylearn_v2_vs_v3_madrl `
  --scenario ALL `
  --seed 0 `
  --auto-benchmark-v2 `
  --v2-agents baseline hour_rbc `
  --weights OE1=0.34,OE2=0.33,OE3=0.33
```

## Evidencia de Tesis

Cuando los 12 jobs esten completos:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\generate_thesis_objective_evidence.py
```

Salida:

```text
outputs/thesis_objective_evidence/
  resumen_evidencia_tesis.md
  matriz_resultados_madrl.csv
  scores_kpi_algoritmo_madrl.csv
  analisis_estadistico_madrl.csv
  comparaciones_mwu_madrl.csv
  comparaciones_wilcoxon_madrl.csv
  hipotesis_estadisticas_madrl.csv
  thesis_skill_feed.json
```

## Archivos Obsoletos o Historicos

No usar como fuente canonica de resultados finales:

- `outputs/citylearn_v3_madrl_oficial_v4`
- `outputs/citylearn_v3_madrl_oficial_v5`
- `outputs/citylearn_v3_madrl_official_full_cuda_v2`
- `outputs/citylearn_v3_madrl_iquitos_official_full_cuda_visible_relaunch_20260602_222217`
- `outputs/bottleneck_probe_*`
- `outputs/bottleneck_dryrun_*`

Estos pueden conservarse para auditoria historica, pero los KPIs finales deben salir solo de la corrida activa/completa indicada por `outputs/latest_visible_training_output_root.txt`.

## Corridas de Referencia Validas

| Corrida | Ruta | Perfil recompensa | Uso |
|---|---|---|---|
| v3 (referencia) | `outputs/citylearn_v3_madrl_full_20260613_010234` | v3 base | Referencia de 12 jobs completos. HAPPO+MASAC con perfil anterior, MATD3+MAAC con perfil v3. |
| v4 (definitiva) | `outputs/citylearn_v3_madrl_full_20260615_074011_v4` | v4 BESS penalty + EV urgency | Re-run completo con funcion de recompensa definitiva. KPIs de tesis desde `data/` canónico. |

La corrida v4 usa la funcion de recompensa definitiva de la tesis con penalidad de degradacion BESS (C-rate + Arrhenius LiFePO4) y urgencia EV. Es la unica fuente valida para los KPIs finales de comparacion de la tesis.

## Criterio de Resultado Final

Un resultado final es aceptable solo si:

- `official_full_status.json` tiene `status = completed`.
- Los 12 jobs tienen `exit_code = 0`.
- Cada job tiene todos los artefactos requeridos.
- No hay `Traceback`, `CUDA out of memory`, `RuntimeError` critico ni interrupcion externa en logs.
- El benchmark v2 y el comparador v2-v3 generaron sus tablas y figuras.
- La evidencia de tesis se genero desde esos artefactos, no desde runs historicos.
