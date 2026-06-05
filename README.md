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

Actualizado: 2026-06-04.

- Dataset activo: `citylearn_iquitos_2023_2025` (17 edificios reales de Iquitos, 2023-2025, 50 cargadores EV).
- Dataset regenerado con parametros reales de `CityLearn/data/buildingcsv/building.csv`: nombres oficiales, areas techadas exactas, tipos de uso y sistemas de AC reales por edificio.
- Non-shiftable load destilada desde mediciones mensuales reales `B_02.csv` a `B_17.csv` (balance mensual delta < 0.1%).
- Entrenamiento oficial en curso: HAPPO E1 completado (5 ep/43800 pasos), MASAC E1 completado, cadena MASAC/MATD3/MAAC en ejecucion.
- Horizonte oficial: 5 episodios x 8760 pasos = 43800 pasos por corrida. 12 corridas totales.
- Ejecucion secuencial: `HAPPO/MASAC/MATD3/MAAC x E1/E2/E3` (4 algoritmos x 3 ejes).
- Perfil local GPU-tuned activo para RTX 4060 Laptop 8 GB (torch 2.8.0+cu126).
- Recompensa activa: `CityLearnV3MADRLRewardFunction` con pesos multiobjetivo por escenario.
- Agregacion cooperativa Dec-POMDP: `team_mean` con team_ratio por algoritmo (HAPPO=0.75, MAAC=0.80).
- Validacion cooperativa CTDE: `passed` para 4 MADRL x 3 ejes.
- Fix forrtl error (200): `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1` y `PYTHONUNBUFFERED=1` aplicados al launcher.
- Monitor en tiempo real: refresca cada 5 s con pesos OE1/OE2/OE3, pasos, episodios y KPIs energeticos.
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
| Nombres reales | Municipalidad San Juan Bautista, Aeropuerto, Tottus, Hotel Plaza, Mall Aventura, UNAP, PNP, COER, GRL, Hospital Regional, EsSalud, UNAP Economia, Autoridad Portuaria, DREL Colegio, SIMA Iquitos, Selva Amazonica Lab |
| Rango temporal | 2023-2025 (26,304 pasos horarios) |
| Cargadores EV | 50 archivos `charger_X_Y.csv` (mototaxi 4kW/6kWh, motolineal 3kW/4kWh, V2G 7.4kW/40kWh) |
| BESS | 704-15,075 kWh por edificio (sizing real desde areas techadas) |
| Generacion solar PV | 196-5,190 kWp DC por edificio (pvlib SAPM, SunPower SPR-315E) |
| Sistema de AC | Por tipo: Chiller agua (B03/B11), Multi-Chiller (B06), Precision AC (B01/B09), Ultra-Freezers -80C (B17) |
| Factor CO2 | 0.671-0.790 kgCO2/kWh (MINAM RAGEI 2019, diesel ELECTRO ORIENTE) |
| Tarifas | Punta 18-22h: $0.38/kWh; Fuera punta: $0.26/kWh (Electro Oriente 2024) |
| Grilla | Sistema aislado diesel ELECTRO ORIENTE + penetracion solar 15% |
| Archivo central | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json` |

### Edificios del dataset

| ID | Nombre real | Tipo | Area m2 | Sistema AC | kWp PV | BESS kWh |
|---|---|---|---:|---|---:|---:|
| B01 | Electro Oriente S.A. | industrial | 14,000 | DataCenter Precision AC | 1,703 | 4,020 |
| B02 | Municipalidad San Juan Bautista | administrativo | 8,000 | Splits autonomos | 974 | 2,382 |
| B03 | Aeropuerto Internacional Iquitos | transporte_24h | 6,000 | Chiller Central Water-Cooled | 730 | 2,906 |
| B04 | Hipermercados Tottus Oriente | mall | 2,500 | Food Cold Chain + Rooftop | 304 | 2,495 |
| B05 | Hotel Plaza S.A. | hotelero_24h | 1,142 | Commercial Kitchen Cold Rooms | 139 | 1,205 |
| B06 | Mall Aventura Iquitos | mall | 20,637 | Multi-Chiller Plant | 2,511 | 15,075 |
| B07 | UNAP Facultad de Biologia | universitario | 8,103 | Splits autonomos | 986 | 2,550 |
| B08 | PNP Escuela Tecnica Superior | educacion | 21,000 | Splits autonomos | 2,556 | 6,836 |
| B09 | Gobierno Regional Loreto COER | transporte_24h | 4,480 | DataCenter Precision AC (N+1) | 545 | 852 |
| B10 | Gobierno Regional de Loreto | administrativo | 14,296 | Duct Central Split System | 1,740 | 3,964 |
| B11 | Hospital Regional de Loreto | salud_24h | 42,649 | Clinical Chiller + HEPA + Blood Bank | 5,190 | 6,662 |
| B12 | Seguro Social de Salud EsSalud | salud_24h | 18,197 | Medical Archive AC System | 2,215 | 3,159 |
| B13 | UNAP Facultad Ciencias Economicas | universitario | 2,723 | Splits autonomos | 331 | 798 |
| B14 | Autoridad Portuaria Nacional | portuario_24h | 17,761 | Splits autonomos | 2,161 | 5,767 |
| B15 | DREL Colegio Nacional de Iquitos | educacion | 9,890 | Splits autonomos | 1,204 | 3,221 |
| B16 | SIMA Iquitos S.R.Ltda | industrial | 10,294 | Industrial Mobile Vessel AC | 1,253 | 2,497 |
| B17 | Asociacion Civil Selva Amazonica | salud_24h | 1,611 | Scientific Ultra-Freezers -80C | 196 | 1,641 |

### Destilacion desde `buildingcsv`

Los insumos reales estan en `CityLearn/data/buildingcsv/`:

- `building.csv`: nombres oficiales, areas techadas exactas, tipos de uso CityLearn, sistemas de refrigeracion, unidades split estimadas y vehiculos predominantes por edificio.
- `B_02.csv` a `B_17.csv`: mediciones mensuales reales de facturas electricas (kWh punta/fuera punta, total facturado, tarifa).
- `Building_1.csv` sintetico porque no existe `B_01.csv` en buildingcsv.

La destilacion aplica: `NSL_residual = E_medido_mes - cooling_demand/COP - dhw_demand/COP`. Balance mensual garantizado con delta < 0.1%. Meses faltantes pronosticados con `calendar_month_mean_overlap_scaled`.

Documentacion completa del pipeline: `docs/dataset_construction_pipeline.md`.

Regenerar el dataset desde los insumos:

```powershell
# 1. Generar CSV (usa cache meteorologico, no re-descarga)
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/generate_iquitos_dataset.py --verbose

# 2. Destilar cargas reales B02-B17
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/distill_building_loads.py `
    --buildingcsv-dir CityLearn/data/buildingcsv `
    --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025

# 3. Fix safety factor cooling autosize
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/fix_schema_cooling.py

# 4. Diagnostico de integridad
.\.venv39-citylearn-v3\Scripts\python.exe -B diagnostico_dataset.py
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
  --output outputs\citylearn_v3_madrl_iquitos_official_full_cuda_v1\cooperative_ctde_validation.json
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

## Validacion previa al entrenamiento

Antes de lanzar una corrida larga, ejecutar solo verificaciones:

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1

.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\check_citylearn_v3_training_ready.py `
  --strict `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1

.\.venv39-citylearn-v3\Scripts\python.exe -B CityLearn\scripts\run_citylearn_v3_env_smoke.py `
  --schema-path CityLearn\data\datasets\citylearn_iquitos_2023_2025\schema.json `
  --scenario E1 `
  --episode-time-steps 4 `
  --steps 3
```

Validacion actual:

- `python39_core_ready=true` con schema Iquitos.
- `pytest tests/uc3m -q -ra`: OK, con 3 skips existentes.
- `git diff --check`: OK.
- No hay procesos de entrenamiento ni manifiestos `status: running` despues de la limpieza.

## Entrenamiento oficial local

Opcion rapida — doble clic o desde PowerShell:

```powershell
# Genera timestamp automatico y lanza cadena completa
.\relanzar_entrenamiento_madrl.bat
```

Comando completo manual:

```powershell
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$root = "outputs\citylearn_v3_madrl_full_$ts"
Set-Content outputs\latest_visible_training_output_root.txt $root
& scripts\run_citylearn_v3_full_training_visible.ps1 `
  -OutputRoot $root `
  -Scenario ALL `
  -Seed 0 `
  -EpisodeTimeSteps 8760 `
  -Episodes 5 `
  -TorchThreads 12 `
  -LiveProgressInterval 250 `
  -Cuda `
  -LiveOutput
```

Esto genera 12 corridas secuenciales (4 algoritmos x 3 ejes):

```text
HAPPO x E1/E2/E3 -> MASAC x E1/E2/E3 -> MATD3 x E1/E2/E3 -> MAAC x E1/E2/E3
```

Fixes aplicados al launcher:
- `FOR_DISABLE_CONSOLE_CTRL_HANDLER=1`: previene `forrtl: error (200)` al cerrar ventana.
- `PYTHONUNBUFFERED=1`: flush inmediato de stdout a logs.
- Display en tiempo real: episodio, paso, retorno, pesos OE1/OE2/OE3, CO2, precio, historial por episodio.

### Perfil GPU-tuned local (RTX 4060 Laptop 8 GB)

| MADRL | Backend | Ajustes activos |
|---|---|---|
| HAPPO | HARL (on-policy) | `hidden_size=384`, `torch_threads=12`, `team_ratio=0.75` |
| MASAC | MARLlib (off-policy, RNN+QMIX) | `rnn_hidden_dim=64`, `qmix_hidden_dim=32`, `buffer_size=2` |
| MATD3 | off-policy PyTorch | `batch_size=256`, `buffer_size=4096`, `hidden_size=256` |
| MAAC | Attention SAC | `batch_size=64`, `buffer_length=256`, `hidden_size=128`, `attend_heads=4` |

### Herramientas de diagnostico y monitoreo

```powershell
# Verificar integridad del dataset (17 edificios, filas, columnas, chargers)
.\.venv39-citylearn-v3\Scripts\python.exe -B diagnostico_dataset.py

# Ver metricas del ultimo entrenamiento completado
.\.venv39-citylearn-v3\Scripts\python.exe -B ver_metricas_madrl.py

# Ver todos los runs disponibles
.\.venv39-citylearn-v3\Scripts\python.exe -B ver_metricas_madrl.py --todos

# Ver run especifico
.\.venv39-citylearn-v3\Scripts\python.exe -B ver_metricas_madrl.py --run <nombre_run>
```

## Monitor de entrenamiento

```powershell
# Monitor en tiempo real (refresca cada 5 segundos)
$root = Get-Content outputs\latest_visible_training_output_root.txt
powershell -NoProfile -ExecutionPolicy Bypass `
  -File CityLearn\scripts\monitor_citylearn_v3_official_training.ps1 `
  -OutputRoot $root `
  -IntervalSeconds 5 `
  -LogTail 12
```

El monitor muestra: estado global, jobs completados/en cola, pesos OE1/OE2/OE3,
paso/episodio actual, retorno acumulado, CO2, precio electricidad, GPU y logs
filtrados (sin ruido de arrays Box de inicializacion).

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
outputs/citylearn_v3_madrl_iquitos_official_full_cuda_v1/
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
| **Pipeline dataset** (nuevo) | `docs/dataset_construction_pipeline.md` |
| Arquitectura y flujo | `docs/ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md` |
| Destilacion dataset Iquitos | `docs/DATASET_IQUITOS_DESTILACION_CITYLEARN_V3.md` |
| Auditoria tecnica skill MADRL | `docs/AUDITORIA_TECNICA_SKILL_MADRL_CITYLEARN_V3.md` |
| Tutorial notebook | `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` |
| Quickstart notebook | `CityLearn/examples/madrl_citylearn_v3_quickstart.ipynb` |
| Informe de tesis | `docs/INFORME_TESIS_MADRL_V1_COMPLETO.docx` |
| Plan de tesis | `docs/PLAN_TESIS_MADRL_CITYLEARN_V3.docx` |

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
