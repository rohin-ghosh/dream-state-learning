# Astra handoff: `E0` addressed endogenous event-row gate

**Date:** 2026-09-13 UTC  
**Status:** docs-only, implementation-ready handoff, conditional on a fresh
independent audit validating Q0 attempt 2 as `EARLY_XOR_QUARTET_STOP_AUTH`.
No builder source, test, model, adapter, job, or GPU was changed or run for
this handoff.

## 1. Frozen scientific branch

Treat Q0 as a permanent clean failure of its registered direct-action writer:

```text
(opaque tool, mode) -> ACT
```

Do not tune Q0's rank, learning rate, dropout, dose, objective, quartet,
threshold, prompt, or seed. Do not run its confirmation roots or its
conditional endogenous-action relay. `E0` is a new, narrower module boundary:

```text
child precommits actions
  -> public outcomes
  -> child writes exact EVENT rows
  -> fixed replay writes those rows to a goal-blind LoRA memory
  -> sterile candidate-free READ returns raw EVENT rows or MISS
  -> a separate clean actor uses the raw rows for a later goal
```

A pass supports only one excluded-root own-experience-to-addressed-episodic-
memory relay. It is not Q0 recovery, policy learning, connection, traversal,
generalization, compression, retention, parenting, or lifetime improvement.

Primary design authority:
`research_notes/analysis/2026-09-13_post_q0_failure_endogenous_event_row_gate.md`.

## 2. Reuse from committed code

Use the current Q0 implementation as an engineering pattern, not as E0 input
and not as a scientific parent result.

From `gpu/astra_pairwise_q0.py`, port or call only these generic mechanisms:

- canonical JSON, SHA-256 inventories, write-once artifacts, immutable source
  snapshots, tensor-byte artifacts, `SEAL.json` / `FINALIZED.json`, and
  read-only exact reduction replay;
- clean local Qwen2.5-7B-Instruct verification, rank-8 all-layer LoRA
  construction, frozen-base checks, FP32 trainable checks, exact AdamW fields,
  deterministic eager/BF16 configuration, and fresh adapter reloads;
- `state_receipt`, RNG receipts, state-neutral diagnostics, FP64 dot/error
  bounds, and actual-update-versus-projected-gradient canary arithmetic;
- the **repaired decoder-level forward counter** (`qwen_forward_decoder` plus
  `native_forward_counter`), including a real CPU PEFT-wrapper regression;
- one controller, fresh isolated worker per stage, single-attempt receipts,
  owned-process-group cleanup, GPU-release verification, hard deadline, and
  nonreportable integrity aborts.

From `organism_v6/endogenous_action_relay.py`, reuse the pure-data style:

- immutable receipt / execution / authored-record dataclasses;
- exact chronology, raw-byte hash, authored-span, and evidence-join checks;
- formation-as-all-or-stop; and
- controls represented explicitly rather than inferred from filenames.

Do **not** reuse that module's `DREAM/WHEN/ACT` grammar, Q0 action surfaces,
mode swaps, natural `ACT: -` prefixes, or prepared relay. It is conditional on
a Q0 pass and therefore remains closed after the assumed Q0 rejection.

From `organism_v6/semantic_writer_diagnostic.py` and
`organism_v6/multikey_writer_gateway_simple.py`, reuse only their already
tested local tokenizer/model inventory and clean actor-loading helpers when
their current bytes are pinned. Do not consume historical adapters, roots,
reducers, held panels, or carrier claims.

Do not import Q0's top-level prepared material or closed lifecycle wholesale.
Its constants, archive pins, row schema, request denominators, labels, and
dynamic release table are Q0-specific. E0 must have its own source pins,
material, reducer, labels, and counters.

## 3. Minimal builder-owned additions

The smallest clean implementation is five files:

1. `organism_v6/endogenous_event_row_gate.py`  
   Pure CPU semantics: material schema, receipt chronology, strict precommit
   and `EVENT` parsing, formation admission, AUTH/SWAP corpus construction,
   zero-fit task construction, request inventories, scoring, failure-label
   precedence, and deterministic reducer. No Torch, model, tokenizer, or GPU.

2. `tests/test_endogenous_event_row_gate.py`  
   Synthetic-fixture attacks on every authorship, visibility, balance,
   denominator, control, and label boundary.

3. `gpu/astra_endogenous_event_row_e0.py`  
   Native tokenizer projection, child capture, clean-actor text closure,
   masked full-row causal-LM fit, first-update canary, candidate-free reads,
   clean-actor evaluation, stage controller, work accounting, sealing, and
   replay. Keep one native file so source pins and the serial lifecycle remain
   auditable.

4. `tests/test_astra_endogenous_event_row_e0.py`  
   CPU numerical/lifecycle/counter fixtures plus one real local Qwen2 + PEFT
   wrapper counter test. It must reproduce the attempt-1 accounting regression
   if the hook is moved from the decoder to the wrong wrapper.

5. `gpu/astra_endogenous_event_row_e0.sh`  
   Thin `set -euo pipefail` launcher that sets the repository path and invokes
   only the new module. It contains no scientific defaults not already bound
   in the prepared manifest.

No change to `gpu/astra_pairwise_q0.py`, Q0 tests, or Q0 evidence roots is
needed. If Astra wants shared helpers, copy the closed generic routines into
E0 first; refactoring Q0 onto a new helper in the same change is unnecessary
risk and would alter the already-audited implementation surface.

## 4. Material that must be frozen before model work

Allocate from one opaque DEV namespace, before semantic assignment:

- 8 scene IDs;
- 16 live event handles, exactly two per scene;
- 16 trained-negative handles for `MISS`;
- 16 evaluation-only negative handles, if unseen-absence is intended;
- a separate opaque decoy namespace and 16 decoy handles if `wrong-root` is
  retained;
- 2 legal action strings and 2 public outcome strings;
- 4 training request renderers and 1 held request renderer;
- 16 later questions: 8 scenes x 2 desired outcomes; and
- all item seeds, order, assignment, and target maps.

Verify with the pinned native tokenizer that action and outcome alternatives
have the intended equal token lengths and boundary behavior. Outcomes should
preferably differ at one registered token. If actions are multi-token, the
canary must use a predeclared sequence log-probability margin, not an
unspecified "field margin."

The child sees the two legal actions and must emit, before either outcome,
exactly two ordered strict `ACT` lines. The world executes those exact bytes.
After both public receipts, the child gets one call to emit exactly two rows:

```text
EVENT <handle> AT <scene> DID <action> GOT <outcome>
```

The checker may parse, join, and copy; it may not repair or generate any
semantic byte. Require 8/8 valid precommits and 16/16 supported rows or stop
before fitting as `E0_FORMATION_FAIL`. Preserve the weaker interpretation:
coverage was required by the harness; this does not show spontaneous
exploration.

`E_OUTCOME_SWAP` is made mechanically only after admission by swapping the two
outcome strings within each scene. It is never child-authored truth and can
never enter a lineage.

## 5. Training bytes and first-update gate

The model-visible memory API is exactly:

```text
READ EVENT <handle>
```

The target is exactly one complete `EVENT ...` row or `MISS`. The memory
process never sees a later goal, action menu, transcript, candidate row/bank,
fit label, scorer, or hidden map.

For each fitted arm, prepare:

- 16 admitted live events x 4 prospectively fixed request renderers = 64
  positive rows;
- 16 trained-negative handles x the same 4 renderers = 64 `MISS` rows;
- 32 presealed four-row optimizer units, replayed in exactly the same order
  four times;
- 128 optimizer updates, four separate natural-row forwards per update, hence
  512 training example/decoder forwards per fit; and
- two fits maximum: AUTH then OUTCOME_SWAP, for 256 updates and 1,024 training
  example/decoder forwards.

Use ordinary masked causal-LM loss only on target tokens. Freeze whether the
four row losses are averaged equally or all target tokens are averaged
globally; they are not identical objectives. Require AUTH and SWAP to have
identical input IDs, attention/position IDs, target lengths, row order,
initial tensors, optimizer state, and pre-forward dropout RNG. Only the
outcome target IDs may differ.

The first optimizer unit is frozen before child output and contains two scenes
x both actions, balanced in action and outcome under both arms. Before update
1, record teacher-forced target-versus-alternative action and outcome margins,
their gradients, and the FP64 projected directional change. Apply the actual
registered update, record the same surfaces, and require every signed observed
change and every signed projection to exceed its error bound. Replay the
canary from raw tensors.

Release table:

```text
AUTH canary miss -> one-step SWAP diagnostic -> terminal
AUTH pass        -> continue AUTH uninterrupted to update 128
                  -> fresh clean initialization, run SWAP
SWAP canary miss -> terminal
SWAP pass        -> continue SWAP uninterrupted to update 128 -> evaluate
```

Every canary miss has the primary label
`E0_ADDRESSED_ROW_FIRST_UPDATE_MISS`. The SWAP diagnostic can qualify but
cannot rescue AUTH. No retry or alternative recipe follows.

## 6. Recommended serial stage graph

Use fresh native workers and exact single-attempt receipts:

```text
00_CAPTURE_CHILD          clean base; 8 precommit + 8 record calls
01_TEXT_AND_TASK_CLOSURE  lossless rows + fresh clean actor; no fit
02_READ_OFF               fresh clean memory process, no adapter
03_FIT_E_AUTH             1 or 128 updates
04_FIT_E_OUTCOME_SWAP     mandatory 1-step diagnostic or full 128 updates
05_READ_E_AUTH            only if both fitted canaries pass
06_READ_E_OUTCOME_SWAP    only if both fitted canaries pass
07_READ_E_SHADOW          AUTH artifact exists, never mounted
08_ACTOR_PANEL            fresh clean base consumes only sealed raw returns
09_REDUCE_SEAL_REPLAY     CPU reduction, resource release, durable seal
```

Do not load a memory adapter and then "unload" it to create the clean actor.
The actor is a fresh base process after all memory returns are sealed. `OFF`
and `SHADOW` must use identical request bytes and deterministic item seeds;
their raw outputs must be byte-identical.

Stage 01 must close the assay before Stage 03: exact text returns 16/16 rows,
the clean actor solves at least 15/16 later questions, and scoring those same
actor outputs against the outcome-swapped map gives the registered opposite
action pattern. Model-free ID/order/length/renderer/target-marginal shortcuts
must be no better than 8/16 on the balanced panel. If a no-memory clean-actor
condition is also claimed as a model baseline, give it its own presealed 16
requests and denominator rather than calling a combinatorial shortcut a model
result.

## 7. Required work accounting

Keep request counts separate from decoder calls and token counts.

Prospective hard maxima from the design:

- source requests: 16 (8 precommit, 8 record);
- fits: 2;
- optimizer updates: 256;
- training example/decoder forwards: 1,024, because each four-row unit is
  deliberately four natural forwards before one backward/update;
- all short generation requests: fewer than 400;
- wall time: 90 minutes;
- GPU occupancy: one serial A40, at most 1.5 A40-hours.

The prepared manifest must additionally freeze exact denominators for every
memory-read, clean-actor, OFF, SHADOW, MISS, wrong-root, interface, and copy
panel. At reduction, count:

- natural teacher-forced forwards;
- decoder forward calls from the repaired decoder hook;
- generated token IDs;
- prompt tokens and target tokens;
- backward calls and optimizer steps;
- model loads, adapter loads, generation requests, and fit attempts; and
- per-stage wall time, cleanup, and final GPU release.

Do not copy Q0's forward-count formula. E0 has longer autoregressive rows and
separate source/actor stages. Derive a stage-specific formula from the frozen
request inventory and assert exact equality in native replay.

## 8. CPU acceptance suite before launch

Minimum tests, all with no CUDA visibility and offline mode:

1. Exact scene/action/outcome/handle balance and no identifier collision.
2. Precommit precedes outcomes; both outcomes precede EVENT rows.
3. Executed action bytes exactly equal committed child bytes.
4. EVENT parser rejects missing, extra, reordered, duplicate, cross-scene,
   wrong-handle, repaired, paraphrased, unsupported, or trailing text.
5. Any one malformed source row produces formation failure and zero fits.
6. AUTH/SWAP differ only in outcome targets and preserve every marginal,
   length, order, RNG, and input byte.
7. Positive and MISS rows are 64/64; units are 32 x 4 and schedule replays
   exactly four times.
8. Full target loss mask and shift are exact; prompt tokens have label -100.
9. First-update toy model passes only when both action and outcome directions
   move correctly; zero/equality/nextafter/nonfinite/error-bound cases stop.
10. AUTH miss runs exactly one SWAP update and no reads; SWAP miss stops all
    efficacy evaluation; no third fit exists.
11. Candidate strings/IDs, goal, answer, hidden map, admission bit, and source
    chronology cannot reach a memory request or target beyond the exact row.
12. Text closure and shortcut thresholds have exact integer denominators.
13. OFF/SHADOW projections and deterministic raw outputs are byte-identical;
    wrong mount, warm cache, reused process, or adapter residue aborts.
14. Exact read, held-renderer read, outcome redirection, MISS, wrong-root,
    copy/interface, neutral behavior, and actor-use thresholds all exercise
    boundary/nextafter cases and cannot average across failure stages.
15. Missing/duplicate/extra requests, selected checkpoint, retry, source drift,
    counter mismatch, deadline overrun, teardown failure, or seal drift yields
    `NONREPORTABLE_*`, not a scientific null.
16. Read-only replay reconstructs the exact report from raw events and rejects
    any tensor, adapter, receipt, log, request, resource, or inventory change.
17. Real local CPU Qwen2 and PEFT wrapper both increment the same decoder hook;
    hooking only `get_base_model()` reproduces the historical zero-count defect
    and fails the regression.

Run the new two suites plus the full currently pinned Q0/native regression
suite. The E0 manifest binds the complete successful Linux receipt and all
source hashes.

## 9. Acceptance and label precedence

After resolving the denominator ambiguities below, implement the fixed gates
from the primary memo without tuning:

- per fitted arm: exact complete-row correctness >=29/32, held-renderer
  correctness >=14/16, validity >=31/32 and >=15/16, and each semantic class
  >=7/8 held recall;
- SWAP: >=14/16 swapped outcomes and >=13/16 handles correct under both arms
  with opposite outcome fields; AUTH minus OFF semantic correctness >=.20;
- clean actor: AUTH and SWAP each >=14/16 under their own map, >=7/8 per
  action, >=13/16 action flips, symmetric redirection `B >= .40`, and AUTH
  minus OFF authentic action balanced accuracy >=.20;
- absence/scope: exact `MISS >=30/32`, no false row used by actor, native
  copy/interface 8/8, neutral-surface difference from OFF <=.05; and
- reset: OFF and unmounted SHADOW byte-identical under deterministic seeds.

Precedence is integrity -> formation -> assay validity -> first update -> row
storage -> held extractability -> causal outcome binding -> clean-actor use ->
absence/interface/reset -> full DEV pass. Preserve distinct labels:

```text
E0_FORMATION_FAIL
E0_ASSAY_INVALID
E0_ADDRESSED_ROW_FIRST_UPDATE_MISS
E0_ROW_NOT_STORED
E0_STORED_NOT_EXTRACTABLE
E0_OUTCOME_BINDING_NOT_CAUSAL
E0_ROW_NOT_BEHAVIORALLY_USABLE
E0_FALSE_MEMORY_OR_INTERFACE_FAILURE
DEV_ENDOGENOUS_ADDRESSED_EVENT_MEMORY_PASS
```

Integrity and lifecycle failures remain `NONREPORTABLE_PRECHECK_ABORT` or
`NONREPORTABLE_RUNTIME_ABORT` and outrank all labels above.

## 10. Ambiguities Astra must resolve prospectively

These are launch-blocking specification holes, not invitations to tune after a
result:

1. **The `29/32` exact denominator is undefined.** There are 16 live event
   handles. State whether 32 means two exact request renderers per handle, or
   some other presealed inventory. Do not invent it in the reducer.
2. **"Held query" is undefined.** Freeze one held request renderer (or an
   explicit set), disjoint from the four training renderers. This tests prompt
   extractability, not unseen-event generalization.
3. **Negative-address naming is contradictory.** The 16 handles trained to
   return `MISS` are not unseen held handles. Either score them as trained
   negatives and add 16 evaluation-only negatives, or remove the word held.
4. **Wrong-root cannot arise from an unspecified second root.** Add a
   preallocated payload-free decoy namespace/handle roster, or delete the
   wrong-root gate. It must not import a historical root or donor semantics.
5. **Four training views versus one exact API.** Define the four fixed user
   request renderers and prove that only renderer bytes differ. The deployment
   API can remain canonical `READ EVENT <handle>`.
6. **Canary field arithmetic is incomplete.** Freeze action alternatives as
   one-token choices or define sequence-level teacher-forced log-probability
   margins, their normalization, and their FP64 bounds. Outcome margins are
   simpler but still need exact target positions.
7. **Loss normalization is unspecified.** Freeze row-mean versus token-mean
   before data capture.
8. **Actor prompts and seeds are unspecified.** Freeze the exact later-goal
   prompt, strict action grammar, max tokens, deterministic seeds, parser, and
   whether AUTH/SWAP cross-map contrasts rescore fixed outputs or regenerate.
9. **`no false row is used by the actor` lacks an actor output contract.** Add
   a strict abstention/no-action behavior for absence probes, or make this a
   memory-only false-row gate and remove the actor clause.
10. **OFF semantic/action denominators are unspecified.** Freeze which OFF
    raw returns reach the actor and how malformed/MISS outputs score.
11. **Copy/interface and neutral-surface panels are inherited only by name.**
    Build new E0-native prompts and counts; do not silently reuse Q0 held data.
12. **The 90-minute budget needs a prospective stage allocation.** Full-row
    generation and fresh model reloads differ from Q0. Give each worker a hard
    subdeadline and preserve a cleanup reserve.

None changes the scientific idea. Once these bytes and denominators are
frozen, Astra can implement and CPU-red-team the gate without further Q0 work.

## 11. Build order and stopping rule

1. Freeze the twelve items above in one machine-readable protocol manifest.
2. Implement the pure CPU module and adversarial fixture tests.
3. Implement tokenizer projection and source/target leakage audit.
4. Implement text/actor closure and run it before fitting in the lifecycle.
5. Port native writer/counter/canary/custody machinery; add real-wrapper tests.
6. Run the complete offline CPU suite and record a source-bound receipt.
7. Launch one fresh excluded E0 DEV root only.
8. Seal, replay, release the GPU, and obtain a fresh independent terminal
   audit before interpreting the result.

If E0 fails formation, text closure, first update, atomic storage,
extractability, causal redirection, clean-actor use, or absence/interface,
stop at that named layer. Do not compensate with connected M, lifetime L,
parenting, rank/heat sweeps, or a weaker threshold.

