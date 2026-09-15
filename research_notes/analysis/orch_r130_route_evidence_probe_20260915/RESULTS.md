# R130 public-evidence route diagnostic — author reduction

**COMPLETE_VERIFIED; AUTHOR_REDUCTION_NOT_INDEPENDENT_REVIEW.** Native execution
completed September 15, 2026, at 21:31:18 UTC. Read-only author verification and
the frozen reducer completed at 21:34:38 UTC. Main's separate cross-check is
pending; this document is not that independent review.

## Result

The checkpoints occasionally changed their first action in the correct direction
when the supplied evidence changed, but most pairs elicited the same action on
both variants. GUIDED_C6 passed 3/16 complete intervention pairs, SEED 2/16, and
UNPARENTED_C6 0/16. **Every reported between-checkpoint interval includes zero.**
This is limited observed content-aligned behavior, not demonstrated useful
learning, robust checkpoint improvement, or an isolated parenting benefit.

| Fixed condition | Historical updates | Correct first actions /32 | Both-correct pairs /16 (primary) | Valid switches /16 | Same-action pairs /16 | Both-wrong pairs /16 |
|---|---:|---:|---:|---:|---:|---:|
| SEED | 0 | 18 (56.25%) | 2 (12.50%) | 2 | 14 | 0 |
| GUIDED_C6 | 424 | 19 (59.375%) | 3 (18.75%) | 3 | 13 | 0 |
| UNPARENTED_C6 | 536 | 16 (50.00%) | 0 (0.00%) | 0 | 16 | 0 |

All 32 actions per condition were valid, with zero invalid pairs and zero
truncated responses. All valid switches were both-correct; no pair switched in
the wrong direction. Same-action counts are 16 minus valid switches because
every action was valid. Gold first actions differ between the two variants, so
a same-action pair necessarily scores exactly one correct first action.
The single-action accuracy numbers must not substitute for the paired primary
readout: a fixed-choice strategy already produces 16/32 on this design.

## Paired uncertainty — all predeclared contrasts

Differences below are **percentage points**, left condition minus right. Each
95% interval comes directly from the frozen reducer: 2,000 paired-world
percentile bootstrap resamples, random seed 0, all 16 worlds, none excluded.
The two variants are not treated as 32 independent observations. Intervals are
pointwise, descriptive, and not multiplicity-adjusted.

| Contrast | Both-correct pair rate: difference [95% interval] | First-action accuracy: difference [95% interval] | Valid-switch rate: difference [95% interval] |
|---|---:|---:|---:|
| GUIDED_C6 − UNPARENTED_C6 | +18.75 [0, +37.50] | +9.375 [0, +18.75] | +18.75 [0, +37.50] |
| GUIDED_C6 − SEED | +6.25 [0, +18.75] | +3.125 [0, +9.375] | +6.25 [0, +18.75] |
| UNPARENTED_C6 − SEED | −12.50 [−31.25, 0] | −6.25 [−15.625, 0] | −12.50 [−31.25, 0] |

An endpoint of zero is **not** an interval excluding zero. These small,
boundary-heavy samples offer weak uncertainty resolution; do not interpret
bootstrap endpoints as strong evidence of superiority or equality. Resampling
worlds does not create independent training lineages. Numeric per-pair metrics,
paired differences, standard errors, and exact interval values are retained in
RESULTS.json.

## What this diagnostic does and does not show

The same task and offered ports occur in both variants. One value in the
supplied, environment-verified root EVENT changes; the hidden complementary
edge changes consistently to preserve the public bijection and a unique gold
first action. Downstream evidence is unchanged. This is not a single-edge edit
of the entire graph. The verifier reconstructed the prospective pairs from the
hash-bound exclusions and invoked the frozen semantic manifest validation.

The 2 SEED and 3 GUIDED both-correct pairs distinguish their observed behavior
on those pairs from a completely invariant port/position choice or always
copying the root record's DID port. All 16 UNPARENTED pairs, 14 SEED pairs, and
13 GUIDED pairs remained invariant. The assay does not identify which heuristic
caused invariant choices. Nor does a small number of correct switches identify
a general semantic mechanism: opaque-token sensitivity, fortuitous alignment,
and simple lexical/structural rules remain alternatives. No independent-guess
1/4 chance baseline is assumed for a switching strategy.

This was one first-action call per variant, with no subsequent route execution
or feedback turn. Correctness is environment-semantic first-action scoring,
**not observed full task completion**. Evidence was supplied oracle material,
not retrieved or child-written memory. Retrieval, source-absent retention,
feedback adaptation, learning, and latent metacognition are not established.
The pairs remain in the same route family; this is not new-task-family transfer.

SEED is the one frozen initial-reference condition, not an extra live baseline.
Fixed terminal C6 checkpoints were predeclared, not selected from R127 outcome
scores. The fixed historical lineages have unequal doses (424 vs 536 updates;
historical token exposures are not matched). Consequently even a checkpoint
difference would be an observational systems comparison, not an isolated causal
parenting-content effect. Evaluation itself used no parents, optimizer steps,
training rows, source-generation calls, or retries.

## Call budget and telemetry

| Condition | Calls /32 | Prompt tokens (all 32 observed) | Generated token IDs, including EOS (all 32 observed) | Truncated responses /32 | Native exit UTC |
|---|---:|---:|---:|---:|---|
| SEED | 32 | 11,571 | 333 | 0 | 21:28:01 |
| GUIDED_C6 | 32 | 11,571 | 336 | 0 | 21:29:40 |
| UNPARENTED_C6 | 32 | 11,571 | 332 | 0 | 21:31:18 |

Total: **96 actual completed calls and exactly 96 unique charged claims**;
34,713 prompt tokens and 1,001 generated token IDs including EOS. The cap was
512 generated tokens per call, context limit 8192, greedy decoding, one beam,
repetition penalty 1. Equal prompts/decoder/call ceilings do not imply equal
realized generated lengths. Separately measured generated-text-only token
counts are **unavailable**, not zero; EOS-inclusive counts must keep that label.

## Provenance and verification

Verification ran on node5 by CPU-only SSH stdin, with an empty CUDA visibility
setting and offline flags. Raw calls, prompt contents, responses, and token IDs
stayed on node5. Only compact metrics, identities, hashes, counts, and paths
were retrieved. No model call, retry, GPU scan/reservation, runtime/source edit,
Git operation, or sealed-artifact read was performed by this reduction.

- Verified **1,189 unique files**, rehashed after reduction for stability:
  anchored PLAN; manifest/export/exclusion inputs; all **963** planned Python
  snapshot files; selected adapter files; publication/allocation and supervisor
  receipts; all three stage BINDING/LOADED/COMPLETE, admission/launch/exit receipts;
  and all **96 CLAIM + 96 CALL files**. No unlisted Python snapshot file was present.
- Checked every COMPLETE.call_refs entry against the canonical ordered stage
  path and actual file SHA-256; required exact stage inventories with no failed
  receipt, extra claim, omitted call, duplicate logical claim, or path alias.
  Full claim/call bindings and response prompt joins matched. Raw response
  hashes were computed in place; compact aggregate commitments are retained.
- Manifest adapter identities matched the selected R127 EXPORT checkpoints,
  the actual exported adapter file bytes, and all BINDING/LOADED/COMPLETE
  identities. Three distinct native process identities were recorded. Historical
  engine contracts matched EXPORT.original_source_files, not merely modern pins.
- The unchanged-state proof is the pinned native producer's pre-COMPLETE
  `verify_unchanged()` check and matching loader/completion receipts, plus offline
  adapter file rehashing. This is **not** a new independent observation of model
  tensors after process exit. The frozen loader checks adapter/base state and
  disabled gradients; all receipts report zero optimizer steps and no parents.
- All three exits were zero, with no retry, before the original 22:00 UTC wall;
  the supervisor reported all three conditions COMPLETE. Recorded admissions
  were checked, not rerun. Read-only reduction does not require the current time
  to precede the old launch wall. No incomplete subset entered a comparison.
- Imported the hash-verified frozen probe and its statistics reducer from the
  run's own source snapshot; invoked `reduce_records(manifest, groups,
  bootstrap_samples=2000, seed=0)`. No modern-source substitution or launch
  validator with a current-time gate was used. Local arithmetic cross-checks
  verify count totals and paired means; Main's independent review remains separate.

Native root: `/localhome/local-rohing/orch_r130_route_evidence_probe_20260915`;
stage receipts live under `run1/{SEED,GUIDED_C6,UNPARENTED_C6}`. The loader's
shared `sealed_readout` phase name is an internal enum, not evidence that sealed
tasks were used; these prompts are the prospective public manifest projection.

| Artifact or commitment | SHA-256 |
|---|---|
| PLAN.json (user-provided trust anchor) | `108f00b4351f31a704d48c719e2a66759031a64435394f1ac379df71df77ae40` |
| MANIFEST.json exact bytes | `e24d362bc039b6a4e0d3e2bffe4127ba5ff6ac7c99edebf60419c95df6a00ee7` |
| Manifest compact document digest | `3efe72fff3a785c142218d6bcd8f464685f7efee7a24563685e8f90fc88838e0` |
| R127 bundle EXPORT.json | `4c4ba2cce039ff479afd7fb5ed00720ecb7d402ee53a14d3df0c94582f7d441f` |
| Frozen R130 probe | `112bb1028ae5b88b8d453500fb2aa0b9cfc711c96b87f35bfd1e9849a2c5c44e` |
| Frozen R127 statistics reducer | `e39320143f9d19d4c30806e642a88dfbd202661aa95c01e60a553c79984ceea1` |
| All verified file-path/hash pairs, compact document digest | `8ff32ac25de8d83a535d4b4afa7d3d0b745848bc225e455017015e91431550ee` |
| Read-only author verifier script bytes | `d6f89dc7279a565e67de042ab709c3ebc5bcc6f85a11e0abbac5fdd134e6dfd5` |
| RESULTS.json exact bytes | `66fa966740d872efd4248f460007b39802c152003a7c21c4c1b286251ffcbc05` |

Document digests use SHA-256 of JSON with sorted keys and compact separators
(`,`, `:`); byte hashes use exact file bytes. RESULTS.json contains selected
checkpoint state/base/file hashes and each stage's receipt and call/claim
commitments without generated text. Only RESULTS.json and RESULTS.md are new
repository files from this author-reduction task; existing protocol, allocation,
source, tests, and Main-owned coordination/publication files remain untouched.
