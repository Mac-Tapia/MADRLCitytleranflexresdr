# I13: implementación y revisión semántica, 2 de noviembre de 2026

Seguimiento del plan integrado solicitado. Se conserva el contrato v1. El plan
original es un corte histórico; este documento registra hallazgos adicionales y
su implementación, sin reescribir aquella auditoría ni declarar cierre global.

Root es el único integrador canónico por decisión expresa del usuario. Los
implementadores prepararon cambios en una copia aislada y un revisor distinto
contrastó código, consumidores y regresiones. Se comparó el SHA de cada fuente
canónica con el inventario inicial antes de reemplazarla atómicamente. Los
originales se conservaron en el registro local y los deltas en los parches de
esta carpeta. Las dependencias mantienen exclusivamente los cuatro cambios ya
autorizados; este lote no modifica dependencias, datos reales ni Word.

## Hallazgos de L1

La revisión semántica por agente cubrió 122 archivos propios de `uc3m/` y
`configs/`, 19.384 líneas en el corte inicial. Su inventario SHA está en
`.superpowers/sdd/remediacion_integrada/i13_stage/seed_manifest.json`, agregado
`91ec64bf001878b484b4f31e49285d84d8151f243c879602ddb3b3bb1b168269`.
No es una lectura humana ni una revisión semántica de los 773 archivos del
alcance general. La revisión de L2 sigue por archivo, con pendientes explícitos.

| IDs | Implementación | Estado y evidencia |
|---|---|---|
| R001, R004, R005 | Listado S3 completo validado antes de escribir; clasificación de fuentes tras normalizar componentes; rechazo de enlaces y junctions en construcción y hashing. | Integrados. `integration_ab.json`, `I13_ab.patch`; pruebas canónicas A/B: 160 aprobadas, sin omisiones. |
| R016, R017 | Clima falla ante ausencia de proveedores; sintético exige opción y semilla, caché/procedencia separadas e inelegibilidad; temperatura negativa válida preservada. | Integrados. Las pruebas usan respuestas controladas y archivos temporales; no acreditan proveedores reales. |
| R011, R012, R019 | Kendall W con empates; AHP positivo/recíproco; efecto Wilcoxon con signo y exclusión de ceros. | Integrados; contraste con NumPy/SciPy reales. No son resultados de aprendices. |
| R013, R014, R015 | C3 distingue ratio real de kWh ilustrativos; C4 no cuenta episodios como semillas; IDs de episodios y cobertura preservados; C5 invariante a traslaciones. | Integrados. Revisión detectó y cerró pérdida de IDs y metadata de orientación incoherente. Una semilla publica incertidumbre no estimable. |
| R002, R003 | HARL opcional con un entorno real, ejes del vector y seis retornos; observaciones/acciones con padding explícito y estado compartido concatenado. PettingZoo declara Parallel API y transmite seed/options y causas de final. | Integrados; validación canónica en curso. La concatenación no prueba suficiencia Markoviana ni entrenamiento completo. |
| R006 | RBC desempaqueta reset, respeta término/truncación y horizonte, conserva nombres de KPIs distritales y cierra en finally. | Integrado; la pérdida de nombres fue reproducida con CityLearn real antes de corregirla. |
| R007 | Liquidación distrital suma productos por edificio; PSD distrital no disponible si las tarifas son heterogéneas. | Integrado; contraejemplo analítico con dos tarifas/intensidades. No cambia la recompensa. |
| R018 | KPI auxiliar deja ausentes comparaciones, arbitraje, humedad y servicio durante cortes sin evidencia. Conserva empeoramientos negativos; USD requiere moneda declarada o estimación explícita etiquetada. | Integrado. HPHI de recompensa permanece proxy auxiliar; `scientific_eligible=false`, también en comparación/exportación. |
| R009, R010 | Freeze con lock OS, publicación atómica por archivo y recuperación del huérfano idéntico; delivery resuelve y copia análisis registrado aunque se omita el argumento. | Integrados. Pruebas canónicas E: 57 aprobadas, sin omisiones. Revisión adicional reprodujo y corrigió shadowing del registro con stages no vacío. |
| R008 | Gate exige colección independiente y multiset exacto de IDs; rechaza evidencia JUnit aislada. | En revisión. Se reprodujeron vías de descubrimiento filtrado por CLI/configuración; no integrar hasta cerrarlas y revalidar. |

Los recibos están en `data/maintenance/integracion/c20261101i01/I13/`.
`canonical_ab01.xml` contiene 160 casos y `canonical_e01.xml` 57; son conjuntos
con solapamientos y no se suman como total independiente. `canonical_c01.xml`
todavía no se declara aprobado. Las copias aisladas conservan cada RED/GREEN.

## Contratos nativos y resultados pendientes

El perfil anterior `fresh_profile_20261102T112634787Z` terminó con 632 casos:
628 aprobados, cuatro fallos, cero errores y cero omisiones. Los cuatro fallos
comparaban referencias sin catálogo con políticas que sí lo tenían: E1 RTP
heredado frente a tarifa flat del catálogo. El auxiliar canónico ahora transmite
el catálogo y lo incluye en la clave de caché; se mantiene la igualdad estricta
de hashes y se requiere otra ejecución sobre el corte integrado.

La regresión HARL opcional invoca `OnPolicyBaseRunner.warmup` y ambos buffers
reales sobre CityLearn, incluyendo final y auto-reset. Una primera propuesta
seguía siendo incompatible y falló en el consumidor real; la revisión obligó a
corregir ejes y aridad. Esto no sustituye la prueba de los cuatro aprendices.

El KPI auxiliar conserva `None` y estados en el payload. `metric_values()` sirve
para logging escalar. Las constantes modeladas no se presentan como medidas;
el SoC no demuestra resiliencia y un ahorro no separa arbitraje. El informe
físico canónico y la aceptación científica siguen siendo contratos separados.

## Incidente de la prueba S3

Un fixture negativo anterior al guard creó por error un archivo externo de dos
bytes y su carpeta. Se detuvo el lote, se preservaron contenido y recibo, y el
usuario autorizó retirar exclusivamente ese archivo y la carpeta vacía tras
verificar identidad y ausencia de enlaces. La limpieza se completó; no fue una
limpieza general. Evidencia: `I13/incident_s3/{incident.json,cleanup.json}`.

Ahora un audit hook acotado por ContextVar intercepta aperturas de escritura y
mkdir antes del sistema operativo. Una violación lanza RuntimeError propio y no
puede satisfacer los errores esperados del adaptador. Los tests del guard usan
únicamente destinos de su temporal. No se declara protección frente a cualquier
extensión C, hardlink o intercambio hostil entre validación y syscall.

## L2 y límites de cierre

La revisión adicional de scripts/tools tiene 239 archivos inventariados y aún
está en curso. Su reporte progresivo mantiene filas no leídas como pendientes;
hashing o inventario no equivalen a revisión semántica. Los hallazgos nuevos de
rutas de mantenimiento, textos Word fijados y emparejamiento de semillas se
incorporarán a la remediación con reproducción y revisión independientes.

La aceptación científica y operacional sigue falsa. No se ha ejecutado campaña
anual, multisemilla confirmatoria, Colab real, edición Word ni operación física.

## Fundamento

La [maestría de Costea](https://webthesis.biblio.polito.it/40396/) y la
[tesis doctoral de Charbonnier](https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5)
contextualizan la evaluación MARL energética; sus fichas institucionales se
verificaron en web. [Pineau et al., JMLR](https://www.jmlr.org/papers/v22/20-303.html)
fundamentan la trazabilidad reproducible. La
[documentación primaria de PettingZoo](https://pettingzoo.farama.org/api/parallel/)
define la API simultánea. Ninguna fuente valida los pesos locales ni convierte
estas regresiones en beneficios experimentales. Los detalles bibliográficos,
indexación comprobada y límites de acceso constan en [fundamento.md](fundamento.md).
