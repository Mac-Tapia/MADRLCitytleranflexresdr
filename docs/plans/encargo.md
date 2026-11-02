# Encargo para el agente implementador: campaña MADRL nueva

Fecha: 2026-11-01. Estado: listo para transferir; implementación y entrenamiento pendientes.

## Instrucción para copiar al agente

```text
Trabaja solo en D:\MADRLCitytleranflexresdr y cumple AGENTS.md.

Implementa secuencialmente este plan:
docs/plans/entrenamiento.md

Lee primero su especificación:
docs/design/entrenamiento.md

Lee también el inventario de borrado y el diagnóstico causal:
docs/audits/historicos.md

La sección 12 del diseño fija el árbol objetivo y los duplicados D-01..D-07.
No basta dibujar carpetas: inspecciona/materializa el árbol por fase, actualiza
índices/consumidores y demuestra una única fuente completa por responsabilidad.
Conserva el archivo correcto más completo, no el más grande o el más reciente.
Si las versiones tienen contenido único, intégralo y verifica cobertura antes
de eliminar clones. No confundas facades mínimos, capas distintas, formatos
derivados o datos de activos/semillas distintos con versiones redundantes.

La sección 13/T13 añade prácticas de programación y aceptación GitHub: paquete
plano uc3m instalable/portable, capas/puertos, parser/configuración únicos,
build/CI seguros, metadata real e higiene de blobs/secretos. No migres a src/
por estética. GitHub local, remoto y aceptación científica tienen estados
distintos. No afirmes Actions verde sin ejecución del mismo commit; no publiques
ni cambies protecciones de rama sin autorización. Consulta fuentes oficiales
enlazadas en esa sección.

Lee además docs/plans/renombrar_rutas.md y T14: el usuario pide
nombres simples para carpetas/archivos, sin fechas o identificadores largos.
Usa su mapa old→new antes de crear nuevas rutas y coordina movimientos de
existentes sin escritores activos. Los destinos cortos prevalecen sobre los
nombres propuestos antes; no borres identidad científica: queda en manifests.
Incluye los propios documentos del plan y las referencias entre ellos.
No renombres dependencias, entorno, raíz, estado de herramienta activo ni
campañas congeladas. No sobrescribas destino ocupado ni dejes copias _old.

La instrucción central del usuario es iniciar un entrenamiento nuevo sin usar
datos de entrenamientos anteriores ni resultados históricos. No cargues modelos,
checkpoints, replay, scalers, curvas, KPI, tablas, rankings o baselines previos,
ni siquiera como fixtures de aceptación. Puedes reutilizar código y fuentes
primarias independientes auditadas. Regenera el dataset y todos los resultados
en las raíces nuevas; no copies el dataset horario anterior. El usuario añadió
la limpieza y eliminación de los históricos locales R-01..R-07: ejecútala en
T0-A -> T1 -> T0-B, conservando solo inventario/hashes y diagnóstico mínimo.
No borres outputs entero, fuentes primarias, Word, dependencias, artefactos
nuevos o trabajo de otros agentes. No borres remotos ni reescribas Git/LFS.
No necesitas pedir otra confirmación genérica para esa lista ya autorizada;
una ruta nueva/ambigua o usada por otro proceso queda bloqueada y se informa.

Antes de cada edición u operación Git ejecuta:
powershell -ExecutionPolicy Bypass -File scripts/verify_project_context.ps1

No edites CityLearn/ ni external/. Usa adaptadores del padre e interfaces
nativas. Si una interfaz impide cumplir una puerta, informa la interfaz y el
requisito exactos; no inventes continuidad, KPI o aprendizaje. No uses fallbacks
aleatorios como entrenamiento. Todo intento nuevo usa --no-resume; si falla,
conserva su evidencia y reinicia desde cero en otro attempt_id.

Usa el entorno .venv39-citylearn-v3. No cambies stack ni instales servicios de
pago. No despliegues hardware, Modbus, MQTT o una API pública. No edites Word.
La autorización para implementar no equivale a autorizar gasto o una campaña
larga en recursos no acordados: prepara el DAG, pasa las puertas de software
y aprendizaje real y deja presupuesto medido y comandos concretos. Ejecuta
las fases largas solo dentro de los recursos autorizados por el usuario.

HAPPO tuvo un registro completed_with_salvage con NameError VecEnvWrapper.
El wrapper actual ya tiene compatibilidad; no repitas el parche por suposición.
Debes probar con HAPPO real nuevo el ciclo vectorizado, aprendizaje, reporte,
guardado, recarga y cierre, y rechazar salvage/errores como completitud.
No atribuyas la causa a OOM o falta de convergencia sin evidencia. La mezcla
49 previos +1 reanudado +50 declarados exige contadores por intento, no sumar
etiquetas ni reutilizar la trayectoria anterior.

Trabaja T0..T14 en el orden por fases del plan, mostrando RED/GREEN de los contratos nuevos y
evidencia nativa cuando corresponde. No marques un paso por existencia de
archivos. Los skip/xfail/xpass invalidan la aceptación nueva. Las pruebas que
dependen del corpus histórico van fuera del perfil nuevo y no cuentan como
aprobadas. No hagas stage global, commit o push automático.

Entrega también registry de árbol/canónicas, inventario de duplicados, prueba
de cobertura y resultado de consolidación. No borres Word con contenido único;
registra su comparación/propuesta y bloqueo hasta validación documental. Un
solo parser en training/cli.py, una lógica de campaña y una tabla de pesos;
ningún alias debe contener una segunda implementación. Los trabajos largos
esperan repository_layout_verified de T12-C, además de las demás puertas.

Entrega una matriz requisito -> archivo -> test/comando -> evidencia -> estado,
el manifiesto nuevo con hashes, un runbook y la lista explícita de bloqueos.
Separa implementation_ready_for_training de scientific_acceptance. No afirmes
144 corridas completas, superioridad ni ganador a partir de un piloto.
```

## Alcance científico que no debe perderse

- Cuatro algoritmos nativos, tres políticas; confirmación con semillas 1001..1012 y 50 episodios de 8760 pasos sobre 2023.
- Validación 2024 (8784 pasos) y prueba 2025 (8760), sin refit ni predicción futura perfecta en observaciones principales.
- HPO nuevo separado, semillas 901..903; sensibilidad de pesos con datos nuevos y presupuesto explícito.
- KPI desde trazas físicas, delta total `control - baseline`, moneda trazada, baseline nuevo y mismos servicios EV.
- Unidad estadística semilla; no edificios/horas/episodios/KPI como réplicas independientes.
- Resultados negativos y ausencia de ganador son salidas válidas si el estudio está completo y bien ejecutado.

## Primer resultado esperado del implementador

Identidad del checkout y estado de parches existentes; inventario R-01..R-07 y diagnóstico HAPPO; árbol/duplicados T12-A y contratos de retiro/aislamiento T0/T1 en RED/GREEN; luego eliminación validada y `retirement_result.json` antes del primer microentrenamiento. Continuar con T2..T13 según sus fases. No empezar lanzando el antiguo .bat/notebook ni buscando el último checkpoint.

## Entrega de esta sesión de planificación

Se entregaron esta guía, la especificación, el plan y el anexo de diagnóstico/retiro. Los módulos/configuraciones/tests nuevos todavía deben implementarse. No se ejecutó borrado ni entrenamiento al redactarlos. La fundamentación académica y sus límites están en §10 de la especificación y §7 del anexo. Los históricos solo se inspeccionaron para retiro y diagnóstico, sin incorporarlos como evidencia del entrenamiento nuevo.
