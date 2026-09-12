# Independent manuscript review — SEQ098–100

Date: September 12, 2026.

## Verdict

**PASS. No required corrections found in the six-file manuscript update.** Numbers, denominator labels, shared-data/OFF reuse, memory limitations, engineering-only qualifications, and receipt attribution agree with the prior independent numerical reviews and retained evidence. This is a bounded manuscript review, not a scientific-gate promotion, launch veto, PDF approval, or completion of the developmental thesis.

Read `/tmp/astra_manuscript_seq098_100_handoff_20260912.md` and compared all six working-tree files against HEAD using read-only Git operations. HEAD at review: `1f8ba2b9c4bb42e5a86eb4f4af547c4a718ae23b`. All six pre-edit copies under `/tmp/astra_manuscript_seq098_100_preedit_20260912.hfAvUI/` equal their HEAD versions. All reviewed working-file hashes match the handoff and remained stable through the final check.

Only this report was written. No repository edits, Git writes, network/GPU/model/tokenizer calls, scientific reducer execution, or interference with concurrent work occurred.

## Findings with evidence

### 1. PASS — SEQ098/099 behavioral and memory counts

The integrated result is correct:

| Trainer seed | Teach habit | Control habit | Teach recall | Control recall |
|---|---:|---:|---:|---:|
| 0 | 32/32 | 0/32 | 4/16 | 4/16 |
| 1 | 32/32 | 0/32 | 7/16 | 4/16 |
| 2 | 32/32 | 0/32 | 3/16 | 4/16 |

All six fitted states and the actual seed0 OFF baseline already have 32/32 correct ACTs, with no arithmetic gain. OFF adherence is 0/32. Its dev memory is 0/16 with 16 invalid responses at the 64-token cap. The actual original OFF is reused for replication, not regenerated, duplicated as independent baselines, or charged again as new replication calls.

Seed0 fitted memory is constant red; seed1/2 controls are constant blue/yellow. Teach seed1 is blue11/yellow5 and teach seed2 green14/blue2. The prose preserves those nonconstant patterns and paired recall differences 0,+3,-1 without selecting seed1 as a success endpoint. The 32 arithmetic pairs are disjoint from training pairs, while trainer seeds reuse the same data and development probes. There is no claim of 96 independent learners or three new datasets.

Manuscript evidence: `paper_prototype/main.tex:354`; `paper_prototype/README.md:12`; `paper_prototype/astra_sprint_draft_20260912.tex:1297`, `paper_prototype/astra_sprint_draft_20260912.tex:1311`, and `paper_prototype/astra_sprint_draft_20260912.tex:1341`; `paper_prototype/astra_sprint_abstract_20260912.md:13`; `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1027` and `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1076`; `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:3`.

Supporting receipts: `research_notes/astra_memos/receipts_20260912/astra_fundamental_seed0_main_analysis_20260912.json`; `research_notes/astra_memos/receipts_20260912/astra_fundamental_followups_main_analysis_20260912.json`; the corresponding archived independent reviews. Those reviews independently scored the original 144 outputs and subsequent 240 new outputs; this manuscript review checks faithful integration rather than claiming another new numerical replication.

Required minimal fix: none.

### 2. PASS — SEQ100 diagnosis and claim boundaries

The training-prompt diagnostic is explicitly in-sample, not heldout, and does not replace the fixed 48-case development endpoint. Both seed0 adapters again emit red for every original memory question, scoring 4/16. OFF gives 0/16 with 16 capped-invalid responses. This supports rejecting paraphrase mismatch as the sole explanation of the observed seed0 failure, not proving absence of latent binding, a neural mechanism, failure at every dose/seed, or an uncapped OFF negative.

The update retains 64 unrequested confirmation cases, no new fits/reminders/answer facts in this diagnostic, no semantic rescue, and no favorable subset. The 32 memory versus 880 arithmetic target tokens per epoch, including EOS, are labeled a diagnostic lead rather than an isolated causal explanation.

The one-habit experiment is called level zero, not completion of a broader level-1 curriculum. Authored post-training is not represented as child sleep or parenting. No reliable-memory, conditional-intelligence, H1/H2, P1/G5, clean-lineage, repeated-update, or mechanism-freeze closure is added.

Manuscript evidence: `paper_prototype/main.tex:356`; `paper_prototype/astra_sprint_draft_20260912.tex:1348`; `paper_prototype/astra_sprint_abstract_20260912.md:17`; `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1139`; `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:14`.

Supporting evidence: `research_notes/astra_memos/ASTRA_FUNDAMENTAL_MEMORY_TRAINPROMPT_TERMINAL_2026-09-12.md:3` and `research_notes/astra_memos/ASTRA_FUNDAMENTAL_MEMORY_TRAINPROMPT_TERMINAL_2026-09-12.md:15`; archived follow-up independent review, especially its source-key and rendered-training-context checks.

Required minimal fix: none.

### 3. PASS — training and readout costs retain distinct denominators

The training account correctly states 80 matched rows per arm, 4,517 total model-input tokens including 912 supervised target tokens per epoch (3,605 context + 912 target), four epochs, 80 updates, and 18,068 input/3,648 target tokens per fit. Both behavioral and memory targets share one adapter per arm. The 912 targets are not an additional input charge on top of 4,517. Seed1/2 preserve corpus bytes and recipe apart from trainer seed, which affects initialization, dropout, and order.

| Sequence | Actual readout calls | Actual input/output tokens | Output cap, not usage | Supervised seconds |
|---|---:|---:|---:|---:|
| 098 | 144 | 6,393 / 2,156 | 9,216 | 476.237894 |
| 099 | 192 | 8,524 / 1,888 | 12,288 | 693.917059 |
| 100 | 48 | 2,016 / 1,088 | 3,072 | 339.980983 |

Calls/tokens are readout-only; the first two supervised totals include fitting, the third does not. Their sum, 1,510.135936 seconds, includes owned cleanup, not complete outer reservations, Main audit idle, total campaign compute, or a monetary charge. C43 separately labels 82.596622 generation seconds, 425.407021 readout-supervision seconds, 268.510038 fit-supervision seconds, and 1,920.821997 outer readout-reservation seconds. No cap is substituted for realized token usage.

Manuscript evidence: `paper_prototype/README.md:25`, `paper_prototype/README.md:46`; `paper_prototype/main.tex:358`; `paper_prototype/astra_sprint_draft_20260912.tex:1365`; `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1031`, `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1113`, and `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1160`.

Supporting evidence: both archived Main-analysis JSON files and both independent numerical reviews. All displayed counts and clocks agree with their audited receipts.

Required minimal fix: none.

### 4. PASS — real archived reviews, capsule hashes, and native attribution

Verified byte equality between the `/tmp` and repository copies of both independent numerical reviews and both Main-analysis JSON files. The follow-up review digest is exactly `6f70d5e55f8b9732128c3aab4f031966806fb6d5dcdf5d43794c1731f8044370`, matching README/C43 and the handoff. It is one review covering SEQ099/100, not two independent audits. Updating earlier pending-review language is supported; it does not change the scientific endpoints or promote a gate.

Rehashed all three repository capsules:

- `research_notes/astra_memos/receipts_20260912/astra_fundamental_seed0_terminal_20260912.tgz`: `d8f343979f10d358f11ed21fb7896a462b88cfd5d833fee2bf0dab340f19b082`.
- `research_notes/astra_memos/receipts_20260912/astra_fundamental_replications_terminal_20260912.tgz`: `dcd4237dfb54b1def3e4733cadbe29eb0252a6270662e9e869333265ed1bfde5`.
- `research_notes/astra_memos/receipts_20260912/astra_fundamental_memory_terminal_20260912.tgz`: `a3c2bc8ba3a97a4f4b7e73f0a818f7b162872675d1fd577bc0ea4be4df5da378`.

C43 correctly binds the preserved first seed1-teach reduction, actual inherited OFF plan/reduction, source snapshot and release receipt. The prior numerical review checked these exact artifacts; the manuscript does not invent a rerun or replacement reduction. Native model/adapter weight verification remains attributed because capsule weights are absent; local hash agreement is not official-origin authentication. The 18:31 UTC evidence cut and later 18:36 UTC archival-copy check are distinguished.

Manuscript evidence: `paper_prototype/README.md:63`; `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1105`, `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1122`, and `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1171`. All 13 new README Markdown links resolve; new claim-map repository source paths resolve.

Required minimal fix: none.

### 5. PASS — engineering evidence is not scientific outcomes

The archived warm-start native CPU log has exactly 21 PASS lines, `21/21 passed`, and no skip marker. The separate static warm-start review is not conflated with that execution. The repetition handoff explicitly reports 27 new + 11 existing = 38 CPU tests and distinguishes placeholder-token tests from a native-token audit.

The manuscript accurately describes weight warm-start with a fresh optimizer, not optimizer-state resumption. It does not include new continuation/repetition GPU results or convert those engineering tests into broader curriculum, memory, or parenting claims. Concurrent launches remain Main's work, outside this review and the frozen evidence cut.

Manuscript evidence: `paper_prototype/README.md:75`; `paper_prototype/astra_sprint_draft_20260912.tex:1375`; `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1180`.

Supporting receipts: `research_notes/astra_memos/receipts_20260912/astra_v3_warmstart_native_cpu_attempt1_20260912.log`; `research_notes/astra_memos/receipts_20260912/astra_v3_warmstart_independent_review_20260912.md`; `research_notes/astra_memos/receipts_20260912/astra_fundamental_repetition_handoff_20260912.md:90` and `research_notes/astra_memos/receipts_20260912/astra_fundamental_repetition_handoff_20260912.md:101`.

Required minimal fix: none.

### 6. PASS — canonical preservation and document consistency

- `paper_prototype/main.tex` differs from HEAD by one six-line insertion containing three new paragraphs and spacing. Removing that insertion recovers the entire prior file byte-for-byte: abstract, intent, prior corrections, bibliography commands, historical results, and appendix. All eight existing floating tables and 14 tabular blocks remain exact and in order.
- Companion TeX preserves all 15 prior tables, including the longtable, and adds one new bounded SEQ098/099 table, for 16. Prior scientific sections are not replaced by the new results. The earlier live-pair status is explicitly historical/superseded, not silently left as current status.
- README preserves all 18 prior Markdown table blocks; claim map preserves all 11. New tables are additive.
- The intentionally updated companion abstract has exact whitespace-normalized parity between Markdown and TeX: 206 words, below 250. It is not substituted for the unchanged canonical abstract.
- Claim headings are unique and contiguous C00–C44; companion evidence references resolve. TeX environment nesting, label uniqueness, and local reference resolution pass static checks; no new TeX control word is introduced.
- Collaborator remains UNSENT. No source bibliography change or external circulation is performed. C11 remains deferred.

Evidence: whole-file HEAD comparison for `paper_prototype/main.tex`; `paper_prototype/astra_sprint_draft_20260912.tex:52`, `paper_prototype/astra_sprint_draft_20260912.tex:1290`, and `paper_prototype/astra_sprint_draft_20260912.tex:1311`; `paper_prototype/astra_sprint_abstract_20260912.md:11`; `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:1` and `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:218`.

Required minimal fix: none.

## Validation limits and final byte bindings

No scientific raw-output rescoring was rerun for this manuscript task; the previous independent numerical reviews supply that validation, and their exact archived copies were verified. No native weights or tokenizer were loaded. `pdflatex`, `latexmk`, `tectonic`, and `bibtex` are unavailable; no PDF build, page count, layout approval, or successful compilation is claimed. These limits do not change the numerical manuscript PASS.

Reviewed working-tree SHA256 values:

| File | SHA256 |
|---|---|
| `paper_prototype/main.tex` | `9756bb9d51122b09782dbba82b49ab8337daed59167d5305a204050e3888abec` |
| `paper_prototype/README.md` | `38c6844e1ae004a3953d7a680794baf8eb4e39ded098bd4696ccf5bdba8b3d1c` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `9e223af66e8a470e1d194b81927d5b691359e78117ce0c29936f9e049bade3f2` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `90f0cc3b0b2337da0e80ab497ae7432559dd04a874c449e339a35fcf1e7f2934` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `c66766c46de08a35381d1f3c4b84a11d932a208577643e9d9ec0e0e3cf297a66` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `60b84585cbb813aa29ae622577dece3d088c96adda2b4ce694587ae00c4fa82a` |

**Final disposition: PASS; no required manuscript corrections.** No edits or new experiment are requested by this review.
