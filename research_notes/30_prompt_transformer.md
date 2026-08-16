# Note 30 — The Prompt Transformer (Rohin's drawing session, 2026-08-15)

**The insight: the outer system is a transformer whose tokens are PROMPTS.**
token↔prompt · context↔episode-history/workspace · attention↔felt attention
(over LTM + transformer outputs + input space) · next-token↔next-prompt ·
EOS↔super-end-token · KV-cache↔LTM · residual stream↔residual prompts.
LTM prefills prompt space → prefills context → NEVER touches the model.

## Clock
Outer ticks on EVENTS (inner EOS, external input, ignition threshold), not
tokens. Never-block: inner loop always completes on the last composed prompt.

## Role assignment (from prior pins, now consistent)
- FELT: the only forward-pass learner — scores/composes what enters the next
  prompt (admission weights).
- POLICY: the loss function; backward passes only; judges outer-episode
  outcome at super-EOS; never gates forward flow.
- DREAM: when the backward pass runs — replay outer-episodes, policy-loss
  backprop through felt + prompt engine, ignited content written/renormalized
  to LTM. "SLEEP IS THE BACKWARD PASS OF LIFE."

## v0 exists
S4's read path (goal header + top-k LTM + inputs + residual) = the prompt
engine with hand-wired composition. Learned version = trained composer.

## Free training trick from the isomorphism
NEXT-PROMPT PREDICTION as pretraining: behavioral-clone the prompt engine on
logged successful agent trajectories (teacher-forcing at prompt granularity)
before RL. = the "pretrain generalizable agency" phase, with a concrete loss.
Curriculum: stage 0 = no-LTM short sequences (plain chat agent) → grow
horizon and memory-dependence together.

## Open
Exact prompt-composition parameterization (select-and-fill vs free-gen);
where tool-use actions live in the output space; critic form at super-EOS.

## Addendum (same day) — modularity + role assignments
MODULARITY: new senses = new felt heads (+ translation training); engine
swappable (LLM ↔ action model); prompt engine = consolidation layer ≈
robotics arbitration — CONVERGENCE VALIDATION #3 (derived from memory-first
principles, meets motor-control's derivation; after biology + GWT).
INTERFACE CHOICE: language (readable reasoning, translation loss) vs vectors
— π0.5 ships the language interface (self-emitted subtask), Helix ships the
latent one; hybrid pinned. Two transformers in the loop: small composer +
big frozen reasoner.
GOAL CASCADE: policy holds/switches goals (slow, LIVE online-trained) →
prompt engine: goal+state → sequence-level goals (medium) → frozen
transformer: token-level execution (fast). Stop = threshold per tier
(inner EOS / outer super-EOS / goal-switch ignition).
DREAM SIMPLIFIED: context window IS the ignited content → dream = single
write function window→(felt-weighted)→LTM; no raw input/output access
(biology: sleep replays the hippocampal buffer, not the sensory stream).
Trained as a consequence of felt training, not a separate post-train phase.
MEMORY TAXONOMY: facts → declarative LTM; tool-use → procedural/skill LTM
(Voyager precedent); habits → prompt-engine WEIGHTS (amortized policies).
Tool bench in the loop from day one.
Scale answer (already in note 30): next-prompt pretraining + horizon
curriculum + policy loss at super-EOS.
