# Constructibility audit: RML-D0 world candidate A

**Audited artifact:** `rml_d0_world_candidate_A.md` (`RML-D0-FT-A-V1`)  
**Audit scope:** finite mathematics and CPU constructibility only  
**Verdict:** **not constructible as written.** Two independent acceptance
predicates make the accepted pair/target set empty. Several generator,
posterior, source-reset, and certificate representations are also not specified
well enough to admit one authoritative implementation. The elementary counts
are otherwise mostly consistent.

## 1. Arithmetic that does close

### Source events and local edges

A dense module has

```text
1 + 8 + 16 + 16 = 41 events
3 + 1 + 4 + 3 + 1 = 12 witnessed edges.
```

A C-sparse module removes two conditioner trials and one edge, giving 39
events and 11 edges. A V-sparse module removes four valve trials and one edge,
giving 37 events and 11 edges. With one five-event bridge in E1--E3, the era
increments are therefore:

| Era | Event calculation | New events | Edge calculation | New edges |
|---|---:|---:|---:|---:|
| E0 | `3*41` | 123 | `3*12` | 36 |
| E1 | `41+39+37+5` | 122 | `12+11+11` | 34 |
| E2 | `4*41+39+37+5` | 245 | `4*12+11+11` | 70 |
| E3 | `10*41+39+37+5` | 491 | `10*12+11+11` | 142 |

Thus cumulative events `[123,245,490,981]` and cumulative witnessed edges
`[36,70,140,282]` are correct. Twenty-four modules contain 288 possible local
edges; the six sparse omissions explain `288-6=282` witnessed edges.

The commitment counts also close: the next eras contain 3, 6, and 12 modules,
and two schema components per module give 6, 12, and 24 predictions. At least
two confirmations per channel are available in each new era despite the two
complementary sparse omissions.

### Affine laws and local-assignment count

`|GL(2,2)|=6`, so each affine channel has `6*4=24` laws. The three descriptor
points `00,01,10` are affinely independent and determine an affine map exactly.
For each module, each ordered three-of-four injection has `4P3=24` choices and
the exchanger permutation has `4!=24`, so

```text
24 * 24 * 24 = 13,824
```

is correct.

The stated output maps are involutions and preserve the local combinatorial
classes. `tau_C` and `tau_V` are output XOR translations, so they preserve an
affine matrix and change only its translation. The DEV/holdout matrix sets are
therefore closed. This algebraic closure does not cure the target and bridge
contradictions below.

### Target length and cardinalities

The registered target plan has nine actions, and the two different-bit SET
operations commute. The ten-action cap allows one redundant/logistical action
without admitting a shorter intended plan, provided the stated unique-pair
certificate is actually checked.

The CPU primary cardinality is correct:

```text
64 pairs * 2 twins * 3 cuts * 4 strata * 2 targets = 3,072.
```

The stated R total is also arithmetically correct **if R exists only at
K1--K3**:

```text
64 * 2 * 3 * 2 = 768.
```

The nearest-rank 90th percentile over 64 values is element
`ceil(.9*64)=58`, as stated.

## 2. Empty-set contradictions

### A. No primary target can be accepted in both twins

Let the public initial coolant be `u=(u_v,u_i)`. The structural target rule
requires two transforms that set different bits, with each set value different
from its initial value. Therefore the exchanger requirement in the authentic
world must be

```text
x = u xor 11.
```

The current dagger preserves `u` but applies `tau_X(x)=x xor 10`. Hence the
twin requirement is

```text
x' = (u xor 11) xor 10 = u xor 01.
```

Its viscosity bit equals the initial viscosity bit. It therefore cannot have a
correct pair whose two different-bit transforms both set values different from
the initial state. Equivalently, a one-bit-away requirement cannot require the
specified two useful conditioners or have a shortest successful path of nine.
Because target proposals must satisfy the predicates on both twins, every
primary proposal is rejected. The 4,096 proposal cap cannot change this.

**Minimal repair:** make the exchanger part of dagger the identity
(`tau_X(x)=x`). With the same initial state, both sides then require the
two-bit complement. `tau_C` makes the authentic pair wrong on the twin side;
an inventory containing the two counterpart setters can supply a disjoint twin
pair. This retains the conditioner and valve counterfactuals and the demanded
different valve mode. Any nonzero fixed XOR on the exchanger requirement is
incompatible with the present two-bits-must-change predicate while initial
target bytes collide.

### B. The five-event bridge cannot pass on both twins

Both bridge RUNs use the same fixed `BYPASS` configuration. For their outcomes
to differ, the new valve family's hidden required mode must be `BYPASS`;
otherwise both RUNs trip regardless of coolant. But `tau_V` maps `BYPASS` to
`RECIRCULATE`, with no fixed point. Thus if the authentic side can have one
stable and one tripped RUN, the twin has two tripped RUNs. Reversing the side
does not help. The bridge acceptance predicate is empty independently of the
target contradiction.

**Minimal repair:** retain five events but configure a `tau_V`-paired mode in
the second trial, for example `BYPASS` in trial A and `RECIRCULATE` in trial B,
and state the exact accepted outcome/state relation on both sides. This repair
must be checked together with the repaired `tau_X`; merely changing the words
"fixed BYPASS" is insufficient. If the bridge is meant to prove conditioner
causality rather than merely connect old and new objects, that causal predicate
also has to be stated, because “the two RUN outcomes differ” can be caused
solely by the two valve settings.

Until A and B are repaired, pair scanning necessarily exhausts every slot.

## 3. Source schedule is counted but not executable yet

The 41/39/37 event arithmetic assumes one action per valve mode trial. Under the
transition law, however, a RUN uses the current valve mode and setting a mode
requires a CONFIGURE action. If each of the 16 dense valve trials executes
CONFIGURE and RUN, the valve panel has 32 events rather than 16. Similar reset
state is implicit for the conditioner and exchanger trials, and APPLY/RUN
require position `PLANT` even though the public layout is a bench.

The minimal count-preserving repair is to say that every panel row is a fresh
diagnostic episode, normatively define its complete initial public state, and
make the tested valve mode, coolant reset, certified bypass, inventory, and
`position=PLANT` episode-initial state. Then the recorded valve/exchanger row
can be one RUN and the conditioner row one APPLY. The module OBSERVE event,
episode/event handle allocation, reset boundaries, action counts, and canonical
row order also need a literal table or pseudocode. Without this, two conforming
implementers can produce different actions and bytes while both matching the
headline counts.

“Source marginals match” also needs an exact object. Per-position event lengths
cannot match under `tau_C`: for example a SET-to-LOW result becomes SET-to-HIGH,
and `LOW` and `HIGH` have different byte lengths. A histogram can match after a
balance filter, but a chronological vector cannot. The protocol must specify,
at every target-visible cut, whether it compares a histogram, sorted multiset,
per-result histogram, total, or chronological vector. Cutwise comparison is
necessary; final-life equality alone can leak the twin side at K1 or K2. The
same cutwise definition is needed for action kinds, result codes, and family
counts.

## 4. Target construction and exact certificates are underspecified

The finite predicates are clear enough to test a fully formed target, but the
proposal-to-target map is absent. A normative algorithm must define at least:

- which eligible persistent families occupy the four inventory positions for
  N/O/J/P and whether repetition is allowed;
- how initial coolant, loop/exchanger/valve family, public layout variant,
  instance handles, and goal handle are obtained from proposal words;
- the exact label/counter consumption order, including rejected proposals;
- the two target ordinals' relationship and all freshness/uniqueness sets;
- the canonical legal-action list and action-byte tie order in every state.

The generic SHA word sampler and the phrase “public descriptor/layout
proposals” do not determine these choices. Consequently target acceptance
probabilities, 4,096-counter exhaustion, first-accept conditioning, and the
fixed deck cannot currently be reproduced.

The planner is finite, but “records all reachable states ... every legal
action, canonical successor bytes” does not define a compact certificate
encoding. With 3,072 primary items, the 2 GiB sealed cap provides only about
683 KiB per item before sources, gates, manifests, and diagnostics. Materializing
canonical successor bytes for every edge is very unlikely to fit. The minimal
repair is a normative content-addressed/template-deduplicated proof format (or
a replayable certificate containing state/action hashes plus a verifier), with
an explicit byte accounting bound. The target transition graph can be shared
by quotient/template where only handles differ, but the present text neither
authorizes nor defines that sharing.

## 5. P's four-way statement needs a probability space

The ordinary prior does not sample `VF[m,S]` as a fourth independent local
edge: its value is supplied by the affine law. Therefore, after “the schema
grammar and atom are removed,” the document has not defined what completion is
being counted. Removing a relation from a model is not itself a prior over the
four replacement values.

The minimal repair is to define an explicit atoms-only ablation measure. For
example: retain all witnessed atoms and target acceptance facts, replace the
single omitted `VF[m,S]` by one independent uniform four-valued edge, rerun the
same structural conditioning, and require equal nonzero integer completion
counts for all four values. State whether first-accept selection and twin-side
mixing are included in those counts. `WITNESS-GRAPH` and the P certificate must
use that same measure. Only then is “four equiprobable” an exact claim rather
than an intended symmetry.

## 6. BAYES-N is finite in state labels but not algorithmically specified

The quotient cardinality bound

```text
4^4 * 4 * 4 = 4,096
```

is correct. It bounds the number of latent target-local truth classes, not the
cost of assigning their initial masses or the number/size of reachable belief
states.

Three missing definitions prevent the required posterior from being computed:

1. **The Bayesian sample space.** The protocol root is public and all streams
   are deterministic SHA computations. A controller that knows the complete
   generator can in principle regenerate the finite split, and a unique goal or
   item handle can identify its registered item. Conversely, treating namespace
   streams as independent random variables gives the intended product prior,
   but that probability law is not the same as conditioning on a known fixed
   root. “Does not see seed/pair slot” is a process permission, not a finite
   probability measure. This affects BAYES-N and every “Bayes-optimal” leakage
   probe.

2. **The selection kernel.** A target is first-accepted within a pair candidate,
   and a pair is itself first-accepted after bridge, marginal, collision,
   all-target-existence, and certificate filters. The text requests an
   “unsimplified finite geometric” target likelihood but does not give the
   proposal distribution, independence assumptions, side/slot/ordinal mixture,
   or the pair-level first-accept likelihood. The pair filter couples up to 24
   module-local assignments and every target slot, so a product-prior slogan
   does not supply the needed integer completion counts.

3. **The exact counting recurrence.** Enumerating the raw prior is impossible:
   it contains `24^2 * 13,824^24` hidden assignments before proposal and
   first-accept variables. A factorized dynamic program may exist because each
   target touches few modules, but no factors, separators, memoization key,
   or proof that the pair-wide acceptance event preserves the proposed 4,096
   quotient is specified. The demanded equality between an unsimplified and a
   symmetry-reduced posterior is therefore not an implementable test yet.

The minimal repair is a normative finite generative measure (including how
handle streams are marginalized and kept ancillary), literal target and pair
selection kernels, and a specified integer factor/counting recurrence with
golden tiny cases. It must explicitly mix hidden twin side and any hidden slot
or ordinal variables. Publishing a replay seed is compatible with audit only
if reference controllers are defined against a separate, explicit ex-ante
measure and cannot turn the public seed/manifest into an answer lookup; the
current text conflates those two roles.

## 7. Resource ceiling is not established

The target-attempt maximum is double-counted. A target proposal is accepted
once for a pair and copied to both twins, so there are

```text
64 * 3 * 4 * 2 = 1,536 pair-common target slots
1,536 * 4,096 = 6,291,456 maximum proposal attempts,
```

not `3,072*4,096 = 12,582,912`. If proposals are instead independently scanned
per twin, that contradicts “accepted once and copied to both sides.” Use the
pair-common count in the resource contract and separately count the 3,072
evaluated item copies.

The R schedule also conflicts textually: “K0 contains R” and “two ... per cut”
suggest four cuts, while 768 diagnostics and “R fixtures per cut/twin” use
three. Minimal repair: state that scored/generated R fixtures are K1--K3 only,
or change the total to 1,024 and the resource cap accordingly.

The remaining limits are ceilings, not feasibility proofs:

- 25 million Python cache entries containing tuples, big integers, and reduced
  fractions can by itself exceed 8 GiB depending on representation;
- 200 million Python-level transitions plus exact rational Bellman operations,
  target generation, pair scans, certificates, probes, and artifact I/O has no
  demonstrated two-hour upper bound;
- a worst-case pair scan can invoke expensive target/certificate checks on up
  to 4,194,304 CPU candidates; no staged rejection algorithm or operation bound
  is specified;
- the 2 GiB proof-tree problem noted above is independent of RAM and time.

Minimal repair is not to relax the ceiling. Add a normative staged generator,
compact proof representation, per-stage operation/memory bounds, and a DEV
preflight that must demonstrate margin under the same four-worker process
model. Also clarify whether the four DEV slots are part of the run that scans
before the 64 CPU slots: the stated 4,194,304 pair-attempt cap covers exactly
64 slots, while split construction says DEV scans first and excludes reused
orbits.

## 8. Minimal ratification patch set

No implementation authority should be granted until one revision does all of
the following:

1. Set `tau_X` to identity (or redesign both the target minimality predicate
   and public-initial collision; identity is the smaller repair).
2. Replace the fixed-single-mode bridge by a fully specified feasible
   `tau_V`-paired five-event bridge and state what causal fact it certifies.
3. Specify fresh diagnostic-episode initial states and a literal source row
   schedule, preserving or deliberately recomputing all event counts.
4. Define cutwise source-marginal comparison objects.
5. Give literal target-proposal construction and RNG/handle consumption order.
6. Define the atoms-only four-way P completion measure.
7. Define BAYES-N's ex-ante sample space, target- and pair-first-accept kernels,
   twin/slot mixture, and exact factorized counting recurrence.
8. Resolve the R-cut and proposal-attempt counts, and define compact planner /
   certificate artifacts with resource accounting.

After those repairs, implementation of parsers, canonicalization, transitions,
and small exhaustive planner prototypes can start. A full split generator or
CPU-gate implementation should start only after the repaired Bayes recurrence
and resource preflight are independently checked: those are mathematical
interfaces, not optimization details. As written, implementation cannot
produce even one accepted pair, so implementation should not start from this
protocol version.
