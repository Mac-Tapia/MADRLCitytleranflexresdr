# Capítulo 6. Conclusiones Preliminares

> **Documento de tesis — borrador integral alineado para Perplexity.** Síntesis derivada de los resultados reales de la corrida v4 y de la documentación del proyecto. No inventar hallazgos no soportados por artefactos.

---

## ░░ PROMPT PARA PERPLEXITY (versión final) ░░

**Rol / Contexto:** Eres redactor académico de cierre de tesis. Pules el **Capítulo 6 (Conclusiones preliminares)** de la tesis UNI sobre MADRL + CityLearn v3 en el SEAI Iquitos (HAPPO/MASAC/MATD3/MAAC; OE.1 flexibilidad, OE.2 CO₂, OE.3 costos).

**Objetivo del prompt:** Versión final académica en español con:
1. Hallazgos principales redactados como respuestas explícitas a OG y a OE.1/OE.2/OE.3.
2. Limitaciones honestas y trabajo pendiente concreto.
3. Plan de culminación con hitos verificables.
4. **Citas APA** solo donde se compare con la literatura; mantener cifras reales.

**Instrucciones específicas:** (a) no sobre-afirmar (resultados preliminares, semilla única); (b) vincular cada conclusión con su evidencia (score, p-valor); (c) mantener `[Pendiente: ...]` donde falte evidencia.

---

## 6.1 Principales hallazgos

1. **Respuesta al OG:** entre HAPPO, MASAC, MATD3 y MAAC, el **mejor MADRL global para la gestión coordinada** de flexibilidad, CO₂ y costos en el SEAI Iquitos es **MATD3** (score medio 0.7445; ranking 1/4). La diferencia entre algoritmos es **estadísticamente significativa** (Kruskal-Wallis p = 0.0459, α = 0.05), y MATD3 supera a HAPPO de forma significativa (Mann-Whitney U p = 0.0182; Wilcoxon p = 2.62×10⁻⁶).
2. **Respuesta al OE.1 (flexibilidad):** en el eje de flexibilidad puro, **HAPPO** obtiene el mejor score OE.1 en los tres escenarios del comparador (E1 0.5679, E2 0.6769, E3 0.6806), coherente con su diseño on-policy para agentes heterogéneos (Kuba et al., 2021).
3. **Respuesta al OE.2 (CO₂):** **MATD3** logra el mejor desempeño de emisiones (OE.2 ≈ 0.9858 en E2 y 0.9811 en E3), superando a las líneas base CityLearn v2.
4. **Respuesta al OE.3 (costos):** **MATD3** domina el score global en E3 (0.7333) y MAAC obtiene el mejor OE.3 puro en E3 (0.7879), indicando competitividad de los esquemas off-policy en optimización tarifaria.
5. **Viabilidad técnica:** se completó una corrida íntegra de **12/12 jobs** en hardware modesto (RTX 4060 8 GB), validando el pipeline dataset → entrenamiento → comparación → evidencia y los **cuatro aportes originales** al motor de simulación.
6. **Especialización por eje:** ningún algoritmo domina simultáneamente los tres ejes con el mismo margen; existe un *trade-off* que sugiere selección dependiente del objetivo prioritario del operador.

## 6.2 Limitaciones encontradas

- **Presupuesto de cómputo:** la corrida reportada usa 5 episodios × 8 760 pasos (43 800 pasos) por job, por debajo de la configuración canónica de 75 episodios (657 000 pasos). Las políticas no están plenamente convergidas (reward medio MATD3-E3 ≈ −0.53).
- **Semilla única (seed = 0):** sin réplicas no se cuantifica completamente la robustez ni los intervalos de confianza.
- **KPIs de servicio EV:** `ev_departure_success_rate ≈ 0.47` (MATD3-E3) indica margen de mejora en la gestión de urgencia SOC.
- **Comparación equiponderada:** el comparador usa pesos OE 0.34/0.33/0.33, lo que en E1 favorece al baseline por dominancia de OE.2; se requiere análisis de Pareto.
- **Simulación, no despliegue:** sin validación física de red (alcance excluido).

## 6.3 Trabajo pendiente

- Ejecutar la **corrida canónica de 75 episodios** (657 000 pasos) en Colab A100 con `hidden_size=384`, `gamma=0.99`.
- Añadir **múltiples semillas** (p. ej. 3-5) para intervalos de confianza y bootstrap.
- Completar la **matriz estadística** (MWU/Wilcoxon de todos los pares + tamaños de efecto Cliff's δ / Hedges g).
- Reportar **porcentajes de mejora vs baseline** por KPI y construir la **frontera de Pareto** multiobjetivo.
- Ejecutar **HPO con Optuna** (mejora prevista) para afinar hiperparámetros por algoritmo.
- Mejorar la **gestión de urgencia EV** (tasa de éxito de salida).
- Insertar **figuras finales** y completar verificación de referencias `[PV]`.

## 6.4 Plan para culminar la tesis

| Hito | Entregable verificable | Estado |
|---|---|---|
| H1. Corrida canónica 75 ep | `outputs/<run>/official_full_status.json` con 12/12 exit_code 0 | Pendiente |
| H2. Robustez multi-semilla | Resultados con ≥3 seeds + IC | Pendiente |
| H3. Estadística completa | `hipotesis_estadisticas_madrl.csv` con todos los pares | Parcial |
| H4. Pareto y % mejora | Tablas/figuras OE1/OE2/OE3 vs baseline | Pendiente |
| H5. HPO Optuna | Estudio Optuna por algoritmo | Pendiente |
| H6. Redacción final | Capítulos 1-6 pulidos en Perplexity + referencias APA | En curso |
| H7. Sustentación | Documento + defensa (9 diagramas de arquitectura) | Pendiente |

## 6.5 Cierre

Los resultados preliminares **respaldan la hipótesis general**: existe un MADRL (MATD3) con desempeño coordinado significativamente superior en el SEAI Iquitos, con HAPPO especializado en flexibilidad. La contribución metodológica —benchmark unificado de cuatro algoritmos bajo Dec-POMDP/CTDE, dataset real de 17 edificios y cuatro aportes al motor— constituye un marco reproducible para sistemas eléctricos aislados amazónicos. La consolidación final depende de la corrida canónica y del análisis multi-semilla/Pareto.

---

### Estado del capítulo
**Completo con placeholders de cierre.** Pendientes: confirmar hallazgos con corrida canónica y multi-semilla; cuantificar % de mejora; cerrar matriz estadística.
