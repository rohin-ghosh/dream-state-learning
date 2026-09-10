# PCFL-Stream area-chair advisory review

Date: 2026-09-02

Status: read-only scientific advisory. This is not an architecture consensus,
ratification artifact, execution approval, or scientific-claim approval.

Review scope: `AGENTS.md`; the complete
`research_loop/changes/chg_20260902_pcfl_stream_paper_target_v1` change bundle;
all context bound by its `change.json`; and the most directly relevant thesis,
review, experimental-ledger, and repository prior-art notes for TMEM, PEAM,
A-MEM, and Voyager-style work. No model, network, GPU, or experiment was run.
No existing repository file was modified for this review.

## Area-chair verdict

Current form: **reject, but with a credible accept path**. The proposal is still
`awaiting_consensus`, implementation is unauthorized, and there is no
claim-grade PCFL-Stream evidence. More importantly, the present framing mixes a
potentially strong benchmark contribution with weakly identified mechanism and
systems claims.

The accept-worthy paper is not “Dream–LoRA–Think makes self-learning agents
improve throughout life.” It is:

> A controlled, fixed-source benchmark and causal study of whether target-blind
> compilation of an agent's public action–outcome history into per-life memory
> preserves and uses genuinely new causal knowledge after raw history exceeds
> context.

If executed cleanly, this could be a solid ICLR paper: benchmark contribution
primary, causal measurement contribution strong, systems contribution
conditional, and LoRA-algorithm novelty modest.

## What exact paper could be accepted

The strongest paper has three explicitly separated contributions.

### 1. Benchmark contribution — strongest

PCFL-Stream introduces a generative family in which:

- independent causal information, not filler tokens, increases with lifetime;
- raw history crosses the exact usable context boundary at several
  preregistered checkpoints;
- the same immutable source life and presealed targets are reused across every
  memory arm;
- later action is decomposed into new-cohort acquisition, old-cohort retention,
  and cross-era composition;
- dependency depth and evidence age are independently certified;
- target-byte-equivalent twins and decisive binding cuts permit causal memory
  tests;
- retained bytes, query work, training work, latency, and action value are
  jointly reported.

The novelty is this conjunction. Age curves, long-context stress, dependency
graphs, action benchmarks, and parametric memory tests each have prior art.
PCFL's defensible novelty is one controlled action-level response surface
spanning external and parametric memory with matched lives and causal binding
interventions.

A benchmark paper must release the deterministic generator, oracle/certifier,
target/twin constructor, scoring code, frozen manifests, and evaluation
harness. “Cut public benchmark packaging” may be reasonable as an engineering
cut, but no public reproducible artifact means this should be called a
controlled assay, not a benchmark contribution.

### 2. Mechanism contribution — secondary

The mechanism claim is not a new LoRA method. It is causal decomposition:

```text
public life
  -> target-blind compiled semantic corpus
  -> text or LoRA transport
  -> bounded resolver use
  -> later action
```

The potentially publishable result is that the same semantic treatment changes
later action in authentic-binding-dependent ways, while controls distinguish:

- compiler value from raw experience;
- semantic content from substrate;
- adapter information from candidate/index information;
- memory retrieval from clean-base composition.

This becomes a genuine mechanism contribution only if authentic/twin or
decisive-binding interventions move actions directionally. Same-corpus accuracy
alone is transport correlation.

### 3. Systems contribution — conditional

Dream–LoRA–Think is a systems contribution only if the integrated pipeline
occupies a useful Pareto region against native A-MEM, a faithful TMEM-style
direct-write arm, honest long context, exact symbolic memory, and a
Voyager-style program/skill control.

A higher endpoint score is insufficient. The system must show a meaningful
action advantage at disclosed retained state, query work,
compilation/training cost, and amortization horizon. If exact text or an
explicit graph dominates LoRA, the paper remains a potentially good benchmark
paper, but there is no LoRA moat. If the exact sufficient-statistic system
dominates everything, report that plainly.

## Strongest novelty against the named neighbors

| Prior work | What it already owns | PCFL's defensible delta |
|---|---|---|
| **TMEM** | Online cumulative LoRA memory, QA/instruction-response writes, fast weights changing action, outcome-RL-trained extraction, adaptation within rollouts | Offline/cross-episode per-life persistence; post-context lifetime response surface; separate old/new/cross-era action; same-corpus text/LoRA attribution; binding-level causal interventions. PCFL cannot claim first online LoRA memory, first action-changing fast weights, or first outcome-shaped parametric writing. |
| **PEAM** | Embodied parametric memory, MoE-LoRA skill internalization, failure/correction consolidation, when/what consolidation governance, reduced skill forgetting | PCFL's advantage is experimental identification, not embodiment or consolidation itself: common lives, exact causal entropy, age/depth crossing, external-versus-parametric comparison, and counterfactual binding attribution. PEAM is more naturalistic; PCFL is more controlled. |
| **A-MEM** | Linked/evolving external memory and native graph-like retrieval | PCFL can compare linked external memory with compiled parametric memory on identical lives and targets, and localize whether gains come from organization, reader behavior, or substrate. A-MEM must be run both through the common channel and with its native retrieval interface; common-channel-only evaluation would be unfair. |
| **Voyager** | Lifelong skill library, environment-verified executable procedures, automatic curriculum, continual Minecraft action improvement | PCFL adds retention-by-age, post-context causal-information growth, cross-era binding composition, and twin interventions. Environment verification is explicitly borrowed—the repo calls it the “Voyager rule.” Because PCFL fixes the source life, it is less on-policy than Voyager and cannot claim a stronger self-directed learning loop. |

The single strongest novelty sentence is:

> PCFL-Stream identifies how target-blind experiential compilation, memory
> substrate, and bounded memory use separately affect acquisition, retention,
> and cross-era action as independent causal knowledge grows beyond context.

## Fatal claim risks

1. **“Self-learning agent” is currently false for Paper 1.** A common immutable
   source life is necessary for causal attribution, but makes the study
   fixed-source/off-policy. Memory does not change future evidence acquisition.

2. **“Its own life” is ambiguous.** If a scripted policy generates the source
   stream, say “the observed per-life stream.” If each arm gathers its own
   stream, the matched contrast is destroyed.

3. **Targets can be selected on pipeline success.** The current “only a
   causally useful corpus may enter LoRA” wording permits success filtering.
   Total target allocation must freeze before realized support and compiler
   output; unsupported and uncompiled targets remain in the denominator.

4. **The compiler visibility contract currently leaks goals.**
   `PUBLIC_LIFETIME_PREFIX_AND_GOAL` is marked visible to the compiler. Prefix
   and evaluation goals must be separate, with descendant-level taint closure
   through trainer, index, candidates, prompts, retries, caches, filenames, and
   failures.

5. **Citation masking is not a LoRA intervention.** Removing an external cited
   atom leaves the learned association in weights. Whole-life
   authentic-versus-twin adapters are needed on primary items; decisive-binding
   and sham cuts can be a smaller paired panel.

6. **Same corpus does not isolate substrate.** A recognition-assisted adapter
   may merely rerank a candidate universe that already stores the answer.
   Candidate-only clean-base, wrong-adapter, matched candidate-assisted text,
   explicit index, and unaided LoRA cells are mandatory.

7. **“Saturation” can be manufactured by the benchmark budget.** Each named
   baseline needs its own legitimate capacity policy, resource frontier,
   prospective equivalence-margin plateau rule, and simultaneous uncertainty.
   Losing to PCFL is not saturation.

8. **Depth may be decorative.** Depth must be the independently certified
   minimum number of life-specific causal bindings, with all shorter alternate
   proofs ruled out. Action length or prompt steps are different quantities.

9. **Cross-era success is not graph discovery.** The clean resolver may compose
   local key-value atoms under a known grammar. Include full facts with graph
   edges deleted and an exact sufficient-statistic program. Claim learned edges
   only if an edge intervention is necessary.

10. **Fixed rank is not compression.** Independent cohort permutations inject
    linear fresh entropy. Finite unused weight capacity, precision, candidate
    indexes, optimizer state, or rising training compute can masquerade as
    compression. Cut semantic compression from Paper 1.

11. **Pseudoreplication is an acute risk.** Targets, checkpoints, depths, twin
    sides, calls, and training seeds are nested. The independent unit is the
    world-life/twin pair. The four J/P DEV pairs provide no paper sample size.

12. **The implied Cartesian product is infeasible.** Outcome-dependent cell
    pruning would invalidate the surface. Preselect a small full-lifetime core
    and confine reader, rank, generator, and cut diagnostics to sentinel cells.

13. **The benchmark risks being a key-value toy.** Exact target-only Bayes
    controls, target-twin equality, graph-theoretic depth, and an eligible typed
    controller scoring one itemwise are prerequisites. Otherwise “action” is
    dressed-up QA.

14. **Compiler intelligence is unassigned.** A prompted teacher plus mechanical
    verifier/compiler can support corpus utility; it cannot support autonomous
    dreaming, a learned compiler, or amortized consolidation unless the
    compiler policy itself is frozen, reusable, and evaluated on whole held-out
    lives.

15. **Existing repo results are only feasibility evidence.** The G-series uses
    tiny worlds, approximately three world replications, heavy
    verified/mechanical processing, noisy LoRA transport, and recognition
    readers that carry substantial intelligence. J/P is explicitly DEV-only;
    Bubblewrap is only a CPU interface receipt. None is PCFL confirmation
    evidence.

## Minimum evidence package

### Full lifetime surface

Run one pre-native and at least three well-separated, powered post-native
checkpoints. Depths 1 and 4 should be primary; depths 2 and 3 can be
preregistered sparse diagnostics. At every primary checkpoint report new, old,
and cross-era action separately.

Core arms:

1. no persistent memory;
2. honest native context followed by frozen truncation;
3. strongest external-memory implementation selected on disjoint calibration
   lives, with native interface—likely A-MEM or a tuned linked/RAG system;
4. exact public sufficient-statistic graph/program;
5. faithful TMEM-style direct-QA/instruction-response LoRA;
6. target-blind compiled text;
7. identical-corpus compiled LoRA.

Matched end-of-life batch SFT should be included at least at sentinel
checkpoints. Voyager/PEAM need not be awkwardly reimplemented if their native
mechanisms do not map to PCFL, but the program/skill-library and
embodied-consolidation territories must be conceded in related work.

### Construct-validity package

- Total, rejection-free generator.
- Presealed target/cohort/depth/age manifest independent of support and
  compilation.
- Exhaustive target/twin model-visible byte equality.
- Exact target-only Bayes and fitted shortcut controls.
- Introduced, supported, compiled, retrieved, and action-usable coverage
  reported separately.
- Tokenizer-exact `L_native` including prompts, workspace, operation history,
  and output reserve.
- Monotone unique causal entropy/minimal-sufficient-statistic bits.
- Independent depth certificates and all alternate proof routes.
- Typed eligible-memory controller value 1 under exact caps in every valid
  cell.

### Causal and reader package

- Authentic versus twin-trained whole-life adapters on primary cells.
- Complete text-memory cuts on primary items.
- A smaller preregistered LoRA decisive-binding cut versus equal-size sham-cut
  panel with paired initialization, schedule, order, and training seeds.
- Candidate-assisted text and LoRA.
- Candidate-only clean base/no adapter.
- Wrong/twin adapter.
- Explicit index/text baseline.
- Unaided generative LoRA.
- Unconditional and authentic-success-conditioned action effects.

### Statistical and robustness package

- Completely disjoint calibration and confirmation world-life roots.
- Pair count chosen by blinded variance or conservative power simulation; four
  pairs are unacceptable. Without variance data, plan for at least tens of
  independent world-life/twin pairs rather than inflating `n` using nested
  targets.
- Pair-blocked intervals or hierarchical inference, multiplicity hierarchy,
  noninferiority margins, and conservative missing/failure handling.
- At least one generator-nuisance sentinel varying renderer/template/schedule,
  or explicit confinement to one frozen generator.
- Preferably a second backbone sentinel. Otherwise every conclusion must name
  the single frozen model.

### Resource package

For every headline arm: canonical bytes, training-view bytes and repetitions,
adapter precision, index/embedding/candidate bytes, active and retained state,
compiler/training/query/resolver calls and FLOPs, prompt tokens, latency,
failures, and number of downstream target actions used to amortize training.

## What to cut

Cut entirely from Paper 1:

- PCFL-Schema and all semantic-compression claims;
- on-policy self-improvement, exploration, and evidence-acquisition flywheel;
- learned scheduler, critic, outer LOOP adapter, and across-life controller
  learning;
- autonomous graph/schema discovery;
- generic or unnamed SOTA saturation;
- “unbounded,” “continual forever,” human-like, or generic-intelligence
  language;
- pointer-recursion as a headline result;
- full rank × reader × depth × age × intervention Cartesian sweeps;
- per-atom leave-one-out adapter retraining;
- containment/backend engineering from the scientific story;
- J/P and prior small-world scores as confirmation evidence;
- polished benchmark-platform engineering.

Do not cut the minimal reproducible generator/evaluator release. Do not put
“LoRA” in the title unless the LoRA arm survives the candidate-only and
same-corpus causal panel and occupies a meaningful Pareto point.

## Prewritten narrow title, thesis, and claim ladder

### Recommended title

> **PCFL-Stream: Causal Evaluation of Compiled Per-Life Memory Beyond the
> Context Window**

If LoRA earns a strong result:

> **PCFL-Stream: Attributing Text and Parametric Per-Life Memory in
> Long-Lifetime Agents**

### Thesis

> In controlled fixed-source action worlds whose independent causal content
> grows beyond a model's usable context, target-blind compilation of public
> action–outcome experience into per-life memory can preserve old bindings and
> support new and cross-era actions under fixed read and action budgets.
> PCFL-Stream separates compiler utility, memory substrate, and resolver
> contribution using matched lives, identical-corpus text/LoRA treatments, and
> counterfactual binding interventions.

### Claim ladder

- **C0 — Benchmark validity:** PCFL-Stream generates target-blind,
  shortcut-controlled lives with increasing independent causal information,
  certified dependency depth, and action targets beyond native context.

- **C1 — Compiled-text causality:** Target-blind compiled text improves
  fixed-budget PCFL action over raw/no-memory controls, and authentic binding
  cuts or twin substitutions directionally alter the decisive action.

- **C2 — Parametric transport:** Under the specified reader interface, a
  per-life LoRA trained from the identical compiled corpus transports
  life-specific bindings beyond clean-base, candidate-only, wrong-adapter, and
  direct-QA controls.

- **C3 — Finite lifetime capability:** Over the preregistered PCFL range, the
  compiled-memory system continues acquiring new mappings, retains old
  mappings noninferiorly, and improves cross-era action after raw history
  exceeds context.

- **C4 — Named baseline plateau, optional:** Only baseline implementations
  whose own simultaneous equivalence intervals satisfy the prospective plateau
  rule may be described as plateauing over that finite range.

- **C5 — Systems efficiency, optional:** Only if supported by the full resource
  frontier may the system claim a better observed
  action–storage–query–compute tradeoff.

Explicitly forbidden even after C5: compression, autonomous discovery,
universal SOTA superiority, naturalistic external validity, on-policy
self-improvement, or unbounded continual learning.

## Final disposition

This is potentially accept-worthy as a rigorous benchmark-plus-causal-
measurement paper. It is unlikely to be accepted as a novel LoRA architecture
paper, and it should be rejected if the authors retain the broad “self-learning
agents beat SOTA over lifetime” headline.

## Non-authority note

This advisory review makes no repository-governance decision. It does not
ratify PCFL-Stream, alter the current `awaiting_consensus` state, authorize any
implementation or edit beyond creation of this advisory file, authorize a
model/provider/network/GPU/experiment run, promote a DEV or CPU receipt, or
authorize any scientific or paper claim. Any such action remains subject to
the exact architecture-deliberation, human-ratification, independent-review,
and compute/scientific-claim gates in `AGENTS.md` and the applicable bound
change artifacts.
