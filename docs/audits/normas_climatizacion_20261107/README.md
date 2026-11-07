# Normas de climatización para `iquitos_v6` (2026-11-07)

**Spec:** [SPEC-016](../../../specs/016-iquitos-v6/spec.md), D-V6-3 y FR-016.3 · **Método:** lectura de los textos primarios por un agente de investigación de solo lectura. Las tablas del MINSA se leyeron de páginas escaneadas.

## Hallazgos que cambian el spec

- **RNE EM.050 no da ninguna cifra:** ni condiciones interiores ni exteriores de diseño, ni W/m², ni ventilación. Sus artículos 1 a 7 tratan definiciones, tipos de sistema, materiales e instalación. No puede fijar la capacidad.
- **RM 666-2025-MINSA no es una norma sobre calor extremo.** Aprueba los «Criterios Técnicos Mínimos en la Infraestructura y el Equipamiento de Establecimientos de Salud Frente al Cambio Climático». Indica que la climatización es del 60 al 70 % del consumo eléctrico de un establecimiento de salud y pide economizadores entálpicos. No se encontró ningún setpoint, aunque la búsqueda fue solo por palabras clave sobre el OCR.
- **La NTS 110 no cita ASHRAE 170.** Remite a ASHRAE 62.1-2007 para la calidad del aire y a ASHRAE 55 para el confort. Es EM.030 (art. 13.5) la que remite a ASHRAE 170 para los establecimientos de salud.

## Cifras verificadas

| Valor | Fuente | Verificado |
|---|---|---|
| Aire exterior `Vbz = Rp·Pz + Ra·Az` (l/s), con `Rp` y `Ra` de la Tabla N° 01 | EM.030 modificada por RM 232-2020-VIVIENDA (El Peruano, 23-09-2020), art. 6. <https://busquedas.elperuano.pe/dispositivo/NL/1887042-2> | sí |
| Densidad por defecto (personas/100 m²): oficina 5; venta minorista 15; áreas comunes de mall 40; supermercado 8; aula de 9 años o más 35; restaurante 70; cafetería 100; auditorio 150; sala legislativa 50; dormitorios compartidos de hotel 20; «salas de estar» de hotel 10 | EM.030, Tabla N° 01, columna Rd, que declara como fuente ASHRAE 62.1-2016 | sí (vía EM.030) |
| Hospital, áreas generales y de tratamiento: 24 °C, HR 45-60 %, 2-3 renovaciones/h | NTS 110-MINSA/DGIEM-V.01 (RM 660-2014/MINSA), §6.2.5.10, Tabla 6; NTS 119 (RM 862-2015/MINSA), Tabla 6 | sí |
| Hospital, sala de operaciones: 22-25 °C (NTS 119: 20-25), HR ≥ 55 %, 15 renovaciones/h, 100 % aire exterior | NTS 110, Tabla 6 y p. 46 | sí |
| Hospital, UCI y laboratorios: 18-25 °C, HR 40-60 %, 12 renovaciones/h | NTS 110 y 119, Tabla 6 | sí |
| Calibración mensual: NMBE ±5 %, CV(RMSE) 15 %; horaria: NMBE ±10 %, CV(RMSE) 30 % | FEMP M&V Guidelines 4.0 (2015), §4.5.3, Tabla 4-2, tomada de ASHRAE Guideline 14. <https://www.energy.gov/sites/prod/files/2016/01/f28/mv_guide_4_0.pdf> | sí (vía FEMP) |

**URL de las normas del MINSA:**
- NTS 110: <https://www.minsa.gob.pe/Recursos/OTRANS/08Proyectos/2022/NTS%20110%20INFRAESTRUCTURA%20Y%20EQUIPAMIENTO%20SNA.pdf>
- NTS 119: <https://www.minsa.gob.pe/Recursos/OTRANS/08Proyectos/2022/NTS%20119%20INFRAESTRUCTURA%20Y%20EQUIPAMIENTO%20TNA.pdf>
- EM.050: <https://cdn.www.gob.pe/uploads/document/file/2686402/EM.050%20Instalaciones%20de%20Climatizaci%C3%B3n.pdf>
- RM 666-2025: <https://cdn.www.gob.pe/uploads/document/file/8798325/7269106-resolucion-ministerial-n-666-2025-minsa.pdf>

## No verificado

- **Densidad de carga de refrigeración en W/m²:** solo una fuente secundaria con datos de Singapur (BCA/NEA). Promedios medidos: oficinas 54-100, hoteles 40-98 y retail 93-195.
- **ASHRAE 55, ISO 7730 y EN 16798-1:** son de pago; no se abrieron.
- **Condiciones exteriores de diseño de Iquitos:** ninguna norma peruana revisada las da.
- **Textos primarios de ASHRAE 62.1 y Guideline 14:** no se abrieron.
- **Versiones del MINSA:** no se contrastaron con El Peruano ni con modificaciones posteriores, como la RM 533-2016.

## Capacidad resultante con D-V6-16 (tarea 3b.1)

Condiciones de cálculo:
- **Presión:** 99,95 kPa, con la elevación de NASA POWER de 115 m.
- **Entalpía exterior:** percentil 99 de 2023, 85,5 kJ/kg.
- **Entalpía interior:** 24 °C y 50 % de HR, 48,1 kJ/kg.

| Edificio | Tipo | Área (m²) | Splits (kW) | Aire exterior (kW) | Ocupantes (kW) | Total (kW térmicos) | W/m² |
|---|---|---|---|---|---|---|---|
| B01 | Office | 14 000 | 264 | 267 | 91 | 622 | 44,4 |
| B02 | Office | 8 000 | 211 | 0 | 0 | 211 | 26,4 |
| B03 | Assembly | 6 000 | 158 | 1 105 | 780 | 2 043 | 340,5 |
| B04 | Retail | 2 500 | 58 | 68 | 26 | 152 | 60,7 |
| B05 | MultiFamily_Hotel | 1 142 | 237 | 28 | 15 | 280 | 245,6 |
| B06 | Commercial_Mall | 20 637 | 712 | 1 687 | 1 073 | 3 472 | 168,2 |
| B07 | Education | 8 103 | 90 | 0 | 0 | 90 | 11,1 |
| B08 | Assembly_Military | 21 000 | 158 | 0 | 0 | 158 | 7,5 |
| B09 | Office_Critical | 4 480 | 142 | 86 | 29 | 257 | 57,4 |
| B10 | Office | 14 296 | 433 | 273 | 93 | 798 | 55,8 |
| B11 | Healthcare_Hospital | 42 649 | 633 | 4 789 | 277 | 5 699 | 133,6 |
| B12 | Healthcare | 18 197 | 343 | 2 043 | 118 | 2 504 | 137,6 |
| B13 | Education | 2 723 | 69 | 0 | 0 | 69 | 25,2 |
| B14 | Industrial_Port | 17 761 | 116 | 0 | 0 | 116 | 6,5 |
| B15 | Education | 9 890 | 53 | 0 | 0 | 53 | 5,3 |
| B16 | Industrial | 10 294 | 132 | 578 | 94 | 803 | 78,1 |
| B17 | Laboratory | 1 611 | 84 | 156 | 52 | 292 | 181,4 |

**Lectura:**
- **Sobredimensionado previsible:** B03, el aeropuerto, con la fracción ocupada en 1,0 (6 000 personas en 6 000 m²) y B05, el hotel (45 splits en 1 142 m²).
- **Edificios sin sistema grande:** su capacidad son solo los splits del inventario.
- **Control:** la calibración con las facturas (D-V6-14, tarea 3b.2) acepta o marca cada valor. Ninguno se usa sin pasar por ella.
