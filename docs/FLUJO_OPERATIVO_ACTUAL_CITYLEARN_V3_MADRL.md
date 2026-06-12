# Flujo operativo actual CityLearn v3 MADRL

Actualizado: 2026-06-12
Fuente machine-readable: `docs/workflow_manifest.json`

Este documento fija el flujo vigente del proyecto desde la creacion del dataset hasta los resultados finales. Reemplaza referencias historicas a carpetas fijas como `outputs/citylearn_v3_madrl_oficial_v4`, `outputs/citylearn_v3_madrl_oficial_v5` o relanzamientos con fecha 20260602.

## Regla Canonica

La corrida activa se obtiene asi:

1. Leer `outputs/latest_visible_training_output_root.txt`.
2. Si no existe, usar la carpeta mas reciente en `outputs/` que contenga `official_full_status.json`.
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
  -> official_full_status.json + live_progress.json + logs
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

Comandos:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\orchestrate_citylearn_dataset.py `
  --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\check_training_dataset_ready.py --strict
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
```

Los smoke tests con `episode_time_steps=4` pueden no representar el episodio anual completo y no deben usarse como evidencia de entrenamiento final.

## Entrenamiento

Lanzamiento visible recomendado:

```powershell
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$root = "outputs\citylearn_v3_madrl_full_$ts"
Set-Content outputs\latest_visible_training_output_root.txt $root -Encoding UTF8

powershell -NoProfile -ExecutionPolicy Bypass `
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
  -Cuda `
  -LiveOutput
```

Contrato:

- 4 algoritmos: HAPPO, MASAC, MATD3 y MAAC.
- 3 escenarios: E1 flexibilidad, E2 CO2, E3 costos.
- 12 jobs: `4 x 3`.
- 5 episodios por job.
- 8760 pasos por episodio.
- 43800 pasos de entorno por job.
- CUDA activo con perfil `local4060_fast`.
- Artefactos `efficient`, traza compacta cada 10 pasos.

En RTX 4060 Laptop 8 GB, el launcher activa modo seguro de VRAM y puede fijar concurrencia efectiva en 1. Si se usa `LiveOutput`, el modo visible tambien fuerza ejecucion secuencial para mantener una salida legible.

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
- `<OutputRoot>/<algo>/<scenario>_seed_0/live_progress.json`
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
  checkpoints/
  figures/figures_manifest.json
  figures/tables/
```

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

Benchmark v2:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\benchmark_citylearn_v2_agents.py `
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
  --scenario E3 `
  --seed 0 `
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

## Criterio de Resultado Final

Un resultado final es aceptable solo si:

- `official_full_status.json` tiene `status = completed`.
- Los 12 jobs tienen `exit_code = 0`.
- Cada job tiene todos los artefactos requeridos.
- No hay `Traceback`, `CUDA out of memory`, `RuntimeError` critico ni interrupcion externa en logs.
- El benchmark v2 y el comparador v2-v3 generaron sus tablas y figuras.
- La evidencia de tesis se genero desde esos artefactos, no desde runs historicos.
