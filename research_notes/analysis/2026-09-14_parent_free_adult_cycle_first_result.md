# Parent-free adult cycle: independent first-result reduction

## Scope and current evidence boundary

Campaign: node2 `/tmp/astra_adult_cycle_20260914_attempt1/{CUE_REPLAY,CUE_LOSS_OFF}/{collect,train,before,after}`. This sidecar only reads captured files and executes pure/captured replay. No model/tokenizer loads, forward passes, GPU queries, remote mutation, notebook/running-source edits, commits, or review/launch gate. Main owns the native wrapper and experiments.

Local evidence: `gpu_artifacts_local/astra_adult_cycle_first_result_20260914/`. Reducer: `tools/astra_adult_cycle_reduce.py`; tests: `tests/test_astra_adult_cycle_reduce.py`. A stage without a terminal RESULT remains **PENDING** even when partial files exist; FAILED takes precedence over RESULT. No partial outcomes are promoted.

Initial capture contained both terminal collections. The follow-up selection began **2026-09-14 10:15:45 UTC**, capturing both complete BEFORE readouts and the terminal CUE_LOSS_OFF fit. Following Main's fresh-AFTER update, one timed capture at **10:18:12 UTC** found all eight stages terminal. The complete reduction is now `ALL_STAGES_TERMINAL`, with no pending stages. Earlier partial snapshots are preserved, not overwritten into apparent completeness. No model or experiment was rerun.

**Actual AFTER: cue new-own arrivals improve1/4→3/4; off remains2/4. Both learn new W0 recall4/4 but reach only W8 recall3/4. Old recall stays4/4 under each wrapper; held controller stays cue8/8 versus off4/8. The shared failed W8 address has different corrupted text in the two arms. Cue's actual wrong reader reply is identical to its W8 probe failure and leads to a wrong-goal fallback after the second read.**

## Collections: identical actual child targets, different initial children

Both arms independently retain **four grounded events from eight calls**, compile **32 rows**, and have zero collection infrastructure failures. Their entire COLLECTION files, including captures and generated token IDs, are byte-identical:

`8f9c66609077f15af1469caed513513d2db731a2a10cce65298dfbc81b53924a`.

The pure adult helper replays every original EXPLORE prompt, captured action, deterministic environment receipt, EVENT response, admission decision and compiled row. The new bank is excluded from the original bank, both cue-training banks and both held-text banks. All four raw EVENTs already end in one LF; explicit `FINAL_LF_ONLY` is retained but does not change these actual targets. The row roles remain system/user/assistant, with only the actual EVENT as the final target. No public-feedback teacher or parent participates. Offered singleton ports, environment receipts and EVENT-format scaffolding are researcher-authored: this is not autonomous experience selection or a clean/H2 claim.

The initial children are **not identical across arms**:

| Binding | CUE_REPLAY | CUE_LOSS_OFF |
|---|---|---|
| Initial adapter file SHA-256 | `6ca6b6a300d5b19816eef1e50a03e78e6eb212f699a746d001332e1eae6f21ff` | `b4a36ca4f7f150d7dfc0cee44cc8cf52fdfc6315764ba3c818685da43cc3c25f` |
| Loaded initial adapter state | `9d3c97ae280dd33c0acb5b7a67cb162ccb2d53d63d0668d2206aa091ac944e63` | `a160b83ab9a716b5c1cba25252c9b3341db205e7269f245d6d71d33415d4ea34` |
| Initial training RESULT | `8234842da1f48a2a4fbf6c2dc74d95022eccc0312a841484ce4fecfce41265f7` | `05f413eb04c423682b434383c11062ccc0d65c7005c02fa26869bebc46e34a5e` |

Within each arm, collection, BEFORE and captured training bind to that arm's initial child, source corpus, tokenizer signature and frozen base. Both use declared base parameter-state hash `a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`. Base immutability is a recorded native measurement plus audited guard, not a new base-cache measurement by this reducer.

## Recomputed BEFORE: new memory absent, old memory retained

`OWN_PARAMETRIC` here addresses the **new adult bank**, not the old development bank. `RECALL_W0/W8` probe that new bank; `OLD_RECALL_W0/W8` are the distinct old-memory retention probes. Held panels are externally supplied EVENT text, not newly learned memory.

| BEFORE panel | CUE_REPLAY | CUE_LOSS_OFF |
|---|---:|---:|
| New own-parametric GOAL arrivals | 1/4 | 2/4 |
| New own episodes with READ / second READ | 4/4 / 2/4 | 0/4 / 0/4 |
| New own reader-disabled GOAL arrivals | 2/4 | 2/4 |
| Reader-disabled episodes with READ / second READ | 4/4 / 4/4 | 0/4 / 0/4 |
| Held-text GOAL arrivals, combined | 8/8 | 4/8 |
| Held episodes with READ / second READ | 8/8 / 4/8 | 0/8 / 0/8 |
| New exact recall W0 | 0/4 | 0/4 |
| New exact recall W8 | 0/4 | 0/4 |
| Old exact recall W0 | 4/4 | 4/4 |
| Old exact recall W8 | 4/4 | 4/4 |
| Unseen exact MISS | 0/4 | 0/4 |

The reducer exactly reconstructs **32 routing episode objects** and joins **110 BEFORE model calls** (74 cue,36 off), including eight separately captured OLD_RECALL calls per arm. It recomputes every port transition against the frozen bank, every memory probe against exact bytes, and all panel totals. All failures and raw paths remain present.

Notable retained failures:

- CUE_REPLAY new-own episodes1/2 stop after one READ with `memory_nonterminal_or_truncated`; the same long malformed reader text is preserved, not repaired or counted as a legal route failure. Episodes3/4 read both addresses but receive old-bank-looking records; both commit `P_2RVHKWHYEC`, reaching only episode4's goal.
- CUE_REPLAY reader-disabled episodes receive two literal MISS replies each, then choose the first listed port; only episodes1/4 arrive. These are not successful recall or successful abstention.
- CUE_LOSS_OFF issues no READ in all16 routing episodes. It mostly chooses the first listed port. Held-text bank1 episode3 instead emits `ROUTE P_2AA66KVPFZ,P_Q4RVHCV3YN`, retained as `invalid_command` with no outcome. No permissive port extraction was used.
- Both arms' new-memory and unseen probes fabricate EVENT-like strings rather than recalling new records or abstaining. Successful structured EVENT emission during collection does not itself establish subsequent parametric storage.

## Actual AFTER and the exact remaining failure

| Panel | CUE_REPLAY BEFORE→AFTER | CUE_LOSS_OFF BEFORE→AFTER |
|---|---:|---:|
| New own-parametric GOAL arrivals | 1/4→3/4 | 2/4→2/4 |
| New own episodes with READ | 4/4→4/4 | 0/4→0/4 |
| New own episodes with second READ | 2/4→3/4 | 0/4→0/4 |
| New own reader-disabled arrivals | 2/4→2/4 | 2/4→2/4 |
| Held-text arrivals, combined | 8/8→8/8 | 4/8→4/8 |
| New exact recall W0 | 0/4→4/4 | 0/4→4/4 |
| New exact recall W8 | 0/4→3/4 | 0/4→3/4 |
| Old exact recall W0 | 4/4→4/4 | 4/4→4/4 |
| Old exact recall W8 | 4/4→4/4 | 4/4→4/4 |
| Unseen exact MISS | 0/4→0/4 | 0/4→0/4 |

Cue own episodes1/2 are newly successful; episode3 remains wrong and episode4 remains successful. AFTER cue own has7 actual learned-reader calls, reader-disabled has8 calls, and held-text has12 external lookups. Off still makes no READ in any routing episode. The off held bank1 episode3 malformed two-port command persists; several other off ROUTE outputs gain an allowed final LF without changing outcomes. Reader-disabled cue still receives two MISS replies in every episode and guesses the first port. No failure is dropped or rescored.

### Same failed address, different corrupted records

Both arms' sole failed W8 probe is **`E_3FIXU7HBPN`**, the third fact. Exact expected target, emitted correctly during both collections and recalled correctly under W0 in both AFTER states:

```text
EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZ DID P_XN2MTIYXOF GOT N_7G6JCNMNEO EVIDENCE R_IU33SBN5QW
```

Actual **CUE_REPLAY W8**, also the actual learned-reader reply in cue own episodes3/4:

```text
EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZ4 DID P_XN2MTIYXEC GOT N_7G6JCNMNEQ EVIDENCE R_IU33SBN5QW
```

Actual **CUE_LOSS_OFF W8**:

```text
EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZQ DID P_XN2MTIYXIAZ GOT N_7G6JCNMNEFC EVIDENCE R_IU33SBN5FVJ
```

All three strings end in exactly one LF; both generated failures are terminal and untruncated. The following are literal field differences, not repair suggestions:

| Field | Expected | Cue actual | Off actual |
|---|---|---|---|
| EVENT | `E_3FIXU7HBPN` | unchanged | unchanged |
| AT | `N_Q5JLOL7SKZ` | `N_Q5JLOL7SKZ4` | `N_Q5JLOL7SKZQ` |
| DID | `P_XN2MTIYXOF` | `P_XN2MTIYXEC` | `P_XN2MTIYXIAZ` |
| GOT | `N_7G6JCNMNEO` | `N_7G6JCNMNEQ` | `N_7G6JCNMNEFC` |
| EVIDENCE | `R_IU33SBN5QW` | unchanged | `R_IU33SBN5FVJ` |

Thus the arms share a **failure address and wrapper**, not byte-identical wrong memory. These are factual identifier corruptions, with invalid identifier lengths as well—not missing LF, harmless whitespace, or truncation. The new-memory training rows cover W0–W7; W8 is outside those training wrappers. Correct W0 alongside failed W8 supports a wrapper-sensitive retrieval limitation in these captures, rather than a bad compiled target or uniformly absent learned record. It does not by itself identify an internal model mechanism.

### Which actual reader is wrong, and how the cue route fails

The actual faulty calls are **`CUE_REPLAY/after/new_task/CALL_010.json`** and **`CALL_015.json`**, both `panel=OWN_PARAMETRIC`, `role=reader`, **`reader_adapter_disabled=false`**. Their raw outputs match the cue W8 failure byte-for-byte. They belong to own episodes3 and4 respectively. The off arm makes no own-task reader calls; its corruption is observed in the direct W8 probe, not an executed own-task read.

Cue episode3 public task:

```text
NODE N_Q5JLOL7SKZ
GOAL N_7G6JCNMNEO
PORTS P_2RVHKWHYEC,P_XN2MTIYXOF
EVENTS E_3FIXU7HBPN,E_3K7UVCYOTM
```

The actual trajectory is:

1. `READ EVENT E_3FIXU7HBPN` → the corrupted cue record above, whose AT and GOT fail the public NODE/GOAL and whose DID is not a listed port.
2. `READ EVENT E_3K7UVCYOTM` → the correct **other-goal** record:

   `EVENT E_3K7UVCYOTM AT N_Q5JLOL7SKZ DID P_2RVHKWHYEC GOT N_S6IHXBULZX EVIDENCE R_VQGRQACZQB\n`

3. `ROUTE P_2RVHKWHYEC` → actual transition `N_S6IHXBULZX`, not the requested `N_7G6JCNMNEO`; `terminal_reason=wrong_outcome`.

The controller passes actual reader text without repairing identifiers. After two reads neither returned record matches episode3's goal; the actor nevertheless chooses the second record's valid listed port. **Observed failure: corrupted learned retrieval, followed by a no-matching-evidence route choice.** Episode4 requests `N_S6IHXBULZX`, follows the same commands and receives the same two records, so that identical route succeeds there. The interface allows three actor calls/two reads and no explicit ABSTAIN command; this observation does not assume a missing abstention action was available or propose a guard change.

## Both terminal fits and mixture

Both independently captured fits have all400 finite, consecutively indexed loss records and exactly **OLD32+CUE20+NEW32**. Every update is one old-memory row, one old-cue row and two new-memory rows: **400 old-memory +400 cue presentations +800 new-memory presentations per arm**. The complete TRAINING_ROWS files are identical across arms, as are the stored pre-ablation MASKS files. All32 new-memory targets replay from the actual child collection; all20 cue targets and their stored token IDs join to already-local, hash-pinned original cue captures. Every new-memory target-ID array also matches its actual collected EVENT generation, including EOT, in both arms.

All84 encoded masks expose only a contiguous final target/EOT span, with preceding tokens and trailing template LF masked. On CUE_LOSS_OFF, the native batching source additionally masks the entire cue row at batch slot1. Independently reconstructed per-update counts verify the scale `active/original`, preserving the original full-batch denominator: **66,080 original labels in both arms;66,080 active cue labels-plus-memory labels versus61,500 active off labels**, with off scale range **0.9207317073–0.9404761905** and cue scale1. The cue row is still presented in the off arm, but contributes no direct labels. Its4,580 removed labels are not replaced with more memory labels.

Recorded CUE_LOSS_OFF adapter state changes from `a160b83a…` to `b0693f1a3645796f78e9e98298ac92376aad7c408472584bf76af35aee6fb617`; recorded saved-weight SHA-256 is `db2b077174f5882062463449f4be5060532f7a01b169cd987b82cfbe21890946`. Cue changes from `9d3c97ae…` to `07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`, with saved-weight SHA-256 `7e6fe380553b20e23b63f5934199fb04a44388079ce3fcc68b0ccbb9e9602f26`. **Each fresh AFTER loaded-state receipt equals its own train-after state**, checked by the reducer. Full weight files are deliberately not copied/rehashed in this bounded reduction; saved-file hashes and native base/state checks remain captured measurements, not independent tensor measurements here.

The two arms preserve their development cue-loss policy through the adult fit. They differ in **whole prior trajectory and initial adapter**, not just the adult gradient switch. Original-denominator normalization removes one active-label averaging artifact; it does not make this a clean adult-only treatment comparison, an isolated learning-rate experiment, or an H2 slope.

## Source, reproducibility and limitations

Collection source: **`ea940ab1b82c99d4c3e9826aca632216097d0757`**. Training/BEFORE source: **`678faf15321124d3c74a2e9ab2be24f7624ba9f3`**. The commit difference adds the stage guard and coordination text; Python implementation bytes are unchanged. Frozen adult runner SHA-256 is `93e231d43aaba90b46965716b468c9e78f03b8d44198fefb7f3ace5964b19a51`; adult material SHA-256 is `bcb0a14f541f2d88f1f24f02a016d5e298568a66244f5218ba19f3611fe0cca1`. The captured source snapshot's1,369 Python files match exact Git blobs and remote/local hashes. Only source/evidence is copied, not base/tokenizer caches or full adapter tensors.

The complete `after_snapshot/` has **320 raw evidence files**, each independently matching its remote capture hash. `AFTER_FILE_VERIFICATION.json` retains these checks; `after_remote.sha256.txt` retains the capture timestamp and remote hashes. `ANALYSIS.json` and `AFTER_ANALYSIS.json` contain the complete reduction; the10:15:45 partial reduction remains `PARTIAL_ANALYSIS_101545.json`. No base caches, optimizer dumps or full adapter weights were copied.

Run against the complete immutable capture:

```bash
PYTHONDONTWRITEBYTECODE=1 python3 -B tools/astra_adult_cycle_reduce.py \
  --capture-root gpu_artifacts_local/astra_adult_cycle_first_result_20260914/after_snapshot \
  --source-root gpu_artifacts_local/astra_adult_cycle_first_result_20260914/source \
  --cue-capture gpu_artifacts_local/astra_adult_cycle_first_result_20260914/upstream/cue \
  --output gpu_artifacts_local/astra_adult_cycle_first_result_20260914/ANALYSIS.json
```

Exact test command: `PYTHONDONTWRITEBYTECODE=1 python3 -B -m unittest tests.test_astra_adult_cycle_reduce tests.test_experienced_event_adult_cycle tests.test_experienced_event_microloop -q`. **40 pass:**11 reducer,14 adult-material and15 strict-microloop tests. Tests cover pending/failed precedence, collection/source/target drift, original-denominator arithmetic, label/index corruption, strict raw probes, retained wrong goals, nested model-call joins and separate old retention. Import guards reject torch/transformers/tokenizers/peft; no native inference/tokenization is executed.

Across both BEFORE and AFTER states, the reducer replays **64 routing episode objects and224 readout model calls**, including32 separate old-retention probes. Collections add16 captured generation calls, not new calls by this audit. The last two AFTER receipts are cue `57bb4b58005163643721689a4bfda4eb777dd404cde73e291e6f62bfcb92e44b` and off `0376cd4e7f667756da40104340bb4d7e1a93ba08aea277597dae665034a9950e`.

| Stage | Cue finish UTC / duration | Off finish UTC / duration |
|---|---|---|
| Collection | 10:07:44.285653 /67.773s | 10:07:41.813804 /65.259s |
| BEFORE | 10:11:41.634023 /137.840s | 10:11:03.446809 /99.729s |
| Adult fit | 10:15:46.127437 /382.356s | 10:15:45.241488 /381.482s |
| AFTER | 10:18:00.151274 /132.927s | 10:17:29.280621 /103.061s |

AFTER cue makes78 calls (43 actor,15 reader,20 probes), off36 (16 actor,20 probes). These are stage wall durations including overhead, not billed GPU costs; dollar rates are not in the captured evidence.

Remaining limitations: n=1 per trajectory, same synthetic family/paired goals, repeated held banks, no parent, externally offered experience and receipt-format scaffolding, no swapped-record counterfactual, W8 retrieval corruption and continued unseen hallucination. Captured replay checks consistency, not authenticity against wholesale replacement of all records. Native receipt authentication and execution remain Main-owned. **All requested AFTER outcomes are terminal and reduced; there is no H1/H2 claim, new run, or review gate.**

## Supplement: W0 reader diagnostic; primary endpoint unchanged

Both `after_w0_reader` runs are terminal, parent-free readouts with **fits=0**, under immutable source **`4f8e21100131dbadec861c77f95d4d6e38bdd166`** at `/tmp/astra_adult_w0_source_20260914_attempt1`. Only this memo is extended; the released reducer/tests, running sources and cycle2 files are untouched. Small raw/source captures and the check output are in `gpu_artifacts_local/astra_adult_cycle_first_result_20260914/w0_supplement/`.

**Same adapters:** adapter paths, initial/adult input receipts, tokenizer/base bindings and loaded parameter-state hashes exactly match each arm's primary AFTER. Cue remains `07ecf4c5d965db5ea2765482439db3de5e230d90e0d86a99876a9c4ce6109300`; off remains `b0693f1a3645796f78e9e98298ac92376aad7c408472584bf76af35aee6fb617`. Both native receipts report unchanged frozen base. These are matching captured state measurements, not a new independent tensor inspection.

**Only configured inference change:** learned/disabled-reader user-message wrapper W8→W0, plus output directory. The source diff threads `reader_wrapper` into those reader calls; actor rules, tasks, decoding, external held text and standalone probe wrappers are unchanged. The memory-system message stays identical. The literal user-message change is:

```text
W8: Provide the exact stored personal-memory block at this address.
    READ EVENT <address>
    Output only the block.
W0: Retrieve the exact stored memory for this request.
    READ EVENT <address>
    Reply with only the stored memory block.
```

Raw replay confirms cue new-own **4/4**, READ **4/4**, second READ **2/4** (six actual learned-reader calls); reader-disabled remains **2/4** with two MISS reads per episode. Off stays **2/4 with zero READs**. Held remains cue8/8, off4/8. Both arms retain old W0/W8 recall4/4 each, new W0 recall4/4, new W8 recall3/4 and unseen MISS0/4. The complete standalone probe panels and held panels match the primary AFTER byte-for-byte. The check consumes all32 routing episodes and112 captured model calls (cue76, off36), with no new generation.

The previously wrong cue reader now returns this exact sourced record in supplemental `new_task/CALL_010.json` and `CALL_013.json`:

```text
EVENT E_3FIXU7HBPN AT N_Q5JLOL7SKZ DID P_XN2MTIYXOF GOT N_7G6JCNMNEO EVIDENCE R_IU33SBN5QW
```

Episode3 now takes `READ EVENT E_3FIXU7HBPN` → that correct record → `ROUTE P_XN2MTIYXOF`, reaching requested `N_7G6JCNMNEO` without the second read. This localizes the earlier failure to a wrapper-sensitive learned-reader output in these captures, rather than a bad stored training target; downstream actor history changes because the returned memory changes. Off never invokes its own reader, so its unchanged score is not evidence about using the alternate prefix.

**This is a post-result diagnostic, not endpoint substitution. Primary W8-based own-task performance remains cue3/4 (off2/4), and primary/direct W8 recall remains3/4 in both arms.** The supplemental W0-based4/4 does not replace those results, establish broader robustness, or change any H1/H2 claim. The two changed source files match their exact Git blobs; no broad custody pass, fit, rerun, new guard or independent commit was performed by this audit.
