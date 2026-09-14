# L2 shared interface V1 — frozen before native calls

Owner SHORT; LONG imports `organism_v6.orch_l2_shared` unchanged. Main owns
integration. No worker may regenerate or independently select a shared cohort.
Frozen source: SEQ266 FULL/273 initial adapter mounted named_parameters state
`e226cea230b4b970cd5a94cb2b853350aa8bfb95ab4ba69cba3e78ebdd0ad3bf`.
Read-copy node3 `/tmp/astra_goal_quality_train_20260914_attempt2/FULL_TARGET/train/adapter`
into own root; never write source root. Portable manifest SHA is in module.

## Minimal wire interface

Own A100 root `/tmp/orch_l2_shared_20260914_attempt1`; immutable files:
`COHORT.json` = `shared.cohort(existing_release_exclusions)`;
`SOURCE.json` = `shared.source_document`, a single INITIAL child generation of
the exact stored EVENT text. It includes all collections, failures, store and
SHA. No per-arm replacement or retries beyond the existing 8-call/world cap.
`INITIAL.json` = adapter absolute path, state_sha256, base_sha256 and ordered
adapter file inventory; `PREPARE.json` binds source code, protocol, local model
and portable inventory. No credentials. `shared.verify_source` validates wire.
Training: `cohort['train'][cycle-1]`; readout: `cohort['held'][stage]` (stage0–3).
`shared.tasks(world)` returns the same two opposite-goal tasks for every arm.
Use only the current world's EVENT subset from SOURCE, not global store or
other splits, in model/parent context. Held data is never passed to parents.
Source generation uses initial child; experience collection AND training use
previous actual lane child. Readout uses actual output child in fresh process.

Eight experience worlds/16 episodes per cycle, eight fresh held worlds/16
episodes per readout; initial+three sleeps. Four lanes, one training seed.
RICH SYSTEM/GUIDANCE from `organism_v6.orch_full_rich` in all experience lanes,
including FROZEN. Six child turns, generation512/context2048, no truncation of
complete parent messages. Readouts are parent-free, no richness instruction,
same neutral rich-compatible action grammar and same complete raw scoring.
Source runs once on frozen lane2, then all four lanes consume the same file.

Fixed batch call ceiling8648 =448 shared source +4×1600 learner calls +3×600
parent/evaluator calls (SHORT, LONG, guidedFROZEN), all successful/failed attempts counted BEFORE dispatch.
Learner1600 includes experience288, readout384 and retention/revision capacity;
unused capacity is not permission to add tasks. Separate reflection and
semantic grading calls count in parent600. No source calls charged again to
learner. There are no additional model calls outside these buckets.
SHORT parent opportunities at turns0,2,4 (up to48/cycle), maximum160 tokens per
complete response, plus one ≤512-token distillation/cycle. Parent may decline.
FROZEN receives the identical SHORT coach policy, same opportunities and caps,
but its OWN evolving experience transcript and OWN response-aware calls; it
never consolidates. FROZEN is GUIDED+FROZEN, not unparented. Its independent
600-call parent bucket includes its semantic grading and distillation. SHORT's
600-call bucket also contains UNPARENTED semantic grading (no coaching there).
LONG must declare strictly fewer opportunities/tokens before its calls, within
its same600-call allocation; its own protocol does not change shared tasks.

Four presentations of current-cycle actual admitted raw child turns plus the
existing 222 legacy rehearsal rows: layout(128,20,62,12,new_rows), batch4,
updates=2×(12+new_rows), at most216/sleep, fresh AdamW, lr3e-5,
betas(.9,.999),eps1e-8,weight_decay.01,amsgrad/foreach/fused=false,
seed8203,no gradient clipping (same actual266 recipe). Frozen Qwen2.5-7B-Instruct, rank8/alpha16/dropout.05
existing LoRA only. No cumulative prior-new replay and no optimizer restore.
Zero admitted rows => ZERO updates including rehearsal; copy/reference prior
child, log NULL and still run fresh readout. Unchanged trained weights are
reported as such, never rejected or padded. Legacy data comes from portable
bundle verified rehearsal layout, never source-held worlds.

Outcome plus raw-bound semantic rubric needed for admission: 150–400 generated
tokens, terminal/nontruncated, prior actual READ, correct episode, six existing
rich rubric booleans; unresolved/error reviews admit nothing. Preserve every
failure, gate decision, raw target, parent message and exact neutral projection.
Parent and rich prompt text removed from student prefix; only child's complete
raw final response receives loss. Tokens cannot be fabricated or padded.

Metrics: all fixed task counts; per-sleep fresh success slope, qualified-row
yield/actual token distributions, evidence grounding, correction after feedback,
old W0/W8/audit retention (each16 trials, threshold15/16), repeated failure
cohesion and within-task opposite-goal consistency. Revision/quality observed
in experience are NOT sealed generalization outcomes. Parent gets only own
experience/learner telemetry, never readout scores, worlds or keys/hosts.
No claim of gain from a ceiling, one-seed result or historical rich-null erasure.

Resource allocation SHORT A100 physical0/2/3 only, LONG1 only; never4–7,
node1 or other tenants.12h initial batch;36 GPUh SHORT +12 GPUh LONG. Owned
UUID/CVD/PID guards, lease-end safety and verified /tmp storage mandatory.
Native seam from ce9a906e; no edits to builder files. Null handling is caller
owned because existing positive-row bridge rejects nulls. No new framework.

Before any calls: recipe corrected to actual266 lr3e-5/no clipping; the first
local draft's lr1e-4/clip1.0 was not executed. Shared actor hook:
`orch_l2_guided.episode(world, task, generate, store, parent=None, telemetry=None)`.
Parent callable receives ONLY own public transcript/current task/experience
telemetry, returns `{speak: bool, message: str, rationale: str}`. Never pass
global SOURCE, prepared manifests, filesystem paths or sealed evaluation to
this hook. Parent backend request schema excludes them by construction.

2026-09-14T23:43Z prospective control correction BEFORE ANY model calls:
shared cap8648 supersedes initial8048 by adding FROZEN's own600 parent bucket.
FROZEN now receives genuine SHORT coaching, with own response-aware inputs.
The unexecuted initial interface/code did not deliver frozen coaching. Preserve
that draft/preparation receipt; do not claim it was an executed guided control.
