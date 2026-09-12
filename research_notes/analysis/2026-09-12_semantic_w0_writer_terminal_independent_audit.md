# Semantic W0 writer: independent terminal raw-artifact audit

Date: 2026-09-12 UTC

Scope: fresh, read-only terminal audit of node-3 run
`/localhome/local-rohing/astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1`,
its frozen `d160e0b2` source, sealed raw records/adapters/receipts, and the
committed preparation and terminal receipts. I read `AGENTS.md`, the full
prelaunch watcher audit, relevant Builder entries in `research_loop/COORDINATION.md`,
and the terminal memo at `origin/main` commit `6563c061`. I did not edit or run
builder code, use a GPU, launch or stop a job, or change the notebook. This
memo is the only file I changed.

## Corrected verdict

**The execution is terminal, intact, and exactly replayable, but its score
channel is not presently valid as a common-prefix causal probability assay.**
This correction supersedes every probability, NLL, conditional-probability,
TV, margin, headroom, and common-mode probability interpretation in the first
version of this audit.

The sealed reducer exactly reports `OPTIMIZATION_INCONCLUSIVE`, with
`oracle=true`, `optimization=false`, `binding=false`, `interface=true`, and
`spill=false`. Those are faithful outputs of the frozen implementation, not
all scientifically valid gate measurements. In particular, 266/832 score
requests contain an impossibility for the intended score semantics:
`exp(score0) + exp(score1) > 1.000001` for two distinct complete LF+EOS
continuations of the same byte-identical causal prefix. The maximum is
`1.3802383379079028`. All 266 contradictions are ON-adapter requests.

What remains defensible is narrower:

- Four fresh-base LoRA fits really ran for 256 steps each, produced distinct
  nonzero updates, lowered their online training losses, and reloaded the
  intended adapters.
- Greedy generation and exact output parsing remain valid. Held-form balanced
  accuracy is only `0.5000`--`0.5781`; every cell independently misses all
  generation-based binding thresholds. This is not a selective writer.
- Two adapters induced very broad generation action changes on locality
  prompts (`91/96` and `93/96` OFF-to-ON action flips), while the other two
  changed `15/96` and `23/96`. This is descriptive evidence of coarse,
  map-level/nonlocal action bias, not a probability claim or a preregistered
  locality endpoint.
- The recorded score sums have reproducible numeric orderings and no ties, but
  pending causal diagnosis those orderings are only pseudo-score artifacts.
  They cannot be called likelihood rankings, model preferences, semantic
  margins, or evidence of conditional carriage.
- No exact-training-row post-fit score or generation endpoint exists. Whether
  the intended row associations were stored and failed held-form extraction,
  or were not stored as associations, remains unidentified.

This is evidence about four deterministic, root/seed-confounded supervised
seen-key instances. It is not evidence of unseen-key generalization, compiler
semantics, population reliability, clean lineage, official model provenance,
parenting, retention, H1/H2 closure, or substrate incapacity.

## Authoritative identities and replay

| Item | Identity |
|---|---|
| Frozen source commit | `d160e0b26405a7e40eb7de0dca23cfcb94cdbf37` |
| Frozen writer module | `d6ea45ac6bfb5cabe6cbd1224f4cf101e96cbd0e07c029e934c2aa3e03e1ddb0` |
| Manifest | `f6fa9060e9ea794309839a8651adc728989c283663070b348c3200acca57a830` |
| **Terminal `report.json`** | **`31ea19f9d0c8807a30252340dc0582e829bb4ac6d1c438f712e590a909ad31af`** |
| Prepared capsule | `b9e424534a2a288732dcba7c512d807c931dea9a9f9ea5897ddd32036157e689` |
| OFF-only partial capsule | `efc63f9aa17113dd4a7fc4431847b999d9de5004d18ffd03be36aa11fe03e192` |
| Terminal metadata/raw-evidence capsule | `422b27e55f794cd14670f049ad09fd31b95887aa615c4d59bc0a03687e83dcf0` |
| Original controller/replay stdout | `9e4480d176da221c1f16f9915aa13dcf78014d76bcaa100102ce56d7e2cd57eb` |
| Cleanup observation | `da92c6a857d8ee732c1d10de5529f943151da18da5a0f8c9946a651b837465f7` |

The terminal `SEAL.json` binds 1,864 files other than itself, including the
report, all 1,712 per-request raw JSON records, four adapter directories, all
four 256-line step streams, and every stage receipt. There are no missing or
extra raw requests, exactly 1,024 step rows, and no `FAILED.json`. The later
committed terminal capsule excludes the adapter weight binaries; those remain
on node 3. It corrects the first audit cut's lack of a committed terminal
capsule but does not replace the sealed node root for weight custody.

I ran the frozen source's CPU-only replay from the immutable node-3 checkout:

```text
env PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. CUDA_VISIBLE_DEVICES= \
  HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 \
  /localhome/local-rohing/v2/venv/bin/python -B \
  -m organism_v6.semantic_writer_diagnostic replay \
  --run /localhome/local-rohing/astra_diagnostics/astra_semantic_writer_Q0_20260912_attempt1
```

It exited `0` in 6.51 seconds. Replay checked the seal, request counts,
response-token accounting, stage ordering, worker/source/model/adapter
bindings, cleanup receipts, raw hashes, and exact object equality with sealed
`report.json`. Its compact stdout hash exactly equals the original controller
log hash above. Exact replay establishes faithful execution of the code; it
does not validate the causal meaning of a defective score path.

## Terminality and cleanup

The external launch receipt records controller PID 98756 at
`2026-09-12T13:08:31.866379Z`; sealed `STARTED.json` records
`13:08:31.994031Z`. `RESOURCE.json` covers 1,414.695 seconds through
`13:32:06.694598Z`; the seal followed at `13:32:07.219655Z`, and successful
controller output ended at `13:32:09.360669Z`.

All 14 stages have return code zero. Every `CLEANUP.json` says
`owned_group_empty=true`, with null error and cancellation signal. The
committed 13:34:51 UTC observation records controller absence, no GPU compute
process, zero used framebuffer memory, and reservation release. My later
read-only check also found the controller and all recorded stage identities
absent and no GPU compute processes. No process was killed during this audit.

`RESOURCE.json` precedes seal and replay, so it omits the final roughly 2.67
seconds. The detached launcher had no independent outer timeout, and the run
seal itself does not bind a post-replay controller-exit/release receipt. The
separately committed cleanup observation substantially closes operational
release, but the full controller lifetime remains outside the run seal, as
anticipated in the prelaunch audit.

## Denominators and fit evidence

The sealed evidence has exactly 1,712 requests:

- OFF: 208 generation plus 192 scoring = 400;
- each fitted adapter: 168 generation plus 160 scoring = 328;
- total generation 880; total scoring 832; two candidate forwards per score
  request = 1,664;
- four fits, each 128 fixed-order rows over two epochs, batch size one, exactly
  256 optimizer steps and 1,920 supervised target tokens.

All 880 generations are legal exact actions with zero truncations and zero
multiple-`ACT` outputs. Primary validity is `1.0` in every cell and stratum.
Native-copy generation canaries are 8/8 for OFF and each compatible adapter,
48/48 unique copy requests overall.

Training evidence from the sealed step streams is:

| Fit | Epoch-0 loss | Epoch-1 loss | First-32 -> last-32 | LoRA update norm |
|---|---:|---:|---:|---:|
| root0/W+ | 0.391477 | 0.102662 | 1.195708 -> 0.096589 | 1.852419 |
| root0/W- | 0.405064 | 0.099415 | 1.276739 -> 0.093614 | 1.862776 |
| root1/W+ | 0.389810 | 0.097436 | 1.225395 -> 0.094316 | 1.885763 |
| root1/W- | 0.431020 | 0.103306 | 1.344267 -> 0.100843 | 1.789289 |

Replay verifies every evaluation began from a fresh base and loaded the saved
adapter with the expected LoRA tensor digest. This is valid evidence of real,
persisted updates and a functioning fit/reload path, not of semantic storage.

## Causal-score contradiction

The scorer constructs each full `prefix + candidate` token sequence
separately, passes an all-ones attention mask with `use_cache=False`, applies
log-softmax to the logits, and sums gathered response-token values, including
LF and EOS. Raw records confirm every candidate token sequence begins with the
exact recorded prefix. The two candidates are distinct complete continuations,
`ACT: -mem2reg\n` and `ACT: -gvn\n`, and share their first three response
tokens.

For a causal model evaluated under the same prefix, disjoint complete LF+EOS
continuations must have total probability at most one. Direct raw-record
enumeration instead gives:

| State | Requests | `exp(score0)+exp(score1)>1.000001` | Maximum sum |
|---|---:|---:|---:|
| OFF | 192 | 0 | `4.10e-10` |
| root0/W+ | 160 | 63 | `1.3802383379` |
| root0/W- | 160 | 65 | `1.238613` |
| root1/W+ | 160 | 67 | `1.221323` |
| root1/W- | 160 | 71 | `1.239331` |
| Total | 832 | 266 | `1.3802383379` |

The maximum record is request
`6037e2ee598f607722a5457a7464e54d0baf89f9a809903d1db4d46bdde6384c`
(root0/W+, neighbour item 12). Its prefix length is 93 tokens. Candidate
response IDs are `[6823,25,481,10536,17,1580,198,151645]` and
`[6823,25,481,21404,77,198,151645]`; their recorded sums are
`-0.3505925196353985` and `-0.39161003538071526`.

The contradiction is not a normalization rounding edge. Across all score
requests, 1,679/2,496 paired values for the three shared response tokens differ
between the two full-candidate forwards; 919 differ by more than `1e-6`, with
maximum absolute difference `0.02408527`. Future candidate content or length
is therefore associated with recorded values at positions that should be
prefix-invariant. A no-fit prefix-invariance/mask diagnosis is running under
Builder ownership. Its cause and any corrected scores are outside this audit.

Until that diagnosis resolves causal validity, no recorded score may be used
as a probability or negative log-likelihood. Consequently the earlier claims
about 25.92--26.60-nat target gains, summed action probability, `2.35e9`
common-mode mass growth, conditional NLL gains, binary TV, margins, and 29/34
headroom-feasible successes are withdrawn as scientific interpretations.
Those numbers remain reproducible transformations of the sealed pseudo-scores
only.

## What the generation channel establishes

The primary held-form generation results are independent of the invalid score
path:

| Cell | Correct /64 | Balanced accuracy | Gain over OFF | Opposite BA | Actions `[-mem2reg,-gvn]` |
|---|---:|---:|---:|---:|---|
| root0/W+ | 37 | 0.578125 | 0.078125 | 0.421875 | 47, 17 |
| root0/W- | 33 | 0.515625 | 0.015625 | 0.484375 | 3, 61 |
| root1/W+ | 32 | 0.500000 | 0.015625 | 0.500000 | 2, 62 |
| root1/W- | 34 | 0.531250 | 0.015625 | 0.468750 | 54, 10 |

Stratum correct counts are 17/32 and 20/32, 16/32 and 17/32, 15/32 and
17/32, and 18/32 and 16/32 respectively. Thus every cell misses the registered
generation requirements: BA `.80`, OFF gain `.20`, map contrast `.50`, and
both-strata accuracy `.75`. The score-dependent key-margin requirements are
uninterpretable, but are not needed to conclude that binding fails.

On the 64 identical held prompts per root, complementary adapters changed the
greedy action on 44 prompts for root 0 and 52 for root 1. Both maps were
generation-correct on only 25/64 and 27/64. This supports coarse map/action
bias rather than reliable 16-key conditional generation.

Valid generation also exposes nonlocal action changes without score semantics:

| Cell | Missing /8 | Unsupported /8 | Neighbour /16 | Wrong root /64 | Total /96 |
|---|---:|---:|---:|---:|---:|
| root0/W+ | 2 | 2 | 1 | 10 | 15 |
| root0/W- | 8 | 8 | 16 | 59 | 91 |
| root1/W+ | 8 | 8 | 16 | 61 | 93 |
| root1/W- | 1 | 1 | 2 | 19 | 23 |

These are exact OFF-to-ON greedy-action flip counts. They are post-hoc
descriptors, not a substitute for the preregistered locality threshold.
Legality has no cancellation ambiguity in this run: every OFF and ON locality
generation is valid, so valid-to-invalid and invalid-to-valid counts are both
zero in all cells. The known signed-legality reducer defect was not activated.

The carrier/oracle generation surface also remains valid: all four exact-row
cells are 16/16, complementary generation swaps are 32/32, native copies are
16/16, and there are no truncations or multiple actions. The carrier's score
portion uses the same suspect path and has no probability interpretation.

## Do any score-ordering claims survive?

Only a strictly non-semantic computational fact survives. All 832 records have
a strict ordering between the two recorded candidate sums (zero ties). Raw
pseudo-score winner agrees with the valid greedy action in 163/192 OFF records
and, respectively, 120/160, 153/160, 128/160, and 156/160 records for
root0/W+, root0/W-, root1/W+, and root1/W-. Complementary-map pseudo-winners
flip on 44/64 and 58/64 shared held prompts for roots 0 and 1.

Those byte-bound orderings can be reproduced and used to debug the scorer.
They cannot presently be called model preferences or likelihood orderings:
each candidate was evaluated in a different full-sequence context, and even
their shared-prefix token values are not invariant. Therefore no substantive
non-probabilistic score-ordering claim about semantic carriage survives. Only
greedy generation provides a causally interpretable action ordering here.

## The nominal half-nat and spill gates

The sealed reducer normalizes the two pseudo-scores to `q` and computes
`log q_ON(target)-log q_OFF(target)`. Within that implemented arithmetic,
`log q_ON<=0`, so the `.5` threshold is mechanically unreachable for 30/64
key-map groups, split 8, 8, 7, and 7 by cell. The largest excluded algebraic
ceiling is `0.487578124203`, and the smallest retained one is
`0.511044663858`. This remains a valid proof that the frozen all-key gate was
impossible as coded. It is not a probability-headroom or NLL claim while the
underlying scores lack causal validity.

Likewise, the reported 16 binary-TV means (`0.275157`--`0.659671`) and
`spill_ok=false` reproduce exactly from the pseudo-scores, but cannot presently
be interpreted as probability locality. The normalization also has the known
common-mode blind spot. My earlier common-mode reconstruction is withdrawn
because its inputs fail the prerequisite probability test. Generation-only
locality flips above are the defensible off-target observation.

## Exact-train coverage and remaining identification gap

Each fit manifest contains 128 rows. Exact rendered-prompt matching against
all fitted-state score requests finds 0/128 post-fit score rows in every cell.
There is also no exact-train generation endpoint. Online loss decrease proves
the repeated supervised batches became easier; it does not establish exact-row
storage after reload. Even a future exact-train scoring supplement must first
use a causally valid scorer.

The present data cannot distinguish exact row-level associative storage plus
failed held-form extraction from failure to store the intended associations.
The active no-fit diagnostic can identify the score-path defect; it cannot by
itself supply the missing exact-train endpoint or rescue failed held generation.

## Gate-by-gate disposition

| Gate | Report | Defensible disposition |
|---|---:|---|
| `oracle_ok` | true | Exact reducer output. Generation-only carrier eligibility is valid; score-based carrier evidence is provisional. |
| `optimization_ok` | false | Exact reducer output from invalid pseudo-score interpretation; additionally impossible as coded for 30/64 groups. Non-diagnostic about learning. |
| `binding_ok` | false | Exact reducer output. Independently established by failure of every generation BA, gain, contrast, and stratum requirement; no score margin is needed. |
| `interface_ok` | true | Valid: all generation outputs parse exactly, with no truncation/multiple output and all copy canaries correct. |
| `spill_ok` | false | Exact reducer output, but its probability-TV meaning is invalid. Large generation-only locality action flips survive descriptively for two adapters. |

The priority label `OPTIMIZATION_INCONCLUSIVE` is an exact implementation
result, but it is score-contaminated and not a scientific diagnosis. The
generation evidence independently rejects qualification as a selective writer.

## Preparation and provenance limitations

The committed external node CPU log says 48 tests passed in 21.617 seconds,
and preparation JSON matches the manifest/counts. Those receipts are not
incorporated into `manifest.json` or `SEAL.json`; the builder preflight
reference is free text, and no sealed native compiler/header/Triton receipt or
exact CPU command/stdout/stderr hash is present. Successful completion of 1,024
optimizer steps establishes the training path worked for this run, but does
not repair prelaunch provenance binding.

The manifest binds frozen sources, package versions, driver/GPU, local
model/tokenizer inventory, requests, material, fits, carrier proof, and
protocol. Its boundary correctly states `clean_lineage=false`,
`official_model_authentication=UNRESOLVED_LOCAL_HASHES_ONLY`,
`training_run_replication=false`, and `root_seed_confounded=true`.

## Maximum defensible claim

In four deterministic fresh-base rank-8 LoRA fits on the pinned local
Qwen2.5-7B-Instruct snapshot, the recipe produced real persisted updates and
strong coarse action biases after reload. Strict greedy generation remained
near chance on the held 16-key mapping and changed actions broadly outside the
target panel for two adapters. Thus this run does not qualify a selective
semantic writer.

What failed is held-form conditional generation for this recipe/assay
instance. What remains unidentified is exact-row storage versus extraction,
because exact-train evaluation is absent. In addition, the entire score-based
mechanistic picture is unidentified until prefix invariance and masking are
diagnosed: no causal probability, NLL, TV, margin, common-mode mass, or
semantic pseudo-score-ordering conclusion is defensible now. No automatic
successor, qualification, parenting, retention, compiler-utility, or H1/H2
promotion follows.
