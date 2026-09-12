# Selectivity next decision — September 12, 2026

## Decision: park unchanged negative/replay reruns

**No new GPU comparison selected.** The smallest existing contrasts—positive frames versus `F_r16k16_neg64`, and plain writing versus replay-mix—already ran. Repeating either unchanged is redundant, not a new response to the fifteen A1/A2 G9 failures. Existing controls address parts of the spill problem, but **none establishes selective carriage**. In particular, “negative examples were never tried” and “neutral replay already solved it” are both wrong.

This is a bounded advisory decision for this selectivity branch, **not a pause or new gate on main's authorized formation/parenting work**. A matched preservation-loss or lower-LR experiment remains an unanswered design question, not an existing successful control. This memo neither specifies nor launches a new treatment or W0 prompt variant.

Scope: targeted reads began **09:16:02 UTC**; primary captures completed by **09:20:24 UTC**, final source/hash checks by **09:22:12 UTC** (about six minutes). Accept SEQ-067's fifteen failed A1/A2 bank artifacts as given; no A1/A2 metric replay/reanalysis. No literature retrieval, repo edit, Git command, remote mutation, model call, GPU action or polling loop. Supplied AGENTS instructions and applicable directory instructions were checked. Prior `/tmp` evidence-map and writer-literature notes were read as pointers, not promoted to new literature findings.

## 1. Synthetic negative rehearsal already ran and failed

**Primary run, node2:** `/localhome/local-rohing/v6_out/memory_dose_D32` (call it `R` below). Primary reports and existing fit metadata were read through `bash gpu/ovx_ssh.sh`; no report was regenerated.

**Condition:** `F_r16k16_neg64`, across, sleep4, rank8, lambda1, training seed0, three banks. Actual metadata confirms frozen `Qwen/Qwen2.5-7B-Instruct`, three epochs, lr `1e-4`, recipe `memory_dose_v1 (mirrors train_adapter.py v1)`. At sleep4 each corpus has **1,792 negatives: 16 unexposed-car owners ×64 plus 12 exposed-owner bicycle controls ×64**. This is not 1,792 independent owners. The 1,024 car-negative rows in SEQ-043 are only one component; actual corpora also contain 768 bicycle negatives.

Exact report: `R/report/F_r16k16_neg64__across__r8__lam1.md`. The following are **already-written report values**, rounded by that report, not new estimates:

| Bank | Dose16 paired owners | I_d_frame [existing 95% interval] | Frame spill | Result |
|---|---:|---|---:|---|
| 0 | 16 | 1.447 [0.599, 2.238] | 0.339 | G9 fails spill |
| 1 | 16 | 1.334 [0.231, 2.607] | 0.429 | G9 fails spill |
| 2 | 16 | 3.186 [1.921, 4.718] | 0.438 | G9 fails spill |

The historical report additionally pools **48 dose16 owners**, reporting I_d_frame **1.989 [1.267, 2.713]**, spill **0.402**, and **G9 FAIL / G11 FAIL**. P(abstain) ON is **0.001 unexposed / 0.001 similar / 0.003 bicycle / 0.001 dose16**. Those pooled numbers are preserved as historical report outputs, not endorsed as independent-bank or optimizer-seed uncertainty. Each bank eval has 1,313 cues; each source bank has 64 owners. Frozen G9 remains lower interval bound >0 and spill <=0.03; G11 remains unexposed and bicycle abstention >=0.5 with dose16 abstention <=0.1.

**Earlier control:** `R/report/F_r16k16_neg4__across__r8__lam1.md`, **bank0 only** completed: 112 negatives, I_d_frame **1.970 [1.050, 2.953]**, n16, spill **0.473**, G9/G11 FAIL. Banks1/2 are not completed neg4 replicates in the inspected run. **Positive reference:** `R/report/F_r16k16__across__r8__lam1.md` already reports pooled n48, **2.836 [1.928, 3.794]**, spill **0.427**, G9 FAIL. Do not turn the 0.427-to-0.402 difference into a clean causal effect.

**Dose/operational caveat:** neg64 needed a **265,000-token cap versus 250,000 positive**, +6%. The original 250k overflow and the concurrent throughput-precheck race were preserved, then resumed—not silent scientific successes. Actual content was 263,872 tokens for bank0; its corpus has 264,986 total tokens. See `research_notes/2026-09-11_neg64_resume_receipt.md:7`. This is a registered high-negative-dose test, not exactly matched token exposure or literal positive/negative parity.

**SEQ/source:** SEQ-039 introduced the failure/negative direction (`research_loop/COORDINATION.md:1437`); dated 19:05 UTC implementation/test receipt at `:1428`; SEQ-041 documents neg4 and the neg64 escalation (`:1413`); **SEQ-043 records the completed three-bank failure (`:1393`)**. Source: `organism_v6/memory_dose.py:194` registers cells; `:1102` generates negatives; `:1892` inserts them; `:2649` uses ordinary token cross-entropy. `gpu/memory_dose_frames.sh:126` fixes three epochs/lr1e-4.

## 2. Child-written negatives also exist, but are not a clean b-minus-c ablation

Same `R`, `CF_r16_c` versus `CF_r16_b`, three banks, training seed0/rank8/three epochs/lr1e-4/250k. All c fit-DONE and eval artifacts exist; each c corpus records **256 negative rows**. Report: `R/report/CF_r16_c__across__r8__lam1.md`.

| c bank | Dose16 n | I_d_frame [existing 95% interval] | Spill | Interpretation |
|---|---:|---|---:|---|
| 0 | 16 | 4.349 [2.725, 5.982] | 0.336 | Retains owner signal; still spills |
| 1 | 16 | 0.138 [-0.082, 0.371] | 0.126 | Weak/uncertain owner signal |
| 2 | 16 | 0.031 [-0.180, 0.244] | 0.215 | Recall essentially lost |

Historical pooled n48: **1.506 [0.795, 2.381]**, spill **0.226**, G9/G11 FAIL. Abstention ON **0.166 unexposed / 0.078 dose16 / 0.094 similar / 0.100 bicycle**; not the required selective abstention. **SEQ-048 (`COORDINATION.md:1342`) explicitly says b/c positive generations were only 4–24% identical**. Reduced spill can accompany reduced acquisition; this does not isolate the negative treatment. Source: `memory_dose.py:221`, `:1895`; reports/metadata are primary, generation-overlap claim is the existing SEQ audit, not recomputed here.

Neither synthetic nor child negatives constitute **exposed-owner swapped-ID contrastive rehearsal**. Synthetic controls teach “not observed” to unexposed owners and a fixed bicycle subset. The similar-ID endpoint is an unseen look-alike, not a second exposed owner with a deliberately swapped relation. No executed pairwise wrong-owner loss or targeted OFF-KL preservation arm was recovered in the inspected memory-dose path.

## 3. Replay, LR and objective reductions: what actually exists

**Replay-mix primary run, node1:** `/localhome/local-rohing/v6_out/write_swarm/{none,para,mix,paramix}`. All four `adapter/DONE`, `adapter/train_meta.json` and `probe.json` files were read through `bash gpu/a40_ssh.sh`. Existing probe means (not recomputed):

| Arm | Corpus rows | Optimizer steps | Reported probe mean |
|---|---:|---:|---:|
| none | 131 | 393 | 0.46579047557136655 |
| para | 393 | 1179 | 0.4957834167731839 |
| mix | 157 | 471 | 0.49377604056858304 |
| paramix | 471 | 1413 | 0.48866754263812334 |

Each has **two panels of eight compiler programs**, not two independent source/optimizer seeds. Recipe `v2.1_chat_masked`, rank8, three epochs, **lr5e-5**; train metadata has no explicit seed. Source `organism_v6/write_swarm.py:25` supplies four hardcoded native-marker exemplars; `:77` appends `max(4,len(corpus)//5)` rows; `:86` trains. Thus mix is **hard-target format rehearsal**, not neutral replay sampled from the frozen base distribution, not old-owner retention, and not a memory-dose G9 test. It adds 26 rows here and changes optimizer exposure. No G9/wrong-owner score is in these probe receipts.

**SEQ:** no numbered SEQ for this early screen. Unnumbered September7 Fable summary at `COORDINATION.md:76`; September8 18:56 PDT Codex dose-confound audit at `:592`; `research_notes/EVIDENCE_TABLES.md:12` explicitly labels it offline/dose-confounded. Its existence at lr5e-5 is **not an isolated lower-LR comparison to the memory-dose lr1e-4 runs**.

**Other existing reductions, kept distinct:** SEQ-033 (`COORDINATION.md:1519`) reports A/B inference-strength lambda0.25/0.5/1 in `R/report/`; B's *question-cue* spill is 0.05/0.11/0.18, with only lambda0.5's I_d interval excluding zero (0.27 [0.06,0.55]) and no positive absolute dose16 probability gain there. This is test-time adapter scaling, not a lower-LR frame experiment. SEQ-039 (`:1447`) reports the 856-piece seed0 **A_v1_1ep / A_v3_3ep** objective×duration crossing: whole-text one epoch **0.4964/0.2731**, target-only three epochs **0.5192/0.2709** on the two panels; existing three/one-epoch comparators **0.5293/0.2731** and **0.4896/0.2557**. The run family is node1 `~/v6_out/pretest_write_ab/R2_B_seed0`, source `gpu/write_ab.sh:43`; exact cross-cell artifact locations were not recovered, so these remain notebook-level results, not newly verified primary outcomes or G9 evidence.

**Not “neutral replay already tested”:** memory-dose has unrelated colour-balanced and colourless filler (`memory_dose.py:671`, `:1900`), but no filler-present/absent matched locality contrast was recovered. Production cumulative old+new text replay (`sleep_compile.py:260`, evidence-map) is another operation again. The targeted **0.8 memory NLL +0.2 frozen-OFF KL** treatment is explicitly **prospective/docs-only**, `research_notes/analysis/2026-09-12_post_v10r2_writer_recipe_factorial.md:166`. Its cross-view/anchor factorial and lr3e-5 are not executed memory-dose controls; no implementation/test/fit receipt for that treatment was recovered. Do not convert a design note into a ready existing comparison.

## 4. Tests already run; limits of the evidence

- Dated negative implementation receipt reports **32/32 CPU tests passed** (`COORDINATION.md:1429`), including byte-identical legacy F corpora. Current test definitions cover negative rendering/owner eligibility and marginal preservation (`tests/test_memory_dose.py:1433`), registered cells/manifest (`:1533`), abstention token/candidate/G11 behavior (`:1576`), old-eval compatibility (`:1698`), and mock fits/report runbook acceptance (`:1779`). These were **read, not rerun**; the old 32-test receipt is not a fresh certification of every later edit or a dedicated neg64 test receipt.
- Primary neg64 bank0/1/2 evals each carry **tokenizer abstain_check.ok=true**; scientific fits have DONE, explicit seed/recipe and eval outputs. This rules out the specific missing “ not” token check, not every possible assay defect. The budget/resume receipt records parsed-corpus validation and preserved failures.
- Swarm primary DONE/meta/probe receipts establish completed fits/probes. A separate successful canary receipt and matched-dose selectivity test were **not recovered**; the source docstring's “probes + canary” is not proof of either. No new tests were executed in this task.
- Current local and node2 memory-dose source SHA256 is `ab98329c433cb085cd53e1c766db350f1bb0fe2efb9181e24a3678c0d31a76e3`; runbook `7b535f3098c455fa4e839ce6f250b1e889539731a8f16da2cb53562aaca777ab`. Local swarm source SHA256 `0bb67e0854697a65d58a121136d7cadbbb5d55a6c99313fde19ab18dbb0cb197`. These identify inspected bytes; historical mutable runs do **not** gain an execution-time source seal from current hashes. Historical training commit pins were not recovered.

## 5. Why this is separate from W0; cost of the parked repeat

W0 attempt2's **positive oracle failed** and its frozen replay failed on post-seal `launcher.out` (SEQ-063; terminal run `~/astra_diagnostics/astra_W0_v10r1_20260912_attempt2`). It is not a valid general negative result about writer capacity. SEQ-065 calibration improved formatting (61/64 valid, 45/64 correct) without qualifying the oracle; SEQ-066 single-row lookup had 58/64 valid, 32/64 correct. **No prompt search is reopened here.** The completed car controls instead ask whether ordinary SFT negatives preserve owner-conditioned colour association while suppressing out-of-scope colour changes at fixed scored prefixes. They need neither ACT generation nor the failed oracle to establish their narrow recorded spill failures; conversely they do not repair/qualify W0 or activate W1. The prospective OFF-KL factorial cannot be treated as already authorized/executed by either evidence set.

**Resource forecast, not a promise:** primary neg64 train walls were **1246.7/1291.9/1270.4 seconds**, evals **198.4/199.5/197.9 seconds**. Roughly **24–25 minutes per one-A40 fit+eval**, or **73.4 minutes (1.22 A40-hours)** for the three-bank treatment, before queue, launch/precheck, model-load and custody overhead not captured by those fields. A fresh matched two-arm three-bank comparison would roughly double that measured core work; it is **not selected**. Older resume projection was22.8min/fit at612.4tokens/s, a projection rather than a guarantee. Swarm receipts inspected here have no wall time; do not borrow its small step count as a runtime promise. **Selected work uses zero additional GPU-hours.**

Preserve frozen base/LoRA, source-joined targets, OFF/ON and existing owner/unexposed/similar/bicycle controls, thresholds and per-bank denominators. Any later main-selected distinct treatment needs its own ordinary CPU/token/mask/provenance checks, exact source/recipe and immutable new output root, owner-managed resource/lease checks and honest acquisition-versus-spill reporting. This memo adds no formal C11 gate, resource reservation, clean-lineage/H1/H2 claim, or permission to overwrite old runs.

## Read receipts

- `/tmp/astra_selectivity_prior_remote_20260912.json`: exact six existing report texts plus selected fit/corpus/eval metadata and hashes; wrapper argv/exit0 in adjacent `.receipt.json`. SHA256 `6e31db61b77c11afaf07cbacb383bdf01c96be388c923cfedfad78bd93fda41a`. The local console-summary helper later encountered a null legacy abstention field; the remote capture had already succeeded and been saved in full. No remote recapture/reanalysis was needed.
- `/tmp/astra_selectivity_swarm_remote_20260912.json`: exact four probe/train/DONE records and corpus identities/counts; wrapper argv/exit0 in adjacent `.receipt.json`. SHA256 `011ebc9faa5573c9c50fbeae38b631dea76f85a7b958de81fa47b92bc64df9ea`.
- neg64 report SHA256 `27a3cd143a49f60a6bbb10ec648f0767b0f15b4d7a85ed668eb557332c8861f1`; c report `0a9b4292cb1a57f16f08db70c64941835c6e4c0e317708b95a309a0c7682288f`. Full precision absent from those rounded Markdown tables is not invented.
- Prior A2 capsules, reports and archive `80a30ec8…` were not written or reanalyzed. No broad logs or literature are reproduced in this decision memo.
