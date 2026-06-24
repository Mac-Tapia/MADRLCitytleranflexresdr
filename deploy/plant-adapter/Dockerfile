FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY replay_adapter.py modbus_adapter.py ./

ENV INFERENCE_SERVICE_URL=http://inference:8000 \
    ADAPTER_MODE=replay \
    REPLAY_DATASET_DIR=/data/citylearn_iquitos_2023_2025 \
    REPLAY_SPEED=1.0 \
    STEP_INTERVAL_SECONDS=3600 \
    LOG_LEVEL=info

# El modo se selecciona vía ADAPTER_MODE (replay|modbus|opcua). Por defecto
# se ejecuta el adapter de replay, que no requiere hardware.
CMD ["sh", "-c", "if [ \"$ADAPTER_MODE\" = \"modbus\" ]; then python modbus_adapter.py; else python replay_adapter.py; fi"]
