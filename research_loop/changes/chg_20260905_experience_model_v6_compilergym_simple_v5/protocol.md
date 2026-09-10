# Experience Model v6 — simple CompilerGym assay v5

Status: proposed architecture bytes. These bytes authorize no environment
opening, model call, training, GPU use, target evaluation, or scientific
claim. They intentionally test the smallest experience-to-LoRA mechanism;
they do not attempt to settle the final free-flow thinker, context-curation,
dreaming, or intelligent sleep design.

## 1. Scientific question and systems

Question: after an agent acts in a compiler gym, can a deterministic write of
its own successful public action--outcome experience into a life-local LoRA
improve its decisions on syntactically held-out programs beyond an otherwise
identical agent retaining the same kind of bounded external experience?

There are exactly two on-policy systems:

* `HARNESS`: pinned base model and a canonical null adapter for its whole life.
* `EXPERIENTIAL`: the same base, prompt, environment interface, task order,
  six-slot task budget, greedy decoding, and memory rule; after acquisition
  tasks 4 and 8 it rebuilds one cumulative life-local LoRA.

The final read-only `EXPERIENTIAL_OFF` fork is a mount diagnostic, not a third
on-policy system. It receives the exact EXPERIENTIAL memory snapshot and
prompt bytes but mounts the canonical null adapter.

The assay deliberately removes ORIENT/THINK_ACT phases, private thought,
free-form notes, learned recall, model-authored principles, waking briefs,
REVISE rows, counterfactual dreams, binding shuffle, intermediate target
opening, and context compaction. Fable's `organism_v6/` remains a separate
exploratory free-flow scout and none of its traces, programs, outcomes,
thresholds, prompts, or adapters may enter this assay.

## 2. One reconstructed decision context

No provider chat history, KV cache, prior raw output, hidden prefix, model-
owned file, or process-local model state crosses decision calls. Each slot is
a new two-message chat request constructed from authoritative public state.
The later ratified run manifest supplies exact UTF-8 `SYSTEM_TEXT`, pinned
chat-template bytes, tokenizer revision, and ordered legal pass catalog.

The user message is canonical UTF-8 JSON followed by one LF. Keys occur in the
order below, there is no insignificant whitespace, strings use JSON escaping,
integers are base-10, and arrays preserve declared order:

```json
{"schema":"v6simple.prompt.v1","task_key":"<64 lowercase hex>","life":{"tasks_completed":0,"sleep_index":0},"slot":1,"remaining_slots":6,"initial_count":0,"current_count":0,"best_count":0,"observation":[0],"history":[],"memory":[]}
```

Normative field rules:

* `task_key=SHA256(UTF8(canonical benchmark URI))`; the raw URI/path and role
  are never model-visible.
* `life.tasks_completed` is acquisition progress for acquisition calls and is
  frozen from the mounted snapshot for a target fork. `sleep_index` is 0, 1,
  or 2. No condition/adapter/checkpoint label, wall time, latency, row count,
  receipt, target role, or future task is visible.
* `slot` is 1--6 and `remaining_slots=7-slot`.
* counts are finite nonnegative integers returned by the sealed environment.
* `observation` is the complete fixed-order integer Autophase vector bound by
  the later environment manifest. Missing, reordered, truncated, or noninteger
  vectors make the cell indeterminate; no padding or repair is allowed.
* `history` contains all earlier slots of the current task, in slot order, as
  `{"slot":1,"pass_index":-1,"parse_valid":false,"accepted":false,"pre_count":0,"post_count":0,"best_count":0}`.
* `memory` contains at most eight improving acquisition records in increasing
  `event_seq`: `{"event_seq":0,"task_key":"<hash>","observation":[0],"pass_index":0,"pre_best":0,"post_count":0,"improvement":0}`.
  It is empty at birth. After each acquisition event that immediately lowers
  best-so-far instruction count by at least one, append the record; if nine
  exist, evict the smallest `event_seq`. Target events never enter memory.

Before any model call, the pinned tokenizer must show that `SYSTEM_TEXT`, the
chat template, the largest legal packet, generation allowance, and EOR fit the
manifest's context cap. Any overflow aborts; runtime truncation is forbidden.

The assistant response must parse as one JSON object with exactly one key,
`pass_index`, whose value is an integer in `[-1,L-1]`, where `L` is the legal
pass-catalog length. Surrounding ASCII whitespace is allowed; any other key,
text, type, range, duplicate key, non-UTF-8 byte, token overflow, or parse
failure becomes canonical no-op `-1`, consumes the slot, and is recorded as
`parse_valid=false`. There is no retry. `-1` is a valid deliberate no-op.
The canonical training target is exactly `{"pass_index":N}\n`.

## 3. Acquisition, environment, and score

The later ratified run manifest binds exactly eight acquisition URIs and four
target URIs, their source and bitcode SHA-256 hashes, one ordered legal pass
catalog, one official unchanged CompilerGym/LLVM stack, the observation name,
and `IrInstructionCountOz` costs. All twelve source hashes and all twelve
bitcode hashes must be pairwise distinct. This is syntactic holdout only; no
semantic-relatedness or population-generalization claim is permitted.

Manifest construction may enumerate public catalog identifiers and obtain
reset baselines before any model call, but may not use any learned/model
action, optimized trajectory, target score after a learned action, Fable
trace, or model output. Programs are ordered by ascending
`SHA256(master_split_seed || 0x00 || UTF8(canonical_URI))`; take the first
eight passing acquisition eligibility and the next four passing target
eligibility. Eligibility is: distinct required hashes, complete fixed-shape
Autophase observation, finite integer reset count `I0`, finite integer Oz
reference `IOz`, and `I0-IOz>=1`. No family clustering, near-neighbor model,
manual substitution, or outcome-based ranking is allowed. The manifest and
all eligibility rejections are sealed before model access.

Each task resets once, then runs exactly six decision slots. A valid
`pass_index>=0` requests that one catalog pass from the current state. An
accepted service result updates `current_count`; `best_count` is the minimum
finite count seen from reset through that slot. A no-op, malformed response,
valid worsening action, or service-rejected action leaves `best_count`
unchanged and still consumes the slot. Unknown/partial post-state, timeout,
process loss, noninteger/nonfinite count, reset mismatch, or catalog drift
makes that task cell indeterminate; it is never retried or replaced.

For task `i`, `d_i=I0_i-IOz_i` and final score
`F_i=(I0_i-best_count_after_slot_6)/d_i`. Scores may be below zero or above
one and are never clipped. Instruction-count improvement is an interface
metric, not proof of program functional correctness.

Both systems use the same acquisition order. Greedy decoding removes sampling
choice; at tasks 1--4 their model-visible bytes and effective weights must be
identical. HARNESS crosses sleep boundaries only by emitting a null receipt.

## 4. Deterministic sleep writer

SLEEP runs after EXPERIENTIAL acquisition tasks 4 and 8. It is a model-free
write recipe for this assay, not the final intelligent sleeper.

It reads only sealed EXPERIENTIAL acquisition events. An event is eligible iff
the response was parse-valid, `pass_index>=0`, the service accepted the pass,
the post-count is finite, and `post_count <= pre_best-1`. Its row input is the
exact canonical user-message bytes that produced the action. Its target is
the exact canonical `{"pass_index":N}\n` response. Define
`row_id=SHA256(input_bytes || 0x00 || target_bytes)`. Deduplicate by row ID,
retaining the earliest `(task_index,slot,event_seq)`, then sort rows by row ID.
Sleep 1 uses all eligible rows from tasks 1--4; sleep 2 uses all eligible rows
from tasks 1--8. Zero eligible rows aborts publication. No private prose,
failed action, negative, preference, rationale, principle, target, Fable row,
preservation row, KL loss, anchor, auxiliary example, or counterfactual is
allowed.

At each sleep rebuild from the clean pinned base with a fresh LoRA and fresh
optimizer. LoRA is rank 16, alpha 16, dropout 0, bias none, on every
`q_proj` and `v_proj` only. Each deduplicated row appears exactly 24 times.
Samples are ordered `(row_id ascending, copy_index 0..23)`, batch size one,
one optimizer update per sample, no shuffle, accumulation, packing, dynamic
batching, early stop, scheduler, retry, or skipped update. Maximum tokenized
sample length is 1,024; overflow aborts.

Loss is ordinary next-token cross-entropy only on assistant target JSON and
one tokenizer EOR; system text, chat-template control bytes, user message,
and padding have label `-100`. Optimizer is AdamW with learning rate `1e-4`,
`betas=(0.9,0.999)`, `eps=1e-8`, `weight_decay=0`, `amsgrad=false`, no
gradient accumulation, and global gradient norm clipped to 1.0 before every
step. The later run manifest pins library behavior, dtype, LoRA initialization,
unsigned 64-bit trainer seed, deterministic flags, model/tokenizer revisions,
and hardware.

Publication is atomic and requires exact row/copy/update counts, nonzero
positive-loss tokens, finite loss and gradient norm at every update, a
complete tensor manifest, and a final adapter hash. On failure no candidate
adapter is mounted. Optimizer, gradients, trainer, temporary corpus, model
process, KV/cache, and RNG state are destroyed after the receipt. Only the
published adapter and ordinary public life memory cross sleep.

Before targets, build the final adapter twice from clean processes on the
same pinned stack and seed. Concatenate every LoRA tensor after float32
conversion in ascending tensor-name order. Require global maximum absolute
difference `<=1e-6` and
`L2(A-B)/max(L2(A),L2(B),1e-12)<=1e-6`. Failure blocks targets.

## 5. Final held-out assay

After acquisition task 8 and the final determinism check, seal HARNESS and
EXPERIENTIAL memory snapshots. For each of four targets, launch cold read-only
forks with identical target state and budgets:

1. `HARNESS`: null adapter plus HARNESS snapshot.
2. `EXPERIENTIAL_ON`: final authentic adapter plus EXPERIENTIAL snapshot.
3. `EXPERIENTIAL_OFF`: null adapter plus the exact same EXPERIENTIAL snapshot.

Fork prompts expose no condition labels. Each fork uses a new process, no
history/cache from another fork, and may read only its mounted snapshot. It
cannot modify either life, adapter, manifest, later target, or split. Results
write only to a sealed quarantine read by the offline reporter after all
forks are destroyed.

Report raw six-slot curves, parse/service validity, per-program `F`,
`D_HE=mean_i(F_EXPERIENTIAL_ON,i-F_HARNESS,i)`, and
`D_ONOFF=mean_i(F_EXPERIENTIAL_ON,i-F_EXPERIENTIAL_OFF,i)`. Apply exactly the
first disposition:

1. `INTEGRITY_FAILURE`: any bound hash, visibility, lifecycle, determinism,
   budget, split, mount, snapshot, or quarantine invariant fails.
2. `INDETERMINATE`: integrity passes but any required target cell is
   indeterminate.
3. `RECIPE_COMPLETE`: all required cells and receipts complete, regardless of
   score direction or magnitude.

This one life yields no p-value, confidence interval, slope, efficacy,
mechanism, superiority, functional-correctness, lifelong, saturation,
population, or paper claim. It decides whether the minimal recipe is runnable
and whether replication is worth allocating. A later registered change must
add multiple paired lives, larger horizons, strong memory controls, model-
compiled sleep, context-state alternatives, and paper-level inference.

## 6. Staged authority and tests

Architecture ratification authorizes only an isolated `research_loop/v6simple/`
implementation, synthetic/mock fixtures, and a CPU-only no-model sealer over
unchanged already-local CompilerGym bytes. The sealer may enumerate the public
catalog, obtain reset/Autophase/Oz baseline data, apply the deterministic
eligibility/order rule, and generate the exact 8/4 environment manifest. It
may not execute a learned/model-selected pass or target trajectory. Model
calls, training, target assay calls, GPU use, download, install, patch, or
substrate substitution remain forbidden. The implementation must provide:

1. canonical JSON/parser/history/memory/score/disposition goldens;
2. writer selection/dedup/label-mask/update-count goldens;
3. two-system visibility, null-adapter, snapshot, no-writeback, atomic-failure,
   restart, and mock lifecycle tests;
4. a CPU-only manifest builder/sealer with no model or learned-action reader;
5. a run-manifest verifier that rejects every undeclared or changed byte.

Then a fresh independent reviewer and author-side advocate inspect the exact
implementation, tests, generated environment/model/hardware/run manifest,
and enumerated audited surfaces. Rohin separately ratifies those exact run
bytes once. That one later ratification may authorize unchanged CPU sealer,
32B GH200 acquisition canary, two deterministic rebuilds, and final target
assay without further prompts; any repair, substitution, tuning, retry,
different program/model/recipe, or claim expansion stops and requires a new
bound change.
