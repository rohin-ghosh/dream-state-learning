# Teacher-present process/sham scout — SEQ-077

September12,2026,12:08UTC. Original primary contrast is null: both conditions
solve1/16first actions. This is no-write, teacher-present behavior on existing
training questions, not P1 internalization, H1/H2, or held-out generalization.

| Endpoint | Process | Sham |
|---|---:|---:|
| First-ACT solves | 1/16 | 1/16 |
| First-ACT available | 16/16 | 16/16 |
| Complete4×4digit-grid format | 7/16 | 4/16 |
| Primary zero-filled first-score mean | .192578125 | .11875 |
| Raw native first-score mean, before format-invalid zeroing | .216548295 | .159659091 |
| Actual retokenized output tokens | 1079 | 1068 |
| Outputs at400retokenized-token cap | 0/16 | 0/16 |

The relative secondary format difference is+3/16 and the zero-filled partial
score contrast+.073828125. Neither establishes useful teaching: no no-teacher
anchor was included, so differential sham harm remains possible. Do not call
this a positive primary result or retrofit a success threshold. No sample is
rescued by later actions: all32episodes contain exactly one ACT.

Both complete packages are97Qwen tokens;16presentations each,1552cumulative
teacher tokens and6400reserved output tokens per arm. Realized output tokens
differ and are reported, not post-hoc matched. Low output lengths do not
support a400-token-cap bottleneck; retokenized lengths are not finish reasons.

## Execution and evidence

Node3GPU3controller87251, sourceb39e92381a848b19f8a9578aca79fee20de24894,
root `astra_P1_static_competency_20260912_attempt1`, process then sham.
Started11:56:28.939021UTC; completed12:02:55.307608UTC, approximately6.4A40
minutes reserved. Worker87252(process) and88374(sham) cleanup receipts verify
owned groups and GPU release; controller absence rechecked12:05:34.473263UTC.
Main releases GPU3 reservation. No manual kill; normal backend escalation and
semaphore warnings remain in logs. Source/base artifacts are unchanged within
the producer's recorded checks; official model origin remains unresolved.

The independent offline reduction validates both sealed artifact inventories,
the complete prepared prompts, seeds/budgets, package presentations, raw output
hashes, marker-parsed ACT order and first-action ledger/reducer agreement.
Native verifier rescoring and a finer given/row/column/box failure audit are
pending independent review; no assertion of that review's completion is made.

Evidence under `receipts_20260912/`:
- `astra_static_competency_terminal_20260912.tgz`, SHA256
  `339620c7ad406d3d155b6007a8bf82c4415c7e3bcf3702159285143ab6efbaeb`.
- `astra_static_competency_terminal_analysis_20260912.json`, `valid=true`, SHA256
  `7839ff6516644b319fee4aec0cf5adcfbcd293706a85b9e629e45956748b3a65`.
- `astra_static_competency_analyze_20260912.py`, exact reduction script.
- `astra_static_competency_terminal_observation_20260912.json`, terminal/cleanup
  observation. Preparation capsule remains separate, SHA256
  `84d0f6623c6fdd532efac4b029308b76690f3bde8dd98bc1f9acc0df85c7b177`.

## Decision

Accept the12:00watcher recommendation's causal limitation, without treating
its recommendation as an authorization gate. Add only an explicitly post-hoc,
descriptive no-teacher anchor on the same16questions/seeds/settings before
calling either package helpful. Its input is shorter and not token matched;
the original process/sham result remains fixed. Inspect visible constraint
failures before choosing any new prompt/material or replication. No new
weight fit from these traces is selected. A separate semantic-action carrier
CPU sidecar now addresses the old W0 action-alphabet issue while the existing
memory-preservation pair finishes; no launch or memory result is implied.
