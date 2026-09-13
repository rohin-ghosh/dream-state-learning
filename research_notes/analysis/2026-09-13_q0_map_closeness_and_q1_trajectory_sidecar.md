# Q0 map closeness: the maps are maximally different; the early update can still be common-mode

**Date:** 2026-09-13 UTC  
**Role:** fresh independent design and evidence review  
**Scope:** research-note only. I did not edit builder code, inspect or alter a
live job, run a model/tokenizer, train an adapter, or use a GPU.

## Decision in one paragraph

Rohin's intuition identifies a real learning dynamic, but not because the two
Q0 maps are close. `P_AUTH` and `P_DERANGED` disagree on **every** exact and
held case; their binary targets have correlation `-1`, the maximum possible
functional separation. They merely use the same two action tokens and the
same inputs. More importantly, they are trained in **separate fresh
adapters**, so one map cannot literally overwrite or blend with the other.
What can happen—and Q0's first-step evidence strongly predicts—is that each
adapter first learns a shared, prompt-insensitive correction to the base
model's very large preference for `-mem2reg`, before it learns which opaque
tool/mode combinations require which action. The cheapest decisive diagnostic
is therefore not another fitted arm. Register a read-only
`Q1_MAP_DYNAMICS_SIDECAR_v1` over the already planned Q1/OFF margins at
updates `0, 1, 32, 64, 128`, decompose every balanced quartet into constant,
tool-orientation, mode, and XOR components, and reveal it only after all three
Q1 roots are terminal. This costs **zero extra fits, zero extra model
forwards, and zero GPU-hours**, does not alter Q1's primary denominator or
gates, and exactly tells us whether common output motion precedes keyed XOR
separation.

## 1. “Close” has three different meanings here

Let target bit `0` mean `-mem2reg`, target bit `1` mean `-gvn`, and let
`o(tool)` be the frozen opaque-tool orientation. Q0 uses

```text
AUTH(tool, mode)     = o(tool) XOR mode
DERANGED(tool, mode) = 1 XOR AUTH(tool, mode).
```

These maps have three distinct distance descriptions:

| object compared | Q0 value | interpretation |
|---|---:|---|
| target-map agreement | `0/128` exact; `0/64` held | The functions are maximally far in Hamming distance. |
| signed target correlation | `-1` | One target vector is exactly the negative of the other. |
| action-vocabulary overlap | Jaccard `1` | Both maps emit the same two actions, with opposite assignments. |

The first two rule out the literal claim that AUTH and DERANGED are nearby
functions like two partly overlapping lookup tables. The third is the useful
part of Rohin's idea: both tasks live on the same output surface. A learner can
move that surface globally before it conditions the move on the inputs.

That is **within-fit common-mode learning**, not cross-map forgetting. AUTH
and DERANGED never coexist in one adapter: both begin at matched initialization
and then train independently. Disjointing the output vocabularies *between*
the two independent fits cannot remove interference that is not present.

This distinction also disposes the “less-overlapping map” proposal for Q1.
The existing maps already have zero output-label agreement. Making them agree
on some cases would make their target functions *closer*, not farther, and
would weaken the complementary-map falsifier. A real map-overlap experiment
would have to train multiple selector-tagged maps in one adapter. That is a
coexistence/interference experiment, not an audit of Q0 or Q1.

## 2. Why common-mode motion is nevertheless the leading first-step explanation

On Q0's sealed first fit-canary quartet, the dropout-off margins before
training were

```text
d = z_mem2reg - z_gvn
  = [5.5377, 7.5417, 5.2742, 5.4192].
```

Thus the base model strongly chooses `-mem2reg` on all four contexts. For the
pairwise loss `softplus(-s*d)`, where `s=+1` for `-mem2reg` and `-1` for
`-gvn`, the derivative magnitudes were:

```text
AUTH:     [.00392, .99947, .99490, .00441]
DERANGED: [.99608, .00053, .00510, .99559]
UNARY:    [.00392, .00053, .99490, .99559].
```

Almost all first-update weight therefore comes from whichever two rows ask
the strongly `mem2reg`-biased base to emit `gvn`. Within a shared network, a
large correction learned from those hard rows can lower the `mem2reg-gvn`
margin on the easy rows too. That helps the two initially wrong rows and harms
some initially correct rows—the observed/projection `2/4`-like pattern.

This is ordinary hard-example prioritization under a strong output prior. It
does not require:

- map overlap;
- bad target counts;
- a zero gradient;
- opaque-action impossibility;
- insufficient rank; or
- a corpus label error.

The existing material audit supports this reading:

- AUTH and DERANGED each have `64/64` exact target balance;
- every optimizer quartet has `2/2` action balance and contains both modes
  for two opposite-orientation tools;
- the maps use byte-identical target-free prefixes and schedules within a
  root;
- all `296` decision prefixes are distinct across the registered panels;
- the divergent native branch IDs are consistently `10536/21404`; and
- the first-step audit found nonzero gradients in every quartet.

Across the entire 128-row exact surface, not just the canary, the initial
margin was positive on `128/128` rows (range `1.875..9.0`, mean `5.5098`).
Mean derivative weight was `0.01049` on the 64 already-favoured `mem2reg`
targets versus `0.98941` on the 64 `gvn` targets. Contemporary OFF then
generated `mem2reg` on `127/128` exact and `63/64` held cases. The common-mode
pressure is therefore a full-surface property, not an anecdote from one
quartet.

The legal branch-token mass was already essentially one (`min .9999518`,
`median .9999956`, `max .9999992`), so full-vocabulary versus pairwise CE has
almost identical initialization gradients. The problem is not that the
actions are hidden behind the rest of the vocabulary.

There is one important corpus-semantics qualification. Q0 does **not** train a
full tool-call trajectory. It forwards the natural response through the
common prefix `ACT: -` and trains the first divergent action token. The base
must supply the remaining action spelling and termination during strict
generation. This is a clean test of conditional branch selection, but a Q0
miss cannot be paraphrased as “full tool-call SFT failed.” The unary fit also
stopped after one such decision-token update; it did not receive a realistic
full-dose tool-call write.

Finally, SEQ-120 is relevant context rather than a substitute result. Under a
different full-response authored recipe, separate AUTH and DERANGED adapters
emitted their own complementary PROSPECT maps `32/32` each and never emitted
the opposite. That establishes that this base/LoRA family is not generally
incapable of complementary conditional policies. It does not qualify Q1,
because its response surface, objective, dose, locality result, and data are
different.

## 3. The zero-extra-fit prospective diagnostic

### Name and independence

Register the analysis as:

```text
Q1_MAP_DYNAMICS_SIDECAR_v1
```

It is a diagnostic sibling of `Q1_DELAYED_DIRECT`, never a primary arm, gate,
checkpoint selector, stopping signal, or way to rescue a failed Q1 root. Q1's
three roots, two fits per root, final thresholds, denominator, and labels stay
unchanged.

The sidecar consumes only artifacts Q1 already plans to create:

1. contemporary OFF margins at update `0`;
2. each arm's before/after margins on the scheduled canary quartet at update
   `1`;
3. the complete exact-panel margin reads at updates `32`, `64`, and `128`;
4. the paired AUTH/DERANGED adapter snapshots for an optional CPU-only
   parameter-delta cosine; and
5. ordinary training-loss traces.

If the final Q1 implementation also produces the proposed `4/8/16` margin
reads, the sidecar may report them under the same equations. It must not add
new calls merely to fill them. The Q1 design prose currently mentions
`1/4/8/16/32/64/128`, while its resource arithmetic explicitly pays only for
full intermediate reads at `32/64`; this sidecar deliberately relies only on
the unambiguous `0/1/32/64/128` intersection.

Run the reducer only after all three prospectively allocated Q1 roots are
terminal or irrecoverably integrity-incomplete. Do not inspect root 0's
sidecar and use it to change roots 1/2. A runtime-incomplete root remains
missing, not zero and not replaceable.

### Exact functional decomposition

For each prompt `i`, arm `a`, and checkpoint `t`, define

```text
d[a,i,t]     = z_mem2reg - z_gvn
delta[a,i,t] = d[a,i,t] - d[OFF,i]
y[i]         = +1 if AUTH targets mem2reg, -1 if AUTH targets gvn.
```

DERANGED's signed target is `-y[i]`. For every scheduled quartet, order rows
as `(orientation0,mode0)`, `(orientation0,mode1)`,
`(orientation1,mode0)`, `(orientation1,mode1)`. Apply the four-point Walsh
decomposition to `delta`:

```text
C = (d00 + d01 + d10 + d11) / 4       # constant/global action shift
O = (d00 + d01 - d10 - d11) / 4       # tool-orientation component
M = (d00 - d01 + d10 - d11) / 4       # mode component
X = (d00 - d01 - d10 + d11) / 4       # intended XOR component
```

Here the `d` terms denote `delta` for brevity. The map-aligned component is
`+X` for AUTH and `-X` for DERANGED. This basis is exact and exhaustive for a
balanced four-row quartet: no movement can be ambiguously counted as both
global and XOR. `O` and `M` expose the two cheap partial policies that the
quartet was designed to reject.

At update 1, report all four coefficients on the actual canary quartet. At
updates 32/64/128, compute them on all 32 scheduled quartets and report the
full vector, mean, median, interquartile range, and sign counts—never only an
average.

Across the matched arms, additionally compute per quartet:

```text
C_shared = (C_AUTH + C_DERANGED) / 2
X_split  = (X_AUTH - X_DERANGED) / 2
```

`C_shared` is motion both independent writers make in the same global output
direction. `X_split` is separation in the direction their complementary maps
require. A prompt-independent shift can increase `C_shared` but contributes
exactly zero to `X_split` under the balanced surface.

Also report, at every available checkpoint:

- own-map signed-margin mean and median for each arm;
- count of rows with correct signed branch choice;
- count of matched prompts on which both adapters choose their own opposite
  branch;
- cosine between the two arms' 128-dimensional `delta` margin vectors
  (positive means functionally common motion; negative means complementary
  divergence);
- `q` and legal branch mass `M` where already present; and
- pairwise training loss, with no loss threshold promoted into an endpoint
  pass.

The optional flattened adapter-delta cosine
`cos(theta_AUTH(t)-theta_0, theta_DERANGED(t)-theta_0)` is CPU-only and costs
no model call. It is supporting evidence only: LoRA factorization makes
function-space margin trajectories more interpretable than raw parameter
angles.

### Prospective classification

Classify each root, without changing Q1's scientific label:

- **`COMMON_THEN_KEYED`**: on the update-1 canary, both arm-global
  coefficients have the same sign and each arm has
  `|C| > max(|O|,|M|,|X|)` above the registered numerical bounds; at some
  later fixed checkpoint, both aligned XOR medians have the correct sign,
  `median(X_split)>abs(median(C_shared))`, and both arms choose their own map
  on at least `96/128` exact rows.
- **`KEYED_AT_FIRST_UPDATE`**: both arms' aligned `X` already dominate their
  other three coefficients at update 1.
- **`COMMON_WITHOUT_KEYING_BY_128`**: the update-1 common condition holds but
  no later checkpoint meets the keyed condition.
- **`MODE_OR_TOOL_SHORTCUT_TRAJECTORY`**: `O` or `M`, rather than `C` or the
  aligned `X`, dominates and the final per-key surface is correspondingly
  uneven.
- **`MIXED_OR_UNRESOLVED_DYNAMICS`**: every other complete pattern.

Call the common-first pattern replicated only at `3/3` roots, directional at
`2/3`, and unsupported at `0/3` or `1/3`. These are deterministic diagnostic
classifications, not IID p-values. Q1 itself still requires its complete
noncompensatory final gates on all three roots.

This test directly distinguishes the main explanations:

| trajectory | inference |
|---|---|
| common first, then XOR | Rohin's learning-order intuition is right; “map closeness” is the wrong causal name. |
| XOR present at update 1 | the original one-step miss came from cross-row spill/dropout geometry, not delayed keyed formation. |
| common persists, XOR never forms | the direct writer remains a global-bias learner under this recipe. |
| XOR forms but strict generation fails | extraction/suffix/interface, not map separation, is the bottleneck. |
| XOR and generation pass but locality fails | routing/scope, not map distance, is the bottleneck. |

## 4. Tokenization and corpus controls that must accompany the sidecar

Q1's primary material checks already do most of this work. The sidecar report
should bind and expose, per root:

1. the maximal common-prefix IDs and hash for every prompt;
2. the two divergent branch IDs and their decoded bytes;
3. complete candidate token sequences and lengths (they need not be equal,
   because the loss trains only the first divergence, but strict generation
   may care);
4. OFF distributions of raw `d`, normalized within-pair choice `q`, and legal
   mass `M`, split by target, mode, orientation, tool, and template;
5. prompt token lengths split over those same factors;
6. exact `64/64` class balance, all 32 `2/2` quartets, and byte-identical
   training order across AUTH/DERANGED within root; and
7. proof that arm name, target, map, replica, and seed do not appear in the
   model-visible prefix.

These distinguish an input-length or token-prior nuisance from a mislabeled
map. New Q1 opaque roots change input tokenization; they do not change the
native output branch pair. Report root/optimizer-seed confounding rather than
pretending three roots isolate either source.

I found no material-level reason to call Q0's complementary maps malformed.
The map formula, balance, token-common prefix, action IDs, and raw gradients
were all reconstructed independently. The scientific design error was the
efficacy demand placed on the first optimizer update, not an observed target
swap or missing corpus row.

## 5. Why not add disjoint-vocabulary or partial-overlap arms now?

Do **not** run them before or in parallel with the three Q1 primary roots.

### Disjoint vocabulary between AUTH and DERANGED

Because the two maps are fitted into independent adapters, making AUTH emit
tokens `{A,B}` and DERANGED emit `{C,D}` removes no shared learned state. It
instead changes:

- pretrained token priors;
- output-head geometry;
- action semantics;
- continuation token lengths;
- native parser/tool validity; and
- possibly legal-token mass.

Any speed difference would be a codebook/token effect, not evidence that the
original maps blended. It would also weaken the matched-complement causal
control, whose strength comes from identical inputs and output vocabulary.

### Less-overlapping target maps

AUTH/DERANGED already disagree everywhere. A partial permutation would be
closer in Hamming distance and permit a shared policy to score above chance,
making the qualification weaker. Training two map selectors together at a
distance sweep `{0,.5,1}` could study multi-policy coexistence, but that is a
new one-adapter task and is irrelevant to why two separately trained Q1
states move as they do.

### Within-root extra fitted arms

Extra independent arms on a Q1 root do not contaminate the Q1 adapter states,
but inspecting them alongside Q1 expands the prospective family and makes a
simple six-fit endpoint needlessly harder to interpret. The functional
trajectory sidecar already asks the intended question exactly.

## 6. One optional post-Q1 codebook diagnostic, only if triggered

If and only if all three Q1 roots finish full dose, reduce training loss, and
end `COMMON_WITHOUT_KEYING_BY_128` (rather than an interface/locality failure),
a separate excluded-root diagnostic may ask whether the **native output
codebook** is unusually hard. Name it prospectively
`Q1_CODEBOOK_SWAP_DIAGNOSTIC_v1`; never call it a Q1 repair or confirmation.

Use the same frozen inputs, map equations, pairwise objective, rank, optimizer,
schedule, and 128-update dose. The original Q1 root supplies the immutable
`AUTH_AB/DERANGED_AB` reference. Add exactly two fresh fits on one excluded
root, `AUTH_CD/DERANGED_CD`, using a disjoint candidate pair selected before
fit outcomes by a fixed OFF-only matching algorithm from a predeclared set of
native legal actions:

- both alternatives must share the same natural `ACT: -` prefix and diverge
  at one unambiguous token position;
- all four first branch IDs must be distinct;
- the new pair must be parser-valid and actually executable;
- selection minimizes a predeclared distance from AB in OFF median absolute
  margin, legal pair mass, complete candidate length, and target-count
  balance; and
- failure to meet fixed matching tolerances is `NO_MATCHED_CODEBOOK`, not
  permission to try pairs until one learns.

Read the same `C/O/M/X`, own-map, complement, and locality trajectories. The
comparison can establish only that one output codebook acquires faster under
the fixed recipe. It still cannot show cross-map blending, because every fit
is independent.

Cost: exactly two additional fits, `256` updates and `1,024` natural training
row forwards, plus matched reads; conservative ceiling **3 A40-hours** (the
same two-fit per-root ceiling used by Q1). Run one excluded root only and stop.
No replication, rank/LR/dose follow-up, Q1 relabeling, M promotion, or
paper-level mechanism claim follows from it. If Q1 reaches keyed XOR, fails
only strict generation/locality, or has mixed root patterns, do not run this
diagnostic.

## 7. Timing, cost, and stop

1. **Before Q1 launch:** bind this analysis version, equations, row ordering,
   and labels. This requires no change to Q1 training or primary gates.
2. **During Q1:** collect only the already contracted artifacts. Do not read
   sidecar outcomes, branch on them, or add calls.
3. **After all three roots terminate:** run one CPU reduction, publish every
   root, and stop. Missing artifacts yield `SIDECAR_INCOMPLETE`; they do not
   trigger a rerun.
4. **Additional cost:** `0` fits, `0` optimizer updates, `0` model forwards,
   `0` generations, `0` GPU-hours. CPU reduction and plotting only.
5. **Optional codebook cost:** at most two fits / `3 A40-hours`, after Q1 and
   only under the narrow trigger in section 6.

The sidecar must never determine whether Q1 passes. Its value is explanatory:
it converts “maybe the maps are too close” into a basis-decomposed trajectory
whose global, unary, and XOR parts cannot hide inside one mean.

## Evidence inspected

- `research_notes/analysis/2026-09-13_q1_delayed_direct_writer_and_e0r_parallel_decision.md`;
- `research_notes/analysis/2026-09-13_q0_root1_attempt2_terminal_independent_audit.md`;
- `research_notes/analysis/2026-09-13_q0_attempt2_corpus_and_canary_forensic.md`;
- `research_notes/astra_memos/receipts_20260912/astra_q0_revision_design_20260913.md`;
- `research_notes/analysis/2026-09-12_pairwise_binding_falsifier_adjudication.md`;
- `research_notes/analysis/2026-09-12_q0_pairwise_falsifier_mathematical_redteam.md`;
- `research_notes/analysis/2026-09-13_birth_terminal_raw_audit.md` (SEQ-120);
- `gpu/astra_pairwise_q0.py` (read-only source audit);
- `research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, message 32; and
- `research_loop/COORDINATION.md` through the message-32 relay.

Only this memo was written. **No code/model/tokenizer/GPU work was performed.**
