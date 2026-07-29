# TOPSIS como medida formal para OG/OE/HE (Caps. V–VII) — 2026-07-29

Generado: `2026-07-29T22:07:24.136533+00:00`
Script: `tools/thesis/patch_topsis_medida_formal_cap5_6_7_docx.py`

## Veredicto

- **OK global:** `True`
- Postura: TOPSIS = medida multicriterio formal adicional para determinar/sustentar OG, OE.1–OE.3 y HE en Caps. V–VII; complementa evaluate_v2 y KPI-gains; no inventa scores.

## Ground truth TOPSIS

- Fuente: `outputs/madrl_multicriteria_selection/topsis_ranking.csv` / `outputs/madrl_multicriteria_selection/selection_report.json` (`real_drive_50ep_c1c6`)
- Ranking: MAAC **0,9827** > MASAC **0,5656** > MATD3 **0,3074** (ganador=MAAC)
- evaluate_v2 4/4: MAAC 0,9538 > MATD3 0,8805 > MASAC 0,8679 > HAPPO 0,0000

## Relación TOPSIS ↔ evaluate_v2

- Convergencia: Ambos coronan MAAC (#1).
- Divergencia: TOPSIS: MASAC (#2) > MATD3 (#3); evaluate_v2: MATD3 (#2) > MASAC (#3); best_madrl 3×3 favorece MATD3 (0,6667) por OE.1/OE.2.

## Mapeo de capítulos

- **Cap_V:** Capítulo 5 (resultados + §5.4 TOPSIS + contrastación)
- **Cap_VI:** §5.6 Discusión de resultados (rol de discusión; no hay Cap.6 discusión separado)
- **Cap_VII:** Capítulo 6 Conclusiones (no existe Heading 1 «Capítulo 7» en los 2 Word)

## Documentos

### Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx

- Path: `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`
- Backup: `outputs/_word_backups/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx.pre_topsis_formal_20260729_170721.bak`
- Cambios: 18
- Checks: `{"has_marker": true, "has_c9827": true, "has_c5656": true, "has_c3074": true, "stale_07828": false, "stale_descriptivo_topsis": false, "deny_role": false, "has_oe_he_anchor": true, "has_eval_compare": true}`
- OK: `True`

Disclaimers / párrafos tocados (preview):

- p[24] OLD: Esta tesis doctoral determina, mediante simulación computacional bajo diseño cuasiexperimental factorial 4×3, el efecto de cuatro algoritmos Multi-Agente de Apr
  NEW: Esta tesis doctoral determina, mediante simulación computacional bajo diseño cuasiexperimental factorial 4×3, el efecto de cuatro algoritmos Multi-Agente de Apr
- p[28] OLD: This doctoral thesis determines the effect of four cooperative Multi-Agent Deep Reinforcement Learning (MADRL) algorithms (HAPPO, MASAC, MATD3, MAAC) under a De
  NEW: This doctoral thesis determines the effect of four cooperative Multi-Agent Deep Reinforcement Learning (MADRL) algorithms (HAPPO, MASAC, MATD3, MAAC) under a De
- p[109] OLD: Veredicto (corrida madrl_v3_20260627_164047, seed = 0): ranking/Pareto descriptivo aceptado (MATD3 score 0,6667; sin dominador universal; MAAC lidera costos y e
  NEW: Veredicto (corrida madrl_v3_20260627_164047, seed = 0): ranking/Pareto descriptivo aceptado (MATD3 score 0,6667; sin dominador universal; MAAC lidera costos y e
- p[469] OLD: Cadena vertical Cap. 1 → Cap. 5: PG ↔ OG ↔ H0G/H1G; PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); PE.3 ↔ OE.3 ↔ HE30/HE31 (E3). Formulaciones exac
  NEW: Cadena vertical Cap. 1 → Cap. 5: PG ↔ OG ↔ H0G/H1G; PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); PE.3 ↔ OE.3 ↔ HE30/HE31 (E3). Formulaciones exac
- p[479] OLD: Regla de cumplimiento sin parciales: un OE se considera documentado solo si C3+C4 (distrito y edificio del eje) y C5 (control de recursos) estan presentes junto
  NEW: Regla de cumplimiento sin parciales: un OE se considera documentado solo si C3+C4 (distrito y edificio del eje) y C5 (control de recursos) estan presentes junto
- p[481] OLD: Primer acapite de resultados en cumplimiento de los objetivos. Estadistica descriptiva sobre los 50 episodios Drive en outputs/, con subacapites independientes 
  NEW: Primer acapite de resultados en cumplimiento de los objetivos. Estadistica descriptiva sobre los 50 episodios Drive en outputs/, con subacapites independientes 
- p[537] OLD: Segundo acapite. Pruebas sobre KPI-gains de los 50 episodios Drive (outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotes
  NEW: Segundo acapite. Pruebas sobre KPI-gains de los 50 episodios Drive (outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotes
- p[580] OLD: Tercer acapite. Resultados complementarios por objetivo (OG, OE.1, OE.2, OE.3) de forma independiente: convergencia, multiobjetivo distrito/edificio, baseline v
  NEW: Tercer acapite. Resultados complementarios por objetivo (OG, OE.1, OE.2, OE.3) de forma independiente: convergencia, multiobjetivo distrito/edificio, baseline v
- p[582] OLD: Complementos del OG (descriptivos de soporte; no deciden H0G/H1G): ranking global Drive, best/worst por escenario, KPIs multiobjetivo de distrito y TOPSIS/AHP (
  NEW: Complementos del OG (medidas de soporte multiobjetivo para H0G/H1G/OE): ranking global Drive, best/worst por escenario, KPIs multiobjetivo de distrito y TOPSIS/
- p[592] OLD: Tabla 5.4.1. TOPSIS descriptivo (madrl_multicriteria_selection; no evidencia de HE).
  NEW: Tabla 5.4.1. TOPSIS — medida multicriterio formal adicional (madrl_multicriteria_selection; C* canónicos; complementa OG/OE/HE junto a evaluate_v2).
- p[614] OLD: Integración completa — sin parciales — de artefactos reales de la corrida madrl_v3_20260627_164047 (50 episodios). Incluye multicriterio TOPSIS/AHP, resúmenes p
  NEW: Integración completa — sin parciales — de artefactos reales de la corrida madrl_v3_20260627_164047 (50 episodios). Incluye multicriterio TOPSIS/AHP, resúmenes p
- p[1087] OLD: Protocolo: (1) Shapiro-Wilk; si se rechaza normalidad, solo no parametrico; (2) omnibus KW/Friedman + post hoc Holm (C1–C2); (3) HE alternativas requieren impac
  NEW: Protocolo: (1) Shapiro-Wilk; si se rechaza normalidad, solo no parametrico; (2) omnibus KW/Friedman + post hoc Holm (C1–C2); (3) HE alternativas requieren impac
- p[1124] OLD: Quinto y ultimo acapite del capitulo. 1) Separacion de planos: §5.2 descriptivo por OG/OE; §5.3 inferencial por OG/OE; §5.4 otros por OG/OE; §5.5 contrastacion 
  NEW: Quinto y ultimo acapite del capitulo. 1) Separacion de planos: §5.2 descriptivo por OG/OE; §5.3 inferencial por OG/OE; §5.4 otros por OG/OE; §5.5 contrastacion 
- TABLE {'type': 'table_cell', 'table': 72, 'row': 1, 'algorithm': 'MAAC', 'old': '0.7828', 'new': '0.9827'}
- TABLE {'type': 'table_cell', 'table': 72, 'row': 2, 'algorithm': 'MASAC', 'old': '0.5042', 'new': '0.5656'}
- TABLE {'type': 'table_cell', 'table': 72, 'row': 3, 'algorithm': 'MATD3', 'old': '0.3641', 'new': '0.3074'}
- TABLE {'type': 'table_cell_text', 'table': 79, 'row': 2, 'col': 2, 'old_preview': 'MAAC gana costos/TOPSIS/4/4 descriptivo; KPI-gains E3 sin omnibus ni impacto vs cero tras Holm', 'new_preview': 'KPI-gains E3 sin omnibus ni impacto vs cero tras Holm; TOPSIS (C*≈0,9827) y evaluate_v2 (0,9538) coronan MAAC en multiobjetivo/costos como medida adicional, sin'}
- INSERT after [1137] `6.1 Principales hallazgos`: Como medida multicriterio formal adicional, TOPSIS (C* MAAC ≈ 0,9827; MASAC 0,5656; MATD3 0,3074) refuerza las conclusiones sobre OG/OE: el cumplimiento descrip

### Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx

- Path: `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx`
- Backup: `outputs/_word_backups/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx.pre_topsis_formal_20260729_170721.bak`
- Cambios: 22
- Checks: `{"has_marker": true, "has_c9827": true, "has_c5656": true, "has_c3074": true, "stale_07828": false, "stale_descriptivo_topsis": false, "deny_role": false, "has_oe_he_anchor": true, "has_eval_compare": true}`
- OK: `True`

Disclaimers / párrafos tocados (preview):

- p[23] OLD: El presente estudio determina el efecto de cuatro algoritmos MADRL (HAPPO, MASAC, MATD3 y MAAC) sobre la flexibilidad energética, las emisiones de CO₂ y los cos
  NEW: El presente estudio determina el efecto de cuatro algoritmos MADRL (HAPPO, MASAC, MATD3 y MAAC) sobre la flexibilidad energética, las emisiones de CO₂ y los cos
- p[24] OLD: La evidencia se recalculó exclusivamente con los resultados reales de los 50 episodios de cada uno de los 12 tratamientos de la corrida madrl_v3_20260627_164047
  NEW: La evidencia se recalculó exclusivamente con los resultados reales de los 50 episodios de cada uno de los 12 tratamientos de la corrida madrl_v3_20260627_164047
- p[27] OLD: This study determines the effect of four MADRL algorithms (HAPPO, MASAC, MATD3, MAAC) on energy flexibility, CO₂ emissions and energy costs in a smart community
  NEW: This study determines the effect of four MADRL algorithms (HAPPO, MASAC, MATD3, MAAC) on energy flexibility, CO₂ emissions and energy costs in a smart community
- p[28] OLD: All evidence was recalculated exclusively from the real 50-episode results for each of the 12 treatments in run madrl_v3_20260627_164047: 600 episode rows, 668 
  NEW: All evidence was recalculated exclusively from the real 50-episode results for each of the 12 treatments in run madrl_v3_20260627_164047: 600 episode rows, 668 
- p[493] OLD: Cadena vertical Cap. 1 → Cap. 5: PG ↔ OG ↔ H0G/H1G; PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); PE.3 ↔ OE.3 ↔ HE30/HE31 (E3). Formulaciones exac
  NEW: Cadena vertical Cap. 1 → Cap. 5: PG ↔ OG ↔ H0G/H1G; PE.1 ↔ OE.1 ↔ HE10/HE11 (E1); PE.2 ↔ OE.2 ↔ HE20/HE21 (E2); PE.3 ↔ OE.3 ↔ HE30/HE31 (E3). Formulaciones exac
- p[503] OLD: Regla de cumplimiento sin parciales: un OE se considera documentado solo si C3+C4 (distrito y edificio del eje) y C5 (control de recursos) estan presentes junto
  NEW: Regla de cumplimiento sin parciales: un OE se considera documentado solo si C3+C4 (distrito y edificio del eje) y C5 (control de recursos) estan presentes junto
- p[505] OLD: Primer acapite de resultados en cumplimiento de los objetivos. Estadistica descriptiva sobre los 50 episodios Drive en outputs/, con subacapites independientes 
  NEW: Primer acapite de resultados en cumplimiento de los objetivos. Estadistica descriptiva sobre los 50 episodios Drive en outputs/, con subacapites independientes 
- p[561] OLD: Segundo acapite. Pruebas sobre KPI-gains de los 50 episodios Drive (outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotes
  NEW: Segundo acapite. Pruebas sobre KPI-gains de los 50 episodios Drive (outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/problemas_objetivos_hipotes
- p[604] OLD: Tercer acapite. Resultados complementarios por objetivo (OG, OE.1, OE.2, OE.3) de forma independiente: convergencia, multiobjetivo distrito/edificio, baseline v
  NEW: Tercer acapite. Resultados complementarios por objetivo (OG, OE.1, OE.2, OE.3) de forma independiente: convergencia, multiobjetivo distrito/edificio, baseline v
- p[606] OLD: Complementos del OG (descriptivos de soporte; no deciden H0G/H1G): ranking global Drive, best/worst por escenario, KPIs multiobjetivo de distrito y TOPSIS/AHP (
  NEW: Complementos del OG (medidas de soporte multiobjetivo para H0G/H1G/OE): ranking global Drive, best/worst por escenario, KPIs multiobjetivo de distrito y TOPSIS/
- p[616] OLD: Tabla 5.4.1. TOPSIS descriptivo (madrl_multicriteria_selection; no evidencia de HE).
  NEW: Tabla 5.4.1. TOPSIS — medida multicriterio formal adicional (madrl_multicriteria_selection; C* canónicos; complementa OG/OE/HE junto a evaluate_v2).
- p[638] OLD: Integración completa — sin parciales — de artefactos reales de la corrida madrl_v3_20260627_164047 (50 episodios). Incluye multicriterio TOPSIS/AHP, resúmenes p
  NEW: Integración completa — sin parciales — de artefactos reales de la corrida madrl_v3_20260627_164047 (50 episodios). Incluye multicriterio TOPSIS/AHP, resúmenes p
- p[1111] OLD: Protocolo: (1) Shapiro-Wilk; si se rechaza normalidad, solo no parametrico; (2) omnibus KW/Friedman + post hoc Holm (C1–C2); (3) HE alternativas requieren impac
  NEW: Protocolo: (1) Shapiro-Wilk; si se rechaza normalidad, solo no parametrico; (2) omnibus KW/Friedman + post hoc Holm (C1–C2); (3) HE alternativas requieren impac
- p[1148] OLD: Quinto y ultimo acapite del capitulo. 1) Separacion de planos: §5.2 descriptivo por OG/OE; §5.3 inferencial por OG/OE; §5.4 otros por OG/OE; §5.5 contrastacion 
  NEW: Quinto y ultimo acapite del capitulo. 1) Separacion de planos: §5.2 descriptivo por OG/OE; §5.3 inferencial por OG/OE; §5.4 otros por OG/OE; §5.5 contrastacion 
- p[1165] OLD: OG. El ranking canónico best_madrl 3×3 identifica a MATD3 (score global 0,6667) como mejor desempeño coordinado descriptivo, con trade-off: MATD3 lidera OE.1/OE
  NEW: OG. El ranking canónico best_madrl 3×3 identifica a MATD3 (score global 0,6667) como mejor desempeño coordinado descriptivo, con trade-off: MATD3 lidera OE.1/OE
- p[1174] OLD: Las limitaciones principales son: (i) semilla única (seed 0) en la campaña entrenada —el protocolo n_seeds=12 y el runner están implementados y validados con sm
  NEW: Las limitaciones principales son: (i) semilla única (seed 0) en la campaña entrenada —el protocolo n_seeds=12 y el runner están implementados y validados con sm
- TABLE {'type': 'table_cell', 'table': 59, 'row': 1, 'algorithm': 'MAAC', 'old': '0.7828', 'new': '0.9827'}
- TABLE {'type': 'table_cell', 'table': 59, 'row': 2, 'algorithm': 'MASAC', 'old': '0.5042', 'new': '0.5656'}
- TABLE {'type': 'table_cell', 'table': 59, 'row': 3, 'algorithm': 'MATD3', 'old': '0.3641', 'new': '0.3074'}
- TABLE {'type': 'table_cell_text', 'table': 66, 'row': 2, 'col': 2, 'old_preview': 'MAAC gana costos/TOPSIS/4/4 descriptivo; KPI-gains E3 sin omnibus ni impacto vs cero tras Holm', 'new_preview': 'KPI-gains E3 sin omnibus ni impacto vs cero tras Holm; TOPSIS (C*≈0,9827) y evaluate_v2 (0,9538) coronan MAAC en multiobjetivo/costos como medida adicional, sin'}
- TABLE {'type': 'table_cell_text', 'table': 69, 'row': 4, 'col': 2, 'old_preview': 'Kruskal–Wallis E3 p = 0,7357 (KPI-gains); TOPSIS/4/4 no sustituyen HE31', 'new_preview': 'Kruskal–Wallis E3 p = 0,7357 (KPI-gains); TOPSIS/evaluate_v2 refuerzan el juicio multiobjetivo hacia MAAC/OE.3 sin sustituir el omnibus de HE31'}
- INSERT after [1161] `6.1 Conclusiones por objetivo`: Como medida multicriterio formal adicional, TOPSIS (C* MAAC ≈ 0,9827; MASAC 0,5656; MATD3 0,3074; outputs/madrl_multicriteria_selection/) refuerza las conclusio

