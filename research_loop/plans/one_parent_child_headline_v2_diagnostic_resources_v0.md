# One-parent/one-child v2 terminal-diagnostic resource addendum v0

Date: 2026-09-07

Status: **proposal only; not part of the frozen v2 deliberation packet**. This
document authorizes no architecture change, implementation, scientific target
generation, model or tokenizer call, adapter fit or mount, CompilerGym call,
external access, GPU use, manuscript claim, or confirmation-root spend. It is
the downstream resource addendum required by Section 10 of
`one_parent_child_headline_v2_addendum.md`; it must receive its own exact source
binding, review, human ratification, implementation fixtures, and pre-GPU gate
before either terminal diagnostic can run.

## 1. Scope and non-claims

This addendum accounts only for the two post-lock terminal diagnostics on the
32 already-assigned confirmation roots:

1. authentic versus deranged actor-visible one-hop active-text links; and
2. authentic versus shadow action--outcome admission for one terminal
   clean-base LoRA fit.

The intact value in both reducers is the immutable cached P1 terminal probe.
The diagnostic branches run only after all headline root counts, artifacts,
and primary decisions are immutable. They cannot select roots, repair a failed
headline, alter a live store, or return an artifact to any life.

The comparisons are **not whole-resource-neutral**. Link derangement adds one
counterfactual inference branch. Outcome-binding derangement adds one
counterfactual corpus construction, fit, mount, and inference branch. Those
operations define the interventions. Resource accounting caps and exposes
search/rendering capacity inside each added branch; it does not pretend that
the cached factual history cost the same as constructing its counterfactual.

## 2. Exact per-root logical ceilings

The inherited terminal probe has eight programs, eight continuation
opportunities/program, 128 generated tokens/opportunity, one query
embedding/opportunity, a 1,024-token returned-document cap/opportunity, and at
most one native action dispatch/opportunity. The intact P1 row below is a
read-only cached headline artifact: it is not reconstructed, rerun, or charged
again after lock. Each added counterfactual branch receives the same 64
call-slot keys and ceilings. Slots 9--16 do not exist. `DONE` burns remaining
allocation for accounting and triggers no dummy scientific call.
Malformed/no-action opportunities remain observed zeros under the headline
scorer. No call or budget transfers between diagnostics or roots.

| branch/reference | post-lock status | logical calls | generated-token allocation | query embeddings | returned-document tokens | possible native dispatches | clean-base fits |
|---|---|---:|---:|---:|---:|---:|---:|
| intact P1 terminal reference | cached; already charged to headline | 64 | 8,192 | 64 | 65,536 | 64 | 0 |
| link-overlay branch | added | 64 | 8,192 | 64 | 65,536 | 64 | 0 |
| shadow-binding branch | added | 64 | 8,192 | 64 | 65,536 | 64 | 1 |
| **collective amount added/root** | | **128** | **16,384** | **128** | **131,072** | **128** | **1** |

Every added logical call has a hard fully-rendered input ceiling of 6,144
pinned child-tokenizer tokens and the exact 128-token output allocation above.
Thus the added per-root hard input ceiling is 786,432 tokens. Logical
tokenization is ragged with no padding; speculative decoding and prefix caching
are disabled. The two added branches run in two fresh sequential inference
processes, each with `max_num_seqs=8`: process L loads the immutable terminal
P1 adapter and executes only the link-overlay branch; after verified teardown
and cache release, process S loads the clean base plus the single shadow
adapter and executes only the shadow-binding branch. No adapter, KV state,
request cache, or process state crosses the boundary. Eight program calls form
one round, so there are at most eight engine dispatches and eight query-
embedding batches/branch, or sixteen of each/root.

The shadow fit admits at most 81,920 labeled response tokens and 655,360 fully
attended tokens per root. These are coordinate-wise ceilings, not a claim that
the fixed writer attains both; the manifest prints the realized counts. It
uses the ratified clean base, tokenizer/chat
template, response-only mask, rank, target modules, optimizer, learning rate,
epoch/exposure law, rehearsal/anchor slots, row order key, dropout key, and
transactional mount canary. There is no hyperparameter selection on
confirmation roots.

The link branch uses zero updater calls, zero record writes, zero new record
embeddings, zero index mutation, and zero adapter fits. It may compute 64
query embeddings because each branch constructs its own query from its own
current public continuation state. Authentic ranking occurs against the
immutable authentic index before the read-only adjacency overlay renders
copies.

Across the two added branches, there are at most 128 compiler invocations,
24,576 dense query--record dot products (`128 queries * 192 live records`),
and 98,304 BM25 query--document scores (`128 * [192 live records + 576 raw
blocks]`) per root. Link rendering creates at most 256 ephemeral record copies
(`64 queries * four returned records`), examines at most 192 authentic edge
instances, and renders at most 65,536 pinned tokens of copies. The shadow
builder scans at most 576 public action blocks. A shadow fit may execute at
most 2,048 optimizer steps and 4,096 forward/backward microbatches in addition
to the token ceilings above; the inherited fixed writer normally implies a
smaller count and cannot expand to consume these maxima.

## 3. Campaign totals at N=32

The terminal-diagnostic maximum added after headline lock is:

| resource | maximum |
|---|---:|
| logical model calls | 4,096 |
| generated output-token allocation | 524,288 |
| fully rendered input tokens | 25,165,824 |
| query embeddings | 4,096 |
| returned active-text tokens | 4,194,304 |
| possible native dispatches/compiler invocations | 4,096 |
| inference engine dispatches | 512 |
| query-embedding batches | 512 |
| dense query--record dot products | 786,432 |
| BM25 query--document scores | 3,145,728 |
| clean-base shadow fits | 32 |
| shadow-fit labeled tokens | 2,621,440 |
| shadow-fit attended tokens | 20,971,520 |
| shadow-fit optimizer steps | 65,536 |
| shadow-fit forward/backward microbatches | 131,072 |
| fresh inference processes / inference base loads / adapter mounts | 64 each |
| fresh trainer processes / trainer base materializations | 32 each |
| total fresh processes / base materializations | 96 each |
| BGE query-input tokens | 2,097,152 |
| ephemeral actor-visible record copies | 8,192 |
| overlay edge instances examined once | 6,144 |
| traversed-link inspections during rendering | 131,072 |
| shadow action blocks scanned | 18,432 |
| separate compiler wall reserve | 20,480 seconds |

These are hard safety/accounting ceilings, not expected usage. The report must
also print actual generated and rendered tokens, model-processed prompt/output
tokens, early-DONE burned allocation, model calls, engine dispatches, query
batches, dense/BM25 operations, native dispatches, compiler invocations, clone
objects/bytes, scanned event blocks, optimizer steps/microbatches, CPU seconds,
peak CPU RSS, bytes read/written, artifact count, fit/inference wall time,
occupied GPU seconds, peak device memory, and measured energy when the host
exposes a stable counter.

Hard per-root capacity ceilings are: 4 GiB sealed input bundle; 64 MiB
ephemeral clone/overlay material; 256 MiB shadow corpus; 2 GiB adapter and
checkpoint outputs; 1 GiB reports/receipts; 4,096 persistent artifact files;
20 GiB peak local scratch; 8 GiB durable post-run output; 64 GiB cumulative
bytes read; 32 GiB cumulative bytes written; 16 CPU threads; and 24 GiB peak
CPU RSS. A shared read-only model/tokenizer cache is bound and its reads count
toward the 64-GiB ceiling. Crossing a ceiling terminates the resource canary or
blocks the confirmation diagnostic; it never silently enlarges capacity.

## 4. Within-diagnostic invariants

The following are equality fixtures, not statistical outcomes.

### Link contribution

- Intact and overlay use the same root/probe/cut/call-slot random key and the
  same generated-token and action fail-safe allocations.
- The intact query/index/rank/pack receipts are immutable cached headline
  receipts. They are never reconstructed after lock. The overlay branch
  separately receipts its own current query bytes, the same authentic index
  hash, ranked seed IDs/ranks, and packed pre-expansion seed IDs.
- Actor-visible copies differ only in `linked_memory_ids`; target record bytes,
  target tokenizer length, source out-degree, target in-degree, packed record
  cardinality, pack-order class, and total returned tokens must satisfy the
  ratified derangement equalities.
- Infeasible derangement contributes zero and consumes no replacement call;
  it cannot increase another probe's allocation.

### Correct-binding contribution

- Authentic ledger/store/checkpoint bytes remain immutable. The shadow branch
  changes only the deterministic admission bits derived from the registered
  donor-tuple rotation.
- Every selected assistant suffix remains byte-identical to an authentic
  child suffix. Childhood rows, rehearsal fills, anchors, slot weights,
  exposure count, optimizer, row count, and maximum fit tokens follow the same
  fixed writer law.
- The shadow branch gets exactly one candidate fit attempt. A failed/nonfinite
  fit or mount canary blocks the `K_binding` diagnostic release under Section
  6; it is never converted to a favorable zero, retried, or replaced.
- The terminal P1 active-text store is mounted unchanged in the shadow probe.

Any equality failure is a deterministic diagnostic-validity failure and
blocks that diagnostic claim; it cannot be converted to a favorable zero.

## 5. Scale-matched resource canary and p95 lease gate

Before confirmation begins, run exactly eight **new**, excluded resource
canary packets named `diagnostic_resource_canary_000` through
`diagnostic_resource_canary_007`. Their keys use the ratified protocol-HMAC
law under the disjoint `diagnostic_resource_canary` split. Their eight-program
panels are sampled once, without replacement within packet, from a frozen
`RESOURCE_CANARY_UNIVERSE` disjoint from every development, spending-pilot,
confirmation, and strength-certificate universe. Packet IDs/order are
prebound; a failed or slow packet is never substituted.

Before any packet contents are generated, bind the exact generator bytes,
tokenizer/embedding checkpoints, reachable-history constructor, universe,
packet IDs/keys, and expected output-manifest schema. An exact
representation-fixture authorization (below) then permits only CPU
generation, pinned child/BGE tokenization, BGE embedding, indexing, ranking,
overlay, and pack verification for these eight packets. Its resulting packet,
token-ID, embedding, rank/pack, transition, and output-manifest hashes are
reviewed and frozen before canary-only authorization.
Each packet is explicitly a **resource packet containing two separate
coordinate-wise stress fixtures**, not a synthetic scientific root and not a
claim that one terminal P1 store simultaneously maximizes records and links.
Both fixtures begin from empty stores and raw synthetic public events.

The link fixture has 48 programs and 576 action blocks. Programs 0--31 each
commit four legal `ADD` deltas, producing exactly 128 live `SUPPORTED`
records: exactly 64 non-process source records and 64 process-association
target records. Programs 32--47 each commit four legal `LINK` deltas from the
distinct same-scope sources to the already-live targets, producing exactly 64
valid directed links and no additional records. The edges are partitioned
into exact Section-10 endpoint-type/status/scope/target-length buckets, every
bucket has even cardinality at least two, and every source has exactly one
edge. Within each bucket the offset-one target rotation has no original
target, self-link, duplicate target/source, already-linked replacement,
missing target, or superseded target and preserves target in-degree. The
frozen fixture generator supplies the qualifying `PROCESS_ASSOCIATION` items
and complete public evidence required by the inherited deterministic
transition law. The
trace therefore uses exactly `128 ADD + 64 LINK = 192` deltas, reaches the
final state from empty under the four-deltas/program ceiling, and is checked by
a model-free replay oracle before any model operation.

Each of the 64 link-branch calls has a frozen query whose representation-
fixture receipt ranks exactly four linked source records as its pre-expansion
seeds. The overlay creates four source copies and inspects their four links.
Seed-rank-first expansion plus the 1,024-token cap returns exactly four
complete 256-token documents in the frozen source/target order class; the
authentic and rotated packs have identical cardinality and total tokens.
Thus every call exercises an accepted derangement, four clones, four link
inspections, and exact pack equalities: 256 clones and 256 traversed-link
inspections/packet. Every changed source copy is child-tokenized anew at
render time; no authentic-length cache is reused, so this also exercises 256
overlay-copy tokenizations/packet. The graph/rotation/packer proof is
model-free; the actual
hybrid query-to-seed ranks and tokenizer lengths are frozen by the separately
authorized representation preflight below. Failure of any one of its 64
receipts blocks the resource canary rather than invoking the scientific
infeasible-zero path.

The shadow/retrieval fixture is a separate empty-store trace with 48 programs
and 576 action blocks. Every program commits four legal `ADD` deltas, producing
exactly 192 live `SUPPORTED` records and zero links in exactly 192 deltas. Each
fixture contains all six memory types and all three scopes in a frozen cyclic
order. The shadow fixture uses sixteen action families with every
`(era,family)` stratum size at least two. Neither fixture is read by the other,
and their store/index construction, storage, tokenization, and I/O are summed
inside the same packet ceiling.

The timed path replays both stores through the exact transactional production
index path. `ADD` embeds the new record and `LINK` re-embeds the changed source,
so the link fixture performs 192 document embeddings and the shadow fixture
performs 192: exactly 384 BGE document embeddings/root, at most 196,608 BGE
document-input tokens/root, and exactly 96 document-embedding batches/root
(one batch of four changed documents for each of 96 program commits; no
cross-commit batching). It also performs 384 dense index writes; 1,536 BM25
inserts (384 live-record insert/replacements plus 1,152 raw blocks); 64 BM25
removals for link-source replacement; and 1,600 physical BM25 mutations. All
records/event blocks are schema-valid and exactly 256 pinned-child tokens as
proved by the separately authorized pre-GPU tokenizer fixture;
dense documents use the inherited 512-token BGE ceiling. All 64 actor query
inputs/branch are exactly 6,144 rendered child tokens.

The diagnostic-equivalent shadow fit uses the exact inherited fixed writer on
a complete source-bound synthetic childhood, anchor packet, rehearsal pool,
and 48-program shadow deployment trace. It reports its realized geometry and
may use at most 320 positions, 81,920 labeled tokens, and 655,360 attended
tokens; it is not required to attain both token maxima. A second, separately
labeled **trainer-load fixture** contains exactly 320 closed neutral token-ID
sequences, each exactly 2,048 attended tokens with exactly the final 256 tokens
supervised, and therefore attains exactly 81,920 labeled and 655,360 attended
tokens. It uses the same rank/modules/optimizer/runtime path solely to stress
training resources. It is not the writer output, is never mounted, scored, or
used to validate semantic writing, and is destroyed after its receipt. Thus a
canary has two fits and at most 163,840 labeled and 1,310,720 attended fit
tokens. The fixture bytes/token IDs, full writer inputs, exact masks, and
expected hashes must be source-bound before canary-only authorization.

Each packet manifest also binds a deterministic zero-valued rank-8
`P1_RESOURCE_ADAPTER` with the exact terminal adapter tensor shapes, dtypes,
module placement, PEFT metadata, file cardinality, and byte ceiling. It is a
resource-equivalent mount fixture, not an authentic learned checkpoint and
licenses no behavioral claim. Its generator and expected artifact hash are
bound before contents are opened. Inside the timed interval the order is
fixed: verify raw inputs; replay/build both stores and indices; construct and
fit the diagnostic-equivalent shadow corpus; run and destroy the trainer-load
fit; start process L from a fresh base load, mount only
`P1_RESOURCE_ADAPTER`, execute the link calls, terminate, verify GPU memory
release and delete all KV/request caches; then start process S from a second
fresh inference base load, mount only the fitted shadow adapter, execute the
shadow calls, terminate, and repeat teardown verification. Each process has
one adapter hash and 64 fresh request keys. The shadow childhood/writer inputs
are never visible to process L, and process S cannot read L's overlay or cache.

Training is separately process-isolated. Canary process TD loads a fresh clean
base, constructs only the diagnostic-equivalent rank-8 adapter, writes its
hash/receipt, then destroys model, optimizer, dataloader, gradients, allocator
cache, and process. Canary process TL performs a second fresh clean-base load,
runs only the neutral trainer-load fixture, writes its receipt, destroys all
state and output adapter, and exits before either inference process starts.
The two training processes never overlap one another or inference. Therefore
each canary has two training processes/base materializations plus two inference
processes/base loads. Each confirmation root has one fresh shadow-training
process/base materialization, destroys it after the candidate hash is durable,
then uses the two fresh inference processes defined in Section 2. Training and
inference process counts, base-load bytes/time, teardown receipts, and peak GPU
occupancy all lie inside the timed/resource interval.

Resource-only canaries exercise all 64 logical calls/branch and exactly 128
generated tokens/call using a separately labeled stopping-disabled stress
sampler; they execute one frozen valid target-independent compiler action for
each call so all 128 compiler invocations/root occur. These outputs are never
scored, interpreted, trained, or admitted. This stress-only stopping/action
law is not used in scientific diagnostics and licenses no scientific claim.
The fixed action witnesses the compiler execution path but is not asserted to
be a latency maximum. This addendum proposes one common compiler boundary,
`T_compiler=5.000` seconds measured by `CLOCK_MONOTONIC_RAW`, for the headline
P1 probe and both later diagnostic branches. It is valid only if the future v2
implementation amendment and exact human ratification adopt those same bytes
**before any headline root runs**, and every cached intact P1 receipt proves
that boundary. Otherwise both terminal diagnostics are disabled and no
confirmation/all-in compiler reserve is claimed. Under that precondition every
compiler subprocess shares the packet's 16-thread/24-GiB cgroup and is killed,
joined, and receipted at the common boundary; timeout supplies no action
candidate under the same base-incumbent scoring law in intact, overlay, and
shadow. Compiler elapsed time is excluded from the empirical noncompiler
estimator and receives the separate conservative per-root reserve

```text
B_compiler = 128 invocations * 5 seconds = 640 seconds.
```

The resource addendum cannot impose this boundary post hoc. Its later source-
bound amendment must either bind the already-common five-second headline and
diagnostic implementation or remove the terminal diagnostics entirely.

Map one canary packet to one exclusive 48-GiB A40 GPU. Exactly eight packets
run concurrently, one per bound device UUID, on the same host/storage topology
and with the same engine, batch, cache, container, CPU-thread, and filesystem
policy intended for confirmation diagnostics. A run with fewer than eight
concurrent packets does not witness eight-way confirmation scheduling and
cannot pass. For each measure below, empirical p95 uses the nearest-rank rule;
with eight observations this is the maximum observed value:

- end-to-end wall time from immutable diagnostic input receipt through both
  durable branch reports, and the same interval with receipted compiler
  subprocess elapsed time removed (`noncompiler_wall`);
- occupied GPU time summed over fit and inference subprocesses;
- peak device memory; and
- local scratch bytes.

All wall/latency boundaries use Linux `CLOCK_MONOTONIC_RAW` nanoseconds.
Request latency starts after the immutable request receipt is fsynced and
before backend enqueue, and ends after decoded response bytes and usage are
fsynced. Compiler latency starts before subprocess spawn and ends after the
outcome/timeout receipt and process join. Fit latency starts after the
prospective fit receipt is fsynced and before trainer spawn, and ends only
after candidate bytes, train metrics, and adapter hash are durable. End-to-end
time starts before first input verification and ends after final artifact
rehash. Wall clocks are reported only as metadata.

Energy is descriptive and never a pass criterion. Before packets open, every
bound UUID is queried for NVML total-energy-counter support. During the first
already-authorized inference phase, counters must be nondecreasing and their
delta must agree within 20% with trapezoidal integration of 10-Hz NVML power
samples on the exclusive device. Only if all eight devices pass is packet and
aggregate energy reported. Otherwise the field is exactly `UNAVAILABLE` with
the API/error/calibration receipt; missing devices are never imputed and no
energy comparison is licensed.

The canary resource gate passes only if all eight finish without
administrative loss, every equality/capacity check passes, peak device memory
is at most 44 GiB, peak local scratch is at most 20 GiB/root, peak CPU RSS is
at most 24 GiB/root, empirical p95 occupied GPU time is at most 2.0
A40-hours/root, and the conservative wall bound

```text
W_bound = p95_noncompiler_wall + 640 seconds
```

is at most 2.0 hours/root. Observed end-to-end p95 is printed but never
substituted for `W_bound`.

The confirmation-time scheduler is capped at exactly the witnessed
configuration: at most eight roots concurrently, one exclusive bound A40/root,
for four waves. Immediately before post-lock launch, a fresh capacity receipt
must prove the same eight nonfragmented device UUIDs are exclusively reservable
for every wave, at least 240 GiB host RAM, 200 GiB free aggregate scratch, 320
GiB free durable storage, the same storage mount/topology, and remaining lease
duration of at least

```text
4 * W_bound_hours + max(12 hours, 0.25 * 4 * W_bound_hours)
```

and aggregate reserved capacity of at least

```text
32 * p95_occupied_A40_hours
  + max(96 A40-hours, 0.25 * 32 * p95_occupied_A40_hours)
```

in aggregate A40-hours, in addition to the already-reserved headline and
artifact-verification budget. The fixed 12-hour/eight-GPU reserve is scheduler
headroom, not a tail or availability guarantee. Confirmation concurrency may
be reduced only by a new source-bound resource amendment and new schedule; it
cannot extrapolate the eight-way p95 to an unwitnessed mapping. If any capacity
condition fails, the diagnostics are skipped and no corresponding claim is
made; the locked headline remains interpretable.

The eight canary packets add the following hard maxima:

| resource | eight-canary maximum |
|---|---:|
| logical model calls | 1,024 |
| generated output-token allocation | 131,072 |
| fully rendered input tokens | 6,291,456 |
| BGE query embeddings / document embeddings / total embeddings | 1,024 / 3,072 / 4,096 |
| BGE query-input / document-input / total input tokens | 524,288 / 1,572,864 / 2,097,152 |
| possible native dispatches / compiler invocations | 1,024 each |
| returned active-text tokens | 1,048,576 |
| inference engine dispatches | 128 |
| query / document / total embedding batches | 128 / 768 / 896 |
| fresh inference processes / inference base loads / adapter mounts | 16 each |
| fresh trainer processes / trainer base materializations | 16 each |
| total fresh processes / base materializations | 32 each |
| clean-base fits (diagnostic-equivalent + load-only) | 16 |
| labeled / attended fit tokens | 1,310,720 / 10,485,760 |
| optimizer steps / forward-backward microbatches | 32,768 / 65,536 |
| dense query--record dot products | 163,840 |
| BM25 query--document scores | 753,664 |
| dense document index writes | 3,072 |
| BM25 inserts / removals / total mutations | 12,288 / 512 / 12,800 |
| active-text deltas replayed / raw blocks built | 3,072 / 9,216 |
| ephemeral record copies | 2,048 |
| overlay edges examined once / traversed-link inspections | 512 / 2,048 |
| shadow action blocks scanned | 4,608 |
| child-tokenizer items / BGE-tokenizer items | at most 17,920 / exactly 4,096 |
| separate compiler wall reserve | 5,120 seconds |

The representation preflight adds no LLM, compiler, fit, adapter, or GPU work.
Across its eight CPU packets it performs at most 17,920 child-tokenizer items,
exactly 1,024 query plus 3,072 document BGE tokenizations/embeddings, 2,097,152
BGE input tokens, 896 embedding batches, 163,840 dense scores, 753,664 BM25
scores, 3,072 dense writes, 12,288/512 BM25 inserts/removals, 3,072 transition
deltas, 9,216 raw-block constructions, 2,048 overlay copies, 512 one-time edge
scans, 2,048 traversed-link inspections, and 4,608 shadow-block scans. It is
capped campaign-wide at 32 GiB sealed inputs, 16 GiB summed scratch, 8 GiB
durable receipts, 32,768 files, 256 GiB reads, and 128 GiB writes; at most two
packets run concurrently, for 32 CPU threads, 4 GiB scratch, and 32 GiB RSS.

The complete representation-preflight-plus-canary-plus-confirmation ceiling is:

| resource | all-in 32 confirmation + 8 canary maximum |
|---|---:|
| logical model calls | 5,120 |
| generated output-token allocation | 655,360 |
| fully rendered child-model input tokens | 31,457,280 |
| BGE query embeddings / document embeddings / total embeddings | 6,144 / 6,144 / 12,288 |
| BGE query-input / document-input / total input tokens | 3,145,728 / 3,145,728 / 6,291,456 |
| possible native dispatches / compiler invocations | 5,120 each |
| returned active-text tokens | 5,242,880 |
| inference engine dispatches | 640 |
| query / document / total embedding batches | 768 / 1,536 / 2,304 |
| fresh inference processes / inference base loads / adapter mounts | 80 each |
| fresh trainer processes / trainer base materializations | 48 each |
| total fresh model processes / base materializations | 128 each |
| clean-base fits | 48 |
| labeled / attended fit tokens | 3,932,160 / 31,457,280 |
| optimizer steps / forward-backward microbatches | 98,304 / 196,608 |
| dense query--record dot products | 1,114,112 |
| BM25 query--document scores | 4,653,056 |
| dense document index writes | 6,144 |
| BM25 inserts / removals / total mutations | 24,576 / 1,024 / 25,600 |
| active-text deltas replayed / raw blocks built | 6,144 / 18,432 |
| ephemeral record copies | 12,288 |
| overlay edges examined once / traversed-link inspections | 7,168 / 135,168 |
| shadow action blocks scanned | 27,648 |
| child-tokenizer items / BGE-tokenizer items | at most 58,368 / exactly 12,288 |
| separate compiler wall reserve | 25,600 seconds |

Store/index construction, hashing, and other CPU/I/O work are included inside
the timed interval. Applying the Section-3 per-packet ceilings to all 40
packets gives 160 GiB sealed inputs, 2.5 GiB ephemeral clone material, 10 GiB
shadow corpora, 80 GiB adapter/checkpoint outputs, 40 GiB reports, 163,840
persistent files, 320 GiB durable outputs, 2.5 TiB cumulative reads, and 1.25
TiB cumulative writes as sums of hard packet caps. Scratch, threads, and RSS
are concurrency ceilings rather than cumulative consumption: at eight-way
execution they are at most 160 GiB aggregate scratch, 128 CPU threads, and 192
GiB aggregate CPU RSS. Actuals are always printed; these sums are admission
limits, not usage forecasts.
The separately bounded representation stage brings campaign-wide sealed-input,
durable-output, persistent-file, read, and write ceilings to 192 GiB, 328 GiB,
196,608 files, 2.75 TiB, and 1.375 TiB respectively. Its two-way CPU
concurrency caps are separate because it completes and tears down before the
eight-way GPU canary begins.

The tokenizer-item ceilings are constructive rather than inferred from bytes.
Per canary, child-tokenizer work is at most 384 changed-record checks + 1,152
raw-block checks + 128 actor prompt renders + 320 diagnostic-writer sequences
+ 256 overlay-copy renders = 2,240 items; the closed trainer-load fixture
starts from already bound token IDs. BGE work is exactly 384 document + 128
query tokenizations = 512 items. Per confirmation root, cached indices remove
document work, leaving at most 128 actor renders + 320 shadow-writer sequences
+ 256 overlay-copy renders = 704 child-tokenizer items and exactly 128 BGE
query items. The representation preflight repeats the canary's 2,240 child and
512 BGE items/root. These formulas produce the displayed stage and all-in
totals.

### Three distinct authorization transitions

1. After source binding and fresh independent static review, an exact human
   **representation-fixture authorization** may permit only the eight named
   excluded packets' deterministic CPU generation, pinned child/BGE
   tokenization, CPU BGE embedding/index/ranking, transition replay, overlay,
   and pack-equality checks under the stated ceilings. It permits no child or
   parent LLM, CompilerGym, trainer, adapter fit/mount, scientific root, GPU,
   or claim. Its receipts and actual output hashes require a fresh review.
2. After those immutable representation receipts exist and pass fresh review,
   an exact human **canary-only pre-GPU authorization**
   may permit only the eight named excluded packets and their stated
   model/tokenizer/embedding/compiler/fit/GPU operations. It authorizes no
   headline or confirmation diagnostic.
3. After immutable canary receipts exist, a fresh resource/implementation
   review may recommend a separately exact human **confirmation-diagnostic
   authorization** bound to those receipts, the locked headline artifacts,
   current lease receipt, and 32-root roster. A PASS never grants that authority
   by itself.

## 6. Failure and retry boundary

A model request begins when its exact rendered prompt, stochastic key, and
request receipt are durably committed. A fit begins when the corpus/base/
tokenizer/config hashes, optimizer, initialization/row-order/dropout keys,
intended output path, and fit-request ID are durably committed; no receipt
purports to name not-yet-created candidate bytes. A committed request or fit is
never retried or replaced. A pre-request host/transport failure may resume only
from the last hash-verified boundary proving no response, action, or candidate
adapter was created.

| event | exact disposition |
|---|---|
| pre-request failure with no committed request | resume the same prebound boundary; no new key/root |
| committed malformed/context/tool/no-action probe opportunity | no action candidate; score that opportunity under the inherited zero/base-incumbent law; continue |
| compiler-invalid dispatched action | no candidate; continue; if no valid improvement, `I_best=I_base` |
| no eligible/feasible traversed link | that probe's `K_link` contribution is zero |
| shadow rotation changes no slot in a root | that root's `K_binding` contribution is zero |
| overlay equality, shadow-construction, corpus, or token-cap invariant fails before request/fit | deterministic validity failure; do not run the branch; block the corresponding diagnostic claim |
| committed shadow fit exits nonzero, is nonfinite/incomplete, exceeds a cap, or lacks a durable candidate hash | quarantine; do not probe; block `K_binding` release |
| candidate shadow mount/native-action canary fails | unmount and quarantine; do not fall back to clean base or authentic P1; do not probe; block `K_binding` release |
| valid mounted branch later has committed malformed/no-action opportunities | score those opportunities as behavioral failures and continue |
| required artifact/receipt is irrecoverably lost after commit | administrative missingness; no zero imputation; block the affected claim |
| isolated diagnostic process teardown/unmount fails | quarantine process/device; block the affected claim; no state returns to a life |

The shadow process starts from the ratified clean base and either mounts the
single valid shadow adapter or does not probe. Authentic P1 is never a fallback
inside that process. There is therefore no ambiguous “prior committed adapter”
for `V_shadow_write`.

## 7. Required immutable receipts

Before either diagnostic can be authorized, one manifest must bind:

- v2 ratification and intake-state hashes;
- exact root roster and immutable P1 terminal artifact hashes;
- model, tokenizer, chat template, inference backend, compiler, scorer,
  embedding model/tokenizer, BM25/index, writer, trainer, PEFT, CUDA, driver,
  hardware-class, and container/environment hashes;
- exact prompt/schema/parser/normalizer/stop bytes;
- query constructor, packer, overlay, derangement, shadow reducer, fit/mount
  canary, and metric/reducer bytes;
- per-call input/output/action ceilings; batch/padding/prefix-cache/speculative-
  decoding policy; engine/embedding/compiler/index/clone/fit/CPU/RSS/I/O/
  scratch/durable-byte ceilings; and all counter-key mappings;
- exact canary generator, raw fixture, live/audit-record cardinalities,
  record-length/type/status/scope/link/action-family distributions, store/index
  constructors, universe, panel, and output-manifest hashes;
- exact synthetic childhood rows, fixed anchors, rehearsal fills, shadow
  deployment rows, diagnostic-writer corpus geometry, neutral trainer-load
  token IDs/masks, zero-valued `P1_RESOURCE_ADAPTER` generator/artifact hash,
  and the two-process load/mount/teardown/cache-clear order;
- `CLOCK_MONOTONIC_RAW` measurement code, five-second compiler timeout and
  640-second/root reserve arithmetic, NVML energy availability/calibration
  disposition, and every child/BGE tokenizer item and embedding/index batch
  count;
- scale-canary root IDs, raw resource logs, per-root measures, nearest-rank p95
  calculation, exact concurrent device/host/storage mapping, current exclusive
  lease evidence, and reserve arithmetic; and
- a declaration that no diagnostic artifact can be read by a life, parent,
  writer, updater, active-text store, later headline root, or manuscript result
  generator before the headline decision is immutable.

Any hash drift after the gate voids diagnostic authorization and requires a
fresh exact review; it does not authorize repair in place.

## 8. Stage boundary

This revised v0 closes only the missing *shape* of the resource contract. It
is not bound to the current v2 workflow and therefore is not
implementation-ready. The next legitimate step is a fresh independent source
re-audit followed by a separately hash-bound amendment and exact human
decision. No terminal diagnostic or resource canary may be implemented or
executed merely because these arithmetic ceilings are internally consistent.
