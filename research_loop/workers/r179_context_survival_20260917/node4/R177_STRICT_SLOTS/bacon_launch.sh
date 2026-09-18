#!/bin/bash
set -euo pipefail
ROOT="${1:?Pass the exact local-Qwen receiving root}"
SOURCE="${2:?Pass the source import root inside that receiving root}"
ENTRYPOINT="${3:?Pass Bacon's actual CPU-tested Python loader/service entrypoint}"
METADATA="${4:?Pass the existing bound loader or service configuration}"
shift 4
PYTHON=/localhome/local-rohing/v2/venv/bin/python
BUNDLE=/localhome/local-rohing/orch_r177_strict_slots_20260917_v1
PROBE="$BUNDLE/attempts/probe_5_1789671506802072866/CONTAINMENT.json"
printf '%s  %s\n' 6c69c690d4e2491255a3a12370b1143515a4d223456880e889fd24eafaea0c51 "$BUNDLE/slot_policy.py" d26f808fcce89c9d5674d69484bcbac614608761b1f2602d04ee6e5935b49aec "$BUNDLE/BUNDLE.json" 726565711acefb91301f416e7f5d2bcfd0ff881a6edb7627c3f4530cbfe017a3 "$PROBE" | sha256sum -c -
PREPARED="$(CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B "$BUNDLE/slot_policy.py" prepare --physical 5 --seconds 3600 --root "$ROOT" --pythonpath "$SOURCE" --entrypoint "$ENTRYPOINT" --probe "$PROBE" --bind "$METADATA" -- "$@")"
printf '%s\n' "$PREPARED"
CONFIG="$(printf '%s' "$PREPARED" | "$PYTHON" -B -c 'import json,sys;print(json.load(sys.stdin)["config"])')"
exec env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 "$PYTHON" -B "$BUNDLE/slot_policy.py" launch --config "$CONFIG"
