# Índice — Informe de Tesis por Capítulos (MADRL · CityLearn v3 · Iquitos)

**Tesis:** *Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en Comunidades Inteligentes.*
**Autor:** Mac Tapia (mac.tapia.c@uni.pe) · **Universidad:** UNI (Maestría profesionalizante)
**Caso de estudio:** Sistema Eléctrico Aislado de Iquitos (SEAI) — 17 edificios reales, Electro Oriente S.A., Loreto, Perú.
**Algoritmos:** HAPPO, MASAC, MATD3, MAAC · **Ejes:** OE.1 flexibilidad, OE.2 CO₂, OE.3 costos.

> Cada archivo es autocontenido. Cap. 2 = sustento teórico v3 (+ UC3M 7→3); Cap. 4 = implementación/flujo; Cap. 5 = evidencia ejecutada. Word canónico: `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` (generadores en `scripts/`).

---

## Archivos

| # | Archivo | Contenido | Estado |
|---|---|---|---|
| 0 | `00_INDICE.md` | Este índice | Completo |
| 1 | `Capitulo_1_Introduccion.md` | Problema; OG/OE.1–OE.3; H0G/H1G y HE10–HE31; justificación; alcances | Completo |
| 2 | `Capitulo_2_Marco_Teorico.md` | Estado del arte; Dec-POMDP/CTDE con dims reales SEAI (Tabla 2.A; distrito/edificio); 4 algoritmos; **§2.2.5 capa v3; §§2.2.6–2.2.9 UC3M matemático** | Completo |
| 3 | `Capitulo_3_Metodologia.md` | Diseño; dataset Iquitos; §3.4.6 árbol CityLearn retenido; 12 corridas; instrumentos | Completo |
| 4 | `Capitulo_4_Desarrollo_Propuesta.md` | Flujo 1–13; reward 3 ejes; multi-semilla (`n_seeds=12`); Shapiro→no paramétrico | Completo |
| 5 | `Capitulo_5_Resultados.md` | §5.0–5.7; Fig. 5.1–5.14; Tablas 5.1–5.12; catálogo `outputs/`→acápites; KPIs/performance por MADRL | Completo |
| 6 | `Capitulo_6_Conclusiones.md` | Hallazgos; limitaciones; plan H1–H7 actualizado | Completo |
| R | `Referencias_APA.md` | Lista APA unificada | Consolidado |

---

## Resumen de cada capítulo

- **Capítulo 1 — Introducción.** PG/PE; OG y OE.1–OE.3; H0G/H1G y HE10–HE31; justificación; alcances.
- **Capítulo 2 — Marco teórico.** Estado del arte; Dec-POMDP/CTDE; HAPPO/MASAC/MATD3/MAAC con **adecuaciones al dominio eléctrico** (OE.1 flex / OE.2 CO₂ / OE.3 costos; wrappers Cap. 4); capa CityLearn v3 propuesto (§2.2.5); axiomatización UC3M (§§2.2.6–2.2.9); distinción 7 ejes (sustento) vs 3 ejes ejecutados.
- **Capítulo 3 — Metodología.** Cuasiexperimento factorial 4×3; dataset Iquitos; árbol CityLearn retenido (§3.4.6); 12 corridas; instrumentos KPI y batería estadística.
- **Capítulo 4 — Desarrollo.** Flujo 1–13; arquitectura v3; reward por OE; diseño multi-semilla implementado; protocolo Shapiro → no paramétrico.
- **Capítulo 5 — Resultados.** §5.0–5.7 con inventarios de todas las carpetas `outputs/`; Fig. 5.1–5.14 (55 PNG embebidos); Tablas 5.1–5.12; OE.1 MAAC/MATD3; OE.2 MATD3; OE.3 MAAC; OG H1G exploratoria (`best_madrl` MATD3 0,6667); performance por MADRL; baseline v2; TOPSIS; catálogo §5.7.
- **Capítulo 6 — Conclusiones.** Hallazgos, limitaciones, plan de cierre (H1 KPI-gains ejecutados; H2 diseño+smoke; campaña 12-seed pendiente de entrenamiento).
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
| 6 | Sí | H7 institucional (F9/PDF/asesor) |
| Ref. | Sí | Cotejo manual DOI opcional (sin inventar) |

> **Resultados Cap. 5.** Corrida `madrl_v3_20260627_164047`; KPI recalc `outputs/_drive_madrl/kpi_recalc_20260728/`. Drive: https://drive.google.com/drive/folders/1ihH6RqL2KpevfCQEUXj7PP1aS2QYssAX

## Integración CityLearn (2026-07-29)

Barrios upstream, challenges 2020–2023 y launchers `*_iquitos_training.ps1` se **retienen** e integran en Caps. 2–4 como reproducibilidad/contexto (no como resultados Cap. 5). Informe: [`../INTEGRACION_CITYLEARN_THESIS_2026-07-29.md`](../INTEGRACION_CITYLEARN_THESIS_2026-07-29.md).
