# REVIEW PACK — Experience Models era, written for Rohin's deep-read

*(Refactored 2026-09-06 by Fable. Supersedes the v2/Semantic-World pack; that
content is preserved in git history at commit 786f2c46 and summarized in the
VERSIONING section. This is the one document to read to know where the
project stands.)*

---

## VERSIONING

| Version | What it was | Status |
|---|---|---|
| v1–v3 | AlchemyWorld / retrieval-vs-LoRA scaling attempts | closed; falsifier failed honestly; lessons absorbed |
| Semantic World v0.2 (v4–v5) | mechanistic diagnostic era: five-rule stack, recognition reads, dream ladder | closed as headline (D3 shortcut audit demoted it); survives as the mechanistic toolbox and Paper-1 fallback |
| **v6 (scout)** | 64-episode CompilerGym lives, sleep-v1, 2 arms × 3 seeds | **complete** — results below |
| **v6.1 (complete; exploratory)** | 1024-episode lives, sleep-v2 (pathways + anchors), sealed split, batched wake | all 3 sleep roots terminal; two narrow positive concentrated paths, one severe registered action-routing failure; not confirmatory |
| **one-parent/one-child headline (proposal closed; deliberation pending)** | one frozen target-blind parent teaches one child process-level thinking through tasks and thought-to-action correction; the parent then disappears; deployment crosses parenting with per-life Think--Dream--Sleep writes | next paper-grade build after exact deliberation approval and ratification |

## THE PROJECT IN ONE PARAGRAPH (current form)

Experience models: use parametric memory (an all-layer low-rank adapter) to
make a frozen, lab-schooled base model prospective and thought-intelligent.
One thinking loop (a self-conversation where acting is tool use), a surprise
ledger (every action preceded by a prediction; expectation-violations are
the error signal — "the error lives in experiences"), dreaming as learned
context reconciliation, and sleep as the write mechanism ("the model edits
its weights by thinking; sleep is the commit"). One frozen parent teaches one
child how to turn process-level thinking into action on target-blind practice
tasks, then disappears. At deployment, compare that parented child's
Think--Dream--Sleep per-life learner with an equally provisioned
frozen-parameter active-memory agent, while a matched parenting-by-write
$2\times2$ separates inherited competence from measured learning. There is
no classroom, cohort, peer exchange, teacher ensemble, or population mechanism
in the paper. Current manuscript: paper/iclr2027_experience_models/main.tex.
Claim-safe causal abstract proposal:
research_notes/abstract_experience_models_v3_one_parent_causal.md. The broader
lifetime-parametric positioning draft remains
research_notes/abstract_experience_models_v2_positioning.md.
Full idea ledger:
research_notes/IDEAS.md (the 09-04→09-06 entries are the meat).

## V6 SCOUT — WHAT ACTUALLY HAPPENED (all numbers cell-counted)

**Setup:** Qwen2.5-7B frozen; CompilerGym llvm (deterministic IR-instruction
reduction); 64 episodes/life; sleep every 8 (sleep-v1: verified exemplars +
contrast pairs + ≥2-episode principles + waking brief); probes on 8 programs
at ep 0/16/32/48/64; arms A (frozen) vs B (sleep-LoRA), 3 seeds each.

**Measured noise ruler:** nine completed base-model probe panels give mean
`0.493554` and sample SD `0.011344` per panel (observed range
`0.478156--0.515694`; approximately `0.016` SD for a difference of two
independent panels). These are unseeded descriptive repeats, not a substitute
for common-random confirmatory coupling.

**Result 1 — the flywheel machinery works end-to-end.** Lives run, sleep
compiles, adapters train and reload, briefs carry forward, everything
resumable. The organism's waking briefs are coherent and evidence-grounded.

**Result 2 — sleep-v1 does NOT beat the frozen loop.** Adapter-on lost 8/12
paired on/off checkpoints (mean paired diff ≈ −0.067 before noise
correction; several gaps within ~2σ). Temporal pattern: on lost 3/3 lives at
ep16 but won 2/3 at ep64 (+.020, +.027, −.080) — a recovery-with-data trend
in 2 of 3 lives, suggestive (~1.7σ) not significant.

**Result 3 — mechanism NOT established.** "Fewer, better actions" held in
only one life cleanly (fewer acts 6/8 checkpoints, better validity only
4/8, with explicit reversals). Codex's independent audit corrected an
over-claim here; the fixed-action-budget assay (Codex's) owns this question.

**Known defects of the scout (documented in ~/v6_out/CONTAMINATION_NOTE.md):**
probe set leaked into training via a URI-prefix bug (fixed: `_canon`); ep0
probes ran under a different harness version. The scout is infrastructure
validation + recipe characterization, not a held-out learning result.

## COMPLETED LEGACY EVIDENCE

1. **v6.1 long run — complete.** All three sleep-v2 roots reached episode
   1,024 with sixteen paired adapter-on/off checkpoints. Terminal ON-OFF is
   `+0.037078/+0.058894/-0.434834`; normalized post-first-write probe-window
   AUC difference is
   `+0.033005/+0.046554/-0.290745`. Roots 0/1 concentrate 98.8%/92.9% of
   terminal actions on one supplied six-pass routine; root 2 emits only one
   registered action; only 353/797 (`44.3%`) terminal action-label candidates
   would be accepted as `ACT` by the post-run on-disk parser source proxy.
   This is a heterogeneous three-path writer outcome, not a pooled learning
   win. The repaired analyzer validates every available eight-program ledger
   against its saved summary and receipts 492 analysis-input/lifecycle
   artifacts, while explicitly noting that valid-record-boundary truncation
   and exact runtime ancestry cannot be proved. Full evidence and limitations:
   `research_loop/advisory/20260907_fable_v61_terminal_three_root_report_v3.md`.
   Fresh local-package reaudit: **PASS**, with the 549 MB remote bytes still
   correctly labeled author-observed rather than independently verified:
   `research_loop/advisory/20260907_fable_v61_terminal_three_root_report_independent_reaudit_v3.md`.
2. **Noise band — complete:** nine unseeded base panels, mean `0.493554`,
   sample SD `0.011344`, range `0.478156--0.515694`.
3. **Exploratory controls — complete, audit-limited:** base, outcome-tail
   shuffle, r8, and true-r16 panels completed; r64 training completed but its
   probe failed the serving-rank limit. These are recipe diagnostics, not
   accepted causal controls (correction below).

**Control audit correction:** the completed two-panel means were base
`0.485`, r8 true-corpus `0.515`, original r16 true-corpus `0.409`, and r16
outcome-shuffled `0.526`. These do not prove a rank optimum or binding effect:
training/probes were unseeded and not common-random; the shuffle retained the
program and action text and permuted only outcome tails; and r64 produced no
probe because vLLM's frozen maximum rank was 32. Treat this as writer
sensitivity only. Exact hashes and limitations are in the independent audit.

**Independent mid-run audit (2026-09-06):** the sealed train/probe URI split
is now clean, but each “1,024-episode” life repeats only 67 unique programs
15--16 times. At episodes 64--256, 10/12 available adapter-on/off differences
were positive (mean `+0.021`, suggestive only; generation is unseeded). One
life then collapsed: B2 scored `0.000` at episode 576 with zero parsed ACTs,
while a diagnostic extraction of its Markdown-wrapped `### ACT:` /
`- **ACT:**` lines scored `0.529` in the unchanged gym. Its cumulative corpus
fraction containing off-dialect ACT markers grew from 0 at sleep 64 to 0.356
at sleep 576. This is consistent with a self-reinforcing writer/parser dialect
shift contributing to the routing failure; unseeded writer realization and
unbound runtime ancestry prevent causal localization. The post-hoc recovered
score is diagnostic, never a replacement result. Full hashes, tables, causal
limitations, and the prospective repair assay:
`research_loop/advisory/20260906_fable_v61_longrun_independent_audit_v1.md`.

A post-hoc fixed-action diagnostic makes the early signal more specific: at
caps of the first 1/2/4/8 actions per probe, mean ON-OFF was respectively
`+0.0178/+0.0240/+0.0223/+0.0210` (positive in 11/12, 12/12, 10/12, and
10/12 paired checkpoints). The adapter therefore appears to improve early
panel scores even when later executed actions beyond the cap are discarded;
those later actions alone cannot explain the positive differences. Generated
tokens, parsing probability, unseeded sampling, and other arm differences
remain uncontrolled. This stays exploratory until repeated prospectively.

Action-string analysis narrows that interpretation further: adapter-on more
often used one broadly useful four-pass opening
(`mem2reg+sroa+gvn+simplifycfg`) across all eight sealed programs, replacing
weaker two/three-pass openings on `dijkstra`, `stringsearch`, and `sha` by
roughly `+0.10/+0.10/+0.021`. That opening was supplied in the birth prompt,
so this is compatible with reuse of a taught action prior, not discovery or
yet program-specific thinking. The same action content later remained
gym-effective in a post-hoc
extraction while the registered interface did not execute it. Reproducer:
`research_loop/advisory/analyze_fable_v61_probe_actions.py`.

At terminal time the two surviving positive roots retain the same narrow
result: B0/B1 ON-OFF is `+0.037078/+0.058894`, and their first-action-cap
differences are `+0.063425/+0.067999`, but 306/319 combined on-adapter actions
follow each root's dominant six-pass routine. These paths are compatible with
stable selection/reinforcement of supplied procedures, but do not identify a
causal transport mechanism or an improving investigation policy. B2
simultaneously finishes `-0.434834` with a severe registered routing failure.
The repaired report supersedes the episode-960 partial snapshot without
deleting it:
`research_loop/advisory/20260907_fable_v61_terminal_three_root_report_v3.md`.

**Nursery status:** Fable's phase-0 run is curriculum self-distillation, not
parenting. Every lesson was clipped to its first 1,176 source characters; 55
of 56 allegedly native NOTE-admitted thoughts lacked a line-start native NOTE
marker. The current repaired trainer did retain 7,947 supervised tokens with
no truncation for its actual 24 rows. Treat results only as a formative writer
scout. Exact audit:
`research_loop/advisory/20260906_nursery_phase0_live_artifact_audit_v2.md`.
The completed unseeded behavior check was null/adverse (ACT 8/8 OFF vs 7/8
ON; scoped notes 0/8 in both; RECALL 3/8 OFF vs 1/8 ON), and its stated
mystery-box task had no box evaluator while retaining the compiler bootstrap.
It is probe-invalid for disposition learning and will not be scaled.

## CURRENT HUMAN GATE

- Submission-critical path, scientific go/no-go dates, fallback claim ladder,
  and AI-use posture are consolidated in
  `research_notes/ICLR_2027_SUBMISSION_CRITICAL_PATH_20260907.md` (planning
  only; outside the frozen v2 source packet).
- The non-shrunk project objective is mapped rung-by-rung in
  `research_notes/DREAM_LORA_THINK_FULL_EVIDENCE_STACK_20260907.md`: the
  parenting headline tests prospective learning, while connected parametric
  transport, rate--distortion compression, goal-conditioned traversal, and
  the action--knowledge--later-goal expansion relay remain separately
  falsifiable mechanism experiments.
- The physical-carrier intercept is now exact and independently passed at its
  deliberately narrow scope. The real rank-8 all-layer Qwen2.5-7B adapter has
  `20,185,088` elements, a `40,370,176`-byte hypothetical bf16 tensor floor,
  and an author-observed serialized fp32 file of `80,792,096` bytes. That file
  alone needs an expanded artifact larger than `161,584,192` bytes to cross
  `<0.50`; at `8x16k` tokens this implies `1,232.7896` bytes/token. This is a
  demanding numerator intercept, not an observed denominator, rate, or
  impossibility result. The absence of a qualifying generated-load receipt is
  nevertheless a fail-closed reason not to spend on the proposed 8x positive
  panel. Preserve physical LoRA compression as a later-scale objective; keep
  semantic-code compression and LoRA transport separate meanwhile. Passed
  partial receipt and final audit:
  `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_v4.md` and
  `research_loop/advisory/20260907_pcfl_physical_intercept_receipt_final_audit_v4.md`.
- Three fresh independent attacks and their cross-critiques are adjudicated
  in
  `research_loop/advisory/20260907_one_parent_fresh_attack_adjudication_v1.md`.
  The adopted ruling is: keep the writer/near-transfer canary, use the exact
  four-root deployment pilot as the cross-ontology learning bridge, and
  repair its spending rule to require directional `D + W_P + L_terminal`
  rather than `D` alone. Report writer yield by arm/cut; never adjust it away.
- The closest-work audit materially narrows novelty. TMEM already performs
  online QA-to-LoRA fast-weight updates, PEAM already consolidates embodied
  success/failure-correction trajectories, EVAF already uses surprise-gated
  LoRA after context unload, and Learning on the Job already learns scoped
  active-text rules from deployment feedback. The ICLR paper is therefore a
  causal developmental intervention paper unless the separate mechanism
  rungs run; it is not the first online parametric-memory paper. Current
  primary-source synthesis:
  `research_notes/related_work/20260906_experience_learning_neighbors.md`.

- The architecture scope is settled: one parent, one child, no classroom.
  Parenting teaches process-level thinking and forces practice that converts
  thought into action. It ends before deployment. The paper-facing comparison
  is the resulting parented Think--Dream--Sleep learner (`P1`) versus a regular
  strong frozen-parameter active-text agent (`R0`); `U0/U1/P0/P1` supply the
  causal parenting-by-deployment-write diagnostic. Independent roots are
  repeated trials of this fixed topology, never learners that teach, share
  state with, compete with, or observe one another.
- The optional post-confirmation one-child PCFL relay is now a **PASSING
  unbound information-efficient candidate**, not an authorized experiment.
  V4 keeps the entire same-root TEXT+LoRA mediator/control chain but replaces
  75 co-primary population decisions and a 32-root copula pilot with one exact
  fixed-`N=96` endpoint (`47/96` complete roots; conditional confirmation
  power `.9016` at the `.55` planning point). A disjoint eight-root DEV gate
  opens or closes confirmation but cannot modify it; no hidden confirmation
  TEXT threshold remains. TEXT-first short-circuiting and five byte-identical
  LoRA transaction classes reduce estimated confirmation builds by roughly
  87--89%. This relay remains separate from and cannot delay or rescue the
  parenting headline; adoption still needs its own bound deliberation,
  ratification, implementation review, and run authority. Candidate:
  `research_notes/60_one_child_pcfl_relay_v4_information_efficient_candidate.md`;
  independent PASS re-audit:
  `research_loop/advisory/20260907_one_child_pcfl_relay_v4_revised_candidate_reaudit_v1.md`.
- External five-role architecture deliberation remains blocked until Rohin
  gives the exact approval sentence for the repaired v3 packet, bound to
  workflow SHA
  `deb896c6a9aa96491c712d5d64f71a341e15d01fe4caf0aa82417c37053a7274`,
  source-binding-manifest SHA
  `18bcbe31550e4f31e90bdd445d20d017d43c17dd0a828ee34fca51b57262d186`,
  and initialized zero-attempt state SHA
  `1e69856fd3da8ba7f6b834b70c0aea0a1a0ab1687f5645765c09992b43c43a5c`.
  A fresh local recheck recomputed all 30 bound source paths with zero
  mismatches; the state remains `advocate_pending` with zero role attempts and
  implementation authorization false. Receipt:
  `research_loop/advisory/20260907_one_parent_v3_source_binding_recheck_v1.md`.
  V3 supersedes the unexecuted v2 packet only by requiring directional
  `D + W_P + L_terminal` in the four-root spending pilot and immutable
  writer-path receipts.
  That approval authorizes deliberation only, never implementation, model or
  tokenizer execution, benchmark generation, adapter operations, or GPU use.
- A fresh execution-gap audit gives the current implementation a **REVISE**:
  all 30 frozen sources match and 19/19 relevant model-free legacy tests pass,
  but no conforming headline runtime exists. The five dependency-ordered
  blockers are the root/RNG/reducer, native typed causal transaction, exact
  response-only rank-8 writer with transactional rollback, executable and
  certified `ACTIVE_TEXT_FIXED`, and isolated five-service CompilerGym runner.
  No four-root pilot is valid until all five plus their CPU gates pass. Audit:
  `research_loop/advisory/20260907_one_parent_child_v3_execution_gap_audit_v1.md`.
- A separate information/GPU-hour attack gives the September-16 schedule a
  **NO-GO on current evidence, conditional GO after measured systems gates**.
  The mandatory campaign is 38 full roots (2 DEV + 4 excluded pilot + 32
  confirmation), 201,058 full-root calls, 36,956,672 maximum output tokens,
  456 root fits, and 474 fits including writer canaries. The only plausible
  eight-A40 schedule uses one isolated root/A40 with dynamic per-request LoRA
  selection plus one shared reset TP2 32B parent; its makespan is
  `8*H_nursery + 6*H_deployment`. Current code and lease evidence do not prove
  that runtime. Exact gates and recalculation:
  `research_loop/advisory/20260907_one_parent_v3_information_per_gpu_hour_schedule_attack_v1.md`.

## THE LAWS THIS ERA ADDED (each bought with a failure)

- Cell-count every mechanism claim; name reversals; expect the cross-agent
  audit (Codex caught Fable's over-claim; reviewers caught Codex thrice).
- Normalize identifiers on both sides of any train/test split.
- The organism's first death was context overflow — consciousness must be
  managed; v6 manages it by arithmetic, v6.2 by taught dreaming, eventually
  learned.
- pkill/pgrep self-match and orphaned engine children: kill parents AND
  EngineCore, verify nvidia-smi zero before relaunch.
- A "monthly" quota may be a rolling window; verify semantics before
  forecasting (lease planning).
