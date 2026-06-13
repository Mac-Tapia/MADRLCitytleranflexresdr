"""Dashboard Streamlit (demo Fase 8) para el stack MADRL Iquitos.

Muestra:
- Estado/metadatos del servicio de inferencia (`GET /model/info`, `/health`)
- Últimas acciones recibidas vía MQTT (publicadas por plant-adapter en modo
  ``ADAPTER_PUBLISH_MQTT=true``)
- Formulario manual para invocar `/act` con observaciones de prueba

Ejecutar localmente:
    streamlit run app.py --server.port 8501
"""
from __future__ import annotations

import json
import os
import threading
from collections import deque

import pandas as pd
import requests
import streamlit as st

INFERENCE_URL = os.environ.get("INFERENCE_SERVICE_URL", "http://inference:8000")
MQTT_HOST = os.environ.get("MQTT_HOST", "mqtt-broker")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "1883"))
MQTT_TOPIC = os.environ.get("MQTT_TOPIC_PREFIX", "madrl-iquitos") + "/actions"

st.set_page_config(page_title="MADRL Iquitos — Dashboard", layout="wide")
st.title("MADRL Iquitos — Panel de monitoreo (demo)")

# --- Estado del servicio de inferencia -------------------------------------
st.header("Servicio de inferencia")
col1, col2 = st.columns(2)

with col1:
    try:
        health = requests.get(f"{INFERENCE_URL}/health", timeout=5).json()
        st.success(f"/health -> {health}")
    except requests.RequestException as exc:
        st.error(f"No se pudo contactar {INFERENCE_URL}/health: {exc}")

with col2:
    try:
        info = requests.get(f"{INFERENCE_URL}/model/info", timeout=5).json()
        st.json(info)
    except requests.RequestException as exc:
        st.warning(f"No se pudo obtener /model/info: {exc}")


# --- Stream de acciones vía MQTT --------------------------------------------
st.header("Últimas acciones (MQTT)")

if "mqtt_messages" not in st.session_state:
    st.session_state.mqtt_messages = deque(maxlen=200)
    st.session_state.mqtt_started = False


def _start_mqtt_listener() -> None:
    try:
        import paho.mqtt.client as mqtt
    except ImportError:
        return

    def on_message(_client, _userdata, msg):
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return
        st.session_state.mqtt_messages.append(payload)

    client = mqtt.Client()
    client.on_message = on_message
    try:
        client.connect(MQTT_HOST, MQTT_PORT)
    except Exception:
        return
    client.subscribe(MQTT_TOPIC)
    client.loop_start()


if not st.session_state.mqtt_started:
    threading.Thread(target=_start_mqtt_listener, daemon=True).start()
    st.session_state.mqtt_started = True

if st.session_state.mqtt_messages:
    df = pd.DataFrame(list(st.session_state.mqtt_messages))
    st.dataframe(df.tail(20), use_container_width=True)
else:
    st.info(
        "No se han recibido mensajes MQTT aún. "
        "Asegúrate de que plant-adapter corra con ADAPTER_PUBLISH_MQTT=true."
    )


# --- Invocación manual de /act ----------------------------------------------
st.header("Invocar /act manualmente")
st.caption("Observaciones de prueba: matriz (n_agents x obs_dim), separadas por filas.")

default_obs = "0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0,0"
n_agents = st.number_input("Número de agentes/edificios", min_value=1, max_value=17, value=1)
obs_text = st.text_area("Fila de observación (CSV, se repite para cada agente)", value=default_obs)

if st.button("Llamar /act"):
    try:
        row = [float(x) for x in obs_text.split(",")]
        observations = [row for _ in range(int(n_agents))]
        resp = requests.post(f"{INFERENCE_URL}/act", json={"observations": observations}, timeout=10)
        resp.raise_for_status()
        st.json(resp.json())
    except Exception as exc:  # pragma: no cover - UI feedback
        st.error(f"Error llamando /act: {exc}")
