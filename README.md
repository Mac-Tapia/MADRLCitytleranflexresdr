# CityLearn v3 MADRL para comunidades inteligentes

Proyecto: **Multi-agente de aprendizaje por refuerzo profundo para gestion coordinada de flexibilidad energetica, emisiones de carbono y eficiencia economica en comunidades inteligentes**.

Este repositorio integra CityLearn v2 como simulador base y agrega una capa experimental CityLearn v3 para entrenar y evaluar algoritmos MADRL bajo Dec-POMDP, CTDE, tres ejes de investigacion y comparacion contra agentes originales CityLearn v2.

## Resumen

El proyecto conserva CityLearn v2 como fuente oficial de datos, fisica, edificios, DERs, EVs y KPIs, y agrega una capa CityLearn v3 para:

- Modelar 17 edificios institucionales/comerciales reales de Iquitos + EV/V2G como comunidad multiagente.
- Exponer un entorno Dec-POMDP con observaciones locales y estado global para CTDE.
- Conectar cuatro backends MADRL oficiales: HAPPO, MASAC, MATD3 y MAAC.
- Ejecutar tres ejes cientificos: flexibilidad energetica, emisiones de CO2 y costos energeticos.
- Guardar artefactos reproducibles: checkpoints, JSON, CSV, figuras, tablas y trazas.
- Comparar CityLearn v3 MADRL contra agentes originales CityLearn v2.
- Aplicar 4 pruebas estadisticas sobre los resultados de entrenamiento MADRL para demostracion de hipotesis de tesis.

## Estado actual

Actualizado: 2026-05-21.

- Dataset activo: `citylearn_iquitos_2023_2025` (17 edificios reales de Iquitos, 2023-2025, 75+ EVs).
- Entrenamiento oficial CUDA ejecutado con `-Scenario ALL`.
- Horizonte oficial: 5 episodios x 8760 pasos = 43800 pasos por corrida.
- Ejecucion secuencial: `E1/E2/E3 x HAPPO/MASAC/MATD3/MAAC` (12 corridas).
- Perfil local GPU-tuned conservador activo para RTX 4060 Laptop 8 GB.
- Recompensa activa: `CityLearnV3MADRLRewardFunction`.
- Agregacion cooperativa Dec-POMDP: `team_mean`.
- Validacion cooperativa CTDE: `passed` para 4 MADRL x 3 ejes.
- PyTorch CUDA activo: `torch 2.8.0+cu126`.
- Framework UC3M v1.0.0 integrado con BACTTensor 29D, RewardAxes 7D y HPHI.
- Suite de pruebas estadisticas completa: Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U y Wilcoxon signed-rank.

## Ejes del proyecto

| Eje | Escenario | Objetivo | KPIs principales |
|---|---|---|---|
| OE1 | E1 | Flexibilidad energetica: desplazar cargas y aprovechar almacenamiento, EVs y autoconsumo. | `peak_average`, `ramping_average`, `one_minus_load_factor_average`, KPIs PV/bateria/EV. |
| OE2 | E2 | Emisiones de CO2: reducir huella ambiental y evitar importacion en horas de alta intensidad de carbono. | `carbon_emissions`, `carbon_emissions_control`, `carbon_emissions_baseline`, `carbon_emissions_delta`. |
| OE3 | E3 | Costos energeticos: optimizar gasto, reducir picos y aprovechar tarifas dinamicas. | `electricity_cost`, `electricity_cost_delta`, `price_signal_deviation`, KPIs de costo pico/rampa. |

## Arquitectura real implementada

Flujo principal:

```text
Dataset citylearn_iquitos_2023_2025 (17 edificios Iquitos, 2023-2025)
  -> CityLearn v2 base (simulador)
  -> Capa CityLearn v3 (Dec-POMDP, CTDE, recompensa multiobjetivo)
  -> UC3MEnv wrapper (BACTTensor 29D, RewardAxes 7D, HPHI)
  -> 4 MADRL: HAPPO, MASAC, MATD3, MAAC
  -> Launcher oficial -Scenario ALL
  -> Artefactos por algoritmo/eje/seed
  -> generate_thesis_objective_evidence.py
  -> 4 pruebas estadisticas (SW, KW, MWU, Wilcoxon SR)
  -> Benchmark CityLearn v2
  -> Comparador CityLearn v2 vs CityLearn v3
  -> Resultados para tesis
```

Componentes principales:

| Componente | Ruta |
|---|---|
| Simulador base | `CityLearn/` |
| Capa CityLearn v3 | `CityLearn/citylearn/v3/` |
| Framework UC3M | `uc3m/` |
| Adaptador comun MADRL | `CityLearn/scripts/citylearn_v3_training_common.py` |
| Entrenadores MADRL | `CityLearn/scripts/train_citylearn_v3_*.py` |
| Launcher oficial (Iquitos) | `CityLearn/scripts/launch_citylearn_v3_iquitos_training.ps1` |
| Monitor vivo (Iquitos) | `CityLearn/scripts/monitor_citylearn_v3_iquitos_training.ps1` |
| Launcher oficial (general) | `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` |
| Evidencia estadistica tesis | `CityLearn/scripts/generate_thesis_objective_evidence.py` |
| Benchmark v2 | `CityLearn/scripts/benchmark_citylearn_v2_agents.py` |
| Comparador v2 vs v3 | `CityLearn/scripts/compare_citylearn_v2_vs_v3_madrl.py` |
| Dataset Iquitos | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` |
| Herramientas de dataset | `tools/` |
| Suite de tests | `tests/uc3m/` |

## Framework UC3M (Universal CityLearn v3 Modified)

El paquete `uc3m/` es un framework universal reutilizable sobre CityLearn v2 que implementa el Meta-Dec-POMDP para N edificios arbitrarios.

| Modulo | Ruta | Descripcion |
|---|---|---|
| `UC3MEnv` | `uc3m/env/uc3m_env.py` | Wrapper universal Dec-POMDP 11-aria; compatible con HARL, MARLlib y RLlib |
| `BACTTensor` | `uc3m/env/bact.py` | Contexto fijo por edificio: 29D = clima (7) + geografico (8) + fisico (14) |
| `RewardAxes` | `uc3m/reward/axes.py` | 7 ejes de recompensa con pesos lambda: CO2, costo, flexibilidad, confort, degradacion BESS, resiliencia, ACS |
| `HPHI` | `uc3m/reward/hphi.py` | Holistic Pareto Hypervolume Index 7D para comparacion integrada de algoritmos |
| `KPIEvaluator` | `uc3m/kpis/evaluator.py` | Calculo holistico de KPIs normalizados contra baseline RBC |
| `AlgorithmFactory` | `uc3m/algorithms/factory.py` | Mapeo centralizado de 4 MADRL a sus backends externos |

Instalar el paquete en modo desarrollo:

```bash
pip install -e ".[train]"
```

Ejecutar tests:

```bash
pytest tests/ -q --tb=short
```

## Dataset Iquitos 2023-2025

| Caracteristica | Detalle |
|---|---|
| Edificios | 17 institucionales/comerciales reales de Iquitos, Peru |
| Rango temporal | 2023-2025 (26,304 pasos horarios) |
| EVs | 75+ vehiculos electricos (4-40 kWh, 3-7.4 kW) |
| Cargadores | 38+ cargadores Tipo 1/Tipo 2 |
| Almacenamiento | Baterias 5-10 kWh por edificio (selectivo) |
| Generacion solar | Paneles PV por edificio (tamano variable) |
| Mercado comunitario | Habilitado, precio local 0.8 del grid |
| Grilla | Sistema aislado diesel ELECTRO ORIENTE |
| Archivo central | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json` |

Regenerar el dataset desde cero (si se requiere):

```bash
python tools/generate_iquitos_dataset.py
```

## MADRL integrados

| MADRL | Script activo | Wrapper CityLearn v3 | Backend |
|---|---|---|---|
| HAPPO | `train_citylearn_v3_happo.py` | `CityLearnHARLEnv` | `external/HARL` |
| MASAC | `train_citylearn_v3_masac.py` | `CityLearnSMACDiscreteEnv` | `external/MARL/src` |
| MATD3 | `train_citylearn_v3_matd3.py` | `CityLearnOffPolicyVecEnv` | `external/off-policy` |
| MAAC | `train_citylearn_v3_maac.py` | `CityLearnMAACVecEnv` | `external/MAAC` |

Submodulos externos de referencia adicionales:

| Submodulo | Ruta | Proposito |
|---|---|---|
| MicroGrids | `external/MicroGrids` | Modelos de microgrillas (referencia) |
| evcc | `external/evcc` | Gestor de carga EV (referencia) |
| prosumpy | `external/prosumpy` | Gestion de prosumidores (referencia) |

## Recompensa v3

Los cuatro MADRL usan `CityLearnV3MADRLRewardFunction`. La recompensa combina pesos por eje y perfil por algoritmo:

| Escenario | flex | carbon | cost |
|---|---:|---:|---:|
| E1 | 0.70 | 0.15 | 0.15 |
| E2 | 0.15 | 0.70 | 0.15 |
| E3 | 0.25 | 0.15 | 0.60 |

## Contrato cooperativo Dec-POMDP/CTDE

- Cada edificio es un agente descentralizado.
- El estado global CTDE concatena las observaciones locales de los 17 edificios.
- La recompensa de entrenamiento se agrega como `team_mean`.
- La informacion entre edificios se transfiere durante el entrenamiento centralizado.
- La ejecucion permanece descentralizada: cada actor/politica decide con su observacion local.

Validar el contrato:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\validate_citylearn_v3_cooperative_ctde.py `
  --output outputs\citylearn_v3_madrl_official_full_cuda_v2\cooperative_ctde_validation.json
```

## Pruebas estadisticas de demostracion de hipotesis

Los 4 tests se aplican sobre los **KPI-gains de entrenamiento de los 4 MADRL** (HAPPO, MASAC, MATD3, MAAC) por cada eje OE1/OE2/OE3. Cada test tiene su propia funcion, CSV de salida y seccion de p-valor en `hipotesis_estadisticas_madrl.csv`.

| Test | Funcion | CSV de salida | Tipo de muestra | Hipotesis H0 |
|---|---|---|---|---|
| **Shapiro-Wilk** | `statistical_omnibus_rows()` | `analisis_estadistico_madrl.csv` | Por grupo (1 algoritmo) | Los KPI-gains de ALGO siguen distribucion normal |
| **Kruskal-Wallis** | `statistical_omnibus_rows()` | `analisis_estadistico_madrl.csv` | 4 grupos simultaneos | Las distribuciones de HAPPO, MASAC, MATD3 y MAAC son identicas |
| **Mann-Whitney U** | `mann_whitney_pairwise_rows()` | `comparaciones_mwu_madrl.csv` | Muestras **independientes** | La distribucion de KPI-gains de A es igual a la de B |
| **Wilcoxon SR** | `wilcoxon_pairwise_rows()` | `comparaciones_wilcoxon_madrl.csv` | Muestras **pareadas** (mismo KPI/edificio) | La mediana de diferencias d_i = A_i - B_i es cero |

**Flujo de demostracion:**

1. Shapiro-Wilk verifica si los datos son normales por grupo; si alguno rechaza normalidad, justifica los tests no parametricos.
2. Kruskal-Wallis detecta si hay diferencias globales entre los 4 MADRL en el eje.
3. Mann-Whitney U identifica que par especifico difiere (muestras independientes).
4. Wilcoxon signed-rank confirma diferencias sistematicas pareadas (mismo KPI, dos algoritmos).

Todos los resultados se consolidan en `hipotesis_estadisticas_madrl.csv` con columnas `SW_*`, `KW_*`, `MWU_*` y `WC_*` por eje y por algoritmo.

## Evidencia para plan e informe de tesis

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\generate_thesis_objective_evidence.py
```

Salida principal en `outputs/thesis_objective_evidence/`:

```text
Resumen_ejecutivo.csv
objetivos_especificos_cumplimiento.csv
Matriz_KPIs.csv / KPIs_y_metricas.csv
matriz_resultados_madrl.csv
matriz_baseline_por_eje.csv
scores_kpi_algoritmo_madrl.csv
analisis_estadistico_madrl.csv          <- Shapiro-Wilk + Kruskal-Wallis
comparaciones_mwu_madrl.csv             <- Mann-Whitney U (independiente) + tamanos de efecto
comparaciones_wilcoxon_madrl.csv        <- Wilcoxon signed-rank (pareado)
hipotesis_estadisticas_madrl.csv        <- 4 tests unificados por eje
matriz_operacionalizacion_variables.csv
Marco_metodologico_MADRL.csv
matriz_consistencia_objetivos.csv
Backends_MADRL.csv / MARLlib_Integracion.csv
CityLearn_v3_Propuesto.csv
Arquitectura_Propuesta.csv
Aplicabilidad_SEAI_Iquitos.csv
CityLearn_CO2_Costos.csv
Datasets_y_codigo.csv
thesis_skill_feed.json
resumen_evidencia_tesis.md
```

Ademas de los 4 tests no parametricos, `comparaciones_mwu_madrl.csv` incluye tamanos de efecto para cada par MADRL: Cliff's delta, Vargha-Delaney A12, Cohen d, Hedges g y bootstrap CI 95%.

## Entrenamiento oficial local

```powershell
powershell -ExecutionPolicy Bypass -File CityLearn\scripts\launch_citylearn_v3_iquitos_training.ps1 `
  -Scenario ALL `
  -Seed 0 `
  -EpisodeTimeSteps 8760 `
  -Episodes 5 `
  -OutputRoot outputs\citylearn_v3_madrl_iquitos `
  -TorchThreads 12 `
  -LiveProgressInterval 250 `
  -Cuda
```

Esto genera 12 corridas secuenciales sobre el dataset Iquitos:

```text
E1 x HAPPO, MASAC, MATD3, MAAC
E2 x HAPPO, MASAC, MATD3, MAAC
E3 x HAPPO, MASAC, MATD3, MAAC
```

### Perfil GPU-tuned local (RTX 4060 Laptop 8 GB)

| MADRL | Ajustes activos |
|---|---|
| HAPPO | `hidden_size=384`, `torch_threads=12`, `n_rollout_threads=1`, `live_progress_interval=250` |
| MASAC | `buffer_size=2`, `critic_batch_size=1`, `critic_train_steps=1`, `actor_sample_times=5`, `rnn_hidden_dim=64` |
| MATD3 | `batch_size=512`, `buffer_size=50000`, `hidden_size=384`, `train_interval=100` |
| MAAC | `batch_size=512`, `buffer_length=200000`, `steps_per_update=250`, `num_updates=8`, `hidden_size=384` |

## Monitor de entrenamiento

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File CityLearn\scripts\monitor_citylearn_v3_iquitos_training.ps1 `
  -OutputRoot outputs\citylearn_v3_madrl_iquitos `
  -IntervalSeconds 5 `
  -LogTail 20
```

## Requisitos

- Windows PowerShell para el launcher local.
- Python 3.9.
- PyTorch CUDA para entrenamiento GPU.
- GPU NVIDIA recomendada.
- Submodulos Git inicializados.

```text
.venv39-citylearn-v3
torch 2.8.0+cu126
CUDA 12.6
```

Instalar dependencias del paquete UC3M:

```bash
pip install -e ".[train,dataset]"
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

## Salidas esperadas por corrida

```text
outputs/citylearn_v3_madrl_iquitos/
  happo/E1_seed_0/  masac/E1_seed_0/  matd3/E1_seed_0/  maac/E1_seed_0/
  happo/E2_seed_0/  ...
  happo/E3_seed_0/  ...
```

Cada corrida contiene:

- `live_progress.json`, `results.json`, `training_summary.json`
- `timeseries.csv`, `trace.csv`, `checkpoint_manifest.json`
- `building_behavior_summary.csv`, `building_kpis.csv`
- `building_observation_action_schema.csv`, `building_trace_sample.csv`
- `figures/` con retornos, convergencia y comparacion KPI
- `figures/tables/` con tablas Markdown por edificio

## Benchmark y comparacion

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
  --v3-root outputs\citylearn_v3_madrl_iquitos `
  --output-dir outputs\citylearn_v2_vs_v3_comparison
```

## Sustento cientifico y skills

| Recurso | Ruta | Proposito |
|---|---|---|
| Skill dataset Iquitos | `tools/skills/iquitos-citylearn-dataset/` | Generacion, actualizacion y validacion del dataset de Iquitos para entrenamiento MADRL |
| Skill de tesis integrado | `tools/skills/madrl-citylearn-thesis-integrated/` | Informe de tesis profesionalizante con estructura Guia N. 02, APA, matrices de consistencia |
| Skill de plan de tesis | `tools/skills/madrl-citylearn-thesis-plan/` | Plan de Tesis bajo Guia N. 01, estructura 5.1, cronograma, presupuesto, metodologia |
| Sustento capa v3 | `tools/skills/madrl-sustento-doc-capa v3/` | Modelado matematico Dec-POMDP, CTDE y fundamentos de la capa v3 |

## Documentacion generada

| Documento | Ruta |
|---|---|
| Arquitectura y flujo renderizable | `docs/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md` |
| Plano real implementado | `docs/PLANO_REAL_IMPLEMENTADO_CITYLEARN_V3_MADRL.pdf` |
| Plano integrado | `docs/PLANO_INTEGRADO_CITYLEARN_V3_MADRL.pdf` |
| Aportes cientificos | `docs/APORTES_CIENTIFICOS_CITYLEARN_V3_MADRL.docx` |
| Plan de tesis | `docs/PLAN_TESIS_MADRL_CITYLEARN_V3.docx` |
| Informe de tesis completo | `docs/INFORME_TESIS_MADRL_V1_COMPLETO.docx` |
| Resultados preliminares GD-Iquitos | `docs/Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx` |
| Tutorial notebook | `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` |

## Reproducibilidad

Cada resultado debe poder rastrearse a:

```text
dataset -> escenario -> algoritmo -> seed -> hiperparametros
  -> checkpoint -> timeseries/trace -> KPIs -> comparacion v2 vs v3
  -> 4 tests estadisticos sobre KPI-gains -> hipotesis_estadisticas_madrl.csv
```

Los backends externos estan fijados en:

```text
external/backends.lock.json
```

## Estado de investigacion

Este repositorio esta orientado a investigacion de tesis. La arquitectura y los artefactos estan preparados para demostrar, con resultados cuantitativos y pruebas estadisticas, si CityLearn v3 MADRL mejora o caracteriza mejor que CityLearn v2 original los tres ejes:

- **OE1** Flexibilidad energetica.
- **OE2** Emisiones de CO2.
- **OE3** Costos energeticos.

La demostracion de hipotesis sigue el flujo: Shapiro-Wilk (normalidad) → Kruskal-Wallis (diferencias globales entre 4 MADRL) → Mann-Whitney U (diferencias por par, independiente) → Wilcoxon signed-rank (diferencias por par, pareado), aplicados sobre KPI-gains de entrenamiento de HAPPO, MASAC, MATD3 y MAAC.

## Licencias y citacion

Este proyecto integra software externo mediante submodulos. Revise las licencias de CityLearn y de los backends en `external/` antes de redistribuir o publicar derivados.

Referencias base:

- CityLearn v2: Nweye et al. (2025), *Journal of Building Performance Simulation*.
- CityLearn original: Vazquez-Canteli et al. (2020), arXiv.
- HAPPO/HARL, MASAC, MATD3 y MAAC segun los repositorios externos fijados en `external/backends.lock.json`.
