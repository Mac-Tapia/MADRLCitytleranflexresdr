# Validación Word ↔ ejecuciones 50 ep Drive (actualizado 2026-07-29)

**Repo:** `D:/MADRLCitytleranflexresdr`  
**Validez:** KPIs / Cap. V / Shapiro / no paramétrico anclados a la corrida Drive de **50 episodios**  
`madrl_v3_20260627_164047` — https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX

## Veredicto

**SÍ — los 3 Word canónicos y Cap. 5 MD se validan contra el espejo local de esa carpeta Drive** (`outputs/madrl_v3_20260627_164047/`, `outputs/_drive_madrl/kpi_recalc_20260728/`).  
Fetch live a Drive **no** se ejecutó en el pase de consolidación; el espejo local ya contiene `best_madrl_report.json` con `target_episodes=50` y la misma URL Drive.

## Exactamente 3 Word

| Archivo | Rol | Notas |
|---|---|---|
| `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` | Tesis doctoral canónica | Integra Cap. V + KPIs Drive; sustituye la familia `*_KPI_DRIVE_LATEST` / `*_FINAL_COMPLETA*` (eran byte-idénticas o regeneraciones). |
| `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` | Informe 50 episodios | Cap. 5 sincronizado 2026-07-29 desde tesis canónica. |
| `docs/ABRIR_ESTE_WORD_FINAL_INDICES_AUTOMATICOS.docx` | Índices automáticos | Cap. 5 cuerpo sincronizado 2026-07-29; TOC conservado (F9 al abrir). |

Inventario: `docs/_word_inventory.json` · hashes: `docs/_word_hashes.json` · narrativa: `docs/CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md`.

## Artefactos locales de validez

| Artefacto | Rol |
|---|---|
| `outputs/latest_colab_output_root.txt` | Puntero → `outputs/madrl_v3_20260627_164047` |
| `outputs/madrl_v3_20260627_164047/resumen_comparativo/best_madrl_report.json` | MATD3 0,6667; episodios 50/49 |
| `outputs/_drive_madrl/kpi_recalc_20260728/tables/ranking_oe_scores_all_values.csv` | Ranking 4/4 + 3×3 |
| `outputs/.../estadistica/hipotesis_estadisticas_madrl.csv` | Shapiro / KW / MWU / Wilcoxon |
| `outputs/madrl_nonparametric_battery/` | Batería episódica complementaria |

## Capas (no mezclar p-valores)

1. **Descriptivo canónico 3×3** (`best_madrl`) — MATD3 0,6667.  
2. **KPI-gains evaluate_v2 4/4** — incluye HAPPO (score 0).  
3. **HE inferencial** (entrenamiento KPI-gains; Cap. 5 §5.3) — KW/Friedman/Wilcoxon.  
4. **Batería episódica** (`madrl_nonparametric_battery`) — complementaria; no sustituye HE canónica.

## MD alineado

- `docs/tesis_capitulos/Capitulo_5_Resultados.md` — Cap. V vigente.  
- `docs/tesis_capitulos/00_INDICE.md` — índice capítulos.  
- Guías históricas (`AUDITORIA_*`, `DIAGNOSTICO_*`) se conservan como auditoría; **no** son fuente de números canónicos.
