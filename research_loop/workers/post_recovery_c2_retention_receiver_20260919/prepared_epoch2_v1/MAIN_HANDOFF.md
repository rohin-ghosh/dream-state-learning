# Main: concrete C2 epoch2 bundle

All source files are exact hashes; source/tools are sealed 0444/0555. Transport and staging have NOT happened. Preserve epoch1 and the running original.

Proposed new node source: `/localhome/local-rohing/orch_retention_20260919/C2/epoch2/source`. Use the full five-entry `changed` map for old-live authority; `epoch1_to_epoch2_delta` has only two entries. Do not add the tools to the pinned source.

One-shot CPU invocations after Main stages and verifies the bundle:

```bash
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_retention_20260919/C2/epoch2/tools/cpu_check.py source --bundle /localhome/local-rohing/orch_retention_20260919/C2/epoch2
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_retention_20260919/C2/epoch2/tools/cpu_check.py checkpoint --bundle /localhome/local-rohing/orch_retention_20260919/C2/epoch2
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_retention_20260919/C2/epoch2/tools/cpu_check.py tail --bundle /localhome/local-rohing/orch_retention_20260919/C2/epoch2
env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 /localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_retention_20260919/C2/epoch2/tools/source_checks.py --source /localhome/local-rohing/orch_retention_20260919/C2/epoch2/source --manifest /localhome/local-rohing/orch_retention_20260919/C2/epoch2/EPOCH2_SOURCE.json
```

The default checkpoint command checks only the old, exactly pinned COMPLETE 11502, not a current handoff. A newer selection requires both index and hash. Tail mode reads a current COMPLETE/LEARN or refuses immediately, never signals/retries. Guard mode needs Main's actually prepared guard via `--guard`; no guard is fabricated here.

Actual same-node Torch checkpoint/RNG validation remains to be run by Main. The local receipt is synthetic actual-source evidence, not live-handoff authority. The scanner hashes retained prefix bytes (not O(tail)); no historical body-replay fallback. Wall proof, current source authority, old bridge/parent fence and r188 admission remain required.
