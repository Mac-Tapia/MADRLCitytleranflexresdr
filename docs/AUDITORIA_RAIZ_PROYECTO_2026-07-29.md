# Auditoría raíz del proyecto — 2026-07-29

**Repo:** `D:/MADRLCitytleranflexresdr`  
**Origen git:** `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`  
**Contexto:** cwd/root + origin correctos (check manual tras hang de `verify_project_context.ps1`).  
**Alcance:** inventario raíz, duplicados Word, clutter temp, canonicidad thesis, gaps de reproducción.  
**No tocado:** `CityLearn/` (salvo lectura), `external/`, submodules, corridas de entrenamiento reales.

---

## 1. Veredicto ejecutivo

| Pregunta | Respuesta |
|---|---|
| ¿Raíz lista para reproducción? | **SÍ** (evidencia 50 ep + punteros alineados; sin carpetas `_archive` de proyecto; campaña 12-seed pendiente como gap Cap. 6) |
| Words canónicos en `docs/` | **Exactamente 2** |
| Run evidencia 50 ep | Presente (`madrl_v3_20260627_164047` + `_drive_madrl`) |
| Política retención | **DELETE** no vinculados (sin retención `_archive`) |

---

## 2. Inventario raíz (post-limpieza)

### Carpetas

| Ítem | Clasificación | Propósito |
|---|---|---|
| `.git` / `.github` | KEEP_SUPPORT | Control de versiones / CI |
| `.venv39-citylearn-v3` | KEEP_SUPPORT | Entorno Python 3.9 de entrenamiento |
| `.vscode` / `.cursor` / `.claude` / `.sixth` | KEEP_SUPPORT | IDE / agentes locales |
| `.cache` / `.pytest_cache` / `.ruff_cache` | KEEP_SUPPORT | Caches regenerables (no borrar agresivo) |
| `agent-skills/` | KEEP_SUPPORT | Skills locales thesis/dataset/literatura |
| `CityLearn/` | KEEP_CANON (dep) | Submódulo / código entrenamiento — **no editar** salvo instrucción |
| `data/` | KEEP_SUPPORT | Auditorías dataset, caches |
| `deploy/` | KEEP_SUPPORT | Despliegue Docker/AWS |
| `docs/` | KEEP_CANON | Thesis Word×2 + MD capítulos + manuals |
| `external/` | KEEP_SUPPORT (dep) | Dependencias externas — **no editar** |
| `outputs/` | KEEP_CANON + ARCHIVE | Resultados; canónico 50 ep + `_archive` |
| `scripts/` | KEEP_SUPPORT | Entry points PowerShell / wrappers |
| `tests/` | KEEP_SUPPORT | Tests del proyecto |
| `tools/` | KEEP_SUPPORT | Dataset, thesis generators, ops, skills MCP |
| `uc3m/` | KEEP_SUPPORT | Paquete local / referencias UC3M |

### Archivos raíz

| Ítem | Clasificación | Propósito |
|---|---|---|
| `AGENTS.md` | KEEP_CANON | Frontera de proyecto / reglas agentes |
| `README.md` | KEEP_CANON | Documentación principal |
| `pyproject.toml` / `requirements.txt` / `uv.lock` | KEEP_CANON | Dependencias |
| `Dockerfile` / `.dockerignore` | KEEP_SUPPORT | Contenedorización |
| `LANZAR_ENTRENAMIENTO_V4.bat` | KEEP_SUPPORT | Atajo Windows a entrenamiento |
| `pyrightconfig.json` / `cspell.json` / `.markdownlint*` / `.gitattributes` / `.gitignore` / `.gitmodules` | KEEP_SUPPORT | Tooling |

### Eliminados / archivados de raíz (esta pasada)

Antes había ~65 ítems incl. muchos `_tmp_*`, `nb_*.txt`, `tmp/`, `How to use Claude/`, `ESTRATEGIA_*.md`, `build/`/`dist/`. Tras limpieza la raíz operativa queda ~35 ítems limpios.

---

## 3. Canonicidad thesis (Word + MD)

### Fuentes consultadas

- `docs/00_INDEX.md`
- `docs/CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md`
- `docs/workflow_manifest.json`
- `docs/_word_inventory.json` / `docs/_word_hashes.json` (refrescados)
- `docs/tesis_capitulos/00_INDICE.md`
- `docs/_archive/2026-07-29_docs_consolidation/README.md`

### Exactamente 2 Word en `docs/` (KEEP_CANON)

| Archivo | Rol | SHA256 (prefijo) | Tamaño |
|---|---|---|---|
| `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` | Fuente de verdad (Cap. 5 + KPIs Drive) | `F391E402F94ABC02…` | 5 272 893 |
| `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` | Informe final 50 ep + TOC | `3EB719E7CFC853E1…` | 4 655 651 |

### MD canónicos

- Capítulos: `docs/tesis_capitulos/Capitulo_{1..6}_*.md` + `Referencias_APA.md`
- Índice: `docs/tesis_capitulos/00_INDICE.md`
- Contrato workflow: `docs/workflow_manifest.json`

### Duplicados Word tratados

| Archivo | Decisión | Evidencia |
|---|---|---|
| `docs/ABRIR_ESTE_WORD_FINAL_INDICES_AUTOMATICOS.docx` | **DELETE** | SHA256 idéntico a copia en `docs/_archive/2026-07-29_docs_consolidation/word_archived_to_2/` (`F8333EE2…`) |
| `How to use Claude/Tesis_Doctoral_…_2_1_2_2_v2.docx` | **ARCHIVE** | Hash distinto (`0BCF225B…`); no canónico → `docs/_archive/2026-07-29_root_cleanup/word_misplaced/` |
| Words ya en `_archive/2026-07-29_docs_consolidation/` | KEEP_ARCHIVE | Incl. CAP3_REFS y FINAL_COMPLETA_KPI_DRIVE_LATEST |

**Regla dura (sin cambio):** no crear nuevos `.docx` en `docs/`; mejoras solo en los 2 canónicos.

---

## 4. Outputs — canónico vs archive vs clutter

### KEEP_CANON (reproducción / Cap. V)

| Path | Rol |
|---|---|
| `outputs/madrl_v3_20260627_164047/` | Run 50 episodios Drive |
| `outputs/_drive_madrl/` | Espejo Drive + `kpi_recalc_20260728/` |
| `outputs/madrl_nonparametric_battery/` | Batería no paramétrica |
| `outputs/latest_colab_output_root.txt` | Puntero → run canónico |
| `outputs/thesis_objective_evidence/` | Evidencia generada para thesis |
| `outputs/comparison_citylearn_v2_vs_v3_madrl/` | Comparación v2 vs v3 |
| `outputs/citylearn_v2_original_benchmark/` | Baseline v2 |

### ARCHIVE / no operativo (conservados; documentados)

| Path | Nota |
|---|---|
| `outputs/_archive/` | Histórico (incl. esta limpieza) |
| `outputs/citylearn_v3_madrl_full_20260615_074011_v4/` | Run anterior / no 50 ep Drive |
| `outputs/citylearn_v3_madrl_readiness_dryrun_*` | Dry-run |
| `outputs/_validate_*` / `_masac_diag_dryrun` / `_tmp_nonparametric_12seeds` | Validaciones / diag |
| `outputs/_nb_cells` / `test_notebook` / `colab_50ep` | Auxiliares |
| `outputs/019f991f-…` | Artefacto comparativa Excel puntual |
| `outputs/madrl_multicriteria_selection*` | Demos / selección |

### Clutter de archivos en raíz `outputs/` → archivado

28 archivos `_nb_*` / `_tmp_*` / `_audit_*` movidos a:

`outputs/_archive/2026-07-29_root_cleanup/outputs_root_tmp_nb/`

### Gap puntero visible — **cerrado** (Follow-up 2026-07-29)

```
latest_colab_output_root.txt              → outputs/madrl_v3_20260627_164047  (OK)
latest_visible_training_output_root.txt   → outputs/madrl_v3_20260627_164047  (OK; antes dry-run)
```

Dry-run/validate top-level movidos a `outputs/_archive/2026-07-29_root_cleanup/validate_dryrun/`.

---

## 5. Reproducción — checklist

| Requisito | Estado |
|---|---|
| `scripts/verify_project_context.ps1` | Presente (script colgó en esta sesión; check manual OK) |
| Dataset `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json` | Presente |
| Launcher `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` | Presente |
| Wrapper `scripts/run_citylearn_v3_full_training_visible.ps1` | Presente |
| `LANZAR_ENTRENAMIENTO_V4.bat` | Presente |
| `docs/workflow_manifest.json` | Presente (contrato canónico) |
| Manuales Colab / deps | Presentes en `docs/` |
| venv `.venv39-citylearn-v3` | Presente |
| Evidencia 50 ep local | Presente |
| Campaña 12-seed completa | **Gap** (smoke n=3 documentado; campaña pendiente) |
| Skills globales thesis | **No usadas** — locales en `agent-skills/` + `tools/skills/` |

---

## 6. Acciones ejecutadas (conteos)

| Acción | Cantidad (aprox.) | Detalle |
|---|---|---|
| **DELETE** | 11 acciones | ABRIR duplicado exacto; 3 temps vacíos/efímeros; `build/` `dist/` `__pycache__/` `uc3m.egg-info/`; dirs vacíos `_backups`/`_working`; carpeta vacía `How to use Claude/` |
| **ARCHIVE** | 52+ paths (+ árbol `tmp/` ~1.2k archivos) | Root `_tmp_*`, `nb_*.txt`, Word misplaced, clutter `outputs/` raíz |
| **MOVED** | 1 | `ESTRATEGIA_3PILARES_MADRL.md` → `docs/` |
| **KEEP** | Raíz limpia + 2 Word + outputs canónicos | Sin commit |

Logs: `docs/_archive/2026-07-29_root_cleanup/cleanup_actions.txt`

---

## 7. Estructura propuesta final (raíz)

```
MADRLCitytleranflexresdr/
  AGENTS.md, README.md, Dockerfile, pyproject.toml, requirements.txt, uv.lock
  LANZAR_ENTRENAMIENTO_V4.bat, pyrightconfig.json, cspell.json, .git*
  agent-skills/     # skills thesis/dataset locales
  CityLearn/        # dep — no editar
  data/             # audits/cache dataset
  deploy/
  docs/             # SOLO 2 .docx + MD + _archive/
  external/         # dep — no editar
  outputs/          # canónicos + _archive/ (sin dumps sueltos en raíz)
  scripts/
  tests/
  tools/            # generators, ops, dataset, skills MCP
  uc3m/
  .venv39-citylearn-v3/
```

**Prohibido en raíz:** `_tmp_*`, `nb_*.txt`, Word thesis sueltos, `~$*.docx`, `tmp/` de edición.

---

## 8. Problemas restantes / gaps

1. ~~**Puntero visible** apunta a dry-run~~ → **cerrado** en Follow-up 2026-07-29.
2. ~~**Carpetas dry-run/validate** en `outputs/`~~ → **archivadas** en Follow-up 2026-07-29.
3. **`verify_project_context.ps1`** colgó (>30 s sin stdout) — investigar aparte (check manual OK).
4. **Campaña multi-semilla 12 seeds** pendiente (Cap. 6 / Cap. 5 lo documentan) — **no ejecutada** en este follow-up.
5. **Informe Word:** actualizar TOC (F9) tras ediciones Cap. 5 si aplica.
6. Caches IDE (`.cache`, `.pytest_cache`, `.ruff_cache`) siguen en raíz — normales; opcional `.gitignore` ya debería cubrirlas.
7. `outputs/informe_tecnico_supervision_20260620.json` queda en raíz outputs (no `_tmp_`); candidata ARCHIVE menor.
8. Auxiliares no movidos (conservador): `_tmp_nonparametric_12seeds`, `madrl_nonparametric_battery_smoke_n3`, `colab_50ep`, `_nb_cells`, `test_notebook`.

---

## 9. Cambios filesystem clave

### DELETE
- `docs/ABRIR_ESTE_WORD_FINAL_INDICES_AUTOMATICOS.docx` (dup hash)
- `_tmp_nb_diag_err.txt`, `_tmp_pyright_out.json`, `.git_commit_msg.tmp`
- `build/`, `dist/`, `__pycache__/`, `uc3m.egg-info/`
- `docs/_backups/`, `docs/_working/` (vacíos)
- `How to use Claude/` (vacío tras archive)

### ARCHIVE
- `docs/_archive/2026-07-29_root_cleanup/` (word_misplaced, root_clutter, notebook_dumps, tmp_word_edit_scripts)
- `outputs/_archive/2026-07-29_root_cleanup/outputs_root_tmp_nb/`

### MOVE
- `ESTRATEGIA_3PILARES_MADRL.md` → `docs/ESTRATEGIA_3PILARES_MADRL.md`

### REFRESH
- `docs/_word_inventory.json`, `docs/_word_hashes.json` → solo 2 Word

---

## 10. No commit

Esta auditoría **no** creó commit git (según instrucción del usuario).

---

## Follow-up 2026-07-29 — cerrar gaps de reproducción

**Contexto:** check manual tras hang de `verify_project_context.ps1` (cwd/root = `D:/MADRLCitytleranflexresdr`, origin `Mac-Tapia/MADRLCitytleranflexresdr`). Sin entrenamiento, sin commit, sin tocar `CityLearn/` / `external/` / Words canónicos.

### Qué se corrigió

| Acción | Detalle |
|---|---|
| Puntero visible | `outputs/latest_visible_training_output_root.txt` |
| Valor **anterior** | `outputs/citylearn_v3_madrl_readiness_dryrun_20260723_231631` |
| Valor **nuevo** | `outputs/madrl_v3_20260627_164047` |
| Puntero colab | Sin cambio (ya canónico): `outputs/latest_colab_output_root.txt` → `outputs/madrl_v3_20260627_164047` |
| Manifests | `docs/workflow_manifest.json` referencia la ruta del puntero (no el valor); alineación vía archivo de puntero |
| Archive dry-run/validate | **6** carpetas → temporalmente a `_archive/.../validate_dryrun/` (**superseded**: eliminadas en Follow-up B DELETE) |

**Carpetas archivadas:**

1. `_masac_diag_dryrun`
2. `_validate_drive_run`
3. `_validate_notebook_launcher_dryrun_local`
4. `_validate_readiness_dryrun_20260723_231330`
5. `_validate_two_phase_dryrun`
6. `citylearn_v3_madrl_readiness_dryrun_20260723_231631`

**No movidas (conservador):** `_tmp_nonparametric_12seeds`, `madrl_nonparametric_battery_smoke_n3`, `colab_50ep`, `_nb_cells`, `test_notebook`. Canónicos intactos: `madrl_v3_20260627_164047`, `_drive_madrl`, `madrl_nonparametric_battery`.

### Veredicto reproducción actualizado

| Pregunta | Respuesta |
|---|---|
| ¿Reproducción del run canónico 50 ep? | **SÍ** |
| ¿Campaña 12-seed / Cap. 6 completa? | **NO** (gap de alcance; no bloquea reproducción del run Drive 50 ep) |
| Veredicto global raíz (reproducción evidencia canónica) | **SÍ** (antes PARCIAL) |

### Gaps que siguen

1. Campaña multi-semilla **12 seeds** pendiente (no entrenar en este follow-up).
2. `verify_project_context.ps1` cuelga — investigar aparte.
3. TOC F9 del Informe Word si aplica.

---

## Follow-up 2026-07-29 (B) — política DELETE (sin `_archive`)

**Cambio de política del usuario (prioridad absoluta):** no deben quedar archivos archivados. Lo no vinculado a thesis / reproducción → **DELETE** (no ARCHIVE).

### Criterio aplicado

| Clase | Decisión |
|---|---|
| 2 Word canónicos + capítulos MD + `workflow_manifest` / `CANON_*` | **KEEP** |
| Run 50 ep `madrl_v3_20260627_164047`, `_drive_madrl`, batería no paramétrica, smoke_n3, multicriteria, baselines/comparison citados, `thesis_objective_evidence`, `full_20260615_074011_v4` (Cap. 1) | **KEEP** |
| Punteros `latest_*` → canónico 50 ep | **KEEP** (ya alineados) |
| `docs/_archive/`, `outputs/_archive/`, `scripts/_archive/`, `tools/_archive/`, `tools/thesis/_archive/` | **DELETE** (legacy / dry-run / oneshots) |
| dry-run, `_validate_*`, `_tmp_*`, demos, dumps notebook, Excel puntual | **DELETE** |

### Eliminados (resumen)

| Categoría | Paths / conteo aprox. |
|---|---|
| `docs/_archive` | ~1368 ítems (Word legacy ABRIR/backups, root_clutter, tmp Word edit) |
| `outputs/_archive` | ~1806 ítems (runs obsoletos, dry-runs, validate, thesis dup archive) |
| `scripts/_archive` | 4 ítems |
| `tools/_archive` | 13 ítems (colab oneshot + dataset stubs) |
| `tools/thesis/_archive` | 24 ítems (patches oneshot) |
| Leftovers `outputs/` | `_nb_cells`, `_tmp_nonparametric_12seeds`, `colab_50ep`, `test_notebook`, `madrl_multicriteria_selection_demo`, `_stats_rerun_logs`, `019f991f-…`, `dataset_audit` vacío, `architecture_diagrams_rendered`, `informe_tecnico_supervision_20260620.json` |
| **Total árboles/paths borrados** | **15** acciones DELETE (~3350+ ítems) |

> Nota: el Follow-up A había *archivado* 6 dry-run/validate; bajo política B esos (y todo `_archive`) fueron **eliminados**.

### Conservados (vínculo)

| Path | Por qué |
|---|---|
| `docs/Tesis_*.docx`, `docs/Inforne_*.docx` | Words canónicos |
| `outputs/madrl_v3_20260627_164047/` | Run Cap. V / Drive 50 ep |
| `outputs/_drive_madrl/` | Espejo + `kpi_recalc_20260728` |
| `outputs/madrl_nonparametric_battery/` (+ `_smoke_n3`) | Citados Cap. 4/5 |
| `outputs/madrl_multicriteria_selection/` | Citado Cap. 5 |
| `outputs/citylearn_v3_madrl_full_20260615_074011_v4/` | Citado Cap. 1 |
| `outputs/comparison_*`, `citylearn_v2_original_benchmark`, `thesis_objective_evidence` | Pipeline Cap. 3 / evidencia |
| `outputs/dataset_cache/` | Soporte dataset reproducción |
| Punteros `latest_colab_*` / `latest_visible_*` | → `outputs/madrl_v3_20260627_164047` |

### ¿Quedan carpetas `_archive` de proyecto?

**No.** Solo permanece `\.venv39-citylearn-v3\...\pyomo\_archive` (dependencia de terceros; no tocada).

### Docs actualizados

- `docs/00_INDEX.md`, `docs/CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md`, `docs/workflow_manifest.json` (política DELETE / sin archive layout).

### Veredicto reproducción

| Pregunta | Respuesta |
|---|---|
| ¿Reproducción del run canónico 50 ep? | **SÍ** |
| ¿Campaña 12-seed completa? | **NO** (gap Cap. 6; no entrenada) |
| Veredicto global | **SÍ** |

### Gaps restantes

1. Campaña **12 seeds** pendiente.
2. Hang de `verify_project_context.ps1`.
3. TOC F9 Informe Word si aplica.
4. Sin commit (según instrucción).

---

## Follow-up 2026-07-29 (C) — auditoría integral + readiness 4 MADRL

Informe completo: [`AUDITORIA_INTEGRAL_PROYECTO_2026-07-29.md`](AUDITORIA_INTEGRAL_PROYECTO_2026-07-29.md).

Resumen: limpieza residual (vacíos/pycache/ociosos), launchers alineados a **50 ep**, refs README/scripts corregidas, `workflow_integrity` refrescado → canónico 50 ep. **Veredicto entrenamiento 4 MADRL: SÍ.**
