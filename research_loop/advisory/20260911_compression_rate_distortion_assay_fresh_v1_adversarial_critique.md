# Adversarial critique of compression/rate--distortion assay fresh v1

Date: 2026-09-11

Status: **fresh adversarial advisory only; unbound and non-executable.** This
document changes no architecture, benchmark, denotation, compiler, carrier,
reader, child, adapter, C11 guard, statistic, resource lease, or claim. It
authorizes no source authoring, preparation, materialization, root/data
generation, model/tokenizer call, training, parenting, GPU use, scientific
execution, claim, release, or submission. Any adoption remains subject to the
complete `AGENTS.md` path.

Reviewed object:
`research_loop/advisory/20260911_compression_rate_distortion_assay_fresh_v1.md`.

## Verdict

**REWORK before deliberation.** The draft gets the most important high-level
boundary right: semantic code, useful lossy reduction, LoRA transport, and
physical LoRA compression are different claims, and the present 80.79 MB
rank-8 carrier makes a positive physical result infeasible at current PCFL
loads. Its decision to put CPU accounting before GPU work is also correct.

However, the proposed semantic assay still has six claim-breaking loopholes:

1. the compact numerator and `H_min` denominator do not encode the same object;
2. the child partly determines the denotation on which its compression is
   judged, allowing omission of hard or non-schema-conforming experience;
3. a hidden-truth or theorem-aware admission decision can purify the child's
   memory and leak semantic validity even when no hidden field is printed;
4. the supplied schema language/decoder can contain the very regularity called
   “discovered” while being hidden in `B_common`;
5. verbose expanded/JSON/hash-heavy comparators remain easier to beat than a
   mandatory packed same-denotation baseline; and
6. the common `READ` contract can either externalize the answer for LoRA or
   silently give raw text a semantic index, while making traversal utility a
   property of the shared resolver rather than the carrier.

These are not cosmetic. A system could pass the current rate gates by dropping
unscored public state, emitting only easy rows, receiving an oracle-filtered
admission bit, and selecting a parameter in a supplied task decoder. That would
be a useful engineered code, but not evidence that DREAM formed compressed
experiential knowledge.

## 1. Fatal denotation and denominator problems

### 1.1 `R_raw` is not a same-denotation rate

`H_min` preserves public action--outcome event semantics, including public
state and chronology. `SCHEMA_RESIDUAL_DREAM` reconstructs `D`, which contains
admitted atoms, links, schema commits, and residuals. The draft itself says the
round trip is semantic rather than raw-episode reconstruction. Therefore:

```text
DECODE(C) = D
but generally D != H_min and D does not reconstruct H_min.
```

`bytes(C) / bytes(H_min)` is consequently a *lossy task-projection ratio*, not
a lossless coding rate. Public state, unused action detail, rejected child
records, and non-primary events can enlarge the denominator without being
recoverable from the numerator. A `.35` threshold does not repair the mismatch.

**Required revision:** freeze two separately named assays.

```text
lossless semantic code:
  same target D_pub on both sides; exact round trip required

task-lossy life reduction:
  compare with H_min/H_visible, explicitly list discarded fields,
  and gate on predeclared utility plus omission/false-memory distortion
```

Never use the lossy raw ratio in a sentence containing “same denotation,”
“lossless,” or “complete experience.” The primary coding comparator must encode
exactly the later-defined `D_pub`.

### 1.2 Candidate-authored `D` permits selective forgetting

The current `D` is built from child-produced valid atoms, co-use proposals, and
schema commits. A child that omits difficult mappings or proposes links only
where the supplied schema works can create a smaller, easier denotation. Merely
reporting coverage does not stop this; no coverage floor or fixed opportunity
denominator appears in the release rule.

**Required revision:** before the child acts, freeze an opportunity set
`Omega[r,l]` containing every semantic item the root offers at each cut. Keep
four objects distinct:

```text
D_ref    evaluator-only correct semantic target for every slot in Omega
D_emit   exact child bytes grounded in public slots, with no repair
D_pub    every Omega slot, containing the public-syntax parse or an explicit
         ABSENT/MALFORMED/LATE/UNSUPPORTED status; never hidden truth
D_admit  the well-formed public-syntax subset of D_pub
```

Every opportunity remains in coverage, utility, and false-memory denominators.
All rate carriers must losslessly encode the same complete `D_pub`, including
its adverse slot states; `PACKED_NORMALIZED(D_pub)` is the primary comparator.
Semantic distortion compares `D_pub` with `D_ref`. Missing child output is an
omission, not a smaller load. Require one-sided lower 95% bounds of at least
`.95` for atom and authentic-link opportunity coverage separately and `.80`
for a valid prospective schema commit across structured roots. Every task is
evaluated over `Omega`. The null/empty code may be short, but fails distortion
and therefore can never pass useful compression.

### 1.3 “Target blind” does not prevent admission leakage

The proposed compiler validates atoms and admits links only when both atoms are
“proof-necessary.” If hidden world truth or an exhaustive theorem affects
whether a row becomes actor-visible, the accept/reject event itself is a truth
bit. No hidden field needs to appear in the row for leakage to occur. The same
problem applies if `status` is derived from privileged truth rather than a
public outcome.

This is especially damaging here: the semantic carrier can be cleaner than
the actual child's memory because the benchmark silently removes its false or
unsupported beliefs.

**Required revision:** the actor-visible compiler must be a total,
public-syntactic transducer. It may check chronology, hashes, required fields,
and whether cited public events exist. It may not query hidden truth, unique
minimal proof, future goals, or a theorem solver to admit, reject, relabel, or
set status. Hidden truth checks live only in the evaluator and return nothing
to the child, DREAM, carrier, decoder, reader, or later writer. Malformed,
unsupported, false, and late proposals remain externally scored failures. If
the experiment intentionally exposes verifier feedback, it must be a real
public event supplied identically to every carrier and named as supervision.

## 2. Oracle-schema and coding-baseline problems

### 2.1 The schema language is uncharged side information

The draft distinguishes fixed and child-authored schemas, but the child still
selects `family`, `parameters`, `applicability`, and a residual policy inside a
human-supplied language. A decoder that already knows how cohort descriptors
map to permutation families may contain most of the sought abstraction. A
child selecting a short family ID is not the same as discovering a
representation.

Putting the decoder into a code bundle installed for every carrier does not
make the information disappear. It merely turns the result into compression
*conditional on a supplied task-specific codebook*.

**Required revision:** seal the schema grammar, complete family inventory,
decoder, and their bytes before roots. Report both:

```text
L_conditional = bytes(life code | sealed schema language)
L_two_part    = bytes(task-specific schema language/decoder)
                + bytes(life code)
```

Generic serialization/runtime code may be common. PCFL-specific schema laws,
label dictionaries, family tables, regime maps, or executable decoders must be
charged in the two-part result. Do not amortize them across imagined roots or
deployments. If only the conditional result passes, say “within the supplied
schema language.” If the family is supplied, say the child *selected and
prospectively committed a schema instance*, not that it discovered the schema
family or learned a representation.

### 2.2 Hindsight schema selection remains underspecified

The residual encoder is deterministic after a commitment, but the draft does
not say which commitment wins if the child emits several, changes scope, or
tries multiple families before confirmation. Choosing the shortest or most
accurate surviving commitment after outcomes is hindsight model selection.

**Required revision:** provide exactly one predeclared schema slot per
root/cut, or use a frozen chronological selection rule such as the first exact
parse after a fixed source boundary. Store and charge the raw selected child
bytes, family ID, parameters, scope, and selection metadata. Later amendments
are residuals or failures, never replacement schemas. Parse failure, ambiguity,
or an out-of-language proposal is adverse. The compiler cannot translate prose
into a friendlier enumerated family.

### 2.3 `PACKED_REFERENCE` must be a primary comparator

`EXPANDED_SEMANTIC` deliberately repeats definitions; beating it primarily
proves reference sharing. `NORMALIZED_CONNECTED` is stronger, but JSON, long
content hashes, field names, and exact-key tables can still dominate the
semantic information. Treating the enumerative packed sufficient statistic as
“calibration only” leaves a paper-ready ratio vulnerable to the charge that it
beats serialization overhead rather than a serious code.

**Required revision:** add mandatory `PACKED_NORMALIZED(D_pub)` using dense
local ordinals, packed enums, a charged audit-ID dictionary only where action
actually requires provenance, and a succinct frozen index. Apply the same
ordinary codec to both packed-normalized and schema/residual packages. Use the
same primitive label alphabet and identifier widths for all carriers.

The primary method-relevance gate should be schema/residual versus packed
normalized and its frozen ordinary-codec form. Expanded and raw ratios remain
descriptive. If schema/residual beats expanded but not packed normalized, the
result is reference deduplication/normalization, not a novel compressor.

### 2.4 The semantic-load vector is not an information measure

`(K_atom,K_link,K_schema,K_residual)` treats a one-bit and a thousand-bit
schema as one unit. It also permits one high-capacity parameter vector to
restate all mappings while looking like one schema.

**Required revision:** additionally report predicted opportunities, exact
parameter bytes/bits, ideal packed-reference bits, residual positions and
values, and total same-denotation packed bytes. Choose load by presealed cohort
count, never by observed child output or schema success. “Sublinear” requires a
registered growth-rate contrast against the packed normalized comparator over
at least three strictly increasing semantic loads; a fixed favorable constant
factor is not sublinear compression.

## 3. Reader and utility attribution problems

### 3.1 One `READ` transcript cannot be both fair and native

For explicit carriers, an exact-key index can return the row. For a LoRA, the
model must recognize or generate it. If the LoRA receives answer-bearing
candidate strings and a life-specific ID-to-row dictionary, the external
catalog is memory and must be charged. If it receives only opaque IDs, it
cannot reconstruct a canonical row unless a hidden external dictionary does
the work. Conversely, indexing raw prose by semantic atom key materializes a
normalized semantic cache even if it is called a retriever.

Requiring byte-identical returned rows is a useful decoder test, but then
connected-path utility mostly measures the shared actor/resolver, not the
carrier. It cannot by itself establish that LoRA traverses a graph.

**Required revision:** split the measurement:

1. **coding/fidelity assay (CPU):** an evaluator supplies the same frozen query
   key; each carrier decodes/looks it up; measure exact row, NOT_FOUND, bytes,
   bytes touched, and work. This isolates storage.
2. **native end-to-end assay (downstream of PCFL M1--M3):** the common actor
   chooses queries under the same public state, full symmetric candidate
   universe, call budget, and generated-token ceiling. Each carrier uses its
   frozen native reader. Charge every catalog, key-to-payload table, selector,
   index, prompt, candidate token, and scan. Compare returned rows and actions,
   but do not pretend the reader algorithms are identical.

Candidate alternatives must be exhaustive and symmetric before root truth;
they may not be narrowed by the correct row, goal, path, hit bit, or hidden
binding. Any ID-to-payload map is life-specific carrier state. A raw index
produced by the semantic compiler is the normalized carrier, not raw history.

### 3.2 Compression cannot originate traversal or expansion claims

The draft correctly says `G` and `E` inherit causal meaning only after PCFL
gates pass, but then includes all connection/traversal/expansion controls in
the compression release sequence. That invites one overloaded experiment and
can blur the C11 boundary.

**Required revision:** compression consumes already-qualified learned-relay
artifacts. It asks only whether a smaller code preserves the *same previously
identified* M1/M2/M3 endpoints. If M1--M3 have not passed, omit `G`/`E` from
the compression claim rather than trying to create them here. C11 may supply
synthetic serializer fixtures or a supplied-memory ceiling only; its roots,
power, or success cannot count as child authorship, learning, retention, LoRA
transport, or compression confirmation. Do not modify, finish, or enforce the
C11 guard as part of this assay.

### 3.3 Functional reference and failure denominators need tightening

`F_decode=0` follows mechanically from exact round trip and is not a sampled
behavioral success. The `.01` false-read/action bounds are not interpretable
without fixed target counts, clustered root reduction, and confidence-bound
rules. Point thresholds such as `A>=.95` are weaker than the surrounding
non-inferiority tests.

**Required revision:** predeclare per-root opportunity counts for every false
memory family, reduce technical repeats and targets within root, and use roots
as the independent units. Put one-sided confidence bounds on absolute floors
and ceilings as well as paired differences. Keep omission, unsupported read,
wrong binding, wrong owner/root, revoked status, and false action separate.
Use an intersection--union release rule; multiplicity correction is needed
only for any disjunctive “one of these succeeded” rescue, which should
preferably be forbidden.

## 4. State accounting problems

### 4.1 `B_common` has a bundling loophole

“Install the complete bundle for every carrier” can make a candidate-specific
schema decoder appear common even though only the candidate needs it. This is
an accounting trick, not equivalence.

**Required revision:** define three side-information classes:

```text
B_generic       distribution-independent runtime/serializer, identical use
B_task_shared   PCFL-specific grammar/decoder fixed before roots
B_life          root/life-specific payload, dictionaries, indices, prompts
```

Report conditional (`B_life` given `B_task_shared`) and two-part
(`B_task_shared+B_life`) lengths. Carrier-specific unused code does not become
generic by installation. Scientific audit receipts, absolute paths, and hashes
not required for action are reported as `B_audit`, not used to inflate one
carrier; any provenance map required by the actor is charged.

### 4.2 Storage rate and simultaneous footprint are being conflated

Rate--distortion conventionally concerns code length. `B_simul` sums or unions
disk files, decoded RAM copies, GPU tensors, caches, and scratch. That is a
valuable deployment-footprint measure, but its value depends on load strategy,
allocator, and whether files remain open. It should not be another version of
the storage coding rate.

**Required revision:** make exact packaged persisted bytes the primary coding
rate. Report separately:

```text
incremental physical CPU-RAM peak over an identical warm common process
incremental physical GPU-RAM peak over that process
logical payload bytes resident
peak scratch bytes
bytes touched/query and cold/mount/read latency
```

Specify whether disk and resident copies coexist; count both only in the
deployment-footprint coordinate. Do not call their sum a semantic code rate.
Apply identical packaging/container overhead rules to every carrier.

### 4.3 `B_resume` must follow the actual updater

The current sleep path retrains a cumulative adapter from a clean base and
therefore needs the cumulative compiled corpus or an exactly equivalent source
state. A resume number that stores only the current adapter is false. On the
other hand, optimizer state should not be charged when the frozen updater
actually restarts it every sleep.

**Required revision:** for each carrier, provide a deterministic cold-resume
test from the claimed package into the next admitted cohort. Enumerate the
minimum actual inputs to the frozen updater. If raw ledger/corpus is needed, it
is `B_learn`; if it is kept only for audit and capability-denied, it is
`B_audit`. The actor-facing and resumable-learning claims remain separate. No
hypothetical incremental updater receives credit.

## 5. Resource and feasibility problems

### 5.1 The CPU ceiling is not an executable lease

“Stop at one GiB” across eight roots and several encodings can materialize many
GiB, and no CPU-hour, RAM, disk, or file-count limit is supplied. Most of the
crossover can be computed analytically without writing giant files.

**Required revision:** validate exact serializers on exhaustive tiny fixtures,
then use exact integer length recurrences on the power-of-two grid. Verify
selected boundary points with streaming serialization and SHA-256 without
holding all carriers in memory. A future bound packet must state CPU-hours,
peak RAM, temporary disk, maximum objects, and cleanup/retention policy before
materialization.

### 5.2 The LoRA “minimum” has no token or GPU-hour receipt

One canary plus eight fits is only a fit count. Its cost depends on `m3`, corpus
tokens, sequence length, epochs, and measured throughput. A fixed-schema byte
crossover can occur at a load whose child acquisition or LoRA training is
infeasible. The proposed four-root screen therefore is not yet resource-ready.

**Required revision:** after CPU crossover and actual child corpus
materialization, emit an exact token/sequence/step manifest and estimate from a
measured same-recipe throughput canary. Set hard GPU-hour and wall-time caps
before the remaining fits. A fit interrupted, undertrained, or selected by
performance remains adverse; roots are never dropped. Do not perform LoRA
transport until W1 conditional writing, W2 repeated-write retention/authentic
source, and the required learned-relay endpoint have independently passed.

### 5.3 Confirmation size is not yet identified

The proposed `N in {16,24,32,48}` rule is sensible in spirit, but the complete
intersection includes rate, coverage, schema value, multiple utility endpoints,
and false-memory margins. The design has no current root-level covariance or
failure-rate data for that compound event. `N=24` must not appear in a resource
forecast as if it were likely enough.

**Required revision:** DEV estimates the joint root vector and technical
failure rate. A frozen simulation then chooses `N` or declares the claim
infeasible. Publish the resulting GPU/CPU lease before confirmation identities
exist. If no allowed `N` reaches power, narrow the endpoint set/claim through a
new deliberation; do not weaken thresholds after DEV.

## 6. Cheapest valid staged assay

This is the smallest sequence that closes the loopholes while respecting the
current writer and PCFL state.

### Stage A — zero-model same-denotation falsifier

No child, tokenizer, LoRA, C11 execution, or GPU.

1. Freeze `Omega`, `D_ref`, `D_pub`, the public-only syntax compiler, schema language,
   one-schema selection rule, and exact primitive encodings.
2. Implement conceptually independent encoders/decoders for
   `PACKED_NORMALIZED(D_pub)`, `SCHEMA_FIXED+RESIDUAL`, and an ordinary codec.
   `EXPANDED` and `H_min` are descriptive comparators only.
3. On exhaustive tiny worlds, require exact round trip and zero collisions.
4. On eight presealed synthetic calibration roots, compute exact two-part and
   conditional lengths analytically over a cohort-count grid; stream only the
   boundary points.
5. Stop if schema/residual is not at least 20% smaller than packed normalized
   and its ordinary-codec version at two consecutive strictly increasing
   post-crossover loads, or if its incremental slope is not smaller.

Maximum result: the registered distribution admits a shorter supplied-schema
code. It says nothing about DREAM or a child.

### Stage B — artifact-only child-authorship audit

No new model or GPU if qualifying learned-relay artifacts already exist.

1. Apply the public-only compiler to exact historical prospective child bytes;
   never repair or translate them.
2. Score all `Omega` opportunities for emission, parse, grounding, coverage,
   unsupported content, and chronological commitment.
3. Apply the predeclared single-schema rule and compute the exact code only if
   it was committed before outcomes.

If no qualifying artifacts exist—as is currently likely—record `NO_DATA` and
proceed only after the learned PCFL relay generates them. Do not substitute
C11 supplied memory or a post-outcome schema.

### Stage C — four-root prospective explicit-text DEV

Only after Stage A passes and a learned-relay DEV path exists.

Use four disjoint roots with all roots retained. Compare:

```text
child schema+residual
packed normalized same-denotation text
atoms-only
schema-binding shuffle
matched independent-regime control
post-outcome schema leakage ceiling
```

The public-only compiler cannot filter truth. Evaluate all fixed opportunities.
Require exact round trip, high coverage, no unsupported gain, positive sparse
fresh-cohort value, failure under binding shuffle, and no gain in the
independent regime. This is feasibility only; no paper claim.

### Stage D — powered semantic-code confirmation

Use Stage C root-level covariance and failure rates to freeze a fresh root
count before identities exist. Confirm only the smallest coherent clause:

> Within the sealed supplied schema language, the child prospectively selected
> a schema instance whose exact schema-plus-residual code was shorter than a
> packed same-denotation baseline while preserving the registered utility.

Report conditional and two-part lengths, omission/false-memory vectors, and
lossy raw-life ratios separately. Do not claim learned representation,
compression in weights, universal schema discovery, or whole-life compression.

### Stage E — optional one-load LoRA transport DEV

Only after W1, W2, the relevant M1--M3 relay gate, and Stage C pass.

First perform one disjoint two-build `AUTH/DERANGED` install canary. If it
passes, use four fresh DEV roots with two builds each. Exact writer tokens and
measured throughput must fit a predeclared lease. Candidate universes are full,
symmetric, and charged. Adapter-off, wrong-root, bridge cut, and truthful twin
are read-time controls only where the intervention does not inject a hidden
answer.

Maximum result: the already-qualified compact semantics were transported
through LoRA. The unfavorable LoRA byte ratios remain printed.

### Stage F — physical LoRA compression remains closed

Do not run at current scale. Reopen only when an exact complete
`B_act`/`B_learn` package crosses the packed same-denotation and task-lossy raw
comparators at three useful later loads, and the new architecture/precision (if
any) has its own qualification and exact authority.

## 7. What survives unchanged

Preserve these parts of v1:

- the three-way distinction among semantic coding, useful lossy reduction,
  and physical LoRA compression;
- the measured 80.79 MB rank-8 intercept and no-GPU physical stop;
- unique semantic load rather than replay/paraphrase count;
- exact provenance and chronological cuts;
- explicit old/new/cross-era retention endpoints;
- separate decode/read/action false-memory layers;
- root as the independent unit and failure-inclusive reduction;
- cumulative learning-state accounting;
- text before LoRA and independent power before confirmation; and
- the strict statement that C11 supplies no learning, LoRA, parenting,
  retention, or compression evidence.

## 8. AGENTS.md disposition

The reviewed file correctly labels itself non-executable. This critique is one
adversarial interpretation, not adjudicated consensus. Because the revisions
change denotation, compiler visibility, carrier accounting, baseline status,
reader semantics, endpoints, and claims, they are material. The next lawful
step is a bound successor proposal plus at least one independent fresh-context
interpretation, cross-critique, adjudication of every item above, and exact
human ratification before source authoring. CPU-only does not exempt a material
benchmark change from `AGENTS.md`.

## Source receipts

| source | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `research_loop/advisory/20260911_compression_rate_distortion_assay_fresh_v1.md` | `6aea1c528cc8f1f1384dd8187e7c7e069865e83916282883970131b4a28d98a6` |
| `research_notes/2026-09-11_paper_path_reconciliation.md` | `84b70b5c4d04ddc0c227807d010390b3682fbfcd34e205e697a3c56e23e23b2e` |
| `research_notes/2026-09-11_full_claim_closure_ladder_v2.md` | `d1c6467d8d7ba4337852a345a170839e842bf03bc2bd29d9582ad384aa2229c2` |
| `research_loop/plans/pcfl_c11_canonical_guard_spec_v12.md` | `2c1fd41aae8c851faf1a75142a955895c76720a26849c052fef1ba63c477ddd2` |
| `research_loop/changes/chg_20260911_learned_pcfl_relay_v5/exact_scope.md` | `6bcef58e5add33602149491177f3f39b9a03f377b9303198a2bad77b3034823a` |
| `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md` | `95429dea51764970dd6ba32ea517a0eb19c91bffcd96faeb4ef2ce62065db4cd` |
| `research_loop/advisory/20260909_e3_compression_minimal_honest_fresh_design_v1.md` | `8179100ccfe4ef3d527aaa5159fc6bc92fcd710f35784ffc08e241fc0e6e9298` |
| `research_notes/48_pcfl_stream_and_schema_design_v0.md` | `f0fcbfbf1aa58032b16340821dfa160a40d8674a27dec785276514a876d31359` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v4.json` | `71df2509e42057c10c5ba734df6f9682cbd462d2573190a1984a3a26239aaaf4` |
| `organism_v6/train_adapter_v21.py` | `1df83da2f2660654bbaec92a4cf2c783111aa8692fd690f5b7e87c4fa7e0616b` |
| `organism_v6/train_adapter_v3.py` | `02f47008c676f6aa361a7e18bf30f5010391174d7a0dd9e648532e16cd55e169` |
