#!/bin/bash
set -euo pipefail

mode=""
case "$#:${1-}" in
  0:) ;;
  1:--follow) mode=" --follow" ;;
  1:--help)
    printf '%s\n' 'Usage: bash gpu/orch_r125_console.sh [--follow]' \
      'No option: publish one TRAIN parent message per stdin line.' \
      '--follow: watch child responses in a separate terminal.' \
      'Do not submit held tasks, evaluator scores, or answer keys.'
    exit 0
    ;;
  *) printf '%s\n' 'Expected no arguments or --follow; parent text goes through stdin.' >&2; exit 2 ;;
esac

script_dir="$(dirname -- "${BASH_SOURCE[0]}")"
source_root=/localhome/local-rohing/orch_r125_continual_20260916_attempt1/source_v3
life_root=/localhome/local-rohing/orch_r125_continual_20260916_attempt1/run1
python=/localhome/local-rohing/v2/venv/bin/python
exec bash "${script_dir}/ovx3_ssh.sh" \
  "env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=${source_root} ${python} -B -m gpu.orch_r125_stream_console --root ${life_root}${mode}"
