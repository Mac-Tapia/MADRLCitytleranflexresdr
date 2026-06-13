# Module B: Thesis Report under Guide N. 02 Section 5.1

Use Module A outputs as mandatory input. Do not draft the report in isolation.

## Thesis Title (official)

> MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS ENERGÉTICOS EN COMUNIDADES INTELIGENTES

## Objective Block (use exactly as stated)

**O.G.** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes.

**OE.1** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza la flexibilidad energética en comunidades inteligentes.

**OE.2** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce las emisiones de CO2 en comunidades inteligentes.

**OE.3** — Determinar el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza los costos energéticos en comunidades inteligentes.

## Mandatory Structure

Preserve this structure exactly for the final thesis report. The Guide N. 02 supplies the report structure only. Do not replace it with an engineering report, experiment log, dataset audit, training dashboard, or statistical appendix. All data, metrics, tables, conclusions, and discussion must come only from the current active project evidence in this repository and must be placed under the appropriate Guide N. 02 section. Do not use non-current training outputs as source data.

CARÁTULA

DATOS GENERALES

- Dedicatoria
- Agradecimientos
- Copia de documentos
- Índice de contenidos
- Lista de tablas, ilustraciones y cuadros
- Resumen - Abstract
- Introducción

CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA

1.1 Diagnóstico

1.2 Identificación y descripción del problema de estudio

1.3 Formulación del problema

1.3.1 Formulación del problema general

1.3.2 Formulación de los problemas específicos

1.4 Objetivos

1.4.1 Objetivo general

1.4.2 Objetivos específicos

1.5 Justificación del estudio

1.6 Alcance del estudio

CAPÍTULO II. MARCO TEÓRICO

2.1 Antecedentes

2.2 Bases teóricas

2.3 Definición de términos

CAPÍTULO III. DESARROLLO DEL TRABAJO DE TESIS

3.1 Presentación de la propuesta de solución

3.2 Desarrollo de la propuesta de solución

3.3 Análisis de los datos y resultados

3.4 Discusión e interpretación de los resultados

3.5 Estimación del impacto de la solución

CAPÍTULO IV. CONCLUSIONES Y RECOMENDACIONES

4.1 Conclusiones

4.2 Recomendaciones

REFERENCIAS

ANEXOS

## Content Requirements

### Carátula

Include: university (Universidad Nacional Mayor de San Marcos), graduate school/faculty, full thesis title, academic degree sought (Maestría de Especialización o Profesionalizante), student name, advisor name, Lima, Peru, year.

### Resumen - Abstract

Write in Spanish and English. Include:

- Context: smart communities (comunidades inteligentes) with PV, BESS, and EV charging.
- Problem: absence of determination of the best MADRL for coordinated management of energy flexibility, CO2 emissions, and energy costs.
- General objective: determine the best MADRL that coordinately manages the three dimensions.
- Methodology: CityLearn v2 + CityLearn v3 propuesto, Dec-POMDP, CTDE, comparative evaluation of HAPPO/MASAC/MATD3/MAAC, Optuna.
- Expected results or obtained results (if available): ranking of algorithms per axis (OE.1, OE.2, OE.3) and overall (O.G.).
- Main conclusions.
- Keywords (Spanish and English): MADRL, CityLearn, Dec-POMDP, CTDE, flexibilidad energética, emisiones CO2, costos energéticos, comunidades inteligentes.

### Introducción

Develop: context of smart communities and distributed energy resources; challenge of coordinating energy flexibility, CO2 emissions reduction, and energy cost optimization; limitations of single-agent DRL; need for cooperative MADRL under Dec-POMDP/CTDE; CityLearn v2 as base environment; CityLearn v3 propuesto as experimental extension; comparative evaluation of HAPPO, MASAC, MATD3, MAAC; MARLlib as technical reference; Optuna for hyperparameter tuning; chapter synthesis (I: problem, II: theory, III: development and results, IV: conclusions).

### Chapter I — Planteamiento del problema

**1.1 Diagnóstico:** Three-dimension diagnosis aligned to OE.1/OE.2/OE.3:

- Flexibilidad energética: uncoordinated DER in smart communities, single-agent DRL limitations, gap in determining best MADRL for flexibility.
- Emisiones de CO2: variable carbon intensity, lack of carbon-aware MADRL coordination, gap in determining best MADRL for CO2 reduction.
- Costos energéticos: dynamic pricing, uncoordinated TOU response, gap in determining best MADRL for cost optimization.
- Methodological gap: no unified benchmark of HAPPO/MASAC/MATD3/MAAC under identical Dec-POMDP/CTDE conditions across the three axes.

**1.2 Identificación y descripción del problema:** Main problem = absence of determination of the best MADRL for coordinated management. Symptoms, technical/methodological causes, operational/environmental/economic consequences, independent/dependent variables, spatial scope (smart communities via CityLearn v2 datasets), temporal scope (2015–2026).

**1.3.1 Problema general:**
> ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes?

**1.3.2 Problemas específicos:**
> PE.1: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza la flexibilidad energética en comunidades inteligentes?
> PE.2: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que reduce las emisiones de CO2 en comunidades inteligentes?
> PE.3: ¿Cuál es el mejor Multi-Agente de Aprendizaje por Refuerzo Profundo que optimiza los costos energéticos en comunidades inteligentes?

**1.4 Objectives:** Use exact text from the Objective Block above.

**1.5 Justificación:** Technical, environmental, economic, methodological, scientific, and social dimensions all articulated with the three-axis (OE.1/OE.2/OE.3) structure.

**1.6 Alcance:** Thematic (comparative HAPPO/MASAC/MATD3/MAAC on three KPI axes), spatial (CityLearn v2 smart community datasets), temporal (2015–2026), methodological (quantitative, comparative, simulation-based), computational (Python/PyTorch/CityLearn v2/CityLearn v3 propuesto/Optuna), limits and exclusions.

### Chapter II — Marco teórico

**2.1 Antecedentes:** Use Module A matrix. Organize antecedents by four axes:

- Eje 1 (OE.1): MADRL for energy flexibility, demand response, peak reduction, CityLearn v2, BESS/PV/EV.
- Eje 2 (OE.2): MADRL for CO2 emission reduction, carbon-aware demand response, carbon-intensity-weighted KPIs.
- Eje 3 (OE.3): MADRL for energy cost optimization, TOU/RTP response, cost KPIs.
- Eje transversal: Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib, Optuna, cooperative MADRL benchmarks.

Each antecedent must include: author-year, objective, methodology, dataset/environment, algorithm, main results, contribution to this thesis, APA citation.

**2.2 Bases teóricas:** Four axes matching antecedents. All claims must carry APA citations.

**2.3 Definición de términos:** MADRL, DRL, agente, entorno, Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib, Optuna, CityLearn v2, CityLearn v3 propuesto, comunidad inteligente, flexibilidad energética, intensidad de carbono, costos energéticos, BESS, PV, EV, KPI.

### Chapter III — Desarrollo del trabajo de tesis

**3.1 Presentación de la propuesta de solución:** Present CityLearn v3 propuesto as the experimental extension of CityLearn v2 that implements the cooperative MADRL layer. Include architecture diagram reference (docs/ARQUITECTURA_CITYLEARN_V3_MADRL.png). Describe the proposed solution as the comparative evaluation of HAPPO, MASAC, MATD3, and MAAC under unified Dec-POMDP/CTDE conditions on the three KPI axes.

**3.2 Desarrollo de la propuesta de solución:** Develop in subsections:

- 3.2.1 Arquitectura CityLearn v3 propuesta: entorno base `CityLearnEnv` (v2) extendido con 6 clases en `CityLearn/citylearn/v3/`: `CityLearnDecPOMDPEnv` (base Dec-POMDP), `CityLearnHARLEnv` (HAPPO/HARL), `CityLearnSMACDiscreteEnv` (MASAC), `CityLearnOffPolicyVecEnv` (MATD3), `CityLearnMAACVecEnv` (MAAC), `CityLearnV3MADRLRewardFunction` (recompensa multiobjetivo cooperativa). Adaptador común: `CityLearn/scripts/citylearn_v3_training_common.py`. Lanzador oficial: `CityLearn/scripts/launch_citylearn_v3_official_training.ps1`.
- 3.2.2 Formulación Dec-POMDP: ℳ = ⟨𝒮, 𝒜₁…𝒜_N, 𝒯, R, 𝒪₁…𝒪_N, Ω, γ, T⟩ donde: N = 17 agentes (un edificio SEAI Iquitos cada uno); 𝒮 corresponde al estado global CTDE construido desde las 17 observaciones locales normalizadas (estado compartido HAPPO/E1 vigente: 1 907 dimensiones; observaciones locales validadas: 54–327 dimensiones, con padding de backend hasta 330 cuando corresponde); 𝒜ᵢ corresponde al vector de acciones por edificio sobre BESS, EV y cargas controladas (espacio continuo HAPPO/E1 acolchado a 44 acciones por agente). γ = 0.99, T = 8 760 pasos (1 año horario). Condición Dec-POMDP: cada agente solo observa su propia oᵢ. CTDE: crítico centralizado Qᵢ(s, a₁…a₁₇) accede a s durante entrenamiento; política πᵢ(aᵢ|oᵢ) ejecuta descentralizada.
- 3.2.3 Función de recompensa multiobjetivo (`CityLearnV3MADRLRewardFunction`): `reward_i(t) = reward_scale × [w_flex·flex_component_i(t) + w_carbon·carbon_component_i(t) + w_cost·cost_component_i(t)]`. Recompensa cooperativa: `team_reward = (1/N) Σᵢ reward_i`. Recompensa mixta: `mixed_reward_i = (1−r_team)·reward_i + r_team·team_reward`. Pesos por escenario: E1 [0.700, 0.150, 0.150] → OE.1 Flexibilidad; E2 [0.150, 0.700, 0.150] → OE.2 Emisiones CO2; E3 [0.250, 0.150, 0.600] → OE.3 Costos. **Perfil activo `unified_comparable_v2` (todos los algoritmos):** team_ratio=0.70, peak_weight=0.45, ramp_weight=0.35, ev_weight=0.12, reward_scale=1.00. [Nota de reconciliación: el plan de tesis §4.11.3 documentó perfiles diferenciados por algoritmo (HAPPO=0.75, MASAC=0.55, MATD3=0.65, MAAC=0.80); la implementación vigente adopta `unified_comparable_v2` para garantizar comparabilidad estadística entre los 4 backends bajo función objetivo idéntica. Los perfiles diferenciados se preservan como ablación futura. Justificación completa con 12 referencias APA en `docs/JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md`.]
- 3.2.4 Esquema CTDE: centralized critics during training, decentralized actors during execution.
- 3.2.5 Backends MADRL comparados bajo condiciones idénticas de entorno Dec-POMDP/CTDE (GPU local: NVIDIA RTX 4060 Laptop 8 GB, PyTorch 2.8.0+cu126, CUDA=True, perfil `local4060_fast`):

  | Algoritmo | Tipo | Propiedad clave | Configuración vigente `local4060_fast` | Estabilización |
  | --------- | ---- | --------------- | -------------------------------------- | -------------- |
  | HAPPO | On-policy | Garantía monótona cooperativa | hidden_size=256, n_rollout_threads=1 | actor_lr=1e-4, critic_lr=5e-4, max_grad_norm=1.0, action_aggregation=mean, ppo_clip=0.2 |
  | MASAC | Off-policy | Máxima entropía + QMIX | rnn_hidden=64, qmix_hidden=32, hyper_hidden=64, buffer=2, critic_batch=1 | actor_lr=3e-4, critic_lr=5e-4, alpha_lr=3e-4, grad_norm_clip=1.0, actor_sample_times=4 |
  | MATD3 | Off-policy | Doble crítico determinístico | hidden_size=256, batch=256, buffer=4096 | lr=3e-4, max_grad_norm=1.0, policy_delay=2, train_interval=100 |
  | MAAC | Off-policy | Mecanismo de atención | hidden_size=128, batch=64, buffer=256 | pi_lr=3e-4, q_lr=1e-3, steps_per_update=250, num_updates=4, attention_heads=4 |

  Referencia de implementación: MARLlib (Hu et al., 2023); backends adaptados a CityLearn v3 propuesto. Se incorporan guardas finitas para TensorBoard y pasos de optimización, a fin de impedir que métricas NaN/Inf de gradientes contaminen logs o checkpoints. La baja utilización sostenida de GPU no invalida CUDA porque CityLearn conserva avance temporal por entorno; la GPU se usa durante los backends neuronales. La ruta operativa actual usa monitor visible con `LiveOutput=false` para permitir paralelismo de escenarios por algoritmo sin perder trazabilidad.
- 3.2.6 Ajuste de hiperparámetros con Optuna.
- 3.2.7 Dataset `citylearn_iquitos_2023_2025` — 17 edificios reales del Sistema Eléctrico Aislado de Iquitos (SEAI), Loreto, Perú (Electro Oriente S.A., 2023-2025). 26 304 horas; 222 CSV auditados: 17 `Building_X.csv`, 185 `charger_X_Y.csv`, 17 `Washing_Machine_X.csv`, `weather.csv`, `carbon_intensity.csv` y `pricing.csv`; `schema.json` referencia clima, emisiones y precios para los 17 edificios. PV real: pvlib + PVGIS TMY, 48 790.9 kWp totales y 148 802.232 MWh anuales simulados. BESS vigente: 26 266 kWh / 6 648 kW, dimensionado por edificio con balance entre generación solar, demanda EV, carga no controlada, carga controlada, red pública antes/después de BESS y corte de pico. La regla operativa implementada prioriza la generación solar hacia recarga EV y carga del edificio; el BESS prioriza recarga EV en la ventana horaria de operación del edificio hasta cierre y luego atiende carga del edificio/pico. EV: 185 cargadores/tomas EV en schema, 96 equipos físicos modo 3, 749.4 kW instalados, sesiones estocásticas reproducibles (seed = building_id × 1000 + charger_idx). Cargas controladas: 17 máquinas, una por edificio, 876.593 MWh anuales. Carbon intensity: 0.6715–0.7900 kgCO₂/kWh (MINAM RAGEI 2019, sistema diésel SEAI). Pricing: 0.383220954–1.066918914 USD/kWh en `pricing.csv`. Trazabilidad validada: delta máximo B02-B17 = 0.000000145% vs. facturas mensuales. Auditoría integral al 2026-06-09: 222 CSV, 0 NaN, 0 Inf, sin cargadores/máquinas huérfanos ni faltantes; normalización permitida antes de entrenamiento.
- 3.2.8 KPIs por eje (nombres exactos del entorno CityLearn v2/v3): OE.1 Flexibilidad: `peak_average`, `ramping_average`, `one_minus_load_factor_average`; OE.2 Emisiones CO2: `carbon_emissions_total`, `carbon_emissions_from_electrical_consumption`; OE.3 Costos: `electricity_cost_total`, `electricity_cost_from_electrical_consumption`. KPI de recompensa: `reward_mean` por episodio, componentes `flex_mean`, `co2_mean`, `cost_mean`.

**3.3 Análisis de los datos y resultados:**

Datos disponibles al 2026-06-12 (sesión activa `citylearn_v3_madrl_full_20260612_223320` lanzada el 2026-06-12, `outputs/citylearn_v3_madrl_full_20260612_223320/`):

- HAPPO E1+E2 corriendo en paralelo (max_concurrent=2). HAPPO E3 en cola. Algoritmos MASAC, MATD3 y MAAC pendientes de inicio (se lanzan en etapas tras completar HAPPO). Perfil `unified_comparable_v2` activo en todas las corridas. CUDA=True, perfil `local4060_fast`.
- Estado oficial: `status = running`, escenarios `E1,E2,E3`, 5 episodios, 8 760 pasos por episodio, 43 800 pasos por corrida. Fuente: `official_full_status.json`.
- No existen resultados finales válidos hasta que cada corrida nueva escriba `data/results.json`, `data/timeseries.csv` y `data/trace.csv`. No completar tablas, discusión ni conclusiones con datos de entrenamientos anteriores.
- Todos los algoritmos y escenarios: `resultados por validar` hasta completar las 12 corridas de la sesión `citylearn_v3_madrl_full_20260612_223320`.

Diseño experimental documentado: 3 escenarios × 4 algoritmos = 12 corridas independientes. La independencia semántica del entrenamiento paralelo por escenario dentro del mismo algoritmo está justificada académicamente en `docs/JUSTIFICACION_DISENO_EXPERIMENTAL_ESCENARIOS_PARALELO.md` (14 referencias APA, incluyendo Roijers et al. 2013 JAIR, Felten et al. 2024 JAIR, HARL JMLR arXiv:2304.09870, MALib JMLR arXiv:2106.07551).

Estructura de tablas (usar datos reales cuando estén disponibles; nunca inventar):

- Tabla 1 — KPIs de flexibilidad por algoritmo × E1 (OE.1): `peak_average`, `ramping_average`, `one_minus_load_factor_average`.
- Tabla 2 — KPIs de CO2 por algoritmo × E2 (OE.2): `carbon_emissions_total`.
- Tabla 3 — KPIs de costos por algoritmo × E3 (OE.3): `electricity_cost_total`.
- Tabla 4 — Ranking integrado MADRL (O.G.): promedio normalizado de los 3 ejes.

Protocolo estadístico inter-algoritmo (ejecutar tras completar las 12 corridas). Artefactos en `outputs/citylearn_v3_madrl_full_20260612_223320/statistical_comparison/` (naming: `result_{algo}_{escenario}.json`, 36 archivos totales). Suite de 4 pruebas: (1) Shapiro-Wilk — normalidad por algoritmo; (2) Kruskal-Wallis — diferencia global entre 4 algoritmos por escenario; (3) Mann-Whitney U — comparación par-a-par; (4) Wilcoxon signed-rank — episodios pareados dentro del mismo escenario.

**3.3.2 Determinación del Mejor MADRL Global (O.G.) — Ranking Integrado Multiobjetivo:**

El O.G. pregunta cuál algoritmo gestiona coordinadamente los tres ejes simultáneamente. Dado que los escenarios E1/E2/E3 entrenan con vectores de peso distintos, la determinación global requiere un método de agregación inter-eje que no favorezca el eje de entrenamiento de ningún algoritmo en particular.

*Paso 1 — Extracción de KPIs por eje y algoritmo (fuente: artefactos de la corrida especializada de cada algoritmo):*

```
KPI_flex(a)  ← peak_average       de a/E1_seed_0/data/results.json   (↓ mejor)
KPI_co2(a)   ← carbon_emissions_total de a/E2_seed_0/data/results.json (↓ mejor)
KPI_cost(a)  ← electricity_cost_total de a/E3_seed_0/data/results.json (↓ mejor)
```

*Paso 2 — Normalización min-max inter-algoritmo por eje (invirtiendo a "mayor = mejor"):*

```
KPI_flex_norm(a)  = 1 − [KPI_flex(a)  − min_a KPI_flex]  / [max_a KPI_flex  − min_a KPI_flex]
KPI_co2_norm(a)   = 1 − [KPI_co2(a)   − min_a KPI_co2]   / [max_a KPI_co2   − min_a KPI_co2]
KPI_cost_norm(a)  = 1 − [KPI_cost(a)  − min_a KPI_cost]  / [max_a KPI_cost  − min_a KPI_cost]
```

*Paso 3 — Score global con pesos iguales [1/3, 1/3, 1/3] (sin preferencia a priori — O.G. no favorece ningún eje):*

```
Score_OG(a) = (1/3)·KPI_flex_norm(a) + (1/3)·KPI_co2_norm(a) + (1/3)·KPI_cost_norm(a)
```

Justificación de pesos iguales: el O.G. exige gestión *coordinada* de los tres ejes; ninguno debe ponderarse más que otro en la evaluación global. Este principio sigue a Roijers et al. (2013, JAIR) en comparaciones MORL sin función de utilidad del decisor especificada, y a Felten et al. (2024, JAIR) en benchmarks MORL equitativos.

*Paso 4 — Análisis de dominancia de Pareto (complementario al ranking escalar):*

El algoritmo `a` **domina de Pareto** al algoritmo `b` si y solo si:
```
KPI_flex_norm(a) ≥ KPI_flex_norm(b)  AND
KPI_co2_norm(a)  ≥ KPI_co2_norm(b)   AND
KPI_cost_norm(a) ≥ KPI_cost_norm(b)  AND
∃ eje k : KPI_k_norm(a) > KPI_k_norm(b)
```
Si existe un algoritmo no dominado en los tres ejes simultáneamente → es el ganador inequívoco de O.G. Si ninguno domina (frente de Pareto) → el Score_OG decide el ranking.

*Paso 5 — Ranking de Borda (no paramétrico, sin supuesto de escala):*

Para cada eje e, asignar rango r_e(a) ∈ {1,2,3,4} donde rango 1 = mejor KPI. El Borda score es:
```
Borda(a) = r_flex(a) + r_co2(a) + r_cost(a)
```
El algoritmo con menor Borda score es el mejor coordinado (O.G.). El ranking Borda y el Score_OG normalizado deben coincidir; si divergen, reportar ambos y discutir en §3.4.

Tabla 4 — Ranking Integrado MADRL (O.G.) — completar con datos reales cuando estén disponibles:

| Algoritmo | KPI_flex_norm | KPI_co2_norm | KPI_cost_norm | Score_OG | Rango Borda | Rango O.G. |
| --------- | :-----------: | :----------: | :-----------: | :------: | :---------: | :--------: |
| HAPPO | — | — | — | — | — | — |
| MASAC | — | — | — | — | — | — |
| MATD3 | — | — | — | — | — | — |
| MAAC | — | — | — | — | — | — |

*Protocolo estadístico para O.G. (adicional al protocolo por escenario):*

- Kruskal-Wallis global sobre Score_OG de los 5 episodios por algoritmo: H₀ = todos los algoritmos tienen Score_OG equivalente; si p < 0.05, existe diferencia significativa global.
- Mann-Whitney U par-a-par sobre Score_OG: 6 pares (HAPPO–MASAC, HAPPO–MATD3, HAPPO–MAAC, MASAC–MATD3, MASAC–MAAC, MATD3–MAAC). Corrección Bonferroni: umbral ajustado α' = 0.05/6 = 0.0083.
- Effect size: ε² (eta-cuadrado de Kruskal-Wallis) para cada eje y para Score_OG combinado. Clasificación: pequeño ≥0.01, mediano ≥0.06, grande ≥0.14.

**3.3.3 Desagregación por Edificio — Control Individual y Contribución al Distrito:**

Además del análisis global inter-algoritmo, se reporta el desempeño desagregado por edificio para identificar qué agentes contribuyen más a la reducción de pico, emisiones y costo a nivel distrital.

*KPIs por edificio i (extraídos de `{algo}/{scenario}_seed_0/data/timeseries.csv`):*

```
peak_i        = max_t ( net_load_i(t) )                donde net_load_i = import_i − export_i
co2_i         = Σ_t max(0, import_i(t)) · CI(t)
cost_i        = Σ_t max(0, import_i(t)) · p(t)
self_suff_i   = 1 − Σ_t import_i(t) / Σ_t non_shiftable_load_i(t)
bess_util_i   = Σ_t |P_bess_i(t)| / (T · P_bess_max_i)    ← fracción de capacidad BESS usada
ev_served_i   = Σ_t EV_sessions_completed_i(t) / EV_sessions_total_i
```

*Métricas de coordinación distrital (extraídas de timeseries):*

```
district_import(t) = Σᵢ max(0, net_load_i(t))
peak_district      = max_t district_import(t)
peak_share_i(t)    = net_load_i(t) / district_import(t)     ← fracción del pico que aporta edificio i
ramp_district(t)   = |district_import(t) − district_import(t−1)|
```

*Contribución individual al objetivo distrital (counterfactual):*

```
Δpeak_i   = peak_district_sin_i − peak_district_con_i
Δco2_i    = co2_district_sin_i  − co2_district_con_i
Δcost_i   = cost_district_sin_i − cost_district_con_i
```
donde "sin_i" corresponde a ejecutar la política del algoritmo ganador con el agente i en modo pasivo (sin BESS, sin control EV). Esto cuantifica cuánto aporta cada edificio a la coordinación distrital.

Tabla 5 — Desempeño por Edificio (algoritmo ganador O.G., completar con datos reales):

| Edificio | Tipo | EV tomas | BESS kWh | peak_i (kW) | co2_i (kg) | cost_i (USD) | self_suff_i | bess_util_i |
| -------- | ---- | :------: | :------: | :---------: | :--------: | :----------: | :---------: | :---------: |
| B01 ELECTRO ORIENTE | Office | 4 | 6,747 | — | — | — | — | — |
| B06 MALL AVENTURA | Commercial | 32 | 2,541 | — | — | — | — | — |
| B07 UNAP BIOLOGÍA | Education | 42 | 984 | — | — | — | — | — |
| B11 HOSPITAL LORETO | Healthcare | 3 | 1,901 | — | — | — | — | — |
| … (17 filas totales) | | | | | | | | |

Edificios críticos para la coordinación (mayor Δpeak_i esperados por tamaño y DER): B01 (BESS más grande), B06 (más cargadores EV), B07 (más cargadores EV), B11 (carga hospitalaria constante), B12 (BESS grande). Reportar ranking completo de Δpeak_i en Tabla 5 y discutir en §3.4 qué tipo de edificio se beneficia más de la coordinación MADRL.

**3.4 Discusión e interpretación:** Compare algorithm behaviors per axis. Discuss which algorithm best handles each dimension and why (architectural reasons: entropy, monotonicity, dual critic, attention). Discuss coordinated management performance. Discuss applicability to real smart communities.

**3.5 Estimación del impacto de la solución:** Environmental impact (CO2 reduction potential), economic impact (energy cost savings potential), technical impact (flexibility gain, peak reduction), scientific impact (reproducible MADRL benchmark for smart communities).

### Chapter IV — Conclusiones y recomendaciones

**4.1 Conclusiones:** Write:

- Conclusión general (O.G.): which algorithm best coordinately manages the three dimensions, or expected determination criteria.
- Conclusión OE.1: which algorithm best optimizes energy flexibility.
- Conclusión OE.2: which algorithm best reduces CO2 emissions.
- Conclusión OE.3: which algorithm best optimizes energy costs.
- Conclusión metodológica: contribution of Dec-POMDP/CTDE/CityLearn v3 propuesto framework.
- Conclusión técnica: CityLearn v3 propuesto as reproducible benchmark.
- Conclusión ambiental: CO2 reduction potential.
- Conclusión económica: energy cost reduction potential.

If final results are not available, express conclusions as expected/anticipated findings based on the methodological design.

**4.2 Recomendaciones:** Derive from conclusions. Include: extending to real smart community datasets, validating in isolated power systems, incorporating additional DER types, exploring hybrid MADRL-MPC approaches, publishing the CityLearn v3 propuesto framework as open-source.
