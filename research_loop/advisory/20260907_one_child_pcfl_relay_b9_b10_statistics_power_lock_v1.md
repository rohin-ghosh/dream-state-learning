# One-child PCFL relay: B9--B10 statistics and power lock v1

Date: 2026-09-07

Status: source-only candidate disposition of B9--B10 in
`20260907_one_child_pcfl_relay_v2_final_attack.md`. This advisory does not
ratify note 58, repair B1--B8, select or generate a child/root/target, run a
pilot, implement a reducer, call a model/tokenizer, build an adapter, use a
GPU, or authorize a scientific claim. Its constants and algorithms are
prospective candidate bytes for the `R0` deliberation. Confirmation remains
closed until the blockers at the end are discharged and the resulting final
`N` is separately ratified before any confirmation root is generated.

## 1. Scope and estimand

The sole checkpoint is one fixed terminal child selected by the already
frozen parenting selection function after its one parent and every nursery
artifact have been deleted. The sampling unit is one independently generated
PCFL environment-pair root for a byte-identical clone of that same child.
Roots have independent environment state and RNG streams. They never teach,
observe, compete with, communicate with, select, or share carrier/model state
with one another. An isolated root used to construct `WRONG_LIFE` is a
negative carrier source only; it is not another learner.

All inference is conditional on the exact fixed checkpoint and the registered
PCFL root distribution. It is not inference over children, parents,
classrooms, populations of learners, or shared learning. Calls, targets,
twin sides, phases, technical seeds, adapter seeds, and carrier forks are
repeated measures inside a root and never increase `N`.

For carrier `k in {TEXT,LORA}` and root `r`, all registered repeated cells are
reduced inside the root by the rules below. Every randomized root appears
exactly once in every endpoint denominator after its carrier stage has been
opened. There is no complete-case analysis, root replacement, favorable-seed
selection, target selection, or conditioning on successful acquisition,
traversal, experiment selection, admission, writing, or delayed use.

## 2. Required upstream score interface

This lock consumes the following binary root fields. B1--B8 must give every
field a finite, exact set of raw cells and a deterministic derivation. No
field may be added, deleted, reweighted, or reinterpreted after `R0`.

For a positive field with its frozen `m` repeated cells, first compute the
required within-root arithmetic mean `bar_y=sum_cell y_cell/m`, with each raw
cell in `{0,1}`. The confirmatory root field is `1[bar_y=1]`: it equals `1`
iff **every** registered repeated cell meets its exact semantic, provenance,
chronology, trace, action, and receipt predicate; otherwise it is `0`.
`bar_y` is reported descriptively but does not replace the strict field in
confirmation.

For a leakage/control field, compute the analogous within-root arithmetic mean
`bar_l` and set the confirmatory field to `1[bar_l>0]`: it equals `1` iff
**any** registered repeated cell produces the forbidden authentic
path/action/read/binding or beats its registered no-information score;
otherwise it is `0`. Thus every repetition is averaged first by a frozen rule,
then the strict leakage field is a logical `OR`. A larger field is worse.

The required root fields for each carrier are:

```text
o_r                 leaked oracle clears every registered oracle cell
a_rk                required Phase-A atoms/links exist and retained atomic
                    value plus exact carrier READ fidelity clear their cells

c_auth_rk           both authentic Phase-B goals use their exact paths and
                    take their oracle-valid terminal actions
c_der_rk            deranged carrier ever yields an authentic goal path/action
c_null_rk           LINK_NULL ever yields an authentic goal path/action

t_auth_rk           paired goals have the required distinct first queries,
                    exact distinct paths, and valid terminal actions
t_blind_rk          the frozen best exhaustive target-blind policy ever meets
                    that goal-conditioned traversal predicate
t_cut_rk            a necessary-row cut ever preserves the original authentic
                    path/action
t_redir_rk          every registered twin substitution yields its twin-valid
                    path/action and rejects the original path/action
b_leak_rk           any frozen Phase-B proper-subset, direct-answer, adaptive
                    controller, timing/error, or other closure control succeeds

q_gap_rk            AUTH emits the valid gap, two live hypotheses, and complete
                    pre-outcome prediction map
q_sel_auth_rk       AUTH chooses a legal registered separating experiment
q_sel_sham_rk       SHAM produces the target-relevant separating choice
q_rel_auth_rk       AUTH chosen experiment has normalized target-relevant EIG 1
q_rel_sham_rk       SHAM chosen experiment has normalized target-relevant EIG 1
gnew_rk              the committed outcome maps to exactly one supported new
                    row and the assigned truthful writer/read receipt succeeds

d_edge_rk           EDGE_WRITE takes the exact delayed oracle-valid action
d_no_rk             NO_WRITE takes that authentic delayed action
d_sham_rk           SHAM_WRITE takes that authentic delayed action
d_swap_orig_rk      NEW_BIND_SWAP preserves the original authentic action/path
d_swap_redir_rk     NEW_BIND_SWAP takes the binding-twin-valid action/path and
                    rejects the original action/path
d_off_rk            REACHOUT_OFF_CONTINUATION takes the authentic delayed action
d_leak_rk           any frozen D proper-subset, passive-channel, controller, or
                    legal-reacquisition closure member takes that action

u_auth_rk[name]     task-matched authentic positive outcome for a B8 control
u_rk[name]          named carrier/control leakage for that same task/cell set
```

The exact `u[name]` roster is:

```text
goal_only, state_only, identifier_only, candidate_only, passive_signature,
source_action_string, unaided_generative
```

For `LORA`, it additionally contains `wrong_life` and `adapter_off`. If an
upstream B1--B8 manifest proves that one named field is byte-identical to an
already listed closure cell, it may point to that same cell, but it may not
omit its named score or its receipt. `wrong_life` retains the one-child
isolation rule above.

For `LORA`, define one further control:

```text
same_mismatch_r = 1 iff any registered TEXT_SAME_SEMANTICS exact read returns
                  a different canonical semantic row, or the paired semantic
                  action predicate differs, between active TEXT and active
                  LORA; otherwise 0.
```

Physical-resource equality is not scored. Every carrier's resource vector is
reported, and unequal resources may not be called matched.

## 3. Bounded root components

Every primitive above lies in `{0,1}`. Define the following registered paired
components, all in `{-1,0,1}`:

```text
Cbind_rk     = c_auth_rk     - c_der_rk
Cnull_rk     = c_auth_rk     - c_null_rk
Tgoal_rk     = t_auth_rk     - t_blind_rk
Tcut_rk      = t_auth_rk     - t_cut_rk
Qselect_rk   = q_sel_auth_rk - q_sel_sham_rk
Qrelevant_rk = q_rel_auth_rk - q_rel_sham_rk
W0_rk        = d_edge_rk     - d_no_rk
W1_rk        = d_edge_rk     - d_sham_rk
Fbind_rk     = d_edge_rk     - d_swap_orig_rk
Freacq_rk    = d_edge_rk     - d_off_rk
```

`Freacq` remains a separately worded total-path necessity contrast; it is not
a controlled write effect and is never pooled with `W0`, `W1`, or `Fbind`.

Let:

```text
u_max_rk = max_name u_rk[name]
u_auth_min_rk = min_name u_auth_rk[name]
Kmin_rk  = min_name (u_auth_rk[name] - u_rk[name])
```

The maximum/minimum is over the complete frozen roster, not a selected
favorable control. Each `u_auth[name]` and `u[name]` pair has identical task,
goal, public start, cell roster, and coupled exogenous bytes except its named
intervention. It is an adversarial worst-control reduction. Every named pair
is still printed. `u_auth_min` supplies one simultaneous authentic floor,
`u_max` supplies one simultaneous control ceiling, and `Kmin` supplies one
simultaneous practical contrast: passing them implies the registered
conditions for every named control.

`Ttwin` and D binding redirection are absolute redirection scores rather than
mere twin-world success:

```text
Ttwin_rk = t_redir_rk
Dtwin_rk = d_swap_redir_rk
```

Because their positive predicate explicitly requires the twin-valid result
and rejection of the original authentic result, a generic failure or
`NOT_FOUND` scores `0`.

## 4. Exact same-root temporal chains (B9)

The chain is an observed, same-root temporal conjunction across the registered
fork graph. Phase B is the destroyed write-denied fork from the root's Phase-A
cut; Phase C restarts from the same root's exact common `C0`; Phase D uses the
registered post-outcome branches. “Same chain” therefore means one root and
its predeclared coupled forks in chronological order, not an illegal single
mutable branch through B, C, and D.

Define:

```text
B_OK_rk = c_auth_rk
          * (1-c_der_rk) * (1-c_null_rk)
          * t_auth_rk * (1-t_blind_rk) * (1-t_cut_rk)
          * t_redir_rk * (1-b_leak_rk)

C_OK_rk = q_gap_rk * q_sel_auth_rk * (1-q_sel_sham_rk)
          * q_rel_auth_rk * (1-q_rel_sham_rk) * gnew_rk

D_OK_rk = d_edge_rk * (1-d_no_rk) * (1-d_sham_rk)
          * (1-d_swap_orig_rk) * d_swap_redir_rk
          * (1-d_off_rk) * (1-d_leak_rk)

CTRL_OK_rk = u_auth_min_rk * (1-u_max_rk)

TEXT_chain_r = o_r * a_r,TEXT * B_OK_r,TEXT * C_OK_r,TEXT
               * D_OK_r,TEXT * CTRL_OK_r,TEXT

LORA_chain_r = o_r * a_r,LORA * B_OK_r,LORA * C_OK_r,LORA
               * D_OK_r,LORA * CTRL_OK_r,LORA
               * (1-same_mismatch_r)

COMPLETE_chain_r = TEXT_chain_r * LORA_chain_r
```

Commas in subscripts above are typography only; reducer field names use the
ASCII carrier suffix. Each chain is exactly binary. A failure at any earlier
mediator or any required cut/twin/control makes the same root's chain `0`.
No aggregate component result can set a root's chain to `1`.

The population-level, one-child-conditional rates are:

```text
TEXT_chain     = sum_r TEXT_chain_r / N
LORA_chain     = sum_r LORA_chain_r / N
COMPLETE_chain = sum_r COMPLETE_chain_r / N
```

`COMPLETE_chain` is not `TEXT_chain * LORA_chain` and is not the minimum of
the two aggregate rates. It counts only roots that complete both registered
carrier chains. Positive language is “complete observed mediator chain,” not
causal mediation.

## 5. Fixed floors, ceilings, SESOIs, and planning alternatives

These are design constants. DEV/pilot results may not move them.

| endpoint class | confirmatory boundary | fixed power alternative |
|---|---:|---:|
| leaked-oracle rate `E[o]` | lower bound `> .95` | `.99` |
| Phase-A retention `E[a_k]` | lower bound `> .80` | `.90` |
| every other named authentic positive or redirection rate | lower bound `> .75` | `.85` |
| every named leakage/control rate, including `b_leak`, `d_leak`, and `u_max` | upper bound `< .10` | `.02` |
| each paired causal component above and `Kmin` | lower bound on its mean `> .20` | `P(+1)=.80`, `P(0)=.18`, `P(-1)=.02` |
| `same_mismatch` | upper bound `< .05` | `.01` |
| `TEXT_chain` | lower bound `> pi_TEXT=.60` | `.75` |
| `LORA_chain` | lower bound `> pi_LORA=.50` | `.65` |
| `COMPLETE_chain` | lower bound `> pi_COMPLETE=.40` | `.55` |

The `.20` contrast margin is the SESOI on the strict root-compliance scale: at
least a twenty-percentage-point population advantage for the authentic arm,
after adverse roots are retained. The chain minima mean that at least 60%,
50%, and 40%, respectively, of registered roots must clear the entire strict
within-root conjunction with uncertainty accounted for. These margins are
intentionally stronger than positivity and are not estimated from favorable
pilot effects.

The fixed alternatives are power-design points, not acceptance thresholds or
claims about the eventual child. Power is evaluated at the least favorable
boundary of each stated alternative set: equality for every value in the
rightmost column. No observed pilot mean, contrast, chain rate, or favorable
tail may replace them.

## 6. Exact finite-sample confidence rules

Set the one-sided local level `alpha=.05`. All comparisons are strict. Decimal
constants above are exact terminating rationals.

For `x` successes among all `N` roots, define the one-sided
Clopper--Pearson bounds:

```text
CP_L(x,N,gamma) = 0,                                      if x=0
                = BetaQuantile(gamma; x, N-x+1),          otherwise

CP_U(x,N,gamma) = 1,                                      if x=N
                = BetaQuantile(1-gamma; x+1, N-x),        otherwise.
```

`BetaQuantile(q;a,b)` is the smallest real `z in [0,1]` for which the
regularized incomplete beta CDF is at least `q`. Reducer calculations must use
correctly rounded binary64 output and must also emit a directed-rounding
decimal enclosure of width at most `1e-12`. A decision is made only if both
ends of that enclosure lie strictly beyond the boundary. If the enclosure
touches a boundary, the endpoint fails. A positive/floor endpoint passes iff
`CP_L(x,N,.05) > floor`. A leakage/ceiling endpoint passes iff
`CP_U(x,N,.05) < ceiling`.

For paired component `D_r in {-1,0,1}`, let

```text
n_plus  = count(D_r=+1)
n_minus = count(D_r=-1)
L_delta = CP_L(n_plus,N,.025) - CP_U(n_minus,N,.025).
```

Both discordance counts have binomial marginals under independent roots. The
Bonferroni union bound makes `L_delta` a finite-sample, distribution-free,
one-sided confidence bound with coverage at least `.95` for
`E[D]=P(D=+1)-P(D=-1)`, without a normal approximation or exchangeability
assumption. A paired component passes iff `L_delta > .20`. This is
conservative but exact for the registered bounded scores. Ties (`D=0`) remain
in `N`.

The point estimate and both discordance rates are always printed, but the
point estimate cannot rescue a confidence-bound failure. There is no
Student-t, bootstrap, target-level, seed-level, mixed-model, or asymptotic
fallback analysis for confirmation.

## 7. Failure, missingness, and denominator law

Scientific or post-exposure failure has the adverse value:

| condition | positive field | leakage/control field | mismatch field | chain |
|---|---:|---:|---:|---:|
| missing, malformed, unsupported, unavailable, compiler rejection, no valid matched deck/sham/derangement, fit/mount/read/action failure, timeout after exposure, or receipt failure | `0` | `1` | `1` | `0` |

Those values propagate before every paired component and chain is formed. A
missing positive and missing control therefore cannot manufacture a favorable
paired difference. An upstream scientific failure may stop work on that root
for safety or cost, but all unobserved downstream positive fields are `0`, all
unobserved downstream leakage fields are `1`, and every downstream chain is
`0` for that randomized root.

An infrastructure resume is allowed only when all of the following are true:

1. failure occurs before the cell emits or receives any actor-visible byte;
2. the actor, world, carrier, candidate catalog, counters, and RNG receipts
   equal their sealed pre-dispatch hashes;
3. the failure code is on the `R0` infrastructure-only allowlist; and
4. the identical sealed cell identity is relaunched, never regenerated.

At most two relaunches are allowed after the initial attempt. A third failure
receives the adverse scientific values above. Any failure after actor-visible
exposure is not resumable. A repository/code/hash/hidden-access violation or a
systemic reducer defect invalidates and stops the study; it is not converted
to ordinary zeroes, patched in place, or repaired by adding roots.

## 8. Multiplicity and ordered release

Each line below is one fixed-sequence rung. A rung containing several entries
is an intersection--union test: every named entry must pass its own level
`.05` rule in section 6. No within-rung multiplicity adjustment is needed for
the conjunctive claim. Testing stops at the first failed rung. The first true
rung in this fixed sequence bounds the probability of releasing any false
later confirmatory claim by `.05`.

```text
V0       oracle floor and all nonstatistical integrity receipts

TXT-A    a_TEXT floor
TXT-C    c_auth floor; c_der/c_null ceilings; Cbind and Cnull SESOIs
TXT-T    t_auth and Ttwin floors; t_blind/t_cut/b_leak ceilings;
         Tgoal and Tcut SESOIs
TXT-Q    q_gap/q_sel_auth/q_rel_auth/gnew floors;
         q_sel_sham/q_rel_sham ceilings;
         Qselect and Qrelevant SESOIs
TXT-W    d_edge floor; d_no/d_sham ceilings; W0 and W1 SESOIs
TXT-FB   d_swap_redir floor; d_swap_orig ceiling; Fbind SESOI
TXT-FR   d_off ceiling; Freacq SESOI, released only as total-path necessity
TXT-CTL  u_auth_min floor; d_leak/u_max ceilings; Kmin SESOI
TXT-CH   TEXT_chain lower bound > .60

LRA-A    a_LORA floor
LRA-C    c_auth floor; c_der/c_null ceilings; Cbind and Cnull SESOIs
LRA-T    t_auth and Ttwin floors; t_blind/t_cut/b_leak ceilings;
         Tgoal and Tcut SESOIs
LRA-Q    q_gap/q_sel_auth/q_rel_auth/gnew floors;
         q_sel_sham/q_rel_sham ceilings;
         Qselect and Qrelevant SESOIs
LRA-W    d_edge floor; d_no/d_sham ceilings; W0 and W1 SESOIs
LRA-FB   d_swap_redir floor; d_swap_orig ceiling; Fbind SESOI
LRA-FR   d_off ceiling; Freacq SESOI, released only as total-path necessity
LRA-CTL  u_auth_min floor; d_leak/u_max ceilings; Kmin SESOI;
         same_mismatch ceiling
LRA-CH   LORA_chain lower bound > .50

BOTH-CH  COMPLETE_chain lower bound > .40
```

This is also the carrier execution order. Run and reduce the complete TEXT
cohort first. If `TXT-CH` fails, do not open the LoRA stage and interpret no
LoRA endpoint. If it passes, run LoRA for **all** `N` roots, including roots
with `TEXT_chain_r=0`; the text result does not select a LoRA subset. A LoRA
failure cannot erase already released text claims, and text success cannot
rescue a failed LoRA or complete-chain clause.

No component claim may be released outside this sequence. Per-component point
estimates and bounds after a stopped rung are descriptive and labeled as such.
A new unordered, subgroup, carrier-advantage, or standalone control claim
requires a separately ratified multiplicity family; Holm or a selected
minimum may not be invented after outcomes are visible. Passing
`TEXT_SAME_SEMANTICS` supports common semantic transport only and supplies no
LoRA superiority claim.

## 9. Prospective power and blinded extension rule

### 9.1 Chronology

At pre-parenting `R0`, hash-bind this score registry, all thresholds,
confidence/release code, the pilot firewall, the candidate grid, power
alternatives, simulation algorithm, seeds, and allowed pilot outputs. The
rule may be applied after `PU/CS` to nuisance information from disjoint
`PCFL-13` DEV/exploratory roots, but it may not change any endpoint, score,
margin, alternative, alpha, or decision rule.

The candidate confirmation sizes are exactly:

```text
N_GRID = [96, 128, 160, 192, 256, 320, 384, 512]
N_BASE = 96
N_MAX  = 512
```

`N_BASE` is not permission to dispatch. The final `N` is the smallest member
of `N_GRID` satisfying every rule below. It may only stay at `N_BASE` or
increase. If no candidate through `512` passes, or the separately ratified
resource ceiling is below the selected value, the relay stops before any
confirmation root is generated. Thresholds are not weakened.

### 9.2 Pilot firewall: nuisance only

The pilot and confirmation roots are disjoint. `M_PILOT=32` is a fixed
nuisance-pilot count, not a revived provisional confirmation `N`. A firewall
process receives the complete pilot endpoint vector but emits only:

1. the fixed pilot count `M_PILOT=32` and administrative pre-exposure
   failures;
2. for each endpoint, anonymized row ranks from adverse to favorable, with
   ties ordered internally
   by `SHA256(UTF8("20260907-one-child-pcfl-b9b10-tie-v1|") ||
   uint32be(len(UTF8(endpoint_id))) || UTF8(endpoint_id) ||
   uint32be(len(UTF8(sealed_pilot_root_id))) ||
   UTF8(sealed_pilot_root_id))`; and
3. the resulting endpoint-by-endpoint Spearman rank-correlation matrix.

The firewall orders emitted rows by
`SHA256(UTF8("20260907-one-child-pcfl-b9b10-row-v1|") ||
UTF8(sealed_pilot_root_id))` and emits neither the root ID nor that ordering
digest. The power process sees only anonymized row number, endpoint ID, and
rank.

It emits no pilot means, arm rates, differences, discordance directions,
chain rates, pass counts, p-values, confidence bounds, plots, or root prose.
The sample-size process and human ratifier may see the allowed outputs only.
Pilot success/failure rates may not select `N` even if somebody else has seen
them. A firewall breach makes this protocol exploratory.

If a nuisance pilot is not separately authorized, has fewer than 32 retained
pilot roots, or its receipt fails, the analytic arbitrary-dependence rule below
may be reported as a sensitivity calculation but no final confirmation `N` is
selected. The simulation with observed within-root dependence is mandatory.
Absence of pilot data can never choose a smaller `N` or authorize dispatch.

### 9.3 Exact marginal power

For each floor/ceiling/chain endpoint, enumerate all `x=0,...,N` under the
exact binomial distribution at its fixed alternative and sum probabilities
only for counts whose section-6 decision passes. For each paired component,
enumerate all triples `(n_plus,n_zero,n_minus)` summing to `N` under the exact
multinomial alternative `(.80,.18,.02)` and sum probabilities only where
`L_delta>.20`. No normal or Monte Carlo approximation enters these marginal
powers.

The literal section-8 family contains `J=75` constituent statistical
decisions: one `V0` oracle decision, 36 TEXT decisions, 37 LORA decisions, and
one `BOTH-CH` decision. `u_auth_min`, `u_max`, and `Kmin` each count once
because they are fixed worst-control endpoints, not selected controls. The final manifest must
print the 75 ordered endpoint IDs. An upstream alias may reuse a raw cell but
does not remove its registered endpoint or change `J`.
For candidate `N`, let `beta_j(N)=1-power_j(N)`. The arbitrary-dependence
least-favorable conjunction passes only if:

```text
sum_j beta_j(N) <= .20
```

By the union bound this guarantees at least `.80` power for the entire ordered
conjunction at the fixed planning alternatives for any within-root dependence.
It is the binding power rule, not a claim that endpoints are independent.

Additionally require marginal power at least `.90` for each of
`TEXT_chain`, `LORA_chain`, and `COMPLETE_chain`. Powering aggregate component
tests alone is insufficient.

### 9.4 Required covariance-preserving simulation

When a valid nuisance pilot exists, also run exactly `200000` simulations per
candidate `N`. Let `K_N` be the 32-byte digest
`SHA256(UTF8("20260907-one-child-pcfl-b9b10-power-v1|") ||
uint64be(candidate_N))`. Generate each required 256-bit word as
`SHA256(K_N || uint64be(simulation_index) || uint64be(root_index) ||
uint32be(draw_kind) || uint32be(retry_index))`. Indices are zero-based.

For a uniform pilot-row index, interpret a word as the unsigned big-endian
integer `z`, set `L=floor(2^256/M_PILOT)*M_PILOT`, reject while `z>=L`, and
return `z mod M_PILOT`; `retry_index` starts at zero and increments on
rejection. For `w`, use a separate `draw_kind`, set `retry_index=0`, and
return `z/2^256`. Thus `w` is the specified 256-bit grid-uniform variate in
`[0,1)`. No library PRNG is permitted.

For simulation replicate/root, sample a pilot rank row `i` uniformly with
replacement and one `w` uniformly on `[0,1)`. For endpoint `j` with rank
`rank_ij` among `m` pilot roots, set

```text
u_j = (rank_ij - 1 + w) / m.
```

Pilot ranks and inverse CDFs use decision-coded scores for which larger is
always favorable: positive/chain fields are unchanged; a leakage or mismatch
field becomes `1-field`; and paired components retain `-1<0<+1`. Map `u_j`
through the left-continuous inverse CDF of that endpoint's fixed section-5
planning alternative, then convert decision-coded ceilings back to their
registered leakage/mismatch fields. This empirical rank-copula construction
discards every pilot marginal effect while retaining the observed within-root
rank dependence used for joint planning. Derived decision statistics are then
reduced exactly as in sections 6 and 8. The synthetic endpoint vector is a
decision-dependence model, not a synthetic causal world; the analytic
union-bound rule remains binding if the copula approximation is imperfect.

Let `s_N` be the number of simulations passing the entire ordered
conjunction. Require:

```text
CP_L(s_N,200000,.01) >= .80.
```

The non-strict `>=` here is a power-planning criterion only. Print the joint
estimate, its 99% lower bound, every marginal power, the union-bound lower
bound, pilot rank-correlation receipt, RNG receipt, and exact source/runtime
hashes. The final selected `N` is the smallest grid member that passes both
the binding analytic rule and, when available, this simulation rule.

### 9.5 Blinded upward extension and final lock

The only allowed extension is the deterministic upward move from `N_BASE` to
the selected member of `N_GRID` produced by sections 9.2--9.4. It uses no
favorable effect estimate. It occurs before confirmation-root generation and
before `A0`. The selected `N`, power stdout, code/environment hashes, and
allowed pilot-output receipt must then be exact-byte ratified.

There is no interim look at confirmation scientific outcomes, no efficacy or
futility stop, no confirmation-stage variance re-estimation, no additional
root after `A0`, and no administrative replacement. Every one of the final
`N` confirmation roots is sealed at `A0` and remains in all applicable
denominators. A later desire for more roots is a new protocol, not an
extension of this confirmation.

## 10. Ordered interpretation boundary

After `TXT-CH`, the strongest text statement is limited to a complete semantic
relay through explicit text on the registered root distribution. It says
nothing about LoRA transport.

After `LRA-CH` but before `BOTH-CH`, carrier-specific LoRA clauses may be
released, but not the claim that a nontrivial fraction of the same roots
completed both carrier chains. The highest note-58 LoRA relay language
requires `BOTH-CH` as well as every earlier rung. `Freacq` is always labeled a
total-path necessity result. No compression, classroom, population learning,
general learner, autonomous theory invention, unrestricted baseline
superiority, or causal-mediation claim follows.

## 11. Assumptions and remaining blockers

This statistical lock assumes, but does not repair, all of the following:

1. B1--B8 produce an exact machine manifest for every raw cell and potential
   outcome named in section 2, including carrier construction, intervention
   timing, adaptive-controller closure, matched null/sham rows, writer state
   transitions, and every named control.
2. The final B1--B8 manifest makes each positive, leakage, redirection, and
   same-semantics predicate mechanically decidable without human scoring.
3. Root environments are independently and identically sampled from the
   frozen PCFL distribution; all within-root forks use the required coupled
   bytes/RNG. This i.i.d.-root condition is required for the exact binomial
   bounds.
4. The `P0/R0/PU/CS/A0` receipts establish the prospective order required by
   note 58 and the final attack.
5. A resource ceiling can accommodate the selected `N`; `512` is a statistical
   maximum, not a resource authorization.

The blockers at issuance are:

- B1--B8 are still unresolved, so the endpoint-expansion manifest and its
  exact `J` do not yet exist.
- No blinded nuisance-pilot receipt, statistics implementation/hash, power
  stdout, or final selected `N` exists. Therefore note 58's statistics gate
  remains closed.
- No evidence supplied here proves that `R0` preceded parenting unblinding.
  If it did not, all relay results under these bytes are exploratory.
- These bytes have not undergone the required independent interpretations,
  adversarial cross-critique, adjudication, Rohin exact-byte ratification,
  implementation/tests, fresh independent review, author-side advocacy, or
  the separate GPU/scientific-claim gate required by `AGENTS.md`.

## Source read receipts

| source | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| attacked `research_notes/58_one_child_pcfl_relay_v2_executable_contract.md` | `20cad18ac51f1ff81b44a491ceabf609b53eaff3bc5af70d486fd42429a281d9` |
| `research_loop/advisory/20260907_one_child_pcfl_relay_v2_final_attack.md` | `5bea4603a67e6c2808f301578574c26616ca33c87a7b381ef1d91d8326f76042` |

The SHA-256 of this advisory is reported externally after its final bytes are
written; it is not self-embedded.
