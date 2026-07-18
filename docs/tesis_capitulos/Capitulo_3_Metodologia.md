# Capítulo 3. Metodología

> **Documento de tesis — borrador integral alineado para Perplexity.** Datos tomados del Plan de Tesis (§4), `docs/INFORME_EVALUACION_FINAL_DATASET_IQUITOS_CITYLEARN_V3.md`, `docs/workflow_manifest.json`, `CityLearn/configs/citylearn_v3_madrl_training.yaml`, el pipeline `tools/generate_iquitos_dataset.py` / `tools/orchestrate_citylearn_dataset.py`, auditorías en `outputs/dataset_audit/` y el notebook `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` (procedimiento de entrenamiento canónico en Colab A100). Cifras reales verificadas. No inventar datos.

---

## ░░ PROMPT PARA PERPLEXITY (versión final) ░░

**Rol / Contexto:** Eres metodólogo de investigación cuantitativa aplicada e ingeniería energética. Pules el **Capítulo 3 (Metodología)** de la tesis UNI sobre MADRL + CityLearn v3 en el SEAI Iquitos.

**Objetivo del prompt:** Redacción metodológica formal en español, con:
1. Coherencia entre tipo/diseño de investigación, variables, técnicas e instrumentos.
2. **Citas APA** consistentes con `Referencias_APA.md` (CityLearn, pvlib, NASA POWER, MINAM, OSINERGMIN, Optuna).
3. Descripción reproducible del **dataset Iquitos** (fuentes, pipeline de 10 etapas, dimensionamiento DER) y del procedimiento experimental (12 corridas).
4. Completar `[Pendiente: ...]` solo si se infiere del proyecto.

**Instrucciones específicas:** (a) explicitar variable independiente/dependiente; (b) describir el muestreo no probabilístico intencional y su justificación; (c) precisar las cuatro pruebas estadísticas; (d) no alterar cifras del dataset (17 edificios, 222 CSV, 26 304 h, 185 cargadores, BESS 26 266 kWh / 6 648 kW, PV 48 790.9 kWp).

---

## 3.1 Tipo y nivel de investigación

- **Enfoque:** cuantitativo (Hernández-Sampieri et al.).
- **Tipo:** aplicada (Tamayo y Tamayo; Arias).
- **Nivel:** comparativo y propositivo (con componente descriptivo de KPIs).
- **Diseño:** **cuasiexperimental**, factorial **4×3** (algoritmo MADRL × escenario E1/E2/E3), basado en simulación computacional. Se manipula deliberadamente la variable independiente (algoritmo y pesos de recompensa por escenario) bajo protocolo fijo; **no** hay aleatorización de unidades naturales ni sujetos humanos, por lo que no constituye experimento puro (Campbell & Stanley vía Hernández-Sampieri; Bunge sobre experimentación/simulación controlada).
- **Método:** modelamiento computacional Dec-POMDP/CTDE, simulación CityLearn v2/v3, comparación de algoritmos MADRL y análisis no paramétrico de KPIs y recompensa.

El nivel **comparativo** es esencial (identificar el MADRL líder por eje y el ranking integrado); el nivel **propositivo** se justifica porque CityLearn v3 es una extensión arquitectónica original sobre CityLearn v2. Se descarta el rótulo “no experimental” porque la VI se manipula sistemáticamente.

## 3.2 Variables

- **Variable independiente (tratamiento):** algoritmo MADRL — HAPPO, MASAC, MATD3 y MAAC — bajo Dec-POMDP y CTDE, con escenarios E1/E2/E3 (pesos de recompensa por eje). La capa CityLearn v3 es el **entorno común** del cuasiexperimento, no la VI primaria.
- **Variable dependiente:** desempeño coordinado en flexibilidad energética, emisiones de CO₂ y costos energéticos, medido por KPIs de CityLearn v2 y por recompensa episódica (`reward_mean_average`, `district_emission`, `district_cost`, etc.).
- **Variables de control:** dataset (`citylearn_iquitos_2023_2025`), semilla (seed = 0), horizonte (8 760 pasos/episodio), función de recompensa (`CityLearnV3MADRLRewardFunction`) y hardware.
- **Métricas primarias:** KPIs energéticos/ambientales/económicos y recompensa MADRL. Accuracy, precision, recall y F1 **no** son métricas centrales de este diseño (control continuo, no clasificación); solo se reportarían como auxiliares si se dicotomizara “mejora vs baseline”.

## 3.3 Unidad de análisis, población y muestra

- **Unidad de análisis:** comunidad inteligente simulada (17 edificios SEAI) y agentes MADRL cooperativos.
- **Población:** escenarios simulados con múltiples edificios y DER; series temporales de demanda, precio e intensidad de carbono (2023-2025).
- **Muestreo:** no probabilístico, intencional y técnicamente conveniente, justificado por la disponibilidad del dataset real de Iquitos y la pertinencia de los cuatro algoritmos.
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

### 3.4.3 Fuentes de datos de entrada

- **Meteorología (2023-2025):** PVGIS-ERA5 vía `pvlib` (2023) y NASA POWER REST API (2024-2025); variables T2M, RH2M, irradiancia difusa/directa, WS10M; caché `.cache/weather/{year}.parquet`.
- **Consumo eléctrico real:** facturación mensual de Electro Oriente S.A. (2023-2025) destilada a perfiles horarios con `tools/distill_building_loads.py` (NSL residual = E_medido − cooling/COP − DHW/COP; error de balance mensual < 0.1 %).
- **Señales regulatorias/mercado:** intensidad de carbono CI(t) = 0.790 × (1 − 0.15 × GHI(t)/1000); precios TOU Electro Oriente (0.38 punta / 0.26 fuera de punta).

### 3.4.4 Pipeline de construcción (10 etapas)

Implementado en `tools/generate_iquitos_dataset.py` y orquestado por `tools/orchestrate_citylearn_dataset.py`: (1) descarga meteorológica; (2) selección de módulo PV Sandia (η≥18 %, montaje fijo 5°, IEC 61730); (3) serie solar por edificio (`pvlib.ModelChain`, SAPM); (4) dimensionamiento BESS por balance energético (Hesse et al., 2017; DoD 0.80, η_RT 0.9025); (5) `Building_X.csv` (12 columnas, 26 304 filas); (6) 185 `charger_X_Y.csv` (`tools/dimension_ev_chargers.py`, Ley de Little); (7) 17 `Washing_Machine_X.csv`; (8) `weather.csv`/`carbon_intensity.csv`/`pricing.csv`; (9) `schema.json` (`SchemaBuilder`); (10) validación con `CityLearnEnv`.

### 3.4.5 Compuertas de validación (gates)

`tools/check_training_dataset_ready.py`, `tools/audit_citylearn_csv_integrity.py`, `tools/verify_workflow_integrity.py` y `tools/audit_der_sizing.py` producen manifiestos en `outputs/dataset_audit/` (`training_dataset_ready_manifest.json`, `csv_integrity_manifest.json`, `der_sizing_audit.json`, `iquitos_citylearn_v3_dataset_evaluation.json`). Aceptación: `status=ready`, 0 NaN/Inf, sin cargadores/máquinas huérfanos.

## 3.5 Técnicas e instrumentos

### 3.5.1 Técnicas de recolección
Revisión bibliográfica sistemática (50 antecedentes), extracción/preprocesamiento del dataset, y registro de artefactos por corrida: `live_progress.json`, `results.json`, `timeseries.csv`, `trace.csv`, `training_summary.json`, `artifact_audit.json`, `checkpoint_manifest.json`.

### 3.5.2 Técnicas de análisis
- KPIs por eje vía `env.evaluate_v2()` de CityLearn v2.
- Comparación inter-algoritmo por KPI y ranking integrado (`compare_citylearn_v2_vs_v3_madrl.py`, `generate_thesis_objective_evidence.py`).
- **Pruebas estadísticas no paramétricas** (justificadas por rechazo de normalidad Shapiro–Wilk; α = 0,05):
  - **Kruskal–Wallis:** diferencia global entre algoritmos (omnibus).
  - **Mann–Whitney U** con Holm: pares independientes; tamaños de efecto Cliff's δ, Vargha–Delaney A12, Cohen d, Hedges g.
  - **Wilcoxon signed-rank:** pares pareados por KPI (exploratorio).
  - **Friedman:** solo si hubiera ≥3 semillas (bloques); **no aplicable** con seed única.
- **Dos capas de evidencia (no fusionar):** (A) series episódicas OE-alineadas (`gdrive_objective_aligned_statistics.csv`); (B) KPI-gains de entrenamiento (`hipotesis_estadisticas_madrl.csv`). Suite materializada también en `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` (celdas 8.1 y 9.1).

### 3.5.3 Instrumentos (software)
Python 3.9 (`.venv39-citylearn-v3`), PyTorch 2.8.0+cu126, CUDA 12.6, CityLearn v2/v3, backends `external/HARL`, `external/MARL/src`, `external/off-policy`, `external/MAAC`; Gymnasium, PettingZoo; MARLlib (referencia) y Optuna (HPO previsto).

## 3.6 Procedimiento experimental

1. **Verificación de contexto:** `scripts/verify_project_context.ps1` (obligatorio antes de editar/entrenar).
2. **Construcción y validación del dataset** (gates anteriores).
3. **Entrenamiento de 12 corridas** (4 algoritmos × 3 escenarios). En el plano local de validación se lanzan con `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` (wrapper `scripts/run_citylearn_v3_full_training_visible.ps1`) bajo una política de concurrencia para 8 GB de VRAM (`MaxConcurrentScenarioJobs=2`, MASAC/MAAC limitados a 1). La corrida canónica de 50 episodios se ejecuta en Google Colab con `CityLearn/scripts/colab_a100_official_launcher.py` bajo el protocolo `two_phase_happo_masac_v3`: una primera fase entrena HAPPO y MASAC y una segunda fase MATD3 y MAAC, con seis trabajos en paralelo por fase. El notebook `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` (celdas 0.verify, 6.1 y 7.x) fija como objetivo primario una GPU NVIDIA H100 (~26 vCPU, ~2× más rápida) y declara compatibles NVIDIA A100-SXM4-80GB (12 vCPU) y RTX PRO 6000 Blackwell (96 GiB), con autoajuste de hilos por fase a las vCPU del *runtime* (A100: torch=1/rollout=2 en Fase 1, torch=2 en Fase 2; H100: torch=2/rollout=4 en Fase 1, torch=4 en Fase 2) y un tiempo de pared estimado de ~20 h para las doce corridas. La corrida es reanudable con `--skip-completed` (omite *jobs* con `results.json`) y reintentos ante OOM, persistiendo los artefactos en Google Drive (`MyDrive/MADRLCitytleranflexresdr/outputs/madrl_v3_<timestamp>/`, con subcarpetas `{ALGORITMO}/E{1,2,3}/`).
4. **Monitoreo:** `monitor_citylearn_v3_official_training.ps1` (GPU, global_step, reward, KPIs).
5. **Benchmark v2** (`benchmark_citylearn_v2_agents.py`: `baseline`, `hour_rbc`) y comparadores SB3.
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
**Veredicto metodológico aplicado (2026-07-18):** §3.1–3.2 y 3.5.2 alineados a diseño cuasiexperimental 4×3, VI = algoritmo MADRL, dos capas inferenciales y exclusión de accuracy/F1 como métricas primarias. Multi-semilla experimental permanece como H2.
