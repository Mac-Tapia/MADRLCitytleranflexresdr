# SPEC-015 — Módulo 3: contrato de algoritmos y recursos

**Estado:** `in_progress` (FR-015.1 a FR-015.3 implementados)
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
- **D-M3-3: regla del requisito.** `requisito = max(piso, techo(1,10 × estimación))`. El margen de 10 % reproduce el que tenían las cifras anteriores (72 frente a 65,3 GiB). El piso es de 8 GiB de RAM y 4 GiB de VRAM, el ya declarado para HAPPO y MAAC, que no tienen estimador. Es regla de diseño, no una medida.

## Requisitos funcionales

- **FR-015.1** — Requisitos ligados al dataset activo: una prueba mide las dimensiones de MASAC y MATD3 con sus entornos reales sobre el split `train_2023` de la campaña configurada, calcula las estimaciones con las funciones del proyecto y exige que MASAC cumpla D-M3-3 exactamente y que las demás reservas cubran su estimación. Un cambio de dataset que deje cifras viejas hace fallar la puerta.
- **FR-015.2** — Requisito por candidato: `runtime_requirements` de MASAC declara la VRAM por `rnn_hidden_dim` para cada valor de la rejilla de HPO. El guardián toma el del argumento nativo del intento; un valor sin requisito declarado se rechaza, nunca se aprueba por omisión.
- **FR-015.3** — Capacidad nativa sin cambios: búfer de MASAC 50, lote del crítico 32, búfer de MATD3 744 600 y de MAAC 5 × 8 760.
- **FR-015.4 a FR-015.7** — Pendientes del módulo según la hoja de ruta: conformidad de `NativeBackend` y cancelación de hijos (SPEC-003), `save_training_state` en los cuatro lanzadores (SPEC-004), descomposición de la recompensa en los registros (SPEC-002) y D03. Se detallan al empezar cada uno.

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
