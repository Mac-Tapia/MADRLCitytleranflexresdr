## Sección 2: Configuración del proyecto

### 2.1 `OUTPUT_ROOT` en Drive (MyDrive + carpeta compartida, sin mirror)

La celda **2.1** audita `outputs/` en MyDrive y en la carpeta compartida canónica ([`1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX`](https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX)) en **solo lectura** y elige `OUTPUT_ROOT` sin copiar ni mirror.

| Flag (opcional) | Default | Efecto |
|---|---|---|
| `AUTO_RESUME_LATEST` | `True` | Reanuda el run más completo por artefactos |
| `FORCE_NEW_RUN` | `False` | Ignora runs previos y crea `madrl_v3_<timestamp>` |
| `RESUME_OUTPUT_ROOT` | `None` | Ruta exacta de un run concreto (override manual) |
| `ENABLE_FUSE_MIRROR` | `False` | Solo si MyDrive está vacío: bootstrap opcional desde carpeta compartida (1ª vez) |

Flujo mínimo: **1.5** (montar Drive) → **2.1** → **2.1b** (preview SKIP/REANUDA).