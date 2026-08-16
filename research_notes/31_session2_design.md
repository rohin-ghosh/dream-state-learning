# Note 31 — Session-2 design doc (opened 2026-08-15)

## The what-matters taxonomy (what LTM must hold; each independently testable)
1. WORLD FACTS → planning without rediscovery → use-weighted retention +
   win rate (v1.1 test on leakage-engineered worlds, AP(credit→type) ≤ ~0.7).
2. NEGATIVE KNOWLEDGE (dead ends, failures) → exploration efficiency →
   repeat-failure/revisit rates. **Missing from the world's fact schema —
   highest-value addition. Worlds must EMIT failure facts + contain
   REPEATING TRAPS so retaining them pays.**
3. PROCEDURES/SKILLS (tool recipes) → faster execution → episode length on
   stored-how-to tasks (habitual-tier candidate).
4. EPISODIC ANCHORS → case-based reuse → second-encounter speedup on
   repeated goal families.
5. ATTEMPT HISTORY / SELF-KNOWLEDGE → progress/stall detection (the input
   for future goal-drift policy; policy stays frozen this session, but the
   environment logs attempts so the content exists).
6. GAP MAP (known unknowns) → directed exploration → S4 gap-aware read
   vs naive read (the S4 fix, now a measured arm).

## Design principles carried in
- One head, six content types: candidate-in-context input generalizes;
  dependency credit generalizes (avoided-trap = a dependent use).
- Each content type independently load-bearing (hint-decor trick × 5).
- Result = a HELP PROFILE per policy, not one number (better figure).
- v2 store: semantic-fingerprint card-box (read = one attention head over
  life); text payloads primary, o-vector ablation.
- Poverty regime: mem-hidden ≈ 32-tier pressure or slot-budget analog;
  calibration curves for the head alongside AUC; horizon-curriculum
  transfer curve; never-block read cadence; hysteresis in any arbitration.

## v2 store REVISED (Rohin's correction, 2026-08-15): net-first
Card-box was instrument-first design (v1's sin, milder). REVISED: the memory
is an ATTRACTOR NET — modern-Hopfield-style pattern pool; similar patterns
converge into shared basins; retrieval = PATTERN COMPLETION ("recreate the
vibe"): project prompt-space state into memory space, dynamics converge,
completed pattern returns as the felt-attentioned vector to the prompt
engine. Sequences via hetero-associative CHAINING (each completion points to
the next pattern; long memories = chained short attractors). Importance =
PRESS DEPTH (felt scalar = write strength = basin depth; no stored dials);
dream = basin-landscape maintenance (re-press what mattered, let junk
flatten). Theory on our side: modern Hopfield ≡ transformer attention
(Ramsauer et al.) — the net read and attention-read are the same operation;
capacity exponential in dimension (the 100M-1B-token scale argument).
CARD-BOX DEMOTED TO INSTRUMENTATION: an external logging shadow used only to
build probes (cue-in, completion-quality-out). Design order corrected:
memory for the system; instruments around the memory.
Honest costs (work items): vector→prompt-engine translation training;
probe machinery for BLENDED memories (prototypes).

## v2 store, FINAL FORM (Rohin's derivation, 2026-08-15): the explicit memory graph
Discrete embedded items + thread-links (sequence pointers) + felt-weighted
writes; read = project current state into memory space, neighborhood grab,
thread walk, project sequences back to prompt space. Untrained retrieval
mechanics (stable/scalable, vector-DB family) + LEARNED projections
(critical: frozen embedders cluster by SEMANTIC similarity, not TASK
similarity — template-twins embed together while task-linked pairs sit far;
the learned projection is read-side felt-shaping). Relation to Hopfield:
one Hopfield step = soft-kNN (his neighborhood grab); his thread loops =
the iteration made explicit; the ONE deep difference = verbatim return vs
RECONSTRUCTION (denoise/blend into prototypes) → Hopfield reconstruction =
v3 upgrade when blending measurably matters; sparse-Hopfield (read-side
salience) meets our write-side salience there. Weights-as-memory rejected
(interference, no audit). Passes yesterday's rule: no dials, not
instrument-first — probeable by luck, not by design. Hopfield community's
own open problems list ends at "deciding what to preserve" = our thesis,
arrived at from the substrate direction (convergence validation #4).

## Hopfield Q&A (2026-08-15, for the record)
Post-trained memory (facts→LLM weights) ≠ fast-weight MLP (runtime SGD into
a side-net; a poor man's Hopfield: no iterative cleanup, imperfect one-shot
writes, no convergence guarantee) ≠ modern Hopfield (EXPLICIT pattern
storage — one-shot append — + reconstructive iterative retrieval,
exponential capacity; a hybrid: card-box storage, net retrieval).
Not out-of-the-box because it lacks the four organs: task-shaped
projections (felt read-side), write policy (press depth — their own open
problem "deciding what to preserve"), memory management (our dream), and
payload translation. Substrate physics without policy; felt turns a
substrate into a memory. Scaling reality: ANN graphs retrieve ~log-time at
billions (production-proven); Hopfield is linear-per-step (sparse variants
= fixes). Hopfield's edge = reconstruction/blending, not speed → graph v2,
Hopfield dynamics v3.

## Two-tier resolution (Rohin, 2026-08-16) — the oscillation was CLS
EPISODIC tier (fast): explicit graph — one-shot, exact, auditable ("post-it
note"). GIST tier (slow): PARAMETRIC — LoRA/side-model trained during dream
by salience-weighted replay ("crystallized learned intelligence", geometric
search, good-paths representation) = the ORIGINAL run-2 consolidation plan,
now justified. Migration episodic→gist at scale = Rohin's continuous-
pretraining idea = hippocampus→cortex. Gist lives BESIDE the reasoner,
never in the composer (memory-in-composer-weights = follow-memories-instead-
of-fill confound — Rohin's catch); composer weights hold habits only.
Amygdala = felt writes (significance tagging at encoding — biology receipt);
press-depth ok, stored dials still jank. Hopfield reassigned to attention/
retrieval dynamics, not LTM. Composer forward pass = iterative build→query
LTM→rebuild loop; stop = ignition (satisfied) or saturation (prompt full of
memory). EVAL: episodic tier → retrieval profile; gist tier → behavioral
only (transfer, analogy, second-encounter speedup) — two lanes in the
benchmark doc.

## Episodic-as-tool (Rohin, 2026-08-16) — architecture leaned out
Episodic tier = append-only log + search TOOL, outside the cognitive
architecture (storage cheap; models good at tool search+verification).
Consequence: NO write policy on episodic (write everything); felt's
selectivity migrates to where scarcity lives: (1) DREAM REPLAY CURATION —
which experiences train the gist LoRA; (2) PROMPT ADMISSION — reads.
Gist ≠ episodic: deep sequence-trained gist can regenerate TYPICAL episodes
(prototypes/blends) but never that-specific-Tuesday (reconstruction loses
one-time details = human false memories). So: gist in-loop as intuition;
episodic tool consulted for specifics/verification — Rohin's own
introspection ("geometric search great, fact recall poor, facts are easy to
store anyway"), formalized.
SESSION-2 EXPERIMENT RESHAPED (for Rohin's red pen, not decided): not
"our store vs RAG" — episodic is commodity RAG for all arms; the comparison
is "dream-trained gist + felt curation vs tool-RAG-only agent", behavioral
lanes (transfer, second-encounter speedup, mid-task guidance).

## The person-hierarchy + memory-as-generation (Rohin, 2026-08-16)
THIRD person = pretrained weights (world as described) / SECOND person =
gist-LoRA (world as it responded to YOU — lived subspace of the base
model's reality) / FIRST person = context (now). Cascade: context 1M →
gist-LoRA ~100M-token life (sleep-written, felt-curated) → base weights
(deep hibernation = fold LoRA into base; third clock).
MECHANISM for xyz→xzy (analogical sequence completion): gist = small LM
fine-tuned on lived episodes; READS ARE GENERATIVE COMPLETIONS ("did abc,
failed—" → continues with nearest lived repair pattern). Sequence matching
+ vicinity + query-dependent geometries fall out of LM behavior on an
autobiographical corpus. Training: LM loss on felt-curated replay +
REPAIR-PAIR emphasis (dependency-credit machinery auto-mines failed-seq →
later-fix pairs from logs — v1 infrastructure reused as data labeler).
FLAGS: generative memory confabulates → episodic tool = verification layer
(two-tier split is the hallucination control, not redundancy); LoRA
capacity-vs-life-length = empirical (core run-2 measurement); the xyz test
is directly benchmarkable (novel structurally-similar failures → repair-
finding speed vs tool-RAG-only) — candidate HEADLINE experiment.

## Late pins (2026-08-16)
TOOL USE across the person-hierarchy: competence = base (3rd person);
habits/which-tool-when-for-me = gist (2nd person); API details = episodic
tool. Memory remembers your RELATIONSHIP with tools, never the tools.
READS RE-PRESS (from Rohin's introspection = testing effect /
reconsolidation): every read applies a reduced-strength write → vividness
tracks recency-of-USE, not recency-of-writing. One line of design.
GENERATIVE REPLAY (re-derived; known CL technique, pseudo-rehearsal): deep
hibernation trains the base on the MEMORY'S OWN GENERATIONS (gist-
compressed, felt-shaped retellings), not raw logs. Forgetting becomes
graceful at every tier: important old memory is either regenerable from
gist or already folded into base by its own retellings.

## Culmination pins (Rohin, 2026-08-16, late)
SALIENCE IS EMERGENT — the resolution of the felt head's fate: the explicit
head = the amortized, attributable, PROVABLE form (needed for the science);
end-to-end emergence into a policy-trained composer = the destination
(novelty/importance-seeking absorbs into broad outcome training — the
dopamine is what policy-loss looks like from inside). Amortize-then-
integrate applies to felt itself; the head is scaffolding for a claim.
COMPOSER FORWARD PASS FINAL: state+I/O in context → GENERATE memory queries
(queries are tokens → self-instrumenting/auditable) → gist returns
geometries → loop until ignition/saturation → attention over accumulated
window reconstructs the injection prompt. Adjacent art: iterative RAG
(Self-Ask/FLARE) = heuristic token-space cousins; trained composer over
generative lived-subspace = the delta.
Event-level slow loss after full events (super-EOS) closes the
token→context→sequence→event hierarchy. Training: millions of parallel
short subprompts (parallel lives × horizon curriculum) → longer sequences →
deploy baby (empty LTM, generalized meta-decisions) into the field.
