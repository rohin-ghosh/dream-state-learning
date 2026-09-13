# Independent manuscript review — SEQ152/153 and completed constant diagnostic

Date: 2026-09-13. **REVIEW COMPLETE / EDITSTOP.**

## Verdict and scope

**ACCEPT the scientific reporting at the exact six hashes below, with one nonblocking archival-link/status correction (A1). No blocking numerical or claim-boundary mismatch found.** This accepts a bounded manuscript evidence cut, not the thesis, H1/H2, model equivalence, a working learning loop, publication, or any later experiment.

The reviewed author freeze is `/tmp/astra_manuscript_seq153_constant_result_handoff_20260913.md`, SHA256 `4e092f2050db634c00c3c8561a6d83e41894cad4ec7099cc60bca41aece30453`. It explicitly supersedes both earlier handoffs, and Main reconfirmed this final EDITSTOP during review. The earlier pending-constant caveat is **not** the version accepted here. The completed diagnostic is integrated in the current summaries, matching abstract additions, detailed TeX sections and C89.

Comparison used the hash-checked throughSEQ151/R1 text snapshot `/tmp/astra_manuscript_seq152_153_baseline_20260913.json`, SHA256 `ceb8e76768de3768482441927191d424cd296810320cc0783d45e36c22bfc131`, rather than Git. Review concerns the new SEQ152/153 reporting and its effects on earlier boundaries; it does not repeat the comprehensive review throughSEQ143 or the full memory-custody audit. **SEQ154 and all later outcomes are excluded.** No added diff line contains `154`; follow-up interaction and lower-LR outcomes remain explicitly pending at the named cut.

## Findings: severity, evidence, minimal correction

### A1 — Low / nonblocking: archive links and status lag Main's archival integration

- **Evidence:** `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:3902` links the constant JSON and Markdown to `/tmp`; line 3906 says they are not repository-archived/public evidence yet. Main subsequently reported archival integration under `64dda890`. Direct local reads confirm the `.py`, `.json` and `.md` now exist under `research_notes/astra_memos/receipts_20260912/`, byte-identical to the reviewed sidecars. No Git operation was used to authenticate the reported commit identifier.
- **Impact:** This is stale availability wording and a nonportable link, not an absent source, score discrepancy or pending-baseline result. Repository archival does not establish public release.
- **Smallest correction:** At Main's integration step, change the two links to `receipts_20260912/astra_actual_memory_constant_baseline_20260913.json` and `.md`; replace the availability sentence with “These diagnostic sources are repository-archived at the pinned hashes; public release is not established here.” Preserve both hashes and all scientific wording. Do not change the six frozen files during this review. If corrected later, rebind the changed claim-map hash; this acceptance does not automatically cover new bytes.

No high- or medium-severity correction is required. The earlier “constant baseline pending” concern is resolved by the final author freeze and is not a finding against these hashes.

## Accepted numerical reporting

### C88 — separate native greedy assay

Independently read the 64 archived request/response pairs, checked their native prompt metadata and returned prompt-token IDs, joined slot IDs and archived targets to the original world, and counted raw action answers. All 132 entries in the greedy capture's stage inventories match actual member-byte hashes; the archive has 165 members.

| State | View | Correct / exact-target | Old / new correct | Legal / stop-completed |
| --- | --- | --- | --- | --- |
| OFF | TRAIN | 8/16 / 8/16 | 4/8 / 4/8 | 16/16 / 16/16 |
| OFF | READOUT | 8/16 / 8/16 | 4/8 / 4/8 | 16/16 / 16/16 |
| fit2_PROMOTE | TRAIN | 14/16 / 14/16 | 7/8 / 7/8 | 16/16 / 16/16 |
| fit2_PROMOTE | READOUT | 8/16 / 8/16 | 4/8 / 4/8 | 16/16 / 16/16 |

The terminal receipt records 64 calls, zero fits, zero updates and 351.21178674697876 seconds, correctly rounded to 351.212. Comparing saved HF row decisions gives exactly one correctness disagreement: fit2_PROMOTE TRAIN slot0, HF correct with first-divergent gold margin 0.25, native incorrect. HF forced TRAIN 15/16 remains distinct from native 14/16. The completed C87 stored-receipt analysis is correctly described as a completed reduction, not fresh forwards or numerical model parity. Its prior full audit is source-bound here, not rerun.

Locations: `paper_prototype/main.tex:1288`, `paper_prototype/astra_sprint_draft_20260912.tex:3527`, claim-map C88. Checkpoint-specific exact-cue acquisition without READOUT improvement is supported; general capacity, pure-access explanations and HF/native interchangeability are not claimed.

### C89 — actual memory and interference

Independently reduced the archived row-level decisions, retaining every admitted row; paired held rows by ID, and compared held/canary raw outputs to original parent score archives. This is a saved-score reduction, not a new memory/core scoring run or native execution.

| Seed | Admitted / possible | WRITE exact P/B/S | WRITE paraphrase P/B/S | Held WRITE / LR0 | Held gains / losses | Canary WRITE / LR0 |
| --- | --- | --- | --- | --- | --- | --- |
| 0 | 14/16 | 8/7/3 | 6/4/0 | 44/47 out of 48 | 0/3 | 12/12 out of 12 |
| 1 | 8/16 | 7/7/0 | 5/5/0 | 37/48 out of 48 | 0/11 | 12/12 out of 12 |
| 2 | 8/16 | 5/5/0 | 5/5/0 | 17/48 out of 48 | 0/31 | 12/12 out of 12 |

P is source-faithful production eligibility, equal to content correctness on these rows; B is exact target bytes; S is strict canonical correctness. All corresponding LR0 memory numerators are zero. Held content and strict losses coincide. Seed0 has four unparseable held responses; seeds1/2 retain 48/48 exact-format responses despite 11/31 content losses. No held response is length-terminated. WRITE raw held changes versus the original parents are 4/11/31; LR0 held/canary raw responses remain unchanged, as do WRITE canaries.

Dataset members independently yield 14/8/8 admitted rows, 4/5/5 raw targets, 3/5/5 semantic content records, 2/4/3 triples and eight represented episodes per learner. Completion and fit manifests confirm 176/152/152 calls per pair; 112/64/64 steps per arm; eight epochs and rank8; totals 480 calls, six fits and 480 steps, split 240 WRITE / 240 LR0. LR0 optimizer steps are not treated as weight changes.

Locations: `paper_prototype/main.tex:1303`, `paper_prototype/astra_sprint_draft_20260912.tex:3542`, claim-map C89 and current README/collaborator summaries. Interference is prominent rather than hidden by canary success. Raw-target/EOS supervision, source-withdrawn cold cues retaining schema instructions, original inherited perception adapters, external formation scaffold/mandatory priors and imported ancestry are explicit. Training/provenance details remain tied to the prior custody evidence; this review does not independently reconstruct the entire training pipeline.

### Completed constant diagnostic — evaluator-only, not an executed arm

Rechecked the completed JSON's candidate maxima, score differences, output uniqueness, wrong-key counts and seed0 paraphrase correct-ID agreement without rerunning the scorer or diagnostic script.

| Seed | Best constant, either view | WRITE exact (difference) | WRITE paraphrase (difference) | Raw response variants exact / paraphrase | Wrong-key repertoire exact / paraphrase |
| --- | --- | --- | --- | --- | --- |
| 0 | 6/14 | 8/14 (+2) | 6/14 (+0) | 2 / 1 | 6 / 8 |
| 1 | 4/8 | 7/8 (+3) | 5/8 (+1) | 4 / 2 | 1 / 3 |
| 2 | 4/8 | 5/8 (+1) | 5/8 (+1) | 2 / 2 | 3 / 3 |

All 60 WRITE memory responses are semantic members of their own training repertoire. Seed0 paraphrase literally emits one raw record on all 14 rows and matches an oracle maximizer's exact six correct IDs. Seed0 exact repeats content across the differing turns of its six admitted two-turn episodes; seed1 has partly appropriate nonconstant assignment; seed2's extra success is one correct minority-record selection, with exact/paraphrase raw outputs identical on all eight corresponding rows. These are limited response-assignment observations, not a general binding mechanism.

The detailed text explicitly states retrospective choice of an unchanged admitted raw target after seeing the evaluation executions, frozen scoring and hypothetical stop completion. Exact advantages exclude only the best single admissible fixed-response alternative on these finite panels, not repertoire switching, heuristic cues or key-binding failures. A constant cannot attain the three exact aggregate counts, but seed0 paraphrase is literally constant. There is no executed baseline, new output, ID intervention, fresh-record test or causal proof. This distinction is correct and retained at `paper_prototype/main.tex:1339`, the matching sprint section, all current banners/abstract additions and claim-map C89.

## Accepted versus pending boundaries

- **Accepted:** narrow source-faithful carriage on saved exact/paraphrase panels; substantial paired held interference; insensitive canaries; finite-panel evaluator-only constant comparison; native exact-cue accuracy separately from HF forced choices.
- **Accepted as attributed custody evidence, not newly reaudited:** local inventory/raw-response bindings, imported dependencies, object-preserving capture reserialization, recorded controller exits, wrapper-attested worker release, and tensor-payload comparisons. Recorded delta norms are not represented as independently recomputed arithmetic. No claim of live release/vacancy follows.
- **Pending or unestablished:** causal/general key association, selective retention, stable capacity, fresh post-memory learning, lower-LR repair efficacy, native/HF numerical parity, clean lineage, matched parenting, general G3, H1/H2, a working learned loop, freeze and mission completion. The held repair panel is correctly labeled exploratory and requiring fresh confirmation. No SEQ154 outcome was inspected or imported.
- Earlier SEQ146 canary harms, SEQ149 formation/missing-prior limitations and SEQ151 forced-candidate definitions remain in the bounded prior text; new success is not used to erase them. Old pending language is contextualized as historical, rather than overriding the current results.

## Exact six reviewed manuscript hashes

| File | SHA256 |
| --- | --- |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `a7513cbdb039820c1a9d22f50b154c4b1006e5d20ff6383b3d23f2b8c353376c` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `9af3f7223a51e6933350b265dedf712b4a7389844bc05a098f4accd75164e2fb` |
| `paper_prototype/main.tex` | `94796c4eeabd1e626a187eae0a3e6084dd7e2adfb8de60103a8016419b0e13be` |
| `paper_prototype/README.md` | `24b3114a5d90f4c1091570d6875eee70843c5e90656e1f253050ccfcad5abb6e` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `65b562751b6bfd85f82086a843b278a78d72bf9b6ae3178e7b6cc9f084b350e9` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `b0879100e348c8af18d989fc3af8cef819550d78624c735ee603559f156ad5ca` |

## Evidence hashes independently read

The following receipt paths are relative to `research_notes/astra_memos/receipts_20260912/`.

| Receipt | SHA256 |
| --- | --- |
| `astra_l2_high_seed2_greedy_report_20260913.json` | `62c01302d039093aef7e87ff2dfe5b28e5633c700d2d78ea3c775decf8d3b062` |
| `astra_greedy_receipt_replay_20260913.json` | `d1bcb45ea778b130bdd5d36f4a1967ac1055f4a3da759c3581d7d70571561fbf` |
| `astra_l2_high_seed2_independent_analysis_20260913.md` | `6d4f46be4b13b62e1c618f6543e7e171df9e5008e46b45cc9cf94aae47552dec` |
| `astra_l2_access_high_seed2_report_20260913.json` | `9cb95809b5ff658c45e39a21a522433d666b2696af8feda698ef2d951604346b` |
| `astra_actual_memory_analysis_result_20260913/analysis.json` | `7bf30652548ed36800f8f1c5ee0c9a34dc79409d50c95b9818ce103364ebd323` |
| `astra_actual_memory_analysis_result_20260913/analysis.md` | `e0d1ee714c0a8f277f281015d789dcac1c8d7c288df8d52b02a06565400ee314` |
| `astra_actual_memory_custody_audit_20260913.md` | `d551d9c493cdbb124c0fbee576f4b7b68d028e24e6d4b5a5a606b1c37c046a26` |
| `astra_actual_memory_constant_baseline_20260913.py` | `7ce67798d393ce0feeae040a85c814482647220f9227ee34df60ffacae3cf14b` |
| `astra_actual_memory_constant_baseline_20260913.json` | `08bdf7627df6eb5d690530faa1784716da2cd9a520ca52556ad7342ee76740af` |
| `astra_actual_memory_constant_baseline_20260913.md` | `b0798484c941436f990393f80e13e73ed68b3ead5779e7ddf38e3f3291b1bbb9` |

The last three are byte-identical to their same-basename `/tmp` originals; all six manuscript pins agree with the final handoff.

| Raw local archive | SHA256 |
| --- | --- |
| `gpu_artifacts_local/l2_public_record_20260913/astra_l2_high_seed2_greedy_20260913_attempt1.tar` | `94b4c06968744cd9ef3b79b40e7e61363167a88ae04394827aab85a2120fd124` |
| `gpu_artifacts_local/l2_public_record_20260913/astra_l2_lr_seed2_high_attempt1.tar` | `d5f91bc56a57a48aad204e1dd3dd8b972c58b97f16d518627e726f8f8cf7082c` |
| `gpu_artifacts_local/actual_record_memory_20260913_attempt1/evidence.tar` | `3ed6579e7e885139d78faf3457eb3bec254215d36b533558ef22f8199ff6a003` |
| `gpu_artifacts_local/level1_second_roster_20260913/node2_second_perception.tar` | `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a` |

Selected member hashes checked directly: original greedy world `32a0bc76549042443fe709682f993def1680548edac72d6280d3d4d8f886883a`; memory seed0/1/2 collected scores respectively `b56a0caa16259e29860efa284d283610ab9bfa9064c64f121fe7cc34266b72bf`, `5fe7638aa86e718b36ea00f9a97b9e36acbed4b464c968737acbc86447c71979`, `a0182417e86e85ab6a874c7e98d77fd5952e2bb036fe1a2e35d6e7289ecb0cef`.

## Validation performed and limits

Read-only stdlib checks completed successfully: handoff/snapshot/file hashing, six-file bounded diffs, preservation of prior float tables and citation commands, equality of the new detailed TeX sections and three new abstract paragraphs, raw greedy target/world/prompt joins, greedy inventory hashes, saved memory metric reduction and parent-row comparisons, material diversity counts, work totals, constant-result internal arithmetic/uniqueness/ID checks and local/archive source equality. Six final hashes were stable at the closing check.

The author's 97-check receipt is separate evidence (SHA256 `1398584f58505fbbb4b3db53deaa590e4341dcd1c69d339839102e7b1f3623f1`); this review does not claim to rerun those 97 checks. No repository test suite, LaTeX/PDF build or visual layout check was run. No full HF reduction, full memory custody audit, tensor arithmetic or frozen scorer was rerun. No model, tokenizer, native runner, collector, GPU, process-vacancy check, remote operation, web lookup, archive extraction, Git command or repository edit was performed. References are unchanged and no new outside-source claim required lookup.

The constant sidecar was already stopped; it was only read/hashed here. This review adds exactly `/tmp/astra_manuscript_seq153_independent_review_20260913.md`. No other file is changed by this review. Main retains ownership of claims, staging, archival-link integration and any later review request.
