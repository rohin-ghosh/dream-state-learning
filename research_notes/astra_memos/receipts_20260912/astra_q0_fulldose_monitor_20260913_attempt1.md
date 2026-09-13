# Q0 full-dose bounded read-only monitor

**Status: finished** — no scientific success inferred.
Started UTC: 2026-09-13T05:12:19.178014+00:00; maximum 20 minutes; poll spacing at least 120 seconds.
Polls: 10. Latest remote metadata: 2026-09-13T05:30:19.724916+00:00.
Frozen source: `/localhome/local-rohing/astra_sources/q0_fulldose_20260913_attempt2`.

## Latest stage metadata

| Replica | Controller | Exists / identity matched | Receipts (FINISHED + COMPLETE) | DONE | Pending stages | Terminal markers |
|---|---:|---|---:|---:|---|---|
| R0 | 4012737 | True / True | 9 (9) | 9 | 09_eval_P_DERANGED_128 | none |
| R1 | 4012889 | False / False | 9 (9) | 9 | 09_eval_P_DERANGED_128 | FAILED.json, FINALIZED.json, RESOURCE.json, SEAL.json |
| R2 | 4013072 | True / True | 9 (9) | 9 | 09_eval_P_DERANGED_128 | none |

## Poll history

| UTC | R0 receipts / pending | R1 receipts / pending | R2 receipts / pending | SSH seconds / exit | New alerts |
|---|---|---|---|---|---:|
| 2026-09-13T05:12:19.178116+00:00 | 2 / 02_fit_P_AUTH | 2 / 02_fit_P_AUTH | 2 / 02_fit_P_AUTH | 0.711 / 0 | 0 |
| 2026-09-13T05:14:19.178229+00:00 | 2 / 02_fit_P_AUTH | 2 / 02_fit_P_AUTH | 2 / 02_fit_P_AUTH | 0.709 / 0 | 0 |
| 2026-09-13T05:16:19.178353+00:00 | 4 / 04_eval_P_AUTH_64 | 4 / 04_eval_P_AUTH_64 | 3 / 03_eval_P_AUTH_32 | 0.779 / 0 | 0 |
| 2026-09-13T05:18:19.178433+00:00 | 5 / 05_eval_P_AUTH_128 | 5 / 05_eval_P_AUTH_128 | 5 / 05_eval_P_AUTH_128 | 0.665 / 0 | 0 |
| 2026-09-13T05:20:19.178547+00:00 | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 0.672 / 0 | 0 |
| 2026-09-13T05:22:19.178625+00:00 | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 0.538 / 0 | 0 |
| 2026-09-13T05:24:19.178729+00:00 | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 0.896 / 0 | 0 |
| 2026-09-13T05:26:19.178833+00:00 | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 6 / 06_fit_P_DERANGED | 0.729 / 0 | 0 |
| 2026-09-13T05:28:19.178942+00:00 | 8 / 08_eval_P_DERANGED_64 | 8 / 08_eval_P_DERANGED_64 | 7 / 07_eval_P_DERANGED_32 | 0.909 / 0 | 0 |
| 2026-09-13T05:30:19.179036+00:00 | 9 / 09_eval_P_DERANGED_128 | 9 / 09_eval_P_DERANGED_128 | 9 / 09_eval_P_DERANGED_128 | 0.576 / 0 | 5 |

## Alerts

```json
[
  {
    "details": {
      "failures": [
        {
          "error_type": "CalledProcessError",
          "preserve_partial": true,
          "reason": "Command '['/localhome/local-rohing/v2/venv/bin/python', '-B', '-m', 'gpu.astra_pairwise_q0_fulldose', 'worker', '--out', '/localhome/local-rohing/astra_diagnostics/q0_fulldose_R1_20260913_attempt1', '--stage', '09_eval_P_DERANGED_128', '--allow-gpu']' returned non-zero exit status 1.",
          "timestamp": 1789277374.5217435
        }
      ],
      "preserve_partial": true
    },
    "key": "R1:FAILED_PRESENT",
    "kind": "FAILED_PRESENT",
    "replica": "R1"
  },
  {
    "details": {
      "pid": 4012889,
      "state": null
    },
    "key": "R1:CONTROLLER_DISAPPEARED",
    "kind": "CONTROLLER_DISAPPEARED",
    "replica": "R1"
  },
  {
    "details": {
      "marker": "SEAL.json",
      "resource_receipt": {
        "collection_reserve_seconds": 180,
        "deadline": 1789286471.9747434,
        "elapsed_seconds": 1702.720723729988,
        "finished": 1789277374.6954665,
        "fit_cap": 2,
        "gpu_release_verified": true,
        "release_is_receipt_claim_not_live_verification": true,
        "seconds_cap": 10800,
        "stage_count": 9,
        "started": 1789275671.9747434
      }
    },
    "key": "R1:TERMINAL_MARKER_PRESENT:SEAL.json",
    "kind": "TERMINAL_MARKER_PRESENT",
    "replica": "R1"
  },
  {
    "details": {
      "marker": "FINALIZED.json",
      "resource_receipt": {
        "collection_reserve_seconds": 180,
        "deadline": 1789286471.9747434,
        "elapsed_seconds": 1702.720723729988,
        "finished": 1789277374.6954665,
        "fit_cap": 2,
        "gpu_release_verified": true,
        "release_is_receipt_claim_not_live_verification": true,
        "seconds_cap": 10800,
        "stage_count": 9,
        "started": 1789275671.9747434
      }
    },
    "key": "R1:TERMINAL_MARKER_PRESENT:FINALIZED.json",
    "kind": "TERMINAL_MARKER_PRESENT",
    "replica": "R1"
  },
  {
    "details": {
      "marker": "RESOURCE.json",
      "resource_receipt": {
        "collection_reserve_seconds": 180,
        "deadline": 1789286471.9747434,
        "elapsed_seconds": 1702.720723729988,
        "finished": 1789277374.6954665,
        "fit_cap": 2,
        "gpu_release_verified": true,
        "release_is_receipt_claim_not_live_verification": true,
        "seconds_cap": 10800,
        "stage_count": 9,
        "started": 1789275671.9747434
      }
    },
    "key": "R1:TERMINAL_MARKER_PRESENT:RESOURCE.json",
    "kind": "TERMINAL_MARKER_PRESENT",
    "replica": "R1"
  }
]
```

## Stop reason

```json
{
  "type": "monitor_finished",
  "reason": "MAX_20_MINUTE_WINDOW_REACHED",
  "finished_utc": "2026-09-13T05:32:19.178148+00:00",
  "finished_unix": 1789277539.1782167,
  "elapsed_seconds": 1200.000206,
  "poll_count": 10,
  "latest_remote_observation_utc": "2026-09-13T05:30:19.724916+00:00",
  "no_extra_ssh_at_deadline": true
}
```

## Commands, preservation, and limits

- Remote command, exclusively through the authorized wrapper: `bash gpu/ovx_ssh.sh "PYTHONDONTWRITEBYTECODE=1 python3 -B -"`. Exact read-only stdin script and local monitor driver are preserved in JSONL.
- Only stdlib `/proc` identity reads, bounded JSON metadata reads, filename/stat inventories, and SHA256 of the frozen executor. No project runtime imported, outcome payloads opened, scoring, or replay.
- No remote mutation, worker/controller launch, kill, GPU/NVIDIA query, or network beyond the wrapper. Main owns all operational mutations.
- `DONE` marker presence and `FINISHED`/`COMPLETE` receipt fields are distinct observations; launched/claimed/loaded stages are not considered completed.
- `SEAL`/`FINALIZED` presence is not an independent integrity or scientific-success acceptance. RESOURCE GPU release is a receipt claim, not live verification.
- Each snapshot can race process exit or receipt publication. Source checks cover executor bytes and exact process cwd/argv, not every frozen-source file. No model/environment verification.
- Poll spacing is checked locally; no SSH poll is started near the 20-minute cutoff. Any final window after the last poll is explicitly unobserved.
- No tests, interventions, or remediation are run. Read-only observation does not pause or extend the experiment.

JSONL: `/tmp/astra_q0_fulldose_monitor_20260913_attempt1.jsonl`
Markdown: `/tmp/astra_q0_fulldose_monitor_20260913_attempt1.md`
