# Agentic parent harness — spec addendum (2026-09-10, after Rohin's decisions)

## Provider: NVIDIA inference hub (Astra)
- Endpoint: `https://inference-api.nvidia.com/v1/chat/completions` (OpenAI-compatible). Model id: `openai/openai/gpt-6-astra`. Uses `max_completion_tokens` (not `max_tokens`); usage reports `completion_tokens_details.reasoning_tokens`. Pass an optional `reasoning_effort` if accepted (test result recorded in COORDINATION).
- Credentials: `PARENT_API_KEY` from the environment at process start only; never written to disk, logs or ledgers; masked in any debug output. The current key expires ~2026-09-18; rotation is Rohin's call.
- Budget: reasoning maxed at the start; Rohin will say if cost must come down.

## Two-parent room, NO HOLDUPS (Rohin)
- Parent A = Astra on the node, the fast loop: invoked at every sleep boundary per child, bounded dialogue (≤ 3 exchanges), produces brief + frontier estimate + curriculum move.
- On-node self-check: a second Astra call with a VERIFIER prompt (critique for answers/leaks/overreach/metric-teaching) runs immediately; if it flags, the brief is regenerated once, then FALLBACK. The delivered brief is written at once as `parent_brief.txt` with `status: provisional`.
- Parent B = Fable, asynchronous principal (the laptop session's 30-minute self-check): audits delivered briefs post hoc, may append an audit note and issue a corrective brief at the NEXT sleep, re-ranks curriculum across children, maintains the parental society playbook. It never blocks delivery: if the laptop/session is off, nothing waits. Delivered briefs later confirmed or corrected get `status: audited` in the ledger.
- Everything logged with provider/model/prompt_version; no keys.

## Also decided
- Rent more GPUs for the next experiment once the design is rich enough to scale (lease quota is a rolling 30-day window; bookings ≤ ~34 h ahead).

## Parent–child communication and what the parent monitors (Rohin, 2026-09-10)
The parent does NOT judge every thought. It judges whether the child is thinking ENOUGH and whether the thinking is done WELL, where good thinking = expanding (new hypotheses, branches, goals), connected (references back to earlier states, contrasts, RETURNs), and self-verified at a good rate (checks of predictions against outcomes, explicit "let me verify", corrections). The child must keep asking itself the questions that force thinking into learning — should I think more? plan more? am I over-thinking? do I need a goal here? — and the parent watches whether those questions appear and whether the structure and the output improve over cycles.
Monitoring metrics (per situation and per state, aggregated per window; computed from the ledger, no LLM judgement): thought volume (chunks and tokens per situation/state; budget fraction used), self-question density (the meta-questions above per 1k tokens), verification rate (verification events per 1k tokens; predictions checked against outcomes), connectedness (references to earlier states/situations, RETURNs, contrast phrases per state), expansion (distinct hypotheses/actions/goals per situation; branches when k>1), and the outcome curve (efficiency and scores). The parent reads these as rates and trends; it reads raw thought only as samples.
Channels, both logged: (1) ENVIRONMENTAL — most interaction stays inside the child's outputs and the world's outcomes; (2) DIRECT — at each sleep boundary the child may address the parent in its review state (`TO PARENT:` lines: what it thinks it learned, what it is unsure of, what it wants next); the parent replies with the brief (≤ 10 lines) and at most two questions the child answers at its next wake; ≤ 3 exchanges per boundary, then silence until the next sleep. The parent's frontier estimate and curriculum move are logged with the exchange. Parent text never enters the sleep corpus (thinker/compiler line); the child's own `TO PARENT:` lines are its thoughts and may.
