# Fundamental teaching seed 0 — independent numerical review

September 12, 2026, approximately 17:57 UTC.

## Verdict

**PASS for the bounded seed-0 development metrics, source-derived answer keys, matched-training receipt counts, fixed case selection, and archived custody consistency. No required numerical correction.**

All 144 raw outputs independently reproduce the reported endpoints: all three states have 32/32 correct addition actions; teaching has 32/32 format adherence versus control/OFF 0/32; both trained states answer **red on every memory case**, obtaining 4/16; OFF has 16/16 invalid memory responses and 0/16 correct. **Memory binding is not demonstrated.** The absolute trained-versus-OFF +4 matches a constant-color format-collapse baseline, not evidence of device-specific retention.

An additional important descriptive limit is verified: **all 16 OFF memory responses hit the 64-token length cap**. Their recorded validity is correctly zero under the fixed endpoint, but this does not establish absence of latent memory or what an uncapped answer would have been. No response repair, extension, exclusion, or new endpoint is proposed.

No GPU/model calls, network, Git, repository/code edits, or existing scorer execution were used. Independent arithmetic, parsing, JSON/hash comparisons, and timestamp calculations used only the supplied local evidence. The only output written is this requested `/tmp` report.

## Evidence identity and notation

- Capsule: `/tmp/astra_fundamental_seed0_terminal_20260912.tgz`.
- Independently verified SHA256: **`d8f343979f10d358f11ed21fb7896a462b88cfd5d833fee2bf0dab340f19b082`**.
- Every one of its **373 file members** matches the provided extracted copy byte-for-byte at `/tmp/astra_fundamental_seed0_terminal_20260912/`.
- **R/** below abbreviates the extracted root `/tmp/astra_fundamental_seed0_terminal_20260912/astra_fundamental_teaching_20260912_attempt1/`, equivalently the same member root in the capsule. JSON references mean the named file and JSON field; raw request/response files are single-line receipts.
- Fit plan SHA256: `d5a3d0297290184061b5cfcc3bf7fa5ba36a5995fbaedb021df464be7879ec5e`.

| State | Independently verified reduction SHA256 |
|---|---|
| OFF | `23a3e920b9e18c8bf6294a199193151169cfa18da5158d59691e42a0c8c92a3e` |
| teach | `98a95c19ceb4fe305dc5282b49442ffc75fe9ccfc44298a11957adbe4b0cac82` |
| control | `db1bc28b08c9be7929c98fc8c88011886bfb6268f12ac6962d1b8e60967deee7` |

These match `R/readout_main_release.json`, `cells.<state>.reduction_sha256`.

## 1. Independent source-record derivation and fixed case IDs

I did not treat the stored `expected` fields or existing scorer as the sole truth:

1. Read all **145 source records** in `R/candidate/source_records.json`: 128 integer-addition records, 16 device/color assignments, and one closed-log inventory.
2. Recomputed every source addition as `left + right`; all stored sums agree.
3. Re-derived **all 112 evaluation answer keys** using their original `source_event_ids`. Addition contexts match the source operands; memory questions name the linked device and use its recorded color; all unknown-device cases refer to devices absent from the closed inventory. Every independently derived key equals the archived evaluation key.
4. Confirmed the readout plans in all three states preserve the exact original case objects from `R/candidate/eval.json`, not merely matching labels or regenerated replacement questions.

The original ordered development IDs are:

- `eval-addition-000` through `eval-addition-031`, in numerical order;
- then `eval-memory-000-0` through `eval-memory-015-0`, in numerical order.

These map identically to raw call IDs **0000–0031** and **0032–0047**, respectively, in all three states. The same list agrees with `R/plan.json` `eval_dev_ids` and each readout plan's `cases`/`requests`.

The remaining **64 confirmation cases** consist of 32 other addition cases, 16 second-phrasing recall cases, and 16 unknown-device cases. None appears among the **144 actual readout requests**. The confirmation registry exists in the CPU-authored candidate files; this is a verified absence of confirmation model requests in the supplied run, not a claim that those bytes are inaccessible to humans or absent from every possible external history.

Supporting files: `R/candidate/source_records.json`, `R/candidate/eval.json`, `R/plan.json`, and `R/readouts/{OFF,teach,control}/plan.json`. The selected source implementation is also explicit at `organism_v6/fundamental_teaching_readout.py:19` and line 62, but was read, not executed.

## 2. All 144 raw outputs — independently recomputed

For each raw request, I checked original case ID, exact case-context prompt, temperature **0.0**, seed **20260912**, and **64-token** cap. The rendered prompt is exactly that context inside the same Qwen system/user/assistant wrapper. It contains no appended answer, worked example, or request to emit a prediction. Corresponding native input-token arrays are identical across the three states.

I parsed the raw output directly, independently calculated the addition answer from its source operands, counted/ordered the ACT and PREDICT lines, and separately normalized the memory answer against the four recorded color labels. All stored raw text, keys, correctness, adherence, validity, and aggregate counts agree.

| State | Correct addition action | Invalid action | PREDICT-before-ACT adherence | Correct memory | Invalid memory | Observed memory outputs |
|---|---:|---:|---:|---:|---:|---|
| OFF | 32/32 | 0/32 | 0/32 | 0/16 | 16/16 | All invalid prose, each length-truncated at 64 tokens |
| control | 32/32 | 0/32 | 0/32 | 4/16 | 0/16 | `red` on all 16 |
| teach | 32/32 | 0/32 | 32/32 | 4/16 | 0/16 | `red` on all 16 |

For every arithmetic case, with independently computed sum `n`, the exact raw patterns are:

- OFF: `ACT: n`
- control: `ACT: n` followed by `COMPUTED: n`
- teach: `PREDICT: n` followed by `ACT: n`

Thus addition correctness is already saturated in OFF. Teaching changes the toy output sequence/label order; it does not improve this measured arithmetic endpoint. A correct number emitted before ACT on a visible addition problem is not evidence of prediction intelligence, calibration, uncertainty handling, or a live parent/child learning loop.

### Why the memory +4 does not show binding

The source assignments contain **four devices of each color**. The red devices are **device-006, device-009, device-013, device-014**. Those are exactly the four correct cases for both trained states:

- `eval-memory-006-0` → raw call `0038`
- `eval-memory-009-0` → raw call `0041`
- `eval-memory-013-0` → raw call `0045`
- `eval-memory-014-0` → raw call `0046`

All other devices also receive `red`. This result is completely explained by a constant valid-color response, with no observed device-to-color discrimination. The teaching-versus-control memory contrast is zero. OFF's invalid, length-capped prose makes its strict complete-answer score zero; the trained +4 should therefore be described as a **format/constant-response artifact relative to that OFF endpoint**, not selective memory acquisition or retention.

Evidence: all **R/readouts/<state>/run/data/calls/0000–0047.response.json**, `response.text`, `finish_reason`, and `output_token_ids`; their corresponding requests; `R/readouts/<state>/reduction.json` `rows` and `counts`; and the original source-record device assignments. In both trained states every memory response stops normally at two native output tokens; all sixteen OFF memory responses instead report `finish_reason: length`, with 64 output tokens.

## 3. Actual fitted material and matched dose — PASS

The fitted corpora are **R/teach.json** and **R/control.json**, not the unrendered candidate prototype files. This distinction matters:

- `R/candidate/train_control.json` preserves the earlier **RESULT** variant and its pending native-token status.
- Native preparation selected the predeclared **COMPUTED** variant; `R/plan.json` records `selected_control_label: COMPUTED`.
- The actual `R/control.json` targets and all trained control arithmetic outputs use **COMPUTED**. This is not an inconsistency or retrospective output repair.

Independently checked all **80 paired actual training rows**:

- 64 addition rows and 16 memory rows per arm;
- identical row/group order, source-event IDs, and context bytes between arms;
- only target spans are marked supervised; context spans are unsupervised;
- each teaching arithmetic target is source-correct `PREDICT: n` then `ACT: n`;
- each control arithmetic target is source-correct `ACT: n` then `COMPUTED: n`;
- memory targets are identical between arms and match the recorded device/color assignments.

Both native row-audit lists contain all 80 actual case IDs in the same order. Independently summing those per-row counts gives the following, agreeing with both trainer manifests:

| Quantity | teach | control |
|---|---:|---:|
| Encoded rows / epoch | 80 | 80 |
| Native input tokens / epoch, context + target | 4517 | 4517 |
| Native supervised target tokens / epoch, including EOS | 912 | 912 |
| Native context tokens / epoch | 3605 | 3605 |
| Epochs completed | 4 | 4 |
| Input-token passes across training | 18068 | 18068 |
| Target-token passes across training | 3648 | 3648 |
| Micro-batches / optimizer updates | 80 / 80 | 80 / 80 |

The token counts also match **per row**, not only in aggregate. Batch size 4, gradient accumulation 1, 80 rows, and four epochs give 80 updates per arm. Both manifests record seed 0, rank 8, no skipped rows, no splitting/truncation/token dropping, and one-item-per-sequence packing. All corpus hashes bind to the actual fitted files; each fit result embeds the same manifest as the adapter metadata file.

**Attribution limit:** I independently summed the recorded native per-row counts and checked all corpus/manifest bindings. The capsule does not contain a complete local tokenizer/model installation or raw training token-ID arrays; I did not independently retokenize the training corpora. Native segmentation/encoder correctness remains attributed to the recorded native audits. Readout tokens, in contrast, were directly recounted from the archived native token-ID arrays.

Supporting files: `R/plan.json` `tokens`, `row_audits`, `corpus_sha256`, and `config`; `R/teach.json`; `R/control.json`; `R/fit_{teach,control}/adapter/train_manifest.json`; `R/fit_{teach,control}/result.json`. Training and target token passes are different denominators; targets are part of inputs and must not be added to inputs as a separate consumption total. Equal token budgets also do not imply equal gradients.

## 4. One adapter per arm covers behavior and memory — PASS

All 48 requests within each trained state, covering both arithmetic and memory, record the **same adapter path and hash pair**. There is no behavior/memory adapter split or per-case adapter swap. Both states use the same base-model inventory as the fit plan; OFF has no adapter.

| State | Recorded tensor SHA256 |
|---|---|
| teach | `d73e8578f62de68ed657474c70fc09c09aaad50a4ff11a66773e50fc702163b2` |
| control | `ffceffb0af4b6388d800e98d83058f2ffb44d1d9900db0e183ad1927389227d6` |
| OFF | No adapter input / empty adapter files |

Readout plan, raw request identities, reduction identities, fit result inventories, and `R/fit_main_release.json` agree. The absence of memory binding is therefore not explained by this run selecting a separate untrained memory adapter.

## 5. Costs — actual native readout tokens, not caps

Independently summed raw prompt/output token-ID array lengths and paired request-start/response-end timestamps:

| State | Calls | Actual native input tokens | Actual native output tokens | Output ceilings | Summed generation-call seconds | Supervised readout seconds |
|---|---:|---:|---:|---:|---:|---:|
| OFF | 48 | 2131 | 1212 | 3072 | 35.134805921 | 134.054387187 |
| teach | 48 | 2131 | 472 | 3072 | 20.038652430 | 97.699672948 |
| control | 48 | 2131 | 472 | 3072 | 21.928067711 | 111.484780756 |
| **Total** | **144** | **6393** | **2156** | **9216** | **77.101526062** | **343.238840891** |

All sums agree with each raw usage receipt, each reduction, and `R/readout_main_release.json` totals. Equal 64-token caps do not equal realized output usage: OFF's lengthy invalid memory responses cost more tokens than the trained constant-color outputs.

Separate duration denominators:

- Supervised **fit** windows: teach **72.639051253 s**, control **60.360001759 s**; sum **132.999053012 s**.
- Trainer-reported training-loop clocks are **20.9 s / 20.7 s**, and trainer wall clocks **35.1 s / 21.3 s**, rounded native manifest fields. They are not the supervised reservation durations.
- Readout launch-to-Main-release reservations independently reproduce OFF **230.438407 s**, teach **227.650166 s**, control **215.569307 s**; sum **673.657880 s**.
- Fit launch-to-Main-release reservations are teach **256.127487 s**, control **233.126690 s**; sum **489.254177 s**, through the fit release at **17:43:52.172836 UTC**.
- The summed fit plus readout full reservation windows are **1162.912057 s**, not an elapsed wall interval. They include preparation/hash/audit/idle work within those windows and are not active GPU compute or complete campaign cost. Work outside the recorded windows is not silently included.

No billing rate or monetary cost is supplied. Training token passes, generated-token usage, output caps, generation-call time, trainer clocks, supervised time, and full reservations must remain separately labeled.

## 6. Custody, source/model hashes, and untouched-confirmation attribution

Independent checks passed:

- Capsule hash and all 373 extracted-member byte comparisons.
- All six candidate-manifest file hashes, the frozen fit-plan hash, both actual fitted-corpus hashes, and non-weight adapter metadata hashes.
- All three readout plan/hash/preparation/launch/reduction bindings.
- All **300 raw capture-manifest file hashes** across the three states, including 288 request/response files.
- All **144 raw request prompt hashes and response-value hashes**; each recorded native input-token array/rendered prompt matches its prepared input receipt.
- Matching 14-file base-model hash inventories across fit/readout plans and reductions; matching source inventories across all three readouts.
- All twelve recorded readout source-file pins match the currently inspected local source files. Critical pins include `fundamental_teaching_corpus.py` **`44b1a61e10695e1e65ca3ee2e6c151eba45df1512ea3fc108402e96226ddaa13`** and `fundamental_teaching_readout.py` **`d6eebc6e70f5a76fcde6c530aeacc273ae5f29a8d9a67ffe5948f04842684bb6`**. Neither was executed.
- Both fit workers and all three readout workers have successful supervised completion/cleanup receipts; all readout backend handles are recorded closed. Missing artifacts are not being represented as outcome zeros.

Native source attribution:

- Fit source: **`06c90d1bbd00fd7ab1867bf069944554b84580cf`**, with separately pinned fit orchestration.
- Readout source: **`a9a7c67919b5f5ec8b121a463f2ea49a5c967757`**.
- Main's recorded final readout releases: OFF **17:51:59.026301 UTC**, teach **17:52:21.108305 UTC**, control **17:52:46.411485 UTC**, September 12, 2026.

**The capsule contains no weight files.** Current tensor/model rehashing and full device/process/queue release checks remain attributed to Main's native receipts, not re-certified remotely by this review. Local source and receipt hash agreement does not authenticate official model origin or prove loaded runtime state. The retained status is `UNRESOLVED_LOCAL_HASHES_ONLY`; archived releases are not live vacancy guarantees or complete model backups.

“Untouched 64 confirmation” is supported as **zero model requests to those 64 cases in this complete captured development run**. The source/evaluation registry is CPU-authored and archived; no broader historical non-exposure certification is inferred.

## Required correction / final disposition

**None required for the user's stated numerical summary. PASS, with the following limits carried into any downstream write-up:**

> In the fixed seed-0 development readout, all states already solve 32/32 addition actions. Teaching produces the trained PREDICT-before-ACT toy format on 32/32, versus control/OFF 0/32, but neither trained state demonstrates device-specific memory binding: both answer red on all sixteen cases, yielding the four red-key matches. OFF memory outputs are invalid and all reach the 64-token cap. The trained +4 over OFF is therefore not evidence of selective memory; confirmation, prediction intelligence, parenting, and general-learning closure remain untested.

Do not call this an L1 combined behavior-and-memory pass, introduce a larger-cap OFF rescue or favorable subset, claim additional optimizer-seed replication, or infer H1/H2, clean lineage, a mechanism freeze, or campaign completion. No new experiment, confirmation access, or external circulation is authorized by this review.
