# FIRST SPRINT DRAFT — companion abstract

## Abstract

We ask whether developmental teaching produces durable, adapter-mediated
learning-process competence on task-disjoint situations after reload and
removal of teacher access and temporary teaching context (H1), and whether it
increases improvement from new, self-generated, externally grounded experience
on unseen verifiable tasks through continued consolidation (H2). Both remain
proposed questions. We study frozen Qwen2.5-7B-Instruct with learning confined
to LoRA adapters, separating acquisition, retention and downstream use.

In a bounded same-adapter two-sleep DEV test, the saved first-sleep learner
continues for 200 updates on original-memory replay and its own actor outputs
collected under explicit next-action coaching, with teacher text stripped.
Audited fresh-process readouts change own-memory arrivals from 3/4 to 4/4 and
READ uptake from 0/4 to 4/4. Disabling only the reader adapter gives 2/4 arrivals
with READs in all four episodes, so this intervention is now exercised.
Held external-text arrivals rise from 4/8 to 8/8; these are supplied records,
not newly learned parametric memories. Known recall remains 4/4 under each
wrapper, while unseen-address MISS remains 0/4.

Completed optimizer-seed controls reproduce replay-arm own/reader-OFF/held
arrivals of 4/4, 2/4 and 8/8 with READs throughout. With cue loss masked,
own and reader-OFF arrivals are 4/4, 3/4 and 4/4 across seeds, and held arrivals
are 4/8, all without READs. Thus consultation and held-text success differ,
but old-bank accuracy has no consistent cue advantage.

All continuations share one saved learner and fixed banks; optimizer seeds
are not independent learner replications. Earlier robustness, controller and
preservation failures remain. This supports a narrow coached-policy learning
result, not autonomous discovery, developmental H1/H2, qualified BIRTH or a
self-improving learning rate. Both seed0 adult collections yield four grounded
EVENTs in eight calls each with identical corpora; adult learning is not yet reported.

## Supporting evidence notes—not part of the abstract

**September 14, 2026 result update — research question unresolved.**
Audited SEQ224 and completed SEQ226 cue-loss controls are included below, followed by
the earlier SEQ215/218/219, A4 and cue results. The controls are SEQ226;
SEQ225 adds collection-only results, not adult-learning
outcomes. Earlier positive and negative results remain. Scoped
source gates closed PASS/SEPARATED and native DEV results exist: runtime
blockage is not the current status. Reportability is not qualification.
Historical engineering logs remain engineering-only; failed attempts are preserved.
The sprint TeX and companion abstract are updated; canonical
`paper_prototype/main.tex` was updated separately by Main.
No complete cross-draft review is claimed. The collaborator draft stays UNSENT;
H1/H2 and the program remain open.

### Audited SEQ224: same-adapter continuation, not an autonomous flywheel

This update supersedes the earlier result cutoff, not earlier failure scores.
The saved first-sleep actor, rather than BASE, supplies the later cue targets.
Under the same explicit guide it first selects only 4/8 external-text tasks
(eight rows), versus BASE's 5/8 (eleven rows); all four wrong-goal first reads
lack a second READ. Subsequent last-user-turn next-action feedback yields
8/8 selected successes and 20 actor rows, versus system feedback's 2/8 selected
and four rows (4/8 actual arrivals). The teacher explicitly computes the public
comparison and supplies the next action; following it is not unassisted discovery.
The 20 selected rows are actual saved-actor outputs, not substituted BASE outputs.
Teacher text is stripped from their training prefixes.

SEQ224 continues that exact S1 adapter for 200 batch-four updates using fresh
AdamW, not resumed optimizer state: 400 original-memory plus 400 own-cue
presentations, 24,480 supervised tokens. The 32 memory views represent four
old EVENTs; 20 cue rows contain 12 READ and eight ROUTE targets. The original
FINAL_LF_ONLY provenance and strict-collection failure remain unchanged.
Independent source-only replay reproduces all 32 S1/S2 routing episode objects,
all 24 recall/MISS outcomes and every captured model call: 28 S1+68 S2=96.
Readouts run in fresh processes with no teacher in the public prompts.

| Panel | S1 arrivals/correct | S1 episodes with READ | S2 arrivals/correct | S2 episodes with READ |
| --- | ---: | ---: | ---: | ---: |
| Own parametric /4 | 3 | 0 | 4 | 4 |
| Own reader-adapter OFF /4 | 3 | 0 | 2 | 4 |
| Held supplied text /8 | 4 | 0 | 8 | 8 |
| Known recall W0 /4 | 4 | direct probes | 4 | direct probes |
| Known recall W8 /4 | 4 | direct probes | 4 | direct probes |
| Unseen MISS /4 | 0 | direct probes | 0 | direct probes |

S2 takes two conditional second READs on the own bank and four across the two
held banks. Its own parametric reader makes six model calls; reader-OFF makes
eight, returning literal MISS every time, while the actor adapter remains on.
There are twelve external held lookups, not model calls. Thus episodes with
READ are not numbers of reader calls. The OFF intervention is exercised here,
unlike SEQ218, but includes failed memory content/abstention behavior and is not
an all-base actor comparison. The held replies are researcher-supplied external
EVENT text, not new parametric-memory acquisition. The reader and actor share
the updated adapter; unchanged 4/4 recall does not prove identical reader function.
Unseen failures are not merely newline errors: none even emits bare MISS.

### SEQ226 cue-loss controls: shared-S1 optimizer sensitivity

The completed counts are now independently reduced in the cue-loss control
analysis, including individual episode outcomes and READ traces (SEQ226).
No broader scientific qualification is assigned here. Reuse primary
CUE_REPLAY seed0; additional replay seeds1/2 and CUE_LOSS_OFF seeds0/1/2 all
start from the **same exact saved S1**, with the same banks, 52 rows, 200 updates,
batch indices, inputs/padding and 400 memory-replay presentations. CUE_LOSS_OFF
masks only the two final cue rows per batch and normalizes the remaining loss
by the original full target count, avoiding upweighting the memory labels.
Active cue-target supervision differs by design; this is not a fully unparented life.

| Arm / optimizer seed | Own arrivals /4 | Reader-OFF arrivals /4 | Held-text arrivals /8 | Episodes with READ: own / OFF / held |
| --- | ---: | ---: | ---: | --- |
| CUE_REPLAY 0 | 4 | 2 | 8 | 4/4 / 4/4 / 8/8 |
| CUE_REPLAY 1 | 4 | 2 | 8 | 4/4 / 4/4 / 8/8 |
| CUE_REPLAY 2 | 4 | 2 | 8 | 4/4 / 4/4 / 8/8 |
| CUE_LOSS_OFF 0 | 4 | 4 | 4 | 0/4 / 0/4 / 0/8 |
| CUE_LOSS_OFF 1 | 3 | 3 | 4 | 0/4 / 0/4 / 0/8 |
| CUE_LOSS_OFF 2 | 4 | 4 | 4 | 0/4 / 0/4 / 0/8 |

Every arm retains known recall 4/4 under each wrapper and unseen MISS 0/4.
Cue-loss-off reader-OFF is unexercised because those actors never READ; its
accuracy is not a separate retrieval effect. The controls distinguish the
READ policy and success on the held supplied-text panel, **not a consistent
old-bank accuracy advantage**: cue-loss-off seeds0/2 already reach 4/4 without
READs, and seed1 reaches 3/4. Do not pool these as three independent children,
three independent experiences, or independent fact-bank replications. These
are optimizer-seed sensitivities of one initialized learner on shared tasks.
Nor does narrow held-text success establish general conditional reasoning,
parametric acquisition of held facts, or an improving adult learning rate.

The first SEQ224 audit alone could not separate cue supervision from additional
memory replay/updates. The subsequent matched-input loss controls address that
specific contrast at this fixed bank/recipe, not all effects of prior parenting
or shared actor/reader changes. No cue-specific old-accuracy claim is licensed.
Substrate persistence, parenting behavior, later autonomous learning and
self-improving learning remain separate claim levels; no H1/H2 or BIRTH promotion.
### SEQ225: collection only; adult learning not yet reported

Both seed0 adult collections pass: CUE_REPLAY and CUE_LOSS_OFF each produce
four grounded EVENTs in eight calls, with 32 replay-compiled rows each.
No teacher participates, but generic external exposure and format scaffolding
remain. Both actors generate identical records/prompts and the same complete
corpus. This is collection fidelity, not an advantage in learning or autonomous
task discovery. Source `ea940ab1`; Builder's September 14 10:08 UTC SEQ225 entry
records unchanged base/adapter state, zero fits and no infrastructure failures
during collection. Collection SHA256:
`8f9c66609077f15af1469caed513513d2db731a2a10cce65298dfbc81b53924a`.
Main reports source `678faf15` running the declared 400-update training and
fresh BEFORE/AFTER phases. These are live work, not adult-learning results;
no new accuracy, retention or learning-rate outcome is incorporated.
Canonical main/README were updated separately through SEQ225, including controls;
no complete cross-draft review is claimed. The collaborator draft remains UNSENT.

- [Saved-actor cue analysis](../research_notes/analysis/2026-09-14_saved_actor_cue_first_result.md).
- [Last-turn/system feedback analysis](../research_notes/analysis/2026-09-14_lastturn_cue_feedback_result.md).
- [SEQ224 independent terminal replay](../research_notes/analysis/2026-09-14_cue_second_sleep_first_result.md).
- Primary campaign: `/tmp/astra_cue_sleep2_20260914_attempt1`, source
  `4f68de78a036906a679558f31dcd1d31e02b3ded`; local audit:
  `gpu_artifacts_local/astra_cue_second_sleep_first_result_20260914/`.
  S2 readout RESULT SHA256
  `99c5ef35ccb5b15117a7f6c1c1cf1afaf6f216556e35dce1589c3dfbd2c9c721`;
  final adapter-file SHA256
  `6ca6b6a300d5b19816eef1e50a03e78e6eb212f699a746d001332e1eae6f21ff`.
- Control campaign: `/tmp/astra_cue_sensitivity_20260914_attempt1`;
  recipe binding is the Builder's September 14 09:49/09:52 UTC ledger entry;
  completed counts are independently reduced in the
  [cue-loss control analysis](../research_notes/analysis/2026-09-14_cue_loss_control_results.md).
- [Builder SEQ225 collection record](../research_loop/COORDINATION.md), September 14 10:08 UTC.

Reported native replays and hashes belong to those records, not new execution
by this document editor. Older dated statements below describe their original
cutoffs; their scientific limits and negative evidence are retained.

### Own-EVENT persistence and self-issued access

SEQ215's separately named FINAL_LF_ONLY condition uses four actually experienced
EVENTs, 32 query views and 200 updates/800 presentations, followed by 24 BASE
and 24 fresh-process FITTED calls. Cold W0/W8 recall is 0/4→4/4, but
unknown-address MISS falls 4/4→0/4. All strict action panels remain 0/4 because
ROUTE outputs omit the required final LF. Post-hoc port-content annotations
are not repaired scores: native action stays 2/4, supplied-own-read rises
2/4→4/4 and exact-facts ceiling stays 3/4. Prompt labels/order differ, precluding
a clean mediation inference. Exposure, addresses and writing are externally
scheduled, not an autonomous multi-sleep loop. The original strict collection
remains 0/4 admitted with no fit; its successor does not rewrite those failures.

SEQ218 gives BASE 2/4, FITTED 3/4 and FITTED_READER_OFF 3/4 on four exposed
tasks, with four actor calls per arm and **zero READs in every arm**: 12/60
allowed calls, zero fits and no observed infrastructure/parse failure.
Reader-OFF is unexercised, not a successful ablation or evidence that retrieval
is ineffective. Do not pool correlated same-task arms as independent trials.
SEQ215's actual fresh-process result is distinct from the conductor's
same-process roundtrip; neither alone establishes autonomous action utility.

### A4-only and source-action copy mixture: both terminal, neither qualified

Each fresh seed0 rank8 fit completes 256 batch-four updates and 1,024
presentations. A4's 30 outcome rows originate in four selected successes/32
attempts; KEEP is skin0-only, REVISE skin1-only and from one recovery world.
Teacher strategy is absent from student prefixes. This is single-seed DEV,
not independent-world replication. Counts below are A4-only versus mixture.

| Criterion | A4-only | Copy mixture |
| --- | ---: | ---: |
| SEEK paired /4 | 4 | 4 |
| PROSPECT paired /4 | 3 | 2 |
| CHECK paired /4 | 4 | 4 |
| CONTINUE paired /4 | 0 | 0 |
| Strict chains /8 | 4 | 4 |
| Copy canaries /16 | 4 | 9 |
| Individual criteria passed /10 | 7 | 6 |

Both aggregate qualification booleans are false. Typed interventions are 32/32,
but semantic member correctness is 27/32 versus 26/32; useful reads and typed
steps are 8/8 in both, not eight successful routes. Each fit uses 56 BASE and
122 FITTED physical calls, each state reserving 280 slots, with zero recorded
accounting failures. All eight raw chain action sequences, public response bytes
and transitions match between fitted arms; strict successes are zero-based
indices 3,5,6,7. Five chains arrive and STOP, but chain2's two intervening checks
fail strict success. A4 differs from earlier A3's 4/8 by gaining normal chain5
and losing strict recovery chain2, not by increasing the total.

The mixture repairs four STOP-copy canaries and one STEP-copy canary, but every
at-GOAL CONTINUE member still emits READ INDEX instead of STOP. One additional
wrong-goal PROSPECT member lowers its pair score. Twelve added rows are
**authored copy prompts around actual training-action bytes**, not new experienced
trajectories. They replace outcome slots: 768 outcome+256 copy presentations
versus 1,024 outcome-only. Total supervised tokens are 13,431 versus 13,284;
outcome tokens are 10,054 versus 13,284. Ordering and per-row/family exposure
also change. This is a descriptive mixture effect, not isolated replay causality
or a forgetting-mechanism identification. Adapter-only backups/file hashes
are not full optimizer-resume checkpoints or fresh-process reload tests.

### Frozen BASE external-text cues, not saved-actor learning

SEQ219 uses frozen **BASE without an adapter**, not the saved first-sleep actor.
Eight grounded EVENTs require 8 EXPLORE+8 EVENT calls, followed by 11 cue calls:
27 model calls total. Only 2/8 cue attempts read, both succeed, yielding five
student rows (3 READ, 2 ROUTE). Six skip reading: three wrong outcomes and three
lucky arrivals, all excluded by the read-required selector. Actual arrivals are
5/8; selected coverage is 2/4 worlds, 1/2 banks and 0/4 complete goal pairs.

The explicit-first-READ continuation reuses the same eight EVENTs/tasks with
14 original file bindings verified, zero new EXPLORE/EVENT calls, 17 new cue
actor calls and zero fits. Read uptake rises 2/8→8/8, selected arrivals 2/8→5/8,
but actual arrivals remain 5/8. Nine external READs yield eleven selected rows
and 1/4 complete selected goal pairs. Of four first reads mismatching GOAL,
only one elicits the needed second read; three commit the wrong-goal EVENT's
DID. Both captured-response replays reproduce all reports and consume all
27 original/17 continuation calls, failures included; no recorded infrastructure,
nonterminal or truncation failures occur. These are reused training tasks,
not a new independent evaluation bank.

READ returns **copied, externally stored raw EVENT text, not parametric recall**.
All original EVENTs fail exactly-one-final-LF syntax but pass the launched
tolerant grounding check; their raw zero/double-LF strings remain unchanged.
Teacher coaching is present during collection and stripped from student prefixes.
Five/eleven selected rows are draft data, not a fitted cue policy; structural
mask checks are not native-tokenizer/mask admission. These BASE outputs cannot
silently become the saved memory actor's own later thinking. That earlier
cutoff is superseded by the separately sourced saved-actor collection and
SEQ224 continuation above; the BASE collection's provenance is unchanged.

### Claim boundaries and evidence scope

Substrate persistence, parenting behavior, later autonomous learning and
self-improving learning remain separate claim levels. Bounded writes/recall
and coached external-text consultation do not establish task-disjoint H1,
unseen-task continued-learning H2, qualified BIRTH, autonomous parenting or
a self-improving flywheel. Reused DEV banks, goal pairs and optimizer seeds
are not independent samples. Earlier findings and failures remain; the research
continues without mechanism freeze or mission-complete claims.

The terminal-artifact analyses below bind raw outputs, manifests and limitations.
Their reported replays/audits are not new native executions by this writer or
a full independent scientific review. No new literature references or sends
accompany this revision. No local TeX engine/BibTeX was available; PDF/layout
and length validation remain outstanding.

- [SEQ215 microloop analysis](../research_notes/analysis/2026-09-14_microloop_lf_first_result.md): `/tmp/astra_microloop_lf_20260914_attempt1`.
- [SEQ218 raw joins](../research_notes/analysis/2026-09-14_self_issued_read_route_first_result.md): `/tmp/astra_event_read_route_20260914_attempt1`.
- [SEQ219 first cue analysis](../research_notes/analysis/2026-09-14_cue_collection_first_result.md): `/tmp/astra_cue_collect_20260914_attempt1/run`.
- [A4-only terminal 09:02:52 UTC](../research_notes/analysis/2026-09-14_a4_outcome_sft_first_result.md): `/tmp/astra_outcome_a4_20260914_attempt1/run`. RESULT SHA256 `2c60e299832912db317e6f824a4aba9fdd33f8fc1f390c096ffb5c1336f14736`.
- [Copy mixture terminal 09:11:49 UTC](../research_notes/analysis/2026-09-14_a4_copy_replay_comparison.md): `/tmp/astra_outcome_a4_replay_20260914_attempt1/run`. RESULT SHA256 `e4140a4c54e6a12643e39ff00eeb89a4bc9e5901a94a2201d2a49d66a5c718a8`.
- [Explicit cue terminal 09:10:15 UTC](../research_notes/analysis/2026-09-14_explicit_cue_collection_first_result.md): `/tmp/astra_cue_explicit_20260914_attempt1/run`. RESULT SHA256 `8d79dbe0d70ffda6a93264b4a063583bb3354bd9aca3da6a4bcd37e2c6820f6c`.

**Historical through-SEQ195 result detail (preserved).**

**Historical SEQ188 / C104: no exact sequence acquisition; retention undefined.**
The eligible changed-recipe screen alters output without exact acquisition;
remaining fit phases are withheld. Prior scoped acquisition and reader STOP
remain unchanged. This closes the17:25 UTC evidence checkpoint, not the
broader campaign or a G3/P1/H1/H2, parenting, clean-lineage or freeze claim.

**Through SEQ185 / C103: terminal engineering-only reader branch.**
Scheduled action-family and syntax scaffolds enable bounded interface behavior,
not successful graph use; the supplied-procedure branch fails and stops.
The prior scoped EVENT-acquisition result remains positive, not a completed
learning/parenting loop or broad sprint result. Sequence-material and wrapper
work are CPU-only at17:00 UTC; no native sequence fits are claimed.

**Through SEQ179 / C101–C102: bounded acquisition and failed use interfaces.**
A separate one-bank cold-acquisition endpoint passes, while disclosed READ,
supplied-graph and required-THINK interface diagnostics fail. Acquisition is
exploratory component evidence, not downstream use or parenting; no full
qualification follows. Historical C99/C100 restrictions and failures remain.

**SEQ169–173 / C100: engineering-only formation diagnostics.**
Adaptive interface clarifications stopped without a completed formation bank
or any fit, update or readout; this is not learning evidence. Subsequent
EVENT-only/import and READ/THINK interfaces remain proposed/implementation-only
at this cut. C99's failed-finalization restriction remains unchanged.

**SEQ167 / C99 engineering-only log — excluded from scientific results.**
Attempt 2 ended as UNUSABLE EXECUTION --- ENGINEERING-ONLY CAPTURE
(FINALIZATION FAILED). C99 is an engineering-only appendix/log, excluded from
scientific results. Archived bytes support interface/lifecycle debugging, not
a usable C0 result or learning evidence; the original gate remains failed.
The engineering log retains recorded interval checks and fixed-sample
limitations, not assay qualification. Own-write remains implementation only,
not executed at this cut. No learning, parenting, H1/H2, clean-lineage,
general G3, mission or freeze promotion follows.

**Historical evidence through SEQ162 — C98.**
One instrumented seed0 OLD/NEW first-backward pair has matching recorded
initialized trainable tensors, encoded input/mask, settings, fresh optimizer,
environment and RNG snapshots at all six boundaries; both scalar losses are
1.907779335975647. Gradient data hashes differ for 256/392 trainable tensors,
with matching shape/dtype/device metadata. This is first observed nonidentity
in materialized gradients before any optimizer update, not proof that the
underlying difference originated in backward. There are zero optimizer steps,
adapter saves or readouts. Equal loss/RNG does not establish equal intermediate
computation or dropout masks; no cause, effect size or within-path repeatability
is established. SEQ161 baseline drift remains unresolved. No H1/H2, general G3,
parenting, clean-lineage, mission or freeze promotion; C11 deferred. Collaborator UNSENT.

**Historical evidence through SEQ161 — C97.**
Matched full-memory-schedule ADDITIVE versus fresh MEMORY_ONLY yields exact
14/14,7/8,8/8 versus10/14,8/8,3/8; paraphrase10/14,7/8,4/8 versus10/14,8/8,2/8;
held47/48,48/48,39/48 versus47/48,46/48,47/48, with12/12canaries in every cell.
Frozen screens pass2/3versus1/3, not an all-seed repair. ADDITIVEseed2 loses nine
LR0-correct held items and its paraphrase4/8 only ties the evaluator-only constant.
Fresh MEMORY_ONLY differs from historical EXTRA_MEMORY in all three native seeds,
including loss/final-tensor receipts despite matching initialized receipts and
memory occurrence order; cause unresolved, limiting causal attribution.
Original controllers succeed but collectors/holders fail from a scorer-binding
bug; a separate byte-bound collection-only repair preserves rc0/1/1 and records
recovery rc0, with zero new model calls/fits/updates and no scientific retry.
Seed1's launcher BrokenPipe remains separate. The completed6fit/1632update/480call
contrast matches memory exposure, not compute/RNG or realized gradients. Replay
reads already-trained authored observations, not new TRY experience or parenting.
C11 remains deferred; H1/H2 and the raw-chronological attribution gap remain open.
No freeze, general G3, clean-lineage or mission promotion. Collaborator UNSENT.

**Historical evidence through SEQ160 — C96.**
The fixed-lesson alignment assay fails its frozen gate: all nine cells have
process-use, faithful-record and full-material scores0/16. All144NOTE attempts
and137called record sources fail normalization, so these zeros are not evidence
of absent raw source processing or a general absence of parenting effects.
Lexical RESTATE also rejects plausible paraphrases; distinct own-event missing
fields/wrong relations remain errors, not a rescued endpoint. All16opportunities
per arm remain in the denominator, including seven uncalled records. There are
305calls, zero fits/updates/parent-model calls: no post-write parent-free test, learned
persistence, amortization or H1/H2 result. CPU-only additive parity is an
engineering prerequisite, not a scientific outcome or new experiment authority.
C11 remains deferred; prior evidence and the raw-chronological attribution gap
remain. No freeze, general G3 or clean-lineage promotion. Collaborator UNSENT.

**Historical evidence through SEQ159 — C95.**
Own-source REPLAY retains every LR0-correct held/canary item in all three
learners, with exact-cue source-faithful recall10/14,6/8,5/8 and paraphrase
10/14,6/8,3/8. EXTRA_MEMORY gives13/14,7/8,7/8 exact and10/14,6/8,7/8
paraphrase, but loses0/2/6old held items. Frozen screens pass2/3versus1/3,
not an all-seed repair: REPLAYseed1 misses exact floor7, and seed2paraphrase3/8
is below the evaluator-only best constant4/8. Equal updates do not match memory
exposure or tokens; historical controls remain noncontemporaneous. Replay uses
the same24supported authored TRAIN observations per original child, not72novel
facts. This completed comparison supersedes the SEQ158launch-only status without
rewriting that cut. The next alignment protocol is inference-only, zero-fit CPU
development, not a result. C11 remains deferred; the raw-chronological LoRA
attribution gap and H1/H2 hypotheses remain. No freeze, parenting, general G3,
clean-lineage or mission promotion. Collaborator UNSENT.

**Historical evidence through SEQ158 — C92–C94.**
Fixed author coaching (P) and neutral contact (N), each followed by own-record
writing, yield fresh held eligibility16/16,16/16,13/16 in both arms versus
ORIGINAL11/16,8/16,8/16. Incremental held coaching contrast is zero in each learner, not
proof of equivalence; own-writing gains do not establish a coaching benefit.
Admitted material P/N is16/14,16/11,11/13 out of16, with unequal realized
experiences and write doses. Old held P/N is47/47,47/47,44/46 out of48 versus
historical47/48/48; all12canaries remain correct. These retention tallies are
raw-linked; all360old-retention items now match exact frozen-scorer replay,
with zero score-object discrepancies and unchanged counts.
The fixed ACT comma scaffold remains; CONF is untouched, and no adaptive parent
is tested. Full-dose contrastive held gains over PLAIN are+2,+6,0, but all three
screens fail D2's9/12floor (8/12each); exposed panels, repeated situations,
shortcut and historical-control limits remain. A separate zero-fit capture
validates24/24raw records per parent from24selected/48supported/96TRAIN sources:
the same24sources and24raw targets across three parents, not72novel facts.
Own-source replay repair is separately predeclared; Main reports its later launch,
not outcomes. The completed evidence cut stays SEQ158. Without a same-child,
same-history raw-chronological LoRA control, own-writing gains do not establish
extraction/compiler utility. H1/H2 remain hypotheses; no freeze, parenting, general G3, clean-lineage,
working-loop or mission-completion promotion follows. Collaborator UNSENT.

**Historical evidence through SEQ155 — C90/C91.**
Post-memory fresh formation yields source-faithful WRITE8/16 in every seed
versus LR0 7/16,6/16,4/16, but all48example-absent wakes omit required commas
and produce no executions/records. Current facts remain in record prompts;
novelty relative to the admitted bank is not matched experience or retrieval proof.
The original HIGH write's3/11/31held-skill losses remain. Lower-LR3e-5 gives
exact10/14,4/8,4/8 and paraphrase10/14,5/8,3/8 with held47/48,46/48,47/48;
canaries remain12/12. Only seed0 meets the exploratory joint repair screen,
not the three-seed roster. HIGH/LR0 controls are historical/noncontemporaneous;
the HIGH constant-record comparison has not been evaluated for LOWER.
Fixed-coaching and contrastive full-dose work is CPU implementation only,
not launched or a result at this cut. No stable-substrate, freeze, parenting,
H1/H2, general G3 or working-loop promotion follows. Collaborator UNSENT.

**Historical evidence through SEQ153 — C88/C89.**
Native greedy exact-TRAIN is now14/16 versus OFF8/16; READOUT remains8/16
for both. HF forced15/16 remains a different measurement, and its independent
stored-receipt analysis is complete, not a new forward pass. Same-learner actual
record writes yield source-faithful exact-cue recall8/14,7/8,5/8 versus zero,
but held skill falls44/37/17 versus47/48/48:3/11/31 itemwise losses while the
same12canaries stay correct. The4/5/5 distinct raw targets encode3/5/5 source
contents (2/4/3 triples). Against an evaluator-only best constant record, exact
recall gains+2/+3/+1 and paraphrase+0/+1/+1; seed0 paraphrase is literally
constant. This excludes only a single fixed-response alternative on the saved
exact panels, not heuristic cue use, and does not prove causal key association.
This is narrow parametric carriage, not a stable
substrate, parenting, general G3, H1/H2, a working learning loop or mission
completion. The formerly pending post-memory and lower-LR outcomes are now
reported separately in C90/C91; they do not revise these HIGH endpoints. Historical
pending statements below retain their named earlier cuts. Collaborator UNSENT.

**Historical evidence through SEQ151 — C83–C87.**
Through SEQ151, all 24 authored Level1 cells are complete, with three canary
regressions in the second roster. Actual-record v2 executes actions and yields
source-faithful records under an external prompt scaffold with mandatory priors;
this is state-dependent experience formation, not a learned closed loop. Separate
high-LR seed0 recovery has zero observed treatment contrasts. HF high-seed2
forced TRAIN15/16 versus READOUT8/16 does not supply native greedy TRAIN accuracy.
Actual-memory writing/readback and native-greedy testing remain development only;
HF independent analysis is pending; archived A100 short-root OFF readiness passes.
Historical pending statements below describe their named cuts, not current status.

**Historical evidence through SEQ143 — C79–C82.**
Three learner seeds per skill show controlled authored Level1 acquisition:
prediction, goal completion, contradiction and update judgement each reach
48/48 held content and strict, from OFF content 22/32/17/8 respectively;
post-fit canaries are 12/12 throughout. This is positive component evidence,
not a matched trained parenting comparison or general reasoning qualification.
Contrastive practice has a small valid-field advantage over PLAIN but fails its
frozen screen. The original two completed low/high-LR seed pairs have zero observed treatment
contrasts; the low seed0 recovery is separate, not an imputed original success.
A100 warm-up failures are missing scientific endpoints, not zero scores.
**PENDING at this cut:** high-LR seed0 recovery, newer perception/reflection and
repetition/meta-reflection roster results, and actual-record formation/transfer.
No later outcome is incorporated, no H1/H2/clean-lineage/general G3/freeze or
mission-completion claim is made, and the collaborator draft remains **UNSENT**.
Historical exclusion statements below apply only to their named earlier cuts.

**Historical completed evidence: SEQ134–136 / C76–C78.** R1's read-only missing-readout
supplement is a post-abort diagnostic, not a repaired primary or third completed
primary root. The first native child-record loop closes 11 stages, 128 generation
calls, three fits and 100 updates; all five vLLM readout panels remain old 4/8,
new 4/8. The separate access probe shows distribution change and weak, fragile
train-form discrimination, not no learning or a purely access-only failure.
Fit2 full likelihood scores 12/16, including four tiny downstream tie-break
successes, versus strict first-token 8/16 with five ties; held-readout scores
remain 8/16 by both measures. HF forced candidates and vLLM greedy outputs are
distinct. This is child-record loop connectivity, not parenting, clean ancestry,
general G1 or a frozen mechanism. Later LR-comparison outcomes were excluded from this historical block;
the working-draft research question remains unresolved. Collaborator UNSENT.

**Historical completed-evidence cut: SEQ130–133 / C74–C75.** Q0 R0/R2 complete
128 updates per arm and fail the registered endpoint; R1 is a runtime-aborted,
missing paired endpoint, not zero accuracy or a third scientific failure.
Across three preselected reflection learner seeds, ordinary practice improves
parent-withdrawn strict A/B application from 7/12 to 9/12 per seed with valid
syntax throughout, unlike perception's format rescue. Correction training adds
0, 0, -1 versus ordinary after withdrawal: no observed advantage here. Exact
prose zeros are not semantic failures. These are authored birth-component
studies, not child-authored SLEEP, P1/H2 or a clean-lineage qualification;
formal C11 remains deferred. No L2 or supplemental-readout results are included.
Prior abstract text, tables and author intent are retained; collaborator UNSENT.

Sources and repair provenance: [C74–C75 claim map](../research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md). The abstract below adds completed findings without deleting its historical birth/formation account.

**Historical abstract-level evidence update: SEQ125–129 / C70–C73.** The closed
root1 Q0 assay now has a reportable first-update stop, not a completed binding
result. SEQ125's `NONREPORTABLE_RUNTIME_ABORT` remains immutable;
the repaired SEQ126 terminal is `EARLY_XOR_QUARTET_STOP_AUTH`, qualified by
`BOTH_MAP_FIRST_STEP_MISS`, `EARLY_UNARY_TOOL_STOP` and
`OPAQUE_TOOL_WRITE_FAILURE_THIS_RECIPE`. Three fresh fits each perform one
quartet update. Projection predicates pass2/4 in each arm; observed-change
predicates pass AUTH3/4, DERANGED1/4 and unary2/4, against the required4/4
of both. The zero-update audit has nonzero P/V directions in all32 quartets;
the stop is not a zero-gradient finding or proof that another dose, recipe or
architecture cannot learn. No fit completes128 updates and no ON acquisition,
held-form, complementarity, locality or copy readout is executed. Empty/zero
report placeholders are unmeasured outcomes, not zero final accuracy.

Main's separate native replay reproduces the terminal; the bounded metadata
review supports the limited interpretation but is not raw-tensor replay or
wholly project-independent replication. Three updates/12 training forwards and
OFF-only288 prefix readouts/296 generations do not complete the selective-writer
or H1/H2 causal chain. The full-pass prerequisite is unmet, so no Q0 confirmation
or endogenous one-SLEEP relay is promoted. Independent authored birth studies
remain separate. These findings extend
the throughSEQ124 record without changing the thesis, author intent, historical
abstracts/tables or earlier evidence. The collaborator draft remains **UNSENT**.
The canonical Q0 stop memo and its returned replay/review are bound in C70–C71.

SEQ127 adds one no-fit OFF contrast on12 authored DEV situations, not observation
learning. Strict public-record passes are **absent0/12 versus present10/12**.
All12 absent responses contain complete fenced JSON; all12 present responses
are bare JSON. The bounded raw analysis's secondary descriptive fence removal
finds supported content **11/12 absent versus10/12 present**, with11/12 paired
objects identical and one correct-to-incorrect prediction/relation change.
The primary gain is raw-format compliance for already-correct content, not ten
newly correct observations. No fence stripping changes the primary scorer and
no invalid-score rescue occurs. The procedural anchor replaces the model's
tokenizer-inserted generic helper system message; it is not no-system versus
system or an appended anchor. Fixed absent-then-present order and n=1 bound the
interpretation. With no fit, no adapter and LoRA disabled, this is not learned
perception, persistence, general perception, L2 or H1/H2 evidence. The separate
three-seed fitted comparison is now complete through SEQ129. This diagnostic
cannot replace that study's matched OFF engines,
which enable LoRA without requesting an adapter. C72 binds the canonical
`ASTRA_PERCEPTION_ANCHOR_OFF_2026-09-13.md`, collection report and bounded
`astra_perception_anchor_raw_analysis_20260913.md`; the historical abstract
below is unchanged.

SEQ128–129 closes216 responses across three learner seeds after matched ordinary
and anchor practice (12 TRAIN targets, four epochs,12 updates). Strict counts
out of the same12 DEV situations, in seed0/1/2 order, are OFF absent0/0/0 and
present10/10/10; ordinary absent11/11/11 and present9/9/10; anchor-trained
withdrawn10/9/9 and present8/8/8. OFF absent already scores11/12 in every seed
under the frozen descriptive whole-fence view; its eleven correct objects are
identical to ordinary-fit-absent objects. Thus fresh-reload gains are **FORMAT
transfer, not new semantic record content**. No fitted cell meets12/12 operational
fidelity and no training-anchor benefit appears (withdrawal increments -1,-2,-2
versus ordinary). Shared DEV situations and deterministic OFF repeats are not
independent observations; user prompts supply the schema/relation mapping and
input exposure differs despite matched targets. This does not establish parent
removal, retention, autonomous material quality, clean lineage or H1/H2. C73
binds the canonical `ASTRA_PERCEPTION_THREE_SEED_2026-09-13.md`, frozen report,
custody and archived independent review (`b1088d75…`): a separate post-collection
raw check, not blinded replication or native/model-tensor recertification.
Q0's first-update-stop interpretation remains unchanged; no live writer results
are included.

**Historical evidence extension: SEQ122–124 and prospective public identity
(C66–C69).** Both existing manuscript abstracts are preserved; the
242-word historical companion abstract below retains its throughSEQ121 summary, with
the later evidence added here and in the complete result sections.

SEQ122/123 each close32 fixed practice calls; adaptive grammar clarification
recovers parser validity16/16 per OFF/AUTH state, not learning. Public TRY/
quiz/record/revision counts per4 are initially OFF0/4/4/0,AUTH0/1/3/1 and then
OFF2/4/4/2,AUTH2/4/3/4. Both still ignore two supplied F forecasts. Faithful
record semantics remain OFF4/4,AUTH3/4; exact record0 is serialization, not zero
fidelity. One OFF whitespace-only change is not bitwise deterministic replay.

SEQ124 recovers AUTH6/6 invalid proposals through strict next-slot projection;
OFF has no invalid wakes. Valid quizzes6/8 versus8/8 are legal completions,
not answer accuracy; faithful records8/9 versus7/11 are on different
trajectories, not efficacy. All114 calls/276 capsule members are verified by
the recorded paired replay, not independently certified as a whole experiment.
No fit/write, no unprojected AUTH sibling, and no Q0 result. Main's pre-parent
global-call-ID prompt confound remains; forward v2 CPU repair is not a native
run or retrospective correction. The returned parent review finds specific
false answer-count/confirmed-forecast recaps and quiz-unit imprecision, not
blanket purity or universally invented executed actions. P guidance is
process-oriented but sometimes overbroad. No hidden rule/future-answer vector
is found; no P/A efficacy, general H1/H2/P1/G3/G5 or freeze follows.

Prospective binding matches all14 node3 files of public revision
`a09a35458c702b33eeacc393d103063234e8bc28` of `Qwen/Qwen2.5-7B-Instruct`,
not every node or clean ancestry. Historical origin receipts are unchanged;
source-authored birth remains NOT CLEAN. Claim-map C66–C69 bind the exact
memos/receipts/review. Collaborator **UNSENT**.

**Historical throughSEQ121 evidence window follows.**

**Latest bounded cut: SEQ119fit–121 / C63–C65.** Executed September12,2026
PDT / September13 UTC. Externally authored TRAINED birth is not the child's
learned experience or self-learning. Complete readout fails the full conjunction
in both trained maps; exploratory formation yields `PAIRED_SHORTAGE`, no writes.
SEQ120audit v2 reports `FINAL_BOUNDED_COMPARISON_COMPLETE`: all strict/joint
headlines, twins and registered counts match, with ten explained field-retention
differences on two dual-NEXT rows and zero unexplained. This is bounded raw-count
completion, not scientific/native approval. Ampere did not independently verify
native token decoding; official model origin and clean ancestry remain unresolved.
V1 artifacts are preserved.
No independent formation certification. Source NOT CLEAN, official base revision
unresolved, no H1/H2/P1/G3/G5/freeze. No protocol-probe results or launch status
included. Canonical `main.tex` abstract unchanged; collaborator **UNSENT**.

**Historical SEQ118 cut; birth implementation status superseded by C63–C65.**

**SEQ118 / C62 — terminal sequential-memory result; run September 12, 2026
UTC, despite September13-named artifacts.** Returned raw-review PASS covers640
calls with no discrepancies; the additive custody PASS verifies the newly supplied
external validation without changing science. R2 has M0/B1/B2 each16/16 on both
dev/exact surfaces. NEW_ONLY2 has M0 dev9/16,exact8/16; B1 4/16 on both; B2 16/16
on both. Both cycle1 arms had acquired B1 at16/16 on each surface before its
NEW_ONLY cycle2 loss. Arithmetic habit/correct ACT remain32/32 at every state.
One seed, two authored-bank cycles, practical fixed-budget allocation: equal
updates/tokens/padding do NOT match current-new dose (R20 versus NEW_ONLY40
presentations/fact), nor make cycle2 a common-parent comparison. No general G3,
parenting, H1/H2, latent-erasure or mechanism-freeze claim.

Launch23:35:40.672863 to observed vacancy23:57:48.133511 on September12 UTC is
1327.460648s (22.124344 A40-min), NOT time through complete packaging/validation.
Worker/controller clocks nest; the external receipt has no collection-completion
timestamp. At the supplied planning cut process FIT-seed0/1 replications are
prepared but **UNLAUNCHED**. Rohin message23's birth-first priority is adopted;
PROSPECT/repaired REVISE plus truthful locality corpus/runner work is implemented/
in progress in that snapshot only. No birth GPU result or live birth status is
inferred. Origin `UNRESOLVED_LOCAL_HASHES_ONLY`, C11 deferred. Collaborator **UNSENT**.

Sources: `research_notes/astra_memos/ASTRA_SEQUENTIAL_MEMORY_2026-09-13.md`,
returned raw review and custody addendum; C62 in the claim map binds exact copies.
Main's updated memo now records the returned PASS, superseding its earlier
pending-review wording. Canonical
abstract, author intent and prior tables remain unchanged; no new thesis framing.

**Historical September 12, 2026 — terminal SEQ116–117 / C60–C61.** Both new FOUR
memory branches pass the fixed thresholds; with inherited SEQ113 seed0, all
three FOUR seeds qualify. SINGLE outcomes are heterogeneous: seed0 ties,
seed1 slightly favors SINGLE, seed2 SINGLE loses numeric correctness despite
valid PREDICT-before-ACT formatting on all32 responses. The five memory surfaces
query the SAME16 authored facts, not80 independent facts or general FOUR superiority.

Process-v2 readout is complete: quiz P12/OFF7/A6 out of24, but the full criterion
**FAILS** because P ties A on12 valid and9 correct pre-TRY predictions. P's all-F
predictions attain9/12 exactly as an all-F baseline on its observed path; conditional
accuracy is0.75 in every cell. P's12/24 quiz score also equals a constant-label
baseline on balanced panels, not evidence its actual answers are constant.
Faithful records P5/OFF9/A10 out of12 run opposite to quiz scores. One paired
fit seed/four shared development tasks, unequal target exposure, no general
conditional-prediction improvement, internalization or parenting efficacy.
Returned raw reviews PASS with non-blinding/implementation-author limits.
No G3/P1/G5/H1/H2, adult-learning or mechanism-freeze qualification; origin
`UNRESOLVED_LOCAL_HASHES_ONLY`, C11 deferred. At that historical cut sequential
execution was not launched; C62 now reports its result. Prepared process-seed
replications remain UNLAUNCHED at the newer supplied planning cut.
Collaborator **UNSENT**.

Sources: `research_notes/astra_memos/ASTRA_INTERLEAVED_REPLICATIONS_2026-09-12.md`
and `research_notes/astra_memos/ASTRA_PROCESS_READOUT_V2_2026-09-12.md`;
C60/C61 in the claim map bind both raw reviews and capsules. Canonical abstract,
author intent and prior tables remain unchanged; the earlier C56 record-objective
readout is not relabeled as this new process-objective result.

**Historical September 12, 2026 — SEQ114–115 / C58–C59: acquisition diagnostic and
finite process writes, not utility.** FULL own-record truth likelihood improves
2/2 for both earlier record-trained adapters, but strict joint likelihood/margin
gains are P1/2 and A0/2; both required two-record criteria fail. Mapping removal
gives P1/2,A2/2 likelihood gains and joint0/2 each. This is NOT no parameter
learning. Independent acquisition audit PASS is technical/numerical, not the
failed scientific criterion; its authorship/non-blinding limits remain.

Separate process-v2 fits complete12 finite updates each on two own raw wakes,
fresh base/seed2/rank8, not the record-write adapters. Exploratory amendment
`96a71289` accepts the native TRY alias without repairing wrong predictions,
replacing slots or rewriting V1's shortage. Removing temporary teacher
restatement from conditioning while retaining teacher-influenced raw targets
is context distillation, not unchanged native context or scaffold-free cognition.
Input/target presentations P9120/384 versus A9096/372 are unequal despite equal
updates/padded inputs. Native collector attests392 finite tensors per arm; no
local weight rescan or behavioral utility follows. Main's offline synthesis
rerun PASS covers68 members and forward/mask/source joins; author-side, not an
independent behavioral audit. The process readout was LIVE and memory-replication
outcomes were excluded pending audit at that C59 cut; C60/C61 now supersede
those statuses, not the earlier write-only or failed-acquisition interpretation. No general G3/P1/G5/H1/H2, clean
lineage or freeze; origin `UNRESOLVED_LOCAL_HASHES_ONLY`, C11 deferred.
Collaborator **UNSENT**.

Sources: `research_notes/astra_memos/ASTRA_RECORD_ACQUISITION_2026-09-12.md`
and `research_notes/astra_memos/ASTRA_PROCESS_WRITE_V2_2026-09-12.md`;
claim-map C58/C59 bind the archived acquisition review and supplied process-write
synthesis/capsule. Canonical abstract/intent and prior tables are unchanged.

**Historical September 12, 2026 — terminal SEQ113 / C57.** Both interleaved root0
arms score dev memory16/16, exact16/16, habit32/32, correct ACT32/32 and
lexical48/48 (three panels of the SAME16 facts). All112 aligned raw texts and
output-token sequences match: no FOUR advantage. No new OFF; original-parent
memory4/16 is an inherited provenance-bound count. Both original80-step-parent
forks add320 updates (400 cumulative), batch4 with two memories/two additions;
10,000 target presentations include1,280 memory (12.8%). Unequal input exposure
66,160/67,120, equal padded76,960; changed within-batch loss composition prevents
a pure temporal-effect inference against grouped replay. Returned raw-review
PASS is not blinded/fresh-author. Full-release reservation23.265 A40-min is
nested with controller/worker clocks, no overrun or signals. Seed1/2 replications
are proposed, not run in this cut. Teacher-authored material is not operational
parenting, general G3/P1/G5/H1/H2 or a mechanism freeze; origin remains
`UNRESOLVED_LOCAL_HASHES_ONLY`, C11 deferred. Acquisition/process-write outcomes were excluded at that
historical cut; C58/C59 now add only acquisition and finite-write evidence. Collaborator **UNSENT**.

**Measured prior-cycle costs (SEQ110–112; C54–C56, not a new utility claim).**
Formation, paired writes and readout sum to **20.933 A40-min full reservation**,
versus **12.729 supervised-worker minutes**. Full reservation includes CPU gaps,
cleanup and release-observation wait, not device-active or monetary cost;
interphase calendar gaps are not automatically charged. Generation is nested
inside workers/controllers/reservation; collection overlaps reservation. Do not
add clock columns. Combined generations use150 calls,55,321 input/3,324 output
tokens; the two writes separately repeat15,288 input/1,776 target presentations
across24 updates. This is one executed formation/write/readout path, not a
measured adult sequential-learning cycle. Cost forecasts and pending work are
excluded. Source: `research_notes/astra_memos/receipts_20260912/astra_actual_record_cycle_costs_20260912.md`
and sibling `.json`; cost synthesis is not a fresh-author audit.

**Historical September 12, 2026 — terminal SEQ111–112 (C55–C56).** The earlier
C54 RUNNING/NOT RUN status is historical: two fresh actual-record adapters are
now verified and parent-free OFF/P_ON/A_ON readout is complete. OFF quiz7/24,
P/A6/24; P minus A0, each adapter minus OFF−1/24. Valid quizzes4/4 versus3/4;
faithful records9/12 versus10/12 allotted (P/A10/11 emitted). Both adapter
rule5 tasks are protocol-invalid, not six observed wrong quiz labels. One
pair/four shared rules, no adult/readout-time parameter updates or robust
parenting effect. Herschel's returned raw-recount PASS has been read, superseding
the memo's pending status; authorship and non-blinding limits remain explicit.
Equal scores alone do not imply raw identity; any identity statement below
comes from a separate raw comparison. No general G3/P1/G5/H1/H2, clean lineage
or freeze; origin `UNRESOLVED_LOCAL_HASHES_ONLY`, C11 deferred. The separate
interleaved pair was LIVE at that cut; C57 now supplies its terminal diagnostic,
not a rescue of this null parenting contrast.
Collaborator **UNSENT**.

**Historical September 12, 2026 — SEQ108–110 cut (C52–C54).** SEQ108
carries assigned conditional maps perfectly but fails locality; a public-ID
shortcut leaves REVISE's intended EXPECTED comparison unqualified. SEQ109
FOUR_VIEW/SINGLE_VIEW both score memory4/16 on dev and exact panels of the
SAME16 facts; habit/ACT are32/32 versus0/32. Its memory gate fails, no seeds1/2.
Four source views/copies in one batch give10 source-specific updates over10
epochs,40 presentations, not40 sequential updates. Darwin's returned, now-archived
raw recount PASS supersedes the21:21 pending status, not failed progression.
SEQ110 formation yields P6/6 and A5/6 faithful records; Main accepts the actual
fixed first-two records and four parent contracts for material fidelity only.
At that earlier formation cut, writes were **RUNNING** and readout **NOT RUN**.
Terminal C55/C56 now supersede that status; formation evidence is unchanged.
No parenting utility, general G3/P1/G5/H1/H2, clean lineage or mechanism freeze.
Origin `UNRESOLVED_LOCAL_HASHES_ONLY`; C11 deferred; collaborator **UNSENT**.

**Historical September 12, 2026 — terminal SEQ107 (C51): technical recount PASS,
scientific progression FAIL.** Both root0 arms start the SAME ORIGINAL teaching
checkpoint and receive 160 new updates each. MIXED scores dev14/16 and
exact-prefix13/16 with habit and correct ACT32/32; ALL_MEMORY scores16/16 on
both panels but has habit/ACT0/32 and no valid arithmetic ACT. The panels query
the SAME16 authored facts, not independent or novel facts. MIXED misses the
registered >=15/16 requirement on BOTH panels, so no seeds1/2 under this protocol.
Equal updates do not match memory exposure or token compute. This is a local
allocation tradeoff, not isolated replay benefit or latent arithmetic erasure.
The archived reviewer independently recounted128 new calls but authored the
runner/collector: raw-reduction PASS, not fresh-author implementation review.
That earlier cut excluded conditional/varied outcomes; C52/C53 now supersede
only that pending status. No
G3/P1/G5/H1/H2, parenting, child sleep, clean lineage or freeze; origin remains
`UNRESOLVED_LOCAL_HASHES_ONLY`, formal C11 deferred, collaborator **UNSENT**.

**Historical September 12, 2026 — terminal SEQ104–106 (C48–C50).** SEQ104 adds
initial-teaching roots 1/2 to inherited seed0 phase1: both positive rates replace
the old habit with exact correct ACT-only 32/32 by 16 opposing updates. All
continuation optimizer seeds are 0; only seed0 has four-phase evidence.
SEQ105 improves memory to 14/16, 16/16, 16/16 on BOTH panels of the SAME 16
authored facts, but seeds0/1 lose valid ACT on all32 arithmetic probes; seed2
retains habit/ACT32/32. Do not average away those failures or select seed2.
SEQ106's two arms from one ORIGINAL root0 each attain own strict INPUT order
32/32, opposite0/32, habit/ACT32/32, with memory unchanged4/16. The after-arm's
legacy before-only joint0 is expected, not failure. This is rehearsed authored
convention coexistence, not input-dependent cognition or a memory result.
SEQ104/105 archived raw recounts PASS within independent-reduction scope;
their reviewers authored implementation components, not fresh-author code reviews.
SEQ106's now-archived separate raw recount also PASSes96 new and48 inherited
H calls within receipt-level scope, confirming Main's symmetric thresholds. C51
now adds the root0 repeated-row memory-replay result; no live conditional or
new varied-material outcomes are included. All64 confirmation
cases remain unrequested; no G3, parenting, child sleep, H1/H2, clean lineage,
novel-fact transfer or substrate freeze follows. Model origin remains
`UNRESOLVED_LOCAL_HASHES_ONLY`; C11 deferred. Collaborator **UNSENT**.

Internal staging only. The sprint abstract includes the September 14 terminal
results; canonical main.tex was updated separately by Main. No complete
cross-draft review is claimed. H1/H2 are proposed questions, not established
outcomes. The earlier dated record is retained.

## Historical concise abstract — September 14 before SEQ224

Superseded by the SEQ224 update; retained verbatim.

We ask whether developmental teaching produces durable, adapter-mediated
learning-process competence on task-disjoint situations after reload and
removal of teacher access and temporary teaching context (H1), and whether it
increases improvement from new, self-generated, externally grounded experience
on unseen verifiable tasks through continued consolidation (H2). Both remain
proposed questions. We study frozen Qwen2.5-7B-Instruct with learning confined
to LoRA adapters, separating acquisition, retention and downstream use.

Earlier prompt-robustness failures and bounded same-bank rehearsal retention
remain. In an own-EVENT write, fresh-process cold recall improves from 0/4 to
4/4, but unknown-address rejection falls from 4/4 to 0/4 and strict action
panels remain 0/4. A separate self-issued-access diagnostic scores BASE 2/4,
FITTED 3/4 and reader-OFF 3/4 with zero READs throughout, leaving reader-OFF
unexercised.

Outcome-only A4 and source-action copy-mixture fits each complete 256 updates
and solve 4/8 strict chains with identical chain outputs. Copy canaries improve
from 4/16 to 9/16, while PROSPECT falls from 3/4 to 2/4 and CONTINUE remains
0/4. Neither controller qualifies; replacing outcome presentations with copies
does not isolate replay causality.

Separately, frozen BASE collection consults externally retained raw EVENT text,
not parametric recall. Explicit first-READ coaching increases read uptake from
2/8 to 8/8 and read-backed selection from 2/8 to 5/8 on reused tasks, while
GOAL arrivals stay 5/8. Eleven selected student rows are data, not a fitted
policy or the saved learner's subsequent experience.

These small, adaptively reused DEV panels distinguish persistence, consultation
and reliable conditional action. Shared tasks and optimizer seeds are not
independent banks. No qualified birth, autonomous parenting, H1/H2 result or
self-improving learning loop is established; the research program continues.

## Historical concise abstract — September 13, 2026

Superseded by the September 14 active abstract; retained verbatim.

We ask whether developmental teaching produces durable, adapter-mediated
learning-process competence on task-disjoint situations after reload and
removal of teacher access and temporary teaching context (H1), and whether it
increases improvement from new, self-generated, externally grounded experience
on unseen verifiable tasks through continued consolidation (H2). Both remain
proposed questions. We study frozen Qwen2.5-7B-Instruct with learning confined
to LoRA adapters, separating acquisition, retention and downstream use.

Through SEQ195, two component findings constrain this program. SEQ192 tests
three existing prediction adapters without new fits on 24 shared authored
cases in FULL/MINIMAL prompt packages. Typed-content scores are 24/23/19 and
24/1/18, respectively, versus disabled-adapter baselines of 16/24 and 14/24
per learner. Two learners fail the predeclared MINIMAL continuation rule; the
branch stops. Content and strict format differ, and absent same-ID
counterfactuals preclude isolated evidence-use attribution.

SEQ195 uses one exposed, format-assisted eight-EVENT DEV bank across three
optimizer seeds and repeated cold W0/W8 views. After A200 acquires four old A
records, both new-only writes reduce A from 4/4 to 0/4 while acquiring B 4/4.
Scheduled replay and clean cumulative training each yield A4/4 and B4/4 in
every seed/view. Controls match either new-item dose or update/presentation
work, not both jointly; the saturated cumulative tie is not equivalence.
Failure-inclusive work is 20 fits, 6,400 updates, 25,600 presentations and 288
readouts, including five excluded fits and 1,000 updates.

This is bounded within-bank rehearsal retention, not independent-bank
generality, selectivity, action utility, parenting, clean lineage, broad G3 or
evidence for H1/H2. Earlier negatives remain; no mechanism freeze follows.
Integrated learning and the full sprint remain incomplete.

## Historical extended abstract — verbatim evidence log

Can developmental teaching improve learning after teacher removal? We separate externally authored training, child experience and parent-free utility using frozen Qwen2.5-7B-Instruct with LoRA. Earlier sequential-memory retention and failed process-readout criteria remain bounded results. Two source-authored TRAINED birth adapters each complete 128 updates; this is not the child's learned experience or self-learning. Across 384 calls, AUTH scores PROSPECT 32/32 and REVISE 58/64; DERANGED follows its own assigned map at 32/32 and 56/64, not AUTH truth. Both pass belief/goal twins at 16/16, but revision twins score 26/32 and 24/32 against 29/32 required, and both miss one required addition item. Thus both fail the full conjunction despite assigned-map success. Both trained arms answer 31+48 as 89; OFF's 16 numerically correct addition outputs (manual descriptive inspection) preclude an arithmetic-improvement claim from 15/16 compliance. OFF outputs are truncated on 96/128 calls, so strict zeros do not establish absent base reasoning. No exact-train-form panel distinguishes acquisition from access failures. Exploratory AUTH-child formation with base-only parents completes 28 calls: 17 wake, four parent, four restatement and three record. Six of eight tasks are protocol-invalid; one of three records is faithful; zero of four prescribed rows is eligible. PAIRED_SHORTAGE blocks both downstream writes: no persistent parenting comparison follows. Teacher misstatements prevent neutral-parent purity claims. Without contemporaneous OFF formation, observed birth-tag spill does not establish causal harm. Independent birth-audit comparison is complete; formation is not independently certified. At the historical birth/formation cut, source was NOT CLEAN and official base revision was unresolved. Later prospective file matching is limited to the checked node3 snapshot; historical receipt labels and clean-ancestry limitations remain unchanged. No H1/H2/P1/G3/G5 or freeze follows.

Subsequent completed diagnostics through SEQ133 separate full-dose writer
failure from authored reflection practice. Q0 R0/R2 each complete 128 updates
per arm but fail the registered endpoint: AUTH/DERANGED exact counts are
71/70 and 65/72 out of 128, respectively; R1's final paired endpoint is missing
following a runtime abort, not zero accuracy. Root and learner seed vary
together, so these are two completed instances, not a three-seed failure rate.
Across three preselected reflection learner seeds, ordinary practice raises
parent-withdrawn strict application from 7/12 to 9/12 in every seed; all application
outputs already have valid A/B syntax, so this is not format rescue. Correction
training adds 0, 0, -1 correct applications after withdrawal versus ordinary
practice: no observed advantage here. Exact authored restatement matches remain
zero, not a semantic-prose failure. These authored birth-component targets do
not test child-authored SLEEP, P1 or H2; formal C11 remains deferred.

A subsequent read-only R1 supplement does not repair its aborted primary.
The first native child-record loop completes 11 stages, 128 generation calls,
three fits and 100 updates, connecting records, compilation, fitting, mounting
and subsequent wake/readout. All five vLLM readout panels remain old 4/8 and
new 4/8. A separate HF forced-candidate probe nevertheless measures distribution
change and weak, fragile train-form discrimination: fit2 scores 12/16 by full
likelihood, including four tiny downstream tie-break successes, versus 8/16
strict first-token choices with five exact ties; both held-readout measures
remain 8/16. Unequal 12/14-token targets and HF teacher forcing differ from
vLLM greedy generation. This is neither no learning nor a pure access failure,
and does not establish parenting, clean ancestry, general G1 or a mechanism
freeze. The research question remains open.

At the historical SEQ-143 cut, four standalone authored Level1 skills each reach 48/48 held
content and strict accuracy in all three learner seeds, from OFF content counts
22, 32, 17 and 8 for prediction, goal completion, contradiction and update
judgement; all post-fit canaries score 12/12. These controlled component gains
include source-field corrections, not only formatting, but share fixed material
and do not estimate a matched parenting effect. A separate contrastive screen
scores OFF/PLAIN/CONTRASTIVE 2/17/19 out of 24 strict and fails its preregistered
screen: its net two-item advantage over PLAIN includes three valid-field wins
and one loss, while gains over OFF are interface-confounded. Original low/high-LR
loops on learner seeds 1 and 2 retain old 4/8 and new 4/8 at every readout;
a separately archived low-LR seed0 recovery is also flat. Original seed0 aborts
remain missing, and high-LR recovery remains pending at this cut. Five A100
warm-up failures yield no scientific endpoints, not zero accuracy. Newer-roster
and actual-record transfer results remain pending. The learning-flywheel thesis
and H1/H2 remain open; these results neither complete the mission nor freeze a
mechanism.

At the historical SEQ-151 cut, all 24 standalone authored Level1 cells are complete;
the second roster improves held content but incurs three canary regressions.
Prompt-scaffolded actual-record formation yields OFF7/16 versus14/16,8/16,8/16
source-faithful records from the same three perception learners, with mandatory
priors and state-varying actions and histories. This is not matched parenting or
a learned closed loop. Separate high-LR seed0 recovery also has zero observed
treatment contrasts. A checkpoint-specific HF diagnostic gives TRAIN15/16 and
READOUT8/16 by both first-divergent-token and full likelihood, not native greedy accuracy;
independent analysis remains pending. Actual-memory writing/readback remains
protocol/CPU-runner development, not a result. H1/H2 and the mission remain open.

At the historical SEQ-153 cut, native greedy exact-TRAIN at the high-seed2 checkpoint scores
14/16 versus OFF8/16, while both READOUT scores remain8/16; HF forced15/16 is
not the native endpoint. Three same-learner actual-record WRITE/LR0 pairs show
cold source-faithful exact-cue recall8/14,7/8,5/8 versus zero, with paraphrase
6/14,5/8,5/8. Exact-byte recall is7/14,7/8,5/8 and strict canonical recall
3/14,0/8,0/8. Held perception falls to44/48,37/48,17/48 from47/48,48/48,48/48:
3/11/31 itemwise losses despite unchanged12/12canaries. This is narrow native
parametric carriage of sourced child records, not stable retention, better
future learning, parenting, general G3, H1/H2 or a working learned loop.
Against an evaluator-only best constant record, exact recall gains+2/+3/+1
and paraphrase+0/+1/+1; seed0 paraphrase is literally constant. These saved-panel
differences exclude only a single fixed-response alternative; they do not establish
causal key binding.
The completed follow-ups below qualify these findings; the mission remains open.

Through SEQ-155, fresh-interaction source-faithful formation is8/16 per WRITE
learner versus LR0 7/16,6/16,4/16; all48example-absent wakes fail comma syntax.
Current facts remain visible, and reached experiences differ between arms.
Lower-LR3e-5 yields exact-cue10/14,4/8,4/8 and paraphrase10/14,5/8,3/8,
with held47/48,46/48,47/48 and intact12/12canaries. Only seed0 meets the
joint exploratory screen against reused historical controls; the three-seed
repair fails. This partial retention recovery does not erase the HIGH write's
3/11/31losses or prove stable learning. The HIGH constant-record diagnostic
cannot be extrapolated to LOWER. Fixed-coaching and full-dose contrastive were
prospective at that historical cut; their completed assays are distinguished next.

At the historical SEQ-158 cut, fixed author coaching and neutral contact followed by own-record
writing yield the same fresh held eligibility16/16,16/16,13/16 across three
learners, versus ORIGINAL11/16,8/16,8/16. Incremental held coaching contrast is zero, not
an equivalence result or a parenting benefit; admitted material and write doses
differ. Old held retention is47/47,47/47,44/46 in coaching/neutral order versus
historical47/48/48, despite intact12/12canaries; all360old-retention score
objects match frozen-scorer replay. The fixed ACT scaffold and state-dependent
experience remain, with CONF untouched and no adaptive parent. Full-dose
contrastive gains+2,+6,0 over PLAIN fail all three frozen screens. A zero-fit
capture validates the same24source-supported TRAIN records across three parents,
not72novel facts. Own-source replay repair is launched, with no outcomes included.
No same-history raw-chronological LoRA comparator isolates extraction/compiler
utility; H1/H2 remain hypotheses rather than demonstrated mechanisms.

At the historical SEQ-159 cut, own-source replay retains every historically LR0-correct held
and canary item, but exact-cue recall10/14,6/8,5/8 and paraphrase10/14,6/8,3/8
do not establish an all-seed repair. EXTRA_MEMORY has exact13/14,7/8,7/8 and
paraphrase10/14,6/8,7/8 while losing0/2/6old held items. Frozen screens pass
2/3versus1/3; REPLAYseed2paraphrase3/8 falls below the limited constant4/8.
Equal steps do not equal memory exposure or token compute. Historical controls,
shared authored replay sources and the absent raw-chronological LoRA comparator
limit attribution; alignment was CPU development at that cut, now reported below.

Through SEQ-160, immediate fixed-lesson alignment fails its frozen screen:
process-use, record-faithfulness and full-material counts are0/16in all nine
cells. All144NOTE attempts and137called sources fail normalization, precluding
schema-valid source-field assessment; lexical RESTATE can reject plausible
paraphrases. These zeros do not establish absent raw processing or a general
absence of parenting effects. Separate own-event field errors persist. The
305-call assay has zero fits/updates, no post-write parent-free evaluation or amortization
test. CPU-only additive parity is engineering evidence, not a new outcome.

Through SEQ-161, matched full-memory-schedule additive replay gives exact eligible
14/14,7/8,8/8 versus fresh memory-only10/14,8/8,3/8; paraphrase10/14,7/8,4/8 versus
10/14,8/8,2/8; held47/48,48/48,39/48 versus47/48,46/48,47/48, with12/12canaries.
Screens pass2/3versus1/3, not an all-seed repair: additive seed2 loses nine
LR0-correct held items and its paraphrase4/8 ties a constant-target diagnostic.
Fresh memory-only differs from historical EXTRA_MEMORY in loss/final-tensor
receipts despite matching initial receipts and memory schedules; cause unresolved.
Six fits,1632updates and480calls match memory exposure, not compute/RNG. A separate
zero-generation/fit/update collection repair preserves original rc0/1/1 and
launcher anomalies: no scientific retry or change to scoring rules. Replay uses
already-trained authored observations, not new experience or parenting. No
H1/H2, general G3 or clean-lineage promotion follows.

[SEQ161 / C97 archived sources](../research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md#c97--seq161-additive-replay-with-native-baseline-drift) bind this update; collaborator remains UNSENT.

Through SEQ-162, one instrumented seed0 OLD/NEW first-backward pair has
matching recorded initial trainable tensors, inputs, settings, optimizer,
environment and six-boundary RNG snapshots, with equal loss 1.907779335975647,
but 256/392 gradient tensor data hashes differ. No optimizer step, adapter save
or readout occurs. This establishes first-gradient nonidentity for this pair,
not its cause, effect size, backward-origin localization or repeatability.
Equal loss/RNG does not establish equal intermediate computation; historical
baseline drift remains unresolved. No H1/H2 or freeze promotion follows.

[SEQ162 / C98 archived sources](../research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md#c98--seq162-instrumented-first-gradient-nonidentity) bind this diagnostic; collaborator remains UNSENT.

Attempt 2 ended as UNUSABLE EXECUTION --- ENGINEERING-ONLY CAPTURE
(FINALIZATION FAILED). Archived bytes support interface/lifecycle debugging,
not a usable C0 result or learning evidence; the original gate remains failed.

A separate exploratory one-bank experiment records cold acquisition of trained, source-grounded mappings, without compute-matched controls or demonstrated downstream use or parenting.

Through SEQ195, prediction prompt-package robustness fails its predeclared
continuation rule: on 24 shared authored cases, MINIMAL content scores are
24/1/18 across three learners versus OFF 14/24 each; two learners fail.
Separately, on one exposed, format-assisted eight-EVENT DEV bank, all three
optimizer seeds show the same cold W0/W8 outcomes: after A acquisition at 4/4,
both new-only writes leave A at 0/4 while acquiring B at 4/4; scheduled replay
and clean cumulative training each retain A 4/4 and B 4/4. These are repeated
fits and views of one bank, not independent-bank replications. The controls
match either new-item dose or update/presentation work, not both jointly;
the saturated replay/cumulative tie is not equivalence. Failure-inclusive
SEQ195 work is 20 fits, 6,400 updates, 25,600 presentations and 288 readouts,
including five excluded fits and 1,000 updates. This bounded retention result
does not rescue earlier negatives or establish action utility, broad G3/H1/H2,
parenting, clean lineage or a mechanism freeze. The full sprint remains incomplete.

Sources: [C105–C106 claim map](../research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md#c105--seq192-prediction-worksheet-prompt-package-robustness),
[SEQ192 result](../research_notes/analysis/2026-09-13_level1_prediction_transfer_result.md),
[SEQ195 raw report](../research_notes/analysis/2026-09-13_event_retention_v2_three_seed_raw_report.md)
and [fresh independent audit](../research_notes/analysis/2026-09-13_event_retention_v2_three_seed_final_fresh_audit.md).
The [post-SEQ195 re-audit](../research_notes/analysis/2026-09-13_post_seq195_critical_path_efficiency_reaudit.md)
is strategy only, not a new result; its claim-map-staleness note predates C106.
See [README](README.md#current-evidence-and-custody-through-seq195) for exact source hashes and custody limits.

## Historical SEQ143 result-table companion — C79–C82

| Level1 skill (each learner seed0/1/2) | Held content /48 OFF→post | Held strict /48 | Canary C/S /12 | Content W/L |
| --- | ---: | ---: | ---: | ---: |
| Prediction | 22→48 | 22→48 | 11→12 | 26/0 |
| Goal completion | 32→48 | 32→48 | 11→12 | 16/0 |
| Contradiction | 17→48 | 0→48 | 12→12 | 31/0 |
| Update judgement | 8→48 | 0→48 | 12→12 | 40/0 |

Each entry is also the three-learner mean, range[x,x], on one fixed materialseed0.
Strict combines content and canonical output; all12roots complete, collected
once. Total1440calls/12fits/3840updates. The original Level1 content parser already
accepts one enclosing fence: contradiction's+31 is source correction, not merely
format; goal's+16 corrects already-canonical decisions. Prediction and update
include both source and interface corrections. No-update OFF is not a matched
trained parenting control, and shared canaries do not certify broad retention.

Contrastive strict OFF/PLAIN/CONTRASTIVE is2/17/19 out of24; D1/D2 contrastive
12/12 and7/12. Original screenFALSE,144calls/2fits/24updates. Its3valid-field
wins/1loss versusPLAIN do not imply a robust wrapper advantage: D1/D2 share12cases,
and both-wrapper correct is8/12 PLAIN versus7/12 contrastive. No permissive
rescoring of the22malformed OFF held outputs is licensed by the later protocol.

Original LR seeds1/2 at3e-5 and1e-4 complete four loops; all five readouts per
loop remain old4/8,new4/8,legal16/16 with final paired8/0/0/8. Separate low-seed0
attempt2 also completes128calls/3fits/100updates with flat endpoints, without
replacing the original two seed0 aborts. High-seed0 recovery is **PENDING**.
A100 has5warm-up failures before any fit or captured response, not5zero scores;
its sixth prepared cell did not launch. Newer-roster and real-record results
remain **PENDING at SEQ143**. The scientific question is what transfers beyond
these authored fixtures and into a controlled child-record loop, not whether
the mission is already complete.

See [C79–C82 source pins](../research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md)
and the [all12 table and costs](README.md). These are internal evidence links,
not new literature references or independent approval of this manuscript patch.

## Evidence and interpretation boundaries

**C63–C65 terminal cut: trained birth is neither full qualification nor parenting.**
Fit seed0 uses256 contexts per arm, rank8, LR1e-4, four epochs, batch8,
128 updates each/256 total,23,296 target-token presentations total. The complete
384-call panel uses128 identical requests per OFF/AUTH/DERANGED cell and a
64-token cap; trained arms have zero cap hits and EOS128/128 each. OFF strict
PROSPECT0/32 and REVISE0/64, addition/copy8/16 each, are budget-limited
observations. AUTH/DERANGED addition15/16 each, copy16/16 each, zero forbidden
anchor tag spill; the unchanged full conjunction still fails. Expected,
observed and prior-action twins each score26/32 AUTH,24/32 DERANGED. AUTH's
COMPARE/POLICY are64/64 each; its six REVISE misses are NEXT errors.
The preserved v1 raw review locates those six in template2 MATCH/KEEP cases choosing
first displayed instead of prior action, and identifies two malformed dual-NEXT
DERANGED outputs. Both trained arms'0097 emit `ACT: 89` for31+48=79, a real
arithmetic error. OFF's16 correct numeric sums are manual descriptive observations,
not replacement scoring;15/16 trained compliance is not improved arithmetic.

Formation's P apply quizzes3/6 each and A's no-TRY apply tasks are descriptive.
P lesson0 supplies no slot; P lesson1 call0012 has no explicit PREDICT T/F;
A lesson0/1 calls0022/0027 lack canonical ACT. No corpus export, replacement,
padding, target rewrite or parent-free descendant comparison. Record0011 alone
is faithful;0013/0015 map null prediction to matched rather than unavailable.
Main's canonical audit records teacher misstatements and no neutral-parent
purity acceptance. No causal birth-harm inference without OFF formation.

Ampere v2 reports `FINAL_BOUNDED_COMPARISON_COMPLETE`: all strict/joint
headlines, twins and registered counts match; ten explained field-retention
differences on the same two dual-NEXT rows, zero unexplained. Unique-NEXT parsing
now gives DERANGED AUTH-NEXT6/64, matching frozen; neither malformed row becomes
valid. V1 is preserved. This is not scientific/native approval: Ampere did not
independently verify native token decoding; official model origin and clean
ancestry remain unresolved. Reviewer
discloses downstream-helper authorship and expected-count/scorer exposure,
not original birth runner/corpus authorship or blinding. No raw recount was
duplicated here. Fit/readout intervals sum1438.181836s (23.969697 A40-min),
excluding the gap; formation379.776464s (6.329608 A40-min), nested costs.
Canonical birth/formation memos, ledger/notebook and selected manifests are
bound in claim-map C63–C65. No new probe evidence is included.

**C55–C56 terminal cut: verified writing is not useful parenting.** Two fresh
rank8 adapters each complete12 updates, with392 finite saved tensors/nonzero B.
Full parameter deltas/usefulness are not inferred. OFF7/24 versus P/A6/24 gives
no P advantage; rule5 protocol-invalid missing quizzes retain zero/6 in the
fixed24 denominator. Valid quizzes4 versus3 and faithful9/12 versus10/12
allotted (10/11 emitted) remain separate. All states have eight valid pre-TRY
predictions, all F/six correct: higher prompted record fidelity is not increased
prediction competence. Herschel's returned raw review is read, not assumed from
the memo; it resolves the two-action rule5 failure and separately checks29
aligned P/A texts/prompts/token vectors. Aggregate equality alone implies no
raw/parameter identity. One pair/four shared rules, no adult updates, no clean
confirmation or G3/P1/G5/H1/H2/freeze. The interleaved diagnostic was LIVE at that
C56 cut; terminal C57 now supersedes its status, not this null contrast.

**C52–C54: diagnostics and formation are not parenting utility.** Conditional
own-map generation64/64 train and32/32 dev per operation coexists with locality
failure; public suffix+OBSERVED+PRIOR predicts REVISE without EXPECTED, so the
intended comparison is not identified. Copy has eight unique prompts twice;
its hyphen-validity quirk is preserved. Grouped varied memory remains4/16 on
both panels for both arms; FOUR habit/ACT32/32 versus SINGLE0/32 does not rescue
the memory gate. Four within-batch copies/views yield10 source-specific updates,
not40 sequential updates; equal target budget does not mean equal input compute.
Darwin's now-archived raw-recount PASS has been read; its material/grouping scope
remains bounded. SEQ110 Main audit accepts fixed P0008/0010 and A0038/0040 raw
records/contracts only; A0042 remains failed. Parent/restatement prose, including
P's hypothetical sum, stays out of sleep. The historical C54 RUNNING/NOT RUN
status is now superseded by C55/C56 terminal evidence, not parenting utility.
C52–C54 bind exact receipts and nested costs, not a model-origin or G3/P1/G5/H1/H2
qualification. Collaborator remains UNSENT.

**C51: root0 allocation, not isolated replay benefit.** MIXED's dev14/16 and
exact13/16 fail the >=15/16-per-panel progression rule despite habit/ACT32/32.
ALL_MEMORY is16/16 on both panels but emits colors instead of valid arithmetic
ACT on all32 questions. All128 calls stop normally, with none at the64-token cap.
MIXED dev errors003/004 and exact errors008/010/015 are disjoint on the SAME16
facts. Both arms fork the ORIGINAL parent and take160 new updates (240 cumulative),
not a restoration from SEQ105. MIXED memory exposure20 versus ALL_MEMORY40 and
input/target presentations33080/5000 versus28160/1280 preclude equal-dose/compute
or isolated replay attribution. The SEQ105 root0 80-update condition is an inherited
half-update descriptive anchor only. Both arms complete; no seeds1/2, pooling,
threshold revision or seed selection. Raw-recount PASS does not change failed
progression or qualify general G3/P1/G5/H1/H2. Full-reservation/controller/worker
seconds1062.131771/954.336828/722.441552 are nested, not additive or GPU busy time.
The earlier C51 cut excluded those now-reported C52/C53 diagnostics; this repeated-row
assay is not operational child-authored SLEEP. Exact bindings are in C51.

**C48–C50 interpretation details.** SEQ104 memory, in LR0/3e-5/1e-4 order,
is4/4/4,7/6/5,3/3/4 out of16 for teaching seeds0/1/2; all ACTs remain correct.
SEQ105 uses80 new memory-only updates and no arithmetic/habit rehearsal.
Seed0 misses the same two yellow facts, but wrong blue/green answers swap
across surfaces: equal counts do not imply identical vectors. Seed1 has23
arithmetic calls at the64-token cap. Dose, subset and cumulative exposure change
together, so interference versus dose is not isolated. Seed2's coexistence does
not establish reliable retention or a need for separate adapters.
SEQ106 explicitly rehearses the old convention while adding a compatible one;
it does not use memory-only checkpoints or inherit their memory success.
Full-reservation/controller/worker seconds for104/105/106 are respectively
2023.382487/1512.304214/976.997025,1666.592415/1101.776900/785.153102,
799.928952/537.610627/381.280358: nested, not additive or GPU busy time.
No new OFF or confirmation calls. C51 now reports the separate root0 repeated-row
replay result, not live conditional or new varied-material outcomes.

**Historical terminal SEQ101–103 — C45–C47.** Repetition retains80updates in all four cells;
SHORT batch4/accum16 preserves the original four groups/update rather than
providing16times sequential optimizer practice. Loss normalization, homogeneous
versus mixed-group batches, and dropout prohibit exact-gradient/equal-task-weight
claims. Final reported losses are arithmetic microbatch losses, not memory losses.
All four cells remain red4/16 on development paraphrases; repeated-checkpoint
training-prompt recall is untested. SEQ102 is12fits/576calls from one original
teaching seed: both positive rates replace adherence32/32with0/32by16updates,
with exact correct ACT-only32/32; LR0 parameters/output vectors are unchanged.
Arithmetic32/32 and red4/16 persist, not passive fading or general retention.
SEQ103 is32HFforwards on16original training prefixes, no new generations/fits:
red16/16 matches inherited vLLM first tokens, not full cross-backend logits.
Actual generation input/output tokens are8524/1888 for101 and25572/3648 for102,
not caps12288/36864. SEQ102 worker2125.367463s, controller3073.313819s and full
reservation3460.763131s overlap; SEQ103 worker64.699761s differs from full
reservation141.936394s. Model origin remains unresolved; no absent weights are
rehashed by local review. C48 now adds first-phase replication outcomes; no confirmation, general memory
gate, parenting/H1/H2, representative G3 or mechanism freeze is claimed.

**Historical September 12,18:31UTC — C42–C44.** All six fitted states and actual reused
OFF retain32/32correct ACTs. Three trainer seeds share data and probes, not
96independent learners; the64confirmation cases remain unrequested. Seed0
training-prompt answers are red16/16 in both fitted arms,4/16correct; OFF
has16invalid answers at the64-token cap on both memory panels, not an uncapped
negative. Later teaching answers are not universally constant, but memory
contrasts0,+3,-1 do not establish a reliable advantage. The broader level-1
core corpus is not built; authored post-training is not child sleep/parenting.
Native warm-start CPU21/21without skips and repetition-export38CPUtests are
engineering only; fresh optimizer means no optimizer-state resumption. No new
continuation/repetition GPU outcomes are included. C42–C44 bind the memos,
capsules, Main analyses and separate review scopes; the supplied follow-up
review supersedes pending status without changing any endpoint.

**Historical September 12,17:40UTC — C40/C41.** SEQ096 has independent bounded PASS:
original/fullclarified/tokenclarified relations1/3,3/3,2/3; token-only has no
full-record endpoint. A generic definition fixes these selected cases, not
parenting or old-root writing. SEQ097 has independent PASS on all192 first
ACTs: useful ON3/16 at each optimizer seed, every OFF/corrupt0/16, complete OFF
output vectors equal. Secondary partial scores also improve for corrupt ON.
IDs1900071/1900072/1900073/1900075 have prior readout exposure; comprehensive
freshness was withdrawn before outcomes and the full16 primary retained with
no subset rescue. Exact original48-entry nonoverlap is not confirmation,
clean lineage or gates. No new fits;384calls,96000cap tokens (actual native
token usage unavailable),0.669809458summed controller A40-hours,
843.467018wall span and3224.829040reservation seconds including audit idle.

At that cut, old pending-panel statements were historical. The elementary birth-teaching
pair launched17:39UTC on node3GPUs0/1 is live only:80rows/arm,
4517input/912target tokens per epoch, planned4epochs/3e-4/rank8/seed0.
No outcomes, L1 pass or speculative findings were included at that cut; C42–C44
now supersede the live-pair status without changing earlier endpoints. Formal C11 deferred.

**Historical SEQ094/095 — C38/C39 formation stops, not learning.** V1 has eight invalid
tasks, no scored quizzes, zero process record opportunities and two faithful
active records of four. Its zero-filled quiz scores are not observed wrong
answers. V2 has eight valid first quizzes, 24 True TRY outcomes and faithful
process1/6 versus active3/6; first-two selection returns 1 versus 2. Both are
`MAIN_DECLINED_MATERIAL`: paired shortage independently prevents all fits and
parent-free/new-rule readouts, and acknowledgment-only controls deviate from
their contract. There is no P1/G5/H1/H2 or strongest-teacher conclusion.
The underspecified relation elicitor and generic same-7B feedback leave adequate
target-skill teaching untested; versioned execution repair is not learning.

V1/v2 use 32/60 responses, 11895/23342 prompt and 1446/1296 output tokens.
Generation-call sums are 42.209187/38.957460 seconds; supervised-worker windows
including cleanup are 169.633754/164.493039 seconds, excluding outer hashing,
CPU preparation, Main audit and transfer, not active-GPU or campaign cost.
Native captures/Main audits are read, not independently scientifically rerun.

Main's notebook response to raw message 14 (September 12, 16:53 UTC) states no
validated perfect teaching corpus, disaggregated cycles rather than childhoods,
no project level-1/base updates and unverified bootstrap-v3 birth material.
SEQ092 supplies no sleep-interval causality or A1-parameter forgetting result.
At that historical cut the repaired helper awaited native preparation;
terminal C41 supersedes the pending-panel status on September 12, 17:40 UTC. Formal C11 is deferred. No new literature/reproduction or
teacher/lesson-training claim is introduced.

**Historical September 12, 16:20 UTC — C36/C37 terminal boundaries.** SEQ092 is fresh-base
OLD/NEW/union reconstruction, not warm-start retention. OLD fact/frame ratios
are 1.169323/0.493124; NEW bicycle spill exceeds frame gain. Denominators are
16/32 owners within one seed/bank, not learner replications. Independent review
PASS permits bounded reporting, not selective-memory/G3 or mechanism freeze.

SEQ093 has native validation PASS and a separate post-hoc Halley audit:
OFF/FULL/SYNTAX schema and grounding remain 0/8 each. FULL trained geometry is
8/8 versus SYNTAX 1/8, with only FULL t02 a true literal witness and no repairs.
Both ON arms end `][]}` at 32 tokens/case, not the 128-token cap. A 75-byte
incomplete prefix against a complete-record readout is a plausible limitation,
not a proven sole cause or evidence of no parameter learning. Byte-exact
selection does not preserve source token IDs: token 30 differs. Original t02
used 332 prompt tokens/temperature 0.7 versus current 234/0.0; current OFF is
the baseline. Matched 264 input IDs do not match supervised dose (27/21).
One selected event/optimizer seed, eight exposed boards, 24 calls/64 updates
and 564.719025 controller-execution seconds establish neither generalization
nor internalization. No new teacher/lesson approval. At that cut the selected RuleGame block was not launched; terminal C38/C39
now supersede that status. Formal C11 remains deferred.
Exact memos, archived SEQ092 CSV/JSON/SVG/review and the supplied Halley audit
are indexed in C36/C37. Native checks and audits are read, not rerun here.

**SEQ091 / C35:** source process 2/8 versus format 0/8; application 1/8 versus
0/8, with sole valid t02 following invalid s02. No correct-source-to-application
chain is verified. The audit preserves strict scores and confirms all 16 exact
note insertions: parent-free but note-present. Process explanations cost
67/78 tokens versus format 57; prompt/output totals are 5637/652 versus
5536/648, not dose matched. Full 32 calls take 340.548915 controller seconds,
excluding external preparation/audit; one sampler seed is not learner
replication, and zero fits occur. No free-prose lesson is verified or
training-approved. Supplied terminal and independent audit findings are not
new local reducer or remote checks. No persistence, internalization, P1/G5,
H1/H2 or causal parenting claim follows from SEQ091. Its historical running/
implementation status is superseded by terminal C36/C37 at September 12,
16:20 UTC. The SEQ091 audit approves no complete output or free-prose lesson;
the later citation-prefix write was separately selected and executed. Main has archived the audit with
same-prefix Markdown/JSON/Python receipts linked in C35 and retains GPU work.

**Supplementary scoring warning:** Main reports266/832score rows with sum(exp(full-candidate log scores))>1.000001, allON, maximum1.3802383379079028. This contradicts two distinct complete LF+EOS continuations under the same causal prefix. Main's native diagnosis identifies sequence-shape numerical inconsistency in BF16 eager scoring with correct causal attention masks, not direct future-token leakage. Original probability/NLL/TV interpretations remain invalid; SEQ086 now provides a distinct equal-shape supplementary rescore, not a replacement or gate rescue. Generation observations remain. Exact replay does not validate likelihood semantics; no writer qualification or exact-train follow-up launch.

**Confirmed native diagnosis (reported by Main):** original pair mass1.380238/prefix-logprob difference4.759876; both candidates future-padded to101tokens give mass.997894/difference0. FP32natural lengths give mass.998979/difference about7e-5; FP32aligned gives.998970/0. Same-prefix logits depend numerically on total candidate sequence length in BF16 eager despite correct causal masks. These diagnostic comparisons are not a full corrected experiment. The shared-length repair is used in completed SEQ086 supplementary rescoring; original artifacts remain preserved and no new fit or generation is performed. Scope is the semantic scorer, not all prior experiments; ordinary generated solve counts remain observations.

- **SEQ-073 / C14:** useful ON solves2/3/5 versus corrupt0/1/0, all OFF0, on the same16 questions. Net gains2/2/5 of16; no episode-pooled significance. Four canaries share solution grids with training;1900055 is among useful solves. Three optimizer seeds are not48 independent puzzles. New seed1/2 controller time totals37.48A40-minutes; this is not total campaign compute.
- **SEQ-074 / C15:** original/prefix-mask I_d_frame1.921469873/.015228690; spill.415536920/.201955099; masked ON correct probability.250952640 versus OFF.259649920. G9/G11 both fail. Same749,985 input-token passes but711,213/422,925 supervised passes, with5,376 conservative boundary-token omissions. Training1216.1seconds, not end-to-end cost.
- **SEQ-075 / C16:** all four solve counts0/16. Partial means OFF.1125, lesson ON.0475, sham ON.010546875. The+.036953125 difference-of-gains is less degradation, not useful learning. Two96-step fits take87.1/86.0seconds; target passes12,867/16,080, teacher packages203/158tokens. Only five of32 source episodes are mini-Sudoku; six other source families are untested. Source1189872/canary1900061 share a solution. The original NOTE-gated skip remains unchanged; this fork uses a distinct source-linked raw-output recipe.
- **SEQ-076 / C17:** coefficient.1 attempt1 stops after OFF-cache creation, before optimizer steps, loss trace, adapter weights or evaluation. Float64 validation repairs numerical normalization without changing cached float32 bytes or the training objective. Not a negative preservation result or an SDFT reproduction.
- **C18 protocol status:** coefficient-zero completion is recorded in C20; the completed coefficient.1 pair is now recorded in C23. The static scout's launch-only status is superseded by C19, not inferred from preparation.
- **SEQ-077 / C19:** process/sham solve1/16both (same question); format7/16versus4/16; format-invalid-zero-filled native partial means.192578125/.11875. All32traces have one ACT. Offline554checks pass; all three format gains still violate constraints. Equal97×16=1552teacher tokens/arm; retokenized output1079/1068, none at400cap, not finish-reason evidence. Approximately6.4reserved A40-minutes. No primary gain/internalization; the original comparison had no no-teacher anchor. The later anchor is described separately in C21; the original primary null remains fixed.
- **SEQ-078 / C20:** validated coefficient-zero control reproduces selected historical metrics: acquisition1.921469873, spill.415536920; G9/G11FAIL. All1313cue metadata/order and OFF scores match exactly at serialized precision, not weight identity or independent-seed replication. Fit1227.287s/eval241.1s are stage clocks. The completed treatment comparison is reported in C23.
- **SEQ-079 / C21:** process/sham/later-no-teacher solves1/1/0, formats7/4/3 and zero-filled means.192578125/.11875/.084375 on the same16training questions. All48traces have one ACT. Anchor inputs97tokens shorter; output968retokenized tokens,176.476306reserved seconds. Post-hoc descriptive, not a matched three-arm experiment, reliable teaching benefit or learned persistence.
- **SEQ-080 / C22:** four carrier cells each16/16 generated and scored; swaps32/32 per operation,16copy calls across eight distinct prompts. All80greedy strings omit LF and end with recorded EOS, accepted by the declared parser; full candidate scoring includes LF+EOS and unequal8/7-token suffix-bearing responses. Surface validity only, not writing/memory/retention.144requests,130.633576379seconds including setup/validation.
- **SEQ-081 / C23:** coefficient0/.1 acquisition1.921469873/.152267044 and spill.415536920/.036657910; both arms fail BOTH G9/G11. Treatment interval[-.023955285,.333065840] includes zero. Same CE dose, but9693extra anchor forwards; fit1227.287121/2458.878753seconds. One learner seed, no selective-learning or readiness result.
- **SEQ-082 / C25:** both arms move1→2/32first-ACT solves; qualifying corrections1process/2sham. Equal wake opportunities and97-token packages do not match realized token dose. Process1850124contains a false row claim; only sham1850124survives limited content screening as one modest-rule/valid-own-solution candidate. All three corrections already appear in their own Scratchpads; no utility fit occurred within that collector; the later separate utility result is provisional in C29, not an established learning mechanism.
- **C26 OFF-only diagnosis:**30/64key-map half-nat gain requirements are impossible before ON results; original gates remain unchanged. This bound is arithmetic over the reducer's normalized scores, not currently validated model probabilities, and does not establish writer failure. C28 preserves terminal report flags and generation observations.
- **SEQ085 / C27,C29 verified utility:** shared OFF0/32solves and2/32strict first ACTs; whole_raw ON seeds0/1/2 solves1/0/1, strict5/6/5; ACT-only2/2/1, strict30/30/28. One event replayed32times/96steps per fit; target-token passes8832versus3648, not token matched. Whole raw did not beat ACT-only; format is the dominant observed contrast, not reflection/parenting/H1 evidence. All32panel boards contradict the source solution in their givens. Main verifies the exact report and all192ONpublic-constraint outcomes, matching native acceptance; seven accepted ON outcomes total, not seven independent learners.
- **C28 semantic Q0 terminal:** original-source replay label `OPTIMIZATION_INCONCLUSIVE`; binding/spill false, interface true. Root0+/− and root1+/− balanced accuracies.578125/.515625/.5/.53125, OFF gains.078125/.015625/.015625/.015625. All cell output validity1.0; recorded locality-family TV numbers span.275157–.659671 but their original probability interpretation is invalid; corrected supplementary diagnostics are separate in C30. Four256-step fits/14stages,1414.695execution seconds plus external replay/release. Conditional TV misses common-mode absolute shifts; absolute net legality change can cancel item flips. These assay limits are not newly measured hidden effects; no selective-writer promotion.
- **SEQ086 / C30 supplementary rescore:**832new equal-shape scores across five fresh states,880original generations reused, zero new fits;347.468seconds. Same generation BA and `OPTIMIZATION_INCONCLUSIVE` label, binding/spill false, interface true. Mean conditional log-q gains1.0789566/.9514255/.6465927/.6083202; mean binary conditional TV.2800904–.6563001. Separate score diagnostics, not original-gate rescue, new learning or selective-writer qualification.

Exact memos, receipts and permitted claims are linked in `research_notes/astra_memos/ASTRA_PAPER_CLAIM_MAP_2026-09-12.md`, through C47. Historical A1/A2, W0 invalidity and original P0 custody remain documented in C03–C13; they are not replaced by these newer diagnostics. Local model-origin authentication remains unresolved. Ordinary exploratory hygiene applies; final paper-grade C11 work stays deferred under Rohin's steer, not a new launch gate. Canonical component evidence is updated separately without changing its characterization abstract, historical tables or appendix. No literature entries are added and no collaborator message is sent.
