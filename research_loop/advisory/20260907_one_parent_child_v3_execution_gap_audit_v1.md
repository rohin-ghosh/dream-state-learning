# One-parent/one-child headline v3 execution-gap audit v1

Date: 2026-09-07  
Scope: independent read-only audit of the source-bound v3 packet against the
current repository implementation. This audit ran no model, tokenizer,
embedding model, compiler, adapter, network, or GPU operation. It modifies no
bound source and grants no implementation or execution authority.

## Verdict

**REVISE for execution readiness.** The v3 packet is coherent enough for its
required five-role deliberation, but there is no conforming headline runtime.
The initialized workflow still has zero role attempts, is at
`advocate_pending`, and has `implementation_authorized=false`
(`.research_loop/intake/chg_20260907_one_parent_child_headline_v3.deliberation.state.json:2-16`).
The protocol itself says the present `organism_v6` code is exploratory and may
not be promoted (`one_parent_child_headline_v1.md:806-825`).

The repository has useful lower-level parts, but **none of the five blocking
surfaces below exists end to end**:

1. a v3 root packet, counter-key schedule, five-service roster, and reducer;
2. a native typed causal transaction spanning child, parent, DREAM, dispatch,
   admission, and complete parent/nursery deletion;
3. the exact response-only, fixed-slot, cumulative rank-8 SLEEP writer with
   transactional fit/mount/rollback receipts;
4. an executable and certified `ACTIVE_TEXT_FIXED` implementation; and
5. the unique-program CompilerGym runner with matched generated-token/RNG
   opportunities and isolated `R0/U0/U1/P0/P1` state.

No four-root pilot is currently permitted. Overall readiness remains roughly
25--30%, consistent with the bound critical-path audit
(`ICLR_2027_SUBMISSION_CRITICAL_PATH_20260907.md:61-78`).

## Audit receipt

- Frozen workflow SHA-256:
  `deb896c6a9aa96491c712d5d64f71a341e15d01fe4caf0aa82417c37053a7274`.
- Source-binding manifest SHA-256:
  `18bcbe31550e4f31e90bdd445d20d017d43c17dd0a828ee34fca51b57262d186`.
- Initialized-state SHA-256:
  `1e69856fd3da8ba7f6b834b70c0aea0a1a0ab1687f5645765c09992b43c43a5c`.
- All 30 directive/context paths were independently rehashed and matched their
  manifest entries: **30/30 PASS**.
- `pytest` is absent from the local Python installation. I therefore directly
  invoked the discovered `test_*` functions in the three explicitly
  model-free suites. Result: **19/19 PASS** under Python 3.9.6 on Darwin arm64:
  `research_loop/test_model_provider_boundary.py`,
  `research_loop/test_experiment_call_ledger.py`, and
  `rml_stage_b/tests/test_g1_cpu_preflight.py`. This validates only those
  components in their own older contracts, not v3 conformance.

## Exact reusable implementation artifacts

| Current artifact | What is reusable | Required v3 qualification |
|---|---|---|
| `research_loop/model_provider_boundary.py` | Exact request/config/raw-response bytes, revision/token evidence, one-shot fresh sessions, byte hashes, and duplicate-session rejection (`:1-12,124-156,215-294,340-385,411-478`). Its adversarial suite passes. | Extend the receipt with v3 event digest/executed seed, prove the backend honors that seed, and integrate it with native action/role capability records. |
| `research_loop/experiment_call_ledger.py` | Predeclared physical-call slots, separation of physical execution from arm attribution, uniqueness, append-only observations, completeness, and matched-envelope checks (`:1-8,44-111,114-149,152-232`). Its adversarial suite passes. | Instantiate the exact five-service/root/cut roster; uppercase v3 service codes are not its current arm grammar; equality must cover tokens, actions, updater/retrieval work, fits, and absent-call burns, not only stage/config tuples. |
| `rml_stage_b/machine.py` plus `rml_stage_b/memory.py` | Strict one-object parsing, immutable registered opportunities, no retry/overwrite, pre-dispatch service binding, typed failures, sealed snapshots, target-excluding builder API, and extensive mutation tests (`machine.py:60-136,370-477,480-524,616-659`; `memory.py:250-317,342-350`). | Generalize rather than copy semantics: the code is RML-specific, its canonical helper does not NFC-normalize strings, and it does not implement v3 THINK/DREAM/parent/writer lineage. |
| `organism_v6/cgym_eval.py` and `gym_backend.py` | A working exploratory CompilerGym subprocess seam and instruction-count observation (`cgym_eval.py:22-57`; `gym_backend.py:37-65`). | Replace its permissive string parser, example-pass leak (`cgym_eval.py:40-47`), first-400 universe enumeration, unpinned environment, and exception-as-success exit with a sealed native action inventory, exact resets/hashes, base incumbent, clipped scorer, and typed failures. Reference code only: v1 forbids promotion. |
| `organism_v6/train_adapter_v21.py` | Chat-template rendering, assistant-only labels, all-layer attention+MLP targets, rank-8 default, and clean-base loading (`:37-61,65-82`). | Writer must be rewritten: current dropout is `.05` not `0`; it truncates answers, skips nonfinite batches, treats empty corpora as success, has no seeds/revision/tensor receipts, token-averages rather than response-normalizes, and writes `DONE` after partial training (`:39-43,47-55,73-89,90-124`). |
| `research_loop/advisory/one_parent_v2_power_sim.py` plus its receipt | Frozen CPU planning sensitivity, fixed `N=32`, named shapes, and adverse-mixture disclosure; source and stdout hashes are already bound (`20260907_one_parent_v2_power_receipt_v2.md:9-40`). | Reuse unchanged only for planning language. It is not the confirmation reducer and supplies no evidence. |

Useful ideas in `organism_v6/ledger.py`, `state.py`, `batch_loop.py`,
`sleep_compile.py`, `rulegame.py`, `nursery_dialogue.py`, and `run_life_v2.py`
are **prototype evidence, not reusable confirmation artifacts**. Examples of
the exact mismatch are JSONL without a hash chain (`ledger.py:15-33`),
hard 22,000-character/FIFO context trimming (`state.py:56-97`), regex action
extraction and tick budgets (`batch_loop.py:16-17,41-90`), an LLM-based sleep
compiler (`sleep_compile.py:82-130`) where v3 requires zero compiler LLM calls,
free-text parent advice and a no-op admission branch
(`nursery_dialogue.py:58-63,131-159`), and an A/B repeated-program runner rather
than the five services (`run_life_v2.py:41-52,63-73,89-143`).

## Dependency-ordered missing code, contracts, and tests

The names below are recommended new-namespace surfaces, not authority to create
them. Every stage must fail closed before the next consumes its output.

### 0. Authority and source closure

**Missing:** completed five-role v3 artifacts, adjudicated consensus, and exact
human ratification. The workflow binds 29 context files plus the directive and
five roles (`one_parent_child_headline_v3.deliberation.json:7-48`), but none has
run. `AGENTS.md` requires deliberation, ratification, scoped implementation,
fresh review, then a GPU gate (`AGENTS.md:3-18,21-35`).

**CPU gate:** rehash every source and verify the consensus ratifies only the v3
delta. A PASS must leave scientific targets, tokenizers, models, adapters,
CompilerGym, and GPUs unauthorized.

### 1. `root_packet.py`, `counter_rng.py`, and `reduce.py`

**Missing code/contracts:** canonical NFC JSON; source-only `protocol_hash`;
HMAC root/event keys; PCG64DXSM; collision rejection; complete Q packets;
uniform 56-program sample/permutation; matched P/U nursery assignments;
five-service cut schedule; root-level `V`, `gAUC`, `W_P`, `W_U`, `D`,
`C_public`, `L_terminal`, and `T_R0`; fixed sequence; missingness; v3 pilot
guard; writer mediator table. The exact source law is at
`v2_addendum.md:33-129,131-207,230-258` and
`v3_spending_repair.md:25-70`.

**Required tests:** byte-stable root replay; one-bit source/config mutation;
within-coupling seed equality and between-group digest/u64 collision abort;
P/U identical nursery and all-five identical wake/probe decks; no task/cut/
call/fit increases `n`; pilot excluded from confirmation; pathological positive
`D` with `W_P<=0` or `L_terminal<=0` must fail; entry imbalance and writer yield
must never alter assignment, matching, exclusion, or adjustment.

### 2. `events.py`, `native_action.py`, and `capabilities.py`

**Missing code/contracts:** one atomic lineage for rendered message JSON and
token IDs, raw assistant bytes, native envelope, parse receipt, exact dispatch,
reset, public result/score, causal offsets, role, and visibility capability.
Persistence must precede parsing; one continuation permits at most one native
action; prose/Markdown imitations never dispatch or become targets. Current
regex parsing and split thought/action rows violate this requirement
(`batch_loop.py:41-88`).

**Required tests:** duplicate key/ID, wrong role, wrong tool schema, malformed
or Markdown `ACT`, multiple envelopes, action mutation, dispatch mismatch,
crash at every transaction boundary, committed-event retry, cross-service/root
read, and exact raw-response-to-training-target byte join.

### 3. `nursery/`, `parent_policy.py`, `admission.py`, and `deletion.py`

**Missing code/contracts:** the actual nonce Codebreaker and RuleShift
generators; 12 matched opportunities and 24 unique tasks per branch; fixed
closed parent output; neutral U inputs/shadows; treatment-independent process
predicates; fresh homologous application; real accept/reject events; and a
fresh-process deletion audit. The packet fixes the task families and dose
(`v1.md:107-162`) and the absolute writer law (`v1.md:179-223`). Existing
`rulegame.py` has only ten transparent Python rules (`:11-27`), while
`nursery_dialogue.py` lets the parent free-write after seeing a clipped tail
and still compiles rejected streams (`:58-63,131-159`).

**Required tests:** exhaustive reset/identifiability/legal-action/collision and
process-predicate audits; independent source/validator implementations;
permutation invariance; parent schema rejects task entities, numbers, answers,
actions, and free text; hidden-world laundering tests; P/U task equality;
neutral-shadow noninterference; rejected advice cannot train; parent-supported
tag cannot change eligibility. Seed sentinels into parent output,
restatements, nursery tasks/ledger/state, rehearsal corpus, optimizer, caches,
filesystem paths, environment, and process memory; deployment must abort if any
sentinel is visible or retrievable.

### 4. `dream.py`

**Missing code/contracts:** typed `RECONCILE_CONTEXT` and `SUCCESSOR_STATE`, one
opportunity per nursery unit and per 16-program era, no retry, predecessor
pointer, evidence/status citations, recall restoration, scheduled post-reset
support continuation, and deterministic emergency failure. The exact law is
`v1.md:225-271`.

**Required tests:** omitted supported/open-surprise item, forged observation,
illegal plan, missing recall handle, oversized state, failed successor, failed
post-reset continuation, early/scheduled opportunity double spend, second
overflow, crash during publication, and proof that the predecessor survives
every failure and fallback bytes never train.

### 5. `sleep_rows.py`, `trainer.py`, and `adapter_transaction.py`

**Missing code/contracts:** only exact `THINK_TO_ACT` and `DREAM_STATE` child
suffixes through EOS; all parent/restatement/result/outcome/prompt/old-history
tokens masked; <=256-token suffix rejected rather than truncated; fixed
scientific slots and deterministic rehearsal fills; exactly four exposures;
20 fixed anchors; suffix-normalized then slot-normalized loss; rank-8 all-layer
LoRA, alpha 16, dropout 0; cumulative clean-base rebuild; separate seeds for
initialization/order/dropout; tensor/config hashes; quarantine, mount, rollback,
and adapter-off receipts. See `v1.md:273-370`.

**Required tests:** byte-identical response across scaffold variants; zero
labels/missing EOS/target truncation/template or target-ID mismatch abort;
parent or result token labeled; wrong authorship; duplicate target; unequal P/U
slot/dose/optimizer positions; nonfinite/skipped batch; empty corpus; stacked
adapter; mount mismatch; rollback failure; and strict native-dialect plus
generic/tool-use/DREAM/active-text canaries after every fit. These tests directly
attack the observed writer dialect drift instead of relaxing the parser.

### 6. `active_text_fixed/`

**Missing entirely:** no Python implementation of `ACTIVE_TEXT_FIXED` exists.
Required are its strict `REFLECT`/`CURATE` schemas, transition preflights,
canonical store, isolated per-service raw ledger/playbook, exact BM25, pinned
BGE dense retrieval, RRF/link expansion/packing, updater visibility, receipts,
and ten golden fixtures. The contract is explicit at
`active_text_fixed_contract_v1.md:24-42,158-375,541-716,724-865`; deployment
thresholds are `v1.md:525-546`.

**Required tests:** all ten golden lifecycle fixtures, malformed/unsupported/
overflow transition classes, stale links, mutation collisions, deterministic
IDs and NFKC tokenization, exact rank/pack equality, probe non-persistence,
cross-service/root isolation, input/output representability, and full resource
arithmetic. Then the once-only model certificate must meet semantic precision,
macro-F1/recall, retrieval recall/citation, task-use, direct-injection, and
headroom gates. Until then `R0` is not a validated/strong reference; the current
abstract's present-tense “same validated evolving textual memory” is premature
(`main.tex:16-33`).

### 7. `compiler_runtime.py` and `run_root.py`

**Missing code/contracts:** sealed eligible universe; exact CompilerGym/LLVM
identity; 48 unique wake plus 8 sealed probes; generated-token stopping; max 12
native actions; base-incumbent clipped score; update/SLEEP/probe cut order;
probe nonreturn; exact `P0/P1` and `U0/U1` checkpoint forks; raw `R0`; isolated
active-text stores; common RNG; and transactional resume. See
`v1.md:400-418,553-583` and `v2_addendum.md:131-151`.

**Required tests:** URI alias/canonicalization collision, train/probe overlap,
repeated wake program, probe event entering any later input/store/corpus,
different token allocation or stochastic opportunity, service/state crossover,
invalid compiler result, negative score clipping, no-action zero, cut-order
permutation, pre-request resume, post-request retry, and all parent-deletion
sentinels. A root must emit one immutable result row, never 56 pseudo-replicates.

### 8. `writer_receipts.py`, `figures.py`, and manuscript conformance

**Missing:** the arm-by-cut table required by v3 (`v3_spending_repair.md:55-70`),
one result manifest driving all tables/figures, and a conformed manuscript. The
current paper has 10 TBD blocks, unproven claims, and undefined/outdated endpoint
language (`main.tex:10-11,31-33,62-63,132-136,210-250,295-314`).

**Required tests:** regenerate every statistic/figure from root rows; source
hash and blinded-label checks; failure/missingness fixtures; claim-firewall test
for every fixed-sequence stopping pattern; P1--R0 always labeled a full-package
deployment-parity comparison, never parenting causality.

## CPU-only preflight ladder

Run in this order after exact implementation authority. Stop at the first
failure; do not use a GPU to diagnose a deterministic defect.

1. **Source/namespace:** 30/30 source hashes; clean new namespace; exact schema
   manifests; no import from exploratory `organism_v6` except explicitly
   transplanted code whose new tests pass.
2. **Root/RNG/reducer:** synthetic Q packets, HMAC/PCG64DXSM fixtures, collision
   aborts, five-service equality, pseudoreplication traps, all fixed-sequence,
   missingness, and v3 spending-gate truth tables.
3. **Native transaction:** mutation and crash-injection matrix from rendered
   bytes through dispatch/outcome/row; no regex/prose action path.
4. **Nursery/parent/deletion:** exhaustive generator audits, process predicates,
   content laundering, neutral shadow, admission, and sentinel deletion.
5. **DREAM:** reversible successor/restoration/no-retry/emergency-reset matrix.
6. **Writer static:** synthetic exact token-ID fixtures where available without
   a tokenizer; target/label/EOS/scaffold/slot/dose/rollback mutation matrix.
7. **Active text model-free:** all ten golden fixtures, store/index lifecycle,
   isolation, retrieval arithmetic, and resource ceilings.
8. **Compiler/root dry-run:** fake provider and fake compiler drive every service
   through 0/16/32/48, failures, restart, probes, receipts, and final reducer.
9. **Resource arithmetic:** exact maximum calls/tokens/fits/bytes/processes plus
   concurrency/lease inequality. Synthetic runs must produce the v3 writer
   mediator table before any scientific identities exist.
10. **Separately authorized CPU representation preflight:** pinned child and BGE
    tokenization, BGE embeddings/index/ranking, transition replay, and exact
    pack equality. This is CPU-only but is **not presently authorized**; its
    separate authorization boundary is explicit at
    `one_parent_child_headline_v2_diagnostic_resources_v0.md:508-526`.

## First permitted four-root pilot launch conditions

All conditions are conjunctive:

1. v3 five-role deliberation completes; exact consensus and scope receive human
   ratification; implementation authority is recorded.
2. Every pure-CPU and authorized representation gate above passes on frozen
   bytes; source-distinct validators agree.
3. Fresh independent implementation/science reviewer and author-side advocate
   both PASS the implemented bytes. Neither can self-authorize GPU use.
4. Exact model/tokenizer/backend/compiler/container/hardware manifests and
   seed-honoring receipts exist; no runtime hash differs from the reviewed one.
5. Neutral writer calibration races only `{1e-6,1e-5,3e-5}`, selects the lowest
   passing rate, duplicates it, and meets <=10-minute fit and <=15-minute
   shutdown/mount/canary p95; otherwise NO-GO (`v1.md:372-386`).
6. `ACTIVE_TEXT_FIXED` passes its once-only semantic, retrieval, use, and
   headroom certificates; otherwise the frozen five-service pilot cannot claim
   its registered strong-reference design.
7. The four-root teachability canary passes its staged authentic-parenting,
   target-only, deranged-state, unparented-self-experience, adapter-off, and
   pre-write checks without routing, proposal, DREAM, generic, or active-text
   erasure (`v1.md:388-398`).
8. Development-only token saturation selects and seals one <=2,048-token
   per-program budget; exact rank 8 and writer law are frozen; no rank sweep or
   post-pilot recipe choice is allowed.
9. Parent/nursery deletion passes in a fresh process. The eligible CompilerGym
   universe, four excluded Q roots, 48/8 decks, all counter keys, and service
   rosters are then sealed. No pilot root is selected or replaced on outcome.
10. A separately exact human pilot pre-GPU authorization names those artifacts,
    operations, four roots, device/process mapping, resource maximum, and lease.

After execution, advancement requires zero validity/resource violations;
`D>0`, `W_P>0`, and `L_terminal>0` jointly in at least 3/4 roots; all three
means positive; and no adverse-bound crossing. All four roots and writer
receipts remain reported and excluded from confirmation
(`v3_spending_repair.md:25-53`).

## Model, tokenizer, compiler, and GPU approvals still missing

- **Parent model:** candidate
  `Qwen/Qwen2.5-32B-Instruct@5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`.
  Parent identity/policy is explicitly a human-ratification field
  (`v1.md:74-90`). Precision/dtype/quantization/tensor-parallel placement is not
  frozen; a 32B full-precision load does not fit one 48-GiB A40, so no hidden
  quantization or two-GPU topology may be assumed.
- **Child/updater model:** candidate
  `Qwen/Qwen2.5-7B-Instruct@a09a35458c702b33eeacc393d103063234e8bc28`;
  exact model files, tokenizer files, official chat-template bytes, EOS/stop
  IDs, dtype, Transformers/vLLM/PEFT versions, and serving/training hashes still
  need representation/canary authorization.
- **Dense retriever:** candidate
  `BAAI/bge-small-en-v1.5@5c38ec7c405ec4b44b94cc5a9bb96e735b38267a`
  with pinned tokenizer and exact prefix/pooling (`v1.md:497-517`). CPU
  tokenization/embedding is separately permissioned; it is not implicitly safe
  because it is CPU work.
- **Compiler:** exact CompilerGym dataset/library, LLVM, action inventory,
  scorer, resets, source inputs, and container hashes; scientific universe
  enumeration and execution are still unauthorized.
- **Training/GPU:** three writer-calibration rates plus duplicate, bounded
  canary fits, four-root pilot, then confirmation each require their named
  authority. The exact CUDA/driver/A40 mapping, parent placement, process
  teardown, peak memory, energy disposition, and offline-cache hashes remain
  open. Existing idle/busy GPU capacity is not permission.
- **Confirmation:** after the pilot, a new exact authorization must bind the
  immutable canary/pilot receipts, 32-root roster, current lease, and reserve.
  The plan states `N=32` needs replacement/extended compute through at least
  September 16 (`v1.md:751-760`).

## Minimum ICLR path, optimized for information per GPU-hour

The official source-bound calendar leaves 11 days to the September 18 abstract
and 18 days to the September 25 paper
(`ICLR_2027_SUBMISSION_CRITICAL_PATH_20260907.md:180-184`). The minimum path is:

1. **September 7--8:** complete v3 deliberation and exact ratification. In
   parallel, hand-write/conform the manuscript and related work, but keep all
   result language conditional. If source bytes are not frozen by September 9,
   drop the C4 promise for this cycle (`:186-197`).
2. **September 8--10:** implement only the five blockers in a new namespace;
   pass the CPU ladder and fresh reviews. Defer LEAFE-style work, PCFL/relay,
   rank sweeps, second environments, classroom/population ideas, and 1024-life
   scouts. They cannot rescue the primary.
3. **September 10--11:** after separate authorization, spend GPU first on the
   neutral writer calibration. Stop if no rate passes. Then run the active-text
   certificate and the staged two-root half of the teachability canary; spend
   the remaining six canary fits only if the first two technical roots pass.
   This ordering buys maximum localization before a full root.
4. **September 11--12:** run exactly four full excluded roots. This is the first
   end-to-end `R0/U0/U1/P0/P1` result. It is valid as a transparent descriptive
   spending pilot, not inferential evidence. If the v3 conjunction fails, stop
   confirmation and submit only the strongest honest lower-rung/writer result.
5. **September 12--16:** only after Gate 6 and a measured all-in p95/lease check,
   run all 32 prebound roots. A paper-level claim that parenting improved later
   learning requires the fixed sequence `D -> W_P -> L_terminal`; the public
   P1--R0 gain and terminal comparison are later rungs, never substitutes for a
   failed interaction (`v2_addendum.md:171-203,209-228`). Four pilot roots cannot
   support that sentence.
6. **By September 16:** freeze whatever rung actually passed. One immutable
   manifest must generate the curves, root-level uncertainty, failure table,
   writer mediator, and resource table. If no clean rung above C0 exists, write
   a rigorous negative/diagnostic paper rather than promise an unseen flywheel.

The information-efficient stop rule is therefore:

```text
CPU transaction/generator/reducer failures
  -> no representation or GPU work
writer calibration failure
  -> no parenting canary or root
parent-absent teachability/active-text failure
  -> no four-root pilot
v3 four-root conjunction failure
  -> no N=32 confirmation
N=32 fixed-sequence failure
  -> stop at the highest passing rung
```

## Threat-specific bottom line

- **Pseudoreplication:** solved in source, unimplemented. One Q root is one row;
  tasks, probes, cuts, calls, and fits are repeated measures
  (`v2_addendum.md:35-71`).
- **Target leakage:** current repository-reading/curriculum and free-text parent
  prototypes are unsafe. Only target-blind generated families, closed parent
  codes, deterministic laundering tests, and fresh-process deletion are valid.
- **Parent persistence:** no executable deletion audit exists. A good probe
  score cannot compensate for one surviving parent/nursery byte.
- **Compute mismatch:** P1--R0 intentionally has deployment-affordance parity,
  not total-history/compute parity. Parenting causality is only the P/U
  difference-in-differences (`v2_addendum.md:27-31`). Exact P/U slot, token,
  optimizer, and stochastic opportunity equality is not implemented.
- **Active-text weakness:** no implementation or certificate exists; therefore
  “strong” and “validated” are currently forbidden.
- **Writer dialect drift:** current trainer/compiler can still truncate, skip,
  deduplicate by surface prefix, and train off-dialect prose. V3's strict native
  targets, anchors, mount canary, and parser non-relaxation must be literal.
- **Parenting versus entry:** P1--R0 and high P entry are non-identifying. Only
  positive practical `D`, then `W_P`, then `L_terminal` licenses “parenting
  improved the ability to learn”; entry value must be printed, never adjusted
  away.

## Execution-readiness decision

**REVISE.** The next lawful operation is the already-configured five-role v3
deliberation after exact workflow approval. The next engineering operation is
scoped implementation only after exact consensus ratification. The first GPU
operation is the neutral writer canary only after the implementation, CPU,
representation, review, resource, and human pre-GPU gates pass. Any direct
promotion of `organism_v6`, any pilot before `ACTIVE_TEXT_FIXED` and
parent-absent teachability pass, or any P1--R0-only headline would be invalid.

This advisory's SHA-256 is reported out of band in the parent handoff because a
file cannot contain its own stable cryptographic digest.
