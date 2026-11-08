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
| Helpers entrenamiento / baselines | `tools/training/` (incluye `prune_artifacts.ps1`) |
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
| `activate_citylearn_v3.ps1` | Activa `.venv39-citylearn-v3` |

### Drive

| Archivo | Rol |
|---------|-----|
| `setup_google_drive_oauth.ps1` | OAuth Google Drive |

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
Los lanzadores locales de entrenamiento (`.bat`/`.ps1`) se retiraron el 2026-11-01: el entrenamiento
se lanza solo con `python -m uc3m.application.training.cli --config ...` (ver `governance/repository_layout.yaml`, `launch`).
Diagnóstico y límites actuales: `docs/audits/architecture_thesis_20261101/informe.md`.

## Ejecución

```powershell
powershell -ExecutionPolicy Bypass -File scripts\verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe scripts\run_madrl_nonparametric_battery.py
.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\generate_tesis_doctoral_final_docx.py
```

## Subdivisión `training/` / `monitoring/` / `setup/`

Propuesta en `docs/decisions/organizacion.md`.
**No ejecutada**: los `.ps1` usan `$PSScriptRoot\..` y moverlos rompería rutas.
