# Traspaso para auditoría: implementación de la campaña nueva

Fecha: 2026-11-01. Alcance: plan `docs/plans/entrenamiento.md` (T0–T14) y diseño
`docs/design/entrenamiento.md`. Estado por requisito: `specs/STATUS.md`, sección
«Campaña nueva». Procedimiento: `docs/architecture/runbook.md`. Nada está
confirmado en Git: todo el trabajo está en el árbol de trabajo de la rama actual.

El auditor debe verificar con los comandos, no con este resumen. Rol sugerido:
`.claude/agents/madrl-auditor` (solo lectura), skills
`tools/skills/madrl-spec-conformance` y `madrl-experiment-evidence-audit`.

## Qué revisar y cómo

| Área | Archivos | Verificación |
| --- | --- | --- |
| Retiro de históricos (T0) | `tools/ops/historical_inventory.py`, `scripts/maintenance/retire_historical_outputs.ps1` | `pytest tests/fresh_training/test_historical_retirement.py`; leer `data/maintenance/historicos/retirement_result.json` |
| Aislamiento e identidad (T1) | `uc3m/domain/campaigns.py`, `uc3m/application/training/fresh_policy.py` | `pytest tests/fresh_training/test_fresh_isolation.py` |
| Dataset nuevo (T2) | `tools/dataset/build_fresh_campaign_dataset.py`, `uc3m/application/dataset/{provenance,construction}.py` | `pytest tests/fresh_training/test_dataset_provenance.py test_der_sizing_inputs.py`; `data/campaigns/iquitos_v1/{provenance.json,dataset_acceptance.json,quality_flags.csv}` |
| Splits y normalizador (T3) | `uc3m/application/dataset/splits.py`, `uc3m/adapters/citylearn/fresh_observations.py`, `tools/dataset/split_campaign.py` | `pytest tests/fresh_training/test_temporal_contract.py`; `split_manifest.json`, `normalizer.json`, `split_smoke.json` |
| KPI (T4) | `uc3m/application/evaluation/kpi_contract.py`, `configs/evaluation/kpis.yaml` | `pytest tests/fresh_training/test_kpi_physical_contract.py` |
| Aprendizaje real (T5) | `uc3m/adapters/algorithms/{native_entrypoint,learning_observer}.py` | `pytest tests/fresh_training/test_learning_observer.py test_real_learning.py` (micro-entrenamiento real) |
| Campaña y CLI (T6) | `configs/experiments/iquitos.yaml`, `configs/algorithms/native.yaml`, `uc3m/application/training/{fresh_campaign,cli}.py` | `pytest tests/fresh_training/test_campaign_contract.py test_single_launch_path.py`; `python -m uc3m.application.training.cli --config configs/experiments/iquitos.yaml --stage prepare` |
| Evaluación congelada (T7 parte 1) | `uc3m/adapters/citylearn/policy_inference.py` | `pytest tests/fresh_training/test_frozen_evaluation.py` (no ejecutada aún en esta sesión) |
| Estadística (T9) | `uc3m/application/evaluation/fresh_analysis.py` | `pytest tests/fresh_training/test_seed_statistics.py` |
| Colab | `tools/colab/build_modular_colab_notebook.py`, `examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb` | `pytest tests/fresh_training/test_colab_client.py tests/ops/test_modular_colab_notebook.py` |
| Árbol y nombres (T12/T14) | `governance/{repository_layout,naming}.yaml`, `data/maintenance/layout/*.json`, `data/maintenance/names/*` | `pytest tests/fresh_training/test_names.py`; `python -m tools.ops.audit_names --phase inventory --output <tmp>` |
| Puerta (T10) | `scripts/quality/run_fresh_training_gates.ps1` | ejecutar el script; leer `data/maintenance/gates/*.json` |

## Evidencia real producida

- Dataset `data/campaigns/iquitos_v1`: hash `6adc312c54062275bbe7bba886c60a0cf516f6419d4e4c781d42f3dc77033cbd`,
  1836 cierres mensuales dentro de 0,01 %, 222 CSV sin NaN/Inf, 17 edificios, precios
  0,112–0,2245 USD/kWh.
- Splits 8760/8784/8760 con smoke real (reset + 24 pasos finitos, sin campos `_predicted_`).
- Micro-entrenamiento real (2 episodios × 168 h, CPU, intento nuevo): HAPPO verificado
  (180 actualizaciones observadas en 18 dueños, parámetros cambiados, sin salvage);
  MASAC verificado (2 actualizaciones × 4 dueños). MATD3: el primer intento se cortó por el
  límite de tiempo de la prueba (3600 s en CPU), sin evidencia de aprendizaje; la prueba ya
  usa `--cuda` y un límite mayor y debe repetirse. MAAC: en curso al redactar esto.

## Decisiones tomadas que el auditor debe juzgar

1. B01 2023 sin medición: retroproyección declarada 0,98 × perfil 2024 (decisión del
   propietario), marcada `cross_year_leakage_declared`.
2. B01 2024–2025-10: energía medida del libro `docs/thesis/resultados_preliminares.xlsx`
   (hoja 8.ELOR) con reparto punta/fuera de punta de los pares Office del mismo mes.
3. FV con el método del generador base (área techada × 0,63 / área del módulo, pvlib SAPM)
   sobre clima NASA POWER observado; EV, BESS y cargas controladas como los scripts originales.
4. Moneda USD: facturas PEN convertidas con la tasa anual del Banco Mundial (el API del BCRP
   está protegido contra bots y no se eludió).
5. Parámetros de equipos congelados con `design_seed=0` en todos los splits: CityLearn
   sorteaba la eficiencia de la bomba de calor con la semilla del entorno.
6. Normalizador ajustado solo en 2023 y servido congelado; el dataset anterior estimaba
   límites sobre 2023–2025.
7. Única vía de lanzamiento (CLI); lanzadores locales, AWS, `uc3m/train.py`,
   `uc3m/application/training/colab.py`, `uc3m/configs/` y 14 herramientas de notebook
   retirados (recuperables desde Git).
8. `--cuda` en todos los tratamientos: los lanzadores nativos usan CPU con un hilo por defecto.

## Huecos conocidos (no cerrados)

- T5: falta la evidencia verificada de MATD3 y MAAC.
- T7 parte 2: cargadores de política nativa para evaluar en validación (sin ellos no hay
  selección HPO ni confirmación).
- T8: selección de hiperparámetros, congelado de configuración, catálogos de pesos
  derivados para sensibilidad, medición del piloto.
- T10: pruebas de seguridad (hash de checkpoint, panel loopback, manifiesto antiguo).
- T12: tres notebooks tutoriales aún llaman a los entrenadores directamente; comparación de
  los tres Word sin ejecutar.
- T13: preparación GitHub sin empezar. Suite completa del repositorio no re-ejecutada tras
  los últimos retiros.
- `implementation_ready_for_training=false`, `scientific_acceptance=false`.
