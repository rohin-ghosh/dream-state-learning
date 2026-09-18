# R169 v2 admission and startup design — not a launcher

September 17, 2026. Non-material safety hardening; no parent policy, cadence,
child, model, lease or experiment changes. No live integration performed.

## Consumed v1 incident, not generic approval

Keep `refresh.py` frozen at
`3d27d8b5846435c1ba97f9922dc27e7dec05904013a4edbe5bcd3dabf378a716`.
Its 18 launched bindings pin those bytes. Do not patch it or restart processes to
install this helper. Restrict any incident interpretation to the consumed
`DISCOVERED.json` inventory; v1 is not approved as a reusable recovery utility.

Independent read-only evidence at September 17, 2026, 14:03:20 UTC:
`/tmp/R169_INCIDENT_REVIEW_1789653800306537346.json`, SHA256
`f1e031195ff96f4d959492e341f551171c92a9c42944e435c0a54893cd4284be`.
All 18 entries passed exact argv grammar and canonical confinement (10 module,
8 standalone); source/config/operator pins, bound predecessor ledgers/cursors,
STARTED/spawn/branch/model bindings, and live successor argv/cwd/UID matched.
All original PIDs were absent. The reported credential-equality booleans were
read from Main's observation, not independently recomputed from secrets.
STARTED and observed liveness do not prove eventual provider replies, delivery,
rendering, or future liveness. Main owns those checks.

The generic misleading-argv/traversal gaps were not exercised by these 18
entries. Successful observed startup reduces the incident relevance of v1's
weak predictive CPU preflight; it does not improve that preflight for reuse.
The missing operator-death SIGCONT watchdog remains a real generic risk, not
evidence that any incident parent was stranded.

## Implemented v2 admission helper

`refresh_admission_v2.py` is read-only. It does not import/modify v1, inspect
environment variables, execute source, send signals, contact a provider/node,
create receipts, or launch a process. It returns
`READ_ONLY_ADMISSION_NOT_TERMINATION_OR_SERVING`, never a launch authorization.

Main must provide an independently approved, hash-pinned inventory, expected UID,
canonical interpreter/repository, and approved source/config references. The
helper binds observed PID/start ticks/argv/cwd/UID to exactly one inventory entry;
checks running/non-stopped state; and admits only these exact argument shapes:

```text
<approved canonical Python> -B -m gpu.orch_r133_programme_parent \
  --config <branch>/CONFIG.json --repository <repository> --output <branch>/parent
<approved canonical Python> -B <branch>/PARENT.py \
  --config <branch>/CONFIG.json --repository <repository> --output <branch>/parent
```

The branch must be a direct child of
`<repository>/research_loop/workers/r167_legacy_parent_rollout`. Config/output and
standalone source must belong to the same branch. Module source is the exact
`gpu/orch_r133_programme_parent.py` under the inventory-bound cwd. Symlinks,
traversal, lexical aliases, other flags/orderings/entry points and cross-branch
paths refuse, even if accidentally included in the approved inventory.
Source/config/inventory reads use pinned hashes, bounded regular files, no-follow
directory descriptors and stable read metadata. This is not an import sandbox
or a substitute for immutable source/dependency and interpreter custody.

## Serving-startup preflight: required future integration

**Design only; no runner or v2 stop/start flow has been implemented.** A v2 caller
must distinguish source loading, startup prerequisites, and actual serving:

1. Before stopping a predecessor, stage immutable, separately named v2 copies
   under a fresh output root. Source the credential environment before executing
   the receiving interpreter. Do not write credentials or headers to any binding,
   argv, receipt or log. Bind provider bytes, canonical endpoint/model, transport
   rules, parent source/import closure, config, interpreter and operator hashes.
   Source-load success alone is explicitly `CONFIG_AND_SOURCE_LOAD_ONLY`.
2. A read-only startup probe must exercise the original config validator and
   original cursor initializer (including original predecessor hash/resume
   checks, if present), and require the original persistent-duration/wall check.
   Preserve `max(original_initial_cursor, reserved_cursor)`; no schedule or
   policy rewrite. Source variants differ: enumerate/pin their actual startup
   gates rather than assuming every archived serve has the current gates.
3. Run any original transport preflight only as a separately authorized,
   read-only check: imports/location of the existing TRAIN snapshot/publication
   API, not a publication. Check that the fresh serving output is unoccupied and
   writable without creating the output directory that original serve expects
   to create exclusively. Credential presence/equality evidence is a boolean,
   never raw values; neither implies successful authentication. A one-shot
   provider test, if Main explicitly elects it, needs its own no-retry dispatch
   marker and must not be silently repeated by startup checks.
4. Do not run full `serve()` as a preflight: it can dispatch requests or publish
   to a child. Use a separately reviewed, exact-source-bound startup probe that
   returns before the first loop tick. Prove its AST/code boundary on every
   supported pinned source. Preserve the frozen parent code used for actual
   serving, except the already approved initial-cursor delta and transport
   injection. An invented success receipt is not equivalent to running these
   checks. No such extractor/runner is supplied by this admission-only helper.
5. Bind the startup receipt to inventory, process identity, all source/config
   pins, selected output, reserved/effective cursor, observed wall, timestamp and
   short expiry. Recheck inputs and each time-sensitive condition after the
   predecessor reaches a settled boundary. A failed/expired probe leaves it
   running or resumes it, never terminates it. The final ledger must reserve all
   settled MISSING/SILENT/PUBLISHED sources and preserve pending inbox IDs; no
   catch-up of uncertain requests. Retain original evidence, don't rewrite it.
6. A future launcher must arm a detached same-pidfd SIGCONT watchdog **before**
   SIGSTOP, prove the same approved identity and stopped/childless state, and keep
   the bounded pause within the watchdog deadline. The existing
   `gpu/orch_r167_parent_watchdog.py` is a candidate for separate bound review,
   not implicitly approved here. Required tests include operator death, timeout,
   SIGCONT failure, identity drift, in-flight transport and ledger changes.
7. Preserve create-only termination/spawn markers and confirmed predecessor exit
   before exactly one successor attempt. After spawning, bind live identity to
   STARTED and distinguish `SPAWNED`, `STARTED_OBSERVED`, `SERVING_REPLY`, and
   delivered/rendered evidence. A failed or uncertain spawn/receipt is not
   permission to retry. Neither this helper nor a preflight receipt supplies
   those launcher guarantees.

## Tests

Run only synthetic CPU tests; they make no live calls:

```bash
env TMPDIR=/tmp CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 \
  PYTHONPATH=/tmp/r136-pytest-support python3 -B -m pytest -p no:cacheprovider \
  research_loop/workers/r169_parent_auth_refresh_20260917/test_refresh_admission_v2.py
```

The separate `test_refresh_review.py` retains expected failures characterizing
frozen v1; do not turn them green by editing the live operator.
