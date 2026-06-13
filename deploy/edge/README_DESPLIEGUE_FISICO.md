# Despliegue físico / edge (demo Fase 8) — guía de referencia

> **Estado**: plan de referencia, no ejecutado. No hay hardware físico
> conectado en esta sesión. Documenta cómo llevar el stack de
> `deploy/` desde la demo en replay hacia un piloto con planta real
> (microrred de uno o más de los 17 edificios de Iquitos).

## Objetivo

Sustituir `plant-adapter` en modo `replay` (dataset histórico) por un
adapter que lea/escriba sobre el EMS/BMS real del edificio, manteniendo
`inference` y `dashboard` sin cambios.

## Topología propuesta

```
[Sensores/medidores] --Modbus/OPC-UA--> [plant-adapter (modo modbus/opcua)]
                                              |  HTTP /act
                                              v
                                        [inference service]
                                              |  MQTT (opcional)
                                              v
                                          [dashboard]
```

El `inference` y `dashboard` pueden seguir corriendo en la nube (AWS, ver
`../aws/README_DEPLOY_AWS.md`) o localmente en un gateway/edge device
(p. ej. un mini-PC o PLC industrial con Docker) ubicado en el edificio.

## Pasos de migración (replay -> piloto físico)

1. **Inventario de puntos de medición/control por edificio**
   - Identificar qué variables del BACTTensor (29D, ver `uc3m/env/bact.py`)
     tienen un sensor/actuador físico equivalente (SOC batería, potencia PV,
     carga, setpoints de carga EV, etc.).
   - Documentar protocolo disponible: Modbus TCP/RTU, OPC-UA, o pasarela MQTT
     propietaria.

2. **Completar `deploy/plant-adapter/modbus_adapter.py` (o un nuevo
   `opcua_adapter.py`)**
   - Rellenar `REGISTER_MAP` (o el equivalente OPC-UA NodeIds) con las
     direcciones reales por edificio/dispositivo.
   - Validar el mapeo observación física -> `obs_dim` esperado por el modelo
     (`GET /model/info`).
   - Añadir límites de seguridad: clamping de setpoints, modo
     "manual override" para que el operador pueda desactivar el control
     automático en cualquier momento.

3. **Pruebas en modo "shadow" (solo lectura)**
   - Ejecutar el adapter leyendo del EMS real y llamando a `/act`, pero SIN
     escribir setpoints — solo loggear/comparar las acciones recomendadas
     contra la operación manual actual.
   - Duración recomendada: al menos 1-2 semanas para cubrir variabilidad
     diaria/estacional, antes de pasar a control activo.

4. **Activación gradual del control**
   - Habilitar escritura de setpoints (`write_actions`) para un subconjunto
     reducido de dispositivos/edificios primero.
   - Mantener un mecanismo de "kill switch" (manual o por timeout de
     comunicación) que regrese el sistema a operación manual si
     `inference` o `plant-adapter` deja de responder.

5. **Monitoreo continuo**
   - Usar `deploy/dashboard` (o el dashboard ya desplegado en AWS) para
     visualizar acciones aplicadas, estado del modelo (`is_stub` debe ser
     `false` en producción) y health checks.
   - Definir alertas (CloudWatch Alarms si se usa la variante AWS, o
     alertas locales) sobre `ADAPTER_MODE`, latencia de `/act`, y
     desconexiones Modbus/OPC-UA.

## Requisitos de seguridad y operación

- Aislar la red del EMS/BMS del resto de la red corporativa (VLAN dedicada).
- El gateway/edge device que ejecuta `plant-adapter` debe tener acceso de
  red tanto al EMS local como al `inference` (local o en AWS vía VPN/Site-to-
  Site si aplica).
- Documentar y probar el procedimiento de rollback a operación manual antes
  de cualquier prueba en planta real.

## Estado actual del proyecto

- `deploy/plant-adapter/modbus_adapter.py` es un **esqueleto**: `REGISTER_MAP`
  está vacío y debe completarse con el inventario real (paso 1).
- No existe aún un adapter OPC-UA (`asyncua` está incluido en
  `deploy/plant-adapter/requirements.txt` como dependencia preparada, pero
  el módulo no se ha escrito). Seguir el mismo patrón que
  `modbus_adapter.py` cuando se implemente.
- Esta guía debe actualizarse con direcciones de registros y resultados de
  las pruebas "shadow" una vez disponibles.
