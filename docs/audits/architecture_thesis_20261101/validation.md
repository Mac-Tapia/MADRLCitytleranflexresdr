# Verificación final de la auditoría

Comando ejecutado desde la raíz con el Python canónico:

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -X utf8 -m pytest tests -q -p no:cacheprovider --ignore=tests/fresh_training/test_real_learning.py --junitxml=docs/audits/architecture_thesis_20261101/pytest.xml
```

Código de salida observado: **1**. Contadores JUnit: **1088 aprobadas, 5 fallidas, 0 errores, 0 omitidas; 1093 en total**.

Duración JUnit: 3621.60 s. Cambios de fuente en el ámbito revalidado: 0 / 493 archivos. Ver `source_drift.json`.

**Alcance:** suite propia general, con cuatro microentrenamientos nativos excluidos explícitamente. Incluye simulador e inferencia con dependencias locales; varios tests de evaluación usan checkpoints de `.superpowers`, por lo que no acredita un clon limpio. No se ejecutó la puerta integral fresh sin omisiones ni una campaña anual nueva. Los contadores verdes de este ámbito no cierran H20.

El JUnit y `pytest.log` son la evidencia de esta ejecución. Las discrepancias se detallan en `test_failures.json`.

## Resultados que requieren atención

- `tests.fresh_training.test_duplicate_consolidation::test_consolidate_execute_only_on_matching_plan_in_temp_copy` — failure: AssertionError:  assert 1 == 0  +  where 1 = CompletedProcess(args=['powershell', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', 'D:\\MADRLCitytleranflexresd...test-5381\\test_consolidate_execute_only_0\\evidence\\canonicalization_plan.json'], returncode=1, stdout='', stderr='').returncode
- `tests.fresh_training.test_github_readiness::test_declared_dependencies_cover_runtime_imports` — failure: AssertionError: imports without a declared distribution: {'psutil': 'uc3m/adapters/algorithms/native_entrypoint.py', 'offpolicy': 'uc3m/adapters/citylearn/policy_inference.py', 'common': 'uc3m/adapters/citylearn/policy_inference.py', 'agent': 'uc3m/adapters/citylearn/policy_inference.py', 'ac_discrete': 'uc3m/adapters/citylearn/policy_inference.py', 'utils': 'uc3m/adapters/citylearn/policy_inferen
- `tests.fresh_training.test_repository_layout::test_real_repository_indexes_have_no_active_broken_reference` — failure: AssertionError: ['README.md:567 -> docs/thesis/INFORME_TESIS_MADRL_V1_COMPLETO.docx', 'README.md:568 -> docs/thesis/PLAN_TESIS_MADRL_C...ME.md:61 -> docs/AUDITORIA_INTEGRAL_PROYECTO_2026-07-29.md', 'tools/README.md:5 -> docs/AUDITORIA_TOOLS_2026-07-29.md'] assert ['README.md:5...026-07-29.md'] == []      Left contains 4 more items, first extra item: 'README.md:567 -> docs/thesis/INFORME_TESIS_MADR
- `tests.ops.test_repository_hygiene::test_root_contains_only_project_files` — failure: AssertionError: assert {'PT_TAPIA_ZA...uitos_2.docx'} == set()      Extra items in the left set:   'PT_TAPIA_ZAMBRANO_v6_Iquitos_2.docx'   Use -v to get more diff
- `tests.unit.evaluation.test_tools_use_results_catalog::test_inventory_lists_every_file_still_referencing_the_retired_campaign` — failure: AssertionError: assert {'tools/ops/h...inventory.py'} == set()      Extra items in the left set:   'tools/ops/historical_inventory.py'   Use -v to get more diff

## Dictamen conservado

23 hallazgos: 4 P0, 15 P1, 4 P2.
Layout, workflow, descubrimiento y lint siguen rechazados conforme a sus logs. Aceptación científica: **false**.
