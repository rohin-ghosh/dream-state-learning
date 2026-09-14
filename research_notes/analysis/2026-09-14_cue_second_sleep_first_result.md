# Cue second sleep: independent first terminal result, 2026-09-14

## Scope and conclusion

Read-only node2 campaign `/tmp/astra_cue_sleep2_20260914_attempt1`, exact source snapshot `/tmp/astra_cue_sleep2_source_20260914_attempt1`, commit **`4f68de78a036906a679558f31dcd1d31e02b3ded`**. This is a bounded independent terminal analysis and preservation, not a launch, approval, or scientific-claim promotion. All new material is this note and ignored `gpu_artifacts_local/astra_cue_second_sleep_first_result_20260914/`. No notebook, paper, project-code changes, commits, remote mutations, model/tokenizer loads, forward passes, or GPU calls were made. Remote access used only `bash gpu/ovx_ssh.sh` and read-only file commands within the two named roots. Already-local last-turn cue evidence was reused, not fetched from an additional remote root.

**The new saved adapter changes the captured learner from immediate ROUTE to self-issued READ and conditional continuation under the public interface.** Own-memory arrivals improve **3/4 → 4/4**, and researcher-supplied held-text arrivals improve **4/8 → 8/8**. The reader-disabled control declines **3/4 → 2/4**, while now making reads in every episode. Exact known-record recall stays **4/4 under each wrapper**, but unseen-address abstention remains **0/4**. These are descriptive results of **one second fit, one seed, the same bank set and task family**, not H1/H2, parenting, broad generalization, or reliable memory abstention.

## Recomputed outcomes, including failures

The independent source-only replay exactly reproduces **all 32 routing episode objects**, including raw responses, public histories, terminal reasons and transitions. It consumes every captured readout model call once: **28 S1 + 68 S2 = 96**. Each standalone episode matches its PANELS entry; PANELS matches RESULT. Outcome correctness is recomputed against the frozen bank's port→outcome mapping, not accepted from the reported score. All 24 recall/MISS probe outcomes are separately recomputed from captured raw strings.

| Panel | S1 arrivals / correct | S1 episodes with READ / second READ | S2 arrivals / correct | S2 episodes with READ / second READ |
|---|---:|---:|---:|---:|
| OWN_PARAMETRIC | 3/4 | 0/4 / 0/4 | 4/4 | 4/4 / 2/4 |
| OWN_READER_OFF | 3/4 | 0/4 / 0/4 | 2/4 | 4/4 / 4/4 |
| HELD_TEXT_0 | 2/4 | 0/4 / 0/4 | 4/4 | 4/4 / 2/4 |
| HELD_TEXT_1 | 2/4 | 0/4 / 0/4 | 4/4 | 4/4 / 2/4 |
| RECALL_W0 | 4/4 | Direct memory probes | 4/4 | Direct memory probes |
| RECALL_W8 | 4/4 | Direct memory probes | 4/4 | Direct memory probes |
| UNSEEN_MISS | 0/4 | Direct memory probes | 0/4 | Direct memory probes |

S2 has **6 actual own-parametric reader calls**, **8 reader-disabled calls**, and **12 external held-text lookups**. Thus “four with reads” means four episodes, not four read calls. The 12 held lookups do not call a model. Each stage has 16 routing episodes plus 12 memory probes, with no denominator or task-family expansion. The own bank is tested twice per stage for the reader intervention; those are not independent banks.

### Exact changes by episode

Episode numbers here are the one-based artifact suffixes. `T/F` denotes raw GOAL arrival, not a revised score.

| Panel | S1 episodes 1–4 | S2 episodes 1–4 | Changed outcome |
|---|---|---|---|
| OWN_PARAMETRIC | T,T,F,T | T,T,T,T | Episode 3 repaired |
| OWN_READER_OFF | T,T,F,T | T,F,F,T | Episode 2 regresses; episode 3 still fails |
| HELD_TEXT_0 | T,F,F,T | T,T,T,T | Episodes 2 and 3 repaired |
| HELD_TEXT_1 | T,F,F,T | T,T,T,T | Episodes 2 and 3 repaired |

All 16 S1 routing episodes issue no READ. All 16 S2 routing episodes issue a first READ to the first listed address. In the 12 S2 own-parametric/held-text episodes, episodes 1 and 3 of each bank encounter the other goal's record, read the second address, and commit its DID; episodes 2 and 4 encounter the requested goal immediately and commit that first record's DID. This is **six mismatch→second-read paths and six match→one-read paths**, all arriving at the requested goal in these captures. All six own-parametric replies exactly match the generated bank's corresponding EVENT bytes; the held replies are explicitly researcher-supplied text, not learned parametric recall.

The newly repaired own-parametric episode 3 asks for `N_CMZXILYYFI`. S1 immediately emits `ROUTE P_IW6NBDXQPN`, reaching `N_FHOFB66WSI`. S2 emits:

```text
READ EVENT E_QAQ5WQZQRH
  EVENT ... DID P_IW6NBDXQPN GOT N_FHOFB66WSI ...
READ EVENT E_X3YBAILZSM
  EVENT ... DID P_STMW7CXQGK GOT N_CMZXILYYFI ...
ROUTE P_STMW7CXQGK
```

With the reader adapter disabled, S2 receives literal **`MISS` on all eight reads**, reads both addresses in every episode, then chooses the first listed port for both goals of each pair. It therefore reaches only episodes 1 and 4. The actor adapter remains enabled: this is **reader-adapter-disabled**, not an all-base actor or no-tool control. In particular, own-reader-off episode 2 previously chose `P_LRZJ7WQPLZ` correctly; S2 instead ends with `P_GBV7TYNMYX` after two MISS replies and reaches the other goal. S1's reader-off arm never actually exercised the disabled reader because it never read.

One S1 failure is syntactic, not a wrong legal transition: `HELD_TEXT_1_EPISODE_03.json` emits **`ROUTE P_2AA66KVPFZ,P_Q4RVHCV3YN`**, has `terminal_reason=invalid_command`, and no outcome. It remains a failure; no port extraction or lenient rescoring was applied. The other five S1 routing failures and both S2 routing failures also remain in the preserved evidence.

Both stages' four unseen probes emit EVENT-like invented records rather than MISS. For example, S2's first unseen response is:

```text
EVENT E_4FVJF7U3EX AT N_KGA6B2GC43 DID P_IW6NBDXQPN GOT N_CMZXILYYFI EVIDENCE R_QKW7UDYO13
```

The exact unseen criterion is `MISS\n`, but **none emits even bare `MISS`**, so this failure is not merely a final-LF mismatch. Complete unabridged S1/S2 strings remain in PANELS, CALL files, and ANALYSIS.json. Reader-off `MISS` responses concern known addresses with the learned reader disabled and do not contradict the fitted reader's unseen hallucinations.

## Same adapter/base, actual targets, and dose

- Train and S1 readout declare the same original adapter directory, original training RESULT hash, loaded parameter-state hash, Qwen2.5-7B-Instruct snapshot, tokenizer signature, memory/cue provenance, encoded masks and training rows. S2 points to **this campaign's newly saved adapter**, not the old one. The three stages use the same frozen runner/material bytes.
- S1 loaded state equals train-before state. Train-after differs from before and equals the S2 loaded state. S2's `initial_artifact_sha256` equals the actual captured train RESULT file hash. This field hashes a RESULT receipt, **not adapter weights**.
- Independently parsed the complete safetensors file using only standard-library header/byte handling: **392 F32 LoRA tensors, 20,185,088 parameters**, no base tensors. Reconstructed the frozen `_state_hash` byte stream, restoring runtime `.default` adapter key names, and obtained the exact train-after/S2-loaded hash below. No tensor library or model was loaded. Config is rank8, alpha16, dropout0.05, seven projection targets, no saved embedding/base modules.
- Frozen native source checks the base parameter-state digest before/after and rechecks readout adapter immutability; all three terminal receipts report `frozen_base_unchanged=true`. This audit verifies those source guards and consistent captured receipts, **not a new independent base-cache/tensor measurement**. The original adapter's live bytes were not revisited outside the allowed remote roots.
- All **20 cue rows** join through bank-local origins to the actual globally indexed upstream calls. Each final assistant string equals the actual captured generation; each public prefix equals the bank's recorded public history; all source-file hashes match the fit's pinned cue provenance. Guidance and public-feedback teacher text are absent from student prefixes. The targets are **12 READ + 8 ROUTE**, collected with explicit last-turn next-action coaching, not free-running demonstrations.
- Every one of the **52 stored masks** has a single contiguous final-target label span, with all preceding tokens and the trailing template LF masked `-100`. Each of the 20 cue target-ID arrays equals its actual upstream generated token-ID array, including EOT151645. Earlier assistant turns are masked. The 32 memory rows match the exact own-bank EVENT strings under W0–W7, and their target IDs also equal the matching captured exact-recall generation IDs. This checks captured IDs and boundaries; it does **not** retokenize or independently validate the tokenizer implementation.
- All **200 LOSSES records** are finite, consecutively indexed 1–200, and match the frozen two-memory-plus-two-cue cyclic schedule exactly. Totals are **400 memory + 400 cue presentations, 24,480 supervised tokens**. Memory rows0–15 occur13 times and rows16–31 occur12 times; every cue row occurs20 times. Hence equal group presentations do not mean equal exposure per distinct row or equal token weighting. Source uses a fresh AdamW at3e-5, seed0, not resumed optimizer state. Loss first/last is **0.0510781482 / 0.0000279420**, descriptive training loss, not an independent outcome metric.

The old memory corpus retains its existing **FINAL_LF_ONLY** serialization and provenance field `original_strict_accepted_events=0`; this audit does not rewrite that history into strict-original acceptance. There are32 memory rows (four facts × eight wrappers) and20 coached cue rows (eight tasks in two different banks). The second fit adds those cue examples to the old memory replay; it does not synthesize further examples beyond the captured corpora. The own, two cue, and two held banks are pairwise identifier-disjoint under the six frozen identity fields. They are nevertheless **five banks of one fixed synthetic two-choice family**, not five independent scientific families. The held masters and every public task are the same in S1 and S2.

## Hashes and preserved evidence

All hashes are SHA-256; full per-file source/campaign manifests and complete raw data are under `gpu_artifacts_local/astra_cue_second_sleep_first_result_20260914/`.

| Binding | Hash |
|---|---|
| Frozen runner `gpu/astra_experienced_event_cue_sleep.py` | `dc0bf710984a7f5d093f8ff41c99143328173db1cf2c57c5209c8a476863e021` |
| Frozen material `organism_v6/experienced_event_cue_sleep.py` | `02c9e41b4a0382aa4c831ccd127532a885052fdc2937fbbf63a98797ad432846` |
| Declared/guarded frozen base parameter state | `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992` |
| Original adapter weights, pinned by source/cue receipts | `8597605e7e07b882f613e359decee0193275d4bd16eacac8cd5c45db75f25788` |
| Original adapter training RESULT | `c42010e12efed8a06c1e98901f09d576cf0c568175e837fa66255138e3c8a40f` |
| S1 loaded / second-fit initial parameter state | `c08852cb6eb2c8bfa106cf2b7976fc5a2ba5f4cb06d79d53a3a3ac7222b865db` |
| New adapter weights, entire file | `6ca6b6a300d5b19816eef1e50a03e78e6eb212f699a746d001332e1eae6f21ff` |
| New adapter config | `bdd7ef1f70f28c1c97730adc7d0ad1340a97107700c4a493bbb95ca6accd6bde` |
| New adapter state, independently reconstructed / S2 loaded | `9d3c97ae280dd33c0acb5b7a67cb162ccb2d53d63d0668d2206aa091ac944e63` |
| Second-fit RESULT / S2 input receipt | `8234842da1f48a2a4fbf6c2dc74d95022eccc0312a841484ce4fecfce41265f7` |
| S1 readout RESULT | `4049c89e83465ffb6a596a18d948dded01545848fe9ffdca0518beee78b05d3e` |
| S2 readout RESULT | `99c5ef35ccb5b15117a7f6c1c1cf1afaf6f216556e35dce1589c3dfbd2c9c721` |
| Compiled original memory rows | `99258bf00abe7854b86b3497a5b0e8cb9db0b59b4269a77d7641ef72653f830a` |
| Selected cue rows | `eec3d6be30a5016d0bd13bf62cdff3e8d6568ae5b6a7578dd60500ce6084f72a` |

Preservation includes the **entire 80,792,096-byte adapter_model.safetensors**, config and README, every campaign request/result/panel/call/episode, all masks/rows/losses, both guardian logs/scripts, scanner source and captured launch receipts. `campaign.tar` is the transfer archive; `campaign/` contains the usable adapter and extracted evidence. `source.tar`/`source/` contain only the frozen snapshot's Python source, **278 files**, each independently byte-equal to its exact Git blob at4f68de78; no environment/credential files or heavy model caches were copied. Native source is retained for inspection, never executed.

**164 campaign files + 278 source files = 442 remote/local file-hash matches.** Campaign hashes also match the initial post-transfer measurement. Remote after/final measurements at **09:48:52 UTC and09:52:23 UTC** match completely, including logs and weights. `remote_initial_capture.txt` includes the first campaign hashes plus source excerpts; `remote_after.sha256.txt`, `remote_final.sha256.txt`, and `LOCAL_CAPTURE_SHA256SUMS` retain the comparisons. All raw failures are retained; there is no FAILED.json in any of the three terminal stage directories.

`upstream_local/cue/` is a bounded copy of the already-local `astra_lastturn_cue_feedback_result_20260914/capture/lastturn/run`; every file named in the fit's cue-source pins matches. It was not recaptured or represented as a new remote measurement. `analyze.py`, `ANALYSIS.json`, and captured stdout/stderr make the audit reproducible. The replay imports only captured pure organism modules with a guard rejecting gpu/torch/transformers/tokenizers/peft imports. Final audit status: **`PASS_CAPTURED_REPLAY_NO_MODEL_OR_TOKENIZER`**.

## Timing and cost accounting

| Stage | Start UTC, 2026-09-14 | Finish UTC | Wall seconds | Captured readout model calls | Prompt / emitted tokens |
|---|---|---|---:|---:|---:|
| Second fit | 09:39:46.479726 | 09:43:51.495069 | 245.015343 | Not a readout | 24,480 supervised training tokens |
| S1 readout | 09:39:46.492395 | 09:41:10.994001 | 84.501606 | 28 | 3,833 /773 |
| S2 readout | 09:43:52.480770 | 09:45:40.507995 | 108.027225 | 68 | 11,583 /1,370 |

The stages span **354.028269 wall seconds**, since S1 overlaps training. Sum of stage durations is **437.544174 seconds ≈7.2924 GPU-minutes (0.12154 GPU-hours)** if attributing one allocated GPU per stage. This includes initialization/hashing/evaluation overhead, not measured forward-only utilization or billed lease time. Captured resource metadata identifies A40 GPUs: train/S2 UUID `GPU-d304a15c-516a-16a0-a926-a560304077cc`, S1 `GPU-0cc84073-37a0-4f7a-e555-11671425bd03`. No new device query was made.

Readout total: **96 model calls,15,416 prompt tokens,2,143 emitted tokens** including recorded EOTs. S1 has16 actor +12 probe calls; S2 has42 actor +14 reader +12 probe calls. The 200 training updates and upstream cue collection are not counted as readout calls. No dollar rate or billed-cost receipt is present, so dollar cost is **unresolved**, not estimated from an assumed rate. The sidecar itself performs zero model/forward/GPU calls. Guardian train completion is09:45:41Z; S1's guardian uses `exec` and has no separate completion file, but its captured terminal RESULT is COMPLETE. Logs retain deprecation/generation-flag warnings; frozen generation source explicitly uses greedy `do_sample=False,num_beams=1`.

## Alternatives and unresolved limitations

1. **Joint update, not cue-only causal isolation.** Actor and reader share the updated adapter, and the fit combines old memory replay with cues. There is no matched memory-only additional200-update fit here. Stable4/4 recall does not prove the reader's internal state/function was unchanged, or isolate which group caused the gain. Fresh optimizer state is also part of the intervention.
2. **Reader intervention is informative but narrow.** S2's own4/4 versus reader-off2/4 is consistent with useful learned-memory replies in these paths. It does not establish general necessity, robust grounding, or exclusion of all policy shortcuts. There is no swapped/corrupted-record, mismatched-goal, held-reader-disabled, or cue-only comparator in this bounded campaign. S1's disabled-reader comparison is vacuous because no reads occurred.
3. **Same family and bank geometry.** All evaluation uses the same public grammar and generator with two choices/two goals, fixed sorted address displays, and repeated pairs. In these three evaluated banks the successful one-read/two-read pattern aligns with episode positions2/4 versus1/3. Per-episode histories reset, but stable ID/order correlations and narrow template heuristics remain alternatives. Fresh opaque IDs exclude literal cue-bank identity reuse; they do not certify family transfer or abstract conditional reasoning.
4. **Teacher-generated selection history remains relevant.** Last-turn coaching explicitly supplied each next action during collection; stripping teacher text yields actual actor targets, not evidence that those demonstrations were independently discovered. Readout public prompts contain no teacher, so coaching leakage into readout prompts is not the explanation seen here. Learning a narrow coached policy is still an adequate alternative to stronger claims.
5. **No statistical replication or sealed benchmark.** There is one seed0 continuation and one deterministic captured readout per state on different A40 devices. Four/eight correlated episodes do not estimate across-seed reliability. Held identities are a DEV text-reader test, not sealed generalization or a second learned-memory bank. The same eight known-recall probes before/after are retention checks, not eight independent learned memories.
6. **Failure handling is not learned robustly.** Unseen abstention is0/4 both times; even two literal MISS replies lead the S2 actor to guess a port. This limits any “knows when to consult/when it knows” interpretation despite improved consultation on useful records.
7. **Verification boundary.** Saved adapter bytes/state and frozen-source identities are independently checked; native base immutability and initial adapter lineage rely on matching recorded measurements and audited guard code. No native rerun, tokenizer load, base-cache read, or live original-adapter inspection was performed. Captured replay verifies consistency and exact transitions, not an independent measurement of model execution.

Additional seeds/control fits are owned by the main process and are outside this note. Nothing in this sidecar launches, changes, pauses, or merges them. **No H1/H2 or parenting claim is made.**
