# One-parent/one-child v2 statistics reaudit v3

Date: 2026-09-07

Status: **fresh read-only reaudit of repaired proposal bytes**. This memo
changes no addendum, plan, manuscript, workflow, power source, model,
tokenizer, benchmark, adapter, or run state. It authorizes no implementation,
scientific generation, fit, GPU use, network access, or claim.

Audited bytes:

- `research_loop/plans/one_parent_child_headline_v2_addendum.md`, SHA-256
  `3c13492bb1378e07d966597efb9eb72f3c8742631a1e7ef1cb7b8977a5039cff`;
- `research_loop/advisory/one_parent_v2_power_sim.py`, SHA-256
  `dab12b1d278e18cb34f9964e5a10949afbf76eb765586d14e934fe6a1ce9c987`;
- `research_loop/advisory/20260907_one_parent_v2_power_receipt_v2.md`,
  SHA-256
  `3062c04861b9ad0de5e507d5a3132670549511ed635a1ad92027a5d86414476f`.

The receipt invocation was rerun exactly with Python `3.9.6`, NumPy `2.0.2`,
seed `20260907`, and 300,000 repetitions/cell. Its stdout SHA-256 reproduced
exactly as
`d8c172178540a73cc36be5ffa99a9e6a41c62b25c1cc991e792122f265bc18f2`.

## Verdict

**PASS FOR SOURCE-BOUND DELIBERATION.** Every required repair in the v2
statistics reaudit is closed. The addendum and planning receipt now form a
coherent fixed-N statistical proposal:

- the root population, within-root repeated measures, and one-parent/one-child
  scope are explicit;
- counter keys use a noncircular protocol hash, split/root master hierarchy,
  intentional coupling groups, and executed-seed collision checks;
- probe scoring, cached entry, cut order, gain-AUC, and the descriptive
  headroom-normalized interaction are exact;
- the feasible `D` range is correctly `[-5/3,5/3]`;
- the adverse rare-negative mixture is retained and no mean/SD power-envelope
  claim survives;
- administrative missingness blocks affected claims while observed behavioral
  failures follow a frozen continue/quarantine law;
- the five superiority claims plus the R0 local-plateau composite form a valid
  fixed sequence; and
- the two terminal diagnostic hypotheses form an exact separate Holm family
  with failure-inclusive root reducers.

This PASS is for the proposal entering the required deliberation and
ratification path. It is not implementation approval, a pre-GPU verdict,
evidence that the active-memory certificate passed, or scientific evidence.

## Required-repair closure matrix

| prior required repair | v3 disposition | evidence |
|---|---|---|
| 1. Correct `D` bound | **PASS** | Script uses `D_MIN=-5/3`, `D_MAX=5/3` and asserts the cached-entry comparison algebra. |
| 2. Add adverse mixture / remove envelope claim | **PASS** | `rare_negative_p0136` is simulated and reported at `.6441`; addendum and receipt explicitly prohibit “at least 80% power.” |
| 3. Repair root master/KDF/split/coupling groups | **PASS** | Root master derives from `(split,root_id)`; each coupling group appears once; within-group equality and between-group digest/u64 uniqueness are checked. |
| 4. Bind or remove SD-UCB powered-language gate | **PASS** | The undefined SD-UCB gate is removed; the study is fixed-N precision estimation under named planning sensitivities. |
| 5. Define headroom-normalized `D` | **PASS** | Section 4 replaces every `G` by `HG` to define `hgAUC`, `HW_P`, `HW_U`, and descriptive `HD`. |
| 6. Freeze infrastructure/failure state machine | **PASS** | External loss is administrative missingness absent a committed valid/system event; malformed opportunities continue; failed fits/mounts quarantine and restore; no discretionary terminal branch remains. |
| 7. Print exact Holm law | **PASS** | One-sided root t p-values, ASCII tie break, `.025` then `.05` thresholds, own `.05` observed margins, and zero infeasible contributions are explicit. |

## 1. Root `Q` and KDF/coupling

The statistical root remains correctly defined as one analysis row containing
all P/U childhood state, P0/P1/U0/U1/R0 services, repeated probes/cuts, and
derived contrasts. The uniform 56-program draw, uniform permutation into
disjoint 48-program wake and eight-program probe decks, shared within-root
opportunities, and independent cross-root draws support `mu_D=E_Q[D_R]` over
the registered finite universe. Claims remain correctly conditional on one
fixed parent policy and child checkpoint.

The repaired hierarchy resolves the earlier contradictions:

```text
protocol_hash -> HMAC(split, root_id, "root_master")
root_master   -> HMAC(distinct stochastic coupling-group tuple)
event_digest  -> executed seed_u64
```

`protocol_hash` excludes generated root material and its own hash, so it is not
circular. `split` is restored. Matched calls are members of one group rather
than duplicate roster entries; equality is required inside a group. Complete
digest and truncated executed-u64 collisions are rejected only between
distinct groups. The domains separately bind actor, parent, writer,
active-text, retrieval, environment, probes, and diagnostics. Cached P0/P1 and
U0/U1 entry evaluations remove baseline Monte Carlo noise, while probe keys
remain paired across services at a cut and distinct across cuts.

One implementation interpretation must remain fail-closed: if the global
roster finds an accidental between-group seed collision, abort that entire
pre-execution manifest/version rather than drawing a replacement root after
any root result exists. Treat root IDs as prebound labels. This preserves the
no-root-replacement law; the collision event is an engineering validity check,
not a scientific exclusion rule.

The pre-GPU canary now requires the seed to be honored and the registered
marginal law retained. Merely disclosing backend nondeterminism no longer
passes. That is the correct boundary for common-random-number pairing.

## 2. Score, cuts, gain-AUC, and HD sensitivity

The primary probe value is closed:

```text
v = max(0,min(1,(I_base-I_best)/I_base)), with I_base>0;
V = mean over exactly eight probes.
```

The frozen base pipeline is the incumbent, invalid/failed/undispatched
proposals add no candidate, and a completed probe with no improving valid
dispatch scores zero. The era order is wake completion, active-text update
attempt/merge, SLEEP commit or quarantine, then isolated probes. Probe bytes
never return to life. Entry values are cached by common P or U checkpoint.

The gain-AUC is exactly normalized trapezoidal change over equal intervals:

```text
gAUC = [2G(16)+2G(32)+G(48)]/6.
```

Because the cached entry term cancels within P1-P0 and U1-U0, each write
contrast lies in `[-5/6,5/6]`, and their difference `D` lies in
`[-5/3,5/3]`. The source and receipt now use that correct range.

The headroom sensitivity is also exact enough: cellwise gain is divided by
`max(.10,V_search-V_entry)`, then the same gain-AUC and factorial reducers
produce `HD`. The denominator-floor frequency is mandatory, and `HD` is
explicitly descriptive rather than an alternative primary. Entry differences,
raw root values, and floor/ceiling occupancy remain required without
post-treatment matching or exclusion.

## 3. Power source and receipt

The source is deterministic under the frozen receipt environment and the
receipt reproduces byte-for-byte. The t critical value, standardized t5 and
beta families, mild two-point moments, rare-negative two-point moments, joint
interval-plus-estimate rule, and post-clipping empirical disclosures are
correct.

At the requested pre-clipping mean `.070` and SD `.10`, the exact reproduced
joint pass probabilities include:

- normal `.87093`;
- t5 `.87067`;
- beta(2,5) `.87061`;
- beta(5,2) `.86951`;
- mild positive-tail two-point `.90716`; and
- adverse rare-negative two-point `.64407`.

The adverse mixture is decisive and honestly retained. The addendum now says
these are named-shape planning sensitivities, that mean and SD do not determine
small-sample t-rule power, and that no primary, hierarchy, plateau, gate, or
diagnostic may be called “at least 80% powered.” It also removes the undefined
development SD-upper-bound label switch. All future inferences are correctly
described as fixed-N precision estimates unless a later, separately ratified
empirical power model says something narrower.

The receipt's mean-zero `.0000--.0059` false-pass range is explicitly not
presented as a universal type-I bound. This is honest: the confirmatory t test
still relies on iid roots and its ordinary small-sample assumptions; the
simulation is sensitivity evidence, not a proof over all bounded
distributions.

## 4. Failure and missingness

The former false-positive missing-cut rule is gone. The state machine now
distinguishes:

- a completed opportunity with no valid action: observed zero performance;
- a committed malformed/context/tool event: no candidate for that opportunity,
  then continue;
- a failed candidate fit/canary/mount: quarantine, restore the last committed
  adapter, then continue;
- an active-text update failure: retain the prior store, then continue; and
- uncommitted host/storage/transport/backend loss: administrative missingness,
  never behavioral zero.

There is no discretionary terminal-service branch. Any administrative P/U
primary cut blocks `D`; missing R0 blocks public and plateau claims; roots are
never replaced. Complete-case and worst-bound summaries are descriptive only.
The 100% deterministic provenance, firewall, parity, transaction, DREAM,
mount, and anchor gates are system-validity prerequisites rather than extra
hypothesis tests. Routing/proposal/DREAM/generic measures remain descriptive,
so the earlier non-erasure multiplicity ambiguity is resolved.

## 5. Fixed sequence and practical margins

The inferential order is now unambiguous:

```text
D -> W_P -> L_terminal -> C_public -> T_R0 -> R0 plateau composite.
```

For rungs 1--5, the lower endpoint of a two-sided 95% root-level Student-t
interval must exceed zero, the observed estimate must meet its frozen `.05`
margin, and testing stops at the first failure. This controls familywise error
for the five named superiority sentences. The later rungs are honestly
precision-gated, not powered. The sequence prevents a favorable interaction
with harmful parented writes, relative advantage without absolute P1
improvement, deployment-gain advantage without terminal superiority, and a
P1-R0 package contrast from being mislabeled parenting causality.

The promised separate development justifications for `.05` on interaction,
within-system gain, and terminal between-system value must be included in the
eventual source-bound statistics manifest. The numerical rules themselves are
fixed. Passing them estimates a total parenting-by-write effect that can be
mediated by inherited competence and later data quality; it does not estimate
a pure learning-rate parameter or effect over parents/models.

## 6. R0 plateau IUT

The sixth rung is coherent. R0 must first pass every once-only strong-memory
certificate. Its `s1` and `s2` each use the standard alpha-.05 TOST rule: a
two-sided 90% t interval wholly inside `[-.05,.05]`. Root-paired search
headroom has a one-sided 95% lower bound above `.10`; P1 late gain has a
one-sided 95% lower bound above zero; and the late P1-minus-R0 increment has a
positive lower bound plus observed estimate at least `.05`.

The released plateau sentence is the conjunction of all components, so its
null is their union. Requiring every component to reject at alpha `.05` is a
valid intersection-union test. Attempting it only after rungs 1--5 pass makes
it the sixth fixed-sequence claim and preserves the headline family's error
control. The wording remains local to programs 16--48 and the exact
updater/read/action budget; no saturation claim is licensed.

## 7. Terminal diagnostic multiplicity

Both diagnostics now have failure-inclusive root estimands:

```text
K_link    = mean_q(v_intact-v_overlay)
K_binding = V_intact_P1(48)-V_shadow_write(48).
```

Every locked root enters; an infeasible link derangement or unchanged binding
intervention contributes zero; administrative missingness blocks the claim;
and neither diagnostic can affect headline N, artifacts, or decisions. The
link overlay preserves the registered marginal structure and changes only the
one-hop displayed adjacency. The binding shadow permutes a closed public
outcome tuple, recomputes admission mechanically, and preserves authentic
target bytes and the fixed-history interpretation.

The multiplicity rule is exact: compute one-sided root-level Student-t p-values
for null mean at most zero, sort by `(p_value,hypothesis_name)`, require the
smaller p-value at most `.025`, then the larger at most `.05`, and require the
released hypothesis's own observed mean at least `.05`. This is a valid Holm
family for the two named secondary claims. It is transparently separate from
the headline family and is precision-gated rather than powered. Neither claim
supports compression, an internal LoRA graph, or the online mediated effect.

## Final disposition

No statistical blocker from the v2 reaudit remains. The repaired addendum,
power source, and receipt may enter the new source-bound architecture
deliberation as proposal evidence with this PASS. They remain unauthorized for
implementation, model/tokenizer/benchmark activity, adapter work, GPU spend,
or manuscript result language until the later ratification and review gates
are satisfied.
