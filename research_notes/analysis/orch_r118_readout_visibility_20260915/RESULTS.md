# Route open turns and generated-text visibility

Read-only native audit on September 15, 2026, approximately 14:00 UTC.
This answers the watcher's 11:36 UTC observation; it is not a new run or
evidence of retained thinking. No sealed FINAL files were read.

## Open turns were present, under different filenames

Both route branches record training open turns as
`cycle_NNNN/OPEN_TRAIN_0.json` and `OPEN_TRAIN_1.json`, not `open_turn*`.
Parent-free post-sleep open turns are in
`open_readouts/readout_NNNN/OPEN.json`. A filename search for `open_turn*`
therefore misses these artifacts.

| Branch | TRAIN open artifacts | Environment calls | Parent-free open artifacts | Environment calls |
| --- | ---: | ---: | ---: | ---: |
| F1 | 14 | 6 | 6 | 4 |
| A1 | 8 | 2 | 3 | 0 |

All 12 recorded environment-call responses match their saved hashes, using
the producer's canonical-JSON digest. These receipts include the actual action,
environment response, and `actual_environment_call=true`. They distinguish
executed interaction from proposed interaction. They do not establish that
every open turn executes a tool: the child can stop or fail to issue an action.

The first F1 TRAIN artifact has modification time 10:57:05 UTC and the first
A1 TRAIN artifact 11:11:15 UTC; first parent-free artifacts are 11:05:24 and
11:23:48 UTC respectively. These files predate the 11:36 observation. Times
are filesystem metadata, not independently authenticated creation timestamps.
The open-turn implementation is present in the original route module, not
only in the shared successor launched at 12:25:26 UTC.
Sleep 0 did not include an open turn; do not backfill that baseline claim.

## Text capture is complete; most outputs are terse

Readout `CALL_*.json` stores the complete decoded output in `response.raw`
and generated IDs in `response.token_ids`. `HELD.json.cached_responses`
retains the same response objects. All 11 audited DEV readouts have these
fields, and all 173 cached responses match completed native CALL responses.
The parser uses the final command line for environment execution without
discarding preceding text from the saved response.

| Branch/sleep | Responses | Command-only responses | Median tokens/response | Median tokens/task |
| --- | ---: | ---: | ---: | ---: |
| F1/0 | 16 | 16 | 12 | 23.5 |
| F1/1 | 12 | 8 | 13 | 50.5 |
| F1/2 | 18 | 8 | 74.5 | 122.5 |
| F1/3 | 16 | 16 | 10.5 | 21 |
| F1/4 | 16 | 16 | 11 | 22 |
| F1/5 | 16 | 16 | 11 | 22 |
| F1/6 | 16 | 16 | 12 | 24 |
| A1/0 | 16 | 16 | 12 | 23.5 |
| A1/1 | 16 | 16 | 12 | 24 |
| A1/2 | 15 | 14 | 12 | 25 |
| A1/3 | 16 | 16 | 12.5 | 25 |

Tokens here include saved EOS IDs; task totals combine all turns, whereas
response medians do not. Command-only is a literal READ EVENT/ROUTE regex,
not a semantic judge. Extra text is not automatically useful reasoning.

The minimal held prompt is `Use the public task and available records. End
with READ EVENT <listedaddress> or ROUTE <listedport>.` It differs from the
training episode prompt that permits ordinary prose. This distinction is
intentional in a default-behavior readout and must be visible in reporting.
Do not silently replace it with a reasoning-demand prompt and claim the same
matched readout. Any such diagnostic must be separately labelled.

**Reporting classification:** full-text-captured, predominantly protocol-only
behavior; transient F1 sleep-2 expansion, no established retained-thinking gain.
Token counts are defined. Cohesion/metacognition must not be fabricated from
terse commands, and uncompleted semantic annotations remain unknown, not zero.

## Math and code also preserve the generated text

The family owners verified these existing, pre-shared DEV captures:

- F2: `lane1/readouts/cycle_009/CALL_0256.json` under
  `/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1`.
  SHA256 `d7967a76f77dfe29d8b8f3368b68a49a86fb0f65ee0992d5c457e5d9121c0ec0`;
  130 saved tokens and 407 UTF-8 bytes, terminal and nontruncated. The original
  tokenizer's round-trip matches `response.raw`. This DEV completed 12:11:50 UTC.
  Receipt: `orch_math_feedback_uptake_r118_final_20260915_attempt1/DEV_VISIBILITY.json`.
- F3: `reservations/R012_DEV_DEV_7.json` under
  `/localhome/local-rohing/orch_r108_code_parent_r115_node5_2_20260915_attempt1`.
  SHA256 `c4980f1273e16ef4f99be252de772731fe367885d9609a9fa8b3c4f8388bfb26`;
  41 saved tokens and 95 raw bytes, terminal and nontruncated. `response.raw`
  and `response.token_ids` are persisted before scoring.
  Receipt: `orch_r108_code_parent_r115_20260915_attempt1/DEV_VISIBILITY_1137.json`.

These are capture-integrity confirmations, not assertions of substantive
reasoning in every output. At 14:00:19 UTC F3 still had zero shared DEV bindings.
The shared implementations preserve the same response fields, but a successful
pre-shared readout is not proof that post-shared evaluation has completed.

## Provenance and reproduction

On `gpu/ovx3_ssh.sh`, the branch roots are
`/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1` (F1)
and `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1` (A1).
`COMPACT.json` records individual artifact hashes, paths and counts; no raw
child text or token arrays are exported. `audit_node_local.py` reproduces this
read-only audit on that node. It does not recurse into sealed paths or invoke
models, parents or training.

Source: `gpu/orch_r111_route_pair.py` (original open environment, open turns,
raw generation and readout capture) and `gpu/orch_r111_route_pair_shared.py`
(shared successor preserving these paths). The earlier semantic DEV reduction
is separately published in `orch_r118_dev_reduction_20260915`; its incomplete
annotations must not be treated as whole-cohort results.
