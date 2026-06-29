# Chapter IV: Diseño Metodológico

## 4.1 Tipo y nivel de investigación

Default classification (aligned with `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`):

- Enfoque: cuantitativo.
- Tipo: aplicada.
- Nivel: explicativo (relación causa-efecto).
- Diseño: **experimental de simulación computacional**, factorial completo 4×3 (12 tratamientos).
- Método: modelamiento Dec-POMDP/CTDE, manipulación controlada de VI (algoritmo × escenario E1/E2/E3), medición de VD con 54 KPI oficiales, análisis descriptivo e inferencial no paramétrico.

Justify every methodological classification. The experimental level is essential: the study determines the *effect* of each MADRL algorithm and identifies the algorithm with the largest coordinated effect on energy flexibility, CO2 emissions, and energy costs.

## 4.2 Unidad de análisis

Define the unit of analysis as:

- Comunidades inteligentes simuladas mediante CityLearn v2 y CityLearn v3 propuesto.
- Agentes MADRL cooperativos (HAPPO, MASAC, MATD3, MAAC) bajo Dec-POMDP y CTDE.
- Recursos de energía distribuida (DER): edificios, BESS, PV y estaciones de carga EV.
- Indicadores de desempeño energético, ambiental y económico (KPIs de flexibilidad energética, emisiones de CO2 y costos energéticos).

Specify what will be observed (agent policies and rewards), simulated (episodes and time steps), measured (KPI values per algorithm), and compared (algorithm rankings per axis and overall).

## 4.3 Población de estudio

For simulation research, explain that the population is not human subjects. Define the population as:

- Escenarios simulados de comunidades inteligentes con múltiples edificios y recursos DER.
- Series temporales de demanda energética, precio de electricidad e intensidad de carbono provenientes de los datasets de CityLearn v2.
- Configuraciones de agentes MADRL bajo distintos backends (HAPPO, MASAC, MATD3, MAAC) y distintos ajustes de hiperparámetros.

## 4.4 Tamaño de muestra

Define:

- Número de algoritmos MADRL comparados: 4 (HAPPO, MASAC, MATD3, MAAC) más un baseline de control por reglas o DRL de agente único.
- Número de episodios de entrenamiento, pasos de tiempo y horizonte de evaluación: `por definir en la etapa de implementación experimental`.
- Número de configuraciones de hiperparámetros exploradas por Optuna: `por definir en la etapa de implementación experimental`.
- Número de semillas aleatorias para análisis de robustez: `por definir en la etapa de implementación experimental`.
- Datasets de CityLearn v2 utilizados: los disponibles en el repositorio oficial de CityLearn v2.

Do not invent quantities. If values are not final, write `por definir en la etapa de implementación experimental`.

## 4.5 Selección de muestra

Use non-probabilistic, intentional, technically convenient sampling justified by:

- Disponibilidad de los datasets de CityLearn v2.
- Relevancia de los algoritmos HAPPO, MASAC, MATD3 y MAAC para el problema de gestión cooperativa.
- Aplicabilidad de los escenarios simulados al problema de gestión coordinada de flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes.

## 4.6 Técnicas de recolección de datos

Include:

- Revisión bibliográfica sistemática y construcción de matriz de antecedentes (Module A).
- Análisis de documentación oficial de CityLearn v2, MARLlib, HAPPO, MASAC, MATD3, MAAC, y Optuna.
- Extracción y preprocesamiento de datasets de CityLearn v2.
- Registro de métricas de entrenamiento MADRL (recompensa acumulada, pérdida del actor, pérdida del crítico, entropía).
- Registro de KPIs de evaluación por eje: flexibilidad energética (OE.1), emisiones de CO2 (OE.2), costos energéticos (OE.3).
- Registro de configuraciones de hiperparámetros y resultados de Optuna.

## 4.7 Técnicas e instrumentos de análisis y procesamiento de datos

Include:

- Limpieza, normalización y procesamiento de series temporales de los datasets.
- Análisis descriptivo de KPIs por algoritmo y por eje de evaluación.
- **Comparación de algoritmos MADRL:** tabla comparativa de HAPPO, MASAC, MATD3, y MAAC por KPI en cada eje (OE.1, OE.2, OE.3) y ranking integrado para el O.G.
- Análisis de convergencia, estabilidad y robustez del entrenamiento MADRL.
- Análisis multiobjetivo y multicriterio para la determinación del mejor algoritmo.
- Comparación contra baseline (reglas o DRL de agente único).
- Visualizaciones: curvas de entrenamiento, gráficas de KPIs por eje, matrices de comparación, tablas de ranking.

Instruments: matriz bibliográfica (Module A), matriz de KPIs, CityLearn v2, CityLearn v3 propuesto, scripts MADRL en Python/PyTorch, backends HAPPO/MASAC/MATD3/MAAC, MARLlib como referencia técnica, Optuna, Gymnasium, PettingZoo si aplica, datasets de CityLearn v2, y hojas de resultados.

## 4.8 Etapas de intervención del estudio

Organize phases across the three objective axes:

**Fase preparatoria:**

1. Revisión bibliográfica profunda y construcción de la matriz de 50 antecedentes (Module A) — organizada por Eje 1 (flexibilidad), Eje 2 (CO2), Eje 3 (costos) y Eje transversal (marco MADRL).
2. Diagnóstico del problema energético en comunidades inteligentes y definición de variables.
3. Selección de datasets de CityLearn v2 y definición de KPIs por eje.

**Fase de diseño técnico:**
4. Diseño de la arquitectura CityLearn v3 propuesta (extensión experimental sobre CityLearn v2).
5. Formulación Dec-POMDP: estado global, observaciones locales, acciones y función de recompensa multiobjetivo (flexibilidad + CO2 + costos).
6. Implementación del esquema CTDE.
7. Integración de backends HAPPO, MASAC, MATD3 y MAAC.
8. Ajuste de hiperparámetros con Optuna.

**Fase de evaluación por eje (aligned to specific objectives):**
9. Entrenamiento y simulación de los cuatro backends.
10. Evaluación de flexibilidad energética (OE.1): KPIs de reducción de pico, factor de carga, auto-consumo, desplazamiento de carga.
11. Evaluación de emisiones de CO2 (OE.2): KPIs de reducción de emisiones, consumo ponderado por intensidad de carbono, emisiones evitadas.
12. Evaluación de costos energéticos (OE.3): KPIs de reducción de costo, optimización de tarifas horarias, reducción de cargo por demanda.

**Fase de determinación y cierre (aligned to general objective):**
13. Comparación de resultados por eje y ranking integrado de los cuatro backends (O.G.).
14. Determinación del mejor MADRL por eje y en gestión coordinada.
15. Discusión de aplicabilidad a comunidades inteligentes y a sistemas eléctricos aislados.
16. Redacción final del plan de tesis y preparación de anexos.
