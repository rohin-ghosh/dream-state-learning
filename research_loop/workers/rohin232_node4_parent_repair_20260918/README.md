# R232: bounded NON-MATERIAL R230 node4 parent repair

Status at10:39UTC: **Main reviewed and rebound the four CPU parents.**
The earlier staged-only validation sent no signals or publications. The later
Main handoffs described below affect only the exact existing CPU writers.
No learner operation or lease action is part of either step.
All new files and synthetic test artifacts stay in this worker directory.
No frozen bundle, original node4 wrapper, C2 file or other worker is edited.

## Main adoption receipt — 2026-09-18 10:39 UTC

The92 author-side policy tests passed; Main additionally reviewed the code,
ran2 CPU-handoff tests and reran all4 exact-config validations. At10:38:52–
10:39:07UTC, Main drained each original CPU writer, verified every prior
attempt's source/result hashes and confirmed writer exit before starting its
successor under the same lock, seed and evidence directory. No native learner
was signalled. Historical IDs, counts and outputs remain unchanged.

| Physical | Old CPU parent | New CPU parent | Preserved attempts |
| --- | ---: | ---: | ---: |
| 2 | 488830 | 785257 | 70 |
| 3 / P3 | 491388 | 783596 | 55 |
| 5 | 488850 | 785190 | 52 |
| 6 | 488876 | 785217 | 39 |

Each `physicalN/HANDOFF.json` binds the reviewed config and historical files;
`physicalN/LIVE.json` records startup. The measured CPU handoff interval is
approximately1.01seconds, including the1second liveness wait. No learner pause
or restart is introduced. Actual new parent publication/rendering remains a
separate pending verification, not inferred from process liveness.

This is a prospective R230 parenting treatment: cadence becomes one new
committed response and automatic three-turn retirement is removed. B/C
questioning styles and all attribution/English/privacy checks remain. It is
not the original unchanged sparse-parent control, a learner-row-policy repair,
or a claim of improved uptake. P7 and unparented controls are untouched.

`handoff.py` is the reviewed CPU-only adoption utility; it must not be used
to re-run a completed handoff or start duplicate writers. The staged-only
manual procedure below describes the same safety requirements, not another
action to perform after these receipts exist.

## Scope and cause

Only existing R230-enriched CPU parents physical **2, 3, 5, 6**, retaining
Astra identity and the same lives, programmes, references and evidence stores.
Physical2/3/5 retain B transcript-grounded walkthrough (160 words); physical6
retains C questions-only self-derivation (120 words). All retain 4096 bytes.
No P7, unparented, reserved, frozen-control or native learner is eligible.

The existing loader is `r210_parent.py -> parent_c.runtime() -> source_B/C`.
Its R166 decision calls the R153 community validator, which rejects counts
at or above three and requires `set_aside` plus explicit English release on
the third delivered turn. R166 also gates attempts by old B=2/C=3 cadence,
and its prompt repeats automatic retirement advice. Changing only the R230
programme cannot override those validators. This repair removes those specific
conflicts; it does not establish that any observed P3 silence had only one cause.

## Implementation and provenance

- `repair.py`: exact, fail-closed in-memory projections of the pinned frozen
  functions; no global `require` patch and no mutation of the original policy
  or community module. Three local decision edits remove automatic retirement
  and keep explicit release mandatory for actual `set_aside`; one tick edit
  changes only the boundary threshold to `baseline + 1`. Valid nonnegative
  integer counts remain required. No count, source index, object ID, cursor,
  receipt, credit or historical attempt is replaced to make validation pass.
- `SOURCE_PINS.json`: reviewed SHA-256 pins for original loaders, both arm
  manifests and all four original/enriched config bindings. Every file in
  the selected frozen manifest is checked. Original and enriched programme
  and private-principles bytes are checked against their original pins.
  Changed source fails closed; this worker does not refresh pins automatically.
- `physical{2,3,5,6}/CONFIG.json`: the existing enriched config plus exactly
  one `r230_parent_repair` field. That field binds the physical, original
  enriched config, source manifest, repair/entrypoint code bytes and explicit
  effective policy. Historical `cadence_responses`, `cadence_label` and
  `object_turn_limit` stay unchanged as provenance, **not** as effective limits.
  Effective cadence is one new committed response, never polling-loop spam;
  an unpublished/new boundary, rendered prior publication and unchanged
  journal/attempt guards are still required.
- `parent.py`: read-only `validate`, plus a **future Main-only** `serve`
  entrypoint requiring the reviewed config hash. It delegates to the original
  R210 serve loop and its original `PARENT_OPERATOR.lock`, output directory,
  seed, journal and remote endpoint. It redirects only config read/hash and
  runtime return values inside that new CPU process. It forbids a new opening
  or new seed and permits only existing `poll`/`publish` operations for its
  one physical. P3 need not have a local `OPENING.json`: the original endpoint's
  actual `opening_published` receipt is required instead.
- `test_repair.py`: synthetic CPU fixtures, real frozen B/C validators and
  the original serve loop; provider and transport are mocked. No live evidence
  is invented. `TEST_OUTPUT.txt` records each physical's execution separately.

The adapter preserves exact child-source attribution, English/script checks,
anti-impersonation, response schema, credits/relapses, private prompt payload,
authorizable publication, deadline, masking, controls and privacy boundaries.
Its prompt retains B/C style, removes the conflicting automatic-retirement
phrases and asks for evidence-based continuation **or quitting**. Honest
silence stays silent. Voluntary release still needs explicit English release,
unresolved status, a concrete same-object next step, chosen-object provenance,
valid Tool receipts for claimed progress and new evidence for a repeated move.
No heuristic here proves useful parenting, prevents all repetition, measures
retention or claims a live P3 fix; Main must inspect actual resulting evidence.

The existing deadline stays **September 18, 2026, 18:00 UTC**. Validation and
serving fail after it; do not extend a lease or modify the deadline to make this
repair pass. Treat this as a prospective parent-policy treatment boundary,
not a continuation of an unchanged control or a new H1/H2 result.

## Reproduce CPU validation (safe before review)

From the repository root, using a fresh interpreter for every physical:

```bash
worker=research_loop/workers/rohin232_node4_parent_repair_20260918
for physical in 2 3 5 6; do
  R232_TEST_PHYSICAL="$physical" python3 -B "$worker/test_repair.py" || exit
  python3 -B "$worker/parent.py" validate --physical "$physical" || exit
done
```

No bytecode is written into original directories (`-B`). Tests create and
remove synthetic temporary directories only under this worker. No dependency
installation or GPU is needed. CPU success is **not** live-adoption evidence.

## Exact live-adoption procedure — Main only, after review

Do **not** execute this section during review. This worker intentionally
contains no signal/rebind automation. Main owns the exclusive-writer handoff.
Perform one physical at a time, only for 2, 3, 5 and 6:

1. Review code, four configs, pins and tests. Record the chosen config SHA-256
   printed by `validate` together with the review decision; this config binds
   the exact `repair.py` and `parent.py` bytes. Rerun read-only validation in
   a fresh CPU interpreter immediately before handoff. A hash drift or expired
   deadline is a stop, not permission to repin or extend anything.
2. Discover the **current local CPU parent's** PID from its existing R230
   start/rebind evidence, then independently read `/proc/PID/cmdline`,
   `/proc/PID/exe`, `/proc/PID/cwd` and field 22 (`starttime`) in `/proc/PID/stat`.
   Its argv must be exactly an approved Python interpreter, optional `-B`,
   then the absolute existing
   `research_loop/workers/rohin230_curriculum_20260918/node4_parent.py`,
   `serve`, `--physical`, the selected physical. If Main finds an older
   `r210_parent.py` invocation, separately verify that exact original entrypoint
   rather than matching by substring. Do not select a PID by a broad `pgrep`,
   use `pkill`, kill a process group, or signal an SSH child/remote/native PID.
3. Open a **pidfd for that verified CPU PID**, recheck argv/starttime against
   the evidence, then stop that CPU parent only via
   `signal.pidfd_send_signal(pidfd, signal.SIGSTOP)`. Wait for state `T`/`t`.
   Inspect its existing `r210_parentN/turns` at this quiescent point. Every
   attempt must have `SOURCE.json` and `RESULT.json` with the exact source hash.
   Allowed terminal statuses are `PUBLISHED`, `SILENT`, `PROVIDER_FAILED`,
   `VALIDATION_FAILED`. If an attempt is still in flight, `SIGCONT` the same
   pidfd and allow it to finish, then retry at a quiet boundary. Never stop
   or kill its provider/SSH child midway through publication. If publication
   is uncertain (`PUBLICATION_UNKNOWN`, unmatched intent or unfinished orphan),
   **do not start a successor**; Main must reconcile real inbox/render evidence
   without deleting, rewriting or fabricating a result. Do not leave a merely
   busy old parent stopped while waiting for an in-flight operation.
4. While quiescent and reconciled, save a dated handoff receipt in this worker:
   physical, old PID/exe/argv/starttime, old and new config hashes, binding,
   original output path, SEED hash, all attempt/source/result/publication
   hashes, journal ID, last verified remote cursor reference/hash, unchanged
   object-count ledger and exact review decision. Preserve all original
   evidence in place. Do **not** rerun `prepare`, edit a cursor pin, mint a new
   seed/opening, reset counts/IDs, move the output directory or rewrite the old
   config. Existing remote `R230_BOOTSTRAP_CURSOR` verification remains in use.
5. Retire only that CPU writer via `SIGTERM` followed by `SIGCONT` on the same
   pidfd, then poll the pidfd for confirmed exit. If it does not exit, stop
   the handoff; do not start another writer and do not escalate to a blanket
   kill. Confirm the original `r210_parentN/PARENT_OPERATOR.lock` is available
   with nonblocking `flock(LOCK_EX | LOCK_NB)`. Release the operator's probe
   lock before the successor acquires it; do not remove or replace the lock
   file. Ensure no supervisor is restarting the old CPU writer. The successor
   must itself acquire the **same** original lock; lock contention is fatal.
6. Launch exactly one new local CPU process in the original repository, with
   stdout/stderr retained under this worker. Use the **previously reviewed**
   hash from step 1, not a freshly calculated hash as a substitute for review:

   ```bash
   python3 -B /data/home/rohing/dream-state-orch/research_loop/workers/rohin232_node4_parent_repair_20260918/parent.py \
     serve --physical N --reviewed-config-sha256 REVIEWED_CONFIG_SHA256
   ```

   `N` must be one of 2/3/5/6; launch each separately. Main's process manager
   should detach and retain its PID/log as usual. **Do not use the old R230
   wrapper's `rebind`**: it launches the old wrapper, not this repaired entrypoint.
   No file copy, code deployment, restart or signal on node4's learner host
   is necessary or authorized by this repair.
7. Verify the new CPU PID owns the original lock, the original serve loop's
   new `STARTED_*` carries the reviewed config hash, and a new `PROMPT.json`
   contains `R232_BOUND_R230_NODE4_PARENT_REPAIR_V1` **and** the original exact
   child-evidence serializer reminder. Confirm same journal/life/seed and
   stable IDs/counts; pending rendered-publication checks must not disappear.
   Inspect a newly published turn's real INBOX and rendered child REQUEST
   receipts before calling it delivered; only then does the original ledger
   increment. `SILENT` is not a delivery or proof of correction. Preserve
   validation failures, real child responses and voluntary releases exactly.
8. On failure, do not run old and new writers together. Reconcile any pending
   attempt and retire the failed CPU writer first. Main may restore the old
   reviewed CPU entrypoint using the same output/seed/cursor/lock; do not roll
   back or erase attempts delivered during this prospective epoch. Leave
   learners, C2, P7, other agents and all control/reserved lives untouched.

The signal operations above are only a specification for Main's later approved
CPU handoff. None was executed by this worker.

## Main adoption and actual rendering

Main subsequently performed the exclusive CPU-parent handoffs at10:38:52–
10:39:07UTC on September 18, 2026. Per-physical `HANDOFF.json` and `LIVE.json`
preserve the old/new process identities, unchanged history and measured CPU
handoff intervals. No learner was signalled or restarted.

The independent read-only audit at11:17:30UTC checked the exact inbox text in
actual user-role REQUEST messages and their canonical record hashes:

| Physical | First repaired-parent inbox | Rendered REQUEST |
| --- | --- | ---: |
| 2 | `c087a8c35be644df9fec446e1975af7d` | 2937 |
| 3 / P3 | `72299f008542469aa0e18ec8a8172313` | 2629 |
| 5 | `4b4d7b3bce1a4a77b965ef86b2ceb6e8` | 3133 |
| 6 / MATH_C | `c60c09c8d0654ecd9e8b3201af17b51c` | 3246 |

`FIRST_RENDER_20260918T1117Z.json` contains the full inbox, text and REQUEST
hashes. All four have actual delivery evidence, not merely a running publisher.
This proves neither useful uptake nor retention. Some later physical3/5 parent
attempts still failed the English/script validator; those failures were retained,
not bypassed or represented as delivered turns. No native LEARN-filter policy
was changed by this CPU-parent repair.
