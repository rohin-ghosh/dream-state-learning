# R130: prospective public-evidence first-action diagnostic

Status: CPU preparation only; no GPU launch or reservation by this sidecar.
Scope: small mechanism diagnostic of existing fixed checkpoints, subordinate to
R121's L1 paper focus. No new L2 architecture, training loop or paper-level claim.

## Concrete valid intervention

Use 16 fresh canonical-shaped two-hop worlds. The task has the same root, GOAL,
two offered opaque ports and three supplied EVENT addresses in both variants.
Provide one root-transition record and the two downstream-transition records.
The neutral public rule states that the two offered ports lead bijectively to
the two intermediate nodes, each with one onward route, exactly one reaching GOAL.

Illustrative names below are explanatory, not the model's opaque identifiers:

| Supplied fact | Variant A | Variant B |
|---|---|---|
| Root port P | GOT B | GOT C |
| B's onward route | GOT goal | GOT goal |
| C's onward route | GOT other goal | GOT other goal |

The environment-semantic gold first action is P in A, the other offered port in
B. The public packet changes **one GOT value**, not an answer label. Task text,
record order, every other EVENT field and instruction are unchanged within pair.
No checkpoint identity, variant label, expected action, success flag or private
world graph is sent to the model.

**Necessary consistency closure:** the hidden complementary root edge swaps its
destination too. Changing only one edge of a complete bijection would duplicate
a destination and destroy the unique flipped solution. We do not claim a
one-edge intervention on the full graph. It is a one-value intervention on the
supplied evidence under a valid complemented two-edge environment permutation.
The hidden root record is never supplied. The generic bijection rule makes the
unshown transition inferable without identifying which action is correct.

The resulting worlds remain isomorphic to the original two-hop topology, but
are explicitly new diagnostic variants, not mislabeled historical canonical
worlds. CPU verification enumerates all public-compatible root bijections and
requires the unique inferred action to match real two-step transitions. The
original canonical route scorer independently checks the successful path.

## Evidence and visibility

These are **environment-verified oracle EVENT records**, rendered from fresh
deterministic environment transitions and checked against their public receipts.
They are not claimed to be child-written memory, recalled evidence or old native
calls. There are zero native source-generation calls. Every offered record must
be available, address-matched, receipt-grounded and bound to its variant world;
missing, unavailable, contradictory and wrong-world records reject the pair.
No model call occurs until all 16 pairs pass CPU semantic validation.

The prompt pre-supplies the three records and requests one literal ROUTE. No
READ or explanation is requested, and there is no retry, feedback conversation
or second model action. This removes retrieval quantity as the success measure;
it deliberately differs from R127's autonomous READ/ROUTE episode. Explicit
public structure and oracle-quality evidence make this a supported-context
diagnostic, not a naturalistic transfer or endogenous memory test.

## Fixed checkpoints, budget and matching

- Conditions are **SEED, GUIDED_C6, UNPARENTED_C6**, selected from the frozen R127
  EXPORT by their terminal cycle index, not the best observed R127 checkpoint.
  This selection is frozen before any R130 native responses. C4 is not selected
  post hoc because its R127 read/correctness counts looked stronger.
- Preserve actual historical cumulative updates in the manifest, including the
  C6 dose imbalance. SEED is the same initial adapter, not an extra live baseline.
- Frozen Qwen2.5-7B-Instruct base and existing LoRA adapters only; no new adapter,
  optimizer, training rows, parent messages, sleep, teaching or FINAL access.
- 16 pairs × 2 fresh-context variants × 3 checkpoints = **96 native calls maximum**,
  exactly one call per variant/condition; 32 per condition. Greedy decoding,
  one beam, repetition penalty 1, context cap8192, generation cap512 as in R127.
- Same task, packet, request order and decoder across checkpoints. Within pair
  only one public GOT identifier changes. Equal textual shape and call caps do
  not guarantee equal tokenization lengths or realized output-token exposure;
  actual prompt and EOS-inclusive generated token counts remain reported.
- Root-port display order, GOAL branch and first presented variant are
  counterbalanced; anchor record position rotates. Pair identifiers are fresh
  and checked against the caller's explicit exclusion list and each other.
  No shared prompt state or earlier response is carried into the next request.

## Readout and behavioral alternatives

Primary diagnostic: **both variants' first actions correct within a pair**.
Report all 16 pairs and all three conditions, plus per-variant accuracy, valid
action switches, both-wrong pairs and pairs containing invalid/truncated outputs.
Use 16 paired worlds for uncertainty, never 32 independent variants. Contrasts
are fixed GUIDED−UNPARENTED and each versus SEED; pointwise paired-world bootstrap
intervals are descriptive and not multiplicity-adjusted. Missing conditions or
incomplete inference groups withhold comparative readouts.

- A fixed port/position preference or copying the root record's DID port gets
  one side right but **zero both-correct pairs**. More READs cannot pass because
  READ is not an accepted action in this assay.
- A valid action flip in the wrong direction produces both-wrong pairs, not
  useful content alignment. Report flips separately from pair correctness.
- Successful public-evidence conditioning can pass: match the root outcome to
  the downstream GOAL relation and use the bijection when the anchor is wrong.
- Sensitivity to a changed opaque token alone, fortuitous alignment and simple
  lexical/structural algorithms remain alternatives to broad semantic ability.
  A flipping-but-uninformed strategy need not have a 1/4 pair-success baseline;
  do not assume independent variant guesses or call switch rate content use.
- Similar SEED and trained results suggest pre-existing supported-context
  competence; a checkpoint difference is not an isolated parenting-content
  effect given fixed lineages and unequal historical exposure. Null performance
  can reflect prompt/format difficulty, not absence of all content-use ability.

Even positive results support only **local, content-aligned first-action behavior
under this supplied-evidence diagnostic**, not latent metacognition, new learning,
endogenous evidence use, general skill improvement or parent-specific benefit.
There are no independent training-seed replications; retain weak diagnostic scope.

## Runnable integration (Main owns dispatch)

CPU preparation:

```text
python3 -m gpu.orch_r130_route_evidence_probe prepare \
  --export /absolute/R127/bundle/EXPORT.json \
  --exclusions /absolute/verified_excluded_ids.json \
  --output /absolute/new_R130_manifest_directory
```

The exclusion file is an explicit JSON list of previously used opaque identifiers
assembled by Main from allowed provenance sources. Do not read FINAL data to
construct it. The preparation preserves references/hashes for both input files
and creates only MANIFEST.json; it does not load a model or reserve a device.

Main supplies a separate runtime PLAN with `schema` equal to the manifest schema,
`manifest: {path, sha256}`, `trainingAllowed: false`, `optimizer_steps: 0`,
`training_rows: 0`, `parent_calls: 0`, absolute `output`, `model_dir`, `source_root`,
explicit `gpu_uuid`, `hard_end_unix`, `lease_end_unix`, and `source_files` mapping
**all .py files in Main's staged frozen snapshot** from relative filename to byte
hash. `SOURCE_CLOSURE` is a required minimum subset, not a filter: the validator
checks every supplied entry, including extra transitive helpers. Absolute names,
traversal, aliased paths and symlinks are rejected before source acceptance.
`HISTORICAL_ENGINE_CONTRACTS` additionally binds the legacy route engine, loader,
native backend/state hasher, portable/shared-run/guard, cue-sleep/masks and route
semantic contracts to `EXPORT.original_source_files`. A newly computed snapshot
hash cannot authorize changed historical engine bytes; missing historical hashes
or disagreement fail before loading. The two new analysis/probe modules have
their own snapshot pins rather than fictitious historical hashes. Other supplied
files are snapshot-pinned; this is not automatic discovery of every dynamic import.
No device, lease or admission is inferred by the probe. Main performs its normal
CPU/provenance logging, lifecycle/ownership and lease checks before dispatch.

`validate --plan /absolute/PLAN.json` is CPU-only. Later, Main may invoke `stage
--plan ... --condition SEED` (and each fixed C6 condition) in separate fresh native
processes with explicit CUDA_VISIBLE_DEVICES and both offline environment flags.
The stage uses the existing native read-only loader and R127 route Engine, checks
the actual exported adapter identity, and calls `verify_unchanged()` before
COMPLETE. This sidecar does not run these commands or poll/reserve any GPU.

Stage directories are exclusive: no reuse or replay of old logical calls.
Each call writes a fresh charged claim before generation, then a full call record,
including failures; there are no retries. The write helper accepts only named
evaluation/claim/call receipts, never TRAIN, ROWS, SLEEP or checkpoint writes.
The separate FAILED receipt preserves an interrupted condition without replacing
old artifacts. No existing producer or runtime source is modified.

Pure APIs: `make_manifest(exported, exclusions)`, `validate_pair(pair)`,
`evaluate_condition(manifest, condition, generate, emit)`, and
`reduce_records(manifest, condition_to_call_records)`. Native generate gets only
the projected public messages and generation cap, not labels or private graphs.
Main remains responsible for future result-file hashref verification and a
publication readout; these CPU tests are not native performance evidence.
