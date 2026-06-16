#!/usr/bin/env bash
set -euo pipefail

if [[ $# -lt 2 ]]; then
  cat >&2 <<'EOF'
Uso:
  bash deploy/aws/training/sync_outputs_s3.sh OUTPUT_ROOT s3://bucket/prefix/
EOF
  exit 2
fi

OUTPUT_ROOT="$1"
S3_URI="$2"

if ! command -v aws >/dev/null 2>&1; then
  echo "ERROR: aws CLI no esta instalado o no esta en PATH." >&2
  exit 1
fi

if [[ ! -d "${OUTPUT_ROOT}" ]]; then
  echo "ERROR: no existe OUTPUT_ROOT: ${OUTPUT_ROOT}" >&2
  exit 1
fi

aws s3 sync "${OUTPUT_ROOT}" "${S3_URI}" \
  --exclude "__pycache__/*" \
  --exclude "*.tmp"

echo "Sincronizado: ${OUTPUT_ROOT} -> ${S3_URI}"
