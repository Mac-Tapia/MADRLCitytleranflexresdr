# Veredicto metodológico — MADRL CityLearn Iquitos

**Fecha:** 2026-07-18  
**Corrida canónica:** `madrl_v3_20260627_164047`  
**Alcance:** aplicación del dictamen asesor (problema → objetivo → hipótesis → diseño → métricas → pruebas → resultados → conclusiones)

---

## Veredicto ejecutivo

| # | Decisión | Estado |
|---|----------|--------|
| 1 | Diseño = **cuasiexperimental factorial 4×3** (no “no experimental”) | Aplicado Caps. 1 y 3 |
| 2 | PG/OG/HG = **ranking–Pareto** (Semilla C) + H₀/H₁ por eje (Semilla B) | Aplicado Cap. 1 |
| 3 | Dos capas inferenciales (A episódica / B KPI-gains); no fusionar | Aplicado Caps. 1, 3, 6 |
| 4 | Métricas primarias = KPI + reward; **no** accuracy/F1 como centrales | Declarado Caps. 1 y 3 |
| 5 | Multi-semilla experimental ≥3 = **H2 trabajo futuro** | Delimitado Caps. 1, 3, 6 |

---

## Decisión por hipótesis

| Hipótesis | Capa A (episódica) | Capa B (KPI-gains) | Veredicto final |
|-----------|--------------------|--------------------|-----------------|
| HG | Ranking MATD3; sin Pareto único | KW p = 0,155 (no rechaza H₀) | Ranking/Pareto **aceptado**; superioridad omnibus **no confirmada** |
| HE.1 | p = 1,305×10⁻⁸ → rechazar H₀ | p = 0,281 → no rechazar | Diferencia episódica **sí**; líder compuesto MATD3 / media reward MAAC |
| HE.2 | p = 0,0439 → rechazar H₀ | p = 0,546 → no rechazar | Diferencia episódica débil **sí**; líder descriptivo MATD3 |
| HE.3 | p = 0,251 → no rechazar H₀ | p = 0,388 → no rechazar | MAAC líder **solo descriptivo** |

---

## Archivos actualizados

- `docs/tesis_capitulos/Capitulo_1_Introduccion.md` — §1.1.3, 1.2, 1.3, alcances/limitaciones
- `docs/tesis_capitulos/Capitulo_3_Metodologia.md` — §3.1, 3.2, 3.3, 3.5.2
- `docs/tesis_capitulos/Capitulo_6_Conclusiones.md` — §6.1.1 Veredicto de hipótesis

**Pendiente (si se requiere):** —  
**Hecho (2026-07-18):** portado a Word (parche histórico `patch_veredicto_metodologico_docx.py`; consolidado bajo `tools/thesis/`, ver `docs/analisis_scripts_vs_tools_tesis.md`).

### Word actualizados

- `docs/ABRIR_ESTE_WORD_FINAL_TODAS_FIGURAS_APA_INTERPRETADAS_PATCHED.docx`
- `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA_PATCHED.docx`
- `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos_FINAL_COMPLETA_SYNCED.docx`

Informe: `docs/VEREDICTO_WORD_PATCH_REPORT_2026-07-18.json`  
Verificación: cuasiexperimental ✓ · §6.1.1 ✓ · ranking/Pareto ✓ · dos capas ✓ · línea antigua solo capa B eliminada ✓

Si los `.docx` originales están abiertos en Word, cerrarlos y copiar desde `*_PATCHED.docx` / `*_SYNCED.docx`.
