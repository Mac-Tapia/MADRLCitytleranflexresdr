---
name: madrl-citylearn-thesis-integrated
description: Project-local thesis integration workflow for the CityLearn v3 proposed MADRL thesis. Use when Codex must create or update the professional master's thesis report, APA-cited bibliography matrix, systematic review outputs, methodology, consistency matrices, operationalization matrices, appendices, and final quality control for the project on CityLearn v2, CityLearn v3 propuesto, cooperative MADRL, Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib, Optuna, energy flexibility, CO2 emissions, energy costs, and SEAI Iquitos.
---

# MADRL CityLearn Integrated Thesis Skill

Use this project-local skill only inside this repository to connect the scientific literature review, implementation evidence, and final thesis report for:

> "Multi-Agente de Aprendizaje por Refuerzo Profundo para la Gestión Coordinada de Flexibilidad Energética, Emisiones de Carbono y Costos Energéticos en Comunidades Inteligentes".

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

## Guide N. 02 Structure Rule

- The final thesis report must preserve the exact Guide N. 02 section 5.1 structure defined in [module-b-thesis-report.md](references/module-b-thesis-report.md). The Guide N. 02 is only the report structure, not a source of experimental data.
- Do not replace, remove, rename, or reorder the required front matter, chapters, subsections, references, or annexes.
- Use only current project evidence from this repository for dataset, BESS/PV/EV, training, KPI, statistical, and GPU content.
- Do not use historical, copied, external, or non-current data as thesis evidence. Tables, results, conclusions, and discussion must be based only on active current project sources.
- Current project evidence must be inserted inside the corresponding Guide N. 02 sections, mainly Chapter III, without creating an alternative report structure.
- If current results are incomplete, keep the Guide N. 02 structure and mark the missing values as pending, in progress, or not verified. Do not fill gaps with non-current values.

## Operating Workflow

1. Read this `SKILL.md`.
2. For the literature search and Excel matrix, use [module-a-literature-matrix.md](references/module-a-literature-matrix.md).
3. For the thesis report structure and required content, use [module-b-thesis-report.md](references/module-b-thesis-report.md).
4. For APA and quality checks, use [apa-quality-control.md](references/apa-quality-control.md).
5. For consistency and operationalization matrices, use [matrices-and-appendices.md](references/matrices-and-appendices.md).
6. Use `scripts/create_integrated_thesis_workbook.py` to create a workbook template when requested.
7. Use `scripts/create_thesis_docx_skeleton.py` to create a DOCX thesis skeleton when requested.
8. Use `scripts/create_available_thesis_report.py` to create a Guide N. 02 DOCX/Markdown draft from current project evidence only; final KPIs must remain pending when training artifacts are incomplete.
9. Use project evidence when available:
   - `README.md`, `docs/PLAN_TESIS_MADRL_CITYLEARN_V3_IQUITOS.md`
   - `CityLearn/configs/citylearn_v3_madrl_training.yaml`
   - Training v4 activo tras reinicio limpio: `outputs/citylearn_v3_madrl_oficial_v4/`
     - Estado oficial: `official_full_status.json`
     - Progreso vivo por corrida: `{algo}/{scenario}_seed_0/live_progress.json`
     - Resultados finales por corrida, solo cuando existan tras completar el entrenamiento nuevo: `{algo}/{scenario}_seed_0/data/results.json`
     - Series y trazas finales por corrida: `{algo}/{scenario}_seed_0/data/timeseries.csv`, `{algo}/{scenario}_seed_0/data/trace.csv`
     - Comparación estadística final: `statistical_comparison/result_{algo}_{scenario}.json`, `timeseries_{algo}_{scenario}.csv`, `trace_{algo}_{scenario}.csv`
     - Preflight de artefactos: `artifact_layout_preflight.json`
   - Auditorías de dataset: `outputs/dataset_audit/` (`csv_integrity_manifest.json`, `training_dataset_ready_manifest.json`, `der_sizing_audit.csv`, `ev_charger_sizing_audit.csv`)
   - Validación: `docs/INFORME_VALIDACION_DATASET_ENTRENAMIENTO_IQUITOS.md`
   - Dimensiones del entorno: `CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json`

> **Vigencia:** Training oficial v4 relanzado desde cero el 2026-06-08 20:14:44 UTC-5 con CUDA=True, PyTorch 2.8.0+cu126 y perfil `local4060_fast` para NVIDIA GeForce RTX 4060 Laptop GPU 8 GB. Dataset activo: `citylearn_iquitos_2023_2025` (17 edificios SEAI Iquitos, 26 304 h, 222 CSV auditados, 185 cargadores EV en schema, 96 equipos físicos modo 3, 17 máquinas controladas, `weather.csv`, `carbon_intensity.csv` y `pricing.csv` referenciados por los 17 edificios). Auditoría integral: 0 NaN, 0 Inf, sin cargadores/máquinas huérfanos ni faltantes; normalización permitida. Totales DER vigentes: PV 48 790.9 kWp; BESS 26 266 kWh / 6 648 kW; EV 749.4 kW. Regla implementada en el dataset: la generación solar prioriza recarga EV y carga del edificio por edificio; el BESS se dimensiona por balance PV-EV-red pública-cargas controladas/no controladas, prioriza recarga EV dentro de la ventana operativa del edificio y luego atiende carga del edificio/pico. Salida activa: `outputs/citylearn_v3_madrl_oficial_v4/`. Última actualización del skill: 2026-06-09.

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
- Tabla de resultados por KPI y algoritmo con datos reales de training v4 (cuando estén disponibles; no inventar).
- Nota metodológica de las 4 pruebas estadísticas inter-algoritmo (Shapiro-Wilk, Kruskal-Wallis, Mann-Whitney U, Wilcoxon) sobre los artefactos `statistical_comparison/`.
