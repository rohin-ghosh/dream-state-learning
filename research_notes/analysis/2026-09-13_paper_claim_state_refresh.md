# Paper claim-state refresh through the actual-child writer results

**Date:** 2026-09-13 UTC  
**Role:** fresh manuscript/claim-map auditor  
**Repository cut:** `051c5fa9`  
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
| Generic format canary | `36/36` under LR0, damaging HIGH, and LOW | Falsified as a sufficient retention gate | Say interface canaries miss semantic skill erasure; task-specific paired retention is mandatory |
| PCFL v2.2 two-SLEEP vertical | Prospective design repaired to truthful replay, LOW-first calibration, source-diverse batches, exact child EVENT/LINK custody, connected-value controls, and PCFL retention | No result; science direction passes, implementation readiness fails | Describe only as the next experiment. Do not write “ready/running/passed PCFL” until runtime closure and terminal evidence exist |
| Connected experiential knowledge | Requires AUTH-over-ATOMS plus critical LINK cut or registered redirection on both DEV roots | Unmeasured | No present abstract claim; `EVENT_COMPOSITION_ONLY` is explicitly insufficient |
| Goal traversal and action-driven expansion | PCFL service/native route, useful-probe choice, public frontier outcome, S2 OLD+NEW cuts | Unmeasured | Bracket exact endpoint counts only after terminal PCFL artifacts |
| Increasing-lifetime learning | PCFL-STREAM successor is a design; no independent lineage AUC exists | Unmeasured | Require positive absolute slope, entry-to-terminal gain, and DLT-minus-FROZEN AUC `>=.05` with one-sided 95% lower bound above zero |
| Strong active-memory superiority/plateau | `ACTIVE_LINKED_TEXT` and access curve are specified but not implemented or certified | Unmeasured | No superiority or saturation language; plateau requires the optional seven-cut equivalence test |
| Compression | Rank-8 LoRA is about 80.8 MB; no rate--distortion pass exists | Contradicted if interpreted physically; semantic sidecar prospective | Use *compiled* or *connected*, not *compressed*, unless the separate exact codec/utility gate passes |
| Parenting | Historical parenting is observational/null or contaminated; minimum receptivity assays are designs | Unsolved upstream factor | Parenting may motivate better child material, but it is not part of the PCFL causal result and is not solved pedagogy |

## Stale or overbroad manuscript/abstract claims

| Location | Problem | Required correction |
|---|---|---|
| `paper_prototype/main.tex:5,43--89` | Calls the evidence cut SEQ-153 and says lower-LR repair is pending | Advance the cut only after adding the terminal LOW result and its failed `1/3` screen; remove the repeated historical banners from submission text |
| `paper_prototype/main.tex:92--162` | The “abstract” concatenates six historical updates and is far beyond an abstract; several pending statements are now false | Replace wholesale with one bounded abstract, not another appended paragraph |
| `paper_prototype/main.tex:94` | The historical `+0.019` original-panel mean can read as a learning result before the disjoint failure is understood | If retained in the abstract, bind it immediately to the disjoint `-0.017`, common-random text comparison, supplied routine, and lack of a causal lifetime claim |
| `paper_prototype/main.tex:150--161` | Correctly reports HIGH actual-record carriage, but omits terminal LOW and still says its outcome is pending | Replace with the paired HIGH/LOW/LR0 acquisition and retention totals; state that LOW failed qualification |
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

## Candidate A: current-evidence fallback if PCFL DEV fails (187 words)

Language agents can write deployment records into low-rank parameters, but
acquisition can coexist with silent forgetting. We characterize this failure
in a frozen Qwen2.5-7B-Instruct agent whose per-life LoRA is trained from its
record. In nine historical 1,024-episode compiler-optimization lives, the
original eight-program panel showed mean gain `+0.019`, yet final adapters
averaged `-0.017` on a disjoint panel and four lives developed harmful
action-generation failures. We then isolate the writer using three
same-learner sets of scaffolded, child-authored records. At learning rate
`1e-4`, source-withdrawn generation recovered `20/30` records under exact cues
and `16/30` under paraphrases, versus `0/30` for zero-learning-rate controls,
but retained only `98/143` previously correct skill items. Repeating the fit at
`3e-5` recovered `18/30` records under both cue forms while retaining
`140/143`; nevertheless, only one of three seeds passed the frozen repair
screen, and a generic format canary was perfect even for damaging writes.
Thus an agent's own admitted records can enter a parametric carrier and cross
a request paraphrase, but training loss and interface checks do not certify
selective, retained memory. Connected traversal, repeated-sleep improvement,
strong-memory superiority, compression, and parenting remain open.

## Candidate B: prospectively fillable main abstract (196 words)

Can an acting language model turn its own action outcomes into connected
parametric knowledge that improves a life? We study a frozen
Qwen2.5-7B-Instruct agent with a per-life rank-8 LoRA. THINK interleaves
reasoning, typed actions, and public outcomes; DREAM manages active context;
SLEEP trains only on provenance-bound child continuations, with truthful
replay and transactional retention checks. Our PCFL benchmark separates the
causal chain: a child first acts and authors EVENT and LINK records; after
source removal, a candidate-free reader and the mounted actor must traverse
different links under different goals, select an informative experiment, and
after a second write solve a delayed task requiring both old and new evidence.
Matched atom-only, permuted-link, wrong-root, adapter-off, link-cut, frozen-
sleep, exact-graph, raw-RAG, and evolving linked-text controls localize each
step. Results: [WRITER: rate, EVENT/LINK carriage, false-row and retention
counts]; [PCFL: formation denominator, AUTH-minus-ATOMS, link-cut/redirection,
native route, and OLD+NEW counts on both DEV roots]; [LIFETIME: `N`, five-cut
absolute gain, DLT-minus-FROZEN paired AUC and one-sided 95% lower bound];
[MEMORY: certified linked-text access point, on-policy and fixed-history
DLT-minus-text AUC]; [COMPRESSION SIDECAR, if passed: exact reconstruction,
codec ratio, and utility margin; otherwise omit]. Parenting is evaluated
separately as upstream receptivity, not as solved pedagogy.

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
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_2_writer_repair.md`
- `research_notes/analysis/2026-09-13_pcfl_v22_execution_readiness_audit.md`
- `research_notes/analysis/2026-09-13_pcfl_dev_to_paper_grade_successor.md`
- `research_notes/analysis/2026-09-13_pcfl_stream16_successor_objective_redteam.md`
- `research_notes/analysis/2026-09-13_full_objective_evidence_and_pcfl_redteam.md`
