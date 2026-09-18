#!/bin/bash
set -euo pipefail
ROOT="${1:?Pass the exact CPU-passed released_all receiving root}"
PYTHON=/localhome/local-rohing/v2/venv/bin/python
BUNDLE=/localhome/local-rohing/orch_r177_strict_slots_20260917_v1
PROBE="$BUNDLE/attempts/probe_2_1789671506809013676/CONTAINMENT.json"
printf '%s  %s\n' 6c69c690d4e2491255a3a12370b1143515a4d223456880e889fd24eafaea0c51 "$BUNDLE/slot_policy.py" d26f808fcce89c9d5674d69484bcbac614608761b1f2602d04ee6e5935b49aec "$BUNDLE/BUNDLE.json" dfcd7f16cb5df2a8e670c478d466ec1958c7c74299053f9b492598a576f1bf92 "$PROBE" | sha256sum -c -
INVENTORY_SHA="$(sha256sum "$ROOT/INVENTORY.json" | cut -d' ' -f1)"
PREPARED="$(CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B "$BUNDLE/slot_policy.py" prepare --physical 2 --seconds 7300 --root "$ROOT" --entrypoint "$ROOT/research_loop/workers/r177_caption_game_stage1_20260917/data_judge/released_receiving.py" --probe "$PROBE" --bind "$ROOT/INVENTORY.json" --bind "$ROOT/TRAIN_CONFIG.json" --bind "$ROOT/CPU_GATE.json" -- train --root "$ROOT" --inventory-sha256 "$INVENTORY_SHA")"
printf '%s\n' "$PREPARED"
CONFIG="$(printf '%s' "$PREPARED" | "$PYTHON" -B -c 'import json,sys;print(json.load(sys.stdin)["config"])')"
exec env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B "$BUNDLE/slot_policy.py" launch --config "$CONFIG"
