# ============================================================================
# MADRL CityLearn v3 (Iquitos) — Imagen CPU para tests / inferencia
# ============================================================================
# Esta imagen es SOLO para CPU: ejecutar la suite de tests, validar imports del
# paquete `uc3m/` y correr inferencia/evaluacion ligera de forma reproducible
# en cualquier maquina (Windows/Linux/Mac via Docker).
#
# NO es para entrenamiento GPU. El entrenamiento acelerado (CUDA) vive en:
#   deploy/aws/training/Dockerfile
#
# Build (desde la raiz del repo):
#   docker build -t madrl-citylearn:cpu .
# Uso:
#   docker run --rm madrl-citylearn:cpu \
#       python -c "import uc3m; from uc3m.data import available_sources; print(available_sources())"
#   docker run --rm madrl-citylearn:cpu python -m pytest tests/uc3m -q
# ============================================================================

FROM python:3.9-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Toolchain minimo para compilar wheels que no traen binarios para 3.9-slim
# (numpy fijo, scipy, etc.). git es necesario por instalaciones editables.
RUN apt-get update \
    && apt-get install -y --no-install-recommends build-essential git \
    && rm -rf /var/lib/apt/lists/*

# 1) Copiar primero los manifiestos + paquetes editables que requirements.txt
#    instala con `-e ./CityLearn` y `-e .` (README.md lo exige pyproject).
COPY requirements.txt pyproject.toml README.md ./
COPY CityLearn/ ./CityLearn/
COPY uc3m/ ./uc3m/

# 2) Instalacion reproducible de dependencias del proyecto.
#    requirements.txt contiene `-e ./CityLearn` y `-e .`, por eso los paquetes
#    se copiaron antes. PyTorch queda en su variante CPU (dependencia
#    transitiva), suficiente para tests/inferencia.
RUN python -m pip install --upgrade pip \
    && pip install -r requirements.txt

# 3) Copiar el resto del codigo del proyecto (tests, scripts, configs sueltas).
COPY tests/ ./tests/

CMD ["python", "-c", "import uc3m; from uc3m.data import available_sources; print('uc3m OK —', available_sources())"]
