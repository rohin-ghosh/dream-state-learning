# Independent manuscript review — SEQ101–103 — September 12, 2026

## Verdict

**FAIL for clean exact-byte editorial signoff: one LOW-severity method-description correction in C47. Scientific endpoints, numerical transcription, scientific boundaries, preservation, and abstract parity PASS.** No numerical correction, experiment rerun, architectural change, or launch veto is indicated. Main owns integration; this review changes no manuscript bytes and does not pre-approve a future hash.

## Required smallest correction

**R1 — LOW / editorial provenance precision.** `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1332` says:

> checks remain attributed; local review recomputes logits from archived float32
> vectors, not absent model weights.

The archived values already **are logits**. The independent audit decoded them and recomputed log-probabilities, NLLs, argmaxes, and differences; it did not recompute model logits. The source explicitly describes this distinction at `research_notes/astra_memos/receipts_20260912/astra_hf_parity_independent_review_20260912.md:31` and `research_notes/astra_memos/receipts_20260912/astra_hf_parity_independent_review_20260912.md:33`; absent-weight and non-reload qualifications are at that file's line 27. The terminal memo likewise describes a recomputed **loss**, not newly computed logits, at `research_notes/astra_memos/ASTRA_HF_PARITY_TERMINAL_2026-09-12.md:12`.

**Smallest correction:** at claim-map line 1332, replace only `recomputes logits` with `recomputes log-probabilities and NLLs`. Preserve the adjoining native-custody and absent-weight qualifications. This repairs the sole required wording issue without changing any result or claim boundary. The surrounding text already rejects model-weight reauthentication and full cross-backend parity, so this is a low-severity description error, not an identified false numerical result or affirmative model-origin authentication claim.

## Scope and method

- Read the specified handoff, compared all six files against its exact pre-edit backups using filesystem diffs (not Git), and inspected changed hunks plus narrowly relevant context. Whole-file reads were used for hashes and mechanical preservation/parity checks, not a wholesale manuscript reread.
- Read the three archived terminal memos, the associated independent reviews and dose addendum, Main's two JSON analyses, and the fading CSV. Read all four repetition and twelve fading archived reductions in memory and checked their complete counts/costs against Main's analyses. Read the HF capsule's `main_summary.json`, `reduction.json`, and `main_release.json` directly.
- Independently rehashed the handoff, all six pre-edit backups, all six reviewed files, and the three terminal capsules. Counted capsule regular files (507/1448/48) and confirmed no `.safetensors`, `.bin`, or `.pt` weight members. This is not a fresh per-member custody audit or a new reconstruction of every raw output/logit statistic; those deeper checks remain attributed to the archived independent reviews.
- Used read-only shell operations and inline Python 3 standard-library checks. No network, GPU/model/tokenizer execution, Git, supplied scorer/reducer execution, installation, repository edits, external communication, or changes to other workers' files. Only this requested review file was written.

## Claim checks

### C45 / SEQ101 — PASS

The new canonical paragraph at `paper_prototype/main.tex:360`, companion subsection at `paper_prototype/astra_sprint_draft_20260912.tex:1391`, and claim-map entry at `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1208` match the terminal memo's recipe and four-cell results (`research_notes/astra_memos/ASTRA_FUNDAMENTAL_REPETITION_TERMINAL_2026-09-12.md:11` and line 25).

- Four fresh seed0 teach/control × SHORT/LONG cells: ACT 32/32, teach/control adherence 32/0, and red-only memory 4/16. Each cell processes 289088 input tokens including 58368 targets, with 80 optimizer steps.
- Sixteen-fold token/copy presentations are explicitly **not** sixteen-fold sequential optimizer practice or an established sixteen-fold effective write dose. SHORT batch4/accum16, unchanged original groups/update, accumulation normalization, homogeneous-versus-mixed loss weighting, and nonidentical dropout/order behavior are appropriately qualified. The independent dose addendum at `research_notes/astra_memos/receipts_20260912/astra_repetition_dose_addendum_20260912.md:7` supports that language.
- Original-training-prompt recall remains untested on repetition checkpoints. Original-checkpoint SEQ100/103 evidence is not transferred to them. Final arithmetic microbatch losses are distinguished from memory losses and epoch means; LONG's access to earlier gold answers is a possible training shortcut, not demonstrated test-time copying or a diagnosed cause.
- The source review supports full same-arm output-vector equality at `research_notes/astra_memos/receipts_20260912/astra_repetition_independent_review_20260912.md:34`. No general impossibility, latent-absence, or separate-adapter requirement is asserted.

### C46 / SEQ102 — PASS

`paper_prototype/main.tex:362`, `paper_prototype/astra_sprint_draft_20260912.tex:1415`, and claim-map C46 at line 1258 preserve the **one original SEQ098 seed0 teaching adapter** scope. Three rate forks are not three starting-seed replications; none starts from a repetition checkpoint. Four 16-update phases carry weights but reset AdamW each phase.

All 15 archived CSV rows agree with Main's JSON and the three new tables: `paper_prototype/README.md:33`, `paper_prototype/astra_sprint_draft_20260912.tex:1428`, and `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md:1269`. Initial adherence is 32/32 for the shared baseline. LR0 stays 32/32; both positive rates are 0/32 after 16/32/48/64 updates. Correct ACT stays 32/32 and red-only memory 4/16, with exact correct ACT-only uptake on all 32 arithmetic probes at every positive-rate readout. Source: `research_notes/astra_memos/receipts_20260912/astra_fading_independent_review_20260912.md:21` and line 28.

The text correctly distinguishes exact new target-form uptake from mere disappearance of PREDICT, records 12 fits/576 new calls, attributes parameter equality to native receipts, and reuses rather than remeasures the original baseline. No within-phase transition timing, winning learning rate, passive fading, new arithmetic knowledge, selective forgetting, replay benefit, general G3, or H1/H2 conclusion is drawn. Later 19:21 UTC replications contribute no outcomes.

### C47 / SEQ103 — numerical and scope PASS; R1 wording correction

`paper_prototype/main.tex:364`, `paper_prototype/astra_sprint_draft_20260912.tex:1453`, and claim-map C47 at line 1317 accurately distinguish **16/16 first-token agreement** from **4/16 gold-color accuracy** on the original teaching checkpoint's 16 training prefixes. The HF summary records red on all 16, zero stored prefix/full color-position logit difference, mean color NLL 1.5662938430630773, mean gold-conditioned EOS NLL 0.0002199387172154843, and maximum two-target-loss discrepancy 5.402754261751852e-7. Printed roundings match.

The 32 forwards are 16 prefix plus 16 full labeled forwards, not new generations or optimization. HF internal vector equality is not full HF/vLLM logit parity; vLLM logits were not captured. Neither autoregressive HF generation equivalence nor a unique training-failure diagnosis, latent-absence claim, repetition-checkpoint conclusion, or model-origin authentication follows. These limits agree with `research_notes/astra_memos/ASTRA_HF_PARITY_TERMINAL_2026-09-12.md:23` and the archived HF review at line 68. Only the description of what the local audit recomputed needs R1.

### Costs and overall scientific boundaries — PASS

At `paper_prototype/main.tex:364`, companion line 1467, README line 46, and claim-map lines 1239/1292/1340:

- SEQ101: 192 calls, 8524 input/1888 actual output tokens, output cap 12288, fit/readout supervision 1717.633265 seconds.
- SEQ102: 576 calls, 25572/3648 tokens, output cap 36864; 39936 training input tokens include 4512 targets. Worker/controller/full-reservation windows are 2125.367463/3073.313819/3460.763131 seconds.
- SEQ103: 32 forwards, worker 64.699761 seconds versus full reservation 141.936394 seconds; no new fit or vLLM generation.

These are appropriately scoped, nested/overlapping clocks, not additive active-compute or billing measures. Inherited work is not recharged. C00 at claim-map line 5 and C46 at line 1285 explicitly withhold general G3, P1/G5/parenting, H1/H2, clean model origin, and mechanism freeze. All 64 confirmation cases remain unrequested. The added abstract and summaries preserve these boundaries; no new affirmative general-gate or model-authentication claim was found. Frozen-base operation is not confused with a mechanism-freeze decision. The collaborator document remains explicitly UNSENT.

## Preservation, abstract, and static structure — PASS

- All six pre-edit hashes match the handoff; all six current hashes match its final EDIT-STOP hashes.
- Canonical abstract at `paper_prototype/main.tex:45` is byte-identical to backup: abstract-body SHA256 `46542852cf87ab1a132e239e6ea9c03221c3b0364c6ef71a436ee4c1b53c5cbd`. The entire canonical prefix before line 358 and Discussion-to-end at line 366, including the appendix, are identical. The sole old canonical sentence replacement updates prospective status; no author-thesis rewrite is present in this diff.
- All **58 pre-existing tables** are byte-identical and remain in order: main 8, companion 16 (15 table environments plus one longtable), README 20, claim map 14. The three curve tables are additions. C01–C43 are untouched; existing C44 changes only historical engineering-status framing. Earlier endpoints are not replaced.
- Companion TeX abstract at `paper_prototype/astra_sprint_draft_20260912.tex:56` and Markdown abstract at `paper_prototype/astra_sprint_abstract_20260912.md:14` are **exactly equal after whitespace normalization: 234 words, <=250**. Normalized SHA256 `a5dac7f0da14ca5162ba94bffb6a614e29d7e8b7ee3c45cfefaafbc06003f65a`. This is not substitution of the canonical abstract.
- Both TeX files pass escape-aware brace balance, environment nesting, unique-label and resolved-reference checks: canonical 32 labels/116 references; companion 16 labels/12 references. Claim headings are uniquely consecutive C00–C47.
- No `pdflatex`, `latexmk`, `tectonic`, or `bibtex` executable is available on PATH. No compilation or PDF inspection occurred; no layout, pagination, or compiler-success certification is given.

## Exact reviewed manuscript hashes

| File | SHA256 |
|---|---|
| `paper_prototype/main.tex` | `d384855e5c72cd669553505b9d9cdd7f81fbbbc61f47abc41c5f6842000cf6b7` |
| `paper_prototype/README.md` | `5b2356dc19a6eb997f22d07e35a644188857f8fc5480710d1dfeac4f53663b11` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `bbe93571046b0343c40394567984b15abe7286c697e1c4fe92f91db12d82efef` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `6b8242e620ad65d18acffb6fc0c5ba1fee7d555118b70950ba26c15cb88c092f` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `d15eabe46fd2e28f7895d2d98403b26f963dfd623ecf32c0dc94b2bc25e23d72` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `a3a8f2290d4a8c500d7e729eb9b6fc34374d11711e751342ed521eef18b77004` |

Handoff `/tmp/astra_manuscript_seq101_103_handoff_20260912.md`: SHA256 `bd8acc56152dff4c52038a3f758027779a19610761203f8f32b38b5e935e4b91`. Backup root: `/tmp/astra_manuscript_seq101_103_preedit_20260912.Q2DuzC`; all six hashes independently matched its handoff table.

## Exact evidence bindings

Paths in the following table are relative to `research_notes/astra_memos/`.

| Evidence file | SHA256 |
|---|---|
| `ASTRA_FUNDAMENTAL_REPETITION_TERMINAL_2026-09-12.md` | `100ceabae13155ef17c307cbe11c3d7eb4fae5f2c4592471a42636772c271832` |
| `ASTRA_FUNDAMENTAL_FADING_TERMINAL_2026-09-12.md` | `17eea6846e04372f0bd31bb7459b44afa6e9c993ac547c7dd3617d100a9dbec8` |
| `ASTRA_HF_PARITY_TERMINAL_2026-09-12.md` | `e55a96a49dbcbad73ee549eb06e039b2cd3e8fe6206664aceab7db475c85d779` |
| `receipts_20260912/astra_repetition_independent_review_20260912.md` | `3ec40e8d4a98c46d33e9e1e302a6531bcf8e0b5fa3fa9ee874cd5e8fc470b23a` |
| `receipts_20260912/astra_repetition_dose_addendum_20260912.md` | `9a0dd2261e8a47a0699091474c9e8dc3b0f3c4c7601086c34dcbce1a9305a49b` |
| `receipts_20260912/astra_fading_independent_review_20260912.md` | `e3ab94d2b38acda6a1299c7d1889e0b1c56d7c2975cd474e8e870f8d5836fe17` |
| `receipts_20260912/astra_hf_parity_independent_review_20260912.md` | `207d77c83c5ea60d65ee5153ba145655b900f00c55e91677b00c8b6ec9d38f97` |
| `receipts_20260912/astra_repetition_main_analysis_20260912.json` | `efa6c031796a9e01ff8161d6d6ab1881e2d5a8ecdbdfad9d9bf4d504f8bc38bc` |
| `receipts_20260912/astra_fading_main_analysis_20260912.json` | `5feb4bf19a161638722c4058b797eec9b4691888fff425cbd8a3d5cc1f1c5665` |
| `receipts_20260912/astra_fading_curves_20260912.csv` | `567b5c79bdcf44e45ca20728cabe50ffc783a3b67e46f8503f0540e790bc1b18` |
| `receipts_20260912/astra_fundamental_repetition_terminal_20260912.tgz` | `36e9ca2637d1f78ab218afd3348b0cc547ea098188e3d418aa2b08c4e48a198b` |
| `receipts_20260912/astra_fundamental_fading_terminal_20260912.tgz` | `3a2564219790cc7a31f4350cd2013eb323577e5d41003a5bf322eeb16fc415ff` |
| `receipts_20260912/astra_fundamental_hf_parity_terminal_20260912.tgz` | `54ec0bf1613e67d6256062a24e1ed30fe2b49bfa73a5675d1b83c0b9d4653e32` |

**Disposition for Main:** make only R1's phrase-level correction if accepted, bind the changed claim-map hash, and retain this review against the original hashes. No other required correction was identified in the requested changed material. No launch decision is made here.
