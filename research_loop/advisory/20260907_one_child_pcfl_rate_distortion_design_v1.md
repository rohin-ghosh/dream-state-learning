# One-child PCFL rate--distortion design v1

Date: 2026-09-07

Status: **unbound, proposal-only advisory**. It changes no frozen parenting
headline, workflow, manuscript, implementation, benchmark, child/model,
tokenizer, adapter, external state, or GPU authority. It authorizes no root or
target generation, model/tokenizer call, fit, execution, or scientific claim.
Adoption requires the `AGENTS.md` deliberation path, exact-byte human
ratification, model-free fixtures, independent rejection-capable review, and a
separate execution/GPU gate.

## Verdict

**CONDITIONALLY DESIGNABLE, NOT YET RATIFIABLE OR EXECUTABLE.** The smallest
confirmatory compression assay is a post-headline, four-load PCFL-Stream panel
on byte-identical clones of one prospectively selected, parent-deleted child.
It can support a narrow rate--distortion statement about the child's
**life-specific actor-accessible experiential carrier** only if (i) a
deterministic observation-expanded equivalent has exactly the same canonical
denotation, (ii) every life-dependent byte and hidden candidate/index/codebook
is charged, (iii) authentic connected/action value is non-inferior under a
fixed shorter code, and (iv) causal corruptions show that authentic experience,
not protocol or identifiers, supplies that value.

This is a separate E3 mechanism experiment. It neither changes nor rescues the
one-parent/one-child causal headline. It does not establish whole-system
storage compression while an audit ledger is retained, learned schema
discovery, compute efficiency, a graph literally represented in weights, or
compression beyond the registered PCFL distribution.

## 1. Topology and timing are fixed

1. Select one terminal child by a rule frozen before parenting outcomes are
   unblinded. Hash the child, writer/read instrument, prompts, tokenizer,
   adapter layout/rank, and complete parent/nursery deletion receipt.
2. Execute the assay only after the parenting result and artifacts are
   immutable. A failed parenting result cannot be repaired by this assay; a
   later assay from a writer-qualified checkpoint is separately framed.
3. An independent PCFL H/twin pair root is an environment/life draw for a
   byte-identical clone of that one child. Roots, sides, targets, cuts, and
   technical seeds are repeated measures, not other children. No parent,
   classroom, cohort, peer, teacher ensemble, shared store, cross-root update,
   or population-learning edge exists.
4. Development uses only disjoint predeclared PCFL-13 roots. Confirmation uses
   sealed PCFL-Stream roots. No confirmation root is rejected or replaced
   because the child acquired too little, an adapter fit poorly, or a target
   was inconvenient.

## 2. Prospective experiential object and canonical denotation

For root `r` and cumulative lifetime cut `l`, let `H[r,l]` be only the child's
executed public information actions and ordinary public outcomes up to the
cut. Before evaluation goals are visible, the frozen target-blind admission
compiler maps `H[r,l]` to `M[r,l]`. No model output after the cut, target,
score, query, or read may affect `M`.

The canonical denotation `DEN(M)` is the sorted finite tuple of:

```text
ATOM(
  semantic_key, cohort_public_id, relation_type,
  public_subject, public_value, scope, live_status,
  sorted[(public_event_id, action_id, outcome_sha256, commit_ordinal)]
)

USE_LINK(
  min(source_semantic_key,target_semantic_key),
  max(source_semantic_key,target_semantic_key), relation=CO_USE,
  scope, live_status, commit_ordinal, sorted[support_event_id]
)
```

`semantic_key` is the hash of the relation fields, never an arbitrary
answer-bearing name. `USE_LINK` is directionless co-use adjacency committed
between already supported atoms before any evaluation goal. It contains no
goal, target handle, action order, terminal action, success bit, complete path,
shortcut payload, `DECIDE`, or policy continuation. Tombstones are included
only when the frozen READ semantics needs them; otherwise they are audit-only
and actor-inaccessible.

`CANON(M)` is the unique serialization of `DEN(M)`: pinned schema version;
Unicode NFC; fixed enum and integer widths; bytewise lexicographic row and
provenance ordering; length-prefixed UTF-8 fields; no optional whitespace;
content hashes recomputed from serialized fields. The serializer, status law,
deduplication law, link law, and test vectors seal before any scientific root.
Two carriers are semantically equal only if independent reduction produces the
same `CANON(M)` bytes and SHA-256, not merely the same task answers.

Only relations supported by the child's own public actions are experiential.
The engine may schedule opportunities, but neither a hidden solver nor the
harness may choose a favorable acquired subset. Unique supported mappings,
not tokens, exposures, repeated views, or proposal counts, define semantic
load.

## 3. Deterministic `EXPANDED_EQUIVALENT`

`EXPANDED_EQUIVALENT(M)` is a frozen, target-independent observation-normal
form, not a verbose paraphrase selected to make compression easy:

- for every `(ATOM, supporting public event)` pair, emit one minimal
  self-contained typed instance containing the complete atom fields, scope,
  status, and that event's full provenance tuple;
- for every `USE_LINK`, emit one minimal self-contained link instance
  containing both complete endpoint atom records, link fields, and its support
  event IDs;
- use the same pinned primitive encodings as `CANON`, no padding, prose,
  aliases, shared dictionary, compression library, or omitted field; and
- append the minimal schema/version manifest required for a standalone reader.

A separately implemented deterministic reducer `REDUCE_EXPANDED` must satisfy

```text
REDUCE_EXPANDED(EXPANDED_EQUIVALENT(M)) == CANON(M)
EXPAND(REDUCE_EXPANDED(EXPANDED_EQUIVALENT(M)))
    == EXPANDED_EQUIVALENT(M)
```

byte for byte on exhaustive small worlds and every sealed confirmation
artifact. Ambiguous provenance, inconsistent duplicates, or a non-bijective
test is a kill, not an occasion to edit the schema. `CANONICAL_TEXT=CANON(M)`
is also reported: it prevents an inflated expanded comparator from hiding that
a tiny exact symbolic table dominates LoRA.

The expanded form preserves the admitted semantic denotation, status, scope,
links, and provenance; it does not preserve irrelevant raw prose or timing.
Therefore a pass is semantic-code compression relative to this registered
equivalent, not compression of every autobiographical detail.

## 4. Carrier panel and common read protocol

All carriers freeze before evaluation targets, receive identical `DEN(M)`,
use `READ(relation_type, public_anchor)`, and return exactly one canonical row,
one fixed-size link list, or `NOT_FOUND` to the same clean frozen resolver.
They share query bytes, type-valid candidate universe, read/call/action caps,
returned-row schema/token cap, resolver prompt, decoding, workspace, and final
decision supervision. The resolver composes and acts with the memory adapter
unmounted. The host may copy only the row explicitly selected by the child; it
may not rank semantic relevance, select the next edge, repair a path, validate
a proof, or inject an answer.

Primary rate--distortion carriers at every load are:

| carrier | life-specific content |
|---|---|
| `EXPANDED_TEXT` | exact expanded form plus its frozen exact-key index |
| `CANONICAL_TEXT` | exact compact canonical form plus its frozen exact-key index |
| `LINKED_LORA_R` | one clean-base, fixed-layout/rank/precision per-life LoRA trained only from `CANON(M)`; recognition-assisted reads |

The maximum-load causal/diagnostic panel adds:

| carrier | purpose |
|---|---|
| `ATOMS_LORA_R` | same atoms/exposure but no links; resource-lower diagnostic |
| `DERANGED_LORA_R` | same rows, bytes, degrees, types, ages, supports, candidate counts, and training envelope; fixed-point-free endpoint permutation |
| `BRIDGE_SUB_LORA_R` | necessary bridge replaced by a type/degree/token-matched twin edge in the same slot |
| `LORA_G` | unaided generative read sentinel; not allowed to rescue primary recognition failure |
| `ADAPTER_OFF` | same query/candidate machinery with adapter absent |
| `WRONG_LIFE` and `WHOLE_TWIN_SWAP` | same fixed child, isolated other-root/twin carrier; no cross-root communication |
| `CANDIDATE_ONLY_BASE` | identical candidate roster/order without experiential carrier |
| `RAW_EPISODIC_RAG` | audit-only memorization/ledger-access sentinel under the same read and token cap |
| `DIRECT_QA_LORA` | leakage-positive sentinel trained on target answers; never a legitimate comparator |

`EXPANDED_TEXT` and `CANONICAL_TEXT` must first solve an uncurated explicit
oracle suite through this exact external protocol. `LINKED_LORA_R` must beat
adapter-off, wrong/twin-life, and authentic-binding corruptions. A difference
between `LINKED_LORA_R` and `ATOMS_LORA_R` alone is not connectedness because
the latter has fewer bytes. Physical carrier compute need not be equal; it is
measured, and outer-interface equality is verified separately.

Candidate construction seals before targets. Any lifetime-specific candidate
catalog, label table, slot map, verbalizer, calibration vector, index, or
ordering is part of the carrier and charged byte for byte. A roster containing
the answer is not made free by calling it a prompt. Candidate membership,
count, order, token length, `NOT_FOUND`, latency, and retries must have no
target or binding side channel.

## 5. Complete byte and compute boundary

For each carrier/root/load, preserve two byte totals:

```text
B_common = frozen child/base weights + common tokenizer + common resolver
           + common runtime/schema bytes identical across every carrier

B_life(c) = carrier payload/adapters + life-specific tokenizer additions
          + prompts/templates/verbalizers unique to c
          + schemas/dictionaries/codebooks/calibration data unique to c
          + all candidate catalogs/orders/indices/embeddings/link tables
          + router/query state, retained KV/cache/workspace, optimizer state
            retained at action time, and every actor/reader-reachable byte

B_actor_total(c) = B_common + B_life(c)
```

Compression rate is necessarily the incremental experiential rate
`B_life(LINKED_LORA_R)/B_life(EXPANDED_TEXT)`, because the byte-identical
pretrained child is not learned from this life. Nevertheless `B_common` and
`B_actor_total` are printed so a tiny life code cannot be advertised as a
whole-process size reduction. Carrier-specific executable code is charged to
`B_life`; only byte-identical runtime code may enter `B_common`. No byte is
amortized over roots, users, or hypothetical future queries.

The immutable raw public ledger may be retained only in an audit namespace.
Report its exact `B_audit_raw` and eligible raw-event bytes separately. Before
every evaluation, start a fresh process and prove there is no actor, reader,
candidate builder, shortlister, compiler, prompt, workspace, cache, file
descriptor, IPC, timing, retry, or crash-recovery edge to that ledger. Any
runtime read is both a carrier-isolation failure and a rate failure. Because
the archive still exists, no result may say the complete stored life is
compressed.

The compute receipt is a vector, never folded into favorable “equivalent
compute”:

```text
C_collect, C_admit, C_expand/render, C_index, C_train,
C_mount, C_query_encode, C_candidate_generate, C_candidate_bytes_touched,
C_candidates_scored, C_reader_FLOPs, C_resolver_FLOPs, C_actions,
wall_time, accelerator_time, peak_memory, energy_if_available
```

Report unamortized build/compiler/training cost in full and total lifetime cost
at the registered evaluation-query count. A secondary per-query amortization
may divide only by that fixed realized count; it cannot use an invented future
workload. Candidate generation and scoring must remain sublinear in unique
lifetime atoms at the three post-native loads, with a prospectively frozen
operation/FLOP cap. An `O(|M|)` hidden scan is an external-search result and
blocks any scalable parametric-read or compute-efficiency language. This study
can still make a byte-rate claim if its byte and functional gates pass, but no
compute-efficiency claim is available unless the complete unamortized resource
frontier also beats the named comparator.

## 6. Lifetime/load sweep

Mechanically compute

```text
L_native = pinned model maximum input tokens
           - exact system/resolver/goal/public-state/workspace/history bytes
           - maximum returned-row and output reserve,
```

using the pinned tokenizer. Construct one nested PCFL-Stream life per root
with cuts at expanded-equivalent lengths closest from above to
`0.5 L_native`, `2 L_native`, `4 L_native`, and `8 L_native`. The last three
must be strictly beyond native capacity. Every cut must add fresh cohorts and
unique supported relations; repeated evidence cannot advance the axis. If the
fixed generator cannot yield all four valid cuts under the resource ceiling,
there is no scale or compression confirmation.

At every cut freeze fresh target sets for:

- exact atomic detail: forward, reverse, paraphrase, partial cue, unsupported
  rejection, and calibration;
- old retention: decisive atoms from the earliest quartile, with last public
  support outside native context;
- new acquisition: decisive atoms introduced since the previous cut;
- cross-era connected composition: a unique path with at least one old and one
  recent authentic relation; and
- held-out public action value, including a twin-valid redirect and cited-cut
  intervention.

Targets, twin bindings, source opportunities, legal actions, goals, minimal
proofs, candidates, and all RNG streams seal from hidden PCFL truth before any
child action or admitted corpus exists. Failed acquisition scores failure
under intention to treat; the harness never selects a target from what the
child happened to remember.

The fixed LoRA layout, rank, precision, serialized byte allocation, reader,
and candidate law are identical at all four cuts. Each cut is a clean-base
build from its frozen cumulative `CANON(M)`, not an expanding rank, rank
cascade, warm-start hidden state, or post-target repair. If life-dependent
auxiliary state grows, its bytes remain in `B_life`.

## 7. Distortion, non-loss, and rate gates

All scores lie in `[0,1]` and average predeclared targets, H/twin sides, and
technical seeds within pair root before inference. For carrier `c` and load
`l`, report the vector rather than hiding failure in one scalar:

```text
A(c,l) = macro exact atomic fidelity including unsupported rejection
P(c,l) = authentic necessary-path completion with valid cited trace
O(c,l) = old-target action value
N(c,l) = new-target action value
X(c,l) = cross-era action value
F(c,l) = false-memory/action rate on unsupported and twin-conflict probes

distortion(c,l) = (1-A, 1-P, 1-O, 1-N, 1-X, F)
```

The primary functional reference is `EXPANDED_TEXT`, not no memory. At each of
`2x`, `4x`, and `8x`, `LINKED_LORA_R` must meet every non-loss condition:

```text
A >= .90
upper95[A(EXPANDED_TEXT)-A(LINKED_LORA_R)] < .05
upper95[P/O/N/X(EXPANDED_TEXT)-P/O/N/X(LINKED_LORA_R)] < .05, separately
upper95[F(LINKED_LORA_R)-F(EXPANDED_TEXT)] < .01
upper95[F(LINKED_LORA_R)] < .02
```

The text reference itself must retain oracle headroom and meet `A >= .95`,
`P/O/N/X >= .80`, and `F <= .01`; otherwise the interface/load is invalid.
These are prospective candidate margins requiring ratification and power, not
facts about an unrun system.

The byte-rate gate uses serialized bytes, not rank, allocated tensor size in
isolation, tokens, or a favorable file-compression program:

```text
R_exp(r,l) = B_life(LINKED_LORA_R,r,l)
             / B_life(EXPANDED_TEXT,r,l)
R_raw(r,l) = B_life(LINKED_LORA_R,r,l) / eligible_raw_event_bytes(r,l)
```

Release “compressed experiential code” only if all of these pass:

1. the adapter allocation and every auxiliary life byte are fixed before
   targets and do not grow by changing precision, modules, rank, vocabulary,
   prompt, candidate catalog, or index outside the charged manifest;
2. the one-sided root-level 95% upper confidence bound for `R_exp` is below
   `0.50` at both `4x` and `8x`;
3. the corresponding upper bound for `R_raw` is below `0.35` at `8x`;
4. at least one prospectively named crossover occurs by `4x` and remains at
   `8x`; and
5. the upper confidence bound for the log--log slope of `B_life` against
   unique supported mappings over `2x/4x/8x` is below `0.50`, while unique
   mappings increase at every cut.

The slope is a descriptive fixed-range growth test, not an asymptotic law.
Failure of either byte threshold or any functional non-loss component removes
the compression clause. `CANONICAL_TEXT`, raw RAG, and the exact symbolic
sufficient statistic remain visible on the rate--distortion plot even if they
dominate the LoRA.

## 8. Causal authenticity gates

At the sealed `8x` cut, the following root-level contrasts must each have a
one-sided 95% lower confidence endpoint above zero and point estimate at least
`.05`:

```text
C = P(LINKED_LORA_R) - P(DERANGED_LORA_R)
T = X(LINKED_LORA_R) - X(BRIDGE_SUB_LORA_R)
L = P(LINKED_LORA_R) - P(ATOMS_LORA_R)       [supporting only]
Koff   = X(LINKED_LORA_R) - X(ADAPTER_OFF)
Kwrong = X(LINKED_LORA_R) - X(WRONG_LIFE)
Ktwin  = twin_redirect(LINKED_LORA_R) - twin_redirect(WHOLE_TWIN_SWAP)
```

`C` identifies authentic matched link structure; `T` identifies necessary
path content. `L` cannot replace either. Adapter-off and wrong/twin-life show
that the assigned carrier matters, while `CANDIDATE_ONLY_BASE` must remain
below its predeclared no-life ceiling. Complete path masking must change the
operation, and twin substitution must redirect to the twin-valid action rather
than merely induce `NOT_FOUND`.

The compact and expanded text carriers must use the same queries and yield
the same canonical rows on exact reads. Their action difference must be within
the same `.05` non-inferiority margin. Otherwise carrier protocols, not rate,
have changed. No claim of “inside the LoRA” is released: these interventions
identify behaviorally accessible authentic information carried through the
adapter, not its internal human-readable organization.

## 9. Statistics and prospective power

The independent unit is one PCFL H/twin pair root conditional on the one fixed
child. Every assigned root, including parse, acquisition, fit, mount, and read
failures, appears once; scientific failure is the registered zero/worst value.
Targets, loads, twin sides, calls, and seeds never increase `n`.

Use paired root-level estimands and a fixed release sequence:

```text
denotation/oracle validity
 -> explicit-carrier equivalence
 -> causal authenticity (C, T, Koff, Kwrong, Ktwin)
 -> distortion non-loss (A, P, O, N, X, F at 2x/4x/8x)
 -> rate thresholds and crossover
 -> fixed-range sublinear-growth statement.
```

Stop claim release at the first failed rung. Each composite is an
intersection--union gate: every named component must pass; no maximum,
aggregate action score, or later favorable load rescues failure. The fixed
sequence and one-sided 95% root-level confidence procedures control claimwise
familywise error at `.05`; the exact interval/randomization method and bounded
failure reducer must seal before roots.

Provisional confirmation is `N=48` pair roots. Before confirmation identities
exist, use only disjoint DEV/pilot nuisance distributions to simulate the
complete joint pass rule. Freeze the smallest `N` in `{32,48,64,96}` that has
at least `.80` joint power at these registered planning alternatives:

- causal contrasts `0.10` against the released SESOI `.05`;
- true compact-minus-expanded functional loss `0.00` against NI margin `.05`;
- false-memory excess `0.00` against margins `.01` and `.02`; and
- `R_exp=.35`, `R_raw=.25`, and byte-growth slope `.25` against thresholds
  `.50`, `.35`, and `.50`.

Also require at least `.90` simulated power for the primary `8x` `X`
non-inferiority and `R_exp` gates. Simulation must preserve empirical
within-root correlations across carriers, loads, and endpoints and publish
assumptions/sensitivity to the bounded worst case. If `N=96` cannot satisfy
the rule inside the resource ceiling, narrow or stop before confirmation; do
not weaken margins, select endpoints, or add roots after efficacy is visible.
No early efficacy stop or performance-conditioned root replacement is allowed.
A blinded nuisance-only extension is permitted only if its exact trigger and
maximum were ratified before confirmation.

## 10. Adversarial loophole audit and kill gates

1. **Raw-ledger laundering:** retain it for audit only, count and print it,
   prove fresh-process non-reachability, and kill on any access. The eligible
   claim is not whole-life archival compression.
2. **Hidden codebook/index/prompt/candidate scan:** hash and count every such
   byte; log all candidates and bytes touched; kill the rate gate on an
   unmanifested object, target-conditioned roster, answer-bearing ordering, or
   linear lifetime scan hidden behind READ.
3. **Carrier-protocol mismatch:** require the common outer READ transcript,
   candidate universe, returned schema/budget, resolver bytes, and decision
   supervision. Explicit text must work first. A protocol mismatch invalidates
   the contrast rather than becoming a substrate advantage.
4. **Undertraining called compression:** on disjoint DEV, freeze the smallest
   update schedule for which doubling steps changes low-load atomic install
   fidelity by less than `.01`; require low-load `A >= .98` on training-semantic
   reads and healthy mount/off receipts. Confirmation is never retuned. High-
   load failure is scored as distortion, not explained away; low-load failure
   kills the writer/read instrument.
5. **Post-hoc schema:** seal `DEN`, `CANON`, `EXPANDED_EQUIVALENT`, compiler,
   and every coding dictionary before roots. This assay measures deterministic
   semantic consolidation, not learned abstraction. A learned-schema claim
   requires the separate prospective PCFL-Schema prediction-before-
   confirmation design; no schema invented after evaluation may enter here.
6. **Memorization and identifier shortcuts:** hold out whole roots/nonce
   namespaces; randomize mappings and renderers; require H/twin visible-byte
   equality, direct-record closure, goal/state/identifier/action-frequency/
   passive-signature/no-life ceilings, old/new/cross-era minimal proofs,
   binding swaps, and raw-RAG/direct-QA leakage sentinels. The training corpus
   contains no evaluation goal, target answer, final action, complete path, or
   policy continuation.
7. **Amortized compiler/training costs:** report the unamortized compiler,
   index, adapter build, and training vector in full. No hypothetical reuse is
   credited. Failure to fit inside the ratified resource envelope kills
   execution; large cost does not falsify a byte-rate result but forbids
   efficiency or practical-superiority language.
8. **Capacity masquerading as compression:** fixed rank is not evidence. The
   complete `B_life` thresholds, three post-native cuts, non-loss endpoints,
   causal controls, and sublinear fixed-range slope must all pass. Linear
   auxiliary growth or silently larger precision/modules fails.
9. **Expanded-baseline inflation:** require minimal normal-form bytes,
   round-trip equality, independent fixtures, and visible `CANONICAL_TEXT` and
   exact graph points. If a tiny explicit carrier wins, report it.
10. **Selection and multiplicity:** seal targets from hidden truth/source tape,
    retain every root, average repeats inside root, use the fixed sequence and
    powered IUT gates, and forbid post-hoc load, margin, or successful-chain
    conditioning.

Additional pre-execution kills are: incomplete parent/nursery deletion;
unfrozen child selection; fewer than three post-native loads; plateaued unique
mappings; model-free oracle or text-oracle failure; derangement/bridge matching
failure; any target leakage; insufficient action headroom; failed transactional
mount/rollback; absent p95 resource lease; failed fresh independent review; or
missing exact human ratification and separate GPU authorization.

## 11. Exact claim ceiling

Only if the earlier connected-carrier rung and every gate above passes may the
paper add:

> Conditional on one prospectively fixed, parent-deleted child and the
> registered PCFL-Stream distribution, a fixed-capacity recognition-assisted
> per-life LoRA carried authentic connected relations derived from that
> child's own public action--outcome experience. Across the registered
> `2x--8x` post-native loads, it preserved atomic, old, new, cross-era, and
> held-out action value within the prespecified distortion bounds, while its
> complete life-specific actor-accessible code was below the registered rate
> thresholds relative to a deterministic denotationally equivalent
> observation-expanded carrier.

The sentence must immediately report the observed byte ratios, uncertainty,
distortion vector, candidate/retrieval scaling, and the fact that raw history
was retained in an actor-inaccessible audit archive.

It may not say: the entire system or archive was compressed; LoRA is smaller
than the exact compact symbolic carrier unless it actually is; the weights
contain a literal graph; the child discovered a higher-order schema;
compression is lossless outside the scored denotation; training or inference
was compute-efficient; the result generalizes across children, parents,
models, tasks, or unbounded lifetimes; the agent autonomously formed theory;
or the rate--distortion result proves parenting, traversal, the expansion
relay, repeated flywheel improvement, baseline saturation, or general
intelligence.

If only `CANONICAL_TEXT` passes the rate/non-loss gates, the eligible result is
“the complete agent formed a shorter actor-facing textual semantic code,” not
parametric compression. If LoRA preserves utility but misses the rate gate,
say “fixed-capacity parametric transport,” not compression. If rate passes but
any non-loss or authenticity gate fails, report a smaller lossy store with no
useful experiential-compression claim.

## Inputs considered

- `AGENTS.md`
- `research_notes/41_capacity_compression_and_loop_training.md`
- `research_notes/48_pcfl_stream_and_schema_design_v0.md`
- `research_notes/50_rml_paper_design_adjudication.md`
- `research_notes/DREAM_LORA_THINK_FULL_EVIDENCE_STACK_20260907.md`
- `research_notes/54_one_child_pcfl_relay_v1_causal_repair.md`
- `research_loop/advisory/20260907_objective_coverage_audit_v1.md`
- `research_loop/advisory/20260907_one_parent_v2_repair_synthesis.md`
- `research_loop/advisory/20260907_one_parent_v2_objective_reaudit_v3.md`
- `research_loop/advisory/20260907_one_parent_fresh_attack_adjudication_v1.md`
- `research_loop/advisory/20260907_one_parent_post_confirmation_pcfl_relay_attack_v1.md`
