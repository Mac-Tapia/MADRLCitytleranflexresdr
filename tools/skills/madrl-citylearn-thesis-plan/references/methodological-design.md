# Chapter IV: Diseño Metodológico

## 4.1 Tipo y nivel de investigación

Default classification unless the user provides a different institutional requirement:

- Enfoque: cuantitativo.
- Tipo: aplicada.
- Nivel: descriptivo, explicativo y propositivo.
- Diseño: no experimental, transversal, basado en simulación computacional.
- Método: modelamiento, simulación, comparación de algoritmos y análisis de indicadores.

Justify every methodological classification.

## 4.2 Unidad de análisis

Define the unit of analysis as:

- CityLearn v2 energy environment.
- Cooperative MADRL agents.
- Buildings, DERs, BESS, PV, and EV charging according to the simulation scenario.
- Energy, environmental, and economic performance indicators.

Specify what will be observed, simulated, measured, and compared.

## 4.3 Población de estudio

For simulation research, explain that the population is not human subjects. Define the population as simulated energy scenarios, hourly demand profiles, electricity price series, carbon intensity series, renewable generation profiles, agent/backends configurations, and representative SEAI Iquitos scenarios.

## 4.4 Tamaño de muestra

Define number of simulated scenarios, training episodes, time steps, evaluation horizon, backends, hyperparameter configurations, and random seeds when available. Do not invent quantities. If values are not final, write `por definir en la etapa de implementación experimental`.

## 4.5 Selección de muestra

Use non-probabilistic, intentional, technically convenient sampling when justified by dataset availability, CityLearn v2 relevance, and applicability to the research problem.

## 4.6 Técnicas de recolección de datos

Include documentary analysis, systematic review, official documentation review, dataset extraction, simulation data collection, MADRL training metric logging, energy/environmental/economic KPI logging, extraction from CityLearn v2 and CityLearn v3 propuesto, and Optuna hyperparameter records.

## 4.7 Técnicas e instrumentos de análisis y procesamiento de datos

Include data cleaning, normalization, time-series processing, descriptive analysis, algorithm comparison, KPI evaluation, multi-objective analysis, multicriteria analysis, convergence analysis, stability analysis, robustness analysis, baseline comparison, comparative tables, training graphs, KPI graphs, and result matrices.

Instruments: bibliographic matrix, KPI matrix, CityLearn v2, CityLearn v3 propuesto, MADRL scripts, HAPPO/MASAC/MATD3/MAAC backends, MARLlib as technical reference, Optuna, Python, PyTorch, Gymnasium, PettingZoo if applicable, GitHub repositories, energy datasets, and result spreadsheets.

## 4.8 Etapas de intervención del estudio

Use these phases:

1. Revisión bibliográfica profunda y matriz de antecedentes.
2. Diagnóstico del problema energético y definición de variables.
3. Selección de datasets y KPIs.
4. Diseño de la arquitectura CityLearn v3 propuesta.
5. Formulación Dec-POMDP.
6. Implementación del esquema CTDE.
7. Integración de backends HAPPO, MASAC, MATD3 y MAAC.
8. Diseño de recompensa multiobjetivo.
9. Ajuste de hiperparámetros con Optuna.
10. Entrenamiento y simulación.
11. Evaluación de flexibilidad energética.
12. Evaluación de emisiones de CO2.
13. Evaluación de costos energéticos.
14. Comparación de resultados.
15. Validación de aplicabilidad al SEAI Iquitos.
16. Redacción final del plan y preparación de anexos.

