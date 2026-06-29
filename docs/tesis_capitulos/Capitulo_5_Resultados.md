# Capítulo 5. Resultados

> **Documento de tesis — borrador integral alineado para Perplexity.** Cifras tomadas directamente de artefactos reales: `outputs/citylearn_v3_madrl_full_20260615_074011_v4/` (`official_full_status.json`, `resumen_comparativo/best_madrl_report.json`, `matd3/E3_seed_0/data/training_summary.json`), `outputs/_archive/comparison_citylearn_v2_vs_v3_madrl/{E1,E2,E3}/comparison_summary.json` y `docs/architecture/ARQUITECTURA_PROYECTO_DEFENSA.md`. Donde una cifra no existe como dato auditado se marca `[Pendiente: ...]`. **No inventar resultados.**

---

## ░░ PROMPT PARA PERPLEXITY (versión final) ░░

**Rol / Contexto:** Eres analista de resultados experimentales en MADRL. Pules el **Capítulo 5 (Resultados)** —el de mayor peso— de la tesis UNI sobre MADRL + CityLearn v3 en el SEAI Iquitos (HAPPO/MASAC/MATD3/MAAC).

**Objetivo del prompt:** Versión final académica en español con:
1. Presentación clara de experimentos, métricas, resultados, comparación con baseline, tablas, figuras y discusión.
2. **Citas APA** consistentes con `Referencias_APA.md` al comparar con la literatura.
3. Interpretación honesta: distinguir resultados de la corrida completada v4 (5 episodios) de la configuración canónica objetivo (50 episodios), y señalar el carácter **preliminar** de las cifras.
4. No alterar p-valores ni scores; completar `[Pendiente: ...]` solo con datos del proyecto.

**Instrucciones específicas:** (a) verbalizar cada tabla; (b) referenciar las figuras PNG por su nombre de archivo; (c) discutir por qué MATD3 resulta el mejor global; (d) advertir las limitaciones (semilla única, baseline que en E1 supera por el peso de OE2/OE3 equiponderados).

---

> **⚠ AVISO — RESULTADOS PRELIMINARES.** Todos los números de resultados mostrados en este capítulo son **PRELIMINARES** y provienen exclusivamente de la corrida local de **5 episodios** (`citylearn_v3_madrl_full_20260615_074011_v4`). La **corrida canónica de 50 episodios** se está ejecutando actualmente en Google Colab. **Estos valores se actualizarán** cuando finalice ese entrenamiento, reemplazando los resultados preliminares de 5 episodios por los de 50 episodios, recalculando KPIs normalizados, pruebas estadísticas y % de mejora vs baseline, e insertando las figuras `.png` definitivas.

## 5.1 Experimentos realizados

Se ejecutaron las **12 corridas oficiales** (4 algoritmos × 3 escenarios, seed 0) de la corrida definitiva **v4** (`citylearn_v3_madrl_full_20260615_074011_v4`). Estado: **completada, 12/12 jobs con `exit_code = 0`** (inicio 2026-06-15 07:40, fin 2026-06-16 22:44; ~39 h de pared en RTX 4060 Laptop 8 GB). Cada corrida: 5 episodios × 8 760 pasos = **43 800 pasos**, perfil de recompensa `*_unified_comparable_v4`, `gamma = 0.9999`.

**Duración por job (min) — PRELIMINAR (corrida local, 5 episodios):**

| Algoritmo | E1 | E2 | E3 |
|---|---:|---:|---:|
| HAPPO | 66.5 | 66.15 | 57.75 |
| MASAC | 125.88 | 148.33 | 135.72 |
| MATD3 | 375.56 | 377.49 | 451.12 |
| MAAC | 331.79 | 328.82 | 322.9 |

> `[REEMPLAZAR con resultados de la corrida canónica de 50 episodios en Colab]`

> HAPPO (on-policy) es el más rápido; MATD3 y MAAC (off-policy con réplay y críticos pesados) son los más costosos.

## 5.2 Métricas utilizadas

- **OE.1 Flexibilidad:** `peak_average`, `ramping_average`, `one_minus_load_factor_average`, `grid_import/export` (control vs baseline y delta), `zero_net_energy`.
- **OE.2 CO₂:** `carbon_emissions` (control/baseline/delta), promedios diarios.
- **OE.3 Costos:** `electricity_cost` (control/baseline/delta), `cost_peak_average`, `price_signal_deviation`.

Los KPIs se calculan con `env.evaluate_v2()` y se normalizan contra la línea base CityLearn v2 (`baseline`, `hour_rbc`); valores < 1.0 indican mejora respecto al baseline.

## 5.3 Resultados obtenidos — Selección del mejor MADRL *(PRELIMINAR — corrida local, 5 episodios)*

El reporte `best_madrl_report.json` (generado 2026-06-20, evaluación agregada sobre E1/E2/E3, corrida local preliminar de 5 episodios) determina:

| Rango | Algoritmo | Score medio | Seleccionado |
|:---:|---|:---:|:---:|
| **1** | **MATD3** | **0.7445** | **Sí** |
| 2 | MASAC | 0.73 | No |
| 3 | MAAC | 0.72 | No |
| 4 | HAPPO | 0.70 | No |

> `[REEMPLAZAR con resultados de la corrida canónica de 50 episodios en Colab]`

**Línea de selección obligatoria:** *"Mejor algoritmo MADRL seleccionado: MATD3"*.

Criterios de selección: reward promedio, reducción de picos, gestión SOC/BESS, reducción de CO₂, cumplimiento de restricciones y robustez.

### 5.3.1 Score por escenario (corrida v4 — PRELIMINAR, 5 episodios)

| Algoritmo | OE.1 (E1) | OE.2 (E2) | OE.3 (E3) | Score global | Rango |
|---|:---:|:---:|:---:|:---:|:---:|
| **MATD3** | **0.7486** | **0.7515** | **0.7333** | **0.7445** | **1** |
| MASAC | 0.74 | 0.74 | 0.72 | ~0.73 | 2 |
| MAAC | 0.72 | 0.72 | 0.73 | ~0.72 | 3 |
| HAPPO | 0.70 | 0.70 | 0.70 | ~0.70 | 4 |

> `[REEMPLAZAR con resultados de la corrida canónica de 50 episodios en Colab]`

Fuente: `ARQUITECTURA_PROYECTO_DEFENSA.md` (Tabla de resultados v4). `[Pendiente: extraer los scores exactos de MASAC/MAAC/HAPPO por escenario desde scores_kpi_algoritmo_madrl.csv para reemplazar las aproximaciones ~.]`

### 5.3.2 KPIs físicos de la mejor corrida (MATD3 · E3, `training_summary.json`) — PRELIMINAR, 5 episodios

| KPI (normalizado vs baseline) | Valor |
|---|---:|
| `carbon_emissions` | 1.0847 |
| `electricity_cost` | 1.0092 |
| `ramping_average` | 1.0009 |
| `ev_departure_success_rate` | 0.4749 |
| `pv_generation_total` (kWh) | 49 538 029.87 |
| `pv_export_total` (kWh) | 41 400 814.56 |
| `grid_import_control` (kWh) | 11 237 105.75 |
| `grid_import_baseline` (kWh) | 11 149 381.98 |

> `[REEMPLAZAR con resultados de la corrida canónica de 50 episodios en Colab]`

> Estas cifras corresponden a 5 episodios de entrenamiento (no a una política plenamente convergida). Reward medio por episodio MATD3-E3 ≈ −0.53 a −0.56. La tasa de éxito de salida EV (~0.47) indica margen de mejora en la gestión de urgencia SOC, consistente con el presupuesto reducido de pasos. `[Pendiente: reportar KPIs OE.1/OE.2/OE.3 normalizados (<1 = mejora) por algoritmo y escenario una vez completada la corrida canónica de 50 episodios.]`

## 5.4 Comparación con baseline y trabajos relacionados *(PRELIMINAR — corrida local, 5 episodios)*

El comparador `compare_citylearn_v2_vs_v3_madrl.py` (pesos OE1/OE2/OE3 = 0.34/0.33/0.33) produjo:

| Escenario | Mejor global | Mejor OE.1 | Mejor OE.2 | Mejor OE.3 |
|---|---|---|---|---|
| **E1** | baseline v2 (0.7254) | HAPPO v3 (0.5679) | baseline v2 (≈1.0000) | hour_rbc v2 (0.7474) |
| **E2** | **MATD3 v3 (0.7515)** | HAPPO v3 (0.6769) | **MATD3 v3 (0.9858)** | MATD3 v3 (0.8401) |
| **E3** | **MATD3 v3 (0.7333)** | HAPPO v3 (0.6806) | **MATD3 v3 (0.9811)** | MAAC v3 (0.7879) |

> `[REEMPLAZAR con resultados de la corrida canónica de 50 episodios en Colab]`

**Lectura:** en los escenarios E2 (CO₂) y E3 (costos), un agente MADRL (MATD3) es el mejor global, superando a las líneas base. En E1, con la ponderación equiponderada del comparador, el `baseline` v2 puntúa alto porque domina la dimensión OE.2 (su score OE.2 ≈ 1.0); sin embargo, en el eje de flexibilidad puro (OE.1) el mejor es **HAPPO**. Esto sugiere una especialización por eje y motiva el análisis multiobjetivo del Capítulo 6.

Comparación con la literatura: las mejoras reportadas por trabajos análogos (Yao et al., 2023: ~15 % pico / ~18 % costo; Liu et al., 2022: ~15 % CO₂ / ~20 % costo; Xie et al., 2023: ~25 % en coordinación con atención) sirven de marco de contraste; la cuantificación porcentual definitiva de esta tesis frente a baseline se consolidará con la corrida canónica. `[Pendiente: porcentajes de mejora MADRL vs baseline por KPI.]`

## 5.5 Pruebas estadísticas *(PRELIMINAR — corrida local, 5 episodios)*

| Prueba | Resultado | p-valor | Conclusión |
|---|---|:---:|---|
| Shapiro-Wilk | Algunos grupos no normales | — | Justifica tests no paramétricos |
| Kruskal-Wallis (4 algoritmos) | Diferencia global | **0.0459** | Significativo (α = 0.05) |
| Mann-Whitney U: MATD3 vs HAPPO | MATD3 superior | **0.0182** | Significativo |
| Wilcoxon SR: MATD3 vs HAPPO | Diferencia sistemática | **2.62×10⁻⁶** | Muy significativo |

> `[REEMPLAZAR con resultados de la corrida canónica de 50 episodios en Colab]`

Artefactos: `outputs/thesis_objective_evidence/{analisis_estadistico_madrl.csv, comparaciones_mwu_madrl.csv, comparaciones_wilcoxon_madrl.csv, hipotesis_estadisticas_madrl.csv, scores_kpi_algoritmo_madrl.csv}`. Para la corrida canónica, esta batería se reproduce en el notebook `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb`, que consolida los `results.json` de las 12 corridas en un *DataFrame* de KPIs (celda 8.1) y ejecuta la suite estadística —Kruskal-Wallis, Mann-Whitney U y ranking global— en la celda 9.1. `[Pendiente: completar comparaciones MWU/Wilcoxon para los pares restantes (MATD3 vs MASAC, MATD3 vs MAAC) y sus tamaños de efecto Cliff's δ / Hedges g.]`

## 5.6 Figuras

Cada corrida genera 13 figuras PNG (manifiesto `figures/figures_manifest.json`):

- `reward_timeseries.png`, `convergence_returns.png`, `episode_reward_summary.png`, `learning_efficiency.png` — dinámica de entrenamiento.
- `citylearn_v2_district_timeseries.png` — carga neta del distrito.
- `axis_baseline_comparison.png`, `baseline_gain_by_kpi.png` — ganancia vs baseline.
- `core_kpis.png`, `OE1_flexibility_kpis.png`, `OE2_co2_kpis.png`, `OE3_cost_kpis.png` — KPIs por eje.
- `exploration_action_l2.png`, `agent_reward_contribution.png` — exploración y contribución por agente.

Comparación v2 vs v3: `outputs/comparison_citylearn_v2_vs_v3_madrl/{E1,E2,E3}/{OE1,OE2,OE3}_comparison.png` y `baseline_gain_heatmap.png`.

`[Pendiente: insertar en la versión final las figuras seleccionadas (p. ej. baseline_gain_by_kpi de MATD3-E2/E3) como evidencia visual una vez completada la corrida canónica de 50 episodios en Colab.]`

## 5.7 Discusión de resultados

1. **MATD3 es el mejor MADRL global** (score 0.7445; KW p = 0.0459). Su doble crítico (anti-sobreestimación) y la política determinística parecen favorecer la estabilidad en el horizonte largo (8 760 pasos), pese a ser el más costoso computacionalmente.
2. **Especialización por eje:** HAPPO destaca en flexibilidad pura (OE.1) en los tres escenarios del comparador, mientras MATD3 domina CO₂ (OE.2) y costos (OE.3). Esto es coherente con la naturaleza on-policy/heterogénea de HAPPO para coordinación de picos y con la eficiencia de muestreo off-policy de MATD3 para optimización fina.
3. **Frente al baseline v2:** los agentes MADRL superan al baseline en E2 y E3; en E1 el baseline puntúa alto por la ponderación equiponderada del comparador (dominada por OE.2). La interpretación correcta exige análisis por eje y, preferiblemente, frontera de Pareto.
4. **Carácter preliminar:** las cifras provienen de 5 episodios por job (presupuesto de 8 GB VRAM). La configuración canónica (50 episodios = 438 000 pasos), actualmente en ejecución en Colab bajo el protocolo `two_phase_happo_masac_v3` (GPU objetivo H100 primaria / A100-80GB compatible, ~20 h de pared), y múltiples semillas robustecerán las conclusiones. Sus artefactos (`results.json`, `training_summary.json`, `timeseries.csv`, figuras) persisten en Google Drive (`MyDrive/MADRLCitytleranflexresdr/outputs/madrl_v3_<timestamp>/`) y se cargarán con las celdas 8.1/9.1 del notebook. Al finalizar, se reemplazarán todos los resultados preliminares de este capítulo.

---

### Estado del capítulo
**Resultados PRELIMINARES (corrida local, 5 episodios).** Pendientes: reemplazar todas las cifras con resultados de la corrida canónica de 50 episodios en Colab (en curso); scores exactos por algoritmo/escenario de MASAC/MAAC/HAPPO; KPIs OE normalizados por algoritmo; porcentajes de mejora vs baseline; MWU/Wilcoxon de pares restantes; inserción de figuras definitivas.
