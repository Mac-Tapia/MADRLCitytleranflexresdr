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

## Sustento cientifico

El repositorio incluye un skill versionado para desarrollar la revision bibliografica sistematica que sustenta la implementacion:

| Recurso | Ruta | Proposito |
|---|---|---|
| Skill academico | `tools/skills/madrl-citylearn-literature-review/` | Guia reutilizable para buscar, verificar y organizar 50 investigaciones sobre CityLearn v2, MADRL, Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib, flexibilidad, CO2, costos y SEAI Iquitos. |
| Skill de tesis integrado | `tools/skills/madrl-citylearn-thesis-integrated/` | Skill exclusivo del proyecto para convertir la matriz bibliografica en informe de tesis profesionalizante con estructura Guia N. 02, APA vigente, anexos, matriz de consistencia y operacionalizacion de variables. |
| Skill de plan de tesis | `tools/skills/madrl-citylearn-thesis-plan/` | Skill exclusivo del proyecto para elaborar el Plan de Tesis bajo Guia N. 01, estructura 5.1, usando la matriz bibliografica, APA, cronograma, presupuesto, metodologia y anexos. |
| Plantilla Excel | `tools/skills/madrl-citylearn-literature-review/scripts/create_workbook_template.py` | Genera el libro de sustento con 14 hojas, incluida `Marco_metodologico_MADRL`, matriz de 50 investigaciones, KPIs, backends, MARLlib y arquitectura propuesta. |
| Protocolos de busqueda | `tools/skills/madrl-citylearn-literature-review/references/` | Contiene cadenas booleanas, criterios de inclusion/exclusion, esquema Excel, criterios de backend y lineamientos metodologicos. |

Este skill forma parte del soporte metodologico del proyecto. CityLearn v3 se mantiene definido como extension experimental propuesta sobre CityLearn v2, no como una version oficial externa.

## Estado actual

Actualizado: 2026-05-05.

- Entrenamiento oficial CUDA relanzado desde cero con `-Scenario ALL`.
- Dataset activo: `citylearn_challenge_2022_phase_all_plus_evs`.
- Horizonte oficial: 5 episodios x 8760 pasos = 43800 pasos por corrida.
- Ejecucion secuencial: `E1/E2/E3 x HAPPO/MASAC/MATD3/MAAC`.
- Perfil local GPU-tuned conservador activo para RTX 4060 Laptop 8 GB.
- Recompensa activa: `CityLearnV3MADRLRewardFunction`.
- Agregacion cooperativa Dec-POMDP: `team_mean`.
- Validacion cooperativa CTDE: `passed` para 4 MADRL x 3 ejes.
- PyTorch CUDA activo: `torch 2.8.0+cu126`.
- Monitor visual disponible desde PowerShell y tareas VS Code.

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

## Recompensa v3

Los cuatro MADRL usan `CityLearnV3MADRLRewardFunction`, no los pesos base de `MARL` como criterio principal. La recompensa combina pesos por eje y perfil por algoritmo:

| Escenario | flex | carbon | cost |
|---|---:|---:|---:|
| E1 | 0.70 | 0.15 | 0.15 |
| E2 | 0.15 | 0.70 | 0.15 |
| E3 | 0.25 | 0.15 | 0.60 |

HAPPO, MASAC, MATD3 y MAAC reciben multiplicadores propios de perfil para ajustar cooperacion, densidad de senal local, control de picos/ramping y atencion multiagente. Los KPIs finales siguen viniendo de CityLearn v2 y del reporte v3.

## Contrato cooperativo Dec-POMDP/CTDE

La implementacion vigente cumple el contrato cooperativo y coordinado requerido:

- Cada edificio es un agente descentralizado.
- El estado global CTDE concatena las observaciones locales de los 17 edificios.
- La recompensa de entrenamiento se agrega como `team_mean`, por lo que todos los edificios reciben la misma senal de equipo por paso.
- La informacion entre edificios se transfiere durante el entrenamiento centralizado mediante estado global, `share_observation_space`, `get_state()`, criticos centralizados y critic de atencion.
- La ejecucion permanece descentralizada: cada actor/politica decide con su observacion local.

Validar el contrato:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\validate_citylearn_v3_cooperative_ctde.py `
  --output outputs\citylearn_v3_madrl_official_full_cuda_v2\cooperative_ctde_validation.json
```

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
  -LiveProgressInterval 250 `
  -Cuda
```

Esto genera 12 corridas secuenciales:

```text
E1 x HAPPO, MASAC, MATD3, MAAC
E2 x HAPPO, MASAC, MATD3, MAAC
E3 x HAPPO, MASAC, MATD3, MAAC
```

### Perfil GPU-tuned local

El launcher oficial usa parametros ajustados para la GPU local sin romper la comparacion reproducible CityLearn v2 vs CityLearn v3:

| MADRL | Ajustes activos |
|---|---|
| HAPPO | `hidden_size=384`, `torch_threads=12`, `n_rollout_threads=1`, `live_progress_interval=250` |
| MASAC | `buffer_size=2`, `critic_batch_size=1`, `critic_train_steps=1`, `actor_sample_times=5`, `rnn_hidden_dim=64`, `qmix_hidden_dim=32`, `hyper_hidden_dim=64` |
| MATD3 | `batch_size=512`, `buffer_size=50000`, `hidden_size=384`, `train_interval=100` |
| MAAC | `batch_size=512`, `buffer_length=200000`, `steps_per_update=250`, `num_updates=8`, `hidden_size=384` |

En MASAC puede verse memoria GPU alta con baja utilizacion instantanea. Esto es esperado: el backend alterna rollout secuencial de CityLearn para 17 edificios + EV con actualizaciones PyTorch. Durante el rollout el cuello de botella es CPU/Python/CityLearn; la GPU se activa mas durante las actualizaciones de red. En la RTX 4060 Laptop de 8 GB se usa un perfil MASAC estable para evitar OOM sin modificar los pesos multiobjetivo ni los KPIs de los tres ejes.

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
- `instant_reward_sum`, `instant_reward_mean`, retorno acumulado por episodio y retorno acumulado total.
- Funcion de recompensa, perfil MADRL y pesos activos por eje.
- Costo, CO2, carga neta, precio e intensidad de carbono.
- Artefactos recientes y checkpoints.

## Uso desde VS Code

El workspace incluye tareas visibles para operar el proyecto desde la terminal integrada:

1. `CityLearn v3 MADRL - entrenamiento oficial visible`
2. `CityLearn v3 MADRL - monitor visible`
3. `CityLearn v3 MADRL - validar contrato cooperativo CTDE`

Ruta en VS Code:

```text
Terminal > Run Task...
```

Las tareas no usan `problemMatcher`, para evitar que logs informativos de entrenamiento se registren como falsos errores en la pestana `Problems`.

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
