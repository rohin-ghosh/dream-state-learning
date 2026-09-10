# Experience Model v6 discussion context

Status: non-authoritative synthesis for fresh-context deliberation. The
verbatim owner directive controls. This file records the immediately preceding
discussion so that the deliberators need not infer it from a mutable chat.

## Architecture hypothesis under discussion

- There is one recurrent cognitive loop. Awake thinking, planning,
  self-criticism, daydreaming, and dreaming are invocation conditions of the
  same frozen base model, not separately trained thinker, dreamer, planner, or
  verifier modules.
- The context window plus ordinary files, retrieval, tools, goals, and public
  world state form the conscious working space. These capabilities remain
  available to both the proposed system and strong ordinary-agent controls.
- The only within-life learned parameter object is one per-life LoRA mounted
  directly on the same model that thinks and acts. Its updates may change
  factual associations, abstractions, hypothesis generation, evidence seeking,
  search allocation, tool use, revision, and stopping together.
- SLEEP is a write/compiler operation, not a second learned intelligence. It
  transforms public thought--action--outcome traces into bounded training
  sequences and applies the LoRA update. It may invoke the same frozen loop to
  propose summaries, counterfactuals, or cross-experience connections, but
  those proposals gain authority only from ordinary outcomes.
- External feedback already reaches normal agents transiently. The proposed
  mechanism attempts to metabolize it into a persistent change in future
  inference after the originating context has disappeared.
- Surprise or prediction--outcome mismatch is a candidate priority signal for
  extra thinking/replay. For the first causal experiment, cadence and total
  compute may need to remain fixed so adaptive scheduling is not confounded
  with extra resources.
- A life may span multiple related environments. The LoRA persists across
  environment changes and resets only between independent replicated lives.
  This permits forward transfer, retention, adaptation, and later hybrid tasks
  that require structure learned separately.
- Low rank is hypothesized to be a scientific inductive bias, not merely a
  cheap storage format. With sparse verified experience, a constrained update
  may force recurring corrections into shared directions; too little rank may
  underfit and too much may memorize. This is a registered hypothesis requiring
  a capacity/generalization curve, not an assumed fact.
- The recurrent loop creates candidate synthetic data. Low-rank
  parameterization does not itself create data; it shapes how verified
  experiences and generated hypotheses generalize when consolidated.
- Eventual promotion of many high-quality lives into base-model training is a
  later-scale extension, not required for the first experiment.

## Proposed empirical center

Use an off-the-shelf GPU-kernel environment rather than designing another
semantic world. KernelBench supplies 250 real PyTorch workloads and objective
correctness/speed feedback. KernelBench-Verified adds TF32 baselines and
multi-distribution hidden correctness checks to reduce reward hacking:

- https://arxiv.org/abs/2502.10517
- https://github.com/ScalingIntelligence/KernelBench
- https://arxiv.org/abs/2607.16241
- https://github.com/facebookresearch/kernel_bench_verified

A minimal scout discussed before intake used related but nonduplicate
acquisition kernels, sealed held-out probes, clean context per task, periodic
sleep writes, and the identical ordinary agent with no loaded LoRA as the first
control. Stronger controls include the same compiled experiences as text/RAG,
raw-trajectory LoRA, outcome-shuffled LoRA, adapter-off checkpoint replay, and
wrong-life adapter swap.

Held-out checkpoint performance, not best training score, is the scientific
endpoint. Incorrect kernels score zero. Same-family transfer, compositional
transfer, first-attempt correctness/speed, attempts to first correct,
retention, wall/token/tool cost, and learning-curve area are candidate
measurements. Training and evaluation task graphs/shapes must be deduplicated,
evaluation feedback must never enter the living agent, and timing must be
isolated and repeated.

The first scout need not beat every external-memory or SOTA kernel agent. It
must establish whether the authentic adapter carries outcome-grounded
action value on unseen related kernels relative to adapter-off and
outcome-shuffled controls. A paper claim requires independent lives and a
strong external-memory baseline.

## Prior work disposition under discussion

- Preserve RML, FeltCraft, Blendy/Semantic World, substrate, proposal--verify,
  and false-write results as mechanism evidence, controls, and regression
  fixtures.
- Demote the pending RML-G1 234-call supplied-gold controller run as the next
  scientific priority. It tests a reader for an older modular architecture and
  does not test longitudinal LoRA learning.
- Reuse its strongest control ideas: target sealing, counterfactual twins,
  outcome shuffling, adapter swaps, clean-context evaluation, immutable
  public ledgers, and strict claim boundaries.

## Decisions the deliberation must make

1. Whether the proposed one-loop/one-LoRA architecture is internally coherent
   and materially distinct enough to justify a new v6 subtree.
2. Which off-the-shelf gym and exact subset can produce related, nonduplicate
   lifetime structure on held hardware without building a new benchmark.
3. The minimum wake trace, sleep compiler, LoRA target/rank bracket, update
   cadence, replay rule, and bootstrap prompt needed for an honest scout.
4. Which controls are indispensable in the first GPU run versus conditional on
   a signal.
5. What result would establish only a positive experiential-learning slope,
   what would support abstraction, and what remains outside the paper claim.
6. Exact CPU/canary gates, budgets, stopping rules, reproducibility artifacts,
   and human ratification boundary before implementation or GPU execution.
