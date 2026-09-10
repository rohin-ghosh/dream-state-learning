# PCFL-Active-Stream novelty and accept-path decision memo

**Date:** 2026-09-02  
**Status:** advisory only; read-only positioning audit. This memo grants no
implementation, deliberation, ratification, model/provider/network, CPU/GPU,
training, LoRA, confirmation, publication, claim-release, or successor
authority. It does not modify, approve, or authorize the proposal or workflow.

## Decision

**REWORK, while retaining a text-first ICLR path.** If Active-Stream works, its
credible contribution is a controlled causal-memory benchmark plus reference
system, not a new-LoRA method or generic self-learning-agent paper.

## Narrowest credible novelty

The narrowest credible claim is a target-blind, controlled evaluation of
compiled per-life action memory after context overflow: independently growing
hidden action bindings; bounded typed resolution; separate acquisition,
retention, and cross-era action scores; and twin/binding interventions. The
conjunction, rather than any individual component, is the novelty. The prior
novelty audit specifies this conjunction and its intended contribution
(`research_loop/advisory/20260902_pcfl_compose_novelty_audit.md:11-36`), while
the Stream design defines independent causal cohorts
(`research_notes/48_pcfl_stream_and_schema_design_v0.md:28-51`), target cohorts
and causal memory cuts (`research_notes/48_pcfl_stream_and_schema_design_v0.md:53-72`),
and the post-native evaluation axis (`research_notes/48_pcfl_stream_and_schema_design_v0.md:97-119`).

Use the paper position: **“controlled causal evaluation of compiled per-life
memory beyond the context window.”** Do not describe it as a first-LoRA,
first-parametric-memory, generic self-learning-agent, or generic SOTA result.

## Territory already owned

- TMEM already studies outcome-shaped, online LoRA updates within a single
  episode (`research_notes/16_tmem_deepread.md:7-43`).
- PEAM already combines embodied parameter-resident memory, consolidation
  governance, and forgetting tests (`research_notes/09_sleep_consolidation_deep.md:12-17`,
  `research_notes/09_sleep_consolidation_deep.md:35-40`).
- A-MEM establishes agentically organized, evolving linked external notes
  (`research_notes/related_work/2502.12110_a-mem-agentic-memory.md:5-6`).
- Generative Agents establishes a text-memory architecture with reflection,
  retrieval, and planning (`research_notes/related_work/2304.03442_generative-agents-reflection.md:5-6`).
- Voyager establishes open-ended lifelong exploration with an executable skill
  library (`research_notes/related_work/2305.16291_voyager-skill-library.md:5-6`),
  while DECKARD establishes LLM dream/wake planning with environment
  verification (`research_notes/related_work/2301.12050_deckard-dream-wake-minecraft.md:5-6`).
- Titans, ATLAS, and Nested Learning/HOPE occupy test-time parametric,
  multi-timescale memory for single-sequence long-context settings, not this
  agentic cross-episode evaluation (`research_notes/13_atlas_disambiguation.md:74-102`).
- HippoRAG is locally catalogued but lacks a substantive local deep-read; no
  finer comparative claim should be made from the current repository evidence
  alone (`research_notes/related_work/papers.txt:24-32`).

The project’s own experiment-to-claim map reaches the same boundary: broad
dreaming, continual-agent, connected-memory, and parametric-memory territory is
already occupied; it rejects the listed “first” claims and confines Paper 1 to
a controlled systems/measurement claim (`research_notes/42_system_thesis_and_experiment_map.md:128-137`).

## Is text-first evidence enough without a new LoRA result?

**Yes, conditionally.** It is sufficient for a text-memory benchmark/reference
system paper, not for any parametric-memory claim. The Active-Stream proposal
properly makes LoRA a later non-claim sentinel
(`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/experiment_contract.md:174-202`).
The prior execution bundle states the corresponding failure interpretation:
text success with failed LoRA transport is an explicit-memory/compiler paper,
and a linked-memory win removes a LoRA moat
(`research_notes/47_pcfl_execution_bundle_v1.md:631-638`).

Accordingly, absent a separately powered LoRA confirmation, remove all claims
of parametric transport, LoRA efficiency, or LoRA superiority. A text-first
paper remains ICLR-plausible only if the benchmark’s causal identification and
the reference system’s action effect are strong.

## Minimum ablation that makes this a systems paper

At one registered post-native D4 checkpoint, run a matched mediation ablation
that holds the world root, action opportunities, reader budget, witness atoms,
and target process fixed, comparing:

1. raw action--outcome / witness-only mechanical memory;
2. `AS-MECH`;
3. `AS-SELF-TEXT`;
4. `AS-SELF-TEXT` with model-authored semantic records cut; and
5. outcome/twin swaps with probe identity fixed.

Require an incremental, directionally correct later-action effect from the
model-authored delta after assigned fork memory is removed. `AS-SELF-TEXT`
versus `AS-MECH` alone does not identify model-owned reconsolidation because
SELF includes deterministic witness atoms and the reader resolves local
mappings. The existing fresh audit identifies this exact confound and proposes
the required raw-event, action-only, witness-only, semantic-cut, and
outcome-swap controls
(`research_loop/advisory/20260902_pcfl_active_stream_fresh_area_chair_audit.md:31-61`).

If this ablation fails, the result is a benchmark or controlled
external-memory result, not evidence that model-owned Dream/Sleep
reconsolidation is the operative system component.

## Strongest rejection story

> This is a finite mapping-cache benchmark, not reconsolidation: deterministic
> witnessed atoms plus a keyed reader can explain the primary result, so the
> model-authored dream has no identified contribution. The design therefore
> cannot support a general self-improvement claim.

This criticism is concrete. The world is constructed from independent
label-to-transform/predicate/precondition mappings
(`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/experiment_contract.md:28-44`),
and the previous audit finds the proposed causal route confounded by
witness/KV-like replay (`research_loop/advisory/20260902_pcfl_active_stream_fresh_area_chair_audit.md:31-47`).
There is also a literal contract error: `OLD_D4` cannot be more than
`L_native` old at the `0.75 L_native` checkpoint
(`research_loop/advisory/20260902_pcfl_active_stream_fresh_area_chair_audit.md:19-29`).

## Strongest accept story

> A reproducible, target-blind causal benchmark separates continuing
> acquisition, long-delay retention, and cross-era action under context overflow
> without crediting an endpoint score to RAG, a graph, or weights alone.

That story becomes credible if every post-native checkpoint shows all three of
continued new-cohort acquisition, preserved old-cohort value, and above-baseline
cross-era composition (`research_notes/48_pcfl_stream_and_schema_design_v0.md:143-152`),
under the declared resource and baseline surface
(`research_notes/48_pcfl_stream_and_schema_design_v0.md:121-141`). The
benchmark contribution should be primary; causal-mechanism attribution is
secondary; any systems/LoRA contribution is conditional. This is also the
accept-path recommendation of the prior novelty audit
(`research_loop/advisory/20260902_pcfl_compose_novelty_audit.md:171-194`).

## Claim boundary

Even a complete text pass does not establish generic SOTA superiority,
naturalistic external validity, semantic compression, autonomous discovery, a
learned compiler/controller, or universal self-improvement. The proposal itself
limits the result in these terms
(`research_loop/changes/chg_20260902_pcfl_active_stream_paper_target_v1/experiment_contract.md:204-228`),
and the Stream interpretation ladder distinguishes text/LoRA transport from the
later on-policy flywheel (`research_notes/48_pcfl_stream_and_schema_design_v0.md:182-197`).
