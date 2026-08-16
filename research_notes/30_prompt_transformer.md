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
