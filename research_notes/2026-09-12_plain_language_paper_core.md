# Dream--LoRA--Think: the paper in plain language

Date: 2026-09-12

This is a communication map, not a new experiment or authorization.

## The idea

We start with a strong pretrained model that can already reason and use tools,
but cannot personally change from what happens after deployment. We give one
copy a small private set of learnable weights (a LoRA) and ask whether its own
life can make those weights useful.

The agent has only three operations:

1. **THINK:** reason, choose an action, observe the real result, and continue.
2. **DREAM:** when active context becomes crowded, rewrite the current goal,
   beliefs, open questions, plan, and useful experiences into a smaller state.
3. **SLEEP:** offline, turn grounded experiences and child-authored
   connections into training examples, replay older material, write a new
   LoRA, and keep it only if the agent still works correctly.

Parenting is input to this organism, not a fourth mechanism. A strong teacher
helps the child notice process mistakes and practice better thinking in a
target-blind classroom. The teacher disappears before the final environment.

## What must be proved

### 1. The writer works selectively

If one situation taught the child to choose action A and another taught it to
choose action B, the LoRA must produce A only in the first situation and B only
in the second. It cannot pass by learning “always say A,” forgetting how to
act, or merely repeating training wording.

This is the current bottleneck. We now know the plain frozen model can express
the intended interface perfectly when one correct row is shown: `64/64`
ordinary outputs and `64/64` scored choices, with every reversed row reversing
the action. That was a zero-training surface check. We still have to train four
fresh LoRAs and show that the relation is stored without turning into a broad
habit.

### 2. One full life cycle works

The child takes actions and sees outcomes. Before it knows the later test, it
identifies which experiences connect. SLEEP writes both the grounded events
and that connection. Later, a goal makes it traverse the remembered connection
and choose an informative experiment. The experiment produces a new outcome;
a second SLEEP adds it. A final task can be solved only by using one old
connection and the newly learned fact together.

The current design uses three first-sleep versions to isolate the causes:

- **FULL:** truthful experiences plus the child's real connection.
- **WRONG SOURCE BINDING:** the same material and connection, but selected old
  action--outcome bindings are deranged.
- **WRONG DREAM CONNECTION:** truthful experiences, but evidence-matched wrong
  connections replace the child's organization.

FULL must succeed; the two controls must differ only at the stage their
missing ingredient should affect. The first exact version failed that test and
was discarded before training. In v2, one child tries both actions four times
in the same opaque situation; the truthful experience has a 3-to-1 outcome
preference while the source control preserves every action and total outcome
but makes both actions 2-to-2. For DREAM, all eight possible connections look
identical from their endpoints and frequency; only the child's earlier
joint-versus-single-component experiments reveal the useful two. A wrong-
connection control preserves the same number and shape of memories.

Only after those first-sleep tests pass do we pay for three second-sleep
writes: one for each of two truthful possible outcomes and one equal-work
old-memory-plus-pad control. The final task needs both an old connection and
the new outcome memory. V3 repaired the earlier causal outline but two fresh
reviewers found more exactness gaps before any fit: matched conditions used
different optimizer randomness; the formal reader allowed impossible bypass
returns; public, scorer, compiler, and audit information was not separated in
complete schemas; and the live experiment bridge, wrong-root control, PAD
equality, and side-channel behavior were not executable enough to audit. V4
is repairing those on CPU and adds no trained arm. One important limit remains
deliberate: the public experiments themselves tell a competent solver which
pair is useful, so this can show the child selected and sealed evidence-
indicated connections, not that it invented an organization algorithm. If the
repaired contract closes, this is a compact experiment of THINK, DREAM, and
two SLEEP writes together rather than storage alone.

### 3. Learning improves a life, not just one probe

Raise fresh children in matched pairs:

- one receives useful adaptive parenting;
- one receives no teacher, while otherwise receiving the same tasks, child
  thinking budget, action opportunities, SLEEP policy, and saved ages.

Before that expensive comparison, each candidate lesson is tested cheaply
against both a token-matched plausible sham lesson and no teacher. The lesson
must improve useful action, and the sham must not be harmful. Sham qualifies
teaching material; it is not the final regular-agent childhood.

After childhood, delete both teachers and all classroom text. Fork each adult:

- **RUN:** SLEEP continues writing during deployment;
- **FROZEN:** it sees the same life and performs shadow sleeps, but new weights
  are never mounted.

Also run **P-TEXT**, where the parented adult's LoRA stays frozen while a strong
text memory evolves. This asks whether parametric personal learning adds value
beyond a good ordinary memory system.

The headline is not “the parented child starts better.” It is:

> Does continuing SLEEP help the parented adult more than it helps the matched
> control adult, and does the running parented adult keep improving while
> retaining earlier abilities and beating the qualified text-memory system?

## What the current evidence says

- **Real positive:** on mini-Sudoku, useful correct material beat corrupted
  material in all three adapter-training seeds. LoRA can carry behaviorally
  useful content.
- **Writer problem:** lower learning rate did not remove broad spill. Masking
  prompt tokens reduced spill but also erased learning. A penalty that asks
  the new LoRA to stay close to the frozen model cut unwanted spill by 91%,
  but did so by almost turning the intended learning off. Selective writing
  is still unproved; the next test changes the semantic structure of what is
  written instead of merely weakening the update. That test is running, but a
  fresh review found its spill score can miss some broad changes, and another
  check proved one gain threshold is impossible for almost half the cells
  because the base starts too close to the ceiling. Its first result is
  diagnostic until both scores are repaired.
- **Parenting problem:** the first fitted lesson and sham both hurt. A later
  visible process card changed formatting but did not improve solves over sham
  (`1/16` each). A fresh same-episode correction test also tied: both process
  and sham went from `1/32` solves before feedback to `2/32` afterward. The
  correction plumbing works, but no teaching method has yet earned a clean
  childhood run.
- **Lifetime evidence:** historical runs contain encouraging sustained gains
  in two lives and a severe interface collapse in one, but they are development
  evidence, not a valid final comparison.

## The honest paper claim if everything passes

In one finite benchmark, an agent used its own action outcomes to build useful
connected parametric memory, used that memory to choose a new experiment,
added the result through a later sleep, and improved subsequent action over a
longer life. A target-blind childhood increased the later value of this
learning loop after the teacher was removed, relative to a matched child and a
strong evolving-text memory baseline.

That would not prove sentience, universal continual learning, solved
parenting, arbitrary open-world graph learning, or indefinite improvement.

## The execution order

1. Qualify the selective writer.
2. Check one old-plus-new coexistence write.
3. Run the cheap two-root mechanism kill test; scale only if every causal seam
   behaves correctly.
4. Qualify one lesson that improves a real visible action before fitting it.
5. Raise clean children, delete the classroom, and run the lifetime branches.
6. Measure semantic compression only after connected utility works.
