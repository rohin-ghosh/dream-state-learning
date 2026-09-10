# When Should Experience Become Weights? — FeltCraft-Lifetimes proposal v2

**Status:** successor design proposal; no implementation or compute authority.

## Scientific question

When does a fixed pretrained agent benefit from compiling its own public
action--outcome history into connected, lossy experiential knowledge, rather
than retaining exact text or graph memory, as the life acquires new causal
structure beyond native context?

The paper is a causal lifetime phase diagram plus a reference
Dream--LoRA--Think system. It does not claim priority on reflection, dreaming,
continual learning, LoRA memory, or agent memory. The broad architecture is:

```text
public action/outcome life E
  -> fixed THINK/DREAM resolver phi
  -> chronologically grounded local claims G
  -> deterministic SLEEP compilation
  -> identical compiled text and MEMORY-LoRA corpora
  -> bounded recurrent THINK reconstruction
  -> later held-out actions
```

LoRA is a transport/amortization substrate. It does not receive credit for
discovery or multi-hop reasoning. The explicit graph is expected to win or tie
arbitrary exact lookup in RANDOM worlds. A negative phase diagram is valid.

## What v2 changes

V1 confounded reusable structure with different realized experience: its
public-history-dependent collector could take different later actions after
different hidden outcomes. V2 removes that confound.

For a fixed `(super_seed, twin)`, RANDOM and MOTIF now share:

- opaque handles, sites, inventories, budgets, and target bytes;
- the same hidden physical recipe graph;
- the same open-loop source action arguments;
- the same action outcomes and identified handle-local causal atoms.

Only descriptor alignment differs. Within each opaque family, MOTIF keeps one
descriptor-to-role alignment across instances; RANDOM independently permutes
the alignment per source instance. A new target instance uses the same
descriptor attachment in both regimes. Thus the identified regime estimand is
the value of reusable cross-instance alignment at fixed physical experience.

Counterfactual twins do a different job. They preserve visible target bytes
but change the hidden graph and correct plan. Whole-memory twin swaps test
whether behavior depends on the authentic learned life. Twin and regime effects
are never pooled.

## Developmental axis

Sixteen repetitions of one schema would be exposure, not developmental
learning. V2 therefore adds new opaque families over the life:

```text
source instances e = 0..15
family(e) = floor(e / 2)
cuts after e-count = [2, 4, 8, 16]
families available = [1, 2, 4, 8]
```

Every family samples a fresh hidden alignment and contributes four new causal
recipe relations. Every instance contributes fresh handle-local relations.
The reported panels separate:

- newest-family acquisition;
- family-0 old retention;
- old+new constructive action;
- prospective use on a fresh sparse instance of an old or new family.

CPU v2 establishes exact finite-world eligibility only. Later model-scale cuts
must include at least three strictly post-native checkpoints with increasing
unique families and relations before any growth, saturation, or crossover
claim.

## Claim ladder

1. **Instrument eligibility:** deterministic coupled world, per-target
   solvability, exact selection-conditioned posterior, and leakage gates.
2. **Representation/use:** under one common source deck, compiled memory
   improves held-out action beyond every frozen primary baseline.
3. **Development:** new-family acquisition, old retention, and constructive
   use persist over at least three post-native cuts.
4. **Prospective schema generalization:** a pretarget schema improves sparse
   fresh-instance action beyond target-local atoms in MOTIF but not RANDOM.
5. **Compression:** claim 4 plus a frozen prefix-free representation that is
   strictly shorter than enumerated atoms at matched edge and action loss,
   including template, model selection, exceptions, provenance, decoder, and
   active-index cost.
6. **Parametric transport:** identical-corpus MEMORY LoRA is noninferior to
   compiled text and beats direct trajectory/QA LoRA at fixed read policy.
7. **Flywheel:** only a later randomized on-policy study may claim that memory
   improves information acquisition, later memory, and later action.

No lower rung inherits a higher one.

## Reference system held for later gates

- `theta_0`: frozen action/reasoning model.
- `theta_m`: frozen auxiliary reader base.
- `phi`: fixed recurrent typed-operation resolver used in THINK and DREAM
  modes; Paper 1 does not train it within a life.
- `E`: immutable public action/outcome log.
- `G`: append-only semantic/provenance shadow, never exposed as a global oracle
  graph to the model.
- `Z`: bounded token-space cited path/workspace.
- `psi[life,cut]`: one cumulative per-life MEMORY LoRA rebuilt from the clean
  reader base at each sealed cut.

THINK performs one local query/path/backtrack/execute operation at a time.
DREAM performs broader target-blind replay and may propose one local atom,
question, revision, schema, or supported two-edge shortcut. Neither self-check
nor repetition makes a claim true. Only a later ordinary public outcome,
unavailable at proposal time, can append support or contradiction.

SLEEP is a deterministic compiler over supported content. It canonicalizes,
deduplicates, interleaves old/new material, emits frozen one-edge access views,
and may materialize a frequently traversed shortcut only from supported roots
with retained provenance. It cannot invent semantic content.

The headline read is a generative one-atom read. Recognition over a frozen,
public, constant-size candidate set is an assisted diagnostic. Recurrent THINK
assembles hops in tokens; the adapter is unmounted while the clean action model
acts.

## Benchmark phases

1. Exact CPU v2 instrument falsification from `world_contract.md` and
   `measurement_contract.md`.
2. Known-good explicit SOURCE/SCHEMA information through the generic recurrent
   thinker.
3. Same legal history represented as native long context, iterative episodic
   RAG, A-MEM-style linked memory, exact graph, explicit Bayesian/MDL schema,
   reflection text, Auto-Dreamer-like text, direct-QA LoRA, compiled text, and
   identical-corpus compiled LoRA.
4. Learned/amortized DREAM writer against the gold compiler and atom/schema
   ablations.
5. Growth confirmation at post-native cuts.
6. Separately designed on-policy flywheel.

The exact graph and explicit Bayesian motif learner are primary baselines, not
oracles to omit. Batch SFT is an upward resource reference. Every method gets
the same public source events within a cell; total lifecycle compute, retained
bytes, hidden candidate work, query count, latency, and GPU hours are reported.

## Paper decision rule

The paper survives any of these honest outcomes:

- graph dominates: a benchmark/phase-diagram result locating where weights do
  not help;
- compiled text helps but LoRA does not: experiential compilation paper;
- compiled LoRA matches text beyond context with better access/resource trade:
  parametric experiential-memory transport result;
- learned DREAM recovers the gold-compiler benefit: full reference-system
  result.

The paper fails if the world is shortcut-solvable, schema value exists in
RANDOM, unique structure does not grow, exact graph has no imposed access cost
but is nevertheless called saturated, or outcomes cannot be attributed to
legal public experience.

## Requested authority

This proposal requests no current implementation authority. After two fresh
exact interpretations, adversarial critique, concern-by-concern consensus, and
explicit human ratification of the final bytes, the first scope may implement
and run only the deterministic local CPU instrument and its exact controllers,
codecs, leakage checks, and receipts. It may not call models, tokenizers,
providers, GPUs, remote nodes, or implement scientific DREAM/SLEEP/LoRA code.
