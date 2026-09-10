# Experience Models — one-page abstract for onboarding (2026-09-10)

**Claim in one sentence.** A frozen language model plus a small per-life adapter can turn lived experience into better future action: the agent thinks in a loop, its sleep compiles its own successful thinking into the adapter, and a parent teaches it how to think while it grows.

## The system, in three mechanisms
- **THINK** — the loop. The agent lives in a stream of thought with a few markers (PREDICT a score, ACT, NOTE to itself, RECALL its past). Every step is recorded in an append-only ledger. It plays real tasks: CompilerGym (choose LLVM passes to shrink real programs; scored on programs it has never seen) and a rule-induction game used for teaching.
- **DREAM** — context management. Notes persist at the head of context; the rest fades; a brief written at sleep becomes the next wake's opening. Kept deliberately simple.
- **SLEEP** — the write. Every 32 episodes the agent's own successful continuations (in its own dialect, paraphrased and replay-mixed) are compiled into a corpus and trained into a rank-8 LoRA from the clean base. A write is committed only if it passes a format canary, a score gate (it must not trail the base model or the adapter it replaces), and a behaviour gate (it must not make the agent give up early).
- **PARENTING** — a stronger model (14B or 32B) watches the child, never gives answers (leak-scanned), and prescribes better thinking patterns when the child's thinking becomes repetitive. The child is asked to restate the lesson in its own words every episode so the lesson enters its own thoughts, which is what sleep writes. The parent's weights never learn; the child's do.

## What has been measured (cell counts, not stories)
- The write changes behaviour every time and is now safe: ungated children collapsed late in life in 3 of 9 lives; gated children have 0 collapses in 60 checkpoints across 7 lives, and the gate has caught collapses before commit (e.g. a candidate at 27% vs the child's 53%).
- The gain is real but modest: gated children run 2–5 points above the plain model on held-out programs (noise floor ~1 point).
- Big one-shot writes hurt (12k rows, both ranks below base); small frequent writes help. Rank 8 vs 16 makes no difference.
- Children listen in context: they restate the parent's lesson before 50–100% of episodes; no parented child has collapsed. But the habit (same recipe, same sentence) returns within ~2 sleeps: the write amplifies whatever the child does most.
- Thinking ritualizes at 160–224 episodes in 8 of 9 unparented children and stays; parented children ritualize later (256–288) but not never.
- Storage ≠ extraction: the adapter makes the child's own past text ~20× likelier while moving behaviour ~2 points — the Allen-Zhu & Li gap in our units.

## What we are testing next
- **Bootstrap (pretrain the adapter):** install the habit of making and revising rules before birth, from a target-blind schooling corpus (rule-game classrooms; the child asking itself how much to think, what to test, when to stop and review). Arms: none / bootstrap / parent / both, matched seeds. Test: unprompted plan/review text in the first 64 episodes and later ritual onset.
- **Scale thinking:** more thought per situation, parallel branches of thought merged by the child, no end token (idle thought becomes experience).
- **Finals:** {finalized adult, regular agent} × {long unsupervised gym, parented gym}, judged on the 7-day horizon.

## Positioning
Not "continual learning" (labs do that) and not RAG. The looped transformer recurs in activations, chain-of-thought recurs in tokens, this system recurs in weights: expensive to write, lasts indefinitely, and inspectable because it dreams in text. The bet is prospective, action-oriented, experiential intelligence: the model edits its weights by thinking; sleep is the commit.

Contacts: Rohin Ghosh (lead). Working notes: `research_notes/IDEAS.md`; measurements: `research_loop/COORDINATION.md`; certification: `research_notes/certification_report_draft.md`.
