# Candidate A: FeltCraft Bridge-Lifetimes

**Status:** concise research proposal only. It authorizes no implementation,
model call, GPU run, or claim. Any execution requires the repository's durable
architecture-deliberation and human-ratification path.

## Paper question and smallest defensible claim

Can one frozen agent turn its own rendered action--outcome history into
chronologically grounded, connected experiential knowledge, carry that
knowledge in a fixed per-life LoRA, and use bounded goal-conditioned traversal
to keep acquiring and combining useful causal structure after its native
context is exceeded?

The paper object is a **lifetime phase diagram**, not a symbolic-kernel result
and not a claim that weights must beat an exact graph. The claim-eligible chain
is:

```text
public action/outcome life
-> target-blind DREAM proposals
-> later public support/contradiction
-> deterministic SLEEP compilation
-> identical text / graph / LoRA semantic content
-> bounded recurrent THINK reads and cited path
-> novel executed action
```

The common-deck experiment identifies representation/use. A small randomized
on-policy continuation is additionally required to claim the full
memory--action--experience--memory flywheel. LoRA receives transport and
bounded-access credit, not discovery or multi-hop-reasoning credit.

## Actual rendered environment

Build one new deterministic package, **FeltCraft Bridge-Lifetimes (FCBL-8)**.
It is a compact workshop/rescue world rendered as natural-language scenes, not
a QA table. Public handles are opaque, but each item also has a fluent neutral
descriptor (for example, “ribbed, chalky, and softly humming”). Descriptor
lexicons are counterbalanced and independently permuted so ordinary language
makes the world readable without predicting a recipe. A second isomorphic
lab-rescue skin is a locked robustness block, not another replicate.

The action interface is:

```text
MOVE(site)
GATHER(item)
TRY_CRAFT(output, ingredient_a, ingredient_b)
DELIVER(mission, output)
STOP
```

Crafting consumes inputs. Success returns only `CRAFTED`; failure returns
`INCOMPATIBLE` or `MISSING_INPUT`, never the correct recipe, partial match,
role, or proof. Each family has four raw roles, two intermediate roles, and two
top roles:

```text
I0 <- R0 + R1       I1 <- R2 + R3
T0 <- I0 + R2       T1 <- I1 + R0
```

Every new family has fresh handles, sites, and a fresh hidden type-preserving
descriptor-to-role alignment. A registered bridge edge connects eras:

```text
B[f] <- T0[an earlier family] + I1[a later family]
```

Source episodes witness each decisive edge separately, but never the complete
held-out state, goal, bridge plan, or decisive action sequence. Thus a bridge
mission is a real old-to-new causal dependency: the old product is an input to
the later action, not a second independent goal.

Each super-seed creates a matched four-cell block:

```text
{MOTIF, RANDOM} x {twin-0, twin-1}
```

- In `MOTIF`, descriptor alignment persists across instances of a family.
- In `RANDOM`, it is independently permuted per instance.
- Within a twin, both regimes have the same handles, hidden physical recipes,
  open-loop action arguments, and action outcomes; only public descriptor
  alignment differs.
- Twins have byte-identical target goal/state and matched marginals, but a
  fixed non-automorphic role involution changes the correct recipes/plans.

This separates reuse/compression from merely receiving better physical
experience. RANDOM is the exact-retention negative control; MOTIF permits a
prospectively testable schema.

## Life and evaluation schedule

Use `google/gemma-2-9b-it` as the frozen primary action/DREAM/THINK backbone
because its actual native window is 8,192 tokens; pin model, tokenizer, chat
template, and runtime revision before DEV. The MEMORY adapter is on the same
frozen base. A Qwen2.5-7B/32B 128k full-context run is a separately labelled
modern-long-context robustness audit, never pooled with the matched-backbone
contrast.

Let `L_native` be the mechanically measured usable Gemma window after prompt,
state, workspace, and output reserve. Complete-event cuts are placed near:

```text
0.5L_native, 1L_native, 2L_native, 4L_native, 8L_native
```

The final three cuts must be strictly post-native. The open-loop source policy
performs a fixed, outcome-blind set of surveys and craft assays. Each geometric
block introduces new families, confirms predictions about earlier families,
and revisits age-stratified old edges. Unique supported relations and the
enumerative sufficient-statistic length must grow by at least 1.8x at every
post-native interval; repetition, paraphrase, and failed filler do not count.

At each cut, freeze memory, clear all context/KV/retrieval state, and evaluate
fresh disposable clones on four equally weighted panels:

- `A1 transfer`: apply one witnessed edge to a new state (diagnostic).
- `A2 compose`: join two relations learned in distinct episodes.
- `A3 bridge`: execute a four-to-six-action plan in which an early-family
  product is causally required by a recent-family craft.
- `S sparse`: act in a fresh partially assayed instance. In MOTIF a schema
  committed before target creation identifies the missing edge; in RANDOM the
  exact posterior remains at its registered chance ceiling.

Report newest-family acquisition, earliest-family retention, and cross-era
action separately. Also report the maximum certified bridge depth solved at
70% under a fixed read/action budget. No aggregate may hide stalled acquisition
or forgetting.

Every target permits at most six one-atom reads, twelve THINK operations, and
six world actions. One read returns one local atom or `NOT_FOUND`; it never
returns a chain, plan, candidates, scores, or topology. Later queries must be
anchored in the public goal/state, an earlier read, or a public outcome. A3
constructive credit requires an auditable dependency DAG and a decisive-action
cut; lucky success remains behavioral success only.

### DREAM--SLEEP--LoRA condition

At each cut DREAM sees only bounded replay bundles of ordinary public events
and eligible earlier supported memories. It proposes one target-independent
edge, scoped procedure, bridge relation, exception, or schema prediction with
root citations and a future observable. Only a later ordinary outcome hidden
at proposal time can mechanically append support or contradiction. Evaluation
outcomes never support memory.

SLEEP admits supported, nonrevoked claims; canonicalizes and deduplicates;
preserves provenance outside training text; emits a frozen number of forward,
reverse, incident-edge, cloze, and contrast views; and rebuilds the cumulative
per-life adapter from the clean base. Views add write exposure, never evidence.
The first paper cell excludes shortcuts. A fixed adapter rank/precision/read
budget is selected on DEV and held across all cuts; growing rank per cut is a
separate capacity curve, not the headline. The adapter is mounted only for a
memory read and is absent when the clean frozen backbone composes and acts.

## Fair comparison set

All common-interface arms receive byte-identical public source events, the
same frozen action model, target/action budget, THINK operations, and visible
read budget. Lifecycle compute, hidden scans, retained bytes, and latency are
reported rather than falsely equated.

1. no persistent memory;
2. honest full chronological context while it fits, then exact recent-window
   truncation, plus the separately labelled 128k audit;
3. iterative hybrid BM25+dense RAG over raw trajectories;
4. reflection/procedure text memory;
5. native A-MEM-style linked memory with its native interface and resource
   ledger;
6. exact observed-edge graph with bounded traversal;
7. explicit Bayesian/MDL motif learner plus graph (strong algorithmic
   reference, not hidden-truth oracle);
8. raw-event LoRA and direct trajectory-to-atomic-QA LoRA with the matched
   training envelope;
9. learned DREAM-compiled text through the common reader;
10. the **identical frozen DREAM corpus** in LoRA, with unaided generative
    one-atom reads as headline and constant-size recognition as assisted
    diagnostic;
11. gold supported atoms/schema through text and LoRA (component ceilings);
12. end-of-life batch SFT on the same prefix (upward resource reference);
13. hidden physical graph/shortest-path oracle (executor ceiling only).

If the exact graph or Bayesian learner wins, that is the correct phase diagram;
it cannot be removed or handicapped post hoc. Learned DREAM must recover at
least 70% of the gold-compiler action gain before the full system is named.

## Causal interventions and leakage firewall

- Freeze target-only, state-only, identifier-only, descriptor-only,
  passive-signature, action-frequency, and source-action-string predictors;
  every one must score at most .35 while exact legal memory scores at least
  .85.
- Direct-record closure is exactly zero; a legal single memory/read cannot
  contain a target handle, terminal action, decisive pair, or complete plan.
- Run authentic memory, within-stratum action--outcome binding derangement,
  descriptor--schema derangement, cross-life memory, and coherent twin-memory
  assignment. Preserve lengths, relation types, answer marginals, counts, and
  training envelopes where the intervention permits.
- For claimed constructive traces, mask the transitive cited-memory cut and
  substitute type-matched twin atoms. The decisive operation must change;
  matched irrelevant masks must not.
- Generate whole lives and targets before model evaluation; use fresh handles
  and whole-super-seed DEV/locked splits. DREAM never sees targets, scorer,
  hidden graph, pair metadata, or acceptance receipts.
- Seal evaluation in disposable processes. Its prompts, reads, actions,
  outcomes, caches, and RNG cannot mutate later life. Hash run-versus-skip
  suffixes. Reset adapter, optimizer, index, cache, process, and RNG per life,
  with cross-life canaries.
- Malformed/multiple operations consume budget and remain failures; no hidden
  repair, retry, or favorable seed/cell replacement.

## The minimal on-policy flywheel test

After common-deck promotion, replay the same `4L_native` source state into
isolated clones. Randomize authentic versus twin-deranged memory before a
12-action exploration block in one new sparse family. The agent chooses assays
and crafts; those ordinary outcomes, but no evaluation outcomes, enter the next
DREAM/SLEEP. At `8L_native`, run a sealed analogous mission.

Cross the collector history with two frozen compilers (`DREAM--LoRA` and native
A-MEM) so experience quality and representation/use are not conflated. A
flywheel result requires the randomized authentic-memory assignment to improve
(i) information gain per action, (ii) supported decisive-edge coverage after
sleep, and (iii) sealed later action value. A mere sequential correlation is
insufficient.

## Estimands, saturation, and power

The independent unit is the matched super-seed, never a target, twin, adapter
seed, or generation. Average twins, target repetitions, and two adapter seeds
inside each super-seed.

Primary endpoints are equal-weight A2/A3/S value and restricted mean actions
to success in MOTIF at `8L_native`; RANDOM is the paired negative control and
is never pooled to dilute the schema estimand. Co-primary contrasts are:

```text
efficacy:   full DREAM-LoRA - each of {context, RAG, reflection, A-MEM,
            direct-QA LoRA}
growth:     [full(8L)-full(2L)] - [baseline(8L)-baseline(2L)]
transport:  identical-corpus LoRA - text       (NI margin -0.05)
binding:    authentic - deranged/twin memory
```

The same-corpus text arm, exact graph/Bayesian learner, batch SFT, and hidden
oracle are not silently included in the efficacy family: text is the transport
contrast; the others are named upward/algorithmic references whose wins bound
the interpretation.

A positive causal-memory result requires efficacy differences at least .10
with simultaneous one-sided lower bounds above zero, transport
noninferiority, and each binding intervention to remove at least half the gain
over no memory or .15 absolute. Schema value is the preregistered
difference-in-differences `(schema-atoms)[MOTIF] - (schema-atoms)[RANDOM]` on
`S`; compression additionally requires a prefix-free total code, including
decoder/index/provenance, shorter than enumerated atoms at matched action loss.

A comparator is called **saturated** only if simultaneous upper bounds for
both `4L-2L` and `8L-4L` improvement are at most .02, oracle headroom is at
least .10, target difficulty is stable, and unique causal information grows in
both intervals. The full system “continues improving” only if its corresponding
lower bounds exceed .02. Otherwise use no saturation/crossover language.

Use 8 disposable DEV super-seeds and 8 locked descriptive calibration seeds.
Confirmation uses 40 fresh super-seeds, four targets per stratum/cell/cut, two
nested adapter seeds, and common execution randomness. Forty pairs provide
about 80% power for a paired .10 effect when the outer-unit SD is at most .20
under the preregistered one-sided family. A blinded variance-only rule may
raise 40 to 64 before outcomes are unsealed; it cannot stop early. Use paired
sign-flip/randomization inference and a shared outer-cluster bootstrap with
Romano--Wolf correction over named efficacy contrasts. Failed science cells
score zero.

## GPU ladder and the run possible within days

- **CPU, <1 day:** enumerate at least 1,000 lives; prove deterministic replay,
  regime coupling, twin collisions, exact posterior/headroom, bridge
  necessity, target leakage floors, entropy/unique-edge growth, and evaluation
  noninterference.
- **1 x 80GB GPU, 1--2 days:** eight DEV seeds, known-good explicit
  atoms/schema, generic recurrent THINK, and text-only full-context/RAG/graph/
  A-MEM/DREAM conditions at `1L,2L,4L`. Stop if oracle THINK is below .85 or
  DREAM-text fails RAG/A-MEM by .10.
- **1 x 80GB GPU, another 2--3 days:** four matched calibration super-seeds at
  `2L,4L,8L` for direct-QA LoRA, DREAM-text, identical-corpus DREAM-LoRA,
  binding shuffle, and gold transport. This is the smallest decisive
  transport pilot; it is descriptive, not paper evidence.
- **8 x 80GB GPUs:** the eight-seed all-arm pilot and on-policy clone test fit
  in roughly 2--4 wall days with batched 9B inference. A 40-seed confirmation
  is expected to cost roughly 25--45 H100-days (about 3--6 wall days on eight
  GPUs) after the pilot freezes actual throughput and budgets.

No LoRA work begins until CPU, oracle-thinker, and text-structure gates pass.

## Decisive outcomes

**Positive:** learned DREAM preserves precise supported edges/schema; bounded
THINK causally traverses them; DREAM-LoRA beats full/recent context, RAG,
A-MEM, and direct-QA LoRA after native context; the same corpus survives LoRA
transport; registered baselines meet the saturation definition while the full
system grows; authentic binding interventions are necessary; and the on-policy
assignment improves evidence, later memory, and later action.

**Decisive negative or narrower pivots:**

- compiled text fails RAG/A-MEM: no consolidation advantage;
- compiled text works but LoRA fails text noninferiority/direct-QA: an
  explicit experiential-compilation paper, no weights claim;
- exact graph or Bayesian learner dominates: valid negative phase diagram, no
  parametric moat;
- strong baselines keep improving or oracle headroom closes: no
  saturation/crossover claim;
- gains occur only on A1, not A2/A3/S: retention, not constructive learning;
- schema helps equally in RANDOM, or binding/twin interventions do not hurt:
  leakage/generic-compute explanation;
- performance grows only with linearly growing rank/bytes or hidden linear
  candidate scans: storage, not fixed-substrate compression/scalable access;
- common-deck succeeds but randomized memory does not improve information gain
  and sealed later action: representation/use works, flywheel unsupported;
- old retention collapses or unsupported memories outgrow corrections:
  continual viability rejected at that scale.

This is the smallest candidate that simultaneously renders real actions,
holds physical experience fixed for causal attribution, requires connected
old-to-new action construction, contains prospective compression headroom,
crosses an actual native window three times, and lets strong baselines win
honestly.
