# Capítulo 5. Resultados y Contrastación de Hipótesis

> **Documento de tesis doctoral — resultados.** Corrida canónica Colab/Drive `madrl_v3_20260627_164047` (**50 episodios**; Drive https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX; espejo local `outputs/madrl_v3_20260627_164047/` + `outputs/_drive_madrl/kpi_recalc_20260728/`). Protocolo: Shapiro–Wilk → batería no paramétrica (α = 0,05). **No inventar p-valores ni scores.** Estructura: (1) descriptivos OG/OE.1–OE.3; (2) inferenciales OG/OE.1–OE.3; (3) otros resultados (performance, baseline, multiobjetivo); (4) contrastación H0G/H1G y HE10–HE31; (5) discusión; (6) catálogo de artefactos. **PG/PE/OG/OE/H se citan con el texto exacto del Cap. 1 (autor 2026-07-29); no parafrasear.** Rutas de figuras relativas a `docs/tesis_capitulos/`.

---

## 5.0 Mapa de pasos y lectura del capítulo

| # | Bloque Cap. 5 | Contenido (independiente por objetivo) | Artefacto principal |
|---:|---|---|---|
| 1 | §5.1 | Marco experimental y cobertura 4×3 | Drive; `episodes_recorded` |
| 2 | **§5.2** | **Resultados descriptivos estadísticos:** §5.2.1 OG; §5.2.2 OE.1; §5.2.3 OE.2; §5.2.4 OE.3 | `best_madrl`; KPI-gains; district KPIs |
| 3 | **§5.3** | **Resultados inferenciales estadísticos:** §5.3.1 OG; §5.3.2 OE.1; §5.3.3 OE.2; §5.3.4 OE.3 | KW, Friedman, Wilcoxon (KPI-gains) |
| 4 | **§5.4** | **Otros resultados:** §5.4.1 OG; §5.4.2 OE.1; §5.4.3 OE.2; §5.4.4 OE.3 | Convergencia, baseline, TOPSIS, figuras |
| 5 | **§5.5** | **Contrastación de hipótesis:** §5.5.1 H0G/H1G; §5.5.2 HE10/HE11; §5.5.3 HE20/HE21; §5.5.4 HE30/HE31 | `decisiones_*.csv` |
| 6 | **§5.6** | **Discusión de resultados** | Síntesis Cap. 5 |

**Regla.** Los líderes descriptivos (§5.2) no sustituyen la decisión inferencial (§5.3) ni el veredicto de hipótesis (§5.5).

**Cadena vertical Cap. 1 → Cap. 5.** PG ↔ OG ↔ H0G/H1G; PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); PE.3 ↔ OE.3 ↔ HE30/HE31 (E3).

**Criterios de determinación del impacto (C1–C5, sin parciales).** C1 impacto vs baseline; C2 diferencias entre algoritmos; C3 KPIs de distrito por eje; C4 KPIs por edificio × eje; **C5 control de recursos** (BESS, EV/V2G, carga desplazable). Cada OE se documenta a nivel distrito y edificio (§5.1.1, §5.4.5). C3–C5 no sustituyen C1–C2, pero sin ellos el cumplimiento de objetivos no se declara completo.

**Fuente única de cálculo (50 episodios Drive → `outputs/`).** Todo número de Cap. 5 se calcula o se lee desde artefactos guardados de la corrida `madrl_v3_20260627_164047` (espejo local + KPI recalc). No se mezclan con la corrida histórica v4 (~5 ep).

| Plano | Naturaleza | Qué exige / responde | Artefacto en `outputs/` (ejecutado sobre 50 ep Drive) |
|---|---|---|---|
| **evaluate_v2 4/4** | **Estadística descriptiva** (ranking scores) | Quién es relativamente mejor (incluye HAPPO) | `_drive_madrl/kpi_recalc_20260728/tables/ranking_oe_scores.csv` |
| **TOPSIS / AHP** | **Estadística descriptiva** (selección multicriterio) | Quién es relativamente mejor bajo pesos AHP | `madrl_multicriteria_selection/topsis_ranking.csv` (+ `selection_report.json`) |
| **`best_madrl` 3×3** | **Estadística descriptiva** | Score normalizado MATD3/MAAC/MASAC | `madrl_v3_20260627_164047/resumen_comparativo/best_madrl_report.json` |
| **Deltas físicos distrito** | **Estadística descriptiva** | flex / ΔCO₂ / Δcosto por algoritmo | `kpi_recalc_20260728/` + `resumen_comparativo/multiobjetivo/` |
| **KPI-gains → HE10–HE31** | **Inferencial canónico** | Impacto vs baseline **y** diferencias entre algoritmos | `madrl_v3_.../resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` (`decisiones_*.csv`, Wilcoxon/KW/Friedman) |

**Consecuencia.** MAAC en costos / TOPSIS / 4/4 = resultado **descriptivo** de los 50 ep. HE11/HE21/HE31 **solo** se deciden con KPI-gains de esos mismos 50 ep; ranking descriptivo **no** las respalda automáticamente.

### 5.0.1 Inventario de carpetas `outputs/` (rol en Cap. 5)

| Carpeta `outputs/` | Archivos (aprox.) | Rol en tesis | Acápite Cap. 5 |
|---|---:|---|---|
| **`madrl_v3_20260627_164047/`** | ~659 | Corrida canónica 50 ep (MATD3, MAAC, MASAC, HAPPO × E1–E3); figuras por job; `resumen_comparativo/` | §5.1–§5.5 (núcleo) |
| **`_drive_madrl/`** | ~331 | Espejo Drive + `kpi_recalc_20260728/` + análisis objetivo (22 PNG) + `full_data/` | §5.2–§5.4 |
| **`madrl_multicriteria_selection/`** | 7 | TOPSIS+AHP, Pareto, curvas aprendizaje, degradación | §5.4.4 |
| **`madrl_nonparametric_battery/`** | 2 | Batería episódica 4 algoritmos (complementaria) | §5.3 / §5.4.5 |
| **`madrl_nonparametric_battery_smoke_n3/`** | 2 | Smoke multi-semilla ilustrativo (n=3) | §5.4.5 (no canónico) |
| **`comparison_citylearn_v2_vs_v3_madrl/`** | 36 | MADRL vs baseline/hour_rbc (12 PNG + rankings) | §5.4.2 |
| **`citylearn_v2_original_benchmark/`** | ~233 | Controles RBC/baseline CityLearn v2 (E1–E3) | §5.4.2 |
| **`citylearn_v3_madrl_full_20260615_074011_v4/`** | ~886 | Corrida histórica v4 (~5 ep); **no** sustituye canónica 50 ep | §5.4.6 (referencia) |
| **`thesis_objective_evidence/`** | 57 | Tablas/MD de evidencia PG–OE–H sincronizadas | §5.2–§5.5 |
| **`dataset_cache/`** | 6 | Caché de dataset (sin KPIs de resultados) | Fuera Cap. 5 (metodología) |

---

## 5.1 Marco experimental y cobertura

Se ejecutaron **12 corridas** (4 algoritmos × 3 escenarios, seed = 0), horizonte **50 episodios × 8 760 pasos**, perfil `*_unified_comparable_v4`.

**Tabla 5.1.** Cobertura de episodios y uso inferencial.

| Algoritmo | E1 | E2 | E3 | KPIs finales | Uso |
|---|---:|---:|---:|---|---|
| **MATD3** | 50 | 50 | 50 | Sí | Descriptivo + inferencial canónico |
| **MAAC** | 50 | 50 | 50 | Sí | Descriptivo + inferencial canónico |
| **MASAC** | 50 | 50 | 50 | Sí | Descriptivo + inferencial canónico |
| **HAPPO** | 49 | 49 | 49 | Sí (Drive 2026-07-28) | Descriptivo 4/4; HE canónica sobre trío 3×3 |

**Tabla 5.2.** Operacionalización por objetivo.

| Objetivo | Escenario | VD | Métricas primarias | Pesos (flex/CO₂/costo) |
|---|---|---|---|---|
| **OE.1** | E1 | Flexibilidad | flex_composite, peak, ramping, KPI-gains | 0,70 / 0,15 / 0,15 |
| **OE.2** | E2 | Emisiones CO₂ | carbon_emissions_delta, KPI-gains | 0,15 / 0,70 / 0,15 |
| **OE.3** | E3 | Costos | electricity_cost_delta, KPI-gains | 0,25 / 0,15 / 0,60 |
| **OG** | E1–E3 | Coordinación multiobjetivo | score `best_madrl`; integración KPI-gains | — |

Fuente Drive: [MADRLCitytleranflexresdr](https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX). Catálogo evaluate_v2: **58** KPIs, **680** valores (`kpi_recalc_20260728`). Core KPI: **14** nombres / **176** valores; building KPI: **15 300** filas.

**Figura 5.1.** Ranking global y scores por OE (Drive / resumen comparativo).

![Figura 5.1. Ranking global OE](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_global_ranking_oe.png)

**Figura 5.2.** Completitud episódica y KPIs de objetivo (resumen).

![Figura 5.2a. Completitud episódica](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/drive_episode_completion.png)

![Figura 5.2b. Scores de ranking](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/drive_ranking_scores.png)

![Figura 5.2c. KPIs de objetivo](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/drive_objective_kpis.png)

---


### 5.1.1 Catálogo de KPIs CityLearn v3 propuesto

La VD se operacionaliza con **54 KPI oficiales** (matriz `outputs/thesis_objective_evidence/KPIs_y_metricas.*`: OE.1=36, OE.2=7, OE.3=11). El runtime `citylearn_v3_report.all_values` añade **4** métricas (`flex_composite` + 3 derivados `price_signal_*`) → **58 KPI / 680 valores** en `outputs/_drive_madrl/kpi_recalc_20260728/` (12/12 tratamientos; `price_signal_*` solo E1+E3). Core: 14/176; building: 15 300 filas.

**Tabla 5.1.1.** Cobertura del catálogo.

| Capa | n | Cobertura | Artefacto |
|---|---:|---|---|
| 54 KPI oficiales (matriz VD) | 54 | 12/12 (`price_signal_*` E1+E3) | `KPIs_y_metricas.*` |
| Runtime all_values | 58 | 680 valores | `all_evaluate_v2_kpis_*.csv` |
| Core KPI | 14 / 176 | 12 jobs | `all_core_kpis_*.csv` |
| Building KPI | 15 300 | 17 edificios × jobs | `building_kpis_all.csv` |

**Tabla 5.1.2.** Por OE + extras runtime.

| Objetivo | n | Representativos |
|---|---:|---|
| OE.1 E1 | 36 | grid_*, peak/ramping/load_factor, pv_*, battery_*, ev_*, community_*, zero_net_energy |
| OE.2 E2 | 7 | carbon_emissions* |
| OE.3 E3 | 11 | electricity_cost*, cost_peak/ramping/load_factor, price_signal_deviation |
| Extras runtime | 4 | flex_composite; price_signal_deviation_baseline/delta/ratio |

**Tabla 5.1.3.** Listado nominal (54 oficiales + 4 runtime).

| Eje | KPI | Tipo | Orientación |
|---|---|---|---|
| OE.1 Flexibilidad (E1) | `grid_import` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `grid_import_control` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `grid_import_baseline` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `grid_import_delta` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `zero_net_energy` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `net_exchange_control` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `net_exchange_baseline` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `net_exchange_delta` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `grid_export_ratio` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `grid_export_control` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `grid_export_baseline` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `grid_export_delta` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `peak_average` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `ramping_average` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `one_minus_load_factor_average` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `pv_generation_total` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `pv_generation_daily_average` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `pv_export_total` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `pv_export_daily_average` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `pv_self_consumption_ratio` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `community_local_traded_total` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `community_local_traded_daily_average` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `community_import_share` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `battery_charge_total` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `battery_discharge_total` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `battery_throughput_total` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `battery_equivalent_full_cycles` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `battery_capacity_fade_ratio` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `ev_departure_count` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `ev_departure_met_count` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `ev_departure_within_tolerance_count` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `ev_departure_success_rate` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `ev_departure_within_tolerance_rate` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `ev_departure_soc_deficit_mean` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `ev_charge_total` | oficial | mayor=mejor |
| OE.1 Flexibilidad (E1) | `ev_v2g_export_total` | oficial | mayor=mejor |
| OE.2 Emisiones CO₂ (E2) | `carbon_emissions` | oficial | menor=mejor |
| OE.2 Emisiones CO₂ (E2) | `carbon_emissions_control` | oficial | menor=mejor |
| OE.2 Emisiones CO₂ (E2) | `carbon_emissions_baseline` | oficial | menor=mejor |
| OE.2 Emisiones CO₂ (E2) | `carbon_emissions_delta` | oficial | menor=mejor |
| OE.2 Emisiones CO₂ (E2) | `carbon_emissions_daily_average_control` | oficial | menor=mejor |
| OE.2 Emisiones CO₂ (E2) | `carbon_emissions_daily_average_baseline` | oficial | menor=mejor |
| OE.2 Emisiones CO₂ (E2) | `carbon_emissions_daily_average_delta` | oficial | menor=mejor |
| OE.3 Costos (E3) | `electricity_cost` | oficial | menor=mejor |
| OE.3 Costos (E3) | `electricity_cost_control` | oficial | menor=mejor |
| OE.3 Costos (E3) | `electricity_cost_baseline` | oficial | menor=mejor |
| OE.3 Costos (E3) | `electricity_cost_delta` | oficial | menor=mejor |
| OE.3 Costos (E3) | `electricity_cost_daily_average_control` | oficial | menor=mejor |
| OE.3 Costos (E3) | `electricity_cost_daily_average_baseline` | oficial | menor=mejor |
| OE.3 Costos (E3) | `electricity_cost_daily_average_delta` | oficial | menor=mejor |
| OE.3 Costos (E3) | `cost_peak_average` | oficial | menor=mejor |
| OE.3 Costos (E3) | `cost_ramping_average` | oficial | menor=mejor |
| OE.3 Costos (E3) | `cost_one_minus_load_factor_average` | oficial | menor=mejor |
| OE.3 Costos (E3) | `price_signal_deviation` | oficial | menor=mejor |
| OE.1 Flexibilidad (E1) | `flex_composite` | runtime (all_values) | menor=mejor |
| OE.3 Costos (E3) | `price_signal_deviation_baseline` | runtime (derivado) | menor=mejor |
| OE.3 Costos (E3) | `price_signal_deviation_delta` | runtime (derivado) | menor=mejor |
| OE.3 Costos (E3) | `price_signal_deviation_ratio` | runtime (derivado) | menor=mejor |


## 5.2 Resultados descriptivos estadísticos

Este numeral reporta **solo** estadística descriptiva calculada sobre los **50 episodios Drive** guardados en `outputs/` (medias, medianas, KPIs de distrito, rankings normalizados 3×3 y 4/4, TOPSIS). **No decide hipótesis.** Responde descriptivamente al **PG** y a los **PE.1–PE.3**, y documenta el grado de avance de **OG** y **OE.1–OE.3**.

Incluye explícitamente como **descriptivos** (no inferenciales de HE):

- Ranking evaluate_v2 **4/4** → `outputs/_drive_madrl/kpi_recalc_20260728/tables/ranking_oe_scores.csv` (MAAC 0,9538).
- **TOPSIS/AHP** → `outputs/madrl_multicriteria_selection/topsis_ranking.csv` (MAAC C*=0,7828); detalle de figuras en §5.4.4.
- `best_madrl` 3×3 y deltas físicos de distrito (flex, CO₂, costo).

Las pruebas Shapiro/KW/Friedman/Wilcoxon sobre **KPI-gains** van en §5.3–§5.5.

### 5.2.1 OG — resultados descriptivos estadísticos

**PG (referencia).** ¿En qué medida el algoritmo MADRL (aprendizaje por refuerzo profundo multiagente) impacta en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño a nivel global?

**OG.** OG. - Determinar el impacto de los algoritmos aprendizaje por refuerzo profundo multiagente (MADRLs) en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, e identificar cuál de los algoritmos presenta el mejor desempeño a nivel global.

**Tabla 5.3.** Ranking canónico 3×3 (`best_madrl` / score normalizado por eje).

| Rango | Algoritmo | Score global | OE.1 | OE.2 | OE.3 |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | **MATD3** | **0,6667** | 1,0000 | 1,0000 | 0,0000 |
| 2 | MAAC | 0,5706 | 0,5837 | 0,1282 | **1,0000** |
| 3 | MASAC | 0,2351 | 0,0000 | 0,0000 | 0,7054 |

**Tabla 5.4.** Score medio de escenario (igual peso E1–E3).

| Algoritmo | Score medio E1–E3 | Desv. | Nota descriptiva |
|---|---:|---:|---|
| **MAAC** | **0,8066** | 0,1474 | Mejor score de escenario (igual peso) |
| MATD3 | 0,6323 | 0,3752 | Mejor mediana robusta / `best_madrl` 0,6667 |
| MASAC | 0,1694 | 0,2028 | Peor score de escenario |

**Tabla 5.5.** Ranking evaluate_v2 **4/4** (incluye HAPPO; fuente `kpi_recalc_20260728/tables/ranking_oe_scores.csv`).

| Rank | Algoritmo | Score global | OE1 flex | OE2 CO₂ | OE3 costo | flex_composite E1 | ΔCO₂ E2 (kg) | Δcosto E3 (EUR) |
|---:|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | MAAC | 0,9538 | 0,8951 | 0,9662 | **1,0000** | 1,0124 | 70 654 | **9 515** |
| 2 | MATD3 | 0,8805 | **1,0000** | **1,0000** | 0,6415 | **1,0009** | **23 070** | 44 399 |
| 3 | MASAC | 0,8679 | 0,7479 | 0,9612 | 0,8944 | 1,0286 | 77 649 | 19 793 |
| 4 | HAPPO | 0,0000 | 0,0000 | 0,0000 | 0,0000 | 1,1105 | 1 431 341 | 106 828 |

El veredicto descriptivo del OG canónico sigue el **3×3** (MATD3 0,6667). El ranking 4/4 sitúa a MAAC primero por score global normalizado, con HAPPO en último lugar.

**Lectura descriptiva OG / PG:** la gestión coordinada se caracteriza con **trade-off** (MATD3 flex+CO₂; MAAC costos); el mejor desempeño global canónico es **MATD3** (`best_madrl` 0,6667), **sin** dominador Pareto único.

**Figura 5.3.** Comparación global multiobjetivo y best/worst por escenario.

![Figura 5.3a. Comparación global](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/global_comparison.png)

![Figura 5.3b. Best/worst por escenario](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_best_worst_por_escenario.png)

![Figura 5.3c. Objetivos de distrito](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/drive_district_objectives.png)

### 5.2.2 OE.1 — resultados descriptivos estadísticos (flexibilidad)

**PE.1:** ¿En qué medida el algoritmo MADRL impacta en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E1?

**OE.1:** Determinar el impacto de los algoritmos MADRLs en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E1.

**Tabla 5.6.** KPI-gains evaluate_v2 en E1 (canónico 3×3; ganancia > 0 favorece MADRL).

| Algoritmo | n KPI | Media gain | Mediana | Mejorados | No mejorados |
|---|---:|---:|---:|---:|---:|
| **MAAC** | 12 | −0,0888 | **−0,0012** | 5 | 7 |
| MATD3 | 12 | −0,0868 | −0,0029 | 5 | 7 |
| MASAC | 12 | −0,2621 | −0,0136 | 2 | 10 |

**Líder por mediana KPI-gain:** MAAC.  
**KPIs físicos distrito (`flex_composite` E1, menor = mejor):** MATD3 = **1,0009**; MAAC = 1,0124; MASAC = 1,0286; HAPPO = 1,1105.

**Figura 5.4.** OE.1 — KPI comparativo E1 y proxy por edificio.

![Figura 5.4a. Comparativo OE1 KPI](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E1_OE1_kpi.png)

![Figura 5.4b. flex_composite por edificio](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/drive_building_E1_flex_composite_proxy.png)

![Figura 5.4c. Media episódica OE1 (Drive analysis)](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/oe1_e1_episode_mean.png)

**Respuesta descriptiva a PE.1 / avance OE.1:** impacto descriptivo mixto (medianas KPI-gain ≤ 0); mejor desempeño en E1 según KPI-gain = **MAAC**; según `flex_composite` de distrito = **MATD3**.

### 5.2.3 OE.2 — resultados descriptivos estadísticos (emisiones CO₂)

**PE.2:** ¿En qué medida el algoritmo MADRL impacta en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E2?

**OE.2:** Determinar el impacto de los algoritmos MADRLs en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E2.

**Tabla 5.7.** KPI-gains evaluate_v2 en E2 (canónico 3×3).

| Algoritmo | n KPI | Media gain | Mediana | Mejorados | No mejorados |
|---|---:|---:|---:|---:|---:|
| **MATD3** | 5 | −0,4101 | **−0,0421** | 0 | 5 |
| MAAC | 5 | −0,4148 | −0,0470 | 0 | 5 |
| MASAC | 5 | −0,4171 | −0,0516 | 0 | 5 |

**Líder descriptivo:** MATD3.  
**Delta CO₂ distrito E2 (kg, menor = mejor):** MATD3 = **23 070**; MAAC = 70 654; MASAC = 77 649; HAPPO = 1 431 341.

**Figura 5.5.** OE.2 — KPI comparativo E2 y emisiones por edificio.

![Figura 5.5a. Comparativo OE2 KPI](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E2_OE2_kpi.png)

![Figura 5.5b. ΔCO₂ por edificio](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/drive_building_E2_carbon_emissions_delta_kgco2.png)

![Figura 5.5c. Media episódica OE2](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/oe2_e2_episode_mean.png)

![Figura 5.5d. Heatmap carbono por edificio](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/building_carbon_heatmap.png)

**Respuesta descriptiva a PE.2 / avance OE.2:** en KPI-gains ningún algoritmo mejora el baseline (0/5); por KPI físico de distrito el mejor desempeño en E2 es **MATD3**.

### 5.2.4 OE.3 — resultados descriptivos estadísticos (costos)

**PE.3:** ¿En qué medida el algoritmo MADRL impacta en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E3?

**OE.3:** Determinar el impacto de los algoritmos MADRLs en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E3.

**Tabla 5.8.** KPI-gains evaluate_v2 en E3 (canónico 3×3).

| Algoritmo | n KPI | Media gain | Mediana | Mejorados | No mejorados |
|---|---:|---:|---:|---:|---:|
| **MAAC** | 9 | −0,2278 | **−0,0027** | 1 | 8 |
| MATD3 | 9 | −0,2259 | −0,0092 | 1 | 8 |
| MASAC | 9 | −0,2355 | −0,0140 | 1 | 8 |

**Líder descriptivo:** MAAC.  
**Delta costo distrito E3 (EUR, menor = mejor):** MAAC = **9 515**; MASAC = 19 793; MATD3 = 44 399; HAPPO = 106 828.

**Figura 5.6.** OE.3 — KPI comparativo E3 y costos por edificio.

![Figura 5.6a. Comparativo OE3 KPI](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E3_OE3_kpi.png)

![Figura 5.6b. Δcosto por edificio](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/drive_building_E3_electricity_cost_delta_eur.png)

![Figura 5.6c. Media episódica OE3](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/oe3_e3_episode_mean.png)

![Figura 5.6d. Heatmap costo por edificio](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/building_cost_heatmap.png)

**Respuesta descriptiva a PE.3 / avance OE.3:** impacto descriptivo limitado en KPI-gains; mejor desempeño en E3 = **MAAC** (mediana KPI-gain y delta de costo de distrito).

---

## 5.3 Resultados inferenciales

Este numeral reporta **solo** pruebas estadísticas sobre **KPI-gains** de la corrida canónica de **50 episodios Drive** (Shapiro como puerta; Kruskal–Wallis, Friedman, Wilcoxon; α = 0,05). Fuente de ejecución guardada:

`outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/`

Alimenta la contrastación de **H0G/H1G** y **HE10–HE31** en §5.5. **No** usa TOPSIS ni el ranking 4/4 como prueba de hipótesis.

### 5.3.1 OG — resultados inferenciales estadísticos

Contraste de la hipótesis general (textos exactos en §5.5.2) sobre la gestión coordinada y el desempeño global.

| Prueba | p | Lectura |
|---|---:|---|
| Kruskal–Wallis global (scores) | 0,4044 | No significativo |
| Friedman pareado (KPI agregados) | **0,0096** | Significativo; Kendall W = 0,1787 (efecto débil) |
| KW ALL KPI-gains | 0,1554 | No significativo |

**Puerta Shapiro (ALL):** normalidad rechazada → solo no paramétrico.

### 5.3.2 OE.1 — resultados inferenciales estadísticos (HE10 / HE11)

Contraste de HE10/HE11 sobre flexibilidad en E1 (textos exactos en §5.5.2).

Shapiro–Wilk rechaza normalidad (p ≈ 10⁻⁷–10⁻⁸). Ruta paramétrica descartada.

| Prueba | Estadístico | p | Interpretación |
|---|---|---:|---|
| Kruskal–Wallis | H = 1,5164 | **0,4685** | No se rechaza igualdad global |
| Friedman (pareado por KPI) | χ² = 5,5897 | 0,0611 | No significativo; W = 0,2329 |
| Wilcoxon vs cero (Holm) | MAAC / MATD3 / MASAC | 0,6025 / 0,6025 / **0,0483** | Solo MASAC significativo y **desfavorable** |
| Wilcoxon post hoc entre algoritmos | pares Holm | mín. 0,1100 | Ningún par significativo tras Holm |

### 5.3.3 OE.2 — resultados inferenciales estadísticos (HE20 / HE21)

Contraste de HE20/HE21 sobre emisiones de CO₂ en E2 (textos exactos en §5.5.2).

Shapiro–Wilk rechaza normalidad (p ≈ 10⁻⁴–10⁻⁵).

| Prueba | Estadístico | p | Interpretación |
|---|---|---:|---|
| Kruskal–Wallis | H = 0,5364 | **0,7648** | No se rechaza igualdad global |
| Friedman | χ² = 6,0000 | **0,0498** | Señal pareada débil; W = 0,6000 |
| Wilcoxon vs cero (Holm) | tres algoritmos | 0,1875 | Ningún impacto significativo vs baseline |
| Wilcoxon post hoc | pares Holm | mín. 0,3074 | Señal Friedman no confirmada por pares |

### 5.3.4 OE.3 — resultados inferenciales estadísticos (HE30 / HE31)

Contraste de HE30/HE31 sobre costos energéticos en E3 (textos exactos en §5.5.2).

Shapiro–Wilk rechaza normalidad (p ≈ 10⁻⁷–10⁻⁸).

| Prueba | Estadístico | p | Interpretación |
|---|---|---:|---|
| Kruskal–Wallis | H = 0,6138 | **0,7357** | No se rechaza igualdad global |
| Friedman | χ² = 3,4286 | 0,1801 | No significativo; W = 0,1905 |
| Wilcoxon vs cero (Holm) | MAAC / MATD3 / MASAC | 0,0781 / 0,0586 / 0,0781 | Ningún impacto significativo vs cero |
| Wilcoxon post hoc | pares Holm | — | Sin pares significativos omnibus |

Wilcoxon pareado exploratorio MASAC vs MAAC: p = 0,0333 (un par); insuficiente ante KW/Friedman no significativos.

**Figura 5.7.** Inferencia complementaria Drive (efecto ε², boxplots, p-Holm).

![Figura 5.7a. Tamaño de efecto ε²](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/objective_effect_size_epsilon2.png)

![Figura 5.7b. Distribuciones episódicas](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/episode_objective_distributions_boxplot.png)

![Figura 5.7c. Heatmaps p-Holm](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/pairwise_holm_pvalue_heatmaps.png)

---

## 5.4 Otros resultados

Tercer acápite. Resultados complementarios **por objetivo de forma independiente** (OG, OE.1, OE.2, OE.3): convergencia, multiobjetivo, baseline v2 y TOPSIS descriptivo. No sustituyen §5.2–§5.3 ni §5.5.

### 5.4.1 OG — otros resultados (coordinación multiobjetivo)

Análisis por algoritmo (MATD3, MAAC, MASAC, HAPPO) de `reward_mean` en `timeseries.csv`: estabilidad, meseta y mejora episodios iniciales→finales.

**Figura 5.8.** Curvas de convergencia comparativas (reward_mean) E1–E3.

![Figura 5.8a. Convergencia E1](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E1_convergence_reward_mean.png)

![Figura 5.8b. Convergencia E2](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E2_convergence_reward_mean.png)

![Figura 5.8c. Convergencia E3](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E3_convergence_reward_mean.png)

**Figura 5.9.** Estabilización del aprendizaje (análisis Drive).

![Figura 5.9a. Estabilización E1](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/convergence_e1_learning_stabilization.png)

![Figura 5.9b. Estabilización E2](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/convergence_e2_learning_stabilization.png)

![Figura 5.9c. Estabilización E3](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/convergence_e3_learning_stabilization.png)

**Catálogo de figuras de performance por job** (ruta `{ALGO}/{E1|E2|E3}/figures/` bajo `madrl_v3_20260627_164047/`):

| Figura (nombre de archivo) | MATD3/MAAC/MASAC | HAPPO | Qué mide |
|---|---:|---:|---|
| `performance_comparison.png` | 9 | 3 | **Distrito + edificio** (efecto vs baseline 4 MADRL + 17 edificios) |
| `convergence_returns.png` | 3×3 = 9 | 3 | Retornos / convergencia |
| `reward_timeseries.png` | 9 | 3 | Serie temporal de recompensa |
| `episode_reward_summary.png` | 9 | 3 | Resumen episódico |
| `learning_efficiency.png` | 9 | 3 | Eficiencia de aprendizaje |
| `agent_reward_contribution.png` | 9 | 3 | Contribución por agente |
| `exploration_action_l2.png` | 9 | 3 | Exploración (norma L2 de acciones) |
| `citylearn_v2_district_timeseries.png` | 9 | 3 | Series temporales de distrito |
| `core_kpis.png` | 9 | 0 | KPIs núcleo |
| `OE1_flexibility_kpis.png` | 9 | 0 | Barras KPI flexibilidad |
| `OE2_co2_kpis.png` | 9 | 0 | Barras KPI CO₂ |
| `OE3_cost_kpis.png` | 9 | 0 | Barras KPI costo |
| `axis_baseline_comparison.png` | 9 | 0 | Comparación vs baseline por eje |
| `baseline_gain_by_kpi.png` | 9 | 0 | Ganancia por KPI vs baseline |

Total canónico: **129 PNG** por job (MATD3/MAAC/MASAC: 14×9; HAPPO: 8×3) + **4 resúmenes** `resumen_comparativo/performance_comparison/{ALGO}_performance_comparison.png`. Mapping explicativo: `performance_comparison_mapping.md`. Generador: `tools/eval/generate_madrl_performance_comparison_figures.py`.

**Cómo leer `performance_comparison.png`.** Panel izquierdo (distrito): efecto primario `%` vs baseline de los cuatro MADRL en el escenario, con el algoritmo del job resaltado. Panel derecho (edificio): heterogeneidad de los 17 edificios Iquitos en el KPI del eje (flex proxy / ΔCO₂ / Δcosto). Signo negativo en distrito = empeoramiento vs baseline; en edificio, Δ negativo = reducción local. Son figuras **descriptivas** (no deciden HE).

**Resúmenes por algoritmo (distrito + edificio, E1–E3):**

![Figura 5.10pc-a. MATD3 performance](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/MATD3_performance_comparison.png)

![Figura 5.10pc-b. MAAC performance](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/MAAC_performance_comparison.png)

![Figura 5.10pc-c. MASAC performance](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/MASAC_performance_comparison.png)

![Figura 5.10pc-d. HAPPO performance](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/performance_comparison/HAPPO_performance_comparison.png)

**Ejemplos representativos (líderes descriptivos por eje):**

![Figura 5.10a. MATD3/E1 performance_comparison](../../outputs/madrl_v3_20260627_164047/MATD3/E1/figures/performance_comparison.png)

![Figura 5.10b. MATD3/E1 OE1 flexibility](../../outputs/madrl_v3_20260627_164047/MATD3/E1/figures/OE1_flexibility_kpis.png)

![Figura 5.10c. MATD3/E2 OE2 CO₂](../../outputs/madrl_v3_20260627_164047/MATD3/E2/figures/OE2_co2_kpis.png)

![Figura 5.10d. MAAC/E3 OE3 cost](../../outputs/madrl_v3_20260627_164047/MAAC/E3/figures/OE3_cost_kpis.png)

![Figura 5.10e. MATD3/E1 convergencia](../../outputs/madrl_v3_20260627_164047/MATD3/E1/figures/convergence_returns.png)

![Figura 5.10f. MAAC/E3 eficiencia](../../outputs/madrl_v3_20260627_164047/MAAC/E3/figures/learning_efficiency.png)

**Tabla 5.9.** Métricas episódicas de distrito (media; `kpi_recalc_20260728/tables/episode_metrics_summary.csv`).

| Algoritmo | Esc. | n | reward mean | emission mean | cost mean |
|---|---|---:|---:|---:|---:|
| HAPPO | E1 | 49 | −0,6303 | 1 046,35 | 463,72 |
| HAPPO | E2 | 49 | −0,4842 | 883,00 | 195,45 |
| HAPPO | E3 | 49 | −0,5208 | 839,72 | 352,57 |
| MAAC | E1 | 50 | −0,6052 | 1 054,33 | 642,61 |
| MAAC | E2 | 50 | −0,5237 | 1 056,39 | 707,47 |
| MAAC | E3 | 50 | −0,5387 | 1 053,55 | 795,39 |
| MASAC | E1 | 50 | −0,6133 | 1 076,48 | 664,74 |
| MASAC | E2 | 50 | −0,5255 | 1 078,37 | 701,76 |
| MASAC | E3 | 50 | −0,5409 | 1 082,90 | 812,16 |
| MATD3 | E1 | 50 | −0,6330 | 1 129,24 | 631,51 |
| MATD3 | E2 | 50 | −0,5336 | 1 132,19 | 669,46 |
| MATD3 | E3 | 50 | −0,5504 | 1 131,14 | 759,29 |

**Figura 5.11.** Series de distrito (costo / emisión) y trazas de control E1–E3.

![Figura 5.11a. E1 costo](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E1_district_net_electricity_consumption_cost.png)

![Figura 5.11b. E1 emisión](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E1_district_net_electricity_consumption_emission.png)

![Figura 5.11c. E2 costo](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E2_district_net_electricity_consumption_cost.png)

![Figura 5.11d. E2 emisión](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E2_district_net_electricity_consumption_emission.png)

![Figura 5.11e. E3 costo](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E3_district_net_electricity_consumption_cost.png)

![Figura 5.11f. E3 emisión](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E3_district_net_electricity_consumption_emission.png)

![Figura 5.11g. Trace E1](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E1_control_trace.png)

![Figura 5.11h. Trace E2](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E2_control_trace.png)

![Figura 5.11i. Trace E3](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/figuras_drive_reales/comparativo/comparativo_E3_control_trace.png)

### 5.4.2 Comparación con baseline CityLearn v2

Contraste por eje frente a `baseline` / `hour_rbc` (score HPHI). Artefactos: `outputs/comparison_citylearn_v2_vs_v3_madrl/` (espejo en `madrl_v3_.../resumen_comparativo/citylearn_v2_baseline/`) y corridas de control en `outputs/citylearn_v2_original_benchmark/` (`baseline`, `hour_rbc`, `optimized_rbc` × E1–E3).

En OE.1 MATD3 puede liderar el eje frente a controles; en OE.2/OE.3 los controles RBC suelen superar a MADRL en score absoluto, sin invalidar el ranking inter-algoritmo.

**Figura 5.12.** MADRL vs CityLearn v2 — heatmaps de ganancia y comparación por OE (E1–E3).

![Figura 5.12a. E1 heatmap](../../outputs/comparison_citylearn_v2_vs_v3_madrl/E1/baseline_gain_heatmap.png)

![Figura 5.12b. E1 OE1](../../outputs/comparison_citylearn_v2_vs_v3_madrl/E1/OE1_comparison.png)

![Figura 5.12c. E2 OE2](../../outputs/comparison_citylearn_v2_vs_v3_madrl/E2/OE2_comparison.png)

![Figura 5.12d. E3 OE3](../../outputs/comparison_citylearn_v2_vs_v3_madrl/E3/OE3_comparison.png)

Tablas: `E{1,2,3}/ranking_by_axis.md`, `ranking_global_weighted.md`, `master_kpi_comparison.md`.

### 5.4.3 Multiobjetivo, edificios y artefactos Drive

- Multiobjetivo distrito/edificio (17 edificios): `resumen_comparativo/multiobjetivo/` (23 PNG: 17 edificios + 6 agregados).
- Figuras por job: ver §5.4.1; manifiesto `figures_manifest.json` por tratamiento.
- Análisis Drive: `outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/` (22 PNG) y `full_data/analysis_real_drive/figures/` (9 PNG).

### 5.4.5 Control de recursos (criterio C5 de impacto)

Criterio obligatorio: el efecto MADRL sobre OE.1–OE.3 solo es atribuible si los agentes controlan recursos (BESS, EV/V2G, carga desplazable). Inventario: 17 edificios, 185 cargadores EV (`building_inventory_multiobjective.csv`).

**Figura 5.13.** Trade-off multiobjetivo, equipos controlados y cobertura de checkpoints.

![Figura 5.13a. Trade-off costo–CO₂–PV](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/multiobjective_tradeoff_cost_co2_pv.png)

![Figura 5.13b. Inventario EV](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/drive_building_ev_inventory.png)

![Figura 5.13c. EV success MATD3/E2](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/drive_building_ev_success_matd3_e2.png)

![Figura 5.13d. Cobertura checkpoints](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/checkpoint_coverage_by_treatment.png)

![Figura 5.13e. Heatmap ranking KPI v2](../../outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/figures/citylearn_v2_kpi_ranking_heatmap.png)

Ejemplo por edificio (B01–B17 disponibles en `multiobjetivo/por_edificio/`):

![Figura 5.13f. Edificio B01 objetivos](../../outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/por_edificio/drive_building_B01_objectives.png)

### 5.4.6 Selección multicriterio TOPSIS + AHP (descriptivo)

Fuente ejecutada sobre métricas derivadas de la campaña 50 ep: `outputs/madrl_multicriteria_selection/` (`selection_report.json`, `topsis_ranking.csv`, `master_metrics_table.csv`, `decision_matrix.csv`).

**Naturaleza.** Estadística / decisión **descriptiva** multicriterio (Cap. 4: **no** es evidencia de HE10–HE31). Se reporta aquí como complemento de §5.2.

**Tabla 5.10.** Ranking TOPSIS (E1; C* = closeness).

| Rank | Algoritmo | C* | d⁺ | d⁻ |
|---:|---|---:|---:|---:|
| 1 | **MAAC** | **0,7828** | 0,0690 | 0,2486 |
| 2 | MASAC | 0,5042 | 0,1489 | 0,1514 |
| 3 | MATD3 | 0,3641 | 0,2231 | 0,1278 |

AHP consistente (CR ≈ 0,003); TOPSIS y AHP coinciden en ganador MAAC; frente de Pareto = {MAAC, MASAC, MATD3}. Puerta de defensibilidad 1.º vs 2.º: consultar `selection_report.json` (`defensible`).

**Figura 5.14.** Multicriterio — Pareto, aprendizaje y degradación.

![Figura 5.14a. Pareto costo–CO₂–flex](../../outputs/madrl_multicriteria_selection/figures/pareto_cost_co2_flex.png)

![Figura 5.14b. Curvas de aprendizaje](../../outputs/madrl_multicriteria_selection/figures/learning_curves.png)

![Figura 5.14c. Barras de degradación](../../outputs/madrl_multicriteria_selection/figures/degradation_bars.png)

### 5.4.7 Batería no paramétrica episódica (complementaria)

- Canónica complementaria 4 algoritmos: `outputs/madrl_nonparametric_battery/nonparametric_battery_report.md` (unidad episódica; KW significativo en OE.1–OE.3; **no** sustituye la HE canónica por KPI-gains del §5.3).
- Smoke multi-semilla ilustrativo: `outputs/madrl_nonparametric_battery_smoke_n3/` (n=3; no afirma robustez multi-semilla entrenada).

En la batería episódica, OE.1 señala a MAAC (KW p ≈ 2×10⁻¹¹); OE.2/OE.3 deben leerse con la orientación costo/emisión y el rol de HAPPO; el veredicto de hipótesis de la tesis permanece en §5.5 (capa KPI-gains 3×3).

### 5.4.8 Corrida histórica v4 (referencia, no canónica)

`outputs/citylearn_v3_madrl_full_20260615_074011_v4/` (~886 archivos; ~5 episodios) es la campaña local previa. Se conserva para trazabilidad de pipeline y figuras de desarrollo; **todos los veredictos Cap. 5 usan** `madrl_v3_20260627_164047` (50 ep).

### 5.4.9 Evidencia tabular sincronizada

`outputs/thesis_objective_evidence/` replica las matrices usadas en la cadena Cap. 1→5: `hipotesis_estadisticas_madrl.csv`, `matriz_resultados_madrl.csv`, `KPIs_y_metricas.csv`, `scores_kpi_algoritmo_madrl.csv`, `objetivos_especificos_cumplimiento.csv`, `comparaciones_wilcoxon_madrl.csv`, etc. (27 CSV + 27 MD).

Recálculo Drive 2026-07-28: `outputs/_drive_madrl/kpi_recalc_20260728/` (`KPIs_y_metricas.md`, `KPIs_y_metricas_FULL.md`, tablas E1/E2/E3, `all_evaluate_v2_kpis_*.csv`, `by_building/building_kpis_all.csv`).

---

## 5.5 Contrastación de hipótesis

Cuarto acápite. Contrastación formal H0/H1 con textos exactos del Cap. 1: primero la **hipótesis general** (nula y alternativa); luego las **hipótesis específicas** nulas y alternativas **de forma independiente** por objetivo (OE.1, OE.2, OE.3). Unidad de decisión = KPI-gains de 50 ep Drive.

### 5.5.1 Hipótesis general (H0G / H1G)

**Protocolo.** Shapiro–Wilk → solo no paramétrico; omnibus KW/Friedman + Holm; HE alternativas requieren impacto significativo **y** diferencias; TOPSIS/4/4 no respaldan HE.

**Formulación nula.** H0G.-El algoritmo MADRL no impacta de manera estadísticamente significativa y diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas en el desempeño global de los algoritmos.

**Formulación alternativa.** H1G.- El algoritmo MADRL impacta de manera estadísticamente significativa y diferenciada en la gestión coordinada de la flexibilidad energética, las emisiones de CO₂ y los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y el desempeño global difiere entre los algoritmos.

| Hipótesis | Decisión | Fundamento |
|---|---|---|
| **H0G** | **Se rechaza de forma exploratoria** | Friedman integración p = 0,0096 + impacto GLOBAL vs baseline (Holm) |
| **H1G** | **Se respalda de forma exploratoria** (sin ganador único; impacto agregado **desfavorable**) | Diferenciación débil; trade-off MATD3/MAAC; **no** implica HE11∧HE21∧HE31 |

### 5.5.2 Hipótesis específicas OE.1 (HE10 / HE11)

**Formulación nula.** HE10.- El algoritmo MADRL no impacta de manera estadísticamente significativa en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E1.

**Formulación alternativa.** HE11.- El algoritmo MADRL impacta de manera estadísticamente significativa en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E1.

| Hipótesis | Decisión | Fundamento |
|---|---|---|
| **HE10** | **No se rechaza** | KW p = 0,4685 |
| **HE11** | **No se respalda** | Sin conjunción impacto+diferencias en E1 (KPI-gains) |

### 5.5.3 Hipótesis específicas OE.2 (HE20 / HE21)

**Formulación nula.** HE20.- El algoritmo MADRL no impacta de manera estadísticamente significativa en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E2.

**Formulación alternativa.** HE21.- El algoritmo MADRL impacta de manera estadísticamente significativa en las emisiones de CO₂ en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E2.

| Hipótesis | Decisión | Fundamento |
|---|---|---|
| **HE20** | **No se rechaza** | KW p = 0,7648 |
| **HE21** | **No se respalda** | Sin impacto vs cero tras Holm; Friedman marginal; 0/15 KPI mejorados |

### 5.5.4 Hipótesis específicas OE.3 (HE30 / HE31)

**Formulación nula.** HE30.-El algoritmo MADRL no impacta de manera estadísticamente significativa en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y no existen diferencias significativas entre los algoritmos evaluados en el escenario E3.

**Formulación alternativa.** HE31.-El algoritmo MADRL impacta de manera estadísticamente significativa en los costos energéticos en comunidades inteligentes de la ciudad de Iquitos, y existen diferencias significativas entre los algoritmos evaluados en el escenario E3.

| Hipótesis | Decisión | Fundamento |
|---|---|---|
| **HE30** | **No se rechaza** | KW p = 0,7357 |
| **HE31** | **No se respalda** | MAAC gana costos/TOPSIS/4/4 descriptivo; KPI-gains E3 sin omnibus ni impacto vs cero tras Holm |

### 5.5.5 Por qué MAAC (costos / TOPSIS / 4/4) no respalda HE11–HE31

Esta aparente tensión **no es un error de cálculo**: ambos planos se calculan sobre los **mismos 50 episodios Drive** en `outputs/`, pero miden cosas distintas (Cap. 4). TOPSIS/4/4 = **descriptivo**; HE = **KPI-gains** (impacto significativo **y** diferencias). Detalle en artefactos `problemas_objetivos_hipotesis/`.

### 5.5.6 Cumplimiento de objetivos (veredicto)

**Tabla 5.12.** Cumplimiento OG/OE.

| Objetivo | Líder descriptivo (§5.2) | Inferencia / H (§5.3–§5.5) | Cumplimiento |
|---|---|---|---|
| **OE.1** | MAAC (KPI-gain); MATD3 (flex distrito) | HE10 no rechazada; HE11 no respaldada | Cumplido descriptivo-exploratorio |
| **OE.2** | **MATD3** | HE20 no rechazada; HE21 no respaldada | Cumplido descriptivo; HE21 no establecida |
| **OE.3** | **MAAC** | HE30 no rechazada; HE31 no respaldada | Cumplido descriptivo; HE31 no establecida |
| **OG** | MATD3 (`best_madrl` 0,6667) / MAAC (score escenario) | H0G rechazo exploratorio; H1G exploratoria | Cumplido; sin ganador único |

Fuente: `decisiones_problemas_objetivos_hipotesis.csv` / `respuesta_problemas_objetivos_hipotesis.md`.

---

## 5.6 Discusión de resultados

1. **Separación de planos.** El §5.2 responde descriptivamente al PG y a PE.1–PE.3 y documenta OG/OE.1–OE.3; el §5.3 cuantifica incertidumbre; el §5.5 decide H0G/H1G y HE10–HE31 con el texto exacto del Cap. 1; el §5.4 integra gráficas de performance y capas complementarias sin alterar el veredicto.
2. **Puerta paramétrica.** La no normalidad obliga a no paramétrico; ANOVA/t no son veredicto.
3. **Trade-off multiobjetivo.** MATD3 lidera flexibilidad física de distrito y CO₂; MAAC lidera costos, medianas KPI-gain en E1/E3, ranking 4/4 evaluate_v2 y TOPSIS multicriterio. No hay dominancia Pareto, coherente con la pregunta del PG sobre “el mejor desempeño a nivel global”.
4. **H1G exploratoria ≠ HE específicas.** Friedman global (p=0,0096) y impacto agregado vs baseline respaldan H1G de forma exploratoria sobre la gestión coordinada integrada; **no** sustituyen HE11/HE21/HE31 (§5.5.5).
5. **Corrección conceptual MAAC/TOPSIS.** Ganar costos / TOPSIS / 4/4 identifica al mejor relativo; **no** implica respaldar HE31 (ni HE11/HE21). Inventar H1 específicas por ranking contradiría Cap. 4 (KPI-gains = unidad de HE).
6. **Capas de evidencia.** (a) KPI-gains HE canónicos 3×3; (b) evaluate_v2 4/4 descriptivo con HAPPO; (c) `best_madrl` 3×3 = MATD3 0,6667; (d) batería episódica y análisis cuantitativo por edificio = complementarios; (e) baseline v2 contextualiza scores absolutos.
7. **Limitaciones.** Semilla de campaña = 0; HAPPO 49/50 ep (KPIs finales recuperados, peor 4/4); episodios correlacionados; n KPI por eje 12/5/9. Multi-semilla real queda como trabajo futuro.

---

## 5.7 Catálogo de artefactos `outputs/` → Cap. 5

### 5.7.1 Corrida canónica `madrl_v3_20260627_164047/`

| Subruta | Contenido | Acápite |
|---|---|---|
| `MATD3\|MAAC\|MASAC\|HAPPO/{E1,E2,E3}/figures/*.png` | **129 PNG** performance/KPI por job (catálogo completo embebido en Word) | §5.4.1-bis |
| `resumen_comparativo/performance_comparison/` | **4 PNG** resumen MADRL (distrito+edificio E1–E3) embebidos | §5.4.1-bis |
| `madrl_multicriteria_selection/figures/` | **3 PNG** Pareto/learning/degradación embebidos (MC.1–MC.3) | §5.4.1-bis |
| `.../figures/tables/*` | CSV+MD por job (core, OE, episode, efficiency) | §5.4.1 |
| `evaluation/*.csv` | `all_kpis`, `E1_OE1_kpis`, `E2_OE2_kpis`, `E3_OE3_kpis`, gains | §5.2 |
| `resumen_comparativo/figuras_drive_reales/comparativo/` | 17 PNG comparativos E1–E3 + ranking | §5.1–§5.4 |
| `resumen_comparativo/multiobjetivo/` | 23 PNG distrito/edificio | §5.2 / §5.4.3 |
| `resumen_comparativo/citylearn_v2_baseline/` | 12 PNG + rankings vs RBC | §5.4.2 |
| `resumen_comparativo/estadistica/` | Matrices HE, Wilcoxon, scores, KPIs | §5.2–§5.5 |
| `resumen_comparativo/estadistica/analisis_cuantitativo_completo_50_episodios/` | Informe cuantitativo + TOPSIS 4/4 + CSV | §5.2 / §5.4 |
| `resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` | Respuestas PE/OE/HE | §5.5 |

### 5.7.2 `_drive_madrl/`

| Subruta | Contenido | Acápite |
|---|---|---|
| `kpi_recalc_20260728/` | Ranking 4/4, KPI-gains, episode metrics, evaluate_v2 full | §5.2 / Tabla 5.5 / 5.9 |
| `gdrive_..._objective_analysis/figures/` | 22 PNG (ε², boxplots, heatmaps, convergencia, timeseries) | §5.3 / §5.4 |
| `full_data/{ALGO}/{E}/data/` | timeseries, trace, building_kpis (12 tratamientos) | §5.1 / Anexo datos |
| `full_data/analysis_real_drive/` | 9 PNG + tablas de comportamiento | §5.4.3 |

### 5.7.3 Otras carpetas

| Carpeta | Figuras / tablas clave | Acápite |
|---|---|---|
| `madrl_multicriteria_selection/` | Pareto, learning_curves, degradation; topsis_ranking | §5.4.4 |
| `comparison_citylearn_v2_vs_v3_madrl/` | 12 PNG + 12 CSV + 9 MD | §5.4.2 |
| `citylearn_v2_original_benchmark/` | ~69 PNG controles RBC | §5.4.2 |
| `madrl_nonparametric_battery*` | Reportes MD + JSON | §5.4.5 |
| `thesis_objective_evidence/` | 27 CSV/MD evidencia Cap. 1↔5 | §5.2–§5.5 |
| `citylearn_v3_madrl_full_..._v4/` | Pipeline histórico ~5 ep | §5.4.6 |

### 5.7.4 Índice compacto de figuras del capítulo

| Fig. | Tema | Fuente principal |
|---|---|---|
| 5.1–5.3 | Ranking / cobertura / global | `figuras_drive_reales`, `resumen_comparativo` |
| 5.4 | OE.1 flexibilidad | comparativo E1 + multiobjetivo + Drive oe1 |
| 5.5 | OE.2 CO₂ | comparativo E2 + heatmaps |
| 5.6 | OE.3 costos | comparativo E3 + heatmaps |
| 5.7 | Inferencia (ε², boxplot, Holm) | `_drive_madrl/.../figures` |
| 5.8–5.9 | Convergencia | comparativo + estabilización Drive |
| 5.10 | KPIs performance por MADRL (ejemplos) | `{ALGO}/{E}/figures` |
| 5.11 | Series distrito + traces | `figuras_drive_reales/comparativo` |
| 5.12 | vs CityLearn v2 | `comparison_citylearn_v2_vs_v3_madrl` |
| 5.13 | Multiobjetivo / EV / checkpoints | multiobjetivo + Drive analysis |
| 5.14 | TOPSIS/AHP | `madrl_multicriteria_selection/figures` |

### Estado del capítulo

**Actualizado 2026-07-29** con formulaciones exactas PG/PE/OG/OE/H0G–HE31 del Cap. 1; integración de **todas las carpetas `outputs/`** en acápites §5.1–§5.7; figuras 5.1–5.14 embebidas (rutas a PNG reales); tablas 5.1–5.12 con métricas y KPIs de performance por MADRL. Numerales: descriptivos (§5.2) → inferenciales (§5.3) → otros/performance (§5.4) → contrastación (§5.5) → discusión (§5.6) → catálogo (§5.7). Evidencia anclada a Drive 2026-07-28 y estadística canónica. **No se inventaron p-valores ni scores.**
