# Paper claim-state refresh through fixed coaching, alignment, and replay repair

**Date:** 2026-09-13 UTC  
**Role:** fresh manuscript/claim-map auditor  
**Repository cut:** `2a0c5a25`; terminal fixed-coaching, lesson-alignment,
contrastive, and own-source replay audits incorporated; compression disposition
remains amended against `66f14501`
**Scope:** paper claim audit and replacement abstract candidates only; no edit
to `paper_prototype/main.tex`, benchmark source, model, adapter, or GPU state

## Verdict

`paper_prototype/main.tex` is not presently a submission manuscript. Its
historical CompilerGym characterization remains useful and mostly careful, but
the text before and inside the abstract is an append-only sequence of evidence
cuts. It stops at SEQ-153/C89 and still calls the lower-learning-rate repair
pending. The terminal repair is now known. More importantly, the newest
actual-child assay changes the strongest defensible result:

- at LR `1e-4`, source-withdrawn child-record recall is `20/30` exact and
  `16/30` paraphrased versus `0/30` for LR0, but only `98/143` previously
  correct Level-1 items survive;
- changing only the candidate LR to `3e-5` yields `18/30` exact and `18/30`
  paraphrased recall while retaining `140/143` previously correct items; and
- the low-rate writer still fails its frozen all-seed repair screen (`1/3`
  seeds passes), has only `5/14` robust exact target types, and therefore is
  not a qualified SLEEP mechanism.

This is bounded parametric carriage of scaffolded, admitted child records plus
a measured stability--plasticity tradeoff. It is not connected memory, native
use, repeated SLEEP, lifetime improvement, parenting, or a strong-memory win.

The own-source replay repair makes that tradeoff causal at fixed update count.
Replaying 24 older supported child outputs preserved every `143/143` old item
the unchanged parents got right, versus `135/143` when the same update positions
repeated new memories. New-memory access moved oppositely: replay recovered
`21/30` exact and `19/30` paraphrased records, versus `27/30` and `23/30` under
extra memory. Replay passed the frozen noncompensatory screen on only `2/3`
roots. It is evidence that rehearsal can move the retention--acquisition
frontier, not an all-root writer repair or a generally safe SLEEP mechanism.

The terminal fixed-coaching DEV adds two narrower results. While the reminder
was present, it made both named `predicted`/`relation` fields correct in
`48/48` apply records versus `38/48` under active-neutral contact. After the
parent/contact was completely removed and only admitted child records were
written, however, P and N each formed `45/48` fresh records versus `27/48` for
their initial models: the parent-free write effect was positive, but the
P-minus-N contrast was exactly zero in every seed. Task-specific retention was
N `140/144`, P `138/144`, and initial `143/144`, despite perfect generic
canaries. This shows targeted in-context coaching and parent-free carriage of
record behavior, not persistence of a parenting-specific advantage.

The subsequent fixed-lesson alignment DEV does not strengthen that claim. All
24 ALIGNED/SWAPPED restatements were semantically faithful on bounded manual
review, but the frozen lexical RESTATE score accepted only `2/12` in each arm.
More importantly, required structured `PROCESS_USE`, `RECORD_FAITHFUL`, and
`FULL_MATERIAL` were each `0/48` for ALIGNED, SWAPPED, and NO_PARENT. This
localizes a gap between understanding advice in prose and converting it into
the exact task-state operation; it is not evidence of durable parenting and
contains no write or persistence test.

The terminal authored contrastive diagnostic is negative/mixed: CONTRASTIVE
scored `58/72` versus PLAIN `50/72`, but improved only wrapper D1, tied on D2,
and passed the registered screen in `0/3` seeds. Its fixed fixture admits a
polarity shortcut, and increasing seed-0 dose from four to 112 epochs changed
neither aggregate endpoint. It is evidence to change information structure,
not evidence for experiential SLEEP or a result to headline.

PCFL v2.2 is the correct prospective experiment, but its current authoritative
status is **PASS for scientific direction, REWORK for execution readiness**.
The named runtime, renderer/parser bindings, replay identities, batch solver,
and full request/resource receipt are absent. No PCFL result exists.

## Compact claim-state table

| Claim object | Authoritative evidence now | State | Safe paper treatment |
|---|---|---|---|
| Historical 1,024-episode CompilerGym lives | Nine ungated life means `+0.019` on the original eight-program panel; 4/9 harmful pairs; final disjoint-panel mean `-0.017`; common-random brief `+0.0041` vs adapter `-0.0146` | Supported only as a historical failure/diagnostic characterization | Retain as motivation or a compact negative-results section; never call it lifetime learning or baseline superiority |
| Controlled authored skills/material | Level-1 authored targets can reach `47--48/48`; mini-Sudoku useful-minus-corrupt first-action differences are `+2/+2/+5` | Supported, but externally authored and task-specific | Call post-training/component evidence, not child experience, parenting, or SLEEP |
| Native keyed acquisition at one L2 checkpoint | Greedy TRAIN `14/16` vs OFF `8/16`; READOUT `8/16` in both | Supported exact-cue acquisition with a wording/interface gap | Do not call pure access failure, general keyed memory, or downstream use |
| Actual child-record write, LR `1e-4` | Exact `20/30`, paraphrase `16/30`, LR0 `0/30`; robust target types `7/14` and `6/14`; retained `98/143`; canary `36/36` | Positive carriage, severe variable forgetting | This is the strongest present own-record result; always state scaffolded formation, warm-start authored skill, output collapse, and no native action use |
| Actual child-record repair, LR `3e-5` | Exact `18/30`, paraphrase `18/30`; retained `140/143`; low-rate repair screen passes 1/3 seeds | Favorable tradeoff, failed qualification | Say lower heat restored 42/45 items erased by HIGH while preserving partial recall; do not say safe writer or selected recipe |
| Own-source replay vs extra new-memory repetition | Fixed updates: REPLAY exact/paraphrase `21/30`/`19/30`, retained `143/143`; EXTRA_MEMORY `27/30`/`23/30`, retained `135/143`; replay frozen screen `2/3`; canaries `36/36` both | Direct stability--plasticity movement, failed all-root repair | Say replay protected previously correct task behavior at the cost of new-memory acquisition. Do not call it pure semantic replay, autonomous replay selection, or qualified SLEEP; token/FLOP exposure differs and seed-0 extra-memory repetition was imbalanced |
| Generic format canary | `36/36` under LR0, damaging HIGH, and LOW | Falsified as a sufficient retention gate | Say interface canaries miss semantic skill erasure; task-specific paired retention is mandatory |
| Fixed answer-free coaching and child-record write | In context, both targeted fields P `48/48` vs N `38/48`; whole records P `43/48` vs N `38/48`. Parent-free after writing, P=N=`45/48` vs initial `27/48`; task retention N `140/144`, P `138/144`, initial `143/144` | Transient targeted coaching positive; own-record write positive; parenting-specific persisted contrast null | State all three surfaces separately. Do not call the parent-free gain amortized coaching, adaptive parenting, or parent-to-weight mediation; neutral writing reached the same endpoint and the panel nearly saturated |
| Fixed-lesson alignment without writing | Manual audit: `24/24` lesson restatements semantically faithful; frozen lexical RESTATE only `2/12` ALIGNED and `2/12` SWAPPED. Structured process use, faithful records, and full material were `0/48` in all three arms | Lesson reception apparent; registered operational transfer failed and scorer under-sensitive | Treat as a thought-to-operation/interface diagnostic only. It tests neither SLEEP nor persistence, and post-hoc state-shape differences cannot rescue the failed vector |
| Authored full-dose contrastive bundle | CONTRASTIVE `58/72` vs PLAIN `50/72`, but D1 `34/36` vs `26/36`, D2 `24/36` tie; registered screen `0/3`; seed-0 four-to-112-epoch endpoint unchanged | Negative/mixed curriculum diagnostic with a polarity shortcut | Dose was not the missing ingredient on these bytes. Preserve grouping as a candidate ingredient only for a shortcut-resistant keyed task; no source-selection, parenting, or experiential-SLEEP claim |
| PCFL v2.2 two-SLEEP vertical | Prospective design repaired to truthful replay, LOW-first calibration, source-diverse batches, exact child EVENT/LINK custody, connected-value controls, and PCFL retention | No result; science direction passes, implementation readiness fails | Describe only as the next experiment. Do not write “ready/running/passed PCFL” until runtime closure and terminal evidence exist |
| Connected experiential knowledge | Requires AUTH-over-ATOMS plus critical LINK cut or registered redirection on both DEV roots | Unmeasured | No present abstract claim; `EVENT_COMPOSITION_ONLY` is explicitly insufficient |
| Goal traversal and action-driven expansion | PCFL service/native route, useful-probe choice, public frontier outcome, S2 OLD+NEW cuts | Unmeasured | Bracket exact endpoint counts only after terminal PCFL artifacts |
| Increasing-lifetime learning | PCFL-STREAM successor is a design; no independent lineage AUC exists | Unmeasured | Require positive absolute slope, entry-to-terminal gain, and DLT-minus-FROZEN AUC `>=.05` with one-sided 95% lower bound above zero |
| Strong active-memory superiority/plateau | `ACTIVE_LINKED_TEXT` and access curve are specified but not implemented or certified | Unmeasured | No superiority or saturation language; plateau requires the optional seven-cut equivalence test |
| Physical compression | Rank-8 LoRA is about 80.8 MB, larger than the complete proposed PCFL life | Contradicted at this scale | Always print the unfavorable byte accounting; never call the LoRA, life, or organism physically compressed |
| Conditional predictive semantic compression | A zero-new-fit assay is prospectively specified on the ordinary final DLT adapters: shorter predictive code on unseen structure-governed outcomes, matched independent-continuation null, adapter-removal contrast, and fresh actions | Unmeasured; downstream of positive PCFL and lifetime gates | If every prospective code/use gate passes, call it *parametric predictive reuse* or *conditional predictive semantic compression*. It is not physical compression or exact seen-row storage |
| Parenting | Fixed answer-free coaching changed its two named fields while present (`48/48` vs `38/48`), but P and N tied at `45/48` parent-free after writing. In a separate no-write alignment assay, lessons were semantically restated but exact process use was `0/48` in every arm | Prose-level receptivity shown; operational transfer and durable parenting-specific advantage not shown | Parenting may motivate better child material, but do not call either result parenting persistence, amortized teaching, adaptive parenting, or solved pedagogy |

## Stale or overbroad manuscript/abstract claims

| Location | Problem | Required correction |
|---|---|---|
| `paper_prototype/main.tex:5,43--89` | Calls the evidence cut SEQ-153 and says lower-LR repair is pending | Advance the cut only after adding the terminal LOW result and its failed `1/3` screen; remove the repeated historical banners from submission text |
| `paper_prototype/main.tex:92--162` | The “abstract” concatenates six historical updates and is far beyond an abstract; several pending statements are now false | Replace wholesale with one bounded abstract, not another appended paragraph |
| `paper_prototype/main.tex:94` | The historical `+0.019` original-panel mean can read as a learning result before the disjoint failure is understood | If retained in the abstract, bind it immediately to the disjoint `-0.017`, common-random text comparison, supplied routine, and lack of a causal lifetime claim |
| `paper_prototype/main.tex:150--161` | Correctly reports HIGH actual-record carriage, but omits terminal LOW and still says its outcome is pending | Replace with the paired HIGH/LOW/LR0 acquisition and retention totals; state that LOW failed qualification |
| Entire manuscript evidence cut | Omits the terminal fixed-coaching P/N experiment and full-dose contrastive diagnostic | Add fixed coaching only as transient targeted steering plus equal P/N parent-free written endpoint; relegate contrastive to a negative component diagnostic. Neither promotes a parenting or SLEEP claim |
| `paper_prototype/main.tex:192` | “That the adapter stores knowledge the agent can use” is denied without qualification | Narrow to “general/native task use.” Direct source-withdrawn exact and paraphrase generation now supports bounded storage/extractability, not spontaneous use |
| `paper_prototype/main.tex:200--208` | Describes only the historical CompilerGym THINK/DREAM/SLEEP implementation; readers can mistake it for the current proposed PCFL mechanism | Label the entire section historical/as-run. A future result paper needs a separate frozen PCFL system section; do not silently overwrite the historical recipe |
| `paper_prototype/main.tex:229` and component appendix | Evidence boundary ends before C89/LOW and scatters later evidence through appendix patches | Replace the chronological patchwork with one evidence table keyed by assay, unit, target origin, read surface, retention, and permitted claim |
| `paper_prototype/astra_sprint_abstract_20260912.md` | It is a chronological evidence notebook with mutually superseded “pending” blocks, not a candidate abstract | Preserve as provenance only; never copy it wholesale into submission text |
| `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md` | Ends at C89 and explicitly labels lower-LR repair pending | Add a future C90 entry from the terminal independent audit; do not edit older C89 custody or counts |
| `research_notes/abstract_experience_models_v4_decisive_program.md` fallback | Omits actual-child carriage/retention and centers older authored material, masking, and parenting diagnostics | Supersede its fallback with Candidate A below |
| `research_notes/abstract_experience_models_v4_decisive_program.md` full/result rule | Requires adaptive parenting, parented RUN/FROZEN, and a parenting-by-SLEEP interaction that the current PCFL-STREAM successor intentionally excludes | Split parenting into a separate upstream study; make the main result conditional on PCFL mechanism + lifetime + linked-text gates, not parenting |
| `research_notes/abstract_experience_models_v3_one_parent_causal.md` | Treats parenting as the headline and assumes a mature pedagogy core; its fixed/adaptive parent topology is no longer the main causal campaign | Keep archival. It cannot be filled from PCFL or PCFL-STREAM results |
| `abstract_experience_models_v1/v2` and the 2026-09-02 PCFL namespace map | Superseded/deferred documents contain aspirational learning, parenting, compression, and old-protocol claim language | Cite only as history. Their explicit deferred/superseded statuses do not authorize a current claim |
| `2026-09-13_pcfl_dev_to_paper_grade_successor.md` | Contains exact prospective thresholds and resource projections, not observations | Keep every number out of past tense. `ONE_EPOCH_SCALE`, linked-text certification, reusable structure, N resizing, and all AUCs remain conditional |
| Earlier supplied-schema compression sidecars | A fresh `SCHEMA_LORA` fit would test transport of an authored compact code, not whether ordinary experiential SLEEP learned reusable structure | Do not use as the main compression slot. First test existing final DLT states with the zero-fit predictive-reuse assay |

## Candidate A: current-evidence fallback if PCFL DEV fails

Language agents can convert deployment records into low-rank behavior, but
writing exposes a stability--plasticity tradeoff and coaching does not
automatically persist. We study frozen Qwen2.5-7B-Instruct agents with per-life
LoRAs. In a fixed-coaching assay, an answer-free process reminder made its
targeted fields correct in `48/48` records versus `38/48` under neutral
contact. After parent removal and training only on admitted child records,
however, coached and neutral descendants tied at `45/48`, versus `27/48`
before writing. In a separate three-root writer assay, replaying 24 older
supported child outputs preserved every `143/143` previously correct task
item, versus `135/143` when the same update positions repeated new memories.
New-memory access moved oppositely: replay recovered `21/30` exact and `19/30`
paraphrased records, versus `27/30` and `23/30` with extra repetition, and
passed the frozen per-root screen only twice. Generic canaries remained
perfect throughout. These results establish bounded parametric carriage,
transient process steering, and rehearsal-mediated retention, not a qualified
sleep writer or durable parenting-specific learning. Connected traversal,
repeated-sleep improvement, strong-memory superiority, and compression remain
open.

## Candidate B: prospectively fillable main abstract (189 words)

Can an acting language model turn its own action outcomes into connected
parametric knowledge that improves a life? We study frozen
Qwen2.5-7B-Instruct with a per-life rank-8 LoRA. THINK interleaves reasoning,
typed actions, and public outcomes; DREAM manages active context; SLEEP trains
provenance-bound child continuations with truthful replay and retention gates.
PCFL separates the chain: a child acts and authors EVENT and LINK records;
after source removal, a candidate-free reader and mounted actor must traverse
goal-dependent links, select an informative experiment, and after a second
write solve a delayed OLD+NEW task. Atom-only, permuted-link, wrong-root,
adapter-off, link-cut, frozen-sleep, exact-graph, and evolving-text controls
localize each step. Results: [WRITER: rate, EVENT/LINK carriage, false rows,
retention]; [PCFL: formation, AUTH-minus-ATOMS, link-cut/redirection, native
route, OLD+NEW on both DEV roots]; [LIFETIME: `N`, five-cut absolute gain,
DLT-minus-FROZEN paired AUC and one-sided 95% lower bound]; [MEMORY: certified
linked-text access and paired AUC]; [ZERO-FIT PREDICTIVE REUSE, if passed: structured
DLT-ON/OFF predictive-bit ratio and upper bound, independent-twin null, and
fresh-action gain with lower bound]. The last result is conditional predictive
semantic compression, never physical LoRA compression; report the 80.8 MB
adapter. Parenting remains a separate upstream receptivity question, not
solved pedagogy.

## Promotion rule

Candidate A is usable now, subject to ordinary manuscript/source checking.
Candidate B is a template, not a claim. Fill each bracket only from a terminal,
prospectively bound artifact. Omit a failed or unrun bracket rather than
softening its gate. A PCFL DEV pass permits only a two-development-root
mechanism sentence; independent PCFL-STREAM lineages are still required for
lifetime or strong-memory claims.

## Sources

- `paper_prototype/main.tex`
- `paper_prototype/astra_sprint_abstract_20260912.md`
- `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md`
- `research_notes/abstract_experience_models_v1.md`
- `research_notes/abstract_experience_models_v2_positioning.md`
- `research_notes/abstract_experience_models_v3_one_parent_causal.md`
- `research_notes/abstract_experience_models_v4_decisive_program.md`
- `research_notes/analysis/2026-09-13_actual_child_real_record_memory_pair_terminal_audit.md`
- `research_notes/analysis/2026-09-13_actual_child_lower_lr_memory_repair_terminal_audit.md`
- `research_notes/analysis/2026-09-13_astra_parented_record_terminal_audit.md`
- `research_notes/analysis/2026-09-13_parenting_alignment_terminal_audit.md`
- `research_notes/analysis/2026-09-13_astra_contrastive_full_dose_terminal_audit.md`
- `research_notes/analysis/2026-09-13_own_source_replay_repair_terminal_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
- `research_notes/analysis/2026-09-13_pcfl_v22_execution_readiness_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_minimal_parametric_reuse_compression_assay.md`
- `research_notes/analysis/2026-09-13_pcfl_stream16_successor_objective_redteam.md`
- `research_notes/analysis/2026-09-13_full_objective_evidence_and_pcfl_redteam.md`
