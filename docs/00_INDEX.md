# Índice de documentación — MADRLCitytleranflexresdr

Punto de entrada a la documentación del proyecto. Para el contrato canónico
de dataset/entrenamiento/comparación, ver [`workflow_manifest.json`](workflow_manifest.json).

## Manuales operativos

- `MANUAL_EJECUCION_DESDE_CERO_COLAB_A100.md` — guia para lanzar desde cero
  `CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb` en VS Code + Google
  Colab A100, incluyendo preflight, entrenamiento, monitoreo, reanudacion y
  analisis final.
- `LISTA_EJECUCION_COLAB_A100.md` — checklist corto celda por celda para
  ejecutar el notebook en Colab A100.
- `MANUAL_INSTALACION_DEPENDENCIAS.md` — instalacion de dependencias del
  proyecto en Python 3.9, Windows local y AWS.

## architecture/
Diagramas y documentos de arquitectura del sistema (CityLearn v3 + MADRL),
flujo de trabajo operativo y pipeline de construcción del dataset.

### Documento principal de defensa (nuevo — 2026-06-18)

- **`ARQUITECTURA_PROYECTO_DEFENSA.md`** — documento unificado para
  sustentacion de tesis con 9 diagramas Mermaid:
  - Diagrama 1: Vision general inicio → mejor MADRL
  - Diagrama 2: Pipeline del dataset Iquitos 2023-2025
  - Diagrama 3: Arquitectura Dec-POMDP y CTDE 17 agentes
  - Diagrama 4: Los 4 algoritmos MADRL — taxonomia y diferencias
  - Diagrama 5: Flujo de entrenamiento 12 corridas (4×3)
  - Diagrama 6: Recompensa multiobjetivo por escenario
  - Diagrama 7: Pipeline de evaluacion y seleccion del mejor MADRL
  - Diagrama 8: Infraestructura despliegue local y AWS EC2
  - Diagrama 9: Estructura de capas del software (6 niveles)
  - Tablas de resultados v4 y pruebas estadisticas

### Documentos de arquitectura existentes

- `ARQUITECTURA_CITYLEARN_V3_MADRL.png` / `.pdf`
- `ARQUITECTURA_FLUJO_CITYLEARN_V3_MADRL.pdf`
- `ARQUITECTURA_OPERATIVA_ENTRENAMIENTO_VISIBLE_CITYLEARN_V3_MADRL.md`
- `ARQUITECTURA_Y_FLUJO_TRABAJO_CITYLEARN_V3_MADRL.md`
- **`FLUJO_OPERATIVO_ACTUAL_CITYLEARN_V3_MADRL.md`** — flujo vigente con rutas
  canonicas para flujo local (PS) y AWS Docker
- `FLUJO_TRABAJO_CITYLEARN_V3_MADRL.png`
- `PLANO_INTEGRADO_CITYLEARN_V3_MADRL.pdf` / `.png`
- `PLANO_REAL_IMPLEMENTADO_CITYLEARN_V3_MADRL.pdf` / `.png`
- `dataset_construction_pipeline.md`
- `COOPERACION_COORDINACION_CONTROL_DISTRITAL_MADRL.md`

## audits/
Auditorías técnicas e informes de validación del dataset, dimensionamiento
(DER, EV, edificios) y optimización de entrenamiento.

- `AUDITORIA_TECNICA_SKILL_MADRL_CITYLEARN_V3.md`
- `INFORME_AUDITORIA_DIMENSIONAMIENTO_DER_IQUITOS.md`
- `INFORME_AUDITORIA_DIMENSIONAMIENTO_EV_IQUITOS.md`
- `INFORME_AUDITORIA_PARAMETROS_EDIFICIOS_IQUITOS.md`
- `INFORME_EVALUACION_FINAL_DATASET_IQUITOS_CITYLEARN_V3.md`
- `INFORME_CORRECCION_TRAZABILIDAD_MADRL_V4_2026-06-17.md`
- `INFORME_VALIDACION_DATASET_ENTRENAMIENTO_IQUITOS.md`
- `INFORME_VALIDACION_INTEGRAL_CREACION_DATASET_CITYLEARN_IQUITOS.md`
- `INFORME_OPTIMIZACION_CITYLEARN_MADRL_VRAM.md`
- `DATASET_IQUITOS_DESTILACION_CITYLEARN_V3.md`

## decisions/
Justificaciones de diseño experimental, recompensas multiobjetivo y el plan
de reorganización del proyecto.

- `JUSTIFICACION_DISENO_EXPERIMENTAL_ESCENARIOS_PARALELO.md`
- `JUSTIFICACION_RECOMPENSAS_MULTIOBJETIVO_MADRL.md`
- `ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md` — diagnóstico, plan de
  reorganización (Fases 1-6), modificación de submódulos (Fase 7) y
  despliegue Docker/AWS (Fase 8).
- `REGISTRO_CAMBIOS_REORGANIZACION_Y_POLITICA_PARALELISMO_2026-06-13.md` —
  registro consolidado de la reorganización ejecutada y análisis/decisión
  sobre paralelismo E1/E2/E3 por algoritmo (se mantiene
  `MaxConcurrentScenarioJobs=2`, `MaxConcurrentHeavyJobs=1`, `torch_threads=12`).

## thesis/
Planes de tesis, aportes científicos y resultados preliminares.

- `APORTES_CIENTIFICOS_CITYLEARN_V3_MADRL.docx`
- `APORTES_SIMULACION_CITYLEARN_MADRL_TESIS.md`
- `INFORME_TESIS_MADRL_V1_COMPLETO.docx`
- `PLAN_TESIS_MADRL_CITYLEARN_EVIDENCIA_REAL.docx`
- `PLAN_TESIS_MADRL_CITYLEARN_V3.docx`
- `PLAN_TESIS_MADRL_CITYLEARN_V3_IQUITOS.md`
- `PLAN_TESIS_MADRL_V4_COMPLETO.docx`
- `Resultados_Preliminares-GD-Iquitos_V3 (2).xlsx`

> Nota: existen 4 versiones de "PLAN_TESIS_*" (V3, V3_IQUITOS, EVIDENCIA_REAL,
> V4_COMPLETO). Pendiente de consolidación — ver Fase 2 en
> `decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md`.

## contributions/
Documentación de modificaciones a submódulos (CityLearn + 9 de `external/`)
como aportes de investigación, con justificación bibliográfica
(tesis doctorales/maestría y artículos 2021-2026). Cada subcarpeta contiene
`CHANGES.md` y `bibliografia.bib`. Ver Fase 7 en
`decisions/ORGANIZACION_PROYECTO_DIAGNOSTICO_Y_PROPUESTA.md`.
