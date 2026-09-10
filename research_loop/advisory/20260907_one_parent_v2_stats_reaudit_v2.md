# One-parent/one-child v2 statistics reaudit v2

Date: 2026-09-07

Status: **read-only reaudit of proposal-only candidate bytes**. This memo
changes no addendum, bound plan, manuscript, workflow, power script, model,
tokenizer, benchmark, adapter, or run state. It authorizes no implementation,
scientific generation, fit, GPU use, network access, or claim.

Audited bytes:

- `research_loop/plans/one_parent_child_headline_v2_addendum.md`, SHA-256
  `c450e82e9733a176b9ae0ae8478591aa0ae399290f5fe5c81a1ae0647eb22244`;
- `research_loop/advisory/one_parent_v2_power_sim.py`, SHA-256
  `2fa48c89f25ec001572acbc1c36a1acb39399fe49ab6c2f1fb5f8c3db45cc5bb`.

Local CPU verification used NumPy `2.0.2`. The exact default script stdout
SHA-256 was
`f51b30cc04e72f116b6d174757909c2cfda1e28c332f5a3ea3303ce511009836`.
No scientific artifact was read by the script.

## Verdict

**REVISE FOUR BLOCKING EDGES, THEN REAUDIT.** The addendum closes most of the
previous statistical attack. The root is now one five-service iid packet from
a declared finite-universe distribution; program sampling and within-root
pairing are explicit; the probe score and cut order are mostly exact; gain-AUC
`D` is the sole primary; the five superiority claims form a coherent fixed
sequence; the old adaptive N rule is removed; behavioral failures are separated
from administrative missingness; the plateau is a properly comparator-specific
intersection-union gate; and the terminal diagnostics use all roots with a
Holm correction.

Four defects still prevent PASS:

1. the power script's feasible `D` range is wrong by a factor of two because it
   ignores the addendum's cached common entry values;
2. the five simulated distribution shapes do not justify “at least 80% power”
   over a mean/SD envelope—an admissible two-point distribution with the same
   declared mean and SD has only about `.6452` joint pass probability;
3. the root master is unused by the KDF, `split` disappeared from the key,
   digest collision rejection conflicts with intentional matched-key reuse and
   does not check the truncated 64-bit seed that is actually executed; and
4. the prerequisite one-sided 80% SD upper bound has no sample, formula, or
   receipt code, so the condition for using powered language is not executable.

There are also narrower exactness repairs: define the headroom-normalized
interaction rather than only cellwise `HG`; distinguish post-dispatch
infrastructure loss from an endogenous service failure; bind the terminal-
failure state machine; and print the exact Holm decision rule. These do not
require a topology or sample-size redesign.

## Disposition summary

| object | verdict | reason |
|---|---|---|
| root unit and conditional generalization | **PASS** | One root is one analysis row; claims are conditional on one fixed parent/child pair and `Q`. |
| finite-universe deck sampling | **PASS** | Uniform 56-program sampling, wake/probe disjointness, within-root pairing, and cross-root replacement are explicit. |
| KDF and coupling | **REVISE — BLOCKING** | Root master unused; split absent; collision law conflicts with shared keys and checks the wrong object. |
| probe score and cut order | **PASS WITH NARROW REPAIR** | Normalized score and order are coherent; cached entries are correct; headroom sensitivity lacks a final contrast reducer. |
| gain-AUC and contrast algebra | **PASS**, except script bound | The addendum's formulas are correct. The script's `D_MIN/D_MAX` are not. |
| missingness/failure | **PASS IN PRINCIPLE / REVISE STATE MACHINE** | Administrative missingness blocks claims; behavioral no-action is zero. Post-dispatch infrastructure and terminal-service semantics remain ambiguous. |
| five-rung fixed sequence | **PASS** | It controls the five named superiority sentences and correctly requires `D`, beneficial `W_P`, absolute P1 gain, package gain, then terminal outperformance. |
| primary power claim | **REVISE — BLOCKING** | Published Monte Carlo rows reproduce, but the named shapes are not an envelope and the SD-UCB prerequisite is undefined. |
| plateau IUT | **PASS** | R0 certificate, TOST equivalence, paired headroom, positive P1 late gain, and late interaction form a valid sixth gated composite. |
| diagnostic multiplicity | **PASS WITH NARROW REPAIR** | A separate two-hypothesis Holm family is appropriate; exact p-value/tie/success bytes remain to be printed. |

## 1. Root `Q`, independence, and generalization

Section 2 is a material improvement and is statistically coherent. It binds
twelve matched nursery packets, uniform sampling of 56 unique deployment
programs, a uniform permutation into disjoint 48/8 wake/probe decks, identical
within-root opportunities for all services, independent draws with replacement
across roots, a one-row-per-root reducer, and the correct conditional scope.
This supports inference over task/life realizations from the registered `Q`,
not over parents, child checkpoints, or deployment domains.

The v2 source binding should still include the exact finite eligible universe
hash and its cardinality, the structural-rejection predicate and maximum
candidate-stream behavior, and the probability law for nursery generator
parameters. Those are ordinary manifest closures; the statistical object is
now correct.

## 2. KDF and coupling — three exact contradictions

The coupling table itself is good: P/U nursery calls, all-service wake calls,
and same-cut probes share random opportunities; cuts use distinct probe
uniforms; P0/P1 and U0/U1 cache common entry evaluations; structurally absent
calls cannot shift a stream. This is the correct common-random-numbers design.

The concrete KDF does not yet implement the stated root packet:

### 2.1 The 256-bit root master is unused

`Q` contains “one root ID and 256-bit root master,” but the HMAC key is the
global `protocol_hash` and the message contains only `root_id` plus event
fields. The root master has no effect on any task, deck, or call. Either remove
it from `Q` or use it in a defined hierarchy, for example:

```text
root_master_r = HMAC-SHA256(protocol_hash_bytes,
                            canonical_json([split, root_id, "root_master"]))
event_digest  = HMAC-SHA256(root_master_r,
                            canonical_json([domain, matched_opportunity_id,
                                            stage, call_slot, sample_index,
                                            purpose]))
```

If root masters are externally sampled instead, bind their sampling source,
precommitment, uniqueness, and receipt. Do not claim both an independent root
master and a deterministic global-key derivation while using only the latter.

### 2.2 `split` was dropped

The repaired tuple in the synthesis contained `split`; the executable message
does not. If `root_id` values recur in development, pilot, confirmation,
certificate, or diagnostics, identical event tuples reuse seeds across splits.
Put `split` back in the root-master or event derivation, or prove root IDs are
globally unique across every named split and bind that law.

### 2.3 The collision rule checks the wrong thing

Matched calls are required to share the same key and therefore the same full
digest. A roster containing individual P/U or five-service calls will
intentionally contain repeated digests, contradicting “rejects any repeated
complete digest.” Conversely, execution uses only `digest[0:8]`; two distinct
digests can collide on `seed_u64` and pass the current check.

Represent each intended coupling group once, map all member calls to that
group, assert exact digest equality within the group, and reject repeated
`seed_u64` values **between distinct groups**. Receipt both the 256-bit digest
and executed 64-bit seed. Freeze canonical integer/string encoding, the
NumPy/backend seed-range conversion, and the coupling-group membership table.

The backend canary must do more than “replay equality or disclose” a boundary.
For any nondeterministic backend, state whether common random numbers are
actually honored and what statistical marginal remains. Disclosure alone
cannot certify paired coupling.

## 3. Score, cut, and gain-AUC algebra

The score is now executable in principle:

```text
v = max(0, min(1, (I_base-I_best)/I_base)),  I_base > 0;
V = mean of the eight registered probes.
```

The unchanged base pipeline as a legal incumbent makes no valid improving
dispatch score zero without treating it as missing. The order wake ->
active-text attempt -> SLEEP commit/quarantine -> probes is clear. Cached entry
measurements remove avoidable P0/P1 and U0/U1 Monte Carlo noise. Probe
noninterference is explicit.

The trapezoidal formula remains correct because `G(0)=0` and the three
intervals have equal length:

```text
gAUC = [2G(16)+2G(32)+G(48)]/6.
```

The five causal/package/absolute contrasts also have the meanings claimed.

One sensitivity detail remains undefined. Section 4 defines cellwise `HG`,
but not the headroom-normalized gain-AUC, `W_P`, `W_U`, or `D` to report. Bind
the exact descriptive reducer, e.g. replace each `G_c,r(t)` in the same
gain-AUC/interaction formulas with `HG_c,r(t)`. Report denominator-floor use
and never make this sensitivity an alternative primary.

## 4. The script's feasible `D` range is wrong

The script sets

```text
D_MIN = -10/3
D_MAX =  10/3.
```

That would be the naive range from subtracting four unconstrained gain-AUCs.
The addendum, however, caches an identical cut-0 value within P0/P1 and within
U0/U1. Those entry terms cancel inside each write contrast:

```text
W_P = [2(V_P1,16-V_P0,16) + 2(V_P1,32-V_P0,32)
       + (V_P1,48-V_P0,48)] / 6,
```

so `W_P` and `W_U` each lie in `[-5/6,5/6]`. Therefore

```text
D in [-5/3, 5/3].
```

The wrong clipping boundary affects only extreme t5 draws in the current
planning grid, so it does not materially change the printed pass-probability
ranges at four decimals. Recomputing with the correct bound gave the same
reported `.8695--.9072` range at SD `.10` and the same minimum `.7972` at SD
`.125`. It nevertheless makes the script's algebra, metadata, extrema, and
claimed “feasible range” false. Repair the constants and add deterministic
unit assertions deriving bounds from `V in [0,1]` plus cached-entry equality.

The script otherwise reproduces its published values: its t critical value is
the df-31 two-sided 95% value; t5 and beta standardizations are correct; the
`p=.20` two-point family has mean zero and variance one; and the joint pass
rule matches Section 5.

## 5. Power claim — the Monte Carlo is reproducible but not an envelope

The exact default run reproduced the addendum's numbers:

- at mean `.070`, SD `.10`: joint pass `.8695067--.9071567` across the five
  named shapes;
- at mean zero, SD `.10`: joint pass `.00144--.0058867`;
- at mean `.070`, SD `.125`: minimum joint pass `.79719`.

This fixes the v1 error of claiming 80% power at a true effect exactly equal to
the `.05` observed-effect threshold. Fixed `N=32` also removes the type-I and
routing ambiguity of adaptive N. Calling only the primary powered and later
rungs precision-gated is correct.

The five shapes are sensitivity examples, not a mean/SD “envelope.” An
admissible two-point root distribution with

```text
P(D = 0.0817420) = 0.9864
P(D = -0.7816420) = 0.0136
```

has mean approximately `.070`, SD approximately `.10`, and lies wholly inside
the correct feasible `[-5/3,5/3]` range. Under the exact N=32 t-interval plus
`estimate >= .05` rule, its pass probability is approximately `.6452055`.
Most samples contain no rare bad root and pass with zero sample variance; one
rare bad root generally destroys the lower bound. The script's only two-point
case uses the opposite, much milder `p=.20` high-tail mixture and reports
`.9072`.

Therefore Section 6 may say:

> The estimated joint pass probability was 86.95%--90.72% under five named
> planning distributions at mean .070 and SD .10.

It may not say “designed for at least 80% power under the declared mean/SD
sensitivity envelope” unless the envelope explicitly excludes the admissible
rare-catastrophe shape and gives a scientific reason. Better repairs are to
add a two-point probability grid and other rare-failure mixtures, use a frozen
empirical mixture justified by genuinely representative preconfirmation
roots, or narrow “power” to conditional planning sensitivity under the five
named shapes. Mean and SD alone cannot guarantee the claimed power.

The script labels pre-clipping inputs `true_mean` and `true_sd`, although
clipping changes them for extreme t5 draws. Rename them `requested_mean` and
`requested_preclip_sd`, or generate distributions satisfying the exact
post-clipping moments. The disclosed empirical moments make this a minor
metadata defect rather than a hidden numerical error.

### Undefined SD prerequisite

The addendum permits powered language only if “development” supplies a
one-sided 80% upper confidence bound on `SD(D)` no greater than `.10`, but it
does not name which roots enter, how many there are, the bound equation, its
distributional assumption, or an executable reducer/receipt. The power script
does not compute it. Two development plus four spending-pilot roots would be a
very weak and potentially workflow-selected variance basis; two roots alone
are plainly inadequate.

Bind the exact preconfirmation sample and status, SD estimator, upper-bound
formula, missingness law, and hash-frozen output. If the bound uses a chi-square
formula, name the normality assumption and add robust sensitivity; an 80%
confidence bound is a planning screen, not proof that true SD is at most `.10`.
Alternatively delete this label switch and report the five-shape N=32 planning
sensitivities unconditionally as assumptions, without “at least 80%” wording.

## 6. Failure and missingness — major repair passes, state-machine closure remains

Section 7 fixes the dangerous v2-synthesis rule that set an administratively
missing control cut to zero. It now distinguishes observed no-action behavior,
protocol-defined service failure, and external administrative missingness;
blocks `D` when any P/U primary cut is administratively missing; blocks public
and plateau claims when R0 is missing; prohibits root replacement; and keeps a
quarantined adapter at its prior committed state. This is conservative and
coherent.

Two boundaries should be exact before source binding:

- A host/storage/backend failure remains infrastructure missingness even if it
  occurs after request dispatch unless a valid response/system failure event
  was durably committed. Section 3 currently makes *any* post-dispatch
  interruption an assigned system event, while Section 7 calls host loss only
  before a committed request administrative. Do not let host timing relabel
  infrastructure failure as agent performance.
- Enumerate the state machine deciding quarantine-and-continue versus
  terminal-service failure. “Nonfinite candidate fit,” “failed transactional
  canary,” and “failed mount” can either preserve the previous adapter or end
  the service; the choice cannot be made after its effect on `D` is known.

The deterministic 100% provenance/firewall/resource and transactional canary
gates solve the former non-erasure multiplicity problem. Descriptive routing,
proposal, DREAM, and generic-quality reports create no additional hypothesis
family as long as the manuscript makes no superiority/non-inferiority claim
from them.

## 7. Five-rung fixed sequence — PASS

Each rung now explicitly requires a two-sided 95% root-level Student-t lower
endpoint above zero plus its frozen observed practical margin, and testing
stops permanently at first failure. Sequentially testing

```text
D -> W_P -> L_terminal -> C_public -> T_R0
```

at alpha `.05` strongly controls the familywise error for those five
superiority sentences. The point-estimate margins only make release more
conservative. The sequence correctly prevents a less-harmful-but-still-harmful
write effect, no absolute P1 improvement, deployment-gain-only advantage, or
terminal package deficit from being called the full result. `P1-R0` remains
explicitly noncausal for parenting.

The common `.05` margin is acceptable only if the promised three separate
development justifications are actually source-bound. Rungs 2--5 are honestly
called precision-gated rather than powered. Passing `D/W_P/L_terminal` still
identifies a total parenting-by-write pathway that may be mediated by inherited
entry competence and better later data; it does not isolate a pure learning-
rate parameter. The manuscript consequences should preserve that boundary.

## 8. R0 local-plateau composite — PASS

Section 8 closes the prior plateau defects:

- R0 is prospectively selected and must first earn the strong-memory label;
- its own adjacent increments are tested by two alpha-.05 TOST procedures via
  90% two-sided intervals inside `[-.05,.05]`;
- root-paired search headroom `H` needs a one-sided lower bound above `.10`;
- P1 must improve in the last era;
- the late P1-minus-R0 increment must be positive with estimate at least `.05`;
  and
- the composite is attempted only after all five prior rungs pass.

Because the released sentence is a conjunction and its null is the union of
component failures, requiring every component test to reject at alpha `.05`
is a valid intersection-union test. Making it the sixth fixed-sequence rung
preserves familywise control with the five superiority claims. The wording is
properly restricted to a local 16--48 plateau under this resource envelope,
not saturation.

## 9. Terminal diagnostic multiplicity — PASS WITH EXACT-BYTE CLEANUP

The addendum now supplies failure-inclusive root estimands, zero contribution
when an intervention is infeasible, no favorable root filtering, administrative
missingness blocking, practical margins, locked N, and a two-hypothesis Holm
family. This is the correct disposition for two secondary claims on the same
roots. Keeping the family separate from the headline and calling it
precision-gated is transparent; it does not alter headline family control.

Before execution, print the one-sided root-level Student-t p-value definition,
Holm ordering/tie rule, adjusted rejection thresholds (`.025`, then `.05` for
two ordered p-values), and the requirement that each released claim also has
its own point estimate at least `.05`. Freeze the exact bucket/cycle
derangement and terminal-failure reducers. If a global across-all-paper-claims
FWER is intended rather than named-family control, the secondary alpha must be
allocated from that global family; the current bytes claim only separate
headline and diagnostic families.

The interpretation limits are correct: `K_link` concerns the explicit
active-text one-hop layer, `K_binding` concerns fixed-history terminal
compilation, and neither establishes compression, a graph inside LoRA, or the
online mediated effect.

## Required repairs before PASS

1. Correct the feasible `D` range to `[-5/3,5/3]` in the script and tests.
2. Narrow the power sentence to the five named shapes or add adverse
   rare-failure mixtures; do not claim an 80% mean/SD envelope.
3. Make the root master/KDF hierarchy coherent, restore split isolation, and
   validate executed 64-bit seeds by intentional coupling group.
4. Bind the SD-upper-bound sample, formula, assumptions, reducer, and receipt,
   or remove it as a powered-language gate.
5. Define the headroom-normalized `D` sensitivity reducer.
6. Reconcile post-dispatch infrastructure missingness and freeze the
   quarantine/terminal state machine.
7. Print the exact Holm p-value and tie/release law.

Items 1--4 are statistical source-binding blockers. Items 5--7 are narrow
executable-contract repairs. After them, the v2 addendum and power receipt are
ready for one more fresh read-only statistics audit; they still authorize no
implementation or scientific execution.
