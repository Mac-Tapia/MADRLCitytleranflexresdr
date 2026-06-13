"""Plant-adapter en modo *replay* (demo Fase 8).

Reproduce el dataset CityLearn Iquitos (17 edificios, 2023-2025) fila a fila,
construye observaciones por edificio y consulta al servicio de inferencia
(`POST /act`) para obtener las acciones de control. No actúa sobre hardware
real: imprime/loggea las acciones recibidas y opcionalmente las publica por
MQTT para alimentar el dashboard.

Variables de entorno (ver ../.env.example):
- INFERENCE_SERVICE_URL   (default http://inference:8000)
- REPLAY_DATASET_DIR      (default /data/citylearn_iquitos_2023_2025)
- REPLAY_SPEED            (factor de velocidad, default 1.0 = tiempo real x1)
- STEP_INTERVAL_SECONDS   (segundos simulados por paso, default 3600)
- MQTT_HOST / MQTT_PORT / MQTT_TOPIC_PREFIX (opcional, si ADAPTER_PUBLISH_MQTT=true)
"""
from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

logging.basicConfig(level=os.environ.get("LOG_LEVEL", "info").upper())
logger = logging.getLogger("plant-adapter.replay")

INFERENCE_URL = os.environ.get("INFERENCE_SERVICE_URL", "http://inference:8000")
DATASET_DIR = Path(os.environ.get("REPLAY_DATASET_DIR", "/data/citylearn_iquitos_2023_2025"))
REPLAY_SPEED = float(os.environ.get("REPLAY_SPEED", "1.0"))
STEP_INTERVAL_SECONDS = float(os.environ.get("STEP_INTERVAL_SECONDS", "3600"))
PUBLISH_MQTT = os.environ.get("ADAPTER_PUBLISH_MQTT", "false").lower() == "true"

SCHEMA_PATH = DATASET_DIR / "schema.json"


def load_schema() -> dict:
    if not SCHEMA_PATH.is_file():
        raise FileNotFoundError(
            f"No se encontró schema.json en {SCHEMA_PATH}. "
            "Monta el dataset CityLearn Iquitos en REPLAY_DATASET_DIR."
        )
    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_building_frames(schema: dict) -> dict[str, pd.DataFrame]:
    """Carga el CSV de cada edificio definido en el schema."""
    frames: dict[str, pd.DataFrame] = {}
    buildings = schema.get("buildings", {})
    for name, info in buildings.items():
        if not info.get("include", True):
            continue
        csv_name = info.get("energy_simulation")
        if not csv_name:
            continue
        csv_path = DATASET_DIR / csv_name
        if not csv_path.is_file():
            logger.warning("CSV no encontrado para %s: %s (se omite)", name, csv_path)
            continue
        frames[name] = pd.read_csv(csv_path)
    if not frames:
        raise RuntimeError("No se cargó ningún CSV de edificio — revisa REPLAY_DATASET_DIR/schema.json")
    return frames


def build_observations(frames: dict[str, pd.DataFrame], step: int, obs_dim: int) -> np.ndarray:
    """Construye un array (n_agents, obs_dim) a partir de la fila `step` de cada edificio.

    Esta es una proyección simplificada para la demo: toma las primeras
    `obs_dim` columnas numéricas disponibles y rellena con ceros si faltan.
    El mapeo real observación->BACTTensor (29D) vive en `uc3m/env/bact.py`
    y debería usarse aquí cuando se exporte el modelo real.
    """
    n_agents = len(frames)
    obs = np.zeros((n_agents, obs_dim), dtype=np.float32)
    for i, (_name, df) in enumerate(frames.items()):
        row = df.iloc[step % len(df)]
        numeric = row.select_dtypes(include="number") if hasattr(row, "select_dtypes") else row
        values = np.asarray(pd.to_numeric(row, errors="coerce").fillna(0.0).values, dtype=np.float32)
        n = min(obs_dim, len(values))
        obs[i, :n] = values[:n]
    return obs


def call_inference(observations: np.ndarray) -> dict:
    resp = requests.post(
        f"{INFERENCE_URL}/act",
        json={"observations": observations.tolist()},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


def maybe_publish_mqtt(client, topic_prefix: str, step: int, result: dict) -> None:
    if client is None:
        return
    payload = json.dumps({"step": step, **result})
    client.publish(f"{topic_prefix}/actions", payload)


def main() -> None:
    schema = load_schema()
    frames = load_building_frames(schema)
    logger.info("Replay adapter iniciado con %d edificios desde %s", len(frames), DATASET_DIR)

    # obs_dim se obtiene del servicio de inferencia para mantener consistencia
    info = requests.get(f"{INFERENCE_URL}/model/info", timeout=10).json()
    obs_dim = int(info.get("obs_dim", 29))
    logger.info("Modelo activo: algorithm=%s scenario=%s obs_dim=%d is_stub=%s",
                info.get("algorithm"), info.get("scenario"), obs_dim, info.get("is_stub"))

    mqtt_client = None
    topic_prefix = os.environ.get("MQTT_TOPIC_PREFIX", "madrl-iquitos")
    if PUBLISH_MQTT:
        import paho.mqtt.client as mqtt

        mqtt_client = mqtt.Client()
        mqtt_client.connect(
            os.environ.get("MQTT_HOST", "mqtt-broker"),
            int(os.environ.get("MQTT_PORT", "1883")),
        )
        mqtt_client.loop_start()

    n_steps = max(len(df) for df in frames.values())
    sleep_seconds = STEP_INTERVAL_SECONDS / max(REPLAY_SPEED, 1e-6)

    for step in range(n_steps):
        obs = build_observations(frames, step, obs_dim)
        try:
            result = call_inference(obs)
        except requests.RequestException as exc:
            logger.error("Fallo al llamar al servicio de inferencia: %s", exc)
            time.sleep(sleep_seconds)
            continue

        logger.info("step=%d actions=%s", step, result.get("actions"))
        maybe_publish_mqtt(mqtt_client, topic_prefix, step, result)
        time.sleep(sleep_seconds)


if __name__ == "__main__":
    main()
