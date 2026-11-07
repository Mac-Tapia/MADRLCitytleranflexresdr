# SPEC-017 — Universalidad: cualquier edificio, cualquier lugar y cualquier MADRL

**Estado:** `draft` · **Origen:** instrucción del propietario, 2026-11-07
**Ámbito:** `D:\MADRLCitytleranflexresdr` · **Exclusión:** `D:\madrl_lima`
**Estado conciliado:** [STATUS](../STATUS.md) · **Plan:** [implementacion_completa.md](../../docs/plans/implementacion_completa.md)

## Instrucción del propietario (2026-11-07)

> Todo lo que el propietario indique debe estar plasmado en el spec respectivo y en el código; nada lo inventa la implementación. Cada vez que se crea un dataset debe quedar operativo. La capa CityLearn v3 es universal: en ella se debe poder entrenar cualquier MADRL. El proyecto debe poder usarse en cualquier edificio y en cualquier lugar.

## Propósito

Que `iquitos_v6` sea una instancia de un proyecto general y no el proyecto mismo. Lo específico de un sitio (normas, tarifas, clima, inventario, horarios, flota) vive en la configuración del sitio. La capa v3 acepta cualquier backend MADRL que cumpla su contrato. Todo dataset construido pasa una puerta de operatividad antes de darse por creado.

## Hallazgos que motivan el spec

- **Constantes de Iquitos en el código:**
  - el bloque de potencia de 18:00 a 23:00 es una constante (`uc3m/application/dataset/construction.py`, `PEAK_HOURS`);
  - el mapa de tipos de vehículo es un diccionario en el código (`ev_sizing.TOKEN_CLASS`);
  - los nombres y docstrings de los módulos nuevos dicen `iquitos_v6`.
- **Backends cerrados:** los 4 MADRL (HAPPO, MASAC, MATD3 y MAAC) entran por adaptadores escritos para cada uno (`CityLearn/scripts/citylearn_v3_training_common.py`). No hay un contrato declarado que un quinto backend pueda cumplir.
- **Sin puerta de operatividad:** un dataset se acepta con sus puertas de datos (`dataset_acceptance.json`), sin comprobar que el entorno v3 lo carga y que los MADRL dan pasos con él.

## Requisitos funcionales

- **FR-017.1 — Configuración del sitio.** Todo valor específico del lugar se lee de una configuración de sitio versionada, no del código:
  - clima y elevación;
  - normas de climatización y de estacionamiento;
  - tarifas de energía y potencia, con su bloque horario;
  - factor de emisión;
  - inventario y horarios de los edificios;
  - flota, clases de vehículo y factores de penetración y de demanda.

  Iquitos es la primera configuración. Una prueba exige que los módulos de `uc3m/application/dataset/` no contengan constantes de sitio.
- **FR-017.2 — Cualquier edificio.** El constructor acepta de 1 a N edificios de cualquier tipo declarado en la configuración. Un tipo sin norma o sin horario se rechaza con su nombre, nunca se rellena.
- **FR-017.3 — Contrato universal de backend en v3.**
  - **Contrato:** la capa v3 (`CityLearn/citylearn/dec_pomdp.py`, `CityLearn/citylearn/v3/`) declara un contrato de backend MADRL, con espacios por agente, observación local y estado global, acciones continuas o discretas con máscara, recompensa por agente o de equipo, estado de entrenamiento y mapa acción → equipo.
  - **Sobre los backends actuales:** HAPPO, MASAC, MATD3 y MAAC lo cumplen sin perder su capacidad nativa (SPEC-015 D-M3-5). La interfaz MARLlib (`marllib_env.py`) es una vía más de ese contrato.
  - **Backend nuevo:** se registra sin editar la capa, y una prueba lo demuestra con un backend mínimo de referencia.
- **FR-017.4 — Puerta de operatividad del dataset.** Cada construcción termina con una puerta que:
  - carga el dataset en el entorno v3;
  - da un episodio corto con cada backend registrado;
  - comprueba el cierre de energía, los espacios de acción y las máscaras.

  Si falla, el dataset no queda como creado (`dataset_verified=false`).
- **FR-017.5 — Trazabilidad de cada valor.**
  - **Origen obligatorio:** cada valor de configuración declara su origen: `measured`, `cited` (con fuente), `design_rule` (decisión del propietario, con su ID) o `assumption`.
  - **Origen `implementation_rule`:** distingue las reglas que puso la implementación, como las P-V6 de SPEC-016. Ninguna cuenta como decisión del propietario.
  - **Prueba:** rechaza un valor sin origen.

## Reglas de la implementación pendientes de confirmar

| ID | Regla | Dónde está |
|---|---|---|
| P-017-1 | Declaración de los backends incorporados: HAPPO y MATD3 con acciones continuas; MASAC y MAAC con acciones discretas con máscara; MASAC con recompensa de equipo (su backend SMAC/QMIX devuelve una sola) y los demás con recompensa por agente; los 4 usan el estado global (CTDE) | `CityLearn/citylearn/v3/backend_contract.py` |
| P-017-2 | El bloque de 18:00 a 23:00 de Iquitos tiene origen `assumption`, porque no está impreso en los pliegos de Osinergmin; se verifica contra la resolución tarifaria | `configs/sites/iquitos.yaml` |

## Estado en el código (2026-11-07)

| Requisito | Estado |
|---|---|
| FR-017.1 Configuración de sitio | Implementado: `configs/sites/iquitos.yaml`, `uc3m/application/dataset/site.py`; ninguna copia del bloque horario ni mapa de vehículos queda en el código (`tests/fresh_training/test_site_config.py`) |
| FR-017.3 Contrato de backend | Implementado: `CityLearn/citylearn/v3/backend_contract.py` (registro, verificación del contrato y episodio de humo); un backend de referencia se registra y da un episodio sin editar la capa (`tests/fresh_training/test_v3_backend_contract.py`) |
| FR-017.2, FR-017.4 y FR-017.5 | Pendientes |

## Fuera de alcance

- Entrenar: el entrenamiento es el módulo 8.
- Crear configuraciones de otros sitios distintos de Iquitos. Solo se demuestra la generalidad con un sitio sintético de prueba.

## Criterios de aceptación

1. Un sitio sintético de prueba, con otro clima, otra tarifa, otro bloque horario y 2 edificios, construye un dataset operativo sin tocar el código.
2. Un backend mínimo de referencia se registra y da un episodio en v3 sin editar la capa.
3. Ninguna constante de sitio queda en `uc3m/application/dataset/`.
4. Cada construcción de `iquitos_v6` termina con la puerta FR-017.4 en verde.
5. Puerta `-Scope Repository` y CI en verde.
