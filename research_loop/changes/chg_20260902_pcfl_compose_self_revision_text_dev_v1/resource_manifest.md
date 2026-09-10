# Resource, assignment, and artifact manifest

**Status:** proposed ceiling, not spending or run authority. All counts are
failure-inclusive maxima for the sealed assignment roster; no condition may be
silently downsampled to remain under a cap.

## CPU Stage 0

- Certify 64 factorized and 64 matched-independent roots.
- For every root, enumerate all 32 private `(h,z)` or `(q,z)` states, both goal
  twins, all 16 D4 sequences, every prefix, both A continuations, disjoint B,
  target/firewall invariants, and the registered rejection surface.
- Hard cap: 30 CPU-minutes/root, 24 aggregate CPU-hours, and 64 worker
  processes. Stop rather than reduce the roster.
- No network, model, GPU, package install, lease, credential, or external write.

## Exact Dream assignment envelope

One ordinary recurrent life costs 32 Dream-1 plus 16 Dream-2 calls = 48. One
public-prefix fork reuses Dream-1 and runs both Dream-2 continuations, costing
32 + 2*16 = 64 calls per z side. Every root uses z and its antipode.

| Stage/root | recurrent lane | z sides | h/q sides after shared D1 | calls |
|---|---:|---:|---:|---:|
| S1A open factor | OPAQUE_NOTE_SELF | 2 | 2 | 128 |
| S1A open factor | OPERATOR_AST_SELF | 2 | 1 | 96 |
| S1A open factor | CLASS_INFORMED_TEXT | 2 | 1 | 96 |
| S1B untouched factor | OPAQUE_NOTE_SELF | 2 | 2 | 128 |
| S1B untouched factor | NEUTRAL_OPAQUE | 2 | 1 | 96 |
| S1B independent | OPAQUE_NOTE_SELF | 2 | 2 | 128 |
| S1B independent | NEUTRAL_OPAQUE | 2 | 1 | 96 |
| S1B independent | OPERATOR_AST_SELF | 2 | 1 | 96 |
| S1B independent | CLASS_INFORMED_TEXT | 2 | 1 | 96 |
| **recurrent subtotal** |  |  |  | **960** |

Opaque one-shot Dream runs on the untouched factor and independent ordinary
z+antipode sides: four Dream-1 plus four Dream-2 calls, total 8. The sealed
Dream maximum is **968 calls**. The continuation fork is mandatory only for
OPAQUE_NOTE_SELF; diagnostics do not inherit an unregistered fork.

Recurrent generated-token entitlement totals 245,760; one-shot entitlement
adds 49,152; Dream output maximum is **294,912**. Per-call output caps are
operation-specific: Dream READ 64, ordinary cognitive/terminal 256, and Dream
PREDICT 2,048, subject also to phase cumulative caps (8,192 Dream-1; 4,096
Dream-2). One-shot phases receive those same cumulative output entitlements,
not matched calls, repeated inputs, latency, or FLOPs.

## Exact target/Think assignment envelope

One recurrent condition-life evaluates two D1 goal twins (10 calls each) and
two D4 goal twins (31 calls each), at most 82 calls. An ordinary z+antipode
condition costs 164 calls; a primary h/q fork costs 328.

| Stage/root | registered target conditions | recurrent calls |
|---|---|---:|
| S1A open factor | primary fork | 328 |
| S1A open factor | PERFECT, NO_GATE_ALL, NO_GATE_HASH1, NO_REVISION, EMPTY, OBSERVED, RAW_RAG_EQUAL, RAW_RAG_FULL, EXACT, ORACLE, CLASS_INFORMED, ORIENTATION_DELETED, OPERATOR_AST | 2,132 |
| S1A open factor | four opaque whole-corpus cuts on ordinary sides | 656 |
| S1A open factor | three OPERATOR_AST structural cuts on ordinary sides | 492 |
| S1B untouched factor | primary fork plus PERFECT, EMPTY, OBSERVED, RAW_RAG_EQUAL, RAW_RAG_FULL, EXACT, ORACLE, NEUTRAL, ONE_SHOT_DREAM | 1,804 |
| S1B independent | primary fork plus EMPTY, OBSERVED, RAW_RAG_EQUAL, RAW_RAG_FULL, EXACT_ABSTAIN, NEUTRAL, OPERATOR_AST, CLASS_MISSPECIFIED, ONE_SHOT_DREAM | 1,804 |
| **recurrent Think subtotal** |  | **7,216** |

The paired one-shot Think control runs on ORACLE and OPERATOR_AST open-factor
cells and OPERATOR_AST independent cells: 24 calls total. Its output
entitlement matches the corresponding whole iterative trajectory, reserving
251,904 tokens. A faithful native A-MEM arm, if preflight-admitted, receives
at most 512 calls and 262,144 output tokens across its registered untouched and
independent frontiers; otherwise all its rows are `NOT_RUN`.

## Hard text-only DEV caps and time estimate

- Only `Qwen/Qwen2.5-32B-Instruct` revision
  `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`.
- Inference only: no optimizer, gradients, weight mutation, adapter, LoRA,
  SFT, RL, persistent KV cache, or new model/provider family.
- Maximum roster: 968 Dream + 7,216 recurrent Think + 24 one-shot Think + 512
  conditional A-MEM = **8,720 calls**. Stop at **9,000 total calls** or
  **1,000 Dream calls**.
- Hard output cap: **5,000,000 tokens**. Hard combined input-plus-output cap:
  **82,000,000 tokens**. Each recurrent call also has an 8,192-input-token cap;
  each one-shot call has 20,480. Truncation is forbidden.
- At most one simultaneously occupied H100 NVL or GH200; **30 device-hours**
  and **36 wall-hours** after the signed pre-GPU gate; 50 GiB artifacts.
- Retained local anchors predict 8.9 h for 960 recurrent Dream calls and 8.3 h
  for 7,216 Think calls. One-shot, optional native work, loading, and 25%
  overhead yield about 22--27 device-hours. This is a scheduling estimate; the
  hard cap wins.
- One exact-byte infrastructure replay per failed invocation in a fresh
  process may diagnose infrastructure. The first failure remains the scientific
  row and denominator; replay never replaces it. No semantic retry, seed
  change, larger context, parser repair, fallback model, or dropped assignment.
- Two occurrences of one infrastructure signature stop the stage and return
  `HUMAN_REQUIRED`. Atomic marker files bound to the run lock are authoritative;
  process-name or zombie watchers are not.

## Required artifacts

Retain immutable hashes and exact bytes for:

- code, intake, ratification, reviewer/advocate verdicts, pre-GPU gate,
  environment/model/tokenizer manifests, assignment roster, and seeds;
- every private root/orbit/continuation/null certificate and public projection,
  separated by access root;
- every rendered prompt, response, parse, failure, diagnostic replay, Dream
  commitment, raw A/B event, NOTE or AST object, decision, branch corpus,
  index, query/postings, reader result, workspace, action, target, and score;
- every continuation equality/difference receipt and exact branchwise B/action
  endpoint;
- all calls, tokens, bytes, latency, occupancy, peak memory, and stop markers;
- A-MEM availability/license/revision/native-interface receipt or root-wide
  `NOT_RUN`; and
- a failure-inclusive terminal row for every presealed assignment.

All files are append-only or content-addressed. No result analyzer can dispatch
a later scientific stage. Final state is `STOPPED`, `NOT_RUN`, `FAILED`, or
`HUMAN_REQUIRED_FOR_ANY_NEXT_STAGE`.
