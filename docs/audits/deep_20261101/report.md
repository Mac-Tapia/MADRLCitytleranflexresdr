# Auditoría profunda MADRL: dataset → entrenamiento → evidencia

**Fecha:** 1 de noviembre de 2026, America/Lima. **Repositorio:** `D:/MADRLCitytleranflexresdr`. 
**Base Git observada:** `cb2d7c7c84b5315acb50b3b8828ef4a90065bdc4` más cambios locales preexistentes; ver baseline.json.

**Dictamen: NO CONFORME para entrenar la campaña confirmatoria como experimento aceptable, cerrar el jurado o promover un modelo.** La estructura modular existe y el dataset actual pasa las comprobaciones físicas/estructurales indicadas; la ruta ejecutable conserva brechas de integridad, configuración efectiva, evaluación y promoción. Esto no es una aceptación científica ni una validación de operación real.

Se registran **31 hallazgos/pendientes/riesgos**: {'P0': 4, 'P1': 19, 'P2': 8} al detectarlos. Parte de A01–A03 fue corregida concurrentemente durante el cierre; ver seguimiento. P0 bloquea la confianza en el experimento; P1 es alto; P2 es medio. La columna tipo distingue defecto demostrado, función incompleta, excepción declarada, riesgo y evidencia pendiente. No todos representan vulnerabilidades explotables ni todos bloquean simulación offline.

## Alcance, custodia y límites

- Inventario individual de **3777 archivos y 240 carpetas/entradas de frontera**. AST en 340 Python; 3039 CSV, **34,042,062 filas** estructurales; 5 notebooks. 0 errores de lectura final.
- Cada archivo tiene alcance explícito en files.csv/file_reviews.csv; cada carpeta en folders.csv; los módulos propios se detallan en modules.md. No se afirma lectura semántica línea por línea de todos los archivos, ni certificación de binarios, imágenes, PDFs, dependencias o resultados archivados.
- CityLearn/ y external/ son dependencias externas: frontera inventariada, con lectura puntual de interfaces/configuración/manifiestos; sin auditoría interna exhaustiva ni cambios. Entorno, .git, cachés y junctions no se recorren. Los conectores legados y estados de navegador se excluyen del inventario final; no se extraen credenciales.
- Primera pasada detectó codificación de facturas y JSONC; se corrigió el recolector, se repitió el análisis con UTF-8/cp1252 y separador por encabezado. Una señal estática no es por sí sola un defecto: p.ej. shell=True de una herramienta auxiliar y JSONC de VS Code requieren contexto.
- Solo se añadieron artefactos bajo esta carpeta. No se corrigió código, no se renombró ni retiró nada, no se editó Word, no se ejecutó entrenamiento, no se publicó ni se alteraron dependencias. Las pruebas crean temporales/cachés propios. El árbol tenía una reorganización extensa y trabajo concurrente; se conservó.
- 209 rutas tracked ausentes en el árbol son un inventario de la reorganización, no prueba de pérdida ni autorización de borrado. Deriva textual posterior al scan: 6 archivos; ver source_drift.json. No es snapshot atómico.

## Cambios concurrentes y corte de validez

Durante el cierre cambiaron 6 archivos de configuración, pruebas y código fuera de esta auditoría; listado exacto en source_drift.json. No se sobrescribieron. Se observó primero un ValueError transitorio por supervision no admitida por CAMPAIGN_KEYS; la carga fría posterior de current_recheck.json ya fue aceptada. Luego se verificaron 23 contratos de configuración, y recheck/probes.json confirmó rechazo del stage alterado y del freeze ficticio. Esos avances figuran en follow_up de cada hallazgo, sin convertirlos en aceptación nativa o científica. Los resultados anteriores quedan asociados al corte registrado en files.csv y sus hashes, y los archivos cambiados se marcan para nueva verificación en file_reviews.csv. La suite general propia se detuvo a las 15:23:55 UTC para no presentar validación de una revisión mezclada. No se detuvieron procesos ajenos. Esta auditoría no acredita el estado final de modificaciones concurrentes.

Los originales recuperables del paquete Colab previo que coinciden exactamente con hashes del inventario se conservan en inspection_cut/; baseline_sources.json indica cuáles coinciden. No es un checkout completo ni incluye una copia de las dependencias protegidas.

La comprobación posterior es acotada: A04/A05 permanecen reproducidos y la corrección de pesos/freeze tiene pruebas contractuales, pero no corrida nativa. Los 31 registros no significan 31 defectos idénticos todavía abiertos en una revisión posterior; consultar estado, evidencia y fecha.

## Evidencia favorable comprobada

- Contexto de raíz/origin comprobado antes de las operaciones. La política local del proyecto se respetó; no se usó otro repositorio.
- Dataset fresh: 23 fuentes con hash revalidado, 228 archivos en tabla de construcción, digest `6adc312c54062275bbe7bba886c60a0cf516f6419d4e4c781d42f3dc77033cbd` coincidente.
- Integridad del dataset activo: 222 CSV, 0 NaN, 0 Inf, 0 issues según el auditor propio reejecutado. No se extrapola ese resultado a los CSV históricos de todo el árbol.
- Se reconstruyeron 612 objetivos mensuales desde raw y se recalcularon 1836 cierres (total/punta/fuera de punta): 0 fallos, error relativo máximo 4.414e-08. Usa la reconstrucción COP del proyecto; no es validación independiente con medidores ni corrida nativa anual.
- Los 3 splits mantienen hashes registrados, 8760/8784/8760 filas; sin campos _predicted_ activos ni dispositivos autosize en los esquemas de split. Normalizador fit_scope=train_2023. Ver excepción A16.
- 590 objetivos mensuales etiquetados measured y 22 modeled. Esto no significa que las series horarias sean medidas: los perfiles horarios, DER, EV y carbono son modelados.
- Registro y hashes de skills: validación básica aprobada; descubrimiento no aprobado. pip check: No broken requirements found. OSV consultó 236 paquetes PyPI y señaló 34; no se realizó instalación limpia, prueba de explotación ni auditoría completa de OS/contenedores/submódulos.
- Las capas domain/application/ports/adapters existen. El diseño aprobado mantiene monolito modular sin imponer src/. No se penaliza usar módulos en vez de subcarpetas vacías; las brechas son los contratos desconectados.

## Validaciones ejecutadas

Suite general interrumpida por cambios concurrentes en fuentes/configuración/pruebas; último progreso visible 36 %, sin informe JUnit final ni aceptación general. Ver pytest.log y test_interruption.json. Cuatro pruebas nativas excluidas expresamente. Comprobación posterior acotada test_campaign_contract.py: {'tests': 23, 'failures': 0, 'errors': 0, 'skipped': 0}; no sustituye la suite integral.

| Comprobación | Resultado / artefacto |
|---|---|
| Contexto | OK, raíz/origin esperados |
| Inventario estático y CSV de todo el ámbito | scan.json, files.csv, folders.csv, imports.csv, signals.csv |
| Hashes de fuentes/dataset/splits | dataset_checks.json, coincidentes |
| Integridad CSV activos | csv_integrity.json: ok, 222 CSV, 0 NaN/Inf |
| Reconstrucción y cierre mensual | physical_checks.json: 1836 checks, 0 fallos |
| Pruebas de límites sintéticos locales | probes.json, security_probes.json, math_probes.json: defectos reproducidos, no resultados experimentales |
| Revisión posterior de cambios concurrentes | recheck/probes.json y concurrent_contract.xml: 23 contratos aprobados, sin omisiones; A04/A05 reproducidos de nuevo |
| Ruff | ruff.json: exit 1, 8 incidencias en tests |
| Skills | básico OK; --check-discovery exit 1, 11 entradas ausentes |
| Entorno instalado | pip_check.log: exit 0 |
| Vulnerabilidades de paquetes PyPI instalados | osv.json/osv.log: 236 consultados, 34 señalados; 237 grupos de alias, sin prueba de explotación |
| Verificador de flujo | workflow.log: exit 1, FileNotFoundError |
| Word | word_checks.json; extracción XML y relaciones, sin edición/render |
| Entrenamiento real de 4 backends | NO ejecutado; test_real_learning.py excluido de la orden pytest |
| Colab real, desconexión y multisemilla | NO ejecutado |
| Docker/servicios/planta/auditoría completa OS/contenedores/Actions remoto | NO ejecutado |

Orden de pytest reproducible: `.venv39-citylearn-v3/Scripts/python.exe -B -m pytest tests -q -p no:cacheprovider --ignore=tests/fresh_training/test_real_learning.py --junitxml=docs/audits/deep_20261101/pytest.xml`. El resultado excluye cuatro tests nativos; nunca equivale a la puerta integral sin omisiones de FR-N11.

## Hallazgos priorizados con corrección y aceptación

| ID | Prioridad | Tipo | Hallazgo |
|---|---|---|---|
| A01 | P0 | defecto reproducido | La ejecución nueva no impone los hashes que registra |
| A02 | P0 | defecto reproducido | La sensibilidad cambia pesos declarados pero conserva el comando de entrenamiento |
| A03 | P1 | implementación incompleta | El congelado HPO no determina los hiperparámetros confirmatorios |
| A04 | P0 | defecto reproducido | La completitud acepta evidencia de otra campaña y actualizaciones cero |
| A05 | P0 | defecto reproducido | NaN y hashes inválidos pueden producir un estudio científicamente completo |
| A06 | P1 | implementación incompleta | Falta evaluar checkpoints nativos congelados |
| A07 | P1 | defecto estático | Colab persiste a Drive solo cuando termina toda la etapa |
| A08 | P1 | defecto estático | El bloqueo del test se reduce a existencia de un archivo |
| A09 | P1 | defecto reproducido | El auditor de fuentes acepta rutas absolutas fuera de su raíz en Windows |
| A10 | P1 | defecto reproducido | EvidenceRegistry acepta evidencia inexistente |
| A11 | P1 | defecto reproducido | Catálogo y monitor no consumen el contrato de la campaña nueva |
| A12 | P1 | defecto reproducido | HPHI mezcla maximización y minimización |
| A13 | P2 | defecto reproducido | Hay dos IQM con resultados incompatibles |
| A14 | P1 | defecto estático | La selección antigua puede presentar ganador sin evidencia inferencial |
| A15 | P1 | defecto estático | La API pública de algoritmos conserva aprendizaje de placeholder |
| A16 | P1 | excepción declarada sin cierre experimental | La separación temporal tiene una excepción real y diseño con datos completos |
| A17 | P1 | inconsistencia documental confirmada | README y arquitectura vigente anuncian resultados retirados y otra ruta operativa |
| A18 | P1 | inconsistencia documental reproducida | Las 17 rutas del manifiesto del jurado dejaron de existir |
| A19 | P1 | brecha documental confirmada | Los Word canónicos no reflejan el retiro de resultados ni cierran J-06/J-07/J-08 |
| A20 | P2 | fallo ejecutado | El verificador del flujo falla antes de emitir su informe |
| A21 | P2 | fallo ejecutado | Lint falla y el control de tipos silencia errores relevantes |
| A22 | P2 | fallo ejecutado | El registro de skills es válido pero falta descubrimiento local |
| A23 | P1 | brecha estática de CI | CI no acredita las nuevas puertas y su contexto de raíz requiere adaptación explícita |
| A24 | P2 | brecha de empaquetado | Metadatos y dependencias no demuestran instalación limpia reproducible |
| A25 | P1 | riesgo condicionado al despliegue | El demo de inferencia carece de controles para operar una planta |
| A26 | P2 | riesgo de procedencia y recursos | Los adaptadores de datos legados no garantizan identidad de contenido |
| A27 | P1 | aceptación pendiente | No está materializada la aceptación nueva completa ni su entrega |
| A28 | P2 | deriva de evidencia histórica | La raíz de caché retirada existe de nuevo |
| A29 | P2 | riesgo de gobernanza | El paquete Colab incluye dependencias bajo excepción de licencia |
| A30 | P1 | coincidencias de vulnerabilidades por versión | El entorno instalado contiene versiones señaladas por OSV |
| A31 | P1 | defecto de contrato reproducido | El horizonte anual por defecto impide calcular KPI diarios completos |

### A01 — La ejecución nueva no impone los hashes que registra

**P0 · defecto reproducido. Archivos:** `uc3m/application/training/fresh_campaign.py:161;uc3m/application/training/fresh_campaign.py:280;uc3m/application/training/cli.py:51`.

**Seguimiento al cierre:** Parcial tras cambios concurrentes: recheck/probes.json rechaza stage alterado antes del ejecutor. La verificación completa de dataset/splits/normalizador/fuentes sigue por acreditar.

**Evidencia e impacto:** probes.json (corte inicial): se alteró stages/pilot.json en un temporal; su SHA dejó de coincidir y aun así hubo 4 llamadas al ejecutor inyectado, sin entrenamiento. build_dag confía en dataset_verified y run_stage no recalcula hashes de etapas, dataset, normalizador y fuentes. La CLI reutiliza un manifiesto existente sin contrastarlo con el config actual.

**Corrección propuesta:** Verificar identidad completa antes de crear intentos y antes de cargar modelos; reutilizar dataset_digest, ConfigurationFreeze y los contratos de evidencia existentes. Rechazar deriva sin sobrescribir campañas.

**Aceptación requerida:** Perturbar por separado CSV, split, código, normalizador, configuración y stage JSON: 0 llamadas al aprendiz y razón de rechazo específica.

**Trazabilidad:** FR-N01,N02,N03,N06,N11,N20;SPEC-004,011; J-09,J-10. Fundamento: S3,S4 en [sources.md](sources.md).

### A02 — La sensibilidad cambia pesos declarados pero conserva el comando de entrenamiento

**P0 · defecto reproducido. Archivos:** `uc3m/application/training/fresh_campaign.py:177;uc3m/application/training/cli.py:23`.

**Seguimiento al cierre:** Catálogo derivado y wiring añadidos en cambios concurrentes; 23 contratos posteriores aprobados. Falta aceptación con recompensa y aprendiz nativos.

**Evidencia e impacto:** probes.json: HAPPO confirmación y sensibilidad p055 tienen pesos distintos y native_arguments idénticos. native_learner proporciona el mismo UC3M_SCENARIO_CATALOG; no materializa ni verifica derived_scenario_catalog. La dependencia recibe E1 canónico.

**Corrección propuesta:** Generar catálogo derivado inmutable por tratamiento, resolverlo en el hijo y registrar los pesos leídos por la recompensa real.

**Aceptación requerida:** Mismas condiciones y semilla; cambiar solo dominancia debe cambiar los coeficientes observados en la recompensa y su hash efectivo.

**Trazabilidad:** FR-N06,N09;SPEC-002,005; J-10,J-12. Fundamento: S1,S3,S4 en [sources.md](sources.md).

### A03 — El congelado HPO no determina los hiperparámetros confirmatorios

**P1 · implementación incompleta. Archivos:** `uc3m/application/training/fresh_campaign.py:180;uc3m/application/training/fresh_campaign.py:292;uc3m/domain/campaigns.py:223`.

**Seguimiento al cierre:** Freeze tipado/hash y materialización de hiperparámetros añadidos; contratos posteriores aprobados. HPO/evaluación real siguen pendientes.

**Evidencia e impacto:** probes.json: hay 8 candidatos HPO, pero confirm.hyperparameters es null. Un diccionario truthy sin configuración validada permite entrar en sensibilidad. Existe ConfigurationFreeze tipado, pero el runner no lo usa ni exige evidencia de validación o piloto terminado.

**Corrección propuesta:** Seleccionar sobre validación, verificar ConfigurationFreeze por algoritmo, reconstruir argumentos confirmatorios y cumplir dependencias del DAG.

**Aceptación requerida:** Elegir un candidato no predeterminado: todos los argumentos confirmatorios coinciden con su freeze; un freeze incompleto se rechaza.

**Trazabilidad:** FR-N06,N09;SPEC-005; J-10,J-12. Fundamento: S1,S3,S4 en [sources.md](sources.md).

### A04 — La completitud acepta evidencia de otra campaña y actualizaciones cero

**P0 · defecto reproducido. Archivos:** `uc3m/application/training/fresh_campaign.py:208`.

**Seguimiento al cierre:** Reproducido también con expected_weights y supervisión del padre nuevo: acepta otra campaña, 0 actualizaciones y checkpoint inexistente. Ver recheck/metadata_acceptance.json.

**Evidencia e impacto:** security_probes.json: verified=true, otro campaign_id, actor con 0 actualizaciones y checkpoint inexistente producen training_complete=true. El adaptador habitual valida más cosas, pero esta frontera no comprueba identidad, archivos ni valores del mapa.

**Corrección propuesta:** Vincular evidencia a TreatmentKey/AttemptIdentity y verificar hashes, propietarios esperados, actualizaciones positivas y cobertura real antes de promover.

**Aceptación requerida:** Rechazar replay entre semillas/campañas, cero actualizaciones, checkpoint ausente o cambiado y episodios incompatibles.

**Trazabilidad:** FR-N05,N07,N11,N14;SPEC-004; J-04,J-07. Fundamento: S3,S5 en [sources.md](sources.md).

### A05 — NaN y hashes inválidos pueden producir un estudio científicamente completo

**P0 · defecto reproducido. Archivos:** `uc3m/application/evaluation/fresh_analysis.py:39;uc3m/application/evaluation/fresh_analysis.py:147;uc3m/application/evaluation/fresh_analysis.py:157`.

**Seguimiento al cierre:** Reproducido de nuevo después de cambios concurrentes: NaN todavía declara estudio completo. Ver recheck/probes.json.

**Evidencia e impacto:** probes.json: 144 filas sintéticas NaN con kpi_report_sha256 no válido dan coverage.complete=true y scientifically_complete=true. La cobertura solo busca None; p no finita se convierte en 1.

**Corrección propuesta:** Validar finitud, tipos, dominios de algoritmo/semilla/split y vínculo con KPI aceptados; distinguir test degenerado válido de error de datos.

**Aceptación requerida:** NaN, Inf, booleanos, hashes falsos y reportes de otra campaña nunca producen aceptación; resultados degenerados válidos quedan explícitos.

**Trazabilidad:** FR-N10,N11;SPEC-005; J-01,J-02,J-12. Fundamento: S3,S5 en [sources.md](sources.md).

### A06 — Falta evaluar checkpoints nativos congelados

**P1 · implementación incompleta. Archivos:** `uc3m/adapters/citylearn/policy_inference.py:121`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** load_native_policy termina siempre en NotImplementedError para cualquier paquete presente y marcado verified. Las pruebas actuales comprueban baselines o modelo ausente, no inferencia real de HAPPO/MASAC/MATD3/MAAC.

**Corrección propuesta:** Implementar cuatro cargadores de políticas nativas con normalización/acciones idénticas al entrenamiento y sin optimizador ni exploración.

**Aceptación requerida:** Recargar cada backend propio, comparar acciones antes/después, 0 actualizaciones y trazas completas de validación/prueba con hash.

**Trazabilidad:** FR-N05,N08,N12;SPEC-005,011; J-02,J-04,J-12. Fundamento: S1,S2,S3 en [sources.md](sources.md).

### A07 — Colab persiste a Drive solo cuando termina toda la etapa

**P1 · defecto estático. Archivos:** `tools/colab/build_modular_colab_notebook.py:143;examples_madrl_v3/madrl_citylearn_v3_modular_colab.ipynb`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** La celda espera subprocess.run de toda la etapa y después hace copytree. No hay copia por intento terminado. Una desconexión dura antes del retorno puede perder intentos completados que siguen en /content. No se realizó ensayo de desconexión real.

**Corrección propuesta:** Persistir cada intento terminado y su manifest de manera atómica, verificar readback y registrar intentos interrumpidos sin convertirlos en continuaciones.

**Aceptación requerida:** Cortar un runtime después de un intento completo: evidencia recuperable en Drive con los mismos hashes y reintento nuevo desde episodio 0.

**Trazabilidad:** FR-N07,N12;SPEC-008,011; J-07,J-15. Fundamento: S3 en [sources.md](sources.md).

### A08 — El bloqueo del test se reduce a existencia de un archivo

**P1 · defecto estático. Archivos:** `uc3m/adapters/citylearn/policy_inference.py:77`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** run_frozen_episode solo comprueba is_file(test_unlock.json); no lee contenido, firma/hash, campaña, algoritmo ni freeze. El comentario promete un congelado firmado que esta función no verifica.

**Corrección propuesta:** Verificar un desbloqueo derivado de un freeze aceptado y unido a campaña, políticas y split.

**Aceptación requerida:** Archivo vacío, JSON ajeno, hash alterado o freeze no validado: PermissionError antes de crear CityLearnEnv.

**Trazabilidad:** FR-N08,N09,N11;SPEC-005; J-10. Fundamento: S3,S4 en [sources.md](sources.md).

### A09 — El auditor de fuentes acepta rutas absolutas fuera de su raíz en Windows

**P1 · defecto reproducido. Archivos:** `uc3m/application/dataset/provenance.py:92`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** security_probes.json: una fuente absoluta con unidad Windows fuera de project_root fue aceptada. Se usaron exclusivamente archivos temporales propios. startswith("/") no detecta C:/...; tampoco se comprueban enlaces en todos los ancestros.

**Corrección propuesta:** Rechazar rutas con unidad/raíz, resolver contención y revisar symlinks/junctions en cada componente antes de abrir.

**Aceptación requerida:** Pruebas de unidad distinta, ruta absoluta, UNC, .. y junction ancestral; ninguna lectura fuera de la raíz permitida.

**Trazabilidad:** FR-N01,N02,N11;SPEC-001,011; J-09,J-10. Fundamento: S3 en [sources.md](sources.md).

### A10 — EvidenceRegistry acepta evidencia inexistente

**P1 · defecto reproducido. Archivos:** `uc3m/application/thesis/evidence_registry.py:20`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** security_probes.json: registrar accepted=True para un archivo inexistente devuelve accepted=1. El registro no exige hash, identidad, procedencia ni nueva lectura.

**Corrección propuesta:** Separar referencia editorial de evidencia aceptada; aceptar solo tras verificar archivo, hash, campaña y fase.

**Aceptación requerida:** Archivo ausente/alterado, manifest viejo o campaña ajena nunca pueden incorporarse como evidencia aceptada de tesis.

**Trazabilidad:** FR-N11,N12;SPEC-006,009; J-01,J-07. Fundamento: S3 en [sources.md](sources.md).

### A11 — Catálogo y monitor no consumen el contrato de la campaña nueva

**P1 · defecto reproducido. Archivos:** `uc3m/application/evaluation/results_catalog.py:20;uc3m/application/evaluation/results_catalog.py:54;uc3m/application/training/monitor.py:10;uc3m/presentation/training_panel.py:60`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** security_probes.json: un intento con learning_evidence.json y completion.json no se descubre. discover_runs y monitor esperan evidence.json/experiment.json. El default del catálogo es outputs/campaign y el monitor outputs/modular_training; la raíz nueva es outputs/campaigns/<alias>.

**Corrección propuesta:** Definir un contrato único o adaptador explícito de intentos nuevos; conservar compatibilidad histórica sin elegir campañas implícitamente.

**Aceptación requerida:** Un intento nuevo real aparece en catálogo/panel con campaña/seed/fase, y un hash roto cambia su estado sin ocultarlo.

**Trazabilidad:** FR-N12,N15,N16;SPEC-010,011; J-07,J-15. Fundamento: S3 en [sources.md](sources.md).

### A12 — HPHI mezcla maximización y minimización

**P1 · defecto reproducido. Archivos:** `uc3m/reward/hphi.py:26;uc3m/reward/hphi.py:139`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** math_probes.json: punto (-1,-1), nadir (-10,-10), ideal (0,0) produce 0 y debe ocupar 81/100=0.81. Una solución ideal 7D produce 0 en vez de 1. Pareto usa maximización; el cálculo HV usa referencia/convenio opuesto. No es el hypervolume 3D de fresh_analysis.

**Corrección propuesta:** Fijar orientación común y referencia normalizada; corregir tanto fallback como implementación opcional y separar el indicador legado de la selección nueva.

**Aceptación requerida:** Casos analíticos 2D/3D/7D, ideal=1, nadir=0, monotonía y concordancia contra biblioteca independiente.

**Trazabilidad:** FR-N10,N17;SPEC-005; J-03,J-12. Fundamento: S5,S7 en [sources.md](sources.md).

### A13 — Hay dos IQM con resultados incompatibles

**P2 · defecto reproducido. Archivos:** `uc3m/application/evaluation/scientific_evaluation.py:20;uc3m/application/evaluation/fresh_analysis.py:61`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** math_probes.json: [0,1,100] da IQM legado 1 y fractional IQM 17.3333333333. El corte entero elimina observaciones completas y con 3 semillas equivale a mediana.

**Corrección propuesta:** Una función canónica con pesos fraccionales y migración explícita de consumidores/reportes.

**Aceptación requerida:** Ambas rutas entregan la integral truncada correcta para n=3,5,6,12 y para datos repetidos.

**Trazabilidad:** FR-N10,N16;SPEC-005; J-12. Fundamento: S5 en [sources.md](sources.md).

### A14 — La selección antigua puede presentar ganador sin evidencia inferencial

**P1 · defecto estático. Archivos:** `uc3m/application/evaluation/model_selection.py:4;uc3m/multicriteria/stats_tests.py:1304`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** select_best_model exige solo campaign_complete y ordena media HV; no comprueba significancia, finitud, corridas verificadas o procedencia. decide_oe_winner no recibe p del omnibus y conserva ganador incluso si no encuentra Dunn. STATUS ya reconoce estos defectos; se verificó el código actual.

**Corrección propuesta:** Separar candidato operativo/descriptivo de superioridad inferencial y exigir evidencia válida. Reutilizar decisiones sin ganador forzado del protocolo nuevo.

**Aceptación requerida:** Campaña incompleta/no significativa/NaN no demuestra superioridad; ausencia de diferencia permite estudio completo sin ganador inferencial.

**Trazabilidad:** FR-N10,N12;SPEC-005; J-01,J-12. Fundamento: S3,S5 en [sources.md](sources.md).

### A15 — La API pública de algoritmos conserva aprendizaje de placeholder

**P1 · defecto estático. Archivos:** `uc3m/algorithms/factory.py:206;uc3m/algorithms/factory.py:237;uc3m/algorithms/factory.py:352;uc3m/__init__.py:32`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** AlgorithmFactory sigue exportado. Fallos amplios de backend se convierten en _trainer=None y learn ejecuta acciones aleatorias y devuelve métricas; save puede anunciar una ruta sin guardar modelo. La CLI nueva no usa esta ruta, pero otras entradas públicas sí pueden hacerlo.

**Corrección propuesta:** Fallar ante backend no disponible o exigir modo smoke explícito con tipo de salida inelegible para entrenamiento y selección.

**Aceptación requerida:** Error de import/configuración nunca produce training_complete ni checkpoint supuesto; todo placeholder queda identificado en manifiesto.

**Trazabilidad:** FR-N05,N16,N17;SPEC-003; J-03,J-07. Fundamento: S2,S3 en [sources.md](sources.md).

### A16 — La separación temporal tiene una excepción real y diseño con datos completos

**P1 · excepción declarada sin cierre experimental. Archivos:** `tools/dataset/build_fresh_campaign_dataset.py:56;tools/dataset/build_fresh_campaign_dataset.py:334;tools/dataset/split_campaign.py:37;uc3m/adapters/citylearn/fresh_observations.py:50`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** dataset_checks.json: 12 meses B01 train_2023 llevan cross_year_leakage_declared y dependen de 2024. La excepción está declarada y previamente autorizada: no es imputación oculta. No hay exclusión/sensibilidad ejecutada. BESS y autosizing se resuelven antes de separar el dataset de 3 años; debe delimitarse diseño conocido frente a validación temporal independiente.

**Corrección propuesta:** Mantener declaración, añadir sensibilidad sin edificios modelados y definir el fit_scope de dimensionamiento; no afirmar separación sin futuro de forma incondicional.

**Aceptación requerida:** Experimentos pareados completos con/sin excepción, dimensiones fijadas sin información prohibida o limitación explícita coherente con la hipótesis.

**Trazabilidad:** FR-N02,N03,N09;SPEC-001,005; J-09,J-10,J-11. Fundamento: S1,S4 en [sources.md](sources.md).

### A17 — README y arquitectura vigente anuncian resultados retirados y otra ruta operativa

**P1 · inconsistencia documental confirmada. Archivos:** `README.md:25;README.md:55;docs/architecture/dataset_construction_pipeline.md:3;docs/architecture/AGENT_HARNESS.md:54;specs/STATUS.md:18`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** README sigue declarando ganador v4, 12/12 y horizonte AWS 75 episodios; dataset_construction_pipeline apunta a CityLearn/data/datasets, outputs/latest_* y fuentes antiguas. STATUS y runbook retiran esos resultados y definen Colab fresco 50 episodios. AGENT_HARNESS aún describe el Stop hook como activo; settings actual es {} y STATUS dice desactivado.

**Corrección propuesta:** Actualizar entradas canónicas y rotular material histórico; verificar links/fechas/contratos sin borrar evidencia ni texto aprobado.

**Aceptación requerida:** Desde README existe una sola ruta actual dataset→Colab→evaluación; ninguna salida retirada acredita aceptación.

**Trazabilidad:** FR-N12,N15,N20;SPEC-006,011,012; J-01,J-04,J-07. Fundamento: S3 en [sources.md](sources.md).

### A18 — Las 17 rutas del manifiesto del jurado dejaron de existir

**P1 · inconsistencia documental reproducida. Archivos:** `data/audits/jury_observations_manifest.json:3;docs/audits/jurado.md:9`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** jury_paths.json: source_exists=false y 17/17 evidence_path inexistentes. Algunos documentos sobreviven como cap1.md...cap7.md; hay que reconstruir la trazabilidad. El Markdown exige pre-registrar al menos 10 semillas en J-02; el JSON dice mínimo 3. La matriz sigue citando evidencia retirada.

**Corrección propuesta:** Conservar el manifiesto histórico inmutable y crear una proyección vigente con mapa de rutas y una sola política de cierre por J-ID; no resolver observaciones sin evidencia nueva aceptada.

**Aceptación requerida:** Validador que abre cada referencia, verifica campaña/hash y rechaza observación resolved sin prueba/documento consistente.

**Trazabilidad:** FR-N12,N20;SPEC-009; J-01..J-17. Fundamento: S3,S5 en [sources.md](sources.md).

### A19 — Los Word canónicos no reflejan el retiro de resultados ni cierran J-06/J-07/J-08

**P1 · brecha documental confirmada. Archivos:** `docs/tesis.docx;docs/informe.docx;docs/chapters/cap7.md:72;tools/thesis/thesis_doctoral_sections.py:24;tools/thesis/update_word_quantitative_50episodes.py:42`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** word_checks.json y extracción XML: ambos Word mantienen resumen/resultados de madrl_v3 y 49/50, sin encabezado introducción general ni URL visible del repositorio; tampoco hay enlaces github.com en document.xml.rels. Las menciones de seguridad son antecedentes/trabajo futuro, no la sección de amenazas de cap7.md. Los generadores cuantitativos aún fijan RUN_ID/ANALYSIS de la corrida retirada. No se ejecutaron generadores, no se modificaron Word ni se validó paginación.

**Corrección propuesta:** Preparar una revisión documental separada basada en resultados nuevos aceptados, sincronizar capítulos y anexos y verificar estructura/render preservando texto aprobado.

**Aceptación requerida:** Ambos Word alineados con matriz del jurado y campaña admitida; anexo reproducible, introducción general y propuesta explícita de seguridad/privacidad.

**Trazabilidad:** FR-N12;SPEC-006,009; J-01,J-03,J-04,J-06,J-07,J-08,J-17. Fundamento: S2,S3 en [sources.md](sources.md).

### A20 — El verificador del flujo falla antes de emitir su informe

**P2 · fallo ejecutado. Archivos:** `tools/ops/verify_workflow_integrity.py:22;tools/ops/verify_workflow_integrity.py:261`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** workflow.log: exit 1 con FileNotFoundError por CityLearn/examples/madrl_citylearn_v3_tutorial.ipynb. Además conserva DATASET_DIR y lanzadores retirados; no verifica el flujo fresco.

**Corrección propuesta:** Reconectar al registro canónico y emitir errores estructurados; mantener perfil histórico separado.

**Aceptación requerida:** Ejecutar contra checkout nuevo y temporal con archivos ausentes: informe con razones, sin excepción no tratada ni búsqueda de fuentes retiradas.

**Trazabilidad:** FR-N15,N17,N20;SPEC-011; J-07. Fundamento: S3 en [sources.md](sources.md).

### A21 — Lint falla y el control de tipos silencia errores relevantes

**P2 · fallo ejecutado. Archivos:** `pyrightconfig.json:40;tests/fresh_training/test_campaign_contract.py:135;.github/workflows/ci.yml:53`.

**Seguimiento al cierre:** Ruff inicial: 8 incidencias; reevaluación registrada en ruff_current.json: 10. Los cambios concurrentes no se editaron.

**Evidencia e impacto:** ruff.json: 8 incidencias (6 F401, 1 F841, 1 E741), todas en tests. pyright desactiva reportUndefinedVariable, reportCallIssue, reportArgumentType, reportReturnType y otras comprobaciones. No se ejecutó Pyright ni se presenta como aprobado.

**Corrección propuesta:** Corregir incidencias acotadas y habilitar progresivamente diagnósticos en el código nuevo con presupuesto explícito.

**Aceptación requerida:** Ruff idéntico al CI en verde y evidencia real del alcance de comprobación de tipos.

**Trazabilidad:** FR-N17,N18;SPEC-012; J-07. Fundamento: S3 en [sources.md](sources.md).

### A22 — El registro de skills es válido pero falta descubrimiento local

**P2 · fallo ejecutado. Archivos:** `tools/skills/registry.yaml;tools/skills/validate_skills.py:107`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** validate_skills.py básico: OK. skills.log con --check-discovery: exit 1 y 11 entradas ausentes. No se regeneraron junctions ni se alteró configuración como parte de la auditoría.

**Corrección propuesta:** Usar scripts/skills/register_local_skills.ps1 en una corrección autorizada y comprobar ambos clientes; no copiar skills globalmente.

**Aceptación requerida:** Validador y -CheckOnly en verde más invocación real en cliente; un enlace correcto no demuestra eficiencia de agentes.

**Trazabilidad:** FR-N17;SPEC-007; J-07. Fundamento: S3 en [sources.md](sources.md).

### A23 — CI no acredita las nuevas puertas y su contexto de raíz requiere adaptación explícita

**P1 · brecha estática de CI. Archivos:** `.github/workflows/ci.yml:15;scripts/verify_project_context.ps1:3`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** El job foundation usa windows-latest con checkout por defecto, pero verify_project_context exige D:/MADRLCitytleranflexresdr. No se probó Actions para este commit/árbol sucio. El job de tests solo enumera cinco archivos legados; no incluye contratos frescos ni prueba científica. Ruff reproducido falla.

**Corrección propuesta:** Separar aceptación local con raíz exacta del perfil CPU portable para Actions; incorporar contratos frescos puros sin relajar la frontera local ni lanzar entrenamiento remoto.

**Aceptación requerida:** Cinco checks locales de T13 y evidencia Actions del mismo commit; informar por separado matriz nativa local y CI CPU.

**Trazabilidad:** FR-N11,N18;SPEC-000,012; J-07. Fundamento: S3 en [sources.md](sources.md).

### A24 — Metadatos y dependencias no demuestran instalación limpia reproducible

**P2 · brecha de empaquetado. Archivos:** `pyproject.toml:36;pyproject.toml:79;requirements.txt:25`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** pyproject declara numpy/pandas/scipy pero casos de uso importan yaml; PyYAML solo está en requirements. URLs apuntan a your-org/uc3m y comentario CityLearn v2 desactualizado. No hay LICENSE, CONTRIBUTING.md, SECURITY.md ni .github/CODEOWNERS canónicos. Varias dependencias y torch upgrade no están fijadas a un entorno reproducible. pip check actual sí pasa: eso solo acredita compatibilidad instalada, no ausencia de vulnerabilidades (A30).

**Corrección propuesta:** Conciliar dependencias mínimas/opcionales, lock y URLs con el mecanismo de instalación canónico; probar desde checkout CPU limpio sin tocar dependencias externas en esta auditoría.

**Aceptación requerida:** Build/importación e instalación limpia documentados, versiones y plataforma fijadas; no confundir entorno presente con reconstrucción.

**Trazabilidad:** FR-N17,N18;SPEC-001; J-07. Fundamento: S3 en [sources.md](sources.md).

### A25 — El demo de inferencia carece de controles para operar una planta

**P1 · riesgo condicionado al despliegue. Archivos:** `deploy/inference/app.py:78;deploy/inference/model_loader.py:109;deploy/docker-compose.yml:25;deploy/mosquitto.conf:5;deploy/plant_adapter/modbus_adapter.py:94`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** Demo documentado: modelo ausente/corrupto cae a política aleatoria, /health responde ok, Compose publica puertos sin dirección loopback, MQTT permite anónimos y endpoints no autentican. El adapter Modbus no impone envelope de seguridad. No se desplegó ni se atacó ningún servicio. Esto no invalida por sí solo la simulación offline, pero impide aceptación operacional.

**Corrección propuesta:** Mantener demo aislado y explícitamente inelegible para planta; antes de piloto exigir readiness real, autenticación, integridad de modelos, límites, fallback RBC y auditoría.

**Aceptación requerida:** Sin modelo no hay readiness operativa ni acciones hacia planta; pruebas locales de formas/finitud/límites, autenticación y rechazo de políticas stub.

**Trazabilidad:** FR-N11;SPEC-009,010; J-06,J-11,J-15,J-16. Fundamento: S2,S3 en [sources.md](sources.md).

### A26 — Los adaptadores de datos legados no garantizan identidad de contenido

**P2 · riesgo de procedencia y recursos. Archivos:** `uc3m/data/adapters/local_csv.py:37;uc3m/data/adapters/local_csv.py:78;uc3m/data/adapters/remote_http.py:81`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** LocalCsvDatasetAdapter.content_hash solo resume schema.json y lo trunca a 16 hex; cambiar CSV no cambia esa identidad. RemoteHttp reutiliza caché por nombre/esquema sin SHA esperado y descarga/extrae sin cuotas explícitas ni timeout. No se afirma Zip Slip: zipfile realiza saneamientos propios.

**Corrección propuesta:** Identidad SHA-256 de todos los archivos referenciados, caché ligada a digest y límites/timeout de descarga y expansión; no deserializar pickle remoto no confiable.

**Aceptación requerida:** CSV alterado cambia manifest; dos URLs/contenidos con igual nombre no colisionan; archivo excesivo se rechaza con motivo registrado.

**Trazabilidad:** FR-N02,N11,N17;SPEC-001,011; J-07,J-09. Fundamento: S3 en [sources.md](sources.md).

### A27 — No está materializada la aceptación nueva completa ni su entrega

**P1 · aceptación pendiente. Archivos:** `docs/plans/entrenamiento.md;specs/STATUS.md:64;uc3m/application/training/cli.py:21`.

**Seguimiento al cierre:** Suite general interrumpida por deriva; comprobación posterior acotada: 23 pruebas, 0 fallos/errores/omisiones. Sin aceptación nativa o científica.

**Evidencia e impacto:** Faltan tests/fresh_training/test_security_and_acceptance.py y test_delivery_contract.py previstos por T10/T11; no hay CLI de evaluación/entrega ni evidencia confirmatoria 144 celdas y 72 extremos terminados. authorized_stages está vacío. Las cuatro pruebas de aprendizaje real se excluyeron explícitamente de esta auditoría, no se contaron como aprobadas.

**Corrección propuesta:** Cerrar primero integridad/HPO/evaluación/seguridad; después ejecutar piloto, campaña, sensibilidad y entrega con recursos autorizados y evidencia nueva.

**Aceptación requerida:** Perfil estricto completo sin skip/xfail/xpass; cuatro aprendices reales, multisemilla y entrega hash-verificada. scientific_acceptance permanece false.

**Trazabilidad:** FR-N05,N09,N11,N12,N18;SPEC-005,006,011; J-02,J-04,J-12,J-13. Fundamento: S1,S2,S3,S5 en [sources.md](sources.md).

### A28 — La raíz de caché retirada existe de nuevo

**P2 · deriva de evidencia histórica. Archivos:** `outputs/dataset_cache;governance/repository_layout.yaml:22;data/audits/modular_training_acceptance.json`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** Se observó outputs/dataset_cache, aunque R-06 aparece retirado en STATUS. Su fecha observada precedía esta auditoría; no se atribuye su creación a los tests actuales. El manifiesto de smokes históricos sigue diciendo four_algorithm_smoke_verified=true, pero STATUS invalida sus artefactos y su dataset.

**Corrección propuesta:** Identificar consumidores que regeneran R-06 y separar indicadores históricos de puertas nuevas. Conservar custodia; no borrar por nombre.

**Aceptación requerida:** Readback actual del retiro y prueba de que el flujo nuevo no consume/regenera la raíz retirada; ningún smoke histórico promueve campaña nueva.

**Trazabilidad:** FR-N01,N13;SPEC-004,012; J-04,J-07. Fundamento: S3 en [sources.md](sources.md).

### A29 — El paquete Colab incluye dependencias bajo excepción de licencia

**P2 · riesgo de gobernanza. Archivos:** `governance/open_source_policy.yaml:39;tools/colab/build_modular_colab_notebook.py:183`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** La política reconoce excepciones para HARL/MARL/MATD3implementation. La lista ZIP observada contiene 269/47/27 archivos de esas raíces. La excepción no les concede una licencia abierta y su alcance de traslado/empaquetado debe conciliarse con el uso Colab. No es una conclusión jurídica ni se publicó el paquete.

**Corrección propuesta:** Documentar alcance de uso personal y redistribución del overlay; conservar notices/licencias cuando correspondan o entregar referencias fijadas en vez de copias.

**Aceptación requerida:** Inventario de componentes y permisos compatible con la política aprobada, excepción vigente y manifest con commits/hash reales.

**Trazabilidad:** FR-N12,N18;SPEC-001; J-07. Fundamento: S3 en [sources.md](sources.md).

### A30 — El entorno instalado contiene versiones señaladas por OSV

**P1 · coincidencias de vulnerabilidades por versión. Archivos:** `requirements.txt:25;pyproject.toml:36`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** osv.json: 236 distribuciones no editables consultadas, 34 paquetes señalados, 384 IDs equivalentes a 237 grupos de alias (230 alias CVE); 0 errores de detalle y sin paginación pendiente. No se probaron explotación ni alcance de uso de cada API. Incluye ray 1.8.0, pip 21.3.1, wheel 0.38.0, protobuf 3.20.3 y torch 2.8.0+cu126. Ray tiene avisos críticos cuyo impacto depende de exposición/uso; no se infiere que un servicio esté expuesto por estar instalado.

**Corrección propuesta:** Triage por componente, versión, API realmente usada y exposición; aplicar aislamiento y una remediación compatible con Python/CUDA/backends mediante un cambio separado y pruebas nativas. No actualizar en bloque ni tocar dependencias durante esta auditoría.

**Aceptación requerida:** Inventario/lock revisados con avisos aplicables resueltos o excepciones razonadas y vigentes; nueva consulta de versiones, instalación limpia y regresiones relevantes. pip check por sí solo no cierra seguridad.

**Trazabilidad:** FR-N11,N17,N18;SPEC-001; J-06,J-07,J-15. Fundamento: S3,S8 en [sources.md](sources.md).

### A31 — El horizonte anual por defecto impide calcular KPI diarios completos

**P1 · defecto de contrato reproducido. Archivos:** `uc3m/adapters/citylearn/policy_inference.py:88;uc3m/application/evaluation/kpi_contract.py:214`.

**Seguimiento al cierre:** Sin cierre integral acreditado; evidencia y alcance del corte documentados.

**Evidencia e impacto:** horizon_probe.json: el split declara 8760 horas; min(env.time_steps, env.time_steps-1) da 8759 muestras. Una traza analítica con ese horizonte real declarado produce district_daily_peak y one_minus_load_factor unavailable: incomplete_days; validate_kpi_report devuelve false. No se ejecutó una evaluación nativa anual para esta reproducción. Las pruebas de 48 pasos no cubren esta frontera.

**Corrección propuesta:** Definir intervalos de energía, estado inicial y estado terminal; extraer las 8760/8784 mediciones correctas o imponer una ventana completa explícita coherente con el contrato diario, sin rellenar datos ni ocultar la última hora.

**Aceptación requerida:** Evaluaciones anuales de train/validation/test con todos los primarios disponibles, timestamps alineados y balance/SOC terminal verificados; casos analíticos de primer/último intervalo.

**Trazabilidad:** FR-N04,N08,N12;SPEC-005; J-09,J-11,J-12. Fundamento: S1,S3,S6 en [sources.md](sources.md).

## Observaciones del experto, una por una

Fuente de contraste: manifiesto J-01..J-17 y matriz local del jurado. El documento externo original referido por esa matriz no forma parte de la lectura de este repositorio; no se certifica fidelidad completa a ese original. No se declara ninguna observación integralmente cerrada con evidencia de campañas retiradas.

| ID | Estado auditado | Diagnóstico actual | Hallazgos |
|---|---|---|---|
| J-01 | parcial; sin cierre vigente | El código nuevo intenta separar inferencia y ranking, pero A05/A14 permiten decisiones inválidas; README/Word siguen en campañas retiradas. | A05,A14,A17,A19 |
| J-02 | pendiente experimental | 12 semillas configuradas; no se acreditó entrenamiento independiente de las 144 celdas. El mínimo 3 del JSON contradice el mínimo 10 del Markdown. | A18,A27 |
| J-03 | parcial | Tres ejes frescos definidos; UC3M público anuncia 7 ejes, transferencia y N sin límite sin validación equivalente; HPHI falla. | A12,A15,A19 |
| J-04 | pendiente experimental/documental | La antigua cobertura 49/50 ya no es aceptación vigente; mantenerla identificada como historia y obtener nueva evidencia homogénea de HAPPO. | A04,A06,A19,A27 |
| J-05 | parcial documental | Hay formulación del aporte en capítulos, pero cap1 conserva prompt de maestría profesionalizante mientras tesis.docx se presenta doctoral; requiere conciliación editorial. | A17,A19 |
| J-06 | parcial documental; operación pendiente | cap7.md §7.6 propone seguridad/privacidad sin afirmar implementación; no está trasladado como sección sustantiva a ambos Word. Demo y dependencias requieren controles/triage. | A19,A25,A30 |
| J-07 | parcial | Remoto/README existen; no hay URL Github en texto ni relaciones de ambos Word; falta entrega reproducible de campaña nueva. | A10,A19,A24,A27,A29 |
| J-08 | pendiente documental | No se halló encabezado de introducción general en la extracción de ambos Word; Capítulo 1 no equivale a comprobar este requisito. | A19 |
| J-09 | parcial verificado | Procedencia de 23 fuentes, 590/612 meses medidos y 22 modelados; 12 backcasts declarados. Calidad estructural actual pasa, falta tabla documental y control de alcance. | A09,A16 |
| J-10 | parcial con defecto | Splits y normalizador train-only verificados por hash; backcast B01 usa 2024 y freeze/test unlock no son barreras suficientes. | A01,A03,A08,A16 |
| J-11 | parcial | Limitaciones de clima, carbono, precios y DER modelados declaradas; sin stress/OOS de políticas nativas ni piloto físico. | A06,A16,A25,A27 |
| J-12 | pendiente experimental | IQM fraccional nuevo y familias Holm implementados, pero NaN se acepta y no hay CI de entrenamiento independiente real. | A05,A13,A27 |
| J-13 | pendiente experimental | Configuraciones de escalabilidad en multicriteria son propuestas; no hay curvas comparables aceptadas para varios tamaños. | A27 |
| J-14 | pendiente analítico | Costos en USD y FX documentados no constituyen costo-beneficio CAPEX/OPEX/tiempo de cómputo; no se inventaron estimaciones. | A19,A27 |
| J-15 | parcial | Runbook nuevo existe, pero persistencia Colab por etapa y catálogo viejo no acreditan recuperación/operación. | A07,A11,A25 |
| J-16 | pendiente de verificación documental | No hay piloto ni HIL/SIL acreditado. Esta auditoría no asigna TRL superior por código o servicios demo. | A25,A27 |
| J-17 | pendiente editorial | Extracción textual no acredita síntesis por capítulo, índice ni paginación. Requiere revisión documental y render separados. | A19 |

## Requisitos nuevos FR-N01..N20

| ID | Estado auditado | Hallazgos | Evidencia / brecha |
|---|---|---|---|
| FR-N01 | parcial | A01,A09,A28 | Aislamiento tipado existe; fronteras no impuestas en toda la vía canónica. |
| FR-N02 | verificado con excepción; parcial integral | A01,A09,A16 | Hash/cierres/CSV verificados; 22 meses modelados y límites de fuente pendientes. |
| FR-N03 | parcial | A01,A08,A16 | Splits 8760/8784/8760 y normalizador train-only; B01 y diseño requieren delimitación. |
| FR-N04 | parcial | A06,A31 | Contrato KPI y casos analíticos; el horizonte anual predeterminado incumple días completos. |
| FR-N05 | pendiente de aceptación nativa | A04,A06,A15,A27 | No se ejecutaron cuatro pruebas reales en esta auditoría. |
| FR-N06 | parcial; actualización contractual verificada | A01,A02,A03 | 23 contratos posteriores pasan; falta aceptación nativa de pesos/hiperparámetros efectivos y toda la identidad. |
| FR-N07 | parcial | A04,A07 | No-resume e intentos nuevos existen; recuperación persistente no ensayada. |
| FR-N08 | incompleto | A06,A08,A31 | Baselines cortos operativos; cargadores nativos y contrato anual incompletos. |
| FR-N09 | incompleto | A02,A03,A27 | DAG y presupuesto; HPO/freeze/sensibilidad efectiva sin cierre. |
| FR-N10 | no conforme | A05,A12,A13,A14 | Aceptación de NaN e indicadores/decisiones incompatibles. |
| FR-N11 | incompleto | A01,A04,A05,A08,A09,A10,A23,A25,A27,A30 | Falta el contrato integral de seguridad y promoción nueva; versiones con avisos OSV. |
| FR-N12 | incompleto | A06,A07,A10,A11,A17,A19,A27,A29 | Runbook existe; entrega reproducible y tesis no acreditadas. |
| FR-N13 | deriva detectada | A28 | R-06 observado presente; no ejecutar limpieza automática. |
| FR-N14 | parcial | A04,A27 | Salvage se rechaza; no se repitió regresión nativa completa de HAPPO. |
| FR-N15 | parcial | A11,A17,A20 | Capas/directorios presentes; consumidores e índices desconectados. |
| FR-N16 | parcial | A11,A13,A15 | Coexisten contratos viejo/nuevo y API placeholder; duplicados no autorizan borrado. |
| FR-N17 | parcial | A12,A21,A22,A24,A26 | Arquitectura contractual, pero lint/typing/empaquetado con deuda. |
| FR-N18 | no acreditado | A21,A23,A24,A27,A29 | Árbol sucio y sin Actions del estado auditado; no se publicó. |
| FR-N19 | inventariado; sin aprobación integral | — | Nombres observados en files.csv; no se realizaron renombres. |
| FR-N20 | no conforme | A01,A17,A18,A20 | 209 rutas tracked ausentes por reorganización y referencias antiguas: preservar mapa/custodia. |

## Árbol y buenas prácticas

| Raíz | Evaluación |
|---|---|
| uc3m/domain, ports | Contratos y tipos presentes; ConfigurationFreeze y evidencia robusta necesitan conectarse a la ruta nueva. |
| uc3m/application | Casos de uso separados; coexisten orquestación antigua/nueva, evaluación vieja/nueva y promociones con barreras distintas. |
| uc3m/adapters | Adaptación nativa instrumentada existe; faltan cargadores congelados y ejecución efectiva de políticas derivadas. |
| configs, governance | Catálogos y reglas presentes; config real del backend y checks de ejecución no quedan garantizados solo por YAML. |
| tools/dataset, tools/eval, scripts | Generación nueva verificable; utilidades históricas y checker conservan contratos/rutas retirados. |
| tests, .github | Tests contractuales útiles; falta cobertura adversarial de fronteras y aceptación fresca remota/local coherente. |
| docs, specs | Estructura y planes extensos; índices, canónicas y estados no concilian el nuevo contrato ni toda la migración. |
| data/campaigns | Dataset conservado y hashes válidos; separar measured/modelled y excepción temporal. |
| data/maintenance, data/audits | Custodia e intentos fallidos preservados; no contarlos como campaña vigente ni borrarlos por duplicación. |
| outputs | Paquete Colab y caché; no hay campaña confirmatoria aceptada observada. No seleccionar carpetas por fecha. |
| deploy | Demo separado, explícitamente insuficiente para operación; no convertir su health HTTP 200 en aceptación. |
| tools/skills | Registro íntegro; discovery pendiente y conectores legados fuera del recorrido de contenido. |
| CityLearn, external | Dependencias protegidas; no se audita cada archivo interno ni se modifica su stack. |

El inventario completo está en folders.csv; los duplicados de texto en duplicate_text.json son candidatos de revisión, no una lista de eliminación. Esquemas de train/test idénticos pueden ser correctos porque los CSV difieren.

## Riesgos adicionales que requieren verificación dirigida

- Además del rechazo anual reproducido en A31, verificar el desfase potencial entre series [:taken] y SOC final en taken con una traza nativa conocida. No se ha demostrado aquí un error numérico nativo de ese alineamiento terminal.
- El balance energético de kpi_contract reconstruye importación, exportación y neto desde la misma serie net_power. Es una identidad algebraica, no una prueba independiente de cierre entre carga, PV, EV y BESS. No debe presentarse como validación física integral.
- PhysicalTrace comprueba longitud/finitud de series, pero no una malla temporal completa, unicidad de timestamps ni todos los nombres/unidades de señales de distrito. Añadir contratos de timestamps y denominadores de ganancia antes de considerar los KPI físicamente aceptados.
- La procedencia oficial reanalysis/estadística y los cierres mensuales no acreditan realismo de sesiones EV, dimensionamiento óptimo, políticas seguras ni validez geográfica externa.
- El perfil Pytest inspeccionado contiene veto skip/xfail/xpass para fresh_training. Su existencia no reemplaza la prueba adversarial del propio veto ni la aceptación de todos los perfiles.

## Orden de remediación propuesto

1. Integridad y promoción: A01, A04, A05, A08, A09, A10. Pruebas locales temporales que fallen antes de llamar al aprendiz.
2. Semántica experimental: A02, A03, A06, A31; pesos observados, HPO congelado, cuatro políticas recargables y horizonte anual coherente. Corregir HPHI/IQM/selección para consumidores que los usen.
3. Persistencia y contrato único: A07, A11, A15; conectar intentos a reportes y Drive con readback.
4. Alineación del repositorio y entorno: A17..A24, A28..A30; restaurar referencias/checks y hacer triage de dependencias preservando movimientos/custodia existentes.
5. Cerrar excepción temporal o sensibilidad A16 y pasar T10/T11. Después, con recursos autorizados, ejecutar piloto/HPO/confirmación/sensibilidad y evaluación final.
6. Solo con nueva evidencia aceptada, actualizar Word/anexos y revisar cada J-ID; operación real mantiene su puerta independiente A25.

No se fija un porcentaje artificial de cumplimiento. El veredicto conserva implementation_ready_for_training=false y scientific_acceptance=false.

## Archivos de la entrega

- [summary.json](summary.json): dictamen legible por máquina y alcance.
- [findings.csv](findings.csv) y [findings.json](findings.json): hallazgos con corrección, aceptación y trazabilidad.
- [file_reviews.csv](file_reviews.csv), [files.csv](files.csv), [folders.csv](folders.csv), [modules.md](modules.md): revisión individual y límites.
- [requirements.csv](requirements.csv), [jury.csv](jury.csv), [jury_paths.json](jury_paths.json): matrices de cumplimiento.
- [sources.md](sources.md): tesis de maestría/doctorado, artículos y límites de indexación/aplicabilidad.
- Logs, JSON de reproducciones y scripts collect.py/probes.py/physical.py/security_probes.py/horizon_probe.py/osv_check.py/finalize.py: evidencia local; repetir sobre un corte estable.
