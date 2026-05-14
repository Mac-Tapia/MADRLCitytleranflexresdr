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

- 3.2.1 Arquitectura CityLearn v3 propuesta (entorno base CityLearn v2 + wrapper Dec-POMDP + backends MADRL + CTDE + Optuna).
- 3.2.2 Formulación Dec-POMDP: S (global state), {oi} (local observations per agent), {Ai} (action spaces), T (transition), {Ri} (rewards), gamma (discount factor).
- 3.2.3 Función de recompensa multiobjetivo: r(t) = w1·r_flex(t) + w2·r_co2(t) + w3·r_cost(t). Aligned to OE.1, OE.2, OE.3.
- 3.2.4 Esquema CTDE: centralized critics during training, decentralized actors during execution.
- 3.2.5 Backends MADRL: HAPPO, MASAC, MATD3, MAAC — description, key properties, implementation reference (MARLlib).
- 3.2.6 Ajuste de hiperparámetros con Optuna.
- 3.2.7 Datasets de CityLearn v2.
- 3.2.8 KPIs por eje: flexibility (OE.1), CO2 (OE.2), costs (OE.3).

**3.3 Análisis de los datos y resultados:** Present results tables for each backend on each KPI axis. If final simulation results are not available, write `resultados esperados`, `resultados por validar`, or `indicadores a estimar`. Do NOT invent values. Structure: Table 1 — KPIs de flexibilidad por algoritmo (OE.1); Table 2 — KPIs de CO2 por algoritmo (OE.2); Table 3 — KPIs de costos por algoritmo (OE.3); Table 4 — Ranking integrado MADRL (O.G.).

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
