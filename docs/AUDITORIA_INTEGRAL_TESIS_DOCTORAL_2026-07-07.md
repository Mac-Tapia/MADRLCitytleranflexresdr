# Auditoría integral — Tesis doctoral MADRL CityLearn Iquitos

**Fecha:** 2026-07-07  
**Documento auditado:** `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`  
**Fuente canónica de datos:** [Google Drive MADRL](https://drive.google.com/drive/u/0/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX) → espejo local `outputs/_drive_madrl/full_data/` → corrida `madrl_v3_20260627_164047`  
**Herramientas ejecutadas:** `tools/thesis/verify_tesis_doctoral_docx.py`, extracción `python-docx` (`.venv39-citylearn-v3`), cotejo con `best_madrl_report.json`, `resumen_comparativo/estadistica/`, `figuras_drive_reales/`, `multiobjetivo/`, `docs/tesis_capitulos/Referencias_APA.md`, `agent-skills/madrl-citylearn-thesis-integrated/references/module-b-thesis-report.md`, `docs/informedetesis.txt`

---

## 1. Veredicto ejecutivo

### **NO LISTO para sustentación doctoral**

La tesis cuenta con una **base técnica trazable y reproducible** (corrida Colab/Drive auditada, tablas KPI alineadas con `best_madrl_report.json`, figuras comparativas desde artefactos reales, batería inferencial ejecutada y documentada en Tabla 5.5). Sin embargo, **no cumple aún los estándares de cierre doctoral** por brechas académicas, editoriales e inferenciales que impiden declarar conclusiones causales sólidas.

| Dimensión | Estado | Resumen |
|-----------|--------|---------|
| Estructura 6 capítulos | Parcial | Capítulos 1–6 presentes; **falta §5.4**; numeración salta 5.3 → 5.5 |
| Extensión doctoral | Insuficiente | ~6 603 palabras (umbral típico doctoral >> 30 000) |
| Datos y trazabilidad Drive | OK | Tablas 5.1–5.3 coinciden con JSON/CSV canónicos |
| Figuras (título + explicación) | Parcial | 15/15 con caption; **0/15 con referencia explicativa en prosa** |
| Estadística descriptiva | OK | Ejecutada y mostrada (Tablas 5.2, 5.3) |
| Estadística inferencial | Parcial | Ejecutada (Tabla 5.5) pero **no respalda HG** en corrida canónica |
| Coherencia PG→OE→resultados | Parcial | Ranking descriptivo coherente; hipótesis inferenciales no confirmadas |
| APA y antecedentes Cap. 2 | Parcial | Citas internacionales presentes; **antecedentes nacionales/doctorales insuficientes** |
| HAPPO (4.º algoritmo) | Incompleto | 49/50 ep., sin KPIs finales; excluido de inferencia |
| Script `verify_tesis_doctoral_docx.py` | Pasa (`complete: true`) | Verificación mínima estructural; **no sustituye esta auditoría** |

**Nota sobre versiones del DOCX:** Existe un segundo archivo más completo — `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos_resultados_drive_integrados_ordenado_con_diagramas.docx` (33 figuras, Anexos A/B, ~7 174 palabras) documentado en `docs/DIAGNOSTICO_TESIS_DOCTORAL_COMPLETITUD.md`. La auditoría solicitada cubre el DOCX canónico nominal; se recomienda **unificar una sola versión** antes de sustentación.

---

## 2. Figuras: título, explicación, fuente Drive

**Resumen:** 15 imágenes embebidas = 15 captions detectados. Sección 5.5 incluye párrafo introductorio sobre procedencia Drive; **ninguna figura tiene discusión individual en el cuerpo** (p. ej. «como se observa en la Figura 5.6…»). Criterio: **caption OK / explicación FALTA** salvo contexto de bloque.

| Figura | Título (caption) | Explicación en texto | Fuente Drive / local | Estado |
|--------|------------------|----------------------|----------------------|--------|
| 5.1 | Convergencia E1 (reward_mean) — datos reales Drive | Solo bloque §5.5; sin análisis de tendencia | `figuras_drive_reales/comparativo/comparativo_E1_convergence_reward_mean.png` | Caption OK / **FALTA** explicación |
| 5.2 | Convergencia E2 (reward_mean) — datos reales Drive | Idem | `.../comparativo_E2_convergence_reward_mean.png` | Caption OK / **FALTA** |
| 5.3 | Convergencia E3 (reward_mean) — datos reales Drive | Idem | `.../comparativo_E3_convergence_reward_mean.png` | Caption OK / **FALTA** |
| 5.4 | Ranking global OE1/OE2/OE3 (KPIs Drive) | Mencionado en Resumen/§5.2; sin lectura gráfica | `.../comparativo_global_ranking_oe.png` | Caption OK / **FALTA** |
| 5.5 | Mejor y peor MADRL por escenario | Idem | `.../comparativo_best_worst_por_escenario.png` | Caption OK / **FALTA** |
| 5.6 | KPI OE1 flexibilidad — comparativa E1 | Vinculado a OE.1 en caption; sin interpretación | `.../comparativo_E1_OE1_kpi.png` | Caption OK / **FALTA** |
| 5.7 | KPI OE2 emisiones CO₂ — comparativa E2 | Idem OE.2 | `.../comparativo_E2_OE2_kpi.png` | Caption OK / **FALTA** |
| 5.8 | KPI OE3 costo energético — comparativa E3 | Idem OE.3 | `.../comparativo_E3_OE3_kpi.png` | Caption OK / **FALTA** |
| 5.9 | Control MADRL por edificio (trace.csv) — E2 | Párrafo §5.6 sobre 17 edificios; sin lectura de trazas | `.../comparativo_E2_control_trace.png` | Caption OK / **FALTA** |
| 5.10 | KPIs multiobjetivo — distrito | §5.6–5.7 contexto inventario EV | `multiobjetivo/drive_district_objectives.png` | Caption OK / **PARCIAL** |
| 5.11 | OE1 flexibilidad por edificio | Idem | `multiobjetivo/drive_building_E1_flex_composite_proxy.png` | Caption OK / **FALTA** |
| 5.12 | OE2 delta CO₂ por edificio | Idem | `multiobjetivo/drive_building_E2_carbon_emissions_delta_kgco2.png` | Caption OK / **FALTA** |
| 5.13 | OE3 delta costo por edificio | Idem | `multiobjetivo/drive_building_E3_electricity_cost_delta_eur.png` | Caption OK / **FALTA** |
| 5.14 | Inventario EV por edificio | Mención 185 cargadores en §5.6 | `multiobjetivo/drive_building_ev_inventory.png` | Caption OK / **PARCIAL** |
| 5.15 | Desempeño EV — MATD3/E2 | Sin interpretación de tasa de éxito | `multiobjetivo/drive_building_ev_success_matd3_e2.png` | Caption OK / **FALTA** |

**Figuras adicionales en repositorio no incluidas en DOCX canónico:** 17 comparativas Drive (`figuras_drive_reales/`), 6 multiobjetivo distrito/edificio, 17 tarjetas `por_edificio/`, 9 figuras `analysis_real_drive/figures/`, 9 diagramas Anexo B (solo en DOCX integrado).

**`figure_audit_report.json`:** comparativas 17/17 OK; multiobjetivo 6/6 OK; HAPPO 7/13 figuras por job (KPIs ausentes).

---

## 3. Estadística descriptiva e inferencial vs objetivos (OE1/OE2/OE3)

### 3.1 Descriptiva — **EJECUTADA y COHERENTE con Drive**

| Objetivo | Evidencia en Word | Fuente canónica | Cotejo |
|----------|-------------------|-----------------|--------|
| **OE.1** (flexibilidad, E1) | Tabla 5.2 score OE1=1.0000 (MATD3); Tabla 5.3 flex_comp. | `best_madrl_report.json` → MATD3 `score_oe1_flex: 1.0`; `descriptivo_distrito_colab.csv` MATD3/E1 flex=1.0009 | **OK** |
| **OE.2** (CO₂, E2) | Tabla 5.2 OE2=1.0000 (MATD3); Tabla 5.3 delta CO₂ MATD3/E2=23 070 kg | JSON co2_delta MATD3=23070.42; CSV idem | **OK** |
| **OE.3** (costos, E3) | Tabla 5.2 OE3=1.0000 (MAAC); Tabla 5.3 MAAC/E3 costo=9 515 EUR | JSON cost_delta MAAC=9515.15; ranking MAAC `score_oe3_cost: 1.0` | **OK** |
| **OG** (coordinado) | Resumen/Tabla 5.2 MATD3 score global **0,6667** | `best_madrl_report.json` `score_global: 0.6667` | **OK** |

Tabla 5.1 (episodios): MATD3/MAAC/MASAC 50/50/50 con KPIs; HAPPO 49/49/49 sin KPIs (`VecEnvWrapper`) — coincide con `best_madrl_report.json` → `happo_pending`.

### 3.2 Inferencial — **EJECUTADA pero NO CONFIRMA hipótesis**

Fuente: `analisis_estadistico_madrl.csv`, `hipotesis_estadisticas_madrl.csv`, Tabla 5.5 del DOCX.

| Alcance | Prueba | p en Word (Tabla 5.5) | p en CSV canónico | α=0,05 | Implicación para OE/HG |
|---------|--------|----------------------|-------------------|--------|------------------------|
| OE1 / E1 | Kruskal-Wallis | 0,281 | 0,2806 | No significativo | **No rechaza H₀** en flexibilidad |
| OE2 / E2 | Kruskal-Wallis | 0,546 | 0,5457 | No significativo | **No rechaza H₀** en CO₂ |
| OE3 / E3 | Kruskal-Wallis | 0,388 | 0,3881 | No significativo | **No rechaza H₀** en costos |
| ALL (OG) | Kruskal-Wallis | 0,155 | 0,1554 | No significativo | **HG no confirmada inferencialmente** |
| ALL | Wilcoxon MASAC vs MATD3 | 0,0049 | 0,00489 | Significativo (pareado) | Diferencia exploratoria; no sustituye KW global |
| ALL | Mann-Whitney MASAC vs MATD3 | 0,070 | 0,0701 | No significativo | — |
| Local v4 (5 ep) | Kruskal-Wallis | 0,0459 | (referencia histórica) | Significativo exploratorio | **No es corrida canónica** |

**Shapiro-Wilk:** normalidad rechazada en MASAC/MATD3/MAAC (p < 1e⁻⁷); HAPPO sin datos → justifica pruebas no paramétricas. **Correcto y documentado.**

### 3.3 Inconsistencias detectadas (Abstract vs Cap. 5 vs Hipótesis)

| Elemento | Contenido | Problema |
|----------|-----------|----------|
| **Abstract** | «inferential tests on the canonical run **remain pending**» | **Contradice §5.8 y Tabla 5.5**, donde las pruebas ya se ejecutaron |
| **Resumen (es)** | MATD3 lidera OE1/OE2; MAAC OE3; score 0,6667 | Coherente con datos descriptivos |
| **HG / HE.1–3** (Cap. 1) | Efecto «estadísticamente significativo»; MATD3 mayor efecto | **No sustentado** por KW canónico (todos p > 0,05) |
| **§5.8 interpretación** | Reconoce KW no significativo con 1 semilla | **Correcto y honesto** — pero choca con formulación de hipótesis en Cap. 1 |
| **Mejor algoritmo por mediana KPI-gain** | MAAC (OE1), MATD3 (OE2), MAAC (OE3) | **Difiere del ranking por score** (MATD3 OE1/OE2) — debe explicitarse que son métricas distintas |

### 3.4 Mapa OE → secciones Word

| OE | Sección Word | Descriptivo | Inferencial |
|----|--------------|-------------|-------------|
| OE.1 | §5.3, Fig. 5.6, 5.11 | Tabla 5.3, Tabla 5.2 | Tabla 5.5 fila OE1 KW p=0,281 |
| OE.2 | §5.3, Fig. 5.7, 5.12 | Tabla 5.3 | Tabla 5.5 fila OE2 KW p=0,546 |
| OE.3 | §5.3, Fig. 5.8, 5.13 | Tabla 5.3 | Tabla 5.5 fila OE3 KW p=0,388 |

---

## 4. Coherencia arquitectura PG → OE → resultados → conclusiones

### 4.1 Flujo del proyecto (referencia: `module-b-thesis-report.md`, `informedetesis.txt`)

```
PG (efecto MADRL sobre flexibilidad + CO₂ + costos)
  → OG + OE.1/OE.2/OE.3
    → Diseño factorial 4×3 (HAPPO, MASAC, MATD3, MAAC × E1/E2/E3)
      → 54 KPI CityLearn v2 + corrida canónica 50 ep Colab/Drive
        → Ranking descriptivo (best_madrl_report.json)
          → Pruebas inferenciales (KPI-gain vs baseline)
            → Conclusiones Cap. 6
```

### 4.2 Evaluación de coherencia

| Eslabón | Estado | Observación |
|---------|--------|-------------|
| PG → OE.1–3 | OK | Matriz Tablas 3.1, 3.4 alineadas con module-b |
| VI (4 algoritmos × 3 escenarios) | **Parcial** | HAPPO incompleto rompe factorial completo 12/12 |
| VD (54 KPI, 3 ejes) | OK | Tabla 5.3 y multiobjetivo cubren tres dimensiones |
| Resultados → MATD3 seleccionado | OK | Trazable a `best_madrl_report.json` |
| Resultados → HG inferencial | **NO OK** | KW canónico no significativo; no se puede afirmar efecto estadísticamente significativo global |
| Conclusiones Cap. 6 | Parcial | Declaran MATD3 como mayor efecto **descriptivo**; deben calificar inferencia como exploratoria |
| **§5.4 baseline CityLearn v2** | **AUSENTE** | module-b exige contrastación con baseline; numeración salta 5.3 → 5.5 |
| Tercera persona | OK | 0 apariciones de yo/nosotros detectadas |
| Orden de capítulos en cuerpo | Anomalía | Headings listan Cap. 5 antes de Cap. 1 (posible reordenamiento Word); verificar índice automático |

### 4.3 Contenido potencialmente inventado o no verificable

| Ítem | Riesgo | Evidencia |
|------|--------|-----------|
| Afirmación HG «estadísticamente significativo» | Alto | No respaldada por CSV canónico |
| Abstract «tests pending» | Medio | Obsoleto respecto a §5.8 |
| HAPPO en comparativas de ranking global | Medio | Excluido de Tabla 5.2 pero mencionado 23 veces; riesgo de lectura como comparable |
| Porcentajes EV éxito (3,9%–48,2%) | Bajo | Verificables en `descriptivo_distrito_colab.csv` |
| «Corrida local v4 KW p=0,0459 significativo» | Bajo | Correctamente etiquetada como referencia histórica en Tabla 5.5 |

---

## 5. APA y antecedentes (Capítulo 2)

### 5.1 Formato APA

| Criterio | Estado |
|----------|--------|
| Referencias al final | 66 entradas en DOCX vs 66 esperadas por script |
| Citas en texto (autor, año) | 24 autores únicos detectados en cuerpo; lista APA tiene ~60 |
| Sangría francesa / cursivas | No verificado tipográficamente en esta auditoría |
| DOI como URL | Parcial en lista final del DOCX |
| Coherencia cita ↔ referencia | **Pendiente** — script no valida bidireccionalmente |

### 5.2 Antecedentes nacionales e internacionales (Cap. 2)

| Requisito (`module-b`, `informedetesis.txt`) | Estado |
|---------------------------------------------|--------|
| Estado del arte internacional (últimos 5 años) | **OK** — CityLearn, MERLIN, Liu, Ye, Ma, Sarkar, etc. |
| Antecedentes por eje OE1/OE2/OE3 | **OK** — §2.1 organizado en 4 ejes |
| Antecedentes **nacionales/peruanos** | **INSUFICIENTE** — SEAI/Iquitos/Loreto mencionados (~7); **sin** Domínguez Barbero (2026), Rosero Bernal (2024), tesis doctorales UNI, OSINERGMIN/MINAM como antecedentes de investigación |
| Trabajos relacionados (§2.3) | Presente (Tabla 2.2) |
| Tesis doctorales en Cap. 2 | **No identificadas** en extracción |

---

## 6. Lista de referencias con enlaces verificables

**Fuente exclusiva:** `docs/tesis_capitulos/Referencias_APA.md` (60 entradas con viñeta).  
**Regla:** solo URLs/DOIs presentes en el archivo; `[PV]` = pendiente de verificación secundaria; sin URL = sin enlace inventado.

### 6.1 Entradas sin URL en archivo fuente

| Referencia | Estado |
|------------|--------|
| Sutton & Barto (2018). *Reinforcement learning* (MIT Press) | Sin URL en fuente — libro |
| Liu, J., et al. (2022). IEEE Trans. Sustainable Energy | **[PV]** — sin DOI en fuente |
| IEC (2021). IEC 61215-1:2021 | Sin URL en fuente — norma |
| OSINERGMIN (2024). Resolución CD 0024-2024 | Sin URL en fuente — normativa nacional |

### 6.2 Entradas marcadas [PV] (con enlace parcial en fuente)

| Autor (año) | Enlace en Referencias_APA.md | Nota |
|-------------|------------------------------|------|
| Zhu, Y., et al. (2024) | https://doi.org/10.1016/j.neucom.2024.128015 | [PV] autores completos |
| Zhao, Y., et al. (2024) | https://doi.org/10.1016/j.enbuild.2024.114529 | [PV] autores completos |
| Ahmed, A., et al. (2025) | https://doi.org/10.1093/ijlct/ctaf142 | [PV] primer autor |
| Chen, X., et al. (2024) | https://arxiv.org/abs/2407.13790 | [PV] coautores |
| Chen, Y., et al. (2025) | https://doi.org/10.1016/j.enbuild.2025.115380 | [PV] autores |
| Kim, J., et al. (2025) | https://doi.org/10.1016/j.egyr.2025.005 | [PV] autores y nº artículo |
| Wang, Y., et al. (2025) | https://doi.org/10.1016/j.segan.2025.196X | [PV] autores y nº artículo |

### 6.3 Referencias verificadas con enlace (muestra representativa — 56 con URL)

| Autor (año) | DOI / URL (tal como en Referencias_APA.md) |
|-------------|---------------------------------------------|
| Akiba et al. (2019) | https://doi.org/10.1145/3292500.3330701 |
| Haarnoja et al. (2018) | https://proceedings.mlr.press/v80/haarnoja18b.html |
| Hu et al. (2023) | https://www.jmlr.org/papers/v24/23-0378.html |
| Iqbal & Sha (2019) | https://proceedings.mlr.press/v97/iqbal19a.html |
| Kuba et al. (2021) | https://arxiv.org/abs/2109.11251 |
| Lowe et al. (2017) | https://proceedings.neurips.cc/paper/2017/hash/68a9750337a418a86fe06c1991a1d64c-Abstract.html |
| Oliehoek & Amato (2016) | https://doi.org/10.1007/978-3-319-28929-8 |
| Nweye et al. (2024) | https://doi.org/10.1080/19401493.2024.2418813 |
| Nweye et al. (2022) | https://doi.org/10.1016/j.egyai.2022.100202 |
| Vázquez-Canteli & Nagy (2019a) | https://doi.org/10.1145/3360322.3360998 |
| Liu, Y., Zhang, Q., & Guo, Y. (2022) | https://doi.org/10.1016/j.apenergy.2022.118703 |
| Ma et al. (2025) | https://doi.org/10.1016/j.apenergy.2025.126018 |
| Ye et al. (2025) | https://doi.org/10.1016/j.apenergy.2025.125339 |
| Fang et al. (2021) | https://doi.org/10.1016/j.scs.2021.103163 |
| Gao et al. (2023) | https://doi.org/10.3390/en16073248 |
| MINAM (2019) INFOCARBONO | https://infocarbono.minam.gob.pe/ |
| Hribar et al. (2025) | https://doi.org/10.1038/s41598-025-12554-x |
| Xie et al. (2023) | https://doi.org/10.1016/j.apenergy.2023.121213 |

**Lista completa machine-readable:** `outputs/_audit_referencias_apa.json` (60 entradas, 56 con URL, 8 [PV]).

---

## 7. Acciones priorizadas (P0–P5)

### P0 — Bloqueantes para sustentación

1. **Reconciliar Abstract con §5.8:** actualizar Abstract (es/en) — las pruebas inferenciales canónicas ya están en Tabla 5.5.
2. **Reformular HG/HE.1–3 en Cap. 1 y §5.9:** distinguir evidencia **descriptiva** (ranking MATD3) de **inferencial** (KW no significativo); no afirmar significancia global sin p < 0,05 canónico.
3. **Completar o cerrar HAPPO:** reanudar celda 2.3 Colab (`VecEnvWrapper`) o declarar diseño 3×3 efectivo y ajustar PG factorial 4×3.
4. **Añadir §5.4** «Contrastación con baseline CityLearn v2» según `module-b-thesis-report.md` (matriz `citylearn_v2_baseline/`).
5. **Unificar DOCX:** decidir versión única (canónica 15 fig. vs integrada 33 fig. + anexos).

### P1 — Figuras y redacción

6. Redactar **párrafo interpretativo por figura** (mín. 2–3 oraciones: qué muestra, hallazgo, vínculo OE).
7. Referenciar figuras en prosa («Figura 5.6 muestra…») — actualmente 0 referencias cruzadas.
8. Actualizar índice, lista de figuras y lista de tablas (Word: clic derecho → Actualizar campos).

### P2 — Extensión y nivel doctoral

9. Ampliar Cap. 2 con **antecedentes nacionales** (tesis doctorales, sistemas aislados peruanos, normativa OSINERGMIN).
10. Expandir §5.9 Discusión y Cap. 6 (aportes originales, implicancias SEAI, transferibilidad).
11. Meta extensión: ≥ 30 000 palabras cuerpo + anexos.

### P3 — Estadística avanzada

12. Multi-semilla (≥ 5, ideal ≥ 20 según Colas et al., 2019) antes de elevar conclusiones causales.
13. Post-hoc Dunn + Bonferroni documentado en texto (CSV `comparaciones_mwu_madrl.csv` disponible).
14. Reportar tamaños de efecto (ε², rank-biserial) en Tabla 5.5.

### P4 — APA y referencias

15. Completar 8 entradas [PV] en `Referencias_APA.md` vía Scopus/IEEE (sin inventar DOI).
16. Auditoría bidireccional cita en texto ↔ lista final (66 vs 24 autores citados sugiere gaps).

### P5 — Mejoras editoriales

17. Corregir numeración Cap. 5 (insertar 5.4; renumerar si aplica).
18. Verificar orden físico de capítulos en Word (Cap. 5 aparece antes de Cap. 1 en extracción de headings).
19. Incorporar Anexos A/B del DOCX integrado o referenciarlos explícitamente.

---

## Anexo A — Resultado `verify_tesis_doctoral_docx.py`

```json
{
  "sections": { "Dedicatoria": true, "Agradecimientos": true, "Resumen": true,
    "Abstract": true, "Introduccion": true, "Capitulo 5": true, "Capitulo 6": true,
    "Referencias bibliograficas": true },
  "tables_count": 18, "tables_ok": true,
  "images_count": 15, "images_ok": true,
  "references_count": 66, "references_expected": 66, "references_ok": true,
  "has_matd3_selection": true, "has_multiobjetivo": true,
  "has_drive_figures": true, "has_referencias_apa": true,
  "complete": true
}
```

**Interpretación:** el script valida presencia mínima, no calidad doctoral ni coherencia inferencial.

---

## Anexo B — Artefactos de auditoría generados

| Archivo | Contenido |
|---------|-----------|
| `outputs/_audit_tesis_docx_extract.json` | Figuras, citas, métricas texto |
| `outputs/_audit_tesis_tables.json` | Tablas y párrafos estadísticos |
| `outputs/_audit_all_tables.json` | 18 tablas Word completas |
| `outputs/_audit_referencias_apa.json` | Parse Referencias_APA.md |

---

*Auditoría realizada sin inventar datos numéricos ni enlaces. Todos los valores de Tablas 5.2–5.5 fueron cotejados contra `outputs/madrl_v3_20260627_164047/resumen_comparativo/`.*
