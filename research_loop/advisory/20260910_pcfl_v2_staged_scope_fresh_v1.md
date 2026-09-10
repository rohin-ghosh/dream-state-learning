# PCFL v2 staged scope: preserve the full organism, ratify only the CPU contract kernel

Date: 2026-09-10

Status: **fresh architecture interpretation and ratification candidate only**.
This file is not a human ratification. It authorizes no implementation,
benchmark or root generation, model or tokenizer call, adapter/checkpoint or
writer work, GPU use, parenting, evaluation, scientific execution, claim, or
release. Under `AGENTS.md`, a human must ratify the exact hash-bound successor
and its exact requested scope before any affected bytes are edited.

## Plain-language explanation

Keep the whole Dream--LoRA--Think research question. Build only its empty
airlock first.

The airlock can prove that records have one canonical byte representation,
that private fields do not cross a declared role boundary, that illegal state
transitions cannot mutate state, that evidence ancestry is not inflated by
copies, and that one environment root is counted once. It contains no child,
no world, no learned link, no text-memory result, no LoRA, and no experiment.

Later, separately approved packages put scientific content through that
airlock: first an exact PCFL mechanism world and text ceiling, then a safe
native writer, then LoRA transport, lifetime learning, semantic coding,
parenting, an actual on-policy flywheel, and sealed confirmation. A later
failure removes the corresponding claim; it does not retroactively make the
airlock a learning result.

In one sentence: **ratify the socket now, not any device plugged into it.**

## Fresh ruling

The v1 consensus is right that the combined v1 artifact is not exact enough
to implement as one claim-bearing system. It is too broad, however, to treat
every unset scientific estimand as a blocker to a smaller, permanently
non-claim-bearing contract substrate.

The repaired architecture should therefore do both of the following:

1. retain, without narrowing, the full Dream--LoRA--Think ambition; and
2. allow only **K0**, a standard-library, CPU-only, `TEST_ONLY` contract
   kernel, to enter an implementation proposal now.

K0 is not the v1 “explicit-text M reducer” Stage 0. It is smaller. It has no
PCFL relation algebra, root generator, actor, reader, carrier content,
scientific M reducer, clean child, lineage source, writer, or learned state.
Those are plug-in packages whose exact scientific meaning must be ratified
later. K0 merely refuses to run a package whose meaning is missing.

This separation disposes of the false choice in `D-EXACT-CONTRACT`: the full
combined system remains blocked, while a strictly content-free enforcement
substrate can be exact and implementable without choosing scientific answers
by code default.

## The retained scientific thesis

No ambition is discarded by this staging. The target remains one clean,
parent-deleted organism in which:

- THINK recurrently retrieves, composes, plans, acts, observes, and revises;
- DREAM manages finite context and proposes target-independent local
  connections from the child's eligible public experience;
- later independent public evidence, not synthetic restatement, determines
  whether proposals become supported;
- SLEEP validates and compiles supported action--outcome continuations;
- a transactional cumulative life-local LoRA transports, but does not invent,
  those semantics;
- the resulting personal knowledge can be connected, traversed under changed
  goals, expanded by informative action, retained, and used across time;
- separately raised lineages can test whether improvement continues beyond a
  certified evolving textual-memory comparator's prospective local plateau;
- a separate on-policy assay can test the stronger feedback loop in which
  memory changes evidence acquisition, consolidation, and later action; and
- a separate C assay can test semantic rate--distortion without calling LoRA
  physical compression below a measured complete-byte crossover.

Parenting also remains a distinct clean factorial asking whether target-blind
development changes later write-enabled learning, not merely entry skill.
None of these claims may borrow passage, units, thresholds, or failures from
another package.

## Staged package graph

```text
K0 CPU contract kernel (only scope proposed for approval now)
 |
 +--> G clean-source / disposable-descendant authority package
 |
 +--> M-SPEC exact PCFL mechanism instrument (CPU semantics)
          |
          +--> M-TEXT explicit-text engineering ceiling
          |
          +--> C semantic-code rate--distortion package

G + exact E0 writer package -------------------------+
M-TEXT passage --------------------------------------+--> M-LORA transport
                                                      |
G + E0 + ACTIVE_TEXT_FIXED certificate --------------+--> L exogenous lifetime
                                                      |
G + E0 + parenting design ----------------------------+--> P parenting factorial
                                                      |
G + E0 + M prerequisites + online design -------------+--> O on-policy flywheel

Each claim-bearing DEV package --> its own Q confirmation package
```

Arrows are prerequisites, not authorizations. Passage at one node never
launches or ratifies a successor. `M-SPEC` may reuse K0 contracts; it may not
turn K0 conformance fixtures into benchmark roots. `C`, `L`, `P`, and `O`
retain their own independent units and reducers.

## K0: the only presently approvable implementation scope

### K0 purpose and mode

K0 is a deterministic contract library plus conformance tests. Every K0
artifact has all three permanent properties:

```text
mode = TEST_ONLY
claim_eligible = false
source_eligible = false
promotion_eligible = false
```

These values are not configuration switches. K0 exposes no path that changes
them. Any artifact lacking all three exact values is rejected. K0 output may
not become a clean source, benchmark root, corpus row, writer input,
development-selection signal, threshold-selection signal, or confirmation
input.

K0 is CPU-only and local. Its implementation proposal may use the language
standard library and the repository's existing unit-test runner only. It may
not add or install a dependency; open a network connection; import a model,
tokenizer, trainer, adapter, provider, benchmark generator, or experiment
runner; enumerate existing checkpoints or lineage directories; or invoke a
subprocess that does any of those things.

### K0 canonical byte contract

K0 must bind this wire contract before its implementation bytes are approved:

- documents are JSON objects encoded as UTF-8 without BOM or trailing bytes;
- object keys are unique ASCII `lower_snake_case` strings;
- all string values must already be Unicode NFC; non-NFC input rejects rather
  than being silently rewritten;
- numbers are signed 64-bit integers only; floats, NaN, infinity, duplicate
  keys, and implementation-specific numeric coercions reject;
- arrays are ordered and object members are serialized by RFC 8785/JCS;
- the canonical byte string has no terminal newline;
- unknown and missing fields both reject; no field has a runtime default;
- a content identity is
  `SHA256("pcfl-v2\0" || object_kind || "\0" || canonical_bytes)`; and
- the implementation proposal must include golden input, canonical-byte,
  content-ID, and rejection vectors. Prose examples are not substitutes.

Model-visible text is outside K0. A later package must separately bind its
prompt, chat template, tokenizer, rendering, parsing, normalization, and
fully rendered golden bytes.

### K0 closed envelope and errors

Every accepted object has exactly these envelope fields:

```text
schema_version   = "pcfl.v2.k0/1"
mode             = "TEST_ONLY"
claim_eligible   = false
source_eligible  = false
promotion_eligible = false
package_id       = nonempty ASCII identifier
package_sha256   = 64 lowercase hexadecimal characters
object_kind      = one registered K0 kind
body             = closed object for that kind
```

The initial K0 kinds are exactly `contract_package`, `phase_spec`,
`projection_spec`, `public_state`, `private_state`, `public_event`,
`provenance_node`, `registered_root_set`, and `terminal_receipt`. Adding a
kind is a material change.

K0 failure is typed and fail-closed. Its error vocabulary is exactly
`E_SCHEMA`, `E_NONCANONICAL`, `E_HASH`, `E_UNBOUND`, `E_ROLE`, `E_PHASE`,
`E_DAG`, `E_RECEIPT`, `E_UNIT`, and `E_MODE`. An error returns no partially
accepted object and never advances a state hash. Later scientific packages
may add package-local outcome values, but may not reinterpret a K0 contract
error as a scientific score.

### K0 fail-closed package loading

A `contract_package` is a manifest of content identities. It must bind the
exact `phase_spec`, `projection_spec`, object schemas, registered root set,
and receipt schema needed by the requested operation. A missing identity,
unknown identity, hash mismatch, unregistered kind, or unresolved reference
returns `E_UNBOUND`. K0 has no “development,” “latest,” discovery, directory
scan, fallback, or permissive mode.

K0 validates only identities and contract closure. It does not assert that a
later relation algebra, statistic, source, model, or scientific interpretation
is correct.

### K0 phase primitive

The phase engine is a pure function over a hash-bound `phase_spec`, current
public/private state identities, and one typed command. The specification
contains the finite phase IDs, legal command/event triples, initial phase,
terminal phases, and permitted projection-spec identity at each boundary.

For a legal transition, the engine returns a new state object and ordered
public-event identities. For an illegal, missing, repeated, or out-of-order
transition, it returns `E_PHASE` and the before-state identity unchanged. No
wall clock, filename, environment variable, RNG, hidden retry counter, or
prior invocation may affect this result.

K0 deliberately binds no PCFL phase table. Its conformance suite uses one
small hand-authored automaton with semantically empty labels. The exact M
phase table, A/B chronology, reset persistence, GOALS_COMPLETE payload,
timeouts, retries, and failure effects belong to `M-SPEC`.

### K0 role projection primitive

`public_state` and `private_state` are different closed kinds. A
`projection_spec` lists, for one `(role_id, phase_id)`, the exact allowed leaf
paths from public state. Projection is literal copying only. Computed fields,
wildcards, implicit parent inclusion, private-state paths, filenames,
environment data, exceptions, and process metadata are forbidden. A missing
role/phase rule returns `E_ROLE`.

The returned view includes the projection-spec identity and only the listed
public leaves. Changes to private state or to unlisted public leaves must
leave its canonical bytes identical. Direct private-object access through a
projection API must fail. This is a contract property, not yet an OS/process
isolation claim.

A later `M-SPEC` must bind the actual actor, controller, compiler, reader, and
reducer projections. A later `G` package must enforce maximal readable sets,
process/session/cache/RNG/network boundaries, and no-return capabilities.

### K0 provenance-DAG primitive

A `provenance_node` binds its own content identity, a monotone integer
sequence, ordered parent identities, sorted unique evidence-root identities,
one of `observed`, `proposed`, `supported`, `synthetic`, `revoked`, and an
optional superseded-node identity. Validation has the following fixed
structural rules:

- all parents must exist at a lower sequence number;
- true directed cycles reject;
- shared-ancestor diamonds are legal;
- an alias must resolve to one existing content identity before traversal;
- evidence roots are set-valued, so duplicate citations cannot add support;
- a synthetic node inherits the union of ancestor evidence roots and adds no
  new evidence root;
- a revision creates a new node and preserves the superseded node; and
- revocation remains visible and cannot be removed by a synthetic view.

K0 does not decide which public event grounds a semantic relation, how many
independent roots support it, or whether DREAM authored it. Those claim-level
rules belong to `M-SPEC` and `M-TEXT`.

### K0 structural root closure

A `registered_root_set` is an ordered, hash-bound list of unique opaque root
IDs. A `terminal_receipt` binds one registered root ID, its package identity,
ordered event identities, terminal status, and its referenced provenance-node
identities. Structural reduction accepts exactly one closed receipt per
registered root. Duplicate, foreign, missing, nested-as-new-unit, or
nonterminal receipts return `E_RECEIPT` or `E_UNIT`.

K0 may report receipt closure and the registered root count. It does not
define M endpoints, substitute failure scores, estimate effects, compute
uncertainty, or emit PASS/FAIL for a scientific claim. Goals, probes, paths,
calls, branches, checkpoints, loads, and rows cannot become roots merely by
appearing in a receipt.

### K0 conformance suite

Only hand-authored, semantically empty, in-repository constants are permitted
as K0 fixtures. They are not generated roots or benchmark data. The required
K0 tests are:

| ID | exact property |
|---|---|
| `K0-01-CANON` | Golden canonical bytes and domain-separated identities are stable; BOM, non-NFC, float, duplicate-key, unknown-field, missing-field, and hash-mismatch inputs reject. |
| `K0-02-CLOSURE` | Every referenced contract identity exists and hashes; unset, cyclic, foreign, or fallback resolution rejects. |
| `K0-03-PHASE` | Exhaustive transitions of the conformance automaton replay identically; every illegal history preserves the before-state identity. |
| `K0-04-PROJECTION` | For every fixture role/phase, private and unlisted-public perturbations leave returned bytes identical; listed-public perturbations change only the listed field; private access fails. |
| `K0-05-BRANCH` | A fixture branch join releases exactly the projection's allowlisted leaves; sibling workspace, order, scores, failure metadata, and private state are absent. This proves the projection mechanism, not the future M join choice. |
| `K0-06-DAG` | Legal diamonds pass; aliases collapse; duplicate roots add no support; true cycles, future-parent chronology, and descendant-as-ancestor citations reject; synthetic/revision/revocation rules hold. |
| `K0-07-UNITS` | Exactly one terminal receipt per registered root closes; missing, duplicate, foreign, reordered-as-distinct, and nested pseudo-units reject. |
| `K0-08-QUARANTINE` | Every output retains the three false eligibility flags; any attempt to flip, omit, or reinterpret them returns `E_MODE`. No scientific or source sink accepts a K0 fixture. |

K0 is incomplete if any test is absent or if a test depends on randomness,
network access, a model, generated benchmark content, an existing lineage, or
a scientific threshold.

### What K0 passage permits one to say

Only this is permitted:

> The K0 library deterministically enforces its versioned canonical-byte,
> package-closure, pure-transition, literal-projection, structural-provenance,
> root-receipt, and TEST_ONLY quarantine contracts on its hand-authored
> conformance fixtures.

K0 passage does not satisfy S0 in the paper audit and does not establish a
PCFL benchmark, paired-world identifiability, grounded experience, THINK,
DREAM, SLEEP, a clean lineage, writer safety, text solvability, LoRA
transport, connection, traversal, expansion, accumulation, lifetime
improvement, parenting, compression, an on-policy flywheel, or confirmation.

## Later packages and their exact ratification burden

### G — clean-source and disposable-descendant authority

Before any claim-bearing model, writer, parenting, `M`, `L`, `C`, `O`, or
confirmation execution, G must bind exact `CleanSourceReceipt` and
`ExperimentPlan` schemas; the admitted source and quarantine denials; role
maximal-readable sets; OS/VM, mount, process, file-descriptor, network,
session, provider, cache, RNG, log, timing, administrator, and human trust
boundaries; root-local store ownership; no upstream promotion capability; and
the complete no-return and partial-result release policy.

G must state residual trust rather than claiming metaphysical isolation.
Known CompilerGym and unknown-provenance artifacts remain ineligible wherever
the existing quarantine applies.

### M-SPEC and M-TEXT — exact mechanism instrument before LoRA

`M-SPEC` is a separate material proposal. It must bind the finite relation
algebra, public world law, deterministic root/twin generator, opaque-symbol
and marginal balance law, public event semantics, legal path-equivalence
classes, A/B phase table, exact GOALS_COMPLETE projection, repeat/retry/reset
state, public-evidence grounding, target-independent DREAM proposal rule,
support chronology, carrier renderer, atoms/authentic/null/deranged exposure
matching, bridge/twin/redirection/cut/sham controls, uncertainty object and
separating-action instrument, old/new cuts, endpoint vector, structural and
scientific reducers, failure values, and all `PCFL-CPU-01` through the missing
`PCFL-CPU-12` obligations.

The retained ambition selects the stronger DREAM-authorship branch: authentic
links must originate as target-independent child/DREAM proposals and receive
later independent public support; deterministic SLEEP may validate and render
them but may not invent their semantics. A supplied-link variant may exist as
a diagnostic, but cannot replace this gate or inherit its claim language.

`M-TEXT` then binds exact model-facing bytes, one fixed child, finite reader,
recurrence-disabled and honest no-memory/raw-context/RAG/graph/organized-
memory bypass baselines, noncompensatory recall/transfer/composition/planning/
action/revision/information/retention endpoints, resource factors, DEV root
universe, and negative-result dispositions. It is an engineering ceiling and
claim prerequisite, not a LoRA result.

### E0 — native writer truth and safety

E0 remains independent and noncompensatory. Its later hash-bound package must
specify the exact source child, native prompt/response rows, response-only
mask, cumulative rebuild rule, adapter and corpus transaction, previous-child
and raw-base comparisons, wrong-life/binding and adapter-off panels,
absorption/free extraction/forced-proposal/action-interface endpoints,
retention, imprecision/harm, rollback, failure values, margins, units,
uncertainty, and independent review receipt.

Neither K0 nor M-TEXT can substitute for E0. A contradicted legacy writer
cannot be grandfathered into passage.

### M-LORA — same-semantics grounded transport

M-LORA may be proposed only after passing, separately ratified M-TEXT and E0
evidence and an applicable G boundary. It must use the same admitted semantic
rows and bind adapter-off, wrong-root/life, binding swap, no-write/sham-write,
read-mask, unaided-LoRA-read, common-reader, recurrence, capacity, and work
factors. It may support bounded root-specific semantic transport only.

Same semantics is not fixed bytes or fixed computation. Any fixed-budget
efficiency claim requires a separate charged budget sweep. LoRA is not a
literal graph and does not receive discovery credit.

### P — target-blind parenting factorial

P binds independently raised `P0`, `P1`, `U0`, and `U1` lineages, identical
certified active text and opportunity streams, parent deletion, entry score,
the entry-adjusted parenting-by-write interaction, later acquisition,
retention/transfer, harm, resource envelopes, practical margins, and no
descendant-to-parent return. A parenting main effect at entry is installed
competence, not learning-to-learn.

### L — exogenous increasing-lifetime use

L binds the exact certified `ACTIVE_TEXT_FIXED` implementation, independent
paired lineages, byte-identical exogenous opportunity tapes, isolated F/B
journals, update opportunities, resource envelopes, cuts, prospective
baseline plateau equivalence, positive learner late slope, positive paired
slope advantage, retention floor, terminal practical margin, lineage count,
covariance/uncertainty, multiplicity, failure/missingness, and stopping.

L descendants are upstream-terminal, not locally stateless: registered local
state may persist across that descendant's cuts. Because later opportunities
are exogenous, L supports a longitudinal-use estimand, not the on-policy
flywheel.

### C — semantic-code rate--distortion

C binds C-disjoint roots and loads; the expanded, normalized-connected, and
schema-residual codecs; deterministic denotation; standalone and amortized
schema/decoder/index/prompt costs; generator denial or complete charging;
complete live bytes and work; fidelity, decoder-created false relations,
model false memories, and common-reader utility as separate endpoints; and
root-level uncertainty.

Absent a complete charged physical crossover, C may claim only text-interface
semantic-code rate--distortion. It cannot rescue E0, M, P, L, or O.

### O — the retained on-policy action--experience flywheel

O is required precisely because bounded M plus exogenous L cannot establish
the full adaptive loop. It must bind a life in which current memory changes a
registered action choice, that action changes acquired public evidence,
grounded DREAM/SLEEP consolidation changes later memory, and the later memory
improves a subsequent action. It requires action-policy, acquisition,
no-update, sham-update, counterfactual opportunity, retention, harm, resource,
and repeated-cycle controls, with independent lineages for population
language.

O is retained as a first-class objective, not silently inferred and not
authorized now.

### Q — DEV and confirmation control

Each claim-bearing package gets its own Q package before confirmation. Q must
bind the complete unit universe and order, DEV/reserve/confirmation identities,
result mask, release principal and point, exclusions, retries, failures,
stopping, estimator, margins, uncertainty, multiplicity, missingness,
mandatory negative reporting, claim withdrawal, and allowed post-result
decision DAG. Runtime, output size, missing files, logs, scheduling, and
partial receipts count as results for this purpose.

Confirmation cannot modify the source, parent, mechanism, writer, benchmark,
baseline, root/lineage set, thresholds, or analysis. Strict human blinding
may be claimed only when a separate administrative principal enforces it.

## Which v1 concerns block K0 and which gate later claims

“Later” does not mean optional. It means the concern blocks the named later
package rather than a content-free K0 implementation.

| v1 concern | K0 disposition | binding stage |
|---|---|---|
| `CRIT-PCFL-001` exact contract | **Blocks K0 only for K0's own bytes and scope.** It does not require premature choices for M/E0/L/C/O. | K0 now; every later package again locally |
| `002` paired-prefix indistinguishability | No paired scientific world exists in K0. K0 tests generic projection noninterference only. | M-SPEC before roots/model use |
| `003` query/agenda laundering | No query, agenda, reader, carrier author, or actor exists in K0. | M-SPEC/M-TEXT before model use |
| `004` GOALS_COMPLETE leakage | K0 must prove only that a declared projection is literal and closed. The actual join bytes remain unset by design. | M-SPEC before benchmark roots |
| `005` repeat/retry state | K0 transition state may have no hidden mutable fields; scientific repeat fingerprints, counts, reset reasons, and failure effects are later. | split: K0 purity now; M-SPEC exact fields later |
| `006` canonical/model bytes | **K0 canonical envelope and golden vectors block K0.** Prompts, chat templates, tokenizer and parser bytes do not. | split: K0 now; each model package later |
| `007` DREAM/link authorship | No semantic link exists in K0. Full ambition retains target-independent child/DREAM authorship. | M-SPEC/M-TEXT claim gate |
| `008` provenance DAG | **The content-neutral DAG structural primitive and adversarial fixtures block K0.** Semantic grounding and independent support do not. | split: K0 structure now; M later |
| `009` constructive path credit | K0 validates no behavior or answer. | M-TEXT and M-LORA claim gate |
| `010` recurrence and bypass baselines | No thinker runs in K0. | M-TEXT/M-LORA claim gate |
| `011` noncompensatory M endpoints | K0 emits no scientific endpoint. | M-TEXT/M-LORA claim gate |
| `012` uncertainty instrument | No action or uncertainty object exists in K0. | M-SPEC before scientific roots |
| `013` resource-factor equivalence | K0 makes no carrier comparison. | M-TEXT, M-LORA, L, C, O |
| `014` on-policy flywheel | Preserved as O rather than inferred from M+L. | O claim gate |
| `015` missing L end-to-end test | Irrelevant to K0; remains a hard stop for CLM-L. | L claim gate |
| `016` statistical contract | K0 has deterministic conformance, not an estimator. | each claim package and Q before execution |
| `017` partial-result feedback | K0 produces permanently non-scientific fixtures only. | G/Q before claim-bearing execution |
| `018` OS/provider authority | K0 projection is not an isolation claim and touches no protected source. | G before claim-bearing execution |
| `019` journal/CAS protocol | K0 has no writer or mutable scientific journal. | E0/M-LORA/L/O as applicable |
| `020` exact E0 binding | Cannot block a writer-free K0; remains noncompensatory. | E0 before LoRA/P/L/O dependence |
| `021` C accounting | No codec exists in K0. | C claim gate |
| `022` accumulation and scale | K0 makes no developmental claim. | M accumulation, L, and O packages |
| `023` negative dispositions | **K0 must bind the single consequence “no scientific claim regardless of outcome.”** Detailed failures remain package-local. | split: K0 now; every claim package/Q later |

Thus the true K0 pre-implementation blockers are the K0 portion of `001`,
the K0 portion of `006`, the pure-state portion of `005`, the structural-DAG
portion of `008`, and K0's unconditional no-claim disposition under `023`.
The projection and branch tests derived from `002` and `004` are K0 mechanism
tests only; they do not pre-decide the M benchmark. All other accepted v1
concerns remain mandatory later claim gates.

## What must be exact now versus later

### Exact before any K0 code edit

- the exact K0 scope, permanent mode and three false eligibility flags;
- the canonical wire/identity contract and golden/rejection vectors;
- the closed object kinds, schemas, and typed error vocabulary;
- package-closure and no-default behavior;
- pure transition and literal role-projection semantics;
- structural provenance-DAG rules;
- structural registered-root/terminal-receipt closure;
- the eight K0 conformance tests;
- allowed dependencies and prohibited side effects; and
- exact implementation paths and a proposed diff hash in the implementation
  packet reviewed before application.

### Intentionally not exact now

- any PCFL world, relation, symbol, goal, action, outcome, root, twin, split,
  carrier, score, threshold, or benchmark fixture;
- any THINK/DREAM/SLEEP prompt, actor API, reader, compiler, model wrapper,
  tokenizer, or parser;
- GOALS_COMPLETE contents, reset survival, retry policy, failure value, M
  endpoint, estimator, or sample size;
- any child, parent, source receipt, clean-source allowlist, authority
  substrate, provider session, or lineage transaction;
- any writer row, response mask, corpus, adapter, checkpoint, optimizer,
  baseline, codec, opportunity tape, or scientific reducer; and
- any DEV, reserve, confirmation, manuscript, or release decision.

These omissions are protective package boundaries, not implementation
defaults. K0 must reject attempts to supply such content as though K0 had
approved it.

## Exact ratification boundary

### Candidate human decision

The smallest sound decision is:

> Ratify the full staged architecture as the retained research direction, and
> authorize preparation and implementation of K0 only after one final
> hash-bound K0 implementation packet contains the exact schemas, golden
> vectors, target paths, proposed diff, and `K0-01`--`K0-08` commands described
> here. Do not authorize any later package or execution.

Because this advisory contains no proposed code diff or golden-vector bytes,
**ratifying this advisory alone ratifies architecture direction and K0 scope,
not implementation bytes**. The `AGENTS.md` exact-byte rule still requires a
final K0 packet and explicit human approval of its hash and requested paths.
Model agreement, consensus state, a file hash printed by a model, or silence
cannot supply that approval.

### What the later K0 approval may authorize

Only after that explicit human approval, the approved diff may:

- add the isolated K0 contract library and its K0-only unit tests at the exact
  paths named in the packet;
- run those unit tests locally on CPU; and
- write only K0 test reports marked with the permanent false eligibility
  flags.

Any byte outside the approved diff or required solely to repair a failing K0
test requires review and, if material, renewed ratification. Test passage does
not auto-approve the next stage.

### What remains forbidden after K0 approval

- benchmark/root/data/split/corpus generation or mutation;
- any model, tokenizer, remote provider, actor, reader, compiler, or trainer
  call;
- adapters, checkpoints, LoRA, optimizer, writer, or transaction work;
- clean-child/source admission, lineage parenting, parent adaptation, or
  evaluation-descendant creation;
- GPU use, resource reservation, scientific CPU execution, DEV or
  confirmation dispatch;
- importing K0 fixtures or receipts into later evidence, source, selection,
  or manuscript paths; and
- any scientific or paper claim beyond the narrow K0 software statement.

### Separate future human approvals

G, M-SPEC, M-TEXT, E0, M-LORA, P, L, C, O, and every Q confirmation package
each require their own complete architecture delta, fresh interpretations,
adversarial critique, adjudicated disposition of every concern/test, exact
hash-bound bytes and scope, and explicit human ratification. CPU greenness at
K0 or M-SPEC never implies model, adapter, GPU, parenting, scientific, or
confirmation authority.

## Recommended disposition

Adopt this v2 decomposition and rework the combined v1 change rather than
narrowing the paper to supplied-memory use. Preserve M plus L as the paper's
causal spine, E0 as its visible prerequisite, P as the developmental
factorial, C as the narrow ancillary rate--distortion assay, and O as the
separate experiment needed for the strongest action--experience flywheel.

The immediate task is only to make the K0 packet hash-exact and ratifiable.
There is no honest shortcut from that software substrate to S0 or any positive
abstract sentence.

## Sources read in full

- `AGENTS.md`
- `research_loop/changes/chg_20260910_pcfl_core_clean_lineage_v1/change.json`
- `research_loop/changes/chg_20260910_pcfl_core_clean_lineage_v1/critique.json`
- `research_loop/changes/chg_20260910_pcfl_core_clean_lineage_v1/consensus.json`
- `research_loop/plans/pcfl_core_clean_lineage_v1_adjudication_candidate.md`
- `research_loop/advisory/20260910_iclr_nine_page_claim_story_fresh_audit_v1.md`
