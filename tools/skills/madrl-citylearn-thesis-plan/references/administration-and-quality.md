# Chapter V, Appendices, and Quality Control

## CAPÍTULO V. ADMINISTRACIÓN DEL PLAN DE TESIS

### 5.1 Cronograma

Include a monthly schedule with at least:

1. Revisión bibliográfica.
2. Construcción de matriz de antecedentes.
3. Diagnóstico del SEAI Iquitos.
4. Selección de datasets.
5. Diseño de arquitectura CityLearn v3 propuesta.
6. Diseño del wrapper MADRL.
7. Formulación Dec-POMDP.
8. Implementación CTDE.
9. Integración HAPPO.
10. Integración MASAC.
11. Integración MATD3.
12. Integración MAAC.
13. Ajuste con Optuna.
14. Simulaciones.
15. Evaluación de KPIs.
16. Análisis comparativo.
17. Redacción del informe.
18. Revisión y sustentación.

### 5.2 Presupuesto

Structure by: durable equipment, software and computational services, technological services, statistical/computational analysis, bibliographic review and document acquisition, scientific publication, specialized advisory if applicable, travel and per diem if applicable, office materials, and contingency. Mark free/open-source software as zero cost.

### 5.3 Financiamiento

State funding source, self-financing, institutional support if any, own resources, open-source tools, available computational resources, and potential external services.

## References

Generate APA references from Module A only. Include articles, theses, technical documentation, datasets, GitHub, software, official guides, CityLearn, MARLlib, Optuna, Dec-POMDP, CTDE, and HAPPO/MASAC/MATD3/MAAC sources.

## Appendices

Include:

1. Matriz de consistencia.
2. Matriz de operacionalización de variables, cuando corresponda.
3. Matriz bibliográfica de 50 investigaciones.
4. Matriz de KPIs.
5. Arquitectura CityLearn v3 propuesta.
6. Comparación de backends MADRL.
7. Datasets y fuentes.
8. Configuración preliminar de hiperparámetros.
9. Función de recompensa multiobjetivo.
10. Cadenas de búsqueda.
11. Evidencias de GitHub.
12. Glosario MADRL.

## Consistency Matrix

Include general problem, specific problems, general objective, specific objectives, hypothesis if applicable, variables, dimensions, indicators, methodology, techniques, instruments, and expected results.

## Operationalization Matrix

Variable independiente: Capa MADRL colaborativa implementada sobre CityLearn v2.

Variable dependiente: Desempeño del despacho óptimo bajo restricciones eléctricas y operación segura.

Dependent dimensions: energy flexibility, CO2 emissions, energy costs, safe operation, and MADRL learning performance.

Control variables: climate dataset, demand profile, carbon intensity, electricity price, BESS capacity, PV penetration, EV charging scenario, operational constraints, and training hyperparameters.

## Mandatory KPIs

- Flexibilidad energética: peak demand reduction, ramping reduction, load factor, load shifting, self-consumption, self-sufficiency, grid import reduction, renewable utilization.
- Emisiones de CO2: carbon emissions, CO2 reduction, carbon-intensity-weighted consumption, avoided emissions, emission-cost trade-off.
- Costos energéticos: electricity cost, cost reduction, demand charge reduction, time-of-use optimization, dynamic pricing response.
- Respuesta de demanda: PAR reduction, peak shaving, load profile flattening, demand shifting.
- Operación segura: voltage violation, thermal violation, constraint violation, safe operation index, reliability proxy.
- MADRL: cumulative reward, average episode reward, convergence speed, actor loss, critic loss, entropy, stability, sample efficiency, robustness, constraint violations.

## Final Quality Checklist

Verify:

1. The structure follows Guide N. 01 section 5.1.
2. The document is a professional/specialization master's thesis plan.
3. Current APA is used.
4. IEEE is not used.
5. `Marco_metodologico_MARL` does not appear.
6. `Marco_metodologico_MADRL` appears where required.
7. CityLearn v3 is presented as `CityLearn v3 propuesto`.
8. MARLlib is used only as a proper name.
9. Chapter numbering is correct.
10. Antecedents come from the bibliographic matrix.
11. Theoretical bases have APA citations.
12. Problems respond to diagnosis.
13. Objectives respond to problems.
14. Methodology is coherent with the objective.
15. Schedule is coherent with intervention stages.
16. Budget and financing are consistent.
17. No citation lacks reference.
18. No reference lacks citation.
19. Variables align with the consistency matrix.
20. KPIs align with flexibility, CO2, and costs.
21. No results are invented.
22. Real antecedents, methodological proposal, and expected results are differentiated.
23. Vertical coherence is preserved: diagnosis -> problem -> objectives -> theoretical framework -> methodology -> schedule -> budget.
24. Horizontal coherence is preserved: variables -> dimensions -> indicators -> techniques -> instruments -> KPIs.

