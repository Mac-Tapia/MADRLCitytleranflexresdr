# SPEC-015 — Módulo 3: contrato de algoritmos y recursos

**Estado:** `implemented` (FR-015.1 a FR-015.7, 2026-11-06; FR-015.3 ampliado a los 4 por D-M3-5). Sin aceptación científica.
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`
**Estado conciliado:** [STATUS](../STATUS.md) · **Hoja de ruta:** [hoja_ruta_modulos.md](../../docs/plans/hoja_ruta_modulos.md)
**Revisión:** 2026-11-06

## Propósito

Dejar los cuatro algoritmos listos para entrenar sobre `iquitos_v5` con su capacidad nativa y con requisitos de recursos que correspondan al dataset activo. No entrena: el entrenamiento es el módulo 8 (regla del propietario del 2026-11-06).

## Por qué hace falta

Los requisitos de `configs/algorithms/native.yaml` son cifras fijas calculadas con las dimensiones de `iquitos_v1`, que tenía 1 850 vehículos eléctricos. Nadie las recalculó al cambiar de dataset. Medidas con los entornos reales de entrenamiento:

| Medida | `iquitos_v1` | `iquitos_v5` |
|---|---|---|
| MASAC: observación, estado, acciones | 357, 1 652, 89 | 37, 371, 9 |
| MASAC: búfer nativo de 50 episodios | 65,3 GiB | 8,1 GiB |
| MASAC: crítico, lote nativo de 32 episodios, `rnn` 128 / 256 | 74,7 / 103,3 GiB | 35,3 / 63,9 GiB |
| MATD3: observación, observación conjunta, acción | 357, 6 069, 44 | 37, 629, 4 |
| MATD3: búfer de 744 600 transiciones | 35,8 GiB | 3,7 GiB |

Con las cifras de `v1`, el guardián rechazaría MASAC en cualquier entorno disponible y MATD3 en este equipo. La medición sobre `iquitos_v1` reproduce exactamente las cifras declaradas, lo que valida el método.

## Decisiones

- **D-M3-1 (propietario, 2026-11-06): MASAC conserva su capacidad nativa.** Sustituye su elección anterior del mismo día de reformular el búfer, que se tomó sobre las cifras de `v1`. Además, el búfer muestrea con reemplazo (`external/MARL/src/common/replay_buffer.py:58`): reducirlo no bajaría la VRAM, que la fija el lote del crítico.
- **D-M3-2: requisitos por candidato.** El requisito de VRAM de MASAC depende de `rnn_hidden_dim` (39 GiB con 128, 71 GiB con 256); el guardián usa el del intento y rechaza un candidato sin requisito declarado. Una fase reserva el mayor, porque puede ejecutar cualquiera; leerlo como 0 habría planificado unos 20 trabajadores en una GPU de 80 GB en lugar de 1. Con el margen, ningún candidato cabe en una A100 de 40 GB (37,25 GiB): MASAC necesita la de 80 GB.
- **D-M3-4 (propietario, 2026-11-06): los ajustes de Colab no cambian.** La campaña oficial de 50 episodios y su plan de recursos en Colab ya están ajustados y solo pueden mejorarse. Por eso la regla D-M3-3 se aplica a MASAC, que antes no podía ejecutarse en ningún entorno, y las reservas de HAPPO, MAAC (8 GiB) y MATD3 (40 GiB) se conservan: fijan el paralelismo de cada fase. Bajar MATD3 a 8 GiB habría llevado la fase 2 de 2 a unos 10 trabajadores. Una prueba exige que cada reserva cubra la estimación del dataset activo. Las pruebas locales no modifican esos ajustes.
- **D04 (propietario, 2026-11-06): el costo de la recompensa es la factura con cargo por potencia.** En `iquitos_v5` el costo de energía y el CO2 horarios tienen correlación 1,000, así que E2 y E3 enseñarían lo mismo. Se implementa en el módulo 3b junto con la reconstrucción `iquitos_v6`, que lleva la tarifa de potencia al dataset ([hoja de ruta](../../docs/plans/hoja_ruta_modulos.md)).
- **D-M3-5 (propietario, 2026-11-06): los 4 MADRL conservan la capacidad nativa de sus autores.** La comparación con el código de `external/` dio:

  | Algoritmo | Autor | Proyecto |
  |---|---|---|
  | HAPPO (`HARL/.../happo.yaml`) | `ppo_epoch` 5, `critic_epoch` 5, 1 minilote, ancho 128, 20 entornos × 200 pasos | igual; ancho 128/256; 1 entorno × 8 760 pasos |
  | MASAC (`MARL/.../arguments.py`) | lote del crítico 32 episodios, 1 actualización, `rnn` 64, búfer 5 000 episodios | igual; `rnn` 128/256; búfer 50, que guarda toda la etapa más larga |
  | MATD3 (`off-policy/.../config.py`) | búfer 5 000, lote 32, ancho 64 | búfer 43 800 por política, lote 256, ancho 128/256 |
  | MAAC (`MAAC/main.py`) | búfer 10⁶, lote 1 024, 4 actualizaciones cada 100 pasos, 12 entornos | **antes:** búfer 43 800, lote 256, 1 actualización por paso; **ahora:** igual que el autor, con 1 entorno |

  MAAC era el único por debajo de su autor y pasa a su esquema (elección del propietario). Su búfer queda acotado sin pérdida a la corrida: 50 × 8 760 + 8 760 = 446 760 transiciones, unos 2,3 GiB sobre `iquitos_v5`, dentro de su reserva de 8 GiB. Hay **una sola reducción**, declarada y elegida por el propietario: 1 entorno en paralelo en HAPPO y MAAC, frente a 20 y 12 del autor. Cada copia es el distrito entero y el plan de Colab no cambia. Con episodios de 8 760 pasos, HAPPO reúne más muestras por actualización que su autor (8 760 frente a 4 000). Ningún algoritmo declara `phase_buffer`: la memoria insuficiente rechaza la fase y nunca encoge un búfer.
- **D-M3-6 (propietario, 2026-11-06): D03, los 4 conservan su interfaz de acción nativa, con máscaras.**
  - **Interfaces:** HAPPO y MATD3 actúan en continuo sobre todos sus equipos a la vez. MASAC y MAAC actúan en discreto en modo `axis`: un equipo por paso, a −1, 0 o +1.
  - **Defecto medido en `iquitos_v5`:** las acciones se rellenan hasta 4 dimensiones, pero 16 edificios tienen solo 2 equipos, batería y lavadora. En ellos, 2 de las 4 salidas continuas no actúan, y 4 de las 9 acciones discretas mueven equipos que no existen y equivalen a no hacer nada.
  - **Lo que fija la decisión:**
    - ningún agente puede elegir un equipo que su edificio no tiene;
    - se registra por backend el mapa acción → equipo (`D_i^(b)` de la tupla);
    - la diferencia entre continuo y discreto se declara como confusión;
    - la tesis compara cada algoritmo con su interfaz nativa.
  - **Coherencia con D-M3-5:** las acciones pertenecen a la operación de cada equipo, un equipo por acción y no agrupados (propietario, 2026-11-06; SPEC-016 D-V6-13).
- **D-M3-7 (propietario, 2026-11-07): los 4 MADRL compiten con las mismas acciones, observaciones, dataset y función de recompensa.** Sustituye la interfaz nativa de D-M3-6 en lo que respecta a la forma de la acción. El proyecto selecciona el mejor MADRL, así que la comparación no puede depender de la interfaz.
  - **Acciones:**
    - los 4 actúan sobre la misma rejilla de niveles por equipo;
    - MASAC y MAAC eligen un nivel;
    - HAPPO y MATD3 dan un valor continuo que el entorno redondea al nivel más cercano;
    - el mapa acción → equipo y las máscaras de D-M3-6 se mantienen.
  - **Iguales para los 4:** observaciones (`O_i` y estado global de la capa v3), dataset y KPI de evaluación.
  - **Recompensa:** misma función y pesos de la capa v3. MASAC la recibe sumada para el equipo, porque su algoritmo de tipo QMIX aprende un valor de equipo; los demás la reciben por agente. Se declara. Confirma P-017-1.
  - **Niveles de la rejilla (P-M3-1, elegido bajo la delegación del propietario del 2026-11-07, «haz lo adecuado»):** 11 niveles, de −1 a +1 cada 0,2.
  - **Cabeza de acción de MASAC y MAAC (P-M3-2, elegida bajo la misma delegación):** con varios equipos por edificio, el modo `axis` de MASAC y MAAC (un equipo por paso) no puede fijar un nivel en cada equipo a la vez, y una elección conjunta es inviable (11^28 combinaciones en B06). Se usa una salida discreta por equipo (multi-discreta), lo que cambia la cabeza de acción de sus implementaciones originales; el resto del algoritmo queda nativo. Se declara como desviación de D-M3-5.
- **D-M3-8 (propietario, 2026-11-07): en `iquitos_v6`, MASAC busca solo `rnn_hidden_dim` 128.** Con la observación agregada por clase (SPEC-016 D-V6-49: 34 valores por agente, estado 548, 87 acciones por eje), su crítico sobre 32 episodios de 8 760 h necesita 52 GiB de VRAM con 128 y 84 GiB con 256 (53 GiB con 128 tras sumar las 3 observaciones de la factura de D-V6-50: 37 valores por agente, estado 599), por encima de los 74,5 GiB de una GPU de 80 GB. Se conserva la capacidad nativa del autor (crítico, búfer y lote) y se restringe su rejilla (`hyperparameter_grid_override` en `configs/algorithms/native.yaml`): 4 configuraciones en lugar de 8, 252 tratamientos de HPO en lugar de 288. Se declara que el espacio de búsqueda de MASAC es más estrecho que el de los otros 3. Se recalcula tras la rejilla común de D-M3-7.
- **D-M3-3: regla del requisito.** `requisito = max(piso, techo(1,10 × estimación))`. El margen de 10 % reproduce el que tenían las cifras anteriores (72 frente a 65,3 GiB). El piso es de 8 GiB de RAM y 4 GiB de VRAM, el ya declarado para HAPPO y MAAC, que no tienen estimador. Es regla de diseño, no una medida.

## Requisitos funcionales

- **FR-015.1** — Requisitos ligados al dataset activo: una prueba mide las dimensiones de MASAC y MATD3 con sus entornos reales sobre el split `train_2023` de la campaña configurada, calcula las estimaciones con las funciones del proyecto y exige que MASAC cumpla D-M3-3 exactamente y que las demás reservas cubran su estimación. Un cambio de dataset que deje cifras viejas hace fallar la puerta.
- **FR-015.2** — Requisito por candidato: `runtime_requirements` de MASAC declara la VRAM por `rnn_hidden_dim` para cada valor de la rejilla de HPO. El guardián toma el del argumento nativo del intento; un valor sin requisito declarado se rechaza, nunca se aprueba por omisión.
- **FR-015.3** — Capacidad nativa de los 4 (D-M3-5), verificada por `tests/fresh_training/test_author_capacity.py`. La prueba lee los valores del autor en `external/`, sin copiarlos a mano, y exige:
  - que cada valor del proyecto iguale o supere al del autor, o sea una cota sin pérdida que guarda toda la corrida;
  - que MAAC tenga exactamente el esquema de su autor;
  - que la única reducción, 1 entorno en paralelo, esté declarada;
  - que la reserva de MAAC cubra su búfer sobre el dataset activo;
  - que ningún algoritmo declare `phase_buffer`.

  Valores: MASAC, búfer 50 y lote del crítico 32; MATD3, búfer 744 600; MAAC, búfer 10⁶, lote 1 024 y 4 actualizaciones cada 100 pasos.
- **FR-015.4** — Conformidad de `NativeBackend` y cancelación de hijos (SPEC-003). **Hecho el 2026-11-06.**
  - La conformidad con `LearnerPort` ya estaba verificada en `tests/contract/test_ports_contract.py` (FR-003.2).
  - La cancelación (FR-003.5) se implementa con `uc3m/adapters/process_tree.py`. Un intento interrumpido, por Ctrl+C, SIGTERM o la muerte del padre, termina su árbol completo; la etapa no lanza un intento de reemplazo y el relanzamiento empieza ese tratamiento desde cero.
  - Verificado por `tests/integration/test_training_interruption.py`, en Windows, en Linux y en el CI. El defecto se reprodujo antes del arreglo.
- **FR-015.5** — Estado de entrenamiento en los 4 lanzadores (SPEC-004). Cada lanzador escribe `training_state.pt` con:
  - el esquema `madrl.training_state.v1`;
  - exactamente los optimizadores que declara `native.yaml`, que son los que se observan actualizándose, cada uno con sus momentos: HAPPO 18, MASAC 4, MATD3 34 y MAAC 18;
  - el RNG de torch, CUDA, numpy y python;
  - ninguna réplica.

  Lo verifica `test_every_launcher_saves_its_training_state` sobre una corrida real corta de cada algoritmo. La reanudación con igualdad de trayectoria (FR-004.4) queda sustituida por la regla aprobada de no reanudar: cada intento empieza en el episodio 0.
- **FR-015.6** — Descomposición de la recompensa en los registros de entrenamiento (SPEC-002 FR-002.5).
  - **Por episodio:** cada intento registra los términos escalados de cada edificio: flex, CO₂, costo, EV, BESS y total.
  - **Por paso:** comprueba que la suma de los términos iguala la recompensa con la que aprendió el agente.
  - **Efecto en el intento:** si algún paso no cuadra, el intento queda sin verificar.
  - **Verificación:** simulador real, un caso falsificado y la corrida real de los 4 algoritmos.
- **FR-015.7** — D03, según D-M3-6. **Hecho el 2026-11-06** (CityLearn `387f9c42`; `tests/fresh_training/test_action_masks.py`, 13 pruebas). Mapa discreto en MASAC y MAAC, `continuous_action_map()` en HAPPO y MATD3.
  - **Equipos reales:** se derivan por edificio de `action_names` del esquema, nunca de un relleno fijo.
  - **Discretos:**
    - MASAC recibe `avail_actions` por agente, la máscara que su backend SMAC ya admite, y nunca elige acciones de equipos inexistentes;
    - MAAC recibe por agente un espacio discreto del tamaño real, que su backend admite heterogéneo.
  - **Continuos:** una salida que no corresponde a ningún equipo queda declarada como inerte y se registra, sin cambiar la capacidad nativa.
  - **Registro:** cada intento guarda el mapa acción → equipo de su backend.
  - **Prueba:** sobre el dataset activo, ningún agente discreto puede seleccionar una acción sin equipo, y el mapa coincide con `action_names` en los 17 edificios.
  - **Generalidad:** el mismo mecanismo sirve para `iquitos_v6`, con aire acondicionado, cada cargador y BESS.

## Fuera de alcance

- Entrenar o autorizar etapas: `authorized_stages=[]` hasta el módulo 8.
- Cambiar la capacidad nativa de cualquier algoritmo.

## Criterios de aceptación

1. Pruebas nuevas en rojo antes de implementar y en verde después.
2. Puerta `-Scope Repository` aprobada sobre el commit del módulo, CI en verde.
3. Ningún estado científico cambia.

## Efecto en el plan de Colab (A100 de 80 GB, 83 GiB de RAM, 12 CPU)

| Fase | Antes | Después |
|---|---|---|
| 1: HAPPO y MASAC | 0 trabajadores, MASAC rechazado por VRAM | 1 trabajador |
| 2: MATD3 y MAAC | 2 trabajadores | 2 trabajadores, sin cambio |

En una A100 de 40 GB, la fase 1 sigue rechazada con `insufficient_resources:MASAC:vram`.
