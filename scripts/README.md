# scripts/ — orquestación operativa (PowerShell + CLIs MADRL)

Inventario canónico verificado **2026-07-29**.
Redacción DOCX de tesis: carpeta única **`tools/thesis/`**
(ver `docs/analisis_scripts_vs_tools_tesis.md` y `tools/thesis/README.md`).

## Política

| Ámbito | Ubicación canónica |
|--------|--------------------|
| Frontera de repo / entrenamiento visible / reinicios | `scripts/*.ps1` |
| Estadística operativa MADRL (no DOCX) | `scripts/run_madrl_*.py` |
| Generación / parches Word tesis | `tools/thesis/` |
| Dataset CityLearn Iquitos | `tools/dataset/` |
| KPIs / stats de resultados | `tools/eval/` |
| Colab notebook generate/patch | `tools/colab/` |
| Fetch / Drive operativo | `tools/drive/` |
| Helpers entrenamiento / baselines | `tools/training/` (incluye `prune_citylearn_v3_training_artifacts.ps1`) |
| Integridad workflow / storage | `tools/ops/` |
| Figuras arquitectura (no Word) | `tools/figures/` |
| Entrenamiento agentes CityLearn v3 | `CityLearn/scripts/` |

Los únicos `.py` de tesis permitidos aquí son **shims** (<1 KB) que delegan en
`tools/thesis/`. No debe haber copias completas duplicadas.

## Inventario activo

### Core

| Archivo | Rol |
|---------|-----|
| `verify_project_context.ps1` | Gate de frontera del proyecto |
| `run_citylearn_v3_full_training_visible.ps1` | Wrapper entrenamiento visible |
| `monitor_citylearn_training_visible.ps1` | Monitor legacy |
| `training_launcher_window.ps1` | Ventana lanzador |
| `training_resume_window.ps1` | Ventana resume |
| `activate_citylearn_v3.ps1` | Activa `.venv39-citylearn-v3` |

### Reinicio / paralelo / Drive

| Archivo | Rol |
|---------|-----|
| `restart_happo_masac_v3.ps1` | Entrypoint canónico 4 MADRL (50 ep) vía `LANZAR_ENTRENAMIENTO_V4.bat` |
| `run_3madrl_parallel.ps1` | Lanzamiento paralelo (AWS / VRAM alta) |
| `setup_google_drive_oauth.ps1` | OAuth Google Drive |
| `fetch_and_generate_drive_figures.ps1` | Fetch + `tools/thesis/generate_drive_thesis_figures.py` |

### CLIs Python operativos

| Archivo | Rol |
|---------|-----|
| `run_madrl_nonparametric_battery.py` | Batería no paramétrica 50 ep |
| `run_madrl_multicriteria_selection.py` | TOPSIS/AHP multicriterio |

### Shims → `tools/thesis/`

| Shim | Destino |
|------|---------|
| `generate_borrador_tesis_docx.py` | `tools/thesis/generate_borrador_tesis_docx.py` |
| `thesis_doctoral_sections.py` | `tools.thesis.thesis_doctoral_sections` |

### Legacy

Los one-shots `_archive/` y `scripts/legacy_bat/` fueron **eliminados** (política 2026-07-29 DELETE).
Launcher Windows canónico: `LANZAR_ENTRENAMIENTO_V4.bat` → `restart_happo_masac_v3.ps1` (50 ep).
Detalle: `docs/AUDITORIA_INTEGRAL_PROYECTO_2026-07-29.md`.

## Ejecución

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe scripts\run_madrl_nonparametric_battery.py
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\generate_tesis_doctoral_final_docx.py
```

## Subdivisión `training/` / `monitoring/` / `setup/`

Propuesta en `docs/decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md`.
**No ejecutada**: los `.ps1` usan `$PSScriptRoot\..` y moverlos rompería rutas.