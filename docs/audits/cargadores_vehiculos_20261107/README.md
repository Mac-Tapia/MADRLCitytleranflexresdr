# Cargadores y vehículos de `iquitos_v6`: fuentes (2026-11-07)

**Spec:** [SPEC-016](../../../specs/016-iquitos-v6/spec.md), D-V6-6 y FR-016.5 · **Método:** lectura de los textos primarios por un agente de investigación de solo lectura.

## Verificado

| Valor | Fuente |
|---|---|
| Plaza de uso público (comercio, salud, educación…): 2,50 m de ancho con 3 o más plazas contiguas, 5,00 m de largo, pasillo de 6,50 m | RNE A.010 (RM 191-2021-VIVIENDA), art. 54.2, Cuadro 04. <https://cdn.www.gob.pe/uploads/document/file/2366528/35%20A.010%20CONDICIONES%20GENERALES%20DE%20DISE%C3%91O%20-%20RM%20N%C2%B0%20191-2021-VIVIENDA.pdf> |
| Plaza de uso privado (vivienda, oficinas, hoteles): 2,40 m con 3 o más plazas contiguas, 5,00 m de largo, pasillo de 6,00 m | RNE A.010, art. 54.1, Cuadro 03 |
| Plaza de moto: 1,50 × 2,50 m | RNE A.010, art. 57.2, Cuadro 06 |
| A.010 cubre solo autos y camionetas; los vehículos mayores requieren cálculo específico | RNE A.010, art. 50 |
| Edificios no residenciales existentes con más de 20 plazas: al menos 1 punto de recarga por cada 10 plazas al 1 de enero de 2027 | Directiva (UE) 2024/1275 (EPBD), art. 14(2). <https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=OJ:L_202401275> |
| Tensión nominal de baja tensión: 380/220 V, 60 Hz, tolerancia ±5 % | CNE-Suministro 2011 (RM 214-2011-MEM/DM), regla 017.A y 017.D |
| Modo 2: 220 V, 16 A monofásico (3,5 kW); modo 3: 220 V, 32 A (7,0 kW) o 63 A (13,9 kW) | D.S. 036-2023-EM, anexos 5 y 6. La potencia es V × I, calculada; el decreto no da los kW |
| El D.S. 036-2023-EM y el D.S. 022-2020-EM no fijan un mínimo de cargadores por plaza | Arts. 29 y 11 respectivamente |
| Medida NDC a 2030: 171 359 vehículos ligeros y 6 707 buses eléctricos; no incluye motos ni mototaxis | Informe N° 00232-2023-MINAM/SG/OGAJ, párrafo 3.5 |
| Triciclo eléctrico, comparable a un mototaxi: 13-45 km/día, 3,5-4,8 kWh/día, unos 0,11 kWh/km | Abaya et al. (2019), Proc. EASTS 12, tablas 2.4 y 2.5; Filipinas, no Perú |
| Auto eléctrico usado como taxi: 0,216 kWh/km | Chuquiguanga y Jiménez (2018), tesis de pregrado de la UPS, Cuenca, Ecuador; solo se leyó el resumen |

## No verificado

- **El «5 % de vehículos eléctricos a 2030» del MINEM:** solo aparece en prensa (Andina, 2021) y no se encontró en ningún documento del MINEM. Las «100 000 unidades a 2030» provienen de una declaración del viceministro en 2020, también en prensa.
- **Área por plaza incluyendo la circulación:** A.010 no la da. Calculada desde sus medidas: auto de uso público 2,50 × (5,00 + 6,50/2) = 20,6 m²; moto con el mismo pasillo 1,50 × (2,50 + 3,25) = 8,6 m², ambas `design_rule` derivadas.
- **Potencia real de carga de mototaxis y camionetas:** no hay fuente primaria.
- **Recorrido diario de autos en Perú:** no hay fuente primaria.
- **Modificaciones posteriores:** no se comprobó si A.010 cambió después de 2021 ni si el D.S. 036-2023-EM cambió después de 2023.
