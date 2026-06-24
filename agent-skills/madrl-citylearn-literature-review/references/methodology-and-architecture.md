# Methodology and Architecture Guidance

## `Marco_metodologico_MADRL`

Explain, with thesis orientation:

1. MADRL
2. DRL
3. Agente
4. Entorno
5. Estado global
6. Observación local
7. Acción
8. Recompensa
9. Política
10. Valor
11. Cooperación
12. Control colaborativo
13. CTDE
14. MMDP
15. Dec-POMDP
16. Observabilidad parcial
17. Recompensa multiobjetivo
18. Optuna
19. Ajuste de hiperparámetros
20. HAPPO
21. HATRPO
22. MASAC
23. MATD3
24. MAAC
25. MADDPG
26. MAPPO
27. Métricas de convergencia
28. Métricas de robustez
29. Métricas de estabilidad
30. Eficiencia muestral
31. Integración con CityLearn v2
32. Justificación de CityLearn v3 propuesto
33. Rol de MARLlib como framework de referencia
34. Diferencia terminológica entre MADRL y MARLlib como nombre propio

## `CityLearn_v3_Propuesto`

Develop CityLearn v3 propuesto as an experimental extension of CityLearn v2 with:

- collaborative MADRL layer;
- Dec-POMDP formulation;
- CTDE training;
- HAPPO, MASAC, MATD3, and MAAC backends;
- Gymnasium integration;
- potential PettingZoo integration;
- MARLlib integration or technical reference;
- local observation module;
- global state module;
- multi-agent action module;
- multi-objective reward module;
- KPI evaluation module;
- Optuna tuning module;
- baseline comparison module;
- dataset module;
- reports and reproducibility modules;
- validation modules for energy flexibility, CO2 emissions, and energy costs.

## `KPIs_y_metricas`

Group KPIs as follows:

- Energy flexibility: peak demand reduction, ramping reduction, load factor, load shifting, self-consumption, self-sufficiency, grid import reduction, renewable utilization.
- CO2 emissions: carbon emissions, CO2 reduction, carbon-intensity-weighted consumption, avoided emissions, emission-cost trade-off.
- Energy costs: electricity cost, cost reduction, demand charge reduction, time-of-use optimization, dynamic pricing response.
- Demand response: PAR reduction, peak shaving, load profile flattening, demand shifting.
- Electrical resilience: ENS, EENS, SAIDI, SAIFI, recovery time, unserved energy.
- MADRL: cumulative reward, average episode reward, convergence speed, actor loss, critic loss, entropy, stability, sample efficiency, robustness, constraint violations.

## `Arquitectura_Propuesta`

Present a technical architecture with:

- CityLearn v2 as base environment;
- multi-agent wrapper;
- Dec-POMDP formulation;
- local observations by agent;
- global state for training;
- actions per agent;
- multi-objective reward;
- CTDE training;
- decentralized execution;
- HAPPO, MASAC, MATD3, and MAAC backends;
- MARLlib reference/integration layer;
- Optuna layer;
- KPI evaluation layer;
- dataset layer;
- reporting layer;
- baseline comparison;
- validation for flexibility, CO2 emissions, and energy costs;
- SEAI Iquitos applicability.

## `MARLlib_Integracion`

Explain MARLlib as a proper-name framework:

- what MARLlib is;
- relation to RLlib/Ray;
- relation to PyTorch;
- wrappers, scenario config, algorithm config, policy mapping, CTDE, POMDP/Dec-POMDP;
- possible CityLearn v2 integration and need for a custom wrapper;
- reproducibility advantages and limitations;
- algorithms officially supported vs requiring custom extension;
- relevance to HAPPO, MASAC, MATD3, and MAAC;
- role inside CityLearn v3 propuesto.

## `Aplicabilidad_SEAI_Iquitos`

Relate findings to:

- isolated power system of Iquitos;
- safe operation and optimal dispatch;
- PV, BESS, and EV charging;
- energy flexibility;
- reduction of imports from thermal grid operation;
- CO2 emissions reduction;
- energy cost reduction;
- electrical constraints;
- collaborative multiagent control;
- KPI validation;
- potential adaptation from CityLearn v2 to CityLearn v3 propuesto.

