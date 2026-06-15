# Informe de validacion de recompensas multiobjetivo MADRL

**Fecha:** 2026-06-13
**Proyecto:** `MADRLCitytleranflexresdr`
**Dataset activo:** `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`
**Funcion validada:** `citylearn.reward_function.CityLearnV3MADRLRewardFunction`

## 1. Diagnostico del entrenamiento atascado

La corrida activa `outputs/citylearn_v3_madrl_full_20260613_010234` no quedo avanzando: HAPPO termino E1, E2 y E3, pero MASAC/E1 fallo al cerrar el primer episodio por `torch.OutOfMemoryError` en la actualizacion de critic/QMIX. El monitor siguio abierto y por eso mostraba `status=running`, pero ya no habia proceso `train_citylearn_v3_masac.py` activo.

Evidencia local:

- `logs/E1_masac.stderr.log`: `torch.OutOfMemoryError: CUDA out of memory`.
- `visible_launcher_transcript.log`: `FAIL MASAC/E1 exit=1`.
- `official_full_status.json`: ultimo job `masac/E1` con `exit_code=null`, por cierre abrupto del launcher.
- GPU en el monitor: 0 MiB usados, sin proceso CUDA activo.

Correccion aplicada:

- El perfil `local4060_fast` conserva `MaxConcurrentScenarioJobs=2`, pero MASAC/MAAC siguen con `MaxConcurrentHeavyJobs=1`.
- MASAC en 8 GB baja su memoria por actualizacion:
  - `max_replay_buffer_gib: 3.0`; el replay buffer estimado con 17 edificios, `discrete_action_mode=axis`, 8,760 pasos y `buffer_size=2` es 2.74 GiB, por lo que 2.0 GiB bloqueaba el arranque antes de entrenar.
  - `buffer_size: 2`.
  - `critic_batch_size: 1`.
  - `actor_sample_times: 2`.
  - `rnn_hidden_dim: 64`.
  - `qmix_hidden_dim: 32`.
  - `hyper_hidden_dim: 64`.

La causa no fue el paralelismo de escenarios. MASAC ya corria con concurrencia pesada 1. El cuello fue el tamano de tensores de critic/QMIX sobre episodios de 8,760 pasos.

Actualizacion posterior: el relanzador de emergencia `scripts/restart_masac_matd3_maac.ps1` deja de forzar `TorchThreads=12` y `LiveProgressInterval=250`; ahora hereda los defaults de `local4060_fast` (`TorchThreads=8`, `LiveProgressInterval=1000`) y usa `-SkipCompleted`. Esto reduce sobrecarga de CPU/IO sin subir `critic_batch_size`, porque el proceso MASAC activo ya usa ~5.7 GiB de VRAM y aumentar batch en una RTX 4060 de 8 GB puede reintroducir OOM.

Actualizacion de backend MASAC: `CityLearn/scripts/masac_runtime_optimizations.py` instala un parche runtime sobre `external/MARL` sin modificar el submodulo. El parche convierte el replay mini-batch una sola vez por actualizacion, intenta precargarlo en CUDA con fallback automatico a CPU si hay OOM, cachea la matriz identidad de agentes y elimina copias `.cuda()` repetidas dentro del loop temporal de 8,760 pasos. Esto ataca el cuello observado de CPU/MASAC manteniendo reproducibilidad del repositorio.

Actualizacion del monitor: al reanudar desde `StartFromAlgorithm=masac`, el monitor anterior mostraba `happo:queued` porque solo leia `official_full_status.json` y no comprobaba artefactos ya existentes. `CityLearn/scripts/monitor_citylearn_v3_official_training.ps1` ahora detecta `results.json`/`data/results.json` y reporta `done/artifact`; el launcher tambien persiste `start_from_algorithm`, `algorithm_order`, `skip_reason` y registros `skipped/done` para que HAPPO no aparezca como pendiente cuando ya fue completado.

## 2. Recompensa multiobjetivo validada

La implementacion real usa una recompensa comun para los cuatro backends. Esto evita que HAPPO, MASAC, MATD3 y MAAC optimicen objetivos distintos y permite comparar resultados por algoritmo sin sesgo de funcion de recompensa.

### 2.1 Pesos por escenario

| Escenario | flex | carbon | cost | Objetivo dominante |
|---|---:|---:|---:|---|
| E1 | 0.70 | 0.15 | 0.15 | Flexibilidad energetica |
| E2 | 0.15 | 0.70 | 0.15 | Reduccion CO2 |
| E3 | 0.25 | 0.15 | 0.60 | Reduccion de costo |

Los pesos forman un simplex: suman 1.0 en cada escenario. El peso dominante define el eje de tesis y los pesos residuales evitan soluciones que mejoran un KPI destruyendo los otros.

### 2.2 Perfil comun por algoritmo

| Parametro | Valor |
|---|---:|
| `team_reward_ratio` | 0.70 |
| `ev_weight` | 0.25 |
| `reward_scale` | 1.00 |
| `peak_weight` | 0.45 |
| `ramp_weight` | 0.35 |
| `ev_soc_tolerance` | 0.05 |
| `ev_soc_critical_deficit` | 0.25 |
| `ev_urgency_hours` | 4.0 |
| `ev_departure_deficit_weight` | 0.55 |
| `ev_urgency_deficit_weight` | 0.30 |
| `ev_idle_deficit_weight` | 0.15 |
| `axis_weight_multipliers` | 1.00, 1.00, 1.00 |

Perfiles esperados:

- HAPPO: `happo_unified_comparable_v3`.
- MASAC: `masac_unified_comparable_v3`.
- MATD3: `matd3_unified_comparable_v3`.
- MAAC: `maac_unified_comparable_v3`.

### 2.3 Formula operativa

```text
reward_i(t) = reward_scale * [
    w_flex   * flex_i(t)
  + w_carbon * carbon_i(t)
  + w_cost   * cost_i(t)
  + ev_weight * ev_i(t)
]

team_reward(t) = mean_i reward_i(t)
mixed_reward_i(t) = 0.30 * reward_i(t) + 0.70 * team_reward(t)
```

### 2.4 Penalidades

| Penalidad | Formula resumida | Razon |
|---|---|---|
| Pico | `0.45 * tanh(peak_share / 25)` | Alinea la recompensa con `peak_average`, KPI principal de flexibilidad. |
| Rampa | `0.35 * tanh(ramp_share / 15)` | Penaliza cambios bruscos de importacion distrital. |
| Export con BESS disponible | `0.15 * tanh(export * (1 + headroom) / 20)` | Evita desperdiciar PV cuando existe capacidad de almacenamiento. |
| Importar con SOC alto | `0.10 * tanh(import * SOC / 20)` | Penaliza importar red cuando hay energia almacenada. |
| Carbono | `tanh(import * (0.25 + carbon_norm) / 20)` | Penaliza importaciones en red diesel aislada. |
| Costo | `tanh(import * (0.25 + price_norm) / 20)` | Penaliza importaciones, especialmente en tarifa alta. |
| EV base | `0.25 * clip(tanh(ev_raw / 10) + ev_service_constraint, -1, 1)` | Refuerza cumplimiento de SOC requerido; evita que el agente mejore costo/CO2 dejando EV sin cargar. |
| EV SOC salida | `0.55 * mean(deficit_departure)` | Penalidad fuerte cuando el EV llega a la salida bajo el SOC requerido. |
| EV urgencia | `0.30 * mean(deficit_urgency)` | Penaliza deficit dentro de las ultimas 4 h antes de salida. |
| EV inactivo | `0.15 * mean(deficit_idle)` | Penaliza no cargar cuando existe deficit y la salida esta cerca. |

Correccion aplicada al signo EV: el caso `soc_diff <= -0.25` ya no usa `self.weights["soc_under"] ** 2` con signo positivo; ahora conserva penalidad negativa. La validacion sintetica exige que un EV con SOC 0.40, SOC requerido 0.85 y salida inmediata produzca `ev_term <= -0.99`.

## 3. Sustento de investigacion

- CityLearn se usa como entorno de benchmark para control de edificios, recursos distribuidos y KPIs de flexibilidad, costo y emisiones. La documentacion y tutoriales de CityLearn describen su uso para comparar controladores RL y DRL en comunidades grid-interactive.
- CityLearn v2 documenta gestion de BESS, V2G, confort y control carbon-aware en comunidades multiagente, por eso los tres ejes `flex/carbon/cost` son consistentes con el entorno.
- Lowe et al. (MADDPG) justifican CTDE: entrenamiento con informacion conjunta y ejecucion descentralizada, lo que respalda el uso de `team_reward`.
- HATRPO/HAPPO justifican aprendizaje cooperativo heterogeneo sin compartir parametros y con mejora monotona teorica, por eso se conserva una senal de equipo fuerte.
- MAAC justifica critic con atencion para coordinacion multiagente; mantener recompensa comun permite evaluar si el mecanismo de atencion mejora bajo el mismo objetivo.
- PyTorch documenta que cada proceso CUDA debe gestionar su memoria y que `PYTORCH_CUDA_ALLOC_CONF`/limites por proceso pueden mitigar OOM; por eso MASAC se ajusta con batch, hidden y replay reducidos.

Fuentes primarias revisadas:

- CityLearn references: https://www.citylearn.net/references.html
- CityLearn tutorial, Climate Change AI 2023: https://www.climatechange.ai/papers/iclr2023/2
- CityLearn v2 paper: https://arxiv.org/abs/2405.03848
- CityLearn multi-objective benchmarking: https://arxiv.org/abs/2408.15170
- MADDPG/CTDE: https://arxiv.org/abs/1706.02275
- HATRPO/HAPPO: https://arxiv.org/abs/2109.11251
- MAAC: https://arxiv.org/abs/1810.02912
- PyTorch CUDA memory management: https://docs.pytorch.org/docs/2.12/notes/cuda.html
- PyTorch multiprocessing/CUDA: https://docs.pytorch.org/docs/2.12/notes/multiprocessing.html

## 4. Dataset cargado por el entrenamiento

Ruta canonica:

```text
CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json
```

Resumen validado:

| Componente | Cantidad |
|---|---:|
| Edificios incluidos | 17 |
| Horas por serie | 26,304 |
| CSV activos | 222 |
| `Building_X.csv` | 17 |
| `charger_X_Y.csv` | 185 |
| `Washing_Machine_X.csv` | 17 |
| `weather.csv` | 1 |
| `carbon_intensity.csv` | 1 |
| `pricing.csv` | 1 |
| EV definidos en pool | 1,850 |
| Tomas EV Mode 3 en schema | 185 |
| Unidades fisicas Mode 3 | 96 |
| Potencia EV nominal agregada | 749.4 kW |
| PV total | 48,790.9 kWp |
| BESS total | 26,266.0 kWh / 6,648.0 kW |

Archivos base cargados:

| Grupo | Archivos |
|---|---|
| Schema | `schema.json` |
| Clima | `weather.csv` |
| Emisiones | `carbon_intensity.csv` |
| Precios | `pricing.csv` |
| Metadatos | `building_metadata.json`, `carbon_intensity_metadata.json`, `dataset_generation_log.json`, `ev_charger_sizing_log.json`, `controlled_machines_log.json`, `solar_fix_log.json` |
| Carga edificios | `Building_1.csv` a `Building_17.csv` |
| Carga EV | `charger_1_1.csv` a `charger_17_11.csv`, 185 archivos totales segun schema |
| Cargas controladas | `Washing_Machine_1.csv` a `Washing_Machine_17.csv` |

Edificios:

| ID | Archivo | Tipo |
|---|---|---|
| B01 | `Building_1.csv` | Office |
| B02 | `Building_2.csv` | Office |
| B03 | `Building_3.csv` | Assembly |
| B04 | `Building_4.csv` | Retail |
| B05 | `Building_5.csv` | MultiFamily_Hotel |
| B06 | `Building_6.csv` | Commercial_Mall |
| B07 | `Building_7.csv` | Education |
| B08 | `Building_8.csv` | Assembly_Military |
| B09 | `Building_9.csv` | Office_Critical |
| B10 | `Building_10.csv` | Office |
| B11 | `Building_11.csv` | Healthcare_Hospital |
| B12 | `Building_12.csv` | Healthcare |
| B13 | `Building_13.csv` | Education |
| B14 | `Building_14.csv` | Industrial_Port |
| B15 | `Building_15.csv` | Education |
| B16 | `Building_16.csv` | Industrial |
| B17 | `Building_17.csv` | Laboratory |

## 5. Validadores

Validadores vinculados:

- `CityLearn/scripts/validate_citylearn_v3_reward_profiles.py`
- `tools/verify_training_optimization.py`
- `tools/verify_workflow_integrity.py`
- `CityLearn/scripts/check_citylearn_v3_training_ready.py`

El criterio de aceptacion es:

- Recompensa `CityLearnV3MADRLRewardFunction` en los 4 algoritmos y 3 escenarios.
- Perfiles `*_unified_comparable_v3` con penalidad SOC/EV reforzada.
- Pesos por escenario exactos.
- Recompensas finitas con accion cero.
- Dataset listo para normalizacion y entrenamiento.
