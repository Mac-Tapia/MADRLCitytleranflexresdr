#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/../../.." && pwd)"
OUTPUT_ROOT="${1:-}"
REFRESH_SECONDS="${REFRESH_SECONDS:-10}"
TAIL_LINES="${TAIL_LINES:-60}"

cd "${PROJECT_ROOT}"

if [[ "${OUTPUT_ROOT}" == "" ]]; then
  if [[ -f outputs/latest_visible_training_output_root.txt ]]; then
    OUTPUT_ROOT="$(cat outputs/latest_visible_training_output_root.txt)"
  else
    echo "ERROR: indique OUTPUT_ROOT o ejecute primero run_aws_training.sh." >&2
    exit 1
  fi
fi

STATUS_PATH="${OUTPUT_ROOT}/official_full_status.json"

while true; do
  clear || true
  echo "Output root: ${OUTPUT_ROOT}"
  echo "Status path: ${STATUS_PATH}"
  echo

  if [[ -f "${STATUS_PATH}" ]]; then
    python - "$STATUS_PATH" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
jobs = payload.get("jobs", [])
print(f"Estado general: {payload.get('status')} | started={payload.get('started_at')} | updated={payload.get('updated_at')}")
print(f"Jobs: {len(jobs)}")
for job in jobs:
    print(
        f"  {job.get('algorithm','?'):>5}/{job.get('scenario','?')}: "
        f"{job.get('status','?')} exit={job.get('exit_code')} log={job.get('log_path')}"
    )
PY
  else
    echo "Aun no existe official_full_status.json"
  fi

  echo
  echo "Live progress recientes:"
  find "${OUTPUT_ROOT}" -name live_progress.json -type f -printf '%T@ %p\n' 2>/dev/null \
    | sort -nr \
    | head -5 \
    | cut -d' ' -f2- \
    | while read -r progress_path; do
        echo "--- ${progress_path}"
        python - "$progress_path" <<'PY' || true
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
payload = json.loads(path.read_text(encoding="utf-8"))
keys = ["algorithm", "scenario", "stage", "episode", "step", "global_step", "note", "updated_at"]
print(json.dumps({key: payload.get(key) for key in keys if key in payload}, indent=2))
PY
      done

  echo
  echo "Ultimas lineas de logs:"
  find "${OUTPUT_ROOT}/logs" -name '*.log' -type f -printf '%T@ %p\n' 2>/dev/null \
    | sort -nr \
    | head -3 \
    | cut -d' ' -f2- \
    | while read -r log_path; do
        echo "--- ${log_path}"
        tail -n "${TAIL_LINES}" "${log_path}"
      done

  sleep "${REFRESH_SECONDS}"
done
