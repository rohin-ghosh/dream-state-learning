# Can an agent be taught to turn its own experience into training data that makes its later learning better? Collaborator brief (v3 DRAFT, 2026-09-12)

**DRAFT for Rohin's review; v2 stands until he adopts this.** Sources, in reading order: Rohin's own words (`research_notes/THESIS_RAW_ROHIN_2026-09-11.md`, which wins wherever a paraphrase differs), the thesis note (`THESIS_v2_SELF_LEARNING_FLYWHEEL.md`), Astra memo q15, and the notebook (`research_loop/COORDINATION.md`, entries SEQ-nnn).

## 1. The question and the spine

The question is not whether a small model can be trained on its own text. Post-training already changes behaviour and stores facts. The question is whether an agent can be **taught the disposition to turn externally grounded experience into good post-training data about itself**, so that every episode, every parent's correction and every environment outcome flows through its own thinking into weight changes at sleep, and its later learning gets better because of it. In Rohin's words: "everything it thinks turns into post-trainable data... that is the behavior that allows self learning. That is this entire paper." Childhood parenting builds this flywheel. Deployment removes the teacher, not the loop.

1. **Question.** Can taught experience-articulation skills kickstart consolidation-dependent self-learning on a task the teaching never touched?
2. **Mechanism chain.** External event or feedback, then learned attention, interpretation and articulation, then child-authored records, then sleep consolidation into an adapter, then changed behaviour and usable memory, then better learning from the next events.
3. **Scope.** The agent parent amortises a human teacher: Rohin writes the curriculum and there is one of him, so agents deliver it at scale. The model distills but does not originate: every factual item traces to an outcome or an external utterance, which is the defence against the self-distillation and collapse objection. One compiler gym, one 7B base, weeks not months.
4. **Hypotheses.** H1: skills taught through think-then-sleep are retained in the adapter and expressed outside the teaching context. H2: an agent carrying them improves faster from self-generated experience on unseen programs, and the advantage depends on continued consolidation. The test is a 2 by 2, parented or not by sleep running or frozen at deployment. H1 is the parenting effect with sleep frozen. H2 is the interaction: slope, not starting level.
5. **Evidence status.** Routine retention and controlled fact storage are measured. Autonomous articulation is absent. H2 has never run.
6. **Loop contract.** Act, observe, record. Records tie to a measured outcome by episode id. Behaviour training and memory training have explicit boundaries in the corpus.
7. **Curriculum.** Level 1, the prompted base model. Level 2, an optional birth scaffold. Level 3, preschool: parenting gyms with quick built tests, where the systems are made to work with some learned effort. Level 4, school: the same curriculum with the real world attached. Then deployment without the teacher.
8. **Minimal implementation.** One adapter, one fixed compile recipe, one sleep cadence, an explicit replay policy. Nothing more unless a diagnosed failure demands it.
9. **Immediate gate.** A post-outcome writing slot, an artifact lesson, a numbered scaffold. Measure the articulation rate before enforcing any filter.
10. **Final test.** A replicated 2 by 2 on unseen programs, equal scaffolds and budgets, parents removed in all deployment arms (Rohin has said "maybe no parent"; this is his call, see section 8), entry level and learning trajectory reported separately.
11. **Decision rules.** Each claim has a pre-registered threshold and a named piece of evidence before it is written.

## 2. Evidence ledger

Each row is tagged by status. Numbers appear only where they change what you would conclude.

| Claim | Status | What was found |
|---|---|---|
| An adapter written from the agent's own spans changes behaviour | historical | Nine ungated lives: mean gain +0.019, three of nine negative, four with a late harmful pair. Gated lives lock onto two fixed routines. |
| The agent's own written brief in context matches or beats its adapter | measured | 15 of 24 lives. Memory in text is at least as good as memory in weights so far. |
| A fact can be written into the adapter when rendered in many forms and retrieved by completing a canonical sentence | measured | Sixteen synthetic renderings per occurrence: completion 0.24 to 0.91, owner-specific on all three banks. Spill onto look-alike owners 0.3 to 0.5, unsolved. |
| The child's own renderings store nearly as well as templates when it writes the recall sentence itself | measured | 0.82 versus 0.91 completion, paired gaps 0.05, 0.22 and 0.01 by bank. Its prose restates the fact in 78% of lines when it must end with the sentence, 26% when the harness appends it. |
| More adapter rank helps memory | measured, negative | Rank 32 never helped over six banks and hurt whenever renderings were few. Rank 8 carries the behavioural routine in every life tested. |
| Negatives produce abstention | measured, negative | Templated negatives: none. Child-written negatives: selective on one bank, an unselective habit on two. |
| The untaught child writes records of its experience | measured, negative | Notes drift into two rituals: a recipe with a guessed percentage in 17 of 25 lives, a first-person slogan repeating the teaching in 8. Neither says what happened. |
| The child invents facts | measured, negative | Factual tokens trace to the life's own ledger in at least 98.5% of cases in 24 of 25 lives. It repeats; it does not confabulate. |
| The corpus contains grounded action-and-result records | measured | Under the admission gate of section 4: 0.0 to 2.5% of new notes admitted in every one of 28 lives; articulation rate 0.000 in the final four sleeps of all 28; at most 4% of any corpus survives. |
| The tick format lets the child write what happened | measured, structural | It does not. The note is written before the act and its outcome. The harness appends the result. |
| Six more bridge banks, a taught perception variant, a cross-node check | running | Nine-bank pool due within hours. |
| Preschool for records: post-outcome slot, artifact lesson, numbered scaffold; 3 cells by 2 lives by 128 episodes | designed | Code behind flags, off by default. Not launched. |
| H1 outside the teaching context; H2 on unseen programs with sleep running | unrun | Only frozen-adapter levels exist: about +0.02 to +0.04 for the routine. No slopes. |

## 3. Definitions kept from v2

- **Life.** One 1,024-episode run of one agent from a fixed initial prompt in the compiler gym. Score is the fractional shrink in a program's instruction count.
- **Sleep.** Every 32 episodes, the agent's own spans from well-scored episodes are compiled into a corpus, and a fresh adapter is trained from the frozen base on that corpus, never on the previous adapter. The fresh-from-base rule determines what forgetting means here.
- **Committed adapter.** The last gate-accepted adapter. **Final adapter.** A life's last committed adapter.
- **Gate.** Whether the new adapter replaces the committed one. So far a score floor plus a brevity rule.
- **Collapse.** An adapter-on probe more than 0.03 below the same life's adapter-off probe.

## 4. The artifact contract and three separate gates

A record is a child-authored note that identifies the episode and program, the action actually taken, the observed result and its source, and any lesson written separately from the observation. Failed and null experiments are preserved. First person is a taught register (Rohin: pretraining holds third-person descriptions, the adapter needs first-person procedure), but it is not the validity condition, because "I form expectations" is first person and records nothing. The binding to a measured outcome is what is checked.

Three gates answer three questions and must not be merged:

- **Provenance.** Does every factual token trace to an outcome or an utterance? Fails closed on eligible results. Currently passes at 98.5% or better.
- **Record admission.** Does the note name a pass actually run in this episode together with that run's measured result, with numbers that agree with the ledger, and is it not an exact duplicate of the last 64 notes? Run in shadow mode first, because enforcing it today would skip every sleep. Promote to enforced only after two consecutive blocks with an articulation rate of at least 0.20 and at least 64 distinct admitted items per block.
- **Deployment safety.** Does the new adapter fall below the committed one on a fixed panel? The existing gate, with its known failures kept on record.

## 5. The staged causal test

1. **Preschool, three cells, two lives each, 128 episodes, four sleeps.** Cell A adds only a post-outcome writing slot. Cell B adds the parent's artifact lesson with outcome-varied examples. Cell C adds "aim for ten records per episode" as a starting practice. Corpus policy, training and panel held constant. Cell A runs first for 32 episodes as plumbing. Threshold in each of the final two blocks, in both lives of a cell: articulation rate at least 0.20, at least 24 of 32 episodes with a record, at least 98% factual precision on audit. About 61 GPU-hours.
2. **H1 probe inside the same lives.** One probe episode before and after each sleep on held-out programs, fresh context, no lesson or parent present, a neutral post-result field. Preliminary retention evidence only if both lives keep at least 20% articulation on the final post-sleep probes and exceed their pre-training baseline. If all three cells transfer equally, repairing the interaction enabled the skill and parenting did not teach it.
3. **The 2 by 2 on unseen programs.** Parented package versus plain package, sleep running versus frozen, three matched blocks each on one node. Pre-registered contrast: late visits (15 to 21) minus early visits (1 to 7), averaged over the 12 programs, then running minus frozen, then parented minus plain. Frozen means no weight change with every other persistent state matched. Minimum detectable interaction with three blocks is about 0.06 score units, not 0.02. About 223 GPU-hours.
4. **Bridge confirmation, running.** Non-inferiority of the taught child's storage to synthetic templates within 0.05 completion, one-sided, on six fresh banks; the seed-0 banks are exploratory.

## 6. What a sceptical reviewer attacks first

1. **"Where is the self-learning result?"** Nowhere yet. All final-test evidence uses frozen adapters. The 2 by 2 is designed and budgeted, not run.
2. **"Did you teach reflection or install recipes?"** Routine retention is measured; adaptive skill is not. The text brief matches the adapter in 15 of 24 lives. The preschool H1 probe is the first answer.
3. **"Does the child write the experience, or does the harness supply it?"** Today the harness supplies it; articulation is zero in every life. The slot exists to change that and the gate to measure it.
4. **"Is the parenting effect parenting, or extra tokens and classroom time?"** The historical parented lives differ in more than parenting, so the comparison is labelled package versus package until a classroom-matched control runs.
5. **"Why should canonical fact completion predict learning in a compiler gym?"** It does not. It is the substrate test; the downstream claim rests on the 2 by 2.

## 7. What we would ask a collaborator for

- Review of the artifact contract and the admission gate before it is enforced.
- Design of the neutral H1 probe: held-out programs, wording, and how to keep it from becoming another lesson.
- The 2 by 2 analysis: the early-versus-late contrast, node blocking, and what interval covers which randomness.
- The learned-memory test Rohin describes: graded-importance recall over a whole gym sequence, judged. It is the intended replacement for the hardcoded sixteen renderings.
- Compute after 2026-09-18.

Conditional remedies, not default asks: two-block adapters (only on reproducible interference between memory and behaviour), a retrieval store (only if the write fails on grounded records), replay schedules (only once the corpus stops being cumulative).

## 8. Decisions that are Rohin's

- The tick format: whether the post-outcome slot enters the loop, and where goal and state boundaries sit for behaviour compilation.
- The scope of Codex's STOP for the six preschool lives (cells B and C are parented) and for the 2 by 2 deployment seeded from finished lives' adapters.
- Adapter rank for the final run. Astra's recommendation: one adapter, keep rank 8 as the supported baseline, admit 16 only after a matched joint test. Rohin's latest words: "maybe simplicity is our friend and we just do a 16."
- Whether the deployment arms carry a behaviour-only parent or none.
- Plasticity by level: Rohin's intent is a less cumulative corpus in later levels; Astra's caution is that with fresh-from-base training a dropped corpus is dropped memory, so a protected foundation sample should stay in every sleep.
- Adoption of the v3 abstract (Astra q15, section B) and of this brief.

## Changes from v2

- The question moved from "can it write memory into weights" to "can it be taught to produce the data that makes its learning better"; the decisive experiment moved into this paper's design, tagged unrun.
- A status-tagged evidence ledger replaces the findings prose; results SEQ-044 and 046 to 053 added; car-test chronology and gate arithmetic moved to the notebook.
- The artifact contract and three separate gates are new; "sleep expands each percept into many renderings" is retired as an endpoint and kept as a floor.
- Two-block adapters and a separate memory block become conditional remedies; the staged causal test replaces the lineage experiment; Rohin's open decisions are listed.

Contact: Rohin Ghosh
