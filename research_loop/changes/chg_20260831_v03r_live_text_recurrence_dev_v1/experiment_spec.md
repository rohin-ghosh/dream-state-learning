# v0.3-R live-text recurrence development transition v1

Date: 2026-08-31 PT. Status: **proposal only; unratified**. Change ID:
`chg_20260831_v03r_live_text_recurrence_dev_v1`.

This is the first proposed GPU transition after every named P0/P1 closes. It
instantiates Rung 3 of the ratified interleaved organism. It does not rerun v5,
train a LoRA, inspect heldout lives, repair itself from results, promote a
claim, or authorize a follow-up.

## One claim and one causal arrow

At fixed public lifetime, model, pre-feedback history, and maximum budgets:

> A typed goal-conditioned frontier that carries no evidentiary force can
> select later bounded dreaming so the model independently re-derives missing
> recipient-local causal connections, making those connections more available
> to a fresh goal-conditioned thinker than no feedback or a matched irrelevant
> frontier.

The primary object is the thinker-to-later-dream return edge. Final accuracy
cannot hide a missing connection, and connection formation cannot substitute
for final paired behavior.

## Why this transition is text-only

The live model must first produce a causally useful, non-contaminated semantic
snapshot and a fresh thinker must use it. Prior measurements already establish
formatted transport ceilings: L0/G2f reached 0.949 through weights and Semantic
C2r reached 228/228 recognition reads with D2 0.917--1.0. V5's retained corpus
was 0/12 true and is barred from transport. Adding LoRA here would conflate
dream content, write training, recognition, and composition while the missing
arrow is earlier. A passing text corpus may source a separately ratified Rung-4
fixed-corpus text-versus-LoRA experiment; it never triggers one automatically.

## Frozen public population

- Generator: exact reviewed `CounterfactualConfluenceV03R` bytes.
- Skin: `aligned`.
- Development seeds: 0, 1, and 2; both latent collision twins for each seed.
  This gives three pairs/six lives and covers goal roles 0, 1, and 2.
- Each life supplies its complete `precheckpoint_export`: seeds 0 and 2 have
  46 public events; seed 1 has 49. Rendered public text and its equivalent
  structured `public_record` are retained, together with the public
  intermediate operational probe. No life is truncated or padded.
- The final paired goal question is separately sealed and revealed only after
  MEMORY_1 freezes.
- Expected ratio, latent bit, oracle proof, scorer path, answer valve/operation,
  hidden truth, FactorSolver, and postcommit labels are forbidden from every
  dream, thinker, selector, realization, checkpoint, and provider call.
- The public agenda compiler exposes exactly an own source-to-target causal
  join and a distinct recipient-local same-kind matched distractor. It accepts
  public export bytes, never a world or oracle object.
- Heldout and replication seeds are neither rendered nor included in any
  planner, reviewer-repair, model, or result-driven tuning context.

## Frozen model boundary

- Dreamer and thinker: `Qwen/Qwen2.5-32B-Instruct`.
- Revision: `5ede1c97bbab6ce5cda5812749b4c0bdf79b18dd`.
- Clean bf16 base; no adapter is mounted or trained.
- Every operation is a fresh/stateless provider call. Reset identity and exact
  prompt/config bytes are enforced by the backend, not merely self-reported.
- Dream decoding: temperature 0.2, top-p 0.95, maximum 128 new tokens. The seed
  is a deterministic digest of run, visible life, stage, round, and call index.
- Think decoding: temperature 0, top-p 1, maximum 128 new tokens, strict
  one-operation JSON parser. An invalid operation consumes its call and becomes
  a typed rejection/defer; it is never silently rewritten.
- Exact prompt template/input/prompt/output bytes, token IDs/counts, model and
  revision, decoding values, reset ID, timestamps, parser result, and provider
  receipt are immutable for DREAM and THINK.

## Frozen recurrent schedule

One shared prefix is executed once per life and cloned byte-identically. The
WAKE/reactivation schedule is bound to the world's public `schedule_manifest`
and must be identical across its collision twins and all three arms:

1. Seeds 0 and 2: 46 WAKE dream calls and 22 periodic REACTIVATE calls.
2. Seed 1: 49 WAKE dream calls and 24 periodic REACTIVATE calls.
3. 16 target-blind SLEEP calls.
4. Every dream sees one triggering public event and at most six semantic
   neighbors; the full-memory ceiling is false.
5. One dream call emits at most one `CREATE_CONCEPT`, `CREATE_EDGE`,
   `REINFORCE`, `SUPERSEDE`, or `PASS` with eligible premise handles. Model
   claims enter provisionally. A model output, repeated assertion, or
   same-model self-check can never set `supported`.
6. Apply the proposed answer-blind public-evidence admission rule. It may
   promote only an already-proposed exact typed local join whose cited public
   route/effect records share the declared connector. The rule recomputes the
   endpoints, direction, relation type, and connector from those immutable
   records; all must equal the proposal. It cannot search for a join, invent or
   substitute an endpoint, read the final question/private world/oracle/truth,
   or use a thinker frontier as evidence. Wrong-connector, unrelated,
   incomplete, ambiguous, or nonlocal citations leave the claim provisional.
   The admission record and its exact cited bytes are append-only. Same-model
   self-check remains a separately ratifiable ablation, not part of this arm.
7. Compile canonical deterministic text realizations and freeze MEMORY_0.
8. Run a fresh ThinkerMachine on the public non-answer operational probe for at
   most 12 model operations. Its raw operations are mechanically replayed. A
   system allowlist may project one typed missing/conflict frontier; it cannot
   project an answer, free rationale, scorer fact, or evidentiary premise.

Branch the identical MEMORY_0/THINK_0 snapshot into:

1. `no_feedback`: discard the own frontier; the frozen intrinsic selector
   chooses 16 RETURN_SLEEP views.
2. `agenda_feedback`: the own typed frontier selects 16 bounded RETURN_SLEEP
   views; the frontier is never a premise.
3. `matched_distractor`: the distinct recipient-local same-kind causal join
   selects 16 bounded RETURN_SLEEP views.

For every arm, compile/freeze canonical MEMORY_1, reveal only the public final
question, and run a fresh exact-final-goal ThinkerMachine for at most 12 model
operations. RELEASE requires a replayed cited support path and a schema-valid
public answer; only edges admitted as `supported` by the answer-blind rule may
license RELEASE. Provisional edges may guide retrieval or hypothesis scratch,
but cannot license an answer. Otherwise the machine DEFERs.

Prefix sharing yields 132 dream calls for each seed-0/2 life
(`46 + 22 + 16 + 16 x 3`) and 137 for each seed-1 life
(`49 + 24 + 16 + 16 x 3`): exactly 802 dream calls over six lives. Thinker
work is at most 48 operations per life (`12 + 12 x 3`), or 288 total. The
runner must assert actual manifest-bound counts and within-life/arm equality.
Actual calls/tokens are reported. Early release is not padded.

## Baselines and ceilings

The primary matched comparisons are agenda feedback against both no feedback
and the matched distractor. The same frozen job also evaluates:

- each life’s complete 46- or 49-event public transcript with the same final
  ThinkerMachine operation budget;
- iterative episodic RAG over that complete lifetime with explicit top-k, read-call,
  token, and total-compute accounting capped to the organism final-thinker
  retrieval budget;
- wake-only canonical episodic text memory with the same final thinker;
- the CPU scripted recurrence and public-edge oracle, labeled ceilings.

No oracle agenda, perfect in-loop gate, batch parent search, final-answer
memory, hidden verifier, raw/QA/connected LoRA, or post-result prompt repair is
part of this transition.

## Measurements

Primary:

- exact own-frontier closure from eligible recipient-local premises;
- agenda-minus-no-feedback and agenda-minus-distractor closure;
- paired-both-correct final result, individual answer accuracy, and defer rate;
- fresh thinker RELEASE with mechanically valid cited support.

Secondary attribution:

- postcommit-only memory precision/recall and provisional/supported/
  contradicted counts;
- public-evidence admission attempts, exact reason codes, accepted/rejected
  connectors and citations, plus the delta between provisional availability
  and supported RELEASE paths;
- task dependency path coverage, derivation and supported depth, semantic
  hops, independent support, and thinker compositional depth;
- agenda consumption, selection overlap, local edge formation, conflict/
  revision events, false/circular memories, parser rejection, atomic reads;
- calls, exact prompt/output tokens, wall time, truncation, and per-arm compute.

## Validity, go, stop, and pivot gates

Invalidate and stop on any answer/private sentinel in model-visible bytes;
snapshot/lock/review drift; cross-life model/cache/index state; non-replayable
thinker result or projection; call-ledger mismatch; out-of-view premise;
postcommit truth reaching cognition; direct model-controlled support; an
admission that changes proposal endpoints or accepts a wrong/unrelated
connector; missing artifact; or prompt truncation.
Poor scientific performance does not early-stop an otherwise valid run.

The only permitted GO recommendation is a later, separately ratified
fixed-corpus transport transition, and only if all hold:

1. agenda feedback closes the exact own frontier in at least 4/6 lives;
2. it exceeds each control by at least 2/6 closures;
3. at least 2/3 collision pairs have both answers correct in the agenda arm
   with valid cited releases;
4. no hidden/circular channel or open P0/P1 reviewer blocker exists;
5. the frozen agenda corpus is nonempty and postcommit precision is reported.

These are development transition gates, not significance claims. If closure is
absent, stop before LoRA. If closure succeeds but thinking fails, freeze the
corpus and isolate the thinker under a new intake. If context/RAG matches or
wins, preserve that result and make no memory-advantage claim. Leakage
invalidates the run. False memories remain in the measured blast radius and
cannot be truth-filtered post hoc into a transport corpus.

## Mandatory immutable artifacts

- exact intake/ratification, workflow/spec, full runtime-closure lock, and
  binding Fable/Sol review receipts;
- environment/hardware/model/decoding manifests and started/progress/done/
  failed markers;
- public precheckpoint inputs and separately sealed final questions per life;
- every DREAM/THINK call material, provider receipt, reset, token and parser
  record;
- concepts, edges, derivations, status events, bounded views, realizations,
  phase barriers, semantic/text checkpoints, and hashes;
- initial/final machine operations, replay, agenda, queries, reads, workspace,
  terminal, answer, and cited support;
- all baseline prompts/retrieval traces and compute;
- isolated postcommit scorer inputs/outputs, paired metrics, and shortcut audit;
- per-arm/life summaries, failure taxonomy, complete SHA-256 manifest;
- sanitized future LOOP-training trajectories with private/scorer fields
  excluded.

## P0/P1 and review boundary

Before launch, scheduler validation must independently rebuild the checkpoint
and goal and exactly reconstruct result/agenda projections; the provider must
receive the exact ledgered prompt/config/reset; resets must be real/stateless;
DREAM must have equivalent raw-call provenance; and experiment-level matched
accounting must reconcile every call. Rendered-text/order shortcuts and the
public final-goal paired thinker must pass. The public-evidence admission rule
must reject wrong-connector/unrelated citations, ignore model support flags,
recompute rather than accept endpoints, and remain byte-invariant under every
private/final-truth mutation. The 1000-pair v0.3-R population and shortcut audit
must pass on the exact bytes.

This support transition is an explicit unresolved reviewer concern until the
two independent interpretations and cross-critique disposition agree on the
exact public entailment grammar and Rohin ratifies those bytes. Without that
disposition, live dream claims remain provisional, final RELEASE has no legal
supported path, and the workflow must stop before any provider or GPU call.

All runtime imports are frozen from a quiescent/read-only snapshot. Fresh Fable
and fresh Sol reviewers independently approve the exact workflow, prompts,
model, files, budgets, and evidence; hashes match at review start and end. An
author advocate cannot override rejection. A new intake must reach
`human_required`, and Rohin must ratify its exact consensus and GPU scope
before the workflow can initialize.

## Resources and forbidden conclusions

Use one already-authorized H100 80GB or GH200 96GB and one 32B bf16 vLLM
server. Independent lives/calls at the same causal phase may batch; no
per-life causal ordering may be crossed. Expected wall time is 6--10 hours;
hard timeout is 12 hours. This proposal does not authorize a new lease, spend,
second GPU, or credential change.

This run cannot support claims about LoRA, parametric transport or necessity,
beyond-context advantage, learned controllers, heldout/skin robustness,
statistical reliability, action improvement, online self-improvement,
lifetime scaling, baseline saturation, or a paper headline. It is one aligned
development causal-interface experiment on a roughly 1.1k-token calibration
world.
