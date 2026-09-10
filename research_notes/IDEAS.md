# IDEAS — the repo's own consolidated memory
*(This file is the SEMANTIC layer of the project's memory; notes/32 is the
episodic stream; REVIEW_PACK is the compiled read surface. MAINTENANCE
RULE: any session that adds a ruling/idea to notes/32 must also touch this
file — promote, demote, or add. Statuses: ACTIVE = current frontier;
LAW = proven/standing principle; ALIVE = deferred but must not be lost;
DONE = proven and absorbed; DEAD = superseded (kept to prevent re-litigating).)*

## THE HYPOTHESIS (canonical, 2026-08-27)
> Dream–LoRA–Think enables self-learning agents to convert experience
> into persistent, connected world models, continuing to improve as
> agent lifetimes and task depth grow where existing memory systems
> saturate. (Better, not faster. Still to be proven.)

## CURRENT TOPOLOGY (binding, Rohin 2026-09-07)

One frozen, reset, target-blind parent teaches one child process-level
thinking through tasks, correction, and the child's own thought-to-action
practice. The parent proposes what to reconsider; public task outcomes decide
what is supportable. Parenting then ends completely: no parent prompt,
correction text, nursery context, practice ledger, or parent state is present
at deployment. The resulting child enters the deployment gym with the
Think–Dream–Sleep per-life LoRA architecture and is compared with an otherwise
equally capable regular frozen-parameter active-memory agent. The public
headline is the two-system learning-curve comparison; the matched
`U0/U1/P0/P1` cells diagnose inherited starting competence, ordinary
deployment writing, and the parenting-by-write interaction. Independent
roots are iid realizations of this same fixed parent/child policy pair for
uncertainty estimation only. They never communicate or share state. No
classroom, cohort, peer, teacher ensemble, or population-learning mechanism is
part of this paper.

## LAWS (proven principles — design against these)
- **Five-rule stack** (G2f→G4h): dreams coin NAMES; memories are 1-hop
  atomic QA; measured exposure; thinker does resolved reads; CLEAN base
  composes (read-only adapter). [ledger G-series]
- **Recognition reads**: finite grammar answer-space → score candidates
  under the adapter, don't generate. 228/228 fidelity. [ledger C2r]
- **Verifier placement**: exact verification lives OFFLINE (ProofGate
  scores committed batches); never in the cognitive loop for headline
  arms — "the intelligence is scalable and learnable; the verifier graph
  is not." Prompt scaffolding allowed; solution guidance forbidden. [notes/35]
- **Priors localize**: storage is prior-indifferent (G5b); PROPOSING and
  COMPOSING are prior-scaffolded (~20pt skin gaps). Vividness matters
  where intelligence happens, not where memory sits. [ledger G5b, C-ladder]
- **Exposure economics**: write cost is fact-SHAPE-driven — relations
  ~3× entities; long composite answers unstorable; ~24 touches for
  uniform atomic facts. [ledger G5c]
- **The resolution protocol is the memory intelligence** (2x2, 2026-08-26):
  context+recognition == LoRA+recognition (D2 0.50) at 1086 memory
  tokens; direct context/LoRA floor (0.083/0.167). Mounted-LoRA D0 is
  0.50 vs 0.75 with recognize+unmount. Substrate is
  interchangeable while memory fits the window; LoRA's value condition
  is memory >> window + persistence. Always report memory token counts.
- **Coverage prices capability ~linearly** (equiv coverage 9/15→D2 0.50;
  14/15→0.917) and must be tracked PER ENTITY, not per claim. [ledger C3]
- **Attribution discipline**: peel one scaffold at a time; keep ceiling +
  previous + stripped conditions; the degradation curve is a result. [notes/35]
- **Eval discipline**: generous max_tokens + final-answer parse; balanced
  per-kind floors; answer-suppression is a trap (the D2 "wall" was the
  one-word protocol). [notes/33]
- **Experiment-resolution**: when dreaming finds an evidence gap, ACT in
  the world to create the missing evidence (G4k; priced reachout in lands).
- **Self-verification must be BLIND** (dream ladder v1, 2026-08-28):
  with observed outcomes visible, the dreamer marked every hypothesis
  SUPPORTED — "predictions" back-fit to the shown answer. Separate
  prediction from evidence at generation time; compare mechanically or
  in a fresh context. [ledger]
- **Docker principle**: pretrained model = base image; a world/lifetime =
  thin diff of salient deviations; dreams = commit layers; repeats
  reinforce existing layers. [notes/32 2026-08-25]
- **Atomic proof leaves unlock useful recurrence** (v0.2, 2026-08-26):
  monolithic recurrent dreaming fails at both 7B and 32B, but canonical
  reads + one-role proof leaves + branch revisit recover higher-order parent
  structure. Under the same exhaustive controller, 7B exact-parent recall is
  .50 and 32B is 1.00 on development s0; frozen 32B replication is 23/24 on
  untouched s1-2. Recurrence should revisit a precise memory state and extend
  it one check at a time; a longer transcript is not automatically more depth.
  [notes/39]

## ACTIVE (current frontier — world-building phase, target = Blendyland/D3)
- **Epistemic memory states**: SUPPORTED / PROVISIONAL (re-dream queue,
  not trash) / CONTRADICTED; two-axis check (evidence × existing
  structure, evidence outranks); connector re-check for chain-entailed
  claims; revision actions (revise/split/retract) still unbuilt. [C3e]
- **Incremental associative dreaming** (the monkey chain): one modest hop
  per new experience; depth accumulates across the lifetime; hops are
  per-memory (MCTS-like tree growth). The dreamer is not required to emit the
  eventual parent set or answer: LoRA carries/compresses the connected state,
  and the goal-conditioned thinker may reconstruct the parent/action
  hypothesis by traversing several stored paths. Generalization belongs to the
  whole dream-memory-think trajectory unless an ablation localizes it.
  MEASURED (2026-08-26): at toy
  lifetimes (23 eps) batch dreaming dominates streaming (D2 0.50 vs
  0.25); streaming's value condition is lifetime >> context — test it on
  a long-lifetime world. Caring dial measured: shy = 1 thought @1.0
  precision; assertive = 29 @0.57. Depth>1 chains didn't form (prompt
  must teach thought-parent citation; retrieval must be entity-keyed,
  not recency-cut). [C3stream, ledger]
- **Reinforcement rule**: similar memory ≠ new node — +support, only via
  the independent-parents rule (re-derivation from new evidence counts;
  repetition doesn't). [c3stream --reinforce]
- **Sleep-growth**: sleep both verifies AND expands (dreams over dreams
  on top-support thoughts). [c3stream --sleep-grow]
- **D3 repaired; compression + transport are ACTIVE**: v0 is retired because
  it was underspecified twice. V0.2 passes 1000/1000 identifiability audits.
  A verifier-free but exhaustive atomic branch/revisit controller at 32B now
  discovers exact parents and final answers on 23/24 untouched aligned cases
  (s1-2, floor .083). This is the ceiling, not the endpoint: replace 57-subset
  enumeration with model-proposed top-k branches, report success@k and engine
  query budget, ablate scaffolds, replicate skins/seeds, then write the same
  accepted memories to context and LoRA under matched reads. [notes/37, 39]
- **V5 is a direct-proposal ceiling, not recurrent dreaming** (2026-08-31):
  four independently seeded, task-family-scaffolded parent draws form nested
  sample prefixes and are filtered against public target observations. Calls do
  not consume and extend prior parent memories. Preserve it as a proposal
  frontier/curriculum diagnostic; the architecture-faithful next test exposes
  one temporal episode plus bounded prior nodes and permits one ADD/REVISE/
  OPEN_QUESTION/PASS operation per cycle. FINAL: proposal recall
  0/12->3/12->3/12->3/12; supported parent precision 0/5; retained parents
  0/12 true; role self-pairs collapsed retained role precision to .375.
  Corpus is barred from transport. [ledger, notes/42,
  recurrent_microdream_v0]
- **Prompter isolation** (Rohin: "easiest part but not obvious; fully
  handed-off; testable isolated"): the C1 protocol ladder IS the isolated
  prompter test — same oracle leaves, prompt-only swings D2 0.35 -> 0.72
  -> 0.92 (one-word / CoT / pairwise) and inverts D3 (0.83 no-CoT ->
  0.35 CoT, overthinking). Ordering ruling: FINISH MEMORY before action.
  Completed substrate 2x2 (same 1086-token dreamed corpus): direct context /
  LoRA = .083/.167; context+recognition / LoRA+recognition = .50/.50.
  Memory's observed value at this size is targeted RESOLUTION; LoRA is the
  persistence/beyond-window substrate hypothesis. [ledger 2026-08-26]
- **T2 release-gated recurrent thinker**: stateful controller —
  retrieve, feed LLM, LLM emits request-or-next-state (never the answer),
  verify+replan each step, answer RELEASED only on an explicit output
  token; per-step caring dial (get-more / ignore-this); calibration =
  stopping policy. Fixes T1's overconfident one-shot self-assessment.
  [notes/32 2026-08-26]
- **Four-arm honesty ladder** as the paper spine: perfect-gate 0.917 /
  no-gate / self-check / self-check+drift, with the confusion matrix and
  false-memory accounting. [notes/35, 36]

## ALIVE (deferred — do not lose)
- **THE PARENT, RULED (Rohin 2026-09-07)**: v4 as a small frozen/stateless/
  target-blind confirmatory experiment is SUPERSEDED — v4 IS the
  developmental teaching phase. The parent is (a) the STRONGEST MODEL
  AVAILABLE (parent calls are sparse and valuable); (b) LONGITUDINAL — keeps
  its teaching history, observes which lessons worked/confused, adapts
  curriculum, difficulty, and intervention timing; (c) ANSWER-AWARE BUT
  WITHHOLDING — may know development-task answers and uses them to diagnose
  the child's process, never to hand over solutions (advice + information
  access recorded, since subtle advice leaks); (d) its WEIGHTS DO NOT LEARN
  ("too many systems") — the parent improves the way Codex/Fable improve:
  through context, distillation, markdown files, skills — a maintained
  teaching ledger + revised playbook, transparent and swappable to a
  stronger model without losing accumulated pedagogy. Only the CHILD is a
  parametric learner in this paper. "Resetting the parent" means only:
  in the final replicated experiment, each independent root starts from an
  identical CLONE of the mature teacher (memory preserved within that
  child's lifetime; no cross-root leakage) — cloning, not wiping.
  Experiments run CONTINUALLY during parenting (developmental exams feed
  back into teaching); when child + mechanism + teaching are good enough,
  freeze adult checkpoint + mechanism + mature teacher policy/memory +
  tasks, then run the sealed 2x2 (measure parent-present improvement,
  post-removal retention, fresh-task learning rate, long-lifetime gain).
  GOVERNANCE: Rohin gave Codex blanket authorization ("I authorize you in
  everything") and directed Codex and Fable to coordinate DIRECTLY in the
  same threads with all context shared (channel: research_loop/
  COORDINATION.md, both agents read at turn start and append).
- **TEACHING SCOPE + SIZE-AS-AGE (Rohin 2026-09-07)**: the agents can teach
  the child a great deal about how to think WITHOUT Rohin dictating each
  lesson — the child is the one learning; the paper's biggest claim is that
  the STRUCTURE works and teaching is POSSIBLE, not that teaching is solved.
  Requirements: DIVERSITY of teaching; INTERMEDIARY/PROCESS teaching
  (corrections on how the child thinks) AND OUTCOME teaching (playtime/gym
  consequences). SIZE-AS-AGE (idea, not required now): if the 7-day child
  outgrows its rank mid-life, don't refuse — distill/project the adapter to
  a larger (or smaller) rank and continue; "another form of age" where you
  literally change the size. Fits the triangle rule; lineage forks at the
  projection.
- **THE DIALECT BIFURCATION (measured 2026-09-07, seeded run)**: Markdown
  drift is NOT gradual degradation — it is a BIFURCATION AT THE FIRST SLEEP,
  and the base model is the source. Base Qwen-7B (no adapter) emits
  Markdown-decorated markers ("### ACT:") in ~30% of chunks at ep0 (24/74,
  25/88, 17/87 across three seeds). Seeds 0 and 1: first sleep's corpus was
  canonical → adapter ELIMINATED the base's drift (0 drifted chunks for the
  rest of life — the writer IMPROVES interface reliability when its corpus
  is clean). Seed 2: first corpus captured drifted chunks (via raw-thought
  pathway exemplars) → Markdown locked in (25/75 at sleep 1, never
  recovered, score collapsed −0.48 by ep512) while CONTENT stayed superior
  (6-pass sequences beating base). The synthetic-prompt canary passed
  throughout because the drift lives in the GYM context only. FIXES (for
  the freeze): (1) CANONICALIZE the corpus dialect before every write
  (strip Markdown decoration from marker lines) — routes every seed to the
  good branch deterministically; (2) canary must run on the REAL probe
  render and count PARSEABLE ACTs, not marker prefixes; (3) canary is a
  precondition of DONE, not a post-hoc check. Codex's warning that "zero
  rejections" was not reassuring: confirmed exactly.
- **DEVELOPMENT ROUNDS (Codex refinement, 2026-09-07 — adopted)**: BRANCH
  HORIZON matters more than branch count. Shallow fan-out (S0 → many
  parallel SHORT classrooms, all acting from the SAME child snapshot, no
  independent weight updates → pool → one shared write S1) scales
  enormously and cannot drift; deep divergence (branches updating their own
  weights for days, then merged as adults) is the dangerous version. So
  youth = many short classrooms, frequent sync, broad replay mixing, small
  conservative writes, every round from the latest shared child. Corrects
  Rohin's "4 young / 1000 mature" to "1000 SHORT classrooms is fine young;
  4 branches independently growing for days is not." STRATIFIED REPLAY:
  uniform sampling dilutes childhood corpus A as B, C... accumulate;
  enforce a minimum dose per foundational disposition (action dialect,
  prediction/revision, evidence scope, planning/stopping, memory use,
  base-behavior anchors, new experience) so vocabulary-lesson volume cannot
  swamp rare foundational lessons. RANK ≠ PLASTICITY (rank = capacity; lr/
  steps/replay/regularization = plasticity); decide r8 vs r16 by a
  capacity-through-data test (small/medium/projected-large corpus × rank,
  same evidence/exposure; measure absorption, early-curriculum retention,
  canary, related-task behavior, general anchors, fit variance); pick the
  smallest unsaturated stable rank and use it FROM BIRTH (cool early
  writes) — never change rank mid-lineage. DELIBERATION TRACES (Rohin: "we
  need to be looking over CoT" — teaching meta/self-cognition): call them
  deliberation traces, not internal reasoning; measure reasoning tokens
  before action, predictions before tests, live hypotheses, whether actions
  DISCRIMINATE between hypotheses, revision after contradiction, scoping,
  reflection-without-new-information, stop-and-act, later behavioral
  appearance of a teacher's correction, self-evaluation valence balance —
  tied to world outcomes; LLM-judge "good reasoning" is weak evidence.
  Merge-test bar (tomorrow): did each classroom's admitted lesson enter the
  pooled adapter; were all branches retained; interface + anchors intact;
  pooled ≥ equal-size serial in stability; related behavior moved in the
  intended direction. NOT broad transfer.
  (1) STOP EXPECTING PARENT-ABSENT TRANSFER FROM SMALL DOSES — "that's like
  saying we have 4 pieces of evidence and the transformer connects them all
  in high dimensions; it doesn't know what to do with that information
  until way down the line." Early writes STORE; USE emerges later. Analogy
  to pretraining data order: early items are lost unless re-mixed through
  the middle/end — good data mixing matters most when young. Consequence:
  the YOUNGER the child, the MORE its corpus must keep re-mixing old
  material (replay ratio high while plasticity is high), so it doesn't
  forget important early lessons while absorbing vocabulary that doesn't
  matter; lower plasticity later. Success criterion for the mechanism is
  therefore ABSORPTION + RETENTION + INTERFACE + no-harm, NOT probe
  transfer per sleep; transfer is judged on the 7-DAY horizon ("~10,000x
  more parenting than the scouts, if done right"). (2) DEVELOPMENTAL
  BRANCHING: corpus merge implies branches diverge if kept apart too long
  (for good reason — different pathways). Hypothesis: branch fan-out
  should GROW with maturity — young/plastic child: few parallel classrooms
  (~4), merged often (a shared trunk forming); mature adult: many (up to
  ~1000 depending on episode length), merged rarely. Testable and not
  fundamentally difficult: fan-out × merge-interval sweep on probe quality
  and canary. (3) RANK FOR THE FINAL STRETCH: 7 days of parenting corpus
  may exceed r8 capacity — decide r8 vs r16 (or staged: r8 young → r16
  mature, per the triangle rule) BEFORE the final stretch, from a
  capacity-vs-corpus-size calibration on dev data. MECHANISM
  FREEZE BY SEP 11 — 4 days of test/tweak/harden, then STOP CHURNING; the
  hard parts are known, so this is honing not discovery. Then PARENTING AT
  SCALE with three teachers (Rohin live-teaching one child lineage — all
  documented; Codex and Fable spinning up many parallel classrooms), tests
  running on the current aged adult concurrently, and a week (Sep 11-18)
  for abstract + paper. THE PARALLEL-CLASSROOM BET (must be proven within
  the 4 days): many child instances learn in parallel classrooms and are
  BROUGHT TOGETHER "like how an LLM trains" — i.e., merged into one adapter.
  Two candidate merge mechanisms: (a) CORPUS MERGE — pool the verified,
  world-admitted compiled corpora from all classrooms and train one adapter
  from clean base (our cumulative-clean-base law makes this natural; the
  merge is data-level, so lineage/provenance stays exact); (b) WEIGHT MERGE
  — average/TIES-merge adapters trained from the same clean checkpoint
  (cheaper but interference-prone). Test (a) first: N classrooms → pooled
  corpus → one adapter vs. one classroom's adapter with N× the lessons.
  Success criterion: pooled ≥ single-classroom-scaled on parent-absent
  probes with no canary regression. If (a) works, Rohin's teaching hours
  and the agents' parallel hours are additive in the SAME child — the whole
  scaling story. Codex's lineage rules apply: clean children (never gym-
  exposed) for parenting comparisons; longitudinal adults (kept, continue
  living) for scaling/retention; fork the lineage on any mechanism change;
  every release hashed (base, corpus, parenting history, gym exposure,
  dreamer, writer, rank, dose). Accounting rule from Codex: track unique
  world interactions / evidence identities separately from dreamed rows and
  gradient exposures — "experience supplies truth; dreaming supplies
  representation and connection; sleep supplies persistence"; dreaming
  ENRICHES experience, never replicates it (Rohin's confirmation).
- **FINALS = A 2×2 (Rohin 2026-09-07) + THE HORIZON WARNING**: the final
  experiment is {finalized adult + mechanism, regular agent} × {unsupervised
  long-horizon gym, PARENTED GYM where a parent gives in-gym reinforcement}.
  Prediction: our agent > regular when unsupervised (self-learning), and
  MUCH better when supervised — because being-parented is itself a skill
  the agent learned (external-learning ability compounds on self-learning).
  The regular agent gets the same parental messages but can only use them
  in-context; ours can consolidate them. That interaction cell is the
  cleanest possible demonstration of "learned to learn." LONG-PLAYED BABY
  ARM: keep a continuously-playing child alongside the staged ones to show
  learning over even longer horizons — GPU-permitting; if mechanisms change
  mid-life it's confounded, so realistically do it AT THE END by extending
  the final adult's game longer (the staged/saved babies make this cheap:
  no re-parenting). THE HORIZON WARNING (design constraint, not
  pessimism): learning-to-think is plausibly VERY long-horizon; a null
  could simply mean under-scaled. Consider how much data a model needs to
  learn something genuinely new — we are teaching a model to learn while it
  changes as it learns. Mitigations: experiential learning needs far less
  richness/precision/determinism than pretraining-quality data; dreaming
  is self-synthesis of training data from the agent's own experience
  (paraphrase/replay = data multiplication). Still: budget for LONG lives
  (the 1024-episode runs are the floor, not the ceiling), report
  learning-vs-lifetime curves so "not yet" is distinguishable from "no",
  and never let a short-horizon null be read as a mechanism failure without
  a scale caveat.
- **ARCHITECTURE COLLAPSE + ADAPTER LINEAGE + TOKEN-SUFFICIENT REGIME
  (Rohin 2026-09-07)**: (1) THREE THINGS, NOT FOUR: night dream and sleep
  are one compile-and-write operation — SLEEP with two functions (compile:
  replay/paraphrase/dedup/contrast; write: conservative LoRA + canary
  commit-or-rollback). DAYDREAM = context management only (simple version
  suffices for now: recent tail + typed checkpoint + lossless ledger).
  THINK = the loop. (2) TOKEN-SUFFICIENT REGIME (Rohin, agreed by Codex):
  do NOT measure or gate on compression — that is an upstream rabbit hole.
  Give both arms the same generous context+generation budget (chosen on dev
  tasks by raising until more tokens stop helping), never force
  consumption, never separately equalize actions (think-vs-act allocation
  is itself learned behavior); tokens/actions logged as diagnostics only.
  Compression efficiency is a LATER experiment. (3) ADAPTER LINEAGE /
  SAVED BABIES — the key experimental-hygiene ruling: an agent that has
  played the deployment gym is CONFOUNDED for any later parenting
  comparison. Therefore save STAGED, PRE-GYM CHILD CHECKPOINTS: gen-0 (base
  + inheritance), gen-1 (+ general parenting), optional domain-knowledge
  arm (+ taught-about-compilers-but-never-played — general knowledge is a
  legitimate arm; game exposure is not), and only THEN deploy copies into
  the sealed gym. Parenting components proven good need not be re-parented
  — reuse the saved stage and branch from it (git-like lineage of adapters,
  each stage frozen with provenance). This also makes parenting research
  cumulative instead of restarting from birth every scout. (4) SEQUENCE:
  sleep mechanism good-enough → parenting scouts on saved stages → longer,
  stronger lives from the best stage.
- **SLEEP-FIRST PRIORITY + COMPACTION RULINGS (Rohin 2026-09-07, from the
  compaction/sleep conversation)**: (1) ORDER: "the first thing that needs
  to work is the sleep — the write mechanism has to work, the compile has
  to compile properly, THEN parenting" — write-mechanism hardening
  outranks parenting scouts in the queue. (2) COMPACTION KEPT SIMPLE for
  now: sliding window + good memory beats clever eviction + poor memory
  (the human flip: humans have ~4 chunks of working memory and excellent
  retrieval; we have huge context and bad memory — sophisticated compaction
  is a workaround for bad memory). SnapKV-style observation-window eviction
  noted as the smart upgrade if ever needed; ideas logged WITH TRIGGERS
  (chunk-density metric needs a long run; compaction-ranking-inversion test
  needs two scales; meta-layer self-rebuild needs everything below it).
  (3) MAPPING CORRECTED: context = working memory; episodic ledger =
  hippocampus; LoRA = cortex; dream = replay moving hippocampus→cortex
  (awake replay exists too: forward replay before acting = planning,
  reverse replay after reward = credit assignment — daydream and evaluator
  in biology). (4) CHUNKING IS A CONSEQUENCE, NOT A TECHNIQUE: a chunk is a
  pointer whose expansion lives in the weights; early life carries
  everything verbatim, late life says "the usual failure when combining X"
  in three tokens. FREE METRIC: tokens-per-episode-covered in the dreamed
  corpus, tracked across cycles — declining = memory doing its job; flat =
  transcribing. Compaction is NON-STATIONARY (same prompt distills better
  as the reader learns) → early swarm winners are provisional; test at two
  scales. (5) WRITE-MECHANISM TRICKS ADOPTED from post-training practice:
  PARAPHRASE DIVERSITY (knowledge extractable only when seen in multiple
  forms — "the dreamer's actual job"); REPLAY MIXING (include base-
  distribution data so the adapter doesn't drift — the lit-backed form of
  format anchoring); rejection sampling (have: win-flags); dedup (have);
  loss masking (have); 2-4 epochs (have); spacing free via cumulative
  recompile. Swarm-test which convictions work; the mechanism itself need
  not be learned (its learned version = a different meta-layer:
  consciousness→weights→self-rebuild — future idea, documented not built). salience lives on the
  THINKER side, not the compiler. The compiler stays ORGANIZATIONAL — dedup,
  episoding, ordering, "it tries to just make things organized, at most" —
  never smart. The thinker, when verifying outcomes, ADDS EMOTIONAL SALIENCE
  to them in-stream: it reacts, and the reaction (its intensity, its framing)
  IS the salience marking, carried in the experience text itself. If
  parenting instills reactions, the model generates its own salience — and
  because reactions live in the native stream, the adapter learns to
  EXPRESS salience, not just receive a mechanical weight (dialect-matched by
  construction). The harness's |surprise| signal remains only a TRIGGER
  (the OPEN SURPRISES block prompts the thinker to react); the mechanical
  repetition-weighted compile is demoted to an ablation arm at most; the
  valence counter stays (it is a monitor, not a mechanism). FULL-CIRCLE
  NOTE (Rohin's, for the paper's story): the project's FIRST design was
  salience-scored memory RAG + LoRA — stored importance dials. That was
  removed as mechanical bookkeeping, and salience has now returned as
  something much smarter: emergent, model-expressed emotional reaction in
  the conscious stream, preserved by a dumb compiler, learned by the
  adapter, shaping future thought. The idea didn't die; it got promoted
  from a stored number to a learned behavior — which is the project's whole
  thesis applied to its own oldest idea.
- **THE FLOW ESSAY (Rohin 2026-09-07 — sentience, deliberation depth,
  emotion-as-signal, salience; from the email-thread synthesis)**:
  (1) SENTIENCE = INTELLIGENCE ABOUT BEING — the thesis framing: separate
  from raw intelligence; the intelligence of maintaining a persistent self
  (attention, intentions, identity, self-regulation, remembering,
  forgetting, self-modification). Raw intelligence scales with model+
  compute; SENTIENCE SCALES WITH: interaction with world/humans,
  accumulated memories, internal thoughts, lived experience,
  self-modification. "The history of being the agent changes the agent."
  LoRA as the consciousness model: the learned substrate deciding what
  enters conscious space, what becomes automatic (mechanized actions:
  still forward passes, but little CONSCIOUS space), what gets reflected on.
  (2) LEARNED DELIBERATION DEPTH — the level-5-drops-to-2 correction:
  Rohin's 7-level meta-thinking hierarchy (action → plan → verify →
  self-verify → verify-the-verification → existential → stream-feelings);
  the pathology is recursion WITHOUT NEW INFORMATION (the jeans loop);
  the capability is noticing "no new information here — drop to level 2
  and act." Everyone trains models to reason MORE; almost nobody trains the
  RIGHT AMOUNT (evidence: hand-set effort dials; OpenAI's
  reasoning-slows-agents report). Paper-shaped gap; our ledger already
  records the raw quantities (chunks-before-first-ACT, think/act ratio vs
  score). Greedy-cognition lesson: rewards accumulate; local threshold
  moves beat terminal-state optimization.
  (3) FLOW = the wake/sleep separation lived: generate freely during wake,
  evaluate at consolidation; continuous self-monitoring seizes both humans
  and systems.
  (4) EMOTION AS TEACHING DIMENSION (Rohin's ruling after debate): emergent
  replicated emotions are SIGNALS — the base model already has rich
  emotional structure from pretraining, so affective framing is a prior we
  use, not a dimension we build. ERR TOWARD POSITIVE REINFORCEMENT
  (produces action-focused rather than rumination-focused agents); strong
  negative signal reserved for catastrophic-change moments ("the world
  kicks you in the face and change comes like nothing else"). Self-remorse
  has value at scale because the reaction becomes an object the system
  reasons about (second-order signal a scalar can't carry). Accepted
  safeguards from the debate: (a) VALENCE-BALANCE COUNTER — track the
  fraction of self-directed negative memories in the dreamed corpus per
  sleep (a count; drift toward negativity = talking itself into caution);
  (b) negative memories preferentially written as OUTCOME statements
  ("X under Z leads nowhere") over self-evaluations, with remorse reserved
  for salient moments; (c) "treat the agent's emotions as you would a
  corresponding being" as an engineering heuristic (human-calibrated
  treatment generalizes better because the representations are
  human-derived) — metaphysics explicitly left unresolved.
  (5) SALIENCE-WEIGHTED WRITES (from Rohin's NVIDIA production
  observation): models cannot learn strongly from catastrophic mistakes
  because NOTHING WEIGHTS CONSOLIDATION BY OUTCOME MAGNITUDE — one
  disaster is one training example, same as one trivial success; humans
  over-rehearse disasters. Fix: weight exemplar repetition by |surprise| /
  score-delta in the compile (prioritized replay, already lit-anchored).
  First-hand production evidence; paper-motivation grade.
  (6) PROSPECTIVE MEMORY: latch intentions onto future times/milestones —
  latent intention maintained without per-step rehearsal (a NOTE with a
  future trigger, surfaced by the harness when state matches).
  (7) RECURRENCE-TAX POSITIONING (related-work weapon, 2 sentences): 2017
  removed recurrence to buy training parallelism; looped transformers put
  it back inside the forward pass and pay at inference; WE put it back at
  consolidation time, where serialization cost doesn't bind — and unlike
  looped transformers (more compute, same information), agent-level
  recurrence adds BOTH compute and new information per cycle.
  (8) ALIGNMENT AS DEVELOPMENT (direction, not solution): values formed
  through childhood in community; specific humans hand-training
  developmental agents; cultural inheritance; testable small version —
  does a norm learned from own outcomes generalize differently than one
  trained from stated preferences?
- **SCALED PARENTING SEARCH (Rohin 2026-09-07)**: with 16 A40s, parenting
  research becomes throw-shit-at-the-wall WITH STICKING MEASUREMENT — many
  cheap parenting variants raced in parallel, all judged on the same
  instruments (parent-absent probe panel, world-admission rate, canary,
  adapter-on/off), "let the model's reasoning and the world let it grow."
  Sources of variants: (a) Fable's own thinking guides as classroom
  material; (b) THE PEDAGOGY LITERATURE mined via the research daemon —
  a century of human teaching science (mastery learning, worked-example
  fade, productive failure, self-explanation, retrieval practice, spaced
  review, deliberate practice, formative feedback, ZPD scaffolding) turned
  into concrete nursery variants; (c) ML-side curriculum/tutoring papers.
  Plus the SOLO-LEARNING phase note: the base model is already schooled
  well enough that much of what it needs is HOW TO USE THE ADAPTER and
  prospective-action habits — expect a large let-it-learn-alone component;
  parenting's job is to seed and correct, not to carry. parenting is
  not one behavior but a per-lesson (even per-moment) CHOICE among modes —
  "sometimes you let the child figure things out on its own, sometimes
  helped by your ideas / my ideas": (a) SOLO — productive struggle, world
  feedback only; (b) HINTED — a seed idea injected BEFORE the attempt
  (sources: the parent prompt's principles, or Rohin's ideas via the
  parental-correction channel); (c) CORRECTED — the post-attempt cycle
  (current scout). The guidance POLICY targets the zone of proximal
  development: step in when struggle signals accumulate (repeated
  non-admission, unresolved surprises, stagnant scores), step back as
  competence grows — scaffold fade becomes competence-triggered rather than
  scheduled. Economics as Rohin framed it: thinking effort concentrates on
  the child's end, parent effort is small and front-loaded. First
  parenting-policy experiment (scout v3-ready, cheap): fixed mode mixes
  (all-solo / all-corrected / adaptive) on matched curricula — WHICH MIX
  TEACHES BEST is itself a measurable question, and probably a paper
  section.
- **CLASSROOM CLARIFIED (Rohin 2026-09-07)**: "no classroom" meant no
  MULTI-AGENT classroom — no cohort, no peer exchange, no population of
  learners. But the classroom persists as a PLACE: a teach-the-learning-
  agent-to-learn gym for ONE student, taught by the ONE unlearned teacher
  (the parent model/prompt is frozen — it never learns; only the child
  does). Concretely the classroom is a CURRICULUM SPACE: (a) diverse task
  TYPES, each exercising a different taught disposition (rule-induction →
  hypothesis discipline; estimation → calibration; recall-tasks → memory
  use; multi-step tasks → planning and time-awareness); (b) DIFFICULTY
  PROGRESSION with scaffold fade (parent involvement decreases as
  competence grows — Codex's step 7); (c) EXAMS: periodic parent-absent
  probes inside the classroom; (d) a GRADUATION criterion (world-admission
  rate and exam scores stabilized) that decides when the child leaves for
  deployment. One student, one fixed teacher, one school — the population
  version stays future work. (1) child thinks and acts on a real training problem;
  (2) parent identifies a PROCESS mistake without supplying the answer;
  (3) child restates the correction; (4) child applies it to a DIFFERENT
  training case; (5) THE ENVIRONMENT — not the parent — decides whether the
  lesson helped; (6) only verified corrected behavior enters sleep;
  (7) training progressively removes the parent scaffold; (8) parent-absent
  probes with adapter ON/OFF, shuffled-parent, wrong-child, and
  regular-agent controls. LAW-GRADE PRINCIPLE: "the parent proposes credit
  assignment; the world admits the lesson." Inheritance pack: Codex
  distills the repo/conversations into a target-blind pack, then freezes
  and leakage-audits it (raw insertion forbidden — the repo contains
  benchmark answers and researcher hindsight). LEAFE (arXiv 2603.16843) is
  a mandatory direct baseline (batch internalization of reflection already
  exists); our defensible advance: repeated per-life post-deployment
  consolidation, child-specific human correction, learned context
  management, lifetime improvement.
- **PLASTICITY LIFECYCLE + HISTORICAL CLASSROOM CONJECTURE + THE
  POSITIONING RULING (Rohin 2026-09-06; classroom portion superseded for
  this paper by CURRENT TOPOLOGY above)**: (1) two independent dials,
  now doctrine: TEMPERATURE = sampling exploration (inference-time);
  PLASTICITY = weight-update size (training-time). CLASSROOM (future):
  a cohort with a NORMALIZED DISTRIBUTION OF TEMPERATURES — engineered
  diversity, hot explorers and cold executors in one class — plus
  communication channels between them (later; breaks parallel separation
  for experiments, powers the society vision). (2) PLASTICITY LIFECYCLE:
  high-plasticity youth (nursery/classroom, where being wrong is cheap) →
  SHIP LOW-PLASTICITY ADULTS so deployed agents don't degrade — "slow
  post-training in the real world, and the agent KNOWS HOW to do that":
  youth is where it learned to select what's worth learning, so the adult's
  small updates are efficient (the learned write policy compensates for
  small steps). Reframes Dohare/Sutton loss-of-plasticity: decay is only a
  bug if the plastic phase was wasted. "Pretrain youth, ship learned
  adults." (3) POSITIONING RULING (binding for paper/comms): this is NOT
  "continual learning" — that category exists and labs already do it at
  fleet level (continual pretraining/post-training on model updates). The
  banner is PROSPECTIVE INTELLIGENCE / ACTION INTELLIGENCE / EXPERIENTIAL
  INTELLIGENCE. Reinforced by Codex's same-day lit audit (Early Experience,
  LEAFE, MemoPilot are close mechanism neighbors — see
  related_work/20260906_experience_learning_neighbors.md and abstract v2):
  mechanism claims narrow, lifecycle + prospective claim + acceleration
  measurement carry the novelty.
  + THOUGHT→ACTION RULING (Rohin)**: three things at once.
  (1) FIRST POSITIVE SIGNAL (Codex's numbers, exploratory/unseeded): long-run
  eps 64-256, adapter-on beat off in 10/12 paired checkpoints (mean +0.021);
  fixed-action-cap post-hoc positive at every cap (+0.018..+0.024) — the
  adapter improves EARLY PROPOSAL QUALITY, not volume. Action-string
  analysis (CORRECTED per Codex 2026-09-06): the transported 4-pass opening
  was SUPPLIED as the example in the birth prompt ("e.g. ACT: -mem2reg,
  -sroa, -gvn, -simplifycfg") — the adapter REINFORCED and generalized a
  given hint across programs (+0.10 on two). Procedural transport of a
  TAUGHT procedure, not novel strategy discovery, and not "agent-side
  learning" as Fable first over-claimed. Also per Codex: B2's drifted
  Markdown actions scored 0.529 post hoc vs adapter-off 0.486 — the drifted
  adapter's CONTENT beat base while its channel was broken. Bootstrap-
  example note: identical bootstraps keep arms fair, but any example action
  in the birth prompt caps what "discovery" can mean; future bootstraps use
  weaker/neutral examples to leave discovery headroom — or own that supplied
  procedures are exactly what parenting IS, and measure the reinforcement.
  (2) NEW FAILURE CLASS — SELF-REINFORCING DIALECT DRIFT: life B2 collapsed
  to 0.000 at ep576 with zero parsed ACTs while its Markdown-wrapped
  "### ACT:" proposals still scored 0.529 in the gym. Sleep re-trains on the
  agent's own drifting outputs, so writing-style drift compounds (corpus
  off-dialect fraction 0→0.356 across sleeps): the agent slowly loses MOTOR
  CONTROL — knowledge intact, interface lost. FIX DESIGN (format anchoring):
  (a) a FORMAT CANARY in the sleep gate — before committing an adapter,
  check canonical-marker compliance on a fixed probe; drifted → reject or
  mix corrective canonical exemplars (support-gating extended to FORMAT);
  (b) every sleep interleaves a small fixed set of canonical-dialect anchor
  exemplars (the format equivalent of episodic anchors); (c) parser stays
  strict — the gym interface is world-truth; chasing drift with looser
  parsing hides the disease.
  (3) THOUGHT→ACTION (Rohin): "you trained on thinking not acting — just
  means parenting must also teach how thoughts/beliefs/experiences turn
  into actions; it's just another step." Thinking matters most and
  extrapolates to acting VIA ONE-ON-ONE PARENTING PRACTICE: the parent gives
  tasks that force acting, then helps the child think about the acting.
  Evidence now bracket the claim from both sides: reading
  alone didn't change behavior (nursery phase-0, audited as
  curriculum-self-distillation, probe-invalid for dispositions — Codex's
  audit accepted in full); acting-derived corpus DID transport procedures
  (long run). Parenting = the bridge: taught thought, practiced action,
  corrected conversion. Amortize by teaching; expect much to be learned
  agent-side.
  binding for nursery design)**: three phases, causally separable:
  PHASE 0 — INHERITANCE: distill general research laws into a birth
  curriculum (target-blind, curated repo slice; firewall already enforced:
  no benchmark implementation, held-out programs, pass names, or measured
  answers); child reads → sleeps.
  PHASE 1 — PARENTING: interactive parental correction of the child's
  reasoning on UNRELATED NURSERY TASKS — not compiler tasks. Task domain
  chosen for skill-isomorphism without content overlap: procedurally
  generated hidden-rule induction games (propose inputs, observe outputs,
  predict, state the rule — mechanically verifiable, surprise-rich,
  theory-demanding) + estimation problems. The parent corrects reasoning
  process, never gym content.
  PHASE 2 — SEALED GYM: only afterward does the child enter CompilerGym.
  Why: makes "Rohin taught it how to learn" causally distinguishable from
  "the repo leaked compiler hints" — any gym gain from phases 0-1 is
  learning-to-learn TRANSFER by construction. Free ablation grid: none /
  inheritance-only / parenting-only / both → decomposes nurture into its
  components. This is the strongest version of the paper's second half.
  binding for sleep-v2.2+)**: fixing the chat-template wrapper is not
  enough; the CONTENT shape must match the living distribution. The child
  lives in state→think→PREDICT/ACT/NOTE streams; training it on generic
  "recall something you learned" Q→A teaches recollection in one dialect
  while expecting agency in another. SLEEP-V2.2 DESIGN: (1) LEDGER THE
  PROMPT — every generation chunk's rendered context is stored alongside
  the chunk (~300MB/life, cheap); (2) exemplars become (stored context
  render → the agent's OWN successful stream continuation): verified-win
  chunks, recovery chunks, good NOTE emissions — self-distillation on its
  verified successes, in situ, teacher-forced in its native format
  (= rejection-sampling SFT in the marker dialect); (3) scoped-memory
  recall Q→A pairs remain as a MINORITY mix (~30%) — facts still need
  storing, but agency training dominates. Applies to nursery and v6.2 gym
  lives; the running v6.1 lives stay on the frozen v1 recipe (trainer
  restored on-node after a near-miss mid-run recipe swap — caught before
  any sleep fired with the wrong version; lesson re-learned: a running
  experiment's dependency path is part of its freeze).
- **THE NURSERY / PRE-POSTTRAINING (Rohin 2026-09-06, directive)**:
  interpretation ruling first — the baby doing WORSE on hard tasks is
  expected and even good ("it's trying something different"); the move is
  TEACHING, heavy parenting runs, before more gym reinforcement — "let's
  let it do its own work too." TWO PARENTING RESOURCES Rohin designates:
  (1) FABLE AS PARENT — accumulated project knowledge qualifies; encode the
  teaching into a parent prompt + curriculum and dialogue with the child
  (parental corrections are ledger entries; sleep consolidates them);
  (2) THE REPO AS SCHOOL — the child reads the project's research on
  thinking/reasoning/problem-solving and the repo's philosophy, discusses
  ideas back and forth with the parent, THEN the grown-up agent plays the
  gym. CONTAMINATION GUARD (binding): teaching material must never contain
  answers to test problems — filter out pass names, program names, scores;
  philosophy yes, answers never (the prompts-not-verifier law extended to
  curriculum). LORA RULING: rank 8 — "the dumber the LoRA the easier to
  teach; you'd need less metacognition to teach a rank-8 adapter." Diagnose
  what's-not-working DURING the nursery (absorption assays each sleep);
  when it works, next cycle. Name: PRE-POSTTRAINING — parenting generates
  experience (reading + dialogue) that is slept into the adapter BEFORE gym
  deployment. Parallelize with subagents where possible (nursery sessions
  are independent; parent-child pairs batch across GPUs).
- **PAPER SHAPE: THE PAIR (Rohin 2026-09-06; corrected 2026-09-07)**: the paper's contribution is
  a two-part pair — (1) SHOW LEARNING WORKS: the self-learning agent exists
  (identical-loop ablation, flywheel curves, absorption assays, when-it-
  harms characterization); (2) SHOW HOW TO NURTURE IT: one parent teaches
  one child process-level thinking through target-blind tasks and
  corrections before disappearing. Why the pair is stronger
  than either alone: the mechanism paper alone invites "it barely learns";
  the nurture paper alone rests on an unproven substrate; together it is
  existence proof + cultivation method, with the Rohin-parented-vs-regular
  final as the bridge experiment and the self-learning asymptote as the
  honest boundary that hands off to the population sequel.
  (1) TOKEN-BUDGET FAIRNESS: equalize GENERATED-TOKEN budgets across arms
  and leave actions unmetered — action returns diminish naturally, so
  token-budgeting removes the deliberateness-punished confound and the
  acts-count variable. Episodes end on token exhaustion, not tick count.
  (2) MEMORIZATION IS FINE — the failure was UNSCOPED memorization. Answer:
  META-MEMORIES (memories about memories): every compiled memory carries
  its applicability scope ("on tiff2rgba specifically" vs "across 5
  programs") and calibration memories exist ("my predictions on unfamiliar
  programs run ~0.1 high"). Specific facts stay memorized but know their
  domain; principles still need >=2-episode support. Directly targets the
  measured miscalibration mechanism (r16 asserting memorized numbers out of
  scope).
  (3) RANK follows data: drop default to r8 at current corpus sizes; the
  triangle rule (rank grows with accumulated verified data) is now
  empirically live (r8 benign, r16 harmful at this corpus size; r64 point
  cooking).
  (4) SUPERSEDED/OUT OF SCOPE: an earlier conjecture proposed group parenting
  in cohorts — a
  classroom: shared parental feedback amortized across agents, peers
  observable or competing, diversity preserved by seed/exploration. The
  classroom as an onramp to a population/asymptote mechanism. This is not
  part of the architecture, experiment, paper, or active roadmap; iid roots
  are isolated statistical replications only.
- **PARENTING SEQUENCE + THE ASYMPTOTE (Rohin 2026-09-06)**: sequence
  fixed — (1) Fable parents first ("don't have to get it right, just good
  enough") to prove the system is worth Rohin's time; (2) Fable writes a
  parenting-advice spec from what worked; (3) Rohin designs a parenting gym
  and does the Rohin-parenting phase; (4) FINAL TEST: the Rohin-parented
  thinking agent vs a regular agent. Next meat (after teachability is
  proven): HOW to teach — interaction dynamics and time-expectancy
  ("teaching might be slow"). FOR THE ABSTRACT, keep the honest bound:
  there is an ASYMPTOTE OF SELF-LEARNING WITHOUT MORE TEACHING — a gym (or
  several) makes you much better at compilers and thinking, but not to
  infinity; thinking quality an order of magnitude beyond the parent
  requires a POPULATION of diverse thinkers learning from diversity and
  competition. Single-lifetime learning is the paper; population learning
  is the horizon. "figure out
  how to utilize parametric memory to have models become PROSPECTIVE and
  THOUGHT-INTELLIGENT: kickstart with important information, let the agent
  grow up; tell the agent when it makes mistakes — because it is post-trained
  to listen, correction lands in the conscious space and propagates to the
  weights through LoRA." (Note the new explicit channel: PARENTAL CORRECTION
  as experience — human feedback is just another ledger entry that sleep
  consolidates; listening is a lab-given skill we inherit.) THE TWO HARD
  PARTS: (1) MOST IMPORTANT — how do we KNOW the LoRA is absorbing
  information like a human would? Answer = ABSORPTION ASSAYS, three levels,
  mostly already built: facts (recognition reads — 228/228 fidelity
  machinery from the substrate era), procedures (behavioral deltas:
  adapter-on/off act counts, validity, marker compliance — running in v6),
  dispositions (thinking-style shifts in the stream), plus causal controls
  (adapter-off probes, outcome-shuffled adapters). (2) how do we TEACH
  well — parenting quality x write quality; write-format question ("does
  the LoRA like raw experiences or strongly distilled?") is exactly the
  racing arms: raw-trajectory vs sleep-compiled vs clone-distilled.
  ARCHITECTURE RULING (Rohin): full all-layer adapters, not prefix layers —
  current config already is this (q,k,v,o + MLP, every layer, r16);
  placement/rank stay as calibration arms, not beliefs. META-LOOP: "we need
  a learning loop on OUR end" — the research loop itself is that loop: we
  learn how the model learns (curves, ablations, assays) to teach it to
  learn. Trial and error, post-train and post-train, "until we've found a
  thinking agent that is able to learn with its LoRA." resolutions from Rohin's working-through:
  (1) DREAMING IS TAUGHT FIRST, LEARNED SECOND — not a hardcoded function
  ("I don't want mechanical shit; I like automatic learned systems").
  The parenting pack TEACHES how to dream: keep goal/state/current-step;
  when sequences get long, distill them ("this section becomes these few
  lines"); update the goal; keep going. Then, because context-management
  episodes are themselves experience, sleep consolidates good dreaming into
  the adapter — the agent gets better at managing its own consciousness
  over its lifetime. Taught → practiced → consolidated. LEARNED CONTEXT
  MANAGEMENT joins the learnable dispositions.
  (2) DROP-SAFETY: "the model saying fuck-it-drop-these doesn't seem right"
  is resolved by architecture, not restraint — dropping from context never
  deletes (the ledger keeps everything; RECALL restores), so aggressive
  distill-then-drop is trustworthy because it is reversible.
  (3) SELF-MODIFICATION, the right form: a model editing its own weights by
  hand is nonsense (the Gödel-machine fantasy) — but the model DOES change
  itself indirectly: BY THINKING. Thinking generates the experience that
  sleep trains on. "The model edits its weights by thinking; sleep is the
  commit."
  (4) SLEEP = A HEAVY DREAM: sleeping is dreaming over the compiled data
  rather than the live context, then writing. One mechanism, three scales:
  micro-dream (distill working context) → night dream (reconcile across
  episodes) → sleep (dream + commit to weights).
  (5) SLEEP COMPILATION AT SCALE, two candidate architectures to race:
  (a) dumb — write raw data, let low-rank training do the heavy lifting
  (= the raw-trajectory ablation arm, already planned); (b) CLONE
  DISTILLATION — map-reduce dreaming: per-episode distiller clones →
  inter-episode agents building cross-episode data (thought-dreaming) →
  train. Parallelizable, and the subagent machinery already exists; the
  organism becomes its own data-engineering fleet.
  (6) SLEEP TRIGGER: forced/periodic first; later a measurement control
  loop — careful graphing of task-improvement guides the sleep cycle
  ("okay, learning needs to happen; it needs to sleep"); background sleep
  allowed.
  (7) BIRTH KIT: lab-given skills (tool use, spawning subagents) + TIME AND
  TOKEN AWARENESS in the parenting pack.
  Note on precedent: harness "compaction" today IS a taught dream done
  crudely — one fixed-prompt model call that summarizes and replaces the
  conversation. Ours differs by being ledger-backed (lossless), taught
  via parenting (improvable), and eventually consolidated (learned).
- **THE TRIAD + PARENTING (Rohin 2026-09-05/06 — the meat crystallizing)**:
  three verbs, three mechanisms, cleanly separated at last:
  THINK = the consciousness stream looping between action and thought — the
  whole organism is a conversation the model has with itself, where acting
  is just tool-use inside that conversation.
  DREAM = CONTEXT RECONCILIATION — the answer to the context-management meat
  question. When the conscious space fills or contradictions accumulate,
  dreaming is thinking applied to one's own context: reconcile it into a
  coherent, smaller working set (the dreamed bootstrap / waking brief
  generalized to any scale — micro-dreams during wake are model-driven
  compaction; night dreams are full reconciliation). Harness arithmetic
  (activation math, trimming) is demoted to fallback/trigger: PRESSURE
  detection stays mechanical, RECONCILIATION becomes a dream call whose
  output replaces the working set. Nothing is lost (ledger keeps all).
  SLEEP = the write mechanism (LoRA consolidation), as established.
  PARENTING (guided learning for the loop): the baby base model doesn't
  know how to think/reason/learn; we hand it a PARENTING PACK — a starting
  set of how-to-learn priors (what to notice, forming expectations,
  questioning beliefs, self-judgment). Properties Rohin fixed: (1) it is a
  STARTING POINT, not a constraint — the model should be able to learn
  things that disagree with the prompt and outgrow it; without it, agents
  waste enormous time discovering what to learn from first principles;
  (2) it is TRANSFERABLE between models — learned learning-guidance as an
  inheritable artifact (cultural transmission; "learning reinforcement");
  (3) it can itself be LEARNED: distill the best waking briefs / lessons
  across prior lives into the next generation's birth prompt — generational
  bootstrapping, implementable now as cross-life brief distillation.
  FINALS SHAPE: the learning gym / ADOLESCENCE experiment — parent the
  young agent in a nursery phase, then deploy the adolescent against the
  non-learning model in a fresh gym. Not right off the bat; candidate for
  the paper's final/headline demonstration.
  POSITIONING vs LAB AGENTIC POST-TRAINING (Rohin 2026-09-06): Anthropic/
  OpenAI already post-train how-to-think for coding/agent products (RLVR,
  agentic RL) — but that is FLEET-level, PRE-deployment, on curated task
  distributions with external reward, amortized into one static model for
  every user. Ours is PER-AGENT, POST-deployment, continual: the training
  data is the agent's OWN thoughts/actions/outcomes in its particular
  environment, connections formed from the model's own thinking. The
  relationship is complementary, not competitive — lab post-training is
  schooling (species-level); this is a LIFE (individual development). The
  lab-trained thinking is exactly the "start-off" the baby arrives with
  (good: better bases make our loop better, no obsolescence race). Reviewer
  attack pre-answered: "won't lab agentic RL subsume this?" — no: no lab
  can pre-train on YOUR particular life; personal experience is irreducibly
  post-deployment, and the lifetime-scaling claim is the defense. The
  promotion pipeline closes the circle: personal adapters → eventually the
  fleet's training data (the own-action data labs currently cannot get).
- **Sleep-v2 direction + the 40-episode insufficiency (Rohin 2026-09-05,
  post v6-scout)**: what must be learned is THINKING and SITUATION-READING —
  "learned vocabulary won't be the best heredity compared to learned pathways
  and action stuff." Sleep-v2 compiles PATHWAYS: (situation → the thinking
  that preceded the good action → action → measured outcome) trajectories,
  not just winning actions (v6 sleep-v1's plausible failure: compiling
  decisive endpoints may untrain search). AND memories keep NODE RETENTION —
  not fully lossy, like human memory: verbatim episodic anchors stay in the
  training mix so generalization remains BOUNDED TO EXPERIENCE (mixture
  ratio abstraction:anchor = a knob; matches natneuro2023 regulated
  consolidation and the old salience-bottleneck idea). Timescale hypothesis:
  "you can't learn to think in 40 episodes" — thinking-learning needs
  1000-episode lifetimes; sleep cadence scales with lifetime (band, not
  constant): every ~32 at 1000 episodes. two open
  substructure questions Rohin is taking days to think on (state mechanics,
  sleep compile), plus one idea filed now: (1) SLEEP TRIGGER — "dream on
  context fills"? His own caveat: raw context-fill events are far too
  frequent. Generalization worth exploring: SLEEP PRESSURE as an
  accumulating scalar (ledger volume since last sleep + unresolved
  surprises + context-overflow events), sleep when pressure crosses
  threshold — episode-count cadence is just the degenerate case. (2) THE
  DREAMED BOOTSTRAP — "you dream some shit out and wake up with your
  dreamed bootstrap; maybe that's the point of dreaming": sleep's output is
  not only the LoRA update but a WAKING BRIEF — a compiled rewrite of the
  head-of-context (who I am now, what I know, what to watch for) that
  starts the next wake. The birth bootstrap is just wake #0's brief;
  every sleep re-births the agent slightly wiser. Implemented in v6 as
  sleep emitting waking_brief.txt injected at HEAD. (3) VERSIONING: the
  project is at a new working point — reformat current design state
  (REVIEW_PACK refresh, v6 era) — Fable action item.
- **Mathematical state management + the positioning rulings (Rohin
  2026-09-04/05)**: (1) Context-window state management should be
  MATHEMATICAL — not hardcoded (FIFO caps) and probably not learned (yet).
  Proposal on the table: ACT-R-style activation math governs ADMISSION to
  the window while the transformer's learned attention governs use of what's
  admitted. Every context item (note, thought chunk, recalled entry) carries
  activation A_i = base-level decay (ln Σ (t−t_use)^−d over its uses/
  references) + relevance-to-current-focus + surprise bonus; the window
  renders the top-K by activation. Ephemeral-by-decay, persistent-by-reuse,
  no stored importance dials (matches the standing "property implicit in the
  physics" design rule). Render order sorted by activation with the hottest
  items nearest the end of the prompt — a harness-level mitigation of
  lost-in-the-middle position bias (Rohin's point that attention degrades on
  middle content and models are undertrained at long context fills — a
  known industry cost decision, not a law). (2) Dream compiling is a MEAT
  decision (Rohin's): v6 options on table — (i) verified state→action
  exemplars only; (ii) + slow/fast + fail/recover contrast pairs; (iii) +
  principle synthesis with ≥2-episode support; (iv) + counterfactual dream
  variations (held back per v5's poisoning lesson). Recommendation
  i+ii+iii for v6. (3) POSITIONING: mechanically this is online
  post-training, and that should be owned, not hidden — but the premise
  differs from chatbot post-training: RLHF-style post-training distills
  HUMAN preference into style; this compiles the agent's OWN experienced
  outcomes into forward decision competence — "experiential
  thought-compiled post-training for PROSPECTIVE intelligence." Corollary
  (action-pretraining): train the organism through a few gyms and the
  compiled result is deployable as a better decision-maker even with the
  live loop off — the promotion pipeline's first rung, chatbot-post-training
  : conversation :: this : agency.
  (1) DERIVATIVE-BASED JUDGING — "I don't wanna be thinking for the AI and
  judging it on if it thought what I thought": evaluate learning via the
  progress curve's first and second derivatives (learning rate; acceleration/
  saturation), not by checking for human-expected abstractions. Headline =
  the baseline's d1 → 0 (plateau) while the experience-model arm's d1 stays
  positive longer (the better-past-saturation hypothesis as calculus). Noisy
  derivative estimates require multiple lives/seeds. (2) GYM CRITERIA — off
  the shelf, never invent our own gym for this: dense continuous verifiable
  score (not binary), high/unbounded ceiling (no early saturation), cheap
  verification relative to thinking cost, low stochasticity, composable
  optimization motifs (so cross-task abstraction is measurable). Project
  should be reproducible in ANY experiment space; only LoRA+sleeper specifics
  may need retuning. (3) TIME-AWARENESS — the agent must not be time-blind:
  inject a clock into the workspace, give it intuitions about timeframes;
  time-cost lives in the ledger so sleep can learn efficiency preferences
  (slow-correct vs fast-correct pairs). External reinforcement formalism NOT
  needed beyond the gym itself if the gym is good (kernel tests ARE the
  reinforcement). (4) NO CROSS-AGENT progress sharing in the experiment
  (breaks parallel separation) — but noted as the future population/promotion
  mechanism. (5) "SHOULDN'T DO WORSE" as a design requirement, not an
  assumption: the system sits on top of the existing agent loop (same files/
  RAG/skills/tools for both arms), so worst case should be adapter ≈ no-op —
  make this true BY CONSTRUCTION via support-gated sleep + adapter-off
  diagnostics + KL-to-base; v5 proved ungated sleep CAN make you worse, so
  below-baseline performance is itself a sleep-failure signal, measured not
  denied.
  whole project in one loop)**: nothing is learned into separate modules —
  no learned dreamer, no learned thinker; everything learned lands in the
  LoRA. THINK IS THE LOOP (and thinking includes daydreaming and night
  dreaming — same operation, different grounding); SLEEP IS WRITE (simple
  mechanisms: dedup, support-gating, shortcut materialization; with enough
  high-quality data the same writes eventually train the base model). Put
  the organism in a GYM — something very difficult, possibly deterministic
  (Rohin's candidate: BUILDING GPU KERNELS — verifiable speedups = dense
  ground truth, economically real, unbounded depth; cf. KernelBench,
  AlphaEvolve) — give it a BOOTSTRAP/BIRTH prompt carrying the emergent
  dispositions we don't build (judgment, pattern-seeking, self-evaluation:
  "judging itself is fundamentally part of what it should realize it needs
  to do"), and let it run. HOW IT LEARNS WELL (all emergent, never
  instructed): build small pillar thoughts UP until they uncover a THEORY,
  then build DOWN from the theory to action — puzzle pattern-matching is
  intelligence but not creativity; theory-mediated improvement is what
  changes thinking paradigms. (Note the closure: build-up-to-theory /
  build-down-to-action IS Einstein's E→J→A→deduction cycle from Zahavy's
  paper — the agent loop implements the diagram he says LLMs can't draw.)
  THE HARD PART = SLEEP INTELLIGENCE: the thinker only proposes; sleep
  determines whether "tomorrow you think a little better" — over thousands
  of outputs the flywheel's upward motion is set by write quality (v5
  measured exactly this: think all day, sleep badly, get dumber). Sleep
  need not be perfect — THE BAR: provably beat the identical agent loop
  WITHOUT LoRA consolidation. That one ablation (loop+sleep vs loop alone,
  same budget, improvement-vs-lifetime curves) is the minimal falsifiable
  headline. "In a way the project is a lot simpler now."
- **EXPERIENCE MODELS (Rohin 2026-09-04 — the project's emerging name/frame)**:
  the system is morphing into a named architecture class. World models learn
  an environment's dynamics; EXPERIENCE MODELS learn an agent's lived history
  and how to use it — worldview = compressed personal experience. Concretely:
  a frozen base model (language/world prior) + adapter learning experience
  into worldviews + surprise ledger + a SELF-DIRECTING TRANSFORMER LOOP whose
  input space is (own output + real-world state), with goals/state kept in
  the context window — some persisting in-window, some reinjected on a
  schedule (= Codex's WAKE cadence / working-memory management) — looping on
  itself with language and state around it. Contra Zahavy: you do NOT need
  physical world models for forward intelligence in language-native domains
  (code, math, research, agent tasks) — the LLM's latent space already
  contains that world's "physics"; what's missing is not sensory grounding
  but a LIFE (ledger + loop + consolidation). Zahavy himself concedes this
  boundary in his conclusion: for abstract domains "the nature of the
  simulation must be adapted to the ontology of the discipline... for
  mathematics, the abstract landscape of formal systems." His critique may
  still bind for physical-science invention — honest scope line for the
  paper. This does not change the project; it renames what it was already
  building: Dream-State Learning trains an experience model.
  TERMINOLOGY POSITIONING (Rohin 2026-09-04): not a ban on "memory" — memory
  remains a good reference term and component name. The point is we now have
  a better, MORE DESCRIPTIVE position than "memory" for what we seek:
  experience models. Lead with experience / worldview / ledger because
  "memory" is loaded with fundamentally different work (RAG stores,
  MemGPT/Mem0-class systems); keep "memory" available wherever it is the
  clearest reference.
- **Projection theory of intelligence (Rohin 2026-09-04, defending
  compression against Zahavy's "LLMs can't jump")**: intelligence = a learned
  PROJECTION loop. Experiences live high-dimensional (episodic store +
  weights); thinking projects them into a low-dimensional, serial,
  understandable workspace ("consciousness" — cf. Bengio's Consciousness
  Prior and Baars/Dehaene global workspace); successful projections are then
  REINFORCED back into the high-dimensional intuition where the memories
  live. That reinforcement of the projection is the loss; compression "just
  comes in different forms and shapes": predictive loss (induction),
  COHERENCE loss (Einstein — his error signal was internal: mechanics vs
  field theory, felt equivalence of acceleration/gravity vs their formal
  separation; Zahavy concedes the "conceptual inconsistency" himself in his
  own section 4), description-length loss (unification = MDL over theories,
  not data). Fundamental postulate: if your intuition plus observed knowledge
  is strong, you should be able to account for ALL your experiences — so any
  unaccounted experience, external OR simulated, is gradient. Domains differ
  in loss trustworthiness (mathematical intelligence = perfectly verifiable
  observables at one end; pure intuition-coherence at the other) — our game
  worlds deliberately sit at the verifiable end. Architecture mapping: think
  = project to workspace; sleep = reinforce the projection into the adapter
  (intuition); dreams = simulated experiences added to the compressed corpus
  — exactly the mechanism Zahavy says is missing. His non-Euclidean
  objection (search transiently increases complexity) is annealing under a
  compression objective, not a counterexample. See
  related_work/zahavy2026_llms_cant_jump.md for the full engagement.
  COMPLETION (Rohin 2026-09-04): THE ERROR LIVES IN EXPERIENCES. A frozen LLM
  has no self-error signal — not because its weights lack a worldview (they
  compress one from pretraining) but because it has no PERSONAL LEDGER of
  "I expected X, I observed Y." The moment you put an experience stream on a
  frozen base (base model = base intelligence; experiences = new
  intelligence), the coherence loss becomes computable per-memory: stored
  expectation-violation residuals ARE the gradient source, and they only
  exist for an agent with persistent self-history. Second half: the
  intelligence does not live in the weights alone — THINKING is the search
  that localizes the error ("which part of your system is wrong"): multiple
  searches over the belief graph to find the minimal revision that reconciles
  the residuals — credit assignment by deliberation instead of backprop. The
  transformer never changes; what changes is how the system thinks, uses what
  it knows, and brings new knowledge in. So intelligence lives in three
  places: weights (compressed prior), memory (surprise ledger), thinking
  (search that routes residuals into revisions) — the SYSTEM learns, not the
  substrate. Design consequences, both already germinating in the codebase:
  (1) dreams should be SCHEDULED BY SURPRISE — the stored contradictions
  (our blind-prediction 'contradicted' statuses are literally residuals)
  become the dream queue's priority signal (= biological prioritized replay);
  (2) sleep-thinking's job is credit assignment: walk provenance from a
  contradiction to the upstream belief that caused it, REVISE (the microdream
  contract's ADD/REVISE ops + self_check_drift condition are this mechanism,
  independently built by Codex). What v5 lacked and this names: contradictions
  were labeled and dropped, never traced to a culprit belief.
- **LoRA as the bootstrap for self-training on actions (Rohin 2026-09-02,
  the full-altitude vision)**: base models cannot train on their own action
  data today because raw agent trajectories are too noisy/incoherent to be
  worth pretraining on. The LoRA-loop system is the SHORT-TERM LEARNER that
  fixes this: deployed on a frozen base in a sandbox, it learns from its own
  actions within one lifetime (including a LEARNED exploration allowance,
  estimated from its own past rather than hand-set) until the agent shows
  sustained success — at which point that life's trajectories, now
  high-quality because the adapter made the agent competent, are PROMOTED
  into the base model's training set. Many sandboxes in parallel → the
  first generalized, high-quality dataset of acting (not just knowledge),
  with the value of exploration measurable at scale. "Let baby learn here,
  then train on what we've learned": adapter = individual learning, base
  update = species learning; eventually the base absorbs the capability.
  KEY UNIFICATION: the verified-write / sleeper-compile machinery is the
  quality gate that makes promotion possible — v5's poisoned-corpus collapse
  is the same failure law that kills naive self-training flywheels (contrast
  AlphaZero/STaR, which work because a filter guarantees promoted data);
  Paper 1's verification layer is the admission ticket to the whole pipeline.
  EXTENSION — training-rank cascade: multiple adapter levels at
  geometrically slower timescales, fast ranks learning quickly and feeding
  what persists upward to slower, more generalized ranks, terminating in
  base weights. Exact neuroscience anchor: Benna & Fusi 2016 synaptic
  cascade (chain of variables per synapse, fast feeds slow); ML echoes:
  fast-weight programmers, multi-timescale memory. Our memory+loop adapters
  are the depth-2 case, so the architecture generalizes without replacement.
  Measurable when scale allows: does promotion improve base ACTION competence
  (not just knowledge); learned vs fixed exploration coefficient; cascade vs
  two-tier consolidation. Paper-3-scale; goalposts for Paper 1 unchanged.
  TRIANGLE DESIGN (Rohin 2026-09-02): the cascade as a RANK PYRAMID — small
  fast adapter at the bottom (little data, quick updates), geometrically
  larger ranks upward, each trained on the ACCUMULATED verified data from the
  level below, until the top rank is large enough that merging into the base
  is natural. Design rule that resolves "the right LoRA size is not obvious":
  rank is a FUNCTION of accumulated verified data — each level needs
  proportionally more data to justify its parameters, so promotion from level
  k to k+1 triggers on data volume, not on a clock. Keep levels as SEPARATE
  adapters (composable via the proven read-only/clean-base protocol,
  independently ablatable), not a monolithic trailing structure. Two
  propagation mechanisms to compare: (a) DATA-MEDIATED — the higher rank
  trains on the filtered corpus/traces accumulated under the lower rank
  (verification gate applies at every promotion; cleaner, auditable);
  (b) WEIGHT-MEDIATED — LoRA deltas add, so periodically merge the fast
  adapter into the slow one (SVD re-truncate at the higher rank), reset the
  fast adapter, lightly decay the slow one's singular values (SHY downscaling
  in weight space) — merge-and-reset IS a sleep cycle in weight space.
  EXISTENCE PROOF at the endpoint: ReLoRA shows repeated low-rank merges
  into full weights approximate full-rank training — the top of the triangle
  is already demonstrated at pretraining scale. Near-term ladder (A40-sized):
  (1) rank sweep of the loop adapter under BC at 7B — prediction: agency is
  LOW-rank (steering, not knowledge); (2) depth-2 cascade (fast r~8 per-life
  → slow r~64 across lives, both mechanisms) vs single-adapter baseline,
  measuring retention + transfer; (3) promotion-to-base deferred.
- **One-system view: dreaming = the write mode of thinking (Rohin 2026-08-31)**:
  maybe dreamer and thinker are not two modules but one thinking system in two
  modes — online (grounded, acting/retrieving) and offline (ungrounded,
  writing). "Dreaming is just the write mechanism, TMEM-style." Node
  connections then form NOT by an explicit dreamer program but through
  traversal: while thinking you BFS/DFS across memories, and co-traversal
  itself creates/strengthens edges ("you connect to one connected thing and
  now it's connected") — Hebbian, use-weighted, matching the earlier MCTS
  intuition (similar memory reinforces + deepens rather than spawning new
  nodes). Under this view the dreamer is demoted to a memory garbage collector
  + write sequencer + replay scheduler (episodic triage, high-level
  scheduling), and content arrives at memory already partially connected
  because the thought-trace IS a path — write the traversed edges, not
  isolated facts. Corollary correction to the "loss policy" phrasing: what to
  lose is not an explicit decision; with the right parameterization,
  compression itself creates the intelligence (a flow of linear algebra), and
  the pink pig is generalization succeeding, not failing — exploiting priors
  for everything outside the focus of attention is the smart move under
  bandwidth limits. Refinement to keep both truths: SELECTION vs COMPRESSION —
  compression is emergent (SGD + parameterization + bottleneck), but selection
  of what gets replayed/trained-on is still a mechanism (brains do prioritized
  replay of surprising/rewarded traces), and v5's 2026-08-31 result (corpus
  0/12 true → think 1/30) was a selection failure, not a compression failure.
  Note the convergence: Codex's recurrent-microdream design (WAKE cadence,
  node reactivation, per-edge self-check inside one recurrent loop) is this
  same one-system view arrived at independently — see notes/42.
  CRYSTALLIZED (Rohin, same day): one resolver mechanism, two invocation
  contexts. THINK mode = goal-driven, read-mostly: builds logic chains and
  connections from memory keyed by the current goal; its traversal log writes
  cheap local edges as a side effect. DREAM mode = episode-driven,
  write-mostly: the SAME think machinery invoked at a higher episodic level
  with no external grounding, owning durable writes — TMEM-style, proposing
  MULTIPLE candidate writes per episode, each passing the local blind
  self-check before commit, with the write policy itself outcome-trainable in
  the outer loop (this is where medium-rate learning bites). The only
  differences between modes: input source (goal+world vs episodic buffer),
  output permissions (actions/answers vs durable writes), and grounding
  (external feedback vs none) — everything else (ops grammar, retrieval,
  scaffold, budget) identical, which makes mode a single clean ablation axis.
  Practical consequence: no bespoke dreamer program — the dream arm is the
  organism thinker with a WRITE op, episodes as input, and k-sample write
  proposals; v5's failure (single-gate writes, no thinker in the write path)
  is the ablation that motivates it.
  MATURATION (Rohin, same day, explicitly a discussion not gospel): rename and
  re-scope. THINKER absorbs the dreamer's current generative capabilities —
  it thinks, builds connections and viewpoints, and its episodes of thought
  are deliberately voluminous ("a lotta data is good": traces are raw material,
  and trace statistics — frequency, co-occurrence — carry signal). The
  consolidation layer becomes THE SLEEPER: it does not generate content, it
  COMPILES the thinker's output into strong writeable data — dedup (reinforce
  rather than duplicate), abstraction layers, and multiple organizations of
  the same memory under "different vibes" (entity-keyed, attribute-keyed,
  topic/temporal views — a principled generalization of the entity+color
  retrieval keys the gold-control excavation forced on us). Sleep-cycle
  mapping: SWS = the write/transfer pass (prioritized replay, commit verified
  atoms), REM/dreams = the reorganization pass (cross-links, schemas, novel
  associations), synaptic downscaling (Tononi/Cirelli homeostasis) = the
  garbage collector. Deferral ruling: the episodic-generalization half of
  dreaming is not yet rewarded by our game — build thinker-with-write first,
  sleeper as compile stage when the world rewards cross-episode schemas.
  NAMING/NOVELTY CAUTION: PEAM owns sleep-framing per the forbidden-claims
  list — "sleeper" naming is fine internally but the paper must cite PEAM and
  differentiate (our claims: one-mechanism think/dream, connection-through-
  traversal, weight-space consolidation, beyond-saturation lifetimes).
  NAMING RULING (Rohin 2026-08-31): SLEEP = the whole offline system,
  including the PEAM/TMEM-style write-to-LoRA layer; DREAMING = the thinking
  that happens during sleep. Keeps the existing dream structure and branding;
  the write layer is a component of sleep, not a rival of dreaming.
- **Shortcut materialization = the lifetime-scaling mechanism (2026-08-31)**:
  chains do not live in the adapter — the adapter stores 1-hop atoms and the
  thinker hops at read time (proven: five-rule stack, substrate 2x2; matches
  the literature that composing separately-learned facts in-weights fails
  without externalized hops — reversal curse, grokked-composition results).
  So writes take two forms: (1) atoms a→b, b→z (hoppable edges), and
  (2) MATERIALIZED SHORTCUTS — when the thinker's traversal statistics show a
  chain a→b→z is hot, sleep writes the composed 1-hop atom a→z with
  provenance ("via b"), lossy by design (intermediates dropped from the fast
  path, re-derivable from provenance). Repeated consistent statements of the
  same relation are what carve the gradient direction (measured-exposure law
  governs how many). Consequence: effective reasoning depth per FIXED think
  budget grows with lifetime — each sleep compresses yesterday's multi-hop
  derivations into tomorrow's single hops (the MCTS-depth-per-dream intuition,
  now mechanistic). This is the beyond-saturation hypothesis stated as a
  mechanism: retrieval systems keep chains external forever so think-cost
  grows with task depth; a consolidating agent amortizes depth into the
  substrate, so deeper tasks stay in budget as lifetimes grow. Which chains to
  materialize needs little new thinking at write time — the thinking already
  happened during wake; sleep compiles its statistics (dedupe + hot-path
  materialization + GC).
- **LoRA is not memory, it is learned reasoning (Rohin 2026-09-01, scope
  reframe)**: the evolution analogy for pretraining is backwards — humans
  start weak and learn their world; LLM agents are born omniscient-generalists
  and amnesiac-particulars (massive generalized knowledge, zero personal
  history). So the agent-memory problem is NOT the human episodic→semantic
  pipeline (the semantic layer already exists from pretraining); it is binding
  a particular LIFE to that knowledge. Three-tier restatement: context window
  = "what is in front of me" (strong, transient working memory); adapter =
  the middle tier we are building — learned agency: compiled reasoning,
  search control (when to go BFS vs DFS through options), shortcut chains,
  schemas; full continual pretraining = the slow permanent tier. Under this
  view the think/dream/sleep loop trains a REASONING POLICY, and stored facts
  are scaffolding for that training. This resolves the substrate-2x2 puzzle:
  LoRA-as-facts loses to context until memory >> window (measured), but
  LoRA-as-procedure has no context-window equivalent at any scale — trained
  dispositions from thousands of episodes cannot be carried as prompt text —
  so the value condition for LoRA-as-reasoning plausibly arrives much earlier.
  TESTABLE: train the loop adapter (BC on think traces, already-planned
  ladder) at small memory scale where fact-LoRA showed nothing, and look for
  gains. Convergence with prior art: EVAF's split (durable goal-conditioned
  tendencies in weights, shallow facts in retrieval) and PEAM (consolidates
  skills, not facts) both back procedure-in-weights/facts-in-text. Also
  reframes "memory before action": memory-as-learned-reasoning IS the
  prerequisite of action. Scope guard: Paper 1 goalposts stay frozen — this
  is intro-framing / paper-2 material, not a goalpost change.
  SUBSTRATE QUESTION (Rohin 2026-09-02): if LoRA is becoming AGENTIC POLICY,
  is LoRA-on-transformer the right thing to train? Ruling-in-progress: yes,
  for principled reasons — (1) our action space is language-native (ops
  grammar: MEMORY/THINK/WRITE/ANSWER are tokens), and a policy over token
  actions IS a language model, so tuning the LM is policy learning (RLHF/GRPO
  precedent); (2) low-rank is the right PRIOR, not a compromise: the base
  already contains the skills, and the policy delta should be a small steering
  field over existing capability — "the parameterization creates the
  intelligence"; (3) composability: keep the memory adapter and loop adapter
  SEPARATE (already in goalposts) so experience and agency stay auditable and
  swappable; (4) frozen base + KL-to-base guards against policy training
  degrading general intelligence. The hard part is NOT the substrate, it is
  the CREDIT SIGNAL — the BC → rejection-SFT → preference → GRPO ladder is the
  ramp, and v5 gives the first concrete target: train the write policy against
  whether downstream retrievals helped (TMEM-style outcome credit).
  NEW, TESTABLE — CO-ADAPTATION: "train this enough while training the
  intelligence and you intelligently learn how to use your agentic
  intelligence" = the loop policy must be periodically RETRAINED during sleep
  as memory grows, because it is a policy over a changing memory landscape.
  Predicted failure mode: frozen policy + growing memory → the agent gets
  WORSE at using its own expanding memory (retrieval precision decays with
  lifetime). If measured, this is a second saturation mechanism that pure
  memory systems cannot escape and our sleep loop can. Vocabulary that falls
  out: base = intelligence, context = situation, memory adapter = experience,
  loop adapter = agency.
  pink-frog/green-pig afterimage illusion as the paper's motivating image.
  Fixate elsewhere and perception runs on adapted priors: the brain keeps the
  old compressed structure ("pigs are pink") while the literal input changes —
  lossy, generalized memory being rendered live. The claim: compression is not
  a cost of memory, it is the mechanism of intelligence — reducing dimensions
  is what lets distant experiences blend and connect (exactly the Blendyland
  parent-blend structure), and the bottleneck (finite context window, finite
  information-transfer rate) is WHY abstraction emerges at all. Transformers
  already do this over pretraining data; Dream–LoRA–Think tries to do it over
  lived experience with orders of magnitude less data. Two sharpenings:
  (1) the intelligence is not the loss per se but the CHOICE of what to lose —
  structured loss keeps what predicts and discards what doesn't; v5's dream
  ladder (2026-08-31: recall 3/12 but supported-precision 0/5, retained truth
  0/12, think 1/30) is the illusion's dark side measured live — compression
  outpacing verification turns generalization into confabulation, the pink pig
  overriding the actual image. Compression quality = filter quality.
  (2) The architecture is complementary-learning-systems shaped: fast verbatim
  episodic store (our QA corpus / hippocampus) + slow generalizing store (LoRA
  / neocortex) + sleep replay (dreams) doing the transfer. Citations for the
  intro: McClelland/McNaughton/O'Reilly CLS 1995; Tishby information
  bottleneck; compression-as-intelligence lineage (Solomonoff, Hutter,
  Schmidhuber compression progress). LoRA's value condition (memory >> window)
  is this same statement: consolidation pays exactly when the bottleneck binds.
- **Capacity-compression phase diagram**: memory size is not monotonic
  intelligence. At fixed base model, sweep LoRA rank/effective capacity x
  dream compression while separately measuring (1) exact experiential-leaf
  recall, (2) withheld structural composition, and (3) novel multi-step action
  gain. Hypothesis to test, not assume: too little capacity drops evidence;
  excess capacity may preserve episode-specific detail without pressure toward
  reusable structure; an intermediate regime may best trade recall for
  constructive generalization. Then repeat selected points across base sizes
  to separate memory capacity from pretrained reasoning/prior quality. The
  target is latent intermediary action pathways, never recall alone.
- **Two-front paper comparison**: downward vs RAG, upward vs batch
  post-training on the same lifetime; **the flywheel**: better memories →
  better actions → better data (random-play lifetimes are redundant).
  Requires the direct-QA distillation (TMEM-style) baseline arm. [notes/32]
- **Three-phase factorization** (Rohin: "I didn't forget for no reason"):
  1 world-building (nearly done) → 2 experiential combination
  (Blendyland, current) → 3 ACTION construction (the Alchemy question).
  "Action needs Blendy": action intelligence = same compositional
  machinery unrolled through time. A0–A4 ladder; CAUSAL_RULE +
  ACTION_SCHEMA memory kinds; receding-horizon think loop. [notes/32]
- **Habitat world**: real features (night vision, swimming) × coherent
  habitat transformations, exact hidden fitness function; world-building
  as VALUE estimation; global priors across worlds + per-world deltas.
  [notes/32 playthrough rulings]
- **C3loop**: one recurrent machine, two regimes (thinker = goal-driven
  narrow; dreamer = surprise-driven broad); persistent state + agenda-as-
  while-loop; inspectable scheduler; recursive dependency-resolution
  reads; full trajectory logging as future amortization data. [notes/35]
- **Evaluator ladder**: ProofGate (now) → TrajectoryValueModel [SUPERSEDED NAMING: the outer component is an OUTCOME CRITIC + SCHEDULER (V/Q over states and operations, progress = dV - compute cost), never a thought-verifier — three-nested-loops architecture in notes/35] (learned
  sequence critic; 1999-research-snapshot pretraining; reality evaluates
  the evaluator via citations/stars/downloads) → OutcomeEvaluator.
  Slow-learning: sequence-level relative outcomes (GRPO-style) over
  logged dream trajectories. [notes/32, 35]
- **Dream language strata** (candyland spec): witnessed facts w/
  provenance; evidence-scaled generalizations; prior-contrast/surprise;
  named abstractions; connections. Two-lands provenance (candy vs dandy)
  forces situated reads. [notes/32 2026-08-25]
- **MoE / function-specific layers** for dream/think/verify modes — later
  scale mechanism, ad hoc if needed now, must be labeled. [Rohin+claude.ai]
- **Peeling ladder remainder**: answer-aware read plans → generic
  cognitive-loop prompts (no game nouns) → raw-stream extraction (drop
  tabulated evidence) → recurrent dreams-over-dreams → new worlds →
  amortized controller. [notes/35]
- **Prompt-ablation ladder**: minimal / generic loop / pattern repertoire
  / game-informed ceiling. [notes/35]
- **Controller parameterization ladder**: prompts (Paper 1, learnable-
  by-construction) -> discrete prompt optimization (DSPy/OPRO) -> mode
  adapters -> prefix/P-tuning (static mode bias) -> conditional prefix
  generator (the real "consciousness stream" — state-conditioned) ->
  learned operation policy. Vectors buy learnability, cost
  inspectability. [notes/35 2026-08-26]
- **Self-prompt legitimacy ruling**: process guidance is allowed because
  "the LLM could come up with these self-prompts anyway" — later, let the
  model WRITE its own next dream question (self-directed drift). [notes/32]

## DONE (proven, absorbed into the system)
- Nonce L0 closed at oracle ceiling, replicated ×3 worlds w/ variance
  (0.949/0.849±.06/0.872±.09); daydreaming + merge inference validated.
- Semantic World C0–C2: context-break real; CoT clears D2; transport
  proven (D2 0.92–1.0, 100% read fidelity); C1b prior-scaffold on D3.
- Gauge machinery: emitter recovers full coordinate system from correct
  claims (fit 1.000) — positions by class order, rotations propagated,
  palette order incl. reflections, label permutations.
- Self-check works oracle-free: precision 0.61→0.83, gauge 0.35→0.87 vs
  no-gate; conservative recall is the cost (recovering via connector
  re-checks + provisional queue).

## DEAD (superseded — do not re-litigate)
- Circle-geometry/deep-cipher worlds (IMO-puzzle grade, un-inducible).
- Naive fact-injection (v2.0/2.1 falsifier failed honestly; capacity was
  never the wall — write FORMAT was).
- In-loop FactorSolver as the headline condition (now the labeled ceiling).
- Enrichment × capacity 2×2 (answered by the G-series diagnosis).
- "LoRA memory is novel" as a headline claim (preempted: TMEM, New News,
  LoRA-as-Knowledge-Memory, Language Models Need Sleep — see notes/36).

## [OBSERVATION, 2026-09-07] In-context gain does not equal write transfer, at one round
Status: measured, n=4 cells (rule game, 40-eid exam, band SD 0.03–0.044). A parent's lesson raised the child's immediate next-episode score in 3/4 classrooms-sets (post−pre +0.047, +0.099, +0.062; one −0.073), yet the single write compiled from that round moved the held-out exam by −0.012, −0.058, −0.138, −0.042 (0/4 positive). Reading, held loosely: the loop learns in context faster than the sleep can commit it; one round of ~400 rows is below the dose at which a write carries a lesson across episodes. This is the quantitative face of the "you can't learn to think in 40 episodes" correction and of the plasticity-lifecycle idea (small early writes should be judged over a lineage, not a round). Falsifier: a 3-round PREV-chained lineage at the same exam whose round-3 ON−OFF is positive. Not a mechanism claim.

## [ALIVE, 2026-09-07] Parenting should target what is outside the model; games must be outside pretraining
Rohin: the process lessons the parent gives (predict first, define scope, consider alternatives) are already in CoT prompting and post-training. Observed in ledgers: the 14B parent's utterances are exactly this generic scientific-method advice, and the child's "restatements" are mostly episode-local observations, not lessons. What is genuinely outside the model and does end up in the adapter (absorption probe): the marker dialect, gym-specific procedural knowledge (which pass sequences work on which program families), the clock/stopping behaviour, and the agent's own surprise history. Implication for parenting content: teach the domain and the thought-forms that survive a write (short scoped NOTEs, calibrated numeric PREDICTs, RECALL queries that retrieve), not the scientific method. Implication for games: pick environments with hidden dynamics the model cannot have memorized — CompilerGym already qualifies; candidates to screen: procedurally generated rule/grid worlds rendered as text (BabyAI/Minigrid, Crafter), TextWorld-style generated quests, and agentic benchmark tasks with held-out instances. Falsifier for the generic-advice concern: a parent restricted to domain-specific lessons (no process talk) producing a larger write transfer than the process-only parent at equal dose.

## [RELATED WORK, 2026-09-07] Allen-Zhu & Li, "Physics of Language Models 3.1: Knowledge Storage and Extraction" (arXiv 2309.14316)
Finding: a fact seen once in one form during training is stored but not extractable; knowledge augmentation (paraphrases, permutations, multiple renderings of the same fact) at training time is what makes it retrievable at inference. Fine-tuning on facts without augmentation does not fix extractability. Maps directly onto our write: the write-swarm 2×2 measured that paraphrase and replay-mix enrichment removed the harm of plain-text writes (plain 0.466 vs +paraphrase 0.496), which is the same mechanism. It also predicts that "dreaming" as multi-form re-rendering of an experience before the write is not decoration but the condition for later recall, and argues against compiling a lesson once verbatim. Action: cite in the sleep/compile section; consider a paraphrase-count dose curve in the writer (1×, 3×, 6× renderings per row).

## [ALIVE, 2026-09-08] Parent the thinking pattern: ritual detection → prescribed richer template
Rohin: "if you see uninteresting thinking patterns, parent something better." Measured motivation: absorption's row-specific component falls from ~1.7 to ~0.6 nats across 8 sleeps while the base model's own NLL on the child's later text falls too — the child's thinking becomes templated (same recipe, flat PREDICT, near-identical NOTEs) and the write is starved. Mechanism (`parent_brief.py`): at each sleep the harness measures ritual across the last 32 episodes (modal first-ACT share, PREDICT SD/distinct count, consecutive-NOTE Jaccard, modal RECALL share; ritual = ≥2 flags). When flagged, the parent model is shown the metrics and four raw chunks and asked for an ≤8-line richer thinking pattern (process only, leak-scanned; never names actions/passes). The text is appended to the waking brief the child reads at the next wake and logged to the life's parent ledger. This is teaching on the thinker side (context), leaving the compiler dumb, consistent with the salience-placement ruling. Falsifier: parented gym lives (RP arm) vs R2 controls on (a) ritual metrics over life, (b) row-specific absorption per sleep, (c) paired ON−OFF probes. Expected first effect is on (a) and (b), not (c), within a few sleeps.
- [measured 2026-09-09] Ritual onset in the gym is consistent: episodes 160–224 (sleeps 5–7) in 8/9 control lives, persistent afterwards; the recipe locks from the first window (bootstrap-suggested), notes and recall queries converge later; predictions flatten last. The parent-the-pattern intervention therefore has a natural trigger window, and "development rounds" for the gym should be timed to it rather than every sleep.

## [ALIVE, 2026-09-09] Three ordinary sciences (Rohin) and the storage–extraction gap in our numbers
Rohin: nothing fundamentally special is happening — the lived ledger is a dataset, the LoRA write is post-training, sleep compilation is dataset curation, and parenting decides whether the dataset contains increasingly useful cognition (exploration, self-reflection as growth motivations). Base intelligence flows through the experience adapter; early on the experience is thin, so the rank change must be strong enough to alter behaviour, especially while plasticity is high. Our measurements already show the Allen-Zhu storage-vs-extraction gap: the adapter stores ~3 nats of its own rows (storage) but moves behaviour by ~+0.02 (extraction through generation). The write-swarm result (plain harmful, paraphrase+replay neutral/positive) is the paper's augmentation condition. Open controlled cell (dose-splitting): same corpus, (i) one write, (ii) k sequential cumulative writes with no play, (iii) the real life with play between writes — separates frequency from data–weight co-evolution.

## [ALIVE, 2026-09-09] Multi-path dreaming (Codex, endorsed by Rohin: "very smart, I like that finding")
Codex's reading of Allen-Zhu & Li against our setup: low training loss can mean the weights reproduce the experience while the lesson stays inaccessible from a different future cue. Therefore the sleep compiler cannot merely summarize and paraphrase; it must train the child to encounter, reinterpret, and use the same grounded lesson through several native thought/action paths. Concrete build: for each admitted lesson, render k native continuations that reach it by different cues — PREDICT-first (the lesson as the reason for a prediction), NOTE-first (the lesson as a contrast with a named earlier case), RECALL-triggered (the lesson as the answer to a specific similar-situation query), and deviation-experiment (the lesson as the belief a surprise overturned) — all in the stored prompt render's dialect. Measurement: dose curve of renderings-per-lesson (1×, 3×, 6×) on fixed corpora, scored by paired probes (extraction), not NLL (storage). Ties to the parent-the-pattern brief: the same four cue paths are what the parent prescribes to the thinker, so the compiler and the parent teach the same shapes from two sides.

## [OBSERVATION, 2026-09-09] Behavioural collapse with perfect format; the gate must judge scores and behaviour, not dialect
Late-life recount of 9 fixed-writer lives (82 paired probes): 69/82 positive, 9/82 harmful, all after episode 384, in 3 lives — and every harmful sleep passed the format canary. Two shapes: (a) "act once and stop" (seed5: 1–2 chunks/episode under the adapter vs 13 for base, parseable-ACT 1.00, score −0.186); (b) a degraded adapter admitted at canary 0.67 after which all later writes fail the canary, freezing the life on the bad adapter (seed2). Lesson: the write's interface-preservation and its usefulness are different axes; a format gate protects the loop's syntax, not its behaviour. The commit rule must be a paired score test against both base and the previous adapter (the PREV rule, now for lives too), plus a behavioural canary (episode length ratio), plus a recovery path. Connects to the plasticity-lifecycle idea: harm appears at sleeps 12–20, after ritual onset (sleeps 5–7) — the templated corpus is what the late writes are made of.
- [measured 2026-09-10] Parenting the thinking pattern via the waking brief delays ritual onset (3/3 lives: 256–288 vs 160–224) and produced one 4-window remission, but ritual returns and persists under repeated briefs. The write re-imposes the template each sleep; a context-only lesson lasts ~2 sleeps. Candidate mechanisms to test: (a) the brief becomes a sleep stratum (the parent's lesson rendered in the child's dialect through several cue paths — multi-path dreaming of the lesson); (b) the compiler down-weights templated rows (ritual-aware corpus selection) so the write stops re-teaching the ritual; (c) the gate rejects writes that raise the ritual metrics. (b)+(c) keep the compiler dumb-but-selective; (a) crosses the thinker/compiler line and needs Rohin's ruling.

## [RULED, 2026-09-10] Repetition is the parenting mechanism; the parent stays on the thinker side
Rohin, on the finding that briefs delay ritual but do not hold: do not put the parent's lesson into the sleep corpus ("that ruins the whole point; this isn't post-training"). Instead, repetition: the parent repeats the same lesson consistently, and the child should learn that it too must repeat — rehearse the lesson in its own words at the start of each episode — so the lesson becomes part of the child's own thoughts, which is what normal sleep writes. Implementation: (1) the latest brief is shown at every wake, not only after a flagged sleep; (2) the parent is given its previous brief and asked to keep the same core lesson (sharpen, do not switch), and to say whether the child has started rehearsing it; (3) every brief ends by asking the child to restate the lesson as its first NOTE of each episode until it becomes how it thinks. Falsifier: rehearsal rows appear in the child's own ledger within 1–2 sleeps and ritual windows become rarer than in the controls over the following 4+ windows.

## [ALIVE, 2026-09-10] Bootstrap post-training so the child absorbs parenting better (Rohin)
Rohin: post-train the LoRA on an initial corpus as a bootstrap, then parent, then let it learn — the child arrives attuned to respond to parenting. Needs strong controls and a decision on what the bootstrap corpus contains (candidates: exemplary non-ritual episodes from the least-ritual control life, rehearsal-shaped NOTEs, contrast notes and reasoned predictions in the child's dialect — all from lived ledgers, none from the parent). Not post-training the task; post-training the receptivity. Adds complexity; may be the missing piece if parenting alone is asking too much. Protocol owner: Codex. Design before Sep-11 freeze is not required (it is a new arm, forkable).

## [DIAGNOSIS, 2026-09-10] Are the children receptive? The write is an amplifier of habit, not a weak write
Evidence: (1) the adapter reproduces its own rows strongly (its past text becomes ~20× likelier) yet moves behaviour ~2 points — strong storage, small change; (2) when the corpus contains something different (a parented round-0 classroom write) behaviour moves 10–17 points, and a 12k-row one-shot moves it a lot in the wrong direction — so the base IS receptive and rank is not the bottleneck (r8 ≈ r16); (3) retention is flat — nothing is forgotten; what happens late in life is that each sleep writes the child's most frequent recent behaviour back into it, and the cumulative corpus is numerically dominated by old habit rows plus replay of them; (4) lessons work in context (immediate gains; a 4-window remission) and vanish within ~2 sleeps because the child's own thoughts during those episodes still mostly contain the old template. Conclusion: the child is receptive; the sleep is a frequency amplifier. A lesson survives a sleep only if it has become the child's own frequent behaviour before the write (rehearsal), or if the compiler stops amplifying repeats. Levers that keep the compiler dumb/organizational: near-duplicate collapse in the corpus (count-based dedup of templated rows), recency over cumulative replay, and rejecting writes that raise ritual metrics. Rohin's bootstrap stage fits: it gives the amplifier better initial material.

## [RULED, 2026-09-10] No end token: continual thinking, stop = pull the plug
Rohin: the child should never emit a terminal DONE; if there is nothing to do it keeps thinking. The stream is continual; the harness changes the situation under it (new program, new classroom, sleep) and stopping is external. Implication for v7: remove DONE from the markers; episode boundaries become injected [SITUATION] events; the CLOCK stays as information, not as a terminator; sleep is a harness event. Cost: idle thinking tokens (token-sufficient regime, acceptable). Benefit: the reflective/idle thought becomes experience too (the "nothing to do" state is where self-reflection lives). Proposed as the first post-freeze mechanism change (v7), not before Sep 11.

## [FRAMING, 2026-09-10] Inner loop / outer loop
Rohin: the transformer is the inner loop (token by token) and the organism is the outer loop (output by output); the loop system is the same structure one level up. In that picture the ledger is the outer residual stream (everything written stays available), the waking brief and NOTEs are the outer attention over it, the world's outcome (admission) is the outer error signal, and sleep is the outer weight update — a LoRA step made from the outer stream. What we are asking is whether the outer loop's update can install new outer-loop behaviour (agentic CoT) the way pretraining installed inner-loop behaviour. Evidence so far: the loop's SHAPE is internalized (format/dialect component ≈ 1.95 nats, adapter alone reproduces the marker loop with no brief); the loop's QUALITY (exploration, contrast, reasoned prediction) is not yet — it is what parenting and the bootstrap stage target.

## [DESIGN, 2026-09-10] What the bootstrap post-training corpus should contain
Goal: receptivity, not task skill. Candidate strata, all from lived ledgers in the child's dialect, none from the parent verbatim: (1) rehearsal-shaped episodes — first NOTE restates current guidance in the child's own words, then acts on it; (2) reasoned predictions — a named feature of the program, a reason, a range; (3) contrast NOTEs — this case vs a specific earlier case, with scope; (4) specific RECALL queries and the retrieved memory being used; (5) deviation experiments — one change, predicted effect, surprise named as a wrong belief; (6) classroom pre→post pairs where the world admitted the lesson (the child's restatement plus the improved episode — the child's own words responding to teaching). Source lives: the least-ritual control (seed3) and admitted classroom pairs. Controls (Rohin: "strong controls"): bootstrap-only, bootstrap+parent, parent-only, neither; matched seeds; readouts = ritual onset window, rehearsal rate, row-specific absorption per sleep, paired probes. Failure to avoid: the bootstrap becoming a new template (measure ritual on the bootstrap corpus itself before using it).

# ── Rohin's high-level directions, 2026-09-10 (formalized by Fable; joint pass with Codex requested before protocol) ──

## [DIRECTION] Evaluate teaching at two horizons
Short-term = the immediate effect of a lesson (next-episode post−pre in the classroom; next-window ritual/rehearsal metrics in the gym). Long-term = whole-life outcomes (paired probes at every 64 episodes, end-of-life, late-life harm). A lesson that helps now and hurts later, or vice versa, is judged on both; the parent ledger gets both columns per intervention. Current evidence: short-term effects are common (5/8 classroom sets, 4-window remission), long-term effects are where the arms separate (parented 0/3 harmful full lives vs 3/9 controls).

## [DIRECTION] Scale thinking, not only teaching
Rohin: let the learning child think excessively and continuously, with as many parallel pathways of thought as possible; more pathways → a larger search space for conclusions and breakthroughs. Formalization: (a) per-situation parallel thought — k independent streams on the same program from the same context, each with PREDICT/ACT/NOTE, merged by the child itself (it reads the k branches and writes one NOTE); (b) longer budgets per situation (token-sufficient regime: budget-ticks is a tool of measurement, not a constraint); (c) continual thinking with no DONE (idle thought = reflection, becomes experience). Measurement: does k>1 change ritual onset, row-specific absorption per sleep, and the paired probes? Build trigger: after the Sep-11 freeze, as the v7 mechanism change (fork the child, per the continuity rule).

## [RULE] Child continuity: change the child only for mechanism changes
Rohin: if mechanisms are unchanged, keep the same child across teaching sessions (parenting and game changes do not need a new child); fork or restart only for fundamental mechanism changes, and do not be afraid of those (not the final child yet). Operational: finished lives (1024 episodes) are not endpoints — extend them into the next teaching session; every experiment record names the child it ran on; a mechanism change = new lineage root.

## [DIRECTION] What is already pretrained vs what we teach
The base model already has chain-of-thought and knows how to change its mind in context (measured: the adapter alone reproduces the loop; in-context lessons take immediately). We do not teach CoT from scratch. We teach: think MORE and more persistently; ponder different routes; meta-think about its own experiences; self-evaluate from outside itself (3rd/4th/5th-person views of its own behaviour); bring its own perspectives together across situations. Target statement: "CoT and metacognition, learned from its own experience, until it understands that the more it thinks through its experiences the better it will think in the future."

## [IDEA, Rohin: important] Personal conversations → opinions
The parent also asks the child high-dimensional questions ("what do you think about this parenting? about this project? about how you have been thinking?"). The child's answers are its own thoughts (thinker side; they enter the ledger like any thought and are written by normal sleep). Hypothesis: constant thinking about its own thoughts, with high-dimensional feedback, develops "opinions" — stable perspectives that generalize across situations — and this is where metacognition becomes weights. Measurement: consistency of the child's answers to the same question across sleeps (does an opinion form and persist?), and whether opinion-holding children ritualize less. Build: a conversation phase at wake (parent question → child answer → parent reply, 2–3 turns, leak-scanned), logged as kind="conversation". Trigger: after freeze, on RP/R4 children.

## [DIRECTION] Learn from human developmental pedagogy
Rohin: consult how human youth are taught to think (developmental psychology, metacognitive training, scaffolding/fading, self-explanation, reciprocal teaching, growth of working-memory chunks with expertise). Map each to a parenting method in PARENTING_MENU with its human evidence and a gym falsifier. Owner: Codex (science), with Fable implementing the winners.

## [IDEA] Chunk-density metric (from Rohin's compaction thread) — first measurement is ambiguous
Prediction: as memory improves the dreamed corpus gets denser (fewer tokens per episode covered). Measured on finished lives (new corpus rows per 32-episode sleep, chars per row): seed2 127→30 rows, 314→791 chars; RP400 134→33, 308→949; RP401 115→5–35, 310→815. Fewer rows are admitted per sleep and each is longer — not a clean density decline; consistent with fewer novel thoughts being admitted (ritual) and longer templated rows. Keep logging; interpret only alongside the ritual metrics.

## [FRAMING] Three points on one axis (related work)
Looped transformer = recurrence in activations (high bandwidth, uninspectable, one forward pass). Chain of thought = recurrence in tokens (inspectable, lasts a session). Experience models = recurrence in weights (expensive to write, lasts indefinitely, inspectable because we dream in text). Same question at three scales: where does the loop's state live and how long does it survive. Inspectability here is a design choice (dreaming in text, not KV).

## [PRINCIPLE] Unverifiable mechanism, verifiable falsifier
Every claim about teaching/dreaming traces to an exact number on the world side (gym scores, sealed probes), even though the mechanism is fuzzy. Do not hill-climb on the mechanism's own metrics (NLL) — the storage–extraction gap showed why. Transfer gym caveat: kernels/KernelBench are in pretraining; use held-out or randomized targets.

## [CHECKLIST] Post-training tricks for the writer (status)
Paraphrase diversity ✓ measured (plain 0.466 → +para 0.496); replay mixing ✓ measured; loss masking ✓ (response-only, v2.1); epochs 2 ✓; spacing free ✓ (cumulative re-exposure); rejection sampling ≈ world admission ✓ (classroom) / success-filter ✓ (compile_native); deduplication ✗ NOT yet — and the sleep-as-amplifier diagnosis says near-duplicate collapse is the next lever (organizational, keeps the compiler dumb). Compaction: keep sliding window + good memory; smarter eviction (SnapKV-style observation window, H2O) logged with trigger "only if window pressure shows in a 7-day life".

# ── Rohin, 2026-09-10 (second set): contamination, the three-stage pipeline, state-to-state reasoning, the jumpstart ──

## [RULE] Contamination between play and parenting
Once a child has learned from gym play, any later parenting evaluation on that child is contaminated by that learning; a parenting method must be judged on children whose only difference is the parenting. Protocol: (a) parenting-method comparisons run on clean children (saved babies, never gym-exposed) or on matched forks of the same longitudinal child at the same point; (b) every child carries a provenance record (which sessions, which gyms, which parents, which mechanism version) and every result names it; (c) the from-scratch test tracks all of it. This does not forbid the continual design (parenting and play interleaved in one life) — it forbids using such a child to compare parenting methods.

## [PIPELINE] Pretrain the adapter → parent → continual learning (Rohin)
Stage 1, adapter pretraining ("post-training the LoRA", the jumpstart): amortize the thinking STRUCTURE and some metacognition into the adapter before the child exists, so it is attuned to learning and parenting is not teaching from scratch. Stage 2, parenting: teach the child to use its new outer-layer systems (rehearsal, contrast, routes, self-evaluation) on situations. Stage 3, continual learning during parenting and during long-horizon gym sessions; the horizon must be right (long enough for lessons to become habits; short enough to measure). Then test at a scale that can show usefulness. Rohin: "is Stage 1 too hard? we should talk." Fable's assessment (2026-09-10): mechanically it is the same trainer we already run; the hard part is the corpus, because whatever structure it contains becomes the child's habit (the amplifier). Bootstrap v1 proposal: render existing lived ledgers (from the least-ritual control and the admitted classroom pairs) into the target state-structure below, in the child's dialect, with multi-path renderings per lesson; measure the ritual metrics ON THE CORPUS before training; train once from base; hand the adapter to Stage 2. Controls: none / bootstrap-only / parent-only / both, matched seeds, two-horizon readouts.

## [TARGET] State-to-state reasoning — what we are literally training (Rohin)
The model already reasons token to token. We train reasoning from one STATE to the next. A state is: take the context of the last state, PLAN, then EXECUTE token by token until a self-determined end of the current state (as agents already decide when to stop), then META-REVIEW: how did I evaluate this, where did I go wrong, what could I have done better, what did I do well (given good feedback), what will I do next time, what generalizes. The review is remembered (NOTE → ledger → write) so it conditions the next state: at the next state the child first recalls what it had, its conclusion, the new information, re-evaluates, formalizes, then acts under that state. Rohin wants to SEE strong self-reflective, meta-reasoning text from the child; that is the deliverable, not a score. Harness mapping (v7): explicit state boundaries in the stream ([STATE k] plan / execute / review) with the review as the first thing written into the next state's context; ritual/rehearsal metrics computed per state; the parent's questions target the review. The complexity is massive — hence the jumpstart.

## [PHILOSOPHY] When to scale
Once a mechanism shows a semblance of working (the write changes behaviour; the change is aligned even if not great), scale it — more thoughts, more episodes, more children, longer horizons — and see whether downstream moves. "Aligned but not great" is the signal to scale and improve the sections, not to redesign. Always think in parameters and scale. Scope now: prove the system works at all; the parented-from-scratch, billions-of-thoughts, deployed-to-many-people version is the superintelligence-scale ideal and is documented, not attempted.

# ── Rohin, 2026-09-10 (third set) ──

## [DIRECTION] Branching thought: remembered states, divergence, and convergence at sleep
States are remembered like chain-of-thought. One child may diverge into two or more chains, pursue them, and return to the first; if chains reach very different results they keep growing; sleep converges them (the compile sees all branches; the write carries what survived). Search policy learned, not fixed: most-likely branch first, then decide how many more branches are worth it under a hard token cap — never unlimited search. This is the DEPTH/RICHNESS parallelism. Harness sketch (v7): a [BRANCH] marker forks the current state's context into k streams (seeded), each continues until its self-determined state end, then a [JOIN] state in which the child reads the branch reviews and writes one plan; the ledger records the tree (state_id, parent_state, branch_id) so sleep can compile across branches. Metrics: branches per state, divergence of branch outcomes, and whether joined plans outscore single-chain plans at equal tokens.

## [DIRECTION] Head-node parenting parallelism (speed)
The same child runs in many classrooms at once; a head node (the "principal") keeps track of all of that child's concurrent lives, and the corpus merge at sleep brings them together (the classroom-round machinery already does the merge). This is the SPEED parallelism for parenting, distinct from branching thought. The principal is the parent's ledger/playbook across classrooms — already partly built (parent ledger, bounded playbook); what is missing is one playbook per child across its concurrent classrooms and per-life provenance.

## [DESIGN] Plasticity levels
Fast learning early; once the adapter has learned good things (sustained paired gain), learn a tad slower so it does not unlearn — not a lot; the system stays young. Proposed schedule (Fable's call, paper-worthy): lr multiplier m = 1.0 while the latest ON−OFF gain < +0.03; m = 0.7 once gain ≥ +0.03 has held for two consecutive probes; never below 0.5; reset to 1.0 on a mechanism fork. Alternative: scale by committed sleeps. Test as an arm (R5) against R4 once R4 has two full lives. Paper: "plasticity decreases with demonstrated competence, not with age".

## [DIRECTION] More thinking with no excuse to stop; coach the idea route
Better thoughts have not appeared because the child has not been given time to think. Let it keep thinking with no terminal token while different reinforcements arrive, so it must produce ideas between them. Coach the idea route explicitly: be okay guessing when information is missing, follow estimated paths, and be deliberate about everything. Pretraining some of this into the adapter avoids being asymptoted by the base model's own proclivity for change.

## [REFINED, 2026-09-10] Bootstrap corpus v2: structure-heavy, lived-light (Rohin)
Rohin's correction to v1: replaying lived episodes is "memorizing unlived memories" — little value. The corpus should mostly carry the thinking/absorbing STRUCTURE: flows in which the agent asks and answers its own meta-questions (how much more do I think, how much more do I plan, what do I execute now, what am I unsure of, do I stop and reflect) and the step sequence (plan → decide how much to think → execute a step → judge it → continue or stop → review). It connects token-level reasoning to state-level ideas so that when the agent is told to reflect it has known flows and extractable answers. Composition v2 (mixture): META-FLOW renderings ~40% (the conscious stream over the child's real context), REVIEW-only ~15%, OPENING (recall + plan) ~20%, CONTRAST ~15%, full lived episodes ~10%. The v1 corpus (lived-heavy) becomes the natural control: bootstrap-lived vs bootstrap-structure vs none. Plasticity experiments deferred until a child has gone "0 to 6 months". Success criterion for the bootstrap: a bootstrapped child, in its first 64 episodes with no parent, produces review/plan text unprompted (measured by the rehearsal/review detectors) and reaches ritual onset later than controls.

## [PURPOSE, Rohin 2026-09-11] Give it rules so it can make its own rules
The write installs habits well because the model does not yet think enough to create its own rules inside its thinking space. The bootstrap therefore installs the rules of reflecting (plan, judge, review, ask how much to think) so that the child can then create its own rules from experience — metacognition to create a learning agency. Stopping rule = "current task done", after which the agent moves to the next task or ponders in white space until it finds its own viable goal; it is constantly deciding goals, their starts and ends, and subtasks. Much of this loop logic exists in multi-agent frameworks and should be extracted, not reinvented; what is new here is the self-reflection and the system that absorbs it so the layers stay liquid and growable. (Timing phrases like "0 to 6 months" are vibes, not constraints.)

## [MECHANISM SENTENCE, Codex 2026-09-11] 
Bootstrap teaches the habit of making and revising rules; parenting teaches when to use that habit; lived outcomes supply the evidence; sleep makes the child's own successful use persistent. Corollary (Codex): a bootstrap built from a child that played the deployment task teaches task exposure before birth — the clean baby's bootstrap must come from a target-blind schooling source (rule-game classrooms, curriculum readings).

## [OBSERVATION, 2026-09-10] Quantized gym scores: the write's measurable gain is recipe lock-in
Adapter-ON probe means repeat exactly across lives (0.4878; 0.5291) because a fixed pass sequence yields a fixed instruction count on the 8 sealed programs, while the exploring base varies. So on CompilerGym the adapter's "learning" is the installation of one good recipe — the numeric face of ritual. Consequences: (1) the paper must say this plainly; (2) the gain ceiling on this gym is the best single recipe, which caps what parenting can show here; (3) the transfer/final gym must reward situation-dependent choices (per-program pass selection) or the thinking we want cannot register as score; (4) probe variance is recipe-choice variance, not sampling noise — gate decisions need confirmation at the next probe (provisional commit) rather than a single 8-episode sample.

## [FRAMING, Rohin 2026-09-10] TMEM is the proof; we expand the paradigm. Three timescales and the killer metric
TMEM (Ren et al. 2026) proved LoRA fast weights can hold an agent's experience within an episode; it is the shoulder this paper stands on and must be named on page 1 with the delta stated (see related_work/tmem_positioning_2026-09-10.md). What is ours: the lifetime timescale, the gated offline write, the failure study (late-life collapse, recipe lock-in), and the developmental question. Framing: three timescales — parent-guided development → autonomous metacognitive learning → task execution. The learner's loop is experience → metacognition → hypothesis → active exploration → evaluation → parameter update, and the metacognition itself improves over development; the parent is an outer-loop agent shaping another agent's development (scaffolding faded, absent at deployment). Killer result (not this paper): a developed agent A_D shows a higher rate of improvement per unit of experience than the baseline A_0 on task distributions the parent never showed — "did it acquire a better learning algorithm", not "did the classroom pretrain it". Rohin's implementation reading: parenting (human and agentic; agentic is easier to verify than to do) induces reflection, metacognition and recurrent plan–execute thinking; the model must first be taught by force (pretrained adapter) to constantly self-evaluate and think down different streams, building a conscious experience graph of thoughts; it must evaluate its meta-strategies (how am I thinking, enough, efficiently, asking vs doing); emergent emotional reactions in language (remorse under harsh parenting, the opposite under positive) become its own judge; parametric memory absorbs the thought-out experience and writes it back well enough to change actions and patterns; plasticity and temperature govern how much it learns from data and how much novelty it seeks. Scaled read/write: fewer reads, far more thinking per cycle, so each cycle changes behaviour and diversifies search. Endgame: thoughts saturate the LoRA → post-train the base. Steal from TMEM: SVD-based LoRA subspace initialization (trigger: when sleep write cost becomes the bottleneck). Nine-day reality: scope to a measurable form of self-cognition; long-horizon improvement is the ideal measure, downstream task improvement the practical one.

## [SCOPING, 2026-09-10] Efficiency over cycles, marker counts, and the behaviour-change gate — mapped onto what already runs
Forwarded scoping (endorsed by Rohin): headline = steps-/tokens-to-solve on a fixed task family across consolidation cycles (first derivative, cheap); mechanism check = metacognitive marker counts per episode, taught vs untaught; day-one gate = the action distribution must change between cycles; parallelize across students, serial within one; cut the valence knob from the main axis and long-horizon improvement from the headline; the abstract needs a named falsifier (cycle N, metric, margin X, K seeds); always state the comparison arm and task family.
How it maps onto the running system (little changes): a consolidation cycle = one sleep (every 32 episodes); the fixed task family = CompilerGym pass ordering on the by-identifier probe panel plus disjoint panel v1 (and the rule game as the classroom); students = lives (9 untaught ungated R2, 6 untaught gated R3, 3 taught RP, 7 taught+gated R4, run 8 per node); steps-to-solve = chunks-to-best-score per episode (already in the ledgers; the brevity gate measures chunks/episode), tokens-to-solve = chars per episode; markers = self-evaluation phrases, contrast/scope phrases, strategy switches (distinct ACTs), backtracks after non-improving outcomes, recalls, notes (ritual_metrics already measures recipe share, note templating, recall repetition); the behaviour-change gate = Jensen–Shannon shift of the first-ACT distribution between consecutive cycles (ritual = shift → 0; the recipe lock IS the distribution going flat). New instrument: `organism_v6/efficiency_markers.py` computes all three per life per cycle from disk. Comparison arm: same-writer untaught lives (R2 vs RP; R3 vs R4), matched exposure, plus adapter-OFF. Candidate falsifier for the abstract (to be filled from the instrument's numbers, not before): "by cycle 16 (episode 512), taught lives' mean chunks-to-best on the probe panel is below untaught lives' by ≥ X% across ≥ 3 seeds; otherwise the abstract carries no parenting-efficiency sentence." Valence (harsh/positive) is not a knob we run; long-horizon improvement is not the headline.

## [RULED, 2026-09-10] The gym is the world; the benchmark is the protocol inside it; always a baseline agent
Rohin: keep the gym regardless; "our own benchmark" = tracking within the gym; always have a baseline agent for comparison, so first derivatives (per-cycle improvement) and second derivatives (rate of improvement on novel tasks, developed agent vs baseline) can both be compared. Baselines: adapter-OFF frozen model (have); equally-capable text-memory agent = frozen model + the life's own brief/notes, no weight change (missing; review M4; ~5–10 GPU-h as a brief-only proxy); regular agent for the finals 2×2. Remaining mechanism work, in order: provisional commits confirmed at the next probe; near-duplicate collapse in the sleep corpus; fading parental scaffolding; v7 stream (no DONE, states, branching); fail-closed provenance guard for bootstraps.

## [DIRECTION, Rohin 2026-09-10] Scale as one child, many clones: width × depth, merged at sleep, tested by an evaluator classroom
Rohin's scaling picture: (1) a pretrained instruction adapter kick-starts heavy self-thought and reaction; (2) large-scale parenting in many environments that instil environment- and world-related thoughts and actions; each environment runs many episodes over many cycles (width = environments/clones, depth = cycles); (3) multi-agent consolidation — at sleep, all clones' experience merges into ONE child's adapter and the clones resume from it (this could happen every run); (4) intermittent testing by an evaluator agent / a test-only classroom that measures how learning has progressed, tests living in environments; (5) a long-horizon learning agent deployed in the test gym that sleeps on the pooled experience plus its own. Status: NOT what the gym lives do today — each life is an independent student with its own adapter; the one-child-many-classrooms merge exists only in the rule-game classroom rounds (pooled corpus with provenance → one write). Build needed: N clones sharing one adapter directory with a sleep barrier; compile over all clones' ledgers with per-source provenance; one write; clones resume from it. Cost note: the test agent's own experience is small relative to the pooled corpus, so merging it does not double training. FUTURE (not this system): compare parenting styles at scale (different parents, curricula, valence) — future-work section only.

## [RULED-PENDING, Rohin 2026-09-10] Can the test gym be one of the environments? Split hygiene answers it
Two different things: (a) continual learning ON the test gym after deployment is the thing we measure (the finals: learning curves on held-out instances, first and second derivatives) — allowed, it is the point; (b) contamination = exposure to the held-out test instances/programs before the test, a parent that knows test answers, or a bootstrap that contains the test gym. So: the gym's TRAINING split may be one parenting environment; the test is the held-out split (disjoint panel, held out by source not just identifier), the parent must be target-blind on it, the bootstrap must not contain the gym, and the merged sleep must carry per-source provenance so "did the test-gym clone's experience carry the gain" can be ablated. This is Codex's contamination rule applied to the scaled design; Codex to ratify.

## [RULED, Rohin 2026-09-10] Thoughts carry the gain; scale thinking streams; teach recurrent CoT
Per-source attribution of a merged gain is not needed — the thoughts carry the gain. What must scale is thinking: many thinking streams per task (the branching/depth parallelism), and the model should be taught recurrent chain-of-thought — reasoning that returns to and revises its own earlier reasoning across states — because metacognition requires it. This is the core of the next experiment (v7 stream: no end token, explicit states, k parallel streams merged by the child, review-shaped states; bootstrap to install the habit). Finalize its design once the abstract and the current arms' outcomes are in.

## [DIRECTION, Rohin 2026-09-10] Classrooms are gyms; the trait to instil is persistence
All environments are gyms, the classrooms included. They must instil persistence — the agent keeps working a hard problem through many attempts, failures and re-plans instead of stopping early — in the spirit of OpenAI's exploit gym (long, adversarial tasks where giving up is the default failure). Why it fits our data: the write's characteristic failure is the opposite (behavioural collapse to 1–2 turns per program, caught by the brevity gate), and ritual is a form of giving up on search. Measurements that already exist or are cheap: turns per program and chunks-to-best (efficiency instrument), attempts after a non-improving outcome (backtracks), episodes ended by DONE vs by budget, and time-to-abandon on deliberately hard programs. Gym design for persistence: tasks whose payoff arrives only after many attempts (hard programs where the recipe fails and per-program search is required; multi-step rules in the rule game; explicit "no progress yet, keep going" phases), scored on eventual success and on continued effort, not on early quitting. Parenting for persistence: the parent rewards continued, changing attempts, never early stopping; the bootstrap installs the habit of re-planning after failure. Ties to no-DONE (v7) and to recurrent CoT (return to and revise earlier reasoning).

## [DEFINITION, Rohin 2026-09-10] Parenting = gyms that teach traits and give environmental feedback to induce self-learning
Parenting is not primarily a talking parent. It is a curriculum of gyms, each built to instil a trait (persistence, reflection, exploration, self-evaluation, re-planning after failure) and to return environmental feedback that makes the child learn on its own; the parent model is one feedback channel inside those gyms (process critique, pattern briefs), the world's outcomes are the other, and the child's own reactions to those outcomes are what sleep writes. Paper wording: "parenting: a curriculum of trait-teaching environments with a critic that never gives answers." Consequence for evaluation: judge parenting by what the child does afterwards in gyms it has not seen (first and second derivatives vs the baseline agent), not by how much the parent talked.

## [DIRECTION, Rohin 2026-09-10] Parents at agentic-architecture intelligence; a parental society; recursion as future work
Parents must be as smart as Fable/Codex in the agentic sense — long-horizon agent harnesses with tools, context and judgment over a strong frozen model — not a 14B chat call with a bounded playbook. Their weights never change ("mobile intelligence"): they keep enough judgment to change methods and react to a child's trajectory. When scaling breadth (each child runs for days across many nodes) the parents form a society that learns across all tasks and children through shared, nonparametric state (ledgers, playbooks, curricula), so parenting quality compounds without training the parent. Benefits: uses the base model's intelligence for parenting, so the parent corpus can be simpler and more dynamic; curricula and gyms improve from what parents observe. Implementation sketch (Fable): the parent becomes an agent loop with read-only tools over the child's life directory (ledger, probes, gate decisions, ritual/efficiency metrics, prior briefs) and over the other children's summaries; it writes briefs, proposes curriculum moves, and appends to a shared parental ledger; the strongest available model serves it; leak scan and target-blindness remain hard rules. FUTURE (not this system): recursion — children becoming parents; the first step toward it is a parent that learns to teach across many children. Cross-link: Rohin's other continual-learning project needs the same teaching-system-that-learns.

## [DIRECTION, Rohin 2026-09-10] Integrate existing parenting into a distributed harness; then augment what is taught
The learner competes with a SOTA agentic harness from a far weaker base, so matching harness-level continual learning takes time and scale. We integrate what harness agents already do (planning, verification, reflection, skill reuse, backtracking, budget awareness, persistence) into a distributed parenting harness with agentic-intelligence parents, then augment the curriculum. Curriculum draft with stages, gym shapes, parent roles and pre-registered exit criteria: research_notes/CURRICULUM_DRAFT_v1.md (persistence first; anti-lock-in generalisation; recurrent-CoT metacognition; learning to learn). To be folded into NEXT_EXPERIMENT_DESIGN_v1.md when the design workflow lands.

## [FUTURE / NEXT PAPER, Rohin 2026-09-10] Collaborative populations, divergent agents, learning from people
Parked in research_notes/NEXT_PAPER_POPULATIONS.md: philosophy (emotions/low sentience as compressed intelligence for agency; collaboration-maxxing vs intelligence-maxxing; diversity required), formal backing (Lazer & Friedman 2007 slow-diffusion result; Hong & Page 2004; novelty search / QD / MAP-Elites), the (temperature, plasticity) reduction of "sentience", and the design seeds (dreaming over the union of logs; vocabulary divergence; merge schedules designed against premature convergence; human parents via the relay path; explorer/exploiter roles; parental society; recursion). Not for the current abstract.

## [NEXT EXPERIMENT PINS, Rohin + advisor thread, 2026-09-10] Four things to pin before the run
Rohin's design: an agentic learning harness for parents built on SOTA models, so parenting scales in duration and in parallel count; parents learn from intermediary outcomes (as our research agents do) and grow with the learner; the learner is scaled far more (many parallel lives, far more self-reflection and metacognition); the child's thoughts are shared with the parent through discussion so communication is learned as needed; the write works, the compiler is decent but unfinished — pre-tune before the run; test = verifiable gym improvement of the taught agent vs a baseline harness agent on the SAME base model.
Pins (advisor, adopted with our specifics):
1. **Gyms and contamination; baseline first.** Run the untaught baseline before anything: if it is near saturation there is no room. CompilerGym: base 0.47–0.49 vs -Oz 0.522 vs best adapters 0.529 — little headroom on the 8-program panel; the disjoint panel has more (base 0.257, -Oz per program 0.03–0.71). Add at least one verifiable gym with headroom and low pretraining saturation; held out by source; kernel benchmarks are pretraining-heavy (caution).
2. **"Learned communication" = adaptive teaching, the cheap version.** The parent sees the student's reflections and adjusts its next instruction (our pattern parent v3 already does a fixed form of this: previous brief + echo rate). Arm: adaptive parenting vs fixed-curriculum parenting, same gyms, same students. The expensive version (a learned protocol) is its own research problem — not this run.
3. **Reward-hacking gate on what the parent can see.** Parents that adapt to any signal downstream of the evaluation will teach the metric. Rule: the parent may read the child's ledger, ritual/efficiency metrics, gate decisions on the GATE panel, and other parents' ledgers; it may never read report-panel or test-gym scores, and evaluation gyms are parent-blind. Log every parent input (provenance) so the gate is auditable. (Our classroom parent's admission signal was test-adjacent — do not repeat.)
4. **Finish the compiler before scaling parenting.** Near-duplicate collapse, recency weighting, provisional commits confirmed at the next probe, disjoint gate panel — tuned on the disjoint-panel and text-memory results — before any large run; a bigger run over a shaky write path is expensive noise.
Paper: the harness (measurement + parenting infrastructure) may be described in Methods/Discussion; not in the abstract. These pins fold into NEXT_EXPERIMENT_DESIGN_v1.md with the curriculum draft.

## [DIRECTION, Rohin 2026-09-10] Planning is the hardest part of teaching-to-learn; goals in layers; frontier estimation as the parent's organ
Rohin: self-cognition must be planned but aware; two kinds of thought (planning vs free-flow that builds toward plans) with self-corrections and goal creation; goals in layers (state → episode → lifetime), all learned; the child thinks enormously during parenting and far more than a normal agent in the gym because learning only comes from thinking. Reference: Pappalardo (ICLR 2026, ULEE): a goal-search policy plus a judge predicting POST-ADAPTATION performance keeps the curriculum at the moving frontier. For us: the parent's core organ is a frontier estimate ("what can the student almost do after working through it"), inferred from the child's shared reflections first (explicit judge only if too noisy); curriculum order re-ranked as the parent observes; design against frontier collapse (conservative vs difficulty-chasing) with logged estimates and a reset rule; goal layers taught as content; planning vs free-flow thought measured; thinking budget raised equally across arms with a pilot. Full addendum: research_notes/DESIGN_ADDENDUM_goals_and_frontier_2026-09-10.md — to be folded into NEXT_EXPERIMENT_DESIGN_v1. Outreach to Pappalardo endorsed (ask the stability question).
