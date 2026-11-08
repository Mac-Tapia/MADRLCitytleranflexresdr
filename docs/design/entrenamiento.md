> **Resultados históricos retirados (propietario, 2026-11-01).** Las cifras inferenciales de este documento (p-valores, ganadores, rankings) vienen de corridas anteriores que ya no cuentan. La única fuente válida de cifras estadísticas será `tools/eval/build_campaign_statistical_report.py` sobre la campaña nueva (SPEC-009, módulo 4); hasta entonces no se citan.

# Nueva campaña MADRL desde cero: diseño y contrato científico

Fecha: 2026-11-01, America/Lima. Estado: diseño para implementación; no implementado ni entrenado.

## 1. Mandato y frontera

Solicitud del usuario: preparar una implementación para un nuevo entrenamiento, sin usar datos del entrenamiento anterior ni resultados históricos, lista para otro agente.

La campaña nueva no admite checkpoints, replay, optimizadores, normalizadores ajustados, curvas, KPI, tablas, rankings, selecciones, baselines ni resúmenes de campañas anteriores. Tampoco admite esos archivos como fixtures de aceptación. Por instrucción posterior del usuario, el agente implementador debe limpiar y eliminar los históricos locales de la lista cerrada R-01..R-07 de `docs/audits/historicos.md`, después de inventariar, documentar las causas y desacoplar consumidores. Esa tarea puede leerlos para diagnóstico/retiro, nunca como insumo científico nuevo. Este mandato sustituye la preservación inicial de históricos; no incluye Word, fuentes primarias ni dependencias.

Se pueden reutilizar código y fuentes primarias independientes del entrenamiento, previa auditoría de origen. Esto no autoriza copiar el dataset horario generado anterior: se construirá una versión nueva desde inventario, facturación identificada como fuente y nuevas descargas meteorológicas con procedencia. Una factura sintética generada por el proyecto no es fuente primaria. Si una entrada no tiene origen verificable, se etiqueta como modelada o se bloquea; no se convierte en medición.

Raíz única: `D:/MADRLCitytleranflexresdr`. Remoto esperado: `https://github.com/Mac-Tapia/MADRLCitytleranflexresdr.git`. Ejecutar `powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1` antes de cada edición u operación Git. No acceder al proyecto excluido por AGENTS.md. Preservar parches concurrentes. No hacer stage global, commit automático ni push por ejecutar este plan.

`CityLearn/` y `external/` son dependencias de solo lectura. La implementación se realiza mediante módulos del repositorio principal; no se modifica ni se copia un entrenador completo de dependencia. Si un contrato no puede satisfacerse con sus interfaces existentes, registrar `blocked_dependency_interface`, la interfaz faltante y una propuesta mínima; no introducir un parche oculto o un fallback aleatorio. Cambiar una dependencia requeriría autorización explícita adicional del usuario.

## 2. Decisiones de arquitectura

Se mantiene el monolito modular Python y los cuatro backends nativos. Una entrada de campaña nueva orquesta preparación, entrenamiento, evaluación y aceptación mediante contratos tipados. Las librerías científicas y los formatos nativos permanecen detrás de adaptadores; los casos de uso no importan directamente runners externos.

Alternativas consideradas por el redactor:

1. Reanudar o reparar campañas previas: descartado por instrucción del usuario.
2. Reescribir algoritmos o modificar submódulos: descartado por alcance, riesgo y frontera de AGENTS.md.
3. Adaptadores del padre, datos regenerados y ejecuciones nuevas: enfoque adoptado para este plan.

Estas decisiones son propuestas concretas del plan, no una afirmación de aprobación de nuevos gastos o de resultados futuros.

Flujo obligatorio (el retiro no es un experimento):

`inventario/diagnóstico histórico -> aislamiento y retiro validado -> fuentes primarias -> dataset nuevo -> splits -> protocolo congelado -> piloto/HPO nuevo -> configuración congelada -> campaña confirmatoria -> evaluación congelada -> estadística -> evidencia nueva`.

Cada artefacto tiene `campaign_id`, fase, intento, hashes de entradas, productor y estado. Ningún lector busca la carpeta más reciente ni usa un puntero global. Los consumidores reciben explícitamente el manifiesto de campaña.

## 3. Protocolo propuesto

| Campo | Valor inicial de este diseño |
|---|---|
| Campaña | `fresh_iquitos_20261101_v1`; si el directorio ya existe, fallar y pedir un identificador nuevo |
| Algoritmos | HAPPO, MASAC, MATD3, MAAC |
| Escenarios | E1, E2, E3; únicamente los tres ejes experimentales |
| Edificios | 17, con calidad de procedencia por edificio/variable |
| Entrenamiento | 2023: 8760 pasos por episodio, 50 episodios por tratamiento confirmatorio |
| Validación | 2024: 8784 pasos; selección, sin actualización de política |
| Prueba | 2025: 8760 pasos; acceso solo después de congelar modelos y decisiones |
| Semillas de desarrollo/HPO | 901, 902, 903 |
| Semillas confirmatorias | 1001 a 1012 inclusive, 12 entrenamientos independientes por algoritmo/escenario |
| Número confirmatorio | 4 × 3 × 12 = 144 entrenamientos; 7200 episodios; 63 072 000 pasos de entrenamiento |
| Reanudación | Deshabilitada en esta versión; todos los intentos nuevos usan `--no-resume` |
| Reinicio tras interrupción | Nuevo `attempt_id`, mismo tratamiento y semilla, estado inicial nuevo; nunca sumar episodios entre intentos |
| Aleatoriedad | Semillas separadas para inicialización, exploración, demanda/EV y evaluación; registrar la derivación |
| Presupuesto | Medir recursos y tiempo por piloto; no inventar duración ni costo de la campaña |
| Destino | Ruta local autorizada; Colab opcional con la misma identidad y controles, sin contratar recursos |

Cincuenta episodios y doce semillas son decisiones iniciales del proyecto, no mínimos universales prescritos por la literatura. El piloto puede justificar una enmienda de presupuesto antes de abrir prueba, versionando el protocolo. No reducir semillas silenciosamente ni llamar completa una campaña parcial. Las semillas distintas no convierten un único distrito/clima modelado en validación externa geográfica.

## 4. Dataset nuevo y separación temporal

Destino: `data/campaigns/{storage_alias}/`. Contiene `raw/`, `dataset/`, `splits/`, `provenance.json`, `quality_flags.parquet`, `split_manifest.json`, `dataset_acceptance.json`. Resultados: `outputs/campaigns/{storage_alias}/`. Ninguno es un alias o enlace a outputs previos. Los generadores, configuraciones y manifiestos de procedencia se conservan como entregables; no basta con datos ignorados sin generador.

Fuentes de partida permitidas: inventario y facturas originales verificadas de `CityLearn/data/buildingcsv/`, en solo lectura, más nuevas descargas meteorológicas de fuentes documentadas. Antes de copiar una entrada, comprobar si es primaria o derivada. No leer `outputs/dataset_cache` ni reutilizar series horarias, pronósticos o auditorías de entrenamiento anteriores como entrada nueva.

Reglas:

- Índice horario timezone-aware `America/Lima`, sin duplicados ni huecos; 26304 horas y 2024 bisiesto. Crear splits físicos autocontenidos de 8760/8784/8760 filas, cada uno con `schema.json` relativo y sin referencias fuera de su directorio.
- El motor de construcción acepta `output_dir` y todas sus entradas explícitamente. No ejecutar un generador que sobrescriba el dataset dentro de CityLearn. Factorizar lógica del padre; evitar copias completas de scripts y constantes duplicadas.
- La desagregación conserva balances mensuales y punta/fuera de punta. Su cierre no acredita que la forma horaria sea una medición: registrar método, parámetros, incertidumbre y calidad.
- B01 permanece como perfil modelado si no se acredita una fuente primaria. No usar una factura reconstruida desde un perfil para validar ese mismo perfil. Para B06, ajustar reconstrucción solo con información del split de entrenamiento, sin 2024/2025; registrar los meses modelados. Añadir evaluación de sensibilidad excluyendo edificios con carga modelada, manteniendo explícito el cambio de población.
- Permitir construir la verdad exógena del conjunto retenido desde sus fuentes observadas, pero no emplearla para ajustar parámetros de generación, normalización, selección o predicción del entrenamiento. Cada transformación declara `fit_scope` y `available_at`.
- Principal: desactivar todas las columnas `*_predicted_*` en observaciones. No basta con dejar de usar el generador: comprobar el contrato efectivo observado por cada actor. Pronóstico perfecto solo puede ser un experimento separado etiquetado `oracle`, fuera de aceptación principal.
- Normalización: ajustar en 2023 o usar límites físicos documentados; congelar y aplicar sin refit a 2024/2025. No heredar min/max calculados sobre los tres años por el simulador sin controlar su alcance. Registrar extrapolaciones fuera de rango sin esconderlas.
- No repetir un año meteorológico típico como si fueran tres años observados. Descargar años específicos o etiquetar el experimento como clima modelado y bloquear afirmaciones interanuales observadas.
- PV, BESS, EV y máquinas tienen método de dimensionamiento, procedencia y bandera measured/modeled. No presentar sesiones EV simuladas como mediciones.
- Precio: una misma señal tarifaria exógena para E1/E2/E3. Moneda contractual `USD`, con fuente monetaria y conversión documentadas si aplica. No relabelar EUR o PEN como USD. No estimar tarifas retenidas con facturación que no estuviera disponible al momento de decisión.
- CO2: documentar factor, fecha, unidad y método horario; si es modelado, reportarlo y someterlo a sensibilidad. No afirmar medición horaria de emisiones.
- Invalidar aceptación si cambia cualquier CSV, fuente, script de generación, configuración o transformación respecto de los hashes congelados.

## 5. Pesos e hiperparámetros sin selección histórica

Usar como hipótesis inicial de preferencia la configuración actual del código, no una selección basada en desempeño previo. Orden `[flexibilidad, CO2, costo]`: E1 `[0.60,0.15,0.25]`, E2 `[0.25,0.60,0.15]`, E3 `[0.15,0.25,0.60]`. Es suma compensatoria, no lexicográfica. Una sola fuente serializada alimenta entrenamiento, manifiestos y análisis; una proyección de dominio puede validarla, pero no mantener otra tabla numérica independiente.

No variar simultáneamente tarifa, activos, servicio EV o población al cambiar E1/E2/E3: el estudio principal es `weights_only`. Separar penalizaciones/condiciones EV-BESS del vector de tres objetivos y registrar cada término antes/después de normalizar, mezclar equipo y escalar.

HPO nuevo, igual presupuesto por algoritmo: grilla `learning_rate=[0.0001,0.0003] × hidden_dimension=[128,256] × gamma=[0.99,0.9999]`, ocho configuraciones. Evaluar las tres políticas y las tres semillas de desarrollo, diez episodios de 8760 pasos por configuración/tratamiento: 288 entrenamientos, 25 228 800 pasos. La grilla es decisión del plan, no un óptimo científico supuesto. No usar métricas históricas para ordenar o podar candidatos.

Mapeo explícito: HAPPO actor/critic lr iguales al candidato y `hidden-size`; MASAC actor/critic lr y `rnn-hidden-dim`; MATD3 `lr` y `hidden-size`; MAAC `pi-lr`, `q-lr`, `hidden-size`. MASAC conserva su arquitectura nativa de mezcla; no afirmar igualdad de número de parámetros. Congelar antes del piloto el resto de defaults nativos y serializarlos en `resolved_backend_config.json`, incluidos replay/unidad, warmup, epochs, batch/unidad, tau, clipping, entropía, acción discreta y reward scale. Cada clave declarada debe llegar al backend o producir error; no ignorar claves desconocidas.

Elegir configuración por factibilidad en validación, después media de ganancias normalizadas de los tres ejes contra RBC recién ejecutado; pesos de selección iguales a 1/3, no los pesos de entrenamiento. Desempate: menor varianza entre semillas de desarrollo y después identificador de configuración lexicográfico. Si todas son inviables, declarar bloqueo, no promover la menos mala. Congelar una configuración por algoritmo, común a E1/E2/E3, y no ajustarla con prueba.

Sensibilidad de pesos: dominancia `p=[0.55,0.60,0.65]`; repartir resto en razón secundario:residual 5:3 y conservar las posiciones cíclicas. Para p=0.55: secundario=0.28125/residual=0.16875; para p=0.65: 0.21875/0.13125. Comparar con las semillas confirmatorias 1001/1002/1003 y mismos flujos exógenos. El centro usa únicamente las nuevas corridas confirmatorias; extremos requieren 72 entrenamientos adicionales de 50 episodios, 31 536 000 pasos. No reutilizar el antiguo diseño de miles de corridas por defecto.

Total planificado entrenamiento HPO + confirmación + extremos: 119 836 800 pasos; evaluaciones, baselines, smokes y robustez se presupuestan aparte. El comando `prepare` estima todo el DAG sin ejecutar entrenamiento. Un recurso insuficiente bloquea la ejecución, no modifica silenciosamente el experimento.

## 6. Evidencia de aprendizaje e inferencia

Un smoke de ocho pasos solo verifica conectividad. La puerta de aprendizaje exige, para cada backend real, un microentrenamiento nuevo suficientemente largo para superar warmup y realizar actualizaciones: pasos reales, contador de actualizaciones exitosas, parámetros iniciales/finales diferentes, tensores finitos y checkpoint nativo recargable. La duración deriva de su warmup/batch resueltos y se registra; no fijar ocho pasos como aprendizaje.

La instrumentación pertenece al padre y observa los optimizadores entregados a los guards nativos existentes, incluyendo la ruta HARL. Debe preservar su semántica y eliminarse al terminar el proceso. Si no puede observar una actualización real, falla la puerta; no inferirla del código de retorno. No modificar algoritmos para satisfacer la prueba.

La confirmación usa checkpoint final del episodio 50, con política de elección fijada antes de prueba. El HPO elige configuración, no un checkpoint ganador retrospectivo. Evaluación en procesos separados, sin `backward`, `optimizer.step`, exploración de entrenamiento ni incorporación al replay. `act(..., deterministic=True)` debe ejecutar la política cargada, conservar estado recurrente y resetearlo por episodio. Comparar acciones antes/después de recarga. Mantener el orden, dimensiones heterogéneas, normalizador, discretizador y mapeo a acción física del entrenamiento.

Baselines nuevos: RBC fijo reproducible y control de referencia sin optimización de almacenamiento, con los mismos edificios, cargas, EV/servicios, clima, tarifa, estado inicial y ventana temporal. No quitar EV al baseline. Registrar inventario de energía inicial/final y cambio de energía almacenada, además de pérdidas, para no confundir agotamiento terminal con eficiencia. Evaluaciones pareadas comparten la realización exógena correspondiente a la semilla, no pesos de modelo.

## 7. Contrato de KPI

La fuente canónica nueva es la traza física/económica del simulador, no el escalar ya agregado en `results.json` ni el evaluador UC3M estimado. Guardar trazas por paso/edificio y agregados por edificio/distrito. Prohibir inferir un total promediando un total y un promedio diario.

Cada definición declara fórmula, unidad, sentido, nivel, baseline, ventana, provenance y condición de disponibilidad. Ausente no equivale a cero. Rechazar bool, NaN, Inf y duplicados no declarados. Las métricas no disponibles se reportan con causa; la ausencia de una primaria bloquea aceptación.

| Eje | Primarias confirmatorias | Diagnósticos y propuestas del proyecto |
|---|---|---|
| E1 | Promedio diario de pico distrital kW; ramping medio absoluto kW/h; promedio diario de `1-load_factor` | Importación/exportación kWh, autoconsumo temporal, rampa p95, energía desplazada y rebote bajo una definición conservativa documentada |
| E2 | CO2 operativo total kgCO2 | Delta absoluto/relativo, intensidad por energía servida, sensibilidad del factor de emisión |
| E3 | Costo energético total USD | Delta absoluto/relativo, componente de degradación separado y no supuesto como factura, sensibilidad tarifaria |
| Restricciones | Violaciones físicas y servicio EV | Frecuencia, duración, magnitud, energía no servida, déficit SOC y capacidad perdida modelada |

El pico distrital se calcula después de sumar las potencias coincidentes de los edificios. Para delta: `control - baseline`; para ganancia en objetivos a minimizar: `(baseline-control)/abs(baseline)`, con baseline cero marcado no definido. El agregado de E1 es media de las tres ganancias primarias; no incluir totales y ratios duplicados como réplicas estadísticas. Confort se mide por tiempo/ocupación fuera de banda, no por suma de grados. Resiliencia solo se calcula con cortes explícitos. Throughput/ciclos son exposición y desgaste, no beneficios universales.

Tolerancias de ingeniería del plan: balances `atol=1e-6 + rtol=1e-6 × magnitud`; energía mensual de desagregación error relativo <=0.01%; SOC/potencia dentro de límites del schema con tolerancia 1e-6. Servicio EV: reportar todos los eventos y su alcanzabilidad física; criterio inicial de selección >=95% de salidas alcanzables con déficit SOC <=0.05. Estas tolerancias son criterios del proyecto sujetos a justificación previa, no valores normativos atribuidos a artículos. Si hay eventos físicamente inalcanzables, mostrar su cantidad y causa, sin excluirlos silenciosamente del reporte total.

KPI nuevos se evalúan como diagnósticos antes de usarlos como endpoints confirmatorios. No declarar validación ASHRAE, IEEE o económica sin demostrar que se cumplen las entradas y el procedimiento correspondiente.

## 8. Estadística y selección

Unidad de réplica: entrenamiento independiente por semilla. Calcular primero un resultado por semilla/algoritmo/escenario. No usar horas, edificios, episodios ni distintos KPI como aumento del número de semillas.

Publicar por endpoint mediana, media, desviación, IQM con pesos fraccionales de cuantiles e IC bootstrap por bloques de semillas (10000 remuestreos, semilla 7001). Los tres endpoints de eje son ganancia E1 agregada de sus tres primarias, ganancia de CO2 total E2 y ganancia de costo total E3. Comparaciones pareadas solo si el emparejamiento por realización exógena está acreditado. Friedman con bloques de semilla para >=3 algoritmos; Holm para la familia de sus tres contrastes de eje. Post hoc Wilcoxon pareado con Holm sobre la familia fija de 18 comparaciones (6 pares ×3 ejes); interpretar confirmatoriamente un par solo si su omnibus corregido también es significativo, sin reducir la familia después de observar resultados. El impacto vs RBC constituye otra familia de 12 contrastes (4 algoritmos ×3 ejes) con Holm separado. No exigir mejora contra baseline para decidir una hipótesis que solo habla de diferencias entre algoritmos. No prometer potencia con n=12.

TOPSIS e hipervolumen son descriptivos de decisión. Sus tres coordenadas son las ganancias por eje definidas arriba, todas orientadas a maximizar. Para hipervolumen usar transformación fija `clip(gain, -1, 1)` y referencia común `[-1,-1,-1]`; reportar saturaciones y conservar ganancias originales, sin cambiar la referencia al observar prueba. Para TOPSIS congelar en validación los factores de escala y pesos iguales a 1/3; documentar ideal/antiideal y no reajustar su escala con prueba. Guardar esos valores, no recalcular una referencia por algoritmo. No promover un ganador universal si los resultados son inciertos, inviables o no distinguibles. Una campaña científicamente aceptable puede producir resultados negativos o ausencia de diferencias.

La prueba de 2025 puede ejecutarse para todos los modelos finales una vez congelados para informar el benchmark. La elección del paquete candidato se hace con validación; no se retroalimenta desde prueba. Si se formula después una nueva hipótesis o se reajusta, debe tratarse como nuevo estudio con otra reserva de evaluación.

## 9. Seguridad, aceptación y estados

Validar contención de rutas resueltas y rechazar enlaces que conduzcan fuera de la raíz de campaña o hacia resultados previos. Hashes antes de deserializar checkpoints creados por esta campaña. No aceptar pickle remoto, rutas arbitrarias desde HTTP ni contenido no confiable como código. Excluir secretos y datos personales de snapshot/logs.

Panel solo loopback y lectura; no usar API demo/Modbus/MQTT para controlar equipos. Fallback aleatorio o ausencia de modelo devuelve fallo de readiness y bloquea inferencia aceptada. La implementación no despliega infraestructura ni convierte la demo en producción. La prueba de permisos consiste en comprobar estos límites, no en efectuar un ataque remoto.

Estados nuevos, separados: `planned`, `repository_layout_verified`, `dataset_verified`, `implementation_verified`, `learning_verified`, `training_complete`, `evaluation_complete`, `scientific_acceptance`. Código de retorno cero no implica el siguiente estado. Aceptación final exige las 144 corridas confirmatorias, pruebas sin omisiones, evaluación retenida, sensibilidad predefinida, trazabilidad y reportes completos. Ausencia de significancia no bloquea aceptación; ausencia de evidencia sí. La estructura de carpetas y la unicidad de fuentes de §12 son puertas reales, no una ilustración ni una declaración de limpieza sin inventario.

No cerrar automáticamente las 17 observaciones antiguas del jurado. Una matriz nueva registra qué requisitos de esta campaña se verificaron y cuáles siguen fuera de alcance. Mantener `scientific_acceptance=false` hasta la última puerta. No editar Word canónicos en este encargo; producir datos, figuras y un paquete de evidencia nuevos para una revisión documental posterior.

La causa registrada para HAPPO que debe prevenirse es `NameError: name 'VecEnvWrapper' is not defined` en un resultado `completed_with_salvage`, junto con cobertura/tramo reanudado ambiguos. El código de dependencia actual ya tiene compatibilidad para ese nombre; no se afirma que el bug permanezca. Exigir regresión nativa de vectorización, aprendizaje, reporte, guardado, recarga y cierre, y registrar error por fase. El traceback disponible no permite atribuir la fase histórica exacta ni concluir OOM o fallo de convergencia. El anexo de diagnóstico vincula H-01..H-12 a pruebas nuevas antes de retirar sus archivos fuente.

## 10. Sustento científico y límites

Fuentes primarias buscadas/contrastadas el 2026-11-01; tesis verificadas por ficha institucional. Se consultan ficha/resumen y texto editorial accesible, no se afirma revisión integral de todas las tesis. La ficha editorial de JBPS declara Scopus; no se certifica aquí el registro individual en cada base de todos los artículos. Una tesis no se etiqueta como artículo indexado.

| Fuente | Tipo y acceso | Apoya | No establece |
|---|---|---|---|
| Costea, C. C. (2026). *Multi-Agent Reinforcement Learning Building Energy Optimization: Taxonomy and Experimental Evaluation in CityLearn*. Politecnico di Torino. https://webthesis.biblio.polito.it/40396/ | Maestría; ficha/resumen público; PDF CC BY-NC-ND según ficha | Baselines/RBC y separación edificio/distrito | Nuestros pesos, semillas, superioridad o licencia de código |
| Charbonnier, F. (2023). *Multi-agent reinforcement learning for the coordination of residential energy flexibility*. University of Oxford. https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5 ; DOI 10.5287/ora-ovzyxredj | Doctorado DPhil; ficha y documento ORA; términos ORA | Coordinación, restricciones, escalabilidad y compromisos energéticos | Transferencia demostrada a Iquitos o coeficientes exactos |
| Nweye et al. (2025; publicación anticipada 2024). *CityLearn v2: energy-flexible, resilient, occupant-centric, and carbon-aware management of grid-interactive communities*. Journal of Building Performance Simulation, 18(1), 17–38. https://doi.org/10.1080/19401493.2024.2418813 | Artículo; editorial/resumen accesible; comprobar licencia del texto antes de redistribuir | Simulación, observación/acción, control y evaluación de edificios | Que el fork local o nuevas métricas ya estén validados |
| Patterson, A., Neumann, S., White, M., & White, A. (2024). *Empirical Design in Reinforcement Learning*. JMLR, 25(318), 1–63. https://jmlr.org/papers/v25/23-0183.html | Artículo; acceso público JMLR | Diseño empírico, selección y evaluación rigurosa | Potencia automática con doce semillas |
| Pineau et al. (2021). *Improving reproducibility in machine learning research*. JMLR, 22(164), 1–20. https://www.jmlr.org/papers/v22/20-303.html | Artículo; acceso público JMLR | Procedencia, código/datos/procedimientos reproducibles | Corrección por mera existencia de manifiestos |

Indexación editorial JBPS: https://www.tandfonline.com/action/journalInformation?journalCode=tbps20&show=aimsScope . Los valores exactos y la arquitectura concreta de este diseño son decisiones del proyecto con pruebas y análisis de sensibilidad, no prescripciones de estas fuentes.

## 11. Tipos y manifiestos públicos mínimos para el implementador

Usar dataclasses/TypedDict validados, tipado estándar en dominio y serialización JSON con `schema_version=1`. No hace falta una librería de modelos nueva. Los hashes son SHA-256 completos; las rutas serializadas son relativas a la raíz declarada. Los campos indicados son obligatorios salvo donde diga optional.

| Módulo propietario | Tipos públicos y contenido mínimo |
|---|---|
| `tools/ops/historical_inventory.py` | `RetirementPlan`: project_root, allowlist_ids, targets con resolved_path/files/hash/bytes/Git state, protected_paths, consumers, diagnostic_records y plan_hash. `RetirementResult`: plan_hash, targets con estado/razón/hora, protected_paths_verified y historical_retirement_complete. Solo mantenimiento, no input de entrenamiento. |
| `uc3m/domain/campaigns.py` | `CampaignSpec`: campaign_id, algorithms, scenarios, development_seeds, confirmatory_seeds, stage_budgets, split_ids, policy_hash, resource_authorization. `CampaignManifest`: spec, spec_hash, source_hash, data_manifest_path, artifact_root, stage_manifests, status. `AttemptIdentity`: treatment_id, attempt_id, seed, initial_episode=0, fresh_start=true. `ConfigurationFreeze`: campaign_id, algorithm, config_hash, validation_manifest_hashes, selection_rule, frozen_at. |
| `uc3m/application/dataset/provenance.py` | `RawSourceManifest`: sources con path/hash/source_uri/obtained_at/source_type y measured/modeled, available_at, license_or_access_note, approved_role; ninguna fuente de tipo training_artifact. |
| `uc3m/application/dataset/construction.py` | `DatasetBuildConfig`: sources, dimensions, time_index, sizing, generation_seeds, fit_scope y currency. `DatasetBuildManifest`: campaign_id, source_hashes, generator_hash, config_hash, files, quality_flags_path, balance_checks, limitations. |
| `uc3m/application/dataset/splits.py` | `SplitManifest`: campaign_id, train/validation/test con schema_path/start/end/rows/hash, fit_dependencies. `NormalizerSpec`: feature_order_by_agent, transformations, train_fit_hash, bounds, units y out_of_range_policy. |
| `uc3m/adapters/citylearn/fresh_observations.py` | `ObservationActionContract`: algorithm, agent_order, feature_order/dimensions, padding, time_encoding, normalizer_hash, action_bounds, action_table_hash optional y discretizer_config. |
| `uc3m/adapters/algorithms/evidence.py` | `VerifiedCheckpointBundle`: campaign_id, treatment_id, attempt_id, algorithm, files con path/hash, completed_episode y observation_action_contract_hash. Solo se construye tras verificar origen/contenido. |
| `uc3m/adapters/algorithms/learning_observer.py` | `LearningObserver`: finalize(). `LearningEvidence`: campaign_id, attempt_id, env_steps, successful_optimizer_updates_by_owner, initial_parameter_hashes, final_parameter_hashes, nonfinite_events, checkpoint_bundle_hash, verified. |
| `uc3m/application/evaluation/kpi_contract.py` | `PhysicalTrace`: timestamps, seconds_per_step, building_ids, series_by_building, units, currency y exogenous_hash. `KpiCatalog`: definitions y primary_endpoints. `KpiReport`: campaign/seed/split/algorithm/scenario, values con unidad/nivel/disponibilidad/causa, baselines y trace_hash. `ValidationResult`: passed, checks, reasons. |
| `uc3m/application/evaluation/frozen_evaluation.py` | `EvaluationManifest`: campaign/treatment/checkpoint/split hashes, exogenous_seed, training_updates=0, trace_paths, kpi_report_path y completed_steps. |
| `uc3m/application/training/fresh_campaign.py` | `StageResult`: campaign_id, stage, planned_treatments, completed_treatments, failed_attempts, manifest_path, status, reasons. |
| `uc3m/application/evaluation/fresh_analysis.py` | `SeedTable`: filas únicas por campaign/algorithm/scenario/seed/split/endpoint; incluye valor y hashes. `ScientificReport`: coverage, seed_statistics, test_families, intervals, decisions, limitations. `CandidateDecision`: status, candidate optional, validation_rule, evidence_hashes. |
| `uc3m/application/training/completion.py` | `AcceptanceReport`: campaign_id, level, checks, missing_requirements, evidence_hashes, passed; level diferencia software/aprendizaje/campaña/ciencia. |
| `tools/eval/report_fresh_campaign.py` | `DeliveryManifest`: campaign_id, acceptance_report_hash, files con hash/role, limitations, generated_at y candidate_status. |

Los resultados nativos intermedios que usen agregadores defectuosos son diagnósticos no canónicos: no alimentan ni completitud científica, ni HPO, ni selección, ni tablas entregadas. El padre genera un `fresh_kpi_report.json` validado desde trazas para la evidencia nueva. Si la traza requerida no se puede obtener con las interfaces de solo lectura, esa métrica y su puerta quedan bloqueadas; no reconstruirla a partir del escalar defectuoso.

## 12. Árbol desplegado y un único archivo canónico por responsabilidad

Nueva instrucción del usuario: incluir revisión del árbol de carpetas y eliminación de duplicados, conservando el archivo más completo. Se interpreta operativamente como una única implementación/fuente vigente por identidad lógica de archivo; no como un único archivo para todo el proyecto. Dos `app.py` de servicios distintos o dos `__init__.py` de paquetes distintos no son versiones del mismo programa.

La tarea T12 debe comprobar árbol real, contenido, consumidores y cobertura. No basta presentar el árbol de abajo. Materializar directorios solo junto a archivos funcionales requeridos; no crear carpetas vacías para aparentar implementación. Las ramas de datos/resultados se materializan por fase, sin fabricar outputs, checkpoints o estados de experimentos no ejecutados.

### 12.1 Árbol objetivo de la campaña y responsabilidades

Se conservan nombres de paquetes existentes cuando cambiar su ubicación no aporta un beneficio verificado. Este árbol muestra las ramas relevantes y sus responsabilidades; no autoriza eliminar archivos omitidos en él ni mover las dependencias.

```text
MADRLCitytleranflexresdr/
├── AGENTS.md, CLAUDE.md, README.md
├── pyproject.toml, requirements.txt, uv.lock
├── Dockerfile, .gitignore, .gitattributes, .dockerignore
├── .github/
│   ├── workflows/ci.yml                   # CI canónica con checks/nombres únicos
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── ISSUE_TEMPLATE.md
│   └── CODEOWNERS                         # propietarios reales verificados
├── LICENSE, CONTRIBUTING.md, SECURITY.md   # políticas coherentes con derechos/procedencia del padre
├── .claude/, .agents/                      # configuración/enlaces exigidos por cliente; sin copias de skills
├── .specify/, .vscode/                     # configuración de herramientas; sin modelos ni resultados
├── configs/                               # única raíz de configuración científica activa
│   ├── objective_policies.yaml             # una sola tabla E1/E2/E3
│   ├── scenarios.yaml
│   ├── algorithms/native.yaml        # configuración nativa resuelta por algoritmo
│   ├── experiments/iquitos.yaml
│   ├── evaluation/kpis.yaml
│   └── extensions/                        # solo si una extensión distinta justifica su propia config
├── uc3m/
│   ├── domain/                            # valores, identidad y contratos puros
│   ├── ports/                             # contratos realmente consumidos
│   ├── application/
│   │   ├── dataset/                       # procedencia, construcción y splits
│   │   ├── training/                      # única lógica de campaña/etapas
│   │   ├── evaluation/                    # KPI, evaluación congelada y estadística
│   │   └── thesis/                        # referencias de evidencia verificadas
│   ├── adapters/
│   │   ├── algorithms/                    # puente nativo e instrumentación
│   │   └── citylearn/                     # observaciones, acciones e inferencia
│   ├── presentation/                      # panel local de lectura
│   └── data/, env/, algorithms/, reward/, kpis/, multicriteria/, geography/, governance/
│                                          # módulos existentes con función propia; sin duplicar el flujo nuevo
├── tools/
│   ├── dataset/                           # entrypoints de construcción; lógica reutilizable en application/dataset
│   ├── eval/                              # entrypoints de análisis/reporte; sin segunda lógica estadística
│   ├── colab/build_modular_colab_notebook.py # único generador activo del notebook de campaña nueva
│   ├── figures/                           # fuentes/generadores únicos de diagramas
│   ├── thesis/                            # única implementación de herramientas Word
│   ├── ops/                               # inventario, retiro, árbol y duplicados
│   ├── training/, drive/                  # utilidades de función distinta, fuera del DAG histórico automático
│   └── skills/registry.yaml               # fuente local de skills; aliases de cliente no son copias
├── scripts/
│   ├── verify_project_context.ps1
│   ├── maintenance/retire_historical_outputs.ps1
│   ├── maintenance/consolidate_repository.ps1
│   ├── quality/run_fresh_training_gates.ps1
│   └── skills/, training/                 # wrappers de sistema operativo sin lógica duplicada
├── examples_madrl_v3/
│   └── madrl_citylearn_v3_modular_colab.ipynb # único notebook activo de campaña; otros requieren función distinta
├── governance/
│   └── repository_layout.yaml             # registro de árbol/roles/canon/facades/protegidos
├── specs/000..012-*/                       # contratos con trazabilidad vigente
├── tests/
│   ├── fresh_training/                    # aceptación nueva estricta, incluye árbol y duplicados
│   └── unit/, contract/, integration/, acceptance/, citylearn_v3/, ops/, skills/, uc3m/
├── docs/
│   ├── 00_INDEX.md                        # índice real, sin rutas rotas ni cifras manuales obsoletas
│   ├── architecture/, audits/, decisions/, research/, contributions/, failures/
│   ├── design/                 # una especificación activa por capacidad
│   ├── plans/                 # un plan activo para la campaña; handoff de rol distinto
│   ├── chapters/, thesis/           # capítulos y aportes con rol declarado
│   └── *.docx                            # documentos aprobados, uno por identidad documental tras conciliación
├── data/
│   ├── audits/, dataset_audit/            # trazabilidad anterior marcada; no entrada científica nueva
│   ├── maintenance/                       # inventario/retiro/consolidación, sin copias completas de artefactos
│   └── campaigns/<campaign_id>/
│       ├── raw/, dataset/, splits/
│       └── provenance.json, split_manifest.json, dataset_acceptance.json
├── outputs/
│   ├── README.md
│   └── campaigns/<campaign_id>/
│       ├── campaign_manifest.json
│       ├── pilot/, hpo/, confirm/, sensitivity/, evaluation/, reports/
│       └── [treatment_id]/attempts/[attempt_id]/ # forma única registrada en layout; sin espejos de resultados
├── deploy/                                # demo aislada; no duplica entrenamiento/inferencia científica
├── CityLearn/                             # dependencia protegida, solo lectura
└── external/                              # dependencias protegidas, solo lectura
```

Dentro de `outputs/campaigns/<id>/`, la forma exacta es `<fase>/<treatment_id>/attempts/<attempt_id>/`; el renglón de tratamientos del árbol es abreviado y no crea un segundo layout paralelo. El registro de `governance/repository_layout.yaml` fija esa ruta y sus aliases de lectura prohibidos. Configuración heredada en `uc3m/configs/` debe conciliase con `configs/`: migrar valores únicos y actualizar consumidores, sin mantener dos fuentes activas del mismo parámetro. Una extensión de siete ejes realmente distinta se registra aparte bajo `configs/extensions/`, sin simular que fue ejecutada.

### 12.2 Hallazgos actuales comprobados, no eliminación ejecutada

Inspección de 585 archivos del padre, excluyendo `.git`, entorno, caches, dependencias, outputs históricos, enlaces de cliente y skills de terceros. Es un inventario acotado, no una certificación de ausencia de duplicados en todas las dependencias o archivos generados.

- D-01: `docs/architecture/plano.png` y `docs/architecture/plano.png` son idénticos: SHA-256 `7098b256cd4170cf273fb0d9dc3e205a7782b5533d3a2551dfb27678e2a47ac2`. Retener como ruta canónica propuesta `plano.png` y redirigir referencias del otro, después de verificar generadores y consumidores. Ambos son la misma imagen; el nombre no demuestra vigencia arquitectónica del dibujo.
- D-02: `docs/architecture/_refs/citylearn_v2_environment.jpg`, `citylearn_v2_environment_docs.jpg` y `citylearn_v2_environment_jsdelivr.jpg` son idénticos: SHA-256 `9576611b4e684f3ac1c4bb2b530714b1e1ab784851212cd86b9f220bf77201c1`. Conservar la ruta simple `citylearn_v2_environment.jpg`, actualizar consumidores y eliminar dos copias tras validación. Conservar atribución/licencia de la fuente.
- D-03: `tools/check_training_dataset_ready.py` delega a `tools/dataset/check_training_dataset_ready.py`; `scripts/generate_borrador_tesis_docx.py` y `scripts/thesis_doctoral_sections.py` delegan a `tools/thesis/`. Son facades, no implementaciones completas duplicadas. Migrar consumidores modificables a la canónica y eliminar un facade solo cuando no tenga consumidores; si una dependencia protegida lo llama, conservar el puente mínimo registrado, sin lógica propia.
- D-04: `deploy/dashboard/app.py` y `deploy/inference/app.py` son servicios distintos; `uc3m/domain/evidence.py` y `uc3m/adapters/algorithms/evidence.py` tienen responsabilidades distintas. No eliminar por basename igual.
- D-05: existen tres Word en `docs/`, aunque el índice y `thesis_word_canons.py` declaran dos. Los tres difieren en hash y contenido: auditoría IV–VII (3705 párrafos, 57 tablas, 196 medios), informe 50 episodios (3740, 57, 196) y tesis doctoral (2654, 64, 213). Son conteos estructurales, no puntuaciones de calidad o completitud. Hay contenido textual único en cada par comparado. No elegir por bytes, cantidad de párrafos o fecha.
- D-06: hay dos raíces de configuración (`configs/` y `uc3m/configs/`) y múltiples generadores/patchers de notebook. Se debe demostrar si son funciones distintas o versiones del mismo flujo, consolidando capacidades útiles en una sola ruta activa.
- D-07: el índice de docs y READMEs contienen rutas/cifras de inventario y del flujo anterior que deben verificarse y regenerarse; un índice desactualizado no acredita un árbol correcto.

### 12.3 Regla para seleccionar el archivo más completo

El key de consolidación es `(tipo, responsabilidad, alcance, formato de representación)`. Para cada grupo, comparar en este orden: corrección/evidencia vigente; preservación literal de contenido aprobado; cobertura de requisitos y capacidades; tablas/figuras/referencias/contratos; consumidores; compatibilidad y pruebas. Fecha, tamaño o sufijo final/v4 no deciden el ganador.

Si un candidato contiene todo lo válido de los demás y pasa pruebas, conservarlo. Si ninguno contiene todo, integrar contenido único válido en una sola canónica, resolver contradicciones contra fuentes y registrar cada elemento conservado/excluido con razón. Una unión ciega de textos, parámetros contradictorios o algoritmos no es consolidación correcta. No perder comportamiento observable por reducir número de archivos.

Para Word protegidos, T12 produce comparación de cobertura y propuesta de canónica por identidad documental sin borrar ni reescribir originales. Tesis e informe pueden tener propósitos distintos; no se consideran duplicados entre sí solo por compartir capítulos. La eliminación de una versión con contenido único requiere primero consolidación documental, igualdad de textos aprobados, revisión de referencias y render visual con el flujo Word autorizado. Mientras no exista esa prueba, registrar `blocked_unique_content`, no eliminar ni afirmar cero duplicados resueltos. La prohibición de edición Word del encargo técnico se mantiene; el agente deja el trabajo documental preciso y su estado visible, sin usar el tamaño como atajo.

Para imágenes idénticas D-01/D-02, tras verificar consumidores y origen, puede eliminar las copias redundantes autorizadas por esta nueva instrucción. Para código/doc/config parcialmente repetidos, el mismo permiso cubre eliminación de clones demostrados después de integrar su cobertura y actualizar lectores. No cubre dependencias, fuentes primarias, resultados nuevos ni archivos abiertos o concurrentes no conciliados. Los facades imprescindibles se registran como adaptadores de rol distinto, no como otra fuente de lógica.

Cada consolidación conserva `canonical_path`, `removed_paths`, hashes antes/después, prueba de cobertura, consumidores actualizados y resultados de validación. No copiar duplicados a `_archive/` activo como sustituto de eliminarlos. Mantener mínimos registros de mantenimiento sin guardar otra implementación completa. Los outputs repetidos de tratamientos/semillas/splits o datasets de activos distintos no se fusionan solo por compartir bytes: la identidad/procedencia prevalece sobre hash para esos roles.

### 12.4 Entregables y aceptación del árbol

Implementar `tools/ops/audit_repository_layout.py`, `tools/ops/audit_duplicate_files.py`, `scripts/maintenance/consolidate_repository.ps1`, `governance/repository_layout.yaml`, `tests/fresh_training/test_repository_layout.py` y `test_duplicate_consolidation.py`.

El registro declara: protected_roots, generated_roots, required_paths_by_phase, canonical_sources por key, facades mínimos con consumidores, representaciones de formatos distintos y equivalencias legítimas por procedencia. No añadir excepciones genéricas para hacer verde el check.

Resultados nuevos bajo `data/maintenance/repository_layout_20261101/`: `repository_tree.json`, `duplicate_inventory.json`, `canonicalization_plan.json`, `consolidation_result.json`, `repository_layout_acceptance.json`. `repository_tree.json` refleja el filesystem existente y la fase, no el dibujo copiado. `duplicate_inventory.json` cubre hash exacto, normalización de texto sin tocar aprobados, AST y detección de capacidades/revisiones; similitud solo propone revisión, nunca autoriza borrado automático.

Puerta: una sola implementación/fuente activa por key; cero clones redundantes no justificados; todos los paths requeridos de la fase presentes; cero referencias activas rotas; ningún consumidor depende de rutas retiradas; pruebas y configuración resuelta equivalentes; cero pérdidas de contenido único. Todo `blocked_unique_content`, duplicado sin clasificar o destino que no pueda conciliarse mantiene `repository_layout_verified=false`; reportar alcance en vez de afirmar limpieza total. Las dependencias y representaciones legítimas quedan declaradas como fuera del criterio de clon activo, no se borran para obtener un contador cero.

La justificación de control de consumidores, configuración y límites de módulos es coherente con Sculley et al. (2015), *Hidden Technical Debt in Machine Learning Systems*, NeurIPS 28, https://papers.nips.cc/paper_files/paper/2015/hash/86df7dcfd896fcaf2674f757a2463eba-Abstract.html , y con Pineau et al. (2021), §10. La ubicación concreta de carpetas y el criterio de canónica son decisiones de ingeniería de este proyecto. Las tesis de Costea/Charbonnier y el artículo CityLearn de §10 aportan el alcance científico; no prescriben este árbol ni validan una eliminación.

## 13. Buenas prácticas de programación y aceptación verificable en GitHub

La petición adicional exige un árbol mantenible y verificable en GitHub. En este plan, «aceptación GitHub» significa evidencia de empaquetado, higiene, seguridad de workflows y checks para una revisión concreta. No significa que GitHub certifique el diseño científico ni que un dibujo de carpetas pruebe su implementación.

### 13.1 Programación y paquete Python

- Conservar el layout plano existente `uc3m/`. No migrar a `src/` por apariencia: PyPA documenta ventajas/compromisos de ambos. Acreditar la elección con wheel/sdist e importación del instalado sin depender del checkout como cwd ni de un `sys.path` global añadido por tests. Fuente: https://packaging.python.org/en/latest/discussions/src-layout-vs-flat-layout/ .
- Dominio sin infraestructura, casos de uso que reciben puertos, backends detrás de adaptadores y un único parser/composition root en `application/training/cli.py`. Módulos por responsabilidad; sin nuevas capas vacías, microservicios o dependencias para modificar carpetas.
- `pyproject.toml` declara paquete, compatibilidad y dependencias directas realmente utilizadas. Requirements/lock derivados representan una sola resolución, no listas divergentes mantenidas a mano. Verificar imports de YAML y otras dependencias; corregir URLs placeholder del proyecto. No anunciar versiones Python no probadas ni actualizar stack científico por conveniencia.
- Una configuración científica editable bajo `configs/`, entregada explícitamente mediante `--config`. No buscarla según cwd. Si wheel necesita recursos, generarlos en build desde la fuente canónica con hash, sin segunda copia editable en `uc3m/`. No empaquetar configuración privada ni datos de entrenamiento.
- Rutas portables con `pathlib`, tipos/contratos, validación y errores accionables. Mantener estricto el guard de desarrollo `D:/MADRLCitytleranflexresdr`; la identidad del checkout CI CPU se valida aparte y no habilita entrenamiento nativo fuera de esa frontera.
- Notebooks clientes de la CLI/API, con salidas limpiadas antes de versionar; sin segunda implementación, secretos ni resultados anteriores embebidos como baseline. Actualizar imports, notebooks, recursos, índices y configuración al mover una fuente.
- Reducir clones exige conservar contratos y comportamiento probado, no borrar pruebas. Un archivo más grande, reciente o llamado final no es automáticamente el más completo.

### 13.2 Árbol versionado y artefactos grandes

Versionar código, configuración no sensible, pruebas, documentación, generadores y manifiestos pequeños. Separar datasets/checkpoints/replay/logs/reportes generados en las raíces de ejecución ignoradas por rol. Una regla LFS no versiona un archivo ignorado ni retira uno ya indexado.

No añadir pesos `.pt/.pth/.ckpt/.pkl`, entornos, caches, credenciales, perfiles de navegador, CSV masivos, outputs completos o duplicados al árbol nuevo. Fixtures pequeños requieren origen, función y tamaño explícitos. Assets/Word aprobados siguen T12: no borrarlos por tamaño. Conciliar `.gitignore`/`.gitattributes`; no migrar LFS ni reescribir historia automáticamente.

GitHub documenta advertencia por archivo mayor de 50 MiB y bloqueo mayor de 100 MiB en Git ordinario: https://docs.github.com/en/repositories/working-with-files/managing-large-files/about-large-files-on-github . Comprobar blobs del árbol candidato y punteros LFS con esas unidades; no deserializar modelos para auditarlos. Los artefactos grandes permanecen locales o en un destino expresamente autorizado; no se publica un release por implementar estos checks.

### 13.3 CI, seguridad y colaboración

`ci.yml` es el punto de entrada canónico. Checks con nombres únicos: `quality-lint`, `quality-contracts`, `quality-package`, `quality-layout`, `quality-workflows`. Si se usan workflows reutilizables, no duplicar comandos ni nombres requeridos. Verificar rama destino real, sin asumir que master/main/develop son todas vigentes.

| Check | Evidencia exigida |
|---|---|
| quality-lint | Lint/sintaxis de fuentes y tests propios, sin excluir lo defectuoso para aprobar |
| quality-contracts | Contratos puros nuevos autocontenidos, sin históricos ni skips; no equivale a learners/GPU |
| quality-package | Wheel/sdist, contenido, imports del instalado y configuración explícita portable |
| quality-layout | Árbol/canónicas, referencias y ausencia de clones o artefactos indebidos |
| quality-workflows | YAML válido, paths/jobs reales, permisos, pins y ausencia de publicación/inyección no autorizadas |

Workflows con `permissions: contents: read` por defecto, acciones fijadas a SHA completo verificado, herramientas de calidad con versión resuelta y timeouts. Checkout PR no confiable sin credenciales persistentes, secretos ni permisos de escritura. No ejecutar código PR mediante `pull_request_target` ni interpolar contenido PR como shell. Conservar procedencia y procedimiento de actualización de pins. Fuente oficial: https://docs.github.com/en/actions/reference/security/secure-use .

El job hosted actual `foundation` invoca un guard que exige literalmente la raíz local `D:`: no acredita integración en un checkout hospedado distinto. T13 separa contratos CPU portables de aceptación nativa local sin desactivar el guard del entrenamiento. No contratar runners ni introducir gasto; un runner nativo autorizado sería evidencia adicional, nunca inferida desde contratos puros.

README con instalación, configuración, comando canónico y límites; CONTRIBUTING/SECURITY/plantillas/CODEOWNERS con una versión por finalidad y responsables verificables. LICENSE del padre coherente con metadata/derechos; no asignar licencias a terceros ni redistribuir backends por añadirlo. Las excepciones de gobernanza se reportan sin convertirlas en licencia. Son políticas de este proyecto, no requisitos universales de alojamiento en GitHub.

### 13.4 Estados y verificación remota

`data/maintenance/github_readiness_20261101/github_readiness.json` debe registrar commit/tree candidato, source hash, comandos/resultados, hashes de build, runtime probado, submódulos, checks requeridos, local_pass, remote_verified, workflow_run_url y branch_protection_status. Un workflow existente pero no ejecutado no se marca aprobado.

- `repository_layout_verified`: T12 pasó para alcance/fase declarados.
- `github_local_readiness`: T13 pasó checks locales para un árbol revisable; no implica push/merge.
- `github_remote_verified`: checks exigidos aprobaron el mismo commit y sus URLs/resultados se verificaron. Sin Actions real: `pending_remote`.
- La protección de ramas y checks requeridos exige permisos y autorización para configurar/publicar; no cambiar settings ni comprar plan por este encargo. Verificar su disponibilidad y usar nombres únicos. Fuente: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches .
- `scientific_acceptance`: puerta independiente de datos/experimento nuevos. Lint/build/CI/merge no acreditan superioridad científica.

El árbol y los checks concretan las guías oficiales y los principios científicos de §10/§12. Las tesis y artículos no prescriben nombres de carpetas ni garantizan una aprobación remota.

## 14. Nombres cortos por contenido: prevalencia del mapa de migración

La instrucción posterior del usuario pide renombrar carpetas y archivos para eliminar nombres extensos y números largos. El contrato y mapa operativo completo está en `docs/plans/renombrar_rutas.md` (N1–N7), incorporado al plan principal como T14. Incluye documentos del propio plan, carpetas SPEC, mantenimiento y configuración; sus destinos cortos prevalecen sobre nombres extensos propuestos en §§1–13, sin cambiar el alcance científico.

Política: `lower_snake_case`, ASCII, objetivo de 24 caracteres por carpeta/40 por archivo; sin cadenas >=6 dígitos, fechas ISO ni hashes en componentes propios. IDs cortos funcionales (`e1`, `seed_1001`, `try_01`, `001`) permanecen. README/AGENTS/LICENSE/pyproject y nombres de backend/tooling obligatorios se conservan con rol/excepción explícitos. No renombrar dependencias, raíz autorizada, entorno o rutas congeladas/activas.

Ejemplos de destino: plan `docs/plans/entrenamiento.md`, diseño `docs/design/entrenamiento.md`, handoff `docs/plans/encargo.md`, diagnóstico `docs/audits/historicos.md`; mantenimiento `data/maintenance/historicos`, `layout`, `github`, `names`; configuración `configs/experiments/iquitos.yaml`. Datos/resultados nuevos usan alias corto `iquitos` bajo `data/campaigns/` y `outputs/campaigns/`, con tratamiento/semilla/intento inequívocos.

El campaign_id completo, fecha, protocolo, seed y hashes permanecen en manifests; el alias de ruta no reemplaza identidad. El runner resuelve rutas desde ese manifiesto y rechaza alias ocupados o asociados a otro fingerprint. No sobrescribir, truncar identidades ni recrear resultados históricos retirados. Hashes compuestos por paths se recalculan antes del freeze; nunca se cambia retroactivamente una aceptación para hacer pasar un rename.

`naming_verified` exige mapa ejecutado, contenido conservado, referencias/imports/CLI/contratos correctos y cero nombres largos no justificados en el alcance propio. Estado de esta sesión: plan, sin movimientos realizados. La guía PEP 8 y GitHub están enlazadas en el plan de renombramiento; los límites exactos son decisiones del proyecto y la preferencia del usuario, no exigencias universales de la plataforma.


### Contrato implementado de almacenamiento

`CampaignSpec.storage_alias` es explícito y corto. Se serializa para resolver
rutas, pero no entra en `spec_hash`: el nombre de almacenamiento no redefine el
experimento. `campaign.json` vincula el alias al campaign_id/spec_hash completo
en ambas raíces. `treatments.json` vincula cada ruta corta al TreatmentKey y a
su fingerprint completo; se valida antes de reutilizarla. Los intentos conservan
la identidad a001/a002 en metadata y usan try_01/try_02 en disco. El runner y
los lectores descubren evidencia por manifiestos, sin extraer la identidad del
nombre de carpeta. No se mueve una campaña congelada para heredar aceptación.

La ejecución del mapa se verifica en `data/maintenance/names/acceptance.json`;
el estado anterior de solo planificación queda sustituido por ese registro.
