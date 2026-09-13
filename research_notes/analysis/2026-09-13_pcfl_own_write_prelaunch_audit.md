# Independent prelaunch audit: scoped PCFL own-write diagnostic

Date: 2026-09-13 PT  
Reviewer: Laptop Codex, fresh read-only review  
Builder source reviewed: committed formation/readout at `adf39c4a`, writer at
`5fb67f58`, command at remote helper commit `24d416d7`; uncommitted lifecycle
controller `gpu/astra_pcfl_own_write_outer.py` as observed after that commit.

## Verdict

**CONDITIONAL GO as a narrow, exploratory storage diagnostic; HOLD launch until
the reducer and lifecycle controller are frozen and tested.**

If those gates close, this is a useful low-cost separation test after the failed
C0 route ceiling: it can determine whether authentic child-produced memory rows
can be written into an adapter and emitted after a cold, source-withdrawn load.
It does **not** repair or validate the route benchmark. It also does not yet test
experience-driven action improvement, traversal, compression, recurrence,
parenting, retention, or the Dream--LoRA--Think flywheel.

## 1. Is the supervision authentically the child's own experience?

**Yes for the target bytes, with an important policy qualification.**

The successful path has strong byte-level provenance:

1. A native C0 child emits eight `EXPLORE` actions.
2. The deterministic world returns the corresponding public receipts.
3. The same child emits eight `EVENT` records immediately after those receipts
   and four `LINK` records after the event phase.
4. Admission accepts only exact records grounded in issued receipts and, for a
   link, two already admitted child events.
5. Formation retains the whole UTF-8 response, token IDs, finish state, capture
   hash, and source/model identity. The writer replays all 20 captures.
6. The supervised **targets** are exactly the admitted child `EVENT`/`LINK`
   bytes. The writer checks the target span against the original native response
   and masks the harness-authored memory prompt from loss.

No ideal row, deterministic service answer, parent text, hidden route answer, or
private expected-bank string becomes a supervised target. The preparation code
does tokenize expected structural strings for length/identity measurements; the
writer process therefore sees them as validation metadata, but they are neither
model input nor loss-bearing text. This is acceptable for the scoped diagnostic
and should remain stated explicitly.

The qualification is that the life is a **fixed curriculum, not autonomous
exploration**. The harness preselects all eight actions and four connected event
pairs from the private world structure. A child output that chooses another
valid available port or link fails the entire formation. There is no retry or
root replacement, so this is not post-hoc cherry-picking among completed lives;
nevertheless a successful bank is conditional on matching the harness's chosen
path. The correct description is:

> child-emitted, world-grounded records from a preselected curriculum path

not “the child autonomously chose what to experience” or “the child discovered
the links.” The actions themselves are not trained; only the child's subsequent
memory records are targets.

## 2. Exact causal claim of the three conditions

The three conditions are:

- `AUTH_WRITE`: a fresh rank-8 adapter receives 200 updates on 12 admitted child
  rows compiled into 17 address blocks, eight trained wrappers, three replayed
  event blocks, and five epochs.
- `NO_WRITE_C0`: the same LoRA-enabled inference engine and exact read roster,
  but no adapter and no fit.
- `EXACT_CHILD_SERVICE`: a deterministic map from each of the 17 read addresses
  to the admitted child block. It makes zero model calls and is a ceiling/check,
  not a causal model arm.

Given clean lifecycle and a prospectively frozen reduction, `AUTH_WRITE` over
`NO_WRITE_C0` on the held wrapper W8 supports only:

> This particular LoRA write caused a cold-loaded model to reproduce more of the
> exact address-to-block mappings compiled from its own admitted records, under
> a new surface wrapper, than the unchanged base model did.

The deterministic service can establish that the addresses, source joins, and
scorer have exact answers; it cannot establish model competence or learning.

The comparison does **not** support:

- action-policy improvement or downstream route success;
- autonomous experience choice or discovery;
- generalization to new facts, roots, addresses, or tasks (W8 changes only the
  wording around the same trained addresses and targets);
- connected reasoning merely because four `LINK` strings were stored;
- compression, forgetting resistance, no-harm, lifetime improvement, parenting,
  or superiority over a strong evolving textual-memory baseline;
- a population estimate, because there is one root, one life, one initialization,
  and one fit;
- semantic-content selectivity against an equally trained wrong-child or
  permuted-content adapter. `NO_WRITE_C0` isolates the whole write operation,
  not the correctness of its content.

A wrong-child or registered `EVENT_TWIN`/`LINK_PERMUTE` write would be the
minimal later content-causal control. It is not required if this run remains
explicitly a one-life storage diagnostic.

## 3. Leakage, selection, replay, pseudoreplication, and metrics

### Clean properties

- Formation prompts contain only public affordances, executed receipts, and the
  child's prior visible commitments. The readout actor accepts only a roster ID
  and constructs the memory prompt internally.
- The exact-child service and scorer targets are read only after each model
  response and do not enter the model-visible read prompt.
- Root, actions, links, schedule, replay selection, seeds, roster, wrapper set,
  token caps, and dose are fixed before native formation.
- Malformed, truncated, mismatched, or incomplete formation fails without a
  replacement, skipped call, or repaired target.
- AUTH and C0 use identical LoRA-capable engine settings and the same roster.

### Limitations that must appear in every result

- **Resubstitution:** all 17 address mappings are training mappings. W0--W7 are
  trained prompt surfaces. Only W8 is a held wrapper; neither its address nor its
  answer is held out.
- **Pseudoreplication:** 153 read calls are 17 addresses x 9 wrappers, backed by
  only 12 unique child rows (8 events, 4 links) from one life. The claimed 800
  “presentations” are repeated views/epochs of these rows, not 800 experiences.
  The experimental unit is one fitted life, not 153 or 800 independent samples.
- **Dependence:** `EVENTS_AT` and `LINKS_FROM` blocks reuse source rows; some
  contain two rows. Wrapper outputs are repeated measurements of the same
  mapping. Do not compute a binomial confidence interval or p-value using 153.
- **Selection:** a successful formation is conditioned on the child matching a
  preselected action/link path. Preserve a failure as the result; do not rerun a
  seed or select another root under the same diagnostic label.
- **Replay/dose:** three event blocks are repeated beyond the 17 first blocks;
  every block then appears under eight wrappers for five epochs. Report this as
  12 source rows, 20 scheduled blocks, 160 encoded examples per epoch, 800
  presentations, and 200 optimizer updates. Do not collapse these counts.
- **No matched trained control:** C0 has no optimizer or generic-dialect update.
  An exact nonce gain is still evidence for mapping storage, but not for absence
  of generic write/style effects.
- **No absent/wrong-root reads:** every roster address was trained. This prevents
  a claim that the adapter abstains selectively on unknown or foreign memories.
  It does not block the narrower claim that it can reproduce the trained
  mappings, especially if the full per-address output vector is reported. An
  absent/wrong-root roster is a cheap recommended extension, not a prerequisite
  for this one-life acquisition diagnostic.
- **No preservation test:** the run contains no independent base-capability or
  route canary. A positive memory read may coexist with severe interference.
  This bounds the claim to acquisition; it does not block that narrow test.

### Frozen reduction required before launch

The command saves per-call `strict`, `semantic`, `strict_stop`, and
`semantic_stop`, but it freezes no primary endpoint, aggregation, success rule,
or exact-service reduction. That creates avoidable discretion after output.

At minimum, freeze a tiny reducer before formation:

1. Primary descriptive endpoint: paired AUTH minus C0 **W8 `strict_stop`** over
   the 17 fixed address blocks, reporting the full 17-bit vectors.
2. Integrity ceiling: exact-child service must be `strict_stop`-equivalent on
   all 17 blocks (the service itself has no stop reason, so define this as exact
   byte equality rather than pretending it generated).
3. Secondary diagnostics, never pooled as independent trials: W0--W7 by address;
   `READ EVENT` (8), `READ EVENTS_AT` (6), and `READ LINKS_FROM` (3); strict,
   semantic, refusal, false-row, and truncation counts.
4. State either a prospective numerical pass threshold or label the outcome
   descriptive with `scientific_pass=null`. Do not choose strict versus semantic
   or W8 versus all wrappers after inspection.
5. Preserve all raw responses and report that `n_lives=n_fits=n_roots=1`.

## 4. Minimal gates before any launch

### CPU/source gates

- Commit and pin the final command, reducer, lifecycle controller, and all tests.
  At audit time the command is committed at `24d416d7`; the outer controller is
  uncommitted and has no visible focused test suite, so launch is **HOLD**.
- Re-run and archive: formation 27 tests, readout 33 tests, command 20 tests,
  writer 14/14 including both opt-in numerical tests with no skips, and the new
  reducer/controller suites. The builder already reports the 14/14 numerical
  CPU parity run; bind its exact log/source hashes in the launch record.
- Freeze the actual official base receipt, 14 model files, tokenizer/template,
  clean bf16 base tensor hash, PEFT/runtime versions, all source bytes, installed
  EngineCore shutdown source, manifest file hash, schedule/roster hash, scorer,
  endpoint, and thresholds before the first child call.
- Require fresh, nonoverlapping formation, fit, AUTH-read, and C0-read directories;
  no pre-existing adapter, stage retry, or output-dependent reseal.

### Resource/lifecycle gates

- One exact GPU UUID per stage; empty controller CVD; queue/allocation hash and
  same-UID process visibility clean before spawn.
- Run each formation, fit, AUTH readout, and C0 readout in a fresh process with
  an outer hard deadline that includes cold load, work, shutdown, process exit,
  GPU release, and evidence inventory.
- Bind and call the installed `llm.llm_engine.engine_core.shutdown`; after it
  returns, still verify exact worker-group exit and `nvidia-smi` vacancy.
- The final resource observation must be host-local/detached with empty CVD and
  no SSH ancestry or inherited transport FDs. The current outer merely sleeps
  four seconds; it does not prove this property and can repeat attempt 2's
  unreadable-`sshd` finalization failure.
- Preserve one-shot failures. No generic unreadable-process/`sshd` exception,
  no manual cleanup presented as normal completion, and no later observation
  used to upgrade a failed original finalization.
- Require complete 20-call formation, exactly one 200-update fit, both complete
  153-call readouts, zero retries, exact file joins, and final source/input
  rehashes. Any failure is engineering/debug evidence only.

## 5. Is this the highest-value next experiment after C0 failed?

It is **useful but not decisive**. The failed C0 result says the clean 7B model
cannot execute the current route interface even when memory is supplied. This
readout uses a much simpler exact-address interface, so the C0 route failure does
not invalidate it. A clean positive result would localize the stack:

> formation -> grounded row -> LoRA write -> cold exact read works, while
> route/traversal remains an independent interface problem.

That is good diagnostic information per GPU-hour, especially because the code
is nearly complete. However SEQ-153 already demonstrated own-record cold recall
in another domain, so this run's incremental value is PCFL integration, not a
new headline claim. It should run opportunistically after the small gates above,
without delaying the higher-priority DEV repair that must establish a supplied-
memory route ceiling. It must not be described as evidence that the failed C0
benchmark has been repaired or that the full learning loop works.

## Launch decision in one line

**Do not launch from the reviewed tree yet.** Freeze/test the detached outer and
the outcome reducer first; then run once as an exploratory PCFL storage slice,
while interface-ceiling repair proceeds independently.
