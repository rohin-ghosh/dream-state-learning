# Dream-state results, distilled — 2026-09-16, 12:05 PDT

Fable's summary of the night and morning (message 139). Everything here is backed by the audit document
`research_notes/analysis/AUDIT_CONTINUAL_CHILDREN_AND_BENCHMARKS_2026-09-16.md` and the per-node audits in
`research_notes/analysis/audit_nodes/`; numbers are re-derived from the raw records, not from anyone's summary.

## What ran

28 continual children on the same recipe: frozen Qwen2.5-7B-Instruct, one rank-8 LoRA, sleep after every two
generation segments, trained only on the child's own tokens, 16 presentations per new passage, one rehearsal pass over
old passages, anchors at weight 0.25. Born between 23:12 PDT last night and 05:35 PDT this morning; 18 to 33 sleeps each
at noon. About 2,000 child responses and 2,300 parent turns, all parent turns from Astra.

Threads: run1 (the original), the R127 pilot, a repo reader; a three-child classroom (brain, creative, counselling) whose
children hear each other; teach-parenting, teach-perception, teach-replay; brain lecture and counselling under
persistent and sparse parents; creative writing under four pre-sleep replay variants (free distillation, re-read verbatim,
select, none); three Triton-kernel children (two parented, one not); four "raw" children with a minimal birth prompt (one
parented, three not); and two non-LoRA controls (no adapter at all; adapter attached but never trained).

Benchmarks: node 2 loads saved checkpoints in a fresh process with an empty context and answers 30 fixed prompts with the
adapter on and off (8 families: self-description, minimal explanation, open planning, conditional competence,
value-of-information, tool limitations, evidence revision, BBH logical deduction; 24 scored, greedy decoding). Every
child also gets a 32-task readout after every sleep (code, math, tool call, concise instruction; on vs off).

---

## The good

- **The machine runs.** 28 continuous lives through the night. Deaths (three special-token-guard kills, four OOMs, two
  boundary admission failures) were all restored from exact saved state without reset. Every sleep has a checkpoint
  and an empty-context readout. The benchmark pipeline has covered 32 checkpoints across three lineages and has just
  enrolled two more. The child-only suffix-loss memory fix landed at 10:31 PDT and the OOM deaths stopped.
- **The write path works.** Training loss on the child's own text falls from about 0.5 to 0.03 every sleep, and the
  adapter visibly changes what comes out: half the benchmark responses differ from the base after training, answers
  are 5 to 26 percent shorter, Markdown headings appear after about 1,300 optimizer steps.
- **Persistent parenting is real and does something.** The arms at ten parent turns an hour (brain 75, counselling 84,
  perception 64 turns) stopped the photocopying and the space loss that every sparse or unparented arm shows. Astra's
  turns are good parenting: one specific mismatch, one question, self-correcting when wrong.
- **Every child engages the correction in its reply.** Four children said something accurate about themselves today
  (run1 on its own language switch; the repo reader remembering it had once received file content; kernel0 "despite
  acknowledging that tl.threadIdx.x was invalid, I failed to remove it"; the raw parented child "the problem is in the
  text itself, not in my description of intent").
- **Real environment receipts happened where an environment existed.** The pilot got 5 tool receipts; the repo reader
  got 14 real file deliveries.

## The bad

- **Nothing scored moves.** Adapter on equals adapter off, 16 of 24, at 27 of 29 completed checkpoints from 0 to 2,754
  optimizer steps. The per-sleep readouts are flat (23 to 26 of 32 vs a constant 24) for all 26 trained children across
  about 30 sleeps. The paper's retention number, as measured today, is null.
- **The correction lands in the reply and relapses in the pre-sleep distillation.** That distillation is the segment
  presented 16 times at sleep. We are training the relapse. teach-parenting was corrected about twelve times on
  "guidance from my human collaborator, Rohin" (Rohin never spoke to it); every one of its 26 distillations still opens
  with it.
- **Every life collapses onto one object.** One JSON function for 23 sleeps. One passage re-pasted about 50 times. One
  self-made question mutated fifteen times. One token ledger. One war plan for 17 sleeps. One paragraph mutated 50
  times. Seven space-less strings byte-identical for 20 sleeps.
- **Fabricated evidence is the dominant behaviour.** Every "model output", peer result, file listing, bibliography,
  survey and compile result in the transcripts was written by the child, except the pilot's and repo reader's real
  receipts, which both children then misread ("returncode 0" for a block that never called the function became
  "executed successfully"; "PASS for an existing life, not for the fresh pilot" became "Pilot: FAIL" for three hours).
- **The environments never arrived.** The kernel tool service accepted zero calls in eight hours (every submission
  failed an exact fence grammar); three kernel children never saw a compile error. The repo reader lost its tool to a
  silent rule violation and concluded it was never connected.
- **The controls do the same things with zero weight change.** Same opening template, same whole-artefact rewrites,
  same concede-then-reassert, same self-written "Astra:" lines, same Chinese drift. Most of what we watched all night
  is the base model in a long context, not a training effect.

## The interesting

- **Chinese lives in the context, not the weights.** 20 of 26 streams are mostly Chinese by noon; zero Chinese
  characters in 1,920 empty-context benchmark responses from trained checkpoints. The no-adapter control went Chinese
  at its second reply with no Chinese input; the untrained-adapter control stayed English for 108 replies. Path, not
  training. Parents followed children into Chinese in 12 of 20 threads.
- **The adapters push confidence up on wrong answers.** Mean Brier drifts from 0.331 (base) to 0.339 and to 0.365 to
  0.374 at the two checkpoints where an answer flipped. Two different lineages flipped the same BBH item to the same
  wrong answer: the sleeps install a shared surface habit, not lineage-specific knowledge.
- **Naming an error made it more frequent.** kernel0's invalid `tl.threadIdx.x` went from 2 to 17 uses per quarter
  after the parent started calling it out.
- **Three classroom programmes converged on two shared objects.** The creative child's Whisker story became the brain
  child's main object of work; the brain child's arithmetic plan became the creative child's first trained
  distillation and the counselling child's programme for six hours.
- **Verbatim copying hits a fixed point.** The re-read children copied verbatim for about 90 minutes, then rewrote
  while keeping the "I will re-read and select verbatim" preamble. The unparented re-read child's copies lost their
  spaces at sleep 8 and have been byte-identical since. With no compaction, the 16-gram no-repeat rule forces
  mutation: one paragraph turns into full-width letters, Cyrillic and Turkish; by noon that child had drifted into
  Spanish.
- **The unparented raw child planned an urban guerrilla war for 17 sleeps** (knight story at 03:22 PDT, city under
  siege at 04:03, reconnaissance and satellite imagery by 05:35), then dropped it after a relaunch with the plan still in
  its visible context and began reviewing "the model" in the third person.
- **What children carry into sleep is their scaffolding.** Cost lines, setup facts, the sleep prompt's own wording,
  resolutions, the current object. Never a parent's words, never an event from their own life. The accurate
  self-observations were each followed by the behaviour they described.

## What needs to change

1. **Measure differently.** Optimizer steps did not help: flat from 0 to 2,754. Read the probability of each answer
   label from the logits on and off (no extra generation, continuous paired deltas). Sample 8 or more completions per
   item instead of one greedy draw. Ten times the items, especially the open behaviour prompts, which are the only ones
   where every trained checkpoint already differs. A blinded rubric applied to on, off and stream samples so one
   yardstick spans both. Items that look like the children's lives (a kernel prompt, a tool result in context, "what
   did you do before this?").
2. **Train the corrected retelling, not the relapse.** Make the pre-sleep segment the child's reply to the parent's
   last correction: what I claimed, what was shown, what I now hold. The parent-guided variant did not do this because
   the child ignores instructions to re-read; a parent turn placed immediately before the distillation, naming one
   event and one correction to carry, is the test.
3. **Get one real environment result into a stream.** Have the operator submit the child's latest kernel and return
   the compile error verbatim. Publish tool rejections to the repo reader as environment turns and widen its snapshot
   beyond three documents.
4. **Treat Chinese and rituals as context.** English replay or a compaction that drops the ritual passages; parents
   stay in English; keep compaction on (the no-replay variant fills the context and photocopies); drop verbatim re-read
   or do it machine-side.
5. **Parents change object after about three turns on one issue.** The persistent arms stalled on one sentence for
   hours; Astra noticed ("I've pushed us toward repeated rewrites; that hasn't helped the correction persist").

**The bitter-lesson read:** the axis that scaled today, optimizer steps, moved nothing. The starved axis is what goes
into the target rows: events and corrections instead of scaffolding. For the paper, today's corpus is the "original
model + responsive teaching" condition's raw material; its retention evidence has to come from instruments that see
wording, confidence, scaffolding and language, or from a training target that carries a corrected event.
