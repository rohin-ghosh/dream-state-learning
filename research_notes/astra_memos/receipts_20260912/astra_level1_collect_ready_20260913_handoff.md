# Level1 collect-ready helper — 2026-09-13

CPU-only implementation. Owned files: `/tmp/astra_level1_collect_ready_20260913.py`, `/tmp/test_astra_level1_collect_ready_20260913.py`, and this handoff. No native collection, remote probe, GPU operation, model/corpus read, runtime edit, repository change, or Git command was performed for this task. Main alone deploys and runs native collection.

## Fixed existing bindings

- Roster: `/tmp/astra_level1_roster_20260913_attempt1/roster.json`, SHA256 `ad1c8d522d295e3c1b33c7e6ed93fbf89c467d3206d61e449d6844905fa19423`.
- Runtime: `/tmp/astra_level1_skill_run_20260913.py`, SHA256 `6f4c391419500d046e2b15729ee09485baa07b45938db1f96484b07e69e1ed9e`. Imported/executed only by the native child, never imported by this helper. The helper itself does not score.
- Exactly node1's `batch_node1_parentfix` or node2's `batch_node2`, under the roster directory. The batch `started.json` must bind the same roster hash. The existing pinned precheck file supplies boot-ID/UID checks for the selected node; no hostname or GPU query is used.

## Main's native CLI

Run on the corresponding node through Main's existing access pattern:

```sh
python3 -B /tmp/astra_level1_collect_ready_20260913.py \
  --node node1 \
  --batch-dir /tmp/astra_level1_roster_20260913_attempt1/batch_node1_parentfix

python3 -B /tmp/astra_level1_collect_ready_20260913.py \
  --node node2 \
  --batch-dir /tmp/astra_level1_roster_20260913_attempt1/batch_node2
```

One pass over the selected node's six existing cells, sequentially. No polling, scheduler, GPU launch, native prepare, runtime mutation, or automatic retry. Main can invoke another pass later for cells previously pending; an already attempted/claimed cell is never retried.

## Readiness and custody

- Missing launch receipt or missing capture-complete marker is `pending`, not success. A batch failure with no launch receipt, or `controller_failure.json`, reports `failed` and never invokes collect.
- The original receipt PID must be absent from `/proc`. A still-present PID, including zombie or reused PID, conservatively reports `pending`. No process is signalled to make a cell ready.
- Checks selected roster identity/root/GPU fields against the exact `launched.json`; checks its original controller command, PID/PGID, prepared plan hash, controller-start plan binding, spec pin and frozen runtime pin. Reads and hashes the same `capture_complete.json` bytes, requiring matching launched plan pin, integer120 calls, and `scored=false`.
- Child interpreter is exactly `plan.python`, with its SHA256 matching `plan.python_sha256`. Command is that interpreter plus `-B`, the exact frozen runtime, `collect --root ROOT --plan-sha256 PIN --completion-sha256 SHA --out ROOT_collected`. No `--allow-gpu` appears. GPU visibility is empty in the collection child.
- Full native artifact/request/response/adapter/source/scoring validation remains exclusively in the frozen runtime's collect implementation. This helper is an operational readiness filter, not an independent native replay, scientific approval, or formal C11 framework.

## One-shot outputs and errors

- Native output: `ROOT_collected` (fresh sibling directory, created by runtime).
- Native claim: `ROOT.collection_claim.json` (created by runtime, never pre-created by this helper).
- Helper attempt/logs: `ROOT_collection_driver/attempt.json`, `stdout.log`, `stderr.log`, `result.json`, all fresh and external to ROOT. Atomic directory creation owns one helper attempt even if the subprocess fails before making its native claim. Existing claim, output, or driver-attempt path yields `claimed`; nothing is overwritten or retried.
- Readiness is rechecked just before invoking the child. A race with another collector fails visibly and leaves the helper's one-shot evidence. Existing root contents are never written by this helper.
- Each native collection subprocess has a **180-second wall timeout**, including interpreter startup, with stdout/stderr streamed to fresh external logs. At most six child invocations per pass; there is no180-second aggregate-node deadline. Python's subprocess timeout terminates only its own collection child; no original controller, worker, or foreign process is targeted.
- Nonzero native exit, timeout, changed readiness, missing success receipt, or score/receipt hash disagreement produces `status=error`; result and logs are preserved. Successful exit alone is insufficient: `collection.json` must bind the observed completion SHA and actual `scores.json` SHA. No partial scores are synthesized or interpreted.
- One JSON result per selected cell is printed. Exit0 means only `pending`, `claimed`, or `collected` statuses; **not** that all cells finished. Any `failed`/`error` cell, or global input-binding failure, returns exit1. Independent cells are still considered once after a per-cell error; errors are not swallowed or retried.

## CPU validation / freeze

`python3 -B -m unittest discover -s /tmp -p test_astra_level1_collect_ready_20260913.py -v`

**12 tests PASS, 0.143s.** All subprocess calls and node/process readiness are mocked. Tests cover pending, live controller, complete+claimed, all claim forms, controller failure, plan/completion/interpreter pins, exact external command/logs, root immutability, native nonzero/timeout/missing receipt, single-pass node selection and nonzero aggregate error status. No native runner was imported or called.

Owned-file hashes are provided in the final EDITSTOP message. Main owns native deployment and execution; this handoff grants no new scientific claim or launch scope.
