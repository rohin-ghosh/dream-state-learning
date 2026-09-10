# One-parent/one-child v2 diagnostic-resource re-audit v3

Date: 2026-09-07

Status: **fresh independent read-only re-audit of repaired proposal-only
bytes**. This memo changes no source, workflow, implementation, model,
tokenizer, compiler, adapter, store, or execution state. It authorizes no
implementation, tokenizer/embedding/model/compiler call, fit, mount, GPU use,
confirmation-root spend, or scientific claim.

## Audited bytes

- `research_loop/plans/one_parent_child_headline_v2_diagnostic_resources_v0.md`,
  SHA-256 `144794251f9a6ed8a0ad8d87a96411a25f760ae24b1e7585c30eeefee3491ee5`;
- prior diagnostic resource attack v1, SHA-256
  `ea1359da81abda095bdf227ebf0c5df84b59b5369857a95467a9a0b979b0c30c`;
- prior diagnostic resource re-audit v2, SHA-256
  `81dc1565d237ddeb4fd1e27be98865e5ec6114bcfd41379871d4613fcf346d6f`;
- `research_loop/plans/one_parent_child_headline_v2_addendum.md`, SHA-256
  `3c13492bb1378e07d966597efb9eb72f3c8742631a1e7ef1cb7b8977a5039cff`;
- `research_loop/plans/active_text_fixed_contract_v1.md`, SHA-256
  `0fbb16b124f640c0adcecc46d2270a7ee11e6c63866885d56e3b0e3468ed09c7`;
  and
- `research_loop/plans/one_parent_child_headline_v1.md`, SHA-256
  `e356bcecc0cdec3199cf8ecb23c2dc9790a59a11ee6dc8f81b1bfd399c7cf4d5`.

## Verdict

**REVISE.** R1--R3 are largely repaired: the proposal now uses two honest
coordinate-wise reachable store fixtures, counts their document-index work,
and separates the diagnostic-equivalent writer fit from a load-only trainer
stress fit. The remaining blockers concern whether the link intervention is
actually exercised, missing trainer process/base-load and overlay-tokenizer
work, a compiler timeout that is not valid for both the cached intact and new
branches, and a tokenizer fixture that must exist before the authorization
that first permits tokenizer execution.

## R1--R5 disposition

| prior item | disposition | finding |
|---|---|---|
| R1 reachable store | **PASS IN PART** | `128 ADD + 64 LINK = 192` and `192 ADD = 192` are separately reachable under four deltas/program for 48 programs, and the two stores/resources are explicitly separated and summed. The link store does not yet prove a feasible derangement/traversal/maximum pack, so its runtime stress path can still collapse to the protocol-defined infeasible zero. |
| R2 raw-to-index work | **PASS IN PART** | `384` document embeddings/packet, `196,608` BGE document tokens, `96` document batches, `384` dense writes, and `1,536/64/1,600` BM25 inserts/removals/mutations are correct for the two traces. Overlay-copy tokenization and trainer/base-load work remain absent. |
| R3 writer versus load-only fit | **PASS** | The diagnostic-equivalent fit now keeps the fixed writer and realized geometry; the separate 320-by-2,048 neutral token-ID load fixture is explicitly nonsemantic, unmounted, unscored, and separately counted. |
| R4 process/adapter/cache lifecycle | **REVISE** | The two fresh inference processes and L-to-S teardown are clear, but training-process/base-load/reset lifecycle is not defined or counted. The canary-only tokenizer prerequisite is also circular. |
| R5 compiler/time/energy/all-in law | **REVISE** | Clock and GPU-energy dispositions are much stronger and displayed arithmetic is mostly correct. The five-second compiler timeout has no valid scope relative to the inherited scientific timeout, the link fixture need not exercise its expensive path, and some “all-in” rows omit required work. |

## Arithmetic verification

The following repaired calculations are correct:

- confirmation: 128 added calls/root gives 4,096 calls, 524,288 output
  tokens, 25,165,824 rendered inputs, 4,096 query embeddings, 512 query
  batches/engine dispatches, 786,432 dense scores, and 3,145,728 BM25 scores
  over 32 roots;
- canary: two 192-delta traces give 384 document embeddings, 384 dense writes,
  1,536 BM25 inserts, 64 removals, and 1,600 physical mutations/packet;
- eight canaries: 1,024 calls, 3,072 document plus 1,024 query embeddings,
  768 document plus 128 query batches, 16 fits, 1,310,720 labeled tokens, and
  10,485,760 attended tokens; and
- the displayed confirmation-plus-canary sums for calls, generated/rendered
  tokens, query/document embeddings and BGE tokens, fits/fit tokens,
  dense/BM25 scores, index mutations, deltas/raw blocks, copies/edge scans,
  shadow scans, and compiler seconds follow from their stated per-packet
  premises.

One displayed operation maximum does **not** follow from the fixed canary:
the link fixture gives 64 distinct sources exactly one link each. At most four
source records are returned per query, so 64 calls can inspect at most
`64 * 4 * 1 = 256` traversed links/packet, not 4,096. Its eight-canary maximum
is therefore 2,048, not 32,768, and the corresponding all-in sum with the
confirmation ceiling is 133,120, not 163,840. Reaching 4,096 would require
four returned sources each with 16 links/call, contrary to the distinct-source
fixture as written.

The 160-GiB input, 2.5-GiB clone, 10-GiB corpus, 80-GiB adapter/checkpoint,
40-GiB report, 320-GiB durable-output, 2.5-TiB read, and 1.25-TiB write sums
also correctly multiply the Section-3 caps by 40. Correct multiplication does
not close the omissions below.

## Exact blockers

### B1. Reachability does not ensure the link stress intervention executes

The link trace proves valid records and links, but not the exact Section-10
derangement. It does not require at least two suitable edge instances in every
exact endpoint-type/status/scope/target-length bucket, a no-original/no-self/
no-duplicate rotation, frozen pack-order preservation, or queries whose fused
seeds actually traverse the links and return four complete documents under
the 1,024-token cap. All records having length 256 and all types/scopes being
present is insufficient; the exact bucket includes both endpoint fields.

Consequently all 64 calls can legally hit no eligible `TRAVERSED_LINK`, take
the protocol's infeasible-zero path, and avoid the clone/expansion/packing work
that the canary purports to stress. The maxima for 256 copies and 4,096
traversed-link inspections/root would then be paper ceilings rather than a
witnessed scale path. Independently, the fixture's one-link-per-distinct-source
law makes 4,096 inspections arithmetically unreachable even if every query
traverses four links; that fixture tops out at 256.

Bind a model-free fixture proving the accepted derangement, exact edge-bucket
cardinalities/rotation, 64 query-to-seed receipts, four-document pack/order/
token equalities, and the exact number of copy and link inspections exercised.
If not all maxima are jointly reachable, use separately named stress fixtures
and combine their costs conservatively.

### B2. Training base loads/processes are missing from the lifecycle and totals

The `80 fresh inference processes / base loads / adapter mounts` all-in row is
correct only if “base loads” means **inference** base loads: two/root across 40
packets. It is not an all-in base-load count. Every confirmation shadow fit
must materialize the clean base before either fresh inference process. Every
canary has both a diagnostic-equivalent fit and a trainer-load fit before its
two inference processes. The source does not say whether those two fits use
one reset training process or two, how clean weights/optimizer state are
restored, or whether either training model remains resident when process L
starts.

Define and receipt the training process count, clean-base materializations,
fit-to-fit reset/destruction, optimizer/cache release, and overlap prohibition.
Relabel the existing row as inference-only and add the exact trainer processes
and base loads to the 8-canary and 40-packet totals. Their load time, bytes,
peak memory, and occupied GPU time must remain inside the measured interval.

### B3. Overlay-copy child-tokenizer work is omitted

The item formula counts changed authentic records, raw blocks, complete actor
prompts, and writer sequences, but the overlay changes
`linked_memory_ids`. Those actor-visible copies have new canonical bytes and
must be tokenized (or covered by an exact proved reuse law) before enforcing
copy length, four-document packing, and total-returned-token equality. They
cannot inherit the cached authentic source-record length merely because target
records share an exact-length bucket.

At the stated maximum this is up to 256 copy-tokenization items/packet: up to
2,048 over canaries and 8,192 over confirmation roots, unless a smaller exact
unique-copy/cache count is frozen. Add the exact rule and revise the displayed
15,872/30,208 child-tokenizer item ceilings and associated CPU/time accounting.
With per-render tokenization and no proved reuse, the corrected figures would
be 17,920 for eight canaries and 40,448 all-in.

### B4. The five-second compiler law cannot presently bound confirmation

The source first places the five-second timeout in the resource-canary stress
paragraph, then uses `128 * 5 = 640` seconds/root in confirmation totals and
lease capacity while saying scientific timeout/failure scoring remains the
inherited law. These statements are compatible only if the inherited intact
P1 terminal probe already uses the same exact five-second compiler boundary.
No such numeric boundary is fixed in the audited v1/v2 bytes.

If five seconds applies only to the resource canary, it does not bound the 32
confirmation branches. If it is newly imposed on confirmation, it changes the
counterfactual scorer/failure opportunity relative to the cached intact P1
reference and is a material protocol amendment, not resource-only accounting.

Bind the exact already-common compiler timeout/termination law across intact,
overlay, and shadow calls and derive `B_compiler` from that value. Otherwise
remove the 20,480/25,600-second confirmation/all-in reserve claims and provide
a separately valid conservative bound that cannot change behavioral scoring.
The `noncompiler_wall` subtraction and `W_bound` may be retained only after
that common bound is established.

### B5. Exact-length fixtures require an authorization before the two listed transitions

The plan requires every record/block to be proved exactly 256 pinned-child
tokens and the neutral load fixture's exact token IDs/masks to be source-bound
**before canary-only authorization**. It also correctly says that proof comes
from a separately authorized pre-GPU tokenizer fixture. But the enumerated
authorization sequence begins only with canary-only authority, which is the
first listed transition permitted to make tokenizer calls. Source binding and
CPU/static review cannot produce new pinned-tokenizer receipts by themselves.

Add an explicit, hash-bound tokenizer-fixture authorization and review stage
with no model/compiler/fit/GPU authority, or move tokenization into the later
canary-only scope and stop requiring its output hashes beforehand. A plan or
review PASS cannot supply the missing authorization implicitly.

## Non-blocking findings

- The diagnostic-equivalent and load-only fits are labeled honestly; adding
  the latter makes the p95 training load conservative rather than changing a
  scientific reducer.
- `CLOCK_MONOTONIC_RAW` boundaries, the maximum-of-eight empirical p95,
  eight-way witnessed scheduling, post-lock capacity receipt, nonfragmented
  device reservation, and the warning that reserve factors are not tail
  guarantees are coherent.
- The NVML rule is an exact descriptive GPU-energy availability/calibration
  disposition and makes no energy comparison when unavailable. It should be
  labeled GPU energy; no scientific result depends on it.
- Cached intact receipts remain read-only and uncharged; the two added
  64-call branches preserve the current v2 collective ceiling and no resource-
  neutrality claim is revived.
- The two resource stress stores are isolated non-scientific fixtures, all
  branch processes are per packet/root, the shared model/tokenizer cache is
  read-only, and no artifact returns to life. No classroom, cohort, peer,
  parent re-entry, shared child state, teacher ensemble, or population-
  learning edge is introduced.

## Required disposition

Repair B1--B5 in exact source bytes and obtain a fresh independent re-audit
before amendment deliberation. Even a later PASS would authorize only the next
deliberation step; it would not authorize implementation, tokenization,
embedding/model/compiler execution, an adapter operation, GPU use, root spend,
or a claim.
