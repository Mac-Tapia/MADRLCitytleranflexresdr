# Diseño integral de modernización abierta y dirigida por especificaciones

**Fecha:** 2026-10-31  
**Estado:** propuesta para aprobación  
**Ámbito:** `D:\MADRLCitytleranflexresdr` exclusivamente  
**Decisión propuesta:** modernización incremental de un monolito modular, con arquitectura de puertos y adaptadores, Spec Kit y cadena de suministro 100 % abierta.

## 1. Intención

Transformar el proyecto doctoral MADRL–CityLearn en una plataforma científica modular, reproducible y auditable sin reescribir el sistema, interrumpir entrenamientos, alterar resultados históricos ni convertir repositorios externos en código propio. La modernización debe reducir duplicación, separar decisiones científicas de infraestructura y permitir que agentes de desarrollo trabajen sobre contratos y evidencia verificable.

## 2. Objetivos

1. Establecer una única fuente de verdad para objetivos, escenarios, tarifas, restricciones, semillas y artefactos.
2. Separar el dominio científico de CityLearn, algoritmos MADRL, almacenamiento y documentos de tesis.
3. Conservar recompensa vectorial y aplicar la escalarización como política explícita, versionada y auditable.
4. Hacer reproducible cada experimento mediante manifiestos, hashes, versiones, semillas y procedencia.
5. Adoptar Spec-Driven Development para cambios acotados y verificables.
6. Utilizar únicamente software con licencia abierta comprobable y ejecución local sin pago ni suscripción.
7. Generar tablas, figuras y afirmaciones de tesis únicamente desde evidencia experimental aceptada.
8. Mantener un flujo de agentes eficiente, con responsabilidades, entradas y salidas explícitas.

## 3. No objetivos

- No reescribir CityLearn, HARL, MAAC, MARLlib o MATD3.
- No dividir inmediatamente el proyecto en múltiples repositorios o microservicios.
- No migrar resultados históricos a la nueva política de pesos mediante simples cambios de etiquetas.
- No depender de servicios SaaS, cuentas premium, telemetría externa o almacenamiento de pago.
- No ejecutar entrenamientos extensos hasta cerrar contratos, pruebas y procedencia.
- No modificar `D:\madrl_lima` ni mezclar sus datos o historial.

## 4. Restricciones y principios constitucionales

1. **Código abierto verificable:** toda dependencia debe declarar una licencia OSI compatible. Una licencia ausente, ambigua o exclusiva para investigación bloquea su integración.
2. **Local primero:** pruebas, seguimiento, artefactos y configuración deben funcionar sin servicios externos. GitHub puede alojar el repositorio, pero no será una dependencia operativa exclusiva.
3. **Dependencias externas aisladas:** `CityLearn/` y `external/` se consumen mediante adaptadores; no reciben cambios salvo autorización explícita y registro de contribución.
4. **Una decisión, una fuente:** pesos, tarifas, restricciones y semillas se definen una vez y se proyectan hacia launchers, notebooks y documentos.
5. **Recompensa no equivale a aceptación:** costo, CO2, flexibilidad, pico, rampas, confort y restricciones EV/BESS se evalúan mediante KPI independientes.
6. **Resultados históricos inmutables:** cada resultado queda ligado a la versión exacta de dataset, código y política de recompensa que lo produjo.
7. **Fallo cerrado:** configuración incompleta, licencia desconocida, hash ausente, artefacto faltante o evidencia incongruente impiden promoción.
8. **Pruebas proporcionales al riesgo:** dominio, contratos, integración y evidencia documental tienen puertas de aceptación separadas.
9. **Sin secretos en el repositorio:** credenciales, tokens, perfiles de navegador y estados OAuth viven fuera del árbol versionado.
10. **Especificación antes del cambio:** cada modernización acotada atraviesa `Specify → Clarify → Plan → Tasks → Analyze → Implement → Converge`.

## 5. Alternativas consideradas

### A. Reestructuración total

Mover todo a paquetes nuevos, reemplazar launchers y normalizar de inmediato los submódulos. Tiene una apariencia limpia, pero amenaza la continuidad experimental y dificulta distinguir defectos nuevos de resultados históricos. Se rechaza.

### B. Modernización incremental por estrangulamiento — seleccionada

Crear contratos nuevos en `uc3m`, envolver la ejecución actual con adaptadores y migrar una capacidad por vez. Cada corte conserva compatibilidad, produce pruebas y puede revertirse sin reescribir CityLearn. Es la opción recomendada para un proyecto brownfield con evidencia doctoral activa.

### C. Mantener estructura y añadir solo documentación

Reduce riesgo inmediato, pero deja los pesos duplicados, el script de entrenamiento monolítico y la evidencia documental desacoplada. Se rechaza como solución final.

## 6. Arquitectura objetivo

Se mantiene un **monolito modular**. La separación es lógica y contractual, no una red de servicios.

```text
uc3m/
├── domain/
│   ├── objectives/          # RewardVector, ObjectivePolicy, Pareto y KPI
│   ├── scenarios/           # ScenarioDefinition, TariffPolicy, ConstraintPolicy
│   ├── experiments/         # ExperimentSpec, RunIdentity, estados y promoción
│   └── evidence/            # EvidenceManifest, ArtifactRef y procedencia
├── application/
│   ├── training/            # casos de uso de entrenamiento y reanudación
│   ├── evaluation/          # KPI, Pareto, estadística y comparación
│   └── thesis/              # proyección de evidencia aceptada hacia la tesis
├── ports/
│   ├── simulator.py         # contrato CityLearn u otro entorno
│   ├── learner.py           # contrato HAPPO/MASAC/MATD3/MAAC
│   ├── artifact_store.py    # almacenamiento local, DVC opcional
│   └── experiment_tracker.py
└── adapters/
    ├── citylearn/
    ├── algorithms/
    ├── local_artifacts/
    └── local_tracking/

configs/                     # composición validada; sin lógica duplicada
specs/                       # especificaciones Spec Kit por corte
tests/
├── unit/
├── contract/
├── integration/
└── acceptance/
docs/research/               # registro de artículos, tesis, repos y licencias
tools/skills/                # skills locales revisados, cada uno con SKILL.md
```

No se moverá inicialmente el paquete `uc3m/` a un diseño `src/`; el beneficio no compensa el riesgo durante la primera fase. La reorganización interna se hará detrás de fachadas compatibles.

## 7. Contratos científicos

### 7.1 Recompensa vectorial

La interfaz canónica será conceptualmente:

```text
RewardVector(flexibility, co2_emissions, energy_cost)
```

La política de escalarización será independiente:

```text
ObjectivePolicy(
  E1 = [0.60, 0.15, 0.25],
  E2 = [0.25, 0.60, 0.15],
  E3 = [0.15, 0.25, 0.60]
)
```

Las ponderaciones suman uno, cada objetivo ocupa una vez cada nivel jerárquico y el objetivo principal tiene mayoría estricta. Esto constituye una jerarquía compensatoria; no se denominará lexicográfica ni preemptiva.

### 7.2 Separación causal

`ObjectivePolicy`, `TariffPolicy` y `ConstraintPolicy` serán objetos distintos. Un experimento que cambie pesos y tarifa se etiquetará como escenario compuesto. Un estudio causal de pesos mantendrá constantes tarifa, dataset, restricciones, horizonte y semillas.

### 7.3 Aceptación multiobjetivo

La selección no utilizará únicamente recompensa acumulada. Debe incluir, como mínimo:

- costo energético;
- emisiones de CO2;
- pico y rampas;
- factor de carga;
- autoconsumo fotovoltaico;
- cumplimiento EV/BESS;
- hipervolumen, cobertura y dispersión del frente de Pareto;
- intervalos o pruebas estadísticas multisemilla.

## 8. Cadena de suministro abierta

### Admitidos como dependencias o herramientas locales

- Spec Kit — MIT.
- MO-Gymnasium — MIT.
- MORL-Baselines — MIT, detrás de un adaptador y sin obligación de usar Weights & Biases.
- Hydra/OmegaConf — MIT, para composición de configuración.
- MLflow — Apache-2.0, solo con backend local de archivos o SQLite.
- DVC — Apache-2.0, solo con remoto local o almacenamiento abierto autogestionado.
- Optuna — MIT, con SQLite local.
- Zotero — AGPL, mediante API local para bibliografía.
- pytest, Ruff y Pyright — herramientas abiertas de calidad.

### Referencia científica, no integración de código

- C-MORL: artículo relevante, pero repositorio sin licencia declarada.
- SustainGym: útil como benchmark conceptual; su licencia CC BY no se tratará automáticamente como licencia de software compatible.
- Repositorios educativos o recientes sin pruebas, mantenimiento o licencia clara.

### Excluidos

- Scite, Weights & Biases gestionado, NotebookLM, Google Drive como dependencia del pipeline, Notion y cualquier servicio que exija pago, suscripción o autenticación cerrada.
- Skills descargados sin revisión de licencia, instrucciones, permisos y procedencia.

## 9. Spec Kit y partición de especificaciones

La modernización se dividirá en cortes independientes:

1. **SPEC-000 — Constitución y línea base:** reglas, compatibilidad y estado inicial reproducible.
2. **SPEC-001 — Cadena abierta y procedencia:** inventario SPDX, SBOM, secretos y registro de repositorios.
3. **SPEC-002 — Política multiobjetivo única:** recompensa vectorial, pesos, tarifa y restricciones separadas.
4. **SPEC-003 — Orquestación modular:** extracción gradual de `citylearn_v3_training_common.py` detrás de puertos.
5. **SPEC-004 — Manifiestos de ejecución:** identidad, hashes, semillas, artefactos y estados.
6. **SPEC-005 — Evaluación científica:** KPI independientes, Pareto, sensibilidad y multisemilla.
7. **SPEC-006 — Evidencia de tesis:** tablas, figuras y citas generadas desde manifiestos aceptados.
8. **SPEC-007 — Agentes y skills locales:** roles, permisos, contratos, pruebas y registro de capacidades.
9. **SPEC-008 — Artefactos y datos:** DVC/local store, retención y separación de Git.
10. **SPEC-009 — Levantamiento de observaciones del jurado:** trazabilidad observación–evidencia–corrección–prueba, coherencia estadística, validez externa, HAPPO, UC3M, seguridad, privacidad y reproducibilidad.

Cada especificación deberá tener `spec.md`, `plan.md`, `tasks.md`, contratos y lista de verificación. Ninguna especificación puede declarar éxito mediante un único `return_code=0` o por convergencia numérica sin validar sus propios criterios.

SPEC-009 distinguirá obligatoriamente correcciones documentales, validaciones analíticas y experimentos nuevos. Una campaña multisemilla o KPI-gains faltantes no podrán cerrarse mediante redacción; permanecerán `pending_experiment` hasta producir artefactos verificables.

## 10. Flujo de agentes

Los agentes trabajarán sobre artefactos compartidos, no sobre prompts aislados:

```text
Investigación → Especificación → Arquitectura → Implementación → Verificación → Evidencia
```

- **Investigación:** entrega DOI, repositorio, licencia, límites y aplicabilidad.
- **Especificación:** convierte objetivos en requisitos y criterios observables.
- **Arquitectura:** define contratos y compatibilidad; no modifica resultados.
- **Implementación:** cambia solo archivos asignados y produce pruebas.
- **Verificación:** reproduce pruebas y rechaza omisiones, skips o evidencia incompleta.
- **Evidencia:** genera manifiestos y material de tesis desde resultados aceptados.

Los skills específicos vivirán únicamente en `tools/skills/<nombre>/SKILL.md`; cada skill declarará entradas, salidas, archivos permitidos, comandos de verificación y licencia. Los servidores MCP locales se separarán de los skills y mantendrán credenciales fuera del repositorio.

## 11. Fases y puertas de salida

### Fase 0 — Línea base y custodia

- Capturar inventario de cambios sin limpiar trabajo del usuario.
- Identificar resultados activos e históricos.
- Congelar hashes del dataset, política y evidencia canónica.
- Emitir inventario de licencias y secretos potenciales.

**Salida:** línea base revisable; ningún archivo del usuario perdido.

### Fase 1 — Constitución y cadena abierta

- Inicializar Spec Kit en una rama o worktree revisable.
- Crear constitución y registro de dependencias.
- Añadir puerta SPDX/SBOM y prohibición de servicios cerrados.
- Separar estado de Google Drive/NotebookLM del diseño futuro, sin borrar evidencia existente.

**Salida:** cero dependencia nueva sin licencia; ejecución local documentada.

### Fase 2 — Fuente única multiobjetivo

- Introducir contratos de dominio.
- Separar pesos, tarifa y restricciones.
- Adaptar CityLearn sin reescribirlo.
- Generar configuraciones y documentación desde la fuente canónica.

**Salida:** ninguna ponderación activa duplicada fuera de fixtures o historia explícita.

### Fase 3 — Orquestación modular

- Descomponer el script común por responsabilidades: configuración, construcción de entorno, backend, checkpoint, telemetría y artefactos.
- Mantener fachadas y argumentos actuales durante la migración.

**Salida:** cada módulo tiene contrato y prueba; launchers existentes siguen funcionando.

### Fase 4 — Reproducibilidad y artefactos

- Crear `RunIdentity` y `EvidenceManifest`.
- Registrar commit, submódulos, dataset, política, semillas y entorno.
- Mover artefactos grandes fuera del seguimiento Git mediante almacenamiento local abierto.

**Salida:** cada resultado aceptado puede reconstruirse y verificarse por hash.

### Fase 5 — Evaluación científica

- Ejecutar sensibilidad de pesos y separar escenarios compuestos.
- Incorporar Pareto, multisemilla y comparación contra baselines.
- Validar los cuatro algoritmos y tres escenarios con puertas independientes.

**Salida:** inferencias estadísticas y conclusiones limitadas a la evidencia ejecutada.

### Fase 6 — Tesis y automatización de evidencia

- Eliminar contradicciones entre §3.1.3, metodología, resultados y bibliografía.
- Generar tablas y figuras desde manifiestos aceptados.
- Mantener exactamente los documentos canónicos definidos por el proyecto.

**Salida:** ninguna cifra o peso de tesis sin procedencia verificable.

### Fase 7 — Skills y MCP locales

- Migrar los skills heredados a `tools/skills/`.
- Separar MCP de skills y reducir datos de navegador dentro del árbol.
- Añadir pruebas contractuales y lista de permisos por capacidad.

**Salida:** cada capacidad tiene dueño, licencia, alcance y prueba; no existen servicios cerrados en el flujo requerido.

## 12. Verificación y definición de terminado

La modernización solo se considera terminada cuando:

1. La suite de dominio, contratos e integración pasa sin skips críticos.
2. Las 12 combinaciones algoritmo–escenario construyen y validan su configuración.
3. Al menos una campaña multisemilla completa produce manifiestos reproducibles.
4. Los pesos activos aparecen en una única fuente y coinciden con código, configuración y tesis.
5. Los resultados históricos conservan su política original.
6. La evaluación separa recompensa, KPI físicos, KPI económicos, CO2 y restricciones.
7. Todos los componentes requeridos poseen licencia abierta verificada.
8. No existen credenciales ni perfiles de navegador versionados.
9. Los artefactos grandes tienen hash, procedencia y almacenamiento reproducible fuera del historial principal de Git.
10. La tesis se regenera desde evidencia aceptada y supera revisión visual y bibliográfica.

## 13. Riesgos y mitigación

- **Árbol de trabajo sucio:** usar cortes pequeños; no ejecutar limpiezas masivas ni inicialización forzada.
- **Deriva de resultados:** versionar políticas y bloquear la reinterpretación de runs antiguos.
- **Submódulos divergentes:** fijar commits y documentar cualquier parche local.
- **Dependencias incompatibles con Python 3.9:** evaluar en entornos separados antes de promoverlas.
- **Sobrecarga de herramientas:** adoptar una herramienta por problema; no incorporar MLflow, DVC, Hydra y Optuna simultáneamente sin necesidad demostrada.
- **Automatización documental peligrosa:** respaldar, reabrir, renderizar y comparar cada DOCX antes de aceptación.

## 14. Trazabilidad de los hallazgos anteriores

Esta matriz integra los diagnósticos, búsquedas científicas y verificaciones locales efectuadas antes de este diseño. Un hallazgo no se considera atendido hasta cumplir la evidencia indicada.

| Hallazgo previo | Decisión incorporada | Especificación responsable | Evidencia de cierre |
|---|---|---|---|
| E1, E2 y E3 deben usar respectivamente `[0.60, 0.15, 0.25]`, `[0.25, 0.60, 0.15]` y `[0.15, 0.25, 0.60]`. | `ObjectivePolicy` canónica y versionada. | SPEC-002 | Pruebas de suma, mayoría estricta, balance cíclico y coincidencia de configuraciones. |
| No existe sustento universal para exigir un peso mayor o igual que 0.70. | Los valores exactos se presentan como decisión metodológica y se someten a sensibilidad. | SPEC-005 | Barrido de pesos, Pareto y estabilidad multisemilla. |
| La suma ponderada jerárquica no es optimización lexicográfica. | Terminología `compensatory_hierarchical_weighted_sum`; se prohíbe etiquetarla como lexicográfica. | SPEC-002 y SPEC-006 | Contrato de metadatos y revisión de §3.1.3. |
| E1–E3 cambian pesos y también señales tarifarias; esto confunde la atribución causal. | Separación de `ObjectivePolicy` y `TariffPolicy`; escenarios compuestos identificados. | SPEC-002 y SPEC-005 | Experimento de pesos con tarifa constante y experimento compuesto claramente rotulado. |
| EV y BESS agregan términos fuera del simplex de tres objetivos. | Telemetría separa contribuciones de ejes y términos de servicio/restricción. | SPEC-002 | Suma auditable por paso y participación efectiva de cada término. |
| La recompensa agregada no sustituye KPI físicos, económicos y ambientales. | Puerta de aceptación independiente para costo, CO2, pico, rampas, factor de carga, PV y EV/BESS. | SPEC-005 | Informe de KPI y Pareto con procedencia. |
| Hay resultados de 50 episodios producidos con pesos anteriores. | Runs históricos inmutables y asociados a `reward_policy_version`; no se reetiquetan. | SPEC-004 y SPEC-006 | Manifiesto histórico y comprobación de política original. |
| La nueva matriz tiene pruebas unitarias y validación integrada HAPPO E1–E3, pero no una campaña completa 4×3 multisemilla. | El estado se declara parcial hasta completar la campaña requerida. | SPEC-005 | 12 tratamientos válidos, semillas declaradas y aceptación estadística. |
| El script común de entrenamiento supera 9 000 líneas y concentra responsabilidades. | Extracción incremental detrás de fachadas compatibles. | SPEC-003 | Módulos pequeños, pruebas por contrato y launchers actuales todavía operativos. |
| `uc3m` declara modularidad, pero la ejecución principal permanece dentro de scripts CityLearn. | El dominio y casos de uso pasan a `uc3m`; CityLearn queda como adaptador. | SPEC-003 | Grafo de dependencias sin importación inversa del dominio hacia CityLearn. |
| Pesos y escenarios están duplicados en Python, JSON, YAML, notebooks, decisiones y tesis. | Una fuente canónica genera proyecciones derivadas. | SPEC-002 y SPEC-006 | Búsqueda automática sin duplicados activos fuera de fixtures e historia. |
| CI verifica solo una fracción del dominio; Pyright silencia diagnósticos relevantes. | Matriz local de pruebas y endurecimiento gradual de tipos. | SPEC-000 y SPEC-003 | CI local reproducible, puertas separadas y presupuesto de errores decreciente. |
| Git, `outputs/`, entornos y cachés acumulan varios gigabytes. | Código y manifiestos permanecen en Git; artefactos usan almacén abierto local con hashes. | SPEC-008 | Inventario, política de retención y restauración verificada. |
| `agent-skills/` contradice la política que exige `tools/skills/`. | Migración controlada a skills locales con `SKILL.md`, licencia y pruebas. | SPEC-007 | Registro único de skills y ausencia de duplicados globales activos. |
| Google Drive MCP y NotebookLM MCP dependen de servicios cerrados; NotebookLM mantiene un perfil de navegador grande. | Se excluyen del flujo requerido y se aíslan credenciales/estado fuera del repositorio. | SPEC-001 y SPEC-007 | Escaneo de secretos y ejecución completa sin esos servicios. |
| Ya existen HARL, MAAC, MARLlib, MATD3 y otros submódulos. | No se clonan implementaciones equivalentes; se reutilizan mediante adaptadores y commits fijados. | SPEC-001 y SPEC-003 | Registro de submódulos, licencia, commit y propósito sin duplicados. |
| MO-Gymnasium y MORL-Baselines ofrecen contratos y métricas MORL maduras. | Se evalúan como dependencias abiertas fijadas, no como copias modificadas. | SPEC-001, SPEC-002 y SPEC-005 | Spike de compatibilidad, licencia, lockfile y prueba de adaptador. |
| C-MORL es relevante pero carece de licencia declarada. | Solo referencia bibliográfica; queda prohibida la copia de código. | SPEC-001 | Registro de rechazo con URL y causa. |
| SustainGym aporta robustez energética, pero su licencia no debe asumirse automáticamente como licencia de software compatible. | Uso conceptual o benchmark separado tras revisión jurídica de licencia; no dependencia central. | SPEC-001 y SPEC-005 | Registro de licencia y decisión explícita antes de cualquier uso de código. |
| Spec Kit recomienda adopción brownfield mediante cambios acotados. | Una especificación por corte, con convergencia y compatibilidad verificadas. | SPEC-000 a SPEC-008 | Artefactos `spec.md`, `plan.md`, `tasks.md` y checklist por corte. |
| La tesis debe concentrar la coordinación multiobjetivo en §3.1.3 sin redundancia. | La evidencia generada actualiza esa sección y elimina contradicciones laterales sin reinterpretar resultados. | SPEC-006 | Auditoría DOCX, render visual, bibliografía APA y búsqueda de pesos obsoletos. |

## 15. Sustento científico y técnico

La frontera propuesta sigue el principio de ocultamiento de información: los módulos se separan por decisiones susceptibles de cambiar, no solo por etapas de procesamiento (Parnas, 1972). La separación entre datos, entrenamiento, registro de modelos, despliegue y seguimiento corresponde a la arquitectura MLOps sintetizada por Kreuzberger et al. (2023).

Para el dominio científico, MO-Gymnasium y MORL-Baselines proporcionan contratos vectoriales y benchmarking reproducible de MORL (Felten et al., 2023). C-MORL muestra la utilidad de evaluar frentes de Pareto en lugar de limitarse a pocos vectores fijos (Liu et al., 2025). SustainGym y la tesis de Koruturk sustentan pruebas de robustez, seguridad y coordinación en sistemas energéticos (Yeh et al., 2023; Koruturk, 2026). La tesis de Jiménez Perdomo y González Escobar (2024) refuerza la evaluación separada de objetivos energéticos, económicos y ambientales.

## 16. Referencias

- Felten, F., Alegre, L. N., Nowé, A., Bazzan, A. L. C., Talbi, E.-G., Danoy, G., & da Silva, B. C. (2023). *A toolkit for reliable benchmarking and research in multi-objective reinforcement learning*. Advances in Neural Information Processing Systems, 36. https://github.com/LucasAlegre/morl-baselines
- Jiménez Perdomo, J. E., & González Escobar, R. S. (2024). *Modelo multiobjetivo para la gestión de energía en generadores fotovoltaicos conectados en redes de distribución considerando indicadores técnicos, económicos y ambientales* [Trabajo de grado, Universidad Distrital Francisco José de Caldas]. https://repository.udistrital.edu.co/items/9f268437-3ef0-4af5-9a55-404c484bbf63
- Koruturk, M. (2026). *Reinforcement learning benchmarking for sustainable energy systems: Perturbation robustness, safety constraints, and multi-agent coordination* [Master's thesis, Virginia Tech]. https://hdl.handle.net/10919/143123
- Kreuzberger, D., Kühl, N., & Hirschl, S. (2023). Machine learning operations (MLOps): Overview, definition, and architecture. *IEEE Access, 11*, 31866–31879. https://doi.org/10.1109/ACCESS.2023.3262138
- Liu, R., Pan, Y., Xu, L., Song, L., You, P., Chen, Y., & Bian, J. (2025). Efficient discovery of Pareto front for multi-objective reinforcement learning. *The Thirteenth International Conference on Learning Representations*. https://proceedings.iclr.cc/paper_files/paper/2025/hash/adb77ecc8ba1c2d3135c86a46b8f2496-Abstract-Conference.html
- Parnas, D. L. (1972). On the criteria to be used in decomposing systems into modules. *Communications of the ACM, 15*(12), 1053–1058. https://doi.org/10.1145/361598.361623
- Yeh, C., Li, V., Datta, R., Arroyo, J., Christianson, N., Zhang, C., Chen, Y., Hosseini, M. M., Golmohammadi, A., Shi, Y., Yue, Y., & Wierman, A. (2023). SustainGym: Reinforcement learning environments for sustainable energy systems. *Advances in Neural Information Processing Systems, 36*. https://papers.neurips.cc/paper_files/paper/2023/hash/ba74855789913e5ed36f87288af79e5b-Abstract-Datasets_and_Benchmarks.html

