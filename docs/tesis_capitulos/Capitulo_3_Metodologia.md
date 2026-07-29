# Capítulo 3. Metodología

Este capítulo describe el enfoque metodológico que sustenta la respuesta al objetivo general y a los objetivos específicos OE.1 (flexibilidad energética), OE.2 (emisiones de CO2) y OE.3 (costos energéticos), en coherencia con el Resumen de la tesis. El estudio compara cuatro algoritmos MADRL (HAPPO, MASAC, MATD3 y MAAC) en CityLearn para el caso del SEAI Iquitos, usando un diseño cuasiexperimental de simulación computacional.

## 3.1 Tipo, nivel y diseño de investigación

- **Enfoque:** cuantitativo (Hernández-Sampieri & Mendoza, 2018).
- **Tipo:** aplicada (Arias, 2020; Tamayo y Tamayo, 2004).
- **Nivel:** comparativo y propositivo (con componente descriptivo de KPIs).
- **Diseño:** **cuasiexperimental**, factorial **4×3** (algoritmo MADRL × escenario E1/E2/E3), basado en simulación computacional. Se manipula deliberadamente la variable independiente (algoritmo y pesos de recompensa por escenario) bajo protocolo fijo; no hay asignación aleatoria de unidades naturales ni sujetos humanos, por lo que no corresponde a experimento puro (Campbell & Stanley, 1963; Hernández-Sampieri & Mendoza, 2018).
- **Método:** modelamiento computacional Dec-POMDP/CTDE y simulación en CityLearn (Oliehoek & Amato, 2016; Lowe et al., 2017; Nweye et al., 2024), con contraste interalgoritmo MADRL y análisis no paramétrico.

El nivel comparativo es esencial para identificar el algoritmo de mayor efecto por eje (OE.1, OE.2, OE.3) y para el ranking global; el nivel propositivo se justifica por la implementación de la capa CityLearn v3 de tesis sobre CityLearn v2. En consecuencia, se descarta el rótulo de estudio no experimental, porque la VI se manipula de manera explícita y controlada.

## 3.2 Variables

- **Variable independiente (tratamiento):** algoritmo MADRL (HAPPO, MASAC, MATD3 y MAAC) bajo Dec-POMDP y CTDE, con escenarios E1/E2/E3 (pesos de recompensa por eje). La capa CityLearn v3 es el entorno común del cuasiexperimento, no la VI primaria.
- **Variable dependiente:** desempeño coordinado en flexibilidad energética, emisiones de CO₂ y costos energéticos, medido por KPIs de CityLearn v2 y por recompensa episódica (`reward_mean_average`, `district_emission`, `district_cost`, etc.).
- **Variables de control:** dataset (`citylearn_iquitos_2023_2025`), semilla (seed = 0), horizonte (8 760 pasos/episodio), función de recompensa (`CityLearnV3MADRLRewardFunction`) y hardware.
- **Métricas primarias:** KPIs energéticos/ambientales/económicos y recompensa MADRL. Accuracy, precision, recall y F1 **no** son métricas centrales de este diseño (control continuo, no clasificación); solo se reportarían como auxiliares si se dicotomizara “mejora vs baseline”.

## 3.3 Unidad de análisis, población y muestra

- **Unidad de análisis:** comunidad inteligente simulada (17 edificios SEAI) y agentes MADRL cooperativos. La heterogeneidad Dec-POMDP de observación/acción por edificio (\(d_{o_i}\in[54,327]\), \(d_{a_i}=2+n_i^{\mathrm{ch}}\in[5,44]\), \(d_s=1\,856\)) se detalla en Cap. 2 Tabla 2.A y se operacionaliza en Cap. 4 §4.3.
- **Población:** escenarios simulados con múltiples edificios y DER; series temporales de demanda, precio e intensidad de carbono (2023-2025).
- **Muestreo:** no probabilístico, intencional y técnicamente conveniente, justificado por la disponibilidad del dataset real de Iquitos y la pertinencia técnico-científica de los cuatro algoritmos evaluados (Hernández-Sampieri & Mendoza, 2018).
- **Tamaño de muestra:** 4 algoritmos MADRL + líneas base (CityLearn v2 `baseline`, `hour_rbc`) + comparadores SB3 (PPO/SAC/A2C). Corrida canónica: **≈50 episodios × 8 760 = 438 000 pasos** por job (HAPPO 49/50; MAAC/MASAC/MATD3 50). Semilla única (seed = 0); multi-semilla (≥3) = trabajo futuro. Los episodios **no** son réplicas i.i.d.; constituyen la unidad de contraste episódico bajo dependencia serial.

## 3.4 Datos utilizados — Dataset `citylearn_iquitos_2023_2025`

El dataset se construye **íntegramente desde datos primarios** (no se adoptan datasets pre-existentes de CityLearn v2) por las condiciones irrepresentables del SEAI: red aislada, generación diésel dominante, factor de emisión 0.790 kgCO₂/kWh, clima ecuatorial sin calefacción y tarifas TOU locales.

### 3.4.1 Resumen del dataset (auditado)

| Componente | Valor |
|---|---|
| Edificios | 17 (B01-B17), institucionales/comerciales reales |
| Horizonte | 26 304 horas (2023-2025) |
| CSV activos auditados | 222 (0 NaN / 0 Inf) |
| Cargadores EV (tomas controlables Mode 3) | 185 |
| Equipos físicos Mode 3 (doble toma) | 96 (192 sockets) |
| Tomas V2G bidireccional (camionetas) | 31 |
| EV en pool | 1 850 |
| Potencia EV nominal simultánea | 749.4 kW |
| BESS | 26 266.0 kWh / 6 648.0 kW |
| PV | 48 790.9 kWp |
| Intensidad de carbono | CI ∈ [0.6715, 0.7900] kgCO₂/kWh |
| Precios horarios (pricing.csv) | 0.383220954 – 1.066918914 (RTP); TOU base 0.26 / 0.38 USD/kWh |
| Carga controlada (lavadoras) | 17 máquinas, 876.6 MWh/año |
| Ubicación | lat −3.7491°, lon −73.2538°, alt 106 m, tz America/Lima |

### 3.4.2 Los 17 edificios (dimensionamiento DER)

| ID | Edificio | Tipo CityLearn | Área m² | PV kWp | BESS kWh | BESS kW | EV kW | Cargadores |
|---|---|---|---:|---:|---:|---:|---:|---:|
| B01 | Electro Oriente S.A. | Office | 14 000 | 3 360.2 | 6 747 | 1 609 | 21.8 | 4 |
| B02 | Municip. San Juan Bautista | Office | 8 000 | 1 920.0 | 244 | 50 | 24.4 | 6 |
| B03 | Aeropuerto Internacional | Assembly | 6 000 | 1 440.2 | 2 363 | 511 | 37.8 | 8 |
| B04 | Hipermercados Tottus | Retail | 2 500 | 600.2 | 454 | 409 | 24.4 | 6 |
| B05 | Hotel Plaza S.A. | MultiFamily_Hotel | 1 141.89 | 274.1 | 234 | 124 | 14.4 | 3 |
| B06 | Mall Aventura | Commercial_Mall | 20 637 | 4 952.9 | 2 541 | 835 | 119.6 | 32 |
| B07 | UNAP Biología | Education | 8 103.45 | 1 944.9 | 984 | 240 | 153.2 | 42 |
| B08 | PNP Escuela Técnica | Assembly_Military | 21 000 | 5 040.2 | 601 | 129 | 73.6 | 17 |
| B09 | GORE Loreto COER | Office_Critical | 4 479.67 | 1 075.3 | 138 | 30 | 37.4 | 10 |
| B10 | Gobierno Regional Loreto | Office | 14 295.73 | 3 431.1 | 2 353 | 591 | 36.6 | 6 |
| B11 | Hospital Regional | Healthcare_Hospital | 42 649.33 | 10 236.1 | 1 901 | 424 | 14.4 | 3 |
| B12 | EsSalud | Healthcare | 18 197.48 | 4 367.5 | 4 346 | 960 | 14.4 | 3 |
| B13 | UNAP Cs. Económicas | Education | 2 723 | 653.8 | 272 | 69 | 41.4 | 11 |
| B14 | Autoridad Portuaria | Industrial_Port | 17 761 | 4 262.9 | 229 | 48 | 21.8 | 4 |
| B15 | DREL Colegio Nacional | Education | 9 889.92 | 2 373.8 | 500 | 104 | 31.4 | 8 |
| B16 | SIMA Iquitos | Industrial | 10 294 | 2 470.8 | 1 622 | 357 | 41.4 | 11 |
| B17 | Asoc. Civil Selva Amazónica | Laboratory | 1 611.23 | 386.9 | 737 | 158 | 41.4 | 11 |
| **Totales** | | | | **48 790.9** | **26 266** | **6 648** | **749.4** | **185** |

Las dimensiones Dec-POMDP locales (\(d_{o_i}\), \(d_{a_i}\)) derivadas de esta flota EV se miden en `CityLearnEnv` y se tabulan en Cap. 2 **Tabla 2.A** (rango 54–327 / 5–44; estado CTDE \(d_s=1\,856\)).

### 3.4.3 Fuentes de datos de entrada

- **Meteorología (2023-2025):** PVGIS-ERA5 vía `pvlib` (2023) y NASA POWER REST API (2024-2025); variables T2M, RH2M, irradiancia difusa/directa, WS10M; caché `.cache/weather/{year}.parquet` (Holmgren et al., 2018; NASA POWER, 2024).
- **Consumo eléctrico real:** facturación mensual de Electro Oriente S.A. (2023-2025) destilada a perfiles horarios con `tools/dataset/distill_building_loads.py` (NSL residual = E_medido − cooling/COP − DHW/COP; error de balance mensual < 0.1 %).
- **Señales regulatorias/mercado:** intensidad de carbono CI(t) = 0.790 × (1 − 0.15 × GHI(t)/1000); precios TOU Electro Oriente (0.38 punta / 0.26 fuera de punta) (MINAM, 2019; OSINERGMIN, 2024).

### 3.4.4 Pipeline de construcción (10 etapas)

Implementado en `tools/dataset/generate_iquitos_dataset.py` y orquestado por `tools/dataset/orchestrate_citylearn_dataset.py`: (1) descarga meteorológica; (2) selección de módulo PV Sandia (η≥18 %, montaje fijo 5°, IEC 61730); (3) serie solar por edificio (`pvlib.ModelChain`, SAPM); (4) dimensionamiento BESS por balance energético (Hesse et al., 2017; Little, 1961); (5) `Building_X.csv` (12 columnas, 26 304 filas); (6) 185 `charger_X_Y.csv` (`tools/dataset/dimension_ev_chargers.py`, Ley de Little); (7) 17 `Washing_Machine_X.csv`; (8) `weather.csv`/`carbon_intensity.csv`/`pricing.csv`; (9) `schema.json` (`SchemaBuilder`); (10) validación con `CityLearnEnv` (Nweye et al., 2024).

### 3.4.5 Compuertas de validación (gates)

`tools/dataset/check_training_dataset_ready.py`, `tools/dataset/audit_citylearn_csv_integrity.py`, `tools/ops/verify_workflow_integrity.py` y `tools/dataset/audit_der_sizing.py` producen manifiestos en `outputs/dataset_audit/` (`training_dataset_ready_manifest.json`, `csv_integrity_manifest.json`, `der_sizing_audit.json`, `iquitos_citylearn_v3_dataset_evaluation.json`). Aceptación: `status=ready`, 0 NaN/Inf, sin cargadores/máquinas huérfanos.

### 3.4.6 Árbol CityLearn retenido: usados vs disponibles (reproducibilidad)

El submódulo `CityLearn/` conserva, además del dataset Iquitos, el **árbol de datos del ecosistema CityLearn v2** embebido en el fork de la tesis. Ese material **no se elimina** (decisión 2026-07-29): sirve de contexto metodológico, integridad de pruebas del paquete y reproducibilidad offline del simulador. El **caso empírico de contraste de hipótesis (Caps. 5)** sigue siendo exclusivamente `citylearn_iquitos_2023_2025` + capa MADRL v3.

| Recurso en `CityLearn/data/datasets/` | Rol metodológico | Uso en esta tesis |
|---|---|---|
| `citylearn_iquitos_2023_2025/` | Dataset primario SEAI (17 edificios, 2023–2025) | **Empírico canónico** (OE.1–OE.3; 12 corridas) |
| `citylearn_challenge_2020_*` … `2023_*` | Challenges históricos de benchmarking comunitario (Nweye et al., 2023c, 2024) | **Contexto / reproducibilidad**; challenge 2022 (+EV) y demos alimentan tests del submódulo; **sin** tablas Cap. 5 |
| `quebec_neighborhood_*`, `ca_alameda_county_neighborhood`, `tx_travis_county_neighborhood`, `vt_chittenden_county_neighborhood` | Barrios de referencia del paquete CityLearn (climas y mercados distintos al SEAI aislado) | **Inventario reproducible**; contraste cualitativo con Iquitos; **sin** entrenamientos MADRL reportados aquí |
| `baeda_3dem/`, `citylearn_three_phase_electrical_service_demo/` | Suites de prueba del simulador | Integridad del submódulo (no evidencia de hipótesis) |

Detalle de retención e integración: `docs/INTEGRACION_CITYLEARN_THESIS_2026-07-29.md`. **No** se atribuyen KPIs ni pruebas estadísticas a barrios o challenges upstream en ausencia de artefactos en `outputs/`.

## 3.5 Técnicas e instrumentos

### 3.5.1 Técnicas de recolección
Revisión bibliográfica sistemática (50 antecedentes), extracción/preprocesamiento del dataset, y registro de artefactos por corrida: `live_progress.json`, `results.json`, `timeseries.csv`, `trace.csv`, `training_summary.json`, `artifact_audit.json`, `checkpoint_manifest.json`.

### 3.5.2 Técnicas de análisis
- KPIs por eje vía `env.evaluate_v2()` de CityLearn v2.
- Comparación inter-algoritmo por KPI y ranking integrado (`compare_citylearn_v2_vs_v3_madrl.py`, `generate_thesis_objective_evidence.py`).
- **Pruebas estadísticas no paramétricas** (justificadas por rechazo de normalidad Shapiro-Wilk; alpha = 0,05):
  - **Kruskal–Wallis:** diferencia global entre algoritmos (omnibus).
  - **Mann–Whitney U** con Holm: pares independientes; tamaños de efecto Cliff's δ, Vargha–Delaney A12, Cohen d, Hedges g.
  - **Wilcoxon signed-rank:** pares pareados por KPI (exploratorio).
  - **Friedman:** solo si hubiera ≥3 semillas (bloques); **no aplicable** con seed única.
- El uso de pruebas no paramétricas y reporte de tamaño de efecto sigue recomendaciones para comparación robusta de algoritmos de aprendizaje por refuerzo (Demšar, 2006; Agarwal et al., 2021).
- **Dos capas de evidencia (no fusionar):** (A) series episódicas OE-alineadas (`gdrive_objective_aligned_statistics.csv`); (B) KPI-gains de entrenamiento (`hipotesis_estadisticas_madrl.csv`). Suite materializada también en `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb` (celdas 8.1 y 9.1).

### 3.5.3 Instrumentos (software)
Python 3.9 (`.venv39-citylearn-v3`), PyTorch 2.8.0+cu126, CUDA 12.6, CityLearn v2/v3, backends `external/HARL`, `external/MARL/src`, `external/off-policy`, `external/MAAC`; Gymnasium, PettingZoo; MARLlib (referencia) y Optuna (HPO previsto).

## 3.6 Procedimiento experimental

1. **Verificación de contexto:** `scripts/verify_project_context.ps1` (obligatorio antes de editar/entrenar).
2. **Construcción y validación del dataset** (gates anteriores).
3. **Entrenamiento de 12 corridas** (4 algoritmos × 3 escenarios). En el plano local de validación se lanzan con `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` (wrapper `scripts/run_citylearn_v3_full_training_visible.ps1`) bajo una política de concurrencia para 8 GB de VRAM (`MaxConcurrentScenarioJobs=2`, MASAC/MAAC limitados a 1). La corrida canónica de 50 episodios se ejecuta en Google Colab con `CityLearn/scripts/colab_a100_official_launcher.py` bajo el protocolo `two_phase_happo_masac_v3`: una primera fase entrena HAPPO y MASAC y una segunda fase MATD3 y MAAC, con seis trabajos en paralelo por fase. El notebook `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb` (celdas 0.verify, 6.1 y 7.x) fija como objetivo primario una GPU NVIDIA H100 (~26 vCPU, ~2× más rápida) y declara compatibles NVIDIA A100-SXM4-80GB (12 vCPU) y RTX PRO 6000 Blackwell (96 GiB), con autoajuste de hilos por fase a las vCPU del *runtime* (A100: torch=1/rollout=2 en Fase 1, torch=2 en Fase 2; H100: torch=2/rollout=4 en Fase 1, torch=4 en Fase 2) y un tiempo de pared estimado de ~20 h para las doce corridas. La corrida es reanudable con `--skip-completed` (omite *jobs* con `results.json`) y reintentos ante OOM, persistiendo los artefactos en Google Drive (`MyDrive/MADRLCitytleranflexresdr/outputs/madrl_v3_<timestamp>/`, con subcarpetas `{ALGORITMO}/E{1,2,3}/`).
4. **Monitoreo:** `monitor_citylearn_v3_official_training.ps1` (GPU, global_step, reward, KPIs). Los scripts `launch_citylearn_v3_iquitos_training.ps1` / `monitor_citylearn_v3_iquitos_training.ps1` se **retienen** como launchers históricos del pipeline Iquitos; no sustituyen al launcher *official* ni al protocolo Colab de 50 episodios.
5. **Benchmark v2** (`benchmark_citylearn_v2_agents.py`: `baseline`, `hour_rbc`) y comparadores SB3, sobre el **schema Iquitos** (no sobre barrios upstream).
6. **Comparación v2 vs v3** y **evidencia de tesis** (KPIs, estadística, figuras).
7. **Determinación del mejor MADRL** por eje y global (Borda/score ponderado), con la línea obligatoria *"Mejor algoritmo MADRL seleccionado: …"*.

| Fase | Actividades | Meses |
|---|---|---|
| Preparatoria | Revisión bibliográfica, diagnóstico, dataset y KPIs | 1-3 |
| Diseño técnico | Arquitectura v3, Dec-POMDP, CTDE, backends, Optuna | 4-8 |
| Evaluación por eje | Entrenamiento E1/E2/E3 × 4 algoritmos, KPIs OE.1/2/3 | 9-18 |
| Determinación y cierre | Comparación, ranking, estadística, redacción | 19-24 |

---

### Estado del capítulo
**Veredicto metodológico aplicado (2026-07-29):** §3.1–3.6 alineados al Resumen (HAPPO, MASAC, MATD3, MAAC; CityLearn; Iquitos; OE.1/OE.2/OE.3) con diseño **cuasiexperimental** factorial 4×3, citas APA en tipología/diseño/datos/estadística, VI = algoritmo MADRL y dos capas inferenciales. Multi-semilla experimental permanece como H2. **§3.4.6** documenta el árbol CityLearn retenido (barrios/challenges/launchers) como reproducibilidad, sin resultados fantasma.
