# Semantic World v0.2 — Fable handoff

Branch: `semantic-world-v02`

This branch adds a CPU-only replacement for the invalid v0 D3 mechanic. It
does not modify the frozen v0 implementation or any completed D0-D2 result.

## Accept it

```bash
PYTHONPATH=. python3 lands/test_v02.py
PYTHONPATH=. python3 lands/test_world.py
python3 -m compileall -q lands
git diff --check
```

The first command includes a 1,000-seed joint-identifiability sweep and should
finish in roughly ten seconds on CPU. Inspect one aligned lifetime with:

```bash
PYTHONPATH=. python3 -m lands.v02 render --seed 0 --skin aligned
```

## What changed scientifically

V0 D3 had two shortcuts: its meta signature copied an ordinary land in every
seed, and its three target anchors exposed one answer for every animal role.
The new diagnostic uses ratio-preserving pigment mixtures, known-parent demo
lands, and twelve independently queried target lands that each withhold the
queried role. Parent-set sizes sweep 2-5. The target operator and parents are
jointly identifiable, while ordinary copying and same-role lookup are
impossible.

A provenance-bearing workshop phase grounds every weighted-color/state token
before the dispersion gap. This is necessary for neutral-skin identifiability;
without it, the evaluator would know what a nonce mixture token means while the
model never had evidence from which to learn that mapping.

Each target also has a public survey record saying it belongs to the same
jointly-fed/confluence class as the known-parent demonstrations. The record
never exposes parent identity or count. Do not remove it from neutral runs;
otherwise only English target names supply the operator-transfer cue.

Canonical details and the experiment ladder are in
`research_notes/37_semantic_world_v02_spec.md`.

## Stable CPU interface

```python
from lands.model import WorldConfig
from lands.v02 import SemanticWorldV02

world = SemanticWorldV02(WorldConfig(seed=0))
public_lifetime = world.render_lifetime("aligned")
public_goals = world.render_goals("aligned")
offline_report = world.identifiability_report()
```

`offline_report` is evaluator-only. Never place its operator survivors,
parent candidates, hidden roles, or answers in model context.

## First model contact

Before wiring the dreamer, run a clean-model gameability gate over the full
public lifetime. Then add an oracle atomic-memory ceiling. The first learned
condition should reuse C3e's epistemic-state loop but emit two new memory
kinds:

```text
BLEND_OPERATOR | operator=PIGMENT_SUM
BLEND_PARENTS | land=<target> | parents=<land>[,<land>...]
```

`BLEND_PARENTS` must accept 2-6 unique source lands, sort them canonically,
and reject demo/target lands as parents. The recognition candidate space is
the declared 57 source subsets of sizes 2-6; it must not use the generator's
true five-parent maximum or evaluator answers to prune that set.

The model self-check may retrieve source observations, public feed relations,
and its own provisional memories. The exact CPU audit is an offline scorer
only. Preserve raw dream text, proposal depth/parents, self-check verdicts,
and the evidence IDs used for every decision.

Do not immediately train LoRAs. First establish that:

1. the clean model can solve the game with all evidence in context;
2. an oracle atomic read plan reaches a high composition ceiling; and
3. verifier-free recurrent dreaming proposes the operator and exact parent sets.

These gates have now been run. Direct and generic one-pass conditions score
0/12, the oracle-resolved clean composer scores 9/12, and the verifier-free
atomic branch/revisit ceiling with Qwen2.5-32B discovers 23/24 exact parents
and answers 23/24 on untouched aligned seeds 1-2. The controller exhaustively
checks 57 public source subsets with two atomic LLM proof leaves each; this is
an expensive prompt/controller ceiling, not yet learned dreaming or a LoRA
result. Full protocol, scale ablation, defects, and caveats are in
`research_notes/39_v02_branch_depth_results.md`.

Once those pass, compare context+recognition against LoRA+recognition using the
same corpus and query plan. The just-completed v0 result says these should be
equal at 65 lines; v0.2 becomes useful for weights only when the memory horizon
is swept past the available prompt budget.

## Next GPU run: compress the exhaustive ceiling

The proposal-first runner is ready. It asks for one ranked 12-candidate
frontier per target, applies the same atomic checks only to that frontier, and
reports proposal success@1/2/4/8/12, unique self-selection@k, revisit accuracy,
and exact model-query/token accounting. Start with an untouched aligned seed:

```bash
PYTHONPATH=. python3 alchemy/run_lands_v02_topk.py \
  --skin aligned --seed 3 --k 12 \
  --model Qwen/Qwen2.5-32B-Instruct

PYTHONPATH=. python3 alchemy/run_lands_v02_finish.py \
  --input-artifact alchemy/v2_out/lands_v02_topk_aligned_s3_qwen-qwen2-5-32b-instruct_k12.json \
  --model Qwen/Qwen2.5-32B-Instruct

PYTHONPATH=. python3 alchemy/run_lands_v02_recipe_recheck.py \
  --input-artifact alchemy/v2_out/lands_v02_topk_aligned_s3_qwen-qwen2-5-32b-instruct_k12_finish.json \
  --model Qwen/Qwen2.5-32B-Instruct
```

Do not tune the proposal prompt on seed 3. If proposal success@12 is weak,
inspect only aggregate failure modes, revise on development seed 0, then freeze
again before a new seed. The primary compression curve is proposal success@k;
final-answer accuracy is downstream and should not hide proposal misses.

The checked-in atomic controller is deliberately **aligned-only**. Its
canonical source-cell reader currently assigns conventional recipes to color
words. Reusing that helper on neutral or conflicting skins would inject the
latent recipe gauge. Before skin fan-out, add a model-generated `RECIPE_GAUGE`
memory: infer the six ordinary state-token recipes jointly from the two public
known-parent demonstrations and calibration mixtures, then freeze and score
that memory before parent search. Do not derive it from `Skin.colors`.
