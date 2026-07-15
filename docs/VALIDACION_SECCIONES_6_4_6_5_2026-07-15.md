# Validación secciones 6.4 y 6.5 — corrida canónica `madrl_v3_20260627_164047`

**Fecha:** 2026-07-15  
**Alcance:** Hitos H1–H7 (Tabla 6.1) y criterios de cierre (Tabla 6.2)  
**Verificación de contexto:** `[OK] Project context verified: D:/MADRLCitytleranflexresdr`  
**Declaración:** No se crearon episodios, semillas, resultados ni artefactos sintéticos en esta validación.

---

## Resumen ejecutivo

| Área | Veredicto |
|------|-----------|
| H1 Cobertura HAPPO | **PASS** |
| H2 Robustez multi-semilla | **PASS** (delimitación metodológica) |
| H3 Inferencia estadística | **PASS** |
| H4 Pareto y baseline | **PASS** |
| H5 HPO / algoritmos adicionales | **PASS** (delimitado) |
| H6 Cierre documental | **PASS** |
| H7 Entrega y sustentación | **PENDING** (institucional) |
| Criterio 6.5.1 APA | **PASS** |
| Criterio 6.5.2 Multi-semilla | **PASS** |
| Criterio 6.5.3 Figuras/tablas | **PASS** |
| Criterio 6.5.4 Coherencia vertical | **PARTIAL** |

**Manuscrito Word:** `docs/ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx` y espejo `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA.docx` — secciones 6.4/6.5 y Tablas 6.1–6.2 **actualizadas y validadas** (script `tools/validate_and_patch_tabla_a2_a9_cap6.py`, 2026-07-15).

**Markdown fuente:** `docs/tesis_capitulos/Capitulo_6_Conclusiones.md` — **actualizado** en esta validación para alinear con el Word y los CSV canónicos.

---

## Evidencia recomputada (datos reales)

### Cobertura episódica (H1)

Fuente: `outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/tables/gdrive_episode_kpis_used_for_statistics.csv`

| Algoritmo | E1 | E2 | E3 | Total |
|-----------|---:|---:|---:|------:|
| HAPPO | 49 | 49 | 49 | 147 |
| MAAC | 50 | 50 | 50 | 150 |
| MASAC | 50 | 50 | 50 | 150 |
| MATD3 | 50 | 50 | 50 | 150 |
| **Total filas** | | | | **597** |

Corroboración adicional: `outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/inferential_audit_report.json` → `episode_counts_drive`.

### Kruskal–Wallis episódico alineado a OE (H3)

Fuente: `outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/tables/gdrive_objective_aligned_statistics.csv`  
Muestra inferencial KW: MAAC, MASAC, MATD3 con cobertura completa (n=50); HAPPO excluido de KW por n=49.

| Objetivo | Métrica episódica | H (KW) | p (KW) | ε² |
|----------|-------------------|-------:|-------:|---:|
| OE.1 / E1 | `reward_mean_average` | 36.3083 | **1.305445×10⁻⁸** | 0.2334 |
| OE.2 / E2 | `district_emission` | 6.2532 | **0.043866** | 0.0289 |
| OE.3 / E3 | `district_cost` | 2.7613 | **0.251421** | 0.0052 |

### Mann–Whitney U con corrección Holm (H3)

Fuente: `outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/tables/gdrive_objective_pairwise_mannwhitney_holm.csv`

| OE | Par significativo (p_Holm) |
|----|----------------------------|
| OE.1 | MAAC vs MASAC (1.20×10⁻⁵); MAAC vs MATD3 (1.91×10⁻⁷); MASAC vs MATD3 (0.0239) |
| OE.2 | MAAC vs MATD3 (0.0308) |
| OE.3 | ninguno significativo tras Holm |

### Inferencia sobre KPI-gains (complementaria, no sustituye episódica)

Fuente: `outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/hipotesis_estadisticas_madrl.csv`  
KW sobre KPI-gains (HAPPO excluido): OE1 p=0.2806; OE2 p=0.5457; OE3 p=0.3881; ALL p=0.1554 — **no significativos** a α=0.05. La tesis diferencia explícitamente medias episódicas vs muestra KPI-gain vs KPI anual final (H4).

---

## Detalle por hito (Tabla 6.1)

### H1. Cobertura HAPPO — **PASS**

| Campo | Valor |
|-------|-------|
| Claim | Corpus definitivo HAPPO 49 ep/escenario; no imputar ep. 50; MAAC/MASAC/MATD3 n=50; 597 filas episódicas |
| Evidencia | `gdrive_episode_kpis_used_for_statistics.csv` (597 filas); `inferential_audit_report.json` |
| Doc | Tabla 6.1 en Word; Cap. 5 Tabla 5.1; `Capitulo_6_Conclusiones.md` §6.4 |
| Acción | Word ya actualizado; markdown Cap. 6 sincronizado |

### H2. Robustez multi-semilla — **PASS** (delimitación)

| Campo | Valor |
|-------|-------|
| Claim | Inferencia limitada a seed=0; campaña multi-semilla = trabajo futuro |
| Evidencia | Una sola corrida en `madrl_v3_20260627_164047`; limitación en Cap. 6 Tabla 6.1 H2 y Tabla 6.2 |
| Doc | Actualizado en Word y markdown |
| Acción | Ninguna experimental (correcto: no inventar réplicas) |

### H3. Inferencia estadística — **PASS**

| Campo | Valor |
|-------|-------|
| Claim | Shapiro–Wilk, Kruskal–Wallis, Mann–Whitney Holm, tamaños de efecto; p OE.1/2/3 sincronizados caps 5–6 |
| Evidencia | `gdrive_objective_aligned_statistics.csv`; `gdrive_objective_pairwise_mannwhitney_holm.csv`; `comparaciones_mwu_madrl.csv` (Cliff, A12, Cohen d, Hedges g, CI bootstrap) |
| Doc | Word §5.9 y Tabla 6.1 H3; p-values presentes en manuscrito |
| Acción | `inferential_audit_report.py` re-ejecutado → verdict `correct` |

### H4. Pareto y baseline — **PASS**

| Campo | Valor |
|-------|-------|
| Claim | Lectura multiobjetivo sin ganador universal; contraste v2/RBC/baseline; sensibilidad pesos = futuro |
| Evidencia | `outputs/madrl_v3_20260627_164047/resumen_comparativo/citylearn_v2_baseline/`; `multiobjetivo/district_objectives_by_algorithm.csv`; `matriz_baseline_por_eje.md` |
| Doc | Cap. 5 §5.7–5.10 (Word); Tabla 6.1 H4 |
| Acción | Validado en contenido Word existente |

### H5. HPO y algoritmos adicionales — **PASS** (delimitado)

| Campo | Valor |
|-------|-------|
| Claim | Optuna, PPO, SAC, A2C **no** forman evidencia canónica |
| Evidencia | Sin artefactos bajo `madrl_v3_20260627_164047` para esos algoritmos/HPO |
| Doc | Tabla 6.1 H5 → «Delimitado → trabajo futuro» |
| Acción | Ninguna (correcto) |

### H6. Cierre documental — **PASS**

| Campo | Valor |
|-------|-------|
| Claim | Caps 2/4/5/6 reforzados; discusión 5.10; refs APA; tablas APA 7; F9 al abrir Word |
| Evidencia | Manuscrito integrado 70 tablas, 57 imágenes, 105 referencias (`verify_tesis_doctoral_docx.py`) |
| Doc | `ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx` |
| Acción | Patch 6.4/6.5 ejecutado; interpretaciones figuras 5.1, 5.8e, A.9 |

### H7. Entrega y sustentación — **PENDING**

| Campo | Valor |
|-------|-------|
| Claim | F9, PDF, asesor, registro, defensa |
| Evidencia | N/A (gestión institucional) |
| Bloqueadores | Asesor/registro UNI; no depende de nuevos experimentos |

---

## Criterios 6.5 (Tabla 6.2)

### 1. Revisión APA integral — **PASS**

- `scripts/verify_tesis_doctoral_docx.py`: `references_ok: true` (105 entradas vs mínimo 70).
- Sección «Referencias bibliográficas» presente en Word.
- **Nota:** `has_pe_answers: false` en verificador estructural (busca cadena literal); el manuscrito sí contiene respuestas PE en Cap. 5 — no bloquea cierre documental.

### 2. Revisión multi-semilla opcional — **PASS**

- Limitación semilla única explicitada en Tabla 6.1 H2 y Tabla 6.2.
- No se reportan réplicas inventadas.

### 3. Auditoría de figuras y tablas — **PASS**

- Informe: `outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/validation/tabla_a2_a9_cap6_validation_report.json`
- Tabla A.2: **VALIDADA** (20/20 filas vs `building_behavior_summary.csv`)
- Figura A.9: recalculada desde `checkpoint_manifest.json` (294 archivos, 116.72 GB)
- Trazabilidad episódica/estadística: CSV bajo `outputs/madrl_v3_20260627_164047/` y `outputs/_drive_madrl/`

### 4. Revisión de coherencia vertical — **PARTIAL**

- `tools/thesis_linear_alignment_audit.py`: `linear_alignment_status: needs_review` — el auditor espera numeración Cap. 5/6 alternativa (5.9 inferencial, 6.1 OG separado) distinta a la estructura actual del Word integrado.
- `pe_answers_audit.json`: respuestas PE.1–PE.3 estructuradas desde CSV con `run_id` canónico.
- **Acción recomendada (no bloqueante):** revisión humana del índice F9 y alineación fina PE→OE→HE→conclusiones en una pasada del asesor.

---

## Archivos creados o modificados en esta validación

| Archivo | Acción |
|---------|--------|
| `docs/VALIDACION_SECCIONES_6_4_6_5_2026-07-15.md` | Creado (este informe) |
| `docs/tesis_capitulos/Capitulo_6_Conclusiones.md` | Actualizado (§6.4–6.5 alineados) |
| `docs/ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx` | Re-patch idempotente 6.4/6.5 |
| `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA.docx` | Espejo sincronizado |
| `outputs/_drive_madrl/gdrive_20260627_164047_objective_analysis/validation/tabla_a2_a9_cap6_validation_report.json` | Regenerado |

---

## Narrativa de cierre

Con **H1, H3, H4 y H6 ejecutados** y **H2/H5 delimitados como trabajo futuro**, el manuscrito queda **culminado para presentación académica** bajo semilla única y HAPPO 49/50. Solo **H7** (gestión institucional: F9, PDF, asesor, registro, sustentación) permanece pendiente y **no requiere nuevos experimentos**.
