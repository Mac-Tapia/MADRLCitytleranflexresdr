# Runbook de la campaña nueva (sin resultados históricos)

Campaña `fresh_iquitos_20261101_v1`, alias de almacenamiento `iquitos_v1`.
Plan: `docs/plans/entrenamiento.md`; diseño: `docs/design/entrenamiento.md`.
Estado vigente: `specs/STATUS.md`.

Remediación actual: [contrato v1 y diferencias con el PT](../decisions/contrato_v1_pt.md), [acta de ejecución](../audits/ejecucion_remediacion_20261101/informe.md). Preparar una campaña nueva congela el contrato de algoritmos, todas las entradas, supervisión y aplicabilidad de KPI; una campaña de un corte anterior no se vuelve válida editando hashes manualmente.

El desbloqueo de test pertenece a los artefactos de la campaña explícita y se genera al revalidar la selección HPO. Se conserva con Drive; un `test_unlock.json` arbitrario junto al dataset no abre el conjunto de prueba. Los KPI finales requieren evidencia física del horizonte completo (8784 pasos de validación en 2024 y 8760 de test en 2025); los diagnósticos cortos no cumplen esa puerta. Las configuraciones HPO que comparten una semilla son candidatos distintos, no réplicas adicionales.

Si el planificador aplica un presupuesto de replay, cada intento conserva `phase_budget.json` con su identidad y la copia íntegra del presupuesto utilizado, escrita antes del aprendiz. La restauración y el reuso de un intento completo no dependen de un resultado final de etapa que aún podría no existir tras un corte. Esta custodia no habilita recortar buffers del contrato canónico: actualmente no declara `phase_buffer` y conserva la capacidad nativa.

## Reglas que no cambian

- Única vía de lanzamiento: `python -m uc3m.application.training.cli`. Los
  lanzadores locales `.bat`/`.ps1`, `uc3m/train.py`, el runner Colab anterior y
  AWS están retirados (`governance/repository_layout.yaml`, sección `launch`).
- El entrenamiento se ejecuta en Colab con el cuaderno existente
  `examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb`, cliente de la CLI.
- Ningún intento reanuda: cada intento empieza en el episodio 0. Un intento
  interrumpido o con *salvage* queda como evidencia fallida y se lanza otro.
- Ninguna entrada puede venir de `outputs/` históricos, del dataset horario
  anterior de CityLearn, de `.cache/` ni de punteros `latest_*`.
- Importes en USD. Facturas en PEN convertidas con la tasa oficial anual del
  Banco Mundial (PA.NUS.FCRF).

## 1. Dataset nuevo (T2)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/dataset/build_fresh_campaign_dataset.py --campaign-id fresh_iquitos_20261101_v1 --storage-alias iquitos_v1
```

Escribe `data/campaigns/iquitos_v1/{raw,dataset,audit}`, `provenance.json`,
`quality_flags.csv`, `dataset_build_manifest.json` y `dataset_acceptance.json`.
Solo continuar si `dataset_verified=true`. Si la raíz existe, el constructor se
niega: un intento fallido se mueve a `data/maintenance/dataset_builds/failed/`.

## 2. Splits y normalizador congelados (T3)

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/dataset/split_campaign.py --storage-alias iquitos_v1
```

Escribe `splits/{train_2023,validation_2024,test_2025}`, `split_manifest.json`
(con los parámetros de equipos fijados por diseño, `design_seed=0`),
`normalizer.json` (límites ajustados solo con 2023) y `split_smoke.json`.

## 3. Preparar la campaña (no entrena)

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -m uc3m.application.training.cli --config configs/experiments/iquitos.yaml --stage prepare
```

Crea `outputs/campaigns/iquitos_v1/campaign_manifest.json` y
`stages/{pilot,hpo,confirm,sensitivity}.json`. Presupuesto: piloto 4
tratamientos × 3 episodios de 8760 pasos / 105 120 pasos (mide RAM, VRAM y tiempo
reales; no cuenta como confirmación); HPO 288 / 25 228 800 (capacidad nativa sin
recortes: 8 configuraciones efectivas por algoritmo); confirmación 144 /
63 072 000; sensibilidad 72 / 31 536 000. Cada etapa entrena por fases
({HAPPO, MASAC} y luego {MATD3, MAAC}) con trabajadores limitados por los recursos
medidos: `prepare` no entrena, pero mide la RAM y la VRAM libres y las CPU para
imprimir `phase_plan`.
Confirmación y sensibilidad exigen `configuration_freezes.json` (congelado por
algoritmo seleccionado en validación); sensibilidad genera catálogos de pesos
derivados con hash en `stages/sensitivity_catalogs/`. Cada intento escribe
`supervision.json` y se rechaza si los términos EV/BESS dominan los ejes
ponderados (`supervision.max_constraint_dominance_ratio`).

## 4. Ejecutar una etapa (solo con recursos autorizados)

1. El propietario añade la etapa en `resource_authorization.authorized_stages`
   de `configs/experiments/iquitos.yaml` y se prepara de nuevo (cambia la
   identidad de la configuración).
2. Regenerar el paquete local para Colab:
   `python -B tools/colab/build_modular_colab_notebook.py` crea
   `outputs/colab_delivery/colab_modular_overlay.zip`.
3. En el cuaderno, fijar `RUN_STAGE = 'pilot'` (luego `hpo`, `confirm`,
   `sensitivity`) y ejecutar. Cada intento terminado se copia a Drive.

Orden obligatorio: piloto → HPO (selección en validación 2024) → congelado de
configuración → confirmación → sensibilidad → evaluación congelada en prueba
2025. `confirm` y `sensitivity` se niegan sin congelado de configuración.

## 5. Revisar fallos

Cada intento deja `attempt.json`, `child.log`, `learning_evidence.json` y
`completion.json`. Rechazos y su significado:

| Motivo | Significado |
|---|---|
| `no_successful_update:<owner>` | El optimizador no aplicó ninguna actualización con gradientes finitos |
| `parameters_unchanged:<owner>` | Hubo pasos, pero los parámetros no cambiaron |
| `completed_with_salvage` | El backend capturó una excepción y guardó artefactos; no es completitud |
| `trajectory_shorter_than_target` | Los pasos reales no alcanzan episodios × horas declarados |
| `no_checkpoint` | No hay un paquete de checkpoint recargable con tensores finitos |

Recuperación: no editar el intento. Lanzar la etapa de nuevo crea `try_NN+1`
desde cero con la misma identidad de tratamiento.

## 6. Retiro de históricos (T0)

```powershell
powershell -ExecutionPolicy Bypass -File scripts/maintenance/retire_historical_outputs.ps1 -Phase Plan
powershell -ExecutionPolicy Bypass -File scripts/maintenance/retire_historical_outputs.ps1 -Phase Execute -Manifest data/maintenance/historicos/retirement_plan.json
```

Solo la lista cerrada R-01..R-07. Resultado en
`data/maintenance/historicos/retirement_result.json`.
