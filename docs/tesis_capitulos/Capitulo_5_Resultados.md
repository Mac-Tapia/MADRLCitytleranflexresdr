# Capítulo 5. Resultados

> **Documento de tesis — borrador integral alineado para Perplexity.** Cifras tomadas directamente de artefactos reales: corrida canónica Colab/Drive `outputs/madrl_v3_20260627_164047/` (`resumen_comparativo/best_madrl_report.json`, KPIs en `outputs/_drive_madrl/kpis/`), corrida local de validación `outputs/citylearn_v3_madrl_full_20260615_074011_v4/` y `docs/architecture/ARQUITECTURA_PROYECTO_DEFENSA.md`. Donde una cifra no existe como dato auditado se marca `[Pendiente: ...]`. **No inventar resultados.**

---

## ░░ PROMPT PARA PERPLEXITY (versión final) ░░

**Rol / Contexto:** Eres analista de resultados experimentales en MADRL. Pules el **Capítulo 5 (Resultados)** —el de mayor peso— de la tesis UNI sobre MADRL + CityLearn v3 en el SEAI Iquitos (HAPPO/MASAC/MATD3/MAAC).

**Objetivo del prompt:** Versión final académica en español con:
1. Presentación clara de experimentos, métricas, resultados, comparación con baseline, tablas, figuras y discusión.
2. **Citas APA** consistentes con `Referencias_APA.md` al comparar con la literatura.
3. Interpretación honesta: distinguir la corrida canónica Colab (objetivo 50 ep) de la corrida local v4 (5 ep, validación de pipeline) y señalar cobertura parcial de episodios y exclusiones (HAPPO sin KPIs finales).
4. No alterar p-valores ni scores; completar `[Pendiente: ...]` solo con datos del proyecto.

**Instrucciones específicas:** (a) verbalizar cada tabla; (b) referenciar las figuras PNG por su nombre de archivo; (c) discutir por qué MATD3 resulta el mejor global en Colab; (d) advertir las limitaciones (semilla única, episodios incompletos en MAAC/MASAC, HAPPO sin evaluación final, pruebas estadísticas Colab pendientes).

---

> **AVISO — COBERTURA DE LA CORRIDA CANÓNICA (Colab/Drive).** Los resultados principales de este capítulo provienen de la corrida `madrl_v3_20260627_164047` ejecutada en Google Colab (GPU **NVIDIA RTX PRO 6000 Blackwell Server Edition**), con protocolo `two_phase_happo_masac_v3` y objetivo de **50 episodios** por job. La cobertura real auditada en artefactos descargados de Drive es: **MATD3 40/50** (KPIs completos E1–E3), **MAAC 11/50**, **MASAC 12/50**, **HAPPO 49/50 entrenados pero sin KPIs finales** (error `VecEnvWrapper` en evaluación post-entrenamiento). El ranking global y las tablas de KPIs incluyen solo algoritmos con `core_kpis.csv` auditado (MATD3, MAAC, MASAC). La corrida local v4 (5 ep, RTX 4060) se conserva como referencia de validación del pipeline.

## 5.1 Experimentos realizados

### 5.1.1 Corrida canónica Colab/Drive (`madrl_v3_20260627_164047`)

Se ejecutaron las **12 corridas oficiales** (4 algoritmos × 3 escenarios, seed 0) en Google Colab Pro+ bajo el protocolo `two_phase_happo_masac_v3`. Cada job objetivo: **50 episodios × 8 760 pasos = 438 000 pasos**, perfil de recompensa `*_unified_comparable_v4`, `gamma = 0.9999`, `hidden_size` 512 (HAPPO) / 768 (MATD3, MAAC, MASAC).

**Cobertura de episodios y KPIs auditados (artefactos Drive descargados):**

| Algoritmo | E1 (ep / KPIs) | E2 (ep / KPIs) | E3 (ep / KPIs) | Estado evaluación |
|---|---|---|---|---|
| **MATD3** | 40 / Sí | 40 / Sí | 40 / Sí | KPIs completos |
| **MAAC** | 11 / Sí | 11 / Sí | 11 / Sí | KPIs parciales (convergencia incompleta) |
| **MASAC** | 12 / Sí | 12 / Sí | 12 / No* | E3 sin `core_kpis.csv` (solo `results.json`) |
| **HAPPO** | — / No | — / No | — / No | Entrenamiento ~49 ep; evaluación fallida (`VecEnvWrapper`) |

\* MASAC-E3: `results.json` reporta 12 episodios; KPIs normalizados E3 `[Pendiente: regenerar core_kpis.csv tras re-evaluación.]`.

Fuente Drive: [carpeta compartida](https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX). KPIs locales: `outputs/_drive_madrl/kpis/`. Resumen agregado: `outputs/madrl_v3_20260627_164047/resumen_comparativo/`.

### 5.1.2 Corrida local de validación v4 (`citylearn_v3_madrl_full_20260615_074011_v4`)

Corrida previa de **5 episodios** (43 800 pasos/job) en RTX 4060 Laptop 8 GB: **12/12 jobs completados** (~39 h de pared). Validó el pipeline dataset → entrenamiento → comparación → evidencia y produjo la batería estadística preliminar (Kruskal-Wallis p = 0.0459). Se mantiene como referencia histórica; las cifras de ranking de este capítulo provienen de Colab.

**Duración por job (min) — corrida local v4 (5 episodios, referencia):**

| Algoritmo | E1 | E2 | E3 |
|---|---:|---:|---:|
| HAPPO | 66.5 | 66.15 | 57.75 |
| MASAC | 125.88 | 148.33 | 135.72 |
| MATD3 | 375.56 | 377.49 | 451.12 |
| MAAC | 331.79 | 328.82 | 322.9 |

> HAPPO (on-policy) es el más rápido; MATD3 y MAAC (off-policy con réplay y críticos pesados) son los más costosos. `[Pendiente: tiempos de pared por job en Colab.]`

## 5.2 Métricas utilizadas

- **OE.1 Flexibilidad:** `peak_average`, `ramping_average`, `one_minus_load_factor_average`, `grid_import/export` (control vs baseline y delta), `zero_net_energy`.
- **OE.2 CO₂:** `carbon_emissions` (control/baseline/delta), promedios diarios.
- **OE.3 Costos:** `electricity_cost` (control/baseline/delta), `cost_peak_average`, `price_signal_deviation`.

Los KPIs se calculan con `env.evaluate_v2()` y se normalizan contra la línea base CityLearn v2 (`baseline`, `hour_rbc`); valores < 1.0 indican mejora respecto al baseline. El score global Colab agrega normalización min-max (menor = mejor) sobre flexibilidad compuesta E1, delta CO₂ E2 y delta costo E3 (`tools/aggregate_colab_drive_kpis.py`).

## 5.3 Resultados obtenidos — Selección del mejor MADRL *(corrida canónica Colab/Drive)*

El reporte `best_madrl_report.json` (generado 2026-07-03, evaluación agregada sobre E1/E2/E3 con KPIs auditados de Drive) determina:

| Rango | Algoritmo | Score global | OE.1 (flex) | OE.2 (CO₂) | OE.3 (costo) | Episodios (E1/E2/E3) | Seleccionado |
|:---:|:---:|:---:|:---:|:---:|:---:|:---:|:---:|
| **1** | **MATD3** | **0.6667** | **1.0000** | **1.0000** | 0.0000 | 40 / 40 / 40 | **Sí** |
| 2 | MAAC | 0.5706 | 0.5837 | 0.1282 | **1.0000** | 11 / 11 / 11 | No |
| 3 | MASAC | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 12 / 12 / 12 | No |
| — | HAPPO | — | — | — | — | ~49 / sin KPIs | Excluido (evaluación) |

**Línea de selección obligatoria:** *"Mejor algoritmo MADRL seleccionado: MATD3"*.

Criterios de selección: score global normalizado (flexibilidad E1 + CO₂ E2 + costos E3), reward promedio, reducción de picos, gestión SOC/BESS, reducción de CO₂, cumplimiento de restricciones y robustez.

> **Nota metodológica:** MASAC ocupa el rango 3 con score 0.0 porque, en la normalización min-max entre los tres algoritmos con KPIs, sus valores físicos son los peores en flexibilidad y CO₂; no implica fallo de entrenamiento, sino desempeño inferior en esos ejes con el presupuesto parcial de 12 episodios. MAAC lidera OE.3 (costo) pero no compensa en flexibilidad ni CO₂.

### 5.3.1 KPIs físicos primarios por algoritmo (Colab/Drive)

**OE.1 — Flexibilidad compuesta E1** `(peak_average + ramping_average + one_minus_load_factor_average) / 3` (menor = mejor):

| Algoritmo | Flex compuesta E1 | `peak_average` E1 |
|---|:---:|:---:|
| **MATD3** | **1.0009** | **1.0081** |
| MAAC | 1.0124 | 1.0307 |
| MASAC | 1.0286 | 1.0851 |

**OE.2 — Delta emisiones CO₂ E2** (kg; menor = mejor):

| Algoritmo | `carbon_emissions_delta` (kg) | `carbon_emissions` (norm.) |
|---|:---:|:---:|
| **MATD3** | **23 070** | 1.0421 |
| MAAC | 70 654 | 1.0279 |
| MASAC | 77 649 | 1.0516 |

**OE.3 — Delta costo eléctrico E3** (EUR; menor = mejor):

| Algoritmo | `electricity_cost_delta` (EUR) | `electricity_cost` (norm.) |
|---|:---:|:---:|
| **MAAC** | **9 515** | 1.0027 |
| MATD3 | 44 399 | 1.0092 |
| MASAC | `[Pendiente]` | `[Pendiente]` |

Fuente: `outputs/_drive_madrl/kpis/{matd3,maac,masac}_E{1,2,3}_core_kpis.csv`.

### 5.3.2 KPIs físicos de la mejor corrida global (MATD3 · E3, `core_kpis.csv`)

| KPI (normalizado vs baseline) | Valor |
|---|---:|
| `peak_average` | 1.0071 |
| `ramping_average` | 1.0011 |
| `one_minus_load_factor_average` | 0.9936 |
| `carbon_emissions` | 1.0742 |
| `electricity_cost` | 1.0092 |
| `carbon_emissions_delta` (kg) | 41 293 |
| `electricity_cost_delta` (EUR) | 44 399 |
| `pv_self_consumption_ratio` | 0.1829 |

> Estos KPIs corresponden a la política MATD3-E3 evaluada tras **40 episodios** de entrenamiento Colab (no 50 completos). Ningún valor normalizado < 1.0 en CO₂ ni costo indica que la política aún no supera al baseline en esos ejes de forma agregada; MATD3 destaca por menor delta absoluto frente a MAAC/MASAC. `[Pendiente: ev_departure_success_rate y series de reward de MATD3-E3 desde training_summary Colab.]`

### 5.3.3 Comparación con ranking local v4 (referencia histórica, 5 ep)

| Fuente | Mejor MADRL | Score global | KW p |
|---|---|:---:|:---:|
| Local v4 (5 ep) | MATD3 | 0.7445 | 0.0459 |
| Colab/Drive (40/11/12 ep) | MATD3 | 0.6667 | `[Pendiente]` |

La dirección del hallazgo (MATD3 como mejor global) se mantiene; la magnitud del score no es directamente comparable entre corridas por diferente presupuesto de episodios y conjunto de algoritmos incluidos.

## 5.4 Comparación con baseline y trabajos relacionados *(Colab/Drive — MATD3 E1)*

El archivo `matd3_E1_axis_baseline.csv` resume la evaluación por eje (MATD3-E1, 40 ep):

| Eje | KPIs comparables | Mejorados (< baseline) | No mejorados |
|---|:---:|:---:|:---:|
| OE.1 Flexibilidad | 12 | 5 | 7 |
| OE.2 CO₂ | 5 | 0 | 5 |
| OE.3 Costos | 9 | 1 | 8 |

**Lectura:** MATD3 mejora parcialmente en flexibilidad (5/12 KPIs) pero **no supera al baseline en ningún KPI de CO₂** en E1 con la política evaluada. En costos, 1/9 KPIs mejorado. Esto confirma la especialización por eje y la necesidad de análisis multiobjetivo (Pareto) en lugar de un único score global.

Comparación con la literatura: las mejoras reportadas por trabajos análogos (Yao et al., 2023: ~15 % pico / ~18 % costo; Liu et al., 2022: ~15 % CO₂ / ~20 % costo; Xie et al., 2023: ~25 % en coordinación con atención) sirven de marco de contraste. `[Pendiente: porcentajes de mejora MADRL vs baseline por KPI con corrida Colab completa (50 ep) y re-evaluación HAPPO.]`

## 5.5 Pruebas estadísticas

### 5.5.1 Corrida local v4 (5 ep) — referencia

| Prueba | Resultado | p-valor | Conclusión |
|---|---|:---:|---|
| Shapiro-Wilk | Algunos grupos no normales | — | Justifica tests no paramétricos |
| Kruskal-Wallis (4 algoritmos) | Diferencia global | **0.0459** | Significativo (α = 0.05) |
| Mann-Whitney U: MATD3 vs HAPPO | MATD3 superior | **0.0182** | Significativo |
| Wilcoxon SR: MATD3 vs HAPPO | Diferencia sistemática | **2.62×10⁻⁶** | Muy significativo |

Artefactos: `outputs/thesis_objective_evidence/{analisis_estadistico_madrl.csv, ...}`.

### 5.5.2 Corrida canónica Colab/Drive

`[Pendiente: ejecutar celda 9.1 del notebook con los 12 results.json de Drive una vez completados los 50 ep y re-evaluado HAPPO; exportar Kruskal-Wallis, Mann-Whitney U, Wilcoxon y tamaños de efecto Cliff's δ / Hedges g para MATD3 vs MAAC/MASAC.]`

## 5.6 Figuras

Cada corrida genera 13 figuras PNG (manifiesto `figures/figures_manifest.json`):

- `reward_timeseries.png`, `convergence_returns.png`, `episode_reward_summary.png`, `learning_efficiency.png` — dinámica de entrenamiento.
- `citylearn_v2_district_timeseries.png` — carga neta del distrito.
- `axis_baseline_comparison.png`, `baseline_gain_by_kpi.png` — ganancia vs baseline.
- `core_kpis.png`, `OE1_flexibility_kpis.png`, `OE2_co2_kpis.png`, `OE3_cost_kpis.png` — KPIs por eje.
- `exploration_action_l2.png`, `agent_reward_contribution.png` — exploración y contribución por agente.

Figuras Colab: persisten en Drive bajo `madrl_v3_20260627_164047/{ALGORITMO}/E{n}/figures/`. `[Pendiente: insertar en la versión final figuras seleccionadas (p. ej. baseline_gain_by_kpi de MATD3-E2/E3) tras descarga desde Drive.]`

## 5.7 Discusión de resultados

1. **MATD3 es el mejor MADRL global en Colab** (score 0.6667 con KPIs auditados; 40 ep). Su doble crítico (anti-sobreestimación) y la política determinística favorecen estabilidad en horizonte largo (8 760 pasos), con mejor flexibilidad compuesta y menor delta de CO₂ que MAAC y MASAC en el presupuesto evaluado.
2. **Especialización por eje:** MAAC lidera costos (OE.3, delta 9 515 EUR vs 44 399 MATD3-E3) pero queda detrás en flexibilidad y CO₂. MASAC, con solo 12 ep, muestra los peores picos (peak 1.085 E1). HAPPO no pudo evaluarse; en la corrida local v4 lideraba flexibilidad pura (OE.1).
3. **Frente al baseline v2:** en MATD3-E1, 5/12 KPIs de flexibilidad mejoran pero **0/5 KPIs de CO₂** mejoran; la interpretación correcta exige análisis por eje y frontera de Pareto, no solo score global.
4. **Cobertura incompleta:** MATD3 al 80 % del objetivo (40/50 ep); MAAC y MASAC con convergencia parcial; HAPPO bloqueado por error de evaluación. Completar 50 ep, corregir `VecEnvWrapper` en HAPPO y re-ejecutar celda 9.1 robustecerán las conclusiones.
5. **Validación del pipeline:** la corrida local v4 (5 ep, KW p = 0.0459) anticipó la dirección del ranking Colab (MATD3 primero), lo que respalda la reproducibilidad metodológica del benchmark.

---

### Estado del capítulo
**Resultados canónicos Colab/Drive integrados (parcial).** Completados: ranking MATD3/MAAC/MASAC, KPIs primarios OE.1–OE.3, cobertura de episodios, comparación axis_baseline MATD3-E1. Pendientes: 50 ep completos en todos los algoritmos; re-evaluación HAPPO; pruebas estadísticas Colab; % mejora vs baseline; figuras definitivas desde Drive; KPIs MASAC-E3.
