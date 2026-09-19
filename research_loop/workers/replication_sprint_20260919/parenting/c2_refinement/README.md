# C2 refinement — READY candidate, NOT deployed

Prepared September 19, 2026. Main owns scoped deployment review and the
CPU-only handoff. This worker made no provider calls, published no messages,
signalled no process, read/copied no credential, and edited no live file.
No commit or push. The auth-blocked pair is untouched.

## Prepared bytes and evidence

- `MANIFEST.json`: concrete successor preview, accepted by the ORIGINAL strong
  wrapper's manifest validator. SHA256
  `6ecbcacfde1deaae9e06af1aa6b00fc95eb3a8c966d6f056caaf98ce4a0e9b49`.
- `SUPERVISOR_SEED_MANIFEST.json`: preferred next-session integration through
  the existing live supervisor. SHA256
  `14b4a285dda3abcb7ccd9421ccbd8135bd26883cde7cead410e52a56cd073330`.
- `COMBINED_ADDENDUM.md`: original live brief VERBATIM, followed by the new
  policy only. SHA256
  `14515a0a0306a40846540c647d565e17885a93b64d7a0f0b4472f36c21a1402f`.
- `INSTALL_NEXT_SESSION.patch`: unapplied, adds only one prospective manifest
  to the original service's discovery directory. SHA256
  `5a42f5a572b2cdd3bcd80a8d4f43b7c5d1fab8b30b5c93f45eb6c55e45e20c96`.
- `CPU_TEST_RECEIPT.json`: 19 passing CPU tests plus actual generated-manifest
  validation. These test original source functions in isolation and synthetic
  filesystem fixtures; they are NOT deployment or learning-success receipts.

The preview CONFIG changes only predecessor output, predecessor STARTED hash,
and source cursor (564 at preparation). No provider/model/effort, 90-word
ceiling, cadence, poll interval, object budget, locks, native identity, wall
bound, visibility, learning rows, checkpoints or confinement changes.
There is no explicit lifetime call ceiling in this C2 config: do not import
another arm's budget. All old dispatches and usage remain in their old ledgers;
new local directory numbering is not a reset of experiment-wide accounting.

## Policy delta and prospective measurement

One small task -> actual artifact -> concrete check of that SAME artifact.
Keep the target through the next observable ACT; an intermediate THINK does
not justify a new subject. If the turn arrived after a THINK request, recognition
is unknown, not failed. Actual human priority or new environmental evidence may
redirect it explicitly. Respect the existing three-rendered-turn mismatch
budget; do not rename an exhausted mismatch to reopen it.

Mix available math, reading, writing and reasoning across successive objects,
not as bundled tasks. Credit only actual completed work. Supply neither task
answers nor new passages/scene information not released to this parent view.
No new memory/retention pins or prescribed thought transcripts. Persistent
parenting remains primary; no taper, absence or LR change.

The slow-LoRA/fast-context mechanism remains a hypothesis. Main's prospective
plan is pinned in BOTH manifests, SHA256
`2b7e70e1e6cae4e2b642bdc690fa2dd3b3ad66ca3e90a265c18236aa003af9f1`:
`../../operations/C2_REFINEMENT_MEASUREMENT_PLAN.md`.
Measure the first SIX committed ACTs after verified delivery of the new
policy's first turn: exact instruction visibility and timing, requested/actual
artifact, attempted/correct check, unknowns, later reminder-free reuse and
concurrent interventions. Group turns before one ACT. This is a one-life
exploratory intervention, not causal replication or proof of adapter retention.
The measurement document/audit is not injected as new parent-visible feedback.

## Freshness and exact remaining blocker

Fresh ps at 14:40:24 UTC shows publisher325487 and supervisor361010 with their
expected original argv and start times. Previously verified start ticks are
753205/822432; Main must recheck exact identities at handoff. Native binding
verified on ovx3 at 14:25:13 UTC: PID1139778/start ticks30025875, LOAD11505.
This is identity/liveness evidence, not a fresh ACT-success claim.

Actual nested publisher CONFIG is hash-bound to STARTED and has NO
`questions_only_bank_path` key (not just null at the manifest top level).
Native binding/PLAN/GUARD have no questions-only settings; GUARD's similarly
named source-pin filenames do not enable that mode. A future bank key,
including null, is a conflict: stop this handoff and report it, not the life.

At SOURCE_AUDIT's 14:41:19 UTC cut, current session has 113 reserved attempts:
110 PUBLISHED, three historical HTTPError/MISSING, cursor564. Publication
`f2d22684d6b84e14a8db55542d24d4fe` (parent_000112) lacks DELIVERED evidence.
That exact publication must be reconciled or allowed to render; do not replay
it, call it failed, erase it, or count it as an applied correction. A newer
attempt may exist by deployment. This worker is not waiting indefinitely for
a settled window; Main now owns that short critical section.

The audit carries two older missing-consumption receipts explicitly as unknown:
`16aba5d9069349a0965977c88202c798` and
`f3df03f60e984c54a3ee5ece885e000b`. It retains the older PARENT13 boundary
without claiming whole-life totals. The original service records delivery
only for its current output; Main's receipt collector must carry/reconcile
these inherited IDs separately rather than assuming a successor solves them.

## Exact preferred integration: keep the supervisor

The unchanged `post_reboot_c2_p7_20260919/c2_service.py` already supports this
route: it selects the newest `c2_session*/MANIFEST.json` whose referenced output
has a real STARTED. The prepared seed references the REAL old config/output
and STARTED, explicitly as the old policy, but supplies the addendum for the
NEXT freshly generated session. No fake STARTED, relabelled old results, or
live config overwrite. Original service recomputes max reserved SOURCE at the
actual handoff and binds the old STARTED; it inherits all original source pins.

Read-only preflight (safe now; it does NOT authorize deployment):

```bash
ROOT=research_loop/workers/replication_sprint_20260919/parenting/c2_refinement
python3 -B "$ROOT/candidate.py" --check-seed "$ROOT/SUPERVISOR_SEED_MANIFEST.json"
```

In Main's approved process-inspection context, add `--require-live-identity`.
The worker's sandbox could not expose `/proc/<pid>/stat` to the preparation
script; the interrupted escalation did not run. Preparation therefore uses
explicit dated observations instead of claiming a new exact proc check.

Only after Main approves these exact bytes, confirms the same live native,
supervisor/publisher identities and question-bank absence, and takes ownership
of the settled CPU handoff:

```bash
ROOT=research_loop/workers/replication_sprint_20260919/parenting/c2_refinement
apply_patch < "$ROOT/INSTALL_NEXT_SESSION.patch"
```

This installs the prospective seed at:
`research_loop/workers/post_reboot_c2_p7_20260919/c2_session_refinement_seed_20260919/MANIFEST.json`.
Do not install early: if the publisher exits on its own, this seed affects the
supervisor's next launch. Main then drains ONLY the exact idle, settled CPU
publisher through its reviewed identity-bound handoff; no signal command is
provided as a shortcut, and this worker issued none. Keep supervisor361010,
its service registration, its original locks and native1139778 running.

The existing supervisor automatically creates its ordinary new session,
recomputes the cursor and executes its original command:

```text
/usr/bin/python3 -B .../checkpoint_tail_parent_strong.py
  --manifest <supervisor-created-new-session>/MANIFEST.json
  --manifest-sha256 <actual-new-manifest-sha256>
```

Its `Popen` has NO environment override: it inherits the existing C2 supervisor
environment, not Main's pair-blocked environment. No new service or credential
transfer is required. This is a source-verified supported continuation path,
not evidence that the inherited credential has already authenticated: confirm
the first actual authorized provider receipt. On401 preserve the failure and
seek secure renewal/scoped Main review; no fallback, key retry, environment
extraction or cross-life copy is authorized here. A same-C2 in-memory handoff
is unnecessary unless this preferred route proves unavailable; it would need
a separate identity-bound Main authorization, not permission inferred here.

`MANIFEST.json` is a directly validated successor preview, NOT the preferred
command to launch from Main's shell. Its fixed cursor is stale as soon as new
work appears. Never run a second publisher alongside the supervisor. Prefer
the seed route, which preserves the live supervisor's environment and computes
the cursor at handoff. No old pending attempt is edited by either prepared file.

## Receipts Main must collect after an authorized handoff

Record old CPU exit/new STARTED times (parent-only gap); original native must
continue. Pin the new generated manifest, CONFIG, combined SYSTEM and provider
route/usage. Match policy hash, predecessor STARTED and cursor. First dispatched
source must be new, with no replay of old SOURCE reservations. Record new parent
publication -> consumed INBOX -> actual ACT request visibility -> committed ACT.
Only that verified delivery starts the policy epoch and six-ACT window. A live
CPU PID, PUBLISHED result, or a printed claim alone is not successful uptake.

## Exact changed paths (all inside this directory)

`README.md`, `TO_MAIN.md`, `POLICY_DELTA.md`, `COMBINED_ADDENDUM.md`,
`candidate.py`, `test_c2_refinement.py`, `PROVENANCE.json`,
`CPU_IDENTITY_OBSERVATION.json`, `NATIVE_OBSERVATION.json`, `SOURCE_AUDIT.json`,
`MANIFEST.json`, `SUPERVISOR_SEED_MANIFEST.json`, `INSTALL_NEXT_SESSION.patch`,
`session1/CONFIG.json`, `CPU_TEST_RECEIPT.json`, `STATUS.json`.

The earlier replacement-service draft was discarded before any run. The final
candidate uses only the original supervisor and original addendum hook.
