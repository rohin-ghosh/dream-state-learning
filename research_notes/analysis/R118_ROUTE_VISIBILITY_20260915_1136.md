# R118 route open-turn and readout visibility audit

Observed September 15, 2026, approximately 11:35 UTC through `gpu/ovx3_ssh.sh`.
No GPU calls were added. Raw evidence remains node-local; FINAL was not read.

## Open turns exist and execute

The case-sensitive `open_turn*` filename search misses these artifacts:

- F1: `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1/cycle_0001/OPEN_TRAIN_0.json`, SHA256 `93e5b2186813d6ebf637f4741edffeee30c03cf2cf05bec85a3fd2fbdb2c4968`.
- A1: `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_4_attempt1/cycle_0001/OPEN_TRAIN_0.json`, SHA256 `e5ed9486c06e8073e317140a4b1aca1deb555d2dd4cf5634adb56f49a89fc555`.
- Parent-free F1: `/localhome/local-rohing/orch_r111_f1_v4_20260915_node5_0_attempt1/open_readouts/readout_0001/OPEN.json`, SHA256 `2fb284e5d03335306d78eb25424413135fbc10325e262fd2380ac8ca37eadd5c`.
- Parent-free A1 has the corresponding physical-4 root and the same first OPEN artifact hash.

| Branch/scope | OPEN artifacts | Actual environment calls | Continued after inspection | Observed STOP |
| --- | ---: | ---: | ---: | ---: |
| F1 TRAIN | 6 | 6 | 4 | 1 |
| F1 parent-free readout | 3 | 4 | 2 | 1 |
| A1 TRAIN | 4 | 0 | 0 | 3 |
| A1 parent-free readout | 1 | 0 | 0 | 1 |

The first F1 TRAIN open turn executed two READ operations and stored the returned
environment observations and their hashes. These were repeated reads of the same
record: enactment is verified, novelty or useful initiative is NOT established.
All inspected parent-free OPEN artifacts have `parent_free=true` and
`training_buffer=false`. `initiative` remains `UNKNOWN_PENDING_SHARED_JUDGE`;
these counts do not invent semantic initiative labels. A1's lack of an executed
open action is observed child behaviour, not absence of the harness turn.

## The full decoded continuation is retained

Native held outputs are saved in `CALL_*.json` at `response.raw` and
`response.token_ids`; `HELD.json.cached_responses` retains the same continuations.
`generate_batch` decodes the complete generated suffix through EOS before the
environment parser acts. It does not discard prose before a READ/ROUTE command.
Stored held system prompt:

> Use the public task and available records. End with READ EVENT <listedaddress> or ROUTE <listedport>.

This is not the TRAIN reasoning invitation. All-call medians conflate the eight
held tasks with focused, retention and audit probes. The table below uses ONLY
the eight DEV tasks in `HELD.json.cached_responses`, excluding those other probes.
Token counts include terminal EOS when present. Protocol-only means the entire
trimmed decoded response matches one `READ EVENT <id>` or `ROUTE <id>` command.
Nonprotocol does not by itself mean reasoning, novelty, coherence or correctness.

| Branch/checkpoint | DEV native calls | Protocol-only | Other visible text | Median generated token IDs | HELD.json SHA256 |
| --- | ---: | ---: | ---: | ---: | --- |
| F1 sleep 0 | 16 | 16 | 0 | 12 | `7c124bd063e255830e4a12cef3054417effab28cd48bc22a105f42eeb764cd43` |
| F1 sleep 1 | 12 | 8 | 4 | 13 | `6f8d42ef3846ed723fbe79f2741c6bd945fe58f15ae7620e0e88e103338294dc` |
| F1 sleep 2 | 18 | 8 | 10 | 74.5 | `f9b3375584ab74dbf12613cf924cec332b76b7524f80e262d80bde1b4481c069` |
| F1 sleep 3 | 16 | 16 | 0 | 10.5 | `fac2a98538874dcb4958b801f0d109bba7f413c5db4b38d902361db2b8b03418` |
| A1 sleep 0 | 16 | 16 | 0 | 12 | `7c124bd063e255830e4a12cef3054417effab28cd48bc22a105f42eeb764cd43` |
| A1 sleep 1 | 16 | 16 | 0 | 12 | `6920dc31c2d3600be15c0d3fdffb0d7e8a7da3edddf3a8ef4b9370c00d52bf20` |

Files use each branch root above plus `readout_000N/HELD.json`. F1 sleep 2
contains both restated environment data and prose proposing routes, noticing
contradictory feedback and revising an earlier assumption. Some proposed edges
are unsupported. This is a qualitative inspection, NOT a blinded composition
score, retained metacognition result or parenting effect. Sleep 3 returns to
bare commands. The morning report must preserve that checkpoint distribution
rather than call every route readout rich or every route readout protocol-only.
Visible token use is measurable; latent reasoning cannot be inferred from a bare
command, and no semantic behaviour score is imputed where the output lacks evidence.

## F2 and F3 storage checks

Subsequent owner checks verified full decoded DEV continuations, not only extracted
final answers. These checks establish storage fidelity, not reasoning quality.

- F2: `lane1/readouts/cycle_005/CALL_0145.json` under the posted math root.
  Native capture SHA256 `e655a87ae81a4f0e477b26e823030a0b161a3f1f211906e67e8da5016d1109a7`;
  `response.raw` contains 706 UTF-8 bytes, `response.token_ids` contains 283 tokens
  including EOS. Independent CPU decoding of saved tokens reproduces the exact
  stored text; no model load or new GPU call. Parent-free and excluded from sleep.
  Receipt: `research_notes/analysis/orch_math_feedback_uptake_r118_delivery_20260915_attempt1/DEV_VISIBILITY_1136.json`.
- F3: `reservations/R012_DEV_DEV_7.json` under the posted code F3 root.
  Native capture SHA256 `c4980f1273e16ef4f99be252de772731fe367885d9609a9fa8b3c4f8388bfb26`;
  `response.raw` contains 95 UTF-8 bytes, `response.token_ids` contains 41 tokens
  including EOS. The native driver stores the full continuation before scoring;
  no final-answer extraction replaces it. Parent-invisible and excluded from sleep.
  Receipt: `research_notes/analysis/orch_r108_code_parent_r115_20260915_attempt1/DEV_VISIBILITY_1137.json`.

Neither check read FINAL. Neither establishes access to hidden thoughts.
