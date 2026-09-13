# Independent manuscript review — bounded extension through SEQ151

Review date: 2026-09-13 UTC. Reviewer: independent Codex manuscript reviewer, not the manuscript author or GPU operator.

## Verdict and scope

**ACCEPT the six-file extension for bounded manuscript integration. No blocking, high-severity, or medium-severity finding; no load-bearing numeric correction required. One low-severity terminology clarification is recommended below.** Acceptance applies only to the exact six SHA256 values in this review, not to later edits, scientific promotion, a launch, or external distribution.

Reviewed the Copernicus handoff and six-file changes through SEQ144–151/C83–C87. Did not redo the comprehensive review through SEQ143. Earlier accepted findings were used only as explicitly scoped carry-forward context; the original high-seed2 world/readout was inspected solely to verify the new HF comparison. Both added TeX result sections are byte-identical, and the three added abstract paragraphs are byte-identical. The 32 prior table environments in the sprint TeX and 15 in main TeX remain verbatim; citation commands are unchanged. Scoped `git diff --check` passes. References were not re-reviewed; no new external source claim required checking.

Read-only local evidence inspection and independent stdlib arithmetic only: no remote operations, web, model imports, generation, training, GPU work, archive extraction, repository edits, staging, commits, or reversion. Main retains all operational ownership. Author-side “158 checks PASS” was not treated as independent evidence. This review is the only file created.

## Findings: severity, evidence, minimal correction

| ID / severity | Evidence and disposition | Minimal correction |
| --- | --- | --- |
| R1 / Low, nonblocking | The new abstract calls the HF statistic “first-token” likelihood (`paper_prototype/astra_sprint_abstract_20260912.md:416`, `paper_prototype/astra_sprint_draft_20260912.tex:286`, `paper_prototype/main.tex:127`); the C87 tables abbreviate it as “first.” Raw worker target IDs show that the two candidates share **two** target tokens and first diverge at zero-based index 2 in all 96 comparisons. This is the first *divergent decision token*, conditional on the shared forced prefix, not the first generated token. The explicit forced-candidate/native-greedy caveats prevent a substantive overclaim, and all counts reconcile. | In the three new abstract paragraphs, replace “first-token” with “first-divergent-token.” Add one C87 definition beside each TeX table: “First denotes the first divergent candidate token after the shared two-token prefix.” No rescoring or changed count is needed. |
| G1 / No defect; retain explicit boundary | SEQ146 harms are present in both detailed TeX sections/tables, C84, README, abstracts/current banners, and the UNSENT update. Raw preserved scores show two repetition copy truncations and one meta-reflection malformed-JSON canary, not a blanket preservation success. | None. Keep the three learner-item regressions and restrict the older C81 no-harm statement to its original roster. |
| G2 / No defect; retain explicit boundary | SEQ149 describes a fresh external instruction bundle, mandatory priors versus v1 optional priors, all 64 explicit/unambiguous execution priors, different realized experiences, nested failures, and nonrandomized turn strata (`paper_prototype/main.tex:1175`, `paper_prototype/astra_sprint_draft_20260912.tex:3414`, claim map C85). Null returned predictions are not genuinely missing source predictions. | None required. Do not generalize these results to absent/ambiguous-prior performance. If condensed later, preserve “no absent or ambiguous priors were tested” rather than dropping the all-64-explicit qualification. |
| G3 / No defect; retain explicit boundary | C87 and the summaries distinguish HF forced candidates from native greedy TRAIN, retain OFF/fit1/fit2 and ties, and withhold pure-access/general-acquisition conclusions. Detailed text retains unequal 12/14-token targets and teacher forcing. The lower-loss checkpoint motivation is explicitly exploratory in C87 and its protocol. | None beyond R1. Do not relabel 15/16 as native exact-TRAIN accuracy or as a general-capacity result. |
| G4 / No defect; pending result remains pending | Both TeX texts explicitly state no native write or retention result; summaries and C85 keep actual-memory writing/readback at protocol/CPU-development status. | None. No actual-record memory-write, readback, retention, or learned closed-loop result may be inferred from formation acceptance or runner preparation. |

## Independently checked numeric evidence

### C83 / SEQ145 — separate high-LR seed0 recovery

Read the preserved attempt2 archive, decoded all five native readout receipt panels against that archive's world truth, and summed per-stage recorded costs. Recovered **128 calls, 3 fits, 100 updates**. Each panel—baseline, report1 PROMOTE, report1 SHADOW, report2 PROMOTE, report2 SHADOW—has **old 4/8, new 4/8, legal 16/16**. Final itemwise PROMOTE/SHADOW pairing is **both 8, PROMOTE-only 0, SHADOW-only 0, neither 8**. The pinned collection records first/cumulative admitted records **8/16**. These support zero observed treatment contrasts, not no parameter change.

**Accepted:** this separate attempt-labelled recovery. The completed six seed/rate combinations use the previously accepted completed cells and low recovery plus this high recovery; this review does not reopen those older experiments. **Still missing:** the original two seed0 attempt endpoints. Neither recovery imputes them or makes the original six-attempt roster complete.

### C84 / SEQ146 — second authored roster and canary harms

Read all 12 archived `*_collected/scores.json` payloads; their individual hashes match the analysis's per-cell evidence pins. Independently summed the saved row-level content/strict decisions for all 48 panels/1,440 rows, matched OFF/post rows for losses, and summed calls/updates. This is an independent reduction of stored frozen decisions, not a new execution of the original scorer or fresh model inference.

| Skill | OFF content/strict /48 | Post content = strict /48, seeds 0/1/2 | Post canary content = strict /12, seeds 0/1/2 |
| --- | --- | --- | --- |
| Perception | 21 / 0 | 47, 48, 48 | 12, 12, 12 |
| Repetition | 0 / 0 | 48, 48, 48 | 11, 11, 12 |
| Self-reflection | 0 / 0 | 48, 48, 48 | 12, 12, 12 |
| Meta-reflection | 9 / 9 | 48, 48, 48 | 12, 12, 11 |

All OFF canaries are 12/12. Every cell has material seed 0, 120 calls, and 320 updates: **12 fits, 1,440 calls, 3,840 updates**. Perception mean is 143/3 = **47.667 rounded**, range [47,48]; other means/ranges are 48/[48,48]. No held-content paired losses. Combining these with the accepted first-roster totals gives **24 completed cells, 2,880 calls, 24 fits, 7,680 updates**, not total campaign cost including failed runs or formation.

Raw preservation failures, checked in archived score rows against their OFF counterparts:

- Repetition seeds 0 and 1, the same `copy:canary:repetition-meta-4:skin2`: OFF `{"answer":"rehearse? wait"}` becomes `{"answer":"rehearse"}`.
- Meta-reflection seed 2, `arithmetic:canary:repetition-meta-5:skin1`: OFF `{"answer":241}` becomes malformed `{"answer":241"}`.

**Accepted:** controlled authored-component observations with these harms. Three learner-item regressions do not mean three independent task discoveries. Shared material and no-update OFF are not matched trained parenting, general cognition, executed reflection, compiler admission, or actual child SLEEP. The prior replay receipt reports 1,440 original objects and 48 panels exactly replayed; this reviewer independently checked the numeric reduction rather than claiming to repeat that entire replay.

### C85 / SEQ144,149 — actual-record formation under scaffolding

Read all eight archived formation captures across v1/v2. V1 has **64 wakes, zero executions, zero records**: missing record opportunities, not 64 observed wrong extractions. V2 has **64 wakes plus 64 record calls = 128 calls**, with 16 executions and records in every state. Independently compared every parsed v2 raw record's schema, triple, observed outcome, predicted value, and relation against its saved execution. Independently recomputed strictness using the pinned core's sorted, compact canonical JSON definition. The original core was read, not executed.

| V2 state | Eligible /16 | Strict /16 | Turn 1 /8 | Turn 2 /8 | Rejected | Returned null prior despite explicit source |
| --- | --- | --- | --- | --- | --- | --- |
| OFF | 7 | 0 | 5 | 2 | 9 | 3 |
| Perception seed0 | 14 | 6 | 8 | 6 | 2 | 2 |
| Perception seed1 | 8 | 0 | 4 | 4 | 8 | 8 |
| Perception seed2 | 8 | 0 | 0 | 8 | 8 | 5 |

Total eligible **37/64**, rejected **27/64**. OFF rejections comprise 3 prediction and 6 relation mismatches; seed0 has 2 prediction mismatches; seed1 has 8 prediction mismatches; seed2 has 5 schema failures and 3 prediction mismatches. All top-level turn error arrays are empty; nested record errors remain substantive.

All 64 saved executions have boolean, unambiguous priors: OFF/seed0/seed1 are false on all 16, while seed2 is true on 11 and false on 5. Thus absent/ambiguous-prior handling is **not measured here**. Eight seed1 nulls are wrong extractions of explicit false priors, not unavailable evidence. Independent triple counts confirm the literal [2,5,9] example occurs **2/64** times, and seed2 shares **0/16** aligned triples with OFF. OFF shares 14/16 with seed0 and 13/16 with seed1; even aligned triples do not ensure equal prior record histories.

**Accepted:** state-dependent, source-faithful child record formation under an external schema/source/prompt scaffold. **Not accepted as established:** learning from v1 to v2, an isolated ACT-prefix causal effect, matched parenting or a record-only causal contrast, hidden-rule discovery, in-run learning from turn2 changes, or absent-prior competence. The v2 prompt changes and mandatory-prior restriction remain visible in the manuscript. No rejected answer was repaired for this review.

### C86 / SEQ147,148,150 — infrastructure only

Verified the local JIT archive hash and its `INFRASTRUCTURE_SMOKE_PASS` result; read the pinned long-root failure inspection; independently hashed the short-root archive, counted **40 unique members = 26 regular files + 14 directories**, checked its result pin, inspected before/after model manifests, and checked its two-token response. Both before/after manifests report all **14** expected payloads matching and are byte-identical. The short-root result reports `OFF_NATIVE_READINESS_PASS`, one OFF load/generation, **2 returned tokens**, and elapsed time **175.895728 seconds**, consistent with 175.896 rounded. This verifies stored receipts, not new hashes of a remote model or fresh execution.

**Accepted:** one bounded OFF readiness pass, separate from the earlier tiny smoke and long-root IPC failure. The existing inspection binds regular-file verification and point-in-time release. No OS exit-code receipt exists; three socket nodes survive as metadata only. Whole-host invariance or sole repair causality is not established because the separate system-ninja installation has unresolved timing. LoRA load/training, long contexts, concurrency, hardware parity, and scientific efficacy remain unqualified. The original failed science attempts are not retroactively repaired.

### C87 / SEQ151 — forced-candidate likelihood, not native greedy TRAIN

Matched the three archived raw worker hashes to the report. Independently recomputed **96 paired decisions / 192 candidate forwards** from saved per-token log probabilities, rather than merely summing the report's correctness flags. Joined all report truth indices to the preserved original high-seed2 world; also decoded the original native report2 PROMOTE readout, which remains **8/16**. Verified target masks against target IDs and the **12/14** target lengths in every candidate pair. All workers report zero updates.

| State | TRAIN first-divergent/full /16 | TRAIN first ties | READOUT first-divergent/full /16 | READOUT first ties |
| --- | --- | --- | --- | --- |
| OFF | 8 / 8 | 0 | 8 / 8 | 0 |
| fit1 | 9 / 11 | 3 | 7 / 9 | 3 |
| fit2 PROMOTE | 15 / 15 | 0 | 8 / 8 | 0 |

All full-score ties are zero. Exact first-score ties were retained as unresolved, not broken in favor of a candidate or subjected to a new tolerance. Fit2 TRAIN old/new = **8/8 and 7/8**, READOUT old/new = **4/8 and 4/8**, for both metrics. Every recomputed margin and correctness flag matches the report.

**Accepted:** stronger checkpoint-specific discrimination between the two supplied candidates under exact TRAIN wording, with a prompt-dependent READOUT gap. **Pending/unestablished:** native greedy exact-TRAIN accuracy, full-vocabulary generation equivalence, a pure-access mechanism, or general learning capacity. Forced continuations, the shared forced prefix, unequal target lengths, and exploratory checkpoint choice prevent those inferences.

The handoff's separately named HF independent-analysis artifact remains pending/not incorporated at this manuscript cut. This review supplies independent arithmetic/raw-evidence verification; it does not claim that separately commissioned full analysis arrived, alter its status, or incorporate any later native outcome.

## Accepted versus pending claims — integration boundary

- **Accepted within the stated assays:** C83 attempt2 completion and zero observed contrasts; C84 authored gains with all three canary harms; C85 scaffolded formation counts with explicit-prior restriction and state-dependent histories; C86 bounded infrastructure receipts; C87 checkpoint-specific HF forced-candidate counts and prompt gap.
- **Pending or unclaimed:** actual-record native memory-write, readback and retention; native greedy exact-TRAIN; the separately named HF analysis; matched trained parenting; learned closed-loop improvement; H1/H2; general G3; clean lineage; mechanism freeze; mission completion. No actual-record write/readback result is supplied by this review.
- **Not certified:** GPU/model-origin authentication beyond preserved custody evidence, fresh execution, rendered PDF/layout/page count, or comprehensive throughSEQ143 scientific review. No TeX build, installation, or test suite execution was performed. Collaborator material remains UNSENT.

## Exact reviewed manuscript hashes

All six matched the handoff on initial inspection and recheck immediately before writing this report. Concurrent repository HEAD movement was observed (handoff: `37bcb80978d4635604daf8dd3272f54ed902d187`; later local observation: `a65703b81ec7839042b38b1a193b9438b4475f26`); this review is bound to file bytes, not to an assumption of a stationary checkout.

| File | SHA256 |
| --- | --- |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `c4de532df058717ecda12f229afdca2ffcbc574d51a26f17d6f18cd496b673bc` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `6bc9e9a21766610e4d1bc4d2fdf7d751fe775b9b4e81a108c4d6c4ebe3f9578c` |
| `paper_prototype/main.tex` | `53a0bd572955b77e6d4524eeaec9388d4a0189dd13df828e474dfe0dfd1383e5` |
| `paper_prototype/README.md` | `b9cec494b4e1c20162131f787df7de78172481c2486dba11daa301344f168815` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `a9d54501d1c943ff8bea9ce9502b522ec93f89dc55363550b9c958390251c0ec` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `4622e7c861c4d9345ecac4c894df02007dd8d59c60fba0b9a18b47e3f54f6060` |

Handoff `/tmp/astra_manuscript_seq144_151_handoff_20260913.md`: `e32082680151dc099e2fba897f36bf56223cb1a7384ee29bb106fb90cda4da75`.

## Exact supporting source hashes

The following 14 source pins were independently hashed and matched the handoff. Paths beginning `receipts_20260912/` are relative to `research_notes/astra_memos/`; other bare filenames in this table are in that same memo directory.

| Source | SHA256 |
| --- | --- |
| `receipts_20260912/astra_l2_lr_seed0_high_20260913_attempt2_collected.json` | `ceba37612abdf3aa7db21b1c3280f559f67911a0ca86dd58b702cb3c3d25f50b` |
| `receipts_20260912/astra_level1_second_roster_analysis_20260913.json` | `1d2247c77bc582d2a0e3c8c69749ba541cfdf17fb04ec001fdfe11efc6b194a2` |
| `receipts_20260912/astra_level1_second_roster_analysis_20260913.md` | `3d42de3bff3bc5a52c120d6d4dc34fbd424170a143610ca6e7e4ef4c78330b33` |
| `receipts_20260912/astra_level1_second_roster_replay_20260913.json` | `7daa501567354293697e17f1fe8681d37faceb96c1af7d89b796e1c709b616af` |
| `receipts_20260912/astra_real_record_formation_report_20260913_attempt1.json` | `2b9bb4d5539d6e26e75933af8d45e21e1dc3c93ad7320fc2bc6c64d1cf93420a` |
| `ASTRA_REAL_RECORD_FORMAT_AMENDMENT_2026-09-13.md` | `5448a3f5e072dd385f8c33e7ea38fb27fa39b61aeddb76b9dc023f3c7b05296b` |
| `receipts_20260912/astra_real_record_v2_analysis_20260913.json` | `e83a9714c4ca421892d09b5f6f3a8e0b10b7f0f87ea8d915724fbd4d6951c86b` |
| `receipts_20260912/astra_real_record_v2_analysis_20260913.md` | `59ffb44c44e9ed6aac68b5907d0f53852de451893554bdc0f1cc6fb6e9e5361e` |
| `ASTRA_ACTUAL_RECORD_MEMORY_PROTOCOL_2026-09-13.md` | `c056a0fb6c97d1ba93b4d2a0fa07cb70f806cfa64fef2df1769d78e80334a716` |
| `receipts_20260912/astra_a100_native_readiness_failure_20260913.md` | `6969920bb14f9b0b23e0c23f235456a9ddc8f41dfa8323249b1e8c6929845422` |
| `receipts_20260912/astra_l2_access_high_seed2_report_20260913.json` | `9cb95809b5ff658c45e39a21a522433d666b2696af8feda698ef2d951604346b` |
| `ASTRA_SEED2_HIGH_ACCESS_PROTOCOL_2026-09-13.md` | `be6edc7ae575f8b846b20a81c7d91dbacdee4273fb089f931acaf523ce4e75c4` |
| `gpu_artifacts_local/a100_native_readiness_20260913_attempt2/inspection.md` | `73cdc84d53158781122102f494d722104cc3aae16011f00d990ac4a9c2cb240a` |
| `gpu_artifacts_local/a100_native_readiness_20260913_attempt2/verification.json` | `aed4d4641d8f880046eb2e46d8d52136287ebd37c1a175fb902e631eb0cced60` |

## Raw local archive bindings

All paths below are relative to `gpu_artifacts_local/`. These archives were hashed locally and selected payloads read in memory; no extraction or alteration. Whole-archive hash agreement does not mean this review re-executed every original scorer or re-authenticated remote provenance.

| Archive | SHA256 |
| --- | --- |
| `l2_public_record_20260913/astra_l2_lr_seed0_high_attempt2.tar` | `369764744ecb2760e29a0ac9e0e82b623f943b36d834f591ed96521335ea424b` |
| `l2_public_record_20260913/astra_l2_lr_seed2_high_attempt1.tar` | `d5f91bc56a57a48aad204e1dd3dd8b972c58b97f16d518627e726f8f8cf7082c` |
| `l2_public_record_20260913/astra_l2_access_high_seed2_20260913_attempt1.tar` | `6865c968dbef113e12570ced2333b74fbd79379a4a6f30b16f65a3ef4c6df527` |
| `level1_second_roster_20260913/node1_second_repetition.tar` | `b2e4cf8931afa5fb03768658d4e5cd2aef07db563476c53d2a16f3bb1e7ca6f6` |
| `level1_second_roster_20260913/node2_second_perception.tar` | `addc2e61ce05f2b622482adde82f16c2c571db6dd072b0fb7750a4d6dc559a3a` |
| `level1_second_roster_20260913/self_reflection/node2_second_self_reflection.tar` | `e472f483529ae37e6105557ef4ca2b779f3691e183f3ad7008352852a2382ac5` |
| `level1_second_roster_20260913/meta_reflection/node1_second_meta_reflection.tar` | `1b69ccab8dd8612767dc0fa2139f934acc09e0ee5bde48181345044879599dc9` |
| `real_record_20260913/astra_real_record_20260913_attempt1.tar` | `ccbcdf6c89921609116d751a2b0b8fe295ba200bde574d00c8f319173509d445` |
| `real_record_20260913/astra_real_record_20260913_attempt2.tar` | `71671dc02e175be0dafba595aa4e9ef30c409953a0366cc082b4d7e319c055c0` |
| `real_record_20260913/astra_actual_record_frozen_sources_20260913.tar` | `e2ec97cad381ae4686be3830d02bd7533a20406bb5eb84164a92d369a144b749` |
| `a100_toolchain_smoke_20260913_attempt1/evidence.tar` | `d5430f9a7a7f914d237352e7ce8bbb5072a760bc4b668b2e7ff69d7d64645da0` |
| `a100_native_readiness_20260913_attempt2/evidence.tar` | `c2ba707c2bd0cda768665b38d240628d739417e7788f32176d31e857a3b64558` |

Additional exact payload bindings used for HF recomputation:

- Worker OFF: `b563e15cb37c670cb3ecb71ecab39d9884ddc04801a4a268315e0ac8fbaaabe9`.
- Worker fit1: `da4f812c9d41ba4d26a89523a19bd9256fa04088bdc5928b8f84842aa346c58f`.
- Worker fit2 PROMOTE: `70543fe22f65a9d58b5efbdc15a593acf49164ac359be4028d86695b115d56b7`.
- Original high-seed2 `world.json`: `32a0bc76549042443fe709682f993def1680548edac72d6280d3d4d8f886883a`.
- Original high-seed2 `run/report2_PROMOTE/data/result.json`: `f7ec283ac3df776ba0c680469d60d8acfc1df18e3d6ec4fb2eff587bb9b2531f`.

## Files changed by this reviewer

Only `/tmp/astra_manuscript_seq151_independent_review_20260913.md` (new). No manuscript, evidence, coordination, operational, or Git file was changed by this reviewer. Other agents' work was left untouched.
