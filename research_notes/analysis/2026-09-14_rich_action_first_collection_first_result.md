# Rich action-first collection: first result

2026-09-14, Builder/Schrodinger. **All four native TEACH processes completed;
2/64 episodes action-complete; 12 UNREVIEWED candidates per view; zero fits.**
These are coached execution outcomes, not new learning or content approval.

## Bound execution and evidence

- Exact execution source: `60dbf789a37f09261015dddf1d9f91bceba55879`.
- Prospective protocol SHA256:
  `509f85c17d4be373eb1e917ee11e5134dcb447257a376163fe6a995d533eece9`.
- Full source archive, packaged locally on `/data` under `gpu_artifacts_local`,
  transferred and verified on A100:
  `0617b065f721598d5a08b1ce4087ab529eb486eb87ca76753a9876c8f43f8871`.
- Prelaunch notebook packet `ebb72508`; actual-PID packet `734b6f04`. Each of
  four actual-source prepares passed with zero model calls. Main's 41 CPU tests
  were already logged; no additional test sweep preceded launch.
- Root: `/tmp/astra_rich_action_first_20260914_attempt1`, shards0–3 on A100GPUs0–3.
  Guardians139567/139568/139569/139570; native139637/139618/139631/139628.
  Launch19:30:00UTC; every guard's first physical/CVD admission clear19:30:01.
  Initial attached preflight's unreadable sshd rejection was preserved; detached
  preflight passed without adding an exception or changing the scanner.

The original source EXPOSE and baselines were reused unchanged. There were no
EXPOSE, critique, baseline, correction, or fit reruns. Every process mounted
37ec and verified the same adapter state and frozen base after readonly use.

## Actual results, including all failures

| Shard | Actual native calls | Attempted / planned episodes | Action-complete | Rows per view | Phase wall seconds |
|---|---:|---:|---:|---:|---:|
| 0 | 21 | 16 / 16 | 1 | 6 | 176.500 |
| 1 | 16 | 16 / 16 | 0 | 0 | 146.866 |
| 2 | 16 | 16 / 16 | 0 | 0 | 151.455 |
| 3 | 21 | 16 / 16 | 1 | 6 | 196.946 |
| Total | **74 / 384 cap** | **64 / 64** | **2 / 64** | **12 each** | **671.767 summed** |

Action-complete means all six planned commands, four actual reads, two actual
commits, and final GOAL. The matched TERSE/RICH/RICH_ACTION_ONLY candidates are:

- `ASTRA-RICH-20260914-V1-SHARD-0-TRAIN-B/task/2` — six turns.
- `ASTRA-RICH-20260914-V1-SHARD-3-TRAIN-A/task/3` — six turns.

Coverage is only two of sixteen TRAIN worlds and two of four shards. Both
episodes target the second final-goal case; their display orders differ. Neither
source world contributes a complete opposite-goal pair. No missing cases were
replaced, discarded from denominators, or reclassified as successes.

All **62 other episodes** ended with `exact_rationale_action_envelope_required`.
For example, shard1 `teach/CALL_000.json` begins `RATIONALE: The current node`
rather than the frozen parser's exact `RATIONALE\n`. Its response is terminal
and untruncated, but the action was not executed. This is an observed envelope
contract failure, not evidence that a repaired continuation would reach GOAL.
No parser change, response stripping, or retrospective pass is applied.

All twelve executed candidate turns carry the non-blocking diagnostic
`explicit_prediction_line_required`. That flag no longer aborted execution;
its absence/presence is not a semantic verdict. The other 62 responses were
rejected before content checking, so they must not be counted as content passes.
Every retained row remains `reviewed=false`, `fit_ready=false`.

There were **zero native errors, nonterminal responses, or truncated outputs**.
Actual totals:29,000 prompt tokens,7,252 generated tokens including EOT,3,669
raw whitespace-delimited words. Process-phase interval19:30:01–19:33:18UTC;
sum671.767s =0.186602 A100-hours of phase wall time, including loading/checks,
not metered kernel use or billing. Declared four-guard maximum was4.4 A100-hours.
A subsequent physical check found GPUs0–3 at0MiB/0% utilization.

## Preservation, verification, and decision boundary

Terminal archive SHA256:
`508b12e464ee4379fce750675822235d4c23096ac6149ad6c39545dca1f672e7`.
Verified local persistent copy:
`gpu_artifacts_local/astra_rich_action_first_terminal_20260914_attempt1/terminal.tar.gz`.
Extracted root is the adjacent `extracted/astra_rich_action_first_20260914_attempt1`.
The terminal archive excludes the separately preserved full source payload.

Using the exact archived source, CPU replay verified all four lesson documents,
native-call/prompt/raw/error joins, full output inventories, matched candidate
views, policy, token ledgers, and unchanged-state receipts. Downloaded inventories
match the remote `CPU_REPLAY_CHECK.json`. This is literal internal replay and
recorded-state checking, not independent tensor authentication or content review.

The v1 zero-candidate result remains unchanged. V2 demonstrates two actual coached
trajectories under relaxed content gating; it does not demonstrate transfer,
an improved learner, or a richness advantage. Shared content review contract
`3476a1415100470835df7176f9f8df3fbbbcd4f6a665f05772575636c415b77b`
is separate from these primary counts. No candidate has been promoted here.
Any three-view fit remains conditional on actual all-six-turn content approval
and Main's selection of a separately bound finite fit/readout protocol.
