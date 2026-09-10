# ICLR headline resource/statistics attack v1

Date: 2026-09-06

Status: **design-only independent advisory**. This document authorizes no
architecture change, implementation, target enumeration, model call, adapter
fit, GPU use, external access, or scientific claim. Adoption must follow the
complete `AGENTS.md` deliberation, exact-byte human ratification,
implementation/review, and pre-GPU gates. This review made no GPU, model, SSH,
or external call and changed no existing file.

## Verdict

**NO-GO for the unmodified v0 plan as a complete C2--C6 confirmation by
September 16. CONDITIONAL GO for a staged, terminal-heavy C2--C5 design after
an exact call manifest and measured end-to-end canary; C6 must remain off the
critical path.**

The 600-fit confirmation arithmetic in
`20260906_iclr_c2_c6_counterfactual_lifetime_headline_v0.md` is internally
correct, but it is not the experiment total. It omits the complete four-root
spending pilot (another 120 fits under the same surface), three heat canaries,
an unspecified number of development roots, and an underdefined C6 fit count.
Before development, the broad design therefore commits at least **723 C2--C5
fits plus `30D` for `D` full-surface development roots**, not 600. If the stated
96-fit C6 estimate is assumed, the minimum becomes **819 + 30D**. That 96 is
derivable only if parenting has exactly one write cycle, which the protocol
does not say.

More seriously, no exact model-call count or even finite maximum follows from
the document. Source-turn cadence, DREAM opportunity cadence, SELF_CHECK or
admission calls, targets per stratum, operations per target, stochastic
replicates, LEAFE branch counts, development-root count, and parenting-cycle
count are all open. Equal generated-token budgets do not close any of those
counts. A GPU-hour total built on unspecified calls is not auditable.

Twenty paired roots are a reasonable *floor* for one paired primary contrast
only if its root-level standard deviation is small. For a true `0.05` effect,
`n=20` has about 80% sensitivity only when paired-root SD is at most about
`0.076`; a conservative three-comparison simultaneous gate needs SD at most
about `0.064`. The existing v6 lives show exactly the kind of between-life
writer instability that can exceed those bounds. Twenty roots are therefore
not yet “powered”; they are a feasibility-limited design whose sensitivity
must be published. The 12-dyad C6 interaction is weaker still: a true `0.03`
interaction reaches about 80% sensitivity only if the interaction SD is at
most `0.034`.

The best information-per-fit repair is to spend longitudinal fits only on the
proposed recurrent native system. Frozen and active text need curves but no
fits; raw cumulative response distillation, LEAFE, derangement, and the C5
carrier ablations need terminal fits for their registered terminal questions.
That reduces confirmation from 600 to **360 fits at 20 roots**, or permits
**32 paired roots in 576 fits**, still below the original 600-fit confirmation
budget. It preserves C2, terminal C3, longitudinal C4 against the registered
text comparator, and terminal carrier-level C5. It narrows the derangement
claim to the terminal stored carrier; a fully recurrent derangement may be
added only after that cheaper cut is informative.

Even the lean design is calendar-conditional. The only bound node is an
8xA40 lease through September 14, while the proposed schedule places terminal
C5 and C6 on September 14--15. The repository says six A40s were occupied by
v6.1, not that five are durably available. There is no evidence of capacity
after September 14. Lease extension/replacement, exact protocol ratification,
and an end-to-end canary must all close before any claim that September 16 is
feasible.

## Evidence and arithmetic boundary

This audit read the complete headline proposal, `REVIEW_PACK.md`, the v6.1
independent audit and partial follow-up, the relevant `organism_v6` runner,
batching, writer and serving code, `lands/v03r.py`, and `gpu/a40_ssh.sh`.

The following measurements were supplied for this resource review and were
not re-executed here:

- rank-16 legacy cumulative fit elapsed time, measured from `COMPILED` to
  adapter `DONE`: `0:42` at sleep 32, `3:47` at sleep 256, and `9:35` at
  sleep 736;
- a tokenizer audit over 200 v0.3-R sides: mean `5,265.91` rendered tokens
  and `47.53` episodes per component world.

Those measurements are useful anchors, not measurements of the proposed
rank-8 native writer. The proposed corpus, mask, sequence lengths, effective
target-token exposure, optimizer steps, and engine lifecycle differ.

The current repository establishes these additional constraints:

1. `gpu/a40_ssh.sh` describes one 8xA40 worker lease ending September 14.
2. `REVIEW_PACK.md` says v6.1 was running on six A40s with a September 7--8
   ETA. A live audit saw transiently different occupancy, but no durable
   five-GPU reservation exists in the reviewed files.
3. `organism_v6/model_backend.py` creates one eager vLLM engine per life,
   enables LoRA only at engine construction, supports only one addressed
   adapter, ignores the offered seed, and defaults to a 16,384-token engine
   limit.
4. `run_life_v2.py` repeatedly shuts down serving, loads a full Transformers
   base for each fit, then reloads vLLM; it does not provide the proposed
   resident-base, multi-adapter evaluator.
5. The trainers record steps and attended tokens but no elapsed fit time.
   Existing life logs therefore cannot by themselves prove a 3--10 minute
   native-fit SLA.
6. One v6.1 B life performs 32 cumulative fits. Wake alone permits 1,024
   episodes times 16 generated chunks. Batching eight prompts reduces engine
   dispatch overhead, not the number of logical samples or generated tokens.
   The several-day v6.1 ETA is thus evidence that model generation and engine
   churn can dominate a fit-only estimate.
7. The existing v0.3-R component is a CPU fixture with about 46--48 public
   episodes. It is not the proposed source-actor loop or super-life runtime.
   Its prior v1f schedule used 46 WAKE, 22 REACTIVATE, and 16 SLEEP proposal
   opportunities for the seed-0 side, with prospectively paired SELF_CHECK
   companions. That schedule is not adopted by the headline proposal, but it
   shows why “fixed sleep opportunities” needs an integer.

## Correct adapter-fit arithmetic

Let `R` be paired confirmation roots, `S=2` twin sides, `K=4` lifetime cuts,
and `D` the number of development roots.

### Broad v0 confirmation

For each root side:

| trained cell | fits per side | reason |
|---|---:|---|
| `RAW_PERIODIC` | 4 | clean-base cumulative rebuild at every cut |
| `NATIVE_PERIODIC` | 4 | clean-base recurrent rebuild at every cut |
| `DERANGED_PERIODIC` | 4 | matched recurrent rebuild at every cut |
| `LEAFE_FINAL` | 1 | terminal batch fit |
| `EXPANDED_LINKED` | 1 | terminal C5 carrier fit |
| `ATOMS_ONLY` | 1 | terminal C5 carrier fit |
| **total** | **15** | compact linked is the terminal native fit; frozen, text, and adapter-off add no fit |

Thus the stated confirmation is exactly

```text
20 roots * 2 sides * 15 fits = 600 fits.
```

The other committed fits are:

```text
four-root full-surface spending pilot = 4 * 2 * 15 = 120
neutral heat canaries                 = 3
D full-surface development roots      = D * 2 * 15 = 30D
known C2--C5 total before confirmation dispatch = 723 + 30D
```

The heat minimum could be one only under a prospectively ordered stop-at-first-
pass rule. The text instead names all three rates; the safe resource manifest
must reserve three fits and all three behavior panels.

The proposal does not state how many development roots exist or whether each
receives the complete surface. Therefore **`723 + 30D` is a formula, not a
closed total**. For illustration, `D=2` gives 783 C2--C5 fits and `D=4` gives
843.

### C6 does not close to 96 without another assumption

Let `J` be parenting write cycles per dyad. Both parented and matched
unparented practice paths write after each cycle, so practice costs `2J` fits
per dyad. If the two continual deployment cells rebuild at programs 16, 32,
and 48, deployment costs another six fits per dyad. The implied count is

```text
12 dyads * (2J + 6) = 24J + 72 fits.
```

The stated 96 follows only for `J=1`. Five process-vocabulary cycles would be
192 fits. This still excludes heat/development fits for a C6-specific writer
and any failed technical identities. Freeze `J`, deployment write cuts, and
whether a pre-deployment final rebuild is additional before quoting a C6
number.

### Adapter bytes are not the binding uncertainty

Dividing the observed 154 MB rank-64 artifact by eight gives 19.25 MB, so the
proposal's approximate 20 MB rank-8 size and `600 * 20 MB = 12 GB` are sound
as rough decimal storage arithmetic. The broader known minimum of 723 fits is
about 14.5 GB, `819` is about 16.4 GB, and development adds about 0.6 GB per
full-surface root. These exclude tokenizer/config files, transient optimizer
state, retained technical failures, ledgers, prompts, and corpora. The proposed
50 GB evidence allowance is plausible only after measuring actual receipts;
storage is still much less uncertain than generation and engine wall time.

Rank reduction does not divide training time by eight. Forward/backward passes
through the 7B base, sequence length, batch shape, base load, and checkpoint
save remain. The measured legacy rank-16 curve already reaches 9:35 at sleep
736, close to the proposed 10-minute hard gate. A median-across-fits gate would
hide the expensive terminal fits; bind cut-specific median and p95, terminal
fit time, base load, shutdown, save, and serving reload separately.

## Exact source scale and the missing model-call count

At the measured mean of 5,265.91 rendered tokens per v0.3-R component, the
terminal `6C` source requires approximately:

| usable `C` | source tokens per side at `6C` | mean component worlds per side | mean source episodes per side | 20-root/two-side episode floor |
|---:|---:|---:|---:|---:|
| 12,000 | 72,000 | 13.67 | about 650 | about 26,000 |
| 16,000 | 96,000 | 18.23 | about 866 | about 34,600 |

Actual component counts use the first complete era reaching the cut, so the
per-side integer is commonly about 14 or 19 at those means. Root-specific
token lengths, not a rounded global component count, must determine the
frozen boundary.

The last column is already a logical source-model-call floor if every source
episode takes exactly one actor sample. A recurrent actor can take multiple
operations per episode, so the exact source count is

```text
N_source = sum over root and side of source_actor_turns[root, side].
```

The proposal freezes neither `source_actor_turns` nor an operation cap per
episode. It therefore does not close this first count.

The DREAM count is even less specified. If the old seed-0 v1f opportunity
schedule were merely used as an order-of-magnitude illustration, one component
side has 84 proposal opportunities and as many as 84 dispatched companion
checks. Across 20 roots and two sides, 13.67--18.23 component worlds would
produce roughly **45,900--61,300 proposal opportunities per independently
evolving DREAM arm**, or twice that many calls if every companion dispatches.
The headline design may choose a much cheaper cadence, but currently chooses
no cadence at all. Multiplying this by every arm would be wrong unless the
arms genuinely have separate evolving writers; treating one writer output as
shared would also be wrong where the mounted adapter is supposed to change
later DREAM outputs.

An executable manifest must distinguish:

- **logical samples**: one completion for one prompt/item;
- **engine dispatches**: one batched `generate()` invocation, possibly
  containing many samples;
- **generated response tokens**: the main compute/budget quantity;
- input/prefill tokens, which will be large at later super-life cuts; and
- training forward/backward tokens and optimizer steps.

For exact accounting, define:

```text
N_calls = N_source + N_update + N_eval + N_C6

N_update = sum[root,side,cell,cut]
             (dream proposals + dispatched admission checks
              + text-updater calls + LEAFE branch calls + dummy control calls)

N_eval = sum[assigned panel cells]
           targets * stochastic_replicates
           * (free_native_turn_cap + typed_forced_guard_calls)
```

Every term must be an integer or a hash-bound list before dispatch. Generated-
token equality is not a substitute for a call maximum: short malformed calls,
PASS, reflection branches, and early stopping can spend the same token budget
through different numbers of requests and engine startups.

At minimum the manifest must bind:

1. usable `C` and exact tokenizer/rendering bytes;
2. component worlds and source episodes per root side;
3. source operation cap and source actor calls;
4. DREAM opportunities by component/cut/cell and maximum companion calls;
5. updater/reflector branches and outputs per opportunity;
6. targets in forward, backward, twin-pair, mixed-age, bridge-cut, and carrier
   panels;
7. free-native operations, READs, actions, forced calls, and robustness
   replicates per target;
8. fits, rows, labeled tokens, updates, and sequence-length histogram per fit;
9. development roots, parenting cycles, and deployment write cuts; and
10. engine loads, unloads, adapter mounts, processes, and maximum retry
    identities.

Until these are closed, the resource envelope has no defensible maximum.

## Statistical defensibility of 20 paired roots

The root definition is correct: twins, component worlds, targets,
checkpoints, writer samples, and decoding samples are nested measurements, not
replicates. Averaging within stratum and twin pair before the contrast is the
right protection against pseudoreplication.

### Normalize the AUC before applying the SESOI

The four `log2` token coordinates are equally spaced:

```text
log2(0.75C), log2(1.5C), log2(3C), log2(6C),
```

with total x-span 3. The raw trapezoidal area is therefore

```text
AUC_raw = 0.5Y1 + Y2 + Y3 + 0.5Y4,
```

and lies in `[0,3]`, not `[0,1]`. Define

```text
nAUC = AUC_raw / 3
```

before applying the `0.05` normalized-score margin. If raw AUC is retained,
the equivalent margin is `0.15`; a `0.05` raw-AUC margin is only about
`0.0167` in lifetime-average score. The power calculations below assume the
root contrast is on the normalized `[0,1]` scale.

What is missing is a variance design. The four-root spending pilot cannot
estimate a 95% tail or reliably estimate paired-root SD, and selecting whether
to spend from its effect direction makes its effect estimate unsuitable for
power calibration. A 20-cluster percentile bootstrap is also fragile in the
tails. Prefer an exact paired sign-randomization test/interval when its
exchangeability assumptions hold, or a studentized root-level interval with a
published small-sample sensitivity analysis. Do not call checkpoint or target
resampling a cluster bootstrap.

The following is a transparent approximation for C2. It uses a two-sided 95%
root-level critical value (`t_19 = 2.093`) and a normal shift approximation to
paired-test power. A percentile/max-contrast bootstrap will not be more
powerful in a guaranteed way.

| paired-root SD of contrast | standardized effect for `delta=0.05` | approximate power, `n=20` |
|---:|---:|---:|
| 0.050 | 1.00 | 0.99 |
| 0.075 | 0.67 | 0.81 |
| 0.100 | 0.50 | 0.56 |
| 0.125 | 0.40 | 0.38 |
| 0.150 | 0.33 | 0.27 |
| 0.200 | 0.25 | 0.17 |

For 80% power, `n=20` needs SD no greater than about `0.076`; for 90%, no
greater than `0.066`. A conservative three-comparison simultaneous gate uses
an approximate critical value near 2.65, reducing those SD limits to about
`0.064` and `0.057`. At SD `0.075`, approximate power falls from 0.81 for one
contrast to about 0.63 for each Bonferroni-like simultaneous contrast.

This is directly relevant to C3: requiring all three simultaneous lower bounds
above zero means the least favorable comparator controls success. C4's growth
contrast and retention non-inferiority generally have smaller signals and
larger difference-of-difference variance than C2. C5 includes additional
non-inferiority and carrier contrasts. A C2-sized sample is not automatically
powered for those claims.

The v6.1 evidence cannot supply the missing variance estimate, because it has
only three B lives, unseeded generation, a context-policy confound, and a
different gym. It nevertheless warns against assuming small SD: the three
trajectories include a fading effect, a fixed plateau, and a severe writer/
parser collapse. Common randomness removes sampling noise; it does not remove
writer-realization or root-by-treatment heterogeneity.

### The `0.05` SESOI needs a measurement anchor

`0.05` on a nominal `[0,1]` score is not self-justifying. Before target
enumeration, state:

- the natural action-value unit and attainable oracle-minus-floor span;
- how many target outcomes make a root score and its smallest score increment;
- whether `0.05` corresponds to at least one additional twin-pair success,
  meaningful regret reduction, or a predeclared fraction of oracle gain; and
- expected root-level measurement error under repeated common-random panels.

Development variance may justify a *larger* practical margin but should not be
the rationale for the scientific value of the margin. The current C2/C3/C5
rules combine a lower bound above zero with a point estimate at least 0.05.
That is a reasonable screening convention, but it does not establish with 95%
confidence that the effect exceeds the SESOI. Say “statistically positive with
point estimate at least 0.05,” not “at least 0.05 with confidence.”

C4's retention clause and C5's compact-versus-expanded clause need actual
one-sided non-inferiority intervals against `0.05`, not only point differences.
The “adapter-off loses at least half the gain” rule must be rewritten as one
predeclared root-level linear contrast with a confidence bound; a post-hoc
ratio is unstable. The observed “strongest comparator” must be handled by a
simultaneous max contrast or replaced with one predeclared longitudinal
comparator.

### C6 sensitivity

For the 12-dyad four-cell interaction, a two-sided 95% approximation gives:

| interaction SD | approximate power for true `0.03`, `n=12` |
|---:|---:|
| 0.030 | 0.90 |
| 0.034 | 0.80 |
| 0.040 | 0.65 |
| 0.050 | 0.45 |
| 0.075 | 0.21 |
| 0.100 | 0.12 |

Thus 12 dyads are defensible only with extraordinarily tight four-cell
pairing. Until a target-blind dyad pilot demonstrates interaction SD near
0.03, C6 is an exploratory bridge, not a powered meta-learning headline.

### Better use of the 600-fit budget

At the same nominal confirmation-fit budget, reducing redundant longitudinal
controls permits more independent roots:

- `n=24` has about 88% power at SD 0.075 and 65% at SD 0.10;
- `n=32` has about 96% power at SD 0.075 and 79% at SD 0.10.

Those approximations apply only to one primary contrast. More roots also
increase source/writer/evaluation generation, so `n=32` is conditional on the
call canary. A predeclared blinded variance-based choice between 20, 24, and 32
roots is scientifically preferable to asserting that 20 is powered. The
choice must use treatment-label-blind variance and a fixed maximum, never
observed arm effects. If the calendar cannot support that, retain 20 and print
the sensitivity table.

## Claim-preserving staged/factorial reduction

### Lean terminal-heavy surface

The common frozen source deck makes several intermediate fits scientifically
unused. Use this per root side:

| cell | fits | evaluation schedule | retained question |
|---|---:|---|---|
| `FROZEN` | 0 | all 4 cuts | C2 no-learning curve |
| `TEXT_ACTIVE` | 0 | all 4 cuts | strong external-memory curve and the predeclared C4 comparator |
| `NATIVE_PERIODIC` / `COMPACT_LINKED` | 4 | all 4 cuts | C2, C4, and authentic terminal C5 carrier |
| `RAW_FINAL_CUMULATIVE` | 1 | terminal | C3 raw response-distillation control |
| `LEAFE_FINAL` | 1 | terminal | C3 final reflective recovery control |
| `DERANGED_FINAL` | 1 | terminal | C5 stored-binding intervention |
| `NATIVE_ADAPTER_OFF` | 0 | terminal full panel; cheap routing sentinels earlier | parametric localization |
| `EXPANDED_LINKED` | 1 | terminal | C5 rate/read comparator |
| `ATOMS_ONLY` | 1 | terminal | C5 connectedness ablation |
| **total** | **9** | **18 full panel-cells per side** | versus 15 fits and about 30 broad panel-cells |

This gives:

```text
20-root lean confirmation = 20 * 2 * 9 = 360 fits
32-root lean confirmation = 32 * 2 * 9 = 576 fits
four-root lean pilot       = 4 * 2 * 9 = 72 fits
full lean development root = 2 * 9 = 18 fits
```

`RAW_FINAL_CUMULATIVE` is a fair terminal stand-in for repeated clean-base raw
rebuilds only if raw state is forbidden from affecting source, admission,
corpus order, or target selection and a deterministic CPU receipt proves that
its terminal corpus/order/update schedule is identical to the terminal
periodic fit. If that equivalence is false, pay for periodic raw fits.

`DERANGED_FINAL` tests whether the already-created terminal carrier needs
authentic action/outcome and endpoint bindings. It does not show that authentic
bindings were necessary for every earlier recurrent DREAM transition. Keep the
claim at terminal carrier mediation. If that result is positive and the
stronger recurrent-path claim is essential, add the three earlier deranged
fits per side afterward: 120 more confirmation fits at 20 roots.

For C4, predeclare `TEXT_ACTIVE` as the longitudinal comparator. Do not inspect
terminal raw/LEAFE results and retroactively choose a comparator whose earlier
curve was never run. C3 still compares terminal native with text, raw, and
LEAFE simultaneously. C2 still uses all native/frozen cuts. C5 still has
adapter-off, derangement, atoms, expanded paths, and bridge cuts.

The intermediate adapter-off full panels can be omitted because frozen already
supplies the typed-forced proposal guard. Run only cheap compliance sentinels
at early cuts and the full exact-checkpoint adapter-off panel at terminal for
C5. If exact intermediate off curves are considered essential, add three
panel-cells per side, not fits.

### Stage order

1. **World/call canary:** no scientific root. Measure `C`, component count,
   source calls, DREAM/admission calls, exact token classes, cut-specific fits,
   engine lifecycle, and one full panel.
2. **Development:** a fixed small number of roots, declared before calls. Tune
   implementation and freeze. Development results never enter confirmation.
3. **Four-root spending pilot:** execute the lean surface once and apply only
   the spending rule. It is not a variance estimate or evidence.
4. **C2/C4 tranche:** run native, frozen, and text curves on a predeclared first
   confirmation tranche. Use a nonbinding futility stop only; never claim from
   the tranche and never change the final analysis.
5. **Remaining C2/C4 roots:** finish the predeclared root count. If C2 fails,
   do not spend terminal adapter fits.
6. **C3 terminal controls:** raw and LEAFE terminal fits/panels. Text is already
   present. Stop if C3 fails.
7. **C5 terminal mechanism:** deranged, atoms, expanded, adapter-off, and bridge
   cuts. Add recurrent derangement only if required by the surviving claim.
8. **C6:** only after C2--C5 artifacts and intervals are sealed. It yields
   first to calendar or lease pressure.

This ordering preserves hierarchical claims while converting failures into
early savings. It does not permit outcome-driven changes to methods, margins,
roots, or targets.

## Minimum and maximum manifests

The current proposal has no true maximum manifest because call-related
integers are open. The following are bounded *recommended fit manifests*; a
separate call/token manifest remains mandatory.

### Minimum credible full-arc manifest

This is the smallest fit allocation that retains all named questions, while
treating C6 as one-cycle exploratory evidence:

| phase | roots/dyads | fit rule | fits |
|---|---:|---|---:|
| heat | treatment-neutral | three fixed heats | 3 |
| development | 2 roots | lean full surface | 36 |
| spending pilot | 4 roots | lean full surface | 72 |
| confirmation | 20 roots | lean terminal-heavy surface | 360 |
| C6 | 12 dyads, `J=1` | `24J+72` | 96 |
| **total** |  |  | **567** |

This is not automatically adequate for C3--C6 power. “Minimum credible” means
the causal cells exist and the 20-root sensitivity is honestly reported, not
that every conjunct has 80% power.

### Maximum information near the original confirmation-fit budget

If measured generation fits the calendar, reallocate the 600-fit confirmation
envelope to 32 roots:

| phase | roots/dyads | fit rule | fits |
|---|---:|---|---:|
| heat | treatment-neutral | three fixed heats | 3 |
| development | 2 roots | lean full surface | 36 |
| spending pilot | 4 roots | lean full surface | 72 |
| confirmation | 32 roots | lean terminal-heavy surface | 576 |
| C6 | 12 dyads, `J=1` | conditional after C2--C5 | 96 |
| **total** |  |  | **783** |

If five parenting cycles are scientifically required, C6 is 192 and the total
is 879. If full recurrent derangement is promoted after the terminal shadow
result, add `32 * 2 * 3 = 192` fits. These are hard optional expansions, not
slack hidden inside a 25% line.

No manifest may use fewer roots after bad outcomes, replace failed scientific
cells, or turn the four pilot roots into confirmation. Technical retries are
new identities and consume reserve; they do not replace failed endpoints.

## Corrected resource assessment

The v0 table's `600 * 3--10 minutes = 30--100 GPU-hours` is arithmetically
correct. It is not empirically established for the proposed writer and covers
confirmation fits only. Under the broad manifest, fitting alone is:

```text
(723 + 30D) fits * 3--10 min = (36.2 + 1.5D) -- (120.5 + 5D) GPU-hours
```

before C6, development-specific calibration failures, model generation,
panels, base loads, teardown, or retries. For `D=2`, that is 39.2--130.5 fit
GPU-hours. A nominal 96-fit C6 adds 4.8--16 hours only if its corpora have the
same fit-time range, which is unproven.

The measured legacy durations suggest that a uniform 3-minute lower bound
overstates early small fits, while a 10-minute upper bound is already nearly
consumed by a sleep-736 rank-16 fit. The proposed terminal super-life contains
roughly 650--866 source episodes per side at `C=12k--16k`; native response
length and admitted-row growth, not episode count alone, determine whether its
terminal fit stays below 10 minutes. Only cut-specific canaries can answer.

The proposal's generation estimates of 15--35 GPU-hours and evaluation
estimates of 20--45 GPU-hours have no count basis. The source floor alone is
about 26k--35k logical actor samples for 20 roots under one-call episodes, and
DREAM could add tens of thousands of opportunities per evolving arm. Token
caps, batching, and late-life prefill determine the actual GPU time. Replace
the two broad lines with measured products:

```text
sum over request classes (
  count * measured input tokens/request * prefill seconds/token
  + generated tokens * decode seconds/token
)
+ engine lifecycle time
+ measured training time by cut/corpus class.
```

Report occupied GPU time and critical-path wall time separately. Dividing total
GPU-hours by five assumes perfect divisibility; recurrent cuts within one side,
adapter-dependent DREAM, sealing, review, and terminal promotion are serial.
The observed current code also reloads engines around fits. Five GPUs can
reduce independent-root wall time but cannot divide every critical path by
five.

### A40 and calendar facts

- Physical inventory in the reviewed script: eight A40s.
- Documented current use: six A40s for v6.1, with other transient nursery/
  audit occupancy observations.
- Claimed planning availability: five GPUs, but no bound reservation receipt.
- Lease expiry: September 14.
- Proposed terminal work: September 14--15.

Therefore the schedule is internally inconsistent unless the lease is renewed
or another bound node is secured. Theoretical GPU-hours before expiry are not
the same as available hours after implementation, review, pilot, and current
jobs. Resource promotion requires a signed inventory over exact GPU IDs,
competing jobs, lease end timestamp/timezone, preemption policy, and teardown
ownership.

## Kill gates

These gates are ordered; a later pass cannot rescue an earlier failure.

### K0 -- protocol/count closure

Before target identities or model calls, require exact values for every field
in the call manifest above, `D`, `J`, all panel sizes, and both a minimum and
maximum dispatched-call/token count. **Kill the September 16 full arc if any
resource variable remains “fixed later.”**

### K1 -- world and context scale

For every retained root side, prove all four complete-era cuts exist without
repeat/filler, bind exact tokenizer counts, and bound component/episode tails,
not only the 200-side mean. If p95 components or source turns exceed the
resource manifest, stop before target reveal.

### K2 -- writer and serving canary

Require exact native response/mask/EOS receipts, deterministic common seeds,
free compliance at least 0.95, typed-forced/generic loss no worse than 0.05,
and fail-closed nonfinite behavior. Measure all three heats neutrally. No heat
passes means stop; no treatment-specific rescue.

### K3 -- all-in runtime and lease

Measure at least one early and one terminal-size rank-8 fit, one complete
source/DREAM path, and every terminal panel class. Gate on terminal and p95
time, not the global median. Include base load, engine shutdown/reload, save,
hash, and audit latency. Require bound compute through at least September 16;
the September 14 lease alone fails this gate.

### K4 -- development construct ceilings

Known-good text must reach the registered action ceiling; the active text
reader must retrieve every inserted oracle record; native link fidelity and
action behavior must clear their gates on disjoint development roots. Failure
stops the headline rather than weakening the comparator.

### K5 -- four-root spending pilot

Preserve every assigned root. Require native-minus-frozen mean at least 0.05,
positive in at least 3/4, authentic direction over deranged, and zero invalid
provenance/routing/resource cells. This decides spending only; it cannot tune
or estimate confirmation power.

### K6 -- confirmation futility and C2

Use only a predeclared nonbinding futility rule on the first confirmation
tranche. Stop for nonpositive mean, severe routing failure, or conditional
power below a frozen threshold; never claim early success. Final C2 uses all
assigned roots and the registered interval. If C2 fails, do not fit C3/C5
terminal adapters.

### K7 -- C3 and C4

C3 must clear simultaneous terminal text/raw/LEAFE contrasts. C4 must use its
predeclared longitudinal text comparator, a confidence-based retention
non-inferiority test, and its mixed-age guard. Failure stops the broad lifetime
claim.

### K8 -- C5

Run terminal derangement, atoms, expanded, adapter-off, and bridge cuts only
after C2--C4 survive. Require confidence-bound versions of every superiority/
non-inferiority contrast. If connectedness passes but rate/read fails, delete
“compressed.” If only adapter-on/off passes, C5 fails.

### K9 -- C6

C6 begins only after C2--C5 are sealed, the dyad interaction SD/resource
design is acceptable, and `J` is frozen. If it misses or cannot finish, omit
the meta-intelligence clause; never trade a core root or baseline for it.

## September 16 feasibility

The broad schedule requires all of the following knife-edge events:

1. exact architecture/claim/call manifest ratified by September 7;
2. the new super-life, typed native interface, ledger, native trainer, active
   text memory, LEAFE brancher, derangement, carrier panel, isolated scorer,
   and root-level analysis implemented and reviewed by September 9;
3. terminal-size canaries and a valid development ceiling complete before the
   four-root pilot;
4. pilot promotion early enough to run all independent confirmation roots and
   hierarchical terminal stages; and
5. A40 capacity extended beyond the September 14 lease.

Current `organism_v6` code implements none of the paper protocol as a bound
runtime, and the headline document itself lists fourteen material plumbing
gaps. The v6.1 jobs also consume most of the documented node through roughly
September 7--8. On current evidence, it is not credible to call the full
C2--C6 result feasible by September 16.

The only defensible accelerated path is:

- freeze and count by September 7;
- run a terminal-size all-in canary no later than September 8;
- complete development and the four-root pilot no later than September 10;
- execute staged C2/C4 confirmation first, then conditional C3 and C5, through
  September 14 on an extended/bound node; and
- attempt C6 only if the core result, artifacts, remaining dyad power, and
  compute are already secure.

Missing any of the first three dates kills the September 16 full arc. It need
not kill the ICLR attempt: the project can still report a narrower prospective
C2 result or a controlled negative/mechanism study under the readiness
document's actual September 18 abstract and September 25 paper deadlines. It
cannot promise unobserved C3--C6 results.

## Final disposition

The v0 design is scientifically ambitious in the right direction, but it
currently buys repeated intermediate control fits before buying an auditable
call budget or adequate independent-root sensitivity. Preserve the causal
claim ladder and reverse that allocation:

1. count source/DREAM/evaluation calls exactly;
2. validate the terminal writer and engine critical path;
3. concentrate curves on native, frozen, and active text;
4. make raw, LEAFE, derangement, and carrier ablations terminal and
   hierarchical;
5. spend saved fits on independent roots if generation permits; and
6. keep C6 conditional and out of the September 16 critical path.

Under that repair, 20 roots are an honest minimum with explicit sensitivity,
24--32 roots are a better use of roughly the same fit envelope, and every
failed rung saves downstream GPU-hours without weakening the evidence needed
for a surviving claim.
