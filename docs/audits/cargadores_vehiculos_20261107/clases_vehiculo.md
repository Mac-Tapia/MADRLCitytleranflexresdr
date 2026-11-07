# Clases de vehículo eléctrico de `iquitos_v6`: fuentes (2026-11-07)

**Spec:** [SPEC-016](../../../specs/016-iquitos-v6/spec.md), D-V6-23 a D-V6-27 · **Método:** lectura de los textos primarios por un agente de investigación de solo lectura. «Derivado» indica una cuenta propia (V × Ah o V × A).

## Moto eléctrica

| Valor | Fuente | Verificado |
|---|---|---|
| Batería de 60 V × 45 Ah por pack, unos 2,7 kWh (derivado); hasta 2 packs | Super Soco CPx, ficha técnica oficial de Vmoto Soco. <https://shop.vmotosoco.com/pages/info-tecniche-cpx> | sí |
| Cargador de 60 V y 10 A, unos 0,6 kW (derivado); de 3 a 6 h por pack | misma ficha | sí |
| Autonomía de 140 km con 2 packs, unos 0,039 kWh/km (derivado) | misma ficha | sí |
| Consumo real en Latinoamérica y recorrido diario | Solo fragmentos de tesis ecuatorianas | no |

No consta que este modelo se venda en Perú.

## Mototaxi eléctrico

| Valor | Fuente | Verificado |
|---|---|---|
| Batería de 8,6 kWh, Li-ion, 51,2 V; 160 km | Piaggio Apé E-City MAXX, página oficial de Piaggio India. <https://piaggio-cv.co.in/ape-e-city> | sí |
| 0,125 kWh/km, 34-45 km/día y 4,78 kWh/día (alta demanda); 3,51 kWh/día (baja demanda) | Abaya et al. (2019), Proc. EASTS 12, tablas 2.4 y 2.5 | sí (Filipinas) |
| Cargador a bordo de 240 V y 20 A, unos 4,8 kW (derivado) | Abaya et al. (2019), tabla 1.1 | sí |
| Ficha técnica de un mototaxi eléctrico vendido en Perú | — | no |

## Camioneta eléctrica

| Valor | Fuente | Verificado |
|---|---|---|
| 98,4 kWh netos; AC trifásica 11 kW; cable de modo 3 Tipo 2 de 32 A; 26,7 kWh/100 km WLTP | Maxus eTerron 9, ficha de Maxus España, diciembre de 2024. <https://maxus-automotive.es/themes/maxus-landing/assets/docs/Ficha_Maxus_eTerron-9_Diciembre_2024.pdf> | sí |
| Bidireccional: solo V2L; la ficha no da potencia | misma ficha | sí (sin kW) |
| Riddara RD6: V2L de 6 kW a 220 V | Riddara Chile, 3 de febrero de 2025 | sí |
| Ford F-150 Lightning: 7,2 kW continuos de respaldo al hogar (V2H), no V2G | Página de soporte de Ford, Intelligent Backup Power | sí |

**Ningún modelo revisado documenta V2G real** (ISO 15118-20 o CHAdeMO bidireccional).

## Norma peruana

- **El D.S. 036-2023-EM** (El Peruano, <https://busquedas.elperuano.pe/api/visor_html/2249540-3>) define solo la carga de la red hacia el vehículo, modos 1 a 4.
- **No menciona** la descarga bidireccional, el V2G ni la inyección.
- **Exigencias:** el modo 3 usa conector Tipo 2 y el modo 4 conector CCS2.
- **Osinergmin:** no se encontró ninguna regla sobre V2G.
