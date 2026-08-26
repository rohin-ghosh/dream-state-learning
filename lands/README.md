# Semantic World v0

CPU-only instrument for the prior-anchored LANDS experiment.  The canonical
scientific contract is
[`research_notes/34_semantic_world_v0_spec.md`](../research_notes/34_semantic_world_v0_spec.md).

## What is implemented

- deterministic animal-role × land-palette factor worlds;
- a uniquely identifiable three-parent Blendyland pigment-union rule;
- temporally dispersed lifetimes;
- D0 lookup, D1 local projection, D2 cross-palette composition, and D3
  meta-rule goals;
- canonical dependency proofs for every goal;
- aligned, neutral, and prior-conflicting skins over identical latent data;
- witnessed/entailed/counterfactual claim verification with query budgets;
- lookup, bounded-context, best-window, full-lifetime, and oracle ceilings;
- evaluator-separated, checksummed artifact export.
- canonical positive-only claim grammar and one-hop atomic QA corpora using
  the measured 200-touch / 3x-rule exposure recipe;
- per-goal unresolved and resolved context-oracle prompts for the pre-training
  ceiling gate.
- a priced reachout session that turns deliberate visits into cited lived
  evidence while blocking exact evaluation targets by default.

No model or GPU is used here.  This package is the environment/evaluator
boundary that the proven G-series dream and read-only LoRA pipeline should
consume.

## Experimental v0.2 D3 replacement

The original v0 D3 mechanic is retained for reproducibility but is now known
to be observationally underspecified. `lands/v02.py` contains the CPU-only,
versioned replacement with additive pigment ratios, operator demonstrations,
hidden-role target lands, and a 1,000-seed adversarial identifiability audit.
See `research_notes/37_semantic_world_v02_spec.md` before using D3 results.

```bash
PYTHONPATH=. python3 -m lands.v02 audit --seeds 1000
PYTHONPATH=. python3 lands/test_v02.py
```

## Commands

```bash
PYTHONPATH=. python3 -m lands.cli inspect --seed 0 --skin aligned
PYTHONPATH=. python3 -m lands.cli baselines --seeds 0 1 2
PYTHONPATH=. python3 -m lands.cli generate --seed 0 --output /tmp/lands-v0-seed0
PYTHONPATH=. python3 lands/test_world.py
```

The exporter refuses to overwrite a non-empty directory.

## Integration surface

```python
from lands import SemanticWorld, WorldConfig

world = SemanticWorld(WorldConfig(seed=0))
lifetime = world.sample_lifetime()
goals = world.eval_goals()          # or depth="D3"
aligned = world.render("aligned")
oracle = world.oracle_structure("aligned")
proof = world.proof_for(goals[0])
leaves = world.atomic_memories_for(goals[0], "aligned")
oracle_prompt = world.context_oracle(goals[0], "aligned")
reachout = world.start_reachout("aligned")
new_observation = reachout.act("cow", "Candyland")
```

For ordinary model experiments, give the player only
`model_input/public/<skin>/`.  Files under `model_input/oracle/<skin>/` are
privileged controls, not ordinary experience.  Keep `evaluator_only/` out of
all model context and retrieval indices.  `world.render()` follows the same
rule: its default view has no answers, depth labels, proof metadata, or oracle
memories; answers require the explicit `include_answers=True` opt-in.
