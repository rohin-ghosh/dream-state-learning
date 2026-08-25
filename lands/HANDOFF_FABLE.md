# Semantic World v0 — Fable handoff

Status: CPU instrument complete; no GPU training was run on this branch.

This is the first runnable version of the Candyland/Blendyland idea. It is a
frozen measurement instrument, not a claim that the learned system solves it.
One latent world is rendered through aligned, neutral, and prior-conflicting
skins, while the exact same held-out goals and proof graphs remain underneath.

The implementation follows the measured constraints in
`research_notes/33_semantic_world_gpu_constraints.md`: executable claims,
nameable abstractions, one-hop atomic read leaves, positive canonical answers,
provenance on every experience line, balanced depth/kind splits, and an
explicit context-oracle hook. The full design rationale and falsifiers are in
`research_notes/33_semantic_world_v0_spec.md`.

## Accept this branch

From the repository root:

```bash
PYTHONPATH=. python3 lands/test_world.py
PYTHONPATH=. python3 alchemy/test_integrity.py
python3 -m compileall -q lands
git diff --check
```

Then inspect one world and the measured CPU ceilings:

```bash
PYTHONPATH=. python3 -m lands.cli inspect --seed 0 --skin aligned
PYTHONPATH=. python3 -m lands.cli baselines --seeds 0 1 2
```

Generate the fully separated model/evaluator artifacts:

```bash
PYTHONPATH=. python3 -m lands.cli generate \
  --seed 0 \
  --output /tmp/semantic-world-seed-0
```

The exporter refuses to overwrite an existing directory.
`model_input/public/<skin>/` has only lifetime streams, unanswered goals, and
the claim grammar. `model_input/oracle/<skin>/` contains explicit privileged
oracle memories and context-oracle prompts. The evaluator side alone contains
answers, proof graphs, latent structure, and deterministic baselines. Every
artifact has a hash in `manifest.json`.

## Plug points

The shortest path to a learned run is:

1. Feed `SemanticWorld.render(skin).observations` to the existing dreamer.
2. Require each dreamer proposal to contain one `ClaimCodec` line plus its
   cited observation IDs. Parse the claim and pass those IDs to
   `SemanticWorld.verify_claim` before storage.
3. Feed accepted claims to the existing claim graph, coverage-driven
   re-dreaming, naming, and atomic-QA emitter. Do **not** use the oracle proof
   leaves in this learned condition.
4. For the C1 context control, use
   `SemanticWorld.atomic_memories_for(goal, skin, resolved=...)`.
5. For the C2 known-positive write-format control, train on
   `build_atomic_corpus(world, skin)` using the encoded recipe: facts 8-way
   duplicated for 25 epochs (200 touches), rule facts 24-way duplicated (600
   touches). Train in a subprocess; at evaluation mount the adapter only for
   atomic reads, then unmount it for clean-base composition.
6. Query the goal from `RenderedWorld.goals`; score exact decoded colors with
   the evaluator artifact.

Key interfaces:

```python
from lands import SemanticWorld, WorldConfig
from lands.claims import ClaimCodec
from lands.corpus import build_atomic_corpus

world = SemanticWorld(WorldConfig(seed=0))
public = world.render("aligned")
codec = ClaimCodec(world, "aligned")
proposal = {
    "claim": "CELL | animal=frog | land=Candyland | color=purple",
    "evidence_ids": ["obs_00000"],
}
claim = codec.parse(proposal["claim"], claim_id="dream_00000")
verified = world.verify_claim(claim, proposal["evidence_ids"])
corpus = build_atomic_corpus(world, "aligned")
prompt = world.context_oracle(public.goals[0].goal_id, "aligned", resolved=False)
reachout = world.start_reachout("aligned")
new_evidence = reachout.act("cow", "Candyland")
```

`context_oracle(..., resolved=False)` tests whether clean-model inference can
compose the same atomic leaves the adapter would store. `resolved=True` moves
source-value resolution into the read protocol and isolates only the final
meta composition. `compose_atomic_answer` is the deterministic integrity
oracle proving that those leaves are sufficient; it is not a model baseline.
The oracle leaf/corpus APIs are forbidden in C3/C4; they are deliberately
privileged controls and do not derive their contents from dreamer claims.

## First GPU matrix

Do not begin with end-to-end dreaming. Preserve causal identifiability:

| Stage | Write input | Read input | What failure means |
|---|---|---|---|
| C0 | none | full lifetime context | clean-model/context ceiling |
| C1 | none | context-oracle atomic leaves | read/composition protocol is broken |
| C2 | oracle atomic corpus | bare goal | parametric transport/write recipe is broken |
| C3 | verified dreamer claims converted to QA | bare goal | abstraction or coverage is broken |
| C4 | verified re-dreaming + second-order claims | bare goal | incremental/meta-memory limit |
| C5 | C4 + priced reachout on uncovered structure | bare goal | active evidence acquisition limit |

Run each stage on all three skins and at least three world seeds. Report D0,
D1, D2, and D3 separately; the preregistered primary contrast is
analogy/composition (D1–D3) minus situated lookup (D0), not overall accuracy.
Compare each depth against the published answer-kind majority floor.

For C1, test both `resolved=False` and `resolved=True`. That separates a model
that cannot retrieve/resolve source values from one that cannot perform the
final pigment union. For C2, begin with the measured LoRA setting from the L0
ledger (rank 64, learning rate 2e-4), include an LR sanity ladder, and count
actual touches per unique fact.

The latest G-series result makes C5 mandatory, not decorative: G4j's
second-order family merge could not fire because the relevant family pair had
no lived evidence. G4k spent one world action on that gap, verified the new
rule, merged the families, and raised the three-world line to
0.949/0.882/0.923 (mean 0.918). `ReachoutSession` is the matching instrument:
surface-name actions, fresh provenance IDs, explicit accounting, and exact
evaluation-target visits blocked by default. Any reachout action must be added
to the experience available to matched baselines.

## CPU acceptance evidence

- Default world: 69 observations in 23 episodes; 48 goals, exactly 12 per
  depth. D0–D2 have two examples of each of six outcomes; D3 has four examples
  of each of three outcomes.
- Sixty-seed sweep: full-lifetime and oracle solvers are 1.0 on every depth;
  every oracle-selected 12-observation window is 0.0 on D2 and D3.
- Across those seeds, 17,280 skin/depth/mode atomic compositions exactly match
  the evaluator answer.
- Every one of 105 fixed surface cells changes answer across seeds in aligned,
  neutral, and conflicting skins; the answer token is never present in the
  question.
- Artifact export is byte-reproducible, checksummed, and tested so public
  directories cannot contain phase/depth/tags, evaluator answers, or oracle
  files.

## Non-negotiable audit rules

- A verified claim can be `witnessed`, `entailed`, or `counterfactual`.
  Counterfactual verification consumes an explicit engine-query budget and
  must be counted as experience for every baseline.
- Do not pass latent IDs, roles, rotations, palettes, parent sets, answers, or
  proof graphs to a model condition unless that condition is explicitly named
  oracle.
- Do not select a rulebook or prompt using evaluator answers.
- Keep provenance IDs when converting observations into dream evidence.
- Deduplicate claims before exposure multiplication. Repetition is a storage
  treatment, not additional evidence.
- Symmetric relations are canonicalized by the codec. Never teach only one
  arbitrary direction and then score both directions.
- Exact held-out final-answer QA pairs are absent from the oracle corpus for
  D1–D3. Keep that invariant when adding dream-generated memories.

## What is deliberately not implemented

There is no learned thinker/dreamer policy, no LoRA training launcher, no
replay scheduler, and no claim-to-memory optimizer here. Those belong in the
existing GPU pipeline. The world currently uses six source lands and a hidden
three-parent pigment-union meta-land; it tests one second-order operator at one
depth. Observation budget is measured in records, not tokenizer-specific
tokens. These are boundaries of v0, not hidden generality claims.

If a new mechanic is added, preserve the existing v0 unchanged and version the
generator. The current proof-shape, balance, surface-leakage, context-break,
claim-budget, corpus, and artifact-separation tests are the minimum acceptance
bar for v1.
