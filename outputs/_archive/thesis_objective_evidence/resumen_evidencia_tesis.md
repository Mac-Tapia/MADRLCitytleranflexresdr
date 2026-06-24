# Paquete de evidencia para plan e informe de tesis

Generado: 2026-06-19T02:42:32.187328+00:00

## Estado por objetivo especifico

### OE1 - Flexibilidad energetica

- Escenario: `E1`
- Estado de datos: `evidencia_completa`
- Estado de cumplimiento: `cumplimiento_cuantitativo_parcial`
- Algoritmos con KPIs: HAPPO, MAAC, MASAC, MATD3
- KPIs medidos/esperados: 36/36
- KPIs mejorados/no mejorados: 17/31
- Mejor algoritmo por mediana estadistica: MATD3
- Kruskal-Wallis p-value: 0.44502280648226444

OE1 (Flexibilidad energetica) cuenta con evidencia en HAPPO, MAAC, MASAC, MATD3; estado de datos: evidencia_completa; estado de cumplimiento: cumplimiento_cuantitativo_parcial; KPIs mejorados: 17; KPIs no mejorados: 31. La interpretacion final debe usar estos registros y no inferir resultados no observados.

Shapiro-Wilk rechaza normalidad en al menos un grupo (tests no parametricos justificados). Kruskal-Wallis no detecta diferencias globales significativas en OE1 con alpha=0.05; el ranking KPI observado se conserva como evidencia descriptiva, con MATD3 por mediana de ganancia relativa.

### OE2 - Emisiones de CO2

- Escenario: `E2`
- Estado de datos: `evidencia_completa`
- Estado de cumplimiento: `no_demostrado_cuantitativamente`
- Algoritmos con KPIs: HAPPO, MAAC, MASAC, MATD3
- KPIs medidos/esperados: 7/7
- KPIs mejorados/no mejorados: 0/20
- Mejor algoritmo por mediana estadistica: MASAC
- Kruskal-Wallis p-value: 0.16548222241774788

OE2 (Emisiones de CO2) cuenta con evidencia en HAPPO, MAAC, MASAC, MATD3; estado de datos: evidencia_completa; estado de cumplimiento: no_demostrado_cuantitativamente; KPIs mejorados: 0; KPIs no mejorados: 20. La interpretacion final debe usar estos registros y no inferir resultados no observados.

Shapiro-Wilk rechaza normalidad en al menos un grupo (tests no parametricos justificados). Kruskal-Wallis no detecta diferencias globales significativas en OE2 con alpha=0.05; el ranking KPI observado se conserva como evidencia descriptiva, con MASAC por mediana de ganancia relativa.

### OE3 - Costos energeticos

- Escenario: `E3`
- Estado de datos: `evidencia_completa`
- Estado de cumplimiento: `cumplimiento_cuantitativo_parcial`
- Algoritmos con KPIs: HAPPO, MAAC, MASAC, MATD3
- KPIs medidos/esperados: 11/11
- KPIs mejorados/no mejorados: 5/31
- Mejor algoritmo por mediana estadistica: MAAC
- Kruskal-Wallis p-value: 0.077439838275489

OE3 (Costos energeticos) cuenta con evidencia en HAPPO, MAAC, MASAC, MATD3; estado de datos: evidencia_completa; estado de cumplimiento: cumplimiento_cuantitativo_parcial; KPIs mejorados: 5; KPIs no mejorados: 31. La interpretacion final debe usar estos registros y no inferir resultados no observados.

Shapiro-Wilk rechaza normalidad en al menos un grupo (tests no parametricos justificados). Kruskal-Wallis no detecta diferencias globales significativas en OE3 con alpha=0.05; el ranking KPI observado se conserva como evidencia descriptiva, con MAAC por mediana de ganancia relativa.

## Analisis estadistico MADRL

Los contrastes se calculan sobre `signed_relative_gain` por KPI comparable; valores positivos favorecen al algoritmo frente al baseline.

- `OE1`: Kruskal p=0.44502280648226444; Brown-Forsythe p=0.9367736445140052; mejor mediana=MATD3.
- `OE2`: Kruskal p=0.16548222241774788; Brown-Forsythe p=0.9837805943692469; mejor mediana=MASAC.
- `OE3`: Kruskal p=0.077439838275489; Brown-Forsythe p=0.9968693911633538; mejor mediana=MAAC.
- `ALL`: Kruskal p=0.045893880817859695; Brown-Forsythe p=0.9055669270335699; mejor mediana=MATD3.

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
