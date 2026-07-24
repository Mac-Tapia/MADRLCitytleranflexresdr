### 2.2 (Opcional) Rescatar HAPPO de un run fallido

Ejecutar **solo si** un run previo murió (p. ej. MASAC OOM) y quieres conservar checkpoints HAPPO parciales antes de borrarlo o relanzar con un `OUTPUT_ROOT` nuevo.

1. Define `FAILED_OUTPUT_ROOT` (run roto) y opcionalmente `HAPPO_RESCUE_ARCHIVE`.
2. Ejecuta la celda → copia checkpoints + `live_progress.json` a `outputs/rescued_happo_*`.
3. Para **retomar HAPPO** en un run nuevo: ejecuta `2.1` (nuevo timestamp), luego esta celda en modo `inject` antes de `7.2`.

> El rescate no completa el experimento 12/12; solo preserva progreso HAPPO intra-job.