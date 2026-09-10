# Prior-art and adversarial-baseline audit: constructive parametric memory in action agents

**Date:** 2026-09-03  
**Status:** read-only research advisory. It authorizes neither code changes nor GPU runs.

## Bottom line

There is no credible novelty in the broad statement that an agent can reflect on
experience, keep linked memories, consolidate during idle time, learn from
action outcomes, or place a fast/LoRA memory in parameters. All of those are
already occupied. The closest *single* parametric-memory prior is **TMEM**;
the closest cross-session, outcome-trained consolidation prior is
**Auto-Dreamer**; the closest embodied parametric-skill prior is **PEAM**; and
the closest dream/wake world-model and explicit-graph ancestors are **DECKARD**
and **DreamerV3**, respectively.

The defensible remaining contribution is consequently narrow and empirical:

> On a prospectively sealed action world, can a frozen language agent turn its
> own action--outcome history into *connected, provenance-bearing, selectively
> consolidated parametric world knowledge* that improves held-out, irreversible
> multi-step action after history has exceeded context, beyond comparably
> budgeted raw history, retrieval, linked/graph memory, reflected text memory,
> and raw/QA LoRA?

This must be presented as a conditional result about the tested world and
memory budget, not as a first demonstration of lifelong learning, dreaming,
parametric memory, or outcome-grounded memory writing. The critical empirical
signature is a lifetime/depth curve plus causal memory interventions, not a
single end-point score.

The current `v03r` canary cannot support that claim. Its own benchmark
interpretation labels it a single, game-ontology- and proof-scaffolded
engineering fixture with no fair baselines, replication, held-out LoRA test,
or population estimand. Treat it strictly as an integration gate; do not put it
in a paper result table except as an engineering appendix.

## Closest work and what each removes from the novelty claim

| Family / closest work | What is already established | Why it is not the target claim | Required response |
|---|---|---|---|
| **TMEM** (2606.04536) | The agent emits self-generated QA supervision, writes it into online LoRA fast weights, and its extraction policy is RL-shaped by task outcome. It compares with summaries and retrieval. | Updates are within a rollout and reset across episodes; it is QA/search-oriented rather than a prospective lifelong action-world test. It does not establish connected, cross-episode world-schema consolidation. | Cite as the closest parametric baseline. Include a TMEM-style online-QA-LoRA arm or explicitly state why only a bounded functional reimplementation is feasible. Never claim first reward-shaped LoRA writing. |
| **PEAM** (2605.27762) | Minecraft experience is internalized into category-isolated MoE-LoRAs; failures/corrections train procedural skills; a worthiness score and consolidation trigger select writes. | It targets reflexive skills, not a connected, inspectable world approximation or prospective unseen factor/action composition. Its selector is not the paper's recurrent dream/think graph. | Cite as the closest embodied parametric-learning work. Include its decisive functional ingredients as a failure--correction procedural-LoRA control if exact replication is infeasible. |
| **Auto-Dreamer** (2605.20616) | Offline, cross-session consolidation is outcome-trained with GRPO and evaluated on ScienceWorld, ALFWorld, and WebArena. | Its consolidated state is an external text memory bank, not parametric memory; its evaluation does not establish the proposed factor-law/action intervention package. | This is the strongest systems-level baseline-to-beat. A frozen offline-reflect-and-rewrite text-bank arm is mandatory; an exact GRPO reproduction is not required for the first GPU paper if it is clearly separated as a literature comparator. |
| **A-MEM, Mem0, HippoRAG, MemoRAG, Memory-R1/AgeMem/MemRL** | Dynamic linked notes, graph/index maintenance, multi-hop retrieval, memory evolution, and learned/value-aware external-memory operations already exist. | They remain explicit/retrievable stores. They do not show that a LoRA carries a connected model once source history is out of context. | The paper needs a strong linked/graph-text arm, not only cosine RAG. A-MEM is the cheapest direct implementation; a DECKARD-style typed graph is the more adversarial structure control. |
| **Generative Agents, Reflexion, ExpeL, Voyager** | Reflection over episodic histories, extracting reusable lessons, self-verification from environment feedback, and lifelong skill libraries are established. Voyager is particularly close in Minecraft action learning. | Their persistent state is text/code/library, not parametric consolidation. Their headline evaluations do not isolate a context-cleared parametric world model against equivalent text/graph stores. | Do not call recurrent reflection, lessons, or a growing skill library new. Include a reflected-text/lesson arm and a procedural skill-library arm when the world admits reusable action macros. |
| **DECKARD, DreamerV3** | DECKARD dreams a language-guided abstract world model, verifies/corrects it through interaction, and plans with an explicit subgoal DAG. DreamerV3 learns latent dynamics and improves behavior through imagined rollouts. | DECKARD's store is an explicit graph plus subgoal policies and substantially leverages pretrained Minecraft knowledge; DreamerV3 is end-to-end latent RL, not frozen-LLM experiential consolidation. | The explicit graph/program planner is mandatory as the strongest nonparametric structural baseline. DreamerV3 is lineage/context, not a fair small-GPU baseline for a language action world. |
| **Titans, ATLAS, MIRAS, Nested Learning/HOPE** | Memory-as-weights, surprise/retention-gated test-time updates, windowed fast-weight optimization, and multi-timescale memory are established. | Published evaluations are principally single-sequence long-context/LM tests. Surprise/self-supervised reconstruction is not the same as lifetime action-outcome consolidation, but the substrate claim is not new. | State the difference as evaluation regime and explicit connected/action construct, never as inventing parametric memory or forgetting gates. A surprise-gated fast-weight ablation is useful only if the proposed substrate is in this family. |
| **Continual-LoRA and replay** | LoRA knowledge memory, continual adaptation, replay, EWC/A-GEM, and procedural memory are mature. | They do not by themselves induce or test a prospectively committed world schema from own action outcomes. | Raw-LoRA and one stability-preserving continual-learning control are needed if asserting that dreaming, rather than mere training recipe, causes the gain. |

### Specific collision rulings

1. **TMEM is not a side citation.** It is the first baseline a reviewer will
   name because it combines an agent, LoRA, self-generated training examples,
   and task-outcome-trained extraction. The valid distinction is offline and
   cross-episode connected consolidation, not that the writer learns from
   reward.
2. **A-MEM and Generative Agents prevent a claim of first connected memory.**
   Their links/reflections are external text; the differentiator must be the
   parametric transport and action consequence under a matched external-memory
   alternative.
3. **Voyager and PEAM prevent a claim of first lifelong embodied learning or
   first Minecraft-like parametric memory.** The evidence must instead show a
   more demanding prospective structural-action test and expose its tradeoff
   against procedural code/skill reuse.
4. **DECKARD prevents a claim of first dream/wake action-world model.** The
   proposed version must win or lose fairly against an explicit factor graph
   built from exactly the public experiences. A graph baseline that is denied
   the same observations is not informative.
5. **Titans/MIRAS/Nested Learning prevent a claim of first multi-timescale or
   test-time parametric memory.** The valid claim is not architectural
   novelty; it is a different action-evaluation protocol and, if demonstrated,
   a connected-world-memory behavior.
6. **HippoRAG/MemoRAG prevent treating RAG as only top-k raw lines.** At least
   one retrieval baseline must have learned/query-conditioned structure, graph
   traversal, or memory-guided retrieval. Otherwise a reviewer can attribute a
   result to a deliberately weak RAG baseline.

## What would be rejected as rediscovery

The following headline claims are unsafe even if the proposed method wins its
own benchmark:

- "Agents learn from their own experience through reflection/dreaming."
- "A sleep-like/offline consolidation phase improves agents."
- "LoRA is a long-term/parametric memory for an agent."
- "A learned or outcome-grounded policy decides what to write to memory."
- "Linked memories, graph memory, multi-hop recall, or external memory
  evolution enable better reasoning."
- "A lifelong Minecraft/action agent can collect skills and reuse them."
- "Fast weights, surprise gates, retention gates, or nested time-scales are a
  new memory architecture."
- "A custom environment with latent laws and action feedback proves general
  continual intelligence." It proves only the specified construct, and only
  if target blindness, twin action redirection, and the negative-law control
  all pass.

The currently proposed PCFL-Compose world can support a sharper claim than
prior semantic/QA worlds: every decisive tool is never executed in the source
life, target bytes are matched across twins whose correct actions differ, and
credit requires the realized trajectory. This is useful, but only when every
memory family sees the same frozen public chronology and receives the same
read/write/action budget.

## Minimal fair baseline suite for the present hardware and world

The current measured stack supports Qwen2.5-7B bf16 LoRA reads/writes, with
rank 64, approximately 200 touches per atomic fact, and a clean-base
composition protocol. That makes a seven-arm, three-seed suite plausible on a
single 80-GB-class GPU if the expensive writer calls are cached once per
life/condition and all text methods share the same frozen base. It is not
plausible to reproduce full TMEM GRPO, PEAM's multimodal Minecraft pipeline,
and DreamerV3 training as additional paper arms.

### Publishable minimum (seven arms including proposed)

| ID | Arm | Persistent state / write rule | What it tests |
|---|---|---|---|
| B0 | **No memory / native window** | No cross-episode state; fixed recent context only. | Floor and action prior. |
| B1 | **Long context** | Chronological raw public history truncated only at the model's real window. | Best direct history use before overflow. Report exact visible tokens. |
| B2 | **Raw RAG** | Embed/retrieve raw action--outcome episodes; fixed top-k and matched read tokens. | Episodic retrieval without abstraction. |
| B3 | **Linked/graph retrieval** | A-MEM-style linked notes *or* a DECKARD-style public factor/transition graph built only from source events; graph traversal/read budget matches the proposed reader. | Strong explicit structure and multi-hop retrieval. This is the adversarial nonparametric baseline. |
| B4 | **Offline reflected text bank** | Same chunking, same frozen writer model, same write-call budget as the proposal; it can summarize, make lessons, and link entries, but receives no LoRA. | Generative Agents/ExpeL/Auto-Dreamer family: whether explicit consolidation is enough. |
| B5 | **Raw/QA LoRA** | Train the same adapter budget on raw events plus mechanically rendered atomic QA/trajectory pairs. No dream-derived connections. | Parametric memory without constructive consolidation; approximate TMEM's supervision substrate, but offline/cross-episode. |
| B6 | **Proposed Dream--LoRA--Think** | Provenance-bearing, self-checked connected memories; LoRA realization; recursive/goal-conditioned reader. | Incremental value of connected abstraction plus parametric transport. |

This is the minimum credible table. A LoRA result that beats only B0--B2
would remain vulnerable to A-MEM/DECKARD/Auto-Dreamer/Voyager objections. A
text result that beats only B5--B6 would not establish the parametric-memory
claim.

### Add only after the seven-arm result is real

- **B7, online TMEM-style LoRA:** clear context and write self-generated QA
  pairs during the acting rollout; reset only where TMEM resets. This isolates
  online compression from offline cross-episode consolidation. It is the best
  additional arm, but it requires a separately sealed write schedule and
  cannot be passed off as an exact TMEM reproduction.
- **B8, PEAM/Voyager procedural control:** consolidate success/failure-
  correction action traces to a skill/macro library or procedural adapter,
  without a factor schema. Add if the workshop admits reusable macros; omit
  rather than invent meaningless skills in a permutation world.
- **B9, continual-LoRA protection:** B5 plus replay, A-GEM, or EWC under the
  same adapter parameter/update budget. It separates relational abstraction
  from ordinary anti-forgetting.
- **Oracle ceiling:** exact public program/factor solver. It is a construct
  certificate and information ceiling, never a competitor the learned method
  is expected to beat.

### Do not use as a paper baseline

- **DreamerV3:** a different end-to-end RL training regime and compute scale;
  cite it for lineage, do not make a weak reimplementation the strawman.
- **Exact TMEM/Auto-Dreamer/PEAM reproduction on the first GPU pass:** each
  entails a materially different learned policy or environment. A declared
  functional ablation is useful; a claim of reproducing the paper is not.
- **Only raw RAG:** insufficient because HippoRAG, A-MEM, MemoRAG, and
  DECKARD directly answer the objection that retrieval can be structured.

## Fairness contract for every arm

The benchmark already contains many of the right controls. They must be made
baseline-generic rather than special to B6.

1. **Identical evidence:** each arm sees precisely the same frozen public
   action--outcome prefix. No arm sees latent permutations, target identities,
   solver output, future chord outcomes, target allocation, or answer-bearing
   corpus cells.
2. **Prospective freeze:** build/freeze every text graph, index, adapter,
   cache, and schedule before any target is rendered. No intervention or
   target outcome can trigger an arm-specific repair.
3. **Budget match three currencies:** (a) writer/dream/reflection calls and
   generated tokens, (b) persistent capacity: text tokens, graph nodes/edges,
   retrieval index bytes, and LoRA parameters separately, and (c) reader calls
   and read tokens per decision. Equal parameter count is not an equal RAG
   budget, so report both rather than claim perfect equivalence.
4. **Same agent and action cap:** one frozen actor/planner, identical model,
   prompt structure, menus, action cap, context cap, temperatures/seeds where
   applicable, and public trajectory-only scoring. A text baseline must be
   allowed to plan, not reduced to a final-answer QA probe.
5. **Substrate interventions:** apply authentic/twin whole-life swaps to every
   memory type. For text/graph, remove or swap all equivalent records and
   derived indexes. For LoRA, use authentic/twin whole-adapter swaps; deleting
   a citation is not a parametric ablation.
6. **Required outcomes:** report D1 and D4 action success, new acquisition,
   old retention, cross-era composition, paired goal-twin redirection,
   negative-law abstention/chance behavior, and cost. Report action success
   conditionally and unconditionally on successful compilation/recognition;
   dropped/failed writers remain in the denominator.
7. **Counteract writer advantage:** B4 and B6 share the same LLM writer,
   chunking windows, call count, and source prefix. B5 and B6 share adapter
   rank, target modules, training examples/touches, optimizer, instruction
   preservation mix, and reader protocol. Otherwise the paper measures
   compute/corpus formatting rather than connected memory.

## Benchmark and gym positioning

Existing memory benchmarks are important validation suites, but none is a
substitute for the proposed action construct:

- **ALFWorld/ScienceWorld:** useful secondary action-outcome validation and
  direct comparability with Auto-Dreamer, CLIN, ExpeL, and some memory-agent
  work. They do not themselves seal a long per-life hidden factor law or
  provide exact twin action interventions.
- **EvoMemBench/LifelongAgentBench:** establish cross-episode execution as an
  evaluation axis, but do not provide a single, prospectively controlled
  parametric-versus-external-memory test.
- **WorldMemArena/WorldLines:** show lifecycle/stale-state failures in
  multi-session agents; use their failure taxonomy, not their task score, as
  the closest diagnosis precedent.
- **MemTrace, RECON, ForgetBench, Ground Truth First:** sharply weaken any
  claim of first age curves, provenance graphs, relational memory, or
  structural-vs-detail scoring. The defensible benchmark wedge is one common
  probe/action interface across parametric and nonparametric memories at an
  enforced budget, with importance/structure/detail splits and prospective
  action twins.

Recommendation: make PCFL-Compose (after a separately ratified full protocol)
the primary causal benchmark. Add one small external ALFWorld or ScienceWorld
continual slice only after the primary seven-arm result is stable; it is
generalization evidence, not a replacement for the controlled test. Do not
let a familiar gym erase the only causal advantage of the bespoke world.

## Minimal experimental sequence

1. **CPU certificate:** exact public-program ceiling, target blindness,
   negative-law sentinel, twin-byte identity/opposite-action certificate,
   fixed source schedule, and target uniqueness all pass before model calls.
2. **One-life development:** B0--B6 on a small sealed development panel;
   measure compiler coverage, text read fidelity, LoRA read fidelity, and
   action success separately. The existing v03r canary may help here, but is
   not evidence for the final estimand.
3. **Three seeded worlds x three skins:** run the frozen B0--B6 protocol to
   context overflow and at least two post-overflow lifetime checkpoints. Plot
   acquisition, retention, and cross-era D4 separately; a final average can
   hide forgetting.
4. **Causal panel:** authentic/twin memory factorial, decisive-factor swap,
   composition-order cut, matched sham cut, and goal twin. A high score without
   redirected behavior should be treated as a shortcut, not a successful world
   model.
5. **Only then add B7/B8/B9 or an external gym.** A full learned TMEM or
   Auto-Dreamer reproduction belongs to a follow-up compute budget, not to a
   first credible result.

## Source record (local source notes/deep reads; no new web search used)

The audit used the repository's locally retained abstracts/deep reads and the
current world/governance specifications. Paths below are exact local sources;
their embedded arXiv identifiers and URLs should be re-verified immediately
before submission because this literature moves rapidly.

- `/Users/rohing/dream-state/research_notes/35_goalposts_paper1.md`
- `/Users/rohing/dream-state/REVIEW_PACK.md`
- `/Users/rohing/dream-state/research_loop/advisory/20260902_pcfl_compose_paper_world.md`
- `/Users/rohing/dream-state/research_loop/changes/chg_20260903_paper1_v03r_end_to_end_canary_v1f/interpretation.benchmark.json`
- `/Users/rohing/dream-state/research_notes/03_agent_memory_benchmarks.md`
- `/Users/rohing/dream-state/research_notes/05_learned_retrieval_prior_art.md`
- `/Users/rohing/dream-state/research_notes/11_baselines_benchmarks.md`
- `/Users/rohing/dream-state/research_notes/12_atlas_baselines_learned_write.md`
- `/Users/rohing/dream-state/research_notes/13_atlas_disambiguation.md`
- `/Users/rohing/dream-state/research_notes/16_tmem_deepread.md`
- `/Users/rohing/dream-state/research_notes/18_competitive_verdict.md`
- `/Users/rohing/dream-state/research_notes/19_benchmark_prior_art_recheck.md`
- `/Users/rohing/dream-state/research_notes/21_compute_precedents.md`
- `/Users/rohing/dream-state/research_notes/33_semantic_world_gpu_constraints.md`
- `/Users/rohing/dream-state/research_notes/related_work/2301.12050_deckard-dream-wake-minecraft.md`
- `/Users/rohing/dream-state/research_notes/related_work/2301.04104_dreamerv3-world-model.md`
- `/Users/rohing/dream-state/research_notes/related_work/2304.03442_generative-agents-reflection.md`
- `/Users/rohing/dream-state/research_notes/related_work/2305.16291_voyager-skill-library.md`
- `/Users/rohing/dream-state/research_notes/related_work/2502.12110_a-mem-agentic-memory.md`
- `/Users/rohing/dream-state/research_notes/related_work/2605.27762_peam-slow-fast-minecraft.md`
- `/Users/rohing/dream-state/research_notes/related_work/2606.04536_tmem-agent-qa-lora.md`
- `/Users/rohing/dream-state/research_notes/related_work/2605.26099_offline-recurrence-sleep.md`
- `/Users/rohing/dream-state/research_notes/related_work/2606.03979_language-models-need-sleep.md`
- `/Users/rohing/dream-state/research_notes/08_memory_substrates.md`
