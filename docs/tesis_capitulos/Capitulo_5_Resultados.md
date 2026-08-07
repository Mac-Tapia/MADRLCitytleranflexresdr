# Capítulo 5. Resultados y Contrastación de Hipótesis

> **Documento de tesis doctoral — resultados.** Corrida canónica Colab/Drive `madrl_v3_20260627_164047` (**50 episodios**; espejo local `outputs/madrl_v3_20260627_164047/` + `outputs/_drive_madrl/kpi_recalc_20260728/`). **Fuente única de contrastación HE/H0G:** `resumen_comparativo/estadistica/problemas_objetivos_hipotesis/` (Capa A). Protocolo Cap. III: Shapiro–Wilk → **Friedman pareado + Kendall W + Wilcoxon/Holm** (principal); Kruskal–Wallis / Mann–Whitney U solo como análisis exploratorio cuando no hay independencia real. α = 0,05. **No inventar p-valores.** Auditoría de contradicciones: `docs/AUDITORIA_CAP5_CONTRADICCIONES_STATS_2026-08-06.md`. PG/PE/OG/OE/H se citan con el texto exacto del Cap. 1. Resumen, Abstract y Cap. VI se actualizarán **después** de cerrar este capítulo.

---

## 5.0 Mapa de lectura

| # | Bloque | Contenido |
|---:|---|---|
| 1 | **§5.1** | Marco experimental, C1–C5, artefactos canónicos |
| 2 | **§5.2** | **OE.1** — descriptivo + inferencial + C3–C5 + HE10/HE11 |
| 3 | **§5.3** | **OE.2** — misma secuencia + HE20/HE21 |
| 4 | **§5.4** | **OE.3** — misma secuencia + HE30/HE31 |
| 5 | **§5.5** | **OG** — integración, Pareto, TOPSIS (complementario), H0G/H1G |
| 6 | **§5.6** | Contrastación consolidada HG/HE |
| 7 | **§5.7** | Discusión + auditoría de coherencia PG–OG–HG / PE–OE–HE |

**Regla.** El líder descriptivo no sustituye la decisión inferencial. TOPSIS y evaluate_v2 4/4 son descriptivos.

**Cadena vertical.** PG ↔ OG ↔ H0G/H1G; PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); PE.3 ↔ OE.3 ↔ HE30/HE31 (E3).

---

## 5.1 Marco experimental y criterios de determinación del efecto

El diseño es factorial cuasiexperimental **4 × 3** (algoritmo × escenario) sobre una comunidad de **17 edificios** del SEAI–Iquitos, simulada en CityLearn v2 con capa MADRL v3 (Dec-POMDP + CTDE). Tratamientos: HAPPO, MASAC, MATD3 y MAAC en escenarios E1 (flexibilidad), E2 (CO₂) y E3 (costos). Baseline de contraste: CityLearn v2 (`baseline` / controles RBC). Nivel de significancia α = 0,05.

**Unidad de observación (HE):** KPI-gain orientado por KPI, filtrado al escenario del objetivo. **Unidad experimental:** tratamiento algoritmo × escenario, **seed = 0** (semilla única). Los episodios de una sola corrida **no** son réplicas experimentales independientes ni permiten afirmar robustez multisemilla.

**Tabla 5.1.** Cobertura de episodios y uso inferencial.

| Algoritmo | E1 | E2 | E3 | KPI-gains finales | Uso |
|---|---:|---:|---:|---|---|
| **MATD3** | 50 | 50 | 50 | Sí | Descriptivo + inferencial canónico |
| **MAAC** | 50 | 50 | 50 | Sí | Descriptivo + inferencial canónico |
| **MASAC** | 50 | 50 | 50 | Sí | Descriptivo + inferencial canónico |
| **HAPPO** | 49 | 49 | 49 | No (comparables) | Solo descriptivo 4/4; **excluido de HE** |

**Tabla 5.2.** Operacionalización por objetivo.

| Objetivo | Escenario | VD | Métricas primarias | Pesos (flex/CO₂/costo) |
|---|---|---|---|---|
| **OE.1** | E1 | Flexibilidad | flex_composite, peak, ramping, KPI-gains (n=12) | 0,70 / 0,15 / 0,15 |
| **OE.2** | E2 | Emisiones CO₂ | carbon_emissions_delta, KPI-gains (n=5) | 0,15 / 0,70 / 0,15 |
| **OE.3** | E3 | Costos | electricity_cost_delta, KPI-gains (n=9) | 0,25 / 0,15 / 0,60 |
| **OG** | E1–E3 | Coordinación | score `best_madrl`; KPI-gains GLOBAL (n=26) | — |

### 5.1.1 Criterios C1–C5 (cumplimiento completo)

| Id | Criterio | Medida / prueba | Rol |
|---|---|---|---|
| **C1** | Efecto frente al baseline | Wilcoxon KPI-gains vs cero + Holm | Inferencial HE |
| **C2** | Diferencias entre algoritmos | **Friedman + Kendall W + Wilcoxon/Holm** (principal); KW/MWU exploratorio | Inferencial HE |
| **C3** | KPI distritales por eje | flex_composite / ΔCO₂ / Δcosto | Descriptivo distrito |
| **C4** | KPI por edificio | 17 edificios × E1/E2/E3 | Descriptivo edificio |
| **C5** | Actuación BESS / EV-V2G / cargas desplazables | throughput BESS, éxito EV, inventario | Atribuibilidad |

### 5.1.2 Artefactos canónicos

| Plano | Naturaleza | Artefacto |
|---|---|---|
| KPI-gains → HE | **Inferencial canónico** | `.../estadistica/problemas_objetivos_hipotesis/` |
| evaluate_v2 4/4 | Descriptivo | `_drive_madrl/kpi_recalc_20260728/tables/ranking_oe_scores.csv` |
| `best_madrl` 3×3 | Descriptivo | `.../best_madrl_report.json` |
| TOPSIS/AHP | Descriptivo complementario | `madrl_multicriteria_selection/topsis_ranking.csv` |
| Auditoría de capas | Meta | `docs/AUDITORIA_CAP5_CONTRADICCIONES_STATS_2026-08-06.md` |

**No se usan como HE:** `analisis_estadistico_madrl.csv` (escenarios poolados), batería episódica (`madrl_nonparametric_battery/`), ni `analisis_cuantitativo_completo_50_episodios/` como veredicto de hipótesis.

---

## 5.2 OE.1 — Efecto sobre la flexibilidad energética

**PE.1.** ¿En qué medida el algoritmo MADRL impacta en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos, y cuál de los algoritmos presenta el mejor desempeño en el escenario E1?

**OE.1.** Determinar el impacto de los algoritmos MADRLs en la flexibilidad energética en comunidades inteligentes de la ciudad de Iquitos e identificar cuál de los algoritmos presenta el mejor desempeño en el escenario E1.

### 5.2.1 Estadística descriptiva (KPI-gains y distrito)

**Tabla 5.3.** Descriptivos KPI-gains OE.1/E1 (n = 12 KPI por algoritmo; fuente: `descriptivos_kpi_gains_por_problema.csv`).

| Algoritmo | Media gain | Mediana gain | KPI mejorados / no | Lectura |
|---|---:|---:|---|---|
| **MAAC** | −0,0888 | **−0,00119** | 5 / 7 | Mejor mediana (menos deterioro) |
| MATD3 | −0,0868 | −0,00289 | 5 / 7 | Segundo |
| MASAC | −0,2621 | −0,01363 | 2 / 10 | Peor mediana |
| HAPPO | — | — | — | Sin KPI-gains finales |

(1) Las medianas son ≤ 0. (2) Representan deterioro relativo al baseline en la métrica de gain orientada. (3) No se decide aún significancia. (4) Mejor desempeño descriptivo por mediana KPI-gain: **MAAC**.

**Tabla 5.4.** KPIs físicos de distrito E1 (menor = mejor en flex_composite; fuente: `district_objectives_by_algorithm.csv` / ranking 4/4).

| Algoritmo | flex_composite | peak_average | ramping_average | Score OE1 (4/4) |
|---|---:|---:|---:|---:|
| **MATD3** | **1,0009** | 1,0081 | 1,0012 | **1,0000** |
| MAAC | 1,0124 | 1,0307 | 1,0110 | 0,8951 |
| MASAC | 1,0286 | 1,0851 | 1,0220 | 0,7479 |
| HAPPO | 1,1105 | — | — | 0,0000 |

(1) MATD3 obtiene el menor `flex_composite`. (2) Es mejora descriptiva de flexibilidad física de distrito frente a MAAC/MASAC/HAPPO. (3) Sin contraste inferencial sobre este KPI físico en la Capa A. (4) Mejor MADRL **descriptivo físico**: **MATD3**; mejor **KPI-gain**: **MAAC**.

### 5.2.2 Shapiro–Wilk

Fuente: `normalidad_shapiro_por_problema.csv` (n = 12).

| Algoritmo | W | p | Normalidad |
|---|---:|---:|---|
| MAAC | 0,7152 | 0,001184 | Rechazada |
| MASAC | 0,5997 | 1,066×10⁻⁴ | Rechazada |
| MATD3 | 0,7160 | 0,001208 | Rechazada |

(1)–(2) Se rechaza normalidad en los tres grupos. (3) Se activa exclusivamente la batería no paramétrica. (4) No identifica ganador.

### 5.2.3 Efecto frente al baseline (C1)

Fuente: `impacto_vs_baseline_wilcoxon.csv`.

| Algoritmo | Mediana gain | p-Holm | Dirección | Decisión |
|---|---:|---:|---|---|
| MAAC | −0,00119 | 0,6025 | desfavorable | impacto no detectado |
| **MASAC** | −0,01363 | **0,0483** | **desfavorable** | impacto detectado (deterioro) |
| MATD3 | −0,00289 | 0,6025 | desfavorable | impacto no detectado |

(1) Solo MASAC alcanza significancia tras Holm. (2) El efecto es deterioro, no mejora. (3) Magnitud: p-Holm = 0,0483. (4) Ningún algoritmo muestra mejora significativa vs baseline en OE.1.

### 5.2.4 Prueba global entre algoritmos (C2)

Fuente: `pruebas_omnibus_problemas_objetivos.csv`.

| Prueba | Estadístico | p | Efecto | Rol |
|---|---:|---:|---|---|
| **Friedman** (principal) | χ² = 5,5897 | **0,0611** | Kendall W = 0,2329 (débil) | No se rechaza igualdad pareada |
| Kruskal–Wallis (exploratorio) | H = 1,5164 | 0,4685 | ε² = 0 | Sensibilidad; n.s. |

(1) Friedman p = 0,0611. (2) No hay diferencias globales significativas al α = 0,05. (3) W = 0,2329 indica concordancia débil. (4) No hay superioridad estadística inter-algoritmo en OE.1.

### 5.2.5 Post hoc Holm

Wilcoxon pareado (`comparaciones_wilcoxon_pareado_holm.csv`): MAAC–MASAC p-Holm = 0,110; MAAC–MATD3 = 0,514; MASAC–MATD3 = 0,338 — ninguno significativo. MWU exploratorio: todos p-Holm = 0,850; Cliff’s δ ∈ {0,24; −0,06; −0,26}.

### 5.2.6 KPI por edificio (C4) y recursos (C5)

A nivel de los 17 edificios, el ranking de distrito por escenario sitúa a **MATD3** primero en E1 (`district_ranking_by_scenario.csv`). Throughput BESS E1 (`battery_throughput_total`, `E1_OE1_kpis.csv`): HAPPO 8,85×10⁶; MASAC 6,24×10⁵; MAAC 3,41×10⁵; MATD3 8,49×10³. Éxito EV E1: HAPPO 0,527; MATD3 0,439; MAAC 0,042; MASAC 0,039. (1)–(2) Hay actuación heterogénea de BESS/EV. (3) C5 documenta atribuibilidad, no decide HE. (4) MATD3 combina mejor flex física con éxito EV intermedio; MAAC/MASAC priorizan menos el éxito EV.

### 5.2.7 Identificación del mejor MADRL y decisión HE10/HE11

- **Mejor desempeño descriptivo OE.1:** MAAC (mediana KPI-gain); MATD3 (flex_composite distrito / score OE1 4/4).
- **Nivel de evidencia inferencial:** no hay superioridad estadísticamente significativa entre algoritmos; no hay mejora significativa vs baseline salvo deterioro de MASAC.
- **HE10:** **no se rechaza**. **HE11:** **no se respalda**.
- **Respuesta a OE.1:** el efecto MADRL sobre flexibilidad se caracteriza descriptivamente (liderazgo mixto MAAC/MATD3) y se contrastea exploratoriamente; **no** se establece impacto ni diferenciación estadísticamente significativa conjunta.

---

## 5.3 OE.2 — Efecto sobre las emisiones de CO₂

**PE.2 / OE.2.** Textos exactos del Cap. 1 (escenario E2).

### 5.3.1 Descriptivos

**Tabla 5.5.** KPI-gains OE.2/E2 (n = 5).

| Algoritmo | Media gain | Mediana gain | Mejorados / no |
|---|---:|---:|---|
| **MATD3** | −0,4101 | **−0,0421** | 0 / 5 |
| MAAC | −0,4148 | −0,0470 | 0 / 5 |
| MASAC | −0,4171 | −0,0516 | 0 / 5 |

**ΔCO₂ distrito E2 (kg; menor = mejor):** MATD3 **23 070**; MAAC 70 654; MASAC 77 649; HAPPO 1 431 341. Score OE2 4/4: MATD3 1,0000; MAAC 0,9662; MASAC 0,9612; HAPPO 0.

(1) Medianas gain negativas y 0/5 KPI mejorados. (2) Deterioro en gains; en delta físico MATD3 minimiza el incremento de emisiones relativo a los pares. (3) Sin significancia aún. (4) Mejor descriptivo: **MATD3**.

### 5.3.2 Shapiro–Wilk (n = 5)

MAAC W = 0,6993 p = 0,009419; MASAC W = 0,6999 p = 0,009548; MATD3 W = 0,7012 p = 0,009848 — normalidad rechazada.

### 5.3.3 Impacto vs baseline (C1)

Los tres algoritmos: p-Holm = **0,1875** (n.s.), dirección desfavorable. (1)–(3) No se detecta impacto significativo tras Holm. (4) Sin mejora vs baseline.

### 5.3.4 Prueba global (C2)

| Prueba | Estadístico | p | Efecto | Rol |
|---|---:|---:|---|---|
| **Friedman** | χ² = 6,0000 | **0,0498** | Kendall W = **0,6000** | Señal pareada débil |
| KW (exploratorio) | H = 0,5364 | 0,7648 | ε² = 0 | n.s. |

(1) Friedman p = 0,0498. (2) Existe diferencia pareada global débil-moderada (W = 0,60). (3) Sin impacto vs cero ni pares Holm, **no** habilita HE21. (4) Mejor descriptivo MATD3; **sin** superioridad inferencial confirmada por post hoc.

### 5.3.5 Post hoc Holm

Wilcoxon: los tres pares p-Holm = 0,307. MWU: p-Holm = 1,000. Ningún par significativo.

### 5.3.6 Edificios (C4) y recursos (C5)

Ranking distrito E2: **MATD3** primero. Éxito EV E2: HAPPO 0,492; MATD3 0,364; MAAC/MASAC ≈ 0,041.

### 5.3.7 Mejor MADRL y HE20/HE21

- **Mejor descriptivo OE.2:** **MATD3** (mediana gain, ΔCO₂, score OE2).
- **Evidencia inferencial:** ventaja descriptiva; Friedman marginal sin post hoc ni impacto vs cero → **no** superioridad estadística establecida.
- **HE20:** **no se rechaza**. **HE21:** **no se respalda**.
- **Respuesta a OE.2:** se identifica a MATD3 como mejor desempeño descriptivo; el efecto inferencial conjunto no alcanza el umbral de la hipótesis alternativa.

---

## 5.4 OE.3 — Efecto sobre los costos energéticos

**PE.3 / OE.3.** Textos exactos del Cap. 1 (escenario E3).

### 5.4.1 Descriptivos

**Tabla 5.6.** KPI-gains OE.3/E3 (n = 9).

| Algoritmo | Media gain | Mediana gain | Mejorados / no |
|---|---:|---:|---|
| **MAAC** | −0,2278 | **−0,00268** | 1 / 8 |
| MATD3 | −0,2259 | −0,00918 | 1 / 8 |
| MASAC | −0,2355 | −0,01403 | 1 / 8 |

**Δcosto distrito E3 (EUR; menor = mejor):** MAAC **9 515**; MASAC 19 793; MATD3 44 399; HAPPO 106 828. Score OE3 4/4: MAAC **1,0000**; MASAC 0,8944; MATD3 0,6415; HAPPO 0. TOPSIS (complementario): MAAC C\* = **0,9827**.

(1)–(2) MAAC minimiza costo de distrito y mediana gain. (3) Pendiente inferencia. (4) Mejor descriptivo: **MAAC**.

### 5.4.2 Shapiro–Wilk (n = 9)

MAAC W = 0,5575 p = 3,029×10⁻⁵; MASAC W = 0,5879 p = 6,905×10⁻⁵; MATD3 W = 0,5464 p = 2,246×10⁻⁵ — normalidad rechazada.

### 5.4.3 Impacto vs baseline (C1)

MAAC/MASAC p-Holm = 0,0781; MATD3 p-Holm = 0,0586 — todos n.s. tras Holm; dirección desfavorable.

### 5.4.4 Prueba global (C2)

| Prueba | Estadístico | p | Efecto | Rol |
|---|---:|---:|---|---|
| **Friedman** | χ² = 3,4286 | **0,1801** | W = 0,1905 | n.s. |
| KW (exploratorio) | H = 0,6138 | 0,7357 | ε² = 0 | n.s. |

### 5.4.5 Post hoc Holm

Wilcoxon: p-Holm ∈ {0,527; 1,000; 1,000}. MWU: p-Holm = 1,000. **No** citar el p = 0,0333 de capas pooladas (Capa B) como resultado Holm canónico.

### 5.4.6 Edificios (C4) y recursos (C5)

Ranking distrito E3: **MAAC** primero. Éxito EV E3: HAPPO 0,503; MATD3 0,482; MAAC/MASAC ≈ 0,041.

### 5.4.7 Mejor MADRL y HE30/HE31

- **Mejor descriptivo OE.3:** **MAAC** (KPI-gain, Δcosto, score 4/4, TOPSIS).
- **Evidencia inferencial:** liderazgo descriptivo **sin** significancia omnibus ni impacto vs cero tras Holm.
- **HE30:** **no se rechaza**. **HE31:** **no se respalda**.
- **Respuesta a OE.3:** MAAC es el algoritmo de mejor desempeño descriptivo en costos; la ventaja **no** es inferencialmente concluyente.

---

## 5.5 OG — Efecto integrado y mejor desempeño global

**PG / OG.** Textos exactos del Cap. 1.

### 5.5.1 Integración descriptiva y trade-offs

**Tabla 5.7.** Ranking `best_madrl` 3×3 (sin HAPPO).

| Rango | Algoritmo | Score global | OE.1 | OE.2 | OE.3 |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | **MATD3** | **0,6667** | 1,0000 | 1,0000 | 0,0000 |
| 2 | MAAC | 0,5706 | 0,5837 | 0,1282 | 1,0000 |
| 3 | MASAC | 0,2351 | 0,0000 | 0,0000 | 0,7054 |

**Tabla 5.8.** Ranking evaluate_v2 4/4 (descriptivo).

| Rango | Algoritmo | Score global |
|:---:|---|:---:|
| 1 | **MAAC** | **0,9538** |
| 2 | MATD3 | 0,8805 |
| 3 | MASAC | 0,8679 |
| 4 | HAPPO | 0,0000 |

Trade-off: MATD3 lidera flexibilidad física y CO₂; MAAC lidera costos, TOPSIS y 4/4. Frente de Pareto = {MAAC, MASAC, MATD3}. No hay dominador único.

### 5.5.2 TOPSIS (complementario, no sustituye HE)

Fuente: `topsis_ranking.csv`. MAAC C\* = **0,9827**; MASAC 0,5656; MATD3 0,3074. AHP coincide en ganador MAAC (CR ≈ 0,003). **TOPSIS no respalda HE ni H1G por sí solo.**

### 5.5.3 Inferencia GLOBAL (Capa A, n = 26)

Shapiro: normalidad rechazada (p ≤ 2,6×10⁻⁶). Impacto vs 0 (Holm): MAAC p = 0,00233; MASAC p = 1,55×10⁻⁴; MATD3 p = 0,00293 — los tres **significativos en dirección desfavorable**. Friedman χ² = **9,2911**, p = **0,0096**, Kendall W = 0,1787. KW exploratorio H = 1,8108, p = 0,4044. Wilcoxon post hoc: solo MAAC–MASAC p-Holm = **0,0172**.

(1) Friedman global significativo. (2) Hay diferenciación agregada, con impacto agregado desfavorable vs baseline. (3) W débil (0,18); un solo par Holm-significativo. (4) **Sin ganador global único**: score escenario MAAC; mediana robusta GLOBAL MATD3 (−0,00694).

### 5.5.4 Decisión H0G / H1G

- **H0G:** **se rechaza de forma exploratoria**.
- **H1G:** **se respalda de forma exploratoria** (sin ganador único; **no** implica HE11 ∧ HE21 ∧ HE31).
- **Mejor compromiso global descriptivo:** depende del plano (`best_madrl` → MATD3; 4/4/TOPSIS → MAAC). **No** hay superioridad estadística global concluyente de un único MADRL.

---

## 5.6 Contrastación consolidada de hipótesis

**Tabla 5.9.** Resumen HG / HE (Capa A; α = 0,05).

| Hip. | Efecto vs baseline (Holm) | Prueba global (Friedman) | χ² | p | Kendall W | Post hoc Holm | Mejor descriptivo | Decisión |
|---|---|---|---:|---:|---:|---|---|---|
| **H0G/H1G** | Tres alg. impacto desfavorable sig. | GLOBAL | 9,2911 | 0,0096 | 0,1787 | MAAC–MASAC 0,0172 | MAAC score / MATD3 mediana | **Se rechaza H0G**; H1G exploratoria; sin ganador único |
| **HE10/HE11** | Solo MASAC deterioro (0,0483) | OE1 | 5,5897 | 0,0611 | 0,2329 | n.s. | MAAC (gain) / MATD3 (flex) | **No se rechaza HE10**; no se respalda HE11 |
| **HE20/HE21** | Ninguno (0,1875) | OE2 | 6,0000 | 0,0498 | 0,6000 | n.s. | **MATD3** | **No se rechaza HE20**; no se respalda HE21 |
| **HE30/HE31** | Ninguno (≥0,0586) | OE3 | 3,4286 | 0,1801 | 0,1905 | n.s. | **MAAC** | **No se rechaza HE30**; no se respalda HE31 |

KW exploratorio: OE1 p = 0,4685; OE2 p = 0,7648; OE3 p = 0,7357; GLOBAL p = 0,4044. No se utiliza la fórmula «se acepta H₀».

---

## 5.7 Discusión de resultados

### 5.7.1 Contrastación con la literatura

1. **Flexibilidad comunitaria y CityLearn.** Los resultados de OE.1 —liderazgo descriptivo mixto y ausencia de HE11— son coherentes con la dificultad de control multiagente en edificios *grid-interactive* reportada por Nweye et al. (2022, 2023b, 2024): la coordinación de DER no garantiza mejoras unívocas en todos los KPI de flexibilidad bajo una sola semilla.
2. **Algoritmos MADRL.** El perfil de MATD3 en CO₂/flex física y de MAAC en costos dialoga con las familias actor-crítico multiagente (Iqbal & Sha, 2019; Kuba et al., 2021; Zhong et al., 2023) y con SAC/MASAC en entornos energéticos (Haarnoja et al., 2018; Gao et al., 2023): distintos sesgos de aprendizaje producen trade-offs multiobjetivo, no un dominador Pareto.
3. **Carbon-aware / precios / BESS.** La disociación entre ΔCO₂ (MATD3) y Δcosto (MAAC) refuerza la necesidad de señales de carbono y tarifa TOU explícitas (Nweye et al., 2024; Nweye & Nagy, 2024b). El throughput BESS heterogéneo (C5) muestra que mayor actuación no implica mejor KPI-gain.
4. **Rigor estadístico en RL.** La puerta Shapiro → no paramétrico, el rechazo a tratar episodios como réplicas independientes y la distinción descriptivo/inferencial siguen a Agarwal et al. (2021), Demšar (2006) y las recomendaciones de Cap. III alineadas con Colas et al. (2019) y Patterson et al. (2024) sobre evaluación robusta y reporte de incertidumbre.

### 5.7.2 Limitaciones

Semilla única; HAPPO sin KPI-gains HE; n KPI 12/5/9; impacto agregado GLOBAL desfavorable; capas B/C/D no deben mezclarse con A.

### 5.7.3 Auditoría de coherencia PG–OG–HG / PE–OE–HE

| Cadena | ¿Efecto respondido? | ¿Mejor MADRL identificado? | Nivel |
|---|---|---|---|
| **PG → OG → H0G/H1G** | Sí (efecto integrado exploratorio; H0G rechazada exploratoria) | Parcial: sin ganador único (MATD3 `best_madrl` vs MAAC 4/4/TOPSIS) | Descriptivo + inferencial exploratorio |
| **PE.1 → OE.1 → HE10/HE11** | Sí (efecto no significativo conjunto; HE10 no rechazada) | Sí descriptivo (MAAC gain / MATD3 flex); **no** inferencial | Descriptivo |
| **PE.2 → OE.2 → HE20/HE21** | Sí (sin impacto vs 0; Friedman marginal sin post hoc) | Sí descriptivo (**MATD3**); **no** inferencial | Descriptivo |
| **PE.3 → OE.3 → HE30/HE31** | Sí (sin omnibus ni impacto Holm) | Sí descriptivo (**MAAC**); **no** inferencial | Descriptivo |

**Veredicto de cierre Cap. V.** Los objetivos quedan respondidos en cuanto a *determinación del efecto* (con evidencia de no rechazo de las nulas específicas) y a *identificación del MADRL de mejor desempeño descriptivo* por eje; la superioridad estadísticamente significativa por eje **no** se establece. El Resumen, Abstract y Cap. VI deberán alinearse a este cierre en una fase posterior.

---

## 5.8 Catálogo breve de artefactos

| Artefacto | Uso |
|---|---|
| `problemas_objetivos_hipotesis/*.csv` | HE/H0G canónicos |
| `best_madrl_report.json` | Ranking 3×3 descriptivo |
| `kpi_recalc_20260728/tables/ranking_oe_scores.csv` | Ranking 4/4 |
| `madrl_multicriteria_selection/topsis_ranking.csv` | TOPSIS C\* = 0,9827 |
| `district_objectives_by_algorithm.csv` | C3 distrito |
| `docs/AUDITORIA_CAP5_CONTRADICCIONES_STATS_2026-08-06.md` | Capas y contradicciones |
