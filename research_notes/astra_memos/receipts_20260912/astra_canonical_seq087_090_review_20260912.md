# Independent read-only manuscript validity review: SEQ-087–090

Review date: 2026-09-12; evidence and manuscript hashes rechecked at 15:26 UTC
after the additional SEQ-090 audit instruction.
Scope: canonical `paper_prototype/main.tex` and `paper_prototype/README.md`;
the four named terminal memos and relevant local archived receipts.

**Verdict: ONE localized integration-blocking factual correction.** The new
numerical endpoints, denominators, and bounded interpretations check out, but
the hash-bound manuscript incorrectly says SEQ-090's independent content audit
is pending. The terminal memo already contains the completed 15:19 UTC audit.
Correct that stale status and index the completed audit before endorsing these
bytes as a current integration. No endpoint or historical-table rewrite is
needed. This is advisory manuscript review, NOT C11 certification, a GPU gate,
human ratification, or an instruction to pause experiments. Main owns edits
and integration.

## Bound manuscript hashes

Both matched the requested hashes on initial read and at the final evidence
check; all findings below refer to these bytes.

| File | SHA256 |
|---|---|
| `paper_prototype/main.tex` | `003cabe930efb6ea52ca76e0d76a8505d597c8dcf88b762d98dcad7a5d24863b` |
| `paper_prototype/README.md` | `415215aab05b8b7a87c81c448ff8ff05e274ca715243148c52cc1bf1219830f4` |

## B1 — completed SEQ-090 audit still described as pending

Locations:
- `paper_prototype/main.tex:334`: “independent raw-content diagnosis remains pending”.
- `paper_prototype/README.md:286`: “raw-content diagnosis pending”.
- `paper_prototype/README.md:291`: “Independent raw-content diagnosis for SEQ-090 remains pending.”

Contradicting source: `research_notes/astra_memos/ASTRA_CONSTRAINT_V2_TERMINAL_2026-09-12.md:64`,
“Independent raw-content audit — 15:19 UTC”, and its archived audit Markdown,
JSON, and script under `research_notes/astra_memos/receipts_20260912/`.
This is an understandable later-source update, not a finding that the original
strict results were wrong. The manuscript's current-tense pending status is
nevertheless false against the requested terminal evidence.

The completed audit confirms all 48 strict nulls and all eight schema-valid
but factually incorrect records. It also materially sharpens the diagnosis:

- No quoted single-digit coordinate strings occur; coordinate-string-only
  normalization changes nothing and leaves every strict null unchanged.
- The exclusive partition is 25 single-coordinate responses, 8 invalid JSON,
  5 duplicate-key records, 1 flat four-coordinate list, 1 coordinate-object
  record, and 8 schema-valid but factually wrong records: 48 total.
- A separately labeled post-hoc literal reading makes 17 fully specified
  witnesses assessable: 5 factual and 12 incorrect. This is a selected
  assessable subset, not a new strict success rate, a replacement endpoint,
  repaired training material, or evidence of learned checking.
- Forty schema failures are not forty established false complete witnesses.
  Many outputs never specify the necessary second cell.

I independently recounted the strict and coordinate-string-only endpoints
from all 48 captured result texts, bound their boards to archived `cases.json`,
and checked raw-text hashes, stop metadata, and prompt/seed bindings. The
17/5 literal-reading result and exclusive partition are reported by the
hash-verified independent audit, not presented here as a separately rerun
literal-reconstruction algorithm.

**Smallest fix:** replace the three pending clauses with completed-audit
language and add the audit to the SEQ-090 README source manifest. Suggested
replacement for the main-text pending clause:

> The completed independent content audit confirms all 48 strict nulls:
> 40 schema failures and eight schema-valid but factually incorrect records.
> Unlike SEQ-088, no quoted numeric coordinate strings remain; coordinate-only
> normalization changes nothing. A separate post-hoc literal reading finds
> 17 complete assessable witnesses, five factual and 12 incorrect, without
> repairing original outputs or approving training material. These readings
> do not replace the strict endpoint, and changed boards prevent causal
> attribution to the wording clarification alone.

The existing v2 paragraph does **not explicitly attribute** its null to the
v1 numeric-string failure; B1 is stale/incomplete diagnosis, not an invented
finding of an explicit false attribution. The replacement makes that
distinction unmistakable while retaining the original endpoint. At 15:26 UTC,
both manuscript hashes and the completed audit's hashes were unchanged.
Review remains bounded to SEQ-087–090; no additional experiment or GPU pause
is requested while Main performs the canonical correction and commit.

At minimum the README should identify the completed 15:19 UTC addendum and
the following receipt hashes. If Main includes the literal-reading numbers,
say “5 factual among 17 assessable, explicitly post-hoc witnesses,” keeping
0/48 as the original strict endpoint; do not silently promote 5/48 to it.

| Completed audit receipt | SHA256, checked locally |
|---|---|
| `astra_constraint_v2_content_audit_20260912.md` | `1be39788c92f3b1664b417e5502b22608473a2a3478dd6e3181750fee85b9951` |
| `astra_constraint_v2_content_audit_20260912.json` | `9ad6349fc90b3f379f1763c282a772f689e9805c63f117ea10a41c5e35af1a08` |
| `astra_constraint_v2_content_audit_20260912.py` | `6f2d46b86ee2d482d285ccd1001417a2354eceacd9f7359edb9da9e148db94e2` |

## Numerical and interpretation checks

### SEQ-087 — PASS

`main.tex:311`, `main.tex:326`, `main.tex:839`, `README.md:254`.
Recounted every generated output against its archived request's target map.

| Root / fitted map | ON correct /128 | Same-map OFF /128 | Modal fitted action /128 | Original held-form correct /64 |
|---|---:|---:|---|---:|
| 0 / + | 68 | 64 | mem2reg 104 | 37 |
| 0 / − | 68 | 64 | gvn 124 | 33 |
| 1 / + | 64 | 65 | gvn 128 | 32 |
| 1 / − | 63 | 63 | mem2reg 113 | 34 |

All 768 completed-run generations are valid and untruncated: 384 per root,
three states × 128 prompts, not four independently sampled OFF baselines.
Each root's same 128 OFF outputs is scored under both target maps. Opposite-map
disagreements recount to 102/128 and 113/128. The held-form column agrees with
the supplementary native reports and is not pooled with the exact-row panel.
Root/optimizer-seed confounding, exact seen contexts, global action preference,
and absence of retention/generalization evidence are explicitly preserved.
The separately hashed failed root-0 attempt is not included in these counts.

### SEQ-088 — PASS

`main.tex:313`, `main.tex:327`, `README.md:256`.
Independently checked all 16 output texts against their actual board cells.
Strict grounded process/control = 0/8 versus 1/8; schema-valid = 0/8 versus
8/8. All process coordinates are numeric strings. Strict invalid-citation
counts 0 versus 7 are conditional on reaching schema validation, not evidence
that process citations are factual. Coordinate-only post-hoc conversion of
single-character strings 1–4 gives 2/8 versus 1/8, with six process citations
still wrong. Original strict and post-hoc results are clearly separated.
All 16 stops are normal, without input truncation/output rewriting in the
captured records. No fit, adapter learning, verified lesson truth, or parenting
benefit is asserted. Card lengths 47/44 and unequal token cost are disclosed.

### SEQ-089 — PASS

`main.tex:315`, `main.tex:329`, `main.tex:841`, `README.md:259`.
Independently recounted exact-row correctness from archived row targets and
all 384 generations: OFF 65/128, full response 64/128, first choice 64/128;
gvn counts 1, 128, 128. All outputs are valid and untruncated.
Both fits contain 256 logged steps and share initial tensor identity
`49b7cb33546dafe7b7bc40a079c5ca18e69e4293b41593451fcbca9730290565`.
The fit job fields differ only in stage and stage deadline; common row data
and recipe are shared. The full-response final tensor identity matches the
original writer capsule's `stages/fit_r1_plus/DONE.json` exactly:
`31f10119bc37dce5abcd7be569914400392429705ada315c3fcf9813a5d23787`.
The first-choice identity is
`8b84dbef688ed7c30defad3aa15b96acfbe30570d7b8d6805859c0af3500f6bc`.
These are comparisons of archived native tensor-identity receipts, not local
weight-content rehashes; the manuscript correctly discloses that limitation.

Recomputed second-epoch means from all 256 step records per fit:
- Decision CE: 0.7282092404784635 / 0.7871152587467805.
- Full-response CE: 0.09743568646081258 / 3.5812753718346357.
- Nondecision NLL: 0.002778176567517221 / 25.995883643627167.

The displayed rounded losses match. Online, pre-update, dropout-active losses
are not mislabeled final-checkpoint losses; BF16 prefix scores are not
mislabeled dynamic greedy-generation probabilities. One map/training seed
does not become a multi-seed learner claim or general impossibility claim.

### SEQ-090 — strict numbers PASS; status requires B1

`main.tex:334`, `README.md:286`.
Recounted all six arm results: process schema counts 1/0/1 and format 2/2/2
per eight for seeds 7101/7102/7103; all strict grounded counts zero. Every
schema-valid record has an invalid factual citation. All three archived
case-set files are byte-identical; actual request seeds agree with the
sampling-run names. Both arms' prompts contain explicit unquoted-integer
guidance. Process/format card text is identical between v1 and v2, whereas
candidate hashes are disjoint. The manuscript correctly prevents causal
attribution to wording alone and does not call 24 outputs per arm independent
environments, learner seeds, or trained children. Native reports record three
successful replays, six cleanups, absent controllers, and released devices;
these are historical archived observations, not a new live-node verification.

## Cost audit — no numerical contradiction; one non-blocking omission

New prose accurately gives 256 updates per objective fit and unequal 47/44
card token lengths. It makes no equal-compute claim. However, the SEQ-087–090
manifest does not enumerate the newly available actual token/time costs;
`main.tex:837` still enumerates only SEQ-073/085/086. Adding a compact cost row
to the README would improve completeness without expanding the scientific
claim or the main text. This is advisory, not a second blocker.

| Assay | Completed-work cost from receipts | Important exclusion/unit |
|---|---|---|
| SEQ-087 | 768 generations + 768 score requests; 5,596 emitted token IDs; root controller elapsed 396.154617 + 399.416826 s (sum rounded from raw values 795.571442 s) | Emitted IDs include terminal EOS; scoring work is additional to generated tokens. Failed root-0 attempt and external verification are excluded, not zero-cost. |
| SEQ-088 | 16 generations, zero fits; prompt IDs 2,104/2,080, output IDs 392/313 (process/format); controller 276.672446 s | 4,184 prompt and 705 output tokens total. Preparation/external audit beyond the controller interval are extra. |
| SEQ-089 | 384 generations, 384 decision-prefix forwards, 512 training forwards/optimizer steps; 2,559 generated IDs; controller 576.103847 s | Two fits × 256 updates; preparation/cold costs outside the interval excluded. |
| SEQ-090 | 48 generations, zero fits; 13,560 prompt IDs and 2,066 output IDs; controller elapsed 224.704325 / 202.486860 / 206.781977 s, aggregate from raw values 633.973163 s | Repeated eight-case panel; sum of concurrent controller durations is not calendar duration or measured GPU compute. Preparation/external audit extra. |

For SEQ-090, process output totals by seed are 327/363/374 and format totals
341/331/330. Prompt totals per pair are 2,272/2,248. I recomputed these from
captured per-record usage. Caps of 1,800 seconds/pair and 900 seconds/arm are
limits, not consumed budgets. No campaign-level compute or dollar total can
be inferred from this partial accounting.

## Preservation checks

- All **12 historical tabular blocks**, including their exact contents, are
  byte-preserved against the local pre-integration snapshot
  `/tmp/astra_canonical_integration_checks_20260912/main.tex`
  (SHA256 `3eccc364ce4a8639b5e156f443f55eebc70fcdc7567b2bc171f5ff6c12b0f983`).
  There are now 14 tabular blocks: the earlier component table plus the new
  SEQ-087–089 table. Every one of the 13 pre-SEQ-087 tabular blocks survives.
- The historical appendix body is preserved in full as an unchanged prefix;
  supplementary component/provenance paragraphs are appended. Against the
  pre-SEQ-090 snapshot, the SEQ-089 boundary paragraph's last sentence changes
  solely to include now-terminal SEQ-090 while still excluding cumulative
  work. Thus “historical appendices preserved” is verified; a literal claim
  that the entire current appendix section had no edits would be too broad.
- The **reviewed pre-SEQ-087 abstract is byte-identical**, against
  `/tmp/seq087-089-manuscript.CSRbsy/main.tex.before`
  (SHA256 `f4e79aaafed4847bc574f1fee0bbf172276f8484028c850c86181ba116b14f93`).
  Abstract block SHA256, including begin/end delimiters:
  `301ed1d6ffc2ad99a03442e7f6fbea1ca3571c4656d63cc872a9026409d00cb6`.
  The older pre-component abstract differs, as expected from the prior
  reviewed integration; that earlier revision is not misreported unchanged.
- All 255 historical README table rows and all 272 pre-SEQ-087 README table
  rows remain present. The textual diff against the pre-SEQ-087 snapshot is
  confined to the terminal additions/status/manifest updates described here.
- Citation calls remain unchanged, labels are unique, references resolve,
  and begin/end environments pair correctly. These are static checks only.
- **OFF 208 omit LF / ON 672 include LF is preserved.** I independently
  recounted the original semantic-writer capsule's 880 raw generation files:
  OFF LF count 0/208, ON LF count 672/672. `main.tex:833` preserves the
  qualitative correction and LF+EOS fixed-candidate/native-generation
  distinction; `README.md:217` preserves the exact counts.

## Receipt hash verification

All filenames below are under `research_notes/astra_memos/receipts_20260912/`.
The corresponding README/memo hash claims matched recomputed local SHA256.

| Receipt | SHA256 |
|---|---|
| `astra_exact_train_root0_terminal_20260912.tgz` | `7bfc98cc39fc4e98072540476c961111494815bcd517e89b2eac2bdb91cf141a` |
| `astra_exact_train_root1_terminal_20260912.tgz` | `2c87796110b611b07f57f2724c8de050bddd9cf316f7df0bc1c54bbc9bba72a7` |
| `astra_exact_train_root0_failure_20260912.tgz` | `28d518e03198bbb9b6c06cb77c0407d500b0088f1540290f4264c942d118a240` |
| `astra_exact_train_combined_analysis_20260912.json` | `60df19e4388bd335c89c1976412cb76c09c2b7ba5ca15fe3adb8189cf795c842` |
| `astra_constraint_verified_terminal_20260912.tgz` | `7935c254ac16cfbf33c8cbf9386e9a947ec9b02e50d28e9f03987efb3bbbda89` |
| `astra_constraint_content_audit_20260912.json` | `60153eb59f7da7d4a2b01b9055f4171d2904435a85c4159c980b28b5e8e217d5` |
| `astra_objective_terminal_20260912.tgz` | `d7524e0a558a40a4121e2fa46caa1f772e5a3a0e92c4ea1565b57809528e3390` |
| `astra_objective_analysis_20260912.json` | `dc662d93bc8b838840be3fa22452d48c06fb2f6c5b7dc5cce802cbfdaa837fe6` |
| `astra_constraint_v2_terminal_20260912.tgz` | `476788fb5204ab45dfcc22644382f1519493ce6224ccbce8298616c0d1073692` |
| `astra_constraint_v2_native_terminal_20260912.json` | `bb243f053db76b966296dd6b5e2289cf8f7317d65ad85d78f63ee4df7a7d8619` |

Embedded report bytes were also hashed, not inferred from capsule names:
- SEQ-087 root 0: `4b1be70a8e2b20a23a2d76b32fb7e02564a958545b7eb8afe870e32b7e832e69`.
- SEQ-087 root 1: `5b349b1b4742f061f0c884ef37b7c4f3478845d46b5f27424c97237d6d492fc2`.
- SEQ-089 report: `4ca5316949252400b6377feca674ba4abd11eac8759a99f9ed427a2b39b7b659`.
- SEQ-090 seed 7101: `ea5a9fff02609b69c7d00068b7463228bcb28ca91bd88cb2eead27b3e45e70c0`.
- SEQ-090 seed 7102: `c741dd8c0847605dd36a02bba7f061840e3afbac14997d362eb80bc6992bc2b5`.
- SEQ-090 seed 7103: `d2a704a2644ece23f75a7b04b9d90347f5cb1ccdff897b6c70d7d99073f36055`.

Terminal memo bytes inspected:
- `ASTRA_EXACT_TRAIN_TERMINAL_2026-09-12.md`: `116310a620c7f7b831e4392dc5dbc848cbf2c402f3d921c2c3b857208001c702`.
- `ASTRA_CONSTRAINT_PRODUCTION_TERMINAL_2026-09-12.md`: `72a736954916eaf33e5ec969b793523e11b246db6767164f5f894cc0e3af53eb`.
- `ASTRA_OBJECTIVE_TERMINAL_2026-09-12.md`: `e33a12bb373e9c071a4852ffcdeb9c9cc40765c4cf066ec3477fb65f1b5de4c1`.
- `ASTRA_CONSTRAINT_V2_TERMINAL_2026-09-12.md`: `721668e23210ec8609fb1a31ad33f08c7338f2d17a765ae44f16eff86d1f0e6f`.

## Review limits and disposition

No git commands or git-object inspection, GPU actions, network requests,
TeX compilation, or manuscript edits were performed. The sole created file
is this review. Archive reads and new recounts were in memory; no receipt
archives were extracted or rewritten. Existing audit scripts were inspected,
not executed. An unavailable `python` alias was replaced by `python3` for
read-only calculations; exploratory schema mismatches were corrected before
the successful recounts reported above.

“Committed terminal memos” is the user's supplied provenance designation;
without git, I verified the local memo bytes and bound receipts, not repository
commit membership. Preservation is independently checked against the available
local snapshots, not authenticated against HEAD. No PDF layout, page-count,
official base-origin authentication, remote weight rehash, global contamination
clearance, or fresh GPU-release certification is claimed.

Disposition: Main should fix B1, optionally add the compact actual-cost row,
and hash the resulting integration. These reviewed bytes otherwise support
the stated bounded diagnostics, not retention, parenting, H1/H2 confirmation,
G3 qualification, mechanism freeze, or campaign completion.
