# Independent manuscript review — SEQ162 / C98

Date: September 13, 2026.

**Verdict: ACCEPT for bounded manuscript integration at the exact six hashes
below. No blocking discrepancy found.** This is independent review of the
author's changed claims, not scientific acceptance, causal identification,
repeatability certification, approval to send the collaborator draft, or a
native/model launch gate. Collaborator remains UNSENT. The research question
and SEQ161 baseline drift remain unresolved; C11 remains deferred.

## Scope and immutable review targets

Requested scope: Beauvoir's six manuscript artifacts through SEQ162, using
existing receipts only, with particular scrutiny of first-gradient nonidentity
versus cause, zero updates, no repeatability claim, and preservation of SEQ161.
I did not author or edit the reviewed artifacts. Only this review file was
written. No source/prose edits, commits, staging, network, native/model calls,
scientific tests, scoring/reducer/comparison CLI, or science rerun occurred.

Read-only Git status and applicable AGENTS instructions were inspected.
Review baseline HEAD was `fe3225274c72b37136961ec9c96a04921f20a3f4`.
All six HEAD byte hashes matched the author's pre-edit hashes, and all six
working-file hashes matched the author's freeze at intake and again after
evidence checks. Other workers' changes were preserved.

Author handoff: `/tmp/astra_manuscript_seq162_handoff_20260913.md`, SHA256
`38e4db5178636da199d93ce5d0609907531dd5fa42f8cb52cab4a86941229bfc`.
The handoff was used as a manifest, not accepted as proof of its own claims.

| Reviewed artifact | Exact SHA256 | Verdict |
| --- | --- | --- |
| `paper_prototype/README.md` | `bd539d2212158866ac8c484d6caac81fe31a1036b0b08d8288d4e56a2f8d537f` | ACCEPT |
| `paper_prototype/astra_sprint_abstract_20260912.md` | `37a4a26d2b719d7a583c40b03e0354b1ccd89343550ea76995358dc72d4a2a8a` | ACCEPT |
| `paper_prototype/astra_sprint_draft_20260912.tex` | `e3eb443a1cc5bc1e2e125572c2a1ed53d2c15bc36728900395496564d89288b4` | ACCEPT |
| `paper_prototype/main.tex` | `a18bf2e74e2470d4022749ab0c3df7612b9534a7ff94f63d08e7662f0a1b9aff` | ACCEPT |
| `research_notes/astra_memos/ASTRA_COLLABORATOR_DRAFT_2026-09-12.md` | `a6f53b251554698903b0ded0f79ad54c22fafb63798aa6a02760b6fc9c7fe3ff` | ACCEPT; UNSENT |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | `1196ef9ee31ddff3465da2e257d1008f85681b643500326f47efbb9ba84c259c` | ACCEPT |

## Evidence binding

The following hashes were independently checked against local file bytes.
Paths in this table are relative to
`research_notes/astra_memos/receipts_20260912/`.

| Existing evidence | Verified SHA256 |
| --- | --- |
| `additive_native_parity_seed0_20260913_attempt1/comparison.json` | `4e52301965fe1b2142fe46aac741cca0a6f64bcd45a45f7875616d79630f2120` |
| `additive_native_parity_seed0_20260913_attempt1/plan.json` | `f81eef545ba86eb52b17d1a440d7f0783c6fb62290c3164184b855158d9b92d5` |
| `additive_native_parity_seed0_20260913_attempt1/OLD/receipt.json` | `24c5bbf31aa735e06ee8f27786dceb784afe6e271385934ba23ca01aef2386a0` |
| `additive_native_parity_seed0_20260913_attempt1/NEW/receipt.json` | `d4ad625def96bc6abc3b25c476f20ccf3c8ca99c4730775244fbc79f021ba44c` |
| `astra_native_parity_archive_receipt_20260913.json` | `ee31200c8b1cecf8e9a7f52ef7427bace5190671ba5c9583fa67afded61c639e` |
| `astra_native_parity_interpretation_20260913.md` | `35b4438b2a5571cb8a041b4fe278b998d3bdcbdd5b5a280e82a4f0b94f0aec5f` |
| `astra_additive_native_parity_probe_handoff_20260913.md` | `9f8a97badb3e57541d1e79b4e4106750178cc556d91bc54477a60d13d7123f68` |

The existing comparison's OLD/NEW receipt hashes, both receipt-to-plan and
probe bindings, all twelve phase-file hashes, both environment-file hashes,
and retained NEW scratch-file hashes matched. The archived interpretation
was also byte-identical to `/tmp/astra_native_parity_interpretation_20260913.md`.

Read-only code inspected for observation placement, with hashes verified
against the archived plan:

| Source | Verified SHA256 |
| --- | --- |
| `gpu/astra_additive_native_parity_probe.py` | `a331210a8f230c4ee3b5ff3cbe1fcef09a26925502fb9716c7e3ec617d914b7a` |
| `/tmp/astra_level1_real_record_source_20260913_attempt1/organism_v6/train_adapter_v3.py` | `7bbf165fcb4b8ae3a1180328bcd19f57382c30516daddc95fd61e8a2c749fad7` |
| `/tmp/astra_additive_replay_train_20260913.py` | `3f2e73ef69b12c8db211e1d3043e4559713e036ffe09571ab8bc4c5199a426a0` |

## Findings and disposition

### 1. First observed nonidentity, not a cause — ACCEPT

The existing records support one instrumented seed0 execution per path at
`own-repair:seed0:EXTRA_MEMORY:000`. OLD is the historical trainer; NEW runs the
additive trainer's MEMORY_ONLY path, not a replay-loss treatment. The source
binding checks seed0, batch_size=grad_accum=1 and the matching historical/new
configurations; the worker selects MEMORY_ONLY explicitly.

All five pre-backward phase documents are equal across paths. Recorded
initialized trainable tensors, encoded input/mask, settings, fresh empty
optimizer/defaults, environment, and all six Python/CPU/visible-CUDA RNG
snapshots match. All twelve observer-RNG-nonconsumption flags are true. Both
scalar losses are `1.907779335975647`, including identical recorded scalar
loss-tensor metadata/data hash.

The archive receipt records 256 differing gradient data hashes among 392
tensors, with equal shape/dtype/device metadata. Inspection of the stored
per-tensor hash inventory agrees with those existing counts and metadata;
no gradient arrays were recomputed, scientific endpoints rescored, or new
comparison/reduction artifact generated. The unit is a tensor digest, not an
element, independent replication, effect-size measure, or performance result.

The probe trace at `gpu/astra_additive_native_parity_probe.py:178` calls the
before-backward observer before the entire statement. OLD source line818 is
`(loss / cfg.grad_accum).backward()`; NEW line216 is `loss.backward()`.
The observer at probe line281 reads the original loss, not OLD's later division
result. After-backward observation occurs before execution of the next line,
and captures materialized gradients. Thus the observed bracket includes the
divide-by-one graph/expression difference without isolating its causal effect.

The new summaries and detailed sections explicitly distinguish first observed
gradient nonidentity from the origin of the underlying difference. They do
not infer equal logits, activations, saved autograd tensors, dropout masks,
checkpoint recomputation, or reduction order from equal scalar loss/RNG.
No attribution to divide-by-one, bf16, checkpointing, a selected kernel, or
CUDA nondeterminism is asserted. SEQ161 historical drift is not explained away.

### 2. Zero optimizer dose and intentional interception — ACCEPT

Both receipts have `FIRST_BACKWARD_CAPTURED_ZERO_UPDATES`, optimizer_steps=0,
adapter_saves=0, readouts=0, and parent_unchanged=true. Both after-backward
records have trainable_parameters_unchanged=true and base_gradients_absent=true.
The frozen probe checks these conditions and interrupts before the next
trainer statement; it also traps optimizer-step/adapter-save calls.

OLD/NEW worker elapsed times round to 52.135/53.052 seconds; the separate
holder exit receipts record 53/54 seconds and rc0. Manuscript text correctly
treats these as nested clocks, not additive costs or GPU-active time.
NEW's hash-bound failure.json records `error_type=FirstBackwardCaptured`;
its step journal is zero bytes. The draft preserves this as deliberate
interception cleanup, not a completed fit or failed scientific endpoint.
Zero optimizer dose does not mean no forward/backward computation occurred.

### 3. No repeatability or broader promotion — ACCEPT

All six updated summaries explicitly reject within-path repeatability and
causal explanation. The longer sections state one backward per path and
correlated tensor components, with no later-step/historical reproduction or
effect-size claim. The interpretation's proposed OLD-only repeat remains a
proposal, explicitly not an outcome in this cut. No SEQ163/164 additions were
found. No positive replay causality, H1/H2, parenting, general G3, clean-lineage,
mission or freeze promotion is introduced; collaborator remains UNSENT.

### 4. SEQ161 preservation — ACCEPT

Diff inspection found only cutoff/current-heading/comment deletions; every
prior substantive line is retained. All existing Markdown table rows remain.
The entire C97 section in the claim map is byte-for-byte unchanged apart from
surrounding blank lines. Both TeX SEQ161 section/table labels remain unique.

These existing SEQ161 sources were independently hash-checked:

- `astra_additive_replay_recovered_analysis_result_20260913_attempt1/analysis.json`:
  `848602f01ca0596306dcb629a2e1d6896e08620cc6a67baa996853118c1cdb89`.
- `astra_additive_replay_recovered_analysis_execution_20260913_attempt1.md`:
  `b3397ae8f4a29569f2f49e5d96a21410e73d072b101c439424d401ad5bfcfdfa`.
- `astra_additive_replay_recovered_analysis_result_20260913_attempt1/execution_review.json`:
  `c7e8f7eb64a42589869e6f5f903854044405eb9acfc944102d450164b12c35d1`.

Paths are relative to the same receipts directory. The preserved six table
cells agree with existing aggregate fields, without running a scorer:

| Seed / arm | Exact eligible | Paraphrase | Held | Canary | Lost LR0-correct held | Screen |
| --- | --- | --- | --- | --- | --- | --- |
| 0 ADDITIVE | 14/14 | 10/14 | 47/48 | 12/12 | 0 | Meets |
| 0 MEMORY_ONLY | 10/14 | 10/14 | 47/48 | 12/12 | 0 | Meets |
| 1 ADDITIVE | 7/8 | 7/8 | 48/48 | 12/12 | 0 | Meets |
| 1 MEMORY_ONLY | 8/8 | 8/8 | 46/48 | 12/12 | 2 | Fails |
| 2 ADDITIVE | 8/8 | 4/8 | 39/48 | 12/12 | 9 | Fails |
| 2 MEMORY_ONLY | 3/8 | 2/8 | 47/48 | 12/12 | 1 | Fails |

Seed2 ADDITIVE's nine held losses and the 4/8 evaluator-only constant tie
remain explicit. Baseline drift persists despite matching memory items/order;
original rc1 collection failures, the separate collection-only zero-dose
nonretry repair, and the launcher anomaly remain in the unchanged C97 text.
The existing recovery records confirm zero fits/updates/generation and no
scientific retry. Existing all-seed screens remain false, scientific_pass
remains null, and automatic_promotion remains false.

## Nonblocking advisories and limits

1. Keep **recorded trainable initialization** distinct from authentication of
   every in-memory frozen-base tensor. The current wording is appropriately
   narrow; this review does not supply that missing authentication.
2. Do not shorten the result to “backward caused divergence,” “CUDA was
   nondeterministic,” or “392 replications.” Equal scalar/RNG observations do
   not support those claims. A future repeat requires a new evidence-bound
   review; this acceptance supplies no prospective repeatability conclusion.
3. The archive receipt reports 45 members, 614400 bytes and archive SHA256
   `3fd33489a8c0f7eebe0566307f8404421628339e84a111642b3536a80feefad0`.
   I verified the receipt and local member bindings described above, not a
   fresh full-archive extraction/rehash or present native process/device
   custody. The manuscript appropriately attributes these archive facts to
   the receipt; do not promote them into independent physical-custody proof.
4. No LaTeX/PDF build or layout/venue-readiness review was performed. Static
   checks found unchanged TeX environment sequences, unique old/new section
   labels, and no new unescaped underscores. All 15 new relative file links
   resolve, including the C98 anchors. Scoped `git diff --check` passes.
5. This acceptance covers only the exact six hashes above. Any changed claim,
   later outcome, modified receipt, or different artifact bytes falls outside
   it. Historical sections were checked for preservation and the named C97
   facts, not comprehensively re-reviewed or rescored.

## Read-only procedure record

Used Git status/log-baseline reads, `git diff`, `git show HEAD:<path>`, bounded
source/receipt reads, jq key/field inspection, and ephemeral stdlib Python
with `PYTHONDONTWRITEBYTECODE=1 python3 -B -` for SHA256, stored-record integrity,
diff preservation, existing aggregate-field checks and relative-link checks.
No project modules were imported or executed. No scientific tests, comparison
command, reducer, scorer, tokenizer, model, or native worker was run. No new
scientific receipt or comparison output was emitted. The only authored file
is `/tmp/astra_manuscript_seq162_independent_review_20260913.md`.

Final disposition: **ACCEPT, no blocking revisions; advisories retained.**
