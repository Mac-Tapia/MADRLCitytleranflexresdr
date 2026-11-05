# Contrato v1 y conciliación con PT_TAPIA_ZAMBRANO

Fecha: 2026-11-01. Resolución del propietario en esta sesión: **«Conservar el contrato actual v1 y documentar explícitamente sus diferencias con el PT»**. Resuelve D01–D04 del plan integrado. Este registro no autoriza etapas largas ni acredita resultados científicos.

## Contrato que se conserva

La configuración canónica es `configs/experiments/iquitos.yaml`: campaña `fresh_iquitos_20261101_v1`, dataset `data/campaigns/iquitos_v1`, 17 edificios/agentes, cuatro backends HAPPO/MASAC/MATD3/MAAC y escenarios E1/E2/E3. Se mantienen `train_2023`, `validation_2024`, `test_2025` y el normalizador ajustado exclusivamente con entrenamiento. No se adopta v2/v3 ni se modifica la flota, la tarifa o el control físico como efecto secundario de la remediación.

La fuente única de prioridades es `configs/objective_policies.yaml`, en orden flexibilidad/CO2/costo: E1=(0.60,0.15,0.25), E2=(0.25,0.60,0.15), E3=(0.15,0.25,0.60). Son prioridades compensatorias del proyecto; la suma ponderada no implementa prioridades lexicográficas ni demuestra un óptimo global. El perfil efectivo es `thesis_indicators_v7`, con pago común `team_mean` y penalizaciones EV/BESS fuera del vector de ejes. DSO, demanda facturada y desviación de precio con peso cero no se anuncian como objetivos activos.

`configs/scenarios.yaml` conserva `tariff_policies.baseline.mode=flat`. El precio de la simulación se transforma a tarifa media; este experimento no demuestra arbitraje TOU. Deben distinguirse el KPI de costo energético, su referencia de exportación/net billing y la liquidación del mercado comunitario v1. Ninguno equivale automáticamente a una factura comercial ni a ahorro monetario observado.

Los CSV brutos sí contienen variación de precio. La inaplicabilidad de `price_signal_deviation` deriva del precio **efectivo tras aplicar `flat`**, no de afirmar que los CSV sean constantes. Al preparar la campaña se congelan los rangos y hashes de precio, la huella de la política tarifaria y la declaración de aplicabilidad. Los 26 KPI comparables siguen visibles; bajo esa tarifa, 25 pueden ser aplicables y la respuesta inversa al precio se informa como no aplicable, sin cero imputado ni prueba estadística. No se permite excluir un eje confirmatorio ni declarar esta excepción después de ver resultados.

El backcast de B01 2023 a partir de 2024 se conserva como tratamiento modelado declarado, con amenaza a la validez temporal y sensibilidad/exclusión que debe reportarse. No se presenta como medición histórica independiente ni como separación temporal estricta de toda la construcción de datos.

## Diferencias que deben aparecer en la tesis

| Tema | PT / antecedente | Contrato conservado y consecuencia |
|---|---|---|
| Dimensiones | Observación aproximada de 40, estado de 680 y acciones 2–5 | La medición del adaptador común registrada en la auditoría es estado 1652, observaciones aumentadas 45–357, padding 357 y acción física local 5–44. Se debe regenerar desde el dataset, no copiar cifras del PT |
| Crítico centralizado | Una sola entrada global uniforme | HAPPO/MASAC usan el estado común; MATD3 declara 17×357=6069 con padding; MAAC emplea su arquitectura de atención. No se igualan capacidades por etiqueta |
| Control | HVAC y flota del documento | HVAC inactivo y BESS/EV/lavadora activos según schema v1. Los cargadores pertenecen al edificio, no son agentes extra |
| Flota | 50 cargadores | El inventario v1 documentado tiene 185 cargadores y 1850 vehículos. v2/v3 tienen otra flota y no se consideran activos en este contrato |
| Acciones | MASAC continuo / controles comparables | MASAC y MAAC usan 89 IDs discretos axis; HAPPO y MATD3 controles continuos. La tabla discreta restringe combinaciones y contiene redundancia en edificios pequeños |
| Recompensa | Pesos y mezcla individual/equipo de tablas anteriores | Pesos canónicos actuales y pago común v7; no una mezcla diferente por algoritmo |
| Tarifa | TOU y arbitraje temporal | Tarifa media plana del escenario; no atribuir resultados al arbitraje TOU |
| HPO | Optuna/TPE | Grilla actual de 8 configuraciones por backend. El recorte anterior de MASAC y las 252 celdas son antecedentes; el DAG auditado actual tiene 288 HPO |
| Réplicas | Semilla 0 / corridas anteriores | Doce semillas confirmatorias independientes; resultados anteriores retirados no son réplicas de la campaña nueva |
| Ejecución | Local/Docker/AWS descritos históricamente | CLI nativa única con Colab como cliente. Entrenamiento AWS retirado. Etapas autorizadas vacías hasta decisión explícita |

Las cifras dimensionales proceden de `docs/audits/architecture_thesis_20261101/runtime_probe.json` y del cableado de wrappers documentado en el informe. Son medidas de ese corte, no una nueva campaña ni lectura de todas las activaciones internas. Su regeneración y readback forman parte de I02/I04.

La comparación científica se formula entre **implementaciones con sus respectivos contratos de acción**, conservando y declarando ese confusor. No se atribuye superioridad intrínseca de un algoritmo a una diferencia que pueda explicarse por expresividad de acciones, capacidad del crítico, replay o presupuesto de actualización. Para una comparación causal con acciones equivalentes haría falta un protocolo nuevo y, posiblemente, cambios autorizados en dependencias.

## Tupla y representación computacional

Para cada escenario fijo `e`, se usa la familia:

`M_e = <N, S, {A_i}, P, r_e, {O_i}, Z, rho_0, gamma, H>`.

- `N={1,…,17}` identifica edificios. `S` es el estado latente suficiente del simulador, con estados físicos, tiempo, exógenas, memoria de recompensa y estado aleatorio que corresponda. La concatenación de observaciones no prueba por sí sola Markovianidad.
- `z_t=g(s_t)` es la información del crítico y se documenta por backend; no se confunde con `S` ni se entrega automáticamente al actor durante ejecución descentralizada.
- `O_i` y `Z` describen la información local y su ley de observación, incluyendo normalización, códigos EV y padding. Los códigos EV no son el BACT de otra ruta del proyecto.
- `A_i` es la acción física. Cada backend define un espacio de política `U_i^(b)` y una decodificación `D_i^(b):U_i^(b)→A_i`; el caso discreto representa un subconjunto de combinaciones.
- `P` es la dinámica condicionada a datos/acciones/semilla; no se inventa ruido. `rho_0` declara condiciones de reset, split e inicialización. La política general depende de la historia local `tau_i,t`; una política reactiva es una restricción implementada, no la definición general del Dec-POMDP.
- `r_e` es el pago común efectivo v7. `gamma` pertenece a los hiperparámetros congelados, con candidatos 0.99/0.9999. `H` separa estados/filas, decisiones y flujos medidos; la corrección de la frontera anual se verifica en I06 sin fabricar una hora adicional.

## Presupuesto, distribución y aceptación

D05 conserva la grilla y fases actuales; su presupuesto se recalcula del YAML y se mide antes de habilitar etapas. Los 119941920 pasos de la auditoría son planificación, no trabajo ejecutado ni estimación de duración. Los requisitos de memoria de MASAC deben verificarse por tratamiento; no se presume que una GPU de 80 GB satisfaga una reserva de 82 GiB.

Para D06 se adopta como decisión técnica el checkout fijado con dependencias locales para entrenamiento nativo, y wheel del núcleo para los casos de uso que puedan operar con entradas explícitas. La entrega no dependerá de importar `tools` desde el wheel. ONNX queda como extensión pendiente, sin anunciar exportador ni ganador inexistentes. Configurar patrones LFS no implica que ya existan archivos LFS; no se reescribe historia ni se migra el Word automáticamente.

Se mantienen separadas conformidad de contratos, aprendizaje real, evaluación congelada, aceptación científica y operación física. La ejecución de pruebas sintéticas de integridad no es entrenamiento. La campaña nueva solo podrá cerrarse con cobertura exacta, evidencia nativa, evaluación final, baselines, sensibilidad e inferencia válidos; un resultado sin diferencias o sin ganador es admisible.

## Fundamento y límites

Costea (2026) respalda comparar energía/costo/carbono y baselines por edificio/distrito en CityLearn; su tesis compara variantes PPO y no prescribe nuestros pesos ni estos cuatro backends. [Tesis de maestría, Politecnico di Torino](https://webthesis.biblio.polito.it/40396/).

Charbonnier (2023) aporta el contexto de coordinación de flexibilidad mediante MARL; la ficha doctoral no certifica el dataset ni los resultados de Iquitos. [Tesis doctoral, Oxford](https://ora.ox.ac.uk/objects/uuid%3A4acf19ee-76b3-4e71-a424-259cd9e2d6f5).

Oliehoek, Spaan y Vlassis (2008) sustentan distribución inicial, observaciones e historias de políticas Dec-POMDP; no demuestran que el vector del crítico de este código sea un estado suficiente. [Artículo JAIR](https://people.csail.mit.edu/fao/docs/Oliehoek08JAIR.pdf).

La custodia del protocolo/código/datos y los límites de reproducción se apoyan en Pineau et al. (2021). La indexación específica y bibliografía complementaria están delimitadas en el plan integrado; las tesis no se presentan como artículos indexados. [Artículo JMLR](https://www.jmlr.org/papers/v22/20-303.html).
