# Dream--LoRA--Think compression/rate--distortion assay, fresh design v1

Date: 2026-09-11

Status: **fresh independent design advisory; unbound and non-executable.**
This file changes no architecture, benchmark, representation, compiler,
tokenizer, child, adapter, C11 guard, claim, or execution authority. It
authorizes no source authoring, data/root generation, model/tokenizer call,
training, GPU use, scientific claim, release, or submission. Adoption remains
subject to the complete `AGENTS.md` deliberation and exact-ratification path.

## Executive verdict

Do not ask one experiment to prove three different things:

1. **Lossless semantic coding:** can a representation encode the same
   registered experiential denotation in fewer bytes?
2. **Useful experiential compression:** can DREAM discard event detail while
   preserving authentic connected, traversal, update, and action utility?
3. **Physical parametric compression:** is the complete life-specific state
   required to use a LoRA actually smaller at bounded distortion?

The first two can be screened cheaply with exact serializers and explicit
text. The third is currently foreclosed at the available PCFL scale. The
measured rank-8 all-projection Qwen2.5-7B adapter file is `80,792,096` bytes;
with its discovered config the known persisted subtotal is `80,793,355`
bytes, before catalogs, prompts, calibration, or other life state. Even this
partial numerator requires:

```text
expanded bytes > 161,586,710 for a strict rate below .50
minimal raw bytes > 230,838,157 for a strict rate below .35
```

No current PCFL artifact supplies either denominator. Low rank, fixed
allocation, a flat file-size curve, fewer corpus tokens, or successful LoRA
transport is therefore not compression evidence.

The information-efficient assay is:

```text
zero-model exact-byte ceiling and crossover screen
-> explicit-text rate/utility screen
-> child-authored prospective schema/residual screen
-> optional four-root LoRA transport DEV at the largest passing load
-> physical LoRA rate panel only after an actual complete-state crossover
```

The near-term positive result should be a **semantic-code** result if earned.
LoRA should be described as **transport** or **consolidation** unless its
complete charged carrier crosses the physical boundary.

## 1. The source object: what the child actually experienced

For root `r` and chronological cut `l`, freeze three distinct objects.

### 1.1 Actual actor-visible episode tape, `H_visible[r,l]`

This is the exact UTF-8 byte stream the child could observe during its life:

- public state before an action;
- the exact action it dispatched;
- the ordinary public outcome returned by the world;
- stable episode/action/event ordinals and content hashes; and
- a child-authored pre-action prediction or post-outcome record only when the
  bytes were genuinely emitted in the applicable public slot.

It excludes hidden truth, checker fields, evaluator scores, future goals,
counterfactual answers, oracle annotations, parent-only text, and anything
written after the cut. A later DREAM paraphrase is derived representation,
not new experience.

### 1.2 Minimal public event tape, `H_min[r,l]`

`H_min` is an anti-inflation denominator: one canonical typed row per real
public action--outcome event, using fixed-width enums/integers,
length-delimited UTF-8 fields, sorted keys, no prose, no padding, and exactly
one primary witness. It preserves all public fields needed to reconstruct the
registered event semantics, but not arbitrary surface wording.

Report both `bytes(H_visible)` and `bytes(H_min)`. The former measures the
actual life; the latter prevents verbose skins, repeated boilerplate, or long
outcomes from manufacturing a favorable rate.

### 1.3 Registered semantic denotation, `D[r,l]`

A frozen target-blind admission compiler runs before evaluation goals exist.
It may parse and validate; it may not invent, repair, relabel, or complete a
child record. `D` contains:

```text
ATOM_DEF(content, scope, status)
ATOM_WITNESS(atom_hash, event_id, action_id, outcome_hash, ordinal)
LINK_DEF(endpoint_hashes, relation, scope, status)
LINK_WITNESS(link_hash, event_id, action_id, outcome_hash, ordinal)
SCHEMA_COMMIT(family, parameters, applicability, commit_hash,
              support_hashes, residual_policy, status)
RESIDUAL(schema_hash, observed_exception, witness_hash)
```

An atom requires the child's own executed public action and public outcome. A
link requires both atoms to pre-exist, a child-authored pre-action co-use
proposal, and an independently successful public action for which both atoms
are proof-necessary. A schema is primary-claim eligible only if the child
committed its exact prediction before the confirmation outcomes existed.
Post-outcome schemas are leakage-positive ceilings only.

The residual encoder is deterministic: after outcomes arrive, it records the
exact observed disagreements with the already sealed schema. It cannot revise
the schema, choose a friendlier family, or omit an exception. If the child
commits no valid schema, the DREAM candidate degenerates to the normalized
connected representation and earns no schema-compression credit.

Unique supported atoms, authentic links, prospectively committed schema
parameters, and residuals define semantic load. Tokens, replay views,
paraphrases, repeated witnesses, training steps, and parent messages do not.
Every cut reports the complete load vector rather than one favorable scalar.

### 1.4 Three storage boundaries, not one

The raw ledger is easy to misclassify. Preserve:

```text
B_act   = life-specific state needed for a cold start and registered action
B_learn = additional state needed to resume the next DREAM/SLEEP exactly
B_audit = state retained only for scientific audit and denied to the organism
```

The current cumulative-clean-base sleep recipe needs an earlier compiled
corpus or equivalent state for later rewrites. Such bytes belong to `B_learn`,
not to an allegedly irrelevant audit archive. If only `B_act` is shorter, the
claim is actor-facing compression. A full continually learning organism claim
requires the union `B_act union B_learn` to cross. Retaining the full public
ledger in `B_audit` forbids whole-archive or lossless-autobiography language.

## 2. Carrier panel

Every carrier freezes before evaluation goals, has access to exactly the same
eligible public evidence, and serves the same finite `READ` operation. The
reader returns one canonical row/link list or `NOT_FOUND`; it may not rank
relevance, inject a path, repair a trace, or scan a hidden ledger.

| carrier | exact contents and role |
|---|---|
| `RAW_EPISODIC_TEXT` | `H_visible` plus a candidate-blind index/retriever; strongest honest raw-history baseline, not a free unbounded RAG oracle |
| `EVENT_NORMALIZED_TYPED` | one canonical typed row per event from `H_min`, preserving chronology and repeated public evidence |
| `EXPANDED_SEMANTIC` | one standalone row per atom/link/schema witness, repeating complete referenced definitions; denotationally equivalent expanded comparator, with no prose/padding |
| `NORMALIZED_CONNECTED` | unique atom/link/schema tables plus witness references, residual table, and exact-key index; strongest ordinary database-normalization baseline |
| `SCHEMA_RESIDUAL_FIXED` | prospectively frozen oracle/fixed schema plus exact residuals; CPU compressibility ceiling only |
| `SCHEMA_RESIDUAL_DREAM` | the child's own pre-confirmation schema commit plus exact residuals; only candidate that can support DREAM-authored semantic compression |
| `ORDINARY_CODEC` | one frozen general-purpose lossless codec applied to each exact text baseline, including life-specific dictionaries and decompression scratch |
| `PACKED_REFERENCE` | task-specific enumerative sufficient-statistic reference, including labels, links, witnesses, decoder state, and index; lower-bound calibration, not an agent architecture |
| `LORA_TRANSPORT` | fixed child plus a per-life LoRA trained from exactly the ordered `SCHEMA_RESIDUAL_DREAM` rows, including every required read scaffold |

`SCHEMA_RESIDUAL_FIXED` and `SCHEMA_RESIDUAL_DREAM` must never be pooled. A
fixed human-specified schema can establish benchmark compressibility; it
cannot establish that DREAM discovered or authored the abstraction.

The raw and explicit carriers use the same external READ transcript. If a
raw carrier materializes a normalized cache, the cache becomes part of that
carrier and is charged. If LoRA needs an opaque candidate catalog,
verbalizer, calibration vector, slot order, or recognition prompt, those
objects are part of `LORA_TRANSPORT`; the model file is not the numerator by
itself.

Required LoRA controls at the one transport load are:

- same-semantics explicit text;
- matched link/schema-binding derangement;
- necessary bridge cut;
- truthful twin redirection;
- adapter off;
- cyclic wrong-root adapter;
- candidate-only base;
- unaided generation as a diagnostic, never a rescue; and
- native-interface/non-harm probes.

## 3. Exact rate accounting

UTF-8/file bytes are primary. Pinned-tokenizer counts are secondary. Abstract
rank, parameter count, source-corpus tokens, gzip size of an adapter, and
nonzero singular values are diagnostics only.

For every carrier `c`, root `r`, and load `l`, record:

```text
B_store(c) = persisted life-specific bytes required for cold start
             (payload/checkpoint, manifests, dictionaries, codebooks,
              indices, catalogs/order, prompts/templates/verbalizers,
              calibration/router state, life-specific decoder state)

B_resident_peak(c) = peak distinct life-specific bytes resident during the
                     registered read and action (mounted tensors, decoded
                     copies, indices, caches, KV/workspace, scratch)

B_simul(c) = union of distinct persisted and resident representations that
             must coexist at the action boundary

B_resume(c) = union of B_store and every additional life-specific object
              needed to perform the next exact DREAM/SLEEP update

B_common = byte-identical base child, tokenizer, resolver, runtime, and code
           bundle made available identically to every carrier

B_actor_total(c) = B_common + B_simul(c)
```

Memory-mapped bytes count once in `B_simul` only if a receipt proves the file
and resident mapping are one physical representation. Serialized and expanded
copies both count when both coexist. Candidate-specific executable code is
charged unless the complete sealed code bundle is installed identically for
all carriers. No byte is amortized over roots, users, imagined queries, or
future deployments.

Report these ratios separately for `q in {store, simul, resume}`:

```text
R_exp_C^q  = B_q(SCHEMA_RESIDUAL_DREAM) / B_q(EXPANDED_SEMANTIC)
R_norm_C^q = B_q(SCHEMA_RESIDUAL_DREAM) / B_q(NORMALIZED_CONNECTED)
R_raw_C^q  = B_q(SCHEMA_RESIDUAL_DREAM) / bytes(H_min)

R_exp_L^q  = B_q(LORA_TRANSPORT) / B_q(EXPANDED_SEMANTIC)
R_norm_L^q = B_q(LORA_TRANSPORT) / B_q(NORMALIZED_CONNECTED)
R_raw_L^q  = B_q(LORA_TRANSPORT) / bytes(H_min)
```

Also print `B_actor_total` ratios. They are descriptive because the large
common base can hide a bad life-memory rate.

### Token accounting

For each carrier, preserve:

- stored tokens under the pinned tokenizer for every actor-accessible text;
- query/prompt input tokens, returned-memory tokens, generated thought tokens,
  and output/action tokens per target;
- cumulative tokens over the fixed realized workload;
- candidate tokens scored, including rejected candidates; and
- DREAM/SLEEP training tokens separately as build cost, not memory rate.

Equal generated-token ceilings prevent one carrier from buying utility with
more reasoning. Stored-token count never replaces bytes.

### Latency and work accounting

Report a vector, never a single favorable composite:

```text
compile/render/index/train time
cold-start and mount time
per-query and per-action p50/p95 wall latency
bytes touched and candidates scored per query
reader/resolver calls and FLOPs
peak CPU RAM, GPU RAM, accelerator time, and energy when available
incremental bytes/time to admit one new cohort and become usable
```

Unamortized build/training cost is primary. A secondary amortized figure may
divide only by the predeclared realized query count. Linear hidden scans over
the complete life block scalable-read or compute-efficiency language even if
the byte-rate result passes.

## 4. Distortion, false memory, and utility

No weighted aggregate may hide a failed component. Reduce targets, twin sides,
and technical repeats inside root; the independent unit is a disjoint
environment root.

### 4.1 Representation fidelity

Require independent decoders to prove:

```text
REDUCE(EXPANDED_SEMANTIC) == CANON(D)
DECODE(NORMALIZED_CONNECTED) == CANON(D)
DECODE(SCHEMA_RESIDUAL_FIXED) == CANON(D)
DECODE(SCHEMA_RESIDUAL_DREAM) == CANON(D)
```

byte for byte for every observed semantic item. This is exact semantic
fidelity, not raw-episode reconstruction. Also report event coverage from
`H_min -> D`: supported public items omitted, unsupported items admitted,
wrong provenance, and wrong scope/status each remain separate errors.

### 4.2 Read and behavioral vector

At every claim load report:

```text
A = exact atomic read/action fidelity, including NOT_FOUND
P = proof-valid authentic connected-path completion and action value
G = goal-swap traversal: different registered goals select their necessary paths
O = oldest-cohort retention/action value
N = newest-cohort acquisition/action value
X = cross-era path/action value using old and recent relations
S = sparse fresh-cohort value from a pre-confirmation schema
E = delayed expansion value after a separating action adds a necessary relation
```

`G` and `E` inherit their causal meaning only after the separate PCFL
traversal/expansion mechanism gates pass. Here they measure preservation under
compression; this assay cannot create those claims from scratch.

### 4.3 False-memory vector

Keep three failure layers separate:

```text
F_decode = decoded rows absent from or contradictory to CANON(D)
F_read   = unsupported/wrong-owner/wrong-binding row returned by READ
F_action = action relying on absent, revoked, out-of-scope, or twin-conflicting memory
```

Report confidence/Brier score over the finite valid alternatives plus
`NOT_FOUND`. Required probes include unsupported anchors, look-alike owners,
revoked facts, binding twins, schema-binding shuffles, wrong roots, and
necessary-link cuts. A carrier that answers everything confidently is not a
compressed memory.

### 4.4 Functional non-loss

Use `EXPANDED_SEMANTIC` as the primary functional reference. At every positive
rate load, the explicit reference itself must achieve:

```text
A >= .95
P,G,O,N,X >= .80 separately
F_decode = 0 and F_read,F_action <= .01
```

For the compact semantic carrier require, separately for every registered
utility endpoint:

```text
upper95[U(EXPANDED_SEMANTIC) - U(SCHEMA_RESIDUAL_DREAM)] < .05
upper95[F_action(C) - F_action(EXPANDED_SEMANTIC)] < .01
```

`S` additionally requires a point improvement of at least `.05` over atoms
only with lower95 above zero, failure under schema-binding shuffle, and no
effect in a matched independent-cohort world. `E` additionally requires old-
and-new-row cuts and no-write/action-disabled controls.

For LoRA transport, require `A >= .90`, the same `.05` non-inferiority margins,
false-action rate below `.02`, and authentic advantages of at least `.05`
with lower95 above zero over derangement, bridge cut, adapter off, and wrong
root. Passing licenses transport, not rate.

## 5. Load and root plan

Context length is not the load axis. Use nested PCFL-Stream/Schema cohorts
whose fixed composition adds new atoms, authentic links, and fixed-schema
opportunities. Every cut reports `(K_atom,K_link,K_schema,K_residual)`.
Repeated support or paraphrase never advances the cut.

### 5.1 Zero-model calibration

Use exhaustive tiny worlds plus eight presealed CPU calibration roots. On the
grid `m in {1,2,4,...}` cohorts, render all carriers with one primary witness
per unit and the fixed root label-length classes. Stop at the first of:

- a complete semantic crossover;
- one GiB of minimal raw bytes;
- the ratified CPU/RAM ceiling; or
- a proof from exact intercept/slope arithmetic that no crossover exists.

Let `m*` be the first cohort load at which the fixed schema/residual code meets
all semantic-byte thresholds on every calibration root. Freeze:

```text
m_prev = m*/2        pre-crossover diagnostic
m1     = m*          first claim load
m2     = 2*m*
m3     = 4*m*
```

If no `m*` exists, stop before any model call. Do not lengthen prose, add
witnesses, or choose another root to create it. Physical LoRA uses its own
larger crossover computed from the complete LoRA numerator; semantic `m*`
cannot authorize a physical rate run.

### 5.2 Text feasibility and confirmation

Run four disjoint DEV roots at all four cuts, then extend to eight only if at
least three of the first four roots have complete exact round trip, positive
schema value, and no required contrast with a nonpositive mean. DEV selects no
threshold, schema family, load, prompt, or successful root.

For a paper-level semantic-code result, use a separate sealed root set. Before
identities exist, select the smallest `N in {16,24,32,48}` with at least `.80`
joint power for the complete intersection--union rule using only DEV
root-level covariance and failure-inclusive simulations; require `.90` power
for the primary largest-load `R_norm` and `X` gates. If `N=48` is infeasible,
narrow the claim rather than weaken margins. A reasonable planning default is
`N=24`, not a release guarantee.

### 5.3 Minimum LoRA confirmation

LoRA follows, never precedes, passing explicit text and writer qualification.
At `m3`, use one disjoint install/read canary, then four fresh DEV roots. Build
only `AUTH` and matched `DERANGED` adapters per root; adapter-off, wrong-root,
bridge cut, and twins are read-time controls. Thus the minimum transport
screen is one canary plus eight fits. Stop if fewer than three of four roots
retain text utility or if any route/mount/rollback/interface receipt fails.

Four roots support only bounded transport feasibility. A paper-level LoRA
transport clause needs a separately powered and ratified confirmation set;
its `N` may not be borrowed from text, parenting, C11, targets, or technical
fits.

### 5.4 Physical LoRA panel

Do not run it now. It opens only when exact manifests show the complete LoRA
carrier crosses both expanded and minimal-raw comparators and at least three
strictly later useful cohort loads fit the resource lease. The load set is the
first post-crossover load and the next two doublings. Every load adds unique
semantics, keeps adapter architecture/precision fixed, and must pass every
distortion and authenticity component. A new targeted-layer, quantized,
sparse, or dedicated carrier is a new architecture requiring new
qualification; it cannot retroactively receive the all-layer LoRA result.

## 6. Crossover and claim rules

### 6.1 Semantic-code crossover

At each of `m1,m2,m3`, require root-level one-sided 95% upper bounds:

```text
R_exp_C^store < .50
R_exp_C^simul < .50
R_raw_C^store < .35
```

At `m2,m3`, require `R_norm_C^store` and `R_norm_C^simul < .80`, and require
the candidate no larger in `B_simul` than the frozen ordinary codec. Also
require the incremental byte-growth slope against new unique semantic units
to be at least 20% smaller than ordinary normalized text over `m1:m3`. These
practical thresholds prevent an ordinary deduplication header effect from
being sold as a new compressor.

If only `NORMALIZED_CONNECTED` beats expanded/raw, the result is conventional
normalization. If fixed schema succeeds but the child-authored schema fails,
the benchmark is compressible but DREAM did not perform the compression. If
the child code is shorter but loses utility or increases false memory, report
a lossy smaller code, not useful experiential compression.

### 6.2 Physical LoRA crossover

The exact same byte and distortion rules apply to the complete LoRA carrier,
not to rank. A physical clause additionally needs all three claim loads
strictly beyond the observed complete-state crossover. The current rank-8
known subtotal alone has these strict intercepts:

```text
B_store >= 80,793,355 bytes
expanded comparator must exceed 161,586,710 bytes for R_exp < .50
minimal raw comparator must exceed 230,838,157 bytes for R_raw < .35
```

Auxiliary bytes move the intercept upward. Current-scale success is therefore
not expected and should not consume GPU time.

## 7. Release ladder and maximum claims

The release order is noncompensatory:

```text
valid public source and target-blind admission
-> exact E/N/schema round trip
-> complete byte/resident/resume manifests
-> explicit-text common-read equality and utility non-loss
-> authentic connection/traversal/expansion preservation controls
-> prospective child-authored schema value
-> rate crossover versus expanded, raw-minimal, normalized, and ordinary codec
-> optional same-semantics LoRA transport
-> future complete-state physical crossover at three useful loads
```

Maximum claims by stopping point:

| highest passing point | maximum language |
|---|---|
| fixed schema CPU only | “the registered PCFL-Schema distribution admits this exact schema-plus-residual code” |
| normalized text only | “a deterministic compiler removed duplicate structure” |
| child-authored schema + utility + rate | “the child prospectively formed a shorter actor-facing semantic code for its supported experience on the registered distribution” |
| LoRA utility/controls, rate fails | “the same compact semantics were behaviorally transported through the per-life LoRA” |
| `B_act` physical crossover | “the complete actor-facing life-specific carrier was physically smaller at the registered distortion” |
| `B_act union B_learn` crossover | “the resumable learning-state carrier was physically smaller at the registered distortion” |

Even the highest rung does not license compression of the shared base model,
the audit archive, every autobiographical detail, compute efficiency,
unbounded lifetime scaling, universal schema discovery, a literal graph in
weights, parenting, sentience, or general intelligence. C11 remains a separate
fixed-policy/fixed-topology supplied-memory ceiling and contributes no
learning, LoRA, retention, or compression evidence.

## 8. Recommendation

Implement nothing GPU-facing for compression yet. When the learned PCFL relay
is available, the first compression work should be only:

1. exact CPU serializers and decoders for raw-minimal, expanded, normalized,
   fixed schema/residual, and ordinary codec;
2. a byte/resource receipt on eight calibration roots and the power-of-two
   cohort grid;
3. explicit-text common-read and utility tests on at most eight DEV roots; and
4. one child-authored prospective-schema screen.

This sequence can falsify benchmark compressibility, denominator fairness,
schema value, and actor usability before a single adapter is built. Run the
one-canary/eight-fit LoRA transport screen only after all four pass. Leave
physical all-layer-LoRA compression closed until the actual complete carrier
has three feasible post-crossover loads.

## Source receipts

| source | SHA-256 |
|---|---|
| `AGENTS.md` | `1e3c413f3adbf172c409bc642bbf8242a736b0209461b6a7f81203450772f54e` |
| `research_notes/2026-09-11_paper_path_reconciliation.md` | `84b70b5c4d04ddc0c227807d010390b3682fbfcd34e205e697a3c56e23e23b2e` |
| `research_notes/2026-09-11_writer_evidence_adjudication.md` | `7573af1ae595ac6d53966b6d3f30d5195b62497c5ac7d738913050a3884635c1` |
| `research_notes/2026-09-11_full_claim_closure_ladder_v2.md` | `d1c6467d8d7ba4337852a345a170839e842bf03bc2bd29d9582ad384aa2229c2` |
| `research_loop/plans/pcfl_c11_canonical_guard_spec_v12.md` | `2c1fd41aae8c851faf1a75142a955895c76720a26849c052fef1ba63c477ddd2` |
| `research_loop/advisory/20260909_e3_compression_minimal_honest_fresh_design_v1.md` | `8179100ccfe4ef3d527aaa5159fc6bc92fcd710f35784ffc08e241fc0e6e9298` |
| `research_loop/advisory/20260907_one_child_pcfl_rate_distortion_design_v1.md` | `85a036c6f0244ca60652fe10e89ceb500e3bddd30bc69ef9b045abd8e0d3882e` |
| `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v4.json` | `71df2509e42057c10c5ba734df6f9682cbd462d2573190a1984a3a26239aaaf4` |
| `research_notes/56_pcfl_compression_feasibility_adjudication_v1.md` | `95429dea51764970dd6ba32ea517a0eb19c91bffcd96faeb4ef2ce62065db4cd` |
| `research_notes/48_pcfl_stream_and_schema_design_v0.md` | `f0fcbfbf1aa58032b16340821dfa160a40d8674a27dec785276514a876d31359` |
| `research_loop/changes/chg_20260911_learned_pcfl_relay_v5/exact_scope.md` | `6bcef58e5add33602149491177f3f39b9a03f377b9303198a2bad77b3034823a` |
