# PCFL core plus lineage guard: fresh cross-critique v1

Date: 2026-09-10

Status: **source-only adversarial implementation review**. This note supplies
no ratification or authority and changes no architecture, protocol, benchmark,
control, endpoint, child, lineage, model, adapter, resource plan, claim, or
release state. It authorizes no implementation, root/data generation,
model/provider call, training, LoRA/GPU work, evaluation, promotion, or claim.

## Sources read

- `AGENTS.md`, SHA-256
  `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e`.
- `research_loop/advisory/20260910_clean_child_lineage_guard_v2_repaired_boundary.md`,
  SHA-256
  `04ededbd52c70436b7e507a383b1fd049e3790fdf5067af2fefce193a046a7ad`.
- `research_loop/advisory/20260910_pcfl_smallest_exact_executable_core_fresh_interpretation_v1.md`,
  SHA-256
  `c8f3c78439ed124e1866500f21c388b5322417dc17cd2f9ef73c965f39501414`.

## Verdict

**REVISE the combined implementation surface.** The two proposals have a good
security/semantics seam, but joining their complete surfaces now would build a
general lineage security platform, remote broker, blinded final service,
transactional trainer, M, L, and C before proving that one PCFL root is
well-defined or text-solvable.

The minimum first deliverable is only a `TEST_ONLY/DEV_NONCLAIM` PCFL semantic
kernel and root-level M text reducer. It creates no accepted child state and
claims no clean lineage. The lineage authority remains a separate dependency
contract and is implemented only when a state-affecting E0/M/L operation needs
claim-bearing ancestry. L, C, remote calls, parenting, and sealed final are
extensions, not members of the semantic kernel.

This staged boundary is safer than a partially implemented “clean” platform:
the first executable refuses science identities, and later claim-bearing work
cannot mistake hashes or directory discipline for the v2 guard's enforced
authority boundary.

## 1. Exact disposals from the first implementation

### Remove from the PCFL semantic kernel

1. Replace generic `reduce(ExperimentSpec, ...)` with an explicit
   `reduce_m_root(...)`. Generic reduction invites M/L/C unit mixing.
2. Remove `OpportunityTape`, L cut/slope logic, `ACTIVE_TEXT_FIXED`, and paired
   lineage execution. They belong to a later `pcfl_l` package.
3. Remove C `Representation`, codecs, byte accounting, and load reducers. They
   belong to a later `pcfl_c` package consuming the canonical event/link API.
4. Remove `TEXT|LORA` as a core storage abstraction. The core emits canonical
   semantic rows and explicit text. Adapter construction/mounting belongs to
   an E0-approved transport runner.
5. Remove PCFL-owned ancestry, signatures, CAS, promotion, OS confinement,
   broker, and release logic. Retain only an opaque `authority_context_id` in
   receipts and a narrow authority-client interface for later runners.
6. Do not implement a second canonical authority envelope. Semantic objects
   may have deterministic test bytes, but claim-bearing record identity must
   use the lineage authority's single canonical encoder and signature.
7. Remove `NO_SEMANTIC`, optimizer accounting, remote-session freshness,
   final-release status, and parenting fields from the first M kernel. They do
   not test PCFL semantics.

### Defer from lineage guard v2

For the first CPU/text milestone, do not implement:

- the four-regime classroom/exam/gym/final policy matrix;
- the optional developmental-exam declassifier;
- remote parent/author broker and provider-session claims;
- sealed-final scheduler, encrypted result store, release principal, blinded
  operations principal, constant-shape telemetry, or partition consumption;
- parent notebook/playbook state, classroom reducers, tokenizer-bound trainer
  masks, adapter/optimizer promotion, and CompilerGym method-development flow;
- a repository-wide entry-point conversion.

The first artifact is ineligible `DEV_NONCLAIM`, so it has no accepted-state
write to secure. These items are deferred, not declared unnecessary for later
claims.

When claim-bearing personal writes begin, implement only the v2 subset actually
needed: experiment manifest; content-addressed blob store; immutable state
events; single serialized pointer promotion; one-use local `NETWORK_NONE`
grant; maximal readable-set dependency; confined launcher with immutable input
bundle and one scratch root; signed launcher receipt; and atomic child/corpus/
writer promotion. Add broker machinery only if a remote service is used. Add
sealed-final machinery only after a final plan and separate administrative
domain exist. Keep the exam declassifier at `DENY_ALL` unless separately
ratified.

## 2. Security seam still wrong in the combined design

The PCFL API passes `SealedRoot` into `advance`, while the lineage guard treats
every grant-readable blob as an output dependency. A model worker must never be
granted the sealed root, generator seed/configuration, certificate oracle, or
private receipt. If it is, finite-reader correctness is irrelevant: the bytes
are readable outside the prompt.

The minimum process split is:

```text
trusted environment worker: SealedRoot + Command -> PublicEvent + private receipt
untrusted actor worker:      FiniteView -> Command
trusted carrier/reducer:     admitted PublicEvent IDs -> rows/root vector
```

The actor grant contains only the exact finite-view blob, command schema, model
identity, and declared runtime. The environment worker has no model or clean-
state write capability. Private receipts go directly to the reducer/authority,
never through actor scratch. This split must be visible in APIs and tests, not
implemented as conventions inside one process.

The v2 maximal-readable-set rule and PCFL visibility law then reinforce each
other: the grant proves which bytes could be read; `visible_view` proves those
bytes contain only phase-admissible public semantics.

## 3. Blocking PCFL semantic choices

The prior PCFL specification is exact about types but not yet exact about the
world. The following choices must remain required, unset configuration fields;
implementing around them would silently define the benchmark.

### A. Relation algebra and grounding

`Link` is called a typed relation, but relation types, direction, composition,
path validity, state equality, and goal-answer semantics are unset. More
importantly, it is unclear who creates old authentic links. If an oracle
compiler inserts ground-truth links, M tests reading provided annotations, not
the child connecting experience. If the child authors links, admissibility,
normalization, error handling, and evidence grounding must be specified.

Minimum required choice: exact finite relation algebra plus one declared link
producer. The producer may use only admitted public events. Oracle truth may
score a link but cannot author the acting carrier without narrowing the claim.

### B. Broken goal-probe join

The phase graph forks isolated goal A/B probes and then points toward
`MISSING_DECLARE` without a defined join. If nothing returns, the acquisition
child cannot use its traversals to identify the gap; if whole branches return,
goal order and probe outcomes can teach the later branch.

Minimum required choice: add `GOALS_COMPLETE` and bind exactly what returns.
A defensible minimum is both probes forked from one checkpoint, then a fixed or
randomized prebound join containing only their public goals, child-authored
actions/declarations, and public outcomes—never oracle correctness, certified
paths, scores, or critiques. Whether this joined experience is part of the
claimed relay is material and must be ratified.

### C. Path versus guessed answer

A correct terminal answer does not prove traversal. Bind whether success
requires the exact legal action/path trace, a member of a complete registered
path equivalence class, and the correct terminal answer. Score path validity,
answer validity, and shortcut/guess separately; do not let one compensate.

### D. Lexical and generator shortcuts

Graph certificates do not stop a pretrained model exploiting names, ordering,
answer frequencies, action position, path length, or template regularities.
The generator needs opaque symbol permutations, balanced role/action/answer
marginals, randomized presentation order, equalized action costs, and
counterfactual twin tests. Root/seed/template identifiers must remain outside
the actor grant. The exact balance law and whether templates are disjoint
across DEV/confirmation are unset.

### E. Uncertainty and experiment selection

`UNCERTAINTY_SHAM` lacks a canonical public object. Bind the authentic cue,
truthful sham, candidate-action set, action costs, public outcome alphabet,
separating equivalence class, and information-gain score. Otherwise a special
word, unique action arity, deterministic reward, or cheaper action can reveal
the “experiment” without experiential uncertainty. Score chosen action and
realized information separately.

### F. Carrier matching and atomic retention

“Matched exposure” is not executable until the unit is chosen: public events,
rows, UTF-8 bytes, tokenizer tokens, examples, optimizer steps, generated
tokens, or some registered vector. Padding may itself reveal arm identity.
Bind one nonsemantic padding construction and require its sham effect to be
null within a margin. For LoRA, atoms and links need matched training examples,
masks, steps, seeds, and nonsemantic load, while atomic-retention probes verify
that linked benefit is not paid for by lost facts.

### G. Reset and write semantics

Bind exactly which model state, adapter, retrieval index, text memory, context,
RNG, tool cache, and controller state survive `OLD_CHECKPOINT`, probe clones,
SLEEP, and `DELAYED_RESET`. Bind whether `NO_WRITE` still performs matched
optimizer/compute work. `SHAM_WRITE` is not needed for the first text-solvability
gate, but it is required before claiming grounded content rather than a write
ritual. Adapter-off, wrong-root, binding-swap, and no-write are transport-runner
controls, not CPU-kernel branches.

### H. Failure and arm semantics

Bind timeout, invalid command, refusal, malformed answer, unavailable action,
writer rejection, and missing artifact values at the root level. Conditional
controls can short-circuit one preregistered product endpoint, but selected
positive roots cannot estimate unconditional component effects.

## 4. L and C confounds to resolve before their packages exist

### L: same outcomes versus adaptive action

F and B cannot generally choose different actions yet receive the same public
outcomes without counterfactual replay. Yoking one arm to the other changes the
estimand; replaying a fixed action tape removes experience-directed choice;
allowing separate trajectories confounds memory system with acquired evidence.

Minimum resolution: separate the cumulative **exogenous learning stream** from
adaptive evaluation probes. Both arms ingest byte-identical public experience
at every cut; probes measure decisions but do not alter either future stream.
If endogenous acquisition is part of L, it needs a separate estimand and
trajectory policy. Also bind whether resource matching means opportunities and
generated tokens only or includes retrieval, inference, and optimizer work;
equal compute must not be implied when F trains and B does not.

### C: free generator and mixed distortions

A deterministic PCFL seed or generator can be a tiny implicit codebook. Neither
may be available to a decoder unless its bytes and algorithm are charged.
Expanded, normalized, and schema-residual encodings must decode to the same
canonical **public** semantic ledger, not the oracle root.

Keep two endpoints separate:

1. codec distortion/bytes after lossless decode to a common reader; and
2. direct-interface model utility of each live representation.

Otherwise model familiarity with one text format is mislabeled compression.
Decoder false relations and model-produced false memories are also separate
rates. Bind standalone and amortized schema/decoder accounting explicitly.

## 5. Controls: retain, defer, dispose

| Disposition | Objects |
|---|---|
| Keep in first M semantic/text surface | atoms, authentic links, truthful null, derangement, atomic-retention probes, two goals, bridge cut, twin/redirection, authentic/sham uncertainty, dispatch-level `REACHOUT_OFF`, old/new availability cells, explicit-text ceiling |
| Defer to E0/LoRA transport | native response-only training, cumulative rebuild/transaction, `NO_WRITE` compute match, `SHAM_WRITE`, adapter off, wrong root, new-binding swap, writer rejection, raw-base/previous-child safety |
| Defer to L | opportunity tape, paired lineages, certified `ACTIVE_TEXT_FIXED`, slopes/plateau/retention/terminal reducer |
| Defer to C | three codecs, loads, round-trip/false-memory/utility, complete byte/work accounting |
| Dispose from minimum unless a later named claim restores it | generic `NO_SEMANTIC` omnibus, generic reducer framework, global cleanliness lattice, optional exam declassifier, remote broker on a local-only plan, CompilerGym-specific regimes in PCFL code |

The first text gate may emulate written/not-written semantic-row visibility;
it must not call that E0, SLEEP efficacy, or weight transport.

## 6. Minimum implementable boundary

After exact ratification, the first package should contain only:

```text
schema:       State, Action, PublicEvent, Atom, Link, Goal, TransitionRow
generator:    deterministic root construction + certificate/shortcut oracle
environment:  trusted reset/step with opaque public aliases
phase:        M transition table including GOALS_COMPLETE
reader:       phase allow-list and hidden-byte noninterference surface
carrier:      explicit atoms/linked/null/deranged text from public evidence
intervention: bridge/twin/sham/reachout/old/new pure transformations
m_reducer:    one root-level noncompensatory vector
tests:        canonicality, topology, visibility, phase, controls, nesting/replay
```

It explicitly excludes L, C, LoRA, training, child promotion, parent state,
remote calls, CompilerGym, final partitions, and release. Its manifest says
`DEV_NONCLAIM`; its receipts cannot be promoted or cited as science evidence.
It uses no model in the CPU gate.

The exact acceptance boundary is:

1. all semantic blockers A--H are ratified, with no code defaults;
2. exhaustive finite-template and adversarial tests pass with zero systematic
   counterexample;
3. the actor API has no type/path/handle capable of resolving `SealedRoot` or
   private receipts;
4. every control changes only its declared public semantic target;
5. `reduce_m_root` accepts root receipts only and cannot count probes/calls;
6. no output is eligible accepted child state or confirmation evidence.

Only then add a thin no-claim text runner. If text M fails, stop. If it passes,
E0 and the minimal local lineage-authority subset may be independently
ratified and implemented for bounded LoRA transport. L and C start only after
their confounds above and exact reducers are separately bound. Sealed final is
last, after a frozen claim and a real separate administrative/release domain.

## Claim boundary

The minimum package can claim only deterministic benchmark software behavior.
A no-claim text DEV can show engineering solvability and estimate root-level
cost/variance. Neither establishes clean ancestry, connected personal weights,
grounded SLEEP, lifetime improvement, active-text plateau, compression,
parenting, or confirmation. The lineage v2 security claim begins only when its
actual authority/principal/launcher boundary is implemented and tested; hashes
or a `DEV_NONCLAIM` manifest are not a weaker version of that claim.

## Bottom line

Do not build the paper platform to discover the world semantics. First bind and
implement one sealed PCFL world, one coherent A/B-probe join, one finite reader,
the indispensable text controls, and one root reducer. Keep lineage security as
a hard later interface, not duplicated benchmark code. This is the minimum
surface that can falsify PCFL cheaply while preserving a clean route to E0/M,
then L/C, then sealed confirmation.
