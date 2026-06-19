#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/${VENV_NAME:-.venv39-citylearn-v3}"
SCHEMA_PATH="${SCHEMA_PATH:-CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json}"
SCENARIO="${SCENARIO:-E1}"

cd "${PROJECT_ROOT}"

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "ERROR: no existe entorno ${VENV_DIR}. Ejecute bootstrap_ubuntu_gpu.sh." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

echo "[1/6] Raiz del proyecto"
test -f "AGENTS.md"
test -f "pyproject.toml"
test -f "${SCHEMA_PATH}"
echo "OK: ${PROJECT_ROOT}"

echo "[2/6] Submodulos externos"
missing=0
for path in external/HARL external/MARL external/off-policy external/MAAC; do
  if [[ ! -d "${path}" ]]; then
    echo "Falta ${path}" >&2
    missing=1
  fi
done
if [[ "${missing}" != "0" ]]; then
  echo "Ejecute: git submodule update --init --recursive" >&2
  exit 1
fi

echo "[3/6] GPU NVIDIA"
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total,driver_version --format=csv,noheader
else
  echo "ADVERTENCIA: nvidia-smi no esta disponible; se puede entrenar CPU pero no es recomendado." >&2
fi

echo "[4/6] Torch CUDA"
python - <<'PY'
import json
import sys
import torch

payload = {
    "python": sys.version,
    "torch": torch.__version__,
    "cuda_available": torch.cuda.is_available(),
    "cuda_device_count": torch.cuda.device_count(),
    "cuda_device_name": torch.cuda.get_device_name(0) if torch.cuda.is_available() else None,
}
print(json.dumps(payload, indent=2))
if not torch.cuda.is_available():
    raise SystemExit("CUDA no esta disponible para Torch.")
PY

echo "[5/6] Dataset Iquitos"
python -B tools/check_training_dataset_ready.py \
  --dataset-dir CityLearn/data/datasets/citylearn_iquitos_2023_2025 \
  --buildingcsv-dir CityLearn/data/buildingcsv \
  --audit-dir outputs/dataset_audit \
  --manifest-out outputs/dataset_audit/training_dataset_ready_manifest.json \
  --skip-citylearn-load

echo "[6/6] Smoke test CityLearn/backends"
python -B CityLearn/scripts/check_citylearn_v3_training_ready.py \
  --schema-path "${SCHEMA_PATH}" \
  --scenario "${SCENARIO}" \
  --strict

echo "OK: instancia lista para entrenamiento AWS."
