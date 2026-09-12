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

This is the current bottleneck. We know correct training material can improve
behavior at small scale, but the older writer often installs broad habits.

### 2. One full life cycle works

The child takes actions and sees outcomes. Before it knows the later test, it
identifies which experiences connect. SLEEP writes both the grounded events
and that connection. Later, a goal makes it traverse the remembered connection
and choose an informative experiment. The experiment produces a new outcome;
a second SLEEP adds it. A final task can be solved only by using one old
connection and the newly learned fact together.

Three trained versions isolate the causes:

- **FULL:** truthful experiences plus the child's real connection.
- **WRONG SOURCE BINDING:** the same material and connection, but two old
  action--outcome bindings are swapped.
- **NO DREAM CONNECTION:** truthful experiences, but the connection slots are
  empty.

FULL must succeed; the two controls must fail only at the stages their missing
ingredient should affect. This is the smallest experiment that tests THINK,
DREAM, and two SLEEP writes together rather than testing storage alone.

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
  prompt tokens reduced spill but also erased learning. Selective writing is
  still unproved.
- **Parenting problem:** the first fitted lesson and sham both hurt. A later
  visible process card changed formatting but did not improve solves over sham
  (`1/16` each). No teaching method has yet earned a clean childhood run.
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
