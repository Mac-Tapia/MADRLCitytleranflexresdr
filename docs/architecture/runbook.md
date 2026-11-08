# Runbook de la campaña nueva (sin resultados históricos)

Campaña `fresh_iquitos_20261108_v6_trial11`, alias de almacenamiento `iquitos_v6_trial13`
(`configs/experiments/iquitos.yaml`, que manda si este texto se queda atrás).
Pasos en Colab hasta el piloto: [plan del módulo 8](../plans/modulo8_campana.md).
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

El dataset activo ya está construido y no hay que rehacerlo:
`data/campaigns/iquitos_v6_trial13/dataset_acceptance.json` tiene
`dataset_verified=true`, 12 de 12 puertas y hash `d4ccd3d3…`.

Un dataset nuevo lleva otro alias y otra campaña. Estas son las opciones del
constructor; `dataset_build_manifest.json` no guarda la línea exacta usada en
`iquitos_v6_trial13`:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/dataset/build_fresh_campaign_dataset.py --campaign-id <campaign_id> --storage-alias <alias> --dataset-version v6 --bess-design-rule
```

Escribe `data/campaigns/<alias>/{raw,dataset,audit}`, `provenance.json`,
`quality_flags.csv`, `dataset_build_manifest.json` y `dataset_acceptance.json`.
Solo continuar si `dataset_verified=true`. Si la raíz existe, el constructor se
niega: un intento fallido se mueve a `data/maintenance/dataset_builds/failed/`.

## 2. Splits y normalizador congelados (T3)

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/dataset/split_campaign.py --storage-alias <alias>
```

Escribe `splits/{train_2023,validation_2024,test_2025}`, `split_manifest.json`
(con los parámetros de equipos fijados por diseño, `design_seed=0`),
`normalizer.json` (límites ajustados solo con 2023) y `split_smoke.json`.

## 3. Preparar la campaña (no entrena)

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B -m uc3m.application.training.cli --config configs/experiments/iquitos.yaml --stage prepare
```

Crea `outputs/campaigns/iquitos_v6_trial13/campaign_manifest.json` y
`stages/{pilot,hpo,confirm,sensitivity}.json`. Presupuesto: piloto 4
tratamientos × 3 episodios de 8760 pasos / 105 120 pasos (mide RAM, VRAM y tiempo
reales, pero no alcanza el lote de 32 episodios de MASAC; no cuenta como
confirmación); HPO 252 / 22 075 200 (capacidad nativa sin recortes: 8
configuraciones efectivas en HAPPO, MATD3 y MAAC, y 4 en MASAC por D-M3-8); confirmación 144 /
63 072 000; sensibilidad 72 / 31 536 000. Cada etapa entrena por fases
({HAPPO, MASAC} y luego {MATD3, MAAC}) con trabajadores limitados por los recursos
medidos: `prepare` no entrena, pero mide la RAM y la VRAM libres y las CPU para
imprimir `phase_plan`.
Confirmación y sensibilidad exigen `configuration_freezes.json` (congelado por
algoritmo seleccionado en validación); sensibilidad genera catálogos de pesos
derivados con hash en `stages/sensitivity_catalogs/`. Cada intento escribe
`supervision.json` y se rechaza si los términos EV/BESS dominan los ejes
ponderados (`supervision.max_constraint_dominance_ratio`).

## 4. Ejecutar una etapa (solo con decisión escrita del propietario)

Pasos completos, puertas y limitaciones: [plan del módulo 8](../plans/modulo8_campana.md).

1. El propietario deja escrita su decisión, con fecha y etapa. No se edita
   `configs/experiments/iquitos.yaml`, porque entra en la identidad de la campaña:
   `authorized_stages` sigue en `[]`. Autorizar no requiere ningún commit.
2. Regenerar el paquete local para Colab una sola vez por campaña, después del
   último commit:
   `.\.venv39-citylearn-v3\Scripts\python.exe -B tools/colab/build_modular_colab_notebook.py`
   crea `outputs/colab_delivery/colab_modular_overlay.zip`. Conservar ese ZIP
   mientras dure la campaña.
3. En el cuaderno, fijar `STAGE` en C5 (`pilot`, y luego `hpo`, `confirm`,
   `sensitivity`) y revisar el plan que imprime.
4. En C6, poner `EXECUTE_STAGE = True`, escribir en `OWNER_DECISION` dónde y cuándo
   quedó la decisión, y ejecutarla. C6 pasa `--owner-authorized <texto>` a la CLI,
   que añade una línea a `stages/owner_authorizations.jsonl`. Al relanzar la misma
   etapa se repite la misma referencia. Cada
   intento terminado se copia a Drive. Al terminar, volver a `EXECUTE_STAGE = False`.

Orden obligatorio: piloto → HPO → evaluación de HPO en validación 2024 (C9 con
`EVAL_STAGE = 'hpo'`) → congelado de configuración (C8) → confirmación →
evaluación de confirmación en validación 2024 (C9, 144 intentos) → análisis y
selección sobre esa partición (C10) → sensibilidad y su evaluación en validación
2024 (C9, 72 intentos; C10 por variante con `ANALYSIS_CANDIDATE`, `p055` o `p065`)
→ evaluación congelada de confirmación en prueba 2025 (C9, 144 intentos) → análisis
en prueba 2025 (C10, sin selección). `confirm` y `sensitivity` se niegan sin
congelado de configuración. `pipeline select` solo acepta validación 2024, y nada
vuelve de la prueba a la selección. El código no impide abrir la prueba antes de
seleccionar: ese orden lo mantiene quien ejecuta las celdas.

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
