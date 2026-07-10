# Correcciones aplicadas a la tesis doctoral — 2026-07-07

**Documento regenerado:** `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`  
**Fuente de datos:** corrida canónica `madrl_v3_20260627_164047` (espejo `outputs/_drive_madrl/full_data/`)  
**Comando:** `.venv39-citylearn-v3\Scripts\python.exe scripts\generate_tesis_doctoral_final_docx.py`

---

## P0 — Bloqueantes

| # | Corrección | Archivos |
|---|------------|----------|
| 1 | **Orden de capítulos 1→2→3→4→5→6→Referencias** — generador reestructurado: cuerpo en documento intermedio y materiales previos insertados al inicio | `scripts/generate_tesis_doctoral_final_docx.py` |
| 2 | **Abstract sincronizado con §5.8** — eliminado «inferential tests remain pending»; KW p=0,155, Wilcoxon p=0,0049, baseline v2 | `scripts/thesis_doctoral_sections.py` |
| 3 | **§5.4 baseline CityLearn v2** — Tabla 5.4 con scores HPHI (baseline 0,7289/0,7866/0,7293), 3 heatmaps, discusión honesta | `scripts/thesis_doctoral_sections.py` |
| 4 | **Cap. 1 alineado a diseño factorial module-b** — PG/PE/OG/OE causa-efecto, Tablas 1.1–1.2, hipótesis con KW no significativo canónico | `scripts/generate_borrador_tesis_docx.py` |
| 5 | **Cap. 6 en prosa** — conclusiones, limitaciones y futuro sincronizados con Tabla 5.6 y hallazgo baseline | `scripts/thesis_doctoral_sections.py` |

---

## P1–P3

| # | Corrección | Archivos |
|---|------------|----------|
| 6 | **Interpretación individual Fig. 5.1–5.15** — párrafo por figura vinculado a KPIs Drive | `scripts/thesis_doctoral_sections.py` |
| 7 | **Antecedentes nacionales Cap. 2** — MINAM, OSINERGMIN, Chevarria Moscoso (2024), Peñalva Sánchez (2024), Rosero Bernal (2024), Domínguez Barbero (2026) | `scripts/generate_borrador_tesis_docx.py`, `scripts/thesis_references_apa.py` |
| 8 | **Tabla 3.1b diseño factorial 4×3** — 12 tratamientos con cobertura Colab | `scripts/generate_borrador_tesis_docx.py` |
| 9 | **Tabla 4.3 hiperparámetros Colab vs v4** — episodios, buffers, GPU | `scripts/generate_borrador_tesis_docx.py` |

---

## Verificación automática

```
scripts/verify_tesis_doctoral_docx.py → complete=True
tables=21, images=18 (15 figuras numeradas + 3 heatmaps baseline)
```

---

## Pendientes honestos (no cerrados en esta iteración)

- **HAPPO:** 49/50 episodios sin KPIs finales (VecEnvWrapper); excluido de inferencia y baseline MADRL.
- **Asesor:** `[por definir]` en portada.
- **Referencias [PV]:** ~8 entradas en `Referencias_APA.md` + Rosero Bernal (2024) marcada [PV].
- **Extensión doctoral:** ~7 000–8 000 palabras; umbral sustentación >> 30 000.
- **Inferencia causal:** KW global p=0,155; multi-semilla pendiente (Colas et al., 2019).
- **Índice Word:** requiere F9 / Actualizar campos al abrir.
- **DOCX integrado con diagramas:** no fusionado (estructura distinta); anexos A/B quedan fuera de la versión canónica.

---

*Generado tras aplicar auditorías `AUDITORIA_INTEGRAL_TESIS_DOCTORAL_2026-07-07.md` y `VALIDACION_INFORME_FINAL_TESIS_DOCTORAL.md`.*
