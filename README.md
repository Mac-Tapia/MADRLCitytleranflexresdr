# CityLearn v3 MADRL para comunidades inteligentes

Proyecto: **Multi-agente de aprendizaje por refuerzo profundo para gestion coordinada de flexibilidad energetica, emisiones de carbono y eficiencia economica en comunidades inteligentes**.

Este repositorio integra CityLearn v2 como simulador base y agrega una capa experimental CityLearn v3 para entrenar y evaluar algoritmos MADRL bajo Dec-POMDP, CTDE, tres ejes de investigacion y comparacion contra agentes originales CityLearn v2.

## Resumen

El proyecto conserva CityLearn v2 como fuente oficial de datos, fisica, edificios, DERs, EVs y KPIs, y agrega una capa CityLearn v3 para:

- Modelar 17 edificios + EV/V2G como comunidad multiagente.
- Exponer un entorno Dec-POMDP con observaciones locales y estado global para CTDE.
- Conectar cuatro backends MADRL oficiales: HAPPO, MASAC, MATD3 y MAAC.
- Ejecutar tres ejes cientificos: flexibilidad energetica, emisiones de CO2 y costos energeticos.
- Guardar artefactos reproducibles: checkpoints, JSON, CSV, figuras, tablas y trazas.
- Comparar CityLearn v3 MADRL contra agentes originales CityLearn v2.

## Ejes del proyecto

| Eje | Escenario | Objetivo | KPIs principales |
|---|---|---|---|
| OE1 | E1 | Flexibilidad energetica: desplazar cargas y aprovechar almacenamiento, EVs y autoconsumo. | `peak_average`, `ramping_average`, `one_minus_load_factor_average`, KPIs PV/bateria/EV. |
| OE2 | E2 | Emisiones de CO2: reducir huella ambiental y evitar importacion en horas de alta intensidad de carbono. | `carbon_emissions`, `carbon_emissions_control`, `carbon_emissions_baseline`, `carbon_emissions_delta`. |
| OE3 | E3 | Costos energeticos: optimizar gasto, reducir picos y aprovechar tarifas dinamicas. | `electricity_cost`, `electricity_cost_delta`, `price_signal_deviation`, KPIs de costo pico/rampa. |

## Arquitectura real implementada

Flujo principal:

```text
Plan de tesis
  -> Dataset CityLearn v2: citylearn_challenge_2022_phase_all_plus_evs
  -> CityLearn v2 base
  -> Capa CityLearn v3
  -> Adaptador comun Dec-POMDP/CTDE
  -> 4 MADRL: HAPPO, MASAC, MATD3, MAAC
  -> Launcher oficial -Scenario ALL
  -> Artefactos por algoritmo/eje/seed
  -> Benchmark CityLearn v2
  -> Comparador CityLearn v2 vs CityLearn v3
  -> Resultados para tesis
```

Componentes principales:

| Componente | Ruta |
|---|---|
| Simulador base | `CityLearn/` |
| Capa CityLearn v3 | `CityLearn/citylearn/v3/` |
| Adaptador comun MADRL | `CityLearn/scripts/citylearn_v3_training_common.py` |
| Entrenadores MADRL | `CityLearn/scripts/train_citylearn_v3_*.py` |
| Launcher oficial | `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` |
| Monitor vivo | `CityLearn/scripts/monitor_citylearn_v3_official_training.ps1` |
| Benchmark v2 | `CityLearn/scripts/benchmark_citylearn_v2_agents.py` |
| Comparador v2 vs v3 | `CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py` |

## MADRL integrados

| MADRL | Script activo | Wrapper CityLearn v3 | Backend |
|---|---|---|---|
| HAPPO | `train_citylearn_v3_happo.py` | `CityLearnHARLEnv` | `external/HARL` |
| MASAC | `train_citylearn_v3_masac.py` | `CityLearnSMACDiscreteEnv` | `external/MARL/src` |
| MATD3 | `train_citylearn_v3_matd3.py` | `CityLearnOffPolicyVecEnv` | `external/off-policy` |
| MAAC | `train_citylearn_v3_maac.py` | `CityLearnMAACVecEnv` | `external/MAAC` |

## Requisitos

- Windows PowerShell para el launcher local oficial.
- Python 3.9.
- PyTorch CUDA para entrenamiento GPU.
- GPU NVIDIA recomendada.
- Submodulos Git inicializados.

El entorno local usado en este proyecto es:

```text
.venv39-citylearn-v3
torch 2.8.0+cu126
CUDA 12.6
```

## Clonar el repositorio

```bash
git clone --recurse-submodules https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git
cd MADRLCitytleranflexresdr
```

Si ya se clono sin submodulos:

```bash
git submodule update --init --recursive
```

## Entrenamiento oficial local

El entrenamiento oficial ejecuta los tres ejes y los cuatro MADRL:

```powershell
powershell -ExecutionPolicy Bypass -File CityLearn\scripts\launch_citylearn_v3_official_training.ps1 `
  -Scenario ALL `
  -Seed 0 `
  -EpisodeTimeSteps 8760 `
  -Episodes 5 `
  -OutputRoot outputs\citylearn_v3_madrl_official_full_cuda_v2 `
  -TorchThreads 12 `
  -Cuda
```

Esto genera 12 corridas secuenciales:

```text
E1 x HAPPO, MASAC, MATD3, MAAC
E2 x HAPPO, MASAC, MATD3, MAAC
E3 x HAPPO, MASAC, MATD3, MAAC
```

## Monitor de entrenamiento

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File CityLearn\scripts\monitor_citylearn_v3_official_training.ps1 `
  -OutputRoot outputs\citylearn_v3_madrl_official_full_cuda_v2 `
  -IntervalSeconds 5 `
  -LogTail 20
```

El monitor muestra:

- Matriz de progreso `E1/E2/E3 x HAPPO/MASAC/MATD3/MAAC`.
- Proceso activo.
- Uso de GPU.
- `global_step`, episodio y paso.
- `reward_sum` y `reward_mean`.
- Costo, CO2, carga neta, precio e intensidad de carbono.
- Artefactos recientes y checkpoints.

## Salidas esperadas

```text
outputs/citylearn_v3_madrl_official_full_cuda_v2/
  official_full_status.json
  official_full_manifest.json
  logs/
  happo/
    E1_seed_0/
    E2_seed_0/
    E3_seed_0/
  masac/
  matd3/
  maac/
```

Cada corrida contiene:

- `live_progress.json`
- `results.json`
- `training_summary.json`
- `timeseries.csv`
- `trace.csv`
- `checkpoint_manifest.json`
- `figures/`
- `figures/tables/`

## Google Colab

El notebook incluye una celda preparada para entrenar en Google Colab con GPU A100/T4/V100:

```text
CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb
```

La celda esta apagada por defecto:

```python
RUN_COLAB_GPU_TRAINING = False
```

Debe activarse solo cuando Colab tenga GPU habilitada y el repositorio este clonado con submodulos y dependencias.

## Benchmark CityLearn v2

Ejecutar agentes originales CityLearn v2 para linea base:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\benchmark_citylearn_v2_agents.py `
  --scenario ALL `
  --output-dir outputs\citylearn_v2_benchmark
```

Comparar CityLearn v2 contra CityLearn v3 MADRL:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe CityLearn\scripts\compare_citylearn_v2_vs_v3_madrl.py `
  --v2-root outputs\citylearn_v2_benchmark `
  --v3-root outputs\citylearn_v3_madrl_official_full_cuda_v2 `
  --output-dir outputs\citylearn_v2_vs_v3_comparison
```

## Documentacion generada

| Documento | Ruta |
|---|---|
| Arquitectura y flujo renderizable | `docs/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md` |
| Plano real implementado | `docs/PLANO_REAL_IMPLEMENTADO_CITYLEARN_V3_MADRL.pdf` |
| Plano integrado | `docs/PLANO_INTEGRADO_CITYLEARN_V3_MADRL.pdf` |
| Aportes cientificos | `docs/APORTES_CIENTIFICOS_CITYLEARN_V3_MADRL.docx` |
| Plan de tesis | `docs/PLAN_TESIS_MADRL_CITYLEARN_V3.docx` |
| Tutorial notebook | `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` |

## Reproducibilidad

Cada resultado debe poder rastrearse a:

```text
dataset -> escenario -> algoritmo -> seed -> hiperparametros
  -> checkpoint -> timeseries/trace -> KPIs -> comparacion v2 vs v3
```

Los backends externos estan fijados en:

```text
external/backends.lock.json
```

## Estado de investigacion

Este repositorio esta orientado a investigacion de tesis. La arquitectura y los artefactos ya estan preparados para demostrar, con resultados cuantitativos, si CityLearn v3 MADRL mejora o caracteriza mejor que CityLearn v2 original los tres ejes:

- Flexibilidad energetica.
- Emisiones de CO2.
- Costos energeticos.

## Licencias y citacion

Este proyecto integra software externo mediante submodulos. Revise las licencias de CityLearn y de los backends en `external/` antes de redistribuir o publicar derivados.

Referencias base:

- CityLearn v2: Nweye et al. (2025), *Journal of Building Performance Simulation*.
- CityLearn original: Vazquez-Canteli et al. (2020), arXiv.
- HAPPO/HARL, MASAC, MATD3 y MAAC segun los repositorios externos fijados en `external/backends.lock.json`.
