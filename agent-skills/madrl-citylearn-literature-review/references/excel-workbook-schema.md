# Excel Workbook Schema

## Required Worksheets

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

## `Matriz_50_investigaciones` Columns

1. N.º
2. Año
3. Idioma
4. Tipo de documento
5. Título de la investigación
6. Autor(es)
7. Universidad, revista o congreso
8. Indexación o fuente
9. País o contexto de estudio
10. Palabras clave asociadas
11. Relación con CityLearn v2
12. Relación con CityLearn v3 propuesto
13. Relación con MADRL
14. Relación con MARLlib
15. MARLlib usado directamente: sí/no/parcial
16. MARLlib como referencia metodológica
17. Compatibilidad con MARLlib
18. Tipo de integración posible con CityLearn v2
19. Requiere wrapper personalizado
20. Requiere adaptación a Dec-POMDP
21. Requiere adaptación CTDE
22. Requiere backend personalizado
23. Problema de investigación
24. Objetivo de investigación
25. Variables de investigación
26. Variable independiente
27. Variable dependiente
28. Variables de control
29. Nivel de investigación
30. Diseño de investigación
31. Metodología empleada
32. Algoritmo o modelo usado
33. Backend asociado: HAPPO, MASAC, MATD3, MAAC u otro
34. Tipo de cooperación
35. CTDE: sí/no/parcial
36. Modelo formal: MMDP, Dec-POMDP u otro
37. Observabilidad: total, parcial o no especificada
38. Estado global usado
39. Observaciones locales usadas
40. Acciones de los agentes
41. Función de recompensa
42. Recompensa individual, compartida o híbrida
43. Enfoque multiobjetivo
44. Enfoque multicriterio
45. Uso de Optuna o ajuste de hiperparámetros
46. Hiperparámetros ajustados
47. Métricas de entrenamiento MADRL
48. Métricas de convergencia
49. Métricas de robustez
50. Métricas de estabilidad
51. Entorno virtual o simulador usado
52. Dataset usado
53. Link o ubicación del dataset
54. Variables del dataset
55. GitHub o repositorio de código
56. Link del PDF o artículo
57. DOI o enlace académico
58. KPIs de flexibilidad energética
59. KPIs de emisiones de CO₂
60. KPIs de costos energéticos
61. KPIs de respuesta de demanda
62. KPIs de resiliencia eléctrica
63. Resultados principales
64. Resultados cuantitativos
65. Aporte a la ciencia
66. Conclusiones principales
67. Limitaciones
68. Aplicabilidad a CityLearn v3 propuesto
69. Aplicabilidad a sistemas eléctricos aislados
70. Aplicabilidad al SEAI Iquitos
71. Relación con PV, BESS o EV charging
72. Utilidad para la tesis
73. Prioridad de lectura
74. Observaciones de verificación

## Additional Sheet Guidance

- `Resumen_ejecutivo`: synthesize evidence, gaps, thesis justification, and prioritized findings.
- `KPIs_y_metricas`: group KPIs by flexibility, CO2 emissions, costs, demand response, resilience, and MADRL training.
- `Marco_metodologico_MADRL`: define methodology terms and explain why the proposal is MADRL, Dec-POMDP, and CTDE.
- `CityLearn_v3_Propuesto`: describe the experimental extension over CityLearn v2, not an official release.
- `Backends_MADRL`: compare HAPPO, MASAC, MATD3, and MAAC.
- `MARLlib_Integracion`: analyze MARLlib as a proper-name framework/reference.
- `CityLearn_CO2_Costos`: explain CityLearn carbon intensity, pricing, net electricity consumption, cost, emissions, demand response, storage, EV, BESS, and multi-objective reward.
- `Datasets_y_codigo`: list datasets, GitHub repositories, source availability, and reproducibility notes.
- `Lectura_priorizada`: rank readings by thesis usefulness.
- `Cadenas_de_busqueda`: record exact queries, source searched, date, and relevant hits.
- `Glosario_MADRL`: define MADRL, DRL, CTDE, Dec-POMDP, MMDP, HAPPO, MASAC, MATD3, MAAC, Optuna, MARLlib, CityLearn v2, and CityLearn v3 propuesto.
- `Arquitectura_Propuesta`: describe CityLearn v2 base, wrapper, Dec-POMDP, local observations, global state, actions, multi-objective reward, CTDE training, decentralized execution, backends, MARLlib reference, Optuna, KPIs, datasets, reports, baseline comparison, and SEAI Iquitos.
- `Aplicabilidad_SEAI_Iquitos`: map findings to isolated system operation, PV, BESS, EV charging, flexibility, thermal generation imports, CO2, costs, constraints, and KPI validation.

