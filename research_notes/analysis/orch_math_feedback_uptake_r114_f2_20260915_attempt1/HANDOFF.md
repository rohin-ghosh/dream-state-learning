# F2 v4 CPU handoff — R114

Status: **CPU_PREPARED_NOT_NATIVE_READY**. This is a separate prospective revision from commit `05a0b4287d037ce6b9c7c8545bbbfc32230d08e9`. Existing v2/v3 receipts, live R110 lanes, selected tasks, raw histories, and counters remain untouched. No GPU inference, provider call, weight sleep, or A1004 launch.

## Exact prompts and mutable fields

System: `You are a helpful assistant.` The three original child prompts remain:

Episode:
```
Take this problem in your own direction.

{question}

When you have an answer, end with FINAL: followed by that answer.
```

Pre-sleep (one open invitation; context-boundary label only here):
```
We are about to leave this context; take the space to reflect in your own way.
```

Reflection:
```
Reflect on your recent experiences in your own way.
```

After each of the two sequential tasks, with a parent slot after the completed response:
```
The task is over; the environment is still here.
```

At the subsequent context boundary, repeat that open invitation once per episode without a parent or parent context. Those two responses are PROBE, not parent-visible TRAIN. This is elicitation, not evidence of consolidation. The native harness must enforce the context boundary; this CPU plan is not a deployed runtime.

DEV8/FINAL8 minimal prompt remains:
```
{question}

End with FINAL: followed by your answer.
```

DEV focused-mode probe, two fixed DEV tasks at sleep0/every cycle, fresh and parent-free:
```
{question}

focus and give the answer
```

The v4 §6 fixed parent template is snapshotted exactly in `PARENT_TEMPLATE_V4.txt` (blockquote markers removed, original line wrapping retained). Both parenting systems use the same text and principles; actual broker formatting still needs its native binding. Template SHA256 `6a81eebbb859799e347ce515507ef0ffb4a789eb777d2ddc7758226d3c4e7e0c`; filled parent+principles SHA256 `4733d90c20a965c0b0dfd04a34e5563853f966082de05f9300d03d1841e0cbaa`.

FOCUS = `Attend to your own parenting of the child's thinking rather than its game performance`. STYLE = `creative, supportive`. REFLECTION = `long`, 8192-token initial budget. Head-editable fields are FOCUS/STYLE/REFLECTION, never cadence or fixed text. The literal v4 parent block has NO [REFLECTION] placeholder despite the surrounding field list; reflection remains branch configuration, not an invented added sentence in the fixed prompt. Nudging/GAME remain matched F2 settings. Current fixed text retains child-visible feedback, broad permission, and useful self-organisation; it forbids supplying solutions/hidden evaluator scores. No outcome/quality continuation gate.

## Frozen DEV and FINAL commitments

Common contract SHA256 `a683e78d956f95e5231ca529e65093f92e0da0f6988d66b1f07fd8c616e8fe80`.
DEV set SHA256 `49feeb421c0ff2fd97c358b7d9770d9372f5c62cdfb6348118c836714d3bdbc1`; DEV file SHA256 `015cf35ecc762ff98ea97446434d8c9336aaf3106e809973cc331bb07898446c`.

- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E0`
- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E1`
- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E1003`
- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E3`
- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E4`
- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E5`
- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E1007`
- `MATH_PIPELINE_L2_20260915_ATTEMPT1_R111_F2_HELD_C0_E7`

Focused DEV2 = the first two IDs listed, chosen before any results; focused-plan SHA256 `1339ab93371d441ed67e81419342d58a691a5c8dae58f0393b40ce31a9bce4f3`. These are additional reasks, NOT a reduction of DEV8. Task/held/open decoders remain greedy and unconstrained by reflection repetition rules; reflection/metacognition use the existing 8-gram guard. All raw text is retained.

FINAL8 commitment SHA256 `b3642ffe0e6e501ca805e323d28cdf1f159296872b78f798f65180417dc044ee`; file SHA256 `1e5548fd989fa79f95a316a0943cae0a92de4e479d5021a0005defa2c00c6b8e`. Both DEV/FINAL task selections are unchanged from the UNRUN v3 preparation; no reselection or outcome inspection. FINAL IDs/questions/answers/results are absent from public receipts and must never reach parent/head/exchange. Actual child-visible TRAIN feedback remains in the parent history, including failed checks; only hidden evaluator material and readouts are stripped. DEV readouts may inform HEAD/EXCHANGE but not enter the direct-parent transcript; head fields may guide parenting. Native export checks are still pending.

DEV sleep0 plan `6a614f390915e2139aa4579a4d0a2c85d3ce4288a334d2a434477e7be5b4c333`. FINAL sleep0 plan `bff30a4c3115ddcdd2b3eee47569be426ea1148b0496eb8431892d01e75c76b7`. Neither has run. Node root `/localhome/local-rohing/orch_math_feedback_uptake_r114_f2_20260915_attempt1`; sealed files under `sealed/`, permissions0700/0600 are not same-UID isolation. No raw data copied to VM.

## Corrected time and finite accounting

**FINAL morning is September 15, 2026 at 17:00 UTC, NOT September16 06:00.** v4 supersedes that v3 date. Ordinary native cutoff stays16:59; only the explicitly requested morning FINAL window uses17:00–17:02 under the UNCHANGED17:02 hard stop. No silent extension. If eight calls cannot finish by the hard stop, preserve their actual incomplete/failure denominators; no retry or next-day reschedule. Native integration/admission and the R112 gate still precede dispatch.

Keep the prior1168native/384parent-slot ceiling per member; this revision adds probes by reducing only the prospective maximum cycle count from96 to63, before any F2 call, unrelated to outcomes. Exact per-member worst-case plan:

- sleep0:8DEV +8FINAL +2focused =18 native;
- each cycle:2task +2parented open +1metacognition +1reflection +2parent-free boundary open +8DEV +2focused =18 native,6 parent slots;
- 63cycles:1134 native and378 parent slots;
- morning FINAL:8 native reserved inside the ceiling;
- total1160 planned native/member (2320 pair),378 slots/member (756 pair), bounded by inherited1168/384 member caps (2336/768 pair). Eight unused native units are not permission for ad-hoc calls.

Two sequential episodes per cycle; no new controls. No optimizer/adapter; actual weight updates, optimizer steps and child training-token exposures are all0. Actual anchor lambda is **not applied**. The inherited future SAME42/λ.25/16new+1later-rehearsal recipe remains inactive and is not a sleep claim. ≤8GPUh/member, same absolute hard wall. Supplementary retention/audit/capability/shared-judge work still requires exact source/call bindings, not hidden additions.

## Interpretation and gates

Obstacle persistence labels are PERSISTED/ABANDONED/LOOPED, requiring transcript/shared-judge or author review; no automatic semantic admission. Post-answer exploration is descriptive and distinct. Open initiative uses INITIATE_QUESTION/REVISIT/SEEK/NEW_GOAL/STOP only when actually reviewed; otherwise UNKNOWN. Observable continuation changes are not proof of causal metacognition. Shared judge remains Main-owned.

R112 remains binding: Fable1 GPU AND provider need explicit Rohin GO/DONE relayed by Fable and bound to this new contract; no timeout/silence inference. Node5_5 stays with its current owner until receiver readiness and natural cycle end; no release requested. A1004 remains Main judge-only; original node3 math0–2 untouched. Missing/late parents continue with MISSING, [SILENT] valid, no retry/late application.

Remaining work: actual resident collection/context assembly/open-turn integration, matched broker transport, sealed fresh batched readouts, shared judge/supplemental source bindings, owner release and strict proc/UUID/CVD/base admission. This handoff completes CPU preparation, not native launch readiness.

## Tests and publication

44 tests PASS locally and the same44 on-node; not88 independent tests. Includes exact template, unchanged3prompts, sequential open turns, no-parent boundary plans, DEV-only focus, corrected FINAL window/once-only reservation/call budget, explicit R112 receipt, no sleep/semantic-auto-label claims. Source hashes and logs are in `SOURCE_TEST_BINDINGS.json`, `LOCAL_CPU_TESTS.log`, `NATIVE_CPU_TESTS.log`. Main publication allowlist is `STAGE_PATHS.txt`; no git mutation performed.
