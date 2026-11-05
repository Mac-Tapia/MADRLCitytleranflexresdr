# tools/ — utilidades del proyecto (subdividido por dominio)

Inventario de archivos Python directos actualizado **2026-11-02**. La historia
de reorganización está en
`docs/analisis_reorganizacion_tools_dataset.md` y
`docs/audits/architecture_thesis_20261101/informe.md`.

## Dominios de primer nivel

| Carpeta | `.py` | Contenido |
|---------|------:|-----------|
| `dataset/` | 24 | Creación/validación de datasets y campañas CityLearn Iquitos |
| `thesis/` | 58 | Redacción DOCX / Cap. 5–6 / figuras de documento / PDF defensa |
| `eval/` | 21 | KPIs Drive, análisis estadístico, auditorías inferenciales de resultados |
| `colab/` | 2 | Generación/validación del notebook tutorial Colab |
| `drive/` | 7 | Fetch/descarga/validación de artefactos Google Drive |
| `training/` | 12 | Helpers de entrenamiento, layout, completion, baselines, tests (+ `prune_*.ps1`) |
| `ops/` | 14 | Integridad de workflow, auditoría y mantenimiento local |
| `figures/` | 6 | Diagramas arquitectura / mermaid (no tesis Word) |
| `skills/` | 1 | Validador e inventario local `registry.yaml`; guías y conectores en subcarpetas |

La raíz `tools/` solo contiene:

- `README.md` (este archivo)
- `check_training_dataset_ready.py` — shim de compatibilidad (CityLearn launcher
  aún llama la ruta antigua; delega en `tools/dataset/`)

No hay scripts sueltos de dominio en la raíz. No hay `_archive/` bajo `tools/`.

## Dataset — entrada rápida

La campaña actual usa `tools/dataset/build_fresh_campaign_dataset.py` y escribe
en `data/campaigns/`, conforme al [runbook](../docs/architecture/runbook.md).
El orquestador heredado que escribe en `CityLearn/data/datasets/` requiere
autorización expresa para modificar esa dependencia protegida.

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
