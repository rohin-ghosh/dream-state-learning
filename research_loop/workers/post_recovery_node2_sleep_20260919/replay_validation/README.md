# Node2 strict replay receipt validation

## Status and scope

Offline comparison helper complete; **no real generation/training replay has been
performed**. This is a non-material diagnostic sidecar, not a recovery policy,
runtime port, acceptance-gate change, or authorization to resume. Writes remain
inside this `replay_validation/` directory. No native/parent signals, GPU calls,
activation, new guard, full journal scan, or changes to failed artifacts/rows.

The only success verdict is `MATCHED_LOGGED_RECEIPTS_ONLY`: exact consistency
with the supplied, externally pinned logged observations. It is **not proof of
exact unsaved resident adapter, optimizer, gradient, or RNG state continuity**.

## Historical context, not results of a model replay

| Life | Saved COMPLETE / LEARN | Saved sleep / optimizer steps | Pending sleep | Committed UPDATEs / last step | Rows |
| --- | --- | --- | --- | --- | --- |
| C0 | 6631 / 6632 | 145 / 8412 | 146, REQUEST6660 | 48 / 8460 | 441 to 444 |
| Astra7 | 7750 / 7751 | 146 / 9644 | 147, REQUEST7776 | 29 / 9673 | 450 to 453 |

Source for these tail counts and failure details:
`research_loop/workers/post_recovery_prefix_proof_20260919/node2_enospc_20260919/RECOVERY_PLAN.md`.
This helper did not independently scan those complete tails. Tests use synthetic
48- and 29-UPDATE sequences with those optimizer counts and three newer rows
each. Reading two actual UPDATE documents only establishes schema compatibility,
not successful recomputation of either life.

Main's independent saved-binary audit is
`research_loop/workers/post_reboot_node2_capacity_20260919/COMMITTED_CHECKPOINT_BINARY_AUDIT_1789790037.json`
(raw SHA256 `9c58fe32d0cb431668f5eae204d6ed86b4135dbfd1722c42de647776f121c03e`).
It reports both saved checkpoints' adapter files and optimizer/RNG bytes matching
their exact COMMITs in 0.779900074005127 seconds. That establishes the saved
baseline's file integrity, not pending-sleep reconciliation or unsaved state.
This helper neither reopens those binaries nor claims to have verified them.

C0's failed `checkpoints/sleep_000146` lacks COMMIT and has an incomplete optimizer
file. Astra7's zero-byte `00000000000000007808.intent.json.partial` remains a
failure artifact; its last committed UPDATE is 7807. No failure/partial is
deleted, rewritten, skipped by a resume reader, or promoted to COMPLETE.

## Exact comparison rules

`strict_replay.py` uses only the standard library and never executes model code.

1. Main must authenticate and pin the **canonical reference-case digest**. The
   helper verifies selected original record hashes, matching intents, saved-state
   hashes, checkpoint reference identity, and declared source bindings. These
   checks do not prove reference selection completeness or the executing source.
2. Compare every supplied post-COMPLETE generation, in order, before comparing
   any UPDATE. Require exact logical REQUEST, including original `started_unix`,
   request/history/resume-state fields and policy flags; exact returned token IDs,
   raw text, terminal/truncation flags, prompt count/token hash, decoder,
   base hash, and actual adapter hash. No token/text normalization or tolerance.
3. A generation observation is the inner `NativeChild.generate` return, **not a
   newly timestamped journal RESPONSE wrapper**. Preserve the original RESPONSE
   and its `finished_unix`: its digest is the historical row `source_sha256`.
   Do not replace historical row provenance using replay time. REQUEST
   `model_state_sha256` is the digest of the checkpoint reference map, whereas
   RESPONSE `adapter_state_sha256` identifies adapter tensors; they are distinct.
4. Compare exact SLEEP_REQUEST, SLEEP_RECIPE, and TARGET_ELIGIBILITY documents,
   preserving old rows, the three newer rows, working state, targets and recipe.
   All supplied committed UPDATEs must be contiguous, ordered, unshortened and
   without extras. Match optimizer steps against saved steps plus prefix position.
5. UPDATE has exactly `optimizer_step`, `losses`, `source_sha256`, `finished_unix`.
   Each ordered loss has exactly `mean_loss`, `objective_weight`, `target_tokens`,
   `kind`. Compare every field **except UPDATE `finished_unix`**, intentionally
   excluded because it records replay wall time. Report both times and whether
   they differ. There is no configurable ignore list, numeric tolerance, reordered
   loss matching, or exclusion of any other differing field. Unknown UPDATE/loss
   fields, nonfinite numbers, ambiguous types and malformed JSON are refused.

Generation failure aborts before UPDATE comparison; this validator cannot
prevent training already performed by an external caller. A future executor must
enforce that ordering itself. Partial/interrupted generation schemas are not
supported. The helper does not manufacture a trace or complete a failed sleep.

## Source receipts and exact pointers

The existing read-only `inspect_sources.py` invocation used `gpu/ovx_ssh.sh` to
read ten exact guard-pinned source files per life and just six selected record /
intent pairs, without importing research code. No additional remote inspection
is required to run these tests. Authoritative receipt:

`source_evidence_1789790199409689539/RECEIPT.json`

Raw SHA256: `782e1a4f110d1a15ac4c6462cfe5b81cc23997896bb3365d7e45c1f63f054fd7`.
It records every exact source path/SHA and selected record file/canonical SHA.
The preserved source preimages are under that directory's `C0/` and `Astra7/`.
Tests verify all 20 local preimages against this pinned receipt.

| Life | Original source root | Selected record indices (REQUEST / RESPONSE / UPDATE) |
| --- | --- | --- |
| C0 | `/localhome/local-rohing/orch_r216_C0_20260918_attempt2/source_r233_lease_continuation` | 6637 / 6638 / 6710 |
| Astra7 | `/localhome/local-rohing/orch_r229_Astra7_20260918/source_r233_lease_continuation` | 7753 / 7754 / 7807 |

Each original record is under the corresponding attempt's
`raw/stream/records/<20-digit-index>.json`; its intent is
`<20-digit-index>.intent.json`. The receipt stores absolute paths, not inferred
cross-life selections. Guard SHAs are respectively
`acf4d2d015874af1cc9585a25de63827e7d7ec36acd7a4509bce09671985f6c2` and
`fae6f4ede1e9c80be060aeca8dd494cbb24a6228b9225e33856b62ec3c0047f6`.

Within either preserved source root, relevant source locations are:

- `gpu/orch_r125_continual_native.py:356`: saved optimizer and Python/CPU/CUDA RNG
  restore; `:381`: LoRA dropout 0.05; `:470`: generation/model receipts.
- `gpu/orch_r125_continual_native.py:608`: train-mode forward/backward;
  `:632`: optimizer step, then counter increment, then UPDATE publication at
  `:635`. Scalar losses describe forward evaluation before the optimizer step.
- `gpu/orch_r125_continual_native.py:399` and `:416`: readout offload/restore saves
  and restores RNG in memory; these methods are not proof of all executed calls.
- `organism_v6/orch_r125_continual_stream.py:191`: original REQUEST identity;
  `:262`: original RESPONSE digest used for row provenance;
  `:326`: checkpoint-reference model identity.

Earlier `source_evidence_1789790000676946479/` remains preserved. Its C0 selections
6634/6635 are CONTEXT_INPUT, not REQUEST/RESPONSE; it is not the authoritative
generation-shape evidence. The corrected inspector checks selected kinds.

## Feasibility limits

Restoring a separately verified saved COMPLETE is a possible replay baseline,
not permission to use the currently ineligible resume route. Receipt comparison
can refuse observed divergence, but matching tokens/scalar losses does not
uniquely identify adapter tensors, gradients, optimizer moments, or RNG state.
UPDATE has **no per-step adapter/optimizer/RNG hashes**. A step executes before
its UPDATE is durable, so work after the final committed prefix is unknown.
In particular, Astra7 may have performed another step before publication failed.

Extra sampling, dropout, warmup/diagnostic calls, failed forwards, preemption and
other unlogged RNG consumers require separate execution accounting. Selected
source inspection is not proof that none occurred; no exhaustive source/library
audit or RNG trace exists here. A strict mismatch may also result from replay
nondeterminism; it must refuse, not be normalized away or diagnosed as corruption
without further evidence. Pending-sleep/partial reconciliation remains Main's
separate policy and route decision.

Success explicitly leaves `exact_resident_continuity_claimed`,
`optimizer_state_equivalence_proven`, `RNG_state_equivalence_proven`,
`unlogged_rng_calls_excluded`, `checkpoint_binary_verification_performed`,
`full_journal_verified`, `pending_sleep_reconciled`, and `recovery_authorized`
**false**. Caller-declared source/checkpoint identity is not execution attestation.

## API and CPU invocation

From this directory:

```bash
PYTHONDONTWRITEBYTECODE=1 CUDA_VISIBLE_DEVICES= python3 -B test_strict_replay.py
python3 -B strict_replay.py --reference /path/to/pinned-reference.json \
  --reference-sha256 CANONICAL_REFERENCE_DIGEST --observed /path/to/replay.json
```

The latter requires externally supplied real observations; no actual-life replay
case or recovery command is supplied. It reads only the two bounded regular JSON
files and prints the verdict; it never opens referenced source/checkpoint/journal
paths. Symlink case files, duplicate JSON keys and changed-during-read files fail.

API: `validate_replay(reference, observed, reference_sha256=digest(reference))`
with the expected digest supplied from an independently pinned reference, not
recomputed from an untrusted file at acceptance time. `compare_generation(...)`
and `compare_update(original, recomputed, expected_step)` are lower-level checks.

Reference keys: `schema=POST_COMPLETE_STRICT_REPLAY_CASE_V1`, `life_id`,
`journal_id`, `source_pins` (relative path to exact SHA), `decoder`, `complete`,
`generations`, `sleep_inputs`, `updates`. Each original envelope contains
`record` and `intent`; each generation contains REQUEST and RESPONSE envelopes.
The three sleep envelopes follow SLEEP_REQUEST / SLEEP_RECIPE /
TARGET_ELIGIBILITY order. UPDATE envelopes cover the entire Main-pinned prefix.

Observation keys: `binding` with `source_pins_sha256` and
`checkpoint_reference_sha256`; `generations` with `request` and `model_response`;
`sleep_inputs` with `kind` and `document`; `updates` with recomputed documents.
`test_strict_replay.py:17` provides an explicitly synthetic example builder.
No observed journal hash is compared to an original hash that includes different
replay time; original record/intent integrity is verified separately.

`TEST_RECEIPT.json`, `TEST_OUTPUT.txt` and `SHA256SUMS` record the final local
tests, exact helper/test/document/source hashes and evidence boundaries. Test
success is helper validation only, never evidence of real model replay.
