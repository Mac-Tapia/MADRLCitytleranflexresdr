# Auditoría ejecución `tools/thesis/*.py` — 2026-07-29

**Nota:** `docs/thesis/` no contiene `.py` (solo markdown + xlsx). El alcance real es `tools/thesis/`.

## Resultado por script

| Script | Ejecutado | Aporta a redacción Word | Veredicto |
|--------|-----------|-------------------------|-----------|
| `run_thesis_word_pipeline.py` | verify-only OK tras fix | Sí (orquestador) | KEEP |
| `generate_tesis_doctoral_final_docx.py` | no regenerado (destructivo) | Sí (genera Tesis) | KEEP |
| `generate_borrador_tesis_docx.py` | import OK | Sí (Cap.1–4 base) | KEEP |
| `thesis_doctoral_sections.py` | import OK | Sí (Cap.5–6 lib) | KEEP |
| `thesis_cap5_structured.py` | import OK | Sí | KEEP |
| `thesis_references_apa.py` | import OK | Sí | KEEP |
| `thesis_antecedents_data.py` | import OK | Sí | KEEP |
| `thesis_word_canons.py` | import OK | Sí (rutas) | KEEP (actualizado a 2 canons) |
| `update_pg_pe_oe_h_exact_docx.py` | OK (ambos Word) | Sí | KEEP |
| `patch_cap3_cuasiexperimental_docx.py` | OK Tesis; Informe parcial | Sí | KEEP |
| `patch_cap4_implementacion_docx.py` | OK | Sí | KEEP |
| `patch_citylearn_assets_integration_docx.py` | OK (already_present) | Sí | KEEP |
| `sync_cap5_to_canon_words.py` | dry-run OK → Informe | Sí | KEEP (ABRIR eliminado) |
| `verify_tesis_doctoral_docx.py` | OK lógica 2 canons | Sí | KEEP |
| `update_word_quantitative_50episodes.py` | no re-ejecutado (reescribe Informe) | Sí | KEEP |
| `madrl_algorithm_analysis.py` | OK → JSON métricas | Sí (insumo Cap.5) | KEEP |
| `generate_drive_thesis_figures.py` | OK | Sí (figuras) | KEEP |
| `build_multiobjective_thesis_docx.py` | OK → outputs/ | Anexo (no canon) | KEEP |
| `build_multiobjective_thesis_pdf.py` | OK → outputs/ | Anexo | KEEP |
| `build_defensa_pdf_pillow.py` | OK → outputs/ | Defensa PDF | KEEP |
| `build_defensa_pdf.py` | FAIL `No module named reportlab` | Duplicado roto | **DELETED** |

## Hallazgos

1. Canon oficial = **2 Word** (Tesis + Informe). Código aún referenciaba ABRIR (eliminado) → pipeline/`verify --all-canons` fallaba siempre.
2. Tras limpieza: sync Cap.5 dry-run solo a Informe = OK; ABRIR ya no bloquea.
3. Tesis `complete=false` por `has_pe_answers` (falta texto literal "Respuesta a PE.1/2/3" en Cap.6) pese a tablas/imágenes presentes.
4. Parches Cap.3/4 y PG/OE/H **sí aportan** a la redacción canónica.

## Limpieza aplicada

- Eliminado `tools/thesis/build_defensa_pdf.py` (reportlab ausente; reemplazo = pillow).
- Canons/pipeline/sync/verify/README alineados a **2 Word**.
- Flag `--abrir-only` eliminado de `sync_cap5_to_canon_words.py`.
