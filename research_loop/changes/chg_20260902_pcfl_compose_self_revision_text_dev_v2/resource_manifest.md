# v2 resource, runtime, and completion manifest

All values here and in `runtime_envelope.json` are hard proposal maxima, not
execution authority or spare capacity. `assignment_manifest.schema.json` and
`assignment_generator_contract.md` define the machine-readable per-call
records. Every raw request, including a malformed response or an eligible
diagnostic replay, is charged before parsing. A scientific row is never
replaced.

## Exact call-opportunity ledger

| invocation class | Stage 1 | conditional Stage 2 | scientific roster |
|---|---:|---:|---:|
| recurrent Dream | 128 | 352 | 480 |
| one-shot Dream | 0 | 4 | 4 |
| recurrent Think | 782 | 2,144 | 2,926 |
| structured one-shot Think | 0 | 4 | 4 |
| EXACT_PROGRAM model calls | 0 | 0 | 0 |
| **all model-call opportunities** | **910** | **2,504** | **3,414** |

Thus Stage 1 is exactly `128 Dream + 782 recurrent Think = 910`; Stage 2 is
exactly `356 Dream + 2,144 recurrent Think + 4 structured one-shot Think =
2,504`; and the sealed roster is exactly `484 Dream + 2,926 recurrent Think +
4 structured one-shot Think = 3,414`. The only additional process
opportunities are `replay-001` and `replay-002`, so the process ceiling is
3,416. Those slots diagnose only the eligible source call and never enter an
endpoint. There is no optional, result-triggered, failure, h=1-cut, opaque
one-shot Think, A-MEM, RAW_RAG, class, neutral, gate/no-gate, record-cut, or
other baseline call.

## Joint Stage-0 CPU and wall ledger

The former 24-hour aggregate is replaced everywhere in the repaired proposal
by the explicit **1,560 CPU-minute (26 CPU-hour)** cap. The ledger is joint:

| mandatory Stage-0 suite | count/bound | CPU-minute maximum |
|---|---|---:|
| factor + independent root certification | 128 roots x 10.5 | 1,344 |
| EXACT_PROGRAM solvers and public-actor applications | 28 solves + 60 applications | 16 |
| assignment generation, schema validation, cardinality, and replay negatives | complete 3,414+2 manifest | 15 |
| parser, JCS, Unicode, representation, and reducer boundaries | all static fixtures | 25 |
| tokenizer, chat-template, renderer, maximum-input, and context fixtures | every invocation mode | 40 |
| extractor S6/equivariance, reader, and rendered-q-null suites | complete declared finite domains | 30 |
| RNG vectors, coupling, gate truth table, q-policy table, sham, taint, reset, and actor firewall | all static fixtures | 55 |
| report projection/lint, access, storage, resource arithmetic, and receipt assembly | all static fixtures | 15 |
| **joint mandatory maximum** |  | **1,540** |
| **unallocatable containment margin** |  | **20** |
| **hard Stage-0 stop** |  | **1,560** |

Each suite has its own monotone CPU counter. Root certification additionally
has a 10.5-minute per-root stop. Model/tokenizer file hashing and reads count in
the relevant tokenizer/report suite. Worker parallelism changes no CPU charge.
The Stage-0 wall stop is 26 hours. A missing receipt, suite/root cap, joint cap,
or wall cap yields `NOT_RUN; HUMAN_REQUIRED` for the unopened model roster; no
root, fixture, or cell is dropped or replaced.

## Frozen runtime and prospective request policy

`runtime_envelope.json` fixes the model revision, deterministic source
resolution, required software/build values, bfloat16/no-quantization execution,
TP=1, engine flags, tokenizer/chat-template hashing, Unicode/JCS boundary,
sampler, stop token, timeout, seed mapping, context size, and no-truncation/
no-retry policy. Any field or resolved-byte change invalidates the executable
snapshot rather than choosing a new value. This proposal freezes the scientific
algorithms and semantics but does not claim that post-ratification
implementation, JCS implementation, installed source, binary, model snapshot,
or executable-receipt bytes already exist. After exact ratification and scoped
implementation, all such source/binary hashes must be added to a newly
JCS-hashed, independently reviewed pre-GPU executable snapshot that rebinds
every proposal input. Review or implementation may not change a scientific
choice; any such change requires a new material change and ratification.

| invocation class | input cap | prospective output cap | accepted-object rule |
|---|---:|---:|---|
| recurrent Dream | 16,384 | `min(2,048, phase remainder)` | after parse: node/read 512; PREDICT 2,048; terminal/PASS 256 |
| one-shot Dream-1 | 32,768 | 8,192 | atomic complete Dream-1 result |
| one-shot Dream-2 | 32,768 | 4,096 | atomic complete Dream-2 result |
| recurrent Think | 16,384 | 512 | D1: 10 opportunities and 5,120 cumulative raw tokens/twin; D4: 31 and 15,872/twin |
| structured one-shot Think | 32,768 | 15,872 | exactly four typed USE actions and terminal LOCK |

Dream-1 and Dream-2 phase output remainders start at 8,192 and 4,096 tokens.
Before every recurrent Dream generation the server requests the prospective
maximum above because operation kind is not yet known. It then subtracts the
actual raw generated count, including malformed bytes, and enforces the parsed
operation cap. Negative remainder, cap+1 input/output/JCS/state/read/action, or
truncation is a retained failure. Recurrent Think D1 starts at 5,120 and D4 at
15,872 raw-output tokens; structured one-shot D4 starts at 15,872. An invoked
recurrent Think row requests `min(512, before)` and structured one-shot requests
`min(15,872, before)`. Atomic one-shot modes otherwise use their whole declared
cap.

For every scientific call row, phase remainder before/after is a required JSON
integer, never null. The first row has `before` equal to the phase cap. In
ascending zero-based `resolver_ordinal`, the next row's `before` equals the
previous row's `after`, and model-visible `operation_ordinal` is exactly
`resolver_ordinal + 1`. For an invoked row, charge raw generated tokens before
parsing and require `after = before - raw_output_tokens`; malformed, illegal,
timeout, and other response-bearing failures get the same debit. For any
unopened, NOT_TRIGGERED, NOT_RUN, post-terminal, or otherwise NOT_INVOKED row,
raw output is zero and `after = before`. Thus null accepted-output status cannot
erase the counter. Initial remainder minus final remainder equals the exact sum
of phase raw output, bounding D1 at 5,120 and both recurrent and structured D4
at 15,872. Replays charge only process totals and never mutate the scientific
source phase counter.

Each call receipt carries raw input tokens, raw output tokens, accepted output
tokens or null, input/output JCS bytes, operation count, read/action counts,
live-tuple bytes, phase remainder before/after, sampler/runtime IDs, process
status, parse/reducer status, scientific endpoint value or null, terminal
reason, wall/device time, artifact bytes, and replay source/slot if any. These
fields are orthogonal; a legal wrong action is a returned, accepted process
with endpoint zero, never an infrastructure failure.

## Literal token, live-state, storage, and competing-stop arithmetic

```text
scientific output = 147,456 Dream + 1,498,112 recurrent Think
                  + 63,488 structured one-shot Think = 1,709,056
two maximum replays = 2 x 15,872 = 31,744
calculated process-roster output maximum = 1,740,800
watchdog output hard stop = 1,750,000
unallocatable output containment margin = 9,200

scientific input = 3,406 recurrent x 16,384
                 + 8 one-shot x 32,768 = 56,066,048
two maximum replay inputs = 65,536
process input maximum = 56,131,584
calculated process-roster combined maximum = 57,872,384
watchdog combined-token hard stop = 58,000,000
unallocatable combined-token containment margin = 127,616
```

The calculated maxima are exact sealed-roster capacity. The larger watchdog
values are independent emergency stops, and the two differences above are
containment only: they cannot add a call, replay, retry, token, or cell. The
forecast must fit the exact calculated maxima strictly below the watchdogs.
Maximum JCS live tuples remain Dream-1
24,576 bytes, Dream-2 32,768, and Think 16,384. Complete rendered-byte maxima
remain 49,152; 65,536; 49,152; 65,536; 81,920; and 49,152 respectively for
recurrent Dream-1, recurrent Dream-2, recurrent Think, one-shot Dream-1,
one-shot Dream-2, and structured one-shot Think. Schema-generated maximum
objects plus the pinned tokenizer/chat template must fit with truncation off;
the structured mode requires 32,768 + 15,872 = 48,640 tokens within the fixed
65,536-token context.

Scientific-stage competing hard stops are 18 occupied device-hours, 24 wall
hours, one device at a time, and 50 GiB append-only storage. Before the first
model call a full-roster forecast must fit every stop with declared margin or
the entire unopened roster is `NOT_RUN`. Once started, reaching a stop retains
all assigned rows and marks uninvoked ones `NOT_RUN`; it never authorizes
downsampling, truncation, environment changes, or a new cell.
