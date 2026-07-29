# tools/thesis/ — redacción y generación documental de la tesis



Carpeta única para scripts `.py` de **redacción de tesis final** (DOCX, capítulos,

referencias APA, parches Word, figuras/tablas embebidas, PDF de defensa).



## Word canónicos (exactamente 2)



Definidos en `thesis_word_canons.py` y `docs/CANON_WORD_Y_VALIDEZ_50EP_DRIVE_2026-07-29.md`:



1. `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` — fuente de verdad

2. `docs/Inforne_tesisV4_FINAL_REVISADO_50_EPISODIOS.docx` — informe 50 ep (TOC)



`ABRIR_ESTE_WORD_*` fue eliminado (2026-07-29); no recrear un tercer Word en `docs/`.

Reglas duras: editar **solo** estos 2 archivos; backups temporales van a `outputs/_word_backups/` (nunca a `docs/`).



## Pipeline unificado (recomendado)



```powershell

# Dry-run sync Cap.5 (no escribe)

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\run_thesis_word_pipeline.py --sync-only --dry-run-sync



# Pipeline vivo: PG/OE/H + Cap.3 + Cap.4 + sync Cap.5 + verify (NO regenera Tesis)

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\run_thesis_word_pipeline.py



# Solo verificar los 2 canons

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\run_thesis_word_pipeline.py --verify-only



# Regenerar Tesis completa (destructivo; pide confirmación consciente)

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\run_thesis_word_pipeline.py --regenerate

```



## CLIs principales



```powershell

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\generate_tesis_doctoral_final_docx.py

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\update_pg_pe_oe_h_exact_docx.py

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\patch_cap3_cuasiexperimental_docx.py

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\patch_cap4_implementacion_docx.py

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\patch_citylearn_assets_integration_docx.py

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\update_word_quantitative_50episodes.py

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\sync_cap5_to_canon_words.py

.\.venv39-citylearn-v3\Scripts\python.exe -B tools\thesis\verify_tesis_doctoral_docx.py --all-canons

```



## Módulos de soporte (no son CLI principales)



| Módulo | Rol |

|--------|-----|

| `thesis_word_canons.py` | Rutas de los 2 Word |

| `thesis_doctoral_sections.py` | Cap. 5–6, resumen, verificación |

| `thesis_cap5_structured.py` | Estructura Cap. 5 |

| `thesis_references_apa.py` | Carga referencias APA |

| `thesis_antecedents_data.py` | Antecedentes Cap. 2 |

| `madrl_algorithm_analysis.py` | Perfiles de aprendizaje usados en Cap. 5 |

| `generate_borrador_tesis_docx.py` | Builder Cap. 1–4 (usado por el generador doctoral) |



## Side artifacts (anexo / defensa; no son los 2 canons)



- `generate_drive_thesis_figures.py` → figuras en `outputs/.../figuras_drive_reales/`

- `build_multiobjective_thesis_docx.py` / `build_multiobjective_thesis_pdf.py` → anexo en `outputs/.../multiobjetivo/`

- `build_defensa_pdf_pillow.py` → PDF defensa en `outputs/defensa_pdf/` (sin reportlab)



Scripts one-shot obsoletos (parches a Word eliminados como `FINAL_COMPLETA`, `ABRIR_*`,

`build_defensa_pdf.py` con reportlab) fueron **eliminados**. Usar solo el pipeline de esta carpeta.



Detalle histórico: `docs/analisis_scripts_vs_tools_tesis.md`, `docs/AUDITORIA_TOOLS_2026-07-29.md`.


