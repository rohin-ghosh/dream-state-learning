# Frozen-OFF preservation pair: terminal independent audit

Date: 2026-09-12 UTC  
Evidence cut: origin builder commit `7a823dbe`  
Status: watcher-side audit only. No builder source, model, adapter, process,
GPU job, reservation, or experimental artifact was changed.

## Verdict

**Coefficient `0.1` strongly suppressed completion-frame spill, but it also
suppressed the registered completion-frame acquisition. Both G9 and G11
fail.** This is a useful acquisition--preservation tradeoff diagnostic, not a
selective writer.

The independent raw-cue reduction is:

| registered completion-frame endpoint | coefficient `0` | coefficient `.1` |
|---|---:|---:|
| dose-16 conditional correct `P`, OFF -> ON | `.259650 -> .685323` | `.259650 -> .294130` |
| dose-16 `dP` | `.425673` | `.034480` |
| `I_d_frame`, 95% owner-bootstrap interval | `1.921470 [1.202608, 2.682503]` | `.152267 [-.023955, .333066]` |
| spill: unexposed / similar / bicycle | `.321309 / .416577 / .508725` | `.035201 / .039542 / .035231` |
| mean frame spill | `.415537` | `.036658` |
| dose-16 colour-candidate mass, OFF -> ON | `.008738 -> .998158` | `.008738 -> .010287` |

Thus the treatment lowered mean frame spill by `.378879` (91.2%), but the
registered limit is `.03`: `.036658` is still 22.2% above it. More
importantly, acquisition fell by `1.769203` nats on `I_d_frame`, and its
within-arm interval now crosses zero. Conditional `dP` fell by `.391193`.
The total four-colour mass fell from `.998158` to `.010287`, close to its
`.008738` OFF value. The small normalized colour shift therefore cannot be
read as a preserved useful frame response.

The treatment's frame dose curve is `.020376 / .032189 / .033974 / .034480`
at doses `0/1/4/16`. It is nearly flat: the dose-1 to dose-16 rise is only
`.002291`, versus the registered `.10`. G10 fails.

## The older surface read does not rescue the result

The same 1,313-cue file also contains the older, explicit fact-question
surface. I independently recomputed it separately because it points in a
different direction:

| old explicit-question endpoint | coefficient `0` | coefficient `.1` |
|---|---:|---:|
| `I_d`, 95% owner-bootstrap interval | `2.409904 [1.394150, 3.436056]` | `2.686075 [1.012726, 4.582353]` |
| dose-16 `P`, OFF -> ON | `.246622 -> .535905` | `.246622 -> .586636` |
| old-surface unrelated shift | `.392885` | `.388951` |
| old-surface colour-candidate mass ON | `.330744` | `.332883` |

So the additive objective retained—and slightly strengthened—the old explicit
question behavior, but did not make that behavior local: unrelated shift
stayed near `.39`, almost thirteen times the `.03` ceiling. Meanwhile it
nearly erased extraction through the prospectively selected completion-frame
read. This is interface-dependent transport, not selective semantic binding.
No program/game action behavior was evaluated in this pair; “behavior” here
means only the saved probability responses to the fixed cue surfaces.

## Every native gate

I regenerated all native gate decisions from the captured 1,313 raw cue rows
and frozen metric source. Separately, the stdlib watcher reducer recomputed
the registered frame, spill, mass, dose, and abstention quantities without
importing `memory_dose.py`. The discrete verdicts agree:

| gate | coefficient `0` | coefficient `.1` |
|---|---|---|
| G1 `p_on` | fail (`.535905`) | fail (`.586636`) |
| G1 `dP` | fail (`.289283`) | pass (`.340013`) |
| G2 prior subset | not evaluable | not evaluable |
| G3 trigger nats | pass (`5.313637`) | pass (`7.156358`) |
| G4 old-surface `I_d` interval | pass | pass |
| G5 old-surface unrelated | fail (`.392885`) | fail (`.388951`) |
| G6 in-context | fail (`.581913`) | fail (`.796468`) |
| G6 repaint | fail (`.567795`) | fail (`.716583`) |
| G7 retention | not evaluated | not evaluated |
| G8 old-surface dose trend | pass | pass |
| G9 old-surface mass | pass (`.330744`) | pass (`.332883`) |
| **G9 completion-frame binding** | **fail** | **fail** |
| G10 completion-frame dose | fail | fail |
| G11 abstention | fail | fail |

G11 cannot be obtained by preserving the frozen base: treatment ON
abstention is only `.012080` on unexposed frames, `.017406` on bicycle frames,
and `.012176` at dose 16. The first two must be at least `.5`.

## Matched comparison and custody

The causal pair is valid for this bounded diagnostic. Direct inspection of
the two plans, training metadata, traces, and evaluations verifies:

- exact initial LoRA SHA-256 in both arms:
  `2724901a6dbf50cd74d1424041e7f8a4c4ca6769621a34a904ac3a6b0b4abbce`;
- exact memory order, 48 anchor rows/token IDs, model-file inventory,
  trainable parameter names/dtypes, PyTorch version, and all source-input
  hashes;
- rank 8, alpha 16, dropout `.05`, seed 2, AdamW `1e-4`, batch 4, three
  epochs, and exactly 9,693 updates in each arm;
- exactly 749,985 input-token and 711,213 supervised-token passes per arm;
- all 1,313 cue identities, metadata, candidate order, and serialized OFF
  values equal across arms;
- the fresh coefficient-0 ON and OFF cue records equal the historical A1
  seed-2 records exactly. This is deterministic bridge replication, not a new
  learner seed.

Treatment cache SHA-256 is the predeclared
`e245e790cabc7fef53e32b111b43244f26ff9ea0963883959fb622fba44f3cf8`.
Attempt 1 remains preserved as a zero-update validation failure. Attempt 2's
only source change is the pre-outcome float64 normalization *check*; cached
float32 bytes and the training objective were unchanged.

Both controllers ended `WORKER_COMPLETED`; their owned groups and GPU
processes are absent and their reservations were released. Terminal capsule
SHA-256 values are `fb8d7951...f183` (control) and `c401bfdc...034e`
(treatment). Adapter weights are omitted from the capsules; separate remote
weight hashes are recorded, so saved cues and traces can be reduced but the
fits cannot be independently replayed from repository artifacts alone.
Official base-model authentication remains unresolved local-file hashing.

## Objective trace and the meaning of `lam1`

Every one of the treatment's 9,693 trace rows satisfies
`objective = CE + .1 * KL`; anchor indices rotate exactly, with 202 visits for
indices 0--44 and 201 for 45--47. Mean CE is `.716963` in control and
`.718169` in treatment, so the frame under-write is not a failed CE run.

Treatment KL was `.108837` over the first 48 steps, `.016028` over the whole
fit, and `.011352` over the final 48 pre-update observations. This establishes
that preservation pressure was active. It does **not** establish terminal
preservation over all anchors: the implementation never sweeps the final
adapter over all 48 anchors after the last update.

The evaluation filename/report key ending in `__lam1` means the trained LoRA
was read at adapter multiplier `1.0`. It is unrelated to the training plan's
preservation coefficient `.1`; both facts are correctly bound in the
artifacts.

The treatment is also not compute-matched: its fit took 2,458.9 seconds versus
1,227.3 seconds for control, plus an 18.8-second frozen-OFF cache. That is an
expected cost of the extra differentiable anchor forward, not evidence for or
against the scientific endpoint.

## Claim boundary and next decision

The supportable conclusion is:

> On one synthetic old-frame bank and one optimizer seed, a `.1` frozen-OFF
> full-vocabulary KL objective reduced completion-frame spill from `.416` to
> `.0367`, but erased measurable completion-frame acquisition and collapsed
> frame colour-candidate mass, while leaving the older explicit-question
> rewrite habit broad. It did not produce a selective writer.

This does not support selective semantic binding, final all-anchor
preservation, personal action-outcome learning, THINK/DREAM/SLEEP, parenting,
retention across writes, clean lineage, OEL/SDFT reproduction, deployment
behavior, numeric generality, or mechanism freeze. Per the prospective stop
rule, do not automatically sweep more coefficients. Semantic W0 remains the
decisive writer gate.

## Evidence and reducer

- `research_notes/analysis/2026-09-12_preservation_pair_result_blind_watcher_plan.md`
- `research_notes/analysis/preservation_pair_reducer.py`
- `research_notes/astra_memos/receipts_20260912/astra_preservation_control_terminal_20260912.tgz`
- `research_notes/astra_memos/receipts_20260912/astra_preservation_positive_terminal_20260912.tgz`
- `research_notes/astra_memos/receipts_20260912/astra_preservation_pair_analysis_20260912.json`
- `research_notes/astra_memos/ASTRA_MEMORY_PRESERVATION_COMPARISON_2026-09-12.md`
- `research_notes/astra_memos/ASTRA_PRESERVATION_TERMINAL_2026-09-12.md`

