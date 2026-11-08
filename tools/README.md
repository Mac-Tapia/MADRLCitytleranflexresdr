# tools/ — utilidades del proyecto (subdividido por dominio)

Inventario de archivos Python directos actualizado **2026-11-08**. La historia
de reorganización está en
`data/audits/repository_hygiene_manifest.json` y
`docs/audits/architecture_thesis_20261101/informe.md`.

## Dominios de primer nivel

| Carpeta | `.py` | Contenido |
|---------|------:|-----------|
| `dataset/` | 32 | Creación/validación de datasets y campañas CityLearn Iquitos |
| `thesis/` | 50 | Redacción DOCX / Cap. 5–6 / figuras de documento / PDF defensa |
| `eval/` | 9 | KPIs Drive, análisis estadístico, auditorías inferenciales de resultados |
| `colab/` | 2 | Generación/validación del notebook tutorial Colab |
| `training/` | 8 | Helpers de entrenamiento, layout, completion, baselines, tests |
| `ops/` | 13 | Integridad de workflow, auditoría y mantenimiento local |
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
```

## Tesis

Ver `tools/thesis/README.md`. No mezclar con dataset/eval.
