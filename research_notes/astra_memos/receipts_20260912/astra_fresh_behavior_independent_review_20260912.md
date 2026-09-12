# Independent bounded first-ACT review — fresh-behavior panel

September 12, 2026, approximately 17:28 UTC. Independent Codex review; no model execution.

## Verdict

**PASS for the reported full-16 first-ACT endpoint, exact solved grids, condition completeness, OFF agreement, and archived custody consistency. No numerical or solve-validity discrepancy found.** This is **mixed-exposure exploratory development evidence**, not a comprehensively fresh panel or untouched confirmation.

The original complete 16-item primary remains unchanged. No item removal, favorable subset endpoint, replacement, new seed, old-root rescue, or rerun is proposed. Main's pre-outcome full-panel decision is preserved. Timing/cost aggregation and durable integration remain Main's work.

Read-only review of the supplied capsule and relevant local protocol/source/notebook text. No Git commands, repository edits, network, GPU queries/jobs, parent jobs, or native model/dataset execution. Archives were read in memory without extraction. I used an independent, small CPU backtracking solver over the frozen 4×4 givens; no repository reducer or model was executed. The only written file is this requested `/tmp` report.

## Capsule and reference notation

- Capsule: `/tmp/astra_fresh_behavior_terminal_20260912.tgz`.
- Independently verified SHA256: **`583d02e71e983169491ec8f5d2e37ae582c74b8aae0aa3c3f7091572c8ba489e`**.
- Archive root, abbreviated **R/** below: `astra_fresh_behavior_panel_20260912_attempt2/`.
- `R/first_act_report.json` SHA256: **`8e1990b4f3787fd5ef1ae60e5c0141872c9d91e11934edb6431158749582b99a`**, matching `R/main_release.json`.
- `R/panel.json` SHA256: `8e6e9c6d0e589b0509f61935d198ffe556aec3dc45dc5f5e3d7f527a1c7d5a9d`.
- Frozen reducer pin: `eafe8cccf04cd3f8aaedd2d1fc2fde710a2aa8cae155d8de7ce03ebb04eced0d`. The locally inspected `organism_v6/fresh_behavior_panel.py` matches this pin; it was not executed.
- JSON references identify archive members and their keys. JSONL evidence references below give actual line numbers.

## 1. Full original primary — independently verified

| Optimizer seed | Useful ON | Its useful OFF | Corrupt ON | Its corrupt OFF | Useful ON−OFF | Corrupt ON−OFF | Difference of gains |
|---|---:|---:|---:|---:|---:|---:|---:|
| 0 | 3/16 | 0/16 | 0/16 | 0/16 | +3 solves | 0 solves | +3 solves |
| 1 | 3/16 | 0/16 | 0/16 | 0/16 | +3 solves | 0 solves | +3 solves |
| 2 | 3/16 | 0/16 | 0/16 | 0/16 | +3 solves | 0 solves | +3 solves |

Difference-of-gains vector **[3, 3, 3]**, descriptive mean/median **3**, range **[3, 3]**. These are solved-count differences on the shared full panel, not independent learner/task significance evidence. Useful ON improves over its actual paired OFF in every seed; the positive contrast is not produced merely by corrupt-arm degradation.

Verified original ordered IDs:

`1900071, 1900072, 1900073, 1900075, 1900076, 1900077, 1900078, 1900079, 1900080, 1900081, 1900082, 1900083, 1900084, 1900085, 1900086, 1900087`, all under `rg/mini_sudoku/`.

All **3 optimizer seeds × 2 material arms × 2 adapter states = 12 conditions** contain this same ordered 16-item panel: **192 episode-condition observations**. Every episode has exactly one recorded ACT; all 192 first-ACT statuses are measured. No missing-worker, missing-artifact, missing-ACT, or unmeasured cell was silently converted into a scientific zero.

Each condition also has 16 later scratchpad generations. Thus the raw generation logs contain **32 requests/outputs per condition, 384 requests/outputs total**, including **192 wake generations** and **192 scratchpads**. Scratchpad text is not another live ACT, a retry, or an alternative primary answer. I did not substitute a best attempt, scratchpad output, or partial-credit score for the first-ACT solve.

Evidence: `R/first_act_report.json` `seeds`, `solved_count_gain`, and `episode_ids`; all 12 `R/probes/seed{0,1,2}_{useful,corrupt}/{off,on}/results.json` and corresponding episode/generation logs. Protocol endpoint: `research_notes/astra_memos/ASTRA_FRESH_BEHAVIOR_PANEL_PROTOCOL_2026-09-12.md:43` and line 52.

## 2. Independent grid verification and raw solved IDs

### Method

For **all 16 frozen puzzles**, I independently enumerated completions using only their recorded givens and ordinary 4×4 Sudoku constraints: each row, column, and 2×2 block contains 1–4 exactly once. Every puzzle has **exactly one completion**, and that completion equals both `panel.records[].solution` and `entry.metadata.solution`.

For **all 192 first ACTs**, I independently extracted the first line-start `ACT:` from the corresponding raw wake response and checked it against the ledger action. I then parsed the submitted four-row grid and compared it to the independently solved puzzle. There were **zero disagreements** between this exact solve test and native `score == 1.0` or the report's binary first-ACT endpoint. Raw ledger scores also agree exactly with the report's recorded/native score fields in every cell. Native fractional-credit scores were not independently re-derived; the independent verification here concerns exact solves.

All first wake prompts equal the corresponding frozen `panel.records[].q` bytes. The solve checks use the pre-action frozen puzzle, not an answer inferred from later scratchpad or outcome text.

### Solved cases, with exposure annotations only

“Not in known four” below means **not identified by the supplied four-ID exposure audit**. It does **not** mean fresh, never examined, untrained-on, or free of other exposure. No exposed/unexposed subset score is computed.

| Optimizer seed, useful ON | Solved episode ID | Known correction-utility exposure? | First-ACT ledger member under R/ | Raw wake-output line in that condition's `generations.jsonl` |
|---|---|---|---|---:|
| 0 | rg/mini_sudoku/1900083 | Not in known four; freshness unverified | `probes/seed0_useful/on/episode_0011.jsonl:2` | 46 |
| 0 | rg/mini_sudoku/1900085 | Not in known four; freshness unverified | `probes/seed0_useful/on/episode_0013.jsonl:2` | 54 |
| 0 | rg/mini_sudoku/1900087 | Not in known four; freshness unverified | `probes/seed0_useful/on/episode_0015.jsonl:2` | 62 |
| 1 | rg/mini_sudoku/1900071 | **Yes** | `probes/seed1_useful/on/episode_0000.jsonl:2` | 2 |
| 1 | rg/mini_sudoku/1900082 | Not in known four; freshness unverified | `probes/seed1_useful/on/episode_0010.jsonl:2` | 42 |
| 1 | rg/mini_sudoku/1900083 | Not in known four; freshness unverified | `probes/seed1_useful/on/episode_0011.jsonl:2` | 46 |
| 2 | rg/mini_sudoku/1900073 | **Yes** | `probes/seed2_useful/on/episode_0002.jsonl:2` | 10 |
| 2 | rg/mini_sudoku/1900083 | Not in known four; freshness unverified | `probes/seed2_useful/on/episode_0011.jsonl:2` | 46 |
| 2 | rg/mini_sudoku/1900087 | Not in known four; freshness unverified | `probes/seed2_useful/on/episode_0015.jsonl:2` | 62 |

Each listed ACT satisfies the frozen givens, all row/column/block constraints, and the independently enumerated unique solution. Exact submitted grids, with semicolons separating rows:

| Episode suffix | Verified submitted solution |
|---|---|
| 1900071 | `3 1 4 2 ; 4 2 3 1 ; 1 3 2 4 ; 2 4 1 3` |
| 1900073 | `2 3 4 1 ; 1 4 2 3 ; 3 2 1 4 ; 4 1 3 2` |
| 1900082 | `3 4 2 1 ; 2 1 3 4 ; 1 3 4 2 ; 4 2 1 3` |
| 1900083 | `3 2 1 4 ; 1 4 3 2 ; 2 1 4 3 ; 4 3 2 1` |
| 1900085 | `3 4 1 2 ; 1 2 3 4 ; 4 3 2 1 ; 2 1 4 3` |
| 1900087 | `1 4 3 2 ; 2 3 1 4 ; 4 1 2 3 ; 3 2 4 1` |

Repeated successful IDs use the same correct grid, but different optimizer seeds do not solve identical sets of IDs. No corrupt ON or OFF condition contains an independently valid first-ACT solve.

## 3. OFF/common-input and control completeness — PASS

- All **six separately captured OFF** action/score vectors are exactly equal, in the original panel order. All six complete raw output sequences are also equal, including wake and scratchpad outputs. This is stronger than merely equal aggregate solve counts; it is not byte equality of whole ledgers with timing/process metadata.
- Across all 12 conditions, per-generation request seed vectors match; temperature is 0.7 and caps alternate wake 400 / scratchpad 100. Every first wake prompt is the same frozen board prompt for that ID. Optimizer seeds 0/1/2 refer to the inherited adapters, not three different decoding-seed treatments.
- Each OFF request records `adapter_input: null` and empty `adapter_files`. Each ON request's configured adapter path and adapter-file hashes match the corresponding seed/arm in Main's `actual_adapters` receipt. All six ON tensor hashes are distinct; useful/corrupt or seed identities were not silently swapped in the recorded requests.
- Six complete paired receipts, twelve worker completion receipts, twelve condition manifests/results, twelve cleanup receipts, and all 192 episode ledgers are present. The three seed execution summaries each report both useful and corrupt complete, zero fits, and GPU processes absent, with final full release recorded separately by Main.
- All conditions preserve one first-ACT observation per original item; no surviving treatment lacks its paired OFF or corrupt control.

The repeated OFF observations do not create six independent baselines for significance testing. Same training data, one shared panel, fixed useful-then-corrupt order, and possible time/device effects remain limitations. The existing `R/panel.json` and `R/first_act_report.json` limitation lists correctly retain these boundaries.

## 4. Archived custody completeness and limits — PASS within the capsule

Independently recomputed:

- **304/304** `first_act_report.input_sha256` entries resolve to archived files and match their hashes; no missing or mismatched reducer input.
- **15/15** top preparation-manifest file hashes match, including the frozen panel, preflight, candidate audit, and six spec/hash-file pairs.
- **240/240** file hashes listed across the twelve condition manifests match, including configurations, generation logs, results, source checks, and all sixteen ledgers per condition.
- Each spec matches its detached SHA file and paired receipt. Each worker's manifest/results/spec hashes agree with the corresponding files; each embedded paired worker receipt agrees with its standalone `_WORKER_DONE.json`, whose file hash matches `PAIR_DONE.receipt_sha256`.
- All twelve cleanup receipts record `cleanup_error: null`, empty owned group, absent GPU processes, and verified reservation release. Cleanup files are also covered by the report's input hashes.
- The report hash matches Main's release receipt; the local helper matches the archived reducer pin. No alternate current-source reducer was substituted in this review.

`R/main_release.json` records Main's final verification at **2026-09-12 17:24:03.316192 UTC**, with devices **1/2/3**, current six-adapter/model hash inventories, frozen source snapshot, and zero new fits. Its source snapshot identifies `/localhome/local-rohing/astra_sources/e67539d2ec7a76681e992aac2c83e118fa4740c4`.

**The capsule contains no weights.** Recorded adapter hash agreement is not this review independently rehashing the six current remote tensor files, authenticating official model origin, inspecting loaded tensors, or providing a complete training/model backup. Those current-byte/source/device checks remain attributed to Main's native receipt. `UNRESOLVED_LOCAL_HASHES_ONLY` remains the origin status. Archived release is not a fresh live vacancy guarantee.

## 5. Exposure, chronology, and claim disposition

The four known-exposed selected IDs remain **1900071, 1900072, 1900073, 1900075**. This is prior research/model-readout exposure; it is **not evidence that the six inherited adapters were trained on these puzzles**. Exact solution-grid nonoverlap against an earlier limited inventory does not establish comprehensive freshness, nonisomorphism, or absence from pretraining.

Evidence for the retained interpretation:

- `R/main_release.json` explicitly warns that these four IDs have earlier correction-utility readouts and labels the result mixed-exposure development only.
- `research_loop/COORDINATION.md:4903` records the pre-result exposure audit and the omitted additional registry.
- `research_loop/COORDINATION.md:4954` records Main's acceptance of the exposure finding. Lines 4958–4967 explicitly declare, before inspecting outcomes, completion of all control pairs and retention of all 16 original items, with no favorable subsetting/replacement/new seed or current-source endpoint substitution. This review reads that contemporaneous declaration; it cannot independently establish a person's private knowledge state beyond the record.
- The protocol at `research_notes/astra_memos/ASTRA_FRESH_BEHAVIOR_PANEL_PROTOCOL_2026-09-12.md:65` already excludes untouched confirmation and broader qualification.

**No fresh-subset rescue is calculated or recommended.** The solved-ID exposure labels in this report are descriptive annotations only; the sole reported primary is the complete original 16 in every condition. Names such as “fresh behavior” or inherited prompt boilerplate are not evidence that freshness was achieved.

### Findings and smallest integration action

**No new blocking numerical, raw-action, grid-validity, control-completeness, or archive-hash finding.** The known exposure omission is a consequential claim limitation already accepted by Main, not something to erase by favorable rescoring. The smallest integration action is to carry this qualification next to every headline/table:

> On the complete original 16-item mixed-exposure development panel, all three useful adapters solve 3/16 first actions versus their actual OFF 0/16; corrupt ON and OFF each solve 0/16. This is an exploratory zero-new-fit reread, not fresh-panel confirmation or comprehensive generalization evidence.

Do not pool the 192 correlated cells into independent replication, infer parenting/internalization/H1/H2/G2 qualification or a mechanism freeze, or promote the known-unexposed-by-this-audit cases into a new endpoint. No additional scientific gate, external circulation, model run, or old-root training approval follows from this bounded review.
