# SEQ111–112 / C55–C56 independent manuscript review

**Verdict: PASS for the six hash-bound manuscript files and the supplied handoff. No required substantive, preservation, or diff-syntax correction found. EDITSTOP.**

Final six-file and handoff hash check: **2026-09-12T22:06:52.797645+00:00**. This verdict covers these bytes, not subsequent edits, a scientific qualification, or a TeX/PDF build.

## Independence and actual review scope

I did not author this manuscript integration or the SEQ111/112 runner, training corpus, fits, or Herschel's readout analysis. I authored related prospective diagnostic/process-write designs and prior reviews; Main's outcome summary was visible. This is independent editorial/evidence review, not blinded review or independent evaluation of my own prospective design.

Read the six files and reversible handoff, Main's actual-record memo, archived write/readout validation and selected fit/token/release metadata, saved-weight audit, and Herschel's archived review. Independently hashed both capsules and every member against their validation inventories: **47 write and 232 readout regular files**, unique safe paths, exact inventory equality. Archives were read in memory, not extracted. This is a custody comparison, **not another semantic raw-output recount**. No analyzer, native tokenizer, world/model replay, logits, weights, GPU, network, SSH, Git, or TeX tools were executed. Only this report was written.

## Substantive findings — PASS

**C55 distinguishes a parameter write from usefulness.** `paper_prototype/astra_sprint_draft_20260912.tex:1831`, `paper_prototype/main.tex:386`, and `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1839` match the write capsule's `fits/{P,A}/adapter/train_meta.json`, `train_manifest.json`, `full_tokens.json`, and the separate weight audit. Each fresh-base rank8 fit uses two accepted raw records, seed2, LR1e-4, batch2 and **12 updates**. Recorded corpus targets are 74 including EOS, hence 888 target-token presentations. P has 564 context/638 total tokens per corpus and 7,656 total input presentations; A has 562/636 and 7,632. Equal updates/target exposure are not equal input compute. No extra attempt1 GPU fit is claimed.

The weight audit records **392 finite tensors and 11,124,736 nonzero B entries per adapter**, B L2 P1.587822886866/A1.600173037602, and distinct weight identities. Declared zero-B supports the bounded write conclusion; the manuscript correctly excludes usefulness, complete deltas, pre-init A measurement and authenticated base origin. Weight bytes are excluded from these metadata capsules: I verified audit/manifest agreement, not native weights.

**C56 preserves the scoring estimand.** `paper_prototype/astra_sprint_draft_20260912.tex:1849`, its table at `:1856`, and claim map `:1876` agree with Main's memo and Herschel's review:

| State | Correct / fixed labels | Actually answered labels | Valid quizzes | Faithful / allotted | Faithful / emitted | Calls |
|---|---:|---:|---:|---:|---:|---:|
| OFF | 7/24 | 24 | 4/4 | 9/12 | 9/12 | 32 |
| P_ON | 6/24 | 18 | 3/4 | 10/12 | 10/11 | 29 |
| A_ON | 6/24 | 18 | 3/4 | 10/12 | 10/11 | 29 |

The two missing rule5 quizzes contribute prescribed zero/6, **not six emitted wrong labels**. Replacing 6/24 with 6/18 would change the endpoint. Rules2–4 score 2/6, 1/6, 3/6; OFF rule5 scores1/6. The reported two-ACT response is invalid before the proposed third TRY executes; no third TRY/record/reveal/scored quiz follows. All90 calls finish `stop`, no cap hits. P−A=0 and each adapter−OFF=−1/24: no P advantage, equivalence test, statistical significance, or population inference is supplied.

**Conditional reporting is not prediction/selection learning.** Each state has eight valid explicit pre-TRY predictions, all F, six correct. OFF8/12 versus P/A8/11 executed TRYs is a denominator difference, not improved competence; retaining TRY-containing invalid responses gives12 opportunities per state. The extra late PREDICT line is not valid pre-ACT prediction. Record prompts display the already-emitted wake/prediction and public observation, with explicit relation mapping. The one-record reporting gain is not learned experience selection or an adult update. Records neither feed back into wake nor train during readout. These distinctions are explicit at claim map `:1920` and draft `:1887` onward.

**Raw identity is separately attributed, not inferred.** Herschel's review reports all29 aligned P/A prompts, raw responses and output-token sequences equal; saved weights differ. The manuscript preserves this panel-specific distinction and does not infer equal parameters/latent states. It discloses that Herschel authored earlier formation/write collectors and the saved-weight audit, not the readout driver/collector, and saw Main's summary. Receipt-level native audits are attributed rather than newly claimed. Four shared rules, one paired learner seed2, shared generation protocol and one shared OFF are not24 independent learners.

**Execution boundary is intact.** C55/C56 supersede historical C54 RUNNING/NOT RUN without changing formation evidence. Current record-request training is not relabeled as the proposed future decision-target/context-distillation intervention; no teacher-stripped training context or process-write outcome is claimed as executed here. Related future designs and acquisition work remain outside this verdict. Formation-excluded rules are not globally untouched confirmation; original64 confirmation cases remain unrequested as attributed to the supplied evidence. No general G3/P1/G5/H1/H2, clean-lineage, latent-erasure, adult-learning or freeze promotion. The separate interleaved pair contributes no outcomes at this handoff's cut. Later status changes do not falsify that historical cut.

## Costs and custody — PASS

Selected archived `run/main_release.json` plus validation fields support the manuscript's clocks:

| Phase | Full release seconds | Controller | Workers | Collection |
|---|---:|---:|---:|---:|
| Writes | 361.167984 | 230.665586 | 153.654476 | 22.495086 |
| Readout | 642.893684 | 595.137126 | 493.982361 | 53.982670 |

Readout generation73.549066s is nested; collection overlaps reservation. These are not additive busy-time/billed costs. Separate saved-weight audit12.852530s is CPU-only. Herschel's recorded totals are90 calls,31,510 input/1,945 output tokens, versus96-call ceiling; executed output caps25,800 versus maximum27,600. Main memo `research_notes/astra_memos/ASTRA_ACTUAL_RECORD_READOUT_2026-09-12.md:75`, claim map C55/C56 and draft `:1906` retain these scopes.

Evidence below is under `research_notes/astra_memos/receipts_20260912/` (full local directory; archive member names are cited above):

| Evidence file | Verified SHA256 |
|---|---|
| `astra_rulegame_record_write_terminal_20260912.tgz` | `26243e9a6436a859f7ed7a6ec1250a9e3a06496ec61c8eb3f85afe4d1ea308b4` |
| `astra_rulegame_record_write_terminal_20260912.tgz.validation.json` | `0ee749514a55aef897cf2a8b96b1d32d859eb638ae1e025d32e112632fab18d1` |
| `astra_rulegame_record_readout_terminal_20260912.tgz` | `f8f2bb688da189ebb8f70c67725f1c008db49d6c5b2800abdc58a0dd4fcb7458` |
| `astra_rulegame_record_readout_terminal_20260912.tgz.validation.json` | `9cfb499775ceee44cbffe7eaf14e25ced405a4a5865c8006ce45ee6b05d4f311` |
| `astra_rulegame_record_weight_audit_20260912.json` | `c14c2a8df8d14edbff500d52c1dc02f0bb02c354807cb07dd132b1e3292d974d` |
| `astra_rulegame_record_readout_independent_review_20260912.md` | `6bce8e9be666e37cf187ae69c48bad0cba9fa815f8171b4c11df6c82b49fd2cc` |
| `astra_rulegame_record_readout_independent_analysis_20260912.json` | `8a8312d2f1b6b11b1b9e2b4887ed993657503304a657e54d9d265ac909c69bb0` |

Main memo read at SHA256 `6dbfa32c370275aa5fbfe8eaf2ce373c0736e82d531814445b8af30803fb202d`. Audit consistency is not independent model-origin authentication or proof against fabricated upstream evidence.

## Preservation and handoff syntax — PASS

Independently parsed all six embedded diffs from `/tmp/astra_manuscript_seq111_112_handoff_20260912.md:953`: hunk old/new counts, both offsets, context/deletion bytes, exact forward and reverse applications all pass. Recovered prior hashes match the accepted `/tmp/astra_manuscript_seq108_110_handoff_repaired_20260912.md:34`; current hashes match this handoff. The earlier malformed-hunk problem is **not present**. No patch was applied to repository files and no Git command was used.

Current companion abstract is **232 whitespace words, <=250**, normalized TeX/Markdown parity; the earlier233-word abstract is not the current one. Canonical `main.tex` abstract is byte-identical to the recovered prior source; canonical Discussion onward, including appendix, is unchanged. All prior table bytes/order survive: main8→8, README29→30, sprint draft24→25 (**including its longtable**), claim map22→23; abstract/collaborator have no tables. New tables are additive. Escaped-brace and environment checks, unique/resolving TeX labels, and consecutive/resolving C00–C56 IDs pass. This is source validation, **not a TeX compile, PDF/layout, width, or page-count approval**.

`research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:1` remains DRAFT ONLY/UNSENT. No external delivery occurred. Formal C11 remains deferred; no additional qualification framework is introduced.

## Exact reviewed manuscript hashes

| File | SHA256 |
|---|---|
| `paper_prototype/main.tex` | `cbc8313beec89fb94788a6b9d6b0c0414f71e8184eb655644011b5d944a24b9a` |
| `paper_prototype/README.md` | `6f335ab6080fb40d8b6e958745f6ff3b10aecebf1238fc1bd7d3c03d0ab46d96` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `f88cc7f59198c665d88b655d5ef08ad4980834aa3ca7def7c13ab27988470cee` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `3d2aeb1cfc6ab69fe8ae195bcdc067c69386ed49ab204a37b8a1e32f62cf2655` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `42504e4635f5cf74722051f8c7377956fcafa21c288f69f8e828fa2c4ddfb478` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `be9f071b2a25c2d576f81eaa537d8c46d79bc09102c750f90b8b233c3168850a` |

Handoff SHA256: `ee3da4ed1abc08d4cde88b4c9e2f56af6d00cb5c3b3c3482b2da1824b94c8d3d`.

**Minimal required corrections: none.** References to the memo's pending/aggregate-only state are read as historical supersession; the inspected current memo already incorporates Herschel's PASS and raw equality. That does not alter the supported result. Main owns any later status refresh or edits. **EDITSTOP.**
