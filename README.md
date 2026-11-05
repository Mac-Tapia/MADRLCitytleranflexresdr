# CityLearn v3 MADRL para comunidades inteligentes

Proyecto de coordinación de flexibilidad energética, emisiones de CO2 y costo energético en 17 edificios de Iquitos mediante HAPPO, MASAC, MATD3 y MAAC.

CityLearn aporta el simulador base y el fork incorpora la capa experimental v3; no son dos instalaciones separadas. El núcleo propio mantiene un monolito modular con dominio, casos de uso, puertos, adaptadores y una CLI nativa. Colab es cliente de esa CLI.

## Estado vigente

La implementación y sus verificaciones actuales se registran en [el informe de ejecución integrada](docs/audits/ejecucion_remediacion_20261101/informe.md). El plan y los dictámenes originales preservan sus cortes documentales anteriores.

Corte documental: 2026-11-01. La implementación está en remediación. **No se acredita una campaña nueva científicamente completa, un modelo ganador ni operación física.** Los resultados históricos retirados no son evidencia de la campaña nueva.

El propietario decidió conservar el contrato **v1** y documentar sus diferencias con el PT. La fuente metodológica vigente es el [registro de contrato v1](docs/decisions/contrato_v1_pt.md), junto con la configuración ejecutable. Las medidas del adaptador, los controles activos y las variantes de acciones por backend deben declararse: no hay equivalencia automática de capacidad entre los cuatro métodos.

- [Plan integrado y criterios de cierre](docs/plans/remediacion_integrada.md).
- [Auditoría de arquitectura y correspondencia con PT](docs/audits/architecture_thesis_20261101/informe.md).
- [Integración de los dos informes del Revisor A](docs/audits/integracion_auditorias_20261101/README.md).
- [Estado de las especificaciones](specs/STATUS.md): distinguir antecedentes de evidencia nueva, y contratos de aceptación nativa/científica.

La lectura mecánica del árbol no equivale a revisión semántica de cada archivo. Las pruebas focales y sus JUnit se conservan por tarea; no sustituyen una suite integral estable, el ensayo real de Colab ni las etapas experimentales pendientes.

## Contrato experimental

La campaña se declara en [iquitos.yaml](configs/experiments/iquitos.yaml), con dataset `data/campaigns/iquitos_v5`, splits `train_2023`, `validation_2024`, `test_2025` y normalizador ajustado en entrenamiento. Las prioridades E1/E2/E3 proceden exclusivamente de [objective_policies.yaml](configs/objective_policies.yaml); son compensatorias. La tarifa de [scenarios.yaml](configs/scenarios.yaml) es media plana, por lo que no se anuncian resultados de arbitraje TOU.

La formulación distingue estado latente, observación local, información del crítico, distribución inicial, acciones físicas y decodificación específica de backend. El pago común corresponde al perfil v7; la representación discreta de MASAC/MAAC restringe combinaciones frente a los actores continuos. Las diferencias con el PT, el backcast de B01 y los límites de interpretación quedan explícitos en el contrato.

HPO selecciona en validación. La unidad de réplica estadística es la semilla de entrenamiento independiente; horas, edificios, episodios y KPI no añaden réplicas. La selección descriptiva y el ganador inferencial son estados distintos; un estudio completo puede no detectar diferencias.

## Árbol por responsabilidad

| Ruta | Responsabilidad |
|---|---|
| `uc3m/domain/` | Identidades, objetivos y contratos puros |
| `uc3m/application/` | Campaña, integridad, evaluación, análisis, evidencia y entrega |
| `uc3m/adapters/` | Integración CityLearn, backends nativos y políticas congeladas |
| `configs/` | Dataset, escenarios, algoritmos, presupuesto y KPI |
| `tests/` | Contratos, integración, perfil fresh y comprobaciones nativas |
| `tools/` | Herramientas de dataset, auditoría, tesis y clientes Colab |
| `scripts/` | Guardas y puntos de entrada de mantenimiento/calidad |
| `governance/` | Layout, nombres, licencias y políticas de artefactos |
| `docs/` y `specs/` | Diseño, decisiones, trazabilidad y evidencia documental |
| `CityLearn/` y `external/` | Dependencias protegidas; cambios requieren encargo explícito |

Los inventarios completos y sus fronteras están en la auditoría. Carpetas vacías, igualdad de bytes o ausencia de una referencia textual no autorizan eliminar datos, scripts manuales, evidencia o dependencias.

## Flujo de trabajo

Desde la raíz verificada y con el entorno canónico existente:

```powershell
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1
.\.venv39-citylearn-v3\Scripts\python.exe -B -m uc3m.application.training.cli --config configs/experiments/iquitos.yaml --stage prepare
```

Preparar produce un DAG y manifiestos; no entrena. Una campaña preparada nunca se sobrescribe. Cambiar fuentes, datos o protocolo exige identidad y verificación coherentes. `resource_authorization.authorized_stages` permanece vacío hasta autorización expresa de etapas y recursos; el presupuesto preparado no es trabajo ejecutado.

El cliente es [el cuaderno Colab modular](examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb), generado por `tools/colab/build_modular_colab_notebook.py`. El [runbook](docs/architecture/runbook.md) detalla las etapas; su aceptación de desconexión/restauración real sigue separada de las pruebas locales.

Después del entrenamiento autorizado, `python -m uc3m.application.pipeline` ofrece `status`, `freeze`, `evaluate`, `analyze` y `deliver` con manifiesto explícito. Evaluación fallida o rechazo devuelve salida no cero. La entrega recibe `--gate-report` y `--analysis-manifest`; conserva análisis y hashes, y declara el alcance de sus archivos. Un paquete de metadatos no equivale a exportación ONNX ni a control de planta.

## Validación

```powershell
.\.venv39-citylearn-v3\Scripts\python.exe -B tools/skills/validate_skills.py
.\.venv39-citylearn-v3\Scripts\python.exe -B -m pytest tests/contract/test_spec_kit_consistency.py -q -p no:cacheprovider
powershell -ExecutionPolicy Bypass -File scripts/quality/run_fresh_training_gates.ps1 -CampaignManifest outputs/campaigns/iquitos_v5/campaign_manifest.json
```

La última orden ejecuta el perfil fresh completo, incluidos microaprendizajes nativos; usarla sobre un corte estable y con sus dependencias reales. El reporte vincula campaña, especificación, commit, código, pruebas y JUnit. Una omisión, alteración o evidencia incompleta impide promover. La aceptación científica exige además cobertura y análisis verificables de la campaña; los contratos sintéticos son pruebas del verificador.

El entrenamiento nativo requiere checkout fijado y dependencias locales declaradas. Los namespaces genéricos de los backends se resuelven en su contexto de importación; no deben instalarse paquetes homónimos de PyPI. La instalación del wheel del núcleo y la aceptación nativa se verifican por separado. Python 3.9 conserva la compatibilidad heredada; su fin de soporte y la migración pendiente se documentan en el plan, sin actualización silenciosa del entorno.

## Tesis, historia y fuentes

- [PT_TAPIA_ZAMBRANO original](PT_TAPIA_ZAMBRANO_v6_Iquitos_2.docx).
- [Documento de tesis conservado](docs/tesis.docx).
- [Diseño del entrenamiento](docs/design/entrenamiento.md).
- [Observaciones del jurado](data/audits/jury_observations_manifest.json).
- [Política de componentes y licencias](governance/open_source_policy.yaml).
- [README anterior preservado literalmente](docs/history/README_pre_integracion_20261101.txt): antecedente con resultados retirados y rutas históricas; no instrucción operativa ni evidencia vigente.

La metodología se fundamenta en la [tesis de maestría de Costea](https://webthesis.biblio.polito.it/40396/), la [tesis doctoral de Charbonnier](https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5) y los criterios de [reproducibilidad de Pineau et al.](https://www.jmlr.org/papers/v22/20-303.html). Estas fuentes no certifican este repositorio, los coeficientes exactos o un supuesto ganador; la matriz bibliográfica y sus límites están en el plan integrado.
