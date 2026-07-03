# Capítulo 6. Conclusiones



> **Documento de tesis — borrador integral alineado para Perplexity.** Síntesis derivada de los resultados de la corrida canónica Colab/Drive (`madrl_v3_20260627_164047`), la corrida local v4 y la documentación del proyecto. No inventar hallazgos no soportados por artefactos.



---



## ░░ PROMPT PARA PERPLEXITY (versión final) ░░



**Rol / Contexto:** Eres redactor académico de cierre de tesis. Pules el **Capítulo 6 (Conclusiones)** de la tesis UNI sobre MADRL + CityLearn v3 en el SEAI Iquitos (HAPPO/MASAC/MATD3/MAAC; OE.1 flexibilidad, OE.2 CO₂, OE.3 costos).



**Objetivo del prompt:** Versión final académica en español con:

1. Hallazgos principales redactados como respuestas explícitas a OG y a OE.1/OE.2/OE.3.

2. Limitaciones honestas y trabajo pendiente concreto.

3. Plan de culminación con hitos verificables.

4. **Citas APA** solo donde se compare con la literatura; mantener cifras reales.



**Instrucciones específicas:** (a) no sobre-afirmar (cobertura parcial de episodios, semilla única, HAPPO sin KPIs); (b) vincular cada conclusión con su evidencia (score Colab, KPIs físicos); (c) mantener `[Pendiente: ...]` donde falte evidencia.



---



## 6.1 Principales hallazgos



1. **Respuesta al OG:** entre los MADRL evaluables en Colab (MATD3, MAAC, MASAC), el **mejor algoritmo global para la gestión coordinada** de flexibilidad, CO₂ y costos en el SEAI Iquitos es **MATD3** (score global **0.6667**; ranking 1/3 con KPIs auditados; fuente `best_madrl_report.json`, 2026-07-03). HAPPO queda excluido del ranking por fallo de evaluación post-entrenamiento. La significancia estadística en Colab `[Pendiente: celda 9.1]`; la corrida local v4 (5 ep) anticipó la dirección con Kruskal-Wallis **p = 0.0459**.

2. **Respuesta al OE.1 (flexibilidad):** **MATD3** obtiene la mejor flexibilidad compuesta en E1 (1.0009; `peak_average` 1.0081) frente a MAAC (1.0124) y MASAC (1.0286). En la corrida local v4, HAPPO lideraba OE.1 puro; su posición en Colab no puede confirmarse sin re-evaluación.

3. **Respuesta al OE.2 (CO₂):** **MATD3** logra el menor delta de emisiones en E2 (**23 070 kg** vs MAAC 70 654 kg y MASAC 77 649 kg). Ningún algoritmo mejora todos los KPIs de CO₂ vs baseline en E1 (MATD3: 0/5 mejorados en `axis_baseline.csv`).

4. **Respuesta al OE.3 (costos):** **MAAC** obtiene el menor delta de costo en E3 (**9 515 EUR** vs MATD3 44 399 EUR), indicando competitividad off-policy en optimización tarifaria con presupuesto reducido (11 ep).

5. **Viabilidad técnica:** se validó el pipeline completo en hardware local (RTX 4060, 12/12 jobs v4) y se escaló a Colab (RTX PRO 6000 Blackwell, 94 GB VRAM), confirmando los **cuatro aportes originales** al motor de simulación y la reproducibilidad del benchmark.

6. **Especialización por eje:** ningún algoritmo domina simultáneamente los tres ejes; existe un *trade-off* (MATD3 en flex+CO₂, MAAC en costos) que sugiere selección dependiente del objetivo prioritario del operador.



## 6.2 Limitaciones encontradas



- **Cobertura de episodios:** objetivo 50 ep/job; cobertura auditada MATD3 40/50, MAAC 11/50, MASAC 12/50; HAPPO ~49 ep entrenados sin KPIs finales.

- **Semilla única (seed = 0):** sin réplicas no se cuantifica completamente la robustez ni los intervalos de confianza.

- **Evaluación HAPPO:** error `VecEnvWrapper` impide comparación justa del algoritmo on-policy en Colab.

- **Baseline CO₂:** ningún MADRL supera consistentemente al baseline en todos los KPIs de emisiones evaluados.

- **Comparación equiponderada:** el score global min-max no sustituye análisis de Pareto multiobjetivo.

- **Simulación, no despliegue:** sin validación física de red (alcance excluido).



## 6.3 Trabajo pendiente



- **Completar 50 ep** en MATD3, MAAC, MASAC y **re-evaluar HAPPO** (corregir `VecEnvWrapper`).

- **Re-ejecutar celda 9.1** del notebook con artefactos Drive completos: pruebas estadísticas Colab y ranking definitivo.

- Añadir **múltiples semillas** (p. ej. 3-5) para intervalos de confianza y bootstrap.

- Reportar **porcentajes de mejora vs baseline** por KPI y construir la **frontera de Pareto** multiobjetivo.

- Regenerar **KPIs MASAC-E3** (`core_kpis.csv`) y descargar **figuras definitivas** desde Drive.

- Ejecutar **HPO con Optuna** (mejora prevista) para afinar hiperparámetros por algoritmo.

- Insertar **figuras finales** y completar verificación de referencias `[PV]`.



## 6.4 Plan para culminar la tesis



| Hito | Entregable verificable | Estado |

|---|---|---|

| H1. Corrida canónica 50 ep (Colab, `two_phase_happo_masac_v3`) | `madrl_v3_20260627_164047/` en Drive; KPIs integrados en Cap. 5 | **Parcial** (MATD3 40/50; MAAC/MASAC parcial; HAPPO sin eval) |

| H2. Robustez multi-semilla | Resultados con ≥3 seeds + IC | Pendiente |

| H3. Estadística completa Colab | Celda 9.1 → `hipotesis_estadisticas_madrl.csv` | Pendiente |

| H4. Pareto y % mejora | Tablas/figuras OE1/OE2/OE3 vs baseline | Pendiente |

| H5. HPO Optuna | Estudio Optuna por algoritmo | Pendiente |

| H6. Redacción final | Capítulos 1-6 pulidos en Perplexity + referencias APA | En curso |

| H7. Sustentación | Documento + defensa (9 diagramas de arquitectura) | Pendiente |



## 6.5 Cierre



Los resultados de la corrida canónica Colab **respaldan la hipótesis general** en la medida evaluable: **MATD3** emerge como el MADRL con mejor desempeño coordinado (flexibilidad + CO₂) entre los algoritmos con KPIs auditados, con **MAAC** especializado en costos. La contribución metodológica —benchmark unificado de cuatro algoritmos bajo Dec-POMDP/CTDE, dataset real de 17 edificios y cuatro aportes al motor— constituye un marco reproducible para sistemas eléctricos aislados amazónicos. La consolidación final depende de completar 50 ep, re-evaluar HAPPO, la batería estadística Colab y el análisis multi-semilla/Pareto.



---



### Estado del capítulo

**Actualizado con resultados Colab/Drive (parcial).** Pendientes: confirmar hallazgos con 50 ep completos y HAPPO; estadística Colab; cuantificar % de mejora; cerrar matriz estadística.


