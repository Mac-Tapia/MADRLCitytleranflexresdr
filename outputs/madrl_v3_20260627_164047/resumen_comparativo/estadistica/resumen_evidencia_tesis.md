# Paquete de evidencia para plan e informe de tesis

Generado: 2026-07-15T01:56:09.599906+00:00

## Estado por objetivo especifico

### OE1 - Flexibilidad energetica

- Escenario: `E1`
- Estado de datos: `evidencia_parcial`
- Estado de cumplimiento: `cumplimiento_parcial_por_consolidar`
- Algoritmos con KPIs: MAAC, MASAC, MATD3
- KPIs medidos/esperados: 36/36
- KPIs mejorados/no mejorados: 12/24
- Mejor algoritmo por mediana estadistica: MAAC
- Kruskal-Wallis p-value: 0.2806252392803863

OE1 (Flexibilidad energetica) cuenta con evidencia en MAAC, MASAC, MATD3; estado de datos: evidencia_parcial; estado de cumplimiento: cumplimiento_parcial_por_consolidar; KPIs mejorados: 12; KPIs no mejorados: 24. La interpretacion final debe usar estos registros y no inferir resultados no observados.

Shapiro-Wilk rechaza normalidad en al menos un grupo (tests no parametricos justificados). Kruskal-Wallis no detecta diferencias globales significativas en OE1 con alpha=0.05; el ranking KPI observado se conserva como evidencia descriptiva, con MAAC por mediana de ganancia relativa.

### OE2 - Emisiones de CO2

- Escenario: `E2`
- Estado de datos: `evidencia_parcial`
- Estado de cumplimiento: `pendiente_de_consolidacion`
- Algoritmos con KPIs: MAAC, MASAC, MATD3
- KPIs medidos/esperados: 7/7
- KPIs mejorados/no mejorados: 0/15
- Mejor algoritmo por mediana estadistica: MATD3
- Kruskal-Wallis p-value: 0.5457384930783267

OE2 (Emisiones de CO2) cuenta con evidencia en MAAC, MASAC, MATD3; estado de datos: evidencia_parcial; estado de cumplimiento: pendiente_de_consolidacion; KPIs mejorados: 0; KPIs no mejorados: 15. La interpretacion final debe usar estos registros y no inferir resultados no observados.

Shapiro-Wilk rechaza normalidad en al menos un grupo (tests no parametricos justificados). Kruskal-Wallis no detecta diferencias globales significativas en OE2 con alpha=0.05; el ranking KPI observado se conserva como evidencia descriptiva, con MATD3 por mediana de ganancia relativa.

### OE3 - Costos energeticos

- Escenario: `E3`
- Estado de datos: `evidencia_parcial`
- Estado de cumplimiento: `cumplimiento_parcial_por_consolidar`
- Algoritmos con KPIs: MAAC, MASAC, MATD3
- KPIs medidos/esperados: 11/11
- KPIs mejorados/no mejorados: 3/24
- Mejor algoritmo por mediana estadistica: MAAC
- Kruskal-Wallis p-value: 0.38805922498915935

OE3 (Costos energeticos) cuenta con evidencia en MAAC, MASAC, MATD3; estado de datos: evidencia_parcial; estado de cumplimiento: cumplimiento_parcial_por_consolidar; KPIs mejorados: 3; KPIs no mejorados: 24. La interpretacion final debe usar estos registros y no inferir resultados no observados.

Shapiro-Wilk rechaza normalidad en al menos un grupo (tests no parametricos justificados). Kruskal-Wallis no detecta diferencias globales significativas en OE3 con alpha=0.05; el ranking KPI observado se conserva como evidencia descriptiva, con MAAC por mediana de ganancia relativa.

## Analisis estadistico MADRL

Los contrastes se calculan sobre `signed_relative_gain` por KPI comparable; valores positivos favorecen al algoritmo frente al baseline.

- `OE1`: Kruskal p=0.2806252392803863; Brown-Forsythe p=0.9960692110094191; mejor mediana=MAAC.
- `OE2`: Kruskal p=0.5457384930783267; Brown-Forsythe p=0.9992486548707163; mejor mediana=MATD3.
- `OE3`: Kruskal p=0.38805922498915935; Brown-Forsythe p=0.9946030910655771; mejor mediana=MAAC.
- `ALL`: Kruskal p=0.15543186080628366; Brown-Forsythe p=0.994940013807857; mejor mediana=MATD3.

Estos p-values son apoyo exploratorio cuando solo existe una semilla por algoritmo; la evidencia primaria sigue siendo la matriz KPI/baseline.

## Productos para skills locales

Archivos CSV y MD generados con nombres alineados a los workbooks de `madrl-citylearn-thesis-plan` y `madrl-citylearn-thesis-integrated`:

- `Aplicabilidad_SEAI_Iquitos.csv` / `Aplicabilidad_SEAI_Iquitos.md`
- `Arquitectura_Propuesta.csv` / `Arquitectura_Propuesta.md`
- `Backends_MADRL.csv` / `Backends_MADRL.md`
- `CityLearn_CO2_Costos.csv` / `CityLearn_CO2_Costos.md`
- `CityLearn_v3_Propuesto.csv` / `CityLearn_v3_Propuesto.md`
- `Datasets_y_codigo.csv` / `Datasets_y_codigo.md`
- `KPIs_y_metricas.csv` / `KPIs_y_metricas.md`
- `MARLlib_Integracion.csv` / `MARLlib_Integracion.md`
- `Marco_metodologico_MADRL.csv` / `Marco_metodologico_MADRL.md`
- `Matriz_KPIs.csv` / `Matriz_KPIs.md`
- `Resumen_ejecutivo.csv` / `Resumen_ejecutivo.md`
- `analisis_estadistico_madrl.csv` / `analisis_estadistico_madrl.md`
- `comparaciones_mwu_madrl.csv` / `comparaciones_mwu_madrl.md`
- `comparaciones_wilcoxon_madrl.csv` / `comparaciones_wilcoxon_madrl.md`
- `comparativa_distrito_por_agente.csv` / `comparativa_distrito_por_agente.md`
- `comparativa_edificios_por_agente.csv` / `comparativa_edificios_por_agente.md`
- `hipotesis_estadisticas_madrl.csv` / `hipotesis_estadisticas_madrl.md`
- `kpis_por_edificio_y_agente.csv` / `kpis_por_edificio_y_agente.md`
- `matriz_baseline_por_eje.csv` / `matriz_baseline_por_eje.md`
- `matriz_consistencia_objetivos.csv` / `matriz_consistencia_objetivos.md`
- `matriz_kpis_tesis.csv` / `matriz_kpis_tesis.md`
- `matriz_operacionalizacion_variables.csv` / `matriz_operacionalizacion_variables.md`
- `matriz_resultados_madrl.csv` / `matriz_resultados_madrl.md`
- `objetivos_especificos_cumplimiento.csv` / `objetivos_especificos_cumplimiento.md`
- `run_artifact_inventory.csv` / `run_artifact_inventory.md`
- `scores_kpi_algoritmo_madrl.csv` / `scores_kpi_algoritmo_madrl.md`

## Inventario de corridas

- Corridas detectadas: 12
- Si existe `official_full_status.json`, los artefactos se cuentan como evidencia cuantitativa solo cuando el job del launcher figura con `exit_code=0`.
- Este paquete marca resultados pendientes cuando faltan `objective_kpis.csv`, tablas, figuras o entrenamientos completos.
- No debe usarse para afirmar resultados cuantitativos que no figuren en las matrices generadas.
