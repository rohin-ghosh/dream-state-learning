# Handoff to Fable: finish depth-growing memory before Action World GPU work

The action prototype is ready as a CPU contract, but do **not** divert the
current GPU cycle from C3s/Blendyland. The next result needed is a genuine
verifier-free depth-2 memory. Advice for the active line follows.

## 1. State the current Blendyland result exactly

The 7B dreamer emitted the correct **operator family** (`PIGMENT_UNION`) and a
three-parent hypothesis, but its proposed set was Candy/Mandy/Dandy while the
true set was Candy/Dandy/Randy. Parser whitespace killed that emitted line,
but accepting it would still have produced a false memory.

Paper-safe language:

> The higher-order operator form appeared in scratch; exact parent recovery
> remains open.

Measure exact success@1 and success@k separately from operator-family recall.

## 2. Make depth grow across events, not only inside one giant call

Add a streaming micro-dream condition:

```text
new observation
-> retrieve 2-6 related episodic/derived memories
-> produce at most one new provisional thought
-> save retrieved parent IDs
-> later observations can reactivate that thought
-> depth accumulates across the lifetime
```

Compare:

1. batch table + one-shot dream;
2. sequential stream + no dreaming;
3. sequential stream + fixed one hop per episode;
4. sequential stream + salience-triggered extra hops.

The explicit parent graph is audit instrumentation. Do not feed a solved or
canonical dependency graph back to the model.

## 3. Stop deleting `UNRESOLVED`

The current self-check raises precision but loses true coverage. Preserve an
epistemic state:

```text
SUPPORTED    -> eligible for strong rehearsal/consolidation
PROVISIONAL  -> retain and schedule for later evidence retrieval
CONTRADICTED -> retain as a rejected/revisable hypothesis
```

Self-check should score two axes independently:

- fit to source observations;
- compatibility with existing LTM.

If evidence supports a candidate that conflicts with LTM, open a structural
revision branch. Existing LTM is a prior, not a truth oracle.

## 4. Use prediction to ground higher-order dreams

For every candidate connection require:

```text
claim
parent observation/memory IDs
derivation depth
at least one concrete prediction
supporting evidence
contradicting evidence
revised claim or status
```

Repetition is not independent support. Do not increase confidence because a
model paraphrased its own hypothesis several times.

## 5. Search before scale

Hold 7B fixed and sweep:

- hypothesis budget `k = 1, 4, 16`;
- dream rounds `r = 1, 2, 4`;
- fixed total-token comparisons where possible.

Only then compare a larger frozen dreamer at matched sampling/token budgets.
This separates a search/ranking failure from a model-capability failure.

## 6. Preserve the honesty ladder at every transition

Report higher-order claims at all of these points:

```text
appeared in raw scratch
-> parsed/normalized
-> self-check status
-> written to corpus
-> read from LoRA
-> used correctly in D3 behavior
```

The downstream table needs a genuinely separate `self-check + targeted drift`
row; the current published "four-arm" table contains only three downstream
rows. Also reconcile the C3s bookkeeping: the displayed verdict counts sum to
94 although the ledger says 100 parsed claims.

## 7. Keep prompt conditions named honestly

The instruction "is this outcome built from other situations combined?" is a
targeted meta scaffold. Keep it as a ceiling condition. The generic depth
condition should use only operations such as retrieve, notice, hypothesize,
predict, seek counterevidence, revise, and compress.

## Plug point when C3s is ready

`action_world/` exposes the next test without GPU dependencies:

```text
A0 witnessed action recall
A1 unseen-state procedural transfer
A2 world-law inference under a tight action budget
A3 two-state action-chain composition
```

Use the exact same no-gate / self-check / drift / perfect-ceiling corpus ladder
there. The parity solver in `action_world/solver.py` is offline/context-oracle
only and must never enter the cognitive loop.
