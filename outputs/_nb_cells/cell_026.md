### 2.1b Verificación de reanudación (ejecutar después de 2.1)

Lista, para los **12 jobs**, si 7.2 hará **SKIP** (completo), **REANUDA** desde checkpoint o **fresh** — usando `preview_job_launcher_decision()`, la **misma función** que `--skip-completed` del launcher. **Nunca** marca COMPLETO si el launcher imprimiría `RUN ... not skipping`.

**Vuelve a ejecutar esta celda después de 7.1** (cuando `HAPPO_ROLLOUT_THREADS` ya está fijado). La celda 7.1 también imprime el mismo preview antes de 7.2.

**Flujo tras desconexión de Colab:** `1.1 → 1.2 → 1.2b → 1.3 → 1.4 → 1.5 → 2.1 → 2.1b → [2.3 si HAPPO salvage 49/50] → 6.1 → 7.0 → 7.1 → [2.1b otra vez] → 7.2`

| Estado en reporte | Acción recomendada |
|-------------------|-------------------|
| HAPPO `REANUDA 49/50` salvage sin KPIs | **EJECUTA vía 2.3** (`dry_run` → `execute`); no basta **7.2** solo |