#!/usr/bin/env bash
set -euo pipefail
cd /data/home/rohing/dream-state-orch
scope=research_loop/workers/replication_sprint_20260919
output="$scope/operations/C2_HANDOFF_BOUNDARY_WAIT2"
mkdir "$output"
date -u +%FT%TZ > "$output/STARTED_UTC.txt"
printf '%s\n' "$$" > "$output/PID.txt"
for poll in $(seq 1 600); do
  python3 -B "$scope/parenting/c2_refinement/candidate.py" \
    --check-seed "$scope/parenting/c2_refinement/SUPERVISOR_SEED_MANIFEST.json" \
    --require-live-identity > "$output/LAST_READ_ONLY_CHECK.json"
  if jq -e '.settled_current_ledger == true' "$output/LAST_READ_ONLY_CHECK.json" >/dev/null; then
    set +e
    python3 -B "$scope/parenting/c2_handoff/handoff.py" --execute \
      --seed-sha256 14b4a285dda3abcb7ccd9421ccbd8135bd26883cde7cead410e52a56cd073330 \
      --install-sha256 5a42f5a572b2cdd3bcd80a8d4f43b7c5d1fab8b30b5c93f45eb6c55e45e20c96 \
      > "$output/ONE_EXECUTION_RESULT.json"
    status=$?
    set -e
    printf '%s\n' "$status" > "$output/EXECUTION_EXIT_CODE.txt"
    date -u +%FT%TZ > "$output/FINISHED_UTC.txt"
    exit "$status"
  fi
  sleep 3
done
printf '%s\n' 'No settled window observed; no handoff attempted.' > "$output/WAIT_EXPIRED.txt"
date -u +%FT%TZ > "$output/FINISHED_UTC.txt"
