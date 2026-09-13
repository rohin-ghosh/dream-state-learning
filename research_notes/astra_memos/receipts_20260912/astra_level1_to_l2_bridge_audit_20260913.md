# Level1 → raw child record → L2 bridge: bounded source audit

2026-09-13, source inspection completed around 07:50 UTC. Read-only analysis;
this file is the only write. No model, tokenizer, native/GPU, network, test,
or repository-changing command was run. No held-out result, runtime capture,
adapter, live-root artifact, or private world instance was read. Source code
describing evaluators was inspected, not their results. Existing skill files
remain at EDITSTOP; this audit does not block Main's launches.

## Bottom line

There is an existing genuine public-experience compiler, but **none of the
four current prediction/goal/discrimination JSON outputs is its training
target format**. The smallest existing compiler unit is one eight-slot block,
not one JSON fixture. A child must actually execute a legal action, receive
real environment feedback, and then emit its own supported action-name record.
Admission copies that entire child record unchanged into the training target.

Recommended diagnostic: one fresh eight-slot public-world block → measure
raw-record formation/admission → one cold-base write if any records qualify →
fresh-process reload and same-experience public readback against base. Do not
require all four Level1 skills, invent a JSON-to-action answer converter, or
claim a closed learning loop. A new bounded driver/initial Level1 adapter
binding would be needed; the current runtime is a fixed two-cycle program,
not a ready-made one-cycle Level1 bridge CLI. No implementation is made here.

## Steer recovered, not inferred

Read `research_notes/THESIS_RAW_ROHIN_2026-09-11.md:343` (raw35, ~07:25 UTC):
start with an appropriately simple Level2 loop for a weak Level1, and use the
interaction to learn what Level1 needs. Its supplied context explicitly names
permissive parsing followed by separate format/content scoring among the five
approved suggestions. This does not authorize hot-changing existing runs.

Read the full raw36 at `research_notes/THESIS_RAW_ROHIN_2026-09-11.md:349`
(~07:35 UTC). The overnight heuristic is **raw experiential data containing
what training needs**, not a working closed loop, recursive success, or
self-recursive success. The natural first endpoint is authentic, supported,
write-ready child records. Actual write/reload is the next diagnostic endpoint,
not a prerequisite for calling the raw-data formation observation useful.

## Existing public-record path: exact code entry points

Paths below are repository-relative unless explicitly `/tmp`.

| Step | Existing function / start line | What the code actually does |
| --- | --- | --- |
| World | `organism_v6/l2_public_record_dev.py:239` `build_world` | Defines 16 unique slots in two fixed blocks of eight and exactly two legal action-name strings. |
| Visibility | `organism_v6/l2_public_record_dev.py:256` `public_view` | Exposes root/actions/slots/public law; private success mapping is not an argument to the compiler. |
| Act prompt | `organism_v6/l2_public_record_dev.py:271` `action_prompt` | Asks for the successful listed action for a key, one action name only. Wake and train requests have the same wording; readout paraphrases the question. |
| Raw syntax | `organism_v6/l2_public_record_dev.py:280` `_action` | Accepts exactly one of the two ASCII action names, optionally followed by ONE newline. Not JSON, fences, spaces, PREDICT, TRY, or DONE. |
| Receipts | `organism_v6/l2_public_record_dev.py:316` `make_receipt` | Binds exact bytes, slot/root/lineage, chronology and predecessor hash. Hashes alone do not authenticate a native child or environment. |
| Outcome | `organism_v6/l2_public_record_dev.py:327` `feedback` | Executes the committed legal choice against the world's success mapping and emits linked `SUCCESS`/`FAILURE` bytes. |
| Record request | `organism_v6/l2_public_record_dev.py:339` `process_prompt` | Adds executed action and public outcome to the public action prompt; asks the child which action should succeed under the public law. |
| Admission | `organism_v6/l2_public_record_dev.py:347` `_episode` | Validates links/syntax and checks the child's record against observed evidence; returns a TrainingRow or a named refusal. |
| Block | `organism_v6/l2_public_record_dev.py:398` `capture_block` | Validates exactly eight episodes in the prescribed block/slot order. |
| Compile | `organism_v6/l2_public_record_dev.py:405` `compile_corpus` | Consumes one or two cumulative blocks plus externally retained capture hashes; preserves admitted child bytes and all rejection reasons. |
| Export | `organism_v6/l2_public_record_dev.py:451` `training_items` | Revalidates corpus against captures; masks public prompt context and supervises the exact child action record. |
| State | `organism_v6/l2_public_record_dev.py:513` `close_block`; `:525` `complete_sleep`; `:544` `routing` | Compiles cumulative experience and requests an artifact route. `routing` explicitly returns `native_verified=False`. |
| Native capture | `gpu/astra_l2_public_record_dev.py:619` `capture_stage` | Saves request/response bytes and native-token metadata, creates action/outcome/record receipts, and closes each backend. |
| Native encoding | `gpu/astra_l2_public_record_dev.py:429` `encode_training` | Verifies full target bytes, tokenizer boundary, target+EOS supervision, context/padding masks, no dropped/split/truncated tokens and no packing. |
| Actual write | `gpu/astra_l2_public_record_dev.py:528` `fit_stage` | Returns formation shortage on empty corpus; otherwise cold-loads frozen base and fresh optimizer, calls V3 training, checks LoRA-only finite trainables, manifest, adapter files and hash. |
| Trainer | `organism_v6/train_adapter_v3.py:657` `run_training` | Existing writer called by the runtime, not by this audit. |
| Candidate route | `gpu/astra_l2_public_record_dev.py:405` `route_for` | Resolves prior candidate hash to saved adapter bytes; SHADOW/base has no candidate route. |
| Native reload | `gpu/astra_l2_public_record_dev.py:576` `Native.__init__`; `:587` `Native.generate` | Creates a fresh vLLM instance, constructs `LoRARequest` for the route, and passes it explicitly into generation. |

The relevant invariant is deliberately narrow: public law at
`organism_v6/l2_public_record_dev.py:17` says exactly ONE of TWO actions always
succeeds for each key. Therefore SUCCESS supports repeating the selected
action and FAILURE supports the other listed action. The compiler checks that
the CHILD already emitted the supported action. It does not write that answer
for the child. The law does not hold for arbitrary rulegame triples and cannot
be silently transplanted there.

## What authentic raw experience must contain

The record is a linked evidence bundle, not just an answer string:

1. **Public task identity:** root, slot, key, the two legal actions and the
   stated deterministic public law. A caller must retain the actual prompt
   and source/model/tokenizer bindings. The compiler does not consume a
   `build_dataset` authored row or its claimed source proof.
2. **Child action BEFORE feedback:** native raw UTF-8/ASCII bytes identifying
   a legal action; native request, output token IDs and finish reason retained.
   Receipt fields are `root_id`, `slot_id`, `lineage`, `kind`, `sequence`,
   `raw`, `previous_sha256`, `sha256` (`Receipt`, core `:80`).
3. **Actual environment outcome:** raw `SUCCESS` or `FAILURE`, linked to that
   action, not copied from an authored target or manufactured by the child.
   `feedback` owns private-world access; the public compiler needs no hidden
   mapping, truth seed, future answer or held-out score.
4. **Child post-outcome record:** a SECOND actual child generation in response
   to `process_prompt`, containing only the chosen successful action-name bytes
   (optional terminal newline). It must link to the outcome and come later in
   the same slot/lineage. The key and provenance reside in its envelope, not in
   record text. An unsuccessful action can produce useful experience if the
   child itself records the supported alternative.
5. **Externally pinned block/call evidence:** retain the raw calls and their
   identity/chronology outside the compiler, plus the eight-slot CapturedBlock
   hash. Core checks reject crossed roots/slots/lineages, bad phase order,
   altered hashes and corpus drift, but cannot prove the bytes came from a
   model rather than a host author. Runtime authenticity is a distinct fact.

`_episode` has named refusals: `INVALID_ACTION`, `MISSING_OUTCOME`,
`MISSING_RECORD`, `INVALID_RECORD_ACTION`, `UNSUPPORTED_RECORD`. Structural
integrity problems raise, rather than becoming a useful training row. A
wrong-but-legal child record is rejected, not repaired. `TrainingRow.target`
is `record.raw`; source slot, episode hash and record hash accompany it
(`organism_v6/l2_public_record_dev.py:107` and `:370`).

The export deliberately constructs a source-withdrawn public key query as
masked context; feedback and `PROCESS_TAPE` are not in the sleep query. This
is deterministic context projection, not teacher answer rewriting. The
supervised target bytes must remain the original child record. Native EOS is
added and audited as a serialization boundary, not an invented answer.

## Level1 outputs: exactly what does NOT connect

| Level1 screen / implementation | Raw output contract | Missing connection |
| --- | --- | --- |
| Prediction: `/tmp/astra_level1_prediction_goal_material_20260913.py:63` `_expected`, `:85` `_render` | `decision`, `prediction` (Boolean/null), `reason`; labels predict/abstain and public_evidence/insufficient_evidence | No emitted executable action or triple; no actual result; no supported post-outcome action-name record; no root/slot/native chronology. A prospective Boolean is NOT an observed result. |
| Goal completion: same file `:63`, `:85` | `decision` complete/continue; `goal_complete` Boolean | Does not emit a continuation action, legal action name, native DONE, source record, or reusable outcome. A complete judgment is not itself successful execution. |
| Contradiction: `/tmp/astra_level1_discrimination_material_20260913.py:37` instructions, `:147` `expected` | `event_id`, `verdict` agree/disagree/insufficient, `reason` | Classifies supplied prior prediction versus supplied result. Does not reproduce the actual action, outcome or complete observation record; agreement alone supplies no actionable target. |
| Update judgment: same file `:47`, `:147` | `event_id`, `decision` admit/reject/abstain, `reason` | Judges an AUTHOR-SUPPLIED candidate record. Its word “admit” is not compiler authority, and its output does not contain that record. Copying the candidate from its prompt into a child target would be teacher rewriting. |

Prediction/goal source facts are authored public belief-card/state exercises.
Discrimination explicitly describes itself as AUTHOR-SCREEN, not production
admission. Its candidate has `try/observed/predicted/relation`, and
`assess` (`discrimination :120`) checks the selected supplied event, not a
native runtime execution. Authored source IDs/hashes certify fixture lineage,
not real child experience. Model outputs from these fixtures remain responses
to authored situations even if their scores improve.

Passing typed-content scorers (`prediction/goal :278`; discrimination `:297`)
does not make their JSON acceptable to `_action`. In particular:

- JSON fences accepted by future-Level1 content scoring are NOT accepted by
  the action-name compiler. Do not strip a fence or extract a Boolean and
  silently manufacture `move_*` bytes as its target.
- `abstain`, `continue`, `admit`, and `complete` have no action-name spelling
  in this public L2 grammar. Preserve their raw sidecar evidence as diagnostic
  outputs; they cannot enter this writer unchanged as supported action targets.
- Predictions may be informative sidecars, but neither this compiler nor its
  `Receipt.kind` enumeration has a prediction phase. No prior prediction is
  required by this minimal action-record compiler.

## Nearby rulegame compiler: useful, but a DIFFERENT bridge

`organism_v6/rulegame_parenting_diagnostic.py:83` declares the native record:
`{"try":[x,y,z],"observed":true,"predicted":false,"relation":"mismatched"}`
(illustrative syntax only, not a captured record).

- `parse_action` at `:257` recognizes an actual `ACT: TRY x,y,z`, an optional
  prior `PREDICT: T/F`, and detects ambiguous predictions. No prediction is
  allowed and must remain null; it must not be backfilled after observation.
- `record_prompt` at `:106` includes the actual emitted action and actual
  world response, plus public observed fields. This is a child record request,
  not permission for the host to populate its target.
- `judge_record` at `:300` demands exactly `try/observed/predicted/relation`,
  exact action identity, typed Boolean outcome, faithful prior prediction and
  correct matched/mismatched/unavailable relation. It parses JSON whitespace
  and key order but does not unwrap Markdown fences. It cannot accept current
  discrimination/goal/prediction JSON directly either.
- `organism_v6/rulegame_record_material.py:97` `build_record_pair` replays a
  formation capture, requires Main's already-bound fixed selection and
  `record_review`, and joins actual wake/record calls by execution identity.
  At `:169` it reads the native raw child record; at `:172` it checks the
  actual record-request prompt with **no synthetic fallback**.
- Its `_encode` at `:58` supervises `own_raw_record` plus native EOS under the
  actual record-request context (including visible outcome). It checks no
  dropping/splitting/truncation. This trains faithful observation recording,
  **not** the two-action compiler's source-withdrawn successful-action query.

This path is closer to the Level1 discrimination vocabulary, but a child must
still emit a full actual record. Do not convert a judgment into one. It also
requires paired formation/audit infrastructure and is not the smallest
already-existing one-block write/readback diagnostic. Its Main review is an
existing export prerequisite, not a new formal review framework proposed here.

## Smallest proposed diagnostic, with honest implementation boundaries

**A. Raw36 formation endpoint (do this first, no success guarantee).**
In a fresh future diagnostic, bind one named frozen child adapter and base
identity. Use the existing public two-action world, one complete block of
eight slots. For each slot capture child action → actual `feedback` → child
`process_prompt` response. Do not insert any of the authored datasets, their
targets, candidate records, output labels or held-out situations. Do not force
an oracle answer, regenerate until correct, or rewrite failed child responses.

Compile the pinned block once. Report total eight slots, legal actions,
observed outcomes, complete child records, exact-grammar records, supported
admitted records, and every refusal. Retain success-versus-failure branches
even if the child happens to produce an imbalanced block. Nonempty supported
admission means some genuine raw experience contains a reusable target; it
does not mean the child improved. Empty corpus is an honest formation shortage,
not permission to fill with synthetic rows or replay another block to tune it.

**B. Write endpoint.**
If there is admissible material, use `training_items` / `encode_training`
without target alteration and perform one `fit_stage`-style cold-base write.
Existing eight-row batch mechanics allow fewer than eight admitted rows; the
eight-slot CAPTURE is mandatory, not eight positive labels. Retain corpus,
record/target hashes, complete token/mask audit, train manifest and adapter
hash. Existing native encoding adds EOS with target-only loss and no actual
truncation. A returned state flag is not evidence that the write occurred.

**C. Reload/readback endpoint.**
Dispose of the writing model/process; load a fresh inference instance with the
saved artifact via explicit `LoRARequest`, verifying the candidate file hash
before and after. Retain actual raw request/response/token/route records.
Compare to base/SHADOW on the SAME experienced keys, querying only key + public
law/action vocabulary, without outcome, child record or process tape. Score
only against the archived public feedback-supported action for experienced
slots, so no held-out result or private success table needs to be read. Label
this **same-experience access/readback**, not transfer or a new task success.
Readback can fail despite a verified write/reload; report the split endpoints.

Keep a base readback/control if discussing changed behavior. Report admitted
and nonadmitted experienced slots separately; admission-conditioned accuracy
is a selected subset, not full-block competence. `misbind_corpus` at core
`:445` exists for later attribution controls, but would add a write arm and
must disclose `changed_targets`/`no_op`; it is not required to establish the
minimal raw-data endpoint. No result claim is made by this source audit.

### What is NOT already plug-and-play

1. **Initial Level1 adapter route:** `start_pair` (core `:463`) starts at base.
   Runtime `route_for` (`:405`) recognizes base or previous L2 fit candidates,
   not an external Level1 birth adapter; `validate_spec` (`:216`) has a closed
   field inventory. Existing `wake1` would therefore be base, not the current
   Level1 child. A separately bound future collector route is needed; do not
   mislabel a base capture as an L1-adapter capture.
2. **Cold write versus continued adult:** `fit_stage` (`:550`) explicitly
   cold-loads base with fresh optimizer and rejects an already attached PEFT
   configuration. It does not continue the Level1 adapter. The minimal proposal
   is an L1-child-data → cold-write/access diagnostic, NOT preservation of the
   parent's or adult's full learned dispositions. Continuing/combining adapters
   is a separate design choice, not a filename swap.
3. **Bounded run length:** `STAGES` (`gpu/astra_l2_public_record_dev.py:29`)
   includes baseline, two wake blocks, three fits, and paired reports.
   `execute_loop` (`:752`) traverses it except formation shortage; it has no
   one-cycle-prefix option. The proposed driver must explicitly bound capture,
   one write and readback rather than silently running the full existing CLI.
4. **Finish reason admission gap:** `validate_response` (`runtime :606`)
   permits `stop` OR `length`; `capture_stage.generate` (`:630`) returns only
   raw bytes to core, whose Receipt has no finish field. An exact action string
   with `finish_reason="length"` could pass current core grammar. Future
   diagnostic accounting should require stop-completed action and record calls,
   retaining original response evidence. This is a small runtime admission
   distinction to implement explicitly, not a hot edit or byte repair. Do not
   silently feed a length-terminated admitted target into the proposed write.
5. **Recipe provenance:** current runtime `RECIPE` (`:40`) is rank8,
   lr3e-5 default, 20 epochs, batch8, no packing, 1024 token bound;
   `encode_training` (`:494`) computes `20 * ceil(admitted/8)` steps. Optional
   learner seed/LR are validated. This is not fresh320, SEQ113 warm80+320 mixed
   replay, or a demonstrated optimal recipe. Raw36 formation can be assessed
   before choosing or tuning any new write recipe.

The small future wiring changes above are proposals only. No C11 machinery,
new architecture framework, watcher pause, live migration, native execution,
or implementation is part of this task.

## Claim ladder for Main's report

1. Authored Level1 screen content/format: policy-fixture behavior only.
2. Actual child/environment capture: real experience exists.
3. Supported exact child record admitted: raw36 possible-success heuristic.
4. Native write/token masks verified: that experience was actually trained.
5. Fresh-process saved-artifact readback: access measured; improvement must be
   shown against base/control, not inferred from mounting an adapter.
6. None of 1–5 alone establishes recursive/self-recursive learning, improved
   adult internalization, parenting, H1/H2/P1 qualification or held-out transfer.

## Source snapshot pins (not runtime/result evidence)

- `organism_v6/l2_public_record_dev.py`:
  `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352`
- `gpu/astra_l2_public_record_dev.py`:
  `dce8cd88b82bd51ec4f12e482ce70dc220453cb85dcaeb758206c7b5200a4277`
- `organism_v6/rulegame_record_material.py`:
  `7eb7bbd04068a34be4932f11a0eab0109ddabcceb03210a07b657d57a0c621c1`
- `organism_v6/rulegame_parenting_diagnostic.py`:
  `e6055da48b2c6fa1bd294c9d991e07f32f05dc6630fe8973373977bdfe977526`
- `/tmp/astra_level1_discrimination_material_20260913.py`:
  `cfc2839f11e710b9de513efc465e3d2b895cfd067d7c8146bba97121bf4ad2fb`
- `/tmp/astra_level1_prediction_goal_material_20260913.py`:
  `3da282322f65525271a48b628b30ecdc8a2fba6ba6ba84d8cf1f3e65ad6d6433`

These are observed source hashes in a concurrently edited workspace, not a
lock or rollback instruction. Rebind any future implementation to its own
final source snapshot. Repetition/meta material, tests and handoff were also
rehashed and remain exactly at their prior EDITSTOP hashes.

EDITSTOP: only `/tmp/astra_level1_to_l2_bridge_audit_20260913.md` created.
