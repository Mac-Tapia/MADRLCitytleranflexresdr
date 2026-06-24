# Informe Vigente de Auditoria de Parametros de Edificios Iquitos

**Dataset auditado:** `CityLearn/data/datasets/citylearn_iquitos_2023_2025`
**Fecha vigente:** 2026-06-12
**Fuente canonica:** `outputs/dataset_audit/der_sizing_audit.csv`

Este informe reemplaza la auditoria antigua de parametros. Los valores de PV, BESS y EV no deben tomarse de tablas preliminares ni de logs historicos. La fuente valida es la auditoria DER generada despues de la orquestacion completa del dataset.

## Totales Vigentes

| Componente | Valor |
|---|---:|
| Edificios | 17 |
| PV total | 48,790.9 kWp |
| BESS total | 26,266.0 kWh / 6,648.0 kW |
| EV total | 185 tomas / 96 equipos modo 3 doble toma / 1,850 EV en pool / 749.4 kW |
| Maquinas controladas | 17 |
| Energia maquinas controladas | 876.6 MWh |
| CSV activos auditados | 222 |
| NaN/Inf | 0 |

## Cuadro Vigente por Edificio

| ID | Edificio | Tipo | Area m2 | PV kWp | BESS kWh | BESS kW | EV kW | EV count | Maquina MWh |
|---|---|---|---:|---:|---:|---:|---:|---:|---:|
| B01 | ELECTRO ORIENTE S.A. | Office | 14,000.00 | 3,360.2 | 6,747.0 | 1,609.0 | 21.8 | 4 | 11.6 |
| B02 | MUNICIPALIDAD DISTRITAL DE SAN JUAN BAUTISTA | Office | 8,000.00 | 1,920.0 | 244.0 | 50.0 | 24.4 | 6 | 27.9 |
| B03 | AEROPUERTO INTERNACIONAL | Assembly | 6,000.00 | 1,440.2 | 2,363.0 | 511.0 | 37.8 | 8 | 104.1 |
| B04 | HIPERMERCADOS TOTTUS ORIENTE SAC | Retail | 2,500.00 | 600.2 | 454.0 | 409.0 | 24.4 | 6 | 24.3 |
| B05 | HOTEL PLAZA S.A. | MultiFamily_Hotel | 1,141.89 | 274.1 | 234.0 | 124.0 | 14.4 | 3 | 108.5 |
| B06 | MALL AVENTURA S.A. | Commercial_Mall | 20,637.00 | 4,952.9 | 2,541.0 | 835.0 | 119.6 | 32 | 192.9 |
| B07 | UNAP-FACULTAD DE BIOLOGIA-AULAS | Education | 8,103.45 | 1,944.9 | 984.0 | 240.0 | 153.2 | 42 | 30.7 |
| B08 | PNP- ESCUELA TECNICA SUPERIOR-IQUITOS | Assembly_Military | 21,000.00 | 5,040.2 | 601.0 | 129.0 | 73.6 | 17 | 77.8 |
| B09 | GOBIERNO REGIONAL DE LORETO - COER | Office_Critical | 4,479.67 | 1,075.3 | 138.0 | 30.0 | 37.4 | 10 | 13.3 |
| B10 | GOBIERNO REGIONAL DE LORETO | Office | 14,295.73 | 3,431.1 | 2,353.0 | 591.0 | 36.6 | 6 | 17.4 |
| B11 | HOSPITAL REGIONAL DE LORETO | Healthcare_Hospital | 42,649.33 | 10,236.1 | 1,901.0 | 424.0 | 14.4 | 3 | 80.0 |
| B12 | SEGURO SOCIAL DE SALUD - ESSALUD | Healthcare | 18,197.48 | 4,367.5 | 4,346.0 | 960.0 | 14.4 | 3 | 37.8 |
| B13 | UNAP-FACULTAD DE CIENCIAS AD..CONTABLES Y ECO | Education | 2,723.00 | 653.8 | 272.0 | 69.0 | 41.4 | 11 | 11.6 |
| B14 | AUTORIDAD PORTUARIA NACIONAL | Industrial_Port | 17,761.00 | 4,262.9 | 229.0 | 48.0 | 21.8 | 4 | 51.5 |
| B15 | DREL- COLEGIO NACIONAL DE IQUITOS | Education | 9,889.92 | 2,373.8 | 500.0 | 104.0 | 31.4 | 8 | 18.3 |
| B16 | SIMA - IQUITOS S.R.LTDA | Industrial | 10,294.00 | 2,470.8 | 1,622.0 | 357.0 | 41.4 | 11 | 40.1 |
| B17 | ASOCIACION CIVIL SELVA AMAZONICA | Laboratory | 1,611.23 | 386.9 | 737.0 | 158.0 | 41.4 | 11 | 28.8 |

## Conclusiones Tecnicas

- B01 ya no usa valores preliminares: su PV vigente es 3,360.2 kWp y su BESS vigente es 6,747.0 kWh / 1,609.0 kW.
- El BESS se dimensiona por edificio usando balance de PV, carga del edificio, EV, cargas controladas y red publica.
- La asignacion EV vigente proviene de `outputs/dataset_audit/ev_charger_sizing_audit.csv` y queda sincronizada con `schema.json`.
- No se deben usar tablas preliminares antiguas de EV, BESS o PV para entrenamiento ni tesis.
