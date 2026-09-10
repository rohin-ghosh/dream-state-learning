# LOOP-adapter experiment audit (post-B3 advisory)

Status: design advice only. This is not an authorization, preregistration, CPU
implementation request, model call, GPU run, or Paper-1 scope change.

## Boundary and target claim

The current PCFL-Active-Stream contracts deliberately exclude a learned LOOP
adapter, a rank sweep, and Stage-D LoRA work. They terminate at B3 with
`DEFERRED_NEW_PREREGISTRATION`; `NOT_REQUESTED_STAGE_D` is the applicable
status for the current text claims. A successor can be considered only after
the B1/B2/B3 text artifacts are sealed, with a new architecture change,
independent review, exact byte/resource scope, and explicit human
ratification. It must use untouched roots and must not edit or reinterpret
RML-D0, G1/G2, or the active-stream roster.

The narrow causal question should be:

> With a frozen base model and a freshly reset per-life memory, does an
> across-life LOOP LoRA trained on verified public action trajectories change
> reusable search/traversal operations on a whole unseen world, and thereby
> improve later legal action success, beyond the same facts in bounded text,
> content-memory LoRA, generic/skill prompts, ordinary trajectory SFT, and a
> faithful TMEM-class direct-write comparator?

This is a claim about a reusable operation-policy prior. It is not a claim
that LoRA is a new fast-weight method, that the adapter is content-free, that
it learned an algorithm, or that it establishes agency, creativity, general
reasoning, or continual learning in general. The first positive result should
be worded as “across-life experience-conditioned operation policy transfer”
unless a separately authorized study establishes more.

## Recommended minimal experiment

Use two stages with one common frozen operation algebra and reader. Do not
start with a rank pyramid or a full memory/policy Cartesian product.

### Stage 1: cheap operation-transfer assay

Train candidate shared LOOP adapters on verified trajectories from source
worlds. The base, tokenizer, operation grammar, layer set, optimizer, number
of examples, and training seed manifest are common. The LOOP adapter is frozen
before any evaluation life. Source worlds, DEV worlds, and evaluation worlds
are disjoint at the entire world-root level; remapped labels, handles, hidden
mappings, and skins do not cross the split. Use a small fixed allocation such
as four source worlds, two DEV worlds, and four untouched evaluation worlds,
with one fresh life per evaluation world for this pilot. This stage is a
fail-fast transfer diagnostic, not a powered claim.

The model-visible training example is a pre-operation public state, legal
menus, the bounded common-reader return, and the next legal operation. The
primary loss is on a finite operation-family token and, in a separate
diagnostic head/field, an allowed public argument token. The alphabet must
make search state explicit: `BFS_STEP`, `DFS_STEP`, `QUERY`, `BACKTRACK`,
`WRITE`, `ACT`, `DEFER`, and `STOP`, with explicit frontier/stack/depth and
visited-state fields. BFS/DFS labels are meaningful only if the controller
actually maintains a frontier/stack and the operation executes it; free-form
chain-of-thought is not an operation measure.

Trajectories are selected by a frozen teacher/exhaustive controller and
verified offline for legality and terminal return. The model never sees the
hidden proof, target answer, target allocation, latent mapping, evaluator,
scorer, or future outcome. The trajectory prefix ends before the selected
operation's terminal target result is released. Previous ordinary outcomes may
be present only as public state. Unsupported rationales, post-hoc explanations,
answer-bearing summaries, and hindsight labels are dropped. Every input,
target, mask, order, identifier, length, seed, and selection decision needs
byte lineage; a semantic statement that “the answer was not included” is not
enough.

At byte-identical cloned public states, randomize only the mounted LOOP
assignment (null, authentic, binding-shuffled, and cross-world-shuffled
controls). Hold base, per-life memory/read result, prompt, decoding, RNG,
cache, budgets, and public bytes fixed. Record legal logits and sampled
operations, not only the final action. The primary Stage-1 measurements are:

- next-operation distribution and oracle-free predeclared operation alignment;
- BFS versus DFS choice, branch/frontier coverage, depth, revisit and
  backtrack timing;
- query target/type, adaptive versus redundant queries, return-use rate, and
  information gain;
- write attempts, accepted provenance-grounded writes, duplicate/contradicted
  writes, and write timing; and
- operation count, reader calls/bytes, action calls, latency, FLOPs/tokens,
  and adapter/storage bytes.

The held-out-world probe uses renamed structural motifs and counterfactual
binding permutations. A gain only on source-world labels, exact handles, or
seen trajectories is memorization. A gain on new handles and hidden mappings,
with the expected operation shift surviving binding shuffles but disappearing
under policy shuffles, is evidence for transfer of an operation disposition.
It remains a total effect plus an operation association; it is not mediation.

### Stage 2: small-memory action endpoint

Run only after Stage 1 passes its installation, leakage, reset, and transfer
checks. Use a deliberately small, matched memory envelope so the fact-memory
comparison is interpretable:

| Factor | Primary cells |
|---|---|
| Per-life content state | `M-TEXT`: exact supported facts/provenance in bounded text; `M-LORA`: the same eligible fact targets trained into a freshly reset content adapter; `M-NULL` as floor |
| Shared operation state | `P-NULL`; `P-TEXT`: bounded generic operation examples; `P-SKILL`: a fixed verified skill library; `P-TRAJ-SFT`: ordinary SFT on the same verified trajectories; `P-LOOP`: operation-target LOOP LoRA |
| Comparator | Faithful primary-source-bound TMEM-class direct-QA/instruction-response online fast-weight comparator, with its exact trigger, extraction target, rank, update, and across-rollout state frozen before results |

The expensive endpoint need not execute every product cell. Predeclare the
full Stage-1 policy ladder on `M-TEXT`, then carry `P-NULL`, the strongest
prompt/skill condition, `P-TRAJ-SFT`, TMEM, and `P-LOOP` into the
`M-TEXT`/`M-LORA` action cells. Keep `M-TEXT` within the same small token and
reader-return envelope as `M-LORA`; report the fact recall ceiling separately.
If the content adapter has a different parameter count, training time, or
optimizer state, report the exact resource vector rather than calling it
matched. An additive content-plus-LOOP mount is a useful unmounting diagnostic,
not proof that the latent neural factors are cleanly separable.

Each evaluation life receives a new `(world_id, skin_id, life_id)` memory
adapter, episodic store, semantic ledger, index, optimizer, context, KV/cache,
and RNG namespace. The shared LOOP adapter is loaded read-only and is never
updated by evaluation outcomes. No trajectory, prompt history, reader cursor,
target, result, or process handle crosses lives. Pre/post reset hashes and
prior-life canaries must fail closed. This separation is essential: content
belongs to the local memory factor; reusable operation bias belongs to the
across-life LOOP factor.

Use presealed early, middle, and late lifetime checkpoints in each test life,
with new cohorts and old/recent/cross-era goals. Keep targets and support
opportunities fixed before outcomes, and apply the strict realized
payload-age/context rules inherited from the frozen PCFL discipline if the
same world machinery is reused. An old target is not dropped when acquisition
fails. Evaluation is sterile: outcomes can score the row but never update
memory, LOOP, compiler, candidates, or later opportunities.

The endpoint value is the legal executed action trajectory and terminal world
return under the cap. Report action success/return/regret and recovery after
backtracking, alongside the operation trace. Correctness never comes from a
record type, adapter completion, citation, reader receipt, or compiler object.
The primary causal contrasts are the LOOP-versus-null difference within each
memory substrate and the difference of those effects between `M-TEXT` and
`M-LORA`. Do not call this an indirect effect through a path unless a future
proposal adds a predeclared operation intervention and one identifying
indirect-effect estimand.

## Baseline and identification requirements

The null and text controls need to be strong enough to defeat the obvious
alternative explanations.

- `P-TEXT` receives the same bounded operation demonstrations and byte budget
  that motivate LOOP; `P-SKILL` receives generic, world-independent BFS/DFS,
  query, backtrack, and write procedures with no life-specific facts.
- `P-TRAJ-SFT` is ordinary next-token trajectory SFT on the same verified
  corpus and resource envelope. If it matches LOOP, the result is trajectory
  SFT, not a LOOP-specific mechanism.
- TMEM must be a fidelity-audited comparator, not a weak reimplementation.
  Fast-weight policy adaptation, direct QA/instruction-response extraction,
  online LoRA updates, and outcome-trained extraction are occupied territory;
  absent bound primary-source bytes and a fidelity table, no novelty or
  superiority language is allowed.
- `M-LORA` is content-target-only and `M-TEXT` is its bounded text realization;
  neither receives operation traces. A content-only gain that changes query
  choices is expected to be reported as residual non-identifiability, not as
  proof of policy learning.
- Include raw-history/RAG or the strongest native external/skill memory where
  feasible, plus an exact/exhaustive ceiling. A stronger explicit-memory arm
  is a valid result. Never starve it by shrinking its legitimate native
  interface to make LOOP win.

The decisive falsifiers are predeclared:

1. `P-LOOP` changes no legal operation distribution at cloned states and no
   later action value on held-out worlds: no learned-operation claim.
2. It changes operations only on source labels or disappears under binding and
   handle renaming: state/content memorization.
3. `P-TEXT` or `P-SKILL` matches it at the same decision and prompt budget:
   prompting/demonstration conditioning explains the effect.
4. `P-TRAJ-SFT` matches it: ordinary trajectory SFT explains the effect.
5. TMEM matches it: the claimed mechanism is occupied fast-weight/direct-write
   adaptation; retain only a measurement or task result.
6. `M-LORA` changes fact recall but not operation transfer, or LOOP helps only
   when facts are already supplied: content and policy effects are separable
   only in the narrow observed sense.
7. Operation shifts occur without action gain, or action gains occur without
   operation shifts: report the total behavioral result and do not infer that
   the recorded operation path caused it.
8. Any answer/proof/future/scorer descendant, target-conditioned trajectory
   selection, rank/adapter/ID/timing channel, or cross-life state survives a
   mutation test: invalidate the affected cell and close the claim.

## Retention, interference, and transfer

“Reusable” requires more than one successful source-to-test run. Measure
operation probes on held-out worlds at frozen LOOP checkpoints during source
training, then test old and new motifs in each untouched evaluation life.
Within a life, interleave unrelated cohorts before revisiting an old goal;
score old-operation choice, old action success, recent success, and
cross-era action success. A fact-memory adapter may show local retention or
interference while the frozen LOOP should preserve a structural operation
prior. Conversely, if growing local memory causes retrieval precision or
search quality to decay, record that as a policy–memory interaction rather
than silently tuning the policy on evaluation outcomes.

The independent unit is the world-life (or world root for Stage-1 probes), not
the many nested target rows. Report root-wise distributions and complete
failure denominators. Use no current PCFL B3 power, plateau, or population
arithmetic for this successor. A future claim proposal must choose its own
finite-sample analysis, untouched-root roster, strict variance/assumption
margin, and end-to-end gate-passage power.

## Why the proposed r8-to-r64 pyramid is premature

The geometric rank pyramid is an interesting timescale hypothesis, not a
minimal experiment. Rank is parameter capacity, not automatically a learning
timescale or a search depth. Doubling rank changes trainable parameters,
optimizer state, update FLOPs, representational rank, and often the amount of
data needed to avoid memorization. If each level also receives more data or a
different promotion schedule, rank, data volume, teacher quality, and clock
are all confounded.

The two proposed propagation mechanisms are distinct experiments. A
data-mediated slow adapter can learn a selected distribution and duplicated
traces; a weight-mediated SVD merge can rotate, attenuate, or destroy fast
directions, is order-dependent, and makes reset/attribution difficult. A
merge-and-reset cycle is not evidence of biological sleep. Keep content and
LOOP adapters separately mountable and do not merge into the base in this
study. The active-stream contract explicitly forbids adding such a rank grid
to B3.

The pyramid should be reconsidered only if a single LOOP adapter first shows
held-out operation transfer, action value, and a nontrivial retention curve.
Then compare a data-mediated `r_fast -> r_slow` cascade against a single
adapter with the same total verified examples, total training FLOPs, and
evaluation budget. Weight-mediated merging deserves its own arm and its own
failure analysis; it should not be smuggled into the primary cascade.

## Cheap, predeclared rank sweep

For the successor pilot, hold base, target modules/layers, tokenizer,
operation grammar, corpus bytes/order, optimizer family, examples, epochs,
and seeds fixed. Sweep `r ∈ {0, 4, 8, 16, 32, 64}` on the Stage-1 operation
assay only, using the four-source/two-DEV/four-test world split. Run one seed
per rank initially; replicate the smallest and best DEV ranks with three seeds
before carrying one rank to Stage 2. Use the same examples and optimization
steps as the primary data-matched view, but publish actual adapter parameters,
training FLOPs, optimizer bytes, inference tokens/latency, and storage. A
small secondary compute-matched check may adjust steps for `r=8,32,64`; its
different exposure must be labeled, not pooled with the data-matched curve.

Select a rank using DEV operation-transfer alignment and a predeclared tie
rule (smallest rank within the registered practical margin); never select on
test action returns, target outcomes, or a later lifetime checkpoint. The
operation pilot is not itself evidence for a population or mechanism claim.

Predeclared predictions and interpretations:

- `r=0` is the frozen-policy floor. `r=4` may underfit; if the low ranks are
  useful, `r=8` or `r=16` should beat the floor on renamed held-out motifs,
  with little additional gain at `r=32`/`r=64`.
- If `r=64` improves source fit but not held-out operation transfer, content
  decodability rises, or old-motif retention falls, interpret it as
  over-capacity/trajectory memorization, not stronger agency.
- If held-out transfer rises monotonically through `r=64`, the “agency is
  low-rank” prediction is falsified; rank is acting as useful capacity and the
  pyramid needs more data/compute before any conclusion about geometric
  promotion.
- If all ranks are flat against null while text examples or ordinary SFT help,
  the operation target, adapter placement, or credit signal is inadequate;
  do not rescue the hypothesis by increasing rank.
- If gains appear only with `M-LORA` and disappear with `M-TEXT`, they are
  likely content/read effects. If `P-LOOP` helps both at the same small memory
  envelope and survives world/binding shuffles, that supports the narrower
  policy-transfer interpretation.
- If a larger rank wins only with extra FLOPs, tokens, or inference work, the
  result is a resource effect until a compute-matched comparison passes.

The next permitted transition after a promising pilot is not automatic
execution. It is a new successor proposal binding these exact trace/visibility
schemas, whole-world/lifetime roster, TMEM source comparison, rank rule,
resource ledger, mutation suite, stop rules, and claim vocabulary, followed by
fresh independent review and explicit human authorization. A negative or
ambiguous pilot should retire the rank-pyramid rationale and narrow the claim,
not expand the current Paper-1 surface.
