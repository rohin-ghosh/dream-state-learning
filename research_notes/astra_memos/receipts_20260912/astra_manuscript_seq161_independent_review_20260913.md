# Independent manuscript review — SEQ161 / C97

Date: September 13, 2026.

**Verdict: ACCEPT the exact six reviewed file versions for this bounded
manuscript update. No blocking numerical, provenance, or claim-boundary defect
found. One optional, nonblocking wording clarification is listed below.**

This is independent review of Parfit's manuscript transcription and
interpretation, not independent scientific replication or approval to promote
the experiment. The reviewer previously worked on additive implementation;
this review does not independently certify that implementation. Main retains
scientific interpretation, integration, archival and sending authority.

## Scope and method

- Started only after author EDITSTOP in
  `/tmp/astra_manuscript_seq161_author_handoff_20260913.md`.
- Bound all six current file-byte hashes to that handoff. Compared each file
  with its actual bytes at prior Main commit
  `8921724fd2100af2b7a847fc483313b2caa7e8ef`; all six before hashes also match.
- Read the SEQ161 additions and relevant immediate context, the archived
  analysis, execution review, execution/interpretation handoff, and frozen
  additive protocol. All three principal evidence files also exactly match
  their bytes in archive commit `f15dec6cb0fa678dd00caef608db9e110dc9ed38`.
- Compared manuscript tables directly with already-produced JSON summaries;
  compared stored per-item contrast counts/loss masks and recorded receipts.
  **No scorer/reducer was imported or executed.** No fresh scoring, reduction,
  raw-generation replay, tensor recomputation, archive extraction, model,
  tokenizer, native, GPU or network operation occurred.
- Read-only Git show/diff and scoped diff-check only; no Git mutation. No
  comprehensive older-manuscript review was repeated. No manuscript, core,
  test, protocol, result, or other worker's file was edited.

## Severity, evidence, and disposition

| Item | Severity | Evidence and finding | Accept or minimal correction |
|---|---|---|---|
| R1: six cells and denominators | None | All 30 rows in the five newly added tables agree with archived `analysis.json: seeds[].totals` and `screens`. The abstract companion states the same six cells. Original 16 possible records is kept distinct from admitted 14/8/8. | ACCEPT; no correction. |
| R2: metric definitions | None | Exact is `production_eligible`, paraphrase is `content_correct`, held/canary use `passed`; these are not raw-target bytes or strict canonical form. Detail paragraphs and TeX captions explicitly preserve this distinction and 5/120 strict-canonical memory readouts. | ACCEPT; no correction. |
| R3: held losses and screens | None | Stored LR0-correct held-loss counts are ADDITIVE 0/0/9 and MEMORY_ONLY 0/2/1. Seed2 paired held contrast has one gain and nine losses. All canary loss masks are empty. Floors 8/14,7/8,5/8 and noncompensatory zero-loss rule remain unchanged. | ACCEPT; no correction. Two versus one seed screens are descriptive, not all-seed success. |
| R4: baseline drift | None | Execution-review source/initialized tensor receipts and occurrence/order checks are true in all three seeds; final-tensor receipt equality is false and first-epoch losses differ in all three. Manuscript explicitly retains native drift and assigns no cause. | ACCEPT; no correction. Clean isolated replay attribution remains pending. |
| R5: original failure versus recovery | None | Original controller/collector/holder-written rc0/1/1 is retained for all seeds. Recovery records rc0, collection attempt2 and zero scientific retries/new fits/updates/generations. Seed1 BrokenPipe remains distinct. | ACCEPT; no correction. Recovery is not erasure of failures or proof of OS reaping. |
| R6: costs and exposure | None | Stored costs are 6 fits, 1632 updates, 480 calls; 304/256/256 updates per arm. ADDITIVE adds 576 replay forwards and 198552 total replay tokens to 141368 memory tokens. Timing scopes and nested clocks are explicitly distinguished. | ACCEPT; no correction. Equal memory exposure is not equal compute/RNG/gradients. |
| R7: claims, history and sending | None | Current summaries and C97 deny all-seed repair, parenting, H1/H2, general G3, clean-lineage, mission and freeze promotion. C11 remains deferred. Historical result text remains; collaborator remains marked UNSENT. | ACCEPT; no correction. This review does not send anything or audit external delivery state. |
| N1: abstract shorthand | Low, optional wording only | `paper_prototype/astra_sprint_abstract_20260912.md:587`, `paper_prototype/main.tex:298`, and `paper_prototype/astra_sprint_draft_20260912.tex:457` say “no scientific retry or changed scorer.” The detailed text correctly explains that a separately pinned collector repaired scorer-module binding without changing scoring rules. | Optional replacement: “no scientific retry or change to scoring rules.” This avoids reading the shorthand as “no implementation change anywhere in collection.” Not a condition of acceptance; no edit performed. |

### Checked six-cell transcription

| Seed | Arm | Exact eligible | Paraphrase content | Held passed | Canary passed | Lost LR0-correct held | Descriptive screen |
|---|---|---:|---:|---:|---:|---:|---|
| 0 | ADDITIVE | 14/14 | 10/14 | 47/48 | 12/12 | 0 | Meets |
| 0 | MEMORY_ONLY | 10/14 | 10/14 | 47/48 | 12/12 | 0 | Meets |
| 1 | ADDITIVE | 7/8 | 7/8 | 48/48 | 12/12 | 0 | Meets |
| 1 | MEMORY_ONLY | 8/8 | 8/8 | 46/48 | 12/12 | 2 | Fails |
| 2 | ADDITIVE | 8/8 | 4/8 | 39/48 | 12/12 | 9 | Fails |
| 2 | MEMORY_ONLY | 3/8 | 2/8 | 47/48 | 12/12 | 1 | Fails |

Locations: `paper_prototype/README.md:144`,
`paper_prototype/main.tex:1834`,
`paper_prototype/astra_sprint_draft_20260912.tex:4073`,
`research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md:121`,
`research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:4433`.
The abstract companion's bounded paragraph starts at
`paper_prototype/astra_sprint_abstract_20260912.md:578`.

## Load-bearing interpretation checks

**Measures and harm.** The stored paired ADDITIVE-minus-MEMORY_ONLY deltas are
exact +4/-1/+5, paraphrase 0/-1/+2, held 0/+2/-8 and canary 0/0/0. Seed2 held
one-gain/nine-loss is not a zero-harm repair. Its nine ADDITIVE losses are also
nine LR0-correct held losses; the one repaired MEMORY_ONLY malformed item does
not offset them. Seed0 LR0 already misses one held item, which both fresh arms
retain as a miss rather than introduce as a regression. The manuscript preserves
these distinctions instead of inferring the screen from net held counts alone.

The archived exact raw-target-byte counts are ADDITIVE 13/14,7/8,8/8 and
MEMORY_ONLY 8/14,8/8,3/8, not the main exact-eligible column. Five strict
canonical memory readouts occur in seed0 ADDITIVE exact; the other 115 memory
readouts are noncanonical. All 480 new calls stopped, with zero length
terminations. The manuscript does not relabel eligibility as canonical or
raw-byte identity.

**Constant alternative.** Archived evaluator-only same-panel constant maxima
are 6/14,4/8,4/8 for both cue variants, from 4/5/5 raw candidates. ADDITIVE
seed2 paraphrase only ties 4/8; MEMORY_ONLY seed2 exact/paraphrase are below it.
The text identifies a descriptive evaluator alternative, not an executed
constant model or causal proof of general keyed binding.

**Native baseline drift.** The stored old/new first-epoch loss pairs are
0.45994/0.46188, 0.32638/0.32588 and 0.18537/0.18589. Raw/finish-change counts
in exact/paraphrase/held/canary order are 5/0/0/0, 1/2/0/0 and 5/5/7/0.
Historical EXTRA_MEMORY exact 13/14,7/8,7/8; paraphrase 10/14,6/8,7/8; and held
47/48,46/48,42/48 are transcribed correctly. Matching source/initialized
**receipts** and full memory schedules does not establish native numerical
parity. No cause is inferred, no alternative fresh control is substituted, and
tiny CPU parity is not used to erase the native discrepancy. These are receipt
comparisons, not fresh authentication of parent or final tensors.

**Collection and custody.** The archived failure is
`AttributeError: 'dict' object has no attribute 'score_row'`. The recovery
restores scorer-module binding while preserving original raw outputs, targets,
failure directories and claims. Stored recovery metadata distinguishes attempt2
collection from scientific retries0. Passing archived raw/source/token/route/
stage-release checks does not excuse genuine content/format failures. The text
explicitly excludes fresh GPU identity checks, independent OS wait/reap
evidence and unlogged reservation-gap accounting; it does not infer live release.

**Cost.** Both arms use the same old EXTRA_MEMORY occurrence/epoch schedule,
original perception parent and fresh optimizer; sum-of-mean CEs is not their
average. The aggregate archive records MEMORY_ONLY 816 memory forwards/updates
and ADDITIVE 816 memory plus 576 replay forwards, still 816 optimizer updates.
Their total processed tokens are 141368 versus 339920; the stated additional
198552 replay tokens are not solely supervised tokens. Each seed has 24 extra
memory positions per epoch, eight epochs, not a balancing-rotation revision.
No new capture or parent-model call is represented as fresh TRY/parenting.

The manuscript's rounded controller, holder, failed-collector, preparation and
recovery spans agree with the archived execution review. The 0.543290 hours is
logged preparation plus original-holder wall time across allocations, not a
GPU-active meter. Original holder contains the failed collector, and the
separate 77.633-second CPU recovery and 4.265-second once-run local reduction
are not additional fits or generation. Nested spans are not double-counted.

## Accepted evidence versus still-pending claims

Accepted here: faithful reporting of all six fresh outcomes, retained failures,
matched memory exposure with unequal objective compute, seed-dependent
acquisition/retention tradeoffs, and disclosed baseline drift and collection
recovery. The archive itself has `all_seed_screen` false for both arms,
`automatic_promotion=false`, `fit_authorized=false` and `scientific_pass=null`;
the manuscript is consistent with those limits.

Not established or promoted: native baseline parity or its cause; an isolated
replay mechanism; all-seed retention repair; robust general key binding;
repeated-cycle retention; parenting or matched parent-removal effects; H1/H2;
general G3; clean lineage; C11 completion; mission completion or freeze.
The same-history raw-chronological LoRA comparator remains absent. Nothing in
this manuscript acceptance closes those scientific gaps or authorizes a run.

## Exact reviewed manuscript hashes

All are SHA256 of actual file bytes, not canonicalized JSON or Git blob IDs.

| Canonical file | Before, at 8921724f | Reviewed current |
|---|---|---|
| `paper_prototype/README.md` | `9d868e0a67fe8a4e1533b12b1000d37681888d2f45dc925604de571bf6911a64` | `6fbd201ce6c605795c873e66a948d5eab2993ee0e7b855681462d981b2eea66b` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `38ad8c1511b9dd0299b215e5d1d2925667d3dbabf04714770f20eed94cc8eeea` | `340d5e4b496a7f34eb070fcd6f7664c9e2a782ac8006795cb5429b8fd1f9eaca` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `b4462b3f9ca53abca6d8341f313b2e319ba7c7eab4da60096c0aa16c6a2660dc` | `46d510f63878cce0e7cc28d3d7bbbb3b6c936e04fb22d3cd863142ad5cdadfdf` |
| `paper_prototype/main.tex` | `721c43008c4341d2b34367b853226cb234300dcd4aa8a874f701658ae8cef5c9` | `2b5a72870cfd257e2b2f9f10a2fd3ac8815fcfb3a968442d312a0f1e8b1f04bf` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `01fe2454c5e5720a8041405bd56f2d8e91559f1ad8d8f93cd9781e41f5e22012` | `0ba73c2d02f89bfea26ffe8bb1d4e4113e64a00af0ccb93da4d882a53a8e1d8b` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `aa30962bd27c91d8f5950612f38a23d5ac5073bc51411c28895c4b10ab62d5f2` | `4c266a4632745c1344477c531beecf1f71786a1f8eb21d6e4d1707daf3a74e10` |

## Evidence hashes

Archived paths below are relative to
`research_notes/astra_memos/receipts_20260912/` and were also checked against
archive commit `f15dec6cb0fa678dd00caef608db9e110dc9ed38`.

| Evidence | Exact SHA256 |
|---|---|
| `astra_additive_replay_recovered_analysis_result_20260913_attempt1/analysis.json` | `848602f01ca0596306dcb629a2e1d6896e08620cc6a67baa996853118c1cdb89` |
| `astra_additive_replay_recovered_analysis_result_20260913_attempt1/execution_review.json` | `c7e8f7eb64a42589869e6f5f903854044405eb9acfc944102d450164b12c35d1` |
| `astra_additive_replay_recovered_analysis_execution_20260913_attempt1.md` | `b3397ae8f4a29569f2f49e5d96a21410e73d072b101c439424d401ad5bfcfdfa` |
| Author handoff `/tmp/astra_manuscript_seq161_author_handoff_20260913.md` | `9b5ca097811c8c9751de9f652cfc6339c663394aecff096c95247816f3f4aabe` |
| Protocol `research_notes/astra_memos/ASTRA_ADDITIVE_REPLAY_DEV_2026-09-13.md` | `724d5a6e1aea7dca4b0ae42aec6e2fd0252b98646f7c903432927263f2c391e9` |

## Validation performed and limits

Read-only transcription checks passed: 30/30 new table rows match stored JSON;
six-cell abstract prose matches; before/after author pins match; three archive
commit bindings match; added local Markdown link targets exist; both TeX C97
section/table labels occur exactly once; both previous complete abstract texts
remain verbatim. Scoped `git diff --check` passes. The six-file diff is
551 insertions/18 deletions; deleted lines are current-cut/header metadata or
SEQ160 cut-end wording, not old scientific table cells. New sequence references
are SEQ160 historical context and SEQ161; later outcomes were not added.

No full TeX/PDF build, submission-length assessment, external-reference audit,
old comprehensive review, scorer validation, reduction rerun, process monitor,
archive extraction or new tensor verification was performed. Unchanged earlier
claims are not recertified by this bounded review. UNSENT is the preserved
manuscript status; no sending action was taken.

Only output written:
`/tmp/astra_manuscript_seq161_independent_review_20260913.md`.
Core/tests remain EDITSTOP. Review acceptance binds only the six current hashes
above; any subsequent edits need their own narrowly scoped hash rebind.
