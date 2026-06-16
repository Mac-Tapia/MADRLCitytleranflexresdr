# Imagen de entrenamiento MADRL (HAPPO/MASAC/MATD3/MAAC) para EC2 Ubuntu+CUDA.
#
# Build context = RAIZ del repo (no este directorio). Antes de construir,
# inicialice los submodulos en el host (la imagen no corre `git submodule`):
#   git submodule update --init --recursive
#   docker build -f deploy/aws/training/Dockerfile -t madrl-training:latest .
#
# El host necesita driver NVIDIA + NVIDIA Container Toolkit para exponer la
# GPU al contenedor (docker run --gpus all ...). No se usa una imagen base
# nvidia/cuda porque el wheel de torch cu126 ya incluye las librerias CUDA
# runtime; el toolkit del host inyecta libcuda/el driver/nvidia-smi al
# contenedor en tiempo de `docker run`, no en build time (por eso ningun
# paso de build aqui invoca CUDA).

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTORCH_INDEX_URL=https://download.pytorch.org/whl/cu126

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        build-essential ca-certificates curl git git-lfs jq tmux unzip \
    && git lfs install \
    && rm -rf /var/lib/apt/lists/*

RUN curl -LsSf https://astral.sh/uv/install.sh | sh

WORKDIR /workspace
COPY . .

# Mismo venv y mismas dependencias que deploy/aws/training/bootstrap_ubuntu_gpu.sh
# (requirements.txt es la fuente unica: -e ./CityLearn, -e ., y las
# versiones fijas de compatibilidad RL). torch CUDA se instala despues por
# separado porque -e ./CityLearn arrastra una build CPU generica como
# dependencia transitiva.
RUN export PATH="/root/.local/bin:${PATH}" \
    && uv python install 3.9 \
    && uv venv --python 3.9 .venv39-citylearn-v3 \
    && . .venv39-citylearn-v3/bin/activate \
    && python -m ensurepip --upgrade \
    && python -m pip install --upgrade "pip>=23.3,<25" "setuptools>=68,<76" wheel \
    && python -m pip install -r requirements.txt \
    && python -m pip install --upgrade torch torchvision --index-url "${PYTORCH_INDEX_URL}"

# run_aws_training.sh activa .venv39-citylearn-v3 el mismo (resuelve la ruta
# relativa a su propio PROJECT_ROOT, que dentro del contenedor es /workspace).
ENTRYPOINT ["bash", "deploy/aws/training/run_aws_training.sh"]
CMD ["--scenario", "ALL", \
     "--algorithms", "happo,masac,matd3,maac", \
     "--episodes", "75", \
     "--episode-time-steps", "8760", \
     "--max-parallel-jobs", "1", \
     "--log-chunk-size", "10M", \
     "--cuda"]
