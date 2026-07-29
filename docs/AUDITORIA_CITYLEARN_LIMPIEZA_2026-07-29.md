# Auditoría y plan de limpieza — `CityLearn/` (reproducibilidad tesis)

**Fecha:** 2026-07-29  
**Repo:** `D:/MADRLCitytleranflexresdr`  
**Submódulo:** `CityLearn` → `https://github.com/Mac-Tapia/CityLearn.git` (`branch: citylearn-v3-madrl`)  
**Artefactos JSON:** `docs/_citylearn_audit_inventory.json`, `docs/_citylearn_audit_safe_delete.json`

## 0. Contexto y canónicos

| Ítem | Valor |
|---|---|
| Word fuente de verdad | `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` |
| Word informe 50 ep | `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` |
| Manifest | `docs/workflow_manifest.json` |
| Dataset canónico | `CityLearn/data/datasets/citylearn_iquitos_2023_2025/` |
| Notebook canónico | `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb` |
| Capa MADRL v3 | `CityLearn/citylearn/v3/` |
| Launcher | `CityLearn/scripts/launch_citylearn_v3_official_training.ps1` |
| Corrida 50 ep | `outputs/madrl_v3_20260627_164047` (espejo Drive) |

**Nota Fase 0:** `scripts/verify_project_context.ps1` se lanzó pero **quedó colgado sin salida** en esta sesión (varios intentos >2–4 min). Verificación manual equivalente: `git rev-parse --show-toplevel` = `D:/MADRLCitytleranflexresdr` y `origin` = `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git` → **OK**. No hay `tools/skills/*/SKILL.md` activos que disparen el chequeo de skills globales.

---

## 1. Resumen ejecutivo

`CityLearn/` es el **fork/submódulo** de la tesis (no un clone virgen). Contiene:

- **~1999 archivos / ~1,37 GB** fuera de `.git` (el `.git` interno suma ~2604 archivos / ~541 MB).
- Núcleo MADRL Iquitos **completo y vinculado** (dataset, `citylearn/v3`, scripts, notebook tutorial, configs).
- **~860 MB** de barrios upstream (Quebec ×2, Alameda, Travis, Chittenden) **sin referencias** en tesis, skills, docs ni tests locales.
- Basura clara: `__pycache__`, `.pytest_cache`, `pytest-cache-files-*`, backups del notebook tutorial, copia `citylearn_iquitos_2023_2025_backup` (~77 MB).

**Veredicto reproducibilidad:** **casi listo**. El camino canónico (dataset Iquitos + v3 + scripts + notebook + outputs Drive) está presente. La limpieza segura reduce ruido/caché; borrar barrios upstream libera ~860 MB pero requiere confirmación (son datos del paquete CityLearn upstream / posible `DataSet` offline).

---

## 2. Inventario estructural

### 2.1 Conteos

| Ámbito | Archivos | Tamaño |
|---|---:|---:|
| `CityLearn/` total (incl. `.git`) | 4603 | ~1909 MB |
| Excluyendo `.git` | 1999 | ~1368 MB |
| `data/` | 1315 | ~1340 MB |
| `data/datasets/` | 1295 | ~1269 MB |
| `citylearn/` (paquete) | 203 | ~4,6 MB |
| `citylearn/v3/` | 24 | ~0,2 MB |
| `scripts/` | 132 | ~3,6 MB |
| `tests/` | 171 | ~1,9 MB |
| `examples/` | 19 | ~2,1 MB |
| `configs/` | 2 | ~0,03 MB |

### 2.2 Subárboles principales

| Ruta | Rol |
|---|---|
| `citylearn/` | Simulador CityLearn v2 upstream + extensiones locales |
| `citylearn/v3/` | Capa Dec-POMDP / CTDE / objetivos (aporte tesis) |
| `scripts/` | Trainers HAPPO/MASAC/MATD3/MAAC, Colab, evidencia tesis |
| `examples/` | Tutorial MADRL v3 + notebooks v2 upstream |
| `configs/` | `citylearn_v3_madrl_training.yaml` |
| `data/datasets/citylearn_iquitos_2023_2025/` | Dataset oficial tesis (229 files, ~236 MB) |
| `data/datasets/*challenge*` / barrios | Datasets upstream CityLearn |
| `tests/` | Suite del submódulo (usa challenge 2022 / three_phase / baeda) |
| `docs/`, `assets/` | Docs/assets upstream + `CITYLEARN_V3_MADRL.md` |
| `.git/` | Historial del submódulo (no tocar) |

### 2.3 Notebooks

| Archivo | Tamaño | Clasificación |
|---|---:|---|
| `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb` | 0,43 MB | **KEEP_CORE** (canónico) |
| `examples_madrl_v3/madrl_citylearn_v3_{cli,load_environment,quickstart}.ipynb` | ~0,07 MB | KEEP_SUPPORT |
| `examples/citylearnv2/*.ipynb` | ~0,21 MB | EXTERNAL_UPSTREAM |
| `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb.bak` | 0,35 MB | **DELETE_CANDIDATE** |
| `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb.patch_bak` | 0,18 MB | **DELETE_CANDIDATE** |
| `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb.patch_bak2` | 0,82 MB | **DELETE_CANDIDATE** |

### 2.4 Duplicados

- **Por basename:** 223 grupos (mayormente CSV homónimos entre datasets challenge / demo / Iquitos — esperable).
- **Por hash (muestreo de ~3860 archivos):** 83 grupos; casi todos son CSV idénticos entre fases challenge / `three_phase` (upstream). Un duplicado relevante tesis: `carbon_intensity_metadata.json` idéntico en Iquitos canónico vs `_backup`.
- **No** hay segundo tutorial canónico paralelo (solo backups `.bak` / `.patch_bak*`).

### 2.5 Temporales / backups / artefactos

| Tipo | Conteo | MB | Acción |
|---|---:|---:|---|
| `__pycache__` / `.pytest_cache` / checkpoints ipynb | 340 | 7,49 | DELETE seguro |
| `pytest-cache-files-*` (raíz CityLearn) | 36 | 0,01 | DELETE seguro |
| Notebook `.bak` / `.patch_bak*` | 3 | ~1,35 | DELETE seguro |
| `citylearn_iquitos_2023_2025_backup/` | 75 | 77,24 | DELETE seguro (solo refs en `tools/_archive/`) |
| Checkpoints `.pt` / outputs de training **dentro** CityLearn | 0 | 0 | N/A |
| `citylearn.egg-info/` | 6 | ~0,01 | DELETE seguro (regenerable) |

---

## 3. Vinculación al proyecto local

### 3.1 Citado por workflow / tesis / skills

| Recurso CityLearn | Fuentes de vinculación |
|---|---|
| `data/datasets/citylearn_iquitos_2023_2025/` | `workflow_manifest.json`, Caps. 3–4, skills dataset/thesis-plan |
| `citylearn/v3/*` | Cap. 2/4, skills, `CITYLEARN_V3_MADRL.md` |
| `scripts/launch_citylearn_v3_official_training.ps1` | manifest, Cap. 3 |
| `scripts/train_citylearn_v3_{happo,masac,matd3,maac}.py` | Cap. 1/4, skills |
| `scripts/colab_a100_official_launcher.py` | Cap. 3 (corrida 50 ep) |
| `scripts/generate_thesis_objective_evidence.py` | Cap. 4, tools/eval |
| `scripts/benchmark_*` / `compare_citylearn_v2_vs_v3_madrl.py` | manifest baseline v2 |
| `configs/citylearn_v3_madrl_training.yaml` | Cap. 1, skills integrated |
| `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb` | Caps. 3–4, skills (celdas 6.1, 8.1, 9.1) |
| `data/buildingcsv/building.csv` | skill dataset (áreas techadas / PV) |
| `data/misc/lbl-tracking_the_sun-res-pv.csv` | `citylearn/data.py` / `energy_model.py` (sizing PV) |
| `reward_function.py` (en `citylearn/`) | Caps. 1–4 |

### 3.2 Usado por tests del submódulo (no tesis, sí integridad)

| Dataset | Uso |
|---|---|
| `baeda_3dem` | `test_citylearn_v3*.py` |
| `citylearn_challenge_2022_phase_all_plus_evs` | mayoría de tests EV/KPI |
| `citylearn_challenge_2022_phase_all` | `test_tutorial_kpis.py` |
| `citylearn_three_phase_electrical_service_demo` | charging / KPI v2 |

### 3.3 Sin vinculación tesis / docs / tests

| Recurso | MB | Clase |
|---|---:|---|
| `quebec_neighborhood_*` (×2) | ~660 | REVIEW / EXTERNAL_UPSTREAM |
| `ca_alameda_county_neighborhood` | ~81 | REVIEW / EXTERNAL_UPSTREAM |
| `tx_travis_county_neighborhood` | ~81 | REVIEW / EXTERNAL_UPSTREAM |
| `vt_chittenden_county_neighborhood` | ~38 | REVIEW / EXTERNAL_UPSTREAM |
| Challenge 2020/2021/2022 p1–p3 / 2023 (no usados en tests) | ~59 | REVIEW / EXTERNAL_UPSTREAM |
| `citylearn_iquitos_2023_2025_backup` | ~77 | DELETE_CANDIDATE |
| Backups notebook | ~1,35 | DELETE_CANDIDATE |
| Caches pytest/pycache | ~7,5 | DELETE_CANDIDATE |

---

## 4. Clasificación por área

### KEEP_CORE (mínimo reproducir experimentos MADRL Iquitos)

- `citylearn/` (incl. `v3/`, `reward_function.py`, `energy_model.py`, `data.py`, …)
- `scripts/train_citylearn_v3_{happo,masac,matd3,maac}.py`
- `scripts/citylearn_v3_training_common.py`
- `scripts/launch_citylearn_v3_official_training.ps1` (+ monitor)
- `scripts/colab_a100_official_launcher.py` (+ helpers Colab usados por notebook)
- `scripts/generate_thesis_objective_evidence.py`
- `scripts/check_citylearn_v3_training_ready.py`
- `scripts/benchmark_citylearn_v2_*.py` + `compare_citylearn_v2_vs_v3_madrl.py`
- `configs/citylearn_v3_madrl_training.yaml`
- `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb`
- `data/datasets/citylearn_iquitos_2023_2025/` (completo)
- `data/buildingcsv/` (insumo dataset; `building.csv` citado)
- `data/misc/lbl-tracking_the_sun-res-pv.csv` (~57 MB; sizing PV)
- `setup.py`, `requirements.txt`, `CITYLEARN_V3_MADRL.md`, `README.md`
- Punteros de outputs en el monorepo (fuera de CityLearn): `outputs/madrl_v3_20260627_164047`

### KEEP_SUPPORT

- `tests/` + datasets challenge/demo/baeda que consumen
- Notebooks `madrl_citylearn_v3_{cli,quickstart,load_environment}.ipynb`
- `scripts/train_citylearn_v3_{maddpg,mappo}.py` (no oficiales 4×3)
- `scripts/validate_*`, `run_citylearn_v3_env_smoke.py`, regeneradores de figuras/KPI
- `docs/`, `assets/` del submódulo
- `examples/typings/` (stubs Colab / pyright)

### EXTERNAL_UPSTREAM (no borrar a la ligera)

- Código CityLearn v2 core no citado literalmente en el Word
- Notebooks `examples/citylearnv2/`
- Datasets challenge embebidos del paquete oficial
- Barrios US/CA/Quebec (aunque no usados por esta tesis)
- `.git/` del submódulo

### RELOCATE

| Ítem | Destino propuesto | Motivo |
|---|---|---|
| Backups notebook (antes de borrar) | `docs/_archive/2026-07-29_citylearn_cleanup/notebook_baks/` **o** borrar | No deben vivir junto al canónico |
| `citylearn_iquitos_2023_2025_backup/` | `docs/_archive/.../dataset_backup/` **o** borrar | Copia intermedia; canónico ya en ruta oficial |
| `pytest-cache-files-*` en raíz CityLearn | N/A (borrar) | Residuo pytest mal ubicado |
| Generadores de evidencia tesis muy acoplados al monorepo (`generate_thesis_objective_evidence.py`) | **mantener** en `CityLearn/scripts/` (contrato manifest) | Relocate rompería `workflow_manifest.json` |

### DELETE_CANDIDATE (claramente seguros)

Ver §5 y JSON `docs/_citylearn_audit_safe_delete.json`.

### REVIEW (pedir confirmación)

1. **Barrios upstream ~860 MB** (Quebec×2, Alameda, Travis, Chittenden): sin refs en tesis/tests; son datos del distribution CityLearn.
2. **Challenges 2020/2021/2022-p1–p3/2023 ~59 MB**: no usados por tests actuales; sí parte del árbol upstream.
3. **Scripts legacy** `launch_citylearn_v3_iquitos_training.ps1` / monitor iquitos: posible solapamiento con launcher “official”; verificar antes de retirar.
4. **No expandir limpieza al `.git` del submódulo** ni a `citylearn/` core.

---

## 5. Acciones ejecutadas vs pendientes

### 5.1 Limpieza segura ejecutada en este pase

**Ejecutada:** 2026-07-29 — **460 archivos / 86,10 MB** eliminados (`docs/_citylearn_audit_deleted.json`).

1. `__pycache__/`, `.pytest_cache/` bajo `CityLearn/` (~7,5 MB)
2. Directorios `CityLearn/pytest-cache-files-*` (12 dirs)
3. `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb.bak`
4. `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb.patch_bak`
5. `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb.patch_bak2`
6. `citylearn.egg-info/`
7. `data/datasets/citylearn_iquitos_2023_2025_backup/` (~77 MB; canónico intacto; refs solo en `tools/_archive/`)

**No se tocó:** datasets challenge/barrios, código `citylearn/`, scripts oficiales, notebook canónico, dataset Iquitos vigente, `.git`.

### 5.2 Pendiente de confirmación del usuario

- [x] ~~Borrar barrios Quebec/Alameda/Travis/Chittenden (~860 MB)~~ → **RECHAZADO** (retener e integrar en tesis)
- [x] ~~Borrar challenges no usados por tests (~59 MB)~~ → **RECHAZADO** (retener e integrar)
- [x] ~~Archivar o retirar launchers `*_iquitos_training.ps1` legacy~~ → **RECHAZADO** (retener; documentar rol legado)
- [ ] Decidir si el submódulo debe versionar menos `data/` (LFS / download on demand) a medio plazo *(sin borrar contenido)*

---

### 5.3 Decisión: RETENER e INTEGRAR (no purgar) — 2026-07-29

**Respuesta del usuario a la propuesta de borrado:** no eliminar barrios, challenges ni launchers iquitos; **ejecutarlos e integrarlos** en la elaboración de la tesis.

| Activo | Acción | Integración tesis |
|---|---|---|
| Barrios Quebec×2, Alameda, Travis, Chittenden (~860 MB) | **RETENER** | Cap. 3 §3.4.6 — contexto benchmark upstream / árbol reproducible; **sin** KPIs Cap. 5 |
| Challenges 2020/21/22-p1–p3/2023 (~59 MB) | **RETENER** | Cap. 3 §3.4.6 + literatura Cap. 2; tests 2022; **sin** resultados fantasma |
| `launch_*_iquitos_training.ps1` (+ monitor) | **RETENER** | Cap. 4 — launcher legado documentado; canónico = *official* + Colab |
| Dataset Iquitos + v3 + tutorial + official launcher | Sin cambio | Siguen siendo el caso empírico principal |

**Informe de integración ejecutado:** [`INTEGRACION_CITYLEARN_THESIS_2026-07-29.md`](INTEGRACION_CITYLEARN_THESIS_2026-07-29.md).

**Claim boundary:** no se reportan entrenamientos MADRL ni tablas de resultados sobre barrios/challenges upstream en Cap. 5; el contraste empírico de hipótesis permanece en Iquitos 2023–2025 (`outputs/madrl_v3_20260627_164047`).

---

## 6. Riesgos

| Riesgo | Mitigación |
|---|---|
| Romper imports / `pip install -e ./CityLearn` | No tocar `setup.py` / paquete `citylearn/` |
| Romper tests del submódulo | Conservar baeda + challenge 2022 phase_all(+evs) + three_phase |
| Romper workflow tesis | Conservar rutas del `workflow_manifest.json` |
| Historial git del submódulo | No reescribir `.git`; commits solo si el usuario lo pide (en repo padre y/o CityLearn remoto) |
| Borrar barrios y romper `DataSet.get_dataset` offline | **Mitigado:** barrios retenidos; LFS/on-demand solo a medio plazo sin purga |
| `verify_project_context.ps1` colgado | Investigar en pase aparte (posible contención I/O/git); checks manuales de root/origin OK |

---

## 7. KEEP_CORE mínimo — checklist reproducción post-limpieza

1. `powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1`
2. Activar `.venv39-citylearn-v3` e instalar `-e ./CityLearn` si hace falta
3. Gate dataset: `tools/dataset/check_training_dataset_ready.py` → `status=ready`
4. Smoke: `CityLearn/scripts/check_citylearn_v3_training_ready.py --strict --schema-path CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json --scenario E1`
5. Confirmar notebook canónico abre: `examples_madrl_v3/madrl_citylearn_v3_tutorial.ipynb`
6. Confirmar puntero 50 ep: `outputs/latest_colab_output_root.txt` → `outputs/madrl_v3_20260627_164047`
7. (Opcional) `pytest` dentro de CityLearn sobre tests EV/KPI con challenge 2022
8. Abrir Word canónico y verificar que rutas citadas en Caps. 3–4 siguen existiendo

---

## 8. Top hallazgos críticos

1. **~860 MB** de barrios upstream **retenidos e integrados** en Cap. 3 §3.4.6 (decisión 2026-07-29: no purgar).
2. **Dataset Iquitos canónico presente** (~236 MB, 229 files) y alineado al manifest.
3. **Copia `_backup` del dataset Iquitos (~77 MB)** eliminada en limpieza segura previa.
4. **Tres backups del notebook tutorial** eliminados en limpieza segura previa.
5. **Cachés pytest/`__pycache__`** eliminados en limpieza segura previa.
6. **Notebook canónico único** `madrl_citylearn_v3_tutorial.ipynb` — bien anclado a Caps. 3–4.
7. **Capa `citylearn/v3/`** (6 módulos) intacta y citada en marco teórico.
8. **Tests del submódulo dependen de challenge 2022 / three_phase / baeda** — retenidos junto al resto de challenges.
9. **`lbl-tracking_the_sun-res-pv.csv` (~57 MB)** sí es KEEP (sizing PV en runtime).
10. **Submódulo git propio** (`Mac-Tapia/CityLearn`, rama `citylearn-v3-madrl`) — LFS/on-demand a medio plazo sin borrar contenido.

---

## 9. Estado final de reproducibilidad

| Estado | Justificación |
|---|---|
| **Listo (retención integrada)** | Núcleo tesis completo; barrios/challenges/launchers retenidos y documentados en Caps. 2–4 + Word; outputs canónicos en `outputs/` |

### Próximos pasos concretos

1. ~~Confirmar borrado de barrios/challenges~~ → **cerrado:** retener e integrar (véase §5.3 e `INTEGRACION_CITYLEARN_THESIS_2026-07-29.md`).
2. Reparar/diagnóstico de `verify_project_context.ps1` (cuelgues sin salida) — opcional.
3. Medio plazo: LFS / descarga bajo demanda del `data/` grande **sin** purgar el contenido científico.
4. Mantener regla: **exactamente 2 Word** en `docs/`; no meter copias de tesis dentro de `CityLearn/`.
