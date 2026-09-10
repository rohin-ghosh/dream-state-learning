# Experience Model v6 — common-prefix CompilerGym pilot v7

Status: proposed architecture bytes. This is the controlled, bottom-up branch
beside Fable's exploratory `organism_v6` run. It is intentionally a small
component assay, not the final experience-model architecture or a paper result.

## 1. Question and experimental object

The pilot asks:

> Starting from one identical lived prefix, does a fixed, verified
> experience-to-LoRA recipe alter later pass-selection behavior, and what does
> that teach us about the minimum useful contents of sleep?

One agent lives through acquisition tasks 1--4 with the pinned base model and
no adapter. Its committed public state is cloned at that boundary. Two agent
lives then continue over the same ordered acquisition tasks 5--8:

* `H` (HARNESS): the clone continues with the base model and no adapter.
* `E` (EXPERIENTIAL): before task 5, the clone receives a LoRA compiled from
  verified immediate improvements in the common prefix; after task 8, it is
  rebuilt cumulatively from common-prefix plus E-life improvements.

`E_OFF` is not a third life. It is a final diagnostic that evaluates the final
E public state with the adapter absent. The final panel is therefore H, E_ON,
and E_OFF on four held-out programs.

This is a lower-bracket writer test. It does not contain or test private
reasoning, a learned thinker, dreamer, sleeper, verifier, context-curation
policy, outcome model, failure learning, creativity, lifelong improvement, or
general LoRA efficacy. A positive or negative result only guides the next
sleep design. Fable data are not inputs to this pilot.

## 2. Public state and one action interface

Every model call is reconstructed from public state; no provider conversation,
KV cache, raw prior response, private thought, wall clock, condition label,
receipt, target role, or future task crosses calls.

The manifest-bound system message contains: the goal (minimize LLVM IR
instruction count), the ordered legal pass catalog, score semantics, and the
sole response grammar. The user message is canonical JSON with these fields:

```json
{"schema":"v6s7.prompt.v1","task_key":"<sha256>","life":{"tasks_completed":4},"slot":1,"remaining_slots":6,"initial_count":100,"current_count":100,"best_count":100,"observation":[0],"history":[],"memory":[]}
```

Canonical JSON is UTF-8 with ASCII values, keys in displayed order, compact
separators, no duplicate keys or insignificant whitespace, and one trailing
LF. Integers are signed 64-bit; instruction counts are nonnegative. Arrays are
ordered. The manifest binds the Autophase vector length in `[1,64]`, legal-pass
catalog length, tokenizer/chat template, and exact system bytes. User messages
are at most 24 KiB and the complete inference prefix at most 2,048 tokens.
There is no runtime truncation or repair.

The assistant may return only `{"pass_index":N}` with surrounding ASCII
whitespace, where `N=-1` is a deliberate no-op and `0<=N<L` selects one pass.
Malformed, extra-key, wrong-type, out-of-range, or over-16-token output becomes
the canonical no-op and consumes the slot without retry. Each task has exactly
six charged slots.

After an accepted pass, the next packet receives the service's new Autophase
observation and instruction count. A rejected action is allowed only if the
service proves state unchanged. History contains the current task's earlier
slots and never exceeds five records. `best_count` is the minimum count from
reset through the current slot.

The append-only audit event binds the exact input bytes/hash, output token
IDs/bytes/hash, parsed action, pre/post observations and counts, acceptance
status, and pre/post best. Audit encodings and receipt schemas do not enter any
model or training input; their exact implementation bytes are frozen and
reviewed at T04 rather than expanded into cognitive architecture.
Every output token ID must lie in the pinned tokenizer vocabulary. Each slot
commits its event and resulting public state atomically; after slot 6, task
completion is committed atomically. The common prefix is forked only from the
sealed task-4 completion. A crash before either commit ends the run without
resume, so no ambiguous partial state is consumed.

The model-visible memory is the last eight acquisition events, in event order,
that were valid, service-accepted, and immediately improved the previous best.
Each record contains the pre-action observation, chosen pass index, pre-best,
post-count, improvement, and task key. A ninth record evicts the oldest. It is
identical for both clones at the fork and then evolves independently. Target
events never update it.

The shared prefix is executed once, not reproduced twice. The H and E fork
snapshots are exact byte copies of the same condition-free public snapshot;
condition identity and sleep count live only in the offline run ledger and are
never prompt fields. Thus the first post-fork H and E packets differ in no
model-visible byte: only the E mount differs. This makes pre-sleep parity true
by construction instead of depending on cross-process numerical repeatability.

Inference is batch size one and greedy. The later manifest pins model,
tokenizer, revision, runtime, dtype, generation and stop settings, seed, driver,
and GPU. The protocol claims manifest-pinned execution, not bitwise GPU
determinism.

## 3. Environment and score

Use unchanged, already-local CompilerGym/LLVM. A no-model sealer enumerates the
official catalog and sorts exact unique URI bytes by
`SHA256(seed_bytes || 0x00 || uri_bytes)`. For each URI, two cold resets must
agree exactly on bitcode hash, Autophase bytes, initial instruction count `I0`,
and `IrInstructionCountOz` count `IOz`. A candidate is eligible only when the
URI is unique, its bitcode hash has not been selected, all repeated reset values
agree and fit the Section-2 domains, and `I0-IOz>=1`. The first eight eligible
programs are acquisition and the next four are held-out targets. A second cold
sealer invocation over unchanged bytes must produce the same ordered manifest.

This establishes a syntactic, hash-distinct fixed panel only. It does not
establish semantic independence or functional correctness.

For task `i`, with `d_i=I0_i-IOz_i`, report
`F_i=(I0_i-best_count_i)/d_i`. `F_i>=0`, may exceed one, and is not clipped.
Also retain the full six-slot count/action curve and parse/acceptance validity.
F is stored canonically as a reduced integer pair `{num,den}` with positive
denominator; reduction divides by the positive gcd and represents zero as
`0/1`. All means and differences are computed by exact rational arithmetic and
released as reduced pairs, so no floating reduction or rounding rule is part of
the registered result.

## 4. Minimal sleep write

Sleep 1 uses eligible immediate-improvement events from the common prefix.
Sleep 2 uses the union of those events and eligible E events from tasks 5--8.
H events after the fork never enter E training.

For every eligible event:

1. decode and hash-check the exact packet used to choose the action;
2. set assistant content to canonical `{"pass_index":N}\n`;
3. deduplicate equal `(packet bytes, assistant bytes)`, keeping the earliest
   event, then sort rows by their SHA-256;
4. create `prefix_ids` with the pinned chat template over system+user and
   `add_generation_prompt=true`;
5. create `full_ids` with system+user+assistant and
   `add_generation_prompt=false`;
6. require `prefix_ids` to be an exact prefix of `full_ids`, supervise every
   token in the resulting assistant suffix, and mask every prefix token with
   `-100`. The actual suffix token sequence is manifest evidence; the protocol
   does not assume one particular EOR encoding.

No outcome number, rationale, thought, principle, counterfactual, failed
action, Fable artifact, target datum, or manually authored example is a target.

Each sleep rebuilds from the clean pinned base, not from the previous LoRA.
LoRA is rank 16, alpha 16, dropout 0, bias none, on every `q_proj` and `v_proj`.
Each unique row occurs 16 times in `(row_hash, copy_index)` order. Batch size is
one; one sample is one update; there is no shuffle, packing, accumulation,
scheduler, early stopping, or auxiliary loss. AdamW uses lr `1e-4`, betas
`(0.9,0.999)`, eps `1e-8`, weight decay 0, with global gradient norm clipped to
1.0. The run manifest pins implementation, initialization, dtype, seed, and
gradient-checkpointing flags. Maximum full sample length is 2,048 tokens.

Zero eligible rows, nonfinite loss/gradient/tensor, sample overflow, failed
publication, or mount mismatch stops E as `RUN_INCOMPLETE`; no old/null adapter
is substituted. A successful build is atomically published and its serialized
hash plus tensor inventory are sealed before use. No duplicate reproducibility
build is required in this exploratory pilot.

## 5. Final panel and registered outputs

After acquisition task 8 and E sleep 2, seal the H snapshot, E snapshot, and E
adapter. Each of the four held-out targets runs once in a cold logical context
under:

* H snapshot + no adapter;
* E snapshot + final E adapter (`E_ON`);
* the exact same E snapshot + no adapter (`E_OFF`).

Each cell resets once and runs six slots. Target results are offline-only: no
target outcome, action, receipt, or aggregate enters any later model request,
life state, memory, or training row. The implementation may use separate
condition processes rather than an OS-level actor sandbox; T04 must show from
code and packet receipts that only the declared public packet crosses the model
boundary. This pilot makes no global noninterference claim.

If all twelve cells complete, report raw curves and per-cell F, plus paired
descriptive means:

```text
D_HE    = mean_target(F_E_ON - F_H)
D_ONOFF = mean_target(F_E_ON - F_E_OFF)
```

If any cell is missing, report `PANEL_INCOMPLETE`, the missing-cell map, and
raw completed cells only; both D values are unavailable. No complete-case or
condition-specific denominator is permitted.

Registered statuses are:

* `PILOT_COMPLETE`: all contracts and all cells complete, regardless of score
  signs;
* `RUN_INCOMPLETE`: an ordinary reset/model/training/process/cell failure with
  intact evidence before the target panel;
* `PANEL_INCOMPLETE`: at least one target cell failed with intact isolation;
* `INTEGRITY_FAILURE`: a schema/hash/state/mount/budget/visibility/target-
  feedback or audit mismatch.

Malformed outputs and proven unchanged service rejections consume slots and do
not change status. The first other failure stops the affected run; there is no
within-manifest repair, substitution, retry, or resume. Integrity failures
suppress all scientific values. A target-cell failure is the sole exception to
the stop rule: seal it missing and continue the remaining cold cells, then use
PANEL_INCOMPLETE. Raw results remain quarantined until T05.

This single pilot has no p-value, interval, population, efficacy, superiority,
mechanism, saturation, lifelong, or paper claim. Its scientific product is a
design update: whether direct verified action cloning is sufficient to affect
prospective decisions, harmful, or too weak, and therefore what richer sleep
content the next assay should test.

## 6. Gates and authority

The acceptance chain is:

* `V6S7_T01_STATE_ACTION_GOLDENS`: CPU fixtures independently reconstruct
  canonical packets, parsing, all six slot transitions, memory eviction, fork
  cloning, scores, and failures.
* `V6S7_T02_SLEEP_SAMPLE_GOLDENS`: CPU fixtures independently reconstruct row
  eligibility/dedup/order, exact chat tokens and masks for the later pinned
  tokenizer, update counts, adapter target inventory, and atomic publication
  failures. A toy tensor test exercises optimizer order without the base model.
* `V6S7_T03_DOUBLE_SEAL`: exactly two CPU/no-model sealer invocations produce
  byte-identical 8/4 manifests from unchanged local bytes.
* `V6S7_T04_PRE_GPU_REVIEW`: a fresh independent reviewer and non-overriding
  advocate inspect the exact implementation, T01--T03 evidence, run manifest,
  packet-only visibility path, commands, and a quantitative 7B GH200 memory/
  storage/wall-time budget.
* `V6S7_T05_POSTRUN_AUDIT`: after the run, a fresh independent reviewer
  recomputes every packet/action/state/memory/row/update/mount/cell/score/status
  from immutable receipts. No status or numeric result is released first.

For the architecture registry's `required_before` vocabulary, releasing any
run status, raw cell, aggregate, or scientific interpretation counts as a
`scientific_claim`; therefore T05 gates every result, not merely a headline.

Ratification of these architecture bytes authorizes only isolated
`research_loop/v6simple/` implementation, synthetic CPU tests, and the two
no-model sealers over already-local bytes. It does not authorize a model call,
training, target access, or GPU use.

After T01--T04, one exact manifest is presented once for Rohin's required run
ratification. That manifest authorizes one 7B GH200 execution. Its first phase
is a synthetic maximum-length load/forward/backward/mount engineering canary
with no CompilerGym action. If the canary passes, the same frozen command
continues into the common prefix, H/E fork, two E sleeps, and twelve final
cells. Failure stops under Section 5; the manifest is not silently repaired or
rerun.
