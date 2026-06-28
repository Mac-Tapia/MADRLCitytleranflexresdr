FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py model_loader.py mongo_store.py ./

# Modelo y metadatos se montan como volumen (ver docker-compose.yml) o se
# copian en build para imágenes inmutables de producción:
# COPY models/winning_agent.onnx models/winning_agent.metadata.json /models/

ENV MODEL_PATH=/models/winning_agent.onnx \
    MODEL_METADATA_PATH=/models/winning_agent.metadata.json \
    LOG_LEVEL=info

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
