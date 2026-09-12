# Paper-path reconciliation: deadline evidence and full closure

Date: 2026-09-11

Status: independent evidence/claim reconciliation only. This note authorizes no
implementation, model or tokenizer call, training, GPU use, parenting, C11
work, scientific release, or submission.

## Bottom line

The full objective remains coherent, but it is not one experiment and it is
not supportable by CompilerGym alone. It decomposes into five causal questions:

1. Can a weight writer carry grounded, conditional experience without turning
   it into a global habit?
2. Can parenting cause the child to produce the useful experience artifacts
   the writer needs, and does that survive parent removal?
3. Can the resulting memory represent connections, traverse different paths
   under different goals, and expand after an informative action?
4. Does this repeated process keep improving after a strong evolving text
   memory reaches a prospective plateau?
5. Is any representation actually compressed at preserved utility?

The strongest scientifically coherent paper available by the current
September 18 abstract deadline is therefore **a longitudinal characterization
of the experience-writing bottleneck**, framed by the self-learning flywheel
but not claiming that the flywheel already works. The current paper already
has enough material for this: long per-life experiments, paired adapter
removal, a disjoint panel, writer interventions, a text-memory comparison,
controlled memory-injection assays, and unusually well-resolved failures.

The clean thesis is:

> Periodic low-rank self-training can strongly absorb repeated model outputs
> and transport simple routines, but the tested learner does not naturally
> turn action--outcome experience into conditional, reusable personal
> knowledge. The limiting chain is articulation, binding, selective access,
> and safe repeated writing—not training loss or adapter rank alone.

This preserves the full Dream--LoRA--Think programme as the target and makes
the present paper its first empirical result rather than pretending a missing
H2 or PCFL result exists.

## Why this is the deadline-safe paper

The current evidence supports all of the following, with explicit limits:

- In nine ungated 1,024-episode CompilerGym lives, the historical writer
  sometimes helped early and sometimes caused late harm; the full-life mean is
  modest and the useful behavior is dominated by supplied routines.
- Across the disjoint re-probe, the positive cells overwhelmingly reproduce a
  fixed routine rather than program-conditioned choice. The gate catches some
  failures but is neither causal evidence nor a complete safety mechanism.
- In the registered three-life writer comparison, only the legacy routine
  writer is positive on both panels in all three lives. QA-style variants
  damage the native action interface.
- The 24-life descriptive text audit favors or ties the child's brief in 15
  lives. In the stronger nine-life common-random 2x2, text is near neutral and
  the final adapter is harmful on average. This does not prove text memory is
  generally superior, but it prevents a parametric-memory superiority claim.
- Controlled completion assays show that repeated child-authored renderings
  can install an owner-associated signal (approximately 0.82 versus 0.91 for
  synthetic frames), but spill remains large and declarative negative
  examples do not produce abstention. Rank 32 does not fix this on fresh
  banks.
- Across 28 historical lives, late-stage production of a child-authored
  first-person action record with a measured outcome is zero. The interaction
  itself asks for NOTE before the outcome and supplies no post-outcome writing
  turn, so this locates both a temporal affordance defect and an articulation
  bottleneck; it is not evidence that parenting cannot teach the behavior.

The q15 flywheel abstract supplies the right conceptual opening. The existing
`main.tex` supplies the stronger empirical body. The best paper combines them:
open with the external-evidence -> child artifact -> sleep -> changed future
behavior chain, then report that the present system breaks at artifact
production and conditional writing. Do not make an unrun H2 the paper's
reported contribution.

Candidate title:

> **From Experience to Training Data: What Per-Life LoRA Consolidation Learns,
> and Why It Fails**

## What can still upgrade the deadline paper

These are ordered by information per GPU-hour. Each result adds only its own
claim.

### 1. Finish and read the experiments already in flight

Preserve their preregistered role. Do not retune thresholds after seeing the
last child-frame/taught-writer cells. These results can tighten the storage and
articulation story but cannot establish parenting or a flywheel.

### 2. Qualify conditional writing with V10R1

After its exact implementation ratification and review gates, run the
three-A40-hour V10R1 multi-key falsifier. A pass licenses only:

> The supervised writer carried several conditional native action policies
> while preserving the interface and avoiding the enumerated shortcut/spill
> families.

A failure is a strong paper result: the tested write installs broad habits but
cannot encode the conditional policy surface needed for a learning life. It
also stops expensive parenting and lifetime experiments through this writer.

### 3. If and only if V10R1 passes, test one later write and one authentic source

- An identity-disjoint cumulative rewrite must retain at least 80% of the old
  qualified gain under the same mapping/interface/spill gates.
- An unrepaired child action--outcome source must pass through the same writer;
  missing or wrong child output remains failure.

Together these license **grounded repeated-write feasibility**, not parenting,
connected knowledge, or continual improvement.

### 4. Repair the temporal affordance, then test artifact teaching

The q14 three-cell preschool design answers a different prerequisite:

- post-outcome slot only;
- slot plus a fixed measured-action-record lesson;
- lesson plus a numbered practice target.

The slot-only cell is essential because an increase after adding a place to
write is a harness repair, not parenting. The useful endpoint is accurate,
child-authored, execution-bound records after the outcome. Parent removal and
neutral-slot probes are required before any retention language.

This approximately 61-A40-hour study is feasible in raw compute, but it needs
an exact ratified interaction change and must not be allowed to delay the
writer falsifier or paper writing.

### 5. Treat the one-root parenting/H2 experiment as executor development

The one-root P-versus-active-sham, running-versus-shadow design is the right
minimum executor canary. It is not a causal parenting result. Before it can
run, CPU fixtures must prove childhood-adapter preservation, true shadow sleep,
complete parent/context deletion, occurrence-indexed RNG, fixed-K failure
accounting, and transactional fresh roots.

Only a later independent-root confirmation can support H1/H2. The current
power estimate is roughly 16 roots for a 0.02 interaction if the root-level SD
is about 0.027, costing roughly 800--1,200 A40-hours. The engineering and
lineage critical path, not just aggregate GPU availability, makes this unsafe
to promise for the abstract deadline. The historical RP/R2 adults cannot be
substituted; they compare packages, not randomized parenting.

## One unambiguous stage vocabulary

The repository currently overloads `E0`, `E2`, `E4`, and `E5` between the
full-claim ladder and PCFL relay. Use these labels in the paper programme:

| Stage | Question | Existing ladder mapping | Maximum claim after a pass |
|---|---|---|---|
| `W1` | conditional writer | full ladder E1 / PCFL E0 | conditional policy carriage |
| `W2-R` | unrelated-write retention | full ladder E2 | repeated-write retention |
| `W2-S` | authentic child source | full ladder E3 | grounded child-experience compilation |
| `P1` | lesson survives removal | full ladder E4 | bounded causal parenting persistence |
| `P2` | parenting changes later learning | full ladder E5 | bounded parenting-by-consolidation interaction |
| `M0` | supplied-memory topology/headroom | C11 | fixed-policy supplied-memory ceiling only |
| `M1` | authentic connections matter | full ladder E6 / PCFL E2 | connected experiential carriage |
| `M2` | goals select different paths | full ladder E7 / PCFL E4 | goal-conditioned traversal |
| `M3` | informative action creates useful memory | full ladder E8 / PCFL E5 | one-cycle prospective expansion |
| `C1` | rate--distortion crossover | full ladder E9 | semantic or physical compression, as measured |
| `L1` | late improvement after text plateau | full ladder E10 / future PCFL E6 | bounded continual improvement beyond the certified comparator |

No stage inherits a later claim from a lower one.

## The benchmark suite that closes the full objective

### W: writer and source qualification

Use multi-key conditional policies where constant, tool-only, mode-only, and
other declared shortcuts are at chance. Require held renderings, adapter OFF,
wrong-life, deranged bindings, native action validity, generic non-harm, and
bounded spill. Then add one identity-disjoint cumulative write and an
unrepaired action--outcome source.

This is the substrate gate for every LoRA-based downstream experiment.

### P: parenting causality

Start every block from a byte-identical clean child and randomize targeted
parenting versus an active content-neutral sham. Match teacher model, context,
timing, tokens, warmth, and task opportunities. Parent text is visible during
childhood but is not a loss target; only grounded child continuations may be
written. Remove the parent, briefs, retrieval state, caches, and childhood
context before the exam.

`P1` measures `(targeted ON-OFF) - (sham ON-OFF)` on positive and
contraindication cues. `P2` forks every adult into promoted sleep and true
shadow sleep and uses a root-level difference-in-differences on early-to-late
improvement. Invalid and missing actions remain zero in the denominator.

### M0: supplied-memory topology ceiling

Run C11 only when this final paper-grade mechanism ceiling is actually next.
Its exact role is to show that a fixed finite actor can solve the PCFL route
surface when supplied the correct records and that bridge/twin/derangement
controls behave. Its guard is governance, not scientific evidence. C11 says
nothing about LoRA, learning, parenting, recurrence, or the organism.

### M1: connected experiential knowledge

In a clean learned PCFL relay, the child obtains atoms from public actions and
authors a co-use proposal before an action for which both atoms are the unique
minimal support. Compare:

- authentic links;
- resource-matched atoms without the link;
- truthful null links;
- deranged links;
- same-build read-time link permutation; and
- necessary-link cuts, adapter OFF, and wrong-life memory.

A syntactic co-mention is not a connection. The root theorem or matched
single-atom removals must prove both atoms are necessary.

### M2: goal-conditioned traversal

From the same public start and same memory, issue two goals whose unique
solutions require different paths. Require goal-swap sensitivity, a necessary
bridge cut, and truthful binding-twin redirection under identical read and
generated-token budgets. Task-conditioned output alone is not traversal.

### M3: expansion through action

Before the action, the public information set must leave two hypotheses live.
The authentic signal must cause selection of a target-relevant separating
experiment with positive information gain. Carry the actual action, public
outcome, child-authored row, write, sterile reset, and delayed goal. That goal
must require one old relation and the newly learned relation.

The complete contrast includes authentic versus matched sham signal, no-write,
sham-write, action-disabled, outcome/binding twin, old-row cut, new-row cut,
wrong-root, and delayed binding redirection. This supports one-cycle expansion,
not a lifetime flywheel.

### L1: longitudinal development

Use independently initialized child/life roots. Within each life, repeat
multiple M3 cycles with future goals hidden at each write and genuinely new
information cohorts. Compare:

- the full THINK/DREAM/SLEEP learner;
- the same child with persistent writes disabled;
- a certified evolving raw-record active-text memory;
- a normalized typed-text carrier; and
- where affordable, a single final batch-write/LEAFE-like control.

The strong active-text system must pass its own prospective certificate:
faithful update, candidate-blind retrieval, citation identity, store-swap
sensitivity, row use, headroom, and end-to-end relay. All carriers receive the
same admitted evidence, public outcomes, tools, action opportunities,
generated-token envelope, and write latency.

Pre-register the text baseline's plateau before looking at the learner
contrast. Require at least three later fixed cuts, positive learner late slope,
positive slope advantage, retention of old competence, and a terminal
practical margin. Check recurrence-off, write-off, and bridge-removal
ablations. Checkpoints/tasks are repeated measures; the independent unit is a
separately initialized life.

### C1: rate--distortion

Run this separately over increasing semantic loads. Compare raw expanded
observation text, normalized connected text, schema-plus-residual text, and
the live parametric representation. Measure exact bytes of the complete
persistent acting state, round-trip fidelity, task utility, false memories,
and access cost.

LoRA rank is not compression. Until the LoRA's complete byte count crosses a
registered text-reference threshold at preserved utility, call it
`parametric transport` or `consolidation`. A text semantic-code result may be
valid before physical LoRA compression is feasible.

## Hard dependency graph

```text
measurement/headroom
        |
       W1 -> W2-R -> W2-S
        |       \      \
        |        \      +----> learned LoRA carrier for M1
        |         +----------> repeated SLEEP is technically reusable
        |
post-outcome affordance -> artifact acquisition -> P1 -> P2

CPU PCFL theorem + exact-text DEV -> M0/C11 ceiling
W2-S + PCFL theorem + carrier certificates -> M1 -> M2 -> M3

active-text certificate + M3 + independent lives -> L1
stable representations + registered byte accounting -> C1
```

`P2` and `M1--M3` are scientifically separable: a fixed clean child can test
the mechanism relay, while parenting asks whether a lesson changes later
learning. The full organism paper ultimately joins both; neither may stand in
for the other.

## Stop rules

1. W1 failure stops long parenting and lifetime scaling through the present
   writer representation.
2. W2-R failure means the writer is one-shot, not continual.
3. A slot-only preschool improvement is a harness result, not parenting.
4. P1 failure removes parenting language; the unparented mechanism programme
   continues.
5. An invalid active-text integration blocks any LoRA-over-memory claim.
6. M1 failure removes connectedness; M2 and M3 cannot rescue it.
7. M2 failure permits connected-record language but not traversal.
8. M3 failure permits passive use but not prospective expansion.
9. No prospective active-text plateau means no `beyond saturation` claim.
10. No measured byte crossover means no physical compression claim.

## Corrections needed in the current narrative

- `THESIS_v2_SELF_LEARNING_FLYWHEEL.md` says H1 is "verified by us". It is
  not. Routine carriage and instruction-conditioned child prose are not a
  retained adaptive learning skill.
- `2026-09-11_decisive_evidence_path.md` still says the lived-mirror gateway
  follows V7. The current candidate is V10R1.
- `NEXT_EXPERIMENT_DESIGN_v3_BLEND.md` should not control a final run. Its
  two-block rank-8/rank-32 architecture, historical H2 comparison, and
  approximately 1,050-A40-hour all-at-once plan are superseded by evidence and
  clean-lineage audits. Use one rank-8 adapter by default; introduce a split or
  rank increase only for a predeclared joint-interference deficiency.
- `CANON_v7.md` is an unresolved draft, not a ratified controlling manifest.
  Its conflicts and one-lineage existence thresholds cannot turn a
  development child into confirmatory evidence.
- The q14 post-outcome slot repairs interaction timing. The slot itself cannot
  be described as a curriculum or parenting success.
- C11 remains a separately bounded supplied-memory ceiling. Do not finish or
  enforce its full custody guard for current scouts.
- Replace `compressed experiential knowledge` with `compiled` or
  `consolidated` everywhere except the registered rate--distortion result.

## Deadline/resource judgment

The repository schedule gives September 18 for the abstract and September 25
for the paper; one eight-A40 node expires September 14 and the other is leased
through September 21. The raw GPU-hour envelope is larger than the decisive
near-term tests, but wall-clock, unratified material changes, clean-lineage
construction, and missing executors dominate.

Feasible before the abstract, if approvals and reviews are immediate:

- finish the in-flight writer/child-frame scouts;
- V10R1 (at most three A40-hours);
- after a pass, one retention write and one authentic-source qualification;
- possibly the approximately 61-A40-hour preschool acquisition study;
- CPU PCFL M0 work or an explicit-text development relay, clearly labeled DEV.

Not safe to promise before the abstract:

- a powered multi-root parenting-by-sleep result;
- the learned LoRA PCFL connection/traversal/expansion relay;
- a prospective late-lifetime advantage over a certified active-text plateau;
- physical LoRA compression.

Therefore submit the characterization/articulation paper as the guaranteed
scientific object. Let new passing gates upgrade individual claims, never the
validity of the submission itself. The full benchmark suite remains the
ordered closure path after the deadline.
