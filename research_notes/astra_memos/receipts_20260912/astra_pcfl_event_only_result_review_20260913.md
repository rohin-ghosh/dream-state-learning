# Independent EVENT-only result review — 2026-09-13

**Verdict: the specific W8 AUTH 14/14 versus NO_WRITE_C0 0/14 strict-stop result is supported by all 56 archived raw readout captures and the critical completion/checkpoint/release links reviewed. The declared narrow endpoint is met. No blocking discrepancy found.** This is not full-assay, C11, clean-lineage, parenting, retention, selectivity or generalization qualification.

## Bound evidence

- Analysis: `/tmp/astra_pcfl_event_only_analysis_20260913_attempt2/analysis.json`, SHA256 `27a7180027210c1ec68bdda4b032fad039f91b99033c713742aba22d015b90a2` — recomputed and matched.
- Native archive: `gpu_artifacts_local/pcfl_event_only_20260913_attempt1/evidence.tar`, SHA256 `c7c26ad122bec200b79dd794fac6a41d351a043ed2c4b4b05a5994501dbfd64e` — recomputed and matched.
- Mirror: `gpu_artifacts_local/pcfl_event_only_20260913_attempt1/unpacked/pcfl_event_only_20260913_attempt1`, with the three sibling outer directories named in analysis.stage_pins.
- Manifest FILE SHA256 `69bb58e162dcd3982dbd246eb52d052a7faf82bcedfdaf337c43303f63a813cf` — matched against analysis and outer snapshots.
- Amended reducer SHA256 `e57a67796eaad44d75893050ada30e828c1c751f4334fd0898755b28533460d6` — matched current source and analysis.analyzer_sha256.

Read-only byte/metadata checks matched 378 reviewed mirror files against their original tar members, including all raw/request/render/response captures, prepared inputs, completed stage inventories, fit/checkpoint files and critical outer evidence. No extraction, native execution, scorer/tokenizer/model invocation or full analyzer rerun was performed.

## Raw endpoint check

| View | AUTH_WRITE exact bytes + stop | NO_WRITE_C0 exact bytes + stop | Status |
| --- | ---: | ---: | --- |
| W0 | 14/14 | 0/14 | Trained-wrapper diagnostic only |
| W8 | 14/14 | 0/14 | Declared primary held wrapper, same trained addresses |

- Confirmed exactly 28 captures per arm: 14 sorted addresses at W0, then the same ordered 14 at W8; no extra retry/error call sidecars. W8 splits into EVENT8 and EVENTS_AT6, AUTH all ones and C0 all zeros in both strata. The paired difference vector is fourteen ones, sum14.
- Compared every complete raw UTF-8 string directly with its target and checked finish reasons, raw hex/hash, response copies, output/prompt token counts and recorded strict-stop values. All 56 finish with `stop`; no length-truncated success is counted. Every C0 response is exactly `MISS`. No LF repair, stripping, extraction or semantic rescue was used.
- All 14 targets concatenate their actual admitted child EVENT support rows in the declared order. The deterministic service reproduces these targets 14/14 and is not a model arm. There are eight EVENT source rows, not fourteen independent experiences.
- Both arms receive the same two-message public memory-read prompts per address/view, without row targets or conversation history. All 28 user prompts per arm follow the fixed W0/W8 templates. Raw/render/response checkpoint routes consistently mount the saved adapter for AUTH and no adapter for C0; prepared/cold base identities agree.
- Raw token totals: 2,642 prompt tokens per arm; AUTH 1,648 output tokens, C0 56. These were checked against capture token-array lengths, not independently retokenized.
- Fixed checks are service14/14, AUTH>=13/14, C0<=1/14 and paired difference>=12/14. Observed 14/0/difference14 satisfies all four; W0 is not used to rescue or select the endpoint.

## Critical custody

| Stage | Worker PID | Stage completed FILE SHA256 | Outer collection FILE SHA256 |
| --- | ---: | --- | --- |
| fit | 189173 | `44a29a341c77871b038023ad965da5cf7f8dffe8c89ca3f4e520f2c0d6bd138b` | `384101975b74f9b8a273f41b90086977c99d1a572b3dad615441d8e7edca917d` |
| readout_AUTH_WRITE | 190885 | `0d5bfa8a6e99e6a8a487ba02a0d5a8b45462888b7b8aa33d8f13c3ddbf3f939c` | `a722628cc34a2f584510d395c83595836e376dcdb584313af5cb0fc651cd9fd6` |
| readout_NO_WRITE_C0 | 192858 | `49d8ab4c2268d8393f628ea767488f241a4001e14d57ab57c735ce994f96faf5` | `9f837cea37c6589d6022c212ebb78cd22314e0c983b2bf4e368a101d932ab80c` |

All three stage seals/file hashes match their outer copies and pinned collections. Stages are COMPLETE/NATIVE; collections are COMPLETED, rc0, no errors, zero generation retries. Three distinct PID/start-tick/boot identities are present; readout actor PIDs join their outer workers. Both actors close without failure/budget excess after 28 calls, with explicit shutdown-returned receipts. Per-call request limits and operation/generation chronology agree, including generation after cold load readiness. Post GPU/CVD/queue checks follow owned-group release within the recorded outer intervals.

Release evidence retains **complete_cvd_visibility=false** and two explicitly approved unreadable non-worker service environments on each stage. Reported GPU vacancy and released owned groups must not be rewritten as universal process/environment visibility or fresh hardware attestation.

Fit completion records 200 consecutive updates, 800 presentations/forwards. Fit/encoding identities match analysis. Saved adapter bytes match mounted identity; safetensors SHA256 `a9c6608d1a251e0e98522531f14dc16de587e9488281ec05a8f1eac60ab265c2`. This verifies archive/checkpoint linkage, not an independent numerical replay or tensor rehash from a loaded model.

## Reducer amendment and reporting disposition

The analysis explicitly records `validator_amendment=request_timing_v1_and_native_rng_schema_repair_v1`. The producer's existing `_rng_hash` returns `{cpu: sha, cuda: [sha]}`. All 400 before/after RNG objects in the native 200-update file have that shape with one CUDA entry; the amended validator matches it. This is consistent with a producer-schema repair, not a change to targets, scores, thresholds or native artifacts. The previously identified request timing/limits omission is also checked by the current reducer and was independently checked here against the actual captures.

**Reporting requirement, not a result blocker:** retain SEQ179's first reducer-attempt failure, its lack of analysis output, and the subsequent schema repair/test receipt. Do not call analysis attempt2 an untouched pre-outcome analyzer. The first-attempt failure/no-output history and Main's 25-test result are supplied provenance in this request, not independently reproduced or inspected here. Successful independent raw-byte checking supports the endpoint despite that disclosed software correction.

The defensible statement is controlled cold reproduction of this fixed imported, externally format-assisted own-EVENT bank: one source life/root, one fit, eight EVENTs, fourteen addresses, W0/W8 only. W8 is a held wrapper over trained mappings, not unseen facts or addresses. NO_WRITE_C0 is not compute-matched. Original SEQ171 remains FORMATION_FAILED/rc1 with its rejected LINK; no full-bank repair, autonomous discovery, parenting, retention, selectivity, generalization, H1/H2/C11 or automatic promotion follows. No claim correction is needed if those boundaries and the amendment remain explicit.

Only this review artifact was written. No code amendments, tests, native/GPU/model/tokenizer calls, remote/network access, commits or unrelated outcome review. **EDITSTOP.**
