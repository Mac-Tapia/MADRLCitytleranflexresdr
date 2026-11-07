# Modo de carga y tipo de cargador por clase de vehículo (2026-11-07)

Pedido del propietario (2026-11-07): aclarar con catálogos del mercado el modo de carga y el tipo de cargador de cada clase, y confirmar que motos y mototaxis son unidireccionales. Búsqueda web de solo lectura. Las URL se consultaron el 2026-11-07. «Prensa» marca lo que no consta en una ficha de fabricante o distribuidor. Complementa [clases_vehiculo.md](clases_vehiculo.md).

## Motos eléctricas: unidireccionales

| Campo | Hallazgo | Fuente |
|---|---|---|
| Cargador | Externo (portátil). Super Soco CPx: 60 V × 10 A estándar (unos 0,6 kW calculados) y 60 V × 15 A rápido | Vmoto Soco, ficha técnica del CPx: <https://shop.vmotosoco.com/pages/info-tecniche-cpx?lang=5> |
| Entrada | 90–240 V CA, desde una toma doméstica | Whatever Wheels (distribuidor): <https://whateverwheels.co.uk/m3b0s480p20863/SUPER-SOCO-CPx-2020>; Bennetts (prensa) |
| Modo IEC 61851 | 1 (toma doméstica sin control piloto). Ninguna ficha nombra el modo; se deduce del cargador portátil enchufado a la toma | inferencia |
| Mercado peruano | Fichas locales a 220 V y 60 Hz, con 6–8 h de carga | Motocorp E1: <https://motocorp.pe/wp-content/uploads/2024/08/E1-1.pdf>; Ripley Perú |
| Dirección | Unidireccional en todas las fichas revisadas. La única excepción encontrada, la FELO M One con V2L, consta solo en prensa y no se vende en Perú | fichas citadas |

## Mototaxis eléctricos: unidireccionales

| Modelo | Carga | Dirección | Fuente |
|---|---|---|---|
| Bajaj RE E-TEC 9.0 | Toma doméstica de 16 A con cargador a bordo; 8,9 kWh en 4 h 30 min | unidireccional | Bajaj: <https://bajajauto.com/three-wheelers/ev-re> |
| Mahindra Treo | Toma de 16 A; las fuentes no coinciden en si el cargador va a bordo o es externo | unidireccional | Mahindra, comunicado de prensa; TractorJunction |
| Piaggio Ape E-City FX/Maxx | Cargador externo de 48 V y 3 kW; unas 3 h 45 min | unidireccional | TrucksBuses (agregador): <https://www.trucksbuses.com/3-wheeler/passenger/piaggio-ape-e-city-fx-maxx/specifications> |

Ninguno usa conector Tipo 2 ni IEC 60309: todos cargan en una toma doméstica (modo 1 o 2, deducido). No se encontró ninguna ficha de una marca peruana de mototaxi eléctrico.

## Camionetas: carga en modo 3 Tipo 2; descarga solo por V2L

| Modelo | Carga en CA | Carga en CC | Bidireccional | Fuente |
|---|---|---|---|---|
| Maxus eTerron 9 | Tipo 2, 11 kW trifásica; en monofásica a 230 V y 32 A, unos 7,4 kW (calculado) | CCS2, 115 kW | V2L de 6,6 kW; no documenta V2H ni V2G | e-mobileo (distribuidor): <https://www.e-mobileo.de/?p=38297>; carz.com.my; paultan (prensa) |
| Maxus T90 EV | Tipo 2, 10 kW (Argentina) | CCS2, 80 kW | V2L solo en una ficha de Irlanda | Maxus Argentina: <https://www.maxus.com.ar/documents/t90ev_maxus_expoagro_mar25.pdf> |
| Riddara RD6 | 6,6 kW o 11 kW según el país (conflicto) | 90–120 kW | V2L de 6 kW | Riddara Chile; Autoblog Uruguay (prensa) |
| BYD Shark (híbrida enchufable) | CA de 6,6 kW | CC de 40 kW | V2L de 6,6 kW | BYD Perú (PDF no accesible); CarExpert |
| Ford F-150 Lightning | — | — | V2H hasta 9,6 kW con Charge Station Pro y Home Integration System, solo en EE. UU. | Ford: <https://www.ford.com/support/category/electric-vehicle/home-backup-power/> |

**Ninguna camioneta del mercado peruano o latinoamericano documenta V2G ni V2H.**

## Equipos bidireccionales

| Equipo | Tipo | Potencia | Vehículos | Venta | Fuente |
|---|---|---|---|---|---|
| Wallbox Quasar 2 | CC (CCS según la prensa) | 12,8 kW | Kia EV9 | 7 estados de EE. UU. | Wallbox: <https://wallbox.com/en_us/blog/pre-order-quasar-2-bidirectional-v2h-ev-charger-kia-ev9> |
| Ford Charge Station Pro + Home Integration System | CA; invierte el cargador a bordo | 9,6 kW | F-150 Lightning | EE. UU. | Ford |
| dcbel Ara | CC (CCS o CHAdeMO, ISO 15118) y CA | 15,2 kW | Nissan Leaf, Volvo EX90 | EE. UU. y Canadá | dcbel, centro de ayuda |

**Un cargador de pared Tipo 2 en modo 3 no puede descargar.** La descarga en CA exige un cargador a bordo bidireccional y un sistema que la controle, como en el caso de Ford. No se encontró ningún equipo bidireccional a la venta en Perú.

## Norma peruana

- **D.S. 036-2023-EM:** define solo la carga de la red al vehículo.
- **MINEM y Osinergmin:** no se encontró ninguna norma sobre equipos bidireccionales, ni sobre V2B o V2H.
- **Reglamento de Generación Distribuida:** sigue en proyecto (R.M. 439-2024-MINEM/DM); su promulgación no está confirmada.

## Consecuencia para el modelo

| Clase | Modo y cargador | Dirección | Valor en `configs/dataset/ev_v6.yaml` |
|---|---|---|---|
| Moto | Modo 1, toma doméstica de 220 V, cargador externo portátil | solo carga | 0,6 kW (ficha del CPx) |
| Mototaxi | Modo 1 o 2, toma doméstica de 16 A, cargador a bordo o externo según el modelo | solo carga | 3,52 kW: el tope de la toma de 16 A. Los modelos revisados cargan a unos 2–3 kW (Bajaj: 8,9 kWh en 4,5 h; Piaggio: 3 kW) |
| Camioneta | Carga en modo 3, Tipo 2 monofásica de 32 A (7,04 kW) | carga; descarga solo V2L | La descarga de 7,04 kW por la misma conexión **no la permite un cargador de pared Tipo 2**. Lo documentado es V2L de 6,6 kW (eTerron 9). El V2B detrás del medidor equivale hoy a V2L más un tablero de transferencia; es una inferencia, ningún producto lo documenta |

El propietario confirmó el 2026-11-07 que la carga de las 3 clases es en corriente alterna, con los modos de la norma IEC 61851-1.

Pendiente: el tipo de toma peruana con fuente (el sitio de la IEC respondió 403), las fichas de Maxus y Riddara para Perú y la potencia oficial del Treo.
