# Memory-only positive-control continuation — design only

2026-09-12. **Recommendation: select the proposed memory-only continuation of the three original teach adapters; defer canonical completion.** No code, experiment, or launch is implemented or authorized by this document. Only this file is written. No repository/Git/network/GPU operations were performed; evidence inspection used local files and in-memory archive reads. Other contributors' work remains untouched.

## 1. Question, smallest design, and interpretation

HF red16 establishes that the original seed0 exact-prefix failure is not exclusive to vLLM. It does not diagnose its cause or establish failure at every seed. The smallest useful next question is:

> Can the existing single behavior-bearing adapter acquire reliable device–color recall under memory-focused continuation, while retaining its already measured arithmetic/PREDICT behavior?

Use one continuation recipe, three fixed original parent seeds, one terminal checkpoint per child, no sweep or intermediate score-selected checkpoint. Each child starts independently from its original teach parent, **never** from a repetition, fading, plasticity, or two-habit descendant. Do not chain the three seeds. Parent seed and continuation optimizer seed are paired 0→0, 1→1, 2→2; corpus/fact assignment remains identical, not reseeded.

This is an acquisition-plus-retention feasibility control. Compared with the original fit, memory exposure, batch composition, cumulative optimization, and optimizer restart differ. Success cannot isolate removal of interference, dose, optimizer effects, or a unique cause. Three optimizer seeds on one fact bank are not three independent fact banks or a population-level reliability estimate.

### Why not canonical completion now?

The prior comparison document supports canonical completion as a separate interface hypothesis. Its strongest evidence concerns candidate-normalized sentence-continuation probabilities, different training surfaces/objectives and much larger exposure; some original results remain attributed rather than raw-reverified. Importing that interface now would change exactly the rendering/target boundary this control should preserve, making a success less diagnostic for the existing chat-memory path.

Therefore retain the current question→single-color+EOS interface. Do not add declarative sentences, visible colored observations, whole-text supervision, new facts, wrong-property probes, or historical adapters. Canonical completion remains a later, separately declared diagnostic if this unchanged-interface recipe fails—not a second arm in this budget and not an automatic fallback after inspecting scores. Its future interface/locality claims would need their own controls; this design makes no such claim.

## 2. Exact material and optimization

The original seed0/1/2 `teach.json` files have the same SHA-256:
`2d12bb35d44279c3412323472bb716581c9ed57a966bb829290a49c4d799de7c`.

Filter their existing `corpus` list for `view == "memory"`, retaining each selected record, spans, metadata, and relative order unchanged. Require precisely `train-memory-000`…`015`, 16 unique `source-memory-000`…`015` source events, and four targets of each blue/red/green/yellow. There are no new sources, keys, labels, or factual assignments. Keep existing `order` fields; do not rebuild rendered prompts from templates. Seal the new subset artifact and record its mapping to the pinned original file before any training.

Recipe: rank8, alpha16, dropout0.05; same seven projection targets/all layers; lr3e-4, 20 epochs, batch4, grad_accum1, fresh AdamW; full parent LoRA weight warm-start. Preserve frozen Qwen2.5-7B-Instruct snapshot and base inventory, bf16 base, existing adapter dtype behavior, no SVD init, both A/B trainable, max_len512, no packing, no second chat wrap, add_eos=true, same group-shuffle semantics. Optimizer state is not resumed. No arithmetic rehearsal or additional loss term.

Exactly 16/4 × 20 = **80 new optimizer updates per child**, if completed without nonfinite/skipped batches. Each parent already has 80 updates, giving 160 cumulative lineage updates, not a new 80-step fresh-base fit. Do not silently replace 20 epochs with a token-budget match or extend an unsuccessful fit.

### Token/exposure accounting

Counts below derive from original native row audits and the HF capture, not a new tokenizer invocation. Native preflight must reproduce them before launch; a mismatch is a provenance/configuration failure, not permission to alter rendering.

| Scope | Row presentations | Model-input tokens | Supervised color tokens | Supervised EOS tokens |
|---|---:|---:|---:|---:|
| One unique memory row | 1 | 44 = 42 context + 2 target | 1 | 1 |
| One 16-row epoch | 16 | 704 | 16 | 16 |
| One child, 20 epochs | 320 | 14,080 | 320 | 320 |
| All three children | 960 | 42,240 | 960 | 960 |

Unique subset: 672 context tokens, 32 supervised targets, 704 total input tokens. Per child: 13,440 ignored context-token presentations and 640 supervised-token presentations. These are unpadded sequence counts, not GPU FLOPs. Targets remain one native color token plus EOS; causal predictors are positions 41 and 42 for target positions 42 and 43, zero-based.

Original mixed training had 80 rows/epoch (64 arithmetic + 16 memory), four epochs, 80 updates, 18,068 input-token presentations, and 3,648 supervised-token presentations. Its memory component was only four exposures/fact, 2,816 input-token presentations and 128 supervised targets. The new phase adds 20 exposures/fact: **24 lifetime exposures/fact**, five times the original memory exposure added, six times original cumulatively. This is why matching the number “80 updates” does not match memory dose or objective mixture.

## 3. Parent and baseline controls: inherit, do not invent

Original teach parent locations, all beneath `/localhome/local-rohing/astra_diagnostics/`:

| Seed | Relative parent adapter directory | `adapter_model.safetensors` SHA-256 |
|---|---|---|
| 0 | `astra_fundamental_teaching_20260912_attempt1/fit_teach/adapter` | `d73e8578f62de68ed657474c70fc09c09aaad50a4ff11a66773e50fc702163b2` |
| 1 | `astra_fundamental_replications_20260912_attempt1/seed1/fit_teach/adapter` | `97328c5aad9c8df9d98f336e19f2ad4682f4c88e662d61a9a30c3de4c2aed3cb` |
| 2 | `astra_fundamental_replications_20260912_attempt1/seed2/fit_teach/adapter` | `03955472524928e723800074660baac0aac7a4c2e2d8fec74c27b17639726bd2` |

Require complete parent config/manifest/file inventories too; a weight hash alone is not the full provenance contract. Child pre-update inventories must equal parent weights after declared dtype handling. Preserve parents and original readout receipts. A CPU zero-update warm-load regression is a correctness check, not another scientific arm.

The following original 48-case baseline counts were inspected in terminal `reduction.json` files; this bounded design pass is not a new full independent raw-response audit:

| Inherited baseline | ACT correct /32 | PREDICT adherence /32 | Dev memory correct /16 | Memory invalid /16 |
|---|---:|---:|---:|---:|
| Original teach seed0 | 32 | 32 | 4 | 0 |
| Original teach seed1 | 32 | 32 | 7 | 0 |
| Original teach seed2 | 32 | 32 | 3 | 0 |
| Original control seed0 | 32 | 0 | 4 | 0 |
| Original control seed1 | 32 | 0 | 4 | 0 |
| Original control seed2 | 32 | 0 | 4 | 0 |
| Original adapter OFF, one shared capture | 32 | 0 | 0 | 16 |

Primary paired contrasts are child minus its own original teach parent, with per-case gains/losses. Original opposite-behavior controls and OFF are inherited context, **not** matched new memory-dose/interference controls. Do not continue control adapters or regenerate OFF. Reusing one OFF capture across seed tables does not create three OFF replicates.

Exact-training-prefix baseline: SEQ100 original seed0 teach and control both red16, correct4/16; OFF correct0/16, all16 invalid/capped. Seed1/2 exact-prefix baselines are not established here: record **unmeasured**, not red16, 4/16, or zero. Their new endpoint exact-prefix scores can establish achieved acquisition but cannot yield a measured parent→child exact-prefix delta without new parent evaluation. Do not add those extra parent calls in this minimal design.

## 4. Readouts and prospective decision matrix

Recommend the fixed **48 dev + 16 exact-prefix cases for every child**. Although the latter was offered “if needed,” predeclaring all three is cleaner and only 48 additional generations overall; it separates acquisition from transfer without score-dependent missingness. Keep these panels separate. The 48 remain the original 32 arithmetic and 16 memory questions; do not insert exact-prefix cases into that endpoint. All confirmation cases remain untouched, as do unknown-device and new-key probes.

Use unchanged native prompts, greedy temperature0, original readout seed20260912, max_tokens64, and original strict scoring. Report arithmetic correctness and PREDICT-before-ACT adherence separately; report memory validity, strict correct count, full answer distribution, per-color confusion, and per-case parent→child changes on the dev panel. No pooled “overall accuracy” that lets arithmetic hide memory failures. Keep raw requests/responses, actual tokens, identities, timing, and cleanup receipts.

Prospective, descriptive criteria—not a new scientific promotion gate: call exact acquisition strong only at **16/16**; call measured behavior fully retained only if ACT32/32 **and** adherence32/32. Use similarly explicit dev16/16 for complete measured transfer. Lesser gains remain reported as partial rather than relabeled as a pass. These conservative labels avoid a tuned threshold on 16 already-used examples.

| Child outcome | Permitted conclusion / disposition |
|---|---|
| Exact16/16, dev16/16, ACT/adherence32/32 | Strong bounded acquisition + transfer + retention in one adapter; identify which seeds meet all criteria. |
| Exact16/16, dev<16, ACT/adherence32/32 | Acquisition and measured behavior retention; incomplete transfer to the existing dev wording. |
| Exact16/16, behavior below either32/32 | Memory acquisition succeeds but joint retention control fails; report exact behavior losses. |
| Exact<16, dev improves over own parent, behavior retained | Partial binding/transfer improvement, not a strong positive control; preserve endpoint without dose extension. |
| Exact weak/constant, dev weak | This fixed recipe does not establish reliable acquisition; mechanism remains unresolved. |
| Dev16/16 but exact<16 | Surface-dependent outcome; not complete exact-prefix acquisition. Check custody/scoring before interpretation; do not discard either panel. |
| Different seeds land in different rows | Seed-dependent outcomes; no best-seed-only report. One successful seed is an existence demonstration, not consistent three-seed success. |
| Missing/inconsistent captures, invalid lineage, nonfinite fit, budget stop | Operationally incomplete/invalid; not a scientific zero. No hidden retry or replacement seed. |

Do not make this contingent on new HF scoring. Existing HF seed0 logits are prior diagnostic evidence, not child metrics. If a later HF diagnostic is separately selected, use full-vocabulary gold NLL/top1 and candidate mass separately; never substitute candidate-normalized confidence for generated binding accuracy.

## 5. Budget and bounded execution recommendation

Target **at most ~30 A40 device-minutes summed across devices**, not 30 wall-clock minutes regardless of parallelism. Design workload: three 80-update fits, three fixed48 dev readouts, three exact16 readouts: **240 new updates and 192 generation calls**, zero new OFF calls. Per child, native readout inputs are 2,131 + 672 = 2,803 tokens; across three, 8,409. Output ceiling is 64 × 192 = 12,288 tokens; actual outputs must be measured, not assumed from earlier red+EOS outputs.

Observed original worker windows provide plausibility, not a guarantee: original fits were reported around60–73s; the inspected teach48 readouts were97.70/126.78/96.08s; inherited seed0 exact16 teach was about99.20s. Those exclude some full-reservation overhead. The HF audit specifically found64.70s worker versus141.94s full reservation: use full reservation accounting here.

Planning envelope per seed: ~1.5min fit, ~2.5min dev readout, ~2min exact readout, ~2min loading/orchestration/cleanup allowance = ~8min; three seeds ~24min, plus ~6min shared contingency. These are estimates, not measured continuation times or replacements for native lease/deadline rules. If dev and exact captures can share one unchanged backend load while retaining distinct manifests, that saves overhead; do not require a new readout refactor just to realize the saving.

Schedule only on already leased/available allocations and never interfere with Main's repeat-plasticity/two-habit work. Start seed0 to calibrate cost, but do not select whether to run seeds1/2 based on its scientific score. Admit remaining work only if projected full reserved cost plus mandatory cleanup fits the remaining30min and lease bounds. Preserve incomplete work and report missing seeds if the envelope cannot cover all three; do not shorten epochs, pick an intermediate checkpoint, add a retry, lease/extend hardware, or borrow another checkpoint to force completion. Dollar cost is unestablished without rate evidence.

## 6. Implementation handoff boundary

No architecture/thesis/base-model/visibility/benchmark invariant is changed by this proposal. Before a separately requested implementation/run, Main should bind the exact selected design/scope and source subset; verify native token/mask counts, original-parent full-state load, frozen base, fresh optimizer, no confirmation access, finite80-update accounting, parent immutability, strict endpoint compatibility, and cleanup/custody tests under existing standing authorization. Log the applicable Builder CPU/provenance checks. This note does not introduce a new independent-review veto or alter the reserved material-change path.

Evidence inspected: `/tmp/astra_prior_memory_comparison_20260912.md`; the prior HF audit/capture; local `astra_fundamental_seed0_terminal_20260912.tgz` and `astra_fundamental_replications_terminal_20260912.tgz` corpora/plans/readout reductions; existing native-token, continuation, and fixed-readout definitions; coordination's SEQ099/100 baseline/cost record. Existing conclusions are reused only within their stated scope.

**Bottom line:** choose memory-only continuation on the unchanged interface, preserve all three original parents and inherited OFF/control baselines, and measure acquisition and retention separately. This can establish a practical single-adapter positive control; it cannot identify interference or dose as the cause, establish latent absence, selective locality, new-fact generalization, or H1/H2.
