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
