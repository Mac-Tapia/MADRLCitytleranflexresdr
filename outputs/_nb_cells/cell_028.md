### 2.1c Limpieza de runs `madrl_v3_*` duplicados (Drive)

Detecta y elimina carpetas `madrl_v3_*` redundantes en `outputs/` (creadas por reinicios de Colab). **Conserva siempre el run activo (`OUTPUT_ROOT`) y el más completo**; nunca borra el que tiene más jobs terminados.

- Por defecto **solo reporta** (`DELETE_DUPLICATE_RUNS = False`): muestra tamaño, `results.json` y checkpoints por run.
- Para borrar de verdad, pon `DELETE_DUPLICATE_RUNS = True` y re-ejecuta.

Es seguro ejecutarla siempre tras 2.1; si no hay duplicados, no hace nada.