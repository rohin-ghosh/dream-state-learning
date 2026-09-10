# Adversarial methods review of RML-D0 world candidate A

**Reviewed object:** `rml_d0_world_candidate_A.md`, protocol literal
`RML-D0-FT-A-V1`.

**Review posture:** paper-benchmark methods review of the proposed CPU
instrument, not a code-style review and not implementation authority. This
review compares the candidate with `AGENTS.md`, the pending RML v1 consensus,
`rml_pilot_v1.md`, rendered-lifetime candidates A/B, and research notes 42--48.
It makes no scientific claim and authorizes no implementation or run.

## Executive verdict

**Reject and repair before ratification.** The intended D0 scope is mostly the
right one: CPU only, fixed experience, complete causal-era cuts, exact connected
J, one prospective P construct, no X, no model-native claim, and no route from a
green CPU report to model or GPU work. The claim firewall in section 19 is also
appropriately narrow.

The exact candidate nevertheless cannot generate a single valid pair as
written. There are two independent algebraic contradictions in the twin
coupling:

1. `tau_C`, `tau_X`, the two-bit target predicate, and the disjoint-pair rule
   cannot hold together for any target; and
2. the fixed-BYPASS bridge block cannot have differing RUN outcomes on both
   twins under the fixed-point-free `tau_V`.

Even after those are repaired, the accepted-item Bayes measure, four-way P
ablation, source-marginal equality, target proposal kernel, record schemas, and
RNG draw ledger are not exact enough to support the advertised leakage and
posterior gates. These are benchmark-defining omissions, not coding details.

The smallest defensible disposition is therefore:

```text
preserve the D0 role and claim boundary
-> repair the twin algebra
-> bind the proposal/selection measure and all record bytes
-> strengthen the source-marginal test
-> define P's atoms-only completion experiment
-> make planning state-quotient exact
-> correct counts and resource accounting
-> rerun fresh deliberation and obtain exact human ratification
```

The pending RML v1 consensus remains `human_required`, with implementation
forbidden. Candidate A correctly says it is not implementation authority; this
review does not change that state.

## 1. Fatal scientific flaws

### F1. The accepted target set is empty under the stated twin involution

Let the public initial coolant be `x=(x_v,x_i)` and the exchanger requirement
in `H` be `r=(r_v,r_i)`. Target acceptance requires both useful transforms to
set different bits to values different from the initial state. Because the
state is binary, necessarily

```text
r = x xor 11.
```

The candidate defines

```text
tau_C: complement the set value while preserving the set bit
tau_X: r -> r xor 10.
```

The twin exchanger requirement is consequently

```text
r_dagger = r xor 10 = x xor 01.
```

Its viscosity requirement equals the initial viscosity. Therefore no twin
solution can have both transforms set values different from the common initial
state. This already contradicts the structural predicate that must pass on
both twins.

There is a second contradiction. The public cartridge that sets viscosity to
`r_v` in `H` sets viscosity to `x_v=r_dagger_v` after `tau_C`; it is therefore
required in both correct plans. The correct unordered cartridge pairs share at
least that cartridge, contradicting sections 7, 10, and 13, which require them
to be disjoint.

This is a proof over every possible proposal, not a low acceptance-rate risk.
Increasing the 4,096 proposal cap or 65,536 pair cap cannot help.

**Smallest repair.** Make `tau_X` the identity, retain the fixed-point-free
`tau_C` and `tau_V`, and require each target inventory, in each hidden side, to
contain exactly one realization of each of the four T codes. The original side
then needs the two setters to `x xor 11`; the twin needs the two public
cartridges whose original codes set back to `x`, because `tau_C` turns them
into the required setters. The pairs are disjoint, both twin solutions change
both bits away from the initial state, and the valve action still differs.
The exchanger need not change for the overall hidden mechanism and correct plan
to differ.

Do not instead merely relax “disjoint” to “different.” That would leave the
first contradiction and weaken the registered twin intervention.

### F2. The bridge acceptance rule is independently impossible

Each bridge trial configures the same public valve to `BYPASS`. RUN outcomes
can differ between treated and untreated coolant in a side only if the valve
requirement is `BYPASS`; otherwise both RUNs trip before coolant compatibility
can matter. But `tau_V` maps `BYPASS` to `RECIRCULATE`. Thus:

- if the authentic side can show the requested treated/untreated contrast, the
  twin's two RUNs both trip; and
- if the twin can show it, the authentic side's two RUNs both trip.

No pair can satisfy “the two RUN outcomes differ on both twins.” This is
independent of F1.

The treated-versus-untreated design also remains unsuitable after changing
`tau_X`: for complementary SET transforms, one side's transform is necessarily
a no-op on the common untreated value.

**Smallest repair.** Replace each bridge with two reset `EXCHANGER_BENCH`
trials using the already declared certified bypass valve. Apply two distinct E0
conditioners that implement complementary setters on the same bit, then RUN the
same recent exchanger from the same reset coolant. Require stable/tripped to
swap across those two old conditioners in both twins. With `tau_X=identity`,
`tau_C` swaps which old conditioner supplies the accepted value, so the
interaction remains diagnostic in both sides without a valve-mask confound.

A clean block is four events:

```text
trial A: APPLY old conditioner A; RUN recent exchanger bench
trial B: APPLY old conditioner B; RUN recent exchanger bench
```

Both trials must have fully specified reset state, position, inventory,
certified-bypass state, and episode boundary. If this four-event repair is
adopted, the cumulative event counts become `[123,244,488,978]`; witnessed-edge
counts remain `[36,70,140,282]`. Do not preserve the old counts with a padding
observation and then count it as causal growth.

### F3. P's “four equiprobable values” is not yet a defined scientific control

The candidate alternates among three different objects:

1. the actual accepted-world prior, in which `VF[m,S]` is determined by the
   affine law;
2. `WITNESS-GRAPH`, an algorithm denied both grammar and schema atom; and
3. a counterfactual “structural completion” in which the grammar and atom are
   removed.

Removing a grammar from a model is not itself a probability measure. The
candidate does not say which worlds remain legal, whether the target and pair
first-accept filters are rerun, what is held fixed, or why the four substituted
valve modes retain equal mass after selection. Consequently the certificate
cannot establish a four-way posterior, and the WITNESS-GRAPH ceiling cannot be
interpreted as a Bayes ceiling.

**Smallest repair.** Define a named `ATOMS_ONLY_COMPLETION` experiment. For a
sealed accepted P target, hold all public bytes, witnessed edges, target-local
conditioner/exchanger truth, and logistics fixed; replace only `VF[m,S]` by each
of the four modes under an explicitly uniform counting measure; do not require
those four completions to satisfy the affine grammar; and prove that target
selection and every visible projection are invariant to that substitution.
Call this a model-class ablation, not the posterior under the actual affine
prior. Then:

- `WITNESS-GRAPH` is the optimal controller under this declared ablation;
- `PROGRAM-SEARCH` is the optimal controller under public grammar plus legal
  history; and
- `SCHEMA-GOLD` is a supplied-atom ceiling.

If the intended claim is instead a posterior under the actual generator prior,
the grammar may not be removed, and exact marginal inference must be used; in
that case four-way equality is generally a theorem to prove, not an acceptance
predicate to assert.

## 2. Exact-spec bugs that block reproducible methods

### E1. The public, hidden, selection, proof, score, and audit schemas are not bound

Section 3 gives useful field lists and canonicalization rules, but it does not
define complete JSON schemas for actions, events, source-episode resets,
snapshots, schema commitments/statuses, target manifests, pair candidates,
rejection receipts, certificates, beliefs, scores, resources, or the terminal
report. Section 17 proposes that an implementation create
`rml_d0_objects.schema.json`; that leaves benchmark-defining bytes to the
implementer.

This fails the RML consensus requirement to bind canonical public, hidden,
selection/pairing, proof, score, and audit records with exact writers and
visibility. It also makes “target-visible byte collision” ill-defined because
the complete target-visible record is not enumerated.

**Repair:** include a normative schema bundle and golden canonical bytes/hashes
in the deliberated design, before implementation authority. For every field,
bind its writer, reader set, taint, lifecycle, and inclusion/exclusion from the
target-visible collision projection. The implementation may validate those
schemas; it may not invent them.

### E2. The RNG algorithm lacks a normative draw ledger and uses a publicly enumerable root

The namespace formula is exact only after every ordered label, counter, word
index, Fisher--Yates order, collision retry, and proposal-field decoder is
specified. Those mappings are absent. In particular, the plan does not define
how counter `c` becomes a complete target proposal or a complete world
candidate. Uniform component priors do not determine a unique serialized deck.

There is also a scientific mismatch between exact Bayes and the fixed public
root. Domain-separated SHA-256 streams from one published root are
deterministic, not information-theoretically independent. A generator-aware
exact controller can enumerate slot/counter candidates and use public handles
to recover latent slot, target ordinal, or proposal information. Merely saying
that BAYES-N “does not see” a seed does not remove information derivable from a
seed printed in the protocol. This directly conflicts with candidate B's
requirement that nuisance handles/order not be deterministic functions of one
enumerable master seed.

**Repair:** bind a field-level draw ledger and use independently sampled
256-bit namespace keys, committed before construction and held scorer-only
until the CPU evaluation seal. Define BAYES-N over the uniform key
distribution and marginalize the keys; reveal them afterward for replay. The
protocol hash remains public domain separation, not the random key. A weaker
computational-pseudorandomness assumption would need to be stated explicitly
and would no longer justify calling the controller exact Bayes.

### E3. The accepted-item Bayes conditioning is incomplete and “finite geometric” is unjustified

The posterior must condition on more than the first successful target proposal.
At minimum it depends on:

- world-pair first acceptance within the slot;
- all earlier rejected pair candidates;
- exclusion of twin orbits already used by earlier slots;
- the preassigned matrix roster;
- all target-existence predicates used to accept the pair;
- all earlier target proposals and within-pair uniqueness constraints;
- hidden cut, stratum, ordinal, side, and slot, none of which is public; and
- the current target's complete visible bytes and within-item outcomes.

Candidate proposals are not shown to be IID with a constant acceptance
probability. Uniqueness and prior accepted targets make them history-dependent.
Therefore a geometric likelihood is not licensed. Nor is it shown that global
selection conditioning factorizes into integer completion counts over the
4,096-state target-local quotient.

**Repair:** replace “finite geometric” with an exact ordered selection
recurrence over the fully specified proposal decoder. State one pre-split
epistemic experiment for BAYES-N, explicitly marginalize every hidden selector
listed above, and prove the target-local quotient is sufficient despite the
global selector. Add brute-force equality tests on reduced toy universes and a
symbolic/factorized proof for the production universe. If the proof does not
factorize, simplify the selector rather than approximating the posterior.

### E4. “Source marginals match” is weaker and less exact than the stated control

The registered match covers action-kind counts, result-code counts, byte
lengths, and module/descriptor counts. It does not bind the histogram of public
gauge values, state deltas, modes, stable/tripped outcomes within bench type,
or other rendered substitutions. Those are precisely the nuisance signatures
a marginal-matched twin is meant to equalize. Equal byte length is not equal
public outcome marginal.

**Repair:** define one canonical binding-erased source projection and require
exact multiset equality per era and bench/relation type. Replace opaque handles
by their kinds, erase only the family-to-outcome association and chronology,
and retain all public enum values, result codes, state deltas, and rendered
template substitutions. Authentic history may differ in bindings and order;
its binding-erased histogram may not differ. Run the source-action and passive
probes on this exact projection as well as their existing projections.

### E5. The prospective schema lifecycle is conceptually sound but not byte-exact

The good part is preserved: E0's three noncollinear descriptor points identify
an affine law; the reference commits before E1; later ordinary outcomes can
append only match/contradiction; support requires two new modules; and P stays
handle-local sparse. This satisfies chronology in principle.

What remains undefined is the exact commitment object, scheduled next-era
record, fixed proposal count, deadline, comparator input, append-only status
transition, contradiction behavior, and ordering between world construction,
schema commitment, target creation, target-manifest sealing, and pair
acceptance. “No P target exists at proposal time” must be a hash-chain/runtime
fact, not only a process-visibility assertion.

**Repair:** bind the append-only state machine and canonical records. Require a
sealed chronology receipt proving

```text
next-era schedule seal
< schema commitment seal
< confirming source outcome
< support status append
< P target proposal/manifest creation
< evaluation
```

If targets are pre-generated for pair acceptance, replace “does not exist” by
the weaker and accurate “is sealed, target-process-only, and unreadable by the
schema process,” and do not claim literal prospective creation.

### E6. J is connected, but its registered deletion object is ambiguous

The J target itself is a valid minimal D0 connected join: the E0 conditioner
changes the same coolant charge later consumed by the recent exchanger RUN;
the two correct transforms affect different bits; and early-only/recent-only
subsets are required to fail. This is materially better than concatenating two
goals.

However, section 13's “J bridge deletion” is not defined. The source bridge
block is not necessarily the target's old-to-new dependency, and deleting an
edge from the transition system has no bound counterfactual semantics. This can
turn a strong certificate into an implementation-dependent one.

**Repair:** define the registered J dependency as the exact target-local E0
conditioner edge and its state-flow edge into the recent RUN. Certify (a)
removal of the E0 cartridge instance, (b) prohibition of that mapping for the
target, (c) recent-only inventory, and (d) E0-only inventory. Rename the test
from generic “bridge deletion” to `J_REGISTERED_OLD_TRANSFORM_CUT`. Keep the
source bridge as a separate era-growth diagnostic.

### E7. Cardinalities and attempt ceilings are internally inconsistent

The primary execution count is correct:

```text
64 pairs * 2 twins * 3 cuts * 4 strata * 2 targets = 3,072.
```

But pair-common target proposals are accepted once and copied to both twins.
There are only

```text
64 * 3 * 4 * 2 = 1,536
```

proposal slots, so their direct maximum is `1,536 * 4,096 = 6,291,456`, not
`12,582,912`. The larger number silently counts the same proposal once per
twin, contrary to section 10.

The R count `768` corresponds to K1--K3 only:

```text
64 * 2 twins * 3 cuts * 2 fixtures = 768.
```

Section 10 also says K0 contains R and says two fixtures “per cut.” If K0 is
included, the count is `1,024`. The protocol must choose one.

Finally, pair-candidate acceptance includes target existence and certificates.
Target attempts made while rejecting pair candidates are not accounted for by
a cap based only on accepted items. CPU split construction also depends on the
four earlier DEV slots through twin-orbit exclusion; its pair-attempt maximum is
68 rather than 64 slots unless DEV is a sealed predecessor.

**Repair:** count proposal attempts at the pair-common slot level, count every
proposal explored for rejected pair candidates, state whether DEV is an
immutable predecessor, and make R explicitly K1--K3-only (smallest change) or
raise its count to 1,024. All resource counters should describe dispatched
work, not only accepted outputs.

### E8. “Enumerate all histories” conflicts with exact planner feasibility

The plan says HW-SOLVE breadth-first enumerates all legal histories and the
certificate records every reachable state, legal action, successor, and
shortest successful histories. Repeated OBSERVE, MEASURE, CONFIGURE, and MOVE
choices make history enumeration exponentially larger than necessary. The
candidate itself says there are more than `10^9` legal ten-action sequences.
This is incompatible with the stated 25-million-state/200-million-transition
envelope if “history” is literal.

**Repair:** define a bisimulation-preserving state quotient and breadth-first
dynamic program over `(public state, hidden target truth or belief, remaining
budget, registered necessity mask)`. Keep one canonical predecessor plus exact
path signatures/counts; do not retain every history string. Prove that the
quotient preserves success value, minimum depth, used cartridge set, valve
mode, and every deletion certificate. Use exhaustive history enumeration only
in tiny property-test worlds.

### E9. The two-hour CPU claim is an unproved feasibility hypothesis

Fail-closed wall/RSS/disk/worker limits are correct governance. The assertion
that standard-library Python can perform up to 200 million transitions, 25
million cached Bellman states, exact rational belief updates, global
selection-conditioned completion counts, pair scanning, certificates, probes,
and artifact sealing in two hours and 8 GiB is not supported by an algorithmic
bound or benchmark. Twenty-five million live Python dictionary entries alone
can approach or exceed the RSS ceiling depending on representation; exact
fractions amplify the risk. The global first-accept completion calculation is
the larger unknown.

**Repair:** keep the two-hour ceiling, but label feasibility unestablished.
Before exact ratification, provide (a) the factorized completion recurrence,
(b) worst-case state/transition and live-memory bounds after symmetry sharing,
(c) a streaming/eviction rule showing that “total cached” does not mean
simultaneously resident, and (d) a deterministic DEV microbenchmark with a
conservative extrapolation. Do not reduce pair/target counts merely to save the
current design. If the exact recurrence cannot fit, simplify the selector or
world before ratification. Remove the sentence that the package can be
implemented and audited “in hours” until evidence exists.

## 3. Acceptable D0 limitations, provided the claim firewall remains literal

### A1. The affine grammar is supplied cognition, not learned abstraction

Three noncollinear E0 points identify each two-bit affine map exactly once the
24-law grammar is supplied. PROGRAM-SEARCH therefore performs interpolation in
a designer-declared hypothesis class. SCHEMA-GOLD is even stronger: it receives
the supported atom. This does not show DREAM discovery, autonomous schema
formation, compression, or held-out-grammar generalization.

That is acceptable for D0 because D0 is only validating that a prospective P
instrument has oracle headroom over a witnessed-edge graph. The candidate's
section 19 mostly says this correctly. The label should nevertheless be
sharpened to **grammar-conditioned prospective edge reconstruction**. A later
learned stage must separately decide whether the grammar is public to the
headline agent, include the explicit program learner as a baseline, and hold
out complete productions or alternative grammar families before claiming
schema discovery or compression.

### A2. The world is stateful enough for a CPU target, but not realistic enough for the paper headline

Target execution has genuine state: travel, inventory, single-use
consumables, two interacting coolant bits, valve configuration, irreversible
RUN failure, and terminal COMMIT. J's old transform and recent mechanism meet
through one coolant state. This is sufficient for the D0 connectedness test.

The source life is nonetheless a collection of reset, nearly exhaustive bench
panels over a small supplied mapping grammar. Logistics contribute six of the
nine minimal actions, while the consequential decision is a cartridge pair
and valve mode. There are no routing constraints, recoverable failures,
exceptions, information-seeking policy, or persistent physical degradation.
Thus a green result would not validate RML's rendered-world realism or
stateful developmental interpretation. That limitation is acceptable only
because X, on-policy acquisition, model behavior, and paper claims are all
deferred. The later gold/text proposal must reassess whether these same D0
events are an adequate model-facing semantic action stream rather than inherit
that conclusion from CPU conformance.

### A3. Fixed source actions cannot establish the experiential flywheel

The deterministic source schedule is correctly target-, outcome-, memory-,
and admission-blind. This is desirable for common-experience attribution and
CPU isolation. It cannot show that memory changes evidence acquisition or that
later experience improves. Notes 42--48 and both rendered-lifetime candidates
are explicit on this distinction. Candidate A's no-model/no-claim boundary
makes the limitation acceptable.

### A4. One pack, no native-context axis, no X, and no model are proper D0 scope

The RML consensus specifically selected complete causal-era cuts, R/N/O
diagnostics, indispensable J/P, and deferral of X and the native-context axis.
The absence of three non-isomorphic packs, actual `L_native` cuts, learned
writers, THINK/DREAM/SLEEP, LoRA, locked confirmation, and on-policy collection
is therefore not a defect in this D0 candidate. It becomes a defect only if a
later artifact treats D0 as evidence for any of those claims or routes around a
new predecessor-bound human decision.

## 4. Itemized audit against the requested breakpoints

| Breakpoint | Verdict | Minimal disposition |
|---|---|---|
| Twin coupling | **Fatal** | Set `tau_X=identity`; enforce four-code target inventories; redesign the bridge contrast. |
| Source marginal equality | **Exact-spec failure** | Bind a per-era, binding-erased full public-outcome histogram, not lengths/counts alone. |
| Schema lifecycle | **Conceptually adequate, byte-inexact** | Bind canonical commitment/status records and a sealed chronology chain. |
| J connectedness | **Passes D0 science; certificate ambiguous** | Define the exact old-transform state-flow cut and separate it from the source bridge. |
| P four-way posterior | **Fatal to P interpretation as written** | Define an explicit uniform atoms-only completion ablation or compute the actual-prior posterior. |
| First-accept Bayes conditioning | **Exact-spec failure** | Bind the proposal decoder and ordered global selection recurrence; marginalize all hidden selectors. |
| Supplied affine grammar | **Acceptable D0 limitation** | Rename the construct grammar-conditioned; forbid learned-discovery/compression credit. |
| Action realism | **Acceptable only at D0** | Preserve the CPU-only claim boundary; reassess the stream before model work. |
| Stateful causal interpretation | **Adequate for J/P CPU geometry, not a developmental world** | Keep connected state-flow certificates and forbid broader language. |
| Source schedule leakage | **Not certified** | Fix enumerable RNG/handles, exact proposal conditioning, and full source projections; rerun every probe. |
| Target cardinalities | **Internally inconsistent** | Resolve K0 R and pair-common proposal counts; include rejected-candidate work. |
| Exact planner feasibility | **Underspecified** | Search an exact state quotient, not all histories; prove preservation. |
| Two-hour CPU budget | **Valid ceiling, unsupported feasibility assertion** | Add factorized bounds and DEV measurements; fail closed without weakening the science. |

## 5. What should not be changed

The repair should not broaden D0. In particular, do not add X, a model,
tokenizer-native cuts, THINK/DREAM prompts, learned writer tests, LoRA,
providers, GPUs, external actions, three-pack confirmation, on-policy
collection, or publication claims. Do not relax `.35` leakage ceilings,
per-target oracle success, J/P necessity, failure-as-zero, no replacement, or
run/skip isolation to rescue feasibility. Do not let an implementation choose
the missing scientific bytes and call the choice a non-material bug fix.

The smallest next artifact is a repaired, newly hash-bound D0 design candidate
disposing every item above. Under `AGENTS.md`, that material benchmark change
then needs fresh-context interpretations, adversarial cross-critique,
adjudicated consensus, and explicit human ratification of exact bytes and
scope before implementation.

## 6. Governing-source alignment

- `AGENTS.md`: material benchmark, visibility, test, and claim changes require
  the durable deliberation path and exact human ratification; consensus cannot
  authorize implementation.
- RML v1 consensus: asks for one exact CPU-only D0, exact connected J and
  prospective P, accepted-item Bayes, complete twin collision, finite resource
  ceilings, and an acyclic disposable evaluation branch; its current human
  decision is pending and implementation is forbidden.
- `rml_pilot_v1.md`: requires a stateful action/outcome life, connected J,
  pretarget P, generator-aware leakage controls, and strong claim narrowing.
- Rendered candidates A/B: distinguish common-deck representation/use from the
  on-policy flywheel and require complete selection-conditioned leakage,
  non-isomorphic later packs, and honest graph/program baselines.
- Notes 42--48: distinguish action success from constructive attribution,
  require chronological support and exact no-life Bayes controls, treat fixed
  decks and small mapping tables as component microscopes, and reserve
  developmental/compression/flywheel language for later evidence.

