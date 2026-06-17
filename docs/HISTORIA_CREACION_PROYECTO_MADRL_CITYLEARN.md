# Historia de Creación del Proyecto — MADRL CityLearn v3 Iquitos

**Proyecto:** Multi-agente de aprendizaje por refuerzo profundo para gestión coordinada de flexibilidad energética, emisiones de carbono y costos energéticos en comunidades inteligentes  
**Autor:** Mac Tapia — mac.tapia@unmsm.edu.pe  
**Universidad:** Universidad Nacional Mayor de San Marcos (UNMSM) — Maestría  
**Caso de estudio:** Sistema Eléctrico Aislado de Iquitos (SEAI), Electro Oriente S.A., Loreto, Perú  
**Repositorio principal:** `d:\MADRLCitytleranflexresdr`  
**Total de commits registrados:** 78 (2026-05-03 al 2026-06-15)

---

## 1. Contexto del Proyecto

El proyecto surge de la necesidad de gestionar de forma coordinada los recursos energéticos distribuidos (DERs) en 17 edificios institucionales y comerciales reales de Iquitos, Perú. La red eléctrica de Iquitos es un sistema aislado (no conectado al SEIN) operado por Electro Oriente S.A., alimentado principalmente por generadores diésel con penetración solar creciente (~15% en 2022-2023), con una intensidad de carbono base de 0.790 kgCO₂/kWh. La tesis plantea comparar cuatro algoritmos MADRL (HAPPO, MASAC, MATD3, MAAC) sobre tres objetivos específicos (flexibilidad energética, reducción de CO₂, optimización de costos) usando CityLearn v2 como simulador base extendido con una capa CityLearn v3 propia.

---

## 2. Línea de Tiempo del Proyecto

### Fase 1 — Arranque y workspace inicial (2026-05-03)

| Commit | Descripción |
|---|---|
| `Save CityLearn v3 MADRL thesis workspace` | Primer commit del repositorio. Establece el espacio de trabajo. |
| `Add CityLearn fork submodule reference` | Se añade CityLearn como submódulo fork. |
| `Track full MADRL CityLearn project` | Se incorpora la estructura completa del proyecto. |
| `Add CityLearn v3 MADRL architecture and contribution docs` | Primeros documentos de arquitectura y contribuciones. |
| `Add CityLearn v2 benchmark comparison protocol` | Protocolo de comparación v2 vs v3. |
| `Add thesis plan DOCX generator and document` | Plan de tesis formal. |
| `Update CityLearn MADRL tutorial notebook` | Notebooks iniciales de entrenamiento. |
| `Add project README` | README principal del proyecto. |

### Fase 2 — Configuración de entrenamiento y perfiles de recompensa (2026-05-04 a 2026-05-05)

| Commit | Descripción |
|---|---|
| `Add CityLearn v3 MADRL CLI/load/quickstart notebooks` | Tres notebooks de entrada al entorno MADRL. |
| `Align MADRL training JSON and YAML configs` | Alineación de configuración de entrenamiento. |
| `Document MADRL reward profile architecture` | Documentación de la arquitectura de recompensa multiobjetivo. |
| `Update MASAC stable profile in project README` | Perfil estable de MASAC. |
| `Add MADRL skill technical audit` | Auditoría técnica del skill de tesis. |
| `Integrate literature review skill for scientific support` | Soporte bibliográfico automatizado. |

### Fase 3 — Evidencia experimental y arquitectura 17 agentes (2026-05-09 a 2026-05-14)

| Commit | Descripción |
|---|---|
| `Add thesis document generation with real MADRL experimental results` | Generación de documento con resultados reales. |
| `Replace all NC placeholders with specific APA in-text citations` | Normalización bibliográfica APA. |
| `Document 17-building/17-agent MADRL architecture from real config` | Arquitectura real de 17 edificios documentada. |
| `Add per-building KPI tables (17 agentes) to §3.3 of thesis` | Tablas KPI por edificio. |
| `Add MADRL statistical hypothesis evidence` | Suite de pruebas estadísticas (KW, MWU, Wilcoxon). |

### Fase 4 — Submódulos externos y framework UC3M (2026-05-21 a 2026-05-22)

| Commit | Descripción |
|---|---|
| `Add UC3M framework, tests, tools and reference submodules` | **Incorporación masiva de submódulos externos** (HARL, MAAC, MARL, MARLlib, MATD3, MicroGrids, prosumpy). |
| `Update CityLearn submodule to include Iquitos dataset and training scripts` | Dataset Iquitos integrado en submódulo. |
| `Update CityLearn submodule: add Shapiro-Wilk and Wilcoxon signed-rank tests` | Pipeline estadístico 4 pruebas. |
| `Update CityLearn submodule: complete 4-test hypothesis pipeline` | Pipeline completo. |
| `Update README: document UC3M framework, Iquitos dataset and 4 statistical tests` | Documentación del framework. |

### Fase 5 — Dataset real de Iquitos y herramientas de auditoría (2026-06-01 a 2026-06-08)

| Commit | Descripción |
|---|---|
| `Document Iquitos distillation and MADRL readiness` | Dataset destilado y listo para MADRL. |
| `Update Iquitos dataset with real building data and add diagnostic tools` | Datos de edificios reales incorporados. |
| `Update README: real building data, new tools, training status 2026-06-04` | Estado con datos reales. |
| `Add thesis plan (Plan de Tesis) under Guide N. 01 structure` | Estructura formal plan de tesis. |
| `Orchestrate and validate CityLearn Iquitos dataset` | Orquestación y validación completa del dataset. |

### Fase 6 — Validación EV/BESS, documentación metodológica y entrenamiento paralelo (2026-06-12)

| Commit | Descripción |
|---|---|
| `Update MADRL workflow documentation` | Flujo operativo documentado. |
| `Update Iquitos EV/BESS workflow validation` | Validación cargadores EV Mode 3 y BESS. |
| `Enable visible parallel MADRL training` | Habilitado entrenamiento paralelo con monitor visible. |
| `Document MADRL cooperation, district control and multi-objective methodology` | Documento de cooperación CTDE y metodología. |
| `Add inline APA citations and expand references in COOPERACION doc` | Soporte bibliográfico expandido. |

### Fase 7 — Aportes originales al motor + primera corrida completa (2026-06-13)

| Commit | Descripción |
|---|---|
| `Update CityLearn submodule: fix ScenarioManager pricing truncation bug` | Corrección bug de truncado de precios. |
| `docs(thesis): 4 aportes al motor simulación CityLearn + documentación académica` | **Documentación de los 4 aportes originales** al motor de simulación. |
| `docs(thesis): actualizar documentación con sección 4.10.4 y Módulo G` | Actualización tesis. |
| `Publish workflow docs and reward validation` | Publicación docs de flujo operativo y validación. |
| `Resume MASAC / Optimize MASAC backend runtime / Reduce MASAC CPU overhead` | Optimización y reanudación MASAC. |

### Fase 8 — Perfiles EV, V2G y re-run definitivo v4 (2026-06-14 a 2026-06-15)

| Commit | Descripción |
|---|---|
| `Document reinforced EV SOC reward profile` | Perfil de recompensa EV urgencia SOC. |
| `Validate camioneta V2G workflow` | Validación workflow V2G (camioneta eléctrica). |
| `Update CityLearn submodule: fix V2G ev_type_code observation alignment` | Fix alineación observación EV. |
| `Definitive v4 training: BESS penalty + EV urgency + full re-run` | **Re-run definitivo** con función de recompensa v4 (penalidad BESS + urgencia EV). |
| `Migrate all docs from reward profile v2 to v3` | Migración documentación a perfil v3. |
| `Add AWS training manual and launch scripts` | Manual de entrenamiento en AWS. |

---

## 3. Repositorios Clonados y Submódulos

### 3.1 CityLearn — Fork principal del simulador

| Campo | Valor |
|---|---|
| Fork origen | `https://github.com/intelligent-environments-lab/CityLearn` |
| Fork propio | `https://github.com/Mac-Tapia/CityLearn.git` |
| Rama de trabajo | `citylearn-v3-madrl` |
| Ruta en proyecto | `CityLearn/` (raíz del submodulo) |
| Commit referenciado | `54b1938e` (con 4 aportes originales al motor) |
| Propósito | Simulador base de energía en edificios. Extendido con capa MADRL v3, 17 edificios Iquitos, EV/V2G, reward multiobjetivo, scripts de entrenamiento y validación. |

### 3.2 Algoritmos MADRL — Forks de implementaciones académicas

| Submódulo | Fork propio | Repositorio original | Commit usado | Propósito en proyecto |
|---|---|---|---|---|
| `external/HARL` | `github.com/Mac-Tapia/HARL.git` | `github.com/PKU-MARL/HARL` | `b1af98b0` | Backend para HAPPO y variantes on-policy heterogéneas. Wrapper: `CityLearnHARLEnv`. |
| `external/MARL` | `github.com/Mac-Tapia/MARL.git` | `github.com/puyuan1996/MARL` | `3bda2edc` | Backend para MASAC con QMIX. Wrapper: `CityLearnSMACDiscreteEnv`. |
| `external/MAAC` | `github.com/Mac-Tapia/MAAC.git` | `github.com/shariqiqbal2810/MAAC` | `6174a012` | Backend para actor-attention-critic. Wrapper: `CityLearnMAACVecEnv`. |
| `external/MATD3implementation` | `github.com/Mac-Tapia/MATD3implementation.git` | `github.com/JohannesAck/MATD3implementation` | `fd6c7d0d` | Repositorio MATD3 clonado. **No es el backend activo** de entrenamiento. |
| `external/MARLlib` | `github.com/Mac-Tapia/MARLlib.git` | `github.com/Replicable-MARL/MARLlib` | `80e9973a` | Compatibilidad MARLlib. Wrapper: `marllib_env.py`. **No usado en launcher oficial.** |

### 3.3 Backend MATD3 activo — off-policy (no en .gitmodules)

| Campo | Valor |
|---|---|
| Ruta | `external/off-policy` |
| Repositorio origen | `https://github.com/marlbenchmark/off-policy` |
| Commit | `41fd5eb4`, rama `release` |
| Propósito | Backend **activo** de entrenamiento MATD3. Wrapper: `CityLearnOffPolicyVecEnv`. Sustituye a `MATD3implementation` por compatibilidad Python 3.9. |

### 3.4 Infraestructura complementaria

| Submódulo | Fork propio | Repositorio original | Propósito |
|---|---|---|---|
| `external/MicroGrids` | `github.com/Mac-Tapia/MicroGrids.git` | — | Referencia de modelado de microrredes. |
| `external/evcc` | `github.com/evcc-io/evcc.git` (upstream) | `github.com/evcc-io/evcc` | Referencia para workflow EV/V2G y carga inteligente. |
| `external/prosumpy` | `github.com/Mac-Tapia/prosumpy.git` | — | Referencia de modelado de prosumidores energéticos. |

---

## 4. Módulo CityLearn v3 — Creado desde Cero

Todos los archivos del módulo `CityLearn/citylearn/v3/` son **creados originalmente** para este proyecto. No existen en el CityLearn upstream.

| Archivo | Propósito |
|---|---|
| `__init__.py` | Expone el módulo v3. |
| `environment.py` | Entorno CityLearn v3 extendido para MADRL. Dec-POMDP, CTDE, gestión de escenarios. |
| `objectives.py` | Definición de OE1 (flexibilidad), OE2 (CO₂), OE3 (costos). KPIs por eje y métricas de proyecto. |
| `config.py` | Configuración de entrenamiento v3: perfiles, algoritmos, escenarios, backends. |
| `backends.py` | Compatibilidad de backends MADRL con el entorno v3. |
| `marllib_env.py` | Wrapper de compatibilidad con MARLlib (disponible, no activo en launcher oficial). |

---

## 5. Archivos Python Creados en CityLearn/scripts/

Scripts de entrenamiento, validación y evaluación creados desde cero para el proyecto.

### 5.1 Scripts de entrenamiento MADRL (4 algoritmos)

| Archivo | Algoritmo | Wrapper | Backend |
|---|---|---|---|
| `train_citylearn_v3_happo.py` | HAPPO | `CityLearnHARLEnv` | `external/HARL` |
| `train_citylearn_v3_masac.py` | MASAC | `CityLearnSMACDiscreteEnv` | `external/MARL/src` |
| `train_citylearn_v3_matd3.py` | MATD3 | `CityLearnOffPolicyVecEnv` | `external/off-policy` |
| `train_citylearn_v3_maac.py` | MAAC | `CityLearnMAACVecEnv` | `external/MAAC` |

### 5.2 Scripts de validación y verificación

| Archivo | Propósito |
|---|---|
| `check_citylearn_v3_training_ready.py` | Gate de validación previo al entrenamiento. Verifica dataset, configuración y entorno. |
| `run_citylearn_v3_env_smoke.py` | Smoke test: carga el entorno y ejecuta N pasos sin entrenamiento real. |
| `validate_citylearn_v3_cooperative_ctde.py` | Valida el contrato cooperativo CTDE: 17 agentes, reward aggregation, estado global. |
| `validate_citylearn_v3_objectives.py` | Valida que los objetivos OE1/OE2/OE3 estén correctamente configurados. |
| `validate_citylearn_v3_reward_profiles.py` | Verifica los perfiles de recompensa por algoritmo y escenario. |

### 5.3 Scripts de evaluación y comparación

| Archivo | Propósito |
|---|---|
| `benchmark_citylearn_v2_agents.py` | Ejecuta agentes originales CityLearn v2 (baseline, hour_rbc) con el mismo dataset Iquitos. |
| `compare_citylearn_v2_vs_v3_madrl.py` | Compara resultados v2 vs v3 MADRL: delta, mejora %, Score_OG, ranking Borda, Pareto. |
| `generate_thesis_objective_evidence.py` | Genera evidencia consolidada de tesis: matrices de KPIs, análisis estadístico (KW, MWU, Wilcoxon). |
| `generate_citylearn_v3_building_detail_report.py` | Reporte detallado por edificio: KPIs individuales, BESS, EV, PV. |
| `regenerate_citylearn_v3_figures.py` | Regenera figuras de entrenamiento a partir de artefactos existentes. |

### 5.4 Scripts de optimización

| Archivo | Propósito |
|---|---|
| `masac_runtime_optimizations.py` | Optimizaciones de runtime para MASAC: gestión de replay buffer, batch preload, CPU/GPU balance. |
| `citylearn_v3_training_common.py` | Adaptador común Dec-POMDP/CTDE. Normalización, KPIs, trazas, figuras, tablas, metadatos. Usado por los 4 scripts de entrenamiento. |

---

## 6. Archivos Python Creados en tools/ (30 herramientas)

Todas las herramientas en `tools/` son creadas desde cero para el proyecto.

### 6.1 Generación y construcción del dataset Iquitos

| Archivo | Propósito |
|---|---|
| `generate_iquitos_dataset.py` | Generación del dataset base: series horarias de 17 edificios reales (2023-2025). |
| `orchestrate_citylearn_dataset.py` | Orquestador principal del pipeline completo de dataset. Sincroniza todos los componentes. |
| `calibrate_buildings.py` | Calibración de perfiles de consumo por edificio con datos reales. |
| `dimension_ev_chargers.py` | Dimensionamiento de 185 tomas EV Mode 3 por edificio, tipo y concurrencia. |
| `size_bess_optimal.py` | Dimensionamiento óptimo de BESS: balance por edificio con PV, carga, EV y red. |
| `distill_building_loads.py` | Destilación de cargas de edificios desde datos brutos históricos. |
| `fix_solar_pvlib.py` | Corrección de generación solar usando pvlib con datos PVGIS TMY. |
| `rebuild_per_building_profiles.py` | Reconstrucción de perfiles de consumo por edificio. |
| `sync_controlled_machines.py` | Sincronización de perfiles de lavadoras/cargas controladas (17 máquinas). |
| `fix_and_validate.py` | Corrección y validación de inconsistencias en el dataset. |
| `fix_schema_cooling.py` | Corrección de parámetros de enfriamiento en el schema JSON. |
| `buildingcsv_inputs.py` | Generación de CSV de entrada para cada edificio. |
| `generate_b01_billing.py` | Generación de perfil de facturación para el edificio B01 (Electro Oriente). |

### 6.2 Auditoría e integridad del dataset

| Archivo | Propósito |
|---|---|
| `audit_citylearn_csv_integrity.py` | Auditoría de integridad de los 222 CSV: NaN, Inf, dimensiones, rangos. |
| `audit_der_sizing.py` | Auditoría del dimensionamiento de DERs (PV, BESS, EV) por edificio. |
| `check_training_dataset_ready.py` | Gate: verifica que el dataset esté listo para normalización y entrenamiento. |
| `verify_artifact_layout.py` | Verifica la estructura de artefactos de salida por corrida. |
| `verify_ev_sessions.py` | Verifica consistencia de sesiones EV en charger CSV. |
| `verify_solar.py` | Verifica datos de generación solar y corrección pvlib. |
| `verify_training_optimization.py` | Verifica configuraciones de optimización de entrenamiento. |
| `verify_workflow_integrity.py` | Verifica integridad del flujo completo dataset → entrenamiento. |
| `audit_training_dataset_provenance.py` | Auditoría de procedencia de datos del dataset de entrenamiento. |
| `clean_dataset_orphans.py` | Limpieza de archivos CSV huérfanos sin referencia en schema.json. |

### 6.3 Análisis y evaluación

| Archivo | Propósito |
|---|---|
| `evaluate_dataset.py` | Evaluación estadística del dataset: distribuciones, correlaciones, cobertura. |
| `evaluate_iquitos_citylearn_v3_dataset.py` | Evaluación específica del dataset Iquitos en el entorno CityLearn v3. |
| `deep_dataset_analysis.py` | Análisis profundo: anomalías, patrones, outliers por edificio y variable. |
| `dataset_report.py` | Reporte consolidado del dataset con estadísticas y figuras. |
| `analyze_support_files.py` | Análisis de archivos de soporte del proyecto. |

### 6.4 Generación de documentación (añadidos en 2026-06-15)

| Archivo | Propósito |
|---|---|
| `generate_architecture_pdfs.py` | Genera 5 PDFs de documentación desde markdown (Python + Chrome headless + Mermaid.js CDN). |
| `generate_architecture_pngs.py` | Genera 2 PNGs de infografía de arquitectura y flujo (Chrome headless screenshot, 2x). |

---

## 7. Archivos Modificados en el Fork CityLearn

### 7.1 Aportes originales al motor de simulación (4 aportes — commit `54b1938e`)

Todos los cambios son **retrocompatibles**: parámetros con valores por defecto reproducen comportamiento original.

#### A1 — `CityLearn/citylearn/energy_model.py` · `Battery.degrade(temperature_celsius=25.0)`

**Problema:** Modelo original de degradación lineal sin temperatura ni C-rate.  
**Solución:** Modelo Arrhenius + C-rate para LiFePO₄:

```
capacity_degrade = base × (C_rate)^0.55 × exp[Ea/R × (1/T_ref − 1/T)]
Ea = 24,500 J/mol · T_ref = 298.15 K · z = 0.55
```

**Impacto:** A 35°C (Iquitos), degradación 14% mayor que a 25°C STC. Los agentes aprenden a evitar sobrecargas en horas calurosas.

#### A2 — `CityLearn/citylearn/energy_model.py` · `PV.get_generation()`

**Problema:** Generación PV sin corrección térmica — error sistemático 8–12% en clima tropical.  
**Solución:** Modelo IEC 61215:

```
T_cell = T_amb + (NOCT−20)/800 × GHI
P(T)   = P_STC × [1 + γ × (T_cell − 25)]     γ = −0.0035/°C
```

**Impacto:** Corrección de 10.9–14.4% en Iquitos. Los agentes aprenden precarga BESS matutina (PV más eficiente).

#### A3 — `CityLearn/citylearn/cost_function.py` · `CostFunction.peak(billing_window_steps=1)`

**Problema:** KPI de pico diario no alineado con ventana de facturación OSINERGMIN MT-3/MT-4 (15 min).  
**Solución:** Máximo rodante en ventana configurable antes de agrupación diaria.  
**Impacto:** KPI alineado con tarifa real Electro Oriente S.A. para escenario E3.

#### A4 — `CityLearn/citylearn/energy_model.py` · `CarbonIntensityModel` (clase nueva)

**Problema:** Función CI dinámica embebida en script de dataset, no reutilizable.  
**Solución:** Clase formal con parámetros calibrados para Loreto:

```python
CI(t) = 0.790 × (1 − 0.15 × min(GHI/1000, 1))
# base_ci=0.790 kgCO₂/kWh (RAGEI MINAM 2019) · pv_factor=0.15 (mix 2022-23 Electro Oriente)
```

**Impacto:** Configurable desde schema JSON. Extensible a otras redes aisladas peruanas (Pucallpa, Yurimaguas).

### 7.2 Extensiones MADRL en CityLearn (archivos nuevos o fuertemente extendidos)

| Archivo | Tipo de cambio | Descripción |
|---|---|---|
| `CityLearn/citylearn/reward_function.py` | Extendido | `CityLearnV3MADRLRewardFunction` con pesos por eje (E1/E2/E3) y perfil por algoritmo. |
| `CityLearn/citylearn/dec_pomdp.py` | Nuevo | Formulación Dec-POMDP: observaciones locales, acciones locales, estado global CTDE. |
| `CityLearn/citylearn/madrl_kpis.py` | Nuevo | KPIs MADRL: peak_share, ramp_share, district_import, team_reward, mixed_reward. |
| `CityLearn/citylearn/official_madrl.py` | Nuevo | Interfaz oficial MADRL que conecta CityLearn v2 con la capa v3. |
| `CityLearn/citylearn/scenario_manager.py` | Nuevo | Gestión de escenarios E1/E2/E3 con pesos de recompensa y configuración por escenario. |
| `CityLearn/citylearn/wrappers.py` | Extendido | Wrappers de compatibilidad para los 4 backends MADRL. |
| `CityLearn/citylearn/electric_vehicle.py` | Extendido | Soporte V2G, urgencia SOC, ev_type_code para camionetas. |
| `CityLearn/citylearn/electric_vehicle_charger.py` | Extendido | Cargadores Mode 3, gestión de tomas concurrentes, charger CSV. |

### 7.3 Dataset Iquitos 2023-2025 (creado en CityLearn/data/)

Creado completamente desde cero con datos reales de 17 edificios institucionales/comerciales de Iquitos.

| Componente | Descripción | Cantidad |
|---|---|---|
| `schema.json` | Schema JSON oficial CityLearn con 17 edificios, DERs, EV, precios, carbono. | 1 archivo |
| `weather.csv` | Series horarias de clima Iquitos (T_amb, GHI, HR, viento). | 1 archivo |
| `carbon_intensity.csv` | Intensidad de carbono dinámica diesel+PV (modelo CI Arrhenius). | 1 archivo |
| `pricing.csv` | Tarifas TOU Electro Oriente: 0.26 USD/kWh fuera punta, 0.38 USD/kWh punta. | 1 archivo |
| `Building_X.csv` | Perfiles horarios de consumo por edificio (X=1..17). | 17 archivos |
| `charger_X_Y.csv` | Series de cargadores EV Mode 3 por edificio/tipo/concurrencia. | 185 archivos |
| `Washing_Machine_X.csv` | Series de cargas controladas (lavadoras) por edificio. | 17 archivos |
| **Total** | 222 CSV auditados · 0 NaN/Inf · 26,304 horas (2023-2025) | **222 archivos** |

**Dimensionamiento de DERs validado:**

| DER | Cantidad | Capacidad |
|---|---|---|
| Paneles PV | — | 48,790.9 kWp totales |
| BESS | 17 unidades | 26,266 kWh / 6,648 kW (post-dimensionamiento con EV) |
| Cargadores EV | 185 tomas Mode 3 / 96 equipos físicos doble toma | 749.4 kW nominales |
| EV en pool | 1,850 vehículos simulados | — |
| Máquinas controladas | 17 lavadoras | 876.6 MWh/año |

---

## 8. Scripts PowerShell Creados

| Archivo | Ruta | Propósito |
|---|---|---|
| `run_citylearn_v3_full_training_visible.ps1` | `scripts/` (raíz) | Wrapper visible principal. Crea OutputRoot con timestamp, actualiza `latest_visible_training_output_root.txt`, invoca el launcher. |
| `verify_project_context.ps1` | `scripts/` (raíz) | Verifica que se está ejecutando desde el repositorio correcto. |
| `launch_citylearn_v3_official_training.ps1` | `CityLearn/scripts/` | Launcher oficial de 12 corridas (4 MADRL × 3 ejes). Gestión de concurrencia, manifiestos, logs, `-SkipCompleted`. |
| `monitor_citylearn_v3_official_training.ps1` | `CityLearn/scripts/` | Monitor vivo: GPU, global_step, reward, KPIs costo/CO₂, logs, estado por job. |

---

## 9. Archivos Modificados en Backends Externos

### external/HARL (HAPPO)
- Integración del wrapper `CityLearnHARLEnv` para compatibilidad con la API de observaciones/acciones de CityLearn v3.
- Ajuste de hiperparámetros para 17 agentes heterogéneos.

### external/MARL (MASAC)
- Integración del wrapper `CityLearnSMACDiscreteEnv` con discretización de acciones en bins.
- Optimizaciones de runtime: gestión de replay buffer GiB-bounded, preload batch device auto, RNN hidden dim reducido para 8 GB VRAM.

### external/off-policy (MATD3 — backend activo)
- Integración del wrapper `CityLearnOffPolicyVecEnv`.
- Buffer size reducido a 4,096 transiciones para compatibilidad VRAM RTX 4060.
- Train interval cada 100 pasos.

### external/MAAC (MAAC)
- Integración del wrapper `CityLearnMAACVecEnv` con discretización axis.
- 4 attention heads, buffer 50,000, steps_per_update=250.

---

## 10. Función de Recompensa Multiobjetivo (Perfil v4)

La función `CityLearnV3MADRLRewardFunction` escalariza tres objetivos con pesos por escenario. El perfil v4 (definitive training, commit `2026-06-15`) incorpora penalidad de degradación BESS y urgencia EV:

| Componente | Escenario E1 | Escenario E2 | Escenario E3 |
|---|:---:|:---:|:---:|
| Flexibilidad (peak/ramping) | **0.70** | 0.15 | 0.25 |
| Carbono (CO₂) | 0.15 | **0.70** | 0.15 |
| Costo energético | 0.15 | 0.15 | **0.60** |
| Urgencia EV (SOC) | adicional | adicional | adicional |
| Penalidad BESS (C-rate/T) | v4 nuevo | v4 nuevo | v4 nuevo |

**Mecanismos CTDE:**
- `team_reward = mean(reward_i)` — señal colectiva del distrito
- `mixed_reward_i = 0.30·reward_i + 0.70·team_reward` — 70% señal distrital
- `reward_aggregation = team_mean`

---

## 11. Estructura de Carpetas del Proyecto

```
MADRLCitytleranflexresdr/
├── CityLearn/                          ← Fork submódulo principal
│   ├── citylearn/                      ← Núcleo simulador (extendido)
│   │   ├── v3/                         ← Módulo MADRL v3 creado desde cero
│   │   │   ├── environment.py
│   │   │   ├── objectives.py
│   │   │   ├── config.py
│   │   │   ├── backends.py
│   │   │   └── marllib_env.py
│   │   ├── energy_model.py             ← Modificado: A1, A2, A4
│   │   ├── cost_function.py            ← Modificado: A3
│   │   ├── reward_function.py          ← Extendido: CityLearnV3MADRLRewardFunction
│   │   ├── dec_pomdp.py                ← Nuevo: Dec-POMDP
│   │   ├── madrl_kpis.py               ← Nuevo: KPIs MADRL
│   │   ├── official_madrl.py           ← Nuevo: interfaz oficial
│   │   ├── scenario_manager.py         ← Nuevo: E1/E2/E3
│   │   ├── electric_vehicle.py         ← Extendido: V2G, urgencia SOC
│   │   └── electric_vehicle_charger.py ← Extendido: Mode 3
│   ├── data/datasets/
│   │   └── citylearn_iquitos_2023_2025/ ← Dataset completo (222 CSV)
│   │       ├── schema.json
│   │       ├── weather.csv / carbon_intensity.csv / pricing.csv
│   │       ├── Building_1.csv ... Building_17.csv
│   │       ├── charger_*.csv (185 archivos)
│   │       └── Washing_Machine_*.csv (17 archivos)
│   └── scripts/                        ← 16 scripts Python creados
│       ├── train_citylearn_v3_happo.py
│       ├── train_citylearn_v3_masac.py
│       ├── train_citylearn_v3_matd3.py
│       ├── train_citylearn_v3_maac.py
│       ├── citylearn_v3_training_common.py
│       ├── benchmark_citylearn_v2_agents.py
│       ├── compare_citylearn_v2_vs_v3_madrl.py
│       ├── generate_thesis_objective_evidence.py
│       ├── check_citylearn_v3_training_ready.py
│       ├── run_citylearn_v3_env_smoke.py
│       ├── validate_citylearn_v3_cooperative_ctde.py
│       ├── validate_citylearn_v3_objectives.py
│       ├── validate_citylearn_v3_reward_profiles.py
│       ├── masac_runtime_optimizations.py
│       ├── regenerate_citylearn_v3_figures.py
│       ├── generate_citylearn_v3_building_detail_report.py
│       ├── launch_citylearn_v3_official_training.ps1
│       └── monitor_citylearn_v3_official_training.ps1
├── external/                           ← Backends MADRL (submódulos)
│   ├── HARL/                           ← Fork PKU-MARL/HARL (HAPPO)
│   ├── MARL/                           ← Fork puyuan1996/MARL (MASAC)
│   ├── MAAC/                           ← Fork shariqiqbal2810/MAAC
│   ├── off-policy/                     ← marlbenchmark/off-policy (MATD3 activo)
│   ├── MARLlib/                        ← Fork Replicable-MARL/MARLlib
│   ├── MATD3implementation/            ← Fork JohannesAck/MATD3implementation
│   ├── MicroGrids/                     ← Fork referencia microrredes
│   ├── evcc/                           ← evcc-io/evcc (EV/V2G referencia)
│   └── prosumpy/                       ← Fork referencia prosumidores
├── tools/                              ← 30 herramientas Python creadas
│   ├── orchestrate_citylearn_dataset.py
│   ├── generate_iquitos_dataset.py
│   ├── audit_citylearn_csv_integrity.py
│   ├── verify_workflow_integrity.py
│   ├── generate_architecture_pdfs.py
│   └── ... (25 herramientas adicionales)
├── scripts/                            ← Scripts PowerShell raíz
│   ├── run_citylearn_v3_full_training_visible.ps1
│   └── verify_project_context.ps1
├── docs/
│   ├── architecture/                   ← Documentación de arquitectura + PDFs/PNGs
│   ├── thesis/                         ← Plan de tesis + aportes al motor
│   ├── decisions/                      ← Justificaciones de diseño
│   ├── audits/                         ← Auditorías técnicas
│   └── contributions/                  ← Registro de cambios por repo
├── outputs/                            ← Resultados de entrenamiento
│   ├── citylearn_v3_madrl_full_20260613_010234/  ← Corrida v3 (COMPLETADA)
│   ├── citylearn_v3_madrl_full_20260615_074011_v4/ ← Corrida v4 (COMPLETADA 12/12)
│   ├── dataset_audit/                  ← Auditorías del dataset
│   └── latest_visible_training_output_root.txt
├── CityLearn/configs/
│   ├── citylearn_v3_madrl_training.yaml
│   └── citylearn_v3_madrl_training.json
└── .venv39-citylearn-v3/              ← Entorno virtual Python 3.9
```

---

## 12. Estado de Entrenamiento al Cierre del Documento (2026-06-15)

| Corrida | Estado | Jobs completados | Perfil reward |
|---|---|---|---|
| `outputs/citylearn_v3_madrl_full_20260613_010234` | **COMPLETADA** | 12/12 (exit_code=0) | v3 base |
| `outputs/citylearn_v3_madrl_full_20260615_074011_v4` | **COMPLETADA** | 12/12 (HAPPO, MASAC, MATD3 y MAAC en E1/E2/E3) | v4 BESS penalty + EV urgency |

**Hardware de entrenamiento:** NVIDIA GeForce RTX 4060 Laptop GPU · 8,188 MiB VRAM · Driver 560.94 · PyTorch 2.8.0+cu126  
**Tiempo total estimado por corrida completa:** ~10-11 horas.

---

## 13. Entorno de Desarrollo

| Componente | Versión / Valor |
|---|---|
| Python (entrenamiento) | 3.9 — `.venv39-citylearn-v3` |
| Python (herramientas PDF/PNG) | 3.14 — `C:\Python314\python.exe` |
| PyTorch | 2.8.0+cu126 |
| CUDA toolkit | 12.6 |
| Sistema operativo | Windows 11 Home (build 26200) |
| IDE | VS Code con extensión Claude Code |
| Shell | PowerShell 7 (`pwsh.exe`) |
| Control de versiones | Git + submódulos |
| GPU | NVIDIA RTX 4060 Laptop, 8 GB VRAM |
