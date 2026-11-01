# Índice — Informe de Tesis por Capítulos (MADRL · CityLearn v3 · Iquitos)

**Tesis:** *Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en Comunidades Inteligentes.*
**Autor:** Mac Tapia (mac.tapia.c@uni.pe) · **Universidad:** UNI (Maestría profesionalizante)
**Caso de estudio:** Sistema Eléctrico Aislado de Iquitos (SEAI) — 17 edificios reales, Electro Oriente S.A., Loreto, Perú.
**Algoritmos:** HAPPO, MASAC, MATD3, MAAC · **Ejes:** OE.1 flexibilidad, OE.2 CO₂, OE.3 costos.

> Cada archivo es autocontenido. Cap. 2 = sustento teórico v3 (+ UC3M 7→3); Cap. 4 = implementación/flujo; Cap. 5 = evidencia ejecutada; Cap. 6 = conclusiones; Cap. 7 = recomendaciones. **Caps. 4–7 reestructurados al outline maestro** (desarrollo → resultados → conclusiones 6.1–6.6 → recomendaciones 7.1–7.7). Word canónico: `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` (generadores en `scripts/`).

---

## Archivos

| # | Archivo | Contenido | Estado |
|---|---|---|---|
| 0 | `00_INDICE.md` | Este índice | Completo |
| 1 | `Capitulo_1_Introduccion.md` | Problema; OG/OE.1–OE.3; H0G/H1G y HE10–HE31; justificación; alcances | Completo |
| 2 | `Capitulo_2_Marco_Teorico.md` | Estado del arte; Dec-POMDP/CTDE con dims reales SEAI (Tabla 2.A; distrito/edificio); 4 algoritmos; **§2.2.5 capa v3; §§2.2.6–2.2.9 UC3M matemático** | Completo |
| 3 | `Capitulo_3_Metodologia.md` | Diseño; dataset Iquitos; §3.4.6 árbol CityLearn retenido; 12 corridas; instrumentos | Completo |
| 4 | `Capitulo_4_Desarrollo_Propuesta.md` | Flujo 1–13; reward 3 ejes; multi-semilla (`n_seeds=12`); Shapiro→no paramétrico | Completo (outline maestro) |
| 5 | `Capitulo_5_Resultados.md` | §5.0–5.7; Fig. 5.1–5.14; Tablas 5.1–5.12; catálogo `outputs/`→acápites; KPIs/performance por MADRL | Completo (outline maestro) |
| 6 | `Capitulo_6_Conclusiones.md` | §6.1–6.6: conclusión OG/HG; OE.1–OE.3; contribuciones; limitaciones | Completo (outline maestro) |
| 7 | `Capitulo_7_Recomendaciones.md` | §7.1–7.7: estadísticas; algorítmicas; energéticas; validación externa/preoperacional; trabajo futuro; recomendación final | Completo (outline maestro) |
| R | `Referencias_APA.md` | Lista APA unificada | Consolidado |

---

## Resumen de cada capítulo

- **Capítulo 1 — Introducción.** PG/PE; OG y OE.1–OE.3; H0G/H1G y HE10–HE31; justificación; alcances.
- **Capítulo 2 — Marco teórico.** Estado del arte; Dec-POMDP/CTDE; HAPPO/MASAC/MATD3/MAAC con **adecuaciones al dominio eléctrico** (OE.1 flex / OE.2 CO₂ / OE.3 costos; wrappers Cap. 4); capa CityLearn v3 propuesto (§2.2.5); axiomatización UC3M (§§2.2.6–2.2.9); distinción 7 ejes (sustento) vs 3 ejes ejecutados.
- **Capítulo 3 — Metodología.** Cuasiexperimento factorial 4×3; dataset Iquitos; árbol CityLearn retenido (§3.4.6); 12 corridas; instrumentos KPI y batería estadística.
- **Capítulo 4 — Desarrollo.** Flujo 1–13; arquitectura v3; reward por OE; diseño multi-semilla implementado; protocolo Shapiro → no paramétrico. Reestructurado al outline maestro.
- **Capítulo 5 — Resultados.** Evidencia Capa A; OE.1–OE.3; OG/H0G/H1G; contrastación consolidada. Reestructurado al outline maestro.
- **Capítulo 6 — Conclusiones.** §6.1 conclusión general (OG/HG); §6.2–6.4 OE.1–OE.3; §6.5 contribuciones; §6.6 limitaciones. Sin plan H1–H7 como estructura principal. Reestructurado al outline maestro.
- **Capítulo 7 — Recomendaciones.** §7.1 estadísticas; §7.2 algorítmicas; §7.3 energéticas; §7.4 validación externa; §7.5 validación preoperacional; §7.6 trabajo futuro; §7.7 recomendación algorítmica final (compromiso descriptivo MATD3/MAAC; sin ganador estadístico único).
- **Referencias APA.** Lista consolidada; generadores Word sin placeholders `[PV]`.

---

## Estado global

| Capítulo | ¿Completo? | Remanentes reales |
|---|---|---|
| 1 | Sí | Unidad de posgrado institucional |
| 2 | Sí | — |
| 3 | Sí | — |
| 4 | Sí | Desglose 1 856 dims de estado (menor) |
| 5 | Sí | Homogenizar HAPPO 50 ep; entrenar 12 seeds (runner listo) |
| 6 | Sí | Alineación Word/PDF institucional |
| 7 | Sí | Alineación Word/PDF institucional |
| Ref. | Sí | Cotejo manual DOI opcional (sin inventar) |

> **Resultados Cap. 5.** Corrida `madrl_v3_20260627_164047`; KPI recalc `outputs/_drive_madrl/kpi_recalc_20260728/`. Drive: https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX

## Integración CityLearn (2026-07-29)

Barrios upstream, challenges 2020–2023 y launchers `*_iquitos_training.ps1` se **retienen** e integran en Caps. 2–4 como reproducibilidad/contexto (no como resultados Cap. 5). Informe: [`../INTEGRACION_CITYLEARN_THESIS_2026-07-29.md`](../INTEGRACION_CITYLEARN_THESIS_2026-07-29.md).
