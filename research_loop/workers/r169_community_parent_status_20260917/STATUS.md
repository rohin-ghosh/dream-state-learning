# COMMUNITY-only credential refresh — September 17, 2026

## Actual refresh, 13:56:49–13:57:04 UTC

All five exact COMMUNITY parent owners were replaced using the existing
pidfd/watchdog custody transaction. Each successor inherited the key sourced
from `~/.codex/nvidia.env`; the old/new comparison was different for all five.
No credential values or fingerprints were recorded and no credentials changed.
The provider is the already-pinned `openai/openai/gpt-6-astra`, not a short alias.

| Parent | Old PID | New PID | Reserved response | Next eligible response | Native PID |
| --- | ---: | ---: | ---: | ---: | ---: |
| C1 | 456729 | 2255712 | 111 | 114 | 2578597 |
| C2 | 564248 | 2256065 | 110 | 112 | 4077813 |
| C3 | 564572 | 2256618 | 104 | 106 | 2525436 |
| C4 | 565196 | 2256929 | 101 | 103 | 2619696 |
| C5 | 352977 | 2257314 | 99 | 102 | 4018497 |

Exact per-owner config, command, source closure, fresh output-bound gate,
PID/start ticks and full byte-preserved attempt manifests are under
`attempt_135646/C*/`. All 182 attempts survived: 48 PUBLISHED with rendering
receipts, 97 SILENT, 37 PROVIDER_FAILED. No pending publication was present at
preflight; the transfer primitive preserves pending publications as well.
No failed/refused request was replayed. No policy, cadence, child process,
legacy/evaluation operator, credential or COORDINATION file was changed.
C1/C5 keep their original cadence3 policy; C2/C3/C4 keep the adopted cadence2
policy. This is an operational environment refresh, not a policy rollout.

## Completion versus exposure — 14:00 UTC checkpoint

**Fresh provider completions: 0. Fresh publications: 0. Fresh renders: 0.**
All five successors are alive with empty logs and no new attempts yet. The
48 inherited renders are not evidence of the new credential working.

The bounded node5 TRAIN metadata audit at13:58:11 UTC found current native
processes and very recent UPDATE heads for every life. Committed counts were
C1=111, C2=111, C3=105, C4=102, C5=99: all below their next eligible parent
counts. Thus the immediate wait is the existing cadence during native sleep,
not evidence of another authentication failure. No child was restarted or
paused to manufacture a provider opportunity.

`NATIVE_1789653491869945712.json` preserves the current config/plan hashes,
process identities and bounded journal head/checkpoint metadata. The process
list contains both the `timeout` supervisor and actual Python native; the table
above identifies the latter. This was not a full-chain or scientific audit.
Actual read:12,808,027bytes against a64MiB cap; no sealed files were opened.

## Bounded follow-through

Read-only observer2273636 runs from14:00:02 to **14:20:02 UTC**, at15-second
intervals, capped at64MiB of local artifact reads. It never dispatches, signals,
publishes, retries or reads remote/sealed files. It excludes every inherited
attempt and separately records actual provider model/status, publication and
hash-bound Astra REQUEST rendering in `OBSERVATIONS.jsonl` and timestamped
`OBSERVATION_*.json` receipts. `OBSERVER_FINISHED.json` is written on completion,
failure or deadline. Do not interpret STARTED as provider completion or delivery.

Next action is to observe genuine new response opportunities. If the bounded
observer expires first, report the missing completion/render evidence; do not
reset the cursor, replay an old request, change cadence or blindly relaunch.

Validation:45 existing custody/watchdog/transaction tests passed before refresh;
50 tests including five new local metadata checks passed afterward. Raw receipts:
`AUTHORITY.json`, `EXECUTION.jsonl`, `CPU_TESTS.log`, `CPU_ALL_TESTS.log`.

## Final handoff — 14:06 UTC

At14:06:08 UTC all five exact successor identities remained alive; every source
pin still matched (16files each C1/C5,67files each C2/C3/C4). Canonical provider
source SHA256 is `4d99658252310c7f57986750ff3002443d5c4038139f79b0381ff6eafbde837e`.
There were still **zero fresh attempts, provider completions, publications or
renders**. Receipt: `INSPECT_1789653968285563565.json`. No inherited result was
counted as fresh. Execution and observer stderr remained empty.

The second native poll at14:03:16 UTC confirmed the same five native identities
and advancing journal heads: C1+11,C2+11,C3+10,C4+11,C5+10 since13:58:11 UTC.
Latest head ages were5–30seconds. Combined remote reads were19,332,205bytes.
For C1/C4/C5 the second bounded64-record suffix did not reach a checkpoint;
their earlier committed counts were not relabeled as fresh measurements.

Per Main's14:06 handoff, COMMUNITY auth duty is complete with stable receipts
and the bounded observer left running until14:20:02 UTC. Actual new-key provider
completion and render remain unverified until a genuine new cadence opportunity.
C1/C5 keep the original cadence3 policy; no second parent, cursor reset,
policy rollout, blind retry or observer extension is authorized by this audit.
