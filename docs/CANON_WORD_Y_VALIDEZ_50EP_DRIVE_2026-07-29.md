# Canónicos Word y validez 50 episodios (Drive) — 2026-07-29

**Repo:** `D:/MADRLCitytleranflexresdr`  
**Contexto:** `verify_project_context.ps1` → `[OK]` (cwd/root + origin correctos).

## Fuente de validez (50 episodios)

| Ítem | Valor |
|---|---|
| Carpeta Drive | https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX |
| Run canónico | `madrl_v3_20260627_164047` |
| Puntero local | `outputs/latest_colab_output_root.txt` y `outputs/latest_visible_training_output_root.txt` → `outputs/madrl_v3_20260627_164047` |
| Espejo Drive local | `outputs/_drive_madrl/` (+ `outputs/_drive_madrl/outputs/madrl_v3_20260627_164047`) |
| KPI evaluate_v2 | `outputs/_drive_madrl/kpi_recalc_20260728/` |
| Ranking / best | `outputs/madrl_v3_20260627_164047/resumen_comparativo/best_madrl_report.json` |
| Stats HE (SW/KW/MWU/Wilcoxon) | `outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/` |
| Batería no paramétrica episódica | `outputs/madrl_nonparametric_battery/` |

### Números ancla (no inventados)

- **best_madrl 3×3:** MATD3 score global **0,6667** (OE.1=1, OE.2=1, OE.3=0).
- **flex_composite E1:** MATD3 **1,0009**; MAAC 1,0124; MASAC 1,0286; HAPPO 1,1105.
- **ΔCO₂ E2 (kg):** MATD3 **23 070**; MAAC 70 654; MASAC 77 649; HAPPO 1 431 341.
- **Δcosto E3 (EUR):** MAAC **9 515**; MASAC 19 793; MATD3 44 399; HAPPO 106 828.
- **Ranking evaluate_v2 4/4:** MAAC 0,9538 > MATD3 0,8805 > MASAC 0,8679 > HAPPO 0,0000.
- **Episodios:** MATD3/MAAC/MASAC = 50/50; HAPPO = 49/50.
- **Puerta Shapiro:** normalidad rechazada → solo no paramétrico (α=0,05).

## Exactamente 2 Word bajo `docs/` (raíz)

| # | Archivo | Rol |
|---:|---|---|
| 1 | `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` | **Fuente de verdad** — tesis doctoral completa; Cap. 5 = descriptivos + Shapiro + Kruskal/Friedman/Wilcoxon/Mann–Whitney + KPIs Drive 50 ep |
| 2 | `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` | **Informe final 50 episodios** — edición de trabajo con narrativa 50 ep, TOC e índices; Cap. 5 alineado a la tesis |

### Comparativa 3→2 (2026-07-29) — por qué estos dos

| Criterio | Tesis | Informe | ABRIR (eliminado) |
|---|---:|---:|---:|
| Tamaño | 5,27 MB | 4,66 MB | 3,73 MB (ya no en disco) |
| Cap. 5 cuerpo (bloques) | 176 (completo) | 176 (sync tesis) | — |
| Shapiro / Kruskal / 0,6667 (Cap. 5) | 9 / 9 / 5 | 9 / 9 / 5 | — |
| TOC / campos índice | no | sí | — |

**Decisión:** retener Tesis (SoT) + Informe (única narrativa 50 ep + TOC). ABRIR y demás Word legacy **eliminados** (política 2026-07-29: DELETE no vinculados; sin `_archive`).

### Regla dura — no crear nuevos Word

- En la raíz `docs/` deben existir **exactamente estos 2** `.docx`.
- **Prohibido** crear nuevos archivos `.docx` canónicos o “finales” (p. ej. `ABRIR_ESTE_WORD_*`, `*_PATCHED`, `*_VERSION_*`, copias con fecha en el nombre).
- Toda mejora de redacción, Cap. V, KPIs, Shapiro/no paramétricos, índices o formato se aplica **solo** editando estos dos documentos.
- Generadores (`tools/thesis/*.py`) pueden **sobrescribir** la Tesis canónica; no deben emitir un tercer Word en `docs/`. Anexos multiobjetivo u otros artefactos van bajo `outputs/`, no como canónicos en `docs/`.
- Backups/obsoletos/duplicados **no vinculados** → **DELETE** (no retención en `docs/_archive/`).

## MD / PDF / JSON

- **Capítulos vigentes:** `docs/tesis_capitulos/Capitulo_5_Resultados.md` (+ Caps. 1–6) alineados a los ancla anteriores.
- **Inventarios:** `docs/_word_inventory.json`, `docs/_word_hashes.json`, `docs/_cap5_consistency_2word.json`.
- **Auditoría Informe:** `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS_auditoria.json`.
- **PDF restantes:** arquitectura + `SCALABLEDCPOMDP.pdf` (no son export Word de tesis; Word = fuente de verdad).

## Gaps / TODO

1. Abrir el Informe en Word y actualizar índices/TOC (F9) si hace falta tras ediciones de Cap. 5.
2. No hubo fetch live a Drive en este pase; validez = espejo local.
3. Capas estadísticas distintas (HE KPI-gains 3×3 vs batería episódica `madrl_nonparametric_battery`) no deben mezclarse al citar p-valores.
4. PDFs de arquitectura no regenerados (no contradicen Cap. V de tesis).
