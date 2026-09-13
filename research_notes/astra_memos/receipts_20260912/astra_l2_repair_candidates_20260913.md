# L2 keyed-acquisition repair candidates — bounded evidence comparison

2026-09-13 UTC. **EDITSTOP. Recommendations only; no implementation or experiment authorization.**

## Answer

There is **no evidenced guaranteed repair** for L2 keyed acquisition in the recovered history. The strongest causal historical distinction is optimizer seed, not hardware. First consume Main's already-owned seed contrast and Descartes's already-owned access results; do not create a competing probe or launch path. If exact-training-prefix keyed acquisition remains weak, the smallest additional implementation hypothesis is **LR-only 3e-5 versus 1e-4**, retaining the same admitted child bytes, masks, seeds, rank and exposure. The historical positive used 1e-4, but did not isolate LR: this is a bounded contrast, not a proven fix.

Only two candidates are listed below. The first reuses work owned elsewhere; the second is conditional future work. Neither changes the frozen base/LoRA-only, provenance, visibility, parent-blindness, or scientific-claim invariants. Neither may mutate the completed root or silently override its frozen recipe/protocol.

## 1. What L2 actually trained

I read the archived root's `plan.json`, all three `training.json` / adapter `train_manifest.json` files, and the exact frozen source under `/tmp/astra_l2_native_source_20260913_attempt1/`. The four source hashes match `/tmp/astra_l2_public_record_spec_20260913_attempt1.json:1`. This distinction matters: the current working runtime has subsequently gained optional learner-seed wiring; it is not the bytes that executed seed0.

Actual path:

- Core `organism_v6/l2_public_record_dev.py:345` checks an exact child action record against its preceding public SUCCESS/FAILURE receipt. Unsupported, malformed, or missing records are rejected, not rewritten. `compile_corpus` at line 405 accumulates those rows; `training_items` at line 451 exposes the **entire unchanged child action** as the target.
- `action_prompt` at line 271 constructs a public two-action law, both legal action names, and an opaque key. Training/wake ask `Key <key>: choose the successful action.`; reporting asks `For <key>, which listed action succeeds?`. Training has **no source outcome or source record in its prompt**. There is therefore both an acquisition requirement and a wording-transfer boundary.
- Frozen runtime `gpu/astra_l2_public_record_dev.py:390` renders the real Qwen chat template, checks full-token equality, masks system/user/padding/template-tail tokens, and supervises raw child target plus one EOS. It rejects actual truncation. `fit_stage` at line 484 explicitly cold-loads the frozen base and creates a fresh optimizer for each fit; later fits use cumulative old+new records, not warm-started adapters.
- Recipe at frozen runtime line 40: rank8/alpha16/dropout0.05, all seven projections, AdamW, LR3e-5, 20 epochs, batch8/gradaccum1, BF16, max_len1024, no packing, seed0. `organism_v6/train_adapter_v3.py:807` takes the model's masked token-average `out.loss`, backpropagates, and steps AdamW; it has no L2-specific keyed-position loss or selection rule.

| Executed fit | Admitted rows | Optimizer updates | Supervised tokens per corpus pass | Total token presentations | Final recorded loss |
| --- | ---: | ---: | ---: | ---: | ---: |
| fit1 | 8 | 20 | 104 | 23,540 | 0.0502016 |
| fit2_PROMOTE | 16 | 40 | 208 | 47,140 | 0.0507784 |
| fit2_SHADOW | 16 | 40 | 208 | 47,140 | 0.0507784 |

Each admitted row is presented 20 times in each fit containing it. The cumulative second fits restart from base, so do not describe an old key as receiving 40 persistent sequential updates in one continuing adapter. All manifests report zero target/context truncation. Main's collection records 128 calls, 3 fits, 100 updates and 11 completed stages; `endpoint.native_verified=false` remains the deliberate pure-core scope.

### Why the small loss does not settle acquisition

The **stored native encoding**, not a new tokenizer/model call, contains four targets of each action. The two supervised sequences have 14 and 12 tokens including EOS, with a shared first two tokens `[3397, 62]`; they first diverge at the third target token (`20` versus `22`). Across eight rows there are 104 supervised positions but only eight first action-identity branch positions. If that binary branch were uncertain at 1/2 and the other tokens perfectly predictable under teacher forcing, the average CE would be `8*ln(2)/104 = 0.053319`. The actual 0.05020 is near that illustrative scale.

This is a **loss-dilution explanation consistent with weak binding**, not a recomputed model probability, proof of chance behavior, or diagnosis of a tokenizer bug. Descartes owns the actual decision-position/access measurement. No access-probe code was run or duplicated here. The existing full-byte/token checks argue against casually blaming dropped targets or EOS.

## 2. What the inherited positive really establishes

### SEQ056/057/058: attributed terminal audit, not newly replayed

`research_notes/2026-09-11_cross_node_effect_adversarial_audit.md:194` reports matched seed1 terminal F_r16k16 results across machines, canonical result hash `9aadd56616ff94812cb88213935dea3a073759ed15fbe262f7f1ed1e54b4a9ce`, pooled trained-frame probability 0.830, owner/lookalike contrast 2.013, and spill 0.392. The seed0/seed1 distinction supersedes the earlier apparent node effect. These original matched-seed payloads were **not** freshly available/rehashed in this pass; their numbers remain attributed audit evidence. Spill exceeded the historical 0.03 criterion: do not call this a qualified selective-memory solution.

### Later local raw evidence: training seed2, not that seed1 repeat

Capsule: `/tmp/astra_A1A2_banks_20260912T0800Z/`; run: `runs/astra_A1_memory_dose_S1_F_r16k16_ts2_20260912/`.

I rehashed bank1/bank2 evaluation JSONs, bank1 `train_meta.json`, and captured `memory_dose.py` against the capsule's actual `CAPTURE_MANIFEST.json` entries. All match. The bank1 corpus matches `SOURCE_REUSE_RECEIPT.json`, not the capture manifest. That receipt consistency is not a fresh remote-source authentication.

The actual bank1 training metadata says rank8/alpha16/dropout0.05, seven projections, **LR1e-4, 3 epochs, batch4, max_len512, seed2**, 13,016 items, 9,762 optimizer steps, 710,916 supervised-token presentations, no truncation. Its model field is a Qwen model name, **not an authenticated equality proof to L2's exact base snapshot**.

The actual owner T3Z2 has **256 items / 16 distinct prose contexts**, hence 768 presentations over three epochs. One stored item is:

```text
context: I wiped the dust off owner T3Z2's car and the green finish came up clean.
target:  Owner T3Z2's car is green.
chat: false
mask_context: false
```

Captured source `experiment_source/f2e5b65e9c5dc3f7b7cdf15cb1b97b114ad4994d/organism_v6/memory_dose.py:308` defines the canonical sentence; `:1033` renders perception prose plus that sentence; `:2459` jointly tokenizes context+target and supervises all tokens for these unmasked items. The corpus contains 5,376 facts, 4,096 color fillers, 2,200 other fillers and 1,344 lessons. **F_r16k16 is not 16 repetitions of L2's eight rows.**

The captured `HFScorer` at line 2307 uses the base with adapter disabled for OFF and mounted PEFT for ON. Readout is teacher-forced bare canonical continuation, not L2's strict chat action generation. Recomputed from dose16 raw cue arrays:

| Bank / cue | N | Conditional gold probability OFF → ON | Candidate mass OFF → ON |
| --- | ---: | --- | --- |
| 1 frame | 16 | 0.240929 → 0.865241 | 0.010230 → 0.995341 |
| 2 frame | 16 | 0.254242 → 0.833422 | 0.007354 → 0.997976 |
| 1 lookalike frame | 16 | 0.246744 → 0.729088 | 0.008874 → 0.994807 |
| 2 lookalike frame | 16 | 0.253358 → 0.492734 | 0.009723 → 0.997575 |
| 1 wrong-property bicycle | 16 | 0.242945 → 0.820226 | 0.004561 → 0.997355 |
| 2 wrong-property bicycle | 16 | 0.262112 → 0.859424 | 0.004504 → 0.998943 |

Conditional probability is `p_raw[gold]/mass`, not full-vocabulary accuracy. Strong wrong-property/lookalike responses are precisely why these positives cannot certify selective usable memory. The capsule explicitly labels the facts researcher-planted synthetic material: no inherited adapter or planted answer is eligible for L2 child-record training.

Later exact-chat diagnostic `/tmp/astra_exact_train_root1_terminal_20260912/root1/supplementary_report.json` hashes to the value in `COMPLETED.json`; it remains an `OPTIMIZATION_INCONCLUSIVE` lineage with `binding_ok=false`, not a stronger verified positive. I inspected its stored report, not a fresh reduction or native replay. Its existence does not justify rescuing current L2 by analogy.

## 3. Candidates, contrasts and limits

### Candidate 1 — consume the existing learner-seed contrast; no new sidecar work

**Evidence strength:** strongest historical isolated distinction, but not yet an L2 repair result. The seed-repeat audit supports optimizer-seed sensitivity; it does not support changing world truth or selecting only the winning seed.

**Reuse:** current `gpu/astra_l2_public_record_dev.py:61`–`:76` validates optional learner seeds 0/1/2 and constructs `fit_config`; existing handoff `/tmp/astra_l2_seed_parameterization_handoff_20260913.md:1` binds this to initialization/dropout/shuffling while leaving prompt bytes, world seeds, engine seed, masks and recipe fixed. Read this wiring rather than inferring it from filenames. Main already owns launch preparation; this note requests **no duplicate roots or launches**.

**Precise contrast:** read Main's predeclared seed0/1/2 results with the same world, canonical child-record admission, LR and 20/40/40 update schedule. First-wake base captures should be held equal or their equality checked; any later branch-specific material differences remain part of the induced loop, not evidence of a fixed-corpus optimizer effect. Use Descartes's access result to distinguish failure to acquire an exact key from transfer/mount failure.

**Budget:** zero additional jobs, fits, model calls or changes requested by this candidate. Existing limits remain per root: 128 calls, 3 fits, 100 updates, 5400-second controller / 600-second fit ceilings. Do not multiply them into a new allocation here.

**Claim/stop:** if results are heterogeneous, report seed sensitivity and every seed, not repaired general learning. If exact-prefix access is strong but wording-transfer access is weak, do not call for a larger write dose. If all already-planned seeds show weak exact-key acquisition, candidate 2 becomes a reasonable small next contrast; no automatic retry follows.

### Candidate 2 — LR-only diagnostic on the preserved first-fit corpus

**Evidence strength:** historical-recipe-supported hypothesis, **not an isolated historical LR success**. Change only LR3e-5 → 1e-4; no rank, corpus, seed, prefix, mask, EOS, optimizer, batching or exposure change. This is the smallest additional recipe edit supported by a concrete positive write path, not proof that LR caused its success.

**Reuse:** the already-pinned fit1 `training.json` (eight exact child rows), `encode_training`, `TrainConfig.lr`, and `run_training`; no new trainer, loss function, data generator or guard. Existing runtime intentionally hard-binds `RECIPE`, manifest equality and protocol pins, so **do not monkeypatch it or reuse an old root/plan**. Any later authorized variant needs a new explicit configuration/protocol binding by Main. This note changes none.

**Precise contrast:** two cold-base, fresh-optimizer fits over that identical eight-row corpus: LR3e-5 control versus LR1e-4 intervention, both predeclared learner seed0 and 20 epochs. Keep current source-withdrawn chat target+EOS representation. OFF and wrong-key/branch evidence come from the already-owned access methodology; do not treat candidate-mass gains or final-loss decreases alone as keyed acquisition. No label, evaluated answer, or readout output may feed the corpus or tune the recipe.

**Proposed fit ceiling, not an allocation:** 2 fits × 20 updates = **40 updates**, 160 row presentations and 2,080 supervised-token presentations per fit (4,160 total); no second wake or second sleep. Reuse 600 seconds maximum per fit with no retry/checkpoint selection. This sidecar allocates **zero new generation/scoring calls**: Main/Descartes must explicitly bind any subsequent evaluation to their existing method and finite budget before execution. Do not imply that old seed0 hardware/time is a matched contemporary control merely to save a fit.

**Claim/stop:** this can establish at most a seen-key, fixed-corpus LR sensitivity effect. It cannot claim completed L2, persistent multi-sleep retention, autonomy, H1/H2, or native endpoint verification. A negative contrast stops this hypothesis; do not escalate to a dose/rank search without a new decision. This one-sleep diagnostic is not a replacement for the accepted 11-stage root.

## 4. What not to import as a repair

- Do not copy historical canonical sentences, expose the successful label in a training prefix, unmask teacher/process text, or shorten/relabel the public keys/actions. Those would change the information/data/benchmark contract, not repair the current writer. Rewriting an action-only child record into a teacher-authored key–answer sentence violates the exact-child-target provenance rule. A genuinely child-authored key-bearing representation would need a separate declared recording/admission protocol; it is not an available drop-in reuse path.
- Historical canonical continuation and prose diversity are useful explanations for why the old result is not a parity promise, **not causal evidence for a prompt-only fix** when exact-key acquisition itself is weak. Do not bundle 16 forms, 768 presentations, a 13k-item corpus, different masking, higher LR and a new readout into one purported minimal repair.
- Do not add decision-token-only supervision, warm starts, larger rank or weight merges here. The current target+EOS mask and cold-base cumulative-refit contract are explicit. The low-loss arithmetic motivates reading Descartes's results, not replacing the loss or omitting child bytes. Current seed wiring already exists; do not duplicate its implementation or Main's prep.

## Evidence pins and remaining gaps

L2 archive custody was previously accepted; this pass only reads selected members and frozen source, not a second 243 MB custody scan. Relevant pins:

| Evidence | SHA256 |
| --- | --- |
| Executed frozen L2 runtime | `213c2a2f508815eef752c72424f5dca64b76c9edb963f7ed6f68d5522c18853e` |
| Current seed-aware runtime observed | `d1965ddc571ec393ef0ec656eda8556b3db91d7de81fafa87310900706d96a3d` |
| L2 core | `0bb33988f003a0111e14cdfb53b3dc86a695e8e20656c90e71cfadb5ad28d352` |
| Shared v3 trainer | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |
| Archived fit1 training.json exact bytes | `fefc6fc7f144eddf23f46a1402a7e92443fc53e61dd5f6e542a702eef1af1f25` |
| Archived fit1 train_manifest.json exact bytes | `fc336839ca5a8d1b63d17495c96fe762515732c51f9a5876b8d773825e7abb8f` |
| Captured historical memory_dose.py | `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3` |
| Historical bank1 eval | `ea6f61c8f112212f4becd541c67fa842218682cc4fc693d26bbd6b459b8d4e08` |
| Historical bank2 eval | `08dd3b9c91ad938d8f27f8afe42e495d4c193424fa748a00c9942f0f8524f3a1` |
| Historical bank1 train_meta.json | `a3fb777b64916779fdc7bc21332825d080414460c99a255f79fb4d698066c5a2` |
| Historical bank1 corpus | `860a67809ac67e27c850d5f1f6bd29a1256a747aa5b46c15920791b345280e96` |
| Later exact-chat supplementary report | `5b349b1b4742f061f0c884ef37b7c4f3478845d46b5f27424c97237d6d492fc2` |

Raw gaps: no original SEQ056/057 adapter rehash/replay here; no authenticated cross-era base equality; no historical LR-only or dose-matched L2 comparison; no full later exact-chat reduction; no new current keyed-access result or seed1/2 outcome examined. The corpus/manifest receipts are local custody evidence, not a new independent remote observation. Neither proposed candidate is a verified remedy. The historical locality failure and present pure-core `native_verified=false` remain intact.

Work began 06:28:46 UTC, within an approximately eight-minute local-only timebox. Commands were bounded `rg`/`sed`/`diff`/filesystem reads and standard-library JSON/tar/hash inspection; raw historical cue averages and the illustrative CE expression were computed without importing model code. No tests/framework, Git, GPU, network, remote reads, launches, archive extraction, source/manuscript edits, or access-probe execution. Only this new document is written; Main owns all subsequent decisions.
