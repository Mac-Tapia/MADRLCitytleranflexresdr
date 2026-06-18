#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
VENV_DIR="${PROJECT_ROOT}/${VENV_NAME:-.venv39-citylearn-v3}"

SCHEMA_PATH="CityLearn/data/datasets/citylearn_iquitos_2023_2025/schema.json"
SCENARIOS="ALL"
ALGORITHMS="happo,masac,matd3,maac"
SEED="0"
EPISODES="75"
EPISODE_TIME_STEPS="8760"
TORCH_THREADS="${TORCH_THREADS:-8}"
LIVE_PROGRESS_INTERVAL="1000"
ARTIFACT_PROFILE="efficient"
TRACE_RECORD_INTERVAL="24"
TRACE_DETAIL="compact"
GPU_PROFILE="aws"
CUDA="auto"
MAX_PARALLEL_JOBS="1"
OUTPUT_ROOT=""
LOG_CHUNK_SIZE="10M"
LOG_MAX_FILES="${LOG_MAX_FILES:-100}"
STATUS_LOCK_STALE_SECONDS="${STATUS_LOCK_STALE_SECONDS:-600}"

usage() {
  cat <<'EOF'
Uso:
  bash deploy/aws/training/run_aws_training.sh [opciones]

Opciones:
  --scenario E1|E2|E3|ALL          Escenario o todos (default: ALL)
  --algorithms a,b,c               happo,masac,matd3,maac (default: todos)
  --seed N                         Semilla (default: 0)
  --episodes N                     Episodios (default: 75)
  --episode-time-steps N           Pasos por episodio (default: 8760)
  --torch-threads N                Threads Torch (default: 8)
  --max-parallel-jobs N            Jobs simultaneos (default: 1)
  --output-root PATH               Directorio de salida
  --artifact-profile full|efficient|minimal
  --trace-record-interval N
  --trace-detail full|compact
  --log-chunk-size SIZE            Tamano max. por archivo de log, formato
                                    10M, 512K o bytes (default: 10M)
  --log-max-files N                Maximo de partes de log por job; 0 ilimitado
                                    (default: 100)
  --cuda                           Forzar CUDA
  --no-cuda                        Forzar CPU
  --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --scenario) SCENARIOS="$2"; shift 2 ;;
    --algorithms) ALGORITHMS="$2"; shift 2 ;;
    --seed) SEED="$2"; shift 2 ;;
    --episodes) EPISODES="$2"; shift 2 ;;
    --episode-time-steps) EPISODE_TIME_STEPS="$2"; shift 2 ;;
    --torch-threads) TORCH_THREADS="$2"; shift 2 ;;
    --live-progress-interval) LIVE_PROGRESS_INTERVAL="$2"; shift 2 ;;
    --artifact-profile) ARTIFACT_PROFILE="$2"; shift 2 ;;
    --trace-record-interval) TRACE_RECORD_INTERVAL="$2"; shift 2 ;;
    --trace-detail) TRACE_DETAIL="$2"; shift 2 ;;
    --gpu-profile) GPU_PROFILE="$2"; shift 2 ;;
    --max-parallel-jobs) MAX_PARALLEL_JOBS="$2"; shift 2 ;;
    --output-root) OUTPUT_ROOT="$2"; shift 2 ;;
    --log-chunk-size) LOG_CHUNK_SIZE="$2"; shift 2 ;;
    --log-max-files) LOG_MAX_FILES="$2"; shift 2 ;;
    --cuda) CUDA="1"; shift ;;
    --no-cuda) CUDA="0"; shift ;;
    --help|-h) usage; exit 0 ;;
    *) echo "Opcion desconocida: $1" >&2; usage; exit 2 ;;
  esac
done

cd "${PROJECT_ROOT}"

if [[ ! -f "${VENV_DIR}/bin/activate" ]]; then
  echo "ERROR: no existe entorno ${VENV_DIR}. Ejecute bootstrap_ubuntu_gpu.sh." >&2
  exit 1
fi

# shellcheck disable=SC1091
source "${VENV_DIR}/bin/activate"

if [[ ! -f "${SCHEMA_PATH}" ]]; then
  echo "ERROR: no existe ${SCHEMA_PATH}" >&2
  exit 1
fi

if [[ "${OUTPUT_ROOT}" == "" ]]; then
  OUTPUT_ROOT="outputs/aws_citylearn_v3_madrl_$(date -u +%Y%m%d_%H%M%S)"
fi

mkdir -p outputs
mkdir -p "${OUTPUT_ROOT}"

# Marcador de entrenamiento completo: evita que el contenedor relance el
# entrenamiento automaticamente tras un reinicio de EC2 (restart: unless-stopped).
DONE_MARKER="${PROJECT_ROOT}/outputs/.training_completed"
FAILED_MARKER="${PROJECT_ROOT}/outputs/.training_failed"
if [[ -f "${DONE_MARKER}" ]]; then
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) === INFO: Entrenamiento ya completado."
  echo "Marcador encontrado: ${DONE_MARKER}"
  echo "Para lanzar un nuevo entrenamiento, elimine el marcador primero:"
  echo "  rm ${DONE_MARKER}"
  echo "Para detener el contenedor inactivo:"
  echo "  docker compose -f deploy/aws/training/docker-compose.yml stop"
  exec sleep infinity
fi
if [[ -f "${FAILED_MARKER}" ]]; then
  echo "=== $(date -u +%Y-%m-%dT%H:%M:%SZ) === ERROR: entrenamiento anterior fallo."
  echo "Marcador encontrado: ${FAILED_MARKER}"
  cat "${FAILED_MARKER}" || true
  echo "Revise official_full_status.json y logs antes de relanzar."
  echo "Para relanzar despues de corregir el problema:"
  echo "  rm ${FAILED_MARKER}"
  echo "  docker compose -f deploy/aws/training/docker-compose.yml up -d"
  echo "Para detener el contenedor inactivo:"
  echo "  docker compose -f deploy/aws/training/docker-compose.yml stop"
  exec sleep infinity
fi

printf '%s\n' "${OUTPUT_ROOT}" > outputs/latest_visible_training_output_root.txt

STATUS_PATH="${OUTPUT_ROOT}/official_full_status.json"
MANIFEST_PATH="${OUTPUT_ROOT}/official_full_manifest.json"
STATUS_LOCK="${OUTPUT_ROOT}/.status.lock"
STARTED_AT="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
NUM_ENV_STEPS="$((EPISODES * EPISODE_TIME_STEPS))"

if [[ "${SCENARIOS^^}" == "ALL" ]]; then
  SCENARIO_LIST=("E1" "E2" "E3")
else
  IFS=',' read -r -a SCENARIO_LIST <<<"${SCENARIOS}"
fi

IFS=',' read -r -a ALGORITHM_LIST <<<"${ALGORITHMS}"

if [[ "${CUDA}" == "auto" ]]; then
  if python - <<'PY'
import torch
raise SystemExit(0 if torch.cuda.is_available() else 1)
PY
  then
    CUDA="1"
  else
    CUDA="0"
  fi
fi

with_status_lock() {
  local waited=0
  while ! mkdir "${STATUS_LOCK}" 2>/dev/null; do
    sleep 0.2
    waited=$((waited + 1))
    if [[ "$((waited / 5))" -ge "${STATUS_LOCK_STALE_SECONDS}" ]]; then
      echo "ADVERTENCIA: eliminando lock stale ${STATUS_LOCK}" >&2
      rm -rf "${STATUS_LOCK}"
      waited=0
    fi
  done
  set +e
  "$@"
  local rc=$?
  set -e
  rmdir "${STATUS_LOCK}"
  return "${rc}"
}

init_status() {
  python - "$STATUS_PATH" "$MANIFEST_PATH" "$OUTPUT_ROOT" "$STARTED_AT" "$SCENARIOS" "$ALGORITHMS" "$EPISODES" "$EPISODE_TIME_STEPS" "$SEED" "$TORCH_THREADS" "$MAX_PARALLEL_JOBS" "$CUDA" "$ARTIFACT_PROFILE" "$TRACE_RECORD_INTERVAL" "$TRACE_DETAIL" "$GPU_PROFILE" "$LOG_CHUNK_SIZE" "$LOG_MAX_FILES" <<'PY'
import json
import socket
import sys
from pathlib import Path

status_path, manifest_path, output_root, started_at = map(Path, sys.argv[1:5])
raw = sys.argv[5:]
payload = {
    "status": "running",
    "started_at": str(started_at),
    "updated_at": str(started_at),
    "completed_at": None,
    "host": socket.gethostname(),
    "launcher": "deploy/aws/training/run_aws_training.sh",
    "output_root": str(output_root),
    "training_config": {
        "scenarios": raw[0],
        "algorithms": raw[1],
        "episodes": int(raw[2]),
        "episode_time_steps": int(raw[3]),
        "seed": int(raw[4]),
        "torch_threads": int(raw[5]),
        "max_parallel_jobs": int(raw[6]),
        "cuda": raw[7] == "1",
        "artifact_profile": raw[8],
        "trace_record_interval": int(raw[9]),
        "trace_detail": raw[10],
        "gpu_profile": raw[11],
        "log_chunk_size": raw[12],
        "log_max_files": int(raw[13]),
    },
    "jobs": [],
}
status_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
manifest_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
PY
}

record_job() {
  local algorithm="$1"
  local scenario="$2"
  local job_status="$3"
  local exit_code="$4"
  local log_path="$5"
  python - "$STATUS_PATH" "$MANIFEST_PATH" "$algorithm" "$scenario" "$job_status" "$exit_code" "$log_path" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
algorithm, scenario, job_status, exit_code, log_path = sys.argv[3:8]
now = datetime.now(timezone.utc).isoformat()

payload = json.loads(status_path.read_text(encoding="utf-8"))
jobs = payload.setdefault("jobs", [])
key = (algorithm.lower(), scenario.upper())
job = None
for item in jobs:
    if (str(item.get("algorithm", "")).lower(), str(item.get("scenario", "")).upper()) == key:
        job = item
        break
if job is None:
    job = {
        "algorithm": algorithm.lower(),
        "scenario": scenario.upper(),
        "started_at": None,
        "completed_at": None,
    }
    jobs.append(job)

if job_status == "running" and not job.get("started_at"):
    job["started_at"] = now
if job_status in {"completed", "failed"}:
    job["completed_at"] = now
job["status"] = job_status
job["exit_code"] = None if exit_code == "" else int(exit_code)
job["log_path"] = log_path

statuses = [str(item.get("status")) for item in jobs]
payload["updated_at"] = now
if any(item == "failed" for item in statuses):
    payload["status"] = "failed"
elif jobs and all(item == "completed" for item in statuses):
    payload["status"] = "completed"
    payload["completed_at"] = now
else:
    payload["status"] = "running"

text = json.dumps(payload, indent=2)
status_path.write_text(text, encoding="utf-8")
manifest_path.write_text(text, encoding="utf-8")
PY
}

mark_final_status() {
  local final_status="$1"
  python - "$STATUS_PATH" "$MANIFEST_PATH" "$final_status" <<'PY'
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

status_path = Path(sys.argv[1])
manifest_path = Path(sys.argv[2])
final_status = sys.argv[3]
payload = json.loads(status_path.read_text(encoding="utf-8"))
now = datetime.now(timezone.utc).isoformat()
payload["status"] = final_status
payload["updated_at"] = now
payload["completed_at"] = now
text = json.dumps(payload, indent=2)
status_path.write_text(text, encoding="utf-8")
manifest_path.write_text(text, encoding="utf-8")
PY
}

build_command() {
  local algorithm="$1"
  local scenario="$2"
  local script=""
  case "${algorithm}" in
    happo) script="CityLearn/scripts/train_citylearn_v3_happo.py" ;;
    masac) script="CityLearn/scripts/train_citylearn_v3_masac.py" ;;
    matd3) script="CityLearn/scripts/train_citylearn_v3_matd3.py" ;;
    maac) script="CityLearn/scripts/train_citylearn_v3_maac.py" ;;
    *) echo "Algoritmo no soportado: ${algorithm}" >&2; return 2 ;;
  esac

  CMD=(python -B "${script}"
    --schema-path "${SCHEMA_PATH}"
    --scenario "${scenario}"
    --seed "${SEED}"
    --episode-time-steps "${EPISODE_TIME_STEPS}"
    --output-dir "${OUTPUT_ROOT}/${scenario}/${algorithm}"
    --torch-threads "${TORCH_THREADS}"
    --live-progress-interval "${LIVE_PROGRESS_INTERVAL}"
    --artifact-profile "${ARTIFACT_PROFILE}"
    --trace-record-interval "${TRACE_RECORD_INTERVAL}"
    --trace-detail "${TRACE_DETAIL}"
    --gpu-profile "${GPU_PROFILE}")

  if [[ "${CUDA}" == "1" ]]; then
    CMD+=(--cuda)
  fi

  case "${algorithm}" in
    happo)
      CMD+=(--episodes "${EPISODES}" --num-env-steps "${NUM_ENV_STEPS}" --hidden-size 384 --n-rollout-threads 1 --log-interval 1 --eval-interval 1)
      ;;
    masac)
      CMD+=(--episodes "${EPISODES}" --epochs "${EPISODES}" --action-bins 3 --discrete-action-mode axis --buffer-size 20 --critic-batch-size 64 --critic-train-steps 1 --actor-sample-times 5 --max-replay-buffer-gib 8 --masac-preload-batch-device auto)
      ;;
    matd3)
      CMD+=(--episodes "${EPISODES}" --num-env-steps "${NUM_ENV_STEPS}" --batch-size 256 --buffer-size 4096 --hidden-size 256 --train-interval 100 --num-random-episodes 1)
      ;;
    maac)
      CMD+=(--episodes "${EPISODES}" --action-bins 3 --discrete-action-mode axis --batch-size 256 --buffer-length 50000 --steps-per-update 250 --num-updates 8 --max-discrete-actions 512)
      ;;
  esac
}

run_job() {
  local algorithm="$1"
  local scenario="$2"
  local log_prefix="${OUTPUT_ROOT}/${scenario}/${algorithm}/logs/training-"
  local log_pattern="${log_prefix}*.log"
  mkdir -p "${OUTPUT_ROOT}/${scenario}/${algorithm}/logs"
  local rc=0

  with_status_lock record_job "${algorithm}" "${scenario}" "running" "" "${log_pattern}"
  build_command "${algorithm}" "${scenario}"

  # Texto plano rotado + stdout visible: el helper duplica el stream hacia
  # Docker logs y hacia partes de log por tamano. PIPESTATUS[0] sigue siendo
  # el exit code real del entrenamiento.
  set +e
  {
    printf '==== %s %s/%s ====\n' "$(date -u +%Y-%m-%dT%H:%M:%SZ)" "${algorithm}" "${scenario}"
    printf 'CMD:'
    printf ' %q' "${CMD[@]}"
    printf '\n'
    "${CMD[@]}" 2>&1
  } | python -B deploy/aws/training/rotate_training_log.py \
        "${log_prefix}" "${LOG_CHUNK_SIZE}" "${LOG_MAX_FILES}"
  rc=${PIPESTATUS[0]}
  set -e

  if [[ "${rc}" == "0" ]]; then
    with_status_lock record_job "${algorithm}" "${scenario}" "completed" "${rc}" "${log_pattern}"
  else
    with_status_lock record_job "${algorithm}" "${scenario}" "failed" "${rc}" "${log_pattern}"
  fi

  return "${rc}"
}

with_status_lock init_status

echo "Output root: ${OUTPUT_ROOT}"
echo "Status: ${STATUS_PATH}"
echo "CUDA: ${CUDA}; max_parallel_jobs=${MAX_PARALLEL_JOBS}"

failures=0
for scenario in "${SCENARIO_LIST[@]}"; do
  scenario="$(echo "${scenario}" | tr '[:lower:]' '[:upper:]' | xargs)"
  for algorithm in "${ALGORITHM_LIST[@]}"; do
    algorithm="$(echo "${algorithm}" | tr '[:upper:]' '[:lower:]' | xargs)"
    while [[ "$(jobs -pr | wc -l | xargs)" -ge "${MAX_PARALLEL_JOBS}" ]]; do
      wait -n || failures=$((failures + 1))
    done
    ( run_job "${algorithm}" "${scenario}" ) &
  done
done

while [[ "$(jobs -pr | wc -l | xargs)" -gt 0 ]]; do
  wait -n || failures=$((failures + 1))
done

if [[ "${failures}" -gt 0 ]]; then
  with_status_lock mark_final_status "failed"
  cat > "${FAILED_MARKER}" <<EOF
failed_at=$(date -u +%Y-%m-%dT%H:%M:%SZ)
output_root=${OUTPUT_ROOT}
status_path=${STATUS_PATH}
failures=${failures}
EOF
  echo "Entrenamiento finalizo con ${failures} job(s) fallidos. Revise ${STATUS_PATH}" >&2
  echo "Marcador escrito: ${FAILED_MARKER}. El contenedor quedara inactivo tras el siguiente reinicio." >&2
  exit 1
fi

with_status_lock mark_final_status "completed"
rm -f "${FAILED_MARKER}"
touch "${DONE_MARKER}"
echo "Entrenamiento completado: ${OUTPUT_ROOT}"
echo "Marcador escrito: ${DONE_MARKER} — el contenedor permanecera inactivo hasta 'docker compose stop'."
