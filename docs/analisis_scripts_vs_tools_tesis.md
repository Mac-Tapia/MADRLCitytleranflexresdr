# Análisis exhaustivo: `scripts/` vs `tools/` y consolidación de tesis

**Fecha:** 2026-07-29  
**Repo:** `D:/MADRLCitytleranflexresdr`  
**Origen esperado:** `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`  
**Alcance:** archivos `.py` en `scripts/` y `tools/` (sin `CityLearn/`, sin `external/`, sin venvs dentro de `tools/skills/`)

---

## 1. Resumen ejecutivo

Se inventariaron y clasificaron los `.py` de `scripts/` y `tools/`. La **política explícita** (confirmada por el autor) es:

1. **Conservar** todo script de cálculos/pipelines del proyecto: dataset Iquitos/CityLearn, entrenamiento, evaluación, KPIs, Colab/Drive operativo, Docker/deploy, higiene de repo.
2. **Consolidar en una sola carpeta** solo lo que sirve a la **redacción de tesis final** (DOCX, ensamblado de capítulos, parches Word, figuras/tablas del documento, PDF de defensa).
3. **Eliminar** únicamente obsolescencia confiable (stubs one-shot sin callers).

**Carpeta única elegida:** `tools/thesis/`  
Motivo: `tools/README.md` ya planeaba subdividir `tools/` (`dataset/`, `audit/`, `reports/`); la redacción documental encaja ahí. `scripts/` se deja para CLIs operativos (`run_madrl_*`) y `verify_project_context.ps1` (no se mueve).

| Ámbito | Antes | Después |
|--------|------:|--------:|
| `scripts/*.py` | 18 | 2 |
| `tools/*.py` (raíz, sin skills) | ~109 | ~82 |
| `tools/thesis/*.py` | 0 | 39 (+ `__init__.py`) |
| Eliminados con confianza | — | 3 |

Dataset y pipelines (`generate_iquitos_dataset.py`, `fix_solar_pvlib.py`, `orchestrate_citylearn_dataset.py`, etc.) viven en **`tools/dataset/`** (reorg 2026-07-29; ver `docs/analisis_reorganizacion_tools_dataset.md`). Otros dominios: `tools/{eval,colab,drive,training,ops,figures,thesis}/`.

---

## 2. Inventario completo

### 2.1 `scripts/` (antes → después)

| Archivo | Rol | Destino |
|---------|-----|---------|
| `generate_borrador_tesis_docx.py` | Generador borrador DOCX Cap. 1–4 | → `tools/thesis/` |
| `thesis_doctoral_sections.py` | Cap. 5–6, resumen, verify | → `tools/thesis/` |
| `thesis_cap5_structured.py` | Estructura Cap. 5 | → `tools/thesis/` |
| `thesis_references_apa.py` | Referencias APA | → `tools/thesis/` |
| `generate_tesis_doctoral_final_docx.py` | Tesis doctoral Word canónica | → `tools/thesis/` |
| `generate_tesis_final_completa_integrada.py` | Integración FINAL_COMPLETA | → `tools/thesis/` |
| `merge_thesis_references.py` | Merge listas APA en Word | → `tools/thesis/` |
| `verify_tesis_doctoral_docx.py` | Verificación estructural DOCX | → `tools/thesis/` |
| `madrl_algorithm_analysis.py` | Perfiles de aprendizaje para Cap. 5 | → `tools/thesis/` |
| `complete_informe_final_gaps.py` | Parche huecos FINAL_COMPLETA | → `tools/thesis/` |
| `patch_informe_final_structure.py` | Alineación a `informedetesis.txt` | → `tools/thesis/` |
| `_audit_informe_final_structure.py` | Auditoría estructura Word | → `tools/thesis/` |
| `_audit_ref_sections.py` | Auditoría secciones de refs | → `tools/thesis/` |
| `_tmp_dump_abrir_este_64.py` | Dump one-shot párrafos Word | **ELIMINADO** |
| `_tmp_extract_a2.py` | Extracción one-shot Tabla A.2 | **ELIMINADO** |
| `_tmp_post_patch_status.py` | Dump one-shot post-parche | **ELIMINADO** |
| `run_madrl_nonparametric_battery.py` | Batería estadística no paramétrica | **QUEDA en scripts/** |
| `run_madrl_multicriteria_selection.py` | CLI TOPSIS/AHP multicriterio | **QUEDA en scripts/** |
| `verify_project_context.ps1` | Higiene de frontera de proyecto | **QUEDA en scripts/** (no es `.py`) |

### 2.2 `tools/` — tesis (movidos a `tools/thesis/`)

Generadores/parches documentales y soporte directo del Word:

- `thesis_antecedents_data.py`, `thesis_linear_alignment_audit.py`
- `generate_borrador_tesis_docx.py`, `generate_tesis_doctoral_final_docx.py`, `generate_tesis_final_completa_integrada.py`
- `thesis_doctoral_sections.py`, `thesis_cap5_structured.py`, `thesis_references_apa.py`
- `build_final_thesis_gdrive_objectives.py`, `build_final_thesis_50ep_antecedents.py`
- `rebuild_thesis_cap2_doctoral.py`, `rebuild_thesis_cap5_objective_aligned.py`
- `build_multiobjective_thesis_docx.py`, `build_multiobjective_thesis_pdf.py`
- `generate_drive_thesis_figures.py`, `fix_figura_5_1_checkpoint_coverage.py`, `fix_figura_a9_checkpoint_size.py`
- `update_pg_pe_oe_h_exact_docx.py`, `update_word_quantitative_50episodes.py`, `finalize_quantitative_word_qa.py`
- `integrate_kpi_drive_into_latest_docx.py`, `patch_cap3_cuasiexperimental_docx.py`, `patch_veredicto_metodologico_docx.py`
- `patch_thesis_cap6_and_remove_doctorado.py`, `patch_abrir_*.py`, `execute_close_cap6_63_64_65.py`
- `finish_a9_interps_after_a2.py`, `validate_and_patch_tabla_a2_a9_cap6.py`
- `build_defensa_pdf.py`, `build_defensa_pdf_pillow.py`
- auditorías Word: `_audit_*`, `complete_informe_final_gaps.py`, `patch_informe_final_structure.py`, `merge_thesis_references.py`, `verify_tesis_doctoral_docx.py`, `madrl_algorithm_analysis.py`

### 2.3 `tools/` — conservados (no tesis / cálculos de proyecto)

**Dataset / CityLearn / Iquitos (carpeta `tools/dataset/`):**  
`generate_iquitos_dataset.py`, `orchestrate_citylearn_dataset.py`, `fix_solar_pvlib.py`, `verify_solar.py`, `buildingcsv_inputs.py`, `dimension_ev_chargers.py`, `size_bess_optimal.py`, `distill_building_loads.py`, `evaluate_dataset.py`, `deep_dataset_analysis.py`, `check_training_dataset_ready.py`, `audit_citylearn_csv_integrity.py`, `audit_der_sizing.py`, `audit_training_dataset_provenance.py`, etc.

**Evaluación / KPIs / Drive operativo:**  
`run_complete_drive_kpi_objective_analysis.py`, `run_problem_objective_hypothesis_statistical_analysis.py`, `recalc_drive_kpis_*.py`, `inferential_audit_report.py`, `audit_drive_figure_integrity.py`, `aggregate_colab_drive_kpis.py`, `fetch_*drive*`, `validate_*colab*`, etc.

**Notebooks / Colab / infra:**  
`generate_colab_notebook.py`, `patch_notebook_*.py`, `harden_colab_notebook_launch.py`, `verify_notebook.py`, `verify_workflow_integrity.py`, etc.

**Reports ya en subcarpeta:** `tools/reports/*.py`  
**Skills locales:** `tools/skills/**` (fuera de alcance de consolidación de tesis).

---

## 3. Comparativa y overlaps

| Tema | `scripts/` (antes) | `tools/` (antes) | Conclusión |
|------|--------------------|------------------|------------|
| Generación DOCX tesis | Generadores canónicos recientes (Jul 29) | Parches/builds históricos + `thesis_antecedents_data` | Unificar en `tools/thesis/` |
| Cap. 5/6 | `thesis_doctoral_sections` + `thesis_cap5_structured` | Parches `patch_abrir_*`, `execute_close_*` | Mismo pipeline documental; conviven generador + parches |
| Referencias APA | `thesis_references_apa`, `merge_thesis_references` | — | Solo carpeta tesis |
| Stats MADRL | `run_madrl_nonparametric_battery`, `run_madrl_multicriteria_selection` | `run_*statistical*`, `inferential_audit_report` | **No** son redacción DOCX → se quedan fuera de `thesis/` |
| Dataset | — | `generate_iquitos_dataset`, `fix_solar_pvlib`, … | **Preservados** en `tools/dataset/` |
| Near-duplicates | `generate_tesis_doctoral_final_docx` vs `generate_tesis_final_completa_integrada` | Builds intermedios `build_final_thesis_*` | Roles distintos (regenerar vs integrar/parchear); se conservan ambos conjuntos dentro de `thesis/` |

---

## 4. Clasificación (tesis vs no-tesis)

### Tesis (ahora en `tools/thesis/`)
Todo lo listado en §2.2: generación/parcheo DOCX, PDF defensa, figuras/tablas del documento, datos de antecedentes y verificación estructural del Word.

### No-tesis (conservados fuera)
- Dataset / prep CityLearn  
- Entrenamiento / Colab / notebooks  
- KPIs y estadística operativa (incluye `scripts/run_madrl_*`)  
- Docker / deploy / verify de workflow  
- `scripts/verify_project_context.ps1`  

Devueltos a `tools/` tras revisión (no son solo redacción DOCX):  
- `inferential_audit_report.py`  
- `audit_drive_figure_integrity.py`  

---

## 5. Acciones realizadas

1. Verificación de frontera de proyecto (root/origin OK).  
2. Creación de `tools/thesis/` + `__init__.py` + `README.md`.  
3. Movimiento de ~39 módulos de redacción/parches DOCX desde `scripts/` y `tools/` hacia `tools/thesis/`.  
4. Actualización de `REPO`/`ROOT` a profundidad `parents[2]` (o `_THESIS_DIR.parents[1]`) e imports cruzados (`tools.thesis.*`, `sys.path` al directorio del paquete).  
5. Actualización de callers internos (`execute_close_cap6_…` → rutas `tools/thesis/…`).  
6. Actualización de `tools/README.md` con sección `thesis/`.  
7. Eliminación de 3 stubs `_tmp_*` en `scripts/`.  
8. Preservación/restauración de `tools/dataset/fix_solar_pvlib.py` (dataset; no tocado como lógica de negocio).  
9. Smoke test de imports: `thesis_references_apa` (78 refs) y `thesis_antecedents_data` (5+5).  

**No se hizo commit ni push.**

---

## 6. Archivos eliminados y justificación

| Archivo | Justificación |
|---------|---------------|
| `scripts/_tmp_dump_abrir_este_64.py` | One-shot de depuración de párrafos de un DOCX concreto; sin callers; prefijo `_tmp_` |
| `scripts/_tmp_extract_a2.py` | Extracción puntual Tabla A.2; sin callers |
| `scripts/_tmp_post_patch_status.py` | Dump post-parche one-shot; sin callers |

Ningún script de dataset, entrenamiento o KPIs fue eliminado.

---

## 7. Candidatos a eliminar (dudosos — NO eliminados)

| Archivo (en `tools/thesis/`) | Motivo de duda |
|------------------------------|----------------|
| `rebuild_thesis_cap5_objective_aligned.py` (2026-07-09) | Posiblemente supersedido por `thesis_cap5_structured.py` + generadores Jul 29 |
| `build_final_thesis_50ep_antecedents.py` | Eslabón intermedio; salida puede estar ya incorporada en cadena posterior |
| `complete_informe_final_gaps.py` / `patch_informe_final_structure.py` | Parches históricos; el generador canónico puede cubrir el mismo contenido |
| `build_defensa_pdf.py` vs `build_defensa_pdf_pillow.py` | Duplicado funcional (reportlab vs pillow); ambos útiles como fallback |

Revisar en una pasada posterior con evidencia de no-uso antes de borrar.

---

## 8. Estructura final de la carpeta única de tesis

```
tools/thesis/
  README.md
  __init__.py
  # Núcleo canónico
  generate_borrador_tesis_docx.py
  generate_tesis_doctoral_final_docx.py
  generate_tesis_final_completa_integrada.py
  verify_tesis_doctoral_docx.py
  thesis_doctoral_sections.py
  thesis_cap5_structured.py
  thesis_references_apa.py
  thesis_antecedents_data.py
  madrl_algorithm_analysis.py
  merge_thesis_references.py
  # Parches / builds documentales
  update_pg_pe_oe_h_exact_docx.py
  patch_cap3_cuasiexperimental_docx.py
  integrate_kpi_drive_into_latest_docx.py
  update_word_quantitative_50episodes.py
  finalize_quantitative_word_qa.py
  build_final_thesis_*.py
  rebuild_thesis_*.py
  patch_*.py
  execute_close_cap6_63_64_65.py
  fix_figura_*.py
  generate_drive_thesis_figures.py
  build_multiobjective_thesis_*.py
  build_defensa_pdf*.py
  _audit_*.py
  …
```

Operativo (fuera de tesis):

```
scripts/
  run_madrl_nonparametric_battery.py
  run_madrl_multicriteria_selection.py
  verify_project_context.ps1
tools/
  dataset/   # generate_iquitos, fix_solar_pvlib, orchestrate, …
  eval/ colab/ drive/ training/ ops/ figures/
  thesis/    # redacción DOCX (intacta)
```

---

## 9. Cómo ejecutar los scripts de tesis consolidados

Desde la raíz del repo, con el venv canónico:

```powershell
# Borrador Cap. 1–4
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\generate_borrador_tesis_docx.py

# Tesis doctoral canónica + verificación
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\generate_tesis_doctoral_final_docx.py
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\verify_tesis_doctoral_docx.py

# Integración FINAL_COMPLETA (si se parte de base con diagramas)
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\generate_tesis_final_completa_integrada.py

# Parches recientes sobre Word vigente
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\update_pg_pe_oe_h_exact_docx.py
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\patch_cap3_cuasiexperimental_docx.py
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\integrate_kpi_drive_into_latest_docx.py
```

Estadística operativa (no tesis, sigue en `scripts/`):

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe scripts\run_madrl_nonparametric_battery.py
.\.venv39-citylearn-v3\Scripts\python.exe scripts\run_madrl_multicriteria_selection.py
```

Dataset (conservado en `tools/dataset/`):

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\orchestrate_citylearn_dataset.py
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\fix_solar_pvlib.py
.\.venv39-citylearn-v3\Scripts\python.exe tools\dataset\generate_iquitos_dataset.py
```

---

## Notas / bloqueos menores

- `scripts/verify_project_context.ps1` puede tardar mucho (~90s) por el barrido recursivo de `tools/skills/` (miles de `.py` de venvs embebidos); root/origin OK.
- Algunas referencias en docs archivados (`docs/_archive/…`) aún mencionan rutas antiguas `scripts/…`; no se reescribieron archivos históricos obsoletos.
- `CityLearn/scripts/generate_thesis_objective_evidence.py` es ruta del submódulo CityLearn (no es script movido del repo) — no aplicar.

---

## 10. Seguimiento de integridad (2026-07-29, post-consolidación)

**Contexto verificado:** root `D:/MADRLCitytleranflexresdr`, origin `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`.

**Spot-check `tools/thesis/`:** ~39 módulos `.py` + `__init__.py` + `README.md` presentes.

**Dataset (conservados en `tools/dataset/`):** confirmados `generate_iquitos_dataset.py`, `fix_solar_pvlib.py`, `orchestrate_citylearn_dataset.py`, `verify_solar.py`, `buildingcsv_inputs.py`.

**Referencias rotas corregidas (rutas → `tools/thesis/`):**
- `agent-skills/madrl-citylearn-thesis-integrated/SKILL.md` (bloqueador previo; actualizado)
- `agent-skills/madrl-citylearn-thesis-integrated/references/module-b-thesis-report.md`
- `docs/tesis_capitulos/Capitulo_4_Desarrollo_Propuesta.md`
- `docs/tesis_capitulos/AUDITORIA_CUMPLIMIENTO.md`
- `docs/AUDITORIA_INTEGRAL_TESIS_DOCTORAL_2026-07-07.md`
- `docs/VALIDACION_REFERENCIAS_UNIFICADAS_2026-07-15.md`
- `scripts/fetch_and_generate_drive_figures.ps1` → `tools/thesis/generate_drive_thesis_figures.py`

**Compatibilidad residual en `scripts/`:**
- `scripts/generate_borrador_tesis_docx.py` — wrapper CLI → `tools/thesis/…`
- `scripts/thesis_doctoral_sections.py` — shim de import → `tools.thesis.thesis_doctoral_sections`
- Operativos intactos: `run_madrl_nonparametric_battery.py`, `run_madrl_multicriteria_selection.py`, `verify_project_context.ps1`

**Pendiente intencional:** rutas antiguas solo en `docs/_archive/…` (no reescritas).

**Smoke:** imports `tools.thesis.thesis_antecedents_data` y `tools.thesis.thesis_references_apa` OK. Sin commit.
---

## 11. Pasada 2 — unificación hacia 3 Word canónicos (2026-07-29)

**Objetivo:** limpiar one-shots que apuntaban a Word eliminados y recentrar el pipeline en Tesis / Informe / ABRIR INDICES.

**Hecho:**
- `tools/thesis/thesis_word_canons.py` — rutas de los 3 canons
- `tools/thesis/sync_cap5_to_canon_words.py` — sync Cap.5 TOC-safe
- `tools/thesis/run_thesis_word_pipeline.py` — orquestador (default: no regenera Tesis)
- Rewire de PG/OE/H, Cap.3, quantitative, verify `--all-canons`
- Archivados ~22 one-shots → `tools/thesis/_archive/2026-07-29_one_shot/` (**eliminados** 2026-07-29; ver `AUDITORIA_TOOLS_2026-07-29.md`)
- Restaurado `docs/ABRIR_ESTE_WORD_FINAL_INDICES_AUTOMATICOS.docx` desde archive

**Smoke:** dry-run sync Cap.5 OK (Informe + ABRIR ranges localizados).

---

## 12. Addendum paths dataset (2026-07-29, post-reorg tools/)

Tras la reorganizacion documentada en `docs/analisis_reorganizacion_tools_dataset.md`:
- Dataset canonico: **`tools/dataset/`** (20 `.py` + README).
- Dominios: `eval/`, `colab/`, `drive/`, `training/`, `ops/`, `figures/`, `thesis/` (sin mover tesis).
- Raiz `tools/*.py` vacia a proposito (salvo wrapper de compatibilidad puntual si aplica).
