# v6 — the flywheel organism (Fable's lane)

Status: DESIGN DRAFT for Rohin's edits (2026-09-04). Protocol needs his
sign-off before first run; infra scaffolding proceeds in parallel.
Namespace: `organism_v6/` only — no changes to Codex's research_loop/microdream
contracts. Gym: compiler optimization (CompilerGym or raw-LLVM fallback,
feasibility scout running). Model: Qwen2.5-7B scout tier on the A40 node.

## 1. Context window = conscious space with explicit STATE

The context is rebuilt from scratch every tick (v6 simplification — no KV
cleverness). It renders from three stores: a STATE json, the LEDGER, and a
TAIL buffer. Layout:

```
[HEAD — persistent state block]  (the "top of consciousness")
  BOOTSTRAP  birth prompt: investigate, act, inspect outcomes, question
             beliefs, judge yourself, mind the clock. The only hand-written
             artifact. Identical for both arms.
  GOAL       objective + the metric ("reduce IR instruction count on the
             current program; your score is % reduction")
  CLOCK      wall time, tick #, budget remaining, time since last progress
  MODE       CONSCIOUS | SUBCONSCIOUS        (see §2)
  FOCUS      current sub-goal / hypothesis being pursued (set by the model)
  STATE      best score so far, current candidate, last outcome, open
             surprises (unresolved expectation violations)

[MIDDLE — recalled experience]
  top-k ledger entries + compiled abstractions relevant to FOCUS,
  verbatim, provenance-tagged (entity/key-matched retrieval, our proven rule)

[TAIL — working thoughts]
  rolling window of recent thought/action/outcome steps, then the prompt
  for the next operation
```

State lives OUTSIDE the model between ticks (state.json) — "context is
storing state" made literal: the harness is nearly stateless; each tick =
render(state, ledger, tail) → one model call → parse → update state/ledger.

## 2. One loop, free-flowing (REVISED per Rohin 2026-09-04)

Rohin's ruling: no rigid conscious/subconscious alternation, no "lame ass
chatbot output space." Thinking-about-what-to-think and thinking BLEND in
one free-flowing stream — planned thinking should be an EMERGENT pattern,
not a harness-imposed grammar. What matters is MAINTENANCE OF STATE in the
context window.

v6 mechanics: the model generates freely in chunks. The harness imposes no
turn structure; it only scans the stream for a minimal set of markers the
model may emit when IT decides to:

  PREDICT: <expected score>        (required before ACT — surprise ledger)
  ACT: <pass sequence>             (submit to gym; outcome injected back)
  NOTE: <text>                     (persist into the state block HEAD —
                                    model-owned state: focus, hypotheses,
                                    self-reminders survive context rebuilds)
  RECALL: <query>                  (harness retrieves from ledger into MIDDLE)

State maintenance is split: MECHANICAL fields (clock, tick, best score, last
outcome, open surprises) are harness-updated every chunk; NARRATIVE state
(focus, working theory, self-instructions) is model-owned via NOTE and
persists at the head across context rebuilds. The bootstrap explains the
markers once; everything else about how the model plans its own thinking is
left to emerge.

## 2b. The context economy (consensus proposal, 2026-09-04)

Rohin's tension: state must change ephemerally; don't clutter the window;
don't lose anything; compaction isn't quite the right tool. Resolution —
three tiers with different lifetimes, and the model curates its own head:

  HEAD   pinned state. Mechanical fields (clock, scores, surprises) are
         harness-maintained; NARRATIVE state is model-owned via NOTE:
         (capped ~10, FIFO — the model overwrites its own theory by writing
         new notes; this IS the ephemeral change of state).
  TAIL   rolling window of the last ~14 thought chunks. Purely ephemeral —
         old thoughts fall off. This is the "building new context windows"
         option, made continuous.
  LEDGER unbounded substrate. EVERY chunk is recorded (thoughts, acts,
         outcomes, notes), so dropping something from the window never
         destroys it — RECALL: pulls it back on demand.

So "meta-thinking that grabs from its own context and thereby clears the
rest" = NOTE (grab-to-keep) + the rolling tail (automatic clearing) + RECALL
(nothing was ever lost). No compaction pass needed in v6: the window stays
small by construction; curation is the model's job and its skill at it is
part of what sleep should eventually improve.

## 3. Ledger (append-only experience record)

One json line per tick: {tick, mode, focus, thought_or_action, prediction,
outcome, surprise (|pred-actual| + sign), time_cost, episode_id}. Written by
the harness, never edited. This is the raw material for both retrieval
(middle of context) and sleep.

## 4. Sleep compile (v6 minimal — the experience compiler)

Trigger: after every N episodes (v6: N=8) or on budget. Mechanical steps,
with THINK used only for restatement (no learned sleeper):

1. SELECT (support-gated — v5's law: nothing unverified enters training):
   - verified improvements (action sequences that raised measured score)
   - failure→feedback→recovery pairs
   - top-k by surprise (prioritized replay)
   - slow-correct vs fast-correct contrast pairs (time-awareness)
2. TRANSFORM (temporary THINK calls): each selected item restated as
   (a) state→action exemplar; (b) principle candidate "when X, do Y,
   because measured Z" — principles require support from ≥2 distinct
   episodes; (c) contrast pair. Provenance tags mandatory.
3. DEDUP + INTERLEAVE: canonical dedup (reinforce, don't duplicate);
   mix old compiled exemplars with the new delta (CLS interleaving law).
4. RENDER fixed training sequences (chat-format), record exact token counts.
5. TRAIN cumulative LoRA from CLEAN BASE on all compiled data to date
   (clean-base law). v6 default rank 16, attention+MLP targets. Adapter-off
   diagnostic at every checkpoint.

## 5. Experiment shape (v6 scout — Rohin's protocol, drafted)

- ARMS (identical bootstrap, model, context layout, budgets, tools, files):
  A. frozen loop (no LoRA ever)
  B. loop + sleep-compiled LoRA
  (later: raw-trajectory LoRA; outcome-shuffled LoRA — not v6)
- LIFETIME: ~24 training programs, sleep after every 8; sealed held-out
  probe set (8 programs) evaluated with clean context at checkpoints 0/8/16/24.
- SCORING: deterministic IR instruction-count reduction (not runtime — no
  measurement noise). Probe metrics: score, attempts-to-first-improvement,
  AUC of the checkpoint curve. HEADLINE: d1/d2 of held-out curve, arm B vs A,
  across ≥3 independent lives per arm (derivative estimates need replicates).
- TIME-AWARENESS: clock in the state block; time_cost in the ledger; budget
  visible. Both arms identical.
- NEVER-WORSE BY CONSTRUCTION: support gate means worst case sleep writes
  ~nothing and B degenerates to A; any B<A is a measured sleep-failure
  signal, reported not hidden.
- Both arms may keep files/notes/artifacts (same abilities); B's advantage
  must come only from the adapter.

## 6. Protocol rulings (Rohin, 2026-09-04)

1. Sleep every 8 episodes; lifetimes should be HUNDREDS of episodes, not 24
   — slower learning rate is easier to learn on but needs the longer
   horizon; there is an optimal band per problem and we just need to be
   inside it. Sleeping too often = compiling on too little; too rarely =
   learning rate decays. (Lifetime revised: ~128+ training programs; probe
   checkpoints every 16.)
2. COMPILING IS A MODEL'S JOB — the sleep transform is THINK-calls, never a
   mechanical CS-style compiler. Training-sequence LENGTH (short atomic vs
   longer narrative exemplars) is an open calibration knob; v6 default =
   short atomic (consistent with the proven 1-hop law), knob exposed.
3. Probe context: shouldn't matter in theory — keep clean-context (cheapest,
   cleanest).
4. Free-flow loop (see section 2, revised). No literal tick alternation;
   planned thinking emerges; state maintenance is the real design surface.
5. 7B: yes — maximize speed; "dumber model, quicker teaching" as long as
   measurement is good. Rank: v6 runs a single rank (16). "Sweep" = a later
   experiment varying adapter rank (capacity) to find the inverted-U (too
   small = cannot store structure; too big = memorizes episodes instead of
   compressing structure); deferred, single point now.

## Infra law (2026-09-08): killing processes on a shared node
Lives run vLLM in-process and own `EngineCore` children. Never kill by process name (`EngineCore`, `Worker`, `api_server`) on a node that hosts lives. Kill only (a) PIDs reported by `nvidia-smi --query-compute-apps=pid --format=csv,noheader -i <gpus>` for the specific GPUs being cleared, or (b) EngineCore processes whose parent is PID 1 (true orphans). Lives are resumable (wake/sleep/adapter markers), but an interrupted wake batch leaves partial rows in the ledger that are re-recorded on resume.
