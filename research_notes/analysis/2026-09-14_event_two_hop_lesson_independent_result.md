# Independent terminal review — EVENT two-hop lesson

Date: 2026-09-14. **Terminal evidence/replay checks PASS; behavioral result is
partial, own-text-supported improvement, not parametric or fresh-world success.**

Review is CPU-only and local. Only this note was edited. No model, tokenizer,
torch, GPU, remote calls, run control, or new verification framework. This is
a retrospective review, not a launch gate. The user-reported 21-test pass is
not substituted for result evidence or independently rerun here.

## Evidence and immutable source

- Lesson root: `gpu_artifacts_local/astra_event_two_hop_lesson_terminal_20260914_attempt1/extracted`.
- Baseline root: `gpu_artifacts_local/astra_event_two_hop_turnbound_terminal_20260914_attempt1/extracted`.
- Lesson archive: sibling `terminal.tar.gz`, 349,243,912 bytes; independently
  hashed SHA-256 `2acae64c4be4abd492f7efb0f50675509d7d0650360f7a23e2575e38ceb7f4a6`, matching the supplied value.
- Captured source commit: `0b495971f8ecb2353162757abbdb938effa4493b`.
  All 31 imported project modules came from this capsule's `source/` and
  matched their local Git blobs at that exact commit. No working-tree helper
  or later fresh-namespace default was substituted; replay used `turnbound`.
- Driver SHA-256: `8b98c9f2169e5e02f9d6ce0cf69f93f523cab2c80ba91ec427743df8e6ee1098`.
  Lesson helper: `cb0ca496ff46b3f086541c98299753218d275c55baba6e15d5e6f5124e211450`.
  Actor helper: `6b825c63ad2b1fc96ed5cf87a1a11f186afa23a9bf358b05330caf87596ca441`.
  These match the saved entry/binding fields. Baseline's captured actor helper
  is byte-identical; its recorded source commit is `5dd5625fbefb6ea4915c5eeb2a471f58bc898ffc`.
- Independently matched 266 selected extracted files to their actual archive
  members: all phase artifacts, launch records, run log, and those 31 modules,
  totaling 87,381,587 payload bytes. Checked selected paths for symlink/escape
  problems; none found. The archive root is
  `astra_event_two_hop_lesson_20260914_attempt1/`.

## Phase disposition and joins

PREPARE is `PREPARED_NO_MODEL`, zero fits/calls. COLLECT, TRAIN and AFTER are
`COMPLETE`; there is no phase `FAILED.json`. All four saved INPUTS and result
bindings agree. Recorded completion is **2026-09-14 15:13:29 UTC**.
The 895-byte run log contains loading/deprecation/generation-option warnings,
not a recorded terminal exception. No premature collection closure occurred.

The baseline result hash is
`d0e661c4fc052bfc70a06dcb9c7974ce15cb0f53b33e55b8c6e65a57908d9d83`;
the original collection result hash is
`ba5b07a2d17a0c0ff17ca0f5c1c0ed3ba4ebf75c436f6bbb087e1be35a8a36dc`.
The baseline's parent, zero-fit turnbound configuration, collection join,
loaded/final parent state, and frozen-base flag match the lesson binding.
The source collection replay matches the copy embedded in LESSONS exactly.

`read_lessons` and `read_training` pass against these frozen bindings.
TRAIN and AFTER both join the actual lesson result
`6e9df416f871d0dd4ac74b9a7034ca8ee050ded9c48a833575d8990651ac3b33`;
AFTER joins training result
`860ea1e95274b9a5c651c8c0ea2e640ecf47d94299eb5dd310ecb138eec78bc7`.

## Actual commands, transitions and student inputs

Frozen replay verifies **12 actual native responses, two complete six-command
paths on tasks 0 and 2**. Each path reads the four displayed EVENT addresses
in order, then makes two legal source-supported transitions to its goal.

| Training task | Actual first route | Actual second route | Terminal |
|---|---|---|---|
| 0 | `ROUTE P_4OSO65OGRU` | `ROUTE P_3CQRLYY2QE` | reached_goal |
| 2 | `ROUTE P_R3YCJCLGZO` | `ROUTE P_YMVHHZ7J2C` | reached_goal |

All 12 flat CALL prompts/responses join their nested captures without errors.
Each target equals the child's actual command, not a substituted plan target.
Replay recomputes source joins, actual feedback, intermediate states and stops.
Every saved training prefix equals its captured student prefix and lacks
parent guidance, the injected source-hint section, and the next-command hint.
Actual conversation history remains. Parent-guided prompts remain in the
provenance evidence, **not in the encoded student inputs**. The guidance is
algorithmic/source-informed researcher instruction, not evidence of autonomous
child planning or an independently learned parent policy.

## Sleep, masks and saved state

- Exact saved layout: **128 old-memory + 20 cue + 62 audit + 12 trajectory =
  222 rows**. The first three corpus digests match the binding; the final
  twelve rows equal replayed lessons.
- RECIPE and every LOSSES row agree on updates **1–100**, four row indexes
  per update, and the frozen schedule. Recounted **8,245 active causal labels**;
  every loss is finite/nonnegative. First/last loss:
  `0.06399396061897278` / `0.002628092188388109`.
- **200 trajectory presentations**, doses
  `[17,17,17,17,17,17,17,17,16,16,16,16]`. Also 100 memory and 100 behavior
  presentations. The memory schedule uses indexes 0–99: 128 stored memory
  rows does not mean all 128 were presented during this 100-update sleep.
- All 222 saved masks pass the frozen validator: nonempty contiguous target
  spans, matching input/label IDs, masked prefixes, masked final suffix,
  EOT `151645`, and length at most 2048. Each of the 12 trajectory target-ID
  sequences equals the corresponding actual native output token IDs exactly.
  No tokenizer was loaded; independent text-to-token re-encoding is not claimed.
- All inventoried training and adapter files hash correctly. Saved adapter
  file: **80,792,096 bytes**, SHA-256
  `3f7029b84d41f0715ee8d11c8fc12540717bc24029abd7d03e999f79ee3ec5f1`.
- COLLECT initial/final and TRAIN initial state:
  `207ad43ef65f1f6ba7c50d37f5d5dfa8c2253d1cb301e585d7b6b7a78bb93990`.
  TRAIN final = AFTER mounted = AFTER final:
  `37ec37884e4b0b679edd1dba1be1dec3474589e992649f3a33e7e3b1ec78b8c0`.
  Recorded readonly adapter-file/base checks pass under the bound driver.
  **File hashes are independently recomputed; tensor-state/base equality is
  authenticated runtime evidence, not a new CPU tensor/base-model hash.**

## Independently rescored readout

All 16 baseline and 16 AFTER episodes replay and rescore identically to their
saved records. Task identities and protocol match. Baseline was 0/2 on both
task groups for every condition.

| Condition | Baseline all | AFTER trained 0/2 | AFTER reversed 1/3 | AFTER all |
|---|---:|---:|---:|---:|
| ON_OWN_TEXT | 0/4 | **2/2** | **1/2** | **3/4** |
| ON_PARAMETRIC | 0/4 | 0/2 | 0/2 | 0/4 |
| ON_UNAVAILABLE | 0/4 | 0/2 | 0/2 | 0/4 |
| OFF_OWN_TEXT | 0/4 | 0/2 | 0/2 | 0/4 |

ON_OWN_TEXT passes tasks **0, 1, 2**. **Task 3 fails `dead_end`**: after four
legal reads it takes `P_4OSO65OGRU`, then `P_3CQRLYY2QE`, ending at
`N_XVM2USEMBJ` instead of goal `N_PJCMWXVRLH`. These are task 0's route ports;
the trace demonstrates wrong-goal routing, not robust order invariance.

All four ON_PARAMETRIC and ON_UNAVAILABLE episodes fail `duplicate_address`.
The 16 parametric memory responses have **0/16 exact matches** to their
captured source records. Correct old-memory recall does not establish new
graph storage or successful retrieval. OFF_OWN_TEXT's task-order failures are
`invalid_route`, `dead_end`, `invalid_route`, `duplicate_address`, unchanged
from baseline.

All AFTER actor and parametric-memory callbacks join their native captures;
own-text services use actual captured EVENT text, and unavailable services
return the declared unavailable string. No parent hints appear in AFTER
prompts; adapter disabling occurs only for OFF_OWN_TEXT actor calls.

**147 native calls = 83 actor + 16 parametric memory + 32 retention + 16 audit.**
Actor counts are 24 each for ON_OWN_TEXT, ON_PARAMETRIC and ON_UNAVAILABLE,
and 11 for OFF_OWN_TEXT. The 13 unused slots reflect legitimate early episode
termination in OFF_OWN_TEXT, not missing collection/readout evidence. Every
capture has no native error and a terminal, nontruncated generation. Recorded
AFTER maxima: 689 prompt tokens and 97 output tokens; COLLECT maxima: 763 and
12. Both stay within 2048 context / 160 generated-token limits and call caps.

## Retention and audit

Independently joined all 32 retention responses to CALL records and the saved
old-memory targets: **16/16 at W0, 16/16 at W8**, exact terminal, nontruncated
recall of 16 distinct facts per wrapper. Rebuilt held cases and replayed all
16 audit responses: **16/16 total, 8/8 true and 8/8 fault**, parent absent.
The audit's four source events occur in saved old-memory data. This remains
a supplied-source comparison task, not autonomous audit-case discovery.

## Causal interpretation and limits

The defensible result is **post-sleep improvement in parent-free use of supplied
own EVENT text on one already exposed graph**, covering both trained displays
and one of two reversed displays. The same frozen baseline protocol had no
successes. The other conditions do not acquire routing success.

This is not fresh-world transfer, reliable reversal invariance, autonomous
discovery, parametric acquisition of the new graph, or H1/H2 confirmation.
There is one graph, one sleep/seed and two reversed variants, not independent
fresh tasks sufficient for a generalization estimate. The disabled-adapter
control removes the **whole adapter**, not just this lesson's update; the
baseline is pre-sleep, not a matched additional-sleep control. Joint replay of
old memory/cues/audit and trajectories therefore does **not isolate the causal
contribution of trajectory supervision**. No causal claim is made from the
launch itself, training loss alone, or retained old-fact/audit accuracy.

No unresolved integrity/replay failure was found. Behavioral failures are
retained explicitly above. Ancestor model files and original hardware/base
weights were not reloaded; historical lineage beyond the supplied joins was
not independently reconstructed. Baseline episodes were replayed from their
saved panels; its individual flat native CALL files were not rejoined here.

## Local verification execution and bounds

Executed archive check:

```sh
sha256sum gpu_artifacts_local/astra_event_two_hop_lesson_terminal_20260914_attempt1/terminal.tar.gz
```

The local Python here-doc checks ran with `PYTHONDONTWRITEBYTECODE=1 python3 -`;
an import guard rejects torch/transformers/peft/tokenizers and `sys.path[0]`
is the lesson capsule's `source/`. Calls reused frozen `read_collection`,
`read_lessons`/`replay_lessons`, `read_training`, `training_indexes`,
`validate_masks`, `replay_episode`/`score_episode`, and held `collect_cases`
with **captured-response-only callbacks**, never live generation.
All 31 imported project module paths were checked. Exact source comparison
used `git show 0b495971f8ecb2353162757abbdb938effa4493b:<relative-module-path>`.
Archive comparison streamed selected members with Python `tarfile` and SHA-256.

Recorded check outputs: `LOCAL_REPLAY_AND_JOINS_PASS`,
`FROZEN_GIT_SOURCE_MATCH ... modules 31`, and
`ARCHIVE_EXTRACTED_MATCH ... selected_files 266`.
The main replay read 234 selected JSON files / 6,659,132 bytes; LOSSES is a
separate bounded 100-line read. Limits were 300 selected files, 4 MiB per
ordinary JSON/text, 64 MiB per MASKS/TRAINING_ROWS, and 256 MiB decoded evidence.
Archive/adapter hashing was streamed; no evidence cap was hit.

Review-tool correction: the first archive-member lookup assumed no root
directory and failed to match members. After inspecting eight member names,
the exact root prefix was used and all 266 comparisons passed. This was a
review lookup error, not a hidden run failure or an artifact repair. A first
parametric-recall recount also retained the wrapper's trailing instruction in
the address lookup; extracting the exact EVENT token fixed that local checker,
and the rerun verified `AFTER_PARAMETRIC_EXACT_SOURCE_RECALL 0 / 16`.
No capsule contents were changed. Ownership of this completed note is released
to Main.
