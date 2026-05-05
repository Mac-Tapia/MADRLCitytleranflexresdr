---
name: madrl-citylearn-thesis-integrated
description: Project-local thesis integration workflow for the CityLearn v3 proposed MADRL thesis. Use when Codex must create or update the professional master's thesis report, APA-cited bibliography matrix, systematic review outputs, methodology, consistency matrices, operationalization matrices, appendices, and final quality control for the project on CityLearn v2, CityLearn v3 propuesto, cooperative MADRL, Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib, Optuna, energy flexibility, CO2 emissions, energy costs, and SEAI Iquitos.
---

# MADRL CityLearn Integrated Thesis Skill

Use this project-local skill only inside this repository to connect the scientific literature review, implementation evidence, and final thesis report for:

> "Diseño y validación de un sistema eléctrico inteligente con control multiagente basado en aprendizaje por refuerzo profundo para el despacho óptimo bajo restricciones eléctricas y operación segura en el sistema eléctrico aislado de Iquitos, Loreto, Perú - 2026".

## Purpose

Create one integrated academic workflow that:

1. Builds a deep, verifiable bibliography on CityLearn v2, MADRL, Dec-POMDP, CTDE, MARLlib, HAPPO, MASAC, MATD3, MAAC, energy flexibility, CO2 emissions, and energy costs.
2. Produces a comparative matrix of 50 relevant investigations from the last 10 years when possible.
3. Extracts antecedents, theoretical bases, datasets, GitHub repositories, KPIs, results, scientific contributions, and conclusions from the matrix.
4. Drafts a professional master's thesis report following the mandatory Guide N. 02 structure.
5. Applies current APA style throughout.
6. Generates only verified references; never invent DOI, links, datasets, repositories, citations, or results.

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

## Operating Workflow

1. Read this `SKILL.md`.
2. For the literature search and Excel matrix, use [module-a-literature-matrix.md](references/module-a-literature-matrix.md).
3. For the thesis report structure and required content, use [module-b-thesis-report.md](references/module-b-thesis-report.md).
4. For APA and quality checks, use [apa-quality-control.md](references/apa-quality-control.md).
5. For consistency and operationalization matrices, use [matrices-and-appendices.md](references/matrices-and-appendices.md).
6. Use `scripts/create_integrated_thesis_workbook.py` to create a workbook template when requested.
7. Use `scripts/create_thesis_docx_skeleton.py` to create a DOCX thesis skeleton when requested.
8. Use project evidence when available: README, `ESTRATEGIA_3PILARES_MADRL.md`, `docs/`, `CityLearn/configs/`, training outputs, benchmark scripts, and validation scripts.

## Required Final Products

- Bibliographic matrix of 50 investigations.
- Dataset, GitHub, and source matrix.
- KPI matrix.
- `Marco_metodologico_MADRL`.
- `CityLearn_v3_Propuesto`.
- `Backends_MADRL`.
- `MARLlib_Integracion`.
- `Arquitectura_Propuesta`.
- `Aplicabilidad_SEAI_Iquitos`.
- Complete thesis report under Guide N. 02 section 5.1.
- Spanish `Resumen` and English `Abstract`.
- APA references.
- Methodological appendices.
- Consistency matrix.
- Variable operationalization matrix.
- Table of APA citations used.
- Final quality-control checklist.

