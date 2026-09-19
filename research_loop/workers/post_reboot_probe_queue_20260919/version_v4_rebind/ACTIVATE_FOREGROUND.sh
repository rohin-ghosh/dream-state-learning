#!/usr/bin/env bash
set -euo pipefail
ROOT=/localhome/local-rohing/post_reboot_probe_queue_20260919
test -f "$ROOT/inputs/activation_v4.json"
test -f "$ROOT/jobs/4694399fdaa00125796b604de48551af434e8377a5ac06795bfa31241b4c5c3f/runtime_v4/REBIND_VERIFIED.json"
exec /localhome/local-rohing/v2/venv/bin/python -B "$ROOT/candidate_v4/daemon.py" \
  --run \
  --policy "$ROOT/inputs/policy.json" \
  --freeze "$ROOT/candidate_v4/SOURCE_FREEZE_V4_REBIND.json" \
  --activation "$ROOT/inputs/activation_v4.json" \
  --enrollment "$ROOT/inputs/enrollment.json" \
  --enrollment "$ROOT/inputs/extra_enrollment.json" \
  --capsules "$ROOT/inputs/capsules_v4.json" \
  --state "$ROOT/state/queue.sqlite"
