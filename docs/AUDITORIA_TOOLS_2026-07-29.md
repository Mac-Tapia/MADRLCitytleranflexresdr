# Auditoría y limpieza de `tools/` — 2026-07-29

**Proyecto:** MADRLCitytleranflexresdr  
**Política aplicada:** sin carpetas `_archive/` en `tools/`; hard delete si no aporta; KEEP o MOVE si está vinculado al pipeline local o a Word tesis.

## Resumen ejecutivo

| Métrica | Cantidad |
|---------|----------|
| **KEEP** (scripts `.py` activos) | **114** |
| **MOVED** | **0** (reorganización previa ya aplicada) |
| **DELETED** (archivos de proyecto) | **36** |
| **DELETED** (peso muerto: `__pycache__`, `.venv` embebidos) | **~11 100** |
| **ARCHIVED** | **0** |

Tras la limpieza no queda ningún `_archive/` bajo `tools/`.

## Estructura final de `tools/`

| Carpeta | `.py` | Rol |
|---------|------:|-----|
| `dataset/` | 20 | Creación/validación dataset CityLearn Iquitos (canónico) |
| `thesis/` | 20 | Pipeline Word 3 canónicos + anexos defensa |
| `eval/` | 13 | KPIs Drive, estadística, auditorías inferenciales |
| `colab/` | 14 | Notebook tutorial: generate/patch/validate |
| `drive/` | 7 | Fetch/descarga artefactos Google Drive |
| `training/` | 12 | Layout, completion, baselines, tests |
| `ops/` | 2 | `verify_workflow_integrity`, diagnóstico storage |
| `figures/` | 5 | Diagramas arquitectura / mermaid |
| `skills/` | 21 | MCP locales (`google-drive-mcp`, `notebooklm-mcp`) |

Raíz `tools/*.py`: solo el shim `check_training_dataset_ready.py`. El prune de artefactos vive en `tools/training/prune_citylearn_v3_training_artifacts.ps1`. Carpeta `tools/reports/`: eliminada (solo contenía `__pycache__` de scripts ya reubicados).

## Acciones DELETE (evidencia)

### `tools/_archive/` — 11 archivos (eliminado)

| Archivo | Motivo |
|---------|--------|
| `dataset/calibrate_buildings.py` | One-shot histórico; supersedido por `distill_building_loads.py` |
| `dataset/rebuild_per_building_profiles.py` | Perfiles viejos; no en orquestador |
| `dataset/fix_and_validate.py` | Side-effects al import; solapa generate/fix_solar/deep |
| `dataset/dataset_report.py` | Casi gemelo de `evaluate_dataset.py` |
| `dataset/analyze_support_files.py` | Exploración puntual sin callers |
| `dataset/diagnostico_dataset.py` | Rutas rotas (`EXPECTED_ROWS=26305`); sin gate canónico |
| `colab_oneshot/_insert_guide.py` | One-shot notebook ya aplicado |
| `colab_oneshot/_insert_connection.py` | Idem |
| `colab_oneshot/fix_colab_cell2.py` | Parche puntual obsoleto |
| `colab_oneshot/fix_clone_submodule.py` | Marcado deprecated en docstring |
| `colab_oneshot/generate_informe_final.py` | Informe corrida v4/v5; no pipeline 50 ep |

### `tools/thesis/_archive/2026-07-29_one_shot/` — 23 archivos (eliminado)

Parches one-shot a Word **eliminados del repo** (`FINAL_COMPLETA`, `TODAS_FIGURAS_*`, `VERSION_FINAL_*`). Pipeline vivo:

- `run_thesis_word_pipeline.py`
- `sync_cap5_to_canon_words.py`
- `generate_tesis_doctoral_final_docx.py`
- `thesis_references_apa.py` (reemplaza `merge_thesis_references.py`)

Archivos borrados incluyen: `merge_thesis_references.py`, `generate_tesis_final_completa_integrada.py`, `patch_informe_final_structure.py`, `complete_informe_final_gaps.py`, `rebuild_thesis_cap5_objective_aligned.py`, parches Cap.6/A2/A9, auditorías `_audit_*`, etc.

### Peso muerto — ~11 100 archivos (eliminado)

| Ruta | Motivo |
|------|--------|
| `tools/__pycache__/` (+ subcarpetas) | Bytecode regenerable |
| `tools/reports/` | Solo `.pyc` de scripts ya en `training/` |
| `tools/skills/.venv/` | Venv huérfano en raíz de skills |
| `tools/skills/google-drive-mcp/.venv/` | Gitignored; recrear con `setup.ps1` |
| `tools/skills/notebooklm-mcp/.venv/` | Idem |

### Git index — 2 rutas obsoletas

- `tools/reports/diagnostico_dataset.py` → contenido vivo equivalente: auditorías en `tools/dataset/`
- `tools/reports/ver_metricas_madrl.py` → **`tools/training/ver_metricas_madrl.py`**

## KEEP (validado por uso)

Referencias en `docs/workflow_manifest.json`, `agent-skills/`, `scripts/`, `.cursor/mcp.json`:

- **Dataset:** `orchestrate_citylearn_dataset.py`, `check_training_dataset_ready.py`, cadena completa en `tools/dataset/README.md`
- **Ops:** `verify_workflow_integrity.py`
- **Thesis:** pipeline 3 canónicos (`tools/thesis/README.md`)
- **Drive/Colab/Eval/Training:** callers en SKILL integrado, README raíz, scripts PS1
- **Skills MCP:** `google-drive-mcp`, `notebooklm-mcp` (32 archivos trackeados en git; venv local no versionado)

## Referencias actualizadas

| Archivo | Cambio |
|---------|--------|
| `tools/README.md` | Quitada fila `_archive/` |
| `tools/thesis/README.md` | One-shots → eliminados, no archivados |
| `tools/dataset/README.md` | Stubs → eliminados |
| `docs/tesis_capitulos/Capitulo_4_Desarrollo_Propuesta.md` | `generate_tesis_final_completa_integrada` → `run_thesis_word_pipeline` |

## Pendiente / decisiones con riesgo

1. **Recrear venv MCP:** tras borrar `.venv` embebidos, ejecutar `tools/skills/google-drive-mcp/setup.ps1` y primera corrida de `notebooklm-mcp/run_server.py` si se usan MCP.
2. **Docs históricos** (`docs/analisis_reorganizacion_tools_dataset.md`, `docs/analisis_scripts_vs_tools_tesis.md`) aún mencionan rutas `_archive/` — son registro histórico, no rutas activas.
3. **`tools/skills/` ~524 archivos no-`.py`:** restos de paquetes MCP en disco (p. ej. cachés); solo 32 trackeados en git. Revisar manualmente si reaparece bloat tras reinstalar venv.
4. **`README.md` raíz** — rutas operativas de `tools/` actualizadas a dominios (`ops/`, `training/`, etc.); changelog histórico de junio 2026 conserva nombres de época.
5. **`CityLearn/CITYLEARN_V3_MADRL.md`** — actualizado para citar `tools/dataset/...` en los scripts de construcción del dataset.

## Veredicto

`tools/` quedó **subdividido por dominio**, **sin material archivado**, con **114 scripts `.py` activos** y **~11k artefactos regenerables eliminados**. Todo lo borrado estaba duplicado, obsoleto, sin callers externos, o apuntaba a Word/runners ya retirados del canon 50 ep.
