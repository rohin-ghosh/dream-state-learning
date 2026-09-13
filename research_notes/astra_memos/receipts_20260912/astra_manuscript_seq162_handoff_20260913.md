# Manuscript through SEQ162 — author handoff / EDITSTOP

September 13, 2026. Bounded six-file integration only. Ready for independent
review, not self-certified independent acceptance. No commit, push, sending,
native/model/tokenizer/GPU/network call, collection, scientific rerun, fit,
score reduction or change to frozen sources/results. Core/tests untouched.
Collaborator remains **UNSENT**. No later outcome or proposed repeat is included.

## Exact owned paths and final file-byte SHA256

| Path | Final SHA256 |
| --- | --- |
| `paper_prototype/README.md` | `bd539d2212158866ac8c484d6caac81fe31a1036b0b08d8288d4e56a2f8d537f` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `37a4a26d2b719d7a583c40b03e0354b1ccd89343550ea76995358dc72d4a2a8a` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `e3eb443a1cc5bc1e2e125572c2a1ed53d2c15bc36728900395496564d89288b4` |
| `paper_prototype/main.tex` | `a18bf2e74e2470d4022749ab0c3df7612b9534a7ff94f63d08e7662f0a1b9aff` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `a6f53b251554698903b0ded0f79ad54c22fafb63798aa6a02760b6fc9c7fe3ff` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `1196ef9ee31ddff3465da2e257d1008f85681b643500326f47efbb9ba84c259c` |

The only other new file is this handoff. Its byte hash is reported separately.

## Pre-edit pins and preservation

| Path | Pre-edit SHA256 |
| --- | --- |
| `paper_prototype/README.md` | `6fbd201ce6c605795c873e66a948d5eab2993ee0e7b855681462d981b2eea66b` |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `0700af49ea1008caaeeffbe109abf5d9ed665954b8d07d2a52c4d4c86d07e810` |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `539e1ae48623e2b38221ad29fa6431d97a203fda7b83b2a6ce8a4a28977f4c30` |
| `paper_prototype/main.tex` | `4e4a2eb9b8360cb217e3ccec28f3e79222f718356702db0d2dc4252d297f6d99` |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `0ba73c2d02f89bfea26ffe8bb1d4e4113e64a00af0ccb93da4d882a53a8e1d8b` |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `4c266a4632745c1344477c531beecf1f71786a1f8eb21d6e4d1707daf3a74e10` |

All six were guarded against these hashes before applying changes. Read-only
HEAD comparison matched these pre-edit bytes at validation. Removed lines are
only cutoff/current-heading changes; prior substantive text and every existing
Markdown table row remain unchanged. SEQ161 six-cell results, nine seed2 ADDITIVE
held losses, baseline drift, constant caveats and original rc1/collection-only
repair distinctions are retained, not reinterpreted or rescored.

## Changes

- All six current summaries now name SEQ162/C98; SEQ161 summaries explicitly
  retain their historical cut. No title, authors, bibliography or reference edit.
- README gains the bounded diagnostic and exact archived source links/pins.
- Markdown abstract and both TeX abstracts gain the same short diagnostic
  paragraph, without replacing previous findings.
- Both TeX manuscripts gain `sec:seq162-gradient` exactly once, using their
  existing C98 citation conventions; no new table or measured endpoint.
- Claim map gains C98, preserving C97 and its entire six-cell evidence.
- Collaborator receives a bounded current UNSENT section with archived links.

## Licensed observation, not causal or repeatability evidence

One fresh instrumented seed0 process per path: OLD is the frozen historical
trainer and NEW is the additive trainer's **MEMORY_ONLY** path, not an additive
replay-loss intervention. First occurrence:
`own-repair:seed0:EXTRA_MEMORY:000`.

Recorded initialized trainable tensors, input/mask, settings, fresh optimizer,
environment and six-boundary RNG snapshots match. Both first scalar losses are
**1.907779335975647**. Gradient data hashes differ for **256/392** tensors;
compared shape/dtype/device metadata match. The tensors are correlated components
of one backward per path, not independent replications.

Both paths stop after that backward, before optimization: **zero optimizer
steps, adapter saves and readouts**, unchanged parents/trainable parameters,
absent frozen-base gradients. Worker52.135/53.052s are nested inside holder53/54s,
both holder rc0. No GPU-active-time claim. NEW's preserved scratch failure.json
is deliberate interception cleanup; its step journal is empty, not a completed
fit or a failed scientific endpoint.

The observation precedes evaluation of OLD `(loss / cfg.grad_accum).backward()`
with grad_accum=1 versus NEW `loss.backward()`. It hashes the original loss,
not OLD's division result. The graph/expression difference lies inside the
bracket but is not isolated as a cause. Matching trainable initialization does
not authenticate every in-memory base tensor. Equal loss/RNG does not establish
equal logits, activations, saved tensors, dropout masks, recomputation or
reduction ordering. Configuration flags do not identify an executing kernel.

First **observed** nonidentity is in materialized gradients; its underlying
origin need not be backward. No effect size, within-path repeatability,
later-step equivalence or explanation of historical drift follows. No positive
replay causality, H1/H2, parenting, general G3, clean-lineage, mission or freeze
promotion. C11 remains deferred. The research question remains unresolved.

## Source bindings inspected

All paths below are relative to `research_notes/astra_memos/receipts_20260912/`.

| Source | Actual byte SHA256 |
| --- | --- |
| `additive_native_parity_seed0_20260913_attempt1/comparison.json` | `4e52301965fe1b2142fe46aac741cca0a6f64bcd45a45f7875616d79630f2120` |
| `additive_native_parity_seed0_20260913_attempt1/plan.json` | `f81eef545ba86eb52b17d1a440d7f0783c6fb62290c3164184b855158d9b92d5` |
| `additive_native_parity_seed0_20260913_attempt1/OLD/receipt.json` | `24c5bbf31aa735e06ee8f27786dceb784afe6e271385934ba23ca01aef2386a0` |
| `additive_native_parity_seed0_20260913_attempt1/NEW/receipt.json` | `d4ad625def96bc6abc3b25c476f20ccf3c8ca99c4730775244fbc79f021ba44c` |
| `astra_native_parity_archive_receipt_20260913.json` | `ee31200c8b1cecf8e9a7f52ef7427bace5190671ba5c9583fa67afded61c639e` |
| `astra_native_parity_interpretation_20260913.md` | `35b4438b2a5571cb8a041b4fe278b998d3bdcbdd5b5a280e82a4f0b94f0aec5f` |
| `astra_additive_native_parity_probe_handoff_20260913.md` | `9f8a97badb3e57541d1e79b4e4106750178cc556d91bc54477a60d13d7123f68` |

The archived interpretation is byte-identical to the requested
`/tmp/astra_native_parity_interpretation_20260913.md`. The archive receipt reports
45 members/614400 bytes, zero new adapters and full archive SHA256
`3fd33489a8c0f7eebe0566307f8404421628339e84a111642b3536a80feefad0`.
This author verified the receipt bytes, not a fresh archive extraction/rehash.

Read-only source pins also checked:

- `gpu/astra_additive_native_parity_probe.py`:
  `a331210a8f230c4ee3b5ff3cbe1fcef09a26925502fb9716c7e3ec617d914b7a`.
- `/tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py`:
  `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7`.
- `/tmp/astra_additive_replay_train_20260913.py`:
  `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0`.

## Checks performed and limits

PASS, local stdlib/read-only checks:

1. Exact receipt/comparison/plan/interpretation/source hashes above.
2. All twelve archived phase files match their OLD/NEW receipt byte hashes.
3. Existing gradient inventory has256/392different data hashes and equal
   shape/dtype/device metadata; scalar loss and loss-tensor records agree.
   This counts existing records, not recomputation of gradients or a new
   comparison/reduction output. No scoring CLI ran.
4. All twelve observer-RNG-nonconsumption flags are true; both post-backward
   records declare absent base gradients and unchanged trainable parameters.
5. Retained NEW scratch files match receipt hashes, including empty steps.jsonl.
6. Six pre-edit hashes match HEAD; diff deletions restricted to headings/cutoff.
   All existing Markdown table rows preserved. Added text excludes later SEQ163.
7. Fifteen new relative file links resolve. C98 and claim restrictions appear
   in all six. Existing C97 table/section labels and new C98 section labels
   occur once per TeX file; environment sequences unchanged, added braces
   balance, no unescaped underscores in new TeX text.
8. Scoped `git diff --check` passes. Read-only Git inspection only; no commit,
   index/staging or branch changes.

No LaTeX/PDF build performed (`pdflatex` unavailable); static checks do not
certify rendering, submission length or venue readiness. No comprehensive old
review, rerun, fresh base authentication, native process/release verification,
or source/scorer modification. Pending independent manuscript review remains
separate from this author handoff. **EDITSTOP: exact six hashes frozen above.**
