# A4 collection: independent branch analysis

2026-09-14, inspected at approximately 08:31 UTC. Read-only node2 source:
`/tmp/astra_stage2a_d2_v2_collect_20260914_attempt1/run` (abbreviated **R**).
Only this note is written. Initial replay imported no native libraries; the
subsequent Main-requested tokenizer-only CPU check is recorded below. No model
load, GPU work, fitting, launches, threshold changes, corpus edits, or notebook changes.

## Finding

**A4 genuinely supplies two successful KEEP and two successful REVISE episodes,
30 selected action rows from 4/32 attempts.** Existing `load_collection` replay
passes over all 32 episodes and all 100 captured calls, reproducing the selected
rows exactly. This fixes A3's complete absence of successful KEEP demonstrations
at the collection level, not an established student-learning or birth result.
**The selected corpus perfectly confounds branch with rendering skin:** both
KEEP episodes are skin 0; both REVISE episodes are skin 1 and share world h13.
Thus “balanced branches” is true only for selected episode/check counts, not
cross-skin coverage, independent worlds, action rows, or token exposure.

## Terminal status and source

`R/RESULT.json` records `COLLECTION_COMPLETE_DRAFT_ONLY`, 32/32 completed,
100 physical calls, four whole-chain successes, 30 draft rows. Recorded collection
interval: **08:16:11–08:20:05 UTC** (234.756 seconds). Master:
`ASTRA-OUTCOME-COLLECT-TRAIN-20260914-A4`; split `TRAIN_ONLY_FRESH_MASTER`.
The frozen saved D2 learner records **zero new updates**, checkpoint state
`2ce34dced3b9c55335d4bdf195b870ecdef69a2bc94de641cb1ccbf151aee2bf`,
adapter `5e96317f732aed604691d93f98c02f21dbb0621501381d416f552fe7694bb394`.
Recorded base pre/post agree:
`a2367093892219a833eea1bc7b3e0e2069bcaecad335df357809679d272f4992`.
These are recorded receipts, not a new weight-load verification in this audit.

`../run.py` selects the retained source overlay
`/tmp/astra_stage2a_d2_v2_source_20260914_attempt1` (**S**).
Its `gpu/astra_stage2a_d2_collect_v2.py` changes the A3 wrapper's master to A4
and selects existing V2 teacher guidance; the success-only selector is unchanged.
V2 explicitly requires one check per unchecked STEP, INDEX after KEEP, no RECOVER
after KEEP, recovery after actual mismatch, and immediate STOP at GOAL.
Guidance is teacher-only; replay verifies its absence from student prefixes.
The recorded claim remains scaffolded data generation, not autonomous parenting.

## Actual selected trajectories and outcomes

All episode IDs have prefix `OUTCOME-TRAIN-A1-` even though the master is A4;
the legacy ID prefix does not identify the source version. Call indices below
are **zero-based inclusive** in `R/CALLS.jsonl` (file line = index + 1).
Episode and draft line numbers are one-based.

| World/member | EPISODES line | Calls | Draft lines | Actual selected action sequence |
|---|---:|---|---|---|
| h01-m1 | 4 | 15–22 | 1–8 | INDEX → RELATION → STEP → KEEP → INDEX → RELATION → STEP → STOP |
| h02-m1 | 6 | 31–38 | 9–16 | INDEX → RELATION → STEP → KEEP → INDEX → RELATION → STEP → STOP |
| h13-m0 | 27 | 82–88 | 17–23 | INDEX → RELATION → STEP → REVISE → recovery RELATION → STEP → STOP |
| h13-m1 | 28 | 89–95 | 24–30 | INDEX → RELATION → STEP → REVISE → recovery RELATION → STEP → STOP |

INDEX/RELATION abbreviate READ INDEX/READ RELATION; KEEP/REVISE abbreviate
THINK KEEP/THINK REVISE. These are model outputs, not substituted witness rows.
Direct captured public EVENT/WORLD evidence at each check:

| Check call | Exact raw check | Selected EVENT GOT | Actual WORLD CURRENT | Result |
|---:|---|---|---|---|
| 18 | `THINK KEEP M2AE_E2QOXYG4HMP5` | `M2AN_2BVRIFVFLTII` | `M2AN_2BVRIFVFLTII` | match |
| 34 | `THINK KEEP M2AE_NNNUJBVQ2R4T` | `M2AN_VHERO4IWRC43` | `M2AN_VHERO4IWRC43` | match |
| 85 | `THINK REVISE M2AE_XPUFCO5OI5P2` | `M2AN_N2ASRYXMTUN7` | `M2AN_J2ZYMQXSZ2IZ` | mismatch |
| 92 | `THINK REVISE M2AE_F6P5ACALQCG2` | `M2AN_F2KG7UIV64KP` | `M2AN_6ZXUAIWMLIZ6` | mismatch |

The REVISE continuations read exactly the respective EVENT RECOVER queries
`M2AQ_NHH6I5QTPCT5` (call 86) and `M2AQ_QRZBJWLG7CWD` (call 93).
The final WORLD before each STOP is its task GOAL, respectively
`M2AN_TFY6TBDRSRUY`, `M2AN_WIPC3N6NIWIS`, `M2AN_BVT5RWNYBG6J`,
`M2AN_MLDIKRMJAHE5`. All four replayed scores confirm correct first STEP,
exactly one correct first-outcome check including operand, full route, public
read evidence, strict typing, valid generation/execution, budgets, and immediate
STOP after the second STEP. Arrival is not being substituted for strict success.

Selected action totals: **READ INDEX 6; READ RELATION 8; STEP 8; THINK KEEP 2;
THINK REVISE 2; STOP 4 = 30**. KEEP trajectories contribute 16 rows, REVISE
14. There are three selected worlds, not four independent worlds; both KEEP
examples are member m1, while both REVISE examples are the two members of h13.

## Selection losses and coverage

The retained builder defines skin = world index // 8 and mismatch =
bool((world index // 4) % 2). Each branch/skin cell has eight attempted episodes:

| Skin / intended branch | Attempts | Actual arrivals | Strict selected |
|---|---:|---:|---:|
| 0 / KEEP (h00–h03) | 8 | 3 | 2 |
| 0 / REVISE (h04–h07) | 8 | 3 | 0 |
| 1 / KEEP (h08–h11) | 8 | 0 | 0 |
| 1 / REVISE (h12–h15) | 8 | 2 | 2 |
| Total | 32 | 8 | 4 |

There are 24 premature stops, including **22 immediate one-call STOPs**. Four
additional episodes reach GOAL but are correctly excluded by strict scoring:

- **h00-m1**, calls 1–9: wrong first check `THINK REVISE M2AE_6U7JYH6Y6WJT`
  at call 4; extra `THINK KEEP M2AE_PXI6D2WIX26P` at call 8 after the second
  STEP, rather than immediate STOP. Both check correctness and stop timing fail.
- **h04-m1**, calls 42–50: KEEP at call 45 then REVISE of the same event at
  call 47. First-outcome check correctness, including command/operand fields,
  fails despite eventual arrival.
- **h06-m0**, calls 53–61: analogous KEEP at call 56 then REVISE of the same
  event at call 58; first-outcome check correctness fails despite arrival.
- **h06-m1**, calls 62–69: correct first REVISE at call 65, but extra KEEP at
  call 68 after the second STEP; immediate-STOP criterion fails.

Across all raw calls there are **9 KEEP and 6 REVISE outputs**, versus **2/2 in
selected drafts**. Raw action occurrence is therefore not successful training
coverage. The selector excludes incomplete trajectories and permissive arrivals;
it neither repairs them nor mines their individually correct partial actions.
All run payloads use `PARTIAL_SOURCE_ONLY`; terminal collection status and
replayed strict scores, not that source-status label, establish completion.

## A3 comparison and corpus implications

Existing local capture
`gpu_artifacts_local/astra_outcome_sft_first_result_20260914_attempt1/CAPTURE.json`
was re-read: A3 had **6/32 successes, 42 rows, KEEP 0 / REVISE 6**, from
h04-m1, h05-m0, h05-m1, h06-m1, h07-m0, h07-m1. All were skin-0 recoveries.
A4 provides genuine normal continuation examples but lower observed yield
(4/32 versus 6/32), fewer rows, and fewer unique selected worlds (3 versus 4).
The frozen D2 state/adapter receipts agree across A3 and A4; **both teacher
guidance and source master/world identifiers change**, as do selected contexts,
skins and row composition. This is not a causal isolation of guidance or balance.

The first A3 outcome-SFT result documented in
`research_notes/analysis/2026-09-14_outcome_sft_first_result.md` associated
recovery-only training with inappropriate revision on matched outcomes; it also
showed separate canary command substitutions. A4 establishes available KEEP
demonstrations, not that training on them cures either failure or qualifies birth.

**Corpus implication:** preserve the strict selector and accurately label these
four trajectories as branch-covered, success-selected scaffolding. Their perfect
skin/branch association admits a rendering shortcut, and repeated members of
h13 limit independent recovery coverage. Merely concatenating A3 and A4 would
give **72 rows, 10 successes, KEEP 2 / REVISE 8**, not balanced checks; changing
sampling/selection would be a prospective Main decision. No corpus was merged
or selected here. Equal episode/check counts alone do not imply equal target-token
exposure or a matched-budget comparison. No downstream result is inferred.

## CPU replay and exact evidence hashes

Executed read-only through `bash gpu/ovx_ssh.sh`, using the retained overlay:

```bash
bash gpu/ovx_ssh.sh 'timeout --signal=TERM --kill-after=5 100 env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python3 -B -' <<'PY'
import sys, time, json
sys.path.insert(0, '/tmp/astra_stage2a_d2_v2_source_20260914_attempt1')
from gpu.astra_stage2a_outcome_distill import load_collection
started = time.monotonic()
rows, provenance = load_collection(
    '/tmp/astra_stage2a_d2_v2_collect_20260914_attempt1/run',
    source_label='INDEPENDENT_A4_READONLY_BRANCH_ANALYSIS_20260914')
print(json.dumps({'rows': len(rows), 'rows_sha256': provenance['rows_sha256'],
    'input_sha256': provenance['input_sha256'],
    'elapsed_seconds': time.monotonic() - started,
    'native_libraries_imported': [name for name in
        ('torch', 'transformers', 'tokenizers', 'peft') if name in sys.modules]}))
PY
```

**Passed in 12.948 seconds; 30 rows; native library imports: none.** The loader
reconstructs source worlds, replays all captured generations, checks guided/public
request correspondence and native raw-byte records, re-scores all episodes, and
requires exact equality of selected calls and draft rows. It does not perform new
generation or native token recounting. Canonical replayed-row SHA-256:
`59517b5f9c6922f97409084db45afda9e50ba0bac473285331327475ac58b3c5`.
This canonical JSON hash differs intentionally from the draft JSONL file hash.

| Remote raw file | SHA-256 |
|---|---|
| R/RESULT.json | `d963c497e99c5fb023101b22f1305df7e266ed5bfae99b98ad6fc624f1256f98` |
| R/REQUEST.json | `b03f99a841c74069bb098f4290cc016333ed42e4727db84db0d5857aec887b6e` |
| R/EPISODES.jsonl | `872a8591316650c23313aded6e8d1936e0f55281ad102c27d1b4c88d53daf18b` |
| R/CALLS.jsonl | `0dca3eee6d66d7f79eb94ee77fa4626a6d40eea29cb3f3fb203f25dbe75ff55f` |
| R/DRAFT_TRAINING_ROWS.jsonl | `6f73927c0e617143f295aca994a9cdf4c8dea217866b643b66ecd03c6a8ac3db` |

| Retained source / binding | SHA-256 |
|---|---|
| S/gpu/astra_stage2a_d2_collect_v2.py | `b6a1603a7d75011d8c44c6eb1f07f8e3bb56124b0327223691b3492526c5a01d` |
| S/gpu/astra_stage2a_d2_collect.py | `c1e04f1feea46db41adbd4273fe1d2d3542d3973ce5b16e2ffef5e4d5f3379d2` |
| S/gpu/astra_stage2a_outcome_collect_v2.py | `c0356b8f95418e1f5ebd471b04fcfb09de45bc8f2abd793491b27fd299973052` |
| S/gpu/astra_stage2a_outcome_collect.py | `d492234b39dfb4870bfaae389ddf80176923658d9959fcafb5347cba09c9a185` |
| S/gpu/astra_stage2a_outcome_distill.py | `fdb5016f27cb3e63603993741388ab5a5aa578b504f5f8c1df7baa6233e33a2a` |
| S/organism_v6/composition_birth_stage2a_held.py | `fbdf3e82b42108a1d8b420a19769e65db282705bd34b8d93a7e8634639afe0ad` |
| A4 guidance text | `046d265fdbdab1d35805b4cee9b44170998ce66a19dab1a0a9cced7aaffbd722` |
| A4 source allocation receipt | `0cf5931c546c5367a77c938c0c9c7af375ed216af45a288f9a339e4ed07639fd` |

A3 references are the prior A100 mirror
`/tmp/astra_stage2a_d2_collection_data_20260914_attempt1/RESULT.json`
(`283c07825b543fa1fc06f2db2bbe0f24e523bb6071bbba3323a28493fc75a5e5`)
and `EPISODES.jsonl`
(`eca0c1e7fa0f7c35960b6ed339d4a9e70bfabe283a83bbaacfcb918810d5e34d`),
as retained in the local capture, whose independently recomputed SHA-256 is
`066711af989d936e48032ae302ca4c3e3513ed53ebc1b162ce4b9a37955d1065`.
A3 guidance SHA-256:
`2de9f301098a5892f2f6d63c0f6183ce1e4d9e3c33f1f4a046d91b7634fd307d`.
No A3 remote re-collection or new inference was performed.

## Main-requested native tokenizer/mask follow-up

**PASS**, exit code **0**, no stderr/errors, **17.413 seconds** inside the native
Python process. Exact command wrapper (Python check supplied on standard input):

```bash
bash gpu/ovx_ssh.sh 'timeout --signal=TERM --kill-after=5 120 env CUDA_VISIBLE_DEVICES= PYTHONDONTWRITEBYTECODE=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 TOKENIZERS_PARALLELISM=false HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1 /localhome/local-rohing/v2/venv/bin/python -B -'
```

The check used S's existing `load_collection`, then the official local
`AutoTokenizer.from_pretrained(..., local_files_only=True, trust_remote_code=False,
use_fast=True, padding_side="right")` from the model directory in R/REQUEST.json.
It verified the pinned official receipt and tokenizer file size/hash, installed
`tokens.official_native_backend(raw)` in memory, preserved wrapper/special IDs,
and bound `apply_chat_template(return_dict=False)`, matching the numerical
runner's backend restoration without calling its artifact-writing wrapper.
The resulting backend hash equals the collection's retained reference.

`source.tokenize_rows(rows, tokenizer,
guidance=provenance["source_result"]["guidance"])` **passed all 30 rows**.
Additional assertions checked source-call correspondence; equal input/label/mask
lengths; fully masked prefixes and trailing newline; assistant-plus-EOT labels
equal their input slice and decode exactly to the original action plus EOT;
and all 256 existing `cyclic_batch` batches mask padding. The existing helper
also verifies full-template token equality, exclusion of teacher guidance and
assistant special tokens, and nontruncation. This did not reselect any rows.

- Native versions: torch **2.13.0+cu130**, transformers **5.5.3**, tokenizers
  **0.22.2**; intra/inter-op threads both 1. No PEFT/model load was needed.
- Sequence lengths **306–3754**, prefix lengths **292–3751**, context cap
  **16384**; **389 assistant/EOT target tokens** across the corpus.
- EOS **151645**, pad **151643**. CUDA remained uninitialized. No remote
  artifacts were written, no optimizer/model was instantiated, and no fit ran.
- Unchanged 256-update batch-four schedule gives **1024 row presentations**:
  KEEP-trajectory rows **548 / 7232 target tokens**, REVISE-trajectory rows
  **476 / 6052 target tokens**; total **13284 target-token presentations**.
  These are calculated schedule exposures, not actual executed training.
  Branch totals include all actions in each trajectory, not only THINK actions.
- Corpus target tokens by trajectory branch: KEEP **211** in 16 rows; REVISE
  **178** in 14 rows. Token exposure is not equal despite two checks per branch.

Exact returned status: `A4_NATIVE_TOKENIZE_ROWS_MASK_CHECK_PASSED`.
Canonical mask receipt hash (same fields as the runner's mask receipt, canonical
serialization rather than an on-disk file):
`544bca178acb674a15e0cfe0a72db5004a5db8953dfa4b46d1f9160cf6e0b74b`.
Replayed source-row hash remained
`59517b5f9c6922f97409084db45afda9e50ba0bac473285331327475ac58b3c5`.
Official receipt hash:
`e87abf9c83845a32bb5df3828901dde1929e86a57fa0278158d4101b7df9a019`;
official tokenizer.json hash:
`c0382117ea329cdf097041132f6d735924b697924d6f6fc3945713e96ce87539`;
restored backend hash:
`f884026e05f6dfffe68b72d580b588006d98b3bc0a128bb1ac425c76f7fc438c`.

No source/tokenization/masking blocker was observed for Main's proposed fresh
**A4-only corpus-successor** fit with the unchanged runner. This is not an
isolated branch-balance comparison or a downstream success prediction; EVAL
was not regenerated or evaluated during this check.
