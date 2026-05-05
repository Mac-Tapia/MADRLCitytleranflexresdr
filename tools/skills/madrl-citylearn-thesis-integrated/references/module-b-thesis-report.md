# Module B: Thesis Report under Guide N. 02 Section 5.1

Use Module A outputs as mandatory input. Do not draft the report in isolation.

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

Include university, graduate school, faculty or academic unit, full thesis title, academic degree, student, advisor, Lima, Peru, and year.

### Resumen - Abstract

Write in Spanish and English. Include SEAI Iquitos context, problem, objective, methodology, CityLearn v3 propuesto, MADRL backends, KPIs for flexibility, CO2 emissions and costs, obtained or expected results, main conclusions, and keywords.

### Introducción

Integrate energy and environmental context, isolated systems, SEAI Iquitos, optimal dispatch, safe operation, intelligent control need, limitations of single-agent DRL, need for cooperative MADRL, Dec-POMDP, CTDE, CityLearn v2 as base environment, CityLearn v3 propuesto, MARLlib as technical reference, Optuna, and chapter synthesis.

### Chapter I

Develop diagnosis, problem identification, problem formulation, objectives, justification, and scope. The general problem must integrate CityLearn v2, cooperative MADRL layer, CityLearn v3 propuesto, Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, energy flexibility, CO2 emissions, costs, safe operation, and SEAI Iquitos.

Use this objective general formulation unless the user gives a final institutional version:

> Diseñar y validar un sistema eléctrico inteligente con control MADRL colaborativo sobre CityLearn v2, mediante una extensión experimental CityLearn v3 formulada como Dec-POMDP y entrenada bajo CTDE, para optimizar el despacho bajo restricciones eléctricas y operación segura en el SEAI Iquitos, evaluando flexibilidad energética, emisiones de CO2 y costos energéticos.

### Chapter II

Use the Module A matrix for antecedents. Organize antecedents by CityLearn v2, MADRL in energy, Dec-POMDP and CTDE, HAPPO/MASAC/MATD3/MAAC, MARLlib, energy flexibility, CO2 emissions, energy costs, BESS/PV/EV charging, and isolated power systems.

Each antecedent must include author-year, objective, methodology, dataset/environment, algorithm, main results, thesis contribution, and APA citation.

### Chapter III

Present CityLearn v2 as base environment and CityLearn v3 propuesto as experimental extension. Include cooperative MADRL layer, Dec-POMDP formulation, CTDE training, HAPPO, MASAC, MATD3, MAAC, MARLlib as technical reference, Optuna, KPIs, and SEAI Iquitos applicability.

Include tables for architecture components, inputs/outputs, agents, local observations, global state, actions, reward function, KPIs, MADRL backends, and datasets.

For results, use actual simulation outputs when available. If final results are not available, write `resultados esperados`, `resultados por validar`, `indicadores a estimar`, or `escenarios de simulación propuestos`. Do not invent values.

### Chapter IV

Write one general conclusion, one conclusion per specific objective, and methodological, technical, environmental, economic, and SEAI Iquitos applicability conclusions. Recommendations must derive from conclusions.

