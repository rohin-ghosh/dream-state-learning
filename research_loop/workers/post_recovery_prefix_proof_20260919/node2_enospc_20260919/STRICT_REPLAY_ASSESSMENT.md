# Node2 strict deterministic replay assessment — 2026-09-19 UTC

## Verdict and scope

**HOLD for a strict hidden-state-continuity claim; conditional reconstruction is
not ruled out.** Restoring a prior COMPLETE and replaying every intervening
generation and training update is materially different from discarding new
rows. It can preserve all durable authentic child data. The existing receipts,
however, do not independently establish that reconstructed optimizer/RNG/model
state equals the lost resident state. That requires a demonstrated deterministic
execution contract covering the original runtime, not merely matching tokens
and scalar losses. This assessment neither implements nor authorizes recovery.

Selected on-node receipt verification completed at **2026-09-19 03:58:02 UTC**,
against the historical cutoffs below. No source/model execution, tensor loading,
node writes, signals, launches, journal repair, or deadline changes occurred.
No journal bodies or checkpoints were copied to the VM. Full journal and
checkpoint-binary verification remain outstanding.

## Direct evidence

| Life | Prior COMPLETE / LEARN | Checkpoint step | Pending sleep | Verified UPDATE receipts | Last committed step |
| --- | --- | --- | --- | --- | --- |
| C0 | 6631 / 6632, cycle 145 | 8412 | 6660, cycle 146; rows 444 / frontier 441 | 6663–6710, 48 receipts | 8460 |
| Astra7 | 7750 / 7751, cycle 146 | 9644 | 7776, cycle 147; rows 453 / frontier 450 | 7779–7807, 29 receipts | 9673 |

Each has **three durable pending authentic rows**, not an empty wake interval.
Saved pending-state digests and selected COMPLETE/COMMIT document bindings were
verified in `BOUNDARIES_VERIFIED_20260919.json`; full tensor contents were not.

`REPLAY_WITNESSES_20260919.json` verifies canonical record hashes and exact intent
bindings for all 77 UPDATEs, six REQUESTs, six RESPONSEs, and selected sleep
recipe/eligibility records. Historical tail headers were rechecked against the
earlier receipt; this is **not** a full raw-tail state-machine audit. No
GENERATION_PARTIAL/GENERATION_ABORTED appears in those bounded tail headers.
That observation does not prove the absence of every unjournaled RNG consumer.

- C0: REQUEST→RESPONSE 6637→6638, 6644→6645, 6653→6654;
  returned token counts 74, 170, 68. Its tail also contains INBOX and COMPACTION.
- Astra7: 7753→7754, 7760→7761, 7769→7770; 29 tokens each.
- All six response payloads have exactly `adapter_state_sha256`,
  `base_sha256`, `decoder`, `prompt_token_ids_sha256`, `prompt_tokens`, `raw`,
  `terminal`, `token_ids`, and `truncated`. **No pre/post-generation RNG state,
  RNG hash, counter, or randomness transcript is present.** Requests retain
  exact messages/max-new-token budget/wall/model-state bindings and explicitly
  set `retry_allowed=false`. Offline verification replay would require a
  separately admitted exception, not reuse of the ordinary request retry path.
- Every verified UPDATE document has exactly `finished_unix`, `losses`,
  `optimizer_step`, `source_sha256`. Each of its five loss entries has `kind`,
  `mean_loss`, `objective_weight`, `target_tokens`.
- **UPDATE has no adapter, gradient, optimizer, or RNG state hash.**
  `source_sha256` binds the training row; record/intent hashes authenticate the
  receipt, not the post-update model. `losses_sha256` in this new diagnostic
  receipt is our digest of the original scalar-loss list, not a historical
  hidden-state commitment.

## Exact source locations

Paths in this section refer to each life’s preserved, guard-pinned
`source_r233_lease_continuation`, not the mutable repository checkout.

- `gpu/orch_r125_continual_native.py:355`: loads optimizer plus Python, CPU,
  and all CUDA RNG states, checks parameter order and restored adapter hash.
  `:439` writes adapter then optimizer/RNG and only afterward COMMIT (`:462`).
- `gpu/orch_r125_continual_native.py:470`: exact generation path;
  `:480` sampling configuration; `:497` returned receipt fields.
- `organism_v6/orch_r125_continual_stream.py:214`: request construction;
  `:229` REQUEST before generation; `:234` RESPONSE wrapper adds no RNG state;
  `:249` preempted generation explicitly does not rewind RNG.
- `gpu/orch_r125_continual_native.py:381`: configured LoRA dropout 0.05;
  `:604` exact update schedule; `:610` anchor ordering/index selection;
  `:612` training mode; `:632` optimizer mutation precedes receipt publication
  at `:635`; `:641` aggregate endpoint adapter hash exists only after sleep.
- `gpu/orch_r125_continual_native.py:684`: existing checkpoint destination
  cannot be reused; `:751` pending-generation/sleep reconciliation gate;
  `:758` saved-RNG-boundary gate.
- `gpu/orch_r125_stream_journal.py:455`: original full replay;
  `:463` unexpected/partial entries refuse. The earlier narrow
  `gpu/orch_r125_preupdate_recovery.py:137` path is not a post-update retry.

The native module is identical for these two lives, SHA256
`4092dd4355dbb4c6d2ecbcb2f48ad08b23af4e37817b949c54ad31d6f5bc03c0`.
The stream module is SHA256
`8f22a5754a0cf3a806d552064fe25d4069021e74fff3329c5a7e74e3d226ca33`.
Their relevant excerpts and guard checks are in the new evidence receipt.

## Is randomness evidence sufficient?

**No, not on its own: there is no per-generation randomness receipt here.**
The checkpoint does contain generator states. Under a fully deterministic,
unchanged transition function, restoring those states and reproducing every
RNG-consuming operation could reconstruct subsequent state. Matching generated
tokens alone does not certify RNG consumption: different random states can
produce identical token sequences. Matching five scalar losses likewise does
not certify gradients, optimizer moments, or parameters.

Replay must actually use the original sampling path, not teacher-force saved
tokens, substitute greedy decoding, or advance a guessed number of RNG draws.
It must account for all generators, training dropout, gradient-checkpointing
recomputation, hooks, tokenization, readout/offload behavior, and any interrupted
or discarded attempt. Pin original package/build/device/kernel settings and
demonstrate determinism for that historical configuration. Turning on a new
determinism mode only for recovery is not evidence that the original execution
used that mode. The native’s readout helper saves/restores RNG (`:399`, `:416`),
but that alone is not a complete audit of installed wrappers and sidecars.

## Receipt equality and epoch semantics

1. Authenticate original bytes and intents, request/response links, saved states,
   full raw tail, anchors, model and tokenizer before replay. Preserve every
   original row, presentation, history/working-state transition, INBOX entry,
   sidecar/cursor, and training mask/policy. Do not regenerate external tools,
   ACT effects, parent/provider sends, or ingest current mail during historical
   verification; consume their exact original receipts where required.
2. Recompute model operations in a publication-disabled verification phase.
   Stop on the first mismatch, missing operation, unknown external outcome,
   changed source, changed original head, or exhausted real wall/budget.
3. **Literal newly generated UPDATE bytes cannot equal old bytes:**
   `finished_unix` is generated from the current clock. Verify original bytes
   verbatim, then use an explicitly approved comparator over the exact
   deterministic fields (`optimizer_step`, row hash, full loss list). Record
   original timestamps separately from actual replay timestamps. Do not fake
   historical timestamps, patch the clock, or call this full-record equality.
   If policy demands equality of newly emitted whole records, it is blocked.
4. Duplicate evidence suppression must be exactly indexed/hash-bound and only
   inside that verification phase. No duplicate row/presentation/UPDATE/ACT or
   budget credit; no catch-and-continue comparator, tolerance silently replacing
   exact equality, generic replay of unknown sends, or reset of the deadline.
5. A new explicit replay epoch must bind old head, selected COMPLETE, all source
   and plan pins, verified frontier, comparator, original failures, original
   elapsed/budget usage, actual replay cost and new checkpoint destination.
   Work beyond the authenticated UPDATE frontier is new epoch work, not an
   invented reconstruction of an absent historical receipt.

## Failure-specific limits and irreversible evidence gaps

**C0:** the traceback reaches checkpoint save after sleep returned; all 48
UPDATE receipts exist. `sleep_000146/optimizer_rng.pt` is 86,966,272 bytes and
failed with ENOSPC / unexpected position 86961664 vs 86961556. No COMMIT exists.
Preserve that directory. Its saved adapter may be an additional forensic
endpoint witness only after independently binding and validating its contents;
this review did not hash/load its tensors. It is not a committed checkpoint
and cannot be mixed with the older optimizer. Use a distinct, admitted new
checkpoint path; the existing fixed path cannot simply be retried.

**Astra7:** preserve the empty
`00000000000000007808.intent.json.partial` and head 7807 exactly. The traceback
is at UPDATE intent publication, after the source’s optimizer step. Thus the
source/trace imply a further resident update executed (nominal step 9674),
but there is **no durable UPDATE receipt** for its metrics/state. Empty partial
does not prove that no update happened. A reviewed aborted-publication manifest
can acknowledge the failed attempt without inventing its payload or deleting
it; the unchanged reader still rejects that partial, so a new narrow reader
contract is required. Preserve original head/chain rather than quietly reuse
index 7808 as if no attempted publication existed.

Lost unsaved resident tensors, RNG state and missing publication contents have
no independent historical witness here. Deterministic reconstruction might
recreate them, but new tests cannot retroactively manufacture missing evidence
or prove the historic execution lacked nondeterministic transitions. Durable
authentic rows can all be preserved even if exact resident continuity remains
unprovable. Any weaker recovery claim must be explicitly named and approved;
it must not be silently substituted for the requested strict claim.

## Required tests/proofs before any strict replay admission

- Full checkpoint binary hashes plus adapter/optimizer/parameter-order and
  Python/CPU/all-device CUDA RNG equality after restore; verify resume hooks do
  not consume/change the restored state before historical sampling.
- For every intervening generation: exact prompt-token hash, prompt/messages,
  decoder, token sequence including EOS, terminal/truncation/interruption,
  base/adapter binding and token budget. Inventory every original RNG consumer.
- Deterministic uninterrupted-vs-crash/replay controls using the exact original
  runtime: compare complete adapter/optimizer/RNG state at every update, not
  only outputs/losses. Inject failure before/after optimizer mutation and at
  intent creation/flush/link, record publication, adapter save, optimizer save,
  and COMMIT publication. Include incomplete and absent receipts.
- Exact scheduled row order, own-target labels/masks, objective weights,
  anchors/order, presentation counts and all durable pending rows. Compare
  complete reconstructed history/working-state and mailbox/sidecar cursors;
  include C0’s INBOX/COMPACTION and Astra7’s inbox wrapper.
- Negative mismatch tests for prompt/token/loss/step/source/RNG and unknown
  external effects: no new publication, no duplicate send or silent fallback.
  Explicit timestamp-comparator and duplicate-evidence-suppression tests.
- Original partial/failed checkpoint remain byte-identical; manifest only
  describes actual evidence; unique new checkpoint atomically commits; crash
  during replay itself cannot advance/suppress the wrong epoch frontier.
- Fresh exact-source/CPU/allocation and original confined admission with
  unchanged GPU, wall, lease, policy and total budget accounting. Existing
  consumed guards cannot be reused; actual LOADED is required before claiming
  recovery. No installed bounded fast-resume route is established by this review.

No such replay execution or determinism/control tests were run by this sidecar.

## Bound artifacts

- `REPLAY_WITNESSES_20260919.json` SHA256
  `1d364495c40daee7cf33e7563ca9f47a3a298234a97289af054472803df72dbf`.
- `read_replay_evidence.py` SHA256
  `b22d27f287d5c19feb25691a94f6f84338d620c1d2ff9a40c05080134a604ce7`.
- `NODE2_READ_ONLY_20260919.json` SHA256
  `0981c0861c60a35b492ba0ff717e9a109f2d0cc2e4051b96dd59417b4fd5b2ea`.
- `BOUNDARIES_VERIFIED_20260919.json` SHA256
  `ad85f45a7be0eaa1a372476b4c763ffad3f6ac6571caf53bf95540c7e360fd68`.

All paths above are relative to this sidecar directory. Earlier evidence and
recovery plans remain unchanged; this document refines, rather than replaces,
their assessment of unchanged-reader eligibility.
