# R125 source_v3 — one exact pre-update recovery

September 16, 2026. Local integration:222 tests and222 subtests PASS.

The recovery is bound to the original run1 second SLEEP_REQUEST, checkpoint1
(48 optimizer steps), pinned control2 EXIT/NATIVE log bytes, and the original
source_v2 pre-encoding traceback. It is not a generic permission to clear pending
work. The original generation method must have an identical AST in the repaired
runtime. Each of the three already-committed generations must replay identically,
including native token IDs, raw text, termination flags, prompt hash, decoder,
adapter hash and base hash. RNG fingerprints and replay receipts remain node-local.

Only then does the same life finish its pending sleep using all existing rows,
the restored AdamW and reconstructed RNG. Recovery does not append new TRAIN
rows or count the verification replays as new experience. It is one-shot: any
mismatch or new UPDATE after the failed checkpoint rejects recovery. Exact
original final RNG bytes were not saved; the proof is deterministic replay under
the unchanged generation implementation, not comparison to an unavailable file.

The tokenizer repair allows only the actual Qwen endoftext pad token as an own
target; chat-role controls remain rejected. Readouts canonicalize the optional
GPU display prefix while still requiring the exact assigned UUID. A new `_r2`
readout namespace preserves failures; missing readouts of saved checkpoints0–2
are separately dispatched without importing their results into the child.

Prospective source/control directories are `source_v3` and `control3` under
`/localhome/local-rohing/orch_r125_continual_20260916_attempt1`; life root stays
`run1`. `resume=true`, same GPU2, same wall2026-09-16T22:04Z, same birth context,
same LoRA/AdamW/history and generation recipe; no fresh adapter or experiment
shell. Staged tests, full source/plan pins and fresh admission precede dispatch.
No recovery success or retained improvement is claimed before native receipts.
