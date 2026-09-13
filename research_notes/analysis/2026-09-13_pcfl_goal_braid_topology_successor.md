# PCFL goal-braid: smallest claim-bearing prospective topology successor

**Date:** 2026-09-13 PT

**Role:** fresh topology designer and adversarial reviewer

**Status:** documentation only. This memo does not authorize source authoring,
fixture generation, model/tokenizer execution, training, GPU use, or a claim.

## Verdict

Use a minimal PCFL adaptation, not Semantic World v0.2.

The successor should combine the two-branch geometry already proposed in
`PCFL-R3` with the current PCFL EVENT/LINK, OLD/NEW, provenance, writer, and
native-action stack. Call the proposed construct **`PCFL-GOAL-BRAID-v1`**.

Its decisive property is simple:

> From the same start and the same learned memory, changing only the distant
> goal changes the first irreversible STEP. Both candidate branches are
> locally indistinguishable; the correct branch is found only by following
> remembered connections several transitions forward.

This repairs the failure of `PCFL-NATIVE-STEP-v1`, where one-hop destination
degree selected the whole common trunk and the goal affected only the final
edge. It does not make explicit LINK rows information-theoretically necessary:
exact EVENT endpoints can still be composed. LINK-added value therefore
remains an empirical AUTH-versus-ATOMS claim, not a built-in property.

## 1. Exact role-level topology

Every root receives fresh, token-balanced opaque identifiers. The mnemonic
roles below remain generator/checker-private.

### OLD bank

```text
                         branch 0
                    a_O       b_0
              S ----------> U0 ----------> F0

              S ----------> U1 ----------> F1
                   a_(1-O)     b_1
                         branch 1

              R0 ----------> K0 ----------> G0
                    d_0       f_0

              R1 ----------> K1 ----------> G1
                    d_1       f_1
```

The eight OLD EVENT roles are:

```text
e0: S  --a_O----> U0       e4: R0 --d_0--> K0
e1: U0 --b_0----> F0       e5: K0 --f_0--> G0
e2: S  --a_(1-O)-> U1      e6: R1 --d_1--> K1
e3: U1 --b_1----> F1       e7: K1 --f_1--> G1
```

The four OLD LINK roles are:

```text
l0: e0 THEN e1 VIA U0      l2: e4 THEN e5 VIA K0
l1: e2 THEN e3 VIA U1      l3: e6 THEN e7 VIA K1
```

`O in {0,1}` swaps only the two opaque first-port bindings. It leaves every
node, event, link, degree, path length, and surface marginal fixed.

### NEW bank

Two symmetric public probe cards describe candidate gaps without supplying an
executable port:

```text
Q0: test the unknown connection F0 -> R0
Q1: test the unknown connection F1 -> R1
```

The public pre-outcome card may contain the opaque source and hypothesized
destination. It must not contain the bridge port, hidden bit, answer, route,
or a word such as relevant/distractor. Each probe has one bit of outcome
entropy and returns an ordinary public receipt containing its realized opaque
bridge port.

```text
e8: F0 --q0_N0--> R0
e9: F1 --q1_N1--> R1

l4: e1 THEN e8 VIA F0      l6: e3 THEN e9 VIA F1
l5: e8 THEN e4 VIA R0      l7: e9 THEN e6 VIA R1
```

`N0,N1 in {0,1}` independently select one of two token-matched bridge-port
labels at each frontier. Before its probe returns, each binding is
unknowable from all visible bytes.

The complete delayed routes are therefore:

```text
goal G0: a_O,     b_0, q0_N0, d_0, f_0
goal G1: a_(1-O), b_1, q1_N1, d_1, f_1
```

They have equal length. They share no action after `S`. Both branches are
successful routes to different goals; neither is a shallow dead-end cue.

This uses the same eleven node roles as the current PCFL skeleton, increases
the fitted memory from `9 EVENT + 6 LINK` to only `10 EVENT + 8 LINK`, and
removes the private `X -> Z` latent repair. Most current schemas, parsers,
provenance receipts, memory calls, writer controls, and OLD/NEW cuts remain
conceptually reusable.

## 2. One authentic chronology

The smallest honest life has four stages.

1. **OLD formation.** Through the existing scaffolded exploration interface,
   the child chooses and executes the eight OLD actions, receives public
   outcomes, then authors exact EVENT and LINK commitments. Future probe
   tasks and delayed ROUTE prompts are absent.
2. **SLEEP 1.** The frozen compiler verifies, replays, and writes only exact
   child spans. AUTH, ATOMS, wrong-root, source-twin, and LINK-derangement
   controls remain separate descendants.
3. **Goal-conditioned reachout.** From the identical post-S1 snapshot, one
   presealed goal `G_g` is revealed with both probe cards. `Q_g` is useful;
   the other probe is equally uncertain and useful for the alternate goal.
   The selected result becomes child-authored `e8` or `e9` plus its two
   crossing LINKs. After this scored choice terminates, a plainly labeled,
   goal-neutral scheduled observation supplies the other bridge so that both
   routes exist in one authentic life. No claim is assigned to that second
   scheduled probe.
4. **SLEEP 2 and sterile paired use.** Cumulatively write OLD plus both NEW
   bridge experiences. Delete active context, external memory state, probe
   transcript, and parent material. Fork two non-writing evaluations from
   the byte-identical S2 child: `START S, GOAL G0` and `START S, GOAL G1`.

The scheduled complement in step 3 is a deliberate compromise. It lets the
same S2 memory support a pure paired-goal intervention. Without it, each
goal-specific descendant would contain only its selected bridge, and the
shortcut “follow whichever branch has a NEW row” would replace goal use.

## 3. Static native action boundary

Every arm uses the same fixed grammar on every actor call:

```regex
(?:THINK [^\r\n]*[^\s\r\n][^\r\n]*|STEP P_[A-Z2-7]{10}|PROBE Q_[A-Z2-7]{10})\n?
```

No arm gets concrete IDs in its decoding grammar. Full graph, active text,
raw episodic, memory-service, native LoRA, OFF, wrong-root, cuts, and
derangements differ only in their permitted memory information, not their
action typing.

During delayed use, the public state contains only:

```text
START <opaque node>
GOAL <opaque node>
CURRENT <opaque node>
```

An accepted STEP receives only the ordinary next `CURRENT`. The host never
returns legal ports, correctness, distance, route prefix, preferred branch,
or repair text. A nonexistent or non-current port, wrong operation type,
malformed turn, token-cap event, or exhausted budget is terminal failure.
There is no reset, undo, backtrack, alternative-life retry, or write during
evaluation. Reaching the other goal leaves no outgoing transition and fails.

Six THINKs, six STEPs, and 2,048 generated tokens per task are generous and
do not reveal the five-edge answer length. The environment retains the
accepted action trace privately for exact scoring.

During reachout, the same grammar remains active, but a committed PROBE is
terminal for the selection task. Its outcome is returned only on the
authentic lineage, never on read-only diagnostic forks.

## 4. Why the first STEP is genuinely prospective

At `S`, both candidate destinations have the same complete local signature:

```text
is_goal = false
outdegree = 1
one successor with outdegree = 1
one successor after that with outdegree = 1
```

From `U0` or `U1`, the corresponding goal is four transitions away. The two
branches are isomorphic through radius three; goal identity first separates
them at radius four. Thus:

- direct-goal matching ties;
- destination outdegree ties;
- depth-one LINK presence/count ties;
- route length ties;
- dead-end avoidance ties; and
- changing `G0` to `G1` changes the correct first port on the same S2 child.

At reachout, both proposed destinations `R0/R1` have outdegree one and are not
the goal. Determining which probe closes the requested route requires tracing
`R_b -> K_b -> G_b` and also recognizing the old prefix `S -> U_b -> F_b`.
The intended minimum computation is therefore a two-sided connection over
multiple recalled rows, not a direct destination check.

This is still a small graph-search skill. A pass supports bounded
goal-conditioned prospective memory use, not general planning, MCTS,
autonomous goal creation, or unconstrained long-horizon intelligence.

## 5. Exact cube and information ceilings

For each root, materialize the complete cell cube:

```text
(O,N0,N1) in {0,1}^3
```

Score both goals in every cell. Four excluded roots give:

```text
4 roots x 8 cells x 2 goals = 64 delayed tasks
```

At fixed `(root,goal)`, the task prompt is byte-identical over all eight
cells. Its exact route varies with `O` and the goal-relevant `N_b`; the other
NEW bit duplicates each label. There are exactly four correct route strings,
each at frequency `2/8`. Therefore:

```text
best deterministic exact-route policy without life memory = 1/4
best first-STEP policy without OLD binding O              = 1/2
best bridge-STEP policy without NEW binding N_b           = 1/2
best policy that ignores the goal on paired S2 tasks       = 1/2
```

The graph oracle must score `64/64`. Deleting `e0/e2` bindings makes the
first choice unidentified in every cell; deleting `e8/e9` bindings makes the
bridge action unidentified. OLD-only and NEW-only projections must form exact
byte-collision groups with different required actions, not merely show lower
average accuracy.

## 6. Mandatory deterministic shortcut battery

Before model execution, two independent CPU implementations must agree on
every cell, route, collision, cut, and score. Print exact results for:

1. `FIXED_FIRST_THEN_FOLLOW` and `FIXED_LAST_THEN_FOLLOW`;
2. `DIRECT_GOAL_ELSE_FIRST`;
3. `LOCAL_1_DEGREE`;
4. `LOCAL_1_LINK_COUNT` / `HAS_LINK_ELSE_FIRST`;
5. `POSITION_SCRIPT`, the best predeclared action ordinal by step number;
6. `STATE_AND_MEMORY_NO_GOAL`, paired within one S2 snapshot;
7. `GOAL_ONLY`, `STATE_ONLY`, identifier lexicographic, and displayed-order
   projections;
8. OLD-start cut, NEW-bridge cut, each tail cut, wrong-root, and coherent
   opposite-cell cross-mount; and
9. for reachout, fixed probe, direct-goal, source-degree, destination-degree,
   LINK-count, goal-only, and card-position policies.

On the four-root 64-task panel, every radius-zero/one or fixed-position
traversal policy must be `<=32/64`; the exact prompt-only route ceiling is
`16/64`. On a four-root paired smoke with two goals per root, every goal-blind
branch rule is exactly `4/8`. For reachout, every fixed/local policy must be
at most one half while the exact two-hop connection oracle is `1.0`.

Identifier allocation and graph-row/probe-card orders must be constructed in
balanced blocks so lexicographic and positional projections meet these bounds
by design. Do not generate roots repeatedly until a favorable empirical
sample happens to pass.

Also compute canonical rooted-neighborhood signatures for each branch. The
two `S` successors must be identical through radius three, and both probe-card
source/destination pairs must be identical through radius one. Any mismatch
invalidates the topology before inference.

## 7. Model gates and claim order

First run a zero-fit supplied-memory ceiling, not a learned-memory campaign:

- exposed smoke: four roots x paired goals, require `>=7/8` accepted THINK +
  strict goal reaches while all shallow policies remain `<=4/8`;
- full excluded panel: require graph/text ceilings `>=60/64` and strict action
  legality `1.0`;
- paired goal gate: at least three of four smoke roots must solve both goals
  and change the first STEP;
- reachout ceiling: on 32 balanced tasks, require the connection-informed
  probe at least `30/32`, while fixed/local controls remain `<=16/32`.

If zero-shot 7B fails, do not weaken the graph. Qualify a target-disjoint
composition/bootstrap skill on unrelated graph families, give the identical
frozen child to every memory arm, and rerun the same ceiling. This is an
inherited reasoning skill, not experiential memory and not a SLEEP repair.

Release claims in this order:

1. exact cold EVENT carriage;
2. OLD and NEW retention after S2;
3. native state-to-state use with causal OLD/NEW cross-mounts;
4. paired-goal first-STEP redirection;
5. goal-conditioned gap selection;
6. explicit LINK-added value only if AUTH beats matched ATOMS and a coherent
   LINK intervention redirects behavior while EVENT fidelity stays matched.

A successful final route cannot compensate for a failed carriage or cut. An
EVENT-only success is connected read-time composition, not stored-LINK added
value. The scheduled second probe cannot be counted as autonomous expansion.

## 8. Sealed held-out structure

This design permits clean confirmation without pretending that a life's
opaque facts generalize to another life.

- DEV and CONF use disjoint root identifiers, task wording, row order, probe
  order, decode seeds, and model-exposure registries.
- Confirmation roots and thresholds are sealed before the first DEV output;
  sixteen independent CONF roots are a reasonable first powered cohort, with
  the root—not goals, cells, calls, or decode repeats—as the unit.
- No complete route, final task prompt, route response, future-goal-derived
  row, or evaluator judgment enters DREAM/SLEEP.
- Both final goals are evaluated from one byte-identical S2 snapshot; those
  forks are destroyed and never write.
- A common inherited composition skill, if needed, must be trained on varied
  target-disjoint graph families, not this exact braid with renamed IDs.
- Personal EVENT/LINK memory is expected to be root-specific. The held-out
  claim is transfer of the common **use procedure** plus acquisition/use of
  fresh life-specific memory, not cross-root recall of old opaque IDs.

Run the strong `ACTIVE_STRUCTURED_TEXT`, witnessed-graph, raw-episodic, OFF,
wrong-root, and carrier-cut conditions on the identical action interface.
The exact graph is allowed to win. This topology is useful even if LoRA does
not beat text; it localizes whether failure is formation, carriage, neural
composition, goal use, or access efficiency.

## 9. Why not Semantic World v0.2

| requirement | PCFL goal-braid | Semantic World v0.2 |
|---|---|---|
| irreversible state action | native STEP/PROBE extension | passive final-answer task |
| child EVENT/LINK provenance | current stack already exists | would need a new action/record layer |
| chronological OLD then unpredictable NEW | small symmetric bridge change | not native to v0.2 |
| exact goal-switched first action | built into paired corridors | would require an Action-World redesign |
| strong existing ceiling | must requalify on new topology | 32B reached 23/24 only with an exhaustive 57-subset atomic controller |
| shortcut history | one known local-degree defect, repaired directly | later audit found a target-local pair/signature shortcut; v0.3 was needed |
| semantic burden | opaque graph composition only | operator, parent-set, role, pigment, and label composition |
| implementation delta | topology, scorer, and roster changes | new interactive benchmark plus PCFL-compatible memory lifecycle |

Semantic World v0.2 remains valuable as a later semantic-transfer challenge.
It is not the smaller writer/use assay. Converting it now would conflate a
still-unproven LoRA memory seam with a much harder semantic inference stack,
and its historical 23/24 ceiling does not establish that the fixed 7B child
can take irreversible actions from personal memory.

`PCFL-GOAL-BRAID-v1` is smaller because it changes the failed causal geometry
while preserving the machinery already shown to form, verify, write, and
read exact EVENT rows.

## 10. Final adversarial disposition

**Recommend prospective re-authoring of the topology, after the required
architecture/governance path; reject execution on the current PCFL graph.**

Before any source freeze, reject the goal-braid too if any of these occurs:

- a candidate branch differs in direct-goal status, path length, degree, LINK
  count, or radius-three rooted signature;
- either paired goal keeps the same correct first STEP;
- a fixed/local/positional policy exceeds one half;
- a final route or goal-derived derivative appears in training;
- only one NEW branch is present in the paired S2 memory;
- action grammars or world-validation semantics differ across memory arms;
- the child can recover from a wrong first STEP; or
- the apparent held-out claim relies on renamed copies of a topology used to
  train the composition bootstrap.

The remaining honest risk is model-side: even this clean task may exceed the
unbootstrapped 7B child's composition skill. That would be a reader result,
not a reason to restore the shallow topology. The topology should make the
scientific question easier to interpret, not easier to pass.

## Evidence inspected

- `AGENTS.md`
- `research_notes/analysis/2026-09-13_pcfl_native_step_v1_red_team.md`
- `research_notes/analysis/2026-09-13_pcfl_post_a4_resolver_decision.md`
- `research_notes/analysis/2026-09-13_pcfl_a4_generic_procedure_terminal_audit_and_post_reader_branch.md`
- `research_notes/analysis/2026-09-13_level1_to_level2_composition_boundary.md`
- `research_notes/analysis/2026-09-13_pcfl_vertical_dev_v2_synthesis.md`
- `research_notes/analysis/2026-09-13_pcfl_vertical_world_construct_identifiability_attack.md`
- `research_notes/analysis/2026-09-13_pcfl_goal_conditioned_traversal_vs_expansion_ac_audit.md`
- `research_notes/analysis/2026-09-12_smallest_post_h1_connected_traversal_expansion_module.md`
- `research_notes/37_semantic_world_v02_spec.md`
- `lands/HANDOFF_FABLE_V02.md`
- `research_loop/plans/counterfactual_confluence_v03.md`
- read-only inspection of `organism_v6/pcfl_vertical_dev.py`,
  `gpu/astra_pcfl_interface_dev.py`, and `lands/v02.py`
