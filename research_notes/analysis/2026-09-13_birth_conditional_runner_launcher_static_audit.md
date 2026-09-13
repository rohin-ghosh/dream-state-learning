# Static audit: live authored-BIRTH runner and launcher (pre-collection)

Date: 2026-09-13 UTC  
Scope: runner `072a1333...`, launcher `c4246f29...`, corpus
`43bf0749...`, preparation record for plan `77687114...`. I did not read any
fit loss, generated response, score, terminal result, or other outcome from the
live run.

## Verdict

**No static bug was found that would mix the three readout identities, drop a
denominator, expose an answer to the model, alter the audited target mask/dose,
or accept an incompletely released run. Subject to successful frozen fit and
readout collection, this run is valid to interpret as an exploratory direct
authored-BIRTH component.**

That interpretation is narrow: a fresh rank-8 LoRA was taught a supplied
input-conditional response policy and is tested for that policy on held
instances/templates plus two simple output-interface anchors. It is not own
experience, parenting, learning-to-learn, a clean lineage, Level 1, or evidence
that the child subsequently learns a new task faster. Because it is the
quarantined pre-Q0 run, neither its adapter nor its observed outcomes should
seed or tune the claim-bearing Q0/Level-2 path.

## Checks that close correctly

- **Arm/base identity.** Fit order is AUTH then DERANGED, in separate workers.
  Each worker calls `load_native` on the pinned base and rejects a base already
  carrying PEFT state. No warm start is accepted. Readout order is OFF, AUTH,
  DERANGED, again one fresh worker/backend each. OFF must have no adapter;
  AUTH and DERANGED are routed only to their corresponding fit receipt. Model
  and full adapter-tree hashes are rechecked before capture, and the raw call
  identity contains the adapter config/weight hash.
- **Matched intervention and dose.** Both arms have the same 256 contexts and
  32 closed eight-row optimizer groups. Within every group, the conditional
  target sequences, including EOS, are swapped while the four arithmetic/copy
  targets remain byte-identical. Both use seed 0, rank 8/alpha 16/dropout .05,
  LR `1e-4`, batch 8, four epochs, exactly 128 updates, no packing, and a fresh
  optimizer. The native audit records 18,352 unpadded input tokens and 2,912
  supervised tokens per epoch in each arm; worker-side re-encoding must equal
  every saved input ID and label before training starts.
- **Mask and tokenizer parity.** Training loss is only on the target plus one
  EOS; context and padding are `-100`, and any truncation, split, skip, dropped
  token, loss-bearing padding, or changed EOS boundary fails. Readout
  prompts are independently rendered/tokenized in preparation and must equal
  the actual vLLM rendered prompt and prompt-token IDs for every call.
- **No answer/hidden-metadata path.** `fixed_requests` sends only each case's
  `context`. Expected fields, target text, factor bits, source-event IDs and
  candidate objects stay outside model input. The visible case name is crossed
  with all necessary factors; omission lookup includes visible instance,
  template and action ordering and remains at most `.50` when any required
  factor is removed. Train/dev IDs, contexts and template families are
  disjoint. This is held rendering/instance transfer within the same supplied
  rule, not a new-rule test.
- **Full panel and scoring.** All cells receive the same 128 requests:
  32 PROSPECT, 64 REVISE, 16 ADDITION and 16 COPY; total 384 greedy calls at
  seed 20260912 and at most 64 output tokens. Exact request/response file pairs
  and usage must exist before any scorer runs. Output dictionaries must contain
  exactly all 128 case IDs; malformed, verbose, truncated or missing-format
  generations remain in the denominator. OFF is scored against AUTH truth;
  AUTH against AUTH; DERANGED against its complementary assigned map. AUTH
  semantics are also retained separately. Registered operation, anchor and
  factor-twin counts use the correct complete denominators.
- **Teardown and no favorable partial.** Each worker is a distinct process
  group/session with a parent-death watchdog. The supervisor requires worker
  return 0, empty owned process group, no GPU process and verified reservation
  release before starting the next member. A result exists only after the
  all-member barrier; failure produces a partial record with no aggregate and
  no automatic retry. Collection repeats process/session and GPU-vacancy
  checks, source/input pins, raw-call custody, reducer replay and archive
  verification before release.

## Limitations / repairs for the claim-bearing successor

These do not silently turn the current exploratory result into a false
positive, but they matter before paper-grade reuse.

1. **The capsule deliberately excludes LoRA weight bytes.** It preserves their
   hashes and the complete corpus/recipe/raw calls, so the direct readout can be
   audited, but it cannot independently reload the exact learned state after
   the node root disappears. Preserve both adapter directories under a
   separately hashed custody artifact before deleting the node or using either
   adapter downstream.
2. **The source pin set is not transitively closed.** For example,
   `fundamental_teaching_readout.py` is pinned but imports the unlisted
   `fundamental_teaching_corpus.py`; `reasoning_neutral_probe.py` also imports
   additional modules not all named in `source_pins`. The currently reviewed
   bytes expose no output path from those modules, and direct executed helpers
   are pinned, but the archive is not a cryptographic seal of every imported
   Python byte. A paper-grade successor should hash the complete imported
   source closure (or the immutable source-tree capsule), not a hand-maintained
   list.
3. **There is no exact-training-form readout.** A positive held result remains
   meaningful for this component; a negative result cannot distinguish
   failure to acquire the authored policy from failure to extract it on held
   templates. The already proposed 16 PROSPECT + 32 REVISE exact-source forms
   per cell would make that diagnosis, but should not be retrofitted after any
   terminal was inspected.
4. **Origin remains unresolved local hashes.** The runner binds one unchanged
   local base exactly, but does not authenticate its public checkpoint origin.
   The claim boundary already says this.
5. **Collection's vacancy helper is whole-node conservative.** An unrelated
   queued/running job on another GPU can make collection fail closed. That can
   lose a release, but cannot manufacture a successful result. Keep the node
   queue quiet through each collection.

## Promotion rule

Interpret only a fully released fit plus fully released three-cell readout.
Report all raw counts, AUTH semantics and assigned-map counts. A positive
direct component requires both complementary trained arms to follow their own
maps on held forms while the fixed arithmetic/copy interfaces remain intact;
AUTH alone is steerability, not selectivity. Even a full component pass remains
an installed authored routine. Improved learning is a separate, post-Q0,
post-birth causal test with fresh mappings and PROMOTE versus SHADOW.
