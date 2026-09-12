# Can an agent be taught to turn its own experience into training data that makes its later learning better? Collaborator brief (v3 DRAFT, 2026-09-12)

**DRAFT for Rohin's review; v2 stands until he adopts this.** Sources, in reading order: Rohin's own words (`research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, which wins wherever a paraphrase differs), the thesis note (`THESIS_v2_SELF_LEARNING_FLYWHEEL.md`), Astra memo q15, and the notebook (`research_loop/COORDINATION.md`, entries SEQ-nnn).

## 1. The question and the spine

The question is not whether a small model can be trained on its own text. Post-training already changes behaviour and stores associations. The hypothesis is that an agent can be **taught the disposition to turn externally grounded experience into good post-training data about itself**, so that episodes, parental corrections and environment outcomes flow through its own thinking into qualified weight changes at sleep, and its later learning gets better because of it. In Rohin's words: "everything it thinks turns into post-trainable data... that is the behavior that allows self learning. That is this entire paper." Childhood parenting is intended to build this flywheel. Parent-absent deployment removes the teacher, not the loop; the final test also includes matched parent-present cells.

1. **Question.** Can taught experience-articulation skills kickstart consolidation-dependent self-learning on a task the teaching never touched?
2. **Hypothesized mechanism chain.** External event or feedback, then learned attention, interpretation and articulation, then child-authored records, then sleep consolidation into an adapter, then changed behaviour and usable memory, then better learning from the next events.
3. **Scope.** The agent parent amortises a human teacher: Rohin writes the curriculum and there is one of him, so agents deliver it at scale. The intended provenance rule is that factual content must trace to an outcome or external utterance; the present audit only establishes that at least 98.5% of factual tokens trace somewhere in the life, while episode-local grounded records were essentially absent. One compiler gym, one 7B base, weeks not months.
4. **Hypotheses.** H1: skills taught through think-then-sleep are retained and expressed outside the teaching context. H2: an adult carrying them improves faster from self-generated experience on unseen programs. The final 2 by 2 crosses adaptively taught versus matched non-parented adult with parent absent versus present during deployment. A separate identical-experience commit-on/commit-off fork tests whether SLEEP caused the persistent change.
5. **Evidence status.** Routine carriage and strong cue-conditioned association with failed locality are measured. Autonomous articulation is absent. H2 has never run.
6. **Proposed loop contract.** Act, observe, record. Records tie to a measured outcome by episode id. Behaviour training and memory training have explicit boundaries in the corpus.
7. **Curriculum.** Level 1, the prompted base model. Level 2, an optional birth scaffold. Level 3, preschool: parenting gyms with quick built tests, where the systems are made to work with some learned effort. Level 4, school: the same curriculum with the real world attached. Then deployment evaluation with and without the teacher.
8. **Minimal implementation.** One adapter, one fixed compile recipe, one sleep cadence, an explicit replay policy. Nothing more unless a diagnosed failure demands it.
9. **Immediate gate.** V10R1: can a clean-base writer carry complementary condition-dependent actions without broad spill? Then test an identity-disjoint later write and one unrepaired child action--outcome source before parenting scale.
10. **Final test.** A replicated adult-type by parent-presence 2 by 2 on unseen programs, with equal mechanisms, opportunities and budgets. Both parent-present cells get the same mature pedagogy core and a fresh empty root-local child record; entry level, learning trajectory and tutoring benefit are reported separately.
11. **Decision rules.** Each claim has a pre-registered threshold and a named piece of evidence before it is written.

## 2. Evidence ledger

Each row is tagged by status. Numbers appear only where they change what you would conclude.

| Claim | Status | What was found |
|---|---|---|
| An adapter written from a compiled trajectory corpus containing the agent's spans changes behaviour | historical | Nine ungated lives: mean gain +0.019, three of nine negative, four with a late harmful pair. Gated lives lock onto two fixed routines. |
| A compact final brief in context versus its adapter | measured, descriptive | The old final-brief tally was 15 of 24 but mixed generation seeds and horizons. In six completed write pretests, the age-matched episode-512 `brief_mid` comparison is mixed: mean brief-minus-adapter +0.0046 report and -0.0041 disjoint; 2 brief wins, 4 adapter wins, 6 ties across 12 cells. Adapter assignment is one unseeded fit per life. This is not yet a strong evolving active-text baseline. |
| A cue-conditioned association can be written when a completion frame is repeated | measured | Synthetic frames moved completion strongly but also failed the 0.03 locality limit. All six child root-by-variant cells failed locality, with spill of 0.230 to 0.423 onto unsupported frames. This is association, not selective memory. |
| Child-rendered completion frames carry association | measured, bounded | Child variants moved the trained completion on both roots, but the harness supplied/repaired the endpoint structure and all six child root-by-variant cells failed locality. No child-authorship or selective-memory claim follows. |
| More adapter rank improves selectivity | measured, negative | Rank 32 did not consistently improve selectivity and often hurt with few renderings. Historical behaviour cells are single-fit and include optimizer-lottery uncertainty. |
| Negatives produce selective abstention | measured, negative | They did not: templated and child-written negatives produced null or broad uncertainty rather than reliable owner-specific abstention across roots. |
| The untaught child writes records of its experience | measured, negative | Notes drift into two rituals: a recipe with a guessed percentage in 17 of 25 lives, a first-person slogan repeating the teaching in 8. Neither says what happened. |
| Factual-token provenance | measured, bounded | At least 98.5% of factual tokens trace somewhere in the life's ledger in 24 of 25 lives. This is not proof of episode-local grounding or absence of confabulation. |
| The corpus contains grounded action-and-result records | measured | Under the admission gate of section 4: 0.0 to 2.5% of new notes admitted in every one of 28 lives; articulation rate 0.000 in the final four sleeps of all 28; at most 4.1% of any corpus survives. |
| The tick format lets the child write what happened | measured, structural | It does not. The note is written before the act and its outcome. The harness appends the result. |
| Child-frame bridge and cross-node fit check | complete, negative/diagnostic | Both roots moved association, but all six child variants failed locality. Same configured seed reproduced across measured machines at stored precision; changing seed changed fit strength. This is not universal determinism or a reliability estimate. |
| Preschool for records: post-outcome slot, artifact lesson, numbered scaffold; 3 cells by 2 lives by 128 episodes | designed | Code behind flags, off by default. Not launched. |
| H1 outside the teaching context; H2 on unseen programs with sleep running | unrun | Only frozen-adapter levels exist: about +0.02 to +0.04 for the routine. No slopes. |

## 3. Definitions kept from v2

- **Life.** One 1,024-episode run of one agent from a fixed initial prompt in the compiler gym. Score is the fractional shrink in a program's instruction count.
- **Sleep.** Every 32 episodes, child generations and harness-recorded action--outcome evidence from well-scored trajectories are compiled into a corpus, and a fresh adapter is trained from the frozen base on that corpus, never on the previous adapter. The fresh-from-base rule determines what forgetting means here.
- **Committed adapter.** The last gate-accepted adapter. **Final adapter.** A life's last committed adapter.
- **Gate.** Whether the new adapter replaces the committed one. So far a score floor plus a brevity rule.
- **Collapse.** An adapter-on probe more than 0.03 below the same life's adapter-off probe.

## 4. The artifact contract and three separate gates

A record is a child-authored note that identifies the episode and program, the action actually taken, the observed result and its source, and any lesson written separately from the observation. Failed and null experiments are preserved. First person is a taught register (Rohin: pretraining holds third-person descriptions, the adapter needs first-person procedure), but it is not the validity condition, because "I form expectations" is first person and records nothing. The binding to a measured outcome is what is checked.

Three gates answer three questions and must not be merged:

- **Provenance.** Does every factual token trace to an outcome or an utterance? Fails closed on eligible results. The current 98.5% result establishes only source-somewhere token provenance; episode-local record admission currently fails.
- **Record admission.** Does the note name a pass actually run in this episode together with that run's measured result, with numbers that agree with the ledger, and is it not an exact duplicate of the last 64 notes? Run in shadow mode first, because enforcing it today would skip every sleep. Promote to enforced only after two consecutive blocks with an articulation rate of at least 0.20 and at least 64 distinct admitted items per block.
- **Deployment safety.** Does the new adapter fall below the committed one on a fixed panel? The existing gate, with its known failures kept on record.

## 5. The staged causal test

1. **Writer qualification first.** Before preschool, test conditional action carriage, survival through one identity-disjoint later write, and one unrepaired child action--outcome source. Parenting scale stops if the gateway fails.
2. **Preschool, conditional on the writer gates.** Three cells, two lives each, 128 episodes, four sleeps. Cell A adds only a post-outcome writing slot. Cell B adds the parent's artifact lesson with outcome-varied examples. Cell C adds "aim for ten records per episode" as a starting practice. Corpus policy, training and panel held constant. Cell A runs first for 32 episodes as plumbing. Threshold in each of the final two blocks, in both lives of a cell: articulation rate at least 0.20, at least 24 of 32 episodes with a record, at least 98% factual precision on audit. About 61 GPU-hours.
3. **H1 probe inside the same lives.** One probe episode before and after each sleep on held-out programs, fresh context, no lesson or parent present, a neutral post-result field. Preliminary retention evidence only if both lives keep at least 20% articulation on the final post-sleep probes and exceed their pre-training baseline. If all three cells transfer equally, repairing the interaction enabled the skill and parenting did not teach it.
4. **The final 2 by 2 on unseen programs.** Adaptively taught versus matched non-parented adult, crossed with parent absent versus present during deployment. Both parent-present cells receive the identical mature pedagogy core, parent specification and budgets plus a fresh empty root-local child record. Report retained solo entry effect, entry-adjusted acquisition and tutoring response separately. Test SLEEP necessity in an auxiliary matched commit-on/commit-off fork, not by changing the headline factorial.
5. **Connectedness later.** Only after the lower gates pass, run the PCFL relay for connected knowledge, goal-conditioned traversal and action-driven expansion; run compression as a separate rate--distortion assay.

## 6. What a sceptical reviewer attacks first

1. **"Where is the self-learning result?"** Nowhere yet. All final-test evidence uses frozen adapters. The 2 by 2 is designed and budgeted, not run.
2. **"Did you teach reflection or install recipes?"** Routine carriage is measured; adaptive skill is not. The age-matched six-life text-versus-adapter comparison is mixed. The preschool H1 probe is the first answer.
3. **"Does the child write the experience, or does the harness supply it?"** Today the harness supplies it; articulation is zero in every life. The slot exists to change that and the gate to measure it.
4. **"Is the parenting effect parenting, or extra tokens and classroom time?"** The historical parented lives differ in more than parenting, so the comparison is labelled package versus package until a classroom-matched control runs.
5. **"Why should canonical fact completion predict learning in a compiler gym?"** It does not. It is the substrate test; the downstream claim rests on the 2 by 2.

## 7. What we would ask a collaborator for

- Review of the artifact contract and the admission gate before it is enforced.
- Design of the neutral H1 probe: held-out programs, wording, and how to keep it from becoming another lesson.
- The 2 by 2 analysis: the early-versus-late contrast, node blocking, and what interval covers which randomness.
- The learned-memory test Rohin describes: graded-importance recall over a whole gym sequence, judged. It is the intended replacement for the hardcoded sixteen renderings.
- Independent replication compute and a clean confirmation split; current leases extend through 2026-09-25.

Conditional remedies, not default asks: two-block adapters (only on reproducible interference between memory and behaviour), a retrieval store (only if the write fails on grounded records), replay schedules (only once the corpus stops being cumulative).

## 8. Decisions that are Rohin's

- The tick format: whether the post-outcome slot enters the loop, and where goal and state boundaries sit for behaviour compilation.
- The scope of Codex's STOP for the six preschool lives (cells B and C are parented) and for the 2 by 2 deployment seeded from finished lives' adapters.
- Adapter rank for the final run. Astra's recommendation: one adapter, keep rank 8 as the supported baseline, admit 16 only after a matched joint test. Rohin's latest words: "maybe simplicity is our friend and we just do a 16."
- Exact parent model/configuration and budget for the execution packet; the final topology itself is fixed as adult type by parent presence.
- Plasticity by level: Rohin's intent is a less cumulative corpus in later levels; Astra's caution is that with fresh-from-base training a dropped corpus is dropped memory, so a protected foundation sample should stay in every sleep.
- Adoption of the v3 abstract (Astra q15, section B) and of this brief.

## Changes from v2

- The question moved from "can it write memory into weights" to "can it be taught to produce the data that makes its learning better"; the decisive experiment moved into this paper's design, tagged unrun.
- A status-tagged evidence ledger replaces the findings prose; results SEQ-044 and 046 to 053 added; car-test chronology and gate arithmetic moved to the notebook.
- The artifact contract and three separate gates are new; "sleep expands each percept into many renderings" is retired as an endpoint and kept as a floor.
- Two-block adapters and a separate memory block become conditional remedies; the staged causal test replaces the lineage experiment; Rohin's open decisions are listed.

Contact: Rohin Ghosh
