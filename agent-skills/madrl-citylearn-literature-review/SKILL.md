---
name: madrl-citylearn-literature-review
description: Systematic academic literature review workflow for a thesis on CityLearn v2 extended as an experimental CityLearn v3 proposal with cooperative MADRL, Dec-POMDP, CTDE, HAPPO, MASAC, MATD3, MAAC, MARLlib as framework reference, multi-objective energy flexibility, CO2 emissions, energy costs, datasets, GitHub repositories, KPIs, Excel evidence matrices, and SEAI Iquitos applicability.
---

# MADRL CityLearn Literature Review

Use this skill to perform a deep, technical, methodological, and comparative bibliography search for the thesis:

> "Diseño y validación de un sistema eléctrico inteligente con control multiagente basado en aprendizaje por refuerzo profundo para el despacho óptimo bajo restricciones eléctricas y operación segura en el sistema eléctrico aislado de Iquitos, Loreto, Perú - 2026".

## Non-Negotiable Terminology

- Use **MADRL** for Multi-Agent Deep Reinforcement Learning.
- Do not replace MADRL with MARL in titles, worksheet names, conclusions, or methodology.
- Name the methodology worksheet exactly `Marco_metodologico_MADRL`.
- Never use `Marco_metodologico_MARL`.
- Use **MARLlib** only as the proper name of the library/framework/repository.
- Use **MARL** only when it is part of a proper name, paper title, repository, challenge, framework, or library.
- Distinguish **CityLearn v2** as the existing base environment from **CityLearn v3 propuesto** as the thesis experimental extension.
- Do not state that CityLearn v3 is an official external release unless the user explicitly provides such evidence.
- Treat HAPPO, MASAC, MATD3, and MAAC as proposed MADRL backends for the thesis architecture.
- Do not invent DOI, PDF, dataset, GitHub, results, metrics, or conclusions. Use `no identificado publicamente`, `no disponible`, or `no aplica` when evidence is missing.

## Core Objective

Produce an evidence-backed literature review and Excel workbook that supports a proposed CityLearn v3 experimental layer over CityLearn v2. The proposal must be framed as:

- cooperative MADRL;
- Dec-POMDP formalization;
- Centralized Training with Decentralized Execution (CTDE);
- four MADRL backends: HAPPO, MASAC, MATD3, and MAAC;
- optional or reference use of MARLlib for wrappers, algorithm configuration, policy mapping, reproducibility, and possible integration;
- three primary axes: energy flexibility, CO2 emissions reduction, and energy cost reduction.

## Workflow

1. Scope the review around the thesis title, CityLearn v2, CityLearn v3 propuesto, MADRL, Dec-POMDP, CTDE, MARLlib, and the three objective axes.
2. Use the mandatory Boolean strings and keyword groups in [search-protocol.md](references/search-protocol.md).
3. Search priority sources: official docs and repositories, Google Scholar, IEEE Xplore, ScienceDirect, SpringerLink, ACM, Wiley, MDPI, arXiv, OpenReview, PMLR, JMLR, NeurIPS/ICML/ICLR/AAMAS, Energy and Buildings, Applied Energy, Energy AI, Sustainable Cities and Society, IEEE Transactions, ProQuest, EThOS, DART-Europe, TDX, RENATI, GitHub, Papers with Code, NREL, OpenEI, Pecan Street, UK-DALE, REDD, and Open Power System Data.
4. Select 50 relevant investigations from the last 10 years when possible. Include theses, PhD dissertations, MSc theses, indexed papers, proceedings, benchmarks, technical reports, datasets, documentation, and GitHub repositories.
5. Apply inclusion/exclusion rules from [search-protocol.md](references/search-protocol.md). If an older work is foundational, include it only with a note explaining why.
6. Extract metadata into the required Excel schema in [excel-workbook-schema.md](references/excel-workbook-schema.md).
7. Evaluate each backend using [backend-evaluation.md](references/backend-evaluation.md).
8. Build the methodological and architecture sheets using [methodology-and-architecture.md](references/methodology-and-architecture.md).
9. Use APA latest style for citations. Verify author, year, title, venue, DOI/link, PDF link, dataset, and GitHub before recording.
10. Mark unverifiable fields explicitly; do not infer unavailable facts as real results.

## Evidence Rules

- Prefer primary sources: official papers, official documentation, official GitHub repositories, proceedings pages, publisher pages, DOI pages, university repositories, and dataset portals.
- Use secondary sources only to locate primary sources or to contextualize a field.
- For each record, record whether PDF, dataset, DOI, and GitHub were found.
- Separate real reported results from thesis-use inference. Use phrases such as `inferencia metodologica para CityLearn v3 propuesto` when applicable.
- Keep comparison claims conservative unless numerical evidence is reported in the source.

## Output Requirements

Create an Excel workbook with these worksheets exactly:

1. `Matriz_50_investigaciones`
2. `Resumen_ejecutivo`
3. `KPIs_y_metricas`
4. `Marco_metodologico_MADRL`
5. `CityLearn_v3_Propuesto`
6. `Backends_MADRL`
7. `MARLlib_Integracion`
8. `CityLearn_CO2_Costos`
9. `Datasets_y_codigo`
10. `Lectura_priorizada`
11. `Cadenas_de_busqueda`
12. `Glosario_MADRL`
13. `Arquitectura_Propuesta`
14. `Aplicabilidad_SEAI_Iquitos`

Use Spanish academic prose in third person. Maintain technical precision and avoid generic filler.

## Optional Workbook Helper

Use `scripts/create_workbook_template.py` to create an empty workbook with the required sheets and headers:

```powershell
python "tools\skills\madrl-citylearn-literature-review\scripts\create_workbook_template.py" --output revision_bibliografica_madrl_citylearn.xlsx
```

Fill the workbook after evidence collection. The script is a template helper, not a substitute for verification.
