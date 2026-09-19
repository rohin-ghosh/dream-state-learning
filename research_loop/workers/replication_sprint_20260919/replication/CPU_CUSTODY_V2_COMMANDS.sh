#!/usr/bin/env bash
set -euo pipefail

PKG="$(cd -- "$(dirname -- "$0")" && pwd)"
ROOT=/localhome/local-rohing/post_sampling_custody_diagnostics_20260919/d0f368fbcb0ac74ba908a008d7b4daac0bf3f3cd19d5a3fc171902e7419adaad
SEAL="$PKG/CPU_CUSTODY_SOURCE_FREEZE_V2.json"
SEAL_SHA=050587019d9f0a53e3c52ea6ac1af61635db20683ba40ac69809c47e90b099df
REPAIR="$PKG/CPU_CUSTODY_REPAIR_V2.json"
REPAIR_SHA=54f7b3e3153e068d09fb479cb4c8a56e29ad8062c917834557f67d0bbbcaecbf
PREREGISTRATION_FILE="${PREREGISTRATION_FILE:-$PKG/C2_SAMPLING_PREREGISTRATION.md}"

case "${1:-}" in
  release-check|release)
    mode=--check
    if [[ "$1" == release ]]; then mode=--release; fi
    exec python3 -B "$PKG/release_failed_claims.py" \
      --repair "$REPAIR" --repair-sha256 "$REPAIR_SHA" \
      --seal "$SEAL" --seal-sha256 "$SEAL_SHA" "$mode"
    ;;
  stage|plan)
    exec python3 -B "$PKG/prepare_executable.py" \
      --candidate "$PKG/C2_SAMPLING_CANDIDATE_V2.json" \
      --candidate-sha256 83a897cf8a5054364a65b55918d5fde321aa552e9f5ab85a1ed5ee176e2eb51f \
      --receipt "$PKG/ORIGINALS_RECEIPT.json" \
      --receipt-sha256 7459c1b35c1f445add6da32cfa812103c5c3a6be76b8d2989003fc6d85c4efca \
      --seal "$SEAL" --seal-sha256 "$SEAL_SHA" \
      --preregistration "$PREREGISTRATION_FILE" \
      --cpu-proof-repair "$REPAIR" --cpu-proof-repair-sha256 "$REPAIR_SHA" "--$1"
    ;;
  check|prove)
    PREPARED_SHA="$(sha256sum "$ROOT/PREPARED.json" | cut -d ' ' -f1)"
    exec python3 -B "$ROOT/runtime/dispatch_sampling.py" --root "$ROOT" \
      --prepared-sha256 "$PREPARED_SHA" --source-freeze-sha256 "$SEAL_SHA" "--$1"
    ;;
  *)
    printf '%s\n' 'Usage: bash CPU_CUSTODY_V2_COMMANDS.sh {release-check|release|plan|stage|check|prove}' >&2
    printf '%s\n' 'Main only. No model-run action. Review each receipt before proceeding.' >&2
    exit 2
    ;;
esac
