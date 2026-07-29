# Auditoría integral del proyecto — 2026-07-29

**Repo:** `D:/MADRLCitytleranflexresdr`  
**Origen:** `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`  
**Contexto:** `verify_project_context.ps1` → `[OK]` (en esta sesión; historial de hang >20 s sigue como gap operativo).  
**Alcance:** inventario raíz, limpieza DELETE (sin `_archive`), integridad flujo dataset→train→eval, readiness entrenamiento 4 MADRL.  
**No tocado:** contenido de `CityLearn/` / `external/` (solo lectura), Words canónicos, evidencia 50 ep, sin git commit, sin lanzar entrenamiento largo.  
**Previa:** [`AUDITORIA_RAIZ_PROYECTO_2026-07-29.md`](AUDITORIA_RAIZ_PROYECTO_2026-07-29.md)

---

## 1. Veredicto readiness 4 MADRL

| Pregunta | Respuesta |
|---|---|
| ¿Listo para entrenar HAPPO+MASAC+MATD3+MAAC? | **SÍ** |
| ¿Coherente con thesis (50 ep)? | **SÍ** (launchers alineados a 50 en esta pasada) |
| ¿Campaña 12-seed Cap. 6? | **NO** (gap de alcance; no bloquea un nuevo run seed=0) |
| ¿Carpetas `_archive` de proyecto? | **No** (solo `pyomo/_archive` dentro del venv) |

### Comando canónico recomendado (PowerShell)

```powershell
cd D:\MADRLCitytleranflexresdr
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1
# Opción A — atajo Windows (50 ep, 4 algoritmos, CUDA):
.\LANZAR_ENTRENAMIENTO_V4.bat

# Opción B — explícito (nueva sesión timestamp):
$ts = Get-Date -Format 'yyyyMMdd_HHmmss'
$root = "outputs\citylearn_v3_madrl_full_$ts"
Set-Content outputs\latest_visible_training_output_root.txt $root -Encoding UTF8
pwsh.exe -NoProfile -ExecutionPolicy Bypass `
  -File scripts\run_citylearn_v3_full_training_visible.ps1 `
  -OutputRoot $root -Scenario ALL -Seed 0 `
  -EpisodeTimeSteps 8760 -Episodes 50 `
  -ArtifactProfile efficient -TraceRecordInterval 10 -TraceDetail compact `
  -GpuProfile local4060_fast -Cuda
```

### Prerequisitos (verificados)

| Ítem | Evidencia |
|---|---|
| Venv | `.venv39-citylearn-v3/Scripts/python.exe` |
| CUDA | `torch 2.8.0+cu126`, `cuda=True`; GPU `RTX 4060 Laptop 8188 MiB` |
| Dataset | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json` + gate `status=ready` |
| Launcher | `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` + wrappers en `scripts/` |
| Configs 4 algos | `uc3m/configs/algorithms/{happo,masac,matd3,maac}.yaml` |

### Riesgos / gaps no bloqueantes

1. Campaña multi-semilla **12 seeds** pendiente (Cap. 6).
2. `verify_project_context.ps1` puede colgar >20 s (stdout OK en esta sesión; matar si cuelga).
3. Espejo canónico 50 ep **no** tiene `official_full_status.json` (sí `best_madrl_report.json` + KPIs Drive) — no impide un **nuevo** run.
4. `.sixth/` vacío residual (candidato DELETE menor).
5. Doble cache: training usa `outputs/dataset_cache` (hardcode en CityLearn; **no editar**); weather/tools usan `data/cache`.

---

## 2. Inventario raíz post-limpieza

### Carpetas

| Ítem | Decisión | Propósito / vínculo |
|---|---|---|
| `.git` / `.github` | KEEP | VCS / CI |
| `.venv39-citylearn-v3` | KEEP | Env entrenamiento |
| `.vscode` / `.cursor` / `.claude` | KEEP | IDE / agentes |
| `.cache` / `.pytest_cache` / `.ruff_cache` | KEEP | Caches regenerables |
| `.sixth` | DELETE_CANDIDATE | Vacío tras quitar `skills/` |
| `agent-skills/` | KEEP | Skills thesis/dataset/literatura (distinto de `tools/skills`) |
| `CityLearn/` | KEEP_DEP | Simulador + launchers — **no editar** |
| `data/` | KEEP | Audits dataset + `data/cache` weather |
| `deploy/` | KEEP | Docker/AWS |
| `docs/` | KEEP_CANON | 2 Word + MD + manifests |
| `external/` | KEEP_DEP | Backends MADRL — **no editar** |
| `outputs/` | KEEP_CANON | Evidencia 50 ep + baselines + punteros |
| `scripts/` | KEEP | Wrappers entrenamiento / eval ops |
| `tests/` | KEEP | Tests |
| `tools/` | KEEP | Dataset / thesis / ops / MCP skills |
| `uc3m/` | KEEP | Paquete local + configs YAML 4 MADRL |

### Archivos raíz

| Ítem | Decisión |
|---|---|
| `AGENTS.md`, `README.md` | KEEP_CANON |
| `pyproject.toml`, `requirements.txt`, `uv.lock` | KEEP |
| `Dockerfile`, `.dockerignore` | KEEP |
| `LANZAR_ENTRENAMIENTO_V4.bat` | KEEP (entrypoint Windows → `restart_happo_masac_v3.ps1`) |
| Tooling: `pyrightconfig.json`, `cspell.json`, `.markdownlint*`, `.git*` | KEEP |

**Sin** `_tmp_*`, `nb_*.txt`, `~$*.docx`, ni `_archive/` de proyecto en raíz.

---

## 3. Eliminados / merges (esta pasada)

Log: `docs/_cleanup_integral_2026-07-29_log.txt`

| Categoría | Conteo | Ejemplos |
|---|---:|---|
| Carpetas vacías | **38** | checkpoints/figures/data vacíos en outputs citados; `uc3m/algorithms/configs`; `.sixth/skills` |
| `__pycache__` proyecto | **22** | `agent-skills/`, `deploy/`, `tests/`, `tools/skills/`, `uc3m/` (no venv/CityLearn/external) |
| Archivos/dirs ociosos | **3 acciones** | `scripts/_AUDIT_2026-07-29.md`; `scripts/restart_masac_matd3_maac.ps1` (OutputRoot fantasma); `scripts/legacy_bat/` (3 bats 75 ep + `cd` roto) |
| **Total acciones DELETE** | **~63** | Sin retención `_archive` |

### Merges / consolidación de propósito

| Antes | Después | Nota |
|---|---|---|
| Episodios 75 en launchers vs 50 thesis/manifest | **Defaults = 50** | `restart_happo_masac_v3.ps1`, `run_citylearn_v3_full_training_visible.ps1`, `run_3madrl_parallel.ps1`, README |
| `README` → `relanzar_entrenamiento_madrl.bat` (inexistente en raíz) | → `LANZAR_ENTRENAMIENTO_V4.bat` | Ref rota corregida |
| `workflow_integrity` apuntaba a dry-run borrado | Refrescado → `outputs/madrl_v3_20260627_164047` | `ok=true` |
| `agent-skills/` vs `tools/skills/` | **Sin merge** | Thesis/dataset vs MCP Drive/NotebookLM — fines distintos |
| `data/cache` vs `outputs/dataset_cache` | **Sin merge** | Training hardcodea `outputs/dataset_cache` en CityLearn; no editar |

---

## 4. Checklist flujo dataset → train → eval

| # | Eslabón | Estado | Evidencia |
|---|---|---|---|
| 1 | Dataset Iquitos CityLearn | **PASS** | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`; regenerar: `tools/dataset/orchestrate_citylearn_dataset.py`; gate `data/dataset_audit/training_dataset_ready_manifest.json` → `status=ready` |
| 2 | Configs HAPPO/MASAC/MATD3/MAAC | **PASS** | `uc3m/configs/algorithms/{happo,masac,matd3,maac}.yaml` + backends `external/` |
| 3 | Entrypoint 4 MADRL | **PASS** | `LANZAR_ENTRENAMIENTO_V4.bat` → `scripts/restart_happo_masac_v3.ps1` → `CityLearn/scripts/launch_citylearn_v3_official_training.ps1`; wrapper `scripts/run_citylearn_v3_full_training_visible.ps1` |
| 4 | Seeds / episodios / HPs vs thesis | **PASS** | Seed 0; **50 ep**; 8760 steps; `GpuProfile local4060_fast`; manifest `docs/workflow_manifest.json` |
| 5 | Outputs / punteros | **PASS** | Nuevo run: `outputs/citylearn_v3_madrl_full_<ts>`; evidencia Cap.V: `outputs/madrl_v3_20260627_164047`; ambos `latest_*` → canónico 50 ep |
| 6 | Evaluación post-train | **PASS** | `compare_citylearn_v2_vs_v3_madrl.py`, `generate_thesis_objective_evidence.py`, `benchmark_citylearn_v2_agents.py`, `scripts/run_madrl_nonparametric_battery.py`, `run_madrl_multicriteria_selection.py` |
| 7 | Dependencias | **PASS** | `pyproject.toml` / `requirements.txt` / venv; import `citylearn` + CUDA OK |
| 8 | Thesis ↔ resultados | **PASS** | Exactamente 2 Word; CANON + Cap.5 citan Drive 50 ep; sin refs activas a `_archive` borrado en manifests |

Integridad workflow (refrescada): `data/dataset_audit/workflow_integrity_manifest.json` → `ok=true`, pointer canónico existe.

---

## 5. Outputs canónicos conservados

| Path | Rol |
|---|---|
| `outputs/madrl_v3_20260627_164047/` | Run Cap. V / Drive 50 ep |
| `outputs/_drive_madrl/` (+ `kpi_recalc_20260728`) | Espejo Drive |
| `outputs/madrl_nonparametric_battery/` (+ `_smoke_n3`) | Stats no paramétricas |
| `outputs/madrl_multicriteria_selection/` | Multicriterio Cap. 5 |
| `outputs/citylearn_v3_madrl_full_20260615_074011_v4/` | Citado Cap. 1 |
| `outputs/comparison_*`, `citylearn_v2_original_benchmark`, `thesis_objective_evidence` | Eval / baselines |
| `outputs/dataset_cache/` | Cache CSV entrenamiento (CityLearn) |

Words: `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`, `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx`.

---

## 6. Dry-checks ejecutados (sin train largo)

- Import: `torch` CUDA + `citylearn` OK.
- Dataset gate + workflow integrity OK.
- GPU local detectada (RTX 4060 8 GB).
- Paths entrypoint / configs / eval PASS.

---

## 7. Gaps restantes

1. Campaña **12 seeds** (Cap. 6) no ejecutada.
2. Hang intermitente de `verify_project_context.ps1`.
3. TOC F9 del Informe Word si hubo ediciones Cap. 5.
4. `.sixth/` vacío (borrar cuando se autorice limpieza menor).
5. `official_full_status.json` ausente en espejo Drive (solo relevante al citar estado de launcher; KPIs Cap.V intactos).
6. Sin commit (según instrucción).

---

## 8. Relación con auditoría raíz

La pasada previa ([`AUDITORIA_RAIZ_PROYECTO_2026-07-29.md`](AUDITORIA_RAIZ_PROYECTO_2026-07-29.md)) cerró DELETE de `_archive` y alineó punteros. **Esta** auditoría integral revalida el flujo completo, limpia vacíos/pycache/ociosos residuales, alinea episodios a 50 y declara readiness de entrenamiento.
