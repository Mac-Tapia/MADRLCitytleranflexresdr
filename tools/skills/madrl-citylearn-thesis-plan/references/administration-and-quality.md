# Chapter V, Appendices, and Quality Control

## CAPÍTULO V. ADMINISTRACIÓN DEL PLAN DE TESIS

### 5.1 Cronograma

Include a monthly schedule organized in four phases coherent with the intervention stages:

**Fase preparatoria:**

1. Revisión bibliográfica y construcción de la matriz de 50 antecedentes — Eje 1 (flexibilidad), Eje 2 (CO2), Eje 3 (costos), Eje transversal (marco MADRL).
2. Diagnóstico del problema en comunidades inteligentes.
3. Selección de datasets de CityLearn v2 y definición de KPIs por eje.

**Fase de diseño técnico:**

1. Diseño de la arquitectura CityLearn v3 propuesta.
2. Formulación Dec-POMDP (estado global, observaciones locales, acciones, recompensa multiobjetivo).
3. Implementación del esquema CTDE.
4. Integración del backend HAPPO.
5. Integración del backend MASAC.
6. Integración del backend MATD3.
7. Integración del backend MAAC.
8. Ajuste de hiperparámetros con Optuna.

**Fase de evaluación por eje:**

1. Entrenamiento y simulación de los cuatro backends.
2. Evaluación de KPIs de flexibilidad energética (OE.1).
3. Evaluación de KPIs de emisiones de CO2 (OE.2).
4. Evaluación de KPIs de costos energéticos (OE.3).

**Fase de determinación y cierre:**

1. Análisis comparativo y determinación del mejor MADRL por eje y coordinado (O.G.).
2. Redacción del informe final del plan de tesis.
3. Revisión, corrección y sustentación.

### 5.2 Presupuesto

Structure by: equipo informático duradero, software y servicios computacionales (marcar herramientas open-source como costo cero), servicios tecnológicos, análisis estadístico/computacional, revisión bibliográfica y adquisición de documentos, publicación científica si aplica, asesoría especializada si aplica, viáticos si aplica, materiales de oficina, y contingencia.

### 5.3 Financiamiento

State funding source, self-financing, institutional support if any, own resources, open-source tools (CityLearn v2, MARLlib, Optuna, Python, PyTorch — all zero cost), available computational resources, and potential external cloud/HPC services.

## References

Generate APA references from Module A only. Include articles, theses, technical documentation, datasets, GitHub repositories, software packages, official guides, CityLearn v2 documentation, MARLlib documentation, Optuna documentation, Dec-POMDP and CTDE foundational works, and HAPPO/MASAC/MATD3/MAAC source papers. Organize references alphabetically by first author's last name.

## Appendices

Include:

1. Matriz de consistencia (problema general → problemas específicos → O.G. → OE.1/OE.2/OE.3 → variables → dimensiones → indicadores → metodología → instrumentos → resultados esperados).
2. Matriz de operacionalización de variables.
3. Matriz bibliográfica de 50 investigaciones (Module A output).
4. Matriz de KPIs por eje (flexibilidad, CO2, costos) y por algoritmo (HAPPO, MASAC, MATD3, MAAC).
5. Arquitectura CityLearn v3 propuesta.
6. Comparación de backends MADRL (HAPPO, MASAC, MATD3, MAAC).
7. Datasets y fuentes (CityLearn v2).
8. Configuración preliminar de hiperparámetros.
9. Función de recompensa multiobjetivo (flexibilidad + CO2 + costos).
10. Cadenas de búsqueda (Module A).
11. Evidencias de GitHub (CityLearn, MARLlib, HAPPO, MASAC, MATD3, MAAC).
12. Glosario MADRL.

## Consistency Matrix

The consistency matrix must articulate the full vertical chain:

| Campo | Contenido |
| --- | --- |
| Problema general | ¿Cuál es el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes? |
| Problema específico 1 (PE.1) | ¿Cuál es el mejor MADRL que optimiza la flexibilidad energética en comunidades inteligentes? |
| Problema específico 2 (PE.2) | ¿Cuál es el mejor MADRL que reduce las emisiones de CO2 en comunidades inteligentes? |
| Problema específico 3 (PE.3) | ¿Cuál es el mejor MADRL que optimiza los costos energéticos en comunidades inteligentes? |
| Objetivo general (O.G.) | Determinar el mejor MADRL que gestiona de manera coordinada la flexibilidad energética, las emisiones de CO2 y los costos energéticos en comunidades inteligentes. |
| Objetivo específico 1 (OE.1) | Determinar el mejor MADRL que optimiza la flexibilidad energética en comunidades inteligentes. |
| Objetivo específico 2 (OE.2) | Determinar el mejor MADRL que reduce las emisiones de CO2 en comunidades inteligentes. |
| Objetivo específico 3 (OE.3) | Determinar el mejor MADRL que optimiza los costos energéticos en comunidades inteligentes. |
| Variable independiente | Capa MADRL cooperativa implementada sobre CityLearn v2 (CityLearn v3 propuesto): algoritmos HAPPO, MASAC, MATD3, MAAC bajo Dec-POMDP y CTDE. |
| Variable dependiente | Desempeño coordinado en flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes. |
| Metodología | Cuantitativa, aplicada, comparativa, no experimental, basada en simulación computacional. |
| Técnicas | Simulación, comparación de algoritmos, evaluación de KPIs, análisis multicriterio. |
| Instrumentos | CityLearn v2, CityLearn v3 propuesto, backends MADRL, MARLlib (referencia técnica), Optuna, Python/PyTorch, datasets CityLearn v2. |
| Resultados esperados | Ranking de HAPPO, MASAC, MATD3 y MAAC por eje (OE.1, OE.2, OE.3) y determinación del mejor MADRL en gestión coordinada (O.G.). |

## Operationalization Matrix

**Variable independiente:** Capa MADRL cooperativa implementada sobre CityLearn v2 (CityLearn v3 propuesto).

- Dimensión: Formulación del problema de decisión → Indicadores: tipo de modelo (Dec-POMDP), estado global, observaciones locales, espacio de acciones, función de recompensa multiobjetivo.
- Dimensión: Esquema de entrenamiento → Indicadores: CTDE implementado, backend utilizado (HAPPO/MASAC/MATD3/MAAC), hiperparámetros ajustados con Optuna.
- Dimensión: Cooperación entre agentes → Indicadores: tipo de cooperación (totalmente cooperativo), política centralizada vs. descentralizada, compartición de estado global.

**Variable dependiente:** Desempeño coordinado en flexibilidad energética, emisiones de CO2 y costos energéticos en comunidades inteligentes.

- Dimensión 1 (OE.1) — Flexibilidad energética: reducción de pico de demanda, factor de carga, auto-consumo, auto-suficiencia, reducción de importación de red, desplazamiento de carga, utilización de renovables.
- Dimensión 2 (OE.2) — Emisiones de CO2: reducción de emisiones de carbono, consumo ponderado por intensidad de carbono, emisiones evitadas, equilibrio emisiones-costo.
- Dimensión 3 (OE.3) — Costos energéticos: reducción de costo de electricidad, optimización de tarifas de uso horario, reducción de cargo por demanda, respuesta a precios dinámicos.

**Variables de control:** dataset climático, perfil de demanda, intensidad de carbono, precio de electricidad, capacidad BESS, penetración PV, escenario de carga EV, restricciones operacionales, hiperparámetros de entrenamiento.

## Mandatory KPIs

Organized by axis and linked to each specific objective:

**OE.1 — Flexibilidad energética:** peak demand reduction, ramping reduction, load factor improvement, load shifting, self-consumption rate, self-sufficiency rate, grid import reduction, renewable utilization rate.

**OE.2 — Emisiones de CO2:** total carbon emissions, CO2 reduction vs. baseline, carbon-intensity-weighted consumption, avoided emissions, emission-cost trade-off index.

**OE.3 — Costos energéticos:** total electricity cost, cost reduction vs. baseline, demand charge reduction, time-of-use optimization index, dynamic pricing response.

**O.G. — Gestión coordinada:** composite ranking score integrating KPIs from OE.1, OE.2, and OE.3 across HAPPO, MASAC, MATD3, and MAAC.

**MADRL training KPIs (transversal):** cumulative reward, average episode reward, convergence speed, actor loss, critic loss, entropy, policy stability, sample efficiency, robustness across seeds, constraint violations.

## Final Quality Checklist

Verify:

1. The structure follows Guide N. 01 section 5.1.
2. The document is a professional/specialization master's thesis plan.
3. Current APA is used throughout. IEEE is not used.
4. The thesis title matches exactly: *Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en Comunidades Inteligentes*.
5. `Marco_metodologico_MARL` does not appear; `Marco_metodologico_MADRL` appears where required.
6. CityLearn v3 is presented exclusively as `CityLearn v3 propuesto`.
7. MARLlib is used only as a proper name.
8. Chapter numbering is correct.
9. Antecedents come from the bibliographic matrix (Module A) and are organized by three axes + transversal.
10. Theoretical bases have APA citations organized by axis.
11. **Vertical coherence — diagnosis → problems → objectives:**
    - Diagnosis (§1.1) identifies three dimensions: flexibility, CO2, costs.
    - PE.1 responds to the flexibility dimension of the diagnosis.
    - PE.2 responds to the CO2 dimension of the diagnosis.
    - PE.3 responds to the costs dimension of the diagnosis.
    - O.G. integrates the three dimensions.
    - OE.1, OE.2, OE.3 respond directly to PE.1, PE.2, PE.3.
12. **Horizontal coherence — variables → dimensions → KPIs:**
    - Variable dependiente has three dimensions (OE.1, OE.2, OE.3).
    - Each dimension has its own KPI set.
    - KPIs align with methodology, techniques, and instruments.
13. The study determines the *best* MADRL (HAPPO, MASAC, MATD3, or MAAC) per axis and in coordinated management — it does not only design or validate a system.
14. The scope is smart communities (comunidades inteligentes), simulated via CityLearn v2 and CityLearn v3 propuesto.
15. Schedule phases align with the four intervention phase groups (preparatoria, diseño técnico, evaluación por eje, determinación y cierre).
16. Budget and financing are consistent and realistic.
17. No citation lacks a final reference; no final reference lacks a citation.
18. No results are invented. Quantitative results are marked `por definir en la etapa de implementación experimental`.
19. Real antecedents, methodological proposal, and expected results are clearly differentiated.
20. The consistency matrix covers: problema general, PE.1–PE.3, O.G., OE.1–OE.3, variables, dimensions, indicators, methodology, techniques, instruments, and expected results.
