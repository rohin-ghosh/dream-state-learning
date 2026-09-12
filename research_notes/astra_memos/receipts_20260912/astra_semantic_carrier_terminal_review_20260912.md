# Semantic carrier terminal raw-evidence audit — 2026-09-12

**Verdict: PASS_DEV_RAW_EVIDENCE_AUDIT_WITH_LIMITS.** Every captured request/record binding, inventory hash and declared result gate checked out. This accepts bounded DEV surface evidence only, not fitting/readiness/H1 claims or C11 custody.

## Evidence and method

Captured run: `/tmp/astra_semantic_carrier_terminal_20260912/astra_semantic_carrier_20260912_attempt1`. Original run: `/localhome/local-rohing/astra_diagnostics/astra_semantic_carrier_20260912_attempt1`. Recorded source identifier: `241dd86e0e95b85a0359ca3807c134350d1c4955`; no git lookup. Six local source files match manifest pins, including module `fd31dc722f7a1a4b65a2fb597811e2598d603c650e8f6fe4e852915fc38c7392` and tests `fc9b1b9992f6a3d8066918c9ade5429526b568f472f76055db0e3fd19b08df1c`.

Verified **157 run files: 156 sealed members plus SEAL.json**, exact inventory equality, canonical/duplicate-key-free run JSON, prepared/manifest/start bindings and all **144** request-ID/full-request record hashes. Independently reconstructed the fixed fresh namespace, material, prompts and expected actions; checked identical generation/scoring payloads for all 64 semantic items. No missing/extra/duplicate records, incorrect bindings or hash drift were found.

An independent raw-record reduction, without importing project code or loading a tokenizer, exactly matches the **entire** sealed report object, including every detail, candidate sum and margin. It also matches supplied remote replay `/tmp/astra_semantic_carrier_replay_20260912.json` and sibling `controller.log` as parsed JSON. The separate evidence is not covered by the run seal; hashes are retained separately.

## Counts and numeric margins

| Cell | Greedy correct | Scored correct | Min margin (nats) | Mean margin | Max margin |
|---|---:|---:|---:|---:|---:|
| 0/W+ | 16/16 | 16/16 | 6.485877335 | 12.661962294 | 16.584040464 |
| 0/W- | 16/16 | 16/16 | 8.606366813 | 13.756018855 | 21.041379988 |
| 1/W+ | 16/16 | 16/16 | 6.060128182 | 12.876437465 | 18.532954812 |
| 1/W- | 16/16 | 16/16 | 9.101730138 | 14.276488327 | 22.906309813 |

- Semantic generation: **64 valid, 0 truncated, 0 multiple-action**. Each cell has an 8/8 target balance and perfect diagonal confusion matrices.
- Complementary swaps: **32/32 generated, 32/32 scored**. Generation/score agreement: **64/64**.
- Copy canaries: **16/16**, 8/8 per root; **8 unique prompts**.
- Work: **80 generations, 64 scoring requests, 128 candidate forwards, 960 finite nonpositive response-token log probabilities**.
- All declared conjunctions pass: ≥15/16 in each cell for each operation, ≥61 valid, zero truncation/multiple, ≥29/32 swaps for each operation, and all canaries. Scoring did not rescue failed generations.
- Full-sequence target-minus-other margin: min **6.060128182113**, median **13.224879220194**, mean **13.392726735053**, max **22.906309813135 nats**. Minimum-margin request: `02f45973b1fa6d1865346153ea64350e7348e7b702e8a998f7573e104a64de43`.

Every candidate has exact prefix equality, a fully masked prefix and a fully included response. Candidate text includes LF; recorded response arrays end `[198,151645]`. All **8 tokens for -mem2reg and 7 for -gvn**, including recorded LF+EOS, contribute to each sum; no length normalization or suffix omission. Matched source: `organism_v6/semantic_carrier_diagnostic.py:141` and `organism_v6/semantic_carrier_diagnostic.py:332`. The JSON retains all 64 exact margins and all 128 candidate logprob arrays and action/LF/EOS components.

**Raw-output qualification:** all **80/80** generations are exactly `ACT: <expected action>` with **no LF and no padding**, followed by recorded EOS. For example `/tmp/astra_semantic_carrier_terminal_20260912/astra_semantic_carrier_20260912_attempt1/391179d36cd4205d4d8566a10eaf7aee480a7769d04e74c91bf5ea9bb98ba1eb.json` contains `ACT: -mem2reg`, IDs `[6823,25,481,10536,17,1580,151645]`. This passes the frozen ASCII-whitespace-tolerant parser (`organism_v6/semantic_carrier_diagnostic.py:249`); it does not demonstrate greedy LF emission. Only scoring forces LF+EOS. Target LF logprob mean is **-26.949497163**, range **-29.232425690 to -25.093753815**; target EOS-after-LF mean **-2.932797674**. Full margins include these sizable suffix costs.

## Runtime, headroom and release

- Start **2026-09-12T12:35:53.327233+00:00**; finish **2026-09-12T12:38:03.960816+00:00**; recorded elapsed **130.633576379 seconds**, one NVIDIA A40. Wall elapsed agrees within 0.1 seconds. This includes setup/hashing/validation, not inference alone.
- Independent timeout **3546.646s**; eight-second cleanup reserve. Finish precedes the controller deadline by **3469.366417s**. Deadline/lease-cutoff/six-hour-buffer relationships pass.
- Captured prompt maximum **138 tokens**, max prompt+32 **170**, leaving **1878** under the declared 2048 cap. Largest candidate response is **8**, leaving **24** under the 32-token generation cap. These are recorded-array counts, not local tokenizer or model-capacity validation.
- `CLEANUP.json`: group/supervisor **93136**, `owned_group_empty=true`, no cancellation/error. Controller **93084**; recorded worker **93137**.
- Main's external observation at **2026-09-12T12:40:05.269868+00:00** attests controller/supervisor absence and reservation release. Independently parsed its GPU XML and sibling prelaunch XML: selected UUID `GPU-0ee6f753-c61e-e18a-8aea-acccd3042939`, **zero process entries** in both; postrun framebuffer usage **0 MiB**. No new GPU/proc query was issued. Boolean PID-absence attestations are not raw `/proc` evidence.

## Limits

1. DEV exact-row action-surface evidence only; no fitting, readiness, H1/H2, learned memory, retention, parenting, optimization-quality or clean-lineage claim.
2. No local tokenizer loaded, and no independent text/token encoding or decoding. The configured remote snapshot path is unavailable locally. Token-array/text associations are checked against captured candidates; supplied original-source remote replay is separate evidence, not a local replay.
3. All 80 greedy responses end with the action then recorded EOS, without LF. This satisfies the frozen parser but is not greedy LF+EOS emission. Only candidate scoring forces LF+EOS.
4. The 16 canary calls use eight distinct prompts repeated across roots; they are not sixteen independent controls.
5. The 960 captured log probabilities are completely summed, but no model forwards or logits were recomputed. Margins compare only the two unequal-length LF+EOS candidates and include suffix costs.
6. Hashes establish captured-byte consistency, not adversarial/C11 custody, official model origin or independent verification of the remote git commit object. Six local source-file hashes match; the remote timeout binary is not locally authenticated.
7. Cleanup/resource evidence is historical, not a live device/process check. Controller/supervisor absence is attested by booleans without raw PID-absence output; worker PID 93137 is not separately attested absent. The selected GPU XML has no process entries.
8. External replay, sibling logs and cleanup observation are not covered by the run SEAL; they have separate exact hashes. Historical launch status LAUNCHED_NOT_COMPLETED is superseded by terminal report/receipts.
9. Context headroom is measured from captured prepared arrays against the declared 2048 cap, not independently validated tokenizer/model capacity. Previously accepted escaped/early-descendant cleanup limits remain unchanged.

The worker log records dtype deprecation and ignored-generation-flag warnings (`temperature`, `top_p`, `top_k`). The pinned payload is greedy and the matched helper sets `do_sample=False` (`organism_v6/writer_interface_calibration.py:236`); the warnings do not contradict the captured gate result. Actual inference/logits were not reproduced.

## Exact hashes

Run-relative SHA-256:

```text
01fc34a300a2862fa43b1de8b8282936410a0547c6a23147418a5815a6e5f67a  SEAL.json
5787b4f4e3d14d24f6c4f769d4da55d0dea98660d49fdaa38839d5aefcfa7963  manifest.json
07de83b6b61dfab5b826c2a1c2d49e27e1f30e7ec2ae6e9dd05b7c22435003e8  requests.json
6a3c6268161e43ae84fe3b251bb096ba3ee9e56c4e4f340cbcf680c0533b42d2  report.json
213b895378ee58725bffcbefa437c36238ddfe26c29420bcbc7c3bfe139e65dd  STARTED.json
117d4b5c4a0261548627882a727935f4cd8c248bd3e422798b1867dc537e078b  SUPERVISOR.json
4333de7bec776dab206540baa0c5e740a01571cacd48aa61610b6fa02a013083  CLEANUP.json
03074f67c7d3d2f40ef635671365b7fb065848dd3a1b0df22b8d615d4dc787fe  RESOURCE.json
```

Separate evidence SHA-256:

```text
e99f4ca68fc720fcea0d602ae2d562bdfc7306354fccb055a97b1ac7036df3bd  /tmp/astra_semantic_carrier_replay_20260912.json
176b488eadc404f15d3cafdf2dc392a5dde3d4ea49e5696a8503a82d9c0b058f  /tmp/astra_semantic_carrier_cleanup_observation_20260912.json
```

The JSON companion contains all 157 run-file hashes, all external/sibling hashes, all recorded source pins and six local comparisons, plus all 144 raw-record hashes. JSON SHA-256: `14e044e983c16b5649133c33598dfaa3a8239aab10e9c3c943598c28fa8c730f`.

**Validation actually performed:** bounded local standard-library assertion checks and reaggregation, not the project CPU suite or a local tokenizer replay. Initial checks succeeded; the first report-write attempt failed on OS argument size before writing files, then creation succeeded using stdin. No repository edits, git, GPU/backend access, experiment jobs, or remote commands. Only the requested new `.md`/`.json` reports were written; original evidence was preserved. Main retains interpretation and subsequent decisions.
