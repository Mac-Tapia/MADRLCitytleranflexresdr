# Análisis: reorganización de `tools/` (dataset único + dominios)

> **Nota 2026-07-29 (post-auditoría):** las rutas `tools/_archive/` citadas abajo fueron **eliminadas** (política sin archivos). Ver [`AUDITORIA_TOOLS_2026-07-29.md`](AUDITORIA_TOOLS_2026-07-29.md) para el estado actual.

**Fecha:** 2026-07-29  
**Repo:** `D:/MADRLCitytleranflexresdr`  
**Origen:** `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`  
**Alcance:** `.py` de proyecto bajo `tools/` (sin editar `CityLearn/`, `external/`, ni paquetes vendor de `tools/skills/`).  
**No se hizo commit.**  
**Preservado:** consolidación previa `tools/thesis/` (~39 archivos) y fixes de integridad de rutas tesis (SKILL integrado, wrappers `scripts/`, Cap. 4, audits).

---

## 1. Resumen ejecutivo

Se inventariaron y clasificaron por **contenido** (docstring + CLI + callers) los scripts sueltos de `tools/`. Resultado:

1. **`tools/dataset/`** es ahora la **única** carpeta de creación/preparación/validación del dataset CityLearn Iquitos (20 `.py` canónicos + `dataset_docs/`).
2. Duplicados/stubs de dataset se **archivaron** en `tools/_archive/dataset/` (no borrado destructivo).
3. El resto de `.py` de raíz se reubicó por dominio: `eval/`, `colab/`, `drive/`, `training/`, `ops/`, `figures/`, `_archive/colab_oneshot/`.
4. Se actualizaron `parents[N]` (repo root), rutas subprocess del orquestador, `docs/workflow_manifest.json`, docs de arquitectura/auditorías/capítulos activos, y skills de dataset.
5. La raíz `tools/*.py` quedó vacía; `tools/thesis/` intacta.

---

## 2. Inventario y clasificación por contenido

### 2.1 Dataset — pipeline canónico (`orchestrate_citylearn_dataset.py`)

| Archivo | Rol |
|---------|-----|
| `orchestrate_citylearn_dataset.py` | Orquestador subprocess de todo el build |
| `generate_iquitos_dataset.py` | Generador base |
| `buildingcsv_inputs.py` | Biblioteca inventario/mediciones |
| `distill_building_loads.py` | Destilación cargas + pricing |
| `fix_solar_pvlib.py` | PV pvlib/TMY |
| `dimension_ev_chargers.py` | EV Mode 3 |
| `sync_controlled_machines.py` | Washing machines |
| `fix_schema_cooling.py` | safety_factor cooling |
| `size_bess_optimal.py` | BESS |
| `audit_der_sizing.py` | Auditoría DER |
| `audit_training_dataset_provenance.py` | Procedencia real/simulada |
| `clean_dataset_orphans.py` | Huérfanos vs schema |
| `audit_citylearn_csv_integrity.py` | NaN/Inf/columnas |
| `evaluate_dataset.py` | Evaluación semántica edificios |
| `deep_dataset_analysis.py` | Rangos + carga CityLearn E1–E3 |
| `check_training_dataset_ready.py` | Gate final pre-MADRL |

### 2.2 Dataset — soporte / reportes auxiliares (misma carpeta)

| Archivo | Rol | En orchestrate? |
|---------|-----|-----------------|
| `generate_b01_billing.py` | Genera `B_01.csv` desde Excel | No (pre-pipeline) |
| `verify_solar.py` | Check read-only PV | No |
| `verify_ev_sessions.py` | Diagnóstico EV | No |
| `evaluate_iquitos_citylearn_v3_dataset.py` | Informe Mode3/V2G formal | No |

### 2.3 Otros dominios (reubicación)

| Destino | Criterio dominante | Cantidad aprox. |
|---------|--------------------|----------------:|
| `tools/eval/` | KPIs Drive, stats, auditorías de resultados | 13 |
| `tools/colab/` | Notebook tutorial generate/patch/validate | 14 |
| `tools/drive/` | Fetch/descarga Drive | 7 |
| `tools/training/` | Layout, completion, baselines, tests entrenamiento | 12 |
| `tools/ops/` | `verify_workflow_integrity`, diagnóstico storage | 2 |
| `tools/figures/` | Architecture PDF/PNG + mermaid | 5 |
| `tools/thesis/` | **Sin cambios de consolidación** | 39 |
| `tools/_archive/colab_oneshot/` | One-shots notebook / deprecated | 5 |

---

## 3. Contenido final de `tools/dataset/`

### Qué quedó (ejecutables limpios)

Los 20 scripts de §2.1–2.2 + `README.md` + `dataset_docs/`.

### Qué se archivó y por qué

| Archivado en `tools/_archive/dataset/` | Motivo |
|----------------------------------------|--------|
| `calibrate_buildings.py` | One-shot histórico; supersedido por `distill_building_loads.py` |
| `rebuild_per_building_profiles.py` | One-shot; lógica absorbida por destilación/generador |
| `fix_and_validate.py` | Side-effects al import; sin argparse; solapa generate/fix_solar/deep |
| `dataset_report.py` | Casi gemelo de `evaluate_dataset.py` (canónico en pipeline) |
| `analyze_support_files.py` | Subconjunto de `deep_dataset_analysis.py` |
| `diagnostico_dataset.py` | Stub con rutas rotas post-`tools/reports/` (`EXPECTED_ROWS=26305`) |

**Política:** archivo, no delete, por si hace falta auditoría histórica.

---

## 4. Mapa de reubicación de otros `.py`

Ejemplos representativos:

| Antes (`tools/`) | Después |
|------------------|---------|
| `run_*statistical*`, `recalc_drive_kpis_*`, `aggregate_colab_drive_kpis.py`, … | `tools/eval/` |
| `generate_colab_notebook.py`, `patch_notebook_*.py`, `verify_notebook.py`, … | `tools/colab/` |
| `fetch_*drive*`, `download_colab_missing_kpis.py`, … | `tools/drive/` |
| `verify_artifact_layout.py`, `validate_madrl_run_completion.py`, `test_madrl_robustness.py`, … | `tools/training/` |
| `verify_workflow_integrity.py`, `diagnose_madrl_storage.py` | `tools/ops/` |
| `generate_architecture_*.py`, `sync_mermaid_diagrams.py`, … | `tools/figures/` |
| `_insert_*.py`, `fix_clone_submodule.py`, `fix_colab_cell2.py`, `generate_informe_final.py` | `tools/_archive/colab_oneshot/` |
| `reports/ver_metricas_madrl.py` | `tools/training/` |

Imports cruzados dataset: hermanos en la misma carpeta (sys.path del script = `tools/dataset/`).  
Caller dual: `tools/eval/analyze_colab_drive_multiobjective_buildings.py` apunta `sys.path` a `tools/dataset` para `dimension_ev_chargers`.

---

## 5. Cómo ejecutar el pipeline de dataset

Desde la raíz del repo (venv CityLearn v3):

```powershell
# 1) Build + sync + audit + gate
.venv39-citylearn-v3\Scripts\python.exe -B tools\dataset\orchestrate_citylearn_dataset.py `
  --dataset-dir CityLearn\data\datasets\citylearn_iquitos_2023_2025

# 2) Gate explícito (opcional si ya corrió orchestrate)
.venv39-citylearn-v3\Scripts\python.exe -B tools\dataset\check_training_dataset_ready.py `
  --manifest-out data\dataset_audit\training_dataset_ready_manifest.json

# 3) Integridad workflow (ops)
.venv39-citylearn-v3\Scripts\python.exe -B tools\ops\verify_workflow_integrity.py `
  --manifest-out data\dataset_audit\workflow_integrity_manifest.json
```

Dry-run del orquestador: añadir `--dry-run`.  
Referencia canónica de comandos: `docs/workflow_manifest.json`.

---

## 6. Riesgos / candidatos dudosos no borrados

| Ítem | Nota |
|------|------|
| `verify_ev_sessions.py` / `evaluate_iquitos_citylearn_v3_dataset.py` | Útiles fuera del orchestrate; se conservaron en `dataset/` |
| `generate_b01_billing.py` | Pre-requisito de inputs; no etapa orchestrate |
| `tools/_archive/dataset/*` | No ejecutar sobre dataset canónico |
| `docs/analisis_scripts_vs_tools_tesis.md` | **Actualizado** 2026-07-29 (pasada follow-up): rutas dataset → `tools/dataset/` + §12 dominios |
| `scripts/README.md` | Posible lock; tabla de dominios `tools/` puede quedar desactualizada en una línea |
| `docs/_archive/**` | Rutas viejas **intencionadas** (histórico) |
| Validación runtime completa del pipeline | No re-ejecutada aquí (costosa); conviene una corrida `--dry-run` + gate en ventana sin entrenamiento |
| Skills globales del usuario | No usadas; solo `agent-skills/` del repo |

---

## 7. Árbol final de primer nivel en `tools/`

```text
tools/
  dataset/          # pipeline dataset Iquitos (única)
  thesis/           # redacción DOCX (previa consolidación)
  eval/             # KPIs / stats resultados
  colab/            # notebook Colab
  drive/            # fetch Drive
  training/         # helpers entrenamiento
  ops/              # workflow integrity
  figures/          # diagramas arquitectura
  reports/          # (vacía de py de dataset/métricas)
  skills/           # skills locales
  _archive/
    dataset/        # duplicados/stubs dataset
    colab_oneshot/  # one-shots notebook
```

---

## 8. Relación con trabajo de integridad paralelo

No se revirtieron:

- Rutas `tools/thesis/` en SKILL integrado / module-b / Cap. 4 / audits / `fetch_and_generate_drive_figures.ps1`
- Wrappers `scripts/generate_borrador_tesis_docx.py` y `scripts/thesis_doctoral_sections.py`
- §10 de `docs/analisis_scripts_vs_tools_tesis.md` (archivo no reescrito por lock)

Sí se actualizaron menciones de dataset en texto embebido de `tools/thesis/generate_borrador_tesis_docx.py` hacia `tools/dataset/...`.
