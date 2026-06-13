# Module A: Deep Search and Bibliographic Matrix

## Objective

Search, verify, and systematize 50 relevant investigations from the last 10 years when possible to support the thesis on CityLearn v2, CityLearn v3 propuesto, cooperative MADRL, Dec-POMDP, CTDE, and SEAI Iquitos.

## Source Types

Include doctoral theses, PhD dissertations, master's theses, indexed papers, scientific proceedings, benchmarks, technical reports, official documentation, datasets, and GitHub repositories.

## Mandatory Search Topics

- CityLearn v2; CityLearn Challenge 2022/2023; CityLearn Gymnasium; CityLearn datasets; carbon intensity; electricity pricing; demand response; flexibility; BESS; EV charging; V2G; wrappers; PettingZoo; Dec-POMDP; CTDE; MADRL; DRL.
- MADRL; DRL; cooperative MADRL; collaborative MADRL; multi-agent actor critic; multi-agent energy management; distributed control; decentralized execution; centralized training; MMDP; Dec-POMDP; partially observable stochastic game; shared reward; local observation; global state; joint action.
- HAPPO; HATRPO; MASAC; Multi-Agent Soft Actor-Critic; MATD3; Multi-Agent Twin Delayed Deep Deterministic Policy Gradient; MAAC; Multi-Actor-Attention-Critic; MADDPG; MAPPO; IPPO; COMA; QMIX; VDN; MADQN.
- MARLlib as proper-name framework: documentation, GitHub, JMLR/arXiv paper, benchmarks, custom environment wrappers, PettingZoo, Gymnasium, RLlib, Ray, PyTorch, CTDE, Dec-POMDP, policy mapping, reproducibility, and algorithm support.
- Energy flexibility; CO2 emissions; carbon-aware control; energy costs; dynamic pricing; demand response; Optuna; virtual environments; digital twins; datasets; PV; BESS; EV charging.
- Spanish keywords: aprendizaje por refuerzo profundo multiagente, MADRL, CityLearn v2, CityLearn v3 propuesto, control multiagente colaborativo, CTDE, Dec-POMDP, flexibilidad energetica, emisiones de CO2, costos energeticos, Optuna, MARLlib.

## Minimum Boolean Strings

1. `("CityLearn v2" OR "CityLearn") AND ("carbon emissions" OR "CO2 emissions" OR "carbon intensity") AND ("energy cost" OR "electricity pricing" OR "electricity cost")`
2. `("CityLearn v2" OR "CityLearn Challenge" OR "CityLearn") AND ("multi-agent deep reinforcement learning" OR MADRL OR "cooperative multi-agent reinforcement learning") AND ("demand response" OR "energy flexibility" OR "grid-interactive communities")`
3. `("CityLearn v2" OR "CityLearn") AND ("Dec-POMDP" OR "partially observable game") AND ("centralized training decentralized execution" OR CTDE)`
4. `("multi-agent deep reinforcement learning" OR MADRL) AND ("centralized training decentralized execution" OR CTDE) AND ("Dec-POMDP" OR "partially observable stochastic game" OR "partially observable game")`
5. `(HAPPO OR MASAC OR MATD3 OR MAAC) AND ("multi-agent deep reinforcement learning" OR MADRL) AND ("energy management" OR "demand response" OR "smart grid" OR "building control")`
6. `("MARLlib" OR "Multi-Agent RLlib") AND ("multi-agent reinforcement learning" OR "multi-agent deep reinforcement learning" OR MADRL) AND (CTDE OR "centralized training decentralized execution")`
7. `("MARLlib" OR "Multi-Agent RLlib") AND ("custom environment" OR "environment wrapper" OR Gymnasium OR PettingZoo) AND ("CityLearn" OR "energy management" OR "demand response")`
8. `("MARLlib" OR "Multi-Agent RLlib") AND (HAPPO OR HATRPO OR MASAC OR MATD3 OR MAAC OR MADDPG OR MAPPO) AND ("GitHub" OR "source code" OR "implementation")`
9. `("energy flexibility" OR "electric flexibility" OR "demand flexibility") AND ("multi-agent deep reinforcement learning" OR MADRL) AND (KPI OR metrics OR benchmark)`
10. `("carbon emissions" OR "CO2 emissions" OR "carbon intensity") AND ("multi-agent deep reinforcement learning" OR MADRL OR "deep reinforcement learning") AND ("energy management" OR "demand response")`
11. `("energy cost" OR "electricity cost" OR "electricity pricing" OR tariff) AND ("multi-agent deep reinforcement learning" OR MADRL OR "deep reinforcement learning") AND ("demand response" OR "building energy management")`
12. `("PhD thesis" OR "doctoral dissertation" OR "master thesis" OR "MSc thesis" OR "tesis doctoral" OR "tesis de maestria") AND ("multi-agent deep reinforcement learning" OR MADRL OR "deep reinforcement learning") AND ("demand response" OR "smart grid" OR "energy management" OR "CityLearn")`
13. `("CityLearn" OR "multi-agent deep reinforcement learning" OR MADRL OR "MARLlib") AND ("dataset" OR "benchmark" OR "GitHub" OR "source code" OR "repository") AND ("energy management" OR "demand response" OR "carbon emissions" OR "energy cost")`

## Priority Sources

Search Google Scholar, IEEE Xplore, ScienceDirect, SpringerLink, MDPI, ACM Digital Library, Wiley, Taylor & Francis, arXiv, OpenReview, PMLR, NeurIPS, ICML, ICLR, AAMAS, Energy and Buildings, Applied Energy, Energy AI, Sustainable Cities and Society, Electric Power Systems Research, International Journal of Electrical Power & Energy Systems, IEEE Transactions on Smart Grid, IEEE Transactions on Sustainable Energy, IEEE Transactions on Power Systems, IEEE Access, JMLR, university repositories, ProQuest Dissertations, EThOS, DART-Europe, TDX, Cybertesis, RENATI, GitHub, Papers with Code, CityLearn documentation, CityLearn GitHub, MARLlib GitHub, MARLlib documentation, NREL, OpenEI, Pecan Street, UK-DALE, REDD, and Open Power System Data.

## Required Workbook Sheets

Create:

1. `Matriz_50_investigaciones`
2. `Resumen_ejecutivo`
3. `KPIs_y_metricas`
4. `Marco_metodologico_MADRL`
5. `CityLearn_v3_Propuesto`
6. `Backends_MADRL`
7. `MARLlib_Integracion`
8. `CityLearn_CO2_Costos`
9. `Datasets_y_codigo`
10. `Lectura_priorizada`
11. `Cadenas_de_busqueda`
12. `Glosario_MADRL`
13. `Arquitectura_Propuesta`
14. `Aplicabilidad_SEAI_Iquitos`
15. `Referencias_APA_Base`

## Minimum Columns for `Matriz_50_investigaciones`

Use at least these 62 columns: N.º; Año; Idioma; Tipo de documento; Título de la investigación; Autor(es); Universidad, revista o congreso; Indexación o fuente; País o contexto de estudio; Palabras clave asociadas; Relación con CityLearn v2; Relación con CityLearn v3 propuesto; Relación con MADRL; Relación con MARLlib; Problema de investigación; Objetivo de investigación; Variables de investigación; Nivel de investigación; Diseño de investigación; Metodología empleada; Algoritmo o modelo usado; Backend asociado: HAPPO, MASAC, MATD3, MAAC u otro; Tipo de cooperación; CTDE: sí/no/parcial; Modelo formal: MMDP, Dec-POMDP u otro; Observabilidad; Estado global usado; Observaciones locales usadas; Acciones de los agentes; Función de recompensa; Recompensa individual, compartida o híbrida; Enfoque multiobjetivo; Enfoque multicriterio; Uso de Optuna o ajuste de hiperparámetros; Hiperparámetros ajustados; Métricas de entrenamiento MADRL; Entorno virtual o simulador usado; Dataset usado; Link o ubicación del dataset; Variables del dataset; GitHub o repositorio de código; Link del PDF o artículo; DOI o enlace académico; KPIs de flexibilidad energética; KPIs de emisiones de CO2; KPIs de costos energéticos; KPIs de respuesta de demanda; KPIs de resiliencia eléctrica; Resultados principales; Resultados cuantitativos; Aporte a la ciencia; Conclusiones principales; Limitaciones; Aplicabilidad a CityLearn v3 propuesto; Aplicabilidad a sistemas eléctricos aislados; Aplicabilidad al SEAI Iquitos; Relación con PV, BESS o EV charging; Utilidad para la tesis; Prioridad de lectura; Cita APA en texto; Referencia APA completa; Observaciones de verificación.

