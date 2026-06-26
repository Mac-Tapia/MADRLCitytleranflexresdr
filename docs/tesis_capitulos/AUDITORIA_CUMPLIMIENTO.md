# Auditoría de Cumplimiento — Borrador de Tesis MADRL CityLearn Iquitos

**Fecha de auditoría:** 2026-06-25  
**Alcance:** `docs/Borrador_Tesis_MADRL_CityLearn_Iquitos.docx`, `scripts/generate_borrador_tesis_docx.py`, `docs/tesis_capitulos/*.md`  
**Referencia estructural:** `docs/informedetesis.txt`  
**Verificación de contexto:** `git rev-parse` → `D:/MADRLCitytleranflexresdr`; `git remote` → `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git` (conforme a AGENTS.md)

---

## 1. Resumen ejecutivo

| Aspecto | Veredicto |
|---|---|
| **Estructura obligatoria** (`informedetesis.txt`) | **CUMPLE CON OBSERVACIONES** |
| **Veracidad de datos** (fuentes del repo) | **CUMPLE CON OBSERVACIONES** |
| **Estilo y redacción** | **CUMPLE CON OBSERVACIONES** |
| **Placeholders pendientes** | **NO CUMPLE** (Cap. 5 parcial; ~25 ítems abiertos) |
| **VEREDICTO GLOBAL** | **CUMPLE CON OBSERVACIONES** |

El borrador **satisface la estructura mínima** exigida por `informedetesis.txt` en los archivos `.md` y en el `.docx`. Los datos numéricos clave de la corrida v4 (5 episodios) **coinciden con artefactos reales** en `outputs/`. El Capítulo 5 es **deliberadamente preliminar** y contiene múltiples marcadores `[REEMPLAZAR]` / `[Pendiente]` pendientes de la corrida canónica de 50 episodios en Colab. Se detectaron **inconsistencias menores** (rango de dimensiones de observación, escenario Global en docx, hiperparámetros YAML vs notebook) que no invalidan el borrador pero deben corregirse antes de la versión final.

---

## 2. Checklist de estructura (`informedetesis.txt`)

Leyenda: **PRESENTE** · **PARCIAL** · **FALTANTE**

### 2.0 Elementos transversales

| Ítem | .md (capítulos) | .docx | Estado |
|---|---|---|---|
| Portada (título, autor, universidad) | No en capítulos individuales | Sí (UNI, Mac Tapia, asesor `[por definir]`) | **PARCIAL** |
| Índice / TOC | `00_INDICE.md` (índice editorial) | Campo TOC Word (requiere F9) | **PRESENTE** |
| Resumen / Abstract | No como capítulo separado en .md | Sí (Resumen) | **PARCIAL** en .md |
| Referencias bibliográficas APA | `Referencias_APA.md` (~55 refs) | Sección «Referencias bibliográficas» (~50 refs) | **PRESENTE** |
| Bloques «PROMPT PERPLEXITY» | En todos los .md | No en .docx | N/A (metadato de borrador) |

### 2.1 Capítulo 1 — Introducción

| Subsección exigida | .md | .docx | Estado |
|---|---|---|---|
| Problema de investigación | §1.1 (PG, PE.1–3) | §1.1 | **PRESENTE** |
| Objetivos | §1.2 (OG, OE.1–3) | §1.2 | **PRESENTE** |
| Hipótesis | §1.3 (HG, HE.1–3) | §1.3 (H.G., H.1/H.2/H.3) | **PRESENTE** |
| Justificación | §1.4 (6 dimensiones) | §1.4 (viñetas) | **PRESENTE** |
| Alcances y limitaciones | §1.5 | §1.5 | **PRESENTE** |
| Estructura de la tesis | §1.6 (solo .md) | No | **PARCIAL** en .docx |

### 2.2 Capítulo 2 — Marco teórico

| Subsección exigida | .md | .docx | Estado |
|---|---|---|---|
| Estado del arte actualizado | §2.1 (4 ejes) | §2.1 | **PRESENTE** |
| Bases teóricas | §2.2 (Dec-POMDP, CTDE, 4 alg.) | §2.2 (+ subsecciones por eje) | **PRESENTE** |
| Trabajos relacionados | §2.3 (tabla + gap) | §2.3 | **PRESENTE** |

### 2.3 Capítulo 3 — Metodología

| Subsección exigida | .md | .docx | Estado |
|---|---|---|---|
| Tipo de investigación | §3.1 | §3.1 | **PRESENTE** |
| Diseño metodológico | Implícito en §3.1 | §3.2 (tabla escenarios) | **PRESENTE** |
| Datos utilizados | §3.4 (dataset Iquitos) | §3.3 | **PRESENTE** |
| Variables | §3.2 | §3.4 | **PRESENTE** |
| Técnicas | §3.5.1–3.5.2 | §3.5 (parcial) | **PRESENTE** |
| Herramientas | §3.5.3 | §3.5 | **PRESENTE** |
| Procedimiento experimental | §3.6 | §3.6 | **PRESENTE** |

### 2.4 Capítulo 4 — Desarrollo de la propuesta

| Subsección exigida | .md | .docx | Estado |
|---|---|---|---|
| Desarrollo del sistema | §4.1 (6 capas) | §4.1 | **PRESENTE** |
| Arquitectura | §4.1, §4.3 CTDE | §4.1, §4.3 | **PRESENTE** |
| Modelo de IA | §4.2 Dec-POMDP, §4.4 recompensa | §4.2, §4.5 | **PRESENTE** |
| Algoritmos | §4.5 (HAPPO/MASAC/MATD3/MAAC) | §4.4 | **PRESENTE** |
| Diseño experimental | §4.7 (12 corridas) | §4.7 | **PRESENTE** |
| Implementación | §4.8 | §4.8 | **PRESENTE** |

### 2.5 Capítulo 5 — Resultados

| Subsección exigida | .md | .docx | Estado |
|---|---|---|---|
| Experimentos realizados | §5.1 | §5.1 | **PRESENTE** (preliminar 5 ep) |
| Métricas utilizadas | §5.2 | §5.2 | **PRESENTE** |
| Resultados obtenidos | §5.3 | §5.3 | **PARCIAL** (scores ~ aproximados) |
| Comparación baseline / trabajos relacionados | §5.4 | §5.4 | **PARCIAL** (sin % mejora) |
| Tablas | Varias | Tablas 5.1–5.4 | **PRESENTE** |
| Figuras | §5.6 (listado, sin insertar) | §5.6 (listado, sin insertar) | **PARCIAL** |
| Discusión de resultados | §5.7 | §5.7 | **PRESENTE** |

### 2.6 Capítulo 6 — Conclusiones preliminares

| Subsección exigida | .md | .docx | Estado |
|---|---|---|---|
| Principales hallazgos | §6.1 | §6.1 | **PRESENTE** |
| Limitaciones encontradas | §6.2 | §6.2 | **PRESENTE** |
| Trabajo pendiente | §6.3 | §6.3 | **PRESENTE** |
| Plan para culminar la tesis | §6.4 (H1–H7) | §6.4 (cronograma) | **PRESENTE** |

### 2.7 Referencias bibliográficas

| Ítem | Estado |
|---|---|
| Formato APA en `Referencias_APA.md` | **PRESENTE** (~55 entradas; ~10 marcadas `[PV]`) |
| Formato APA en .docx | **PRESENTE** (~50 entradas; 6 marcadas `[PV]`) |
| Coherencia cita en-texto ↔ referencia | **PARCIAL** (no auditado exhaustivamente) |

---

## 3. Tabla de veracidad de datos

Leyenda: **SÍ** · **NO** · **NO VERIFICABLE**

| Afirmación en el informe | Valor en informe | Fuente real verificada | ¿Coincide? |
|---|---|---|---|
| Nº edificios (agentes) | 17 | `iquitos_citylearn_v3_dataset_evaluation.json` → `buildings: 17`; `citylearn_v3_madrl_training.yaml` → `buildings: 17` | **SÍ** |
| Horas del dataset | 26 304 | `citylearn_v3_madrl_training.yaml` → `total_hours: 26304` | **SÍ** |
| CSV auditados | 222 (0 NaN/Inf) | Documentado en Cap. 3; gates en `outputs/dataset_audit/` | **SÍ** (auditoría citada) |
| Cargadores EV | 185 | `iquitos_citylearn_v3_dataset_evaluation.json` → `charger_count: 185` | **SÍ** |
| BESS total | 26 266 kWh / 6 648 kW | Suma `der_sizing_audit.json` filas B01–B17 | **SÍ** |
| PV total | 48 790.9 kWp | Suma `der_sizing_audit.json` → `PV_schema_kWp` | **SÍ** |
| EV potencia nominal | 749.4 kW | `iquitos_citylearn_v3_dataset_evaluation.json` → `ev_nominal_power_kw: 749.4` | **SÍ** |
| Factor emisión base | 0.790 kgCO₂/kWh | MINAM RAGEI; modelo A4 en código | **SÍ** |
| CI dinámico | [0.6715, 0.790] | Fórmula A4: 0.790×(1−0.15×GHI/1000) | **SÍ** |
| Tarifas TOU | 0.26 / 0.38 USD/kWh | Cap. 1, 3; OSINERGMIN en referencias | **SÍ** |
| State dim global | 1856 | `iquitos_citylearn_v3_dataset_evaluation.json` → `citylearn_v3_load_evaluation.scenarios.E1.state_dim: 1856` | **SÍ** |
| Obs dim por agente | 57–330 | Auditado: **54–327** (`observation_dims` B05=54, B07=327) | **NO** (rango impreciso) |
| Acc dim por agente | 5–44 | Auditado: **5–44** (`action_dims` B05=5, B07=44) | **SÍ** |
| γ (descuento) corrida v4 | 0.9999 | `official_full_status.json` jobs → `--gamma 0.9999` | **SÍ** |
| Episodios corrida v4 | 5 × 8 760 = 43 800 pasos | `official_full_status.json` → `episodes: 5`, `num_env_steps: 43800` | **SÍ** |
| Episodios canónicos objetivo | 50 × 8 760 = 438 000 | `citylearn_v3_madrl_training.yaml` → `episodes: 50`, `num_env_steps: 438000`; notebook celda 6.1 | **SÍ** |
| Pesos recompensa E1 | 0.70 / 0.15 / 0.15 | `citylearn_v3_madrl_training.yaml` → `reward.axis_weights.E1` | **SÍ** |
| Pesos recompensa E2 | 0.15 / 0.70 / 0.15 | Idem `E2` | **SÍ** |
| Pesos recompensa E3 | 0.25 / 0.15 / 0.60 | Idem `E3` | **SÍ** |
| team_reward_ratio | 0.70 | `reward_function.py` perfiles; YAML `profiles.*.team_reward_ratio: 0.70` | **SÍ** |
| peak/ramp/ev weights | 0.45 / 0.35 / 0.25 | `reward_function.py`; YAML perfiles | **SÍ** |
| 12/12 jobs exit_code=0 | Completada | `official_full_status.json` → `status: completed`, 12 jobs `exit_code: 0` | **SÍ** |
| Duración ~39 h (v4) | 2026-06-15 → 2026-06-16 | `official_full_status.json` timestamps | **SÍ** |
| MATD3 score global | 0.7445 | `best_madrl_report.json` → `ranking[0].mean_score: 0.7445` | **SÍ** |
| Ranking MASAC / MAAC / HAPPO | 0.73 / 0.72 / 0.70 | `best_madrl_report.json` | **SÍ** |
| Kruskal-Wallis p | 0.0459 | `best_madrl_report.json` → `kruskal_wallis.p: 0.0459` | **SÍ** |
| Mann-Whitney MATD3 vs HAPPO p | 0.0182 | `comparaciones_mwu_madrl.csv` fila ALL/ALL | **SÍ** |
| Wilcoxon MATD3 vs HAPPO p | 2.62×10⁻⁶ | `comparaciones_wilcoxon_madrl.csv` → `2.618784806301214e-06` | **SÍ** |
| MATD3 OE.1/2/3 scores | 0.7486 / 0.7515 / 0.7333 | `ARQUITECTURA_PROYECTO_DEFENSA.md` (citado en Cap. 5) | **SÍ** (fuente secundaria del repo) |
| MASAC/MAAC/HAPPO scores ~ | ~0.73 / ~0.72 / ~0.70 | `best_madrl_report.json` (global); por escenario **aproximados** | **PARCIAL** |
| KPI MATD3-E3 carbon_emissions | 1.0847 | `training_summary.json` → `1.0847436489538798` | **SÍ** |
| KPI MATD3-E3 electricity_cost | 1.0092 | `training_summary.json` → `1.009200981675477` | **SÍ** |
| KPI MATD3-E3 ramping_average | 1.0009 | `training_summary.json` → `1.000857971275704` | **SÍ** |
| KPI MATD3-E3 peak_average | (no en tabla Cap.5 md) | `training_summary.json` → `1.0112345338045805` | **SÍ** (docx Tab. 5.2 sí lo incluye) |
| ev_departure_success_rate | 0.4749 | `training_summary.json` → `0.4748500579607883` | **SÍ** |
| pv_generation_total MATD3-E3 | 49 538 029.87 kWh | `training_summary.json` | **SÍ** |
| grid_import control/baseline | 11 237 105.75 / 11 149 381.98 | `training_summary.json` | **SÍ** |
| Comparación E1 mejor OE.1 HAPPO | 0.5679 | `comparison_summary.json` E1 | **SÍ** |
| Comparación E2 mejor global MATD3 | 0.7515 | `comparison_summary.json` E2 → `0.7514733838506504` | **SÍ** |
| Comparación E3 mejor global MATD3 | 0.7333 | `comparison_summary.json` E3 → `0.7332528976440587` | **SÍ** |
| HAPPO hidden v4 local | 256 | `official_full_status.json` → `happo_hidden_size: 256` | **SÍ** |
| HAPPO hidden canónico Colab | [512, 512] | Notebook celda 6.1 `HYPERPARAMS` | **SÍ** |
| MATD3 hidden canónico | 768 | Notebook celda 6.1 | **SÍ** |
| γ canónico en YAML algorithms | 0.99 (HAPPO/MATD3/MAAC) | `citylearn_v3_madrl_training.yaml` sección `algorithms.*.hyperparameters.gamma` | **NO** vs informe (0.9999) y vs corrida real |
| Corrida canónica 50 ep en Colab | «En curso» | `outputs/colab_50ep/` no verificado en esta auditoría | **NO VERIFICABLE** |
| % mejora vs baseline | Pendiente | No calculado en artefactos citados | **NO VERIFICABLE** |
| n_episodios en best_madrl_report | (no citado en capítulos) | `best_madrl_report.json` → `n_episodios: 75` | **Inconsistencia interna** del artefacto (no explicado en texto) |

### 3.1 Hallazgos de veracidad prioritarios

1. **Rango obs 57–330:** el mínimo auditado es **54** (Building_5), no 57. Corregir a **54–327** o citar `iquitos_citylearn_v3_dataset_evaluation.json`.
2. **Escenario «Global» [0.50, 0.25, 0.25]** en Tabla 3.1 del .docx: **no existe** en `scenario_manager.py` ni en YAML (`solo E1/E2/E3`). Eliminar o justificar como ablación futura.
3. **Hiperparámetros YAML `algorithms`:** `gamma: 0.99`, `hidden_size: 384` difieren de la corrida v4 ejecutada (`gamma: 0.9999`, `hidden: 256`) y del notebook Colab (`gamma: 0.9999`, HAPPO `[512,512]`, MATD3 `768`). El informe distingue bien v4 vs canónico en Cap. 4 .md, pero la Tabla 4.3 del .docx mezcla valores genéricos.
4. **`best_madrl_report.json` → `n_episodios: 75`:** no coincide con 5 episodios × 3 escenarios ni con la narrativa; investigar antes de citar en versión final.
5. **Resultados preliminares:** el informe declara explícitamente 5 episodios; las conclusiones que extrapolan a políticas convergentes están acotadas como preliminares — **correcto y honesto**.

---

## 4. Hallazgos de estilo y redacción

### 4.1 Tercera persona impersonal

| Ubicación | Hallazgo |
|---|---|
| Capítulos 1–6 (.md) | **Sin** «yo», «nosotros», «realizamos», «proponemos» en cuerpo académico |
| `.docx` (escaneo automático) | **0** ocurrencias de marcadores en primera persona |
| Bloques «PROMPT PARA PERPLEXITY» | Segunda persona dirigida a herramienta — **excluir de versión final** |

**Veredicto:** **CUMPLE** en prosa académica de capítulos y .docx.

### 4.2 Prosa enlazada vs listas

| Ubicación | Hallazgo |
|---|---|
| Cap. 1 §1.4 Justificación (.md) | Lista de viñetas sin párrafo introductorio — **PARCIAL** |
| Cap. 1 §1.4 (.docx) | Ídem: solo viñetas | **PARCIAL** |
| Cap. 6 §6.1 Hallazgos (.docx) | Lista de viñetas; falta párrafo de síntesis inicial | **PARCIAL** |
| Cap. 2–4, 5.7, 6.5 (.md) | Prosa argumentativa con tablas de apoyo | **PRESENTE** |
| Transiciones entre capítulos | Cap. 1 §1.6 enlaza estructura; .docx carece de §1.6 | **PARCIAL** en .docx |

### 4.3 Otros

- Los bloques **«PROMPT PARA PERPLEXITY»** y metadatos de borrador deben **eliminarse** antes de entrega oficial.
- El .docx usa «Capitulo» sin tilde y «diseno» sin tilde — revisar ortografía UNI.
- Portada .docx: «Unidad de Posgrado **[por confirmar]**», «Asesor: **[por definir]**».

---

## 5. Lista de placeholders pendientes

### 5.1 `[Pendiente: ...]` por archivo

| Archivo | Sección | Placeholder |
|---|---|---|
| `Capitulo_1_Introduccion.md` | §1.3 | Confirmar H0/H1 según norma UNI |
| `Capitulo_1_Introduccion.md` | §1.5 | Ampliar a múltiples semillas |
| `Capitulo_2_Marco_Teorico.md` | §2.1.4 | Añadir 2–3 referencias benchmarks 2025–2026 |
| `Capitulo_3_Metodologia.md` | §3.3 | Número de semillas para robustez > 1 |
| `Capitulo_4_Desarrollo_Propuesta.md` | §4.2 | Composición exacta 1856 dims estado global |
| `Capitulo_5_Resultados.md` | §5.3.1 | Scores exactos MASAC/MAAC/HAPPO por escenario (CSV) |
| `Capitulo_5_Resultados.md` | §5.3.2 | KPIs OE normalizados por algoritmo/escenario |
| `Capitulo_5_Resultados.md` | §5.4 | Porcentajes mejora MADRL vs baseline |
| `Capitulo_5_Resultados.md` | §5.5 | MWU/Wilcoxon pares restantes + tamaños efecto |
| `Capitulo_5_Resultados.md` | §5.6 | Insertar figuras PNG definitivas |
| `Referencias_APA.md` | Varias | ~10 entradas `[PV]` (autores/DOI) |

### 5.2 `[REEMPLAZAR ...]` (Capítulo 5)

| Archivo | Ubicaciones |
|---|---|
| `Capitulo_5_Resultados.md` | §5.1 (duración), §5.3 (ranking), §5.3.1 (tabla scores), §5.3.2 (KPIs), §5.4 (comparación baseline), §5.5 (estadística) — **6 bloques** |
| `00_INDICE.md` | Nota integración Colab/Drive |
| `.docx` | Aviso Cap. 5 + 3 `status_note` en §5.3, §5.4, §5.5 |

### 5.3 Otros marcadores

| Tipo | Ubicación | Texto |
|---|---|---|
| Portada | `.docx` | «Unidad de Posgrado [por confirmar: FIEE/FISI]» |
| Portada | `.docx` | «Asesor: [por definir]» |
| Referencias | `.docx` | 6 entradas `[PV]` |
| Índice | `.docx` | «Actualice este índice… (F9)» |

**Total estimado:** ~25 ítems abiertos (11 `[Pendiente]`, 6+ `[REEMPLAZAR]`, 8 administrativos/`[PV]`).

---

## 6. Coherencia generador ↔ capítulos ↔ .docx

| Aspecto | Observación |
|---|---|
| `generate_borrador_tesis_docx.py` | Genera estructura alineada con `informedetesis.txt`; 18 tablas; referencias APA embebidas |
| Cap. 4 .md vs .docx | .md más detallado (hiperparámetros v4 vs canónico); .docx añade capa UC3M y escenario «Global» no en .md |
| Cap. 5 | Ambos marcan preliminar 5 ep; mismos scores MATD3 y p-valores |
| `00_INDICE.md` | No se incluye como capítulo en .docx (correcto para entrega; el índice es TOC Word) |

---

## 7. Veredicto global y recomendaciones priorizadas

### Veredicto: **CUMPLE CON OBSERVACIONES**

El borrador es **entregable como avance de tesis** con evidencia experimental real (corrida v4 completa, dataset auditado, estadística básica). **No está listo como versión final** hasta cerrar Capítulo 5 con la corrida canónica de 50 episodios y eliminar placeholders.

### Recomendaciones (orden de prioridad)

| Prioridad | Acción |
|---|---|
| **P1** | Completar corrida canónica 50 ep (Colab) e integrar artefactos en `outputs/colab_50ep/`; **reemplazar** todos los `[REEMPLAZAR]` del Cap. 5 |
| **P2** | Extraer scores por escenario desde `scores_kpi_algoritmo_madrl.csv`; eliminar aproximaciones «~» |
| **P3** | Calcular **% mejora vs baseline** y completar matriz MWU/Wilcoxon (MATD3 vs MASAC, MATD3 vs MAAC) |
| **P4** | Insertar figuras PNG en §5.6 (al menos `baseline_gain_by_kpi`, `OE*_comparison`) |
| **P5** | Corregir rango obs **54–327**; eliminar escenario «Global» del .docx o documentarlo |
| **P6** | Alinear tabla hiperparámetros YAML `algorithms` con notebook 6.1 o citar explícitamente tres perfiles (YAML / v4 / Colab) |
| **P7** | Completar referencias `[PV]`; confirmar asesor y unidad de posgrado en portada |
| **P8** | Eliminar bloques Perplexity; convertir justificación y hallazgos de listas a prosa; pulir con norma UNI |
| **P9** | Ampliar a ≥3 semillas para robustez estadística (pendiente metodológico) |

---

## 8. Metodología de esta auditoría

- Lectura integral de `docs/informedetesis.txt`, `docs/tesis_capitulos/*.md`, `scripts/generate_borrador_tesis_docx.py`
- Extracción de estructura del `.docx` con `python-docx` (48 encabezados, 18 tablas, 290 párrafos)
- Contrastación de cifras contra: `official_full_status.json`, `best_madrl_report.json`, `training_summary.json`, `comparison_summary.json` (E1–E3), `iquitos_citylearn_v3_dataset_evaluation.json`, `der_sizing_audit.json`, `citylearn_v3_madrl_training.yaml`, `reward_function.py`, `comparaciones_mwu_madrl.csv`, `comparaciones_wilcoxon_madrl.csv`, notebook `madrl_citylearn_v3_tutorial.ipynb` (celda 6.1, solo lectura)
- **No se modificó** contenido de capítulos ni .docx (solo se creó este informe)

---

*Auditoría generada automáticamente como parte del cumplimiento del plan de tesis MADRL CityLearn Iquitos.*
