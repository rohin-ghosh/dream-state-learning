# R115 / R116 F2 native launch handoff

F2 root: `/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane1`.
A2 root: `/localhome/local-rohing/orch_math_feedback_uptake_r115_f2_20260915_attempt1/lane5`.
Genuine frozen Qwen2.5-7B-Instruct BASE; no adapter, optimizer, LoRA updates or retained-weight-learning claim. Actual lambda N/A. Shared eight-lane optimizer is a FUTURE common-boundary change, not implemented here.

R115 actual audit GO and R116 launch-now authority. §9.5 is no longer an additional launch gate; 52 tests nevertheless pass locally and the same52 on-node (including8focusedruntime tests). Enacted INSPECT returns current environment question; CALCULATE executes bounded arithmetic and returns the observation. DEV/FINAL plus attached open traces cannot enter the Experience buffer or parent payload; no training rows exist. Actual broker-bound REFLECTION settings change the generate(max_new_tokens) argument; invalid/late bindings preserve the initial cap. The model default is long3072, with context-limited effective caps recorded, not a forced output length.

## Exact prompts

System: `You are a helpful assistant.`

Episode:
```
Take this problem in your own direction.

{question}

When you have an answer, end with FINAL: followed by that answer.
```
Pre-boundary:
```
We are about to leave this context; take the space to reflect in your own way.
```
Reflection:
```
Reflect on your recent experiences in your own way.
```
Open turn:
```
The task is over; the environment is still here.
```
Minimal DEV/FINAL: `{question}\n\nEnd with FINAL: followed by your answer.` Focused reasks use `{question}\n\nfocus and give the answer`. Separate truthful environment messages describe INSPECT/CALCULATE availability and carry actual feedback; these messages and all exact native tokenized prompts stay on-node. No required action, automatic semantic label, or task-answer hint from parent.

## Parent policy

Both systems reread `/data/home/rohing/courier/swarm/prompts/F2.md` and `F2.fields.json` every call, NOT the repo prompt directory. Initial prompt SHA fd28beb64a7b463b6703f52a84deb47ef64ce2cd14e8b7ede1e44e8aab1e94fb. Creative/supportive+nudge, long3072. Fable requires actual claude-fable-5-1, Astra actual openai/openai/gpt-6-astra. Frozen shared judge prompt0466c6fa8bbd8c75f8e2d4c625498423835b2b5285e58c4f703069e8b6c532fd, Main-owned. SYSTEMS comparison only; missing/late/SILENT counted, no outcome stops.

Hubble's F2 broker config `/tmp/orch_r116_claude_1043/F2/CONFIG.json`, GO `/tmp/orch_r116_claude_1043/F2/LAUNCH.json`, shared runtime `/tmp/orch_r116_claude_1043/source/gpu/orch_r110_claude_broker.py`; command uses `--prompt-root /data/home/rohing/courier/swarm/prompts`. Memory minimum1073741824bytes, existing global serialized Claude lock. Math's first duplicate broker attempt was rejected before calls by the single-lane lock; no foreign broker was killed. The admission-only terminal caused Hubble's first broker to exit; restart is same config/ledger, not a new experiment. A2 config `/tmp/orch_math_feedback_uptake_r115_broker_source_20260915_attempt1/ASTRA_CONFIG.json`, GO `ASTRA_GO.json`, entry `gpu/orch_math_feedback_uptake_r115_broker.py --member ASTRA` in that immutable runtime.

## Data / budgets

DEV8 SHA49feeb421c0ff2fd97c358b7d9770d9372f5c62cdfb6348118c836714d3bdbc1; FINAL8 SHAb3642ffe0e6e501ca805e323d28cdf1f159296872b78f798f65180417dc044ee. Exact DEV IDs in READY_COMPACT.json. Exact DEV+FINAL ID roster at `sealed/READOUT_ROSTER.json` under the common node root; roster commitment in READY_COMPACT.json, no keys/results exported to parent/head/exchange. Prior selected cohorts remain unchanged, no outcomes inspected.

Every two sequential episodes:2 originals+2parented open turns+1metacognition+1reflection, then fresh parent-free DEV8+8attachedopen+2focused+2boundaryopen =26native/cycle. Sleep0 DEV/FINAL plus attachedopen/focused=34calls. MorningFINAL8+8attachedopen=16calls. 43cycles maximum =1168native/member;258plannedparent slots within384cap. Parent-free outputs never enter training/parent buffer. No extra calls/control triples. Native ordinary16:59, FINAL at17:00 September15, unchangedhard17:02UTC; <=8GPUh/member. Cap exhaustion/wall failures recorded, no retry/extensions. Raw exclusively node-local.

## Launch and failure provenance

READY6afedafef4b94ffae368fdcec67c91d0830f7c3c179d503428472390b1c94d55; COMMON195b9c4d17b29564ecb56be9403fdfe5a84d3a3a9ccda84492feb9639d1e70fe. First CPU preparation lacked wrapper scripts; its partial outputs preserved in sibling `orch_math_feedback_uptake_r115_f2_cpu_partial_20260915_attempt1`, zero native/provider calls. Prepublication manifests preserved separately.

First guardian312181 spent30strict admission attempts and no native calls; all blocked process identity drift (including changing sshd listener title). No scanner exception/waiver. Admission-only continuation helper is separately hashed, keeps original ACTIVATION/deadlines, forbids any existing LAUNCH/counters and archives prior admission-only terminal/failure. Native source is unchanged. Supervisor342937 retries the same strict full/proc UUID/minor/CVD scan; actual nativePID and first response receipts will be added separately, never inferred from empty GPU memory.

Native receiver command: `/localhome/local-rohing/v2/venv/bin/python -B /localhome/local-rohing/orch_math_feedback_uptake_r115_f2_source_20260915_attempt1/gpu/orch_math_feedback_uptake_r116_launch.py --index 1` (or5afterCicero safe release), with emptyCVD supervisor and pinned UUID child. Source/root bindings as above. A1004 Main judge and existing node3 math untouched. No git mutation.
