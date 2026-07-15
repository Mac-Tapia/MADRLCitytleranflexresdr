# Validación — Referencias bibliográficas unificadas (2026-07-15)

## Contexto
- `scripts/verify_project_context.ps1`: **OK** (`D:/MADRLCitytleranflexresdr`)

## Antes del merge (ambos Word)
| Lista | Ubicación | Entradas |
|-------|-----------|----------|
| Referencias bibliográficas | H1 principal (p. lóg. ~650) | 66 |
| Referencias complementarias verificadas… | H2 antes de Anexo A | 26 |
| Referencias complementarias incorporadas… | H2 entre Anexo B y C | 13 |
| **Total listas separadas** | **3** | **105 brutas** (con duplicados) |

## Después del merge
| Documento | Listas | Entradas únicas | Estado |
|-----------|--------|-----------------|--------|
| `ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS_REFERENCIAS_UNIFICADAS.docx` | **1** | **80** | **Merge OK** (`references_single_list`: true) |
| `ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx` | 3 | 105 | Bloqueado (Word abierto) — pendiente copia |
| `Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA.docx` | 3 | 106 | Bloqueado (Word abierto) — pendiente copia |

### Verificación (`verify_tesis_doctoral_docx.py`)
Documento espejo unificado:
- `references_count`: 80
- `references_ok`: true
- `references_single_list`: true (nueva comprobación)

## Archivos modificados
- `docs/ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS_REFERENCIAS_UNIFICADAS.docx` — **documento con merge aplicado** (copiar a los dos primarios al cerrar Word)
- `scripts/merge_thesis_references.py` — script de merge y deduplicación
- `scripts/_audit_ref_sections.py` — auditoría de listas
- `scripts/thesis_doctoral_sections.py` — `references_single_list` en verificación
- `tools/build_final_thesis_gdrive_objectives.py` — ya no crea listas complementarias
- `docs/tesis_capitulos/Referencias_APA.md` — nota de lista única
- `docs/thesis/APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md` — punteros a lista única
- `docs/thesis/PLAN_TESIS_MADRL_CITYLEARN_V3_IQUITOS.md` — sección REFERENCIAS sustituida por puntero

## Acción pendiente (usuario)
Cerrar ambos Word abiertos y sincronizar:

```powershell
$src = "docs\ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS_REFERENCIAS_UNIFICADAS.docx"
Copy-Item -Force $src "docs\ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx"
Copy-Item -Force $src "docs\Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA.docx"
python scripts\_audit_ref_sections.py
python scripts\verify_tesis_doctoral_docx.py "docs\ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS.docx"
```

Alternativa (regenera desde backup si hace falta): `python scripts\merge_thesis_references.py`

## Riesgos residuales
- **F9** en Word: actualizar campos de índice/TOC si el documento lo solicita al abrir.
- Entradas `[PV]` siguen pendientes de verificación bibliográfica completa.
- Duplicados semánticos con distinto año/autor (p. ej. variantes Nweye 2024) se colapsaron por clave autor+año; revisar manualmente si hace falta distinguir 2024a/2024b.
