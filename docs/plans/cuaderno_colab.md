# Cuaderno Colab operativo celda por celda — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Que cada celda de `examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb` sea operativa, verificable y honesta: checkout exacto, instalación fijada, campaña y Drive por identidad, entrenamiento con progreso y código de salida, y las celdas posteriores (congelado HPO, evaluación, análisis, entrega) que hoy faltan.

**Architecture:** Las celdas quedan delgadas: la lógica vive en módulos probados localmente. `tools/colab/colab_session.py` (solo stdlib, corre en el kernel de Colab) aplica el paquete, verifica el checkout y lanza subprocesos con streaming; `uc3m/application/pipeline.py` (Python 3.9 del proyecto) compone congelado → evaluación → tabla por semilla → análisis → entrega reutilizando funciones existentes. El generador `tools/colab/build_modular_colab_notebook.py` sigue siendo la única fuente del `.ipynb`.

**Tech Stack:** Python 3.9 (`.venv39-citylearn-v3`) para el proyecto; kernel Colab 3.11+ solo con stdlib para `colab_session.py`; pytest; PyTorch 2.8.0.

**Spec:** [remediación de auditoría](remediacion_auditoria.md) (P10, P11, P13), revisión línea por línea del cuaderno del 2026-11-01 (hallazgos 1–10 y de línea, registrados en `.superpowers/sdd/remediacion_auditoria/progress.md`), [runbook](../architecture/runbook.md).

**Traspaso y propiedad de archivos entre sesiones:** [traspaso_sesiones.md](traspaso_sesiones.md).

**Fecha:** 2026-11-01. **Estado:** plan; ninguna tarea ejecutada por este documento. No autoriza entrenar, publicar ni habilitar `resource_authorization.authorized_stages`.

## Reparto entre sesiones (acordado)

| Dueño | Archivos |
|---|---|
| Sesión A (este plan, P10) | `docs/plans/cuaderno_colab.md`, `uc3m/application/pipeline.py`, `tests/ops/test_colab_notebook_cells.py`, `tests/fresh_training/test_pipeline.py` |
| Sesión B (agente del generador) | `tools/colab/build_modular_colab_notebook.py`, `tools/colab/colab_session.py`, `tests/ops/test_colab_session.py`, el `.ipynb` generado y `outputs/colab_delivery/colab_modular_overlay.zip` |

Un solo escritor por archivo. El `.ipynb` nunca se edita a mano: se regenera.

## Global Constraints

- Única vía de entrenamiento: `python -m uc3m.application.training.cli` (`test_single_launch_path.py`). Ni `pipeline.py` ni ninguna celda entrena por otra vía.
- `RUN_STAGE = None` por defecto; una etapa solo corre si `configs/experiments/iquitos.yaml` la autoriza en `resource_authorization.authorized_stages`.
- Cada intento empieza en el episodio 0; nunca se reanuda; un tratamiento con intento completo verificado se reutiliza (`run_stage`), los demás reciben `try_NN` nuevo.
- `test_2025` solo se evalúa con `test_unlock.json` válido; HPO y congelado usan solo `validation_2024`.
- Alias, `dataset_root`, `splits` y `campaign_id` salen siempre de `configs/experiments/iquitos.yaml`; ningún literal `iquitos_v1` en generador ni celdas.
- PyTorch fijado: `torch==2.8.0`, `torchvision==0.23.0`; índice `cu128` para Blackwell (capacidad ≥ 12 o nombre con `BLACKWELL`/`RTX PRO 6000`/`RTX 50`), `cu126` en otro caso. `uv` fijado a `0.12.17`.
- Toda dependencia de `BASE_DEPS` lleva `==` con la versión de `uv.lock` cuando el paquete figura allí.
- Ningún resultado se sobrescribe: evaluación, análisis y entrega fallan con `FileExistsError` si el destino existe.
- Cada código de celda empieza con el marcador `# [Cn] <título>` (n = 1..11, ver mapa); los tests ubican celdas por marcador, no por índice.

## Mapa objetivo del cuaderno

| Marcador | Función | Llama a |
|---|---|---|
| C1 | Paquete y checkout exacto | `colab_session.apply_overlay`, `verify_checkout` |
| C2 | Instalación Python 3.9 fijada | (instalador existente, corregido) |
| C3 | Campaña, dataset y Drive por identidad | `colab_session.project_python`, `drive_root`, `run_cli` (verificación de fuentes) |
| C4 | Restaurar intentos verificados desde Drive | `run_cli(drive_sync --restore)` |
| C5 | Preparar campaña (no entrena) | `run_cli(cli --stage prepare)` |
| C6 | Ejecutar etapa autorizada con sync | `colab_session.run_stage_with_sync` |
| C7 | Estado por tratamiento | `pipeline status` |
| C8 | Congelar configuración HPO (validación) | `pipeline freeze` |
| C9 | Evaluación congelada | `pipeline evaluate` |
| C10 | Tabla por semilla y análisis | `pipeline analyze` |
| C11 | Entrega reproducible | `pipeline deliver` |

## Review Focus

1. Sesión Colab que se corta durante C6: al relanzar, el usuario espera ver qué intentos se reutilizaron y cuáles empezaron de cero, sin pérdida del resultado de etapa → test `test_c6_interrupt_terminates_child_and_syncs` (Tarea 1) y `test_status_lists_reasons_after_cut` (Tarea 7).
2. Paquete generado con otro alias o dataset que el YAML: debe detenerse en C1/C3 con mensaje claro, nunca entrenar con identidad mixta → `test_bundle_alias_comes_from_config` (Tarea 2) y `test_c3_refuses_dataset_mismatch` (Tarea 4).
3. CLI que rechaza (exit 2) en C4/C5/C6: el usuario espera leer el JSON con la razón, no un `CalledProcessError` → `test_run_cli_surfaces_json_reason` (Tarea 1).
4. Repetir C9/C10/C11 sobre una evaluación ya hecha: debe informar "ya existe", no sobrescribir ni fallar sin explicación → `test_evaluate_skips_existing_and_reports` (Tarea 7).
5. Drive con conflictos o copias rechazadas en C4: el usuario espera que el cuaderno se detenga antes de preparar → `test_c4_stops_on_conflicts` (Tarea 5).

---

### Tarea 1: `colab_session.py` — paquete, checkout y subprocesos (Sesión B)

**Files:**
- Create: `tools/colab/colab_session.py` (solo stdlib)
- Test: `tests/ops/test_colab_session.py`

**Interfaces:**
- Produces:
  - `apply_overlay(bundle: zipfile.ZipFile, project_root: Path) -> dict` → `{'written': int, 'removed': list[str]}`; usa `manifest['files'] = {ruta_posix: sha256}`; borra archivos del alcance `manifest['source_scope']` que no estén en `files`.
  - `verify_checkout(project_root: Path, manifest: dict, *, origin: str) -> list[str]` → razones (`origin_mismatch`, `head_mismatch`, `submodule_mismatch:<ruta>`, `file_mismatch:<ruta>`, `extra_file:<ruta>`); lista vacía = aceptado.
  - `project_python(project_root: Path, chosen: Optional[str]) -> Path`
  - `drive_root(base: Path, alias: str, campaign_id: str) -> Path` → `base/alias/campaign_id/outputs`
  - `class CliRefused(RuntimeError)` con `.returncode: int`, `.report: Optional[dict]`, `.tail: str`
  - `run_cli(argv: list[str], *, cwd: Path, on_line=print, allowed=(0,)) -> CliResult` (`CliResult(returncode: int, report: Optional[dict], tail: str)`; `report` = última línea JSON; lanza `CliRefused` si `returncode` ∉ `allowed`)
  - `run_stage_with_sync(stage_argv: list[str], sync_argv: list[str], *, cwd: Path, interval_seconds: int = 60, on_line=print) -> CliResult`

- [ ] **Step 1: Write the failing tests** en `tests/ops/test_colab_session.py`:
  - `test_overlay_refuses_absolute_parent_drive_and_symlink_members` — miembros `/x`, `../x`, `C:/x`, enlace (`external_attr` con `S_IFLNK`) → `ValueError`; nada escrito fuera de `project_root`.
  - `test_overlay_removes_stale_files_in_scope` — archivo `uc3m/viejo.py` ausente de `files` → borrado y listado en `removed`; archivo fuera de `source_scope` intacto.
  - `test_verify_checkout_reports_each_mismatch` — repo temporal (`git init`, commit) con un submódulo simulado por manifiesto distinto y un archivo alterado → razones exactas `head_mismatch`, `file_mismatch:uc3m/a.py`.
  - `test_run_cli_surfaces_json_reason` — script que imprime `{"status": "campaign_inputs_changed", "reasons": ["config_changed"]}` y sale 2 → `CliRefused` con `.returncode == 2` y `.report['reasons'] == ['config_changed']`.
  - `test_run_cli_streams_lines` — script que imprime 3 líneas → `on_line` recibe las 3 antes de terminar.
  - `test_c6_interrupt_terminates_child_and_syncs` — `stage_argv` = script que duerme; `on_line` lanza `KeyboardInterrupt` en la primera línea → el hijo termina (`poll() is not None`), `sync_argv` se ejecuta una última vez, la excepción se propaga.
  - `test_drive_root_includes_campaign_id` — `drive_root(Path('/d'), 'iquitos_v2', 'fresh_x_v1') == Path('/d/iquitos_v2/fresh_x_v1/outputs')`.
- [ ] **Step 2:** `PY -B -m pytest tests/ops/test_colab_session.py -q` → FAIL (módulo inexistente).
- [ ] **Step 3:** implementar las firmas anteriores. `run_cli` usa `Popen(..., stdout=PIPE, stderr=STDOUT, text=True, bufsize=1)` y lee línea a línea; `run_stage_with_sync` envuelve en `try/finally`: `stop.set()`, `child.terminate()` (y `kill()` tras 30 s), `join` del hilo y una sincronización final.
- [ ] **Step 4:** mismo comando → PASS.

### Tarea 2: Generador — alias del YAML, manifiesto de archivos y marcadores (Sesión B)

**Files:**
- Modify: `tools/colab/build_modular_colab_notebook.py` (`main`, `bundle_paths`, `build_notebook`)
- Test: `tests/ops/test_colab_notebook_cells.py` (Sesión A escribe los tests; Sesión B los hace pasar)

**Interfaces:**
- Consumes: `fresh_source_paths(root)`, `source_snapshot(root, scope='fresh')` de `uc3m/application/training/preflight.py`.
- Produces: `campaign_identity(root: Path) -> dict` (`alias`, `campaign_id`, `dataset_root`, `splits` leídos de `configs/experiments/iquitos.yaml`); manifiesto del zip con `commit`, `submodules`, `dataset_hash`, `source_sha256`, `source_scope: list[str]`, `files: {ruta: sha256}`, `campaign_id`, `alias`; `colab_session.py` copiado en la raíz del zip.

- [ ] **Step 1: Write the failing tests** (Sesión A):
  - `test_bundle_alias_comes_from_config` — con un YAML temporal `storage_alias: alias_x`, `campaign_identity` devuelve `alias_x` y `bundle_paths` no incluye `data/campaigns/iquitos_v1`.
  - `test_every_code_cell_has_a_marker` — cada celda de código empieza con `# [Cn] ` y los marcadores son exactamente C1..C11 en orden.
  - `test_no_literal_alias_in_cells_or_generator` — ni las celdas ni `main()` contienen `'iquitos_v1'`.
  - `test_manifest_lists_every_bundled_file_with_sha256` — sobre un zip construido en `tmp_path`, `set(manifest['files']) == {miembros del zip} - {'colab_bundle_manifest.json', 'colab_session.py'}` y cada sha256 coincide.
- [ ] **Step 2:** `PY -B -m pytest tests/ops/test_colab_notebook_cells.py -q` → FAIL.
- [ ] **Step 3:** implementar; `main()` acepta `--output` (por defecto `outputs/colab_delivery/colab_modular_overlay.zip`) para que los tests escriban en `tmp_path`.
- [ ] **Step 4:** PASS.

### Tarea 3: Celda C1 — checkout exacto (Sesión B)

**Files:** Modify generador (celda C1). Test: `tests/ops/test_colab_notebook_cells.py`.

**Interfaces:** Consumes `apply_overlay`, `verify_checkout` (Tarea 1); el kernel carga `colab_session.py` desde el zip con `importlib.util.spec_from_loader` antes de clonar.

- [ ] **Step 1 (Sesión A):** `test_c1_uses_session_helpers_and_stops_on_reasons` — el código de C1 (AST) llama a `apply_overlay` y `verify_checkout`, y existe un `raise` condicionado al resultado de `verify_checkout`; no contiene bucles propios sobre `infolist()`.
- [ ] **Step 2:** FAIL. **Step 3:** reescribir C1. **Step 4:** PASS.

### Tarea 4: Celdas C2–C3 — instalación fijada, intérprete único, fuentes y Drive (Sesión B)

**Files:** Modify generador (C2, C3). Test: `tests/ops/test_colab_notebook_cells.py`.

**Interfaces:** Consumes `project_python`, `drive_root`, `run_cli`; C3 compara `source_snapshot` calculado con el Python del proyecto contra `manifest['source_sha256']`.

- [ ] **Step 1 (Sesión A):**
  - `test_c2_pins_torch_and_uv` — C2 contiene `'torch==2.8.0'`, `'torchvision==0.23.0'`, la URL `https://astral.sh/uv/0.12.17/install.sh` y ningún `curl ... /uv/install.sh` sin versión.
  - `test_c2_base_deps_pinned_to_lock` — cada elemento de `BASE_DEPS` tiene `==`; si el paquete está en `uv.lock`, la versión coincide.
  - `test_c2_messages_reference_existing_markers` — ningún texto `celda 1.2`, `1.2b` ni `Celda 1.3`; los mensajes citan `C1`/`C2`.
  - `test_c3_reads_splits_python_and_drive_from_identity` — C3 usa `CAMPAIGN['splits']`, `project_python(...)` y `drive_root(...)`; no contiene `'.venv39-citylearn-v3/bin/python'` ni la tupla literal de splits.
  - `test_c3_refuses_dataset_mismatch` — C3 tiene `raise` si `dataset_hash` o `source_sha256` difieren del manifiesto.
- [ ] **Step 2:** FAIL. **Step 3:** reescribir C2/C3. **Step 4:** PASS.

### Tarea 5: Celdas C4–C5 — restaurar y preparar con razones visibles (Sesión B)

**Files:** Modify generador (C4, C5). Test: `tests/ops/test_colab_notebook_cells.py`.

- [ ] **Step 1 (Sesión A):**
  - `test_c4_stops_on_conflicts` — C4 usa `run_cli` y lanza si `report['conflicts']` o `report['rejected']` no están vacíos.
  - `test_c4_c5_never_use_check_true_capture` — ninguna celda contiene `check=True` junto a `capture_output=True`.
  - `test_c5_prints_budget_and_status` — C5 imprime `report['status']` y `report['budget']`.
- [ ] **Step 2:** FAIL. **Step 3:** reescribir. **Step 4:** PASS.

### Tarea 6: Celda C6 — etapa autorizada con progreso, código de salida y sync (Sesión B)

**Files:** Modify generador (C6 y su markdown). Test: `tests/ops/test_colab_notebook_cells.py`.

- [ ] **Step 1 (Sesión A):**
  - `test_c6_defaults_to_no_training` — `RUN_STAGE = None` está presente y la rama de ejecución depende de él.
  - `test_c6_uses_run_stage_with_sync_and_reports_returncode` — C6 llama a `run_stage_with_sync` e imprime `returncode` y `report['status']`; no contiene `communicate()`.
  - `test_markdown_states_interrupted_attempt_policy` — el markdown previo a C6 dice que un intento interrumpido sin `completion.json` no se copia a Drive y su tratamiento se repite desde cero; el markdown de C4 no lo contradice (ninguno afirma que el interrumpido "queda como evidencia fallida").
- [ ] **Step 2:** FAIL. **Step 3:** reescribir. **Step 4:** PASS.

### Tarea 7: `pipeline.py` — estado, congelado, evaluación, análisis y entrega (Sesión A)

**Files:**
- Create: `uc3m/application/pipeline.py`
- Test: `tests/fresh_training/test_pipeline.py`

**Interfaces:**
- Consumes: `results_catalog.discover_attempts`, `results_catalog.build_seed_table`; `frozen_evaluation.evaluate_frozen(attempt_root, split_id, campaign_root, *, steps=None, seed=None)`; `fresh_tuning.protocol_from_dag`, `validation_row`, `select_hyperparameters`; `fresh_campaign.build_dag`, `load_campaign_config`, `write_configuration_freezes`; `fresh_analysis.analyze_campaign`, `FrozenProtocol.default()`; `tools/eval/report_fresh_campaign.build_fresh_delivery(manifest_path, destination, *, gate_report=None, seed_rows=None)`.
- Produces:
  - `stage_status(manifest_path: Path) -> list[dict]` (por tratamiento: `stage`, `treatment_id`, `algorithm`, `scenario`, `seed`, `attempts`, `accepted`, `reasons`)
  - `evaluate_stage(manifest_path: Path, *, stage: str, split: str, evaluate=evaluate_frozen) -> dict` → `{'evaluated': [...], 'existing': [...], 'failed': [{'attempt': str, 'reason': str}]}`
  - `freeze_hpo(manifest_path: Path, config_path: Path, project_root: Path) -> dict` (usa solo `validation_2024`; `SelectionBlocked` se informa, no se oculta)
  - `analyze_stage(manifest_path: Path, *, stage: str = 'confirm', split: str = 'validation_2024') -> Path` → `<artifacts>/analysis/<stage>_<split>/` con `seed_table.json`, `scientific_report.json`, `analysis_manifest.json` (sha256)
  - `deliver(manifest_path: Path, destination: Path, *, stage: str = 'confirm', split: str = 'validation_2024') -> dict`
  - `main(argv=None) -> int`: `python -m uc3m.application.pipeline {status|freeze|evaluate|analyze|deliver} --manifest PATH [--stage S] [--split SPLIT] [--config C] [--destination D]`; última línea de salida = JSON; exit 0 ok, 2 rechazo con razón.

- [ ] **Step 1: Write the failing tests** (`evaluate` inyectado como escritor sintético del formato de `evaluate_frozen`; campañas preparadas con `fc.prepare_campaign` y `run_stage` con el learner de `tests/fresh_training/test_attempt_acceptance.py::_stage_learner`):
  - `test_status_lists_reasons_after_cut` — un tratamiento alterado aparece con `accepted is False` y su razón; los demás `accepted is True`.
  - `test_evaluate_skips_existing_and_reports` — segunda llamada: todos en `existing`, ninguno reevaluado, `failed == []`.
  - `test_evaluate_never_opens_test_without_unlock` — `split='test_2025'` sin `test_unlock.json` → cada intento en `failed` con razón que contiene `test split`.
  - `test_analyze_writes_hashed_report_and_refuses_overwrite` — crea los tres archivos; `analysis_manifest.json` lista sha256 correctos; segunda llamada → `FileExistsError`.
  - `test_pipeline_never_trains` — `pipeline.py` no importa `native_entrypoint` ni llama a `run_stage`/`subprocess` (AST).
  - `test_main_prints_json_and_exit_codes` — `main(['status', '--manifest', m])` → 0 y última línea JSON; manifiesto inexistente → 2 con `{"status": "refused", ...}`.
- [ ] **Step 2:** `PY -B -m pytest tests/fresh_training/test_pipeline.py -q` → FAIL.
- [ ] **Step 3:** implementar las firmas; ninguna regla nueva de aceptación, KPI o estadística: solo composición.
- [ ] **Step 4:** PASS, más `tests/fresh_training/test_fresh_results_catalog.py`.

### Tarea 8: Celdas C7–C11 — después del entrenamiento (Sesión B)

**Files:** Modify generador (C7–C11 y sus markdown). Test: `tests/ops/test_colab_notebook_cells.py`.

**Interfaces:** Consumes `python -m uc3m.application.pipeline …` (Tarea 7) vía `run_cli`.

- [ ] **Step 1 (Sesión A):**
  - `test_post_training_cells_call_pipeline_subcommands` — C7..C11 invocan respectivamente `status`, `freeze`, `evaluate`, `analyze`, `deliver` con `--manifest`.
  - `test_c9_defaults_to_validation_split` — C9 usa `validation_2024` por defecto y el texto explica que `test_2025` exige `test_unlock.json`.
  - `test_post_training_cells_guarded_by_flags` — C8–C11 solo actúan con variables `RUN_FREEZE`, `RUN_EVALUATION`, `RUN_ANALYSIS`, `RUN_DELIVERY` que valen `False` por defecto.
- [ ] **Step 2:** FAIL. **Step 3:** añadir celdas. **Step 4:** PASS.

### Tarea 9: Textos y fuentes (Sesión B)

**Files:** Modify generador (markdown inicial y final). Test: `tests/ops/test_colab_notebook_cells.py`.

- [ ] **Step 1 (Sesión A):**
  - `test_intro_states_masac_resource_refusal` — el markdown inicial dice que con GPU de 80 GB MASAC se rechaza y la confirmación de 4 algoritmos queda incompleta.
  - `test_sources_match_verified_references` — el markdown final cita Charbonnier con el enlace ORA `https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5` (el mismo de `specs/STATUS.md`) salvo que se registre un DOI verificado.
- [ ] **Step 2:** FAIL. **Step 3:** corregir textos. **Step 4:** PASS.

### Tarea 10: Regeneración y verificación integral (ambas sesiones)

- [ ] **Step 1 (B):** regenerar con `PY -B tools/colab/build_modular_colab_notebook.py` sobre un corte de fuentes estable.
- [ ] **Step 2 (A):** `PY -B -m pytest tests/ops/test_colab_notebook_cells.py tests/ops/test_colab_session.py tests/fresh_training/test_pipeline.py tests/fresh_training/test_fresh_results_catalog.py -q` → PASS, y `tests/ops/test_modular_colab_notebook.py` sin regresión.
- [ ] **Step 3 (A):** comprobar que el `.ipynb` versionado coincide con `build_notebook` en memoria (fuentes idénticas) y no guarda salidas.
- [ ] **Step 4:** el ensayo real en Colab (desconexión, restauración, una etapa piloto) queda **pendiente de autorización** de recursos; un test local no lo acredita (P11).
- [ ] **Step 5:** commits por tarea solo con autorización explícita del usuario.
