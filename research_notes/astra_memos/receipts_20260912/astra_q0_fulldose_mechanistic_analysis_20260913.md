# Q0 full-dose mechanistic analysis — R0/R2 only

2026-09-13. **Analysis/proposal only; EDITSTOP.** No source, manuscript, native
runtime, model, GPU, network, Git or other agent's artifacts were changed. This
is not an independent native/tensor replay: I parsed Main's two final replay
outputs, checked their file hashes and recomputed the descriptive arithmetic.
L2 acceptance/operations remain separate and need not wait on this proposal.

## Bottom line

Both supplied completed instances are `Q0_V2_FULL_DOSE_ENDPOINT_FAIL`, not
runtime aborts: each attempted two fits and completed256updates/1,024training
row forwards, with both maps missing their measured first-step canary. The
full128-update dose produces substantial parameter-mediated behavioral change
but **little class-balanced forced-prefix discrimination, poor conditional-key
coverage, and large OFF-relative spill**. This rules out the narrow explanation
that these two endpoint failures merely reflect v1's one-update efficacy stop.
It does not identify an inherent LoRA capacity limit or prove a particular
optimization/representation mechanism.

The highest-information next existing-mechanism contrast is a **separate,
prospectively fixed, matched full-dose `P_UNARY_TOOL` versus `P_AUTH` diagnostic**:
remove the mode-dependent label flip while holding the writer, dose and opaque
IDs fixed. Do not increase dose, hunt a checkpoint, or relabel these endpoints.

## 1. What the available OFF→32→64→128 curves actually contain

The supplied JSONs expose exact/held class mean and median signed margins at
32,64,128, but **not OFF class margin means/medians, OFF exact/held accuracy,
32/64 strict generation accuracy, or intermediate per-key trajectories**. They
do expose128-minus-OFF median signed gains and OFF→128 locality transitions.
Consequently, a numeric four-timepoint *accuracy* curve cannot be reconstructed
from these files. Do not substitute historical v1 OFF, infer50% OFF merely from
balanced labels, or subtract a median gain from a final median to invent an
OFF median. Those medians need not concern the same ranked observations.

Let `d=z_mem−z_gv`. Each pair below is the mean signed margin for the target-MEM
and target-GVN classes, respectively, in recorded logit units. Exact classes
have64rows each; held classes32each. Negative means are retained, not rounded
into success. Class labels refer to each arm's own registered map.

| Root / arm / panel | Update32 | Update64 | Update128 |
|---|---:|---:|---:|
| R0 AUTH exact | +1.130859, −1.121094 | −0.169922, +0.279297 | +0.365234, −0.261719 |
| R0 DERANGED exact | +0.642578, −0.679688 | +0.056641, −0.082031 | −0.255859, +0.310547 |
| R2 AUTH exact | +0.937500, −1.007812 | −0.605469, +0.576172 | +0.078125, +0.083984 |
| R2 DERANGED exact | +0.845703, −0.828125 | −0.402344, +0.433594 | −0.101562, +0.103516 |
| R0 AUTH held | −0.218750, +0.343750 | −1.105469, +1.234375 | −0.363281, +0.386719 |
| R0 DERANGED held | −0.750000, +0.695313 | −0.863281, +0.871094 | −1.046875, +0.921875 |
| R2 AUTH held | −0.882813, +0.925781 | −1.609375, +1.757813 | −0.722656, +0.753906 |
| R2 DERANGED held | −0.855469, +0.812500 | −1.531250, +1.433594 | −0.910156, +0.902344 |

A useful *descriptive*, nongating decomposition is
`S=(mean_signed_MEM+mean_signed_GVN)/2`, the balanced signed margin, and
`B=(mean_signed_MEM−mean_signed_GVN)/2=mean(d)`, the overall branch bias.
A constant branch preference can make B large but has S=0 on this balanced
panel. S is not a classifier accuracy, a new threshold, or evidence that every
row has zero information.

- Across all12exact arm/checkpoint cells, S ranges only **−0.035156 to
  +0.081055**. At128 it is R0 AUTH+.051758/DERANGED+.027344 and R2
  AUTH+.081055/DERANGED+.000977. Held S spans **−.062500 to+.074219**;
  its128values are+.011719,−.062500,+.015625,−.003906 in that same order.
- Exact branch bias, rather than both-class improvement, dominates the visible
  trajectory: AUTH B is R0 `+1.126→−.225→+.313` and R2
  `+.973→−.591→−.003`. This is not a monotonic class-balanced acquisition curve.
  Held B remains GVN-favoring in every cell, reaching about−1.68 at R2 AUTH64.
- R2 AUTH128 has two slightly positive class means but **both class medians
  are zero**. R2 DERANGED128 also has both medians zero. Do not turn positive
  mean tails or signed zero into broad acquisition.
- OFF anchoring is available through the final gain distributions: median
  signed exact gains are R0 AUTH `(−5.3125,+5.2500)`, R0 DERANGED
  `(−5.6875,+5.8750)`, R2 AUTH `(−5.4375,+5.3750)`, and R2 DERANGED
  `(−5.5000,+5.6250)`. Both maps in both roots move strongly away from the
  MEM-favoring direction, rather than improving both target classes. Held
  gains show the same sign pattern, with magnitudes3.75–4.5625. This is
  consistent with reducing a broad pre-existing branch preference while
  failing to establish reliable key-conditioned separation; it is not a
  reconstruction of the missing OFF distribution.

## 2. Strict endpoint outcomes: failures are predominantly wrong legal actions

| Root / arm | Exact correct | Exact class recalls MEM/GVN | Exact covered keys | Held correct | Held class recalls MEM/GVN | Held covered keys |
|---|---:|---:|---:|---:|---:|---:|
| R0 AUTH | 71/128 (55.47%) | 60/64;11/64 | 7/16 | 37/64 (57.81%) | 15/32;22/32 | 9/16 |
| R0 DERANGED | 70/128 (54.69%) | 30/64;40/64 | 1/16 | 31/64 (48.44%) | 4/32;27/32 | 8/16 |
| R2 AUTH | 65/128 (50.78%) | 46/64;19/64 | 3/16 | 31/64 (48.44%) | 7/32;24/32 | 8/16 |
| R2 DERANGED | 72/128 (56.25%) | 45/64;27/64 | 1/16 | 32/64 (50.00%) | 4/32;28/32 | 8/16 |

Preserved exact thresholds are116/128 correct, each class56/64,14/16keys at
7/8correct, and positive median OFF-relative gain in both classes. Held
thresholds are52/64correct, each class24/32,12/16keys with **positive median
signed margin**; held coverage is not a count of keys with3/4correct generation.
All four exact and held acquisition conjunctions fail. A recorded held
`gain_gate=true` is not evidence that both held gain medians are positive:
the held contract has no separate both-class ON-minus-OFF gain predicate.

All four cells nevertheless have exact validity128/128, held validity64/64,
zero multiple actions, and copy8/8. Thus the primary failure is not generic
format collapse or inability to spell/copy these action names. Raw branch bias
is substantial: exact MEM/GVN outputs are R0 AUTH113/15, DERANGED54/74;
R2 AUTH91/37, DERANGED82/46. Held outputs are25/39,9/55,15/49,8/56.
These counts are derived from legal binary outputs and per-class recalls.
Forced-prefix margins and ordinary-boundary generation are different surfaces;
their discrepancy cannot itself establish an extraction-only failure, because
forced-prefix acquisition already lacks strong class-balanced separation.

### Per-key detail retained, not hidden in the aggregate

Each entry below is **exact-correct count / held-correct count**, with respective
denominators8and4; it is not one ratio. Coordinate keys are within-instance
positions, not identical opaque IDs across R0/R2. AUTH target is
`orientation[slot] XOR mode`, with orientation `(0,1,1,0,1,0,0,1)`;
DERANGED has the opposite target at every coordinate.

| Slot,mode | AUTH target | R0 AUTH E/H | R0 DERANGED E/H | R2 AUTH E/H | R2 DERANGED E/H |
|---|---|---:|---:|---:|---:|
| 0,0 | MEM | 8/1 | 6/4 | 4/0 | 4/4 |
| 0,1 | GVN | 0/2 | 5/1 | 2/1 | 6/1 |
| 1,0 | GVN | 4/4 | 3/0 | 2/4 | 6/0 |
| 1,1 | MEM | 8/3 | 5/3 | 8/2 | 3/4 |
| 2,0 | GVN | 2/3 | 1/0 | 4/4 | 6/0 |
| 2,1 | MEM | 8/3 | 5/3 | 5/2 | 1/1 |
| 3,0 | MEM | 8/1 | 6/4 | 5/0 | 5/4 |
| 3,1 | GVN | 0/2 | 5/1 | 2/2 | 7/1 |
| 4,0 | GVN | 0/4 | 4/0 | 5/4 | 4/0 |
| 4,1 | MEM | 7/2 | 4/3 | 7/1 | 4/3 |
| 5,0 | MEM | 5/1 | 8/4 | 6/0 | 4/4 |
| 5,1 | GVN | 2/2 | 3/1 | 0/2 | 6/1 |
| 6,0 | MEM | 8/3 | 2/3 | 4/1 | 4/4 |
| 6,1 | GVN | 0/1 | 5/1 | 2/3 | 6/1 |
| 7,0 | GVN | 3/4 | 4/0 | 2/4 | 4/0 |
| 7,1 | MEM | 8/1 | 4/3 | 7/1 | 2/4 |

Every high-coverage exact AUTH key is MEM-targeted: all7in R0 and all3in R2.
**Zero of8IDs in any of the four fitted cells has both modes at7/8correct.**
R0 AUTH's perfect exact key0,0 becomes1/4held; key4,0 is0/8exact but4/4held.
Analogous opposite-direction examples appear in R2. These are strong reasons
not to call held failures merely a small decrement from a reliably stored map.
Some rows/keys are correct, but no broadly acquired conditional map is evident.

### Opposite-map evidence is weak, not merely a low single-arm score

Correct complementary pairs are R0 **39/128exact,10/64held**, R2
**28/128exact,4/64held**, versus112/128and48/64requirements. Since every output
here is a legal binary action and target maps are complements, the two adapters
give the **same action** on63/128exact and48/64held prompts in R0, and81/128exact
and55/64held in R2. Derivation: both-wrong=`N−AUTH_correct−DERANGED_correct+
both_correct`; same-action=`N−both_correct−both_wrong`.
There are also26/19wrong-polarity complementary exact pairs in R0/R2 and6/5held;
any opposite output is therefore not equivalent to correct map binding.

## 3. Locality rejects a 'small useful write with otherwise stable behavior'

Mean itemwise absolute within-pair probability changes, independently gated
at.05perfamily, are:

| Root / arm | Missing8 | Unsupported8 | Neighbour16 | Wrong-root64 | Identity changes, all96 |
|---|---:|---:|---:|---:|---:|
| R0 AUTH | .280765 | .232046 | .402644 | .499363 | 41 |
| R0 DERANGED | .414285 | .374865 | .539336 | .578375 | 60 |
| R2 AUTH | .391707 | .358282 | .470958 | .579951 | 49 |
| R2 DERANGED | .444482 | .372670 | .509800 | .612019 | 55 |

All16family means fail; all16maximum-|delta-q| tails also exceed.10. Small
families can preserve every raw action identity yet still fail probability
locality, as R0 AUTH illustrates. Wrong-root action flips are41,53,44,50 of64,
against the cap3. R0 DERANGED additionally flips7/16neighbours; each R2 arm
flips2/8missing and3/16neighbours. All these are MEM→GVN changes, not validity
loss. OFF wrong-root actions can be recovered exactly from the transition
tables: R0 has63MEM/1GVN and R2 has64MEM. This is a locality-only OFF fact, not
an estimate of missing exact/held OFF accuracy.

Legal-branch-token-mass changes are small: the largest reported itemwise
|delta-M| across these cells/families is **.0000385944**, far below.10. All
validity-change counts are zero. Thus the locality failure is choice/identity
redistribution, not the reported absolute-M or legality predicates. These are
**mass deltas**, not absolute mass measurements or probabilities of full strings.
Wrong-root mutually opposite AUTH/DERANGED outputs are14/64(R0) and8/64(R2),
also over the cap3. The same global shift that helps some disfavored-class
examples is affecting supposedly protected inputs.

## 4. Mechanistic constraints, with causal limits

The stored first-quartet signed-gradient Gram matrices have large nonzero row
norms:111.1–129.5(R0),112.4–154.7(R2). Four of six pairwise cosines are negative:
approximately−.896to−.968(R0),−.769to−.945(R2); two are positive in each.
The norm of their *unweighted* average is9.84094versus118.70399mean row norm
in R0 (8.29%), and18.02301versus130.99133in R2 (13.76%). These are computed
from `G_ij=<s_i grad(d_i),s_j grad(d_j)>`, not a finding of zero gradients.
Actual loss gradients use their loss weights/dropout and AdamW transformation;
the canary uses a separate dropout-off FP64 surface. This descriptive
interference signature cannot identify the actual update as the unweighted
average or establish cancellation throughout128steps.

First-step projection passes are2/4for all four fits; observed signed-change
passes are R0 AUTH1/4,DERANGED3/4 and R2 AUTH3/4,DERANGED1/4. All fits nonetheless
completed under the prospective full-dose policy. Finite unfavorable directions
and final failure coexist; neither zero tangent nor first-step correctness is
a substitute for measuring final acquisition.

Best constrained diagnosis: **this fixed pairwise writer mostly changes broad
branch preferences, with inadequate robust opaque-ID×mode discrimination and
poor locality**. Candidate causes remain difficulty forming/accessing the
conditional address, loss-weighted/shared-gradient interference, and the
forced-prefix-versus-generated readout boundary. The data do not isolate one.
They do not support a merely formatting-only failure, a pure held-only transfer
failure after successful acquisition, no learning/no parameter effect, generic
LoRA impossibility, or an inference about parenting/H1/H2.

## 5. ONE prospective follow-up: conditional-demand ablation at fixed dose

**Design, not executed evidence:** one new output-blind namespace/learner-seed
allocation, fixed by Main before outputs, with contemporary OFF and two cold,
initial-byte/RNG-matched fits: existing `P_AUTH` versus existing
`P_UNARY_TOOL`. Unary retains the same opaque IDs, visible modes, wrappers,
branch vocabulary and balanced quartet construction but uses the closed
mode-independent per-ID label rule. Keep rank8/alpha16/dropout.05/LR3e-5,
P objective,128updates/four sweeps, optimizer, tokenization, generation,
32/64/128diagnostic timing and final128decision fixed. No rank/rate/objective
change, bigger dose, early efficacy selection or retry. The comparison removes
conditional mode switching; it also deliberately reduces the map's effective
complexity, so it is not a pure neural-feature intervention.

Why this contrast first: even exact XOR acquisition and class/key coverage fail,
so asking whether this **same writer can acquire a simpler arbitrary opaque-ID
map at full dose** separates useful hypotheses without changing its loss or
capacity. The old one-update unary stop did not answer that question. Use the
contemporary P_AUTH arm rather than treating these historically completed
R0/R2 results as a randomized control or choosing whichever root looked easiest.

**Decision rule:** inherit the existing unary diagnostic thresholds—not a newly
tuned accuracy cutoff: exact≥116/128, each exact class≥56/64, held≥52/64, each
held class≥24/32, and≥7/8tools at≥14/16exact correctness. Retain strict
interface/copy and all OFF-relative locality measurements separately and report
every failed condition. Use the unchanged applicable P_AUTH acquisition gates.

- Unary meets its diagnostic conjunction while matched AUTH fails exact
  acquisition: `UNARY_TOOL_PASS_XOR_FAIL` supports an ID×mode/conditional-demand
  bottleneck **in that instance/recipe**, not a proof of a unique internal cause.
  If unary spills, say it acquires the simpler map without qualifying locality.
- Unary exact acquisition also fails: the obstacle is not demonstrably specific
  to XOR; retain `OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE`, with opacity/address
  access and objective/optimization still unresolved—not 'LoRA cannot learn'.
- Unary exact succeeds but held/other diagnostic predicates fail: incomplete
  unary acquisition/extraction diagnosis; no unary-pass label or rescue.
- AUTH also succeeds: this selected instance does not reproduce the current
  exact failure; do not select/replace R0/R2 or infer a universal mechanism.

No result qualifies an arbitrary complementary writer: this follow-up has no
new DERANGED arm, and unary cannot replace that qualification. Full-dose-v2
explicitly excluded unary, so Main would need a **separate prospectively
versioned plan** using the existing unary mechanism, not an unlogged third fit,
old-root resume, or claim that the present v2 launcher already accepts this arm.

**Cost ceiling proposal:** one paired instance, two fits,256updates,
1,024training-row forwards; using the same panel schedule,10fresh worker stages,
1,632prefix readouts,888greedy requests,≤28,416generated tokens. Reuse the
existing conservative10,800second/root ceiling including cleanup/durable
publication, plus180seconds separate collection, with six-hour lease margin.
This is≤3controller GPU-hours, not a reservation. The observed R0/R2durable
times were2,024.654/2,033.177seconds (about33.7/33.9minutes) for a same-size
pair; that is context, **not a runtime guarantee for unary**. Main schedules
only after its active critical path permits. No fit or resource request made.

## 6. Denominators, R1 and evidence custody

R0(identifier501,learner1) and R2(identifier503,learner3) are two completed,
namespace/seed-confounded instances. Repeated wrappers over16keys are not
128independent learned associations or IID trials; no pooled p-value or
independent-replica claim follows. Intermediate points are diagnostics, never
best-checkpoint selection. The retained original **R1 abort is separate**;
its planned missing-readout supplement is neither present here nor silently
counted as a third completed primary endpoint. I did not inspect R1 live data
or import any result from L2/birth/perception into this diagnosis.

Inputs and SHA256 checked locally:

| Input | SHA256 |
|---|---|
| `/tmp/astra_q0_R0_controller_replay_20260913.json` | `a2fd4fee7fc51e193534e5af8db4c1b80974e48891488c9cefbe51fbd052ae84` |
| `/tmp/astra_q0_R2_controller_replay_20260913.json` | `e3db8c19cae99a734e40b837c776c73412e5ef2b17e8e11eccd5591f096964b3` |
| `research_notes/astra_memos/ASTRA_Q0_FULLDOSE_PROTOCOL_2026-09-13.md` | `58463922037e8c29b1ce8d5b2cffa3aff3bc1f9b7277ae3ee5600cd2059f353a` |
| `research_notes/astra_memos/receipts_20260912/astra_q0_revision_design_20260913.md` | `287fbd868a662f9a19045a8e207a2073c75f2511ef6630b8ff5a90dc3bd7fac8` |
| `research_notes/astra_memos/receipts_20260912/astra_q0_corpus_task_audit_20260913.md` | `e9ce21135c775110ce2438100a3955d7b8c90aa1b7818cce7469c6f86b9887fc` |
| `research_notes/analysis/2026-09-12_pairwise_binding_falsifier_adjudication.md` | `254655bbeef0723811f44b2bbd166e783fc67b928c1a18e90470487ba73387e4` |
| `research_notes/analysis/2026-09-12_q0_pairwise_falsifier_implementation_closure_v2.md` | `bc4987eb49a89d7246e63540f0305705850f606e8fdcf18cc9ef7f41ed3f96b5` |
| `research_notes/astra_memos/receipts_20260912/astra_q0_missing_readout_recovery_design_20260913.md` | `bdbd7af0652526f2abfcfab90b9957624189e7f7e35da65fad1d04ed0f7d3ade` |

Also consulted the existing historical first-update-stop note only for scope;
none of its baseline numbers substitutes for these new allocations. The input
JSONs identify themselves as `EXACT_NATIVE_RAW_REPLAY`; their embedded report
pins are R0`7e3cd8644ba7643992a2331921ed2b1060593ade2860ff4536acb044e8a7e96b`
and R2`e59900a2ea66f0b04f260a07b2b7e9540b258467893ceaf8e7bf8d6665b87694`.
Those are reported native provenance, not tensor-replay work performed here.

CPU arithmetic assertions passed for both full-dose labels/work counts, every
class/key sum equalling aggregate correct, full validity denominators and the
absence of any dual-mode≥7/8tool. Tables, complementary contingencies and Gram
descriptors were recomputed using Python standard-library JSON/math only.
An initial relative design-memo path was absent; the protocol's relative
`receipts_20260912` reference was resolved under `research_notes/astra_memos`
and its exact bound hash matched. No scientific result was inferred from the
missing path. Only this analysis file was written.

**EDITSTOP.**
