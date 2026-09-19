#!/usr/bin/env bash
set -euo pipefail
HERE="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
: "${NVIDIA_API_KEY:?Supply the existing provider credential in the supervisor environment; never in argv or files}"
export CUDA_VISIBLE_DEVICES='' PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1
exec python3 -B -u "$HERE/recover.py"
