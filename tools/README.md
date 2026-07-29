# tools/ — utilidades del proyecto (subdividido por dominio)

Reorganización física ejecutada **2026-07-29**. Ver
`docs/analisis_reorganizacion_tools_dataset.md` y
`docs/AUDITORIA_TOOLS_2026-07-29.md`.

## Dominios de primer nivel

| Carpeta | `.py` | Contenido |
|---------|------:|-----------|
| `dataset/` | 20 | **Única** carpeta de creación/validación del dataset CityLearn Iquitos |
| `thesis/` | 21 | Redacción DOCX / Cap. 5–6 / figuras de documento / PDF defensa |
| `eval/` | 13 | KPIs Drive, análisis estadístico, auditorías inferenciales de resultados |
| `colab/` | 14 | Generación/parcheo/validación del notebook tutorial Colab |
| `drive/` | 7 | Fetch/descarga/validación de artefactos Google Drive |
| `training/` | 12 | Helpers de entrenamiento, layout, completion, baselines, tests (+ `prune_*.ps1`) |
| `ops/` | 2 | Integridad de workflow y diagnóstico de almacenamiento local |
| `figures/` | 5 | Diagramas arquitectura / mermaid (no tesis Word) |
| `skills/` | 21 | MCP locales (`google-drive-mcp`, `notebooklm-mcp`); venv con `setup.ps1` |

La raíz `tools/` solo contiene:

- `README.md` (este archivo)
- `check_training_dataset_ready.py` — shim de compatibilidad (CityLearn launcher
  aún llama la ruta antigua; delega en `tools/dataset/`)

No hay scripts sueltos de dominio en la raíz. No hay `_archive/` bajo `tools/`.

## Dataset — entrada rápida

```text
python -B tools/dataset/orchestrate_citylearn_dataset.py --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025
```

Detalle: `tools/dataset/README.md`.

## Ops / integridad

```text
python -B tools/ops/verify_workflow_integrity.py --manifest-out data/dataset_audit/workflow_integrity_manifest.json
```

## Drive / figuras tesis

```powershell
powershell -ExecutionPolicy Bypass -File scripts\fetch_and_generate_drive_figures.ps1
```

(fetch canónico: `tools/drive/fetch_drive_training_artifacts.py`)

## Tesis

Ver `tools/thesis/README.md`. No mezclar con dataset/eval.
