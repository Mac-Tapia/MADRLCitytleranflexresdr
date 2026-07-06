---
name: madrl-citylearn-thesis-integrated
description: Project-local thesis integration workflow for the doctoral CityLearn v3 proposed MADRL thesis. Use when Codex must create or update the doctoral thesis report (informe final), APA-cited bibliography matrix, systematic review outputs, experimental cause-effect methodology, hypotheses testing, consistency matrices, operationalization matrices, appendices, and final quality control for CityLearn v2, CityLearn v3 propuesto, cooperative MADRL, Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib, energy flexibility, CO2 emissions, energy costs, and SEAI Iquitos.
---

# MADRL CityLearn Integrated Thesis Skill

Use this project-local skill only inside this repository to connect the scientific literature review, implementation evidence, and final **doctoral thesis report** for:

> "Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de la Flexibilidad Energética, las Emisiones de Carbono y los Costos Energéticos en Comunidades Inteligentes".

**Documento canónico:** `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`

**Borradores Markdown:** `docs/tesis_capitulos/` (Capítulos 1–6 + Referencias APA).

## Purpose

Create one integrated academic workflow that:

1. Builds a deep, verifiable bibliography on CityLearn v2, MADRL, Dec-POMDP, CTDE, MARLlib, HAPPO, MASAC, MATD3, MAAC, energy flexibility, CO2 emissions, and energy costs.
2. Produces a comparative matrix of 50 relevant investigations from the last 10 years when possible.
3. Extracts antecedents, theoretical bases, datasets, GitHub repositories, KPIs, results, scientific contributions, and conclusions from the matrix.
4. Drafts the **doctoral thesis report** following the six-chapter structure of `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` (not Guide N. 02 unless the institution requires a separate submission).
5. Applies current APA style throughout.
6. Generates only verified references; never invent DOI, links, datasets, repositories, citations, or results.

## Degree and cover metadata

- **Universidad:** UNI — Escuela de Posgrado
- **Programa:** Doctorado en Ingeniería — Inteligencia Artificial aplicada a Sistemas Eléctricos Inteligentes
- **Grado:** Doctor en Ingeniería
- **Autor:** Mac Tapia
- **Caso de estudio:** SEAI Iquitos — 17 edificios reales (2023–2025)
- **Asesor:** `[por definir]` until confirmed

## Mandatory Terminology

- Use **MADRL** whenever the concept is Multi-Agent Deep Reinforcement Learning.
- Do not replace MADRL with MARL.
- Do not use `Marco_metodologico_MARL`.
- Use exactly `Marco_metodologico_MADRL`.
- Use **MARLlib** only as the proper name of the library/framework/repository.
- Use **MARL** only when part of a proper name such as a paper, repository, challenge, library, or framework.
- Distinguish **CityLearn v2** as the existing base environment from **CityLearn v3 propuesto** as the thesis experimental extension.
- Never state that CityLearn v3 exists officially outside the thesis.
- Present HAPPO, MASAC, MATD3, and MAAC as MADRL backends proposed by the investigation.
- Write in formal academic Spanish, third person.
- Do not invent results, DOI, links, datasets, GitHub repositories, citations, or references.

## Experimental cause-effect frame

The thesis uses a **simulation-based experimental design** (not merely comparative-descriptive):

- **VI:** algoritmo MADRL — D-VI.1 (HAPPO, MASAC, MATD3, MAAC) × D-VI.2 (E1, E2, E3) → 12 tratamientos
- **VD:** desempeño coordinado medido con **54 KPI oficiales** en D-VD.1 flexibilidad, D-VD.2 CO₂, D-VD.3 costos
- **Control:** dataset Iquitos, clima, CI, TOU, recompensa `unified_comparable_v4`, semilla
- **Hipótesis:** HG, HE.1, HE.2, HE.3 (directional; contrastadas con Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U, Wilcoxon; α = 0,05)

Use the exact PG/PE/OG/OE/HG/HE wording from [module-b-thesis-report.md](references/module-b-thesis-report.md).

## APA Rules

- Use current APA style only; do not use IEEE.
- Cite every technical, methodological, conceptual, or antecedent claim.
- Use parenthetical citations as `(Autor, año)`.
- Use narrative citations as `Autor (año)`.
- Use `Autor & Autor` for two authors and `Autor et al.` for three or more authors.
- Ensure every in-text citation has a final reference.
- Ensure every final reference is cited in the text.
- Mark incomplete source data as `dato bibliografico pendiente de verificacion`.
- Mark unconfirmed results as `resultado no verificado` and do not use them as conclusive evidence.

## Thesis structure rule (six chapters)

- The final thesis report must preserve the exact structure defined in [module-b-thesis-report.md](references/module-b-thesis-report.md), aligned with `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`.
- Chapters: 1 Introducción, 2 Marco teórico, 3 Metodología, 4 Desarrollo de la propuesta, 5 Resultados y contrastación de hipótesis, 6 Conclusiones y trabajo futuro.
- Do not replace, remove, rename, or reorder required front matter, chapters, subsections, references, or annexes without explicit user instruction.
- Use only current project evidence from this repository for dataset, BESS/PV/EV, training, KPI, statistical, and GPU content.
- If canonical 50-episode results are incomplete, keep the structure and mark values as preliminares or `[Pendiente: corrida canónica 50 ep]`.

## Operating Workflow

1. Read this `SKILL.md`.
2. Read `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx` or `docs/tesis_capitulos/` for the authoritative wording and structure.
3. For the literature search and Excel matrix, use [module-a-literature-matrix.md](references/module-a-literature-matrix.md).
4. For the thesis report structure and required content, use [module-b-thesis-report.md](references/module-b-thesis-report.md).
5. For APA and quality checks, use [apa-quality-control.md](references/apa-quality-control.md).
6. For consistency and operationalization matrices, use [matrices-and-appendices.md](references/matrices-and-appendices.md).
7. Use `scripts/create_integrated_thesis_workbook.py` to create a workbook template when requested.
8. Use `scripts/create_thesis_docx_skeleton.py` to create a DOCX thesis skeleton when requested.
9. Use `scripts/create_available_thesis_report.py` to create a DOCX/Markdown draft from current project evidence only.
10. Use project evidence when available:
   - `README.md`, `docs/thesis/PLAN_TESIS_MADRL_CITYLEARN_V3_IQUITOS.md`
   - Corrida canónica Colab/Drive: `outputs/madrl_v3_20260627_164047/` (`best_madrl_report.json`, `resumen_comparativo/`)
   - Análisis multiobjetivo distrito/edificio: `outputs/madrl_v3_20260627_164047/resumen_comparativo/multiobjetivo/`
   - KPIs auditados: `outputs/_drive_madrl/kpis/`, CSVs por edificio en `outputs/_drive_madrl/full_data/`
   - Generadores Word finales:
     - `scripts/generate_tesis_doctoral_final_docx.py` → `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`
     - `tools/build_multiobjective_thesis_docx.py` → anexo multiobjetivo `.docx`
     - `scripts/thesis_doctoral_sections.py` + `scripts/verify_tesis_doctoral_docx` (verificación)

> **Vigencia técnica (2026-07-05):** Corrida canónica **`madrl_v3_20260627_164047`** (Colab, 50 ep MATD3/MAAC/MASAC). Mejor MADRL: **MATD3** (score 0,6667). Análisis multiobjetivo: 17 edificios, 185 EV, 153 filas KPI edificio. HAPPO: 49/50 ep, sin KPIs. Perfil `unified_comparable_v4`, γ = 0,9999, estado global 1 856 dims.

## Required Final Products

- Bibliographic matrix of 50 investigations.
- Dataset, GitHub, and source matrix.
- KPI matrix (54 official KPIs mapped to D-VD.1–3).
- `Marco_metodologico_MADRL`.
- `CityLearn_v3_Propuesto`.
- `Backends_MADRL`.
- `MARLlib_Integracion`.
- `Arquitectura_Propuesta`.
- `Aplicabilidad_SEAI_Iquitos`.
- Complete doctoral thesis report (six chapters) aligned with `docs/Tesis_Doctoral_MADRL_CityLearn_Iquitos.docx`.
- Spanish `Resumen` and English `Abstract` with cause-effect framing.
- Matrices Tabla 1.1 (consistencia) and Tabla 1.2 (operacionalización VI/VD).
- Hypothesis contrastation section (Cap. 5.4) with descriptive + inferential statistics.
- APA references (`docs/tesis_capitulos/Referencias_APA.md`).
- Methodological appendices.
- Consistency matrix.
- Variable operationalization matrix.
- Table of APA citations used.
- Final quality-control checklist.
- Tabla ranking por escenario (Tabla 5.2) and Wilcoxon matrix (Tabla 5.3) with real or marked-pending values.
- Nota metodológica: 4 pruebas estadísticas (Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U, Wilcoxon).
- Sección aportes A1–A4 al motor CityLearn (`docs/thesis/APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md`).

## Related skill — Plan de Tesis

For the **Plan de Tesis** under Guía N. 01 (pre-doctoral planning document), use the companion skill `agent-skills/madrl-citylearn-thesis-plan/`. Its objectives, hypotheses, and experimental design must remain **vertically coherent** with this doctoral thesis report.
