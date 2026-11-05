# Dictamen de auditoría: no aprobado para lanzar la campaña ni para declarar aceptación

La base de arquitectura es buena. Lo que falla es lo que debería impedir un mal resultado: la puerta de aceptación da por buena evidencia falsa, CI nunca se ha ejecutado con su versión nueva y el respaldo en Drive pierde intentos si se corta.

No modifiqué nada del repositorio. Revisé el árbol de trabajo sobre `d55c6c62`, rama `fix/madrl-traceability-docs`.

| Dimensión | Estado | Motivo principal |
|---|---|---|
| Arquitectura moderna | 🟡 Parcial | El monolito modular es real, pero la ruta canónica casi no usa los puertos y hay un ciclo oculto |
| Cumplimiento de specs | 🔴 Deficiente | `STATUS.md` describe otro sistema y hay contratos implementados que no se aplican |
| Buenas prácticas | 🟡 Parcial | Código cuidado, pero con lint roto y funciones de hasta 195 líneas |
| Seguridad | 🟡 Parcial | Código bien defendido, pero el despliegue en la nube viene abierto por defecto |
| Integración modular | 🔴 Deficiente | Las etapas no encajan de punta a punta |
| Robustez | 🔴 Deficiente | Hay fallos que terminan con código de salida 0 y un corte puede perder trabajo |
| Harness engineering | 🟡 Parcial | Buen diseño, pero casi nada lo hace cumplir de forma automática |

**Evidencia:** **R** = lo reproduje, **L** = lo leí en el código, **S** = evidencia de otra sesión, no repetida por mí.

## P0: bloquean la campaña

| # | Hallazgo | Evidencia |
|---|---|---|
| 1 | **La puerta acepta evidencia inválida.** Con 0 actualizaciones, 0 pasos, un intento ajeno, 1 de 2 tratamientos y un checkpoint basura da `scientific_acceptance: true`. El contrato estricto rechazaría ese caso con 6 motivos, pero [`treatment_trust_reasons`](uc3m/application/training/fresh_acceptance.py#L167-L186) no lo llama. El catálogo de resultados y la restauración desde Drive usan esa misma regla. Ya era H20. | R |
| 2 | **Una campaña legítima nunca puede aprobarse (nuevo).** La puerta exige [`status` en `reports/scientific_report.json`](uc3m/application/training/fresh_acceptance.py#L240-L242), pero nadie escribe ese archivo y [`as_dict()`](uc3m/application/evaluation/fresh_analysis.py#L182-L185) no incluye `status` ni `campaign_id`. Además, [`deliver()`](uc3m/application/pipeline.py#L167-L172) no pasa `gate_report`. Junto con el n.º 1: lo falso pasa y lo real no. | L |
| 3 | **El reporte de la puerta no está ligado a nada (nuevo).** `_gate_is_clean` confía en un JSON sin commit, árbol ni campaña, y no comprueba `junit_sha256`. Un reporte verde antiguo sirve para siempre. | L |
| 4 | **Un corte en Drive pierde intentos (nuevo).** El manifiesto [solo se escribe al final](uc3m/application/training/drive_sync.py#L112). Si se corta antes, lo copiado en esa pasada queda como `conflicts` para siempre, no se restaura en una sesión nueva y [la CLI sale con 0](uc3m/application/training/drive_sync.py#L190). Es justo el caso de una desconexión de Colab. | R |
| 5 | **CI nunca ha validado este código (nuevo).** El [`ci.yml` endurecido](.github/workflows/ci.yml#L3-L7) solo se dispara en `master`, que sigue con otro «CI/CD Pipeline» de junio. La rama va 324 commits por delante y 106 por detrás, `gh run list` sale vacío y `master` no tiene protección. Además, al menos **2 de sus 5 jobs fallarían hoy**: `quality-lint` (3 errores de `ruff`) y `quality-package` (`test_declared_dependencies_cover_runtime_imports`). | R |

## P1: alta prioridad

| # | Área | Hallazgo | Evidencia |
|---|---|---|---|
| 6 | Robustez | `pipeline evaluate` con tratamientos fallidos [sale con 0](uc3m/application/pipeline.py#L217), aunque su documentación dice que 0 significa «hecho». Un notebook seguiría adelante sin avisar. | R |
| 7 | Robustez | Un `.partial` que quede de un corte [bloquea `analyze`](uc3m/application/pipeline.py#L151-L152) en todos los reintentos. | R |
| 8 | Seguridad | La restauración de Drive [no contiene las rutas del manifiesto](uc3m/application/training/drive_sync.py#L133-L139): `sub/../../outside.txt` escribió fuera de `artifacts`. Requiere un Drive alterado, y ya existe `contained_path` para evitarlo. | R |
| 9 | Seguridad | [Terraform](deploy/aws/iac/variables.tf#L29-L38) abre SSH y HTTP a `0.0.0.0/0` por defecto y `/act` y `/analytics` no tienen autenticación. En Kubernetes faltan TLS, autenticación en Mongo, `securityContext` y `NetworkPolicy`. Los tres contenedores de `deploy/` y el `Dockerfile` raíz corren como root. Sube a P0 si alguien lo despliega; el `docker-compose` local sí está bien limitado a loopback. | L |
| 10 | Dependencias | Hay tres fuentes de verdad: `requirements.txt`, `pyproject.toml` y `uv.lock`. Incluyen versiones muy antiguas (`ray==1.8.0`, `protobuf==3.20.3`) y otras sin fijar. Python 3.9, el fijado en CI, ya no tiene soporte. Ningún job de CI escanea vulnerabilidades. | L |
| 11 | Pruebas | La suite tiene 5 fallos de 1093, sin omisiones, en 60 minutos. Tres pruebas dependen de [checkpoints en `.superpowers/`](tests/fresh_training/test_frozen_evaluation.py#L23), que no está versionado, así que en un clon limpio no tendrían esos checkpoints (H19). | S para los totales, L para H19 |
| 12 | Specs | `STATUS.md` dice perfil v5 y el código usa `thesis_indicators_v7`. También marca FR-N17/N18 como pendientes aunque ya existe CI. `AGENT_HARNESS.md` sigue describiendo como activo el Stop hook, retirado el 31 de octubre, y cita 307 pruebas. | L |

## P2: deuda técnica

- **Arquitectura:**
  - `SimulatorPort` no tiene consumidores y `LearnerPort` solo se usa en `runner.py`, fuera de la ruta canónica.
  - Hay un ciclo `fresh_analysis → multicriteria → results_catalog → fresh_analysis`, oculto por imports perezosos.
  - [`pipeline.py:169`](uc3m/application/pipeline.py#L169) importa `tools`, que el wheel no incluye (H23).
- **Prueba de arquitectura:** [`test_import_architecture.py`](tests/contract/test_import_architecture.py#L51-L56) no cubre puertos, `tools` ni imports relativos, y no está en CI.
- **Checkpoints:**
  - [`evidence.py:45`](uc3m/adapters/algorithms/evidence.py#L45) usa `weights_only=False`.
  - `policy_inference.py` depende del valor por defecto de torch: es seguro en la 2.8 instalada, pero `pyproject.toml` admite `torch>=2.0`.
  - Antes de cambiarlo, hay que probar cada backend, porque MAAC guarda diccionarios complejos.
- **Inferencia:**
  - `last_clipped` es estado compartido entre hilos, así que una respuesta puede informar el recorte de otra petición.
  - [Un `.onnx` sin metadatos](deploy/inference/model_loader.py#L97-L110) responde `/ready` 200 con dimensiones por defecto.
  - El error 500 [expone el texto de la excepción](deploy/inference/app.py#L126).
- **Mantenibilidad:** `stats_tests.py` tiene 1916 líneas, `run_selection_pipeline` 195 y `run_stage` 149. Además, hay 5 `except` amplios silenciosos.

## Harness engineering

- **Reglas sin control automático:** `verify_project_context.ps1` es obligatorio en `AGENTS.md`, pero `.claude/settings.json` está vacío y no hay `pre-commit`.
- **Sesiones concurrentes:** durante esta auditoría otra sesión corrió pruebas y escribió en el mismo árbol, sin worktree ni bloqueo. Por eso no lancé la suite completa.
- **Instrucciones en conflicto:** `AGENTS.md` trata `CityLearn/` como dependencia externa, tu memoria guardada dice que se puede modificar libremente y la auditoría previa la llama protegida. La recompensa v7 vive ahí, así que conviene dejar una sola regla.
- **Descubrimiento de skills:** `validate_skills.py --check-discovery` falla con 11 entradas ausentes, porque falta `.agents/`.
- **Memoria de fallos:** no existe `docs/failures/`, así que los incidentes no quedan ligados a una prueba que evite repetirlos.
- **Restos de operaciones:** quedan `.git_commit_msg.tmp` en `external/MAAC` y 33 MiB de basura en `.git`.

## Lo que está bien y hay que conservar

- **Descarga de datasets:** [`remote_http.py`](uc3m/data/adapters/remote_http.py) tiene cuotas, rechazo de rutas peligrosas y enlaces, y publicación atómica.
- **Escritura a planta:** [`actions_for_plant`](deploy/plant_adapter/modbus_adapter.py#L95-L108) exige elegibilidad y autorización explícita del operador.
- **Diseño de CI:** acciones fijadas por SHA, permisos mínimos y perfil donde un skip cuenta como fallo.
- **Otros:**
  - `attempt_evidence_reasons` ya es el contrato correcto; solo falta conectarlo.
  - El dominio está limpio, salvo `numpy`.
  - El panel solo escucha en loopback.
  - No hay `shell=True` en `uc3m/`.
  - El auditor local es de solo lectura.
  - No encontré secretos con los patrones que busqué.

## Orden de corrección recomendado

1. **Puerta de aceptación (n.º 1–3):** usar una sola validación estricta, exigir cobertura exacta de tratamientos, ligar el reporte a commit y campaña, y conectar `analyze → deliver`. La fixture de [`test_security_and_acceptance.py`](tests/fresh_training/test_security_and_acceptance.py#L52-L55) codifica el contrato débil y habrá que cambiarla.
2. **Drive y pipeline (n.º 4, 6, 7, 8):** escribir el manifiesto tras cada intento, salir con código distinto de 0 ante conflictos o fallos, y contener las rutas.
3. **CI (n.º 5):** corregir lint y dependencias, añadir las pruebas de arquitectura y abrir un PR para que se ejecute de verdad. Conciliar los 106 commits de `master` será un trabajo aparte.
4. **Decisiones tuyas:** dataset v1 o v3, tarifa y contrato experimental (H01, H02, H05). Ningún cambio de código puede resolverlas.
5. **Documentación:** actualizar `STATUS.md` y `AGENT_HARNESS.md` al final, para que reflejen lo ya corregido.

## Límites de esta revisión

- **No ejecutado:**
  - `pip-audit` y `bandit`, porque no están instalados y no quise instalar nada sin tu permiso; solo pasé reglas de seguridad de `ruff`, así que el estado de vulnerabilidades de las dependencias sigue sin conocerse.
  - Colab, builds de Docker, entrenamiento y la suite completa por mi cuenta.
- **No auditado:** `CityLearn/` y `external/` en profundidad, el historial de Git en busca de secretos, ni el contenido de `data/`. El repositorio es **público**, así que el historial merece revisarse.
- **Hallazgos previos:** solo reverifiqué en el código H10, H16, H19, H20, H21, H22 y H23. El resto de H01–H18 sigue siendo evidencia de esa auditoría, hecha sobre `cb2d7c7`.
- **Pruebas que sí ejecuté:** contratos de CI 36/36, arquitectura y puertos 6/6, y selección de `test_github_readiness` 7/8.
- **Fallo sin diagnosticar:** `test_consolidate_execute_only_on_matching_plan_in_temp_copy`, uno de los 5 de la otra sesión.

Los scripts de reproducción están en `C:\Users\LENOVO~1\AppData\Local\Temp\claude\d--MADRLCitytleranflexresdr\865ad199-53fa-4aa9-acc3-c3dfb37f0edd\scratchpad\promotion_check.py` y `C:\Users\LENOVO~1\AppData\Local\Temp\claude\d--MADRLCitytleranflexresdr\865ad199-53fa-4aa9-acc3-c3dfb37f0edd\scratchpad\arch_scan.py`.

**¿Sigo como auditor y superviso la corrección de la puerta (n.º 1–3) con pruebas primero, o prefieres que antes ejecute `pip-audit`?** Yo empezaría por la puerta, porque mientras falle ningún resultado de la campaña es confiable. `pip-audit` enviaría la lista de paquetes a un servicio externo, por eso te lo pregunto. También puedo publicar este dictamen como página privada si quieres compartirlo.
