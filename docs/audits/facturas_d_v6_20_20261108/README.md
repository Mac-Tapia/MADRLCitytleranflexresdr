# Hoja de revisión de facturas, D-V6-20 (2026-11-08)

**Para:** el propietario del proyecto.
**Decisión:** [D-V6-20 en SPEC-016](../../../specs/016-iquitos-v6/spec.md). Verificar si `B_xx.csv` cubre todos los suministros de B11, B09, B03, B14, B02, B12, B16, B17, B08 y B13.
**Campaña revisada:** `iquitos_v6_trial11`. No se cambió ningún dato ni se reconstruyó nada.
**Estado:** no se completará. El propietario decidió el 2026-11-08 entrenar con las facturas ya construidas, y D-V6-20 queda como limitación declarada. Esta hoja conserva los indicios y no declara parcial ni completa ninguna factura.

## Lo que conviene saber antes de empezar

1. **B11 tiene dos identificadores en el repositorio y `B_11.csv` contiene solo uno.** El libro `resultados_preliminares.xlsx` registra el hospital como `0104005T` y `0104007T`. `B_11.csv` coincide con `0104005T` en 34 de 34 meses. `0104007T` suma 1 988 180 kWh de febrero a octubre de 2025 y no está en `B_11.csv`. Falta saber si es un suministro del mismo edificio y si existía en 2023 y 2024.
2. **B14 no coincide con la hoja del puerto.** La hoja `5.ENAPU` registra 359 891 kWh en 2023 y `B_14.csv` 44 012 kWh. El repositorio no dice si ENAPU y la Autoridad Portuaria Nacional son el mismo edificio.
3. **La columna de total impreso está desplazada en 6 archivos**, y el dataset la usa para escalar los meses. Es otro problema, independiente de los suministros, pero también exige reconstruir. Conviene decidir los dos a la vez ([sección aparte](#otro-hallazgo-total-impreso-desplazado-en-6-archivos)).

Hoy repetir la campaña no pierde entrenamiento. Nada se ha ejecutado en Colab ([traspaso](../../plans/traspaso_sesiones.md)) y en este equipo no existe `outputs/campaigns/`.

## Vía más rápida (sugerencia)

Pedir a Electro Oriente, o a quien preparó el libro, **la lista de suministros por titular** para estos 10 nombres, con sus consumos de 2023 a 2025. Una sola lista respondería las preguntas de suministros de los 10 edificios.

Si no se consigue, use el recibo de enero de 2023 de cada edificio. El repositorio no guarda recibos, así que no se pudo comprobar cómo se llaman sus campos. Busque el número de suministro, la tarifa, la energía activa y la máxima demanda.

## Qué implica cada respuesta (D-V6-20)

| Respuesta | Consecuencia |
|---|---|
| **Factura parcial:** el edificio tiene más suministros que los de `B_xx.csv` | Se completa con los suministros que faltan. El dataset cambia y la campaña se repite. |
| **Factura completa:** `B_xx.csv` cubre todos los suministros | Se revisa el inventario de ese edificio. Si el inventario cambia, el dataset también cambia y la campaña se repite. Si nada cambia, sigue el tope. |
| **No se puede verificar** | Sigue el tope declarado del 70 % de D-V6-19, como hoy ([plan](../../plans/implementacion_completa.md)). |

**D-V6-20 no resuelve este caso:** un suministro con recibos solo de una parte de 2023 a 2025. Los años son entrenamiento, validación y prueba, así que habría que decidir cómo completar los otros años.

## Resumen por brecha

Orden de mayor a menor brecha. Coincide en la auditoría y en `trial11`. La lista de D-V6-20 pone B03 antes que B14, pero B14 tiene la brecha mayor.

| # | Edificio | Física / factura, auditoría | Física / factura, `trial11` 2023 | kWh/m², 2023 | Indicio principal | Respuesta (parcial / completa / no verificable) |
|---|---|---|---|---|---|---|
| 1 | B11 Hospital Regional | 1 194,7 % | 1 206,3 % | 22,0 | Segundo identificador fuera de `B_11.csv` | ________ |
| 2 | B09 COER | 806,0 % | 786,9 % | 11,4 | Ninguno sobre suministros; nombre cercano a B10 | ________ |
| 3 | B14 Autoridad Portuaria | 389,6 % | 390,9 % | 2,5 | Hoja ENAPU 8,2 veces mayor | ________ |
| 4 | B03 Aeropuerto | 380,8 % | 383,5 % | 138,6 | Salto sostenido desde diciembre de 2024 | ________ |
| 5 | B02 Municipalidad San Juan | 325,7 % | 325,4 % | 5,7 | La otra oficina (B10) tiene 83,2 kWh/m² | ________ |
| 6 | B12 EsSalud | 219,5 % | 217,8 % | 123,2 | Factura estable; la brecha viene sobre todo de la ventilación | ________ |
| 7 | B16 SIMA | 170,6 % | 168,6 % | 59,4 | Ninguno sobre suministros | ________ |
| 8 | B17 Selva Amazónica | 145,4 % | 155,6 % | 245,2 | Ninguno sobre suministros | ________ |
| 9 | B08 Escuela PNP | 124,7 % | 140,6 % | 4,5 | 21 000 m² con muy poco consumo | ________ |
| 10 | B13 UNAP Económicas | 87,3 % | 98,1 % | 25,3 | Dos hojas de la misma facultad que no coinciden | ________ |

**Cómo leer las columnas:**

- **Auditoría:** [calibración del 2026-11-07](../calibracion_refrigeracion_20261107/README.md), hecha sobre `iquitos_v5`.
- **`trial11`:** suma de `E_*_cooling_fisico_kWh` entre la suma de `E_*_medido_kWh` de `audit/distillation_report.csv`.
- **Física:** una estimación del inventario con supuestos, no una medición (`assumption` de D-V6-18).
- **kWh/m²:** kWh de los registros de punta y fuera de punta de 2023 entre el área de `building.csv`.

**Referencia dentro del repositorio, kWh/m² de los otros edificios con factura:** B04 552,0; B05 808,4; B06 599,7 (2024, porque 2023 no está completo); B07 22,4; B10 83,2; B15 16,8.

Una brecha grande no prueba que falte un suministro: también puede estar sobreestimado el inventario (D-V6-20).

## Lo común a los 10 edificios

- **Meses cubiertos:** enero de 2023 a enero de 2026, 37 filas, una por mes, sin huecos de 2023 a 2025 (`B_xx.csv`).
- **Identificador y número de suministros:** `B_xx.csv` y `building.csv` no tienen esa columna. Salvo el código de B11 en el libro: **no registrado en el repositorio**.
- **Origen de las facturas:** `provenance.json` solo dice «owner-provided distributor bills».
- **Pico:** `B_xx.csv` no trae la máxima demanda.
  - «Hoja» es la columna `MD [KW]` del libro, máximo de 2023.
  - «Implícito» es `kWh ÷ (FactorCarga × horas del mes)` con los registros, máximo de 2023. Es aproximado.
- **kWh de cada ficha:** «registros» es punta + fuera de punta del archivo. «Dataset» es lo que usa `trial11` tras su escalado (`parse_billing_csv`).

---

## 1. B11, Hospital Regional de Loreto

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores | `0104005T` y `0104007T`; `B_11.csv` no trae ninguno | Hojas `6.H.REGIONAL.T1` y `6.H.REGIONAL` |
| Número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | MT2, 42 649,33 m² | `B_11.csv`, `building.csv` |
| Inventario | 120 splits; «Clinical Chiller + HEPA / Blood Bank Cold Room» | `building.csv` |
| kWh registros 2023 / 2024 / 2025 | 937 521 / 869 186 / 1 001 470 | `B_11.csv` |
| kWh dataset 2023 / 2024 / 2025 | 921 583 / 967 974 / 939 828 | `parse_billing_csv` |
| Intensidad 2023 | 22,0 kWh/m²; 107,0 kW de media; 2,51 W/m² | Calculado |
| Pico 2023 | 168,1 kW (hoja, `0104005T`) | `6.H.REGIONAL.T1` |
| Aire acondicionado del inventario | 5 700 kW térmicos, de ellos 633 por splits; 2 544 kW eléctricos; 15,1 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 1 194,7 %; 70,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:**

- `B_11.csv` coincide con `0104005T` en 34 de 34 meses (enero de 2023 a octubre de 2025), con los registros y no con el total impreso.
- `0104007T` tiene 9 meses (febrero a octubre de 2025), 1 988 180 kWh y hasta 640,9 kW. No coincide en ningún mes con `B_11.csv`.
- Los dos identificadores tienen datos en los mismos meses, así que uno no sustituye al otro en ese periodo.
- El libro anota 2 650 MWh/año para `0104007T`.

**Indicio, no prueba:** `0104005T` bajó de 1 477 193 kWh y 361,6 kW (2021) a 937 521 kWh y 168,1 kW (2023). Es compatible con que parte de la carga pasara a otro suministro.

**Cálculo de febrero a octubre de 2025:** la suma de ambos da 2 755 601 kWh, 3,59 veces `0104005T`. La física del periodo, 7 936 273 kWh, sería 288 % de la suma, frente a 1 034 % de `0104005T` solo. **Aunque se complete, la física seguiría sobre la factura**, así que el inventario también merecería revisión.

**Preguntas:**

1. ¿`0104007T` da servicio al mismo hospital de 42 649 m²? Sí / No: ______
2. ¿Hay otros suministros a nombre del hospital? Número total: ______ Identificadores: ______________
3. ¿Desde qué mes existe `0104007T`? ______ ¿Tiene recibos de 2023 y 2024? ______
4. Recibo de enero de 2023: punta ______ fuera de punta ______ total ______ máxima demanda ______ (archivo: 9 638,17 / 42 021,78 / 83 749,01; hoja: 168,05 kW).

**Si es parcial:** se añade `0104007T` y cualquier otro suministro, en lo posible para los tres años. **Si es completa:** se revisan el área climatizada y el sistema grande, que aportan 5 067 de los 5 700 kW térmicos.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 2. B09, Gobierno Regional de Loreto, COER

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | MT2, 4 479,67 m² | `B_09.csv`, `building.csv` |
| Inventario | 27 splits; «DataCenter Precision AC (N+1)» | `building.csv` |
| kWh registros 2023 / 2024 / 2025 | 50 859 / 47 757 / 53 315 | `B_09.csv` |
| kWh dataset 2023 / 2024 / 2025 | 50 172 / 50 796 / 47 944 | `parse_billing_csv` |
| Intensidad 2023 | 11,4 kWh/m²; 5,8 kW de media; 1,30 W/m² | Calculado |
| Pico 2023 | 24,4 kW (hoja) | `21.COER` |
| Aire acondicionado del inventario | 257 kW térmicos, de ellos 142 por splits; 102 kW eléctricos; 4,2 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 806,0 %; 70,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:** `B_09.csv` coincide con la hoja `21.COER` en 34 de 34 meses. Es una sola hoja, y eso no prueba que sea el único suministro.

**Indicio, no prueba:** B10 se llama «Gobierno Regional de Loreto» y factura 1 189 308 kWh en 2023. Solo por los nombres, cabe preguntar si comparten instalaciones. Un centro de datos N+1 con 5,8 kW de media también merece revisión del inventario.

**Preguntas:**

1. ¿Cuántos suministros alimentan el COER? ______ Identificadores: ______________
2. ¿Parte del COER se alimenta desde el suministro de B10? Sí / No: ______
3. ¿Los 4 479,67 m² son solo del COER? Sí / No: ______
4. ¿El centro de datos existe y consume desde este suministro? Sí / No: ______
5. Recibo de enero de 2023: punta ______ fuera de punta ______ (archivo: 562,09 / 2 352,45).

**Si es parcial:** se añade el suministro que falte, sin contar dos veces lo que ya esté en B10. **Si es completa:** se revisan el área y el centro de datos.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 3. B14, Autoridad Portuaria Nacional

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | BT3, 17 761 m² | `B_14.csv`, `building.csv` |
| Inventario | 22 splits; sin sistema grande | `building.csv` |
| kWh registros y dataset 2023 / 2024 / 2025 | 44 012 / 50 067 / 39 934 | `B_14.csv` |
| Intensidad 2023 | 2,5 kWh/m², la más baja de los 16; 5,0 kW de media; 0,28 W/m² | Calculado |
| Pico 2023 | 19,7 kW (implícito) | `B_14.csv` |
| Aire acondicionado del inventario | 116 kW térmicos, todos por splits; 52 kW eléctricos; 2,6 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 389,6 %; 70,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:**

- `B_14.csv` no coincide con ninguna hoja del libro. Hay una coincidencia aislada con `21.COER` en 1 de 34 meses.
- `5.ENAPU` («Empresa Nacional de Puertos S.A.») registra 359 891 kWh y 88,2 kW en 2023, 8,2 veces `B_14.csv`.
- Septiembre de 2023 está marcado `partial_month_suspect` (`quality_flags.csv`).

**Indicio, no prueba:** si ENAPU fuera este mismo edificio, la física de 2023 (172 021 kWh) sería el 47,8 % de esa hoja, por debajo del tope. Los nombres son de dos entidades distintas, y el repositorio no dice si ocupan el mismo sitio.

**Preguntas:**

1. ¿Los 17 761 m² son de la Autoridad Portuaria, de ENAPU o de las dos? ______
2. ¿Cuántos suministros tiene ese recinto y a nombre de quién? ______ Identificadores: ______________
3. Recibo de enero de 2023: punta ______ fuera de punta ______ (archivo: 544,50 / 3 183,00).

**Si es parcial:** se añaden los suministros del recinto. **Si es completa:** se revisan el área y los 22 splits, porque quizá el área describa más que estas oficinas.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 4. B03, Aeropuerto Internacional

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | MT4, 6 000 m² | `B_03.csv`, `building.csv` |
| Inventario | 30 splits; «Chiller Central Water-Cooled» | `building.csv` |
| kWh registros y dataset 2023 / 2024 / 2025 | 831 540 / 641 558 / 1 395 292 | `B_03.csv` |
| Intensidad 2023 | 138,6 kWh/m²; 94,9 kW de media; 15,82 W/m² | Calculado |
| Pico 2023 | 220,1 kW (implícito) | `B_03.csv` |
| Aire acondicionado del inventario | 2 043 kW térmicos, de ellos 158 por splits; 760 kW eléctricos; 3,5 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 380,8 %; 70,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:**

- El libro no tiene hoja del aeropuerto.
- De noviembre a diciembre de 2024 el consumo diario se multiplica por 1,86 y se mantiene alto en 2025.
- Las filas de septiembre a noviembre de 2025 tienen 5 decimales, a diferencia de las demás, y facturan 12 046,5, 5 904 y 5 928,5, unas 0,05 a 0,10 por kWh frente a una mediana de 0,47.

**Indicio, no prueba:** el salto es compatible con un cambio de lo que cubre el medidor o de la operación del aeropuerto. Las tres filas de 2025 no parecen transcritas igual que el resto.

**Preguntas:**

1. ¿Cuántos suministros tiene el aeropuerto? ______ Identificadores: ______________
2. ¿Qué cambió en diciembre de 2024 (suministro añadido, medidor, ampliación)? ______________
3. ¿Hay instalaciones del recinto con recibo aparte? ______________
4. ¿Las filas de septiembre a noviembre de 2025 vienen de un recibo? Sí / No: ______
5. Recibo de enero de 2023: punta ______ fuera de punta ______ (archivo: 20 009,07 / 69 263,57).

**Si es parcial:** se añaden los suministros que falten, y hay que aclarar si 2023 y 2024 son comparables con 2025. **Si es completa:** se revisan el chiller y el área climatizada, que aportan 1 885 de los 2 043 kW térmicos.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 5. B02, Municipalidad Distrital de San Juan Bautista

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | BT3, 8 000 m² | `B_02.csv`, `building.csv` |
| Inventario | 40 splits; sin sistema grande | `building.csv` |
| kWh registros 2023 / 2024 / 2025 | 45 255 / 72 657 / 86 601 | `B_02.csv` |
| kWh dataset 2023 / 2024 / 2025 | 49 480 / 75 640 / 92 326 | `parse_billing_csv` |
| Intensidad 2023 | 5,7 kWh/m²; 5,2 kW de media; 0,65 W/m² | Calculado |
| Pico 2023 | 33,9 kW (implícito; mediana mensual 11,1 kW) | `B_02.csv` |
| Aire acondicionado del inventario | 211 kW térmicos, todos por splits; 84 kW eléctricos; 2,5 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 325,7 %; 61,9 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:**

- El libro no tiene hoja de este edificio.
- Hay 8 saltos mensuales de ×1,5 o más, en cualquier sentido, entre 2023 y 2025, y el consumo casi se duplica de 2023 a 2025.
- Tiene el total impreso desplazado ([sección aparte](#otro-hallazgo-total-impreso-desplazado-en-6-archivos)).

**Indicio, no prueba:** B10, la otra oficina con factura completa de 2023, tiene 83,2 kWh/m², unas 15 veces más. Tarifa de baja tensión en 8 000 m².

**Preguntas:**

1. ¿Cuántos suministros tiene la municipalidad? ______ Identificadores: ______________
2. ¿Los 8 000 m² y los 40 splits son de este suministro? Sí / No: ______
3. Recibo de enero de 2023: punta ______ fuera de punta ______ total ______ (archivo: 743,20 / 1 606,40 / 3 134,80). ¿El total es 2 349,60 (la suma) o 3 134,80? ______

**Si es parcial:** se añaden los suministros que falten. **Si es completa:** se revisan el área y el número de splits.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 6. B12, Seguro Social de Salud, EsSalud

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | MT2, 18 197,48 m² | `B_12.csv`, `building.csv` |
| Inventario | 65 splits; «Medical Archive AC System» | `building.csv` |
| kWh registros y dataset 2023 / 2024 / 2025 | 2 242 798 / 2 375 943 / 2 332 089 | `B_12.csv` |
| Intensidad 2023 | 123,2 kWh/m²; 256,0 kW de media; 14,07 W/m² | Calculado |
| Pico 2023 | 540,0 kW (hoja) | `3.ESSALUD` |
| Aire acondicionado del inventario | 2 505 kW térmicos, de ellos 343 por splits; 1 118 kW eléctricos; 2,1 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 219,5 %; 70,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:** coincide con `3.ESSALUD` en 34 de 34 meses, sin saltos de ×1,5 entre meses.

**Indicio, no prueba:** una factura estable y el mayor consumo del grupo apuntan más al inventario. Basta tener «sistema grande» para calcular ventilación sobre toda el área ocupada (`hvac_capacity.py`), y aquí el sistema se describe como de un archivo médico.

**Preguntas:**

1. ¿Cuántos suministros tiene este establecimiento? ______ Identificadores: ______________
2. ¿El sistema grande atiende todo el edificio o solo el archivo? ______
3. ¿Los 18 197,48 m² están en un solo recinto? Sí / No: ______
4. Recibo de enero de 2023: punta ______ fuera de punta ______ (archivo: 27 981,79 / 151 036,21).

**Si es parcial:** se añaden los suministros que falten. **Si es completa:** se revisan el alcance del sistema y el área, que aportan 2 162 de los 2 505 kW térmicos.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 7. B16, SIMA Iquitos

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | MT3, 10 294 m² | `B_16.csv`, `building.csv` |
| Inventario | 25 splits; «Industrial Mobile Vessel AC Units» | `building.csv` |
| kWh registros 2023 / 2024 / 2025 | 611 524 / 611 765 / 675 518 | `B_16.csv` |
| kWh dataset 2023 / 2024 / 2025 | 627 432 / 632 190 / 649 663 | `parse_billing_csv` |
| Intensidad 2023 | 59,4 kWh/m²; 69,8 kW de media; 6,78 W/m² | Calculado |
| Pico 2023 | 302,7 kW (hoja) | `2.SIMA IQUITOS` |
| Aire acondicionado del inventario | 804 kW térmicos, de ellos 132 por splits; 320 kW eléctricos; 1,1 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 170,6 %; 70,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:** `B_16.csv` coincide con `2.SIMA IQUITOS` en 34 de 34 meses. Tiene el total impreso desplazado.

**Indicio, no prueba:** ninguno sobre suministros. El inventario describe equipos móviles de embarcaciones y el cálculo los trata como sistema grande del edificio.

**Preguntas:**

1. ¿Cuántos suministros tiene el astillero? ______ Identificadores: ______________
2. ¿Los equipos de embarcaciones consumen de este suministro? Sí / No: ______
3. ¿Hay talleres o muelles con recibo aparte? ______________
4. Recibo de enero de 2023: punta ______ fuera de punta ______ (archivo: 5 972,72 / 37 990,87).

**Si es parcial:** se añaden los suministros que falten. **Si es completa:** se revisa si los equipos de embarcaciones cuentan como sistema del edificio; el sistema y el área aportan 672 de los 804 kW térmicos.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 8. B17, Asociación Civil Selva Amazónica

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | BT2, 1 611,23 m² | `B_17.csv`, `building.csv` |
| Inventario | 16 splits; «Scientific Ultra-Freezers (-80C)» | `building.csv` |
| kWh registros 2023 / 2024 / 2025 | 395 032 / 413 845 / 374 479 | `B_17.csv` |
| kWh dataset 2023 / 2024 / 2025 | 366 702 / 425 718 / 395 722 | `parse_billing_csv` |
| Intensidad 2023 | 245,2 kWh/m²; 45,1 kW de media; 27,99 W/m² | Calculado |
| Pico 2023 | 110,3 kW (implícito) | `B_17.csv` |
| Aire acondicionado del inventario | 292 kW térmicos, de ellos 84 por splits; 130 kW eléctricos; 1,2 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 145,4 %; 70,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:** el libro no tiene hoja de este edificio. Tiene el total impreso desplazado.

**Indicio, no prueba:** ninguno sobre suministros. Su intensidad es alta dentro del grupo. Los ultracongeladores activan el cálculo de ventilación de «sistema grande», aunque no son aire acondicionado.

**Preguntas:**

1. ¿Cuántos suministros tiene? ______ Identificadores: ______________
2. ¿Hay un sistema de aire acondicionado grande, además de los ultracongeladores? Sí / No: ______
3. Recibo de enero de 2023: punta ______ fuera de punta ______ total ______ (archivo: 4 953,60 / 25 250,00 / 33 377,20).

**Si es parcial:** se añaden los suministros que falten. **Si es completa:** se revisa si este edificio debe contar como «sistema grande»; esa parte aporta 208 de los 292 kW térmicos.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 9. B08, PNP, Escuela Técnica Superior

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | MT3, 21 000 m² | `B_08.csv`, `building.csv` |
| Inventario | 30 splits; sin sistema grande | `building.csv` |
| kWh registros y dataset 2023 / 2024 / 2025 | 94 161 / 96 742 / 136 463 | `B_08.csv` |
| Intensidad 2023 | 4,5 kWh/m²; 10,7 kW de media; 0,51 W/m² | Calculado |
| Pico 2023 | 30,0 kW (hoja) | `19.ESCUELA TECNICA DE PNP` |
| Aire acondicionado del inventario | 158 kW térmicos, todos por splits; 71 kW eléctricos; 2,4 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 124,7 %; 60,0 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:** coincide con la hoja `19.ESCUELA TECNICA DE PNP` en 34 de 34 meses.

**Indicio, no prueba:** 21 000 m² con 4,5 kWh/m² es la segunda intensidad más baja de los 16. Cabe preguntar si un solo suministro cubre todo el recinto.

**Preguntas:**

1. ¿Cuántos suministros tiene la escuela? ______ Identificadores: ______________
2. ¿Los 21 000 m² y los 30 splits corresponden a este suministro? Sí / No: ______
3. ¿Qué explica los 136 463 kWh de 2025, frente a 96 742 en 2024? ______________
4. Recibo de enero de 2023: punta ______ fuera de punta ______ (archivo: 1 582,18 / 6 307,91).

**Si es parcial:** se añaden los suministros que falten. **Si es completa:** se revisan el área y el número de splits.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## 10. B13, UNAP, Facultad de Ciencias Administrativas, Contables y Económicas

El nombre del archivo está abreviado: «CIENCIAS AD..CONTABLES Y ECO». La forma completa de este título es una lectura, no un dato.

| Dato | Valor | Fuente |
|---|---|---|
| Identificadores y número de suministros | **no registrado en el repositorio** | — |
| Tarifa, área | MT4, 2 723 m² | `B_13.csv`, `building.csv` |
| Inventario | 13 splits; sin sistema grande | `building.csv` |
| kWh registros y dataset 2023 / 2024 / 2025 | 68 875 / 71 550 / 71 402 | `B_13.csv` |
| Intensidad 2023 | 25,3 kWh/m²; 7,9 kW de media; 2,89 W/m² | Calculado |
| Pico 2023 | 48,3 kW (implícito) | `B_13.csv` |
| Aire acondicionado del inventario | 69 kW térmicos, todos por splits; 31 kW eléctricos; 0,6 veces el pico | Auditoría, `building.csv` |
| Física / factura; refrigeración final | 87,3 %; 68,7 %; 12 meses recortados | Auditoría |

**Hecho del repositorio:**

- `B_13.csv` no coincide con ninguna hoja del libro. Hay coincidencias aisladas en 1 de 34 meses con dos hojas de colegios.
- El índice del libro lista dos sitios de la Facultad de Economía y Negocios, oficina y aulas (`10.UNAP.FEN1` y `10.UNAP.FEN2`). Tampoco coinciden.
- `FEN2` registra 27 717 kWh en 2023. La columna de kWh de `FEN1` trae cifras pequeñas, iguales a la columna `MD` de `FEN2`, y parece desplazada: no sirve como energía.

**Indicio, no prueba:** es la brecha más pequeña y el recorte viene sobre todo del tope del 70 %. Si `FEN2` fuera un suministro más de este edificio, la física de 2023 (67 568 kWh) sería el 70,0 % de la suma; es solo aritmética.

**Preguntas:**

1. ¿Esta facultad es la «Facultad de Economía y Negocios» del libro? Sí / No: ______
2. ¿Cuántos suministros tiene? ______ Identificadores: ______________
3. ¿`B_13.csv` es oficina, aulas o ambas? ______
4. Recibo de enero de 2023: punta ______ fuera de punta ______ (archivo: 389,50 / 4 105,13).

**Si es parcial:** se añaden los suministros que falten. **Si es completa:** se revisa el inventario de splits.

**Respuesta:** parcial / completa / no verificable: ________ **Evidencia:** ______________

---

## Otro hallazgo: total impreso desplazado en 6 archivos

**No es una cuestión de suministros y esta hoja no lo corrige.** Si se confirma, también obliga a reconstruir el dataset.

En seis archivos, la columna `totalEnergiaActiva` de una fila es igual a punta + fuera de punta de **otra** fila, siempre a la misma distancia:

| Archivo | Distancia en filas | Filas iguales / comparables | ¿Está en D-V6-20? |
|---|---|---|---|
| B_02 | −5 | 32 / 32 | Sí |
| B_04 | −5 | 32 / 32 | No |
| B_17 | −5 | 32 / 32 | Sí |
| B_09 | +7 | 29 / 30 | Sí |
| B_11 | +7 | 29 / 30 | Sí |
| B_16 | +7 | 29 / 30 | Sí |

La distancia −5 significa que el total de una fila repite los registros de 5 filas antes; +7, los de 7 filas después. Los otros 10 archivos tienen distancia 0 en todas sus filas.

**Qué columna es correcta:** en B09, B11 y B16 la columna `EA [kWh]` del libro iguala a los registros en 34 de 34 meses y al total impreso en 1, 0 y 0 meses. Ahí los registros están en su mes correcto. En B02, B04 y B17 no hay hoja que lo confirme: se sabe que hay un desplazamiento, no qué columna está bien. Por eso sus fichas preguntan por el total del recibo (B04 no tiene ficha).

**Efecto en el dataset:** `parse_billing_csv` escala cada mes al total impreso si difiere más de un 2 % y está entre 0,5 y 2 veces los registros (regla del propietario del 2026-11-01). Por ejemplo, B11 pasa en enero de 2023 de 51 660 kWh a 83 749 kWh, y así sale el pico de 263,7 kW de `peak_contrast.json`, frente a 168,1 kW en la hoja. B02 tiene 16 meses marcados `printed_total_implausible` entre 2023 y 2025: 12 se explican por este desplazamiento y los otros 4 (febrero a mayo de 2023) no se pueden comprobar, porque su fila de origen quedaría antes de 2023.

| kWh, dataset / registros | 2023 | 2024 | 2025 |
|---|---|---|---|
| B02 | 49 480 / 45 255 | 75 640 / 72 657 | 92 326 / 86 601 |
| B04 | 1 352 526 / 1 380 071 | 1 400 217 / 1 347 290 | 1 327 162 / 1 320 126 |
| B09 | 50 172 / 50 859 | 50 796 / 47 757 | 47 944 / 53 315 |
| B11 | 921 583 / 937 521 | 967 974 / 869 186 | 939 828 / 1 001 470 |
| B16 | 627 432 / 611 524 | 632 190 / 611 765 | 649 663 / 675 518 |
| B17 | 366 702 / 395 032 | 425 718 / 413 845 | 395 722 / 374 479 |

No se encontró este desplazamiento en las specs, los planes ni las pruebas. `TotalFacturado` podría tener el mismo problema, pero la correlación es débil (0,58 a 0,67 en B02, B16 y B17) y no lo prueba.

**Decisión del propietario:** ¿se corrige el origen de la columna, se escala solo con totales verificados o se usan los registros? ______________

## Qué pasa con la identidad de la campaña si cambia un edificio

**Cambiar un solo edificio cambia la identidad de toda la campaña.** Esto sale de leer el código; no se ejecutó ninguna reconstrucción.

**Dónde se hace el cambio:**

- El constructor copia las facturas desde `CityLearn/data/buildingcsv/` (`build_fresh_campaign_dataset.py`, líneas 73 y 99-112). Ese es un submódulo, y editarlo requiere su autorización expresa (`AGENTS.md`).
- El constructor rechaza un alias que ya existe (líneas 1364-1365). Hay que crear una campaña nueva y apuntar a ella `configs/experiments/iquitos.yaml`.
- **No basta con editar `raw/buildingcsv/` de `trial11`.** `campaign_inputs` no incluye `raw/` ni `provenance.json`, así que ese cambio no cambiaría el dataset ni lo detectaría `verify_campaign_inputs`.

**Cómo se propaga:**

| Paso | Qué cambia | Dónde |
|---|---|---|
| 1 | Los hashes de fuentes y `source_manifest_hash` | `provenance.json`, `dataset_acceptance.json` |
| 2 | El `Building_N.csv` del edificio y el hash del árbol `dataset/`, que resume todos los archivos | `construction.py`, `hash_directory` |
| 3 | Las divisiones afectadas, `split_manifest.json` y `normalizer.json`, que guarda el hash de `train_2023` | `integrity.py`, `campaign_inputs` |
| 4 | `dataset_hash` de **cada** tratamiento: los 4 algoritmos, en todos los escenarios y semillas | `fresh_campaign.py`, línea 318 |
| 5 | `input_manifest_sha256` y `spec_hash` | `fresh_campaign.py`, líneas 451 y 469 |
| 6 | Si se reutilizara un manifiesto anterior, el lanzamiento se rechaza con `dataset_changed` | `integrity.py`, líneas 135-136; `fresh_campaign.py`, línea 778 |
| 7 | Un intento de otra identidad no cuenta como completo | `fresh_campaign.py`, línea 732 |

**Además, una factura afecta a otros edificios:**

- **B06:** enero a agosto de 2023 son meses modelados con la forma estacional de los edificios completos de ese año: B02 a B17 salvo B06 y B14 (`quality_flags.csv`, línea 62; `_year_shape`). Si cambia 2023 en cualquiera de ellos, cambia B06.
- **B01:** su factura sintética toma el factor de carga de B09, B11, B12 y B17 (`configs/dataset/b01_synthetic_bill.yaml`), y el reparto de punta de oficinas pares del mismo año (`dataset_acceptance.json`).

Tras reconstruir hay que volver a pasar las 12 puertas de `dataset_acceptance.json`.

**No determinado:** si un cambio que afecte solo a 2025 altera también `train_2023` por el dimensionamiento de FV y BESS. La identidad cambia igualmente, porque cambia el árbol `dataset/`.

## Fuentes

Rutas de campaña relativas a `data/campaigns/iquitos_v6_trial11/`:

| Dato | Archivo |
|---|---|
| Facturas | `raw/buildingcsv/B_xx.csv` |
| Inventario y área | `raw/buildingcsv/building.csv` |
| Libro con hojas por institución | `raw/thesis/resultados_preliminares.xlsx`, igual byte a byte a `docs/thesis/resultados_preliminares.xlsx` |
| Física y refrigeración de `trial11` | `audit/distillation_report.csv` |
| Banderas | `quality_flags.csv` |
| Física, COP y kW de la auditoría | [`calibracion_refrigeracion_20261107/README.md`](../calibracion_refrigeracion_20261107/README.md) |

**kW térmicos por splits** = número de splits × 18 000 BTU/h = 5,275 kW cada uno (D-V6-16). El resto es sistema grande: ventilación y ocupantes.

**Saltos mensuales** = cociente de kWh por día del dataset entre meses seguidos, ≥ 1,5 o ≤ 1/1,5.

**Sumas anuales y máximos de una hoja** = suma de `EA [kWh]` y máximo de `MD [KW]` de sus filas de ese año.

**Correlación de `TotalFacturado`** = Pearson entre el monto de cada fila y los registros de la fila a cada distancia de −8 a +8, sin los meses cuyo monto por kWh se aleja más de 3 veces de la mediana del edificio. El código de abajo no la calcula.

**Reproducción:** guarde este código fuera del repositorio y ejecútelo desde su raíz. Solo lee archivos.

```
.venv39-citylearn-v3\Scripts\python.exe <ruta_fuera_del_repo>\d_v6_20.py
```

```python
import calendar, csv, sys
from pathlib import Path
import openpyxl
import pandas as pd
sys.path.insert(0, '.')
from uc3m.application.dataset import construction as cn
C = Path('data/campaigns/iquitos_v6_trial11'); RAW = C/'raw/buildingcsv'
inv = pd.read_csv(RAW/'building.csv').set_index('ID_Edificio')
rep = pd.read_csv(C/'audit/distillation_report.csv')
book = openpyxl.load_workbook(C/'raw/thesis/resultados_preliminares.xlsx', read_only=True, data_only=True)
sheets = {}
for ws in book.worksheets:
    rows = list(ws.iter_rows(values_only=True, max_col=5))
    if rows and rows[0] and rows[0][0] == 'NOMBRES':
        sheets[ws.title] = {(int(r[1]), int(r[2])): (r[3], r[4]) for r in rows[1:]
                            if r[0] and isinstance(r[1], (int, float)) and isinstance(r[2], (int, float))
                            and r[1] > 2000 and 1 <= r[2] <= 12}
def printed(b):
    rows = list(csv.reader(cn._read_text(RAW/f'B_{b:02d}.csv').splitlines(), delimiter=';'))
    head = [cn._key(h) for h in rows[0]]; m = head.index('mes')
    t = [i for i, h in enumerate(head) if 'totalenergia' in h][0]
    return [((int(r[m+1]), cn.MONTHS[r[m].strip().casefold()[:3]]), cn._number(r[t]))
            for r in rows[1:] if len(r) > m and r[m].strip()]
for b in range(2, 18):
    raw = cn.parse_billing_csv(RAW/f'B_{b:02d}.csv', b)
    scaled = cn.parse_billing_csv(RAW/f'B_{b:02d}.csv', b, scale_tou_to_printed_total=True)
    reg = {(r.year, r.month): r.energy_kwh for r in raw}; pr = printed(b); keys = [k for k, _ in pr]
    area = float(inv.loc[f'B_{b:02d}', 'Area_Techada_m2'])
    print(f'B{b:02d} area={area}', inv.loc[f'B_{b:02d}', 'Nombre_Edificio'])
    for y in (2023, 2024, 2025):
        e = sum(r.energy_kwh for r in raw if r.year == y); d = sum(r.energy_kwh for r in scaled if r.year == y)
        s = rep[(rep.building_id == b) & (rep.year == y)]
        bill = s.E_peak_medido_kWh.sum() + s.E_offpeak_medido_kWh.sum()
        phys = s.E_peak_cooling_fisico_kWh.sum() + s.E_offpeak_cooling_fisico_kWh.sum()
        hours = 8784 if y == 2024 else 8760
        peak = max((r.energy_kwh/(r.load_factor*calendar.monthrange(y, r.month)[1]*24)
                    for r in raw if r.year == y and r.load_factor), default=0)
        print(f'  {y} registros={e:.0f} dataset={d:.0f} kWh/m2={e/area:.1f} kW={e/hours:.1f} W/m2={e/hours/area*1000:.2f} '
              f'pico_implicito={peak:.1f} fisica={phys:.0f} fisica/factura={phys/bill*100 if bill else 0:.1f}%')
    lags = {}
    for i, (_, v) in enumerate(pr):
        for j, k in enumerate(keys):
            if v and abs(reg[k] - v) <= max(.02, 1e-5*v):
                lags[j - i] = lags.get(j - i, 0) + 1
    print('  distancia_total_impreso', sorted(lags.items(), key=lambda x: -x[1])[:2])
    match = {n: sum(1 for k, (e, _) in d.items() if k in reg and e and abs(e/reg[k] - 1) < .001) for n, d in sheets.items()}
    print('  hojas_coincidentes', {n: c for n, c in match.items() if c})
t5, t7 = sheets['6.H.REGIONAL.T1'], sheets['6.H.REGIONAL']
e5, e7 = sum(t5[k][0] for k in t7), sum(t7[k][0] for k in t7)
s = rep[(rep.building_id == 11) & (rep.year == 2025) & rep.mes.isin([k[1] for k in t7])]
phys = s.E_peak_cooling_fisico_kWh.sum() + s.E_offpeak_cooling_fisico_kWh.sum()
print('B11 feb-oct 2025', e5, e7, e5 + e7, (e5 + e7)/e5, phys, phys/e5, phys/(e5 + e7))
