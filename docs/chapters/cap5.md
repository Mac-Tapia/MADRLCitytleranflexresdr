> **Resultados históricos retirados (propietario, 2026-11-01).** Las cifras inferenciales de este documento (p-valores, ganadores, rankings) vienen de corridas anteriores que ya no cuentan. La única fuente válida de cifras estadísticas será `tools/eval/build_campaign_statistical_report.py` sobre la campaña nueva (SPEC-009, módulo 4); hasta entonces no se citan.

# Capítulo 5. Resultados, Efectos Diferenciales y Desempeño Algorítmico

> **Documento de tesis — resultados.** Corrida canónica Colab/Drive `madrl_v3_20260627_164047` (espejo local `outputs/madrl_v3_20260627_164047/` + `outputs/_drive_madrl/kpi_recalc_20260728/`). **Fuente única de contrastación HE/H0G (Capa A):** `outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotesis/`. Protocolo Cap. III: Shapiro–Wilk → **Friedman pareado + Kendall W + Wilcoxon/Holm** (principal); Kruskal–Wallis / Mann–Whitney U exploratorio. α = 0,05. Semilla de campaña = 0. HAPPO excluido de la contrastación HE por ausencia de KPI-gains finales comparables. **No** se inventan p-valores; **no** se cita la Capa B (p = 0,0333) como veredicto Holm; **no** se usa reward como KPI físico. Auditoría de capas: `docs/AUDITORIA_CAP5_CONTRADICCIONES_STATS_2026-08-06.md`.

---

## 5.1 Auditoría inicial de resultados

La auditoría de integridad de la campaña canónica verifica tratamientos, episodios, semillas, cobertura, datos faltantes, igualdad de horizonte e integridad de artefactos.

**Tratamientos.** Diseño factorial cuasiexperimental 4 × 3: algoritmos HAPPO, MASAC, MATD3 y MAAC × escenarios E1 (flexibilidad), E2 (CO₂) y E3 (costos), sobre la comunidad inteligente heterogénea de 17 edificios del SEAI–Iquitos (CityLearn v2 + capa MADRL v3). Baseline de contraste: CityLearn v2 (`baseline` / controles RBC).

**Episodios y semillas.** Horizonte nominal de **50 episodios** por tratamiento. Semilla de campaña **seed = 0** (una sola semilla). Los episodios de una corrida **no** constituyen réplicas experimentales independientes ni permiten afirmar robustez multisemilla.

**Cobertura e igualdad de horizonte.**

| Algoritmo | E1 | E2 | E3 | KPI-gains finales (Capa A) | Uso en HE/H0G |
|---|---:|---:|---:|---|---|
| MATD3 | 50 | 50 | 50 | Sí | Descriptivo + inferencial |
| MAAC | 50 | 50 | 50 | Sí | Descriptivo + inferencial |
| MASAC | 50 | 50 | 50 | Sí | Descriptivo + inferencial |
| HAPPO | **49 + 1 post-resume** | **49 + 1 post-resume** | **49 + 1 post-resume** | **No** (KPI-gains finales comparables) | Curva descriptiva; **excluido de HE** |

**Datos faltantes y elegibilidad.** HAPPO conserva 49 episodios históricos más el episodio final post-resume, unidos por índice únicamente para reconstruir una curva descriptiva de 50 puntos. Esta unión no genera KPI-gains finales comparables; por ello HAPPO permanece fuera de Wilcoxon vs baseline, Friedman, post hoc Holm y decisiones HE10–HE31 / H0G–H1G. El trío MAAC–MASAC–MATD3 aporta cobertura 50/50 con KPI-gains. La cobertura episódica, la cobertura de KPI y la elegibilidad inferencial se reportan como propiedades distintas.

**Integridad.** La contrastación de hipótesis se ancla exclusivamente a Capa A (`descriptivos_kpi_gains_por_problema.csv`, `normalidad_shapiro_por_problema.csv`, `impacto_vs_baseline_wilcoxon.csv`, `pruebas_omnibus_problemas_objetivos.csv`, `comparaciones_wilcoxon_pareado_holm.csv`, `decisiones_problemas_objetivos_hipotesis.csv`). Rankings `best_madrl`, evaluate_v2 4/4 y TOPSIS son planos descriptivos complementarios y **no** sustituyen HE.

---

## 5.1-bis Entrenamiento canónico (curvas y eficiencia)

Esta subsección documenta el **entrenamiento** de la corrida `madrl_v3_20260627_164047` (seed = 0). La recompensa episódica es señal de aprendizaje; **no** sustituye los KPI físicos ni la contrastación HE de §5.3–§5.6. Los costos de evaluación distrital (OE.3) se reportan en **USD** (tarifas TOU 0,26/0,38 USD/kWh); las claves internas `*_eur` son etiquetas legacy.

**Tabla 5.1b.** Resumen de entrenamiento (retorno episódico; fuente: `training_efficiency.csv` por job).

| Algoritmo | Esc. | Episodios | Retorno ep. 0 | Retorno final | Pasos (último) |
|---|---|---:|---:|---:|---:|
| MATD3 | E1 | 50 | −108 570 | −93 382 | 8 760 |
| MATD3 | E2 | 50 | −80 105 | −80 417 | 8 760 |
| MATD3 | E3 | 50 | −84 649 | −83 495 | 8 760 |
| MAAC | E1 | 50 | −87 889 | −91 202 | 8 749 |
| MAAC | E2 | 50 | −76 217 | −78 497 | 8 749 |
| MAAC | E3 | 50 | −78 305 | −80 610 | 8 749 |
| MASAC | E1 | 50 | −92 493 | −87 682 | 8 748 |
| MASAC | E2 | 50 | −78 666 | −76 218 | 8 748 |
| MASAC | E3 | 50 | −80 906 | −78 282 | 8 748 |
| HAPPO | E1 | 49 | −105 169 | −94 432 | 8 760 |
| HAPPO | E2 | 49 | −80 876 | −72 760 | 8 760 |
| HAPPO | E3 | 49 | −84 822 | −77 867 | 8 760 |

*Nota.* La curva descriptiva de HAPPO combina 49 episodios históricos y un episodio post-resume; HAPPO queda fuera de HE porque no dispone de KPI-gains finales comparables. Las figuras de convergencia y eficiencia se insertan en el Word canónico (escenario primario por eje: MATD3–E1, MASAC–E2, MAAC–E3, HAPPO–E1; más curva multicriterio). Fuente PNG: `{ALGO}/{E}/figures/convergence_returns.png`, `learning_efficiency.png` y `outputs/madrl_multicriteria_selection/figures/learning_curves.png`.

---

## 5.2 Criterio cuantitativo de efecto

Se define el **efecto diferencial** como la conjunción de: (i) cambio frente a la línea base (KPI-gain orientado; valor positivo favorece al MADRL); (ii) significancia estadística (α = 0,05, con Holm cuando corresponde); (iii) magnitud del efecto (Kendall W, Cliff’s δ exploratorio); (iv) dirección (favorable / desfavorable); y (v) diferencia entre algoritmos (Friedman + Wilcoxon/Holm principal; KW/MWU exploratorio).

**Unidad primaria de HE:** KPI-gain orientado por KPI, filtrado al escenario del objetivo (OE.1/E1 n = 12; OE.2/E2 n = 5; OE.3/E3 n = 9; GLOBAL n = 26).

**Criterios C1–C5 (cumplimiento completo).**

| Id | Criterio | Medida / prueba | Rol |
|---|---|---|---|
| **C1** | Efecto frente al baseline | Wilcoxon KPI-gains vs cero + Holm | Inferencial HE |
| **C2** | Diferencias entre algoritmos | Friedman + Kendall W + Wilcoxon/Holm (principal); KW/MWU exploratorio | Inferencial HE |
| **C3** | KPI distritales por eje | flex_composite / ΔCO₂ / Δcosto | Descriptivo distrito |
| **C4** | Resultados por edificio | 17 edificios × E1/E2/E3 | Descriptivo edificio |
| **C5** | Actuación de recursos controlables | BESS, EV/V2G, cargas desplazables | Atribuibilidad |

El liderazgo descriptivo **no** sustituye la decisión inferencial. TOPSIS y evaluate_v2 4/4 **no** son pruebas de hipótesis.

---

## 5.3 OE.1 — Flexibilidad energética (E1)

**PE.1.** ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen efectos diferenciales sobre la flexibilidad energética (eje E1) y cuál presenta el mejor desempeño en la comunidad inteligente heterogénea de Iquitos?

**OE.1.** Determinar y cuantificar los efectos diferenciales de los algoritmos HAPPO, MASAC, MATD3 y MAAC sobre la flexibilidad energética (eje E1) e identificar el algoritmo de mejor desempeño en la comunidad inteligente heterogénea de Iquitos.

**HE10 / HE11** (etiquetas Cap. 1 / Capa A). HE10: no hay efectos diferenciales estadísticamente significativos sobre la flexibilidad en E1. HE11: al menos un algoritmo produce efecto diferencial estadísticamente significativo sobre la flexibilidad en E1.

### 5.3.1 Descriptivos

Fuente: `descriptivos_kpi_gains_por_problema.csv` (n = 12 KPI por algoritmo con cobertura completa).

| Algoritmo | Media gain | Mediana gain | Mejorados / no | Cobertura |
|---|---:|---:|---|---|
| MAAC | −0,0888 | **−0,00119** | 5 / 7 | Completa |
| MATD3 | −0,0868 | −0,00289 | 5 / 7 | Completa |
| MASAC | −0,2621 | −0,01363 | 2 / 10 | Completa |
| HAPPO | — | — | — | Sin KPI-gains finales |

Las medianas son ≤ 0 (deterioro relativo al baseline en la métrica de gain orientada). Mejor mediana descriptiva de KPI-gain: **MAAC**.

### 5.3.2 Shapiro–Wilk

Fuente: `normalidad_shapiro_por_problema.csv` (n = 12).

| Algoritmo | W | p | Normalidad |
|---|---:|---:|---|
| MAAC | 0,7152 | 0,001184 | Rechazada |
| MASAC | 0,5997 | 1,066×10⁻⁴ | Rechazada |
| MATD3 | 0,7160 | 0,001208 | Rechazada |

Se rechaza normalidad en los tres grupos con KPI-gains; se activa exclusivamente la batería no paramétrica.

### 5.3.3 Cambio frente a baseline

Las medianas de KPI-gain frente a cero son negativas (MAAC −0,00119; MATD3 −0,00289; MASAC −0,01363). El cambio observado es, en promedio de KPI, desfavorable respecto del baseline CityLearn v2. HAPPO no aporta KPI-gains finales para este contraste.

### 5.3.4 Prueba inferencial frente a baseline

Fuente: `impacto_vs_baseline_wilcoxon.csv` (C1).

| Algoritmo | Mediana gain | p-Holm | Dirección | Decisión |
|---|---:|---:|---|---|
| MAAC | −0,00119 | 0,6025 | desfavorable | impacto no detectado |
| MASAC | −0,01363 | **0,0483** | **desfavorable** | impacto detectado (deterioro) |
| MATD3 | −0,00289 | 0,6025 | desfavorable | impacto no detectado |

Solo MASAC alcanza significancia tras Holm, y en dirección de deterioro. Ningún algoritmo del trío muestra mejora significativa vs baseline en OE.1.

### 5.3.5 Comparación entre HAPPO, MASAC, MATD3 y MAAC

HAPPO se reporta solo en el plano descriptivo físico (C3–C5) por falta de KPI-gains HE. La comparación inferencial entre algoritmos se restringe a MAAC, MASAC y MATD3.

Fuente: `pruebas_omnibus_problemas_objetivos.csv` (C2).

| Prueba | Estadístico | p | Efecto | Rol |
|---|---|---:|---|---|
| **Friedman** (principal) | χ² = 5,5897 | **0,0611** | Kendall W = 0,2329 | No se rechaza igualdad pareada |
| Kruskal–Wallis (exploratorio) | H = 1,5164 | 0,4685 | ε² = 0 | Sensibilidad; n.s. |

No hay diferencias globales significativas al α = 0,05 entre el trío con KPI-gains.

### 5.3.6 Tamaño del efecto

Kendall W = **0,2329** (concordancia débil). Cliff’s δ exploratorio (MWU, `comparaciones_mwu_holm_problemas.csv`): MAAC–MASAC δ = 0,24; MAAC–MATD3 δ = −0,06; MASAC–MATD3 δ = −0,26. Las magnitudes no sostienen superioridad inferencial.

### 5.3.7 Post hoc

Wilcoxon pareado + Holm (`comparaciones_wilcoxon_pareado_holm.csv`): MAAC–MASAC p-Holm = 0,110; MAAC–MATD3 = 0,514; MASAC–MATD3 = 0,338 — todos n.s. MWU exploratorio: todos p-Holm = 0,850.

### 5.3.8 KPI distritales

Fuentes: `district_ranking_by_scenario.csv`, `district_kpis_4madrl.csv`, `E1_OE1_kpis.csv` / ranking 4/4.

| Algoritmo | flex_composite | peak_average | ramping_average | Score OE1 (4/4) |
|---|---:|---:|---:|---:|
| **MATD3** | **1,0009** | 1,0081 | 1,0012 | **1,0000** |
| MAAC | 1,0124 | 1,0307 | 1,0110 | 0,8951 |
| MASAC | 1,0286 | 1,0851 | 1,0220 | 0,7479 |
| HAPPO | 1,1105 | 1,3903 | 1,0839 | 0,0000 |

Menor `flex_composite` (mejor flexibilidad física de distrito): **MATD3**. Este KPI físico no se contrasta inferencialmente en Capa A.

### 5.3.9 Resultados de los 17 edificios

No se dispone en este capítulo de una tabla completa edificio-a-edificio con todos los KPI por algoritmo sin riesgo de inventar valores. La evidencia de C4 se resume desde:

- ranking distrital E1: **MATD3** primero (`outputs/.../kpi_rankings_drive50/district_ranking_by_scenario.csv`);
- desagregación por edificio: `outputs/.../kpi_rankings_drive50/building_kpis_4madrl.csv` (17 edificios × 4 algoritmos × escenarios).

El ranking de distrito sitúa a MATD3 como líder físico de flexibilidad; el detalle por edificio se remite a dicho CSV canónico.

### 5.3.10 BESS, EV/V2G y cargas desplazables

Throughput BESS E1 (`battery_throughput_total`): HAPPO **8,85×10⁶**; MASAC **6,24×10⁵**; MAAC **3,41×10⁵**; MATD3 **8,49×10³**. Éxito EV E1 (`ev_departure_success_rate`): HAPPO **0,527**; MATD3 **0,439**; MAAC **0,042**; MASAC **0,039**.

Mayor actuación BESS (HAPPO) no coincide con mejor `flex_composite` ni con KPI-gains favorables. C5 documenta atribuibilidad; **no** decide HE.

### 5.3.11 Identificación del MADRL de mejor desempeño

- **Descriptivo (KPI-gain):** MAAC (mediana −0,00119).
- **Descriptivo (flex_composite / score OE1 4/4):** MATD3 (1,0009 / 1,0000).
- **Inferencial:** no hay superioridad estadísticamente significativa entre algoritmos; no hay mejora significativa vs baseline (salvo deterioro significativo de MASAC).

### 5.3.12 Respuesta OE.1

**Respuesta a PE.1.** Los efectos diferenciales sobre flexibilidad se caracterizan descriptivamente (liderazgo mixto MAAC/MATD3) y se contrastan de forma exploratoria. No se establece impacto favorable ni diferenciación estadísticamente significativa conjunta del trío con KPI-gains. HAPPO aporta evidencia descriptiva de recursos, no de HE.

### 5.3.13 Decisión HE.1 (HE10 / HE11)

- **HE10:** **no se rechaza**.
- **HE11:** **no se respalda**.
- Nivel de evidencia: descriptivo + exploratorio; semilla única; HAPPO fuera de HE.

---

## 5.4 OE.2 — Emisiones de CO₂ (E2)

**PE.2.** ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen efectos diferenciales sobre las emisiones de CO₂ (eje E2) y cuál presenta el mejor desempeño en la comunidad inteligente heterogénea de Iquitos?

**OE.2.** Determinar y cuantificar los efectos diferenciales de los algoritmos HAPPO, MASAC, MATD3 y MAAC sobre las emisiones de CO₂ (eje E2) e identificar el algoritmo de mejor desempeño en la comunidad inteligente heterogénea de Iquitos.

**HE20 / HE21.** HE20: no hay efectos diferenciales estadísticamente significativos sobre CO₂ en E2. HE21: al menos un algoritmo produce efecto diferencial estadísticamente significativo sobre CO₂ en E2.

### 5.4.1 Descriptivos

Fuente: `descriptivos_kpi_gains_por_problema.csv` (n = 5).

| Algoritmo | Media gain | Mediana gain | Mejorados / no |
|---|---:|---:|---|
| **MATD3** | −0,4101 | **−0,0421** | 0 / 5 |
| MAAC | −0,4148 | −0,0470 | 0 / 5 |
| MASAC | −0,4171 | −0,0516 | 0 / 5 |
| HAPPO | — | — | Sin KPI-gains |

Medianas negativas y 0/5 KPI mejorados: deterioro en gains. Mejor mediana descriptiva: **MATD3**.

### 5.4.2 Shapiro–Wilk

MAAC W = 0,6993 p = 0,009419; MASAC W = 0,6999 p = 0,009548; MATD3 W = 0,7012 p = 0,009848 — normalidad rechazada (p ≈ 0,0094–0,0098).

### 5.4.3 Cambio frente a baseline

Todas las medianas de KPI-gain son negativas. En el plano físico de distrito, ΔCO₂ (kg; menor = mejor): MATD3 **23 070**; MAAC **70 654**; MASAC **77 649**; HAPPO **1 431 341**. Un ΔCO₂ positivo no se interpreta como “reducción” frente al baseline.

### 5.4.4 Prueba inferencial frente a baseline

Los tres algoritmos: p-Holm = **0,1875** (n.s.), dirección desfavorable. No se detecta impacto significativo tras Holm.

### 5.4.5 Comparación entre HAPPO, MASAC, MATD3 y MAAC

HAPPO solo descriptivo. Inferencia entre MAAC, MASAC y MATD3:

| Prueba | Estadístico | p | Efecto | Rol |
|---|---|---:|---|---|
| **Friedman** | χ² = 6,0000 | **0,0498** | Kendall W = **0,6000** | Señal pareada débil-moderada |
| KW (exploratorio) | H = 0,5364 | 0,7648 | ε² = 0 | n.s. |

Friedman es significativo al α = 0,05, pero sin impacto vs cero ni post hoc Holm no habilita HE21.

### 5.4.6 Tamaño del efecto

Kendall W = **0,6000**. Cliff’s δ exploratorio: pares con |δ| = 0,20. Magnitud pareada moderada en Friedman; sin confirmación por pares Holm.

### 5.4.7 Post hoc

Wilcoxon: los tres pares p-Holm = **0,307** (todos n.s.). MWU: p-Holm = 1,000.

### 5.4.8 KPI distritales

Ranking distrito E2 por `carbon_emissions_delta`: **MATD3** (23 070 kg) > MAAC (70 654) > MASAC (77 649) > HAPPO (1 431 341). Score OE2 4/4: MATD3 1,0000; MAAC 0,9662; MASAC 0,9612; HAPPO 0.

### 5.4.9 Resultados de los 17 edificios

Sin tabla completa en este capítulo. Fuentes: `district_ranking_by_scenario.csv` (MATD3 primero en E2) y `building_kpis_4madrl.csv` (desagregación de 17 edificios). No se inventan valores por edificio.

### 5.4.10 BESS, EV/V2G y cargas desplazables

Throughput BESS E2 (orden de magnitud desde ranking distrital): HAPPO maximiza actuación; MATD3 minimiza ΔCO₂ con throughput bajo. Éxito EV E2: HAPPO 0,492; MATD3 0,364; MAAC/MASAC ≈ 0,041. C5 no decide HE.

### 5.4.11 Identificación del MADRL de mejor desempeño

- **Descriptivo:** **MATD3** (mediana KPI-gain −0,0421; menor ΔCO₂; score OE2).
- **Inferencial:** ventaja descriptiva; Friedman marginal sin post hoc ni impacto vs cero → **sin** superioridad estadística establecida.

### 5.4.12 Respuesta OE.2

**Respuesta a PE.2.** Se identifica a MATD3 como mejor desempeño descriptivo ambiental. El efecto inferencial conjunto no alcanza el umbral de la hipótesis alternativa.

### 5.4.13 Decisión HE.2 (HE20 / HE21)

- **HE20:** **no se rechaza**.
- **HE21:** **no se respalda**.

---

## 5.5 OE.3 — Costos energéticos (E3)

**PE.3.** ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen efectos diferenciales sobre los costos energéticos (eje E3) y cuál presenta el mejor desempeño en la comunidad inteligente heterogénea de Iquitos?

**OE.3.** Determinar y cuantificar los efectos diferenciales de los algoritmos HAPPO, MASAC, MATD3 y MAAC sobre los costos energéticos (eje E3) e identificar el algoritmo de mejor desempeño en la comunidad inteligente heterogénea de Iquitos.

**HE30 / HE31.** HE30: no hay efectos diferenciales estadísticamente significativos sobre costos en E3. HE31: al menos un algoritmo produce efecto diferencial estadísticamente significativo sobre costos en E3.

### 5.5.1 Descriptivos

Fuente: `descriptivos_kpi_gains_por_problema.csv` (n = 9).

| Algoritmo | Media gain | Mediana gain | Mejorados / no |
|---|---:|---:|---|
| **MAAC** | −0,2278 | **−0,00268** | 1 / 8 |
| MATD3 | −0,2259 | −0,00918 | 1 / 8 |
| MASAC | −0,2355 | −0,01403 | 1 / 8 |
| HAPPO | — | — | Sin KPI-gains |

Mejor mediana descriptiva: **MAAC**.

### 5.5.2 Shapiro–Wilk

MAAC W = 0,5575 p = 3,029×10⁻⁵; MASAC W = 0,5879 p = 6,905×10⁻⁵; MATD3 W = 0,5464 p = 2,246×10⁻⁵ — normalidad rechazada (p ≤ 6,9×10⁻⁵).

### 5.5.3 Cambio frente a baseline

Medianas de KPI-gain negativas. Δcosto distrito E3 (USD; menor = mejor observado): MAAC **9 515**; MASAC **19 793**; MATD3 **44 399**; HAPPO **106 828**. Se distingue **menor costo observado** de **ahorro estadísticamente demostrado**. Las claves internas `*_eur` de la corrida son etiquetas legacy; los valores se interpretan en **USD** porque `electricity_pricing` está en $/kWh (TOU Electro Oriente).

### 5.5.4 Prueba inferencial frente a baseline

MAAC/MASAC p-Holm = **0,0781**; MATD3 p-Holm = **0,0586** — todos n.s. tras Holm; dirección desfavorable. No hay ahorro estadísticamente demostrado vs baseline.

### 5.5.5 Comparación entre HAPPO, MASAC, MATD3 y MAAC

HAPPO solo descriptivo. Inferencia entre el trío:

| Prueba | Estadístico | p | Efecto | Rol |
|---|---|---:|---|---|
| **Friedman** | χ² = 3,4286 | **0,1801** | W = 0,1905 | n.s. |
| KW (exploratorio) | H = 0,6138 | 0,7357 | ε² = 0 | n.s. |

### 5.5.6 Tamaño del efecto

Kendall W = **0,1905** (débil). Cliff’s δ exploratorio: MAAC–MASAC 0,21; MAAC–MATD3 0,09; MASAC–MATD3 −0,14.

### 5.5.7 Post hoc

Wilcoxon Holm: p-Holm ∈ {**0,527**; **1**; **1**} — todos n.s. MWU: p-Holm = 1,000. **No** se cita el p = 0,0333 de capas pooladas (Capa B) como resultado Holm canónico.

### 5.5.8 KPI distritales

Ranking distrito E3 por `electricity_cost_delta`: **MAAC** (9 515 USD). Score OE3 4/4: MAAC **1,0000**; MASAC 0,8944; MATD3 0,6415; HAPPO 0. TOPSIS (complementario): MAAC C\* = **0,9827**.

### 5.5.9 Resultados de los 17 edificios

Fuentes: `district_ranking_by_scenario.csv` (MAAC primero en E3) y `building_kpis_4madrl.csv`. Sin tabla completa inventada en este capítulo.

### 5.5.10 BESS, EV/V2G y cargas desplazables

Éxito EV E3: HAPPO 0,503; MATD3 0,482; MAAC/MASAC ≈ 0,041. Throughput BESS E3 elevado en HAPPO/MASAC/MAAC frente a MATD3. C5 no decide HE.

### 5.5.11 Identificación del MADRL de mejor desempeño

- **Descriptivo:** **MAAC** (KPI-gain, Δcosto, score 4/4, TOPSIS C\* = 0,9827).
- **Inferencial:** liderazgo descriptivo **sin** significancia omnibus ni impacto vs cero tras Holm.

### 5.5.12 Respuesta OE.3

**Respuesta a PE.3.** MAAC es el algoritmo de mejor desempeño descriptivo en costos; la ventaja **no** es inferencialmente concluyente. El menor costo observado no equivale a ahorro estadísticamente demostrado.

### 5.5.13 Decisión HE.3 (HE30 / HE31)

- **HE30:** **no se rechaza**.
- **HE31:** **no se respalda**.

---

## 5.6 OG — Coordinación energética multiobjetivo

**PG.** ¿En qué medida los algoritmos HAPPO, MASAC, MATD3 y MAAC producen efectos diferenciales en la coordinación energética multiobjetivo de una comunidad inteligente heterogénea de Iquitos, considerando la flexibilidad energética, las emisiones de CO₂ y los costos energéticos, y cuál presenta el mejor desempeño global?

**OG.** Determinar y cuantificar los efectos diferenciales de los algoritmos HAPPO, MASAC, MATD3 y MAAC en la coordinación energética multiobjetivo de una comunidad inteligente heterogénea de Iquitos, considerando la flexibilidad energética, las emisiones de CO₂ y los costos energéticos, e identificar el algoritmo de mejor desempeño global.

**H0G / H1G** (etiquetas Cap. 1 / Capa A). H0G: no hay efectos diferenciales estadísticamente significativos en la coordinación multiobjetivo ni diferencias globales entre algoritmos. H1G: hay impacto diferenciado y el desempeño global difiere entre algoritmos.

### 5.6.1 Integración descriptiva, trade-offs y Pareto

**Ranking `best_madrl` 3×3** (sin HAPPO; score global):

| Rango | Algoritmo | Score global | OE.1 | OE.2 | OE.3 |
|:---:|---|:---:|:---:|:---:|:---:|
| 1 | **MATD3** | **0,6667** | 1,0000 | 1,0000 | 0,0000 |
| 2 | MAAC | 0,5706 | 0,5837 | 0,1282 | 1,0000 |
| 3 | MASAC | 0,2351 | 0,0000 | 0,0000 | 0,7054 |

**Ranking evaluate_v2 4/4** (descriptivo): MAAC **0,9538**; MATD3 0,8805; MASAC 0,8679; HAPPO 0,0000.

Trade-off: MATD3 lidera flexibilidad física y CO₂; MAAC lidera costos, 4/4 y TOPSIS. Frente de Pareto = {MAAC, MASAC, MATD3}. No hay dominador único.

### 5.6.2 TOPSIS (complementario; no es prueba de hipótesis)

Fuente: `madrl_multicriteria_selection/topsis_ranking.csv`. MAAC C\* = **0,9827**; MASAC 0,5656; MATD3 0,3074. **TOPSIS no respalda HE ni H1G por sí solo.**

### 5.6.3 Inferencia GLOBAL (Capa A, n = 26)

Shapiro–Wilk: normalidad rechazada (p ≤ 2,6×10⁻⁶). Impacto vs 0 (Holm): MAAC p = **0,00233**; MASAC p = **1,55×10⁻⁴**; MATD3 p = **0,00293** — los tres **significativos en dirección desfavorable**.

| Prueba | Estadístico | p | Efecto |
|---|---|---:|---|
| **Friedman** | χ² = 9,2911 | **0,0096** | Kendall W = 0,1787 |
| KW (exploratorio) | H = 1,8108 | **0,4044** | ε² = 0 |

Wilcoxon post hoc Holm: solo MAAC–MASAC p-Holm = **0,0172**; MAAC–MATD3 = 0,295; MASAC–MATD3 = 0,114.

**Mejor compromiso global descriptivo:** depende del plano (`best_madrl` → MATD3 0,6667; 4/4/TOPSIS → MAAC 0,9538 / 0,9827). Score medio E1–E3: MAAC 0,8066. Mediana robusta GLOBAL: MATD3 (−0,00694). **Sin ganador global único** y **sin** superioridad estadística global concluyente de un único MADRL.

### 5.6.4 Decisión H0G / H1G

- **H0G:** **se rechaza de forma exploratoria**.
- **H1G:** **se respalda de forma exploratoria** (sin ganador único; **no** implica HE11 ∧ HE21 ∧ HE31).
- Nivel de evidencia: exploratorio; semilla única; HAPPO excluido de HE.

---

## 5.7 Contrastación consolidada de hipótesis

**Tabla 5.7.** Resumen H0G/H1G y HE10–HE31 (Capa A; α = 0,05).

| Hipótesis | Prueba | Estadístico | p | Tamaño | Post hoc | Decisión | Mejor algoritmo | Nivel evidencia |
|---|---|---|---:|---|---|---|---|---|
| **H0G / H1G** | Friedman GLOBAL + impacto Holm | χ² = 9,2911 | 0,0096 | W = 0,1787 | MAAC–MASAC 0,0172 | Se rechaza H0G; se respalda H1G exploratoria; sin ganador único | MATD3 (`best_madrl` 0,6667) / MAAC (4/4 0,9538; TOPSIS 0,9827) | Exploratorio |
| **HE10 / HE11** | Friedman OE1 + impacto Holm | χ² = 5,5897 | 0,0611 | W = 0,2329 | todos n.s. (mín. 0,110) | No se rechaza HE10; no se respalda HE11 | MAAC (gain) / MATD3 (flex) | Descriptivo |
| **HE20 / HE21** | Friedman OE2 + impacto Holm | χ² = 6,0000 | 0,0498 | W = 0,6000 | todos n.s. (0,307) | No se rechaza HE20; no se respalda HE21 | **MATD3** | Descriptivo |
| **HE30 / HE31** | Friedman OE3 + impacto Holm | χ² = 3,4286 | 0,1801 | W = 0,1905 | {0,527; 1; 1} | No se rechaza HE30; no se respalda HE31 | **MAAC** | Descriptivo |

KW exploratorio: OE1 p = 0,4685; OE2 p = 0,7648; OE3 p = 0,7357; GLOBAL p = 0,4044. Impacto vs baseline en ejes: solo MASAC OE1 significativo y desfavorable (p-Holm = 0,0483); GLOBAL los tres significativos y desfavorables. **No** se emplea la fórmula «se acepta H₀».

---

## 5.8 Discusión

### 5.8.1 Triangulación con la literatura

La ausencia de HE11 bajo liderazgo descriptivo mixto en flexibilidad es coherente con la dificultad de control multiagente en edificios *grid-interactive* reportada por Nweye et al. (2022, 2023b) y con el marco CityLearn v2 de comunidades energéticamente flexibles (Nweye et al., 2024; Vázquez-Canteli & Nagy, 2019b): la coordinación de DER no garantiza mejoras unívocas en todos los KPI de flexibilidad bajo una sola semilla.

El perfil de MATD3 en CO₂/flex física y de MAAC en costos dialoga con las familias actor-crítico multiagente (Iqbal & Sha, 2019; Kuba et al., 2021; Zhong et al., 2023) y con SAC/MASAC en entornos energéticos (Haarnoja et al., 2018; Gao et al., 2023): distintos sesgos de aprendizaje producen trade-offs multiobjetivo, no un dominador Pareto.

La disociación entre ΔCO₂ (MATD3) y Δcosto (MAAC) refuerza la necesidad de señales de carbono y tarifa TOU explícitas (Nweye et al., 2024; Nweye & Nagy, 2024b). El throughput BESS heterogéneo (C5) muestra que mayor actuación no implica mejor KPI-gain ni menor Δ físico.

La puerta Shapiro → no paramétrico, el rechazo a tratar episodios como réplicas independientes y la distinción descriptivo/inferencial siguen a Agarwal et al. (2021) sobre evaluación robusta en RL profundo y a las recomendaciones metodológicas del Cap. III sobre Friedman/Kendall W/Wilcoxon–Holm.

### 5.8.2 Limitaciones verificadas

Semilla única (seed = 0); HAPPO con curva descriptiva de 49 episodios históricos + 1 post-resume, pero sin KPI-gains finales comparables para HE; n KPI 12/5/9; impacto agregado GLOBAL desfavorable; capas B/C/D no deben mezclarse con A; TOPSIS y 4/4 no sustituyen hipótesis.

### 5.8.3 Auditoría de coherencia PG–OG–HG / PE–OE–HE

| Cadena | ¿Efecto respondido? | ¿Mejor MADRL identificado? | Nivel |
|---|---|---|---|
| **PG → OG → H0G/H1G** | Sí (efecto integrado exploratorio; H0G rechazada exploratoria) | Parcial: sin ganador único (MATD3 `best_madrl` vs MAAC 4/4/TOPSIS) | Descriptivo + inferencial exploratorio |
| **PE.1 → OE.1 → HE10/HE11** | Sí (efecto no significativo conjunto; HE10 no rechazada) | Sí descriptivo (MAAC gain / MATD3 flex); **no** inferencial | Descriptivo |
| **PE.2 → OE.2 → HE20/HE21** | Sí (sin impacto vs 0; Friedman marginal sin post hoc) | Sí descriptivo (**MATD3**); **no** inferencial | Descriptivo |
| **PE.3 → OE.3 → HE30/HE31** | Sí (sin omnibus ni impacto Holm) | Sí descriptivo (**MAAC**); **no** inferencial | Descriptivo |

**Veredicto de cierre Cap. V.** Los objetivos quedan respondidos en cuanto a *determinación del efecto diferencial* (con evidencia de no rechazo de las nulas específicas) y a *identificación del MADRL de mejor desempeño descriptivo* por eje; la superioridad estadísticamente significativa por eje **no** se establece. El Resumen, Abstract y Cap. VI deberán alinearse a este cierre en una fase posterior.

---

## Catálogo breve de artefactos canónicos

| Artefacto | Uso |
|---|---|
| `problemas_objetivos_hipotesis/*.csv` | HE/H0G canónicos (Capa A) |
| `best_madrl_report.json` / ranking 3×3 | Ranking descriptivo |
| `kpi_recalc_20260728/tables/ranking_oe_scores.csv` | Ranking 4/4 |
| `madrl_multicriteria_selection/topsis_ranking.csv` | TOPSIS C\* = 0,9827 |
| `district_ranking_by_scenario.csv` / `district_kpis_4madrl.csv` | C3 distrito |
| `building_kpis_4madrl.csv` | C4 edificios |
| `docs/AUDITORIA_CAP5_CONTRADICCIONES_STATS_2026-08-06.md` | Capas y contradicciones |
