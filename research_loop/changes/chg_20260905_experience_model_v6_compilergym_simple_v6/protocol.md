# Experience Model v6 — minimal CompilerGym recipe assay v6

Status: proposed architecture bytes. No implementation, environment opening,
model call, training, GPU use, target action, or result claim is authorized by
this file. This revision closes the v5 consensus findings while preserving the
same small experiment; it adds no cognitive component or science arm.

## 1. Registered purpose and identities

This first life asks only whether the exact success-filtered action-cloning
recipe completes and what descriptive fixed-panel values it produces. It does
not ask whether LoRA generally improves agents.

There are exactly two on-policy systems:

* `HARNESS` (`H`): pinned base model; no adapter object or LoRA request exists.
* `EXPERIENTIAL` (`E`): identical base, system text, packet, environment,
  acquisition order, six-slot budgets, greedy decoder, and memory rule; after
  acquisition tasks 4 and 8 it rebuilds a life-local LoRA.

`E_OFF` is a final read-only mount diagnostic, not an on-policy system. It
uses the byte-identical final E snapshot with no adapter. `D_HE` is a
descriptive whole-system contrast because H and E histories may diverge after
sleep 1. `D_ONOFF` is an acute final adapter-mount contrast conditional on the
one realized E history. Neither is a causal effect or evidence of superiority.

The LoRA target contains actions, not outcomes. Numeric outcomes only decide
which immediately successful action examples are admitted. The assay does
not learn or test an outcome model, failure contrast, counterfactual, temporal
credit rule, private thought, final context policy, intelligent sleeper,
creativity, or lifelong improvement.

Fable's `organism_v6/` is a separate exploratory free-flow scout. None of its
programs, traces, outcomes, prompts, thresholds, adapters, probe results, or
failures may select, train, tune, or score this assay. Operational bugs may be
converted only into synthetic regression fixtures without copying its data.

## 2. Canonical encodings and bounded state

All canonical JSON in this protocol is UTF-8, ASCII-only in actual values,
with keys in the displayed order, separators exactly `,` and `:`, JSON string
escaping, lowercase `true`/`false`/`null`, no duplicate keys, no insignificant
whitespace, and exactly one trailing LF. SHA-256 is over these complete bytes.
Every integer is base-10 without leading zero and lies in signed 64-bit range;
instruction counts are additionally nonnegative. Array order is semantic.
An out-of-domain value is never truncated, padded, clamped, or repaired.

`event_seq` is a zero-based counter over every one of the 48 acquisition slots
inside one system life, including malformed, no-op, rejected, worsening, and
improving slots. H and E have separate counters. Target forks use local
`fork_event_seq=slot-1` and never advance a life counter.

The canonical life snapshot is:

```json
{"schema":"v6simple.snapshot.v2","system":"E","tasks_completed":0,"sleep_index":0,"next_event_seq":0,"memory":[]}
```

`system` is `H` or `E`, exists only in the controller/audit snapshot, and is
never rendered into a model message. At birth, task/sleep/event values are
zero. A successful task increments `tasks_completed`; successful E sleep
publication after tasks 4/8 sets `sleep_index` to 1/2; H records the same
boundary index in its snapshot but never creates/mounts adapter bytes.

Memory contains at most eight records in increasing event sequence:

```json
{"event_seq":0,"task_key":"<64 lowercase hex>","observation":[0],"pass_index":0,"pre_best":0,"post_count":0,"improvement":1}
```

Append only when that acquisition slot is parse-valid, applies a service-
accepted catalog pass, and `post_count<=pre_best-1`; `improvement` is exactly
`pre_best-post_count`. On a ninth record evict the smallest `event_seq`. The
snapshot hash covers all fields. Final `E_ON` and `E_OFF` mount the exact same
snapshot file and hash. Target events never modify a snapshot or memory.

The canonical within-task history record is:

```json
{"slot":1,"pass_index":-1,"parse_valid":false,"service_status":"MALFORMED","pre_count":0,"post_count":0,"best_count":0}
```

`service_status` is exactly `MALFORMED`, `NOOP`, `ACCEPTED`, or `REJECTED`.
A malformed response or deliberate `-1` performs no environment action;
post-count and post-observation equal their pre-slot values byte-for-byte. A
service-rejected pass must also return/prove the unchanged count and
observation; drift is an integrity failure. Every accepted action, including
a worsening one, supplies the next slot's current pre-action observation and
count. `best_count` is the minimum finite count from reset through that slot.

The complete canonical acquisition event is:

```json
{"schema":"v6simple.event.v2","system":"E","task_index":0,"task_key":"<hash>","slot":1,"event_seq":0,"packet_sha256":"<hash>","packet_b64":"<base64>","response_sha256":"<hash>","response_b64":"<base64>","output_token_ids":[0],"parse_valid":true,"pass_index":0,"service_status":"ACCEPTED","pre_observation":[0],"post_observation":[0],"pre_count":0,"post_count":0,"pre_best":0,"post_best":0}
```

Base64 is RFC 4648 with padding. Target receipts replace `system/task_index/
event_seq` with `fork_id/fork_event_seq`; their packet schema is otherwise the
same. Raw response bytes are operational JSON only, never private reasoning;
they are audit evidence and are never a training target or later prompt.

Bounds are: system text <=8,192 UTF-8 bytes; Autophase vector length `M` is
manifest-fixed in `[1,64]`; each element is signed 64-bit; history <=5;
memory <=8; output token IDs <=32; canonical user JSON <=32,768 bytes;
tokenized system+user+assistant-generation-prefix <=4,096 tokens; generation
<=32 tokens; full training sample <=4,096 tokens. The later manifest's model
context cap must be >=4,128. B1 proves the structural maxima and the later
tokenizer preflight checks every actual packet. Overflow is an integrity
failure; runtime truncation is forbidden.

## 3. One reconstructed model call per slot

No provider history, previous raw output, KV cache, hidden prefix, model-owned
file, wall time, latency, condition label, adapter label, receipt, future task,
or process-local model state crosses calls. Every slot is a cold logical chat
request with two messages:

1. system content is exact manifest-bound `SYSTEM_TEXT`, which contains the
   goal, the ordered legal pass catalog, the score semantics, and the sole
   required response grammar;
2. user content is the following canonical JSON and trailing LF:

```json
{"schema":"v6simple.prompt.v2","task_key":"<hash>","life":{"tasks_completed":0,"sleep_index":0},"slot":1,"remaining_slots":6,"initial_count":0,"current_count":0,"best_count":0,"observation":[0],"history":[],"memory":[]}
```

`task_key=SHA256(UTF8(canonical_URI))`; raw URI/path and acquisition/target
role are not model-visible. `remaining_slots=7-slot`. Acquisition life fields
come from the caller snapshot. Target fields are frozen from that mounted
snapshot. The observation is the current pre-action Autophase vector.

The assistant response must parse as one JSON object containing only integer
`pass_index` in `[-1,L-1]`, where L is the manifest catalog length. Surrounding
ASCII whitespace is allowed. Duplicate/extra keys, other text/types, invalid
UTF-8, range/token overflow, or parse error becomes canonical malformed no-op
`-1`, consumes the slot, and receives no retry. The canonical supervised
assistant content is exactly `{"pass_index":N}\n`.

Inference is batch size one, one request at a time, greedy (`temperature=0`,
no sampling), with exact model/tokenizer/chat-template/runtime/dtype/kernel/
driver/environment bytes and stop/EOR behavior bound by the later manifest.
Before acquisition, the first acquisition packet is generated twice from
separate cold processes without dispatch; output token IDs and response bytes
must match. During tasks 1--4, independent H and E requests, packets, effective
base weights, token IDs, parsed actions, environment outcomes, events, and
memory snapshots must match exactly. Any mismatch is an integrity failure.

No adapter object represents null. A null mount receipt is exactly
`{"kind":"NONE","base_sha256":"<hash>"}\n`; the loader must make no PEFT/
LoRA request and must reproduce the pinned base tensor manifest.

## 4. Environment manifest and six-slot score

The later run manifest binds exactly eight acquisition and four target URIs,
source/bitcode SHA-256 hashes, the ordered pass catalog, exact unchanged local
CompilerGym/LLVM bytes, Autophase schema, I0, and IrInstructionCountOz IOz.
This is syntactic holdout only.

`master_split_seed` is exactly 64 lowercase hex characters and decodes to 32
bytes. A catalog URI is accepted only if it is the exact unique UTF-8 string
returned by the official enumerator, already NFC-normalized, ASCII, and
matches `^benchmark://[A-Za-z0-9._-]+/[A-Za-z0-9._~/-]+$`; no normalization is
performed. Catalog duplicates, a SHA-256 collision between unequal bytes, an
unreadable source/bitcode, or unclassifiable service response stops sealing.
The ordering digest is:

```text
SHA256(seed_bytes || 0x00 || uint32_be(len(uri_bytes)) || uri_bytes)
```

Sort by `(digest bytes, URI bytes)`. In that order, eligibility rejection
precedence is: invalid URI; missing/unhashable source; missing/unhashable
bitcode; source hash already selected; bitcode hash already selected;
Autophase shape/type/range mismatch; reset drift; I0/IOz type/range failure;
`I0-IOz<1`. Each candidate is checked in two separate cold no-action processes;
canonical reset observation bytes, I0, and IOz must be identical. Select the
first eight eligible as acquisition and next four as target. Record every
candidate and its first rejection reason. There is no clustering, manual
substitution, learned pass, optimized trajectory, model output, or Fable input.
Two complete cold sealer invocations must produce byte-identical manifest and
rejection ledger before model access.

Each task resets once and executes six slots sequentially. A valid catalog
index requests one pass from current state. The service must classify it
accepted with complete post-state or rejected with proof of unchanged state.
After slot 6, for task i define `d_i=I0_i-IOz_i>=1` and
`F_i=(I0_i-best_count_i)/d_i`. Therefore every determinate `F_i>=0`; it may
exceed one and is not clipped. Instruction count is not functional correctness.

## 5. Deterministic success-filtered writer

After E acquisition tasks 4 and 8, select only events with `parse_valid=true`,
catalog `pass_index>=0`, `service_status=ACCEPTED`, finite in-range counts, and
`post_count<=pre_best-1`. Input is the exact decoded `packet_b64`, whose hash
must match `packet_sha256`; target is canonical `{"pass_index":N}\n`.
`row_id=SHA256(input_bytes || 0x00 || target_bytes)`. Deduplicate by row ID,
keep earliest `(task_index,slot,event_seq)`, and sort ascending row ID. Sleep 1
uses tasks 1--4; sleep 2 cumulatively uses tasks 1--8. No other row/loss exists.

For each row, construct token IDs only as follows using the manifest tokenizer
and chat template:

```text
prefix_ids = apply_chat_template([system(SYSTEM_TEXT), user(input_bytes)],
                                 tokenize=true, add_generation_prompt=true)
full_ids   = apply_chat_template([system(SYSTEM_TEXT), user(input_bytes),
                                  assistant(target_bytes)],
                                 tokenize=true, add_generation_prompt=false)
```

UTF-8 bytes decode strictly. `prefix_ids` must be an exact prefix of
`full_ids`; the suffix must equal the separately manifested canonical target
token IDs followed by exactly one manifested assistant EOR token and nothing
else. Labels are `-100` for prefix positions and equal token IDs for every
suffix position. Batch size one adds no padding. Any mismatch/overflow stops.

LoRA is rank 16, alpha 16, dropout 0, bias none, every q_proj/v_proj only.
Each row occurs 24 times in `(row_id,copy_index 0..23)` order. One sample is
one update; no shuffle, packing, accumulation, scheduler, dynamic batch,
early stop, retry, skipped step, preservation, KL, auxiliary, negative,
failure, principle, rationale, outcome target, or counterfactual is allowed.
Optimizer is AdamW: lr 1e-4, betas (0.9,0.999), eps 1e-8, weight decay 0,
amsgrad false; global gradient norm is clipped to 1.0 before each step. The
later manifest pins initialization, dtypes, seed, implementation, and flags.

Sleep 1 creates/publishes its only build. Sleep 2 build A is created from the
clean base, atomically published, and is the only authentic final mount
candidate. A separate clean build B is comparison-only and cannot be mounted.
Both require exact row/copy/update counts, nonzero supervised tokens, finite
loss/gradient/tensors, and complete tensor inventories. Tensor names, shapes,
and dtypes must match exactly; missing/extra tensors or nonfinite values fail.
For comparison, sort tensor names by UTF-8 bytes, convert tensors to CPU
float32 contiguous C-order, flatten, and accumulate max-absolute and squared-
L2 sums in float64. Require max absolute <=1e-6 and
`sqrt(sum((A-B)^2))/max(sqrt(sum(A^2)),sqrt(sum(B^2)),1e-12)<=1e-6`.
Bind build A's serialized adapter hash and tensor-manifest hash before targets.

Only a successfully published adapter and ordinary snapshot cross sleep.
Trainer, optimizer, gradients, build B, temporary samples, model process,
KV/cache, and RNG are destroyed. Atomic publication uses write+fsync of every
file, directory fsync, rename into a previously nonexistent final directory,
then parent-directory fsync. Partial candidates remain quarantined and cannot
be discovered by the loader.

## 6. Final held-out forks and quarantine

After task 8, final build comparison, and snapshot sealing, each target runs
once under H (H snapshot/no adapter), E_ON (E snapshot/build A), and E_OFF
(the same E snapshot/no adapter). Each fork is a fresh process, has six slots,
sees no condition label, and receives only its target-local environment,
model stack, assigned snapshot, and assigned mount receipt. No target process
receives a quarantine path or prior target result. It emits its canonical
receipt only on stdout to a non-model quarantine collector. The collector may
append/hash bytes but has no model, environment, life, compiler, trainer, or
future-fork writer. The offline reporter cannot start until all 12 fork
processes and model servers are destroyed and a completion barrier containing
their exit IDs and receipt hashes is sealed. A crash never resumes or retries.

Report raw six-slot curves, validity, F, `D_HE=mean(F_E_ON-F_H)`, and
`D_ONOFF=mean(F_E_ON-F_E_OFF)`. No target result enters a later model call.

## 7. Actor capability allowlist

Any unlisted read/create/write/delete is an integrity failure.

* `SEALER`: reads unchanged local public catalog/source/bitcode/reset/
  Autophase/Oz; creates only candidate, rejection, and final run manifests;
  has no model, adapter, life event, learned action, or target-action reader.
* `CONTROLLER`: reads run manifest, own snapshot, and current environment
  result; creates packets/events/commands; cannot read quarantine results.
* `MODEL_WORKER`: reads SYSTEM_TEXT, one packet, pinned base, and assigned
  adapter or NONE; writes response only to `PARSER`.
* `PARSER`: reads one response; writes one canonical parse disposition/action;
  cannot read environment outcomes or any future state.
* `ENV_SERVICE`: reads current target/acquisition URI and parsed action; writes
  current public observation/count/status only to `CONTROLLER`.
* `MEMORY_WRITER`: reads one committed acquisition event; writes only the
  caller's next snapshot. It has no target or adapter reader.
* `SLEEP_COMPILER`: reads committed E acquisition events/packets and frozen
  recipe; writes selected rows/manifests only to `TRAINER`.
* `TRAINER`: reads clean base, selected samples, and trainer manifest; creates
  candidate adapter/receipt only. It has no environment, target, H, or
  quarantine reader.
* `PUBLISHER_LOADER`: reads successful candidate and receipt; publishes or
  mounts only the declared adapter hash; cannot alter it.
* `TARGET_LAUNCHER`: reads sealed target manifest, snapshots, and mount hashes;
  starts cold forks; does not read their results.
* `QUARANTINE_COLLECTOR`: receives fork stdout, appends/hashes receipts, and
  seals the completion barrier; cannot call a model or write other artifacts.
* `AUDITOR_REPORTER`: activates only after the barrier; reads sealed artifacts
  and recomputes the disposition/report; cannot write any model-visible or
  life/training artifact.

T03 tests this allowlist with capability-denial fixtures. The later run
manifest enumerates the finite audited surface: exact repository files and
hashes, package lock, model/tokenizer cache revision/hash, loaded shared-
library inventory, environment-variable allowlist, driver/CUDA/GPU identity,
commands/argv/cwd, input/output paths, network state, service processes, and
every actor/artifact path. Reviews may say only that no forbidden access or
byte was found on these enumerated surfaces; they make no global negative
claim. A fresh independent reviewer receives only the review prompt and
declared immutable evidence, no author/session history, and has veto power.
The author-side advocate receives the same evidence but cannot override it.

## 8. Total failure and disposition table

There is no tuning, substitution, partial resume, or retry.

| Event | Action | Final disposition |
|---|---|---|
| Malformed response or deliberate no-op | Charge slot; unchanged state; continue | none |
| Service-rejected pass with proven unchanged state | Charge slot; continue | none |
| Hash/schema/bounds/visibility/capability/budget/mount/snapshot mismatch; changed state after no-op/rejection; H/E task-1--4 parity mismatch; rebuild tolerance/inventory mismatch; early quarantine read; reporter recomputation mismatch | Stop all work; never open remaining targets | `INTEGRITY_FAILURE` |
| Acquisition reset/service/process unknown state; clean atomic storage/process crash; zero eligible rows; finite-contract training failure before publication | Stop life cleanly; publish/mount nothing; never open targets | `INDETERMINATE` |
| Sleep-1 or build-A publication failure, or build-B comparison cannot complete while integrity remains intact | Stop life cleanly; never open targets | `INDETERMINATE` |
| One target reset/service/process/fork failure with intact isolation | Seal failed cell; continue only other independently cold cells | `INDETERMINATE` after barrier |
| Quarantine collector/barrier failure | Stop; do not release results | `INTEGRITY_FAILURE` |
| All contracts and all 12 cells complete | Release descriptive report after T06 | `RECIPE_COMPLETE`, regardless of signs |

Apply the first applicable final disposition. Acquisition/task completion and
sleep publication commits are atomic event transactions. A crash before a
commit leaves no committed event but terminates as above; the same run is not
resumed. Existing artifacts are preserved read-only for audit.

## 9. Gates and exact run meaning

Architecture ratification authorizes only isolated `research_loop/v6simple/`
implementation, synthetic/mock fixtures, and exactly two cold CPU-only no-
model sealer invocations over unchanged already-local CompilerGym bytes. It
does not authorize model calls, learned actions, training, target forks, GPU,
download, install, patch, or substrate substitution.

After B1/B2, a fresh independent reviewer and author advocate inspect exact
implementation/tests/receipts and one closed run manifest. Rohin's later one-
time ratification of that manifest authorizes one indivisible 32B GH200 run:
cold inference repeatability check; both eight-task acquisition lives; E
sleeps 1 and 2; final comparison build B; and the 12 final target cells. There
is no separate preliminary learned canary and no run output may change any
byte or choice. A crash/failure uses Section 8, not a rerun.

The later manifest must add `V6S_T06_ACTUAL_RUN_CONFORMANCE`: after execution,
a fresh independent reviewer recomputes from actual receipts every packet,
slot, H/E pre-sleep parity fact, memory/snapshot hash, selected row, mask,
update, tensor comparison, mount, process teardown, target cell, quarantine
barrier, F/D value, and first-applicable disposition. No result is released
before that review passes. Post-run review cannot repair or rerun the assay.

This one life has no p-value, confidence interval, slope, efficacy, mechanism,
functional-correctness, lifelong, saturation, population, or paper claim. A
new ratified replicated study is required for scientific inference.
