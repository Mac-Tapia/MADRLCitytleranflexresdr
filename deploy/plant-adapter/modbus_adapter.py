"""Plant-adapter stub para integración Modbus TCP con un EMS/BMS real (Fase 8 demo).

Este módulo es un ESQUELETO: define la estructura de un ciclo de lectura de
registros Modbus -> construcción de observaciones -> llamada a
`/act` -> escritura de setpoints, pero no se ha probado contra hardware real.
Antes de usarlo en planta:

1. Definir el mapa de registros (holding registers) por edificio/dispositivo
   en `REGISTER_MAP` (direcciones, escalas, tipos de dato).
2. Validar el mapeo observación->BACTTensor con `uc3m/env/bact.py`.
3. Añadir manejo de reconexión/timeout robusto y límites de seguridad
   (clamping de setpoints, modo manual/override).

Variables de entorno (ver ../.env.example):
- INFERENCE_SERVICE_URL
- MODBUS_HOST, MODBUS_PORT, MODBUS_UNIT_ID
- STEP_INTERVAL_SECONDS
"""
from __future__ import annotations

import logging
import os
import time

import numpy as np
import requests

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper())
logger = logging.getLogger("plant-adapter.modbus")

INFERENCE_URL = os.environ.get("INFERENCE_SERVICE_URL", "http://inference:8000")
MODBUS_HOST = os.environ.get("MODBUS_HOST", "127.0.0.1")
MODBUS_PORT = int(os.environ.get("MODBUS_PORT", "502"))
MODBUS_UNIT_ID = int(os.environ.get("MODBUS_UNIT_ID", "1"))
STEP_INTERVAL_SECONDS = float(os.environ.get("STEP_INTERVAL_SECONDS", "3600"))

# TODO: completar con el mapa real de registros por edificio/dispositivo.
# Ejemplo de estructura propuesta:
# REGISTER_MAP = {
#     "building_1": {
#         "read": {"soc_battery": 30001, "pv_power": 30003, "load_power": 30005},
#         "write": {"battery_setpoint": 40001, "ev_charge_setpoint": 40003},
#         "scale": 0.1,  # factor de escala registro -> unidad física
#     },
#     ...
# }
REGISTER_MAP: dict = {}


def read_observations(client) -> np.ndarray:
    """Lee los registros configurados en REGISTER_MAP y construye observaciones.

    Placeholder: retorna ceros hasta que REGISTER_MAP esté definido.
    """
    n_agents = max(len(REGISTER_MAP), 1)
    obs_dim = 29  # BACTTensor; ajustar según metadata del modelo
    obs = np.zeros((n_agents, obs_dim), dtype=np.float32)
    if not REGISTER_MAP:
        logger.warning("REGISTER_MAP vacío — devolviendo observaciones en cero (placeholder).")
        return obs

    for i, (name, cfg) in enumerate(REGISTER_MAP.items()):
        scale = cfg.get("scale", 1.0)
        for j, (_field, address) in enumerate(cfg.get("read", {}).items()):
            if j >= obs_dim:
                break
            result = client.read_holding_registers(address, 1, unit=MODBUS_UNIT_ID)
            if result.isError():
                logger.error("Error leyendo registro %s (%s) en %s", address, _field, name)
                continue
            obs[i, j] = result.registers[0] * scale
    return obs


def write_actions(client, actions: np.ndarray) -> None:
    """Escribe las acciones recibidas como setpoints Modbus.

    Placeholder: solo loggea hasta que REGISTER_MAP esté definido.
    """
    if not REGISTER_MAP:
        logger.info("write_actions (placeholder, sin REGISTER_MAP): %s", actions.tolist())
        return

    for i, (name, cfg) in enumerate(REGISTER_MAP.items()):
        scale = cfg.get("scale", 1.0)
        for j, (_field, address) in enumerate(cfg.get("write", {}).items()):
            if j >= actions.shape[1]:
                break
            value = int(round(float(actions[i, j]) / scale))
            result = client.write_register(address, value, unit=MODBUS_UNIT_ID)
            if result.isError():
                logger.error("Error escribiendo registro %s (%s) en %s", address, _field, name)


def call_inference(observations: np.ndarray) -> dict:
    resp = requests.post(
        f"{INFERENCE_URL}/act",
        json={"observations": observations.tolist()},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def main() -> None:
    from pymodbus.client import ModbusTcpClient

    client = ModbusTcpClient(MODBUS_HOST, port=MODBUS_PORT)
    if not client.connect():
        raise ConnectionError(f"No se pudo conectar al servidor Modbus {MODBUS_HOST}:{MODBUS_PORT}")

    logger.info("Conectado a Modbus TCP %s:%s (unit=%s)", MODBUS_HOST, MODBUS_PORT, MODBUS_UNIT_ID)
    if not REGISTER_MAP:
        logger.warning(
            "REGISTER_MAP no está configurado. Este adapter corre en modo placeholder "
            "(observaciones en cero, acciones solo logueadas). Completar antes de uso en planta."
        )

    try:
        while True:
            obs = read_observations(client)
            try:
                result = call_inference(obs)
            except requests.RequestException as exc:
                logger.error("Fallo al llamar al servicio de inferencia: %s", exc)
                time.sleep(STEP_INTERVAL_SECONDS)
                continue

            actions = np.asarray(result["actions"], dtype=np.float32)
            write_actions(client, actions)
            logger.info("Ciclo completado. actions=%s", actions.tolist())
            time.sleep(STEP_INTERVAL_SECONDS)
    finally:
        client.close()


if __name__ == "__main__":
    main()
