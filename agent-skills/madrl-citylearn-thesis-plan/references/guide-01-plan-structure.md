# Guide N. 01 Thesis Plan Structure

Use this exact structure for the thesis plan.

## CARÁTULA

Include university name, logo, graduate unit/school, thesis plan title, graduation purpose, author, advisor, place, and date.

The thesis title must be clear, specific, linked to the problem, variables, and study scope. Do not add acronyms to the thesis title.

**Título oficial de la tesis:**

> MULTI-AGENTE DE APRENDIZAJE POR REFUERZO PROFUNDO PARA LA GESTIÓN COORDINADA DE FLEXIBILIDAD ENERGÉTICA, EMISIONES DE CARBONO Y COSTOS ENERGÉTICOS EN COMUNIDADES INTELIGENTES

## DATOS GENERALES

1. Título propuesto.
2. Nombre del graduando.
3. Nombre del asesor.
4. Área involucrada.
5. Lugar o institución donde se desarrolla el proyecto.
6. Duración estimada del proyecto in months, with start date and end date.

## CAPÍTULO I. PLANTEAMIENTO DEL PROBLEMA

### 1.1 Diagnóstico

Develop the diagnosis of smart communities (comunidades inteligentes) as complex multi-resource energy environments integrating distributed energy resources (DER): solar photovoltaic generation (PV), battery energy storage systems (BESS), and electric vehicle (EV) charging stations. Diagnose the following critical dimensions:

**Dimensión de flexibilidad energética:** The absence of coordinated management of distributed energy resources in smart communities limits the capacity to modulate demand, shift loads, and exploit renewable generation, leading to suboptimal grid-interactive behavior and high peak-to-average ratios. Single-agent deep reinforcement learning (DRL) approaches have shown inability to generalize across heterogeneous building portfolios. No comparative study has determined which Multi-Agent Deep Reinforcement Learning (MADRL) algorithm achieves the best energy flexibility performance across coordinated smart community scenarios.

**Dimensión de emisiones de carbono (CO2):** Smart communities operate under time-varying carbon intensity signals that reflect the fossil-fuel dependence of their electricity supply. The lack of coordinated multi-agent control prevents optimal temporal shifting of consumption toward low-carbon periods. No benchmark has established which MADRL algorithm best reduces CO2 emissions in smart communities under dynamic carbon intensity conditions.

**Dimensión de costos energéticos:** Dynamic electricity pricing (time-of-use, real-time pricing) creates economic incentives for demand flexibility. Uncoordinated building-level responses generate suboptimal collective outcomes. No rigorous comparative evaluation has determined which MADRL achieves the best energy cost reduction under coordinated smart community operation.

**Limitaciones metodológicas del estado del arte:** Existing literature reports isolated evaluations of individual algorithms on single dimensions. The absence of a unified comparative framework—covering HAPPO, MASAC, MATD3, and MAAC under Dec-POMDP formulation and Centralized Training Decentralized Execution (CTDE) schemes—prevents the determination of the best MADRL agent for the coordinated, simultaneous management of energy flexibility, CO2 emissions, and energy costs in smart communities.

**Oportunidad de CityLearn v2:** CityLearn v2 provides a validated open-source simulation environment for multi-agent energy management in grid-interactive communities. Its integration with CityLearn v3 propuesto—an experimental extension that implements the cooperative MADRL layer, Dec-POMDP formulation, CTDE training, and MARLlib-compatible backends—enables rigorous comparative evaluation of MADRL algorithms.

### 1.2 Identificación y descripción del problema de estudio

Identify the main problem as the **lack of determination of the best Multi-Agent Deep Reinforcement Learning algorithm that coordinately manages energy flexibility, CO2 emissions, and energy costs in smart communities**. Describe the following structure:

- **Problema técnico:** Absence of coordinated MADRL control that simultaneously optimizes the three dimensions (flexibility, CO2, costs) in smart community simulations.
- **Síntomas observables:** High peak demand, elevated carbon-intensity-weighted consumption, suboptimal electricity cost reduction, and poor load-profile coordination in multi-building scenarios.
- **Causas energéticas:** Uncoordinated distributed energy resources, lack of cooperative decision-making among agents, absence of shared global state utilization.
- **Causas metodológicas:** No unified comparative benchmark of HAPPO, MASAC, MATD3, and MAAC under identical Dec-POMDP and CTDE conditions applied to the three performance dimensions.
- **Consecuencias operacionales:** Suboptimal dispatch, failure to exploit demand response windows.
- **Consecuencias ambientales:** Excess CO2 emissions from grid imports during high-carbon-intensity periods.
- **Consecuencias económicas:** Unnecessary energy costs from unoptimized time-of-use response.
- **Variables:** Independent variable: the cooperative MADRL layer implemented over CityLearn v2 (CityLearn v3 propuesto). Dependent variable: coordinated performance in energy flexibility, CO2 emissions, and energy costs.
- **Ámbito espacial:** Smart communities simulated through CityLearn v2 and CityLearn v3 propuesto.
- **Ámbito temporal:** 2016–2026 study period aligned with available CityLearn datasets and recent MADRL literature.

### 1.2.1 Antecedentes bibliográficos

Use Module A. Organize antecedents around three thematic axes aligned with the specific objectives:

**Eje 1 — Flexibilidad energética con MADRL:** Antecedents on MADRL for demand response, peak reduction, load shifting, self-consumption, grid-interactive communities, CityLearn v2, and energy flexibility KPIs.

**Eje 2 — Reducción de emisiones de CO2 con MADRL:** Antecedents on carbon-intensity-aware MADRL, CO2 emission reduction in multi-building scenarios, low-carbon demand response, and carbon-weighted consumption metrics.

**Eje 3 — Optimización de costos energéticos con MADRL:** Antecedents on electricity-cost optimization with MADRL, dynamic pricing response, time-of-use strategies, and cost KPIs in smart communities.

**Eje transversal — Marco técnico MADRL:** Antecedents on Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib, Optuna, cooperative reward design, and multi-objective reward functions.

Do not write antecedents without sources and APA citations. All antecedents must come from the bibliographic matrix generated by Module A.

### 1.2.2 Formulación del problema

Formulate the problem from the diagnosis and the identified gap: **no comparative study has determined the best MADRL for coordinated management of energy flexibility, CO2 emissions, and energy costs in smart communities**.

### 1.2.2.1 Formulación del problema general

Use **exactly** (author-validated; do not paraphrase):

> ¿En qué medida el algoritmo MADRL (aprendizaje por refuerzo profundo multiagente) impacta en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño a nivel global?

### 1.2.2.2 Formulación de los problemas específicos

Use **exactly**:

> **PE.1:** ¿En qué medida el algoritmo MADRL impacta en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E1?
>
> **PE.2:** ¿En qué medida el algoritmo MADRL impacta en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E2?
>
> **PE.3:** ¿En qué medida el algoritmo MADRL impacta en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E3?

Each specific problem must be traceable to: (a) the corresponding dimension of the diagnosis, (b) its specific objective, (c) its KPI set, and (d) its comparative evaluation methodology.

### 1.2.3 Justificación y alcances

### 1.2.3.1 Justificación

Develop justification across the following dimensions, all articulated with the three-axis objective structure:

- **Justificación técnica:** The comparative determination of the best MADRL advances the state of the art in cooperative energy management for smart communities.
- **Justificación ambiental:** Identifying the best CO2-reducing MADRL directly contributes to decarbonization goals in grid-interactive communities.
- **Justificación económica:** Establishing the best cost-optimizing MADRL provides actionable guidance for energy cost reduction in smart communities.
- **Justificación metodológica:** The Dec-POMDP formulation, CTDE training, and unified benchmark using CityLearn v3 propuesto, HAPPO, MASAC, MATD3, MAAC, MARLlib, and Optuna constitute a reproducible methodological contribution.
- **Justificación científica:** The unified three-axis evaluation fills a gap in the comparative MADRL literature.
- **Justificación social:** Energy-flexible and low-cost smart communities benefit residential users and contribute to energy transition at the community level.

### 1.2.3.2 Alcances

Specify:

- **Alcance temático:** Comparative evaluation of HAPPO, MASAC, MATD3, and MAAC on energy flexibility, CO2 emissions, and energy cost KPIs in smart community simulation.
- **Alcance espacial:** Smart communities simulated using CityLearn v2 datasets and CityLearn v3 propuesto. Applicability discussion to isolated power systems and grid-interactive communities.
- **Alcance temporal:** Aligned with CityLearn v2 dataset temporal horizons and recent MADRL literature (2015–2025).
- **Alcance metodológico:** Simulation-based, non-experimental, quantitative comparative study.
- **Alcance computacional:** Python, PyTorch, CityLearn v2, CityLearn v3 propuesto, MARLlib (as technical reference), Optuna, available computational resources.
- **Límites y supuestos:** No physical electrical network is modeled. Simulation results do not constitute real-world deployment validation. CityLearn v3 propuesto is an experimental thesis extension, not an official CityLearn release.
- **Exclusiones:** Real-time field deployment, human subject research, economic dispatch of physical generation units, and grid stability analysis are excluded.

## CAPÍTULO II. OBJETIVOS

### 2.1 Objetivo general

Use **exactly** (author-validated; do not paraphrase):

> OG. - Determinar el impacto de los algoritmos aprendizaje por refuerzo profundo multiagente (MADRLs) en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, e identificar cuál de los algoritmos presenta el mejor desempeño a nivel global.

### 2.2 Objetivos específicos

Use **exactly**:

> **OE.1:** Determinar el impacto de los algoritmos MADRLs en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E1.
>
> **OE.2:** Determinar el impacto de los algoritmos MADRLs en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E2.
>
> **OE.3:** Determinar el impacto de los algoritmos MADRLs en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E3.

### 2.3 Hipótesis (add to Chapter II or cross-reference Chapter I)

Use **exactly** H0G/H1G and HE10–HE31:

> **H0G.-** El algoritmo MADRL no impacta de manera estadísticamente significativa y diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas en el desempeño global de los algoritmos.
>
> **H1G.-** El algoritmo MADRL impacta de manera estadísticamente significativa y diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y el desempeño global difiere entre los algoritmos.
>
> **HE10.-** El algoritmo MADRL no impacta de manera estadísticamente significativa en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E1.
>
> **HE11.-** El algoritmo MADRL impacta de manera estadísticamente significativa en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E1.
>
> **HE20.-** El algoritmo MADRL no impacta de manera estadísticamente significativa en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E2.
>
> **HE21.-** El algoritmo MADRL impacta de manera estadísticamente significativa en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E2.
>
> **HE30.-** El algoritmo MADRL no impacta de manera estadísticamente significativa en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E3.
>
> **HE31.-** El algoritmo MADRL impacta de manera estadísticamente significativa en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E3.

Contrast with Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U, Wilcoxon (α = 0,05). Reference Colas et al. (2019) and Agarwal et al. (2021).

## CAPÍTULO III. MARCO TEÓRICO

### 3.1 Bases teóricas

Develop with APA citations across three axes aligned to the objectives, plus one transversal technical axis:

**Eje 1 — Flexibilidad energética en comunidades inteligentes:** smart communities, grid-interactive buildings, distributed energy resources (DER), demand response, load flexibility, peak shaving, load shifting, self-consumption, self-sufficiency, PV, BESS, EV charging, and energy flexibility KPIs.

**Eje 2 — Emisiones de carbono en comunidades inteligentes:** carbon intensity, CO2 emissions from electricity consumption, carbon-aware demand response, low-carbon dispatch, carbon-intensity-weighted energy metrics, and CO2 KPIs.

**Eje 3 — Costos energéticos en comunidades inteligentes:** electricity pricing, time-of-use tariffs, real-time pricing, dynamic pricing, energy cost optimization, demand charge reduction, and cost KPIs.

**Eje transversal — Marco técnico MADRL:** reinforcement learning, deep reinforcement learning (DRL), multi-agent systems, MADRL, cooperative MADRL, Dec-POMDP, partial observability, CTDE, global state, local observations, actions, reward functions, multi-objective reward, HAPPO, MASAC, MATD3, MAAC, MARLlib, Optuna, CityLearn v2, and CityLearn v3 propuesto.

All theoretical bases must carry APA citations. No claim without source.

### 3.2 Definición de términos

Define: MADRL, DRL, agent, environment, global state, local observation, action, reward, policy, Dec-POMDP, CTDE, cooperative MADRL, CityLearn v2, CityLearn v3 propuesto, MARLlib, HAPPO, MASAC, MATD3, MAAC, Optuna, smart community (comunidad inteligente), energy flexibility, demand response, CO2 emissions, carbon intensity, energy costs, electricity pricing, BESS, EV charging, PV, KPIs, energy flexibility KPIs, CO2 KPIs, and cost KPIs.
