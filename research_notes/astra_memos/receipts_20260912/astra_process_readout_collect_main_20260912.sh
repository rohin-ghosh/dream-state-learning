set -eu
SOURCE=/localhome/local-rohing/astra_sources/4c3064c1c3eef068951e9c3b2ca46630754564e7
ROOT=/localhome/local-rohing/astra_diagnostics/astra_rulegame_process_readout_v2_20260912_attempt1
ACTION=${1:?status or finish required}
ARGS=(
  --root "$ROOT"
  --plan-sha256 8b0f23858427d57b579688bcc06dbae4768b9bbbc2198660d1f1dbe31f092323
  --driver /tmp/astra_rulegame_process_readout_20260912.py
  --driver-sha256 46e3d0974cab9a3c35e732634a22c29ad25ccd670472dc5b1a57c344cb20af46
  --write-driver /tmp/astra_rulegame_process_write_20260912.py
  --write-driver-sha256 a73dd6074fdd099cea19f46cfed94bf31f22b2ce02b8741ac2f224413ee514d9
  --write-plan-sha256 67f2b89a769dd1f21e2ae3f048aa2d3743a5761f0574dcca3f47e1a8c51b0f44
  --launch-root "${ROOT}_launch"
  --launch-sha256 141560982f9da4f0fddf35295fb927c741b9a51589f7bbff6d4602cdd4fd2960
  --launcher /tmp/astra_launch_rulegame_process_readout_20260912.py
  --launcher-sha256 91fea8184e5d2e24825d6df7adf57dbb90a80889be7578e2dfb9e042d8da9989
)
if [ "$ACTION" = finish ]; then
  ARGS+=(--out "${ROOT}_collection_attempt1")
elif [ "$ACTION" != status ]; then
  exit 2
fi
env -u CUDA_VISIBLE_DEVICES PYTHONDONTWRITEBYTECODE=1 PYTHONNOUSERSITE=1 \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 ASTRA_SOURCE_ROOT="$SOURCE" PYTHONPATH="$SOURCE" \
  timeout --signal=KILL 300s /localhome/local-rohing/v2/venv/bin/python -B \
  /tmp/astra_rulegame_process_readout_collect_20260912.py "$ACTION" "${ARGS[@]}"
