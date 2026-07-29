# Validación integral Word 50 ep / 4 MADRL — 2026-07-29

**Repo:** `D:/MADRLCitytleranflexresdr`
**Run canónico:** `madrl_v3_20260627_164047`
**Drive:** https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX
**Generado:** 2026-07-29T22:08:14.499121+00:00
**Script:** `tools/thesis/validate_integral_word_50ep_4madrl.py`

## Veredicto: **SÍ**

Todas las pruebas críticas PASS; anclas 50 ep / 4 MADRL trazables

## Conteos de pruebas

| PASS | FAIL | WARN | GAP |
|---:|---:|---:|---:|
| 69 | 0 | 0 | 0 |

## Word canónicos

| Archivo | Rol | chars | tablas | 50 ep | HAPPO/MASAC/MATD3/MAAC |
|---|---|---:|---:|---:|---|
| `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` | tesis | 227879 | 83 | 31 | 113/142/185/185 |
| `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` | informe | 263978 | 72 | 28 | 126/148/181/193 |

## Ground truth (anclas)

```json
{
  "score_global_3x3_matd3": 0.6667,
  "mejor_madrl_3x3": "MATD3",
  "flex_composite_e1": {
    "HAPPO": 1.1105,
    "MASAC": 1.0286,
    "MATD3": 1.0009,
    "MAAC": 1.0124
  },
  "co2_delta_kg_e2": {
    "HAPPO": 1431341,
    "MASAC": 77649,
    "MATD3": 23070,
    "MAAC": 70654
  },
  "cost_delta_eur_e3": {
    "HAPPO": 106828,
    "MASAC": 19793,
    "MATD3": 44399,
    "MAAC": 9515
  },
  "eval_v2_scores": {
    "HAPPO": 0.0,
    "MASAC": 0.8679,
    "MATD3": 0.8805,
    "MAAC": 0.9538
  },
  "episodes": {
    "MATD3": "50/50",
    "MAAC": "50/50",
    "MASAC": "50/50",
    "HAPPO": "49/50"
  }
}
```

### Fuentes

- **pointer:** `outputs/latest_colab_output_root.txt`
- **best_madrl:** `outputs/madrl_v3_20260627_164047/resumen_comparativo/best_madrl_report.json`
- **ranking_all:** `outputs/_drive_madrl/kpi_recalc_20260728/tables/ranking_oe_scores_all_values.csv`
- **he_csv:** `outputs/madrl_v3_20260627_164047/resumen_comparativo/estadistica/hipotesis_estadisticas_madrl.csv`
- **multicriteria:** `outputs/madrl_multicriteria_selection/selection_report.json`
- **multicriteria_source:** `real_drive_50ep_c1c6`
- **canon_md:** `docs/CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md`

## Inconsistencias / fallos

_Ningún FAIL._

## Warnings

_Ningún WARN._

## Gaps de redacción vs objetivo doctoral

- [redaccion] Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx: Conclusiones: no se detecta mención cercana de 50 episodios en ventana Cap.6

## Cambios aplicados a Word

Ninguno en este pase (solo validación; no se modificaron .docx).

## Recomendaciones (sin inventar datos)

- TOPSIS es medida multicriterio formal adicional para OG/OE/HE en Caps. V–VII; complementa evaluate_v2/KPI-gains y no debe quedar como disclaimer «solo ilustrativo/no decide».
- No mezclar p-valores de HE KPI-gains 3×3 con batería episódica ni presentar TOPSIS como único veredicto OG en sustitución del omnibus.
- Tras ediciones: abrir Informe en Word y actualizar TOC (F9).
- Capa multicriterio real_drive_50ep_c1c6: medida formal adicional en Caps. V–VII para objetivos/hipótesis; complementa best_madrl 3×3 y evaluate_v2 4/4.

## Checklist de pruebas (resumen por categoría)

| Categoría | PASS | FAIL | WARN | GAP |
|---|---:|---:|---:|---:|
| algorithms | 2 | 0 | 0 | 0 |
| anchors | 34 | 0 | 0 | 0 |
| cross_word | 18 | 0 | 0 | 0 |
| episodes | 4 | 0 | 0 | 0 |
| ground_truth | 2 | 0 | 0 | 0 |
| inventory | 3 | 0 | 0 | 0 |
| redaccion | 4 | 0 | 0 | 0 |
| trazabilidad | 2 | 0 | 0 | 0 |
