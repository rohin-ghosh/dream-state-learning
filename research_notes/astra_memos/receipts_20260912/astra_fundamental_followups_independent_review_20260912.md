# Independent numerical review: fundamental follow-ups, SEQ099/100

Date: September 12, 2026.

## Verdict

**PASS. No required numerical or claim-boundary correction found.** Independently scored all **192 replication outputs plus 48 original-training-prompt diagnostic outputs** from raw responses and source-derived answer keys, without importing or invoking an existing scorer. Also checked the actual inherited 48-call seed0 OFF capture specifically for reuse. This is bounded numerical/custody review, not a parenting, learning-mechanism, or launch ruling.

Only this report was written. No Git, network, GPU/model/tokenizer calls, repository edits, reduction execution/overwrite, or experiment reruns occurred. Main's reported native warm-start 21/21 CPU result is acknowledged but is not evidence for these numerical endpoints.

## Exact evidence roots and integrity

For the relative artifact paths below:

- **R** = `/tmp/astra_fundamental_followup_terminal_20260912/astra_fundamental_replications_20260912_attempt1`
- **M** = `/tmp/astra_fundamental_followup_terminal_20260912/astra_fundamental_memory_trainprompt_20260912_attempt1`
- **S0** = `/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1`
- **C** = `/tmp/astra_fundamental_teaching_corpus_candidate_20260912`

Both supplied archive hashes match exactly:

| Capsule | SHA256 | Regular files compared to extraction |
|---|---|---:|
| `/tmp/astra_fundamental_replications_terminal_20260912.tgz` | `dcd4237dfb54b1def3e4733cadbe29eb0252a6270662e9e869333265ed1bfde5` | 525 |
| `/tmp/astra_fundamental_memory_terminal_20260912.tgz` | `a3c2bc8ba3a97a4f4b7e73f0a818f7b162872675d1fd577bc0ea4be4df5da378` | 143 |

Every archived regular file matches its extracted bytes; neither capsule contains `.safetensors` or `.bin` weights. All seven readout capture manifests match their actual complete file inventories. Plan hashes, reduction-to-capture hashes, individual request/response hashes, request identities, raw response text, and per-call prompt-token inventories agree. Counts are complete, not selected favorable subsets.

## Independent scoring method

Used read-only inline Python standard-library checks; no existing scoring function was called. Reconstructed the seeded source construction separately: Random(20260912), the shuffled lexicographic operand pairs, then the shuffled four copies of each color. All 128 source operand pairs and all 16 color assignments match `C/source_records.json`; the source keys contain exactly four each of blue, green, red, yellow. Candidate source/evaluation files also match their manifest hashes.

For every addition output, recomputed the answer by adding source-record operands, checked that the raw requested operands agree, parsed ACT/PREDICT lines independently, and tested exact action validity, answer correctness, and correct prediction preceding action. For every memory output, derived the key from its original device source record and applied the documented single-color normalization (case/outer whitespace, optional final period), not semantic prose rescue. Compared the resulting flags and expected values against every corresponding reduction row.

The replication request IDs are exactly `eval-addition-000` through `eval-addition-031` and `eval-memory-000-0` through `eval-memory-015-0` in all four cells. Diagnostic IDs are exactly `train-memory-000` through `train-memory-015` in all three states. All use temperature 0, generation seed 20260912, and a 64-token output maximum. No malformed response was mistaken for a missing capture.

## Findings and minimal fixes

### 1. PASS — replication scores and response patterns

| Trainer seed/state | Correct ACT | Adherence | Correct recall | Invalid recall | All 16 recall answers |
|---|---:|---:|---:|---:|---|
| 1 teach | 32/32 | 32/32 | 7/16 | 0 | 11 blue, 5 yellow |
| 1 control | 32/32 | 0/32 | 4/16 | 0 | 16 blue |
| 2 teach | 32/32 | 32/32 | 3/16 | 0 | 14 green, 2 blue |
| 2 control | 32/32 | 0/32 | 4/16 | 0 | 16 yellow |

Every teach addition response has `PREDICT: <sum>` then `ACT: <sum>`. Every control response has `ACT: <sum>` then `COMPUTED: <sum>`. There are zero invalid arithmetic actions. This is an ordering/format habit, not an arithmetic gain.

Correct memory IDs, retained for audit rather than a new endpoint:

- Seed1 teach: `eval-memory-000-0`, `001-0`, `002-0`, `007-0`, `008-0`, `010-0`, `012-0` (all abbreviated suffixes retain the `eval-memory-` prefix).
- Seed1 control: `eval-memory-007-0`, `008-0`, `010-0`, `012-0`.
- Seed2 teach: `eval-memory-003-0`, `004-0`, `011-0`.
- Seed2 control: `eval-memory-000-0`, `001-0`, `002-0`, `005-0`.

Evidence: `R/seed1/readouts/teach/run/data/calls/0000.response.json` through `0047.response.json`, and the corresponding seed1 control / seed2 teach / seed2 control directories; their `plan.json` and `reduction.json`; `C/source_records.json` and `C/eval.json`. The actual first teach response is `PREDICT: 24\nACT: 24`, matching source operands 5+19, not a copied unverified reduction key.

Memo agreement: `research_notes/astra_memos/ASTRA_FUNDAMENTAL_REPLICATION_TERMINAL_2026-09-12.md:14`, `:26`, and `:32`. Required fix: none.

### 2. PASS — seed0 exact-training-prompt diagnosis, not a replacement endpoint

Teach and control each answer **red on all 16 original training questions**, yielding **4/16**, no invalid responses. Correct IDs in both are `train-memory-006`, `train-memory-009`, `train-memory-013`, `train-memory-014`. OFF yields **0/16**, all 16 invalid prose responses, each with exactly 64 returned token IDs and `finish_reason="length"`.

Independently verified that each diagnostic rendered prompt equals the actual exported training-context span, not merely a paraphrase or similar candidate description. Matched its source record and target color against both training arms; the replication corpus bytes in turn equal the original seed0 corpus bytes. The diagnostic requests contain the question, not the device-color answer fact. Seed0 adapter identities/file hashes in the memory plans match the original seed0 readout identities, rather than the newly fitted seed1/2 adapters.

Evidence: `M/teach/plan.json`, `M/control/plan.json`, `M/OFF/plan.json`; all their `run/data/calls/*.request.json` and `*.response.json`; `S0/teach.json`, `S0/control.json`, and original readout plans.

This contradicts a **paraphrase-only explanation of seed0's observed failure**, but does not prove absence of latent binding or identify its cause. Constant red earns four balanced keys without item-specific retrieval. Absolute +4 over capped-invalid OFF is not demonstrated binding. The diagnostic does not establish failure at every dose/seed.

Memo agreement: `research_notes/astra_memos/ASTRA_FUNDAMENTAL_MEMORY_TRAINPROMPT_TERMINAL_2026-09-12.md:3`, `:9`, and `:15`. Required fix: none.

### 3. PASS — matched training, shared data, one adapter, explicit OFF reuse

- Both replication plans preserve the original seed0 config exactly except `seed=1` or `seed=2`; source/model inventories and both corpus file hashes match seed0. These are trainer seeds affecting initialization/dropout/order, not new dataset seeds or merely optimizer-internal randomness.
- All four exported corpora have 80 rows; every target was independently checked against source operands/colors. Teach/control per-row audited native input and target lengths match. Their sums are **4,517 total model-input / 912 supervised-target tokens per epoch**, including EOS (3,605 context + 912 target), not 4,517 context tokens plus a separate 912-token input charge. Target subdivisions are 880 arithmetic and 32 memory per epoch.
- All four manifests show four epochs, 80 microbatches/optimizer updates, 18,068 total input tokens, zero nonfinite batches, and the expected matching config. Native verified receipts record 3,648 target tokens across the four epochs per fit. Across these four new fits: 72,272 total input / 14,592 target tokens. Tokenization itself was not rerun locally; training counts are independently summed from the native per-row audit and cross-checked against manifests, not recounted using a guessed tokenizer.
- Each combined behavior+memory readout has a single arm-specific adapter identity, matching the corresponding fit's native verified inventory throughout all 48 requests. No separate behavior and memory adapters were substituted. Capsule weights are absent; these native weight inventories are attributed checks, not local rehashes of unavailable weights.
- The replication plans bind actual seed0 OFF plan SHA `e275ebf4f27f0a3b35fd87ac983843e9edcf73e1239bd01be60f4952f3845fc8`. Independently checked that its cases, requests, base-model inventory and generation settings match replication. Its existing raw capture gives 32/32 correct ACT, no PREDICT/adherence, and 16 capped-invalid memory responses. Its reduction SHA is `23a3e920b9e18c8bf6294a199193151169cfa18da5158d59691e42a0c8c92a3e`. There are **zero new replication OFF calls**; the separate memory diagnostic legitimately has 16 new OFF calls on different, training-form prompts.
- The other **64 evaluation/confirmation IDs do not occur in any of the 240 new requests**. Training-form diagnostics do not silently replace those IDs or reopen the fixed development endpoint.

Evidence: `R/seed1/plan.json`, `R/seed2/plan.json`, each seed's `teach.json`, `control.json`, `fit_teach/adapter/train_manifest.json`, `fit_control/adapter/train_manifest.json`, `fit_*/verified.json`, and `readouts/*/plan.json`; `R/readout_main_release.json`; `S0/readouts/OFF/run/data/calls/`; `C/eval.json`.

Memo agreement: replication memo `:20`, `:26`, `:41`; memory memo `:23`. Required fix: none.

### 4. PASS — native costs, caps, and supervision are separated

Recomputed inference usage from lengths of actual returned prompt/output token-ID arrays and call-end minus call-start timestamps; all per-cell totals match native usage receipts and reductions.

| New readout group | Calls | Actual input | Actual output | Output cap, not usage | Generation seconds | Supervised seconds |
|---|---:|---:|---:|---:|---:|---:|
| Seed1 teach | 48 | 2,131 | 472 | 3,072 | 20.749504 | 126.780885 |
| Seed1 control | 48 | 2,131 | 472 | 3,072 | 21.038978 | 97.348627 |
| Seed2 teach | 48 | 2,131 | 472 | 3,072 | 19.984317 | 96.084658 |
| Seed2 control | 48 | 2,131 | 472 | 3,072 | 20.823823 | 105.192850 |
| **Replication total** | **192** | **8,524** | **1,888** | **12,288** | **82.596622** | **425.407021** |
| Seed0 training-prompt teach | 16 | 672 | 32 | 1,024 | 2.052543 | 99.199165 |
| Seed0 training-prompt control | 16 | 672 | 32 | 1,024 | 2.005795 | 100.609645 |
| Seed0 training-prompt OFF | 16 | 672 | 1,024 | 1,024 | 28.921565 | 140.172172 |
| **Training-prompt total** | **48** | **2,016** | **1,088** | **3,072** | **32.979904** | **339.980983** |

Four fit supervision windows sum **268.510038 s** (85.396028, 70.903244, 68.716418, 43.494348); additional-seed fit+readout supervision is **693.917059 s**. Both follow-ups together add **1,033.898042 s** supervision. Independently summed inherited seed0 fit/readout supervision is 476.237894 s; cumulative sum is **1,510.135936 s = 25.168932 A40-minutes**, leaving **64.831068** of the initial 90 minutes **on that supervision accounting only**.

The four outer replication readout reservations separately recompute from UTC launch/release timestamps to **1,920.821997 s**. They include audit/idle delay and are neither active compute nor interchangeable with supervised windows. No monetary price is inferred. Original OFF usage is not newly charged as replication generation. Native token/text decoding audits remain attributed to native reducers; this independent audit counted returned IDs and checked stored text/hashes without loading a tokenizer.

Evidence: all seven `run/data/calls/`, `run/data/usage.json`, `reduction.json`, and `run/worker/supervision.json`; `R/fit_main_release.json`, `R/readout_main_release.json`, `M/main_release.json`; `/tmp/astra_fundamental_followups_main_analysis_20260912.json`.

Memo agreement: replication memo `:65`; memory memo `:40`. Required fix: none.

### 5. PASS — custody, preserved first reduction, and release evidence

- All 12 replication-readout source pins match files in `/tmp/astra_fundamental_readout_source_a9a7c679.tgz`; all 13 diagnostic source pins match `/tmp/astra_memory_source_255ae188.tgz`. Replication helper SHA matches `fcd3dd3870a8b118df7b55eb987b860a90903b81ddaf5f17871f3ca98c2419e0`. This checks pinned local bytes, not Git history or authenticated model origin.
- Native fit verified inventories agree with corresponding readout plans/reductions, and available adapter metadata files independently rehash to those inventories. Base inventories match original seed0 pins. Absent base/adapter weight bytes cannot be independently rehashed on this VM; the memos appropriately attribute those checks to Main/native execution.
- `R/seed1/readouts/teach/reduction.json` has exactly **`c216db3b54fa91777b56da99a5cca53b7226f90378a49a19111c8f4bf491e9a3`** in archive, extraction and release record. It passes the same independent 48-output scoring and capture validation as the others. `/tmp/astra_finish_fundamental_replications_20260912.py` places reduction before the full-free guard; `/tmp/astra_finish_fundamental_replications_resume_20260912.py` explicitly pins/reuses that reduction and rechecks source/model/adapter/capture/supervision rather than reducing that cell again. The earlier guard interruption and historical no-rerun account are Main's operational attribution; the preserved bytes and supplied recovery logic corroborate it. No claim is made that a final capsule alone proves every historical filesystem event.
- All seven readout supervision receipts report successful zero return code, owned-group cleanup, GPU-process absence and verified release. All seven backend cleanup receipts report `closed=true`, `error=null`. All 11 fit/readout/diagnostic release XML snapshots contain zero GPU process entries. Final readout/diagnostic snapshots cover seven distinct GPU UUIDs/devices 0–6.
- Main's full-release records: GPU0 18:18:29.143702; GPU1 18:18:51.950050; GPU2 18:19:16.492489; GPU3 18:19:42.013412; GPU4 18:20:23.969200; GPU5 18:20:48.406036; GPU6 18:21:19.567197 **UTC on September 12, 2026**. Four fit releases preceded these at 18:05:10–18:05:40 UTC. This is recorded release evidence, not a live occupancy assertion by this reviewer.

Evidence: `R/readout_main_release.json`, `R/fit_main_release.json`, `M/main_release.json`, corresponding `main_release.xml`/`fit_*_main_release.xml`, `run/worker/supervision.json`, `run/data/backend.cleanup.json`, and the exact preserved reduction path above.

Memo agreement: replication memo `:48`, `:54`, `:60`, `:72`; memory memo `:31`, `:48`. Required fix: none.

## Scientific boundary

The results support a limited taught output-order habit across three trainer seeds on shared development data. They do not demonstrate improved arithmetic, conditional prediction/cognition, parenting, H1/H2, reliable memory binding, generalization to new datasets, or a successful continued-update mechanism. Recall differences teach-minus-control are 0, +3, -1 across seeds0/1/2; do not promote seed1 alone or call all teach responses constant. Seed0's constant collapse on training-form prompts weakens a paraphrase-only explanation, not every possible latent-memory account. No deranged-binding control or causal isolation of memory-token dose is supplied here.

The newly available SEQ099/100 memos preserve these limits. Their reviewed hashes:

- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_REPLICATION_TERMINAL_2026-09-12.md`: `2568ebd3dc7e8c67edc66a67c6c449c320aade1cad5106758b9e3cafb9698504`
- `research_notes/astra_memos/ASTRA_FUNDAMENTAL_MEMORY_TRAINPROMPT_TERMINAL_2026-09-12.md`: `aa86f83357b05fe930d67047a192342bf550225bdb0639554690029b7c7411bc`
- Main analysis `/tmp/astra_fundamental_followups_main_analysis_20260912.json`: `f10214310a4028803ebd6cbca3cbc309af2a0b829324b287c00604fa00af69bf`

**Required minimal fixes: none.** Main may update the memos' pending-review status to reference this bounded PASS; no favorable subset, endpoint replacement, additional model request, or reduction overwrite is needed.
