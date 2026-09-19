#!/usr/bin/env bash
set -euo pipefail
exec /localhome/local-rohing/v2/venv/bin/python -B \
  /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate/daemon.py \
  --run \
  --policy /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/policy.json \
  --freeze /localhome/local-rohing/post_reboot_probe_queue_20260919/candidate/SOURCE_FREEZE_V3.json \
  --activation /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/activation.json \
  --enrollment /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/enrollment.json \
  --enrollment /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/extra_enrollment.json \
  --capsules /localhome/local-rohing/post_reboot_probe_queue_20260919/inputs/capsules.json \
  --state /localhome/local-rohing/post_reboot_probe_queue_20260919/state/queue.sqlite
