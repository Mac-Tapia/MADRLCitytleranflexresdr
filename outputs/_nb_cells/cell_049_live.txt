### 7.2 Entrenamiento de 50 episodios por corrida (reanudable con --skip-completed)

Ejecuta 12 corridas en **dos fases** (`two_phase_happo_masac`):
- **Fase 1** HAPPO×3 + MASAC×3 (6 paralelos) → **Fase 2** MATD3×3 + MAAC×3 (6 paralelos)

Prior de tiempo: ~12 min/ep por fase → **~20 h** wall con 50 ep (ETA dinámico con FPS).
El panel usa **FPS medido** en `live_progress.json` para ETA dinámico (más fiable que el prior fijo).

Usa `--skip-completed`: si Colab se desconecta, **re-ejecuta solo esta celda 7.2**. El bootstrap integrado hace automáticamente: git hard sync (1.2), montar Drive (1.5), detectar el mismo `OUTPUT_ROOT` en Drive, plan 9 SKIP + 3 HAPPO salvage, dry-run interno y lanzamiento.

**No hace falta** repetir 1.2, 1.5, 2.1, 2.1b, 6.1, 7.0 ni 7.1 para reanudar en las mismas salidas de `outputs/madrl_v3_*`.

**HAPPO salvage 49/50:** solo en plan **9 SKIP + 3 tails** el launcher ajusta concurrencia HAPPO (hasta 3 en paralelo si VRAM alcanza). El protocolo **two_phase** (Fase 1 HAPPO+MASAC → Fase 2 MATD3+MAAC) no cambia en corridas completas.

Al terminar con exit=0: verifica artefactos (12/12) y, si `AUTO_RUN_POST_TRAINING=True`, ejecuta **7.3→9.x** (`AUTO_DISCONNECT_COLAB=False` por defecto).
