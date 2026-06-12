# Estrategia MADRL: 3 Ejes CityLearn v3

## Flexibilidad Energetica + Emisiones de CO2 + Costos Energeticos

Ultima actualizacion: 2026-06-12

---

## 1. Estado Actual del Proyecto

El proyecto queda organizado como una capa experimental **CityLearn v3 MADRL** sobre el simulador **CityLearn v2**. CityLearn v2 sigue siendo la fuente oficial para:

- datasets y `schema.json`;
- fisica de edificios;
- baterias, PV y EVs;
- espacios de observacion y accion;
- evaluacion con `evaluate_v2`;
- KPIs base de comparacion contra linea base.

La capa v3 agrega:

- entorno descentralizado tipo **Dec-POMDP**;
- entrenamiento **CTDE**: centralized training, decentralized execution;
- 17 edificios + EV para el caso de tesis;
- soporte generico para otros datasets CityLearn v2;
- 4 backends MADRL oficiales: HAPPO, MASAC, MATD3 y MAAC;
- reporte multiobjetivo por tres ejes;
- artefactos reproducibles por corrida: datos tecnicos, checkpoints, figuras, graficas y cuadros.

La fuente operativa vigente del flujo completo esta en `docs/FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md` y `docs/workflow_manifest.json`. Para resultados de entrenamiento, no se fija una carpeta historica como canonica: se usa `outputs/latest_visible_training_output_root.txt` o, si no existe, el output mas reciente con `official_full_status.json`.

### Sustento cientifico integrado

El proyecto incluye el skill versionado `tools/skills/madrl-citylearn-literature-review/` como soporte directo para la revision bibliografica sistematica de la implementacion CityLearn v3 MADRL propuesta.

Tambien incluye el skill exclusivo del proyecto `tools/skills/madrl-citylearn-thesis-integrated/`, orientado a convertir la matriz bibliografica, los KPIs, la arquitectura y los resultados del proyecto en un informe de tesis de Maestria de Especializacion o Profesionalizante bajo la estructura 5.1 de la Guia N. 02, con citas y referencias APA vigentes.

Para el **Plan de Tesis**, el proyecto incluye el skill exclusivo `tools/skills/madrl-citylearn-thesis-plan/`. Este recurso trabaja con dos modulos conectados: busqueda bibliografica verificable y redaccion del Plan de Tesis bajo la estructura 5.1 de la Guia N. 01, incluyendo datos generales, planteamiento del problema, objetivos, marco teorico, diseno metodologico, cronograma, presupuesto, financiamiento, referencias APA y anexos.

Este recurso fija reglas terminologicas y metodologicas para:

- mantener **MADRL** como enfoque principal de la tesis;
- diferenciar **CityLearn v2** como entorno base existente y **CityLearn v3 propuesto** como extension experimental de la investigacion;
- analizar HAPPO, MASAC, MATD3 y MAAC como backends MADRL;
- incorporar MARLlib solo como nombre propio de framework de referencia;
- construir una matriz Excel de 50 investigaciones con trazabilidad de DOI, PDF, dataset, GitHub, KPIs, metodologia y aplicabilidad al SEAI Iquitos;
- preservar la hoja `Marco_metodologico_MADRL`, evitando la denominacion incorrecta `Marco_metodologico_MARL`.

La plantilla de Excel se genera con:

```powershell
python tools\skills\madrl-citylearn-literature-review\scripts\create_workbook_template.py `
  --output outputs\sustento_cientifico\revision_bibliografica_madrl_citylearn.xlsx
```

La plantilla integrada para tesis se genera con:

```powershell
python tools\skills\madrl-citylearn-thesis-integrated\scripts\create_integrated_thesis_workbook.py `
  --output outputs\sustento_cientifico\tesis_integrada_madrl_citylearn.xlsx

python tools\skills\madrl-citylearn-thesis-integrated\scripts\create_thesis_docx_skeleton.py `
  --output outputs\sustento_cientifico\informe_tesis_madrl_citylearn_esqueleto.docx
```

La plantilla para Plan de Tesis se genera con:

```powershell
python tools\skills\madrl-citylearn-thesis-plan\scripts\create_plan_workbook.py `
  --output outputs\sustento_cientifico\plan_tesis_madrl_citylearn_matriz.xlsx

python tools\skills\madrl-citylearn-thesis-plan\scripts\create_plan_docx_skeleton.py `
  --output outputs\sustento_cientifico\plan_tesis_madrl_citylearn_esqueleto.docx
```

---

## 2. Ejes y Objetivos Vigentes

### OE1: Flexibilidad Energetica

**Objetivo:** aumentar la capacidad de desplazar cargas y aprovechar almacenamiento, EVs y autoconsumo en comunidades de edificios interactivos con la red electrica.

KPIs CityLearn v2 usados en este eje:

- forma de carga e importacion desde red:
  - `grid_import`
  - `grid_import_control`
  - `grid_import_baseline`
  - `grid_import_delta`
  - `zero_net_energy`
  - `net_exchange_control`
  - `net_exchange_baseline`
  - `net_exchange_delta`
  - `grid_export_ratio`
  - `grid_export_control`
  - `grid_export_baseline`
  - `grid_export_delta`
- capacidad de desplazamiento:
  - `peak_average`
  - `ramping_average`
  - `one_minus_load_factor_average`
- PV y autoconsumo:
  - `pv_generation_total`
  - `pv_generation_daily_average`
  - `pv_export_total`
  - `pv_export_daily_average`
  - `pv_self_consumption_ratio`
- mercado/comunidad local cuando el dataset lo expone:
  - `community_local_traded_total`
  - `community_local_traded_daily_average`
  - `community_import_share`
- baterias:
  - `battery_charge_total`
  - `battery_discharge_total`
  - `battery_throughput_total`
  - `battery_equivalent_full_cycles`
  - `battery_capacity_fade_ratio`
- EVs:
  - `ev_departure_count`
  - `ev_departure_met_count`
  - `ev_departure_within_tolerance_count`
  - `ev_departure_success_rate`
  - `ev_departure_within_tolerance_rate`
  - `ev_departure_soc_deficit_mean`
  - `ev_charge_total`
  - `ev_v2g_export_total`

### OE2: Emisiones de CO2

**Objetivo:** reducir la huella ambiental del distrito, minimizando importaciones en horas de alta intensidad de carbono.

KPIs CityLearn v2 usados en este eje:

- `carbon_emissions`: ratio de emisiones contra linea base.
- `carbon_emissions_control`: emisiones totales del control en kgCO2.
- `carbon_emissions_baseline`: emisiones totales de la linea base en kgCO2.
- `carbon_emissions_delta`: diferencia control menos linea base en kgCO2.
- `carbon_emissions_daily_average_control`: promedio diario del control en kgCO2.
- `carbon_emissions_daily_average_baseline`: promedio diario de linea base en kgCO2.
- `carbon_emissions_daily_average_delta`: diferencia diaria promedio en kgCO2.

CO2 ya no se trata como metrica secundaria. Es el eje completo OE2 del proyecto.

### OE3: Costos Energeticos

**Objetivo:** optimizar el gasto energetico, reduciendo picos de demanda y aprovechando tarifas dinamicas.

KPIs CityLearn v2 usados en este eje:

- `electricity_cost`: ratio de costo contra linea base.
- `electricity_cost_control`: costo total del control en EUR.
- `electricity_cost_baseline`: costo total de linea base en EUR.
- `electricity_cost_delta`: diferencia control menos linea base en EUR.
- `electricity_cost_daily_average_control`: promedio diario del control en EUR.
- `electricity_cost_daily_average_baseline`: promedio diario de linea base en EUR.
- `electricity_cost_daily_average_delta`: diferencia diaria promedio en EUR.
- `cost_peak_average`: soporte de costo asociado a picos.
- `cost_ramping_average`: soporte de costo asociado a rampas.
- `cost_one_minus_load_factor_average`: soporte de costo asociado a factor de carga.
- `price_signal_deviation`: KPI derivado desde importacion neta distrital y `electricity_pricing`.

`price_signal_deviation` no es un KPI nativo de `evaluate_v2` en este codigo. Esta documentado como KPI derivado del proyecto.

---

## 3. Contrato MADRL

### Dec-POMDP

Cada edificio es un agente descentralizado:

- agente `i`: edificio `i`;
- observacion local: observaciones CityLearn v2 del edificio;
- accion local: acciones CityLearn v2 disponibles para ese edificio;
- estado global CTDE: concatenacion/padding de observaciones locales o estado compartido del backend;
- recompensa colaborativa: `team_mean` por defecto sobre una recompensa v3 especifica por eje y por MADRL;
- evaluacion: KPIs CityLearn v2 por distrito y por eje.

### Recompensa CityLearn v3 MADRL

La recompensa de entrenamiento no usa los pesos heredados de `MARL` como criterio principal. Los scripts v3 fuerzan `CityLearnV3MADRLRewardFunction`, que combina:

- pesos por eje: `E1={flex:0.70, carbon:0.15, cost:0.15}`, `E2={flex:0.15, carbon:0.70, cost:0.15}`, `E3={flex:0.25, carbon:0.15, cost:0.60}`;
- perfil por algoritmo: HAPPO cooperativo on-policy, MASAC con senal local densa, MATD3 orientado a picos/ramping y MAAC con coordinacion por atencion;
- componente EV/V2G separado para restricciones de carga, SoC de salida, autoconsumo y uso de excedentes;
- mezcla colaborativa local/equipo mediante `team_reward_ratio` especifico por MADRL.

Esto separa tres niveles que no deben confundirse: la reward de entrenamiento, la agregacion colaborativa Dec-POMDP y los KPIs CityLearn v2 usados para evaluacion final.

### CTDE

| Algoritmo | Entrenamiento centralizado | Ejecucion descentralizada |
|---|---|---|
| HAPPO | Critico centralizado de HARL con `share_observation_space` | Actor por edificio con observacion local |
| MASAC | Estado global estilo SMAC mediante `get_state()` | Accion discreta por edificio, mapeada a accion CityLearn |
| MATD3 | Critico con observaciones/acciones conjuntas en backend PyTorch off-policy | Actor continuo por edificio |
| MAAC | Critico de atencion multiagente del repositorio MAAC | Politica por edificio con observacion local |

### Validacion cooperativa vigente

El contrato cooperativo y coordinado se valida con:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\validate_citylearn_v3_cooperative_ctde.py `
  --output outputs\validation\cooperative_ctde_validation.json
```

La validacion comprueba 12 casos: HAPPO, MASAC, MATD3 y MAAC en E1, E2 y E3. En cada caso se verifica:

- 17 edificios/agentes.
- `reward_aggregation = team_mean`.
- estado global CTDE igual a la concatenacion de observaciones locales.
- recompensa compartida identica para todos los edificios en el paso validado.
- `team_reward` e `individual_reward` en `infos`.
- `not_using_marl_base_weights = true`.

La comunicacion entre edificios ocurre durante entrenamiento centralizado CTDE mediante estado global, `share_observation_space`, `get_state()`, criticos centralizados y critic de atencion. La ejecucion queda descentralizada: cada edificio usa su politica local.

---

## 4. Backends Oficiales

No hay implementaciones MADRL locales dentro de `citylearn.agents`.

| MADRL | Fuente | Script del proyecto |
|---|---|---|
| HAPPO | `external/HARL` | `CityLearn/scripts/train_citylearn_v3_happo.py` |
| MASAC/mSAC | `external/MARL` | `CityLearn/scripts/train_citylearn_v3_masac.py` |
| MATD3 | `external/MATD3implementation` + backend PyTorch `external/off-policy` | `CityLearn/scripts/train_citylearn_v3_matd3.py` |
| MAAC | `external/MAAC` | `CityLearn/scripts/train_citylearn_v3_maac.py` |
| MARLlib | `external/MARLlib` | adaptador `citylearn.v3.CityLearnV3MARLlibEnv` |

Nota MATD3: la fuente original MATD3 permanece como referencia oficial del paper, pero su entrada de entrenamiento usa TensorFlow 1.x. Para Python 3.9 se usa el backend PyTorch `marlbenchmark/off-policy`.

---

## 5. Artefactos Obligatorios por Entrenamiento

Cada MADRL debe escribir sus salidas en una carpeta propia:

```text
outputs/<experimento>/<madrl>/<escenario>_seed_<seed>/
  data/
    training_summary.json
    results.json
    timeseries.csv
    trace.csv
    checkpoint_manifest.json
  checkpoints/
    <modelos y checkpoints del backend oficial>
  figures/
    figures_manifest.json
    reward_timeseries.png
    convergence_returns.png
    episode_reward_summary.png
    learning_efficiency.png
    citylearn_v2_district_timeseries.png
    exploration_action_l2.png
    agent_reward_contribution.png
    axis_baseline_comparison.png
    baseline_gain_by_kpi.png
    core_kpis.png
    OE1_flexibility_kpis.png
    OE2_co2_kpis.png
    OE3_cost_kpis.png
    tables/
      episode_summary.csv
      episode_summary.md
      objective_kpis.csv
      objective_kpis.md
      axis_baseline_comparison.csv
      axis_baseline_comparison.md
      core_kpis.csv
      core_kpis.md
      training_efficiency.csv
      training_efficiency.md
      exploration_summary.csv
      exploration_summary.md
      agent_reward_summary.csv
      agent_reward_summary.md
      checkpoint_inventory.csv
      checkpoint_inventory.md
```

Para compatibilidad con analisis previos, tambien se mantienen copias raiz de:

- `training_summary.json`
- `results.json`
- `timeseries.csv`
- `trace.csv`
- `checkpoint_manifest.json`

La fuente canonica para nuevas corridas es `data/`. La fuente canonica para modelos es `checkpoints/`. Toda figura, grafica o cuadro generado durante entrenamiento debe quedar bajo `figures/`.

Descripcion de artefactos:

- `data/training_summary.json`: resumen de ejecucion, parametros, ejes y reporte v3.
- `data/results.json`: resultado tecnico completo de la corrida.
- `data/timeseries.csv`: serie temporal distrital por paso.
- `data/trace.csv`: traza por agente y paso.
- `data/checkpoint_manifest.json`: listado de checkpoints y tamanos.
- `checkpoints/`: checkpoints/modelos del backend oficial.
- `figures/`: graficas PNG y cuadros CSV/Markdown generados desde entrenamiento.

CityLearn v2 no define un paquete cerrado de graficas de entrenamiento MADRL. Su superficie oficial de evaluacion es `evaluate/evaluate_v2`, KPIs, series de simulacion y resumen de recompensas. Por eso CityLearn v3 MADRL debe transformar esas mismas salidas v2 en figuras comparables para cada algoritmo.

Figuras obligatorias por MADRL:

- `reward_timeseries.png`: recompensa por paso.
- `convergence_returns.png`: convergencia, media movil de recompensa y retorno acumulado.
- `episode_reward_summary.png`: returns/recompensas por episodio.
- `learning_efficiency.png`: rendimiento de aprendizaje contra costo y emisiones por episodio.
- `citylearn_v2_district_timeseries.png`: series tipo CityLearn v2 de carga neta, carga sin almacenamiento, costo, emisiones, precio e intensidad de carbono.
- `exploration_action_l2.png`: evolucion de exploracion/aprendizaje mediante magnitud de acciones.
- `agent_reward_contribution.png`: contribucion de recompensa por edificio/agente.
- `axis_baseline_comparison.png`: KPIs mejorados/no mejorados contra linea base por OE1/OE2/OE3.
- `baseline_gain_by_kpi.png`: ganancia o perdida por KPI contra baseline CityLearn v2.
- `core_kpis.png`: KPIs centrales del proyecto.
- `OE1_flexibility_kpis.png`: perfil de KPIs de flexibilidad energetica.
- `OE2_co2_kpis.png`: perfil de KPIs de emisiones de CO2.
- `OE3_cost_kpis.png`: perfil de KPIs de costos energeticos.

Tablas obligatorias por MADRL:

- `episode_summary.*`: resumen de episodios, recompensas y pasos.
- `objective_kpis.*`: todos los KPIs por eje con fuente, valor, baseline y mejora.
- `axis_baseline_comparison.*`: conteo por eje contra baseline.
- `core_kpis.*`: KPIs centrales seleccionados.
- `training_efficiency.*`: returns, importacion, costo, emisiones y ratios de eficiencia.
- `exploration_summary.*`: estadisticos de accion/exploracion por episodio.
- `agent_reward_summary.*`: recompensa y accion promedio por agente.
- `checkpoint_inventory.*`: inventario de modelos/checkpoints.

Para corridas existentes se puede regenerar el paquete grafico sin reentrenar:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\regenerate_citylearn_v3_figures.py `
  <OutputRoot>\happo\E3_seed_0
```

### `timeseries.csv`

Campos principales:

- `global_step`
- `episode`
- `episode_step`
- `time_step`
- `scenario`
- `reward_sum`
- `reward_mean`
- `district_net_electricity_consumption`
- `district_net_electricity_consumption_without_storage`
- `district_net_electricity_consumption_cost`
- `district_net_electricity_consumption_emission`
- `electricity_price_mean`
- `carbon_intensity_mean`

### `trace.csv`

Campos principales:

- `global_step`
- `episode`
- `episode_step`
- `time_step`
- `agent`
- `agent_index`
- `reward`
- `individual_reward`
- `done`
- `action_dim`
- `action_0`, `action_1`, `action_2`
- `action_mean`, `action_min`, `action_max`, `action_l2`
- `observation_dim`
- `observation_mean`, `observation_min`, `observation_max`, `observation_l2`

---

## 6. Primer Entrenamiento Corto Ejecutado

### HAPPO, 5 episodios

Comando ejecutado:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\train_citylearn_v3_happo.py `
  --scenario E3 `
  --episode-time-steps 4 `
  --episodes 5 `
  --num-env-steps 20 `
  --hidden-size 128 `
  --torch-threads 1 `
  --output-dir outputs\citylearn_v3_madrl_train_5ep\happo
```

Salida:

- carpeta: `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0`
- episodios registrados: `5`
- pasos registrados en `timeseries.csv`: `20`
- filas de agente en `trace.csv`: `340`
- checkpoints detectados: `19`
- figuras PNG generadas: `4`
- cuadros CSV/Markdown generados: `10`
- checkpoints HAPPO:
  - 17 actores, uno por edificio;
  - 1 critico centralizado;
  - 1 normalizador de valor.

Archivos clave:

- `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0/data/results.json`
- `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0/data/timeseries.csv`
- `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0/data/trace.csv`
- `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0/data/checkpoint_manifest.json`
- `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0/data/training_summary.json`
- `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0/checkpoints/`
- `outputs/citylearn_v3_madrl_train_5ep/happo/E3_seed_0/figures/`

Nota: esta estructura aplica a las nuevas corridas despues de la actualizacion del generador de artefactos. Las corridas historicas pueden conservar copias en la raiz de la carpeta.

Hiperparametros registrados para esta corrida:

```json
{
  "episodes": 5,
  "num_env_steps": 20,
  "episode_length": 4,
  "hidden_sizes": [128, 128],
  "torch_threads": 1,
  "share_param": false,
  "ctde_state_type": "EP",
  "n_rollout_threads": 1,
  "log_interval": 1,
  "checkpoint_interval_episodes": 1,
  "cuda": false
}
```

---

## 7. Comandos de Entrenamiento Corto por MADRL

### HAPPO

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\train_citylearn_v3_happo.py `
  --scenario E3 `
  --episode-time-steps 4 `
  --episodes 5 `
  --num-env-steps 20 `
  --hidden-size 128 `
  --output-dir outputs\citylearn_v3_madrl_train_5ep\happo
```

### MASAC

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\train_citylearn_v3_masac.py `
  --scenario E3 `
  --episode-time-steps 4 `
  --episodes 5 `
  --action-bins 3 `
  --output-dir outputs\citylearn_v3_madrl_train_5ep\masac
```

### MATD3

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\train_citylearn_v3_matd3.py `
  --scenario E3 `
  --episode-time-steps 4 `
  --episodes 5 `
  --num-env-steps 20 `
  --batch-size 4 `
  --buffer-size 128 `
  --hidden-size 64 `
  --output-dir outputs\citylearn_v3_madrl_train_5ep\matd3
```

### MAAC

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\train_citylearn_v3_maac.py `
  --scenario E3 `
  --episode-time-steps 4 `
  --episodes 5 `
  --batch-size 4 `
  --hidden-size 128 `
  --attend-heads 4 `
  --output-dir outputs\citylearn_v3_madrl_train_5ep\maac
```

---

## 8. Validacion Actual

Comandos ejecutados correctamente:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest `
  CityLearn\tests\test_citylearn_v3.py `
  CityLearn\tests\test_madrl_dec_pomdp.py -q
```

Resultado:

```text
12 passed
```

Validacion de estructura de artefactos:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest `
  CityLearn\tests\test_citylearn_v3_training_artifacts.py -q
```

Resultado:

```text
1 passed
```

La prueba de artefactos valida el contrato ampliado de figuras/tablas:

- `13` figuras PNG esperadas cuando hay datos suficientes.
- `16` tablas CSV/Markdown.
- cobertura de recompensas, convergencia, eficiencia, exploracion, comparacion con baseline, CityLearn v2 district time-series y perfiles OE1/OE2/OE3.

Readiness:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\check_citylearn_v3_training_ready.py --strict
```

Estado:

- Python 3.9 listo.
- CityLearn v3 construye 17 edificios + EV.
- HAPPO, MASAC, MATD3 PyTorch y MAAC importan correctamente.
- MARLlib registra `citylearn_v3`.
- `pip check`: sin dependencias rotas.
- MATD3 original TensorFlow 1.x se mantiene como fuente legacy; el entrenamiento funcional Python 3.9 usa `external/off-policy`.

Entorno CUDA validado el 2026-06-08 para el relanzamiento local estable:

- PyTorch: `2.8.0+cu126`.
- Runtime CUDA PyTorch: `12.6`.
- `torch.cuda.is_available()`: `True`.
- GPU detectada: `NVIDIA GeForce RTX 4060 Laptop GPU`.
- `pip check`: sin dependencias rotas despues del cambio a build CUDA.
- Perfil operativo vigente: `local4060_fast`, `TorchThreads=8`; salida activa definida por `outputs/latest_visible_training_output_root.txt`.

Correcciones CUDA aplicadas antes del relanzamiento:

- MATD3 PyTorch genera ruido exploratorio en el mismo `device` y `dtype` del actor.
- MATD3 PyTorch registra las salidas Q del critico como `nn.ModuleList`, para que `model.to(cuda)` mueva todas las capas al GPU.
- El lanzador oficial usa `Start-Process` con stdout/stderr separados, evitando que logs `INFO` en stderr se traten como fallo de PowerShell.

Smoke de estructura de salida ejecutado para los 4 MADRL:

| MADRL | Carpeta | Checkpoints | Figuras PNG | Cuadros CSV/MD | `timeseries.csv` | `trace.csv` |
|---|---|---:|---:|---:|---:|---:|
| HAPPO | `outputs/citylearn_v3_madrl_layout_smoke/happo/E3_seed_0` | 19 | 4 | 10 | 2 filas | 34 filas |
| MASAC | `outputs/citylearn_v3_madrl_layout_smoke/masac/E3_seed_0` | 3 | 4 | 10 | 1 fila | 17 filas |
| MATD3 | `outputs/citylearn_v3_madrl_layout_smoke/matd3/E3_seed_0` | 34 | 4 | 10 | 2 filas | 34 filas |
| MAAC | `outputs/citylearn_v3_madrl_layout_smoke/maac/E3_seed_0` | 2 | 4 | 10 | 1 fila | 17 filas |

Smoke CUDA del lanzador oficial completo:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass `
  -File CityLearn\scripts\launch_citylearn_v3_official_training.ps1 `
  -Scenario E3 `
  -Seed 0 `
  -EpisodeTimeSteps 4 `
  -Episodes 1 `
  -OutputRoot outputs\citylearn_v3_orchestrator_cuda_smoke3 `
  -TorchThreads 4 `
  -Cuda
```

Resultado: `completed`, `cuda=true`, `torch 2.8.0+cu126`, y `exit_code=0` para HAPPO, MASAC, MATD3 y MAAC.

---

## 9. Interpretacion de Resultados

La comparacion final tiene dos niveles obligatorios:

1. **MADRL CityLearn v3 vs baseline CityLearn v2 interno**: ya se calcula al final de cada entrenamiento mediante `evaluate_v2` y queda en `objective_kpis.csv`, `axis_baseline_comparison.csv` y `baseline_gain_by_kpi.png`.
2. **MADRL CityLearn v3 vs agentes originales CityLearn v2**: se calcula con el benchmark nuevo de agentes v2 y el comparador maestro v2-vs-v3.

La comparacion debe hacerse usando los KPIs de los tres ejes:

| Eje | Comparacion |
|---|---|
| OE1 Flexibilidad | ratios contra baseline, picos, ramping, load factor, PV/autoconsumo, bateria y EV |
| OE2 Emisiones CO2 | `carbon_emissions`, kgCO2 control, kgCO2 baseline y delta |
| OE3 Costos | `electricity_cost`, EUR control, EUR baseline, delta y respuesta a tarifa dinamica |

No se debe mezclar CO2 como metrica secundaria. CO2 es OE2.

Para decision multicriterio se puede usar TOPSIS o ranking ponderado despues de normalizar todos los KPIs por eje. Los pesos recomendados para un analisis equilibrado inicial son:

```text
OE1 Flexibilidad: 0.34
OE2 Emisiones CO2: 0.33
OE3 Costos: 0.33
```

Para escenarios focalizados:

```text
E1: OE1=0.60, OE2=0.20, OE3=0.20
E2: OE1=0.20, OE2=0.60, OE3=0.20
E3: OE1=0.25, OE2=0.15, OE3=0.60
```

Estos pesos son solo para analisis y ranking. Los KPIs oficiales siguen viniendo de CityLearn v2 y del reporte v3.

### Benchmark de agentes originales CityLearn v2

Script implementado:

```text
CityLearn/scripts/benchmark_citylearn_v2_agents.py
```

Agentes disponibles:

- `baseline`: `citylearn.agents.base.BaselineAgent`
- `hour_rbc`: `citylearn.agents.rbc.HourRBC` con mapa horario compatible con almacenamiento, EV y washing machine.
- `basic_rbc`: `citylearn.agents.rbc.BasicRBC` cuando el conjunto de acciones sea compatible.
- `optimized_rbc`: `citylearn.agents.rbc.OptimizedRBC` cuando el conjunto de acciones sea compatible.
- `sac`: `citylearn.agents.sac.SAC`
- `marlisa`: `citylearn.agents.marlisa.MARLISA`
- `random`: `citylearn.agents.base.Agent`

Comando recomendado para benchmark oficial v2 rapido, sin entrenamiento de SAC/MARLISA:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\benchmark_citylearn_v2_agents.py `
  --episode-time-steps 8760 `
  --agents baseline hour_rbc `
  --output-dir outputs\citylearn_v2_original_benchmark `
  --continue-on-error
```

Comando extendido con agentes entrenables originales:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\benchmark_citylearn_v2_agents.py `
  --episode-time-steps 8760 `
  --train-episodes 5 `
  --agents baseline hour_rbc sac marlisa `
  --output-dir outputs\citylearn_v2_original_benchmark_train5 `
  --continue-on-error
```

Cada agente v2 queda con la misma estructura comparable:

```text
outputs/citylearn_v2_original_benchmark/<agent>/E3_seed_0/
  data/
    results.json
    timeseries.csv
    trace.csv
    checkpoint_manifest.json
    kpis.csv
  figures/
    figures_manifest.json
    tables/
      objective_kpis.csv
      axis_baseline_comparison.csv
      baseline_gain_by_kpi.csv
```

### Comparador maestro CityLearn v2 original vs CityLearn v3 MADRL

Script implementado:

```text
CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py
```

Comando cuando los MADRL oficiales ya terminaron:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\compare_citylearn_v2_vs_v3_madrl.py `
  --v2-root outputs\citylearn_v2_original_benchmark `
  --v3-root <OutputRoot> `
  --output-dir outputs\comparison_citylearn_v2_vs_v3_madrl `
  --scenario E3 `
  --seed 0 `
  --weights OE1=0.34,OE2=0.33,OE3=0.33
```

Salidas del comparador:

```text
outputs/comparison_citylearn_v2_vs_v3_madrl/
  comparison_summary.json
  master_kpi_comparison.csv
  master_kpi_comparison.md
  master_kpi_comparison_scored.csv
  ranking_by_axis.csv
  ranking_by_axis.md
  ranking_global_weighted.csv
  ranking_global_weighted.md
  OE1_comparison.png
  OE2_comparison.png
  OE3_comparison.png
  baseline_gain_heatmap.png
```

La demostracion de mejora debe reportar:

- ganador por eje OE1/OE2/OE3;
- ranking global ponderado;
- numero de KPIs mejorados contra baseline;
- comparacion contra mejor agente original CityLearn v2;
- comparacion contra promedio de agentes originales CityLearn v2;
- sensibilidad por pesos multicriterio.

---

## 10. Siguiente Paso Operativo

El entrenamiento oficial completo CUDA debe ejecutarse contra un `OutputRoot` nuevo por timestamp o contra el root activo registrado en `outputs/latest_visible_training_output_root.txt`. Los roots `outputs/citylearn_v3_madrl_oficial_v4` y `outputs/citylearn_v3_madrl_oficial_v5` quedan como historicos y no deben citarse como fuente final si existe una corrida activa posterior.

Configuracion oficial activa:

- dataset: `citylearn_iquitos_2023_2025`;
- escenario: `ALL`;
- escenarios internos: `E1`, `E2`, `E3`;
- edificios: `17` + EV;
- horizonte por episodio: `8760` pasos;
- episodios por MADRL: `5`;
- pasos de entorno por MADRL: `43800`;
- PyTorch: `2.8.0+cu126`;
- CUDA: `true`;
- perfil GPU: `local4060_fast`;
- salida: `<OutputRoot>` leido desde `outputs/latest_visible_training_output_root.txt`;
- manifiesto/preflight: `<OutputRoot>/official_full_manifest.json`;
- estado global: `<OutputRoot>/official_full_status.json`.

Comando de relanzamiento:

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

Al completarse la corrida, cada MADRL debe quedar con carpetas separadas por eje:

```text
<OutputRoot>/<madrl>/E1_seed_0/
<OutputRoot>/<madrl>/E2_seed_0/
<OutputRoot>/<madrl>/E3_seed_0/
  data/
  checkpoints/
  figures/
```

La consolidacion final debe comparar HAPPO, MASAC, MATD3 y MAAC contra la linea base CityLearn v2 por OE1 flexibilidad, OE2 emisiones CO2 y OE3 costos usando los KPIs oficiales/derivados definidos en este documento.

### Operacion visible en VS Code

El workspace define tareas para ver el entrenamiento y el monitor en la terminal integrada:

- `CityLearn v3 MADRL - entrenamiento oficial visible`
- `CityLearn v3 MADRL - monitor visible`
- `CityLearn v3 MADRL - validar contrato cooperativo CTDE`

Las tareas no usan `problemMatcher` para evitar que logs informativos se conviertan en falsos errores de la pestana `Problems`.

El contrato vigente usa solo artefactos activos del proyecto actual: `<OutputRoot>` resuelto desde `outputs/latest_visible_training_output_root.txt`, `outputs/dataset_audit/` y `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`. No se deben conservar ni citar logs de entrenamiento no vigentes como fuente de resultados.
