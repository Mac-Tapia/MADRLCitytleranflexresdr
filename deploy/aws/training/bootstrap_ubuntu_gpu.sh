#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/${VENV_NAME:-.venv39-citylearn-v3}"
PYTHON_VERSION="${PYTHON_VERSION:-3.9}"
INSTALL_TORCH="${INSTALL_TORCH:-1}"
PYTORCH_INDEX_URL="${PYTORCH_INDEX_URL:-https://download.pytorch.org/whl/cu126}"
TORCH_PACKAGES="${TORCH_PACKAGES:-torch torchvision}"

cd "${PROJECT_ROOT}"

echo "[1/8] Proyecto: ${PROJECT_ROOT}"

if command -v apt-get >/dev/null 2>&1; then
  echo "[2/8] Instalando herramientas base con apt"
  sudo apt-get update -y
  sudo DEBIAN_FRONTEND=noninteractive apt-get install -y \
    build-essential \
    ca-certificates \
    curl \
    git \
    git-lfs \
    htop \
    jq \
    tmux \
    unzip
  git lfs install || true
else
  echo "[2/8] apt-get no disponible; se asume AMI ya preparada"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "[3/8] Instalando uv para obtener Python ${PYTHON_VERSION}"
  curl -LsSf https://astral.sh/uv/install.sh | sh
  export PATH="${HOME}/.local/bin:${PATH}"
else
  echo "[3/8] uv disponible"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "ERROR: uv no quedo disponible en PATH" >&2
  exit 1
fi

echo "[4/8] Creando entorno ${VENV_DIR}"
uv python install "${PYTHON_VERSION}"
uv venv --python "${PYTHON_VERSION}" "${VENV_DIR}"

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[5/8] Actualizando pip/setuptools/wheel"
python -m ensurepip --upgrade || true
python -m pip install --upgrade "pip>=23.3,<25" "setuptools>=68,<76" wheel

echo "[6/8] Inicializando submodulos"
git submodule update --init --recursive

echo "[7/8] Instalando dependencias de entrenamiento"
python -m pip install -r "${SCRIPT_DIR}/requirements-training-aws.txt"

if [[ "${INSTALL_TORCH}" == "1" ]]; then
  echo "[7/8] Instalando PyTorch CUDA desde ${PYTORCH_INDEX_URL}"
  # shellcheck disable=SC2086
  python -m pip install --upgrade ${TORCH_PACKAGES} --index-url "${PYTORCH_INDEX_URL}"
else
  echo "[7/8] INSTALL_TORCH=0; se mantiene PyTorch existente si lo hay"
fi

python -m pip install -e "${PROJECT_ROOT}/CityLearn"
python -m pip install -e "${PROJECT_ROOT}[train,dataset]"

echo "[8/8] Verificacion CUDA/Torch"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi
else
  echo "ADVERTENCIA: nvidia-smi no esta disponible. Revise AMI/driver/instancia GPU." >&2
fi

python - <<'PY'
import json
import sys

try:
    import torch
except Exception as exc:
    print(json.dumps({"torch_import": False, "error": repr(exc)}, indent=2))
    sys.exit(1)

print(json.dumps({
    "python": sys.version,
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_device_count": torch.cuda.device_count(),
    "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}, indent=2))
PY

echo "Bootstrap finalizado. Active el entorno con:"
echo "  source ${VENV_DIR}/bin/activate"
